"""Модуль сервисного слоя Telegram-бота Finance Helper."""
from datetime import date

from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from . import api
from .bot import dp
from .helpers import build_monthly_report_text, build_workspace_overview_text
from .keyboards import MENU_KB, workspace_manage_members_kb, workspace_member_actions_kb, workspace_menu_kb, workspace_role_kb, workspace_switch_kb
from .states import WorkspaceCreateFlow, WorkspaceMemberFlow
from .navigation import try_interrupt_current_flow


@dp.message(F.text.in_({"👨‍👩‍👧‍👦 Совместные бюджеты", "👨‍👩‍👧‍👦 Общие бюджеты"}))
async def btn_workspaces(message: Message, state: FSMContext):
    """Обрабатывает пользовательский сценарий «workspaces»."""
    await state.clear()
    overview = await build_workspace_overview_text(message.from_user.id)
    await message.answer(overview, reply_markup=workspace_menu_kb())


@dp.callback_query(F.data == "ws:menu")
async def cb_ws_menu(callback: CallbackQuery, state: FSMContext):
    """Выполняет действие «cb ws menu» в рамках логики Finance Helper."""
    await state.clear()
    overview = await build_workspace_overview_text(callback.from_user.id)
    await callback.message.edit_text(overview)
    await callback.message.edit_reply_markup(reply_markup=workspace_menu_kb())
    await callback.answer()


@dp.callback_query(F.data == "ws:list")
async def cb_ws_list(callback: CallbackQuery):
    """Выполняет действие «cb ws list» в рамках логики Finance Helper."""
    items = await api.list_workspaces(callback.from_user.id)
    await callback.message.edit_text("Выбери активное пространство:")
    await callback.message.edit_reply_markup(reply_markup=workspace_switch_kb(items))
    await callback.answer()


@dp.callback_query(F.data.startswith("ws:switch:"))
async def cb_ws_switch(callback: CallbackQuery):
    """Выполняет действие «cb ws switch» в рамках логики Finance Helper."""
    workspace_id = int(callback.data.rsplit(":", 1)[1])
    item = await api.set_active_workspace(callback.from_user.id, workspace_id)
    await callback.message.answer(
        f"✅ Активное пространство переключено на: {item['name']} ({item['type']})",
        reply_markup=MENU_KB,
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("ws:create:"))
async def cb_ws_create(callback: CallbackQuery, state: FSMContext):
    """Выполняет действие «cb ws create» в рамках логики Finance Helper."""
    workspace_type = callback.data.rsplit(":", 1)[1]
    await state.clear()
    await state.set_state(WorkspaceCreateFlow.name)
    await state.update_data(workspace_type=workspace_type)
    await callback.message.answer("Введи название нового бюджетного пространства.")
    await callback.answer()


@dp.message(WorkspaceCreateFlow.name)
async def ws_create_name(message: Message, state: FSMContext):
    """Выполняет действие «ws create name» в рамках логики Finance Helper."""
    if await try_interrupt_current_flow(message, state):
        return
    name = (message.text or "").strip()
    if not name:
        await message.answer("Название не должно быть пустым.")
        return
    await state.update_data(workspace_name=name)
    await state.set_state(WorkspaceCreateFlow.currency)
    await message.answer("Теперь введи базовую валюту, например RUB, USD, EUR.")


@dp.message(WorkspaceCreateFlow.currency)
async def ws_create_currency(message: Message, state: FSMContext):
    """Выполняет действие «ws create currency» в рамках логики Finance Helper."""
    if await try_interrupt_current_flow(message, state):
        return
    currency = (message.text or "").strip().upper()
    if not currency or len(currency) < 3 or len(currency) > 8:
        await message.answer("Валюта должна быть кодом вроде RUB, USD или EUR.")
        return
    data = await state.get_data()
    try:
        ws = await api.create_workspace(
            telegram_id=message.from_user.id,
            name=data["workspace_name"],
            workspace_type=data["workspace_type"],
            base_currency=currency,
        )
        await api.set_active_workspace(message.from_user.id, int(ws["id"]))
    except Exception as exc:
        await message.answer(f"Не получилось создать пространство: {exc}", reply_markup=MENU_KB)
        await state.clear()
        return
    await message.answer(
        f"✅ Пространство создано и выбрано активным: {ws['name']} ({ws['type']})",
        reply_markup=MENU_KB,
    )
    await state.clear()


@dp.callback_query(F.data == "ws:members")
async def cb_ws_members(callback: CallbackQuery):
    """Выполняет действие «cb ws members» в рамках логики Finance Helper."""
    active = await api.get_active_workspace(callback.from_user.id)
    items = await api.list_workspace_members(callback.from_user.id, int(active["id"]))
    lines = [f"👥 Участники пространства «{active['name']}»:"]
    for item in items:
        username = f"@{item['username']}" if item.get("username") else str(item["telegram_id"])
        lines.append(f"• {username} — {item['role']}")
    await callback.message.answer("\n".join(lines), reply_markup=MENU_KB)
    await callback.answer()


