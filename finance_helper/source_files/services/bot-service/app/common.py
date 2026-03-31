"""Модуль сервисного слоя Telegram-бота Finance Helper."""
def ru_type(t: str) -> str:
    """Выполняет действие «ru type» в рамках логики Finance Helper."""
    return "расход" if t == "expense" else "доход" if t == "income" else t


def op_emoji(t: str) -> str:
    """Выполняет действие «op emoji» в рамках логики Finance Helper."""
    return "🔴" if t == "expense" else "🟢" if t == "income" else "⚪"


def fmt_money(x) -> str:
    """Выполняет действие «fmt money» в рамках логики Finance Helper."""
    try:
        return f"{float(x):.2f}"
    except Exception:
        return str(x)


def safe_date_str(op_date: str) -> str:
    """Выполняет действие «safe date str» в рамках логики Finance Helper."""
    return (op_date or "")[:10]


def quick_date_help() -> str:
    """Выполняет действие «quick date help» в рамках логики Finance Helper."""
    return (
        "Укажи дату операции:\n"
        "• сегодня\n"
        "• вчера\n"
        "• позавчера\n"
        "• 3 дня назад\n"
        "• 2026-03-28\n"
        "• 28.03 или 28.03.2026\n\n"
        "Для сегодняшней даты отправь '-'"
    )


PICK_LIMIT = 10
