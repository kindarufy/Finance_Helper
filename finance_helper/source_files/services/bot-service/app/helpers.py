"""Модуль сервисного слоя Telegram-бота Finance Helper."""
import calendar
from collections import defaultdict
from datetime import date

from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, InlineKeyboardButton, InlineKeyboardMarkup, Message

from . import api, ux
from .common import PICK_LIMIT, fmt_money, op_emoji, quick_date_help, ru_type
from .keyboards import MENU_KB, natural_confirm_kb
from .states import NaturalFlow
from .utils import infer_default_category, parse_natural_operation



def _format_limit_alert(alert: dict) -> str:
    """Форматирует данные для сценария «imit alert»."""
    threshold = int(alert.get("threshold") or 0)
    icon = "⚠️" if threshold >= 100 else "🔔"
    return (
        f"{icon} {alert.get('label', 'Лимит')} — достигнуто {threshold}%\n"
        f"Потрачено: {fmt_money(alert.get('spent'))} {alert.get('currency', '')}\n"
        f"Лимит: {fmt_money(alert.get('amount'))} {alert.get('currency', '')}\n"
        f"Остаток: {fmt_money(alert.get('remaining'))} {alert.get('currency', '')}"
    )


async def _send_limit_alerts(message: Message, payload: dict):
    """Отправляет данные, относящиеся к сценарию «limit alerts»."""
    for alert in payload.get("limit_alerts") or []:
        await message.answer(_format_limit_alert(alert), reply_markup=MENU_KB)


async def build_limit_overview_text(telegram_id: int) -> str:
    """Собирает итоговую структуру или текст для сценария «limit overview text»."""
    items = await api.limits_overview(telegram_id)
    if not items:
        return "Активных лимитов пока нет."
    lines = ["💸 Активные лимиты и бюджеты:"]
    for item in items:
        lines.append(
            f"• {item['label']}\n"
            f"  Потрачено: {fmt_money(item['spent'])}/{fmt_money(item['amount'])} {item['currency']}\n"
            f"  Остаток: {fmt_money(item['remaining'])} {item['currency']} • {item['percent_used']}%"
        )
    return "\n".join(lines)


async def build_monthly_report_text(telegram_id: int, year: int, month: int) -> str:
    """Собирает итоговую структуру или текст для сценария «monthly report text»."""
    workspace_id = await _current_workspace_id(telegram_id)
    payload = await api.monthly_report(telegram_id, year, month, workspace_id=workspace_id)
    lines = [
        f"📅 Ежемесячный отчёт за {month:02d}.{year}",
        "",
        f"➖ Расходы: {fmt_money(payload['expense_total'])}",
        f"➕ Доходы: {fmt_money(payload['income_total'])}",
        f"💰 Баланс: {fmt_money(payload['balance'])}",
        "",
        f"Δ расходы: {payload['expense_delta']:+.2f}",
        f"Δ доходы: {payload['income_delta']:+.2f}",
        f"Средний расход в день: {fmt_money(payload['avg_daily_expense'])}",
        f"Средний доход в день: {fmt_money(payload['avg_daily_income'])}",
        "",
        "Топ категорий:",
    ]
    top_categories = payload.get('top_categories') or []
    if top_categories:
        for item in top_categories:
            lines.append(f"• {item['category']} — {fmt_money(item['amount'])}")
    else:
        lines.append("• Нет расходов за период")
    by_user = payload.get('expense_by_user') or []
    if by_user:
        lines.extend(["", "По участникам:"])
        for item in by_user:
            lines.append(f"• {item['user']} — {fmt_money(item['amount'])}")
    return "\n".join(lines)


async def build_spending_analysis_text(telegram_id: int, year: int, month: int) -> str:
    """Собирает итоговую структуру или текст для сценария «spending analysis text»."""
    workspace_id = await _current_workspace_id(telegram_id)
    payload = await api.spending_analysis(telegram_id, year, month, workspace_id=workspace_id)
    return payload.get("text") or "Недостаточно данных для AI-анализа."


