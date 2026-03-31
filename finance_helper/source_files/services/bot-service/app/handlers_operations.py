"""Модуль сервисного слоя Telegram-бота Finance Helper."""
from datetime import date, timedelta

from aiogram import F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from . import api
from .bot import dp
from .common import PICK_LIMIT, fmt_money, op_emoji, quick_date_help, ru_type, safe_date_str
from .helpers import (
    _category_name_by_id,
    _create_from_natural,
    _current_workspace_id,
    _send_export_document,
    _send_limit_alerts,
    build_limit_overview_text,
    build_month_stats_text,
    categories_kb,
)
from .keyboards import MENU_KB, budget_menu_kb, build_miniapp_open_kb, confirm_delete_kb, export_menu_kb, ops_picker_kb
from .states import AddFlow, BudgetFlow, EditAnyFlow, NaturalFlow
from .utils import parse_add_command, parse_report, parse_user_date
from .navigation import try_interrupt_current_flow


@dp.message(F.text.in_({"➖ Добавить расход", "➖ Расход"}))
async def btn_add_expense(message: Message, state: FSMContext):
    """Обрабатывает пользовательский сценарий «add expense»."""
    await state.clear()
    await state.update_data(op_type="expense")
    await state.set_state(AddFlow.amount)
    await message.answer("Введи сумму расхода (например 450).", reply_markup=MENU_KB)


@dp.message(F.text.in_({"➕ Добавить доход", "➕ Доход"}))
async def btn_add_income(message: Message, state: FSMContext):
    """Обрабатывает пользовательский сценарий «add income»."""
    await state.clear()
    await state.update_data(op_type="income")
    await state.set_state(AddFlow.amount)
    await message.answer("Введи сумму дохода (например 30000).", reply_markup=MENU_KB)


@dp.message(AddFlow.amount)
async def addflow_amount(message: Message, state: FSMContext):
    """Выполняет действие «addflow amount» в рамках логики Finance Helper."""
    if await try_interrupt_current_flow(message, state):
        return
    try:
        amount = float((message.text or "").replace(",", "."))
        if amount <= 0:
            raise ValueError
    except Exception:
        await message.answer("Сумма должна быть числом больше 0. Пример: 450")
        return
    data = await state.get_data()
    op_type = data["op_type"]
    await state.update_data(amount=amount)
    await message.answer("Выбери категорию:", reply_markup=await categories_kb(message.from_user.id, op_type, "addcat"))


@dp.callback_query(F.data.startswith("addcat:"))
async def addflow_category(callback: CallbackQuery, state: FSMContext):
    """Выполняет действие «addflow category» в рамках логики Finance Helper."""
    raw = callback.data.split(":", 1)[1]
    data = await state.get_data()
    if "op_type" not in data or "amount" not in data:
        await callback.answer("Сначала нажми «Добавить расход/доход».", show_alert=True)
        return
    if raw == "fallback":
        category = "Другое"
    else:
        category = await _category_name_by_id(callback.from_user.id, int(raw)) or "Другое"
    await state.update_data(category=category)
    await state.set_state(AddFlow.comment)
    await callback.message.answer("Напиши комментарий (или отправь '-' если не нужен).")
    await callback.answer()


@dp.message(AddFlow.comment)
async def addflow_comment(message: Message, state: FSMContext):
    """Выполняет действие «addflow comment» в рамках логики Finance Helper."""
    if await try_interrupt_current_flow(message, state):
        return
    comment = (message.text or "").strip()
    if comment in ("-", ""):
        comment = None
    await state.update_data(comment=comment)
    await state.set_state(AddFlow.date)
    await message.answer(quick_date_help(), reply_markup=MENU_KB)


