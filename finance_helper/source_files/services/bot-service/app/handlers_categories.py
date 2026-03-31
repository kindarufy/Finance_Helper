"""Модуль сервисного слоя Telegram-бота Finance Helper."""
from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton, InlineKeyboardMarkup

from . import api
from .bot import dp
from .helpers import (
    _list_categories_safe,
    _render_categories_text,
    _category_name_by_id,
    categories_kb,
    category_action_type_kb,
    category_manage_menu_kb,
)
from .keyboards import MENU_KB
from .states import CategoryAliasFlow, CategoryCreateFlow, CategoryEmojiFlow, CategoryRenameFlow
from .navigation import try_interrupt_current_flow


@dp.message(F.text == "🗂 Категории")
async def btn_categories(message: Message, state: FSMContext):
    """Обрабатывает пользовательский сценарий «categories»."""
    await state.clear()
    await message.answer(
        "🗂 Управление категориями\n\nВыбери действие ниже 👇",
        reply_markup=await category_manage_menu_kb(),
    )


@dp.callback_query(F.data == "catmenu:root")
async def cb_categories_root(callback: CallbackQuery, state: FSMContext):
    """Выполняет действие «cb categories root» в рамках логики Finance Helper."""
    await state.clear()
    await callback.message.edit_text("Управление категориями:")
    await callback.message.edit_reply_markup(reply_markup=await category_manage_menu_kb())
    await callback.answer()


@dp.callback_query(F.data.startswith("catmenu:view:"))
async def cb_categories_view(callback: CallbackQuery):
    """Выполняет действие «cb categories view» в рамках логики Finance Helper."""
    op_type = callback.data.rsplit(":", 1)[1]
    text = await _render_categories_text(callback.from_user.id, op_type)
    await callback.message.edit_text(text)
    await callback.message.edit_reply_markup(reply_markup=await category_manage_menu_kb())
    await callback.answer()


@dp.callback_query(F.data == "catmenu:create")
async def cb_category_create(callback: CallbackQuery):
    """Выполняет действие «cb category create» в рамках логики Finance Helper."""
    await callback.message.edit_text("Какой тип категории создаём?")
    await callback.message.edit_reply_markup(reply_markup=await category_action_type_kb("create"))
    await callback.answer()


@dp.callback_query(F.data.startswith("cattype:create:"))
async def cb_category_create_type(callback: CallbackQuery, state: FSMContext):
    """Выполняет действие «cb category create type» в рамках логики Finance Helper."""
    op_type = callback.data.rsplit(":", 1)[1]
    await state.clear()
    await state.set_state(CategoryCreateFlow.name)
    await state.update_data(category_type=op_type)
    await callback.message.answer("Введи название новой категории.")
    await callback.answer()


@dp.message(CategoryCreateFlow.name)
async def category_create_name(message: Message, state: FSMContext):
    """Выполняет действие «category create name» в рамках логики Finance Helper."""
    if await try_interrupt_current_flow(message, state):
        return
    name = (message.text or "").strip()
    if not name:
        await message.answer("Название не должно быть пустым.")
        return
    await state.update_data(category_name=name)
    await state.set_state(CategoryCreateFlow.emoji)
    await message.answer("Теперь отправь emoji для категории или '-' без emoji.")


@dp.message(CategoryCreateFlow.emoji)
async def category_create_emoji(message: Message, state: FSMContext):
    """Выполняет действие «category create emoji» в рамках логики Finance Helper."""
    if await try_interrupt_current_flow(message, state):
        return
    data = await state.get_data()
    emoji = (message.text or "").strip()
    if emoji == "-":
        emoji = None
    try:
        cat = await api.create_category(
            telegram_id=message.from_user.id,
            name=data["category_name"],
            category_type=data["category_type"],
            emoji=emoji,
        )
    except Exception as exc:
        await message.answer(f"Не получилось создать категорию: {exc}", reply_markup=MENU_KB)
        await state.clear()
        return
    await message.answer(f"✅ Категория создана: {cat.get('emoji') or '🏷'} {cat['name']}", reply_markup=MENU_KB)
    await state.clear()


