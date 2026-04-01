"""Готовые клавиатуры Telegram-бота для меню, отчётов, операций, лимитов и пространств."""
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    WebAppInfo,
)

from .common import fmt_money, op_emoji, PICK_LIMIT


MENU_KB = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🧠 Примеры"), KeyboardButton(text="📱 Mini App")],
        [KeyboardButton(text="➖ Расход"), KeyboardButton(text="➕ Доход")],
        [KeyboardButton(text="📋 Последние операции"), KeyboardButton(text="📊 Статистика")],
        [KeyboardButton(text="✏️ Изменить"), KeyboardButton(text="🗑 Удалить")],
        [KeyboardButton(text="💸 Лимиты"), KeyboardButton(text="🗂 Категории")],
        [KeyboardButton(text="🗓 Отчёты"), KeyboardButton(text="👨‍👩‍👧‍👦 Общие бюджеты")],
        [KeyboardButton(text="📤 Экспорт"), KeyboardButton(text="🏦 Импорт")],
        [KeyboardButton(text="❓ Помощь"), KeyboardButton(text="📌 Команды")],
    ],
    resize_keyboard=True,
)


def budget_menu_kb() -> InlineKeyboardMarkup:
    """Создаёт клавиатуру раздела лимитов и бюджетов."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 Лимит на день", callback_data="budget:daily")],
        [InlineKeyboardButton(text="🗓 Лимит на месяц", callback_data="budget:monthly")],
        [InlineKeyboardButton(text="🏷 Лимит по категории", callback_data="budget:category")],
        [InlineKeyboardButton(text="📊 Активные лимиты", callback_data="budget:view")],
    ])


def reports_menu_kb() -> InlineKeyboardMarkup:
    """Создаёт клавиатуру раздела отчётов."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📆 Отчёт за текущий месяц", callback_data="report:this")],
        [InlineKeyboardButton(text="📅 Отчёт за прошлый месяц", callback_data="report:last")],
        [InlineKeyboardButton(text="🤖 AI-анализ текущего месяца", callback_data="report:analysis")],
        [InlineKeyboardButton(text="🔔 Настроить автоотчёт", callback_data="report:setup")],
        [InlineKeyboardButton(text="ℹ️ Статус автоотчёта", callback_data="report:status")],
        [InlineKeyboardButton(text="⛔ Выключить автоотчёт", callback_data="report:disable")],
    ])


def export_menu_kb() -> InlineKeyboardMarkup:
    """Создаёт клавиатуру раздела экспорта."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📄 CSV за текущий месяц", callback_data="export:month:csv")],
        [InlineKeyboardButton(text="📗 XLSX за текущий месяц", callback_data="export:month:xlsx")],
        [InlineKeyboardButton(text="📄 CSV расходы месяца", callback_data="export:month_expense:csv")],
        [InlineKeyboardButton(text="📗 XLSX расходы месяца", callback_data="export:month_expense:xlsx")],
        [InlineKeyboardButton(text="📄 CSV доходы месяца", callback_data="export:month_income:csv")],
        [InlineKeyboardButton(text="📗 XLSX доходы месяца", callback_data="export:month_income:xlsx")],
        [InlineKeyboardButton(text="📄 CSV все операции", callback_data="export:all:csv")],
        [InlineKeyboardButton(text="📗 XLSX все операции", callback_data="export:all:xlsx")],
    ])


def build_miniapp_open_kb(url: str) -> InlineKeyboardMarkup:
    """Создаёт клавиатуру с кнопкой открытия Mini App."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📱 Открыть Mini App", web_app=WebAppInfo(url=url))],
        [InlineKeyboardButton(text="🔗 Открыть по ссылке", url=url)],
    ])


def workspace_menu_kb() -> InlineKeyboardMarkup:
    """Создаёт клавиатуру раздела совместных пространств."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📂 Мои пространства", callback_data="ws:list")],
        [InlineKeyboardButton(text="📊 Статистика активного пространства", callback_data="ws:stats")],
        [InlineKeyboardButton(text="➕ Новый семейный бюджет", callback_data="ws:create:shared")],
        [InlineKeyboardButton(text="✈️ Бюджет поездки", callback_data="ws:create:trip")],
        [InlineKeyboardButton(text="🧰 Проектный бюджет", callback_data="ws:create:project")],
        [InlineKeyboardButton(text="👥 Участники активного пространства", callback_data="ws:members")],
        [InlineKeyboardButton(text="➕ Добавить участника", callback_data="ws:add_member")],
        [InlineKeyboardButton(text="⚙️ Управление участниками", callback_data="ws:manage_members")],
    ])


def workspace_switch_kb(items: list[dict]) -> InlineKeyboardMarkup:
    """Создаёт клавиатуру переключения между пространствами."""
    rows = []
    for item in items:
        marker = "✅ " if item.get("is_active") else ""
        rows.append([InlineKeyboardButton(text=f"{marker}{item['name']} ({item['type']})", callback_data=f"ws:switch:{item['id']}")])
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="ws:menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def workspace_role_kb() -> InlineKeyboardMarkup:
    """Создаёт клавиатуру выбора роли участника."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✍️ Editor", callback_data="ws:role:editor")],
        [InlineKeyboardButton(text="👀 Viewer", callback_data="ws:role:viewer")],
    ])


def ops_picker_kb(action: str, items: list[dict], offset: int) -> InlineKeyboardMarkup:
    """Создаёт клавиатуру выбора операции."""
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
    """Создаёт клавиатуру подтверждения удаления."""
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"dy:{op_id}"), InlineKeyboardButton(text="❌ Отмена", callback_data="dcancel")]]
    )


def natural_confirm_kb() -> InlineKeyboardMarkup:
    """Создаёт клавиатуру подтверждения распознанной операции."""
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="✅ Сохранить", callback_data="nsave"), InlineKeyboardButton(text="❌ Отмена", callback_data="ncancel")]]
    )


def workspace_manage_members_kb(workspace_id: int, items: list[dict], owner_tg: int | None = None) -> InlineKeyboardMarkup:
    """Создаёт клавиатуру управления участниками пространства."""
    rows = []
    for item in items:
        tg = int(item['telegram_id'])
        if owner_tg is not None and tg == owner_tg:
            continue
        name = f"@{item['username']}" if item.get('username') else str(tg)
        rows.append([InlineKeyboardButton(text=f"{name} ({item['role']})", callback_data=f"wsm:{workspace_id}:{tg}")])
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="ws:menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def workspace_member_actions_kb(workspace_id: int, member_telegram_id: int) -> InlineKeyboardMarkup:
    """Создаёт клавиатуру действий с выбранным участником."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✍️ Сделать editor", callback_data=f"wsmr:{workspace_id}:{member_telegram_id}:editor")],
        [InlineKeyboardButton(text="👀 Сделать viewer", callback_data=f"wsmr:{workspace_id}:{member_telegram_id}:viewer")],
        [InlineKeyboardButton(text="🗑 Удалить участника", callback_data=f"wsmx:{workspace_id}:{member_telegram_id}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="ws:manage_members")],
    ])