@dp.message(AddFlow.date)
async def addflow_date(message: Message, state: FSMContext):
    """Выполняет действие «addflow date» в рамках логики Finance Helper."""
    if await try_interrupt_current_flow(message, state):
        return
    data = await state.get_data()
    raw = (message.text or "").strip()
    if raw in ("-", ""):
        occurred_at = date.today()
    else:
        occurred_at = parse_user_date(raw, today=date.today())
        if occurred_at is None:
            await message.answer("Не удалось распознать дату.\n" + quick_date_help())
            return

    res = await api.create_operation(
        telegram_id=message.from_user.id,
        op_type=data["op_type"],
        amount=float(data["amount"]),
        category=data.get("category"),
        comment=data.get("comment"),
        source="buttons",
        occurred_at=occurred_at,
    )
    op = res["operation"]
    await message.answer(
        f"✅ Добавлено: #{op['id']} {op_emoji(op['type'])} {ru_type(op['type'])} {fmt_money(op['amount'])} • {op.get('category') or '—'} • {op['occurred_at']}",
        reply_markup=MENU_KB,
    )
    limit = res.get("limit")
    if limit and limit.get("limit_exceeded"):
        await message.answer(
            f"⚠️ Превышен лимит!\nСегодня: {fmt_money(limit['day_expenses_total'])} при лимите {fmt_money(limit['daily_limit'])}",
            reply_markup=MENU_KB,
        )
    await _send_limit_alerts(message, res)
    await state.clear()


# ----------------------------
# Последние операции и статистика
# ----------------------------
@dp.message(F.text.in_({"📋 Последние 10 операций", "📋 Последние операции"}))
async def btn_last10(message: Message):
    """Обрабатывает пользовательский сценарий «last10»."""
    items = await api.list_operations(message.from_user.id, limit=10)
    if not items:
        await message.answer("Операций пока нет. Нажми «➖ Добавить расход» или «➕ Добавить доход».", reply_markup=MENU_KB)
        return
    items = list(reversed(items))
    today = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    lines = ["📋 Последние 10 операций (старые → новые):"]
    current_day = None
    for op in items:
        day = safe_date_str(op.get("occurred_at", ""))
        if day != current_day:
            current_day = day
            lines.append("\n📅 Сегодня" if day == today else "\n📅 Вчера" if day == yesterday else f"\n📅 {day}")
        emoji = op_emoji(op.get("type", ""))
        t_ru = ru_type(op.get("type", ""))
        amount = fmt_money(op.get("amount"))
        cat = op.get("category") or "—"
        comment = (op.get("comment") or "").strip()
        line = f"{emoji} #{op['id']} {t_ru} {amount} ₽ • {cat}"
        if comment:
            line += f" • {comment}"
        lines.append(line)
    await message.answer("\n".join(lines), reply_markup=MENU_KB)


@dp.message(F.text.in_({"📊 Статистика за месяц", "📊 Статистика"}))
async def btn_month_stats(message: Message):
    """Обрабатывает пользовательский сценарий «month stats»."""
    try:
        today = date.today()
        text = await build_month_stats_text(message.from_user.id, today.year, today.month)
        await message.answer(text, reply_markup=MENU_KB)
    except Exception:
        await message.answer("Не получилось посчитать статистику. Попробуй чуть позже.", reply_markup=MENU_KB)


# ----------------------------
# Лимиты и бюджеты
# ----------------------------
@dp.message(F.text.in_({"💸 Лимиты и бюджеты", "💸 Лимиты"}))
async def btn_budget(message: Message, state: FSMContext):
    """Обрабатывает пользовательский сценарий «budget»."""
    await state.clear()
    await message.answer("Выбери действие по лимитам:", reply_markup=budget_menu_kb())


@dp.callback_query(F.data == "budget:view")
async def cb_budget_view(callback: CallbackQuery):
    """Выполняет действие «cb budget view» в рамках логики Finance Helper."""
    text = await build_limit_overview_text(callback.from_user.id)
    await callback.message.answer(text, reply_markup=MENU_KB)
    await callback.answer()


@dp.callback_query(F.data.in_({"budget:daily", "budget:monthly"}))
async def cb_budget_simple(callback: CallbackQuery, state: FSMContext):
    """Выполняет действие «cb budget simple» в рамках логики Finance Helper."""
    period = "daily" if callback.data.endswith("daily") else "monthly"
    await state.clear()
    await state.update_data(limit_scope="user", limit_period=period, category_id=None)
    await state.set_state(BudgetFlow.amount)
    label = "дневной" if period == "daily" else "месячный"
    await callback.message.answer(f"Введи {label} лимит числом, например 2500.", reply_markup=MENU_KB)
    await callback.answer()