async def build_workspace_overview_text(telegram_id: int) -> str:
    """Собирает итоговую структуру или текст для сценария «workspace overview text»."""
    try:
        active = await api.get_active_workspace(telegram_id)
    except Exception:
        active = None
    items = await api.list_workspaces(telegram_id)
    if not items:
        return "У тебя пока только личное пространство."
    lines = ["👨‍👩‍👧‍👦 Мои бюджетные пространства:"]
    if active:
        try:
            members = await api.list_workspace_members(telegram_id, int(active['id']))
        except Exception:
            members = []
        lines.append(f"Активное сейчас: {active['name']} ({active['type']}) • валюта {active.get('base_currency', 'RUB')} • участников: {len(members)}")
        lines.append("")
    for item in items:
        mark = "✅" if item.get("is_active") else "•"
        role = item.get("my_role") or "member"
        lines.append(f"{mark} {item['name']} — {item['type']} ({role})")
    if active:
        lines.append("")
        lines.append("Подсказка: здесь можно переключать пространства, смотреть вклад участников и управлять семейным бюджетом.")
    return "\n".join(lines)




async def _current_workspace_id(telegram_id: int) -> int | None:
    """Возвращает текущее значение для сценария «workspace id»."""
    try:
        active = await api.get_active_workspace(telegram_id)
        return int(active["id"])
    except Exception:
        return None


async def _miniapp_url_for_user(telegram_id: int) -> str:
    """Выполняет действие «miniapp url for user» в рамках логики Finance Helper."""
    workspace_id = await _current_workspace_id(telegram_id)
    return await api.build_miniapp_url(telegram_id, workspace_id=workspace_id)


async def _send_export_document(message: Message, telegram_id: int, mode: str, fmt: str):
    """Отправляет данные, относящиеся к сценарию «export document»."""
    workspace_id = await _current_workspace_id(telegram_id)
    today = date.today()
    first_day = today.replace(day=1)
    date_from = None
    date_to = None
    op_type = None
    if mode == "month":
        date_from, date_to = first_day, today
    elif mode == "month_expense":
        date_from, date_to, op_type = first_day, today, "expense"
    elif mode == "month_income":
        date_from, date_to, op_type = first_day, today, "income"
    data, filename, _content_type = await api.export_file(
        telegram_id=telegram_id,
        fmt=fmt,
        date_from=date_from,
        date_to=date_to,
        op_type=op_type,
        workspace_id=workspace_id,
    )
    pretty_mode = {
        "month": "текущий месяц",
        "month_expense": "расходы текущего месяца",
        "month_income": "доходы текущего месяца",
        "all": "все операции",
    }.get(mode, mode)
    await message.answer_document(BufferedInputFile(data, filename=filename), caption=f"Готово ✅ Экспорт: {pretty_mode} ({fmt.upper()})")


def pretty_commands_text() -> str:
    """Выполняет действие «pretty commands text» в рамках логики Finance Helper."""
    return ux.pretty_commands_text()

async def _list_categories_safe(telegram_id: int, op_type: str | None = None, include_archived: bool = False) -> list[dict]:
    """Выполняет действие «list categories safe» в рамках логики Finance Helper."""
    try:
        return await api.list_categories(telegram_id, category_type=op_type, include_archived=include_archived)
    except Exception:
        return []


async def _category_name_by_id(telegram_id: int, category_id: int) -> str | None:
    """Выполняет действие «category name by id» в рамках логики Finance Helper."""
    for op_type in ("expense", "income"):
        cats = await _list_categories_safe(telegram_id, op_type=op_type, include_archived=True)
        for cat in cats:
            if int(cat["id"]) == int(category_id):
                return cat["name"]
    return None