@dp.callback_query(F.data == "catmenu:add_alias")
async def cb_category_add_alias(callback: CallbackQuery):
    """Выполняет действие «cb category add alias» в рамках логики Finance Helper."""
    await callback.message.edit_text("Выбери категорию, для которой нужно добавить ключевое слово:")
    await callback.message.edit_reply_markup(reply_markup=await category_action_type_kb("add_alias"))
    await callback.answer()


@dp.callback_query(F.data.startswith("cattype:add_alias:"))
async def cb_category_add_alias_type(callback: CallbackQuery):
    """Выполняет действие «cb category add alias type» в рамках логики Finance Helper."""
    op_type = callback.data.rsplit(":", 1)[1]
    await callback.message.edit_text("Выбери категорию:")
    await callback.message.edit_reply_markup(reply_markup=await categories_kb(callback.from_user.id, op_type, "aliasaddpick"))
    await callback.answer()


@dp.callback_query(F.data.startswith("aliasaddpick:"))
async def cb_category_add_alias_pick(callback: CallbackQuery, state: FSMContext):
    """Выполняет действие «cb category add alias pick» в рамках логики Finance Helper."""
    raw = callback.data.split(":", 1)[1]
    if raw == "fallback":
        await callback.answer("Сначала создай категорию.", show_alert=True)
        return
    category_id = int(raw)
    category_name = await _category_name_by_id(callback.from_user.id, category_id)
    await state.clear()
    await state.set_state(CategoryAliasFlow.alias)
    await state.update_data(category_id=category_id, category_name=category_name)
    await callback.message.answer(f"Введи ключевое слово для категории «{category_name}». Например: такси, зп, кофе")
    await callback.answer()


@dp.message(CategoryAliasFlow.alias)
async def category_add_alias_text(message: Message, state: FSMContext):
    """Выполняет действие «category add alias text» в рамках логики Finance Helper."""
    if await try_interrupt_current_flow(message, state):
        return
    alias = " ".join((message.text or "").strip().split())
    data = await state.get_data()
    if not alias:
        await message.answer("Ключевое слово не должно быть пустым.")
        return
    try:
        await api.create_alias(message.from_user.id, int(data["category_id"]), alias)
    except Exception as exc:
        await message.answer(f"Не получилось добавить ключевое слово: {exc}", reply_markup=MENU_KB)
        await state.clear()
        return
    await message.answer(f"✅ Добавлено ключевое слово «{alias}» для категории «{data['category_name']}».", reply_markup=MENU_KB)
    await state.clear()


@dp.callback_query(F.data == "catmenu:rename")
async def cb_category_rename(callback: CallbackQuery):
    """Выполняет действие «cb category rename» в рамках логики Finance Helper."""
    await callback.message.edit_text("Выбери тип категории для переименования:")
    await callback.message.edit_reply_markup(reply_markup=await category_action_type_kb("rename"))
    await callback.answer()


@dp.callback_query(F.data.startswith("cattype:rename:"))
async def cb_category_rename_type(callback: CallbackQuery):
    """Выполняет действие «cb category rename type» в рамках логики Finance Helper."""
    op_type = callback.data.rsplit(":", 1)[1]
    await callback.message.edit_text("Выбери категорию:")
    await callback.message.edit_reply_markup(reply_markup=await categories_kb(callback.from_user.id, op_type, "catrenamepick"))
    await callback.answer()