@dp.callback_query(F.data == "ws:add_member")
async def cb_ws_add_member(callback: CallbackQuery, state: FSMContext):
    """Выполняет действие «cb ws add member» в рамках логики Finance Helper."""
    active = await api.get_active_workspace(callback.from_user.id)
    if active.get("my_role") != "owner":
        await callback.answer("Добавлять участников может только владелец пространства.", show_alert=True)
        return
    await state.clear()
    await state.set_state(WorkspaceMemberFlow.telegram_id)
    await state.update_data(active_workspace_id=int(active["id"]))
    await callback.message.answer(
    "Введи @username или числовой Telegram ID участника, которого нужно добавить в активное пространство."
)
    await callback.answer()


@dp.message(WorkspaceMemberFlow.telegram_id)
async def ws_member_tg(message: Message, state: FSMContext):
    """Выполняет действие «ws member tg» в рамках логики Finance Helper."""
    if await try_interrupt_current_flow(message, state):
        return
    txt = (message.text or "").strip()

    if not txt:
        await message.answer(
            "Введи @username или числовой Telegram ID. Например: @nikol_user или 123456789"
        )
        return

    await state.update_data(member_identifier=txt)
    await message.answer("Выбери роль для участника:", reply_markup=workspace_role_kb())


@dp.callback_query(F.data.startswith("ws:role:"))
async def cb_ws_member_role(callback: CallbackQuery, state: FSMContext):
    """Выполняет действие «cb ws member role» в рамках логики Finance Helper."""
    role = callback.data.rsplit(":", 1)[1]
    data = await state.get_data()
    try:
        await api.add_workspace_member(
            telegram_id=callback.from_user.id,
            workspace_id=int(data["active_workspace_id"]),
            member_identifier=data["member_identifier"],
            role=role,
        )
    except Exception as exc:
        text = str(exc)
        if "member_user_not_found" in text or "404" in text:
            await callback.message.answer(
                "Не нашёл этого пользователя среди тех, кто уже запускал бота. "
                "Попроси его сначала открыть бота и нажать /start, потом я смогу добавить его.",
                reply_markup=MENU_KB,
            )
        else:
            await callback.message.answer(
                "Не получилось добавить участника. Проверь @username или Telegram ID и попробуй ещё раз.",
                reply_markup=MENU_KB,
            )
        await state.clear()
        await callback.answer()
        return


@dp.callback_query(F.data == "ws:stats")
async def cb_ws_stats(callback: CallbackQuery):
    """Выполняет действие «cb ws stats» в рамках логики Finance Helper."""
    active = await api.get_active_workspace(callback.from_user.id)
    today = date.today()
    report_text = await build_monthly_report_text(callback.from_user.id, today.year, today.month)
    header = f"📊 Активное пространство: {active['name']} ({active['type']})\n\n"
    await callback.message.answer(header + report_text, reply_markup=MENU_KB)
    await callback.answer()


@dp.callback_query(F.data == "ws:manage_members")
async def cb_ws_manage_members(callback: CallbackQuery):
    """Выполняет действие «cb ws manage members» в рамках логики Finance Helper."""
    active = await api.get_active_workspace(callback.from_user.id)
    if active.get("my_role") != "owner":
        await callback.answer("Управление участниками доступно только владельцу пространства.", show_alert=True)
        return
    items = await api.list_workspace_members(callback.from_user.id, int(active["id"]))
    await callback.message.edit_text(f"⚙️ Управление участниками: {active['name']}")
    await callback.message.edit_reply_markup(reply_markup=workspace_manage_members_kb(int(active["id"]), items, owner_tg=callback.from_user.id))
    await callback.answer()


@dp.callback_query(F.data.startswith("wsm:"))
async def cb_ws_manage_member(callback: CallbackQuery):
    """Выполняет действие «cb ws manage member» в рамках логики Finance Helper."""
    _, workspace_id, member_tg = callback.data.split(":")
    items = await api.list_workspace_members(callback.from_user.id, int(workspace_id))
    member = next((item for item in items if int(item["telegram_id"]) == int(member_tg)), None)
    if not member:
        await callback.answer("Участник не найден", show_alert=True)
        return
    name = f"@{member['username']}" if member.get("username") else member_tg
    await callback.message.edit_text(f"Участник: {name}\nТекущая роль: {member['role']}")
    await callback.message.edit_reply_markup(reply_markup=workspace_member_actions_kb(int(workspace_id), int(member_tg)))
    await callback.answer()


@dp.callback_query(F.data.startswith("wsmr:"))
async def cb_ws_member_role_change(callback: CallbackQuery):
    """Выполняет действие «cb ws member role change» в рамках логики Finance Helper."""
    _, workspace_id, member_tg, role = callback.data.split(":")
    await api.update_workspace_member_role(callback.from_user.id, int(workspace_id), int(member_tg), role)
    await callback.message.answer(f"✅ Роль участника обновлена: {role}", reply_markup=MENU_KB)
    await callback.answer()


@dp.callback_query(F.data.startswith("wsmx:"))
async def cb_ws_member_remove(callback: CallbackQuery):
    """Выполняет действие «cb ws member remove» в рамках логики Finance Helper."""
    _, workspace_id, member_tg = callback.data.split(":")
    await api.remove_workspace_member(callback.from_user.id, int(workspace_id), int(member_tg))
    await callback.message.answer("✅ Участник удалён из пространства.", reply_markup=MENU_KB)
    await callback.answer()