async def categories_kb(telegram_id: int, op_type: str, prefix: str, include_keep: bool = False, keep_text: str = "Без изменений") -> InlineKeyboardMarkup:
    """Выполняет действие «categories kb» в рамках логики Finance Helper."""
    categories = await _list_categories_safe(telegram_id, op_type=op_type, include_archived=False)
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for idx, cat in enumerate(categories, 1):
        label = f"{cat.get('emoji') or '🏷'} {cat['name']}"
        row.append(InlineKeyboardButton(text=label, callback_data=f"{prefix}:{cat['id']}"))
        if idx % 2 == 0:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    if include_keep:
        rows.append([InlineKeyboardButton(text=keep_text, callback_data=f"{prefix}:keep")])
    if not rows:
        rows.append([InlineKeyboardButton(text="Другое", callback_data=f"{prefix}:fallback")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def category_action_type_kb(action: str) -> InlineKeyboardMarkup:
    """Выполняет действие «category action type kb» в рамках логики Finance Helper."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔴 Категория расхода", callback_data=f"cattype:{action}:expense"),
                InlineKeyboardButton(text="🟢 Категория дохода", callback_data=f"cattype:{action}:income"),
            ],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="catmenu:root")],
        ]
    )


async def category_manage_menu_kb() -> InlineKeyboardMarkup:
    """Выполняет действие «category manage menu kb» в рамках логики Finance Helper."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👀 Посмотреть расходы", callback_data="catmenu:view:expense"),
                InlineKeyboardButton(text="👀 Посмотреть доходы", callback_data="catmenu:view:income"),
            ],
            [
                InlineKeyboardButton(text="➕ Новая категория", callback_data="catmenu:create"),
                InlineKeyboardButton(text="🏷 Добавить ключевое слово", callback_data="catmenu:add_alias"),
            ],
            [
                InlineKeyboardButton(text="✏️ Переименовать", callback_data="catmenu:rename"),
                InlineKeyboardButton(text="😀 Emoji", callback_data="catmenu:emoji"),
            ],
            [
                InlineKeyboardButton(text="🗃 Архивировать", callback_data="catmenu:archive"),
                InlineKeyboardButton(text="🧹 Удалить ключевое слово", callback_data="catmenu:delete_alias"),
            ],
        ]
    )


async def _render_categories_text(telegram_id: int, op_type: str) -> str:
    """Выполняет действие «render categories text» в рамках логики Finance Helper."""
    cats = await _list_categories_safe(telegram_id, op_type=op_type, include_archived=False)
    title = "🔴 Категории расходов" if op_type == "expense" else "🟢 Категории доходов"
    if not cats:
        return f"{title}\nПока пусто."
    lines = [title, ""]
    for idx, cat in enumerate(cats, 1):
        try:
            aliases = await api.list_aliases(telegram_id, cat["id"])
        except Exception:
            aliases = []
        alias_text = ", ".join(a["alias"] for a in aliases[:8]) if aliases else "—"
        lines.append(f"{idx}) {cat.get('emoji') or '🏷'} {cat['name']} — ключевые слова: {alias_text}")
    return "\n".join(lines)


def ops_picker_kb(action: str, items: list[dict], offset: int) -> InlineKeyboardMarkup:
    """Выполняет действие «ops picker kb» в рамках логики Finance Helper."""
    rows: list[list[InlineKeyboardButton]] = []
    for op in items:
        op_id = op["id"]
        emoji = op_emoji(op.get("type", ""))
        amount = fmt_money(op.get("amount"))
        cat = (op.get("category") or "—")[:18]
        text = f"{emoji} #{op_id} {amount} {cat}"
        callback = f"{action}:{op_id}"
        if action == "e":
            callback = f"e:{op_id}:{op.get('type', 'expense')}"
        rows.append([InlineKeyboardButton(text=text, callback_data=callback)])

    nav = []
    if offset > 0:
        nav.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"{action}pg:{max(0, offset - PICK_LIMIT)}"))
    if len(items) == PICK_LIMIT:
        nav.append(InlineKeyboardButton(text="➡️ Ещё", callback_data=f"{action}pg:{offset + PICK_LIMIT}"))
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton(text="❌ Отмена", callback_data=f"{action}cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def confirm_delete_kb(op_id: int) -> InlineKeyboardMarkup:
    """Выполняет действие «confirm delete kb» в рамках логики Finance Helper."""
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"dy:{op_id}"), InlineKeyboardButton(text="❌ Отмена", callback_data="dcancel")]]
    )