@dp.callback_query(F.data.startswith("catrenamepick:"))
async def cb_category_rename_pick(callback: CallbackQuery, state: FSMContext):
    """Выполняет действие «cb category rename pick» в рамках логики Finance Helper."""
    raw = callback.data.split(":", 1)[1]
    if raw == "fallback":
        await callback.answer("Категории не найдены.", show_alert=True)
        return
    category_id = int(raw)
    category_name = await _category_name_by_id(callback.from_user.id, category_id)
    await state.clear()
    await state.set_state(CategoryRenameFlow.name)
    await state.update_data(category_id=category_id, category_name=category_name)
    await callback.message.answer(f"Введи новое название для категории «{category_name}».")
    await callback.answer()


@dp.message(CategoryRenameFlow.name)
async def category_rename_name(message: Message, state: FSMContext):
    """Выполняет действие «category rename name» в рамках логики Finance Helper."""
    if await try_interrupt_current_flow(message, state):
        return
    name = (message.text or "").strip()
    data = await state.get_data()
    if not name:
        await message.answer("Название не должно быть пустым.")
        return
    try:
        cat = await api.update_category(message.from_user.id, int(data["category_id"]), name=name)
    except Exception as exc:
        await message.answer(f"Не получилось переименовать категорию: {exc}", reply_markup=MENU_KB)
        await state.clear()
        return
    await message.answer(f"✅ Категория переименована: {cat.get('emoji') or '🏷'} {cat['name']}", reply_markup=MENU_KB)
    await state.clear()


@dp.callback_query(F.data == "catmenu:emoji")
async def cb_category_emoji(callback: CallbackQuery):
    """Выполняет действие «cb category emoji» в рамках логики Finance Helper."""
    await callback.message.edit_text("Выбери тип категории:")
    await callback.message.edit_reply_markup(reply_markup=await category_action_type_kb("emoji"))
    await callback.answer()


@dp.callback_query(F.data.startswith("cattype:emoji:"))
async def cb_category_emoji_type(callback: CallbackQuery):
    """Выполняет действие «cb category emoji type» в рамках логики Finance Helper."""
    op_type = callback.data.rsplit(":", 1)[1]
    await callback.message.edit_text("Выбери категорию:")
    await callback.message.edit_reply_markup(reply_markup=await categories_kb(callback.from_user.id, op_type, "catemojipick"))
    await callback.answer()


@dp.callback_query(F.data.startswith("catemojipick:"))
async def cb_category_emoji_pick(callback: CallbackQuery, state: FSMContext):
    """Выполняет действие «cb category emoji pick» в рамках логики Finance Helper."""
    raw = callback.data.split(":", 1)[1]
    if raw == "fallback":
        await callback.answer("Категории не найдены.", show_alert=True)
        return
    category_id = int(raw)
    category_name = await _category_name_by_id(callback.from_user.id, category_id)
    await state.clear()
    await state.set_state(CategoryEmojiFlow.emoji)
    await state.update_data(category_id=category_id, category_name=category_name)
    await callback.message.answer(f"Отправь новый emoji для категории «{category_name}» или '-' чтобы убрать emoji.")
    await callback.answer()


@dp.message(CategoryEmojiFlow.emoji)
async def category_emoji_value(message: Message, state: FSMContext):
    """Выполняет действие «category emoji value» в рамках логики Finance Helper."""
    if await try_interrupt_current_flow(message, state):
        return
    emoji = (message.text or "").strip()
    data = await state.get_data()
    if emoji == "-":
        emoji = ""
    try:
        cat = await api.update_category(message.from_user.id, int(data["category_id"]), emoji=emoji)
    except Exception as exc:
        await message.answer(f"Не получилось обновить emoji: {exc}", reply_markup=MENU_KB)
        await state.clear()
        return
    shown = cat.get("emoji") or "🏷"
    await message.answer(f"✅ Обновлено: {shown} {cat['name']}", reply_markup=MENU_KB)
    await state.clear()


@dp.callback_query(F.data == "catmenu:archive")
async def cb_category_archive(callback: CallbackQuery):
    """Выполняет действие «cb category archive» в рамках логики Finance Helper."""
    await callback.message.edit_text("Выбери тип категории для архивирования:")
    await callback.message.edit_reply_markup(reply_markup=await category_action_type_kb("archive"))
    await callback.answer()