@dp.callback_query(F.data == "budget:category")
async def cb_budget_category(callback: CallbackQuery, state: FSMContext):
    """Выполняет действие «cb budget category» в рамках логики Finance Helper."""
    await state.clear()
    await state.update_data(limit_scope="category", limit_period="monthly")
    await callback.message.answer(
        "Выбери категорию расходов для месячного лимита:",
        reply_markup=await categories_kb(callback.from_user.id, "expense", "limitcat", include_keep=False),
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("limitcat:"))
async def cb_budget_category_pick(callback: CallbackQuery, state: FSMContext):
    """Выполняет действие «cb budget category pick» в рамках логики Finance Helper."""
    raw = callback.data.split(":", 1)[1]
    if raw == "fallback":
        await callback.answer("Категории не найдены.", show_alert=True)
        return
    await state.update_data(category_id=int(raw))
    await state.set_state(BudgetFlow.amount)
    await callback.message.answer("Введи месячный лимит для этой категории числом.", reply_markup=MENU_KB)
    await callback.answer()


@dp.message(BudgetFlow.amount)
async def budgetflow_amount(message: Message, state: FSMContext):
    """Выполняет действие «budgetflow amount» в рамках логики Finance Helper."""
    if await try_interrupt_current_flow(message, state):
        return
    txt = (message.text or "").strip().lower()
    if txt in ("отмена", "cancel"):
        await state.clear()
        await message.answer("Ок, отменено ✅", reply_markup=MENU_KB)
        return
    try:
        amount = float((message.text or "").replace(",", "."))
        if amount <= 0:
            raise ValueError
    except Exception:
        await message.answer("Лимит должен быть числом больше 0. Пример: 2500 (или «отмена»)")
        return
    data = await state.get_data()
    if data.get("limit_scope") == "category":
        result = await api.create_budget_limit(
            telegram_id=message.from_user.id,
            scope="category",
            period=data.get("limit_period", "monthly"),
            amount=amount,
            category_id=data.get("category_id"),
        )
        await message.answer(
            f"✅ Лимит по категории сохранён: {fmt_money(result['amount'])} {result['currency']} ({'месяц' if result['period']=='monthly' else 'день'})",
            reply_markup=MENU_KB,
        )
    else:
        period = data.get("limit_period", "daily")
        result = await api.create_budget_limit(
            telegram_id=message.from_user.id,
            scope="user",
            period=period,
            amount=amount,
            user_telegram_id=message.from_user.id,
        )
        if period == "daily":
            await api.set_limit(message.from_user.id, amount)
        await message.answer(
            f"✅ {'Дневной' if period == 'daily' else 'Месячный'} лимит сохранён: {fmt_money(result['amount'])} {result['currency']}",
            reply_markup=MENU_KB,
        )
    await state.clear()


# ----------------------------
# Удаление операции
# ----------------------------
@dp.message(F.text.in_({"🗑 Удалить операцию", "🗑 Удалить"}))
async def btn_delete_any(message: Message):
    """Обрабатывает пользовательский сценарий «delete any»."""
    items = await api.list_operations(message.from_user.id, limit=PICK_LIMIT)
    if not items:
        await message.answer("Удалять нечего — операций пока нет.", reply_markup=MENU_KB)
        return
    await message.answer("Выбери операцию для удаления:", reply_markup=ops_picker_kb("d", items, offset=0))


@dp.callback_query(F.data.startswith("dpg:"))
async def cb_delete_page(callback: CallbackQuery):
    """Выполняет действие «cb delete page» в рамках логики Finance Helper."""
    offset = int(callback.data.split("dpg:", 1)[1])
    items = await api.list_operations_page(callback.from_user.id, limit=PICK_LIMIT, offset=offset)
    if not items:
        await callback.answer("Больше операций нет.")
        return
    await callback.message.edit_text("Выбери операцию для удаления:")
    await callback.message.edit_reply_markup(reply_markup=ops_picker_kb("d", items, offset=offset))
    await callback.answer()


@dp.callback_query(F.data.startswith("d:"))
async def cb_delete_pick(callback: CallbackQuery):
    """Выполняет действие «cb delete pick» в рамках логики Finance Helper."""
    op_id = int(callback.data.split(":", 1)[1])
    await callback.message.edit_text(f"Удалить операцию #{op_id}?")
    await callback.message.edit_reply_markup(reply_markup=confirm_delete_kb(op_id))
    await callback.answer()


