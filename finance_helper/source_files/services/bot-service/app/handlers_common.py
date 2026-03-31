"""Общие команды и действия Telegram-бота Finance Helper."""
from aiogram import F
from aiogram.filters import Command
from aiogram.types import Message, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

from . import api, ux
from .bot import dp
from .config import settings
from .keyboards import MENU_KB


@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Обрабатывает пользовательский сценарий «start»."""
    await api.upsert_user(message.from_user.id, message.from_user.username)
    await message.answer(ux.welcome_text(message.from_user.first_name), reply_markup=MENU_KB)
    await message.answer(ux.onboarding_text(), reply_markup=MENU_KB)


@dp.message(Command("help"))
@dp.message(F.text == "❓ Помощь")
async def cmd_help(message: Message):
    """Обрабатывает пользовательский сценарий «help»."""
    await message.answer(ux.help_text(), reply_markup=MENU_KB)


@dp.message(Command("examples"))
@dp.message(F.text.in_({"🧠 Примеры ввода", "🧠 Примеры"}))
async def cmd_examples(message: Message):
    """Обрабатывает пользовательский сценарий «examples»."""
    await message.answer(ux.examples_text(), reply_markup=MENU_KB)


@dp.message(Command("open"))
@dp.message(F.text == "📱 Mini App")
async def cmd_open(message: Message):
    """Обрабатывает пользовательский сценарий «open»."""
    try:
        await api.upsert_user(message.from_user.id, message.from_user.username)

        if not settings.miniapp_public_url:
            await message.answer(
                "MINIAPP_PUBLIC_URL не задан в .env, поэтому Mini App пока нельзя открыть.",
                reply_markup=MENU_KB,
            )
            return

        url = await api.build_miniapp_url(message.from_user.id)

        kb = InlineKeyboardBuilder()
        kb.button(text="Открыть Mini App", web_app=WebAppInfo(url=url))
        kb.adjust(1)

        await message.answer(
            "Открывай Mini App по кнопке ниже 👇",
            reply_markup=kb.as_markup(),
        )
    except Exception as exc:
        await message.answer(
            f"Не получилось подготовить Mini App: {exc}",
            reply_markup=MENU_KB,
        )


@dp.message(F.text.in_({"📌 Список команд", "📌 Команды"}))
async def btn_commands(message: Message):
    """Обрабатывает пользовательский сценарий «commands»."""
    await message.answer(ux.pretty_commands_text(), reply_markup=MENU_KB)