def natural_confirm_kb() -> InlineKeyboardMarkup:
    """Выполняет действие «natural confirm kb» в рамках логики Finance Helper."""
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="✅ Сохранить", callback_data="nsave"), InlineKeyboardButton(text="❌ Отмена", callback_data="ncancel")]]
    )


async def _match_or_infer_category(telegram_id: int, description: str | None, op_type: str) -> str:
    """Выполняет действие «match or infer category» в рамках логики Finance Helper."""
    if description:
        try:
            matched = await api.match_category(telegram_id, description, op_type)
            if matched.get("matched") and matched.get("category"):
                return matched["category"]["name"]
        except Exception:
            pass
        guessed = infer_default_category(description, op_type)
        if guessed:
            return guessed
    return "Другое"


async def _create_from_natural(message: Message, state: FSMContext, text: str) -> bool:
    """Выполняет действие «create from natural» в рамках логики Finance Helper."""
    parsed = parse_natural_operation(text, today=date.today())
    if not parsed:
        return False

    category = await _match_or_infer_category(message.from_user.id, parsed.get("description"), parsed["op_type"])
    payload = {
        "op_type": parsed["op_type"],
        "amount": parsed["amount"],
        "currency": parsed["currency"],
        "occurred_at": parsed.get("occurred_at") or date.today(),
        "category": category,
        "comment": parsed.get("description"),
        "raw_text": parsed.get("raw_text"),
    }
    await state.clear()
    await state.set_state(NaturalFlow.confirm)
    await state.update_data(natural_payload=payload)
    lines = [
        "Я распознала операцию так:",
        f"{op_emoji(payload['op_type'])} Тип: {ru_type(payload['op_type'])}",
        f"💰 Сумма: {fmt_money(payload['amount'])} {payload['currency']}",
        f"🏷 Категория: {payload['category']}",
        f"📅 Дата: {payload['occurred_at'].isoformat()}",
    ]
    if payload.get("comment"):
        lines.append(f"📝 Комментарий: {payload['comment']}")
    await message.answer("\n".join(lines), reply_markup=natural_confirm_kb())
    return True


def month_range(y: int, m: int) -> tuple[date, date]:
    """Выполняет действие «month range» в рамках логики Finance Helper."""
    last_day = calendar.monthrange(y, m)[1]
    return date(y, m, 1), date(y, m, last_day)


async def build_month_stats_text(telegram_id: int, y: int, m: int) -> str:
    """Собирает итоговую структуру или текст для сценария «month stats text»."""
    d1, d2 = month_range(y, m)
    all_ops = []
    offset = 0
    while True:
        items = await api.list_operations_page(telegram_id=telegram_id, limit=100, offset=offset, date_from=d1, date_to=d2)
        if not items:
            break
        all_ops.extend(items)
        offset += len(items)
        if len(items) < 100 or offset > 5000:
            break
    if not all_ops:
        return f"📊 Статистика за {y}-{m:02d}\nОпераций за этот месяц пока нет."

    income_total = 0.0
    expense_total = 0.0
    by_cat = defaultdict(float)
    for op in all_ops:
        amt = float(op["amount"])
        if op["type"] == "income":
            income_total += amt
        else:
            expense_total += amt
            by_cat[op.get("category") or "Без категории"] += amt

    balance = income_total - expense_total
    sorted_cats = sorted(by_cat.items(), key=lambda x: x[1], reverse=True)
    lines = [
        f"📊 Статистика за {y}-{m:02d} ({d1.isoformat()} — {d2.isoformat()})",
        f"🟢 Доходы: {fmt_money(income_total)}",
        f"🔴 Расходы: {fmt_money(expense_total)}",
        f"Баланс: {fmt_money(balance)}",
        "",
        "Куда потрачено (по категориям):",
    ]
    if not sorted_cats:
        lines.append("— расходов нет")
    else:
        for i, (cat, total) in enumerate(sorted_cats[:12], 1):
            lines.append(f"{i}) {cat}: {fmt_money(total)}")
    return "\n".join(lines)


