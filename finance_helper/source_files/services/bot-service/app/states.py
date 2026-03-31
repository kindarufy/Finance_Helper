"""Модуль сервисного слоя Telegram-бота Finance Helper."""
from aiogram.fsm.state import State, StatesGroup


class AddFlow(StatesGroup):
    """Класс «AddFlow» описывает состояние или структуру данных данного модуля."""
    amount = State()
    comment = State()
    date = State()


class LimitFlow(StatesGroup):
    """Класс «LimitFlow» описывает состояние или структуру данных данного модуля."""
    value = State()


class BudgetFlow(StatesGroup):
    """Класс «BudgetFlow» описывает состояние или структуру данных данного модуля."""
    amount = State()


class ReportScheduleFlow(StatesGroup):
    """Класс «ReportScheduleFlow» описывает состояние или структуру данных данного модуля."""
    day = State()
    send_time = State()


class WorkspaceCreateFlow(StatesGroup):
    """Класс «WorkspaceCreateFlow» описывает состояние или структуру данных данного модуля."""
    name = State()
    currency = State()


class WorkspaceMemberFlow(StatesGroup):
    """Класс «WorkspaceMemberFlow» описывает состояние или структуру данных данного модуля."""
    telegram_id = State()


class EditAnyFlow(StatesGroup):
    """Класс «EditAnyFlow» описывает состояние или структуру данных данного модуля."""
    amount = State()
    comment = State()
    date = State()


class NaturalFlow(StatesGroup):
    """Класс «NaturalFlow» описывает состояние или структуру данных данного модуля."""
    confirm = State()


class CategoryCreateFlow(StatesGroup):
    """Класс «CategoryCreateFlow» описывает состояние или структуру данных данного модуля."""
    name = State()
    emoji = State()


class CategoryAliasFlow(StatesGroup):
    """Класс «CategoryAliasFlow» описывает состояние или структуру данных данного модуля."""
    alias = State()


class CategoryRenameFlow(StatesGroup):
    """Класс «CategoryRenameFlow» описывает состояние или структуру данных данного модуля."""
    name = State()


class CategoryEmojiFlow(StatesGroup):
    """Класс «CategoryEmojiFlow» описывает состояние или структуру данных данного модуля."""
    emoji = State()



class StatementImportFlow(StatesGroup):
    """Класс «StatementImportFlow» описывает состояние или структуру данных данного модуля."""
    waiting_file = State()
    confirm = State()