@dp.callback_query(F.data.startswith("dy:"))
async def cb_delete_confirm(callback: CallbackQuery):
    """Выполняет действие «cb delete confirm» в рамках логики Finance Helper."""
    op_id = int(callback.data.split(":", 1)[1])
    res = await api.delete_operation(callback.from_user.id, op_id)
    await callback.message.edit_text("✅ Операция удалена." if res.get("deleted") else "Не найдено (возможно уже удалено).")
    await callback.answer()


@dp.callback_query(F.data == "dcancel")
async def cb_delete_cancel(callback: CallbackQuery):
    """Выполняет действие «cb delete cancel» в рамках логики Finance Helper."""
    await callback.message.edit_text("Ок, отменено ✅")
    await callback.answer()


# ----------------------------
# Редактирование операции
# ----------------------------
@dp.message(F.text.in_({"✏️ Изменить операцию", "✏️ Изменить"}))
async def btn_edit_any(message: Message):
    """Обрабатывает пользовательский сценарий «edit any»."""
    items = await api.list_operations(message.from_user.id, limit=PICK_LIMIT)
    if not items:
        await message.answer("Изменять нечего — операций пока нет.", reply_markup=MENU_KB)
        return
    await message.answer("Выбери операцию для изменения:", reply_markup=ops_picker_kb("e", items, offset=0))


@dp.callback_query(F.data.startswith("epg:"))
async def cb_edit_page(callback: CallbackQuery):
    """Выполняет действие «cb edit page» в рамках логики Finance Helper."""
    offset = int(callback.data.split("epg:", 1)[1])
    items = await api.list_operations_page(callback.from_user.id, limit=PICK_LIMIT, offset=offset)
    if not items:
        await callback.answer("Больше операций нет.")
        return
    await callback.message.edit_text("Выбери операцию для изменения:")
    await callback.message.edit_reply_markup(reply_markup=ops_picker_kb("e", items, offset=offset))
    await callback.answer()


@dp.callback_query(F.data.startswith("e:"))
async def cb_edit_pick(callback: CallbackQuery, state: FSMContext):
    """Выполняет действие «cb edit pick» в рамках логики Finance Helper."""
    _, op_id, op_type = callback.data.split(":", 2)
    await state.clear()
    await state.update_data(op_id=int(op_id), op_type=op_type)
    await state.set_state(EditAnyFlow.amount)
    await callback.message.answer(
        f"✏️ Введи новую сумму для операции #{op_id} (например 650).\nЕсли передумала — напиши «отмена».",
        reply_markup=MENU_KB,
    )
    await callback.answer()


@dp.message(EditAnyFlow.amount)
async def edit_any_amount(message: Message, state: FSMContext):
    """Выполняет действие «edit any amount» в рамках логики Finance Helper."""
    if await try_interrupt_current_flow(message, state):
        return
    txt = (message.text or "").strip().lower()
    if txt in ("отмена", "cancel"):
        await state.clear()
        await message.answer("Ок, отменено ✅", reply_markup=MENU_KB)
        return
    try:
        amount = float((message.text or "").replace(",", "."))
        if amount <= 0:
            raise ValueError
    except Exception:
        await message.answer("Сумма должна быть числом больше 0. Пример: 650 (или «отмена»)")
        return
    await state.update_data(amount=amount)
    await state.set_state(EditAnyFlow.comment)
    await message.answer(
        "Теперь введи комментарий.\n"
        "• '-' — оставить как есть\n"
        "• '0' — удалить комментарий\n"
        "• любой текст — заменить\n"
        "Можно отменить: «отмена»",
        reply_markup=MENU_KB,
    )


@dp.message(EditAnyFlow.comment)
async def edit_any_comment(message: Message, state: FSMContext):
    """Выполняет действие «edit any comment» в рамках логики Finance Helper."""
    if await try_interrupt_current_flow(message, state):
        return
    txt = (message.text or "").strip()
    low = txt.lower()
    if low in ("отмена", "cancel"):
        await state.clear()
        await message.answer("Ок, отменено ✅", reply_markup=MENU_KB)
        return
    if txt == "-":
        comment_mode = "keep"
        comment_value = None
    elif txt == "0":
        comment_mode = "clear"
        comment_value = None
    else:
        comment_mode = "set"
        comment_value = txt
    await state.update_data(comment_mode=comment_mode, comment_value=comment_value)
    data = await state.get_data()
    await state.set_state(EditAnyFlow.date)
    await message.answer(
        "Теперь выбери новую категорию или оставь как есть:",
        reply_markup=await categories_kb(message.from_user.id, data["op_type"], "editcat", include_keep=True),
    )