@dp.callback_query(F.data.startswith("cattype:archive:"))
async def cb_category_archive_type(callback: CallbackQuery):
    """Выполняет действие «cb category archive type» в рамках логики Finance Helper."""
    op_type = callback.data.rsplit(":", 1)[1]
    await callback.message.edit_text("Выбери категорию для архивирования:")
    await callback.message.edit_reply_markup(reply_markup=await categories_kb(callback.from_user.id, op_type, "catarchivepick"))
    await callback.answer()


@dp.callback_query(F.data.startswith("catarchivepick:"))
async def cb_category_archive_pick(callback: CallbackQuery):
    """Выполняет действие «cb category archive pick» в рамках логики Finance Helper."""
    raw = callback.data.split(":", 1)[1]
    if raw == "fallback":
        await callback.answer("Категории не найдены.", show_alert=True)
        return
    category_id = int(raw)
    name = await _category_name_by_id(callback.from_user.id, category_id)
    try:
        await api.update_category(callback.from_user.id, category_id, is_archived=True)
    except Exception as exc:
        await callback.message.answer(f"Не получилось архивировать категорию: {exc}", reply_markup=MENU_KB)
        await callback.answer()
        return
    await callback.message.answer(f"✅ Категория «{name}» архивирована.", reply_markup=MENU_KB)
    await callback.answer()


@dp.callback_query(F.data == "catmenu:delete_alias")
async def cb_category_delete_alias(callback: CallbackQuery):
    """Выполняет действие «cb category delete alias» в рамках логики Finance Helper."""
    await callback.message.edit_text("Выбери тип категории:")
    await callback.message.edit_reply_markup(reply_markup=await category_action_type_kb("delete_alias"))
    await callback.answer()


@dp.callback_query(F.data.startswith("cattype:delete_alias:"))
async def cb_category_delete_alias_type(callback: CallbackQuery):
    """Выполняет действие «cb category delete alias type» в рамках логики Finance Helper."""
    op_type = callback.data.rsplit(":", 1)[1]
    await callback.message.edit_text("Выбери категорию:")
    await callback.message.edit_reply_markup(reply_markup=await categories_kb(callback.from_user.id, op_type, "aliasdelpick"))
    await callback.answer()


@dp.callback_query(F.data.startswith("aliasdelpick:"))
async def cb_category_delete_alias_pick(callback: CallbackQuery):
    """Выполняет действие «cb category delete alias pick» в рамках логики Finance Helper."""
    raw = callback.data.split(":", 1)[1]
    if raw == "fallback":
        await callback.answer("Категории не найдены.", show_alert=True)
        return
    category_id = int(raw)
    aliases = await api.list_aliases(callback.from_user.id, category_id)
    if not aliases:
        await callback.message.answer("У этой категории пока нет ключевых слов.", reply_markup=MENU_KB)
        await callback.answer()
        return
    rows = [[InlineKeyboardButton(text=a["alias"], callback_data=f"delalias:{a['id']}")] for a in aliases[:20]]
    await callback.message.edit_text("Выбери ключевое слово для удаления:")
    await callback.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))
    await callback.answer()


@dp.callback_query(F.data.startswith("delalias:"))
async def cb_category_delete_alias_confirm(callback: CallbackQuery):
    """Выполняет действие «cb category delete alias confirm» в рамках логики Finance Helper."""
    alias_id = int(callback.data.split(":", 1)[1])
    try:
        await api.delete_alias(callback.from_user.id, alias_id)
    except Exception as exc:
        await callback.message.answer(f"Не получилось удалить ключевое слово: {exc}", reply_markup=MENU_KB)
        await callback.answer()
        return
    await callback.message.answer("✅ Ключевое слово удалено.", reply_markup=MENU_KB)
    await callback.answer()


