"""Навигация и безопасное прерывание активных FSM-сценариев Telegram-бота."""
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from .handlers_common import btn_commands, cmd_examples, cmd_help, cmd_open, cmd_start
from .keyboards import MENU_KB

MENU_TEXTS = {
    "🧠 Примеры",
    "🧠 Примеры ввода",
    "📱 Mini App",
    "➖ Расход",
    "➖ Добавить расход",
    "➕ Доход",
    "➕ Добавить доход",
    "📋 Последние операции",
    "📋 Последние 10 операций",
    "📊 Статистика",
    "📊 Статистика за месяц",
    "✏️ Изменить",
    "✏️ Изменить операцию",
    "🗑 Удалить",
    "🗑 Удалить операцию",
    "💸 Лимиты",
    "💸 Лимиты и бюджеты",
    "🗂 Категории",
    "🗓 Отчёты",
    "👨‍👩‍👧‍👦 Общие бюджеты",
    "👨‍👩‍👧‍👦 Совместные бюджеты",
    "📤 Экспорт",
    "🏦 Импорт",
    "❓ Помощь",
    "📌 Команды",
    "📌 Список команд",
}

CANCEL_TEXTS = {
    "отмена",
    "cancel",
    "назад",
    "back",
    "❌ отмена",
    "⬅️ назад",
}


async def try_interrupt_current_flow(message: Message, state: FSMContext) -> bool:
    """Прерывает текущий FSM-сценарий и переводит пользователя в выбранный раздел меню."""
    text = (message.text or "").strip()
    low = text.lower()

    if not text:
        return False

    current_state = await state.get_state()
    if current_state is None:
        return False

    if low in CANCEL_TEXTS:
        await state.clear()
        await message.answer("Текущее действие отменено.", reply_markup=MENU_KB)
        return True

    if text not in MENU_TEXTS and text not in {"/start", "/help", "/examples", "/open"}:
        return False

    await state.clear()

    from . import (
        handlers_categories,
        handlers_operations,
        handlers_receipts,
        handlers_reports,
        handlers_workspaces,
    )

    if text == "/start":
        await cmd_start(message)
        return True
    if text in {"❓ Помощь", "/help"}:
        await cmd_help(message)
        return True
    if text in {"🧠 Примеры", "🧠 Примеры ввода", "/examples"}:
        await cmd_examples(message)
        return True
    if text in {"📱 Mini App", "/open"}:
        await cmd_open(message)
        return True
    if text in {"📌 Команды", "📌 Список команд"}:
        await btn_commands(message)
        return True
    if text in {"➖ Расход", "➖ Добавить расход"}:
        await handlers_operations.btn_add_expense(message, state)
        return True
    if text in {"➕ Доход", "➕ Добавить доход"}:
        await handlers_operations.btn_add_income(message, state)
        return True
    if text in {"📋 Последние операции", "📋 Последние 10 операций"}:
        await handlers_operations.btn_last10(message)
        return True
    if text in {"📊 Статистика", "📊 Статистика за месяц"}:
        await handlers_operations.btn_month_stats(message)
        return True
    if text in {"✏️ Изменить", "✏️ Изменить операцию"}:
        await handlers_operations.btn_edit_any(message)
        return True
    if text in {"🗑 Удалить", "🗑 Удалить операцию"}:
        await handlers_operations.btn_delete_any(message)
        return True
    if text in {"💸 Лимиты", "💸 Лимиты и бюджеты"}:
        await handlers_operations.btn_budget(message, state)
        return True
    if text == "🗂 Категории":
        await handlers_categories.btn_categories(message, state)
        return True
    if text == "🗓 Отчёты":
        await handlers_reports.btn_reports(message, state)
        return True
    if text in {"👨‍👩‍👧‍👦 Общие бюджеты", "👨‍👩‍👧‍👦 Совместные бюджеты"}:
        await handlers_workspaces.btn_workspaces(message, state)
        return True
    if text == "📤 Экспорт":
        await handlers_operations.btn_export(message, state)
        return True
    if text == "🏦 Импорт":
        await handlers_receipts.menu_statement_import(message, state)
        return True

    return False