@dp.callback_query(F.data.startswith("editcat:"))
async def cb_edit_category(callback: CallbackQuery, state: FSMContext):
    """Выполняет действие «cb edit category» в рамках логики Finance Helper."""
    raw = callback.data.split(":", 1)[1]
    if raw == "keep":
        category_mode = "keep"
        category_name = None
    elif raw == "fallback":
        category_mode = "set"
        category_name = "Другое"
    else:
        category_mode = "set"
        category_name = await _category_name_by_id(callback.from_user.id, int(raw)) or "Другое"
    await state.update_data(category_mode=category_mode, category_name=category_name)
    await callback.message.answer(
        "Последний шаг — дата операции.\n"
        "• '-' — оставить как есть\n"
        + quick_date_help(),
        reply_markup=MENU_KB,
    )
    await callback.answer()


@dp.message(EditAnyFlow.date)
async def edit_any_date(message: Message, state: FSMContext):
    """Выполняет действие «edit any date» в рамках логики Finance Helper."""
    if await try_interrupt_current_flow(message, state):
        return
    raw = (message.text or "").strip()
    low = raw.lower()
    if low in ("отмена", "cancel"):
        await state.clear()
        await message.answer("Ок, отменено ✅", reply_markup=MENU_KB)
        return
    data = await state.get_data()
    payload: dict[str, object] = {"amount": float(data["amount"])}

    comment_mode = data.get("comment_mode")
    if comment_mode == "clear":
        payload["comment"] = None
    elif comment_mode == "set":
        payload["comment"] = data.get("comment_value")

    category_mode = data.get("category_mode")
    if category_mode == "set":
        payload["category"] = data.get("category_name")

    if raw not in ("-", ""):
        parsed_date = parse_user_date(raw, today=date.today())
        if parsed_date is None:
            await message.answer("Не удалось распознать дату.\n• '-' — оставить как есть\n" + quick_date_help())
            return
        payload["occurred_at"] = parsed_date

    op = await api.edit_operation(message.from_user.id, int(data["op_id"]), **payload)
    await state.clear()
    await message.answer(
        f"✅ Обновлено: {op_emoji(op.get('type',''))} #{op['id']} {ru_type(op.get('type',''))} {fmt_money(op['amount'])} ₽ • {op.get('category') or '—'} • {op['occurred_at']}",
        reply_markup=MENU_KB,
    )


# ----------------------------
# Команды
# ----------------------------
@dp.message(Command("add"))
async def cmd_add(message: Message):
    """Обрабатывает пользовательский сценарий «add»."""
    parsed = parse_add_command(message.text or "")
    if not parsed:
        await message.answer("Формат: /add <сумма> <расход|доход> <категория> [комментарий]", reply_markup=MENU_KB)
        return
    amount, op_type, category, comment = parsed
    res = await api.create_operation(
        telegram_id=message.from_user.id,
        op_type=op_type,
        amount=amount,
        category=category,
        comment=comment,
        source="command",
        occurred_at=date.today(),
    )
    op = res["operation"]
    await message.answer(
        f"✅ Добавлено: #{op['id']} {op_emoji(op_type)} {ru_type(op_type)} {fmt_money(amount)} • {category} • {op['occurred_at']}",
        reply_markup=MENU_KB,
    )
    await _send_limit_alerts(message, res)


