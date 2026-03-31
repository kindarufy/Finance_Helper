"""Модуль сервисного слоя Telegram-бота Finance Helper."""
import asyncio

from aiogram import Bot, F
from aiogram.fsm.context import FSMContext
from aiogram.types import BotCommand, Message

from . import ux
from .bot import dp
from .config import settings
from .helpers import _create_from_natural
from .keyboards import MENU_KB

from . import handlers_common  # noqa: F401
from . import handlers_categories  # noqa: F401
from . import handlers_operations  # noqa: F401
from . import handlers_reports  # noqa: F401
from . import handlers_workspaces  # noqa: F401
from . import handlers_receipts  # noqa: F401


@dp.message(F.text)
async def fallback(message: Message, state: FSMContext):
    """Выполняет действие «fallback» в рамках логики Finance Helper."""
    current_state = await state.get_state()
    if current_state is None:
        handled = await _create_from_natural(message, state, message.text or "")
        if handled:
            return
    await message.answer(ux.unknown_input_text(message.text), reply_markup=MENU_KB)


async def main():
    """Запускает основной рабочий сценарий модуля."""
    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN пустой. Заполни его в .env")
    bot = Bot(token=settings.bot_token)
    await bot.set_my_commands(
        [BotCommand(command=item["command"], description=item["description"]) for item in ux.BOT_COMMANDS]
    )
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
