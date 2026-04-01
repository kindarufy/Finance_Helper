"""Обработчики Telegram-бота для просмотра отчётов и настройки автоматической отправки."""
from datetime import date, timedelta

from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from . import api
from .bot import dp
from .common import fmt_money
from .helpers import build_monthly_report_text, build_spending_analysis_text
from .keyboards import MENU_KB, reports_menu_kb
from .states import ReportScheduleFlow
from .navigation import try_interrupt_current_flow


@dp.message(F.text == "🗓 Отчёты")
async def btn_reports(message: Message, state: FSMContext):
    """Открывает раздел отчётов в боте."""
    await state.clear()
    await message.answer("Выбери действие по отчётам:", reply_markup=reports_menu_kb())


@dp.callback_query(F.data == "report:this")
async def cb_report_this(callback: CallbackQuery):
    """Обрабатывает callback для отчёта за текущий месяц."""
    today = date.today()
    text = await build_monthly_report_text(callback.from_user.id, today.year, today.month)
    await callback.message.answer(text, reply_markup=MENU_KB)
    await callback.answer()


@dp.callback_query(F.data == "report:last")
async def cb_report_last(callback: CallbackQuery):
    """Обрабатывает callback для отчёта за прошлый месяц."""
    today = date.today().replace(day=1)
    prev = today - timedelta(days=1)
    text = await build_monthly_report_text(callback.from_user.id, prev.year, prev.month)
    await callback.message.answer(text, reply_markup=MENU_KB)
    await callback.answer()


@dp.callback_query(F.data == "report:analysis")
async def cb_report_analysis(callback: CallbackQuery):
    """Обрабатывает callback для анализа трат."""
    today = date.today()
    text = await build_spending_analysis_text(callback.from_user.id, today.year, today.month)
    await callback.message.answer(text, reply_markup=MENU_KB)
    await callback.answer()


@dp.callback_query(F.data == "report:status")
async def cb_report_status(callback: CallbackQuery):
    """Обрабатывает callback для просмотра статуса автоматических отчётов."""
    items = await api.list_report_schedules(callback.from_user.id)
    if not items:
        await callback.message.answer("Автоотчёт пока не настроен.", reply_markup=MENU_KB)
    else:
        lines = ["🗓 Настройки автоотчётов:"]
        for item in items:
            state = "включён" if item.get("enabled") else "выключен"
            lines.append(f"• {item.get('frequency')} — день {item.get('day_of_month')} в {item.get('send_time')} ({state})")
        await callback.message.answer("\n".join(lines), reply_markup=MENU_KB)
    await callback.answer()


@dp.callback_query(F.data == "report:setup")
async def cb_report_setup(callback: CallbackQuery, state: FSMContext):
    """Обрабатывает callback для настройки автоматического отчёта."""
    await state.clear()
    await state.set_state(ReportScheduleFlow.day)
    await callback.message.answer("Введи день месяца для автоотчёта: от 1 до 28.", reply_markup=MENU_KB)
    await callback.answer()


@dp.message(ReportScheduleFlow.day)
async def reportflow_day(message: Message, state: FSMContext):
    """Обрабатывает ввод пользователя на шаге ввода дня месяца для автосообщения."""
    if await try_interrupt_current_flow(message, state):
        return
    txt = (message.text or "").strip().lower()
    if txt in ("отмена", "cancel"):
        await state.clear()
        await message.answer("Ок, отменено ✅", reply_markup=MENU_KB)
        return
    try:
        day = int(txt)
        if day < 1 or day > 28:
            raise ValueError
    except Exception:
        await message.answer("День должен быть числом от 1 до 28.")
        return
    await state.update_data(day_of_month=day)
    await state.set_state(ReportScheduleFlow.send_time)
    await message.answer("Теперь введи время отправки в формате ЧЧ:ММ, например 09:00.", reply_markup=MENU_KB)


@dp.message(ReportScheduleFlow.send_time)
async def reportflow_send_time(message: Message, state: FSMContext):
    """Обрабатывает ввод пользователя на шаге ввода времени отправки отчёта."""
    if await try_interrupt_current_flow(message, state):
        return
    txt = (message.text or "").strip()
    if txt.lower() in ("отмена", "cancel"):
        await state.clear()
        await message.answer("Ок, отменено ✅", reply_markup=MENU_KB)
        return
    try:
        hour, minute = txt.split(":", 1)
        hour_i = int(hour)
        minute_i = int(minute)
        if hour_i < 0 or hour_i > 23 or minute_i < 0 or minute_i > 59:
            raise ValueError
    except Exception:
        await message.answer("Формат времени: ЧЧ:ММ, например 09:00.")
        return
    data = await state.get_data()
    item = await api.upsert_report_schedule(
        telegram_id=message.from_user.id,
        user_telegram_id=message.from_user.id,
        day_of_month=int(data['day_of_month']),
        send_time=f"{hour_i:02d}:{minute_i:02d}",
        enabled=True,
    )
    await message.answer(
        f"✅ Автоотчёт включён: каждый месяц {item['day_of_month']} числа в {item['send_time']}",
        reply_markup=MENU_KB,
    )
    await state.clear()


@dp.callback_query(F.data == "report:disable")
async def cb_report_disable(callback: CallbackQuery):
    """Обрабатывает callback для отключения автоматического отчёта."""
    items = await api.list_report_schedules(callback.from_user.id)
    monthly = next((item for item in items if item.get('frequency') == 'monthly'), None)
    if monthly is None:
        await callback.message.answer("Автоотчёт ещё не был настроен.", reply_markup=MENU_KB)
    else:
        await api.upsert_report_schedule(
            telegram_id=callback.from_user.id,
            user_telegram_id=callback.from_user.id,
            day_of_month=int(monthly.get('day_of_month') or 1),
            send_time=monthly.get('send_time') or '09:00',
            timezone=monthly.get('timezone') or 'Europe/Moscow',
            enabled=False,
        )
        await callback.message.answer("⛔ Автоотчёт выключен.", reply_markup=MENU_KB)
    await callback.answer()


