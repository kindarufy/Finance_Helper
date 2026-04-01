"""Небольшие форматирующие функции и текстовые подсказки Telegram-бота."""
def ru_type(t: str) -> str:
    """Преобразует технический тип операции в понятное русское название."""
    return "расход" if t == "expense" else "доход" if t == "income" else t


def op_emoji(t: str) -> str:
    """Возвращает emoji для типа операции."""
    return "🔴" if t == "expense" else "🟢" if t == "income" else "⚪"


def fmt_money(x) -> str:
    """Форматирует сумму в строку с двумя знаками после запятой."""
    try:
        return f"{float(x):.2f}"
    except Exception:
        return str(x)


def safe_date_str(op_date: str) -> str:
    """Безопасно обрезает строку даты до формата YYYY-MM-DD."""
    return (op_date or "")[:10]


def quick_date_help() -> str:
    """Возвращает краткую подсказку по допустимым форматам даты."""
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