@dp.message(Command("report"))
async def cmd_report(message: Message):
    """Обрабатывает пользовательский сценарий «report»."""
    parsed = parse_report(message.text or "")
    if not parsed:
        await message.answer("Формат: /report YYYY-MM-DD YYYY-MM-DD", reply_markup=MENU_KB)
        return
    d1, d2 = parsed
    try:
        rep = await api.report_summary(message.from_user.id, d1, d2)
    except Exception:
        await message.answer("Не получилось сделать отчёт. Возможно, сервис аналитики сейчас недоступен.", reply_markup=MENU_KB)
        return
    lines = [
        f"📈 Отчёт {d1} — {d2}",
        f"🟢 Доходы: {fmt_money(rep['income_total'])}",
        f"🔴 Расходы: {fmt_money(rep['expense_total'])}",
        f"Баланс: {fmt_money(rep['balance'])}",
        "",
        "Топ категорий:",
    ]
    if rep.get("top_categories"):
        for i, it in enumerate(rep["top_categories"], 1):
            lines.append(f"{i}) {it['category']}: {fmt_money(it['amount'])}")
    else:
        lines.append("— данных нет")
    await message.answer("\n".join(lines), reply_markup=MENU_KB)


@dp.message(Command("daily"))
async def cmd_daily(message: Message):
    """Обрабатывает пользовательский сценарий «daily»."""
    try:
        res = await api.notify_daily(message.from_user.id)
    except Exception:
        await message.answer("Не получилось сделать дневную сводку. Возможно, сервис аналитики сейчас недоступен.", reply_markup=MENU_KB)
        return
    if isinstance(res, dict) and res.get("sent") is False and "text" in res:
        await message.answer(res["text"], reply_markup=MENU_KB)
    else:
        await message.answer("✅ Сводка отправлена.", reply_markup=MENU_KB)


# ----------------------------
# Экспорт и Mini App
# ----------------------------
@dp.message(F.text == "📤 Экспорт")
async def btn_export(message: Message, state: FSMContext):
    """Обрабатывает пользовательский сценарий «export»."""
    await state.clear()
    await message.answer("Выбери вариант экспорта:", reply_markup=export_menu_kb())


@dp.callback_query(F.data.startswith("export:"))
async def cb_export(callback: CallbackQuery):
    """Выполняет действие «cb export» в рамках логики Finance Helper."""
    _, mode, fmt = callback.data.split(":", 2)
    await callback.answer("Готовлю файл…")
    try:
        await _send_export_document(callback.message, callback.from_user.id, mode, fmt)
    except Exception:
        await callback.message.answer(
            "Не получилось сформировать экспорт. Возможно, сервис экспорта сейчас недоступен. Попробуй ещё раз чуть позже.",
            reply_markup=MENU_KB,
        )


@dp.callback_query(F.data == "nsave")
async def cb_natural_save(callback: CallbackQuery, state: FSMContext):
    """Выполняет действие «cb natural save» в рамках логики Finance Helper."""
    data = await state.get_data()
    payload = data.get("natural_payload")
    if not payload:
        await state.clear()
        await callback.answer("Не нашла данные для сохранения.", show_alert=True)
        return
    res = await api.create_operation(
        telegram_id=callback.from_user.id,
        op_type=payload["op_type"],
        amount=float(payload["amount"]),
        category=payload.get("category"),
        comment=payload.get("comment"),
        source="natural_text",
        occurred_at=payload.get("occurred_at"),
        currency=payload.get("currency") or "RUB",
    )
    op = res["operation"]
    await callback.message.edit_text(
        f"✅ Добавлено: #{op['id']} {op_emoji(op['type'])} {ru_type(op['type'])} {fmt_money(op['amount'])} {op['currency']} • {op.get('category') or '—'} • {op['occurred_at']}"
    )
    limit = res.get("limit")
    if limit and limit.get("limit_exceeded"):
        await callback.message.answer(
            f"⚠️ Превышен лимит!\nСегодня: {fmt_money(limit['day_expenses_total'])} при лимите {fmt_money(limit['daily_limit'])}",
            reply_markup=MENU_KB,
        )
    await _send_limit_alerts(callback.message, res)
    if not res.get('limit_alerts') and not (limit and limit.get('limit_exceeded')):
        await callback.message.answer("Готово 👌", reply_markup=MENU_KB)
    await state.clear()
    await callback.answer()


@dp.callback_query(F.data == "ncancel")
async def cb_natural_cancel(callback: CallbackQuery, state: FSMContext):
    """Выполняет действие «cb natural cancel» в рамках логики Finance Helper."""
    await state.clear()
    await callback.message.edit_text("Ок, отменено ✅")
    await callback.answer()
