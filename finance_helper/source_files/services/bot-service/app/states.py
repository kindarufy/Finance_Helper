"""Наборы состояний FSM для пошаговых сценариев Telegram-бота."""
from aiogram.fsm.state import State, StatesGroup


class AddFlow(StatesGroup):
    """Состояния пошагового добавления операции."""
    amount = State()
    comment = State()
    date = State()


class LimitFlow(StatesGroup):
    """Состояние ввода дневного лимита."""
    value = State()


class BudgetFlow(StatesGroup):
    """Состояние ввода суммы бюджетного лимита."""
    amount = State()


class ReportScheduleFlow(StatesGroup):
    """Состояния настройки дня и времени автоматического отчёта."""
    day = State()
    send_time = State()


class WorkspaceCreateFlow(StatesGroup):
    """Состояния создания нового пространства."""
    name = State()
    currency = State()


class WorkspaceMemberFlow(StatesGroup):
    """Состояние ввода идентификатора участника для приглашения."""
    telegram_id = State()


class EditAnyFlow(StatesGroup):
    """Состояния редактирования выбранной операции."""
    amount = State()
    comment = State()
    date = State()


class NaturalFlow(StatesGroup):
    """Состояние подтверждения операции, распознанной из естественного текста."""
    confirm = State()


class CategoryCreateFlow(StatesGroup):
    """Состояния создания новой категории."""
    name = State()
    emoji = State()


class CategoryAliasFlow(StatesGroup):
    """Состояние добавления ключевого слова для категории."""
    alias = State()


class CategoryRenameFlow(StatesGroup):
    """Состояние ввода нового названия категории."""
    name = State()


class CategoryEmojiFlow(StatesGroup):
    """Состояние ввода emoji для категории."""
    emoji = State()



class StatementImportFlow(StatesGroup):
    """Состояния загрузки и подтверждения банковской выписки."""
    waiting_file = State()
    confirm = State()
