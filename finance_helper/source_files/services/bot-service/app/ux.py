"""Модуль сервисного слоя Telegram-бота Finance Helper."""
from __future__ import annotations

from typing import Iterable

BOT_COMMANDS: list[dict[str, str]] = [
    {"command": "start", "description": "Запустить бота и открыть главное меню"},
    {"command": "help", "description": "Справка по возможностям"},
    {"command": "examples", "description": "Примеры ввода операций"},
    {"command": "add", "description": "Добавить операцию командой"},
    {"command": "report", "description": "Отчёт за период"},
    {"command": "daily", "description": "Дневная сводка"},
    {"command": "open", "description": "Открыть Mini App"},
]


def _bullet_lines(items: Iterable[str]) -> str:
    """Выполняет действие «bullet lines» в рамках логики Finance Helper."""
    return "\n".join(f"• {item}" for item in items)


DATE_FORMATS_TEXT = _bullet_lines(
    [
        "Сегодня / вчера / позавчера",
        "3 дня назад",
        "2026-03-28",
        "28.03",
        "28.03.2026",
    ]
)


def welcome_text(first_name: str | None = None) -> str:
    """Выполняет действие «welcome text» в рамках логики Finance Helper."""
    name = (first_name or "").strip()
    greet = f"Привет, {name}!" if name else "Привет!"
    return (
        f"{greet}\n\n"
        "Я Finance Helper — умный Telegram-бот для учёта личных и совместных финансов.\n\n"
        "Я помогаю быстро записывать расходы и доходы, контролировать бюджет, смотреть отчёты, "
        "анализировать траты и держать все финансы под рукой прямо в Telegram."
    )


def onboarding_text() -> str:
    """Выполняет действие «onboarding text» в рамках логики Finance Helper."""
    return (
        "🚀 Быстрый старт\n\n"
        "1. Добавь первую операцию простым сообщением: `700 пицца` или `+30000 зарплата`.\n"
        "2. Если нужно, укажи дату: `1500 такси вчера`.\n"
        "3. Открой «🗂 Категории», чтобы создать свои категории и ключевые слова.\n"
        "4. В разделе «💸 Лимиты и бюджеты» можно настроить дневные и месячные лимиты.\n"
        "5. В разделе «🗓 Отчёты» смотри сводку по финансам и AI-анализ трат.\n"
        "6. Для графиков и наглядной аналитики открой «📱 Mini App».\n\n"
        "Хочешь посмотреть готовые примеры сообщений? Нажми «🧠 Примеры ввода»."
    )


def examples_text() -> str:
    """Выполняет действие «examples text» в рамках логики Finance Helper."""
    expense_examples = _bullet_lines(
        ["700 пицца", "1490 подписка", "2400 продукты вчера", "799 usd iphone 2026-03-28"]
    )
    income_examples = _bullet_lines(
        ["+30000 зарплата", "+5000 подарок", "+120 usd freelance"]
    )
    return (
        "🧠 Примеры ввода\n\n"
        "Расходы:\n"
        f"{expense_examples}\n\n"
        "Доходы:\n"
        f"{income_examples}\n\n"
        "Поддерживаемые форматы даты:\n"
        f"{DATE_FORMATS_TEXT}\n\n"
        "Операции можно добавлять и кнопками, если удобнее вводить всё пошагово."
    )


def help_text() -> str:
    """Выполняет действие «help text» в рамках логики Finance Helper."""
    features = _bullet_lines(
        [
            "Добавлять расходы и доходы текстом и кнопками",
            "Добавлять операции прошедшей датой",
            "Создавать свои категории и ключевые слова",
            "Настраивать лимиты и бюджеты",
            "Смотреть отчёты и AI-анализ трат",
            "Экспортировать данные в CSV и XLSX",
            "Открывать Mini App с графиками",
            "Импортировать банковские выписки CSV/XLSX",
            "Вести совместные бюджеты",
        ]
    )
    commands = _bullet_lines(
        [
            "/start — Запуск бота и главное меню",
            "/help — Справка по возможностям",
            "/examples — Примеры ввода операций",
            "/add — Добавить операцию",
            "/report — Отчёт за период",
            "/daily — Дневная сводка",
            "/open — Открыть Mini App",
        ]
    )
    return (
        "❓ Справка по Finance Helper\n\n"
        "Что я умею:\n"
        f"{features}\n\n"
        "Полезные команды:\n"
        f"{commands}\n\n"
        "Чтобы начать прямо сейчас, просто отправь сообщение вроде: `700 кофе`."
    )


def pretty_commands_text() -> str:
    """Выполняет действие «pretty commands text» в рамках логики Finance Helper."""
    quick_start = _bullet_lines(
        [
            "Написать `700 пицца`",
            "Написать `+30000 зарплата`",
            "Нажать «➖ Добавить расход» или «➕ Добавить доход»",
        ]
    )
    sections = _bullet_lines(
        [
            "🗂 Категории — свои категории и ключевые слова",
            "💸 Лимиты и бюджеты — дневные, месячные и по категориям",
            "🗓 Отчёты — сводка по финансам и AI-анализ",
            "📤 Экспорт — выгрузка в CSV и XLSX",
            "📱 Mini App — графики и дашборд",
            "🏦 Импорт выписки — загрузка CSV/XLSX из банка",
            "👨‍👩‍👧‍👦 Совместные бюджеты — семья, поездка, проект",
        ]
    )
    return (
        "💳 Finance Helper\n"
        "Удобный учёт финансов прямо в Telegram.\n\n"
        "Как можно начать:\n"
        f"{quick_start}\n\n"
        "Главные разделы:\n"
        f"{sections}\n\n"
        "Поддерживаемые форматы даты:\n"
        f"{DATE_FORMATS_TEXT}"
    )


def unknown_input_text(user_text: str | None = None) -> str:
    """Выполняет действие «unknown input text» в рамках логики Finance Helper."""
    text = (user_text or "").strip().lower()
    if any(word in text for word in ["выписк", "банк", "csv", "xlsx"]):
        return (
            "Похоже, речь о банковской выписке.\n\n"
            "Открой «🏦 Импорт выписки» и загрузи CSV или XLSX. Я покажу найденные операции перед импортом."
        )
    if any(word in text for word in ["категор", "alias", "ключев"]):
        return (
            "Похоже, ты хочешь управлять категориями.\n\n"
            "Открой «🗂 Категории»: там можно создать категорию, добавить emoji и ключевые слова для автоподстановки."
        )
    examples = _bullet_lines(["700 пицца", "+30000 зарплата", "1500 такси вчера"])
    return (
        "Я не до конца понял сообщение.\n\n"
        "Попробуй один из вариантов:\n"
        f"{examples}\n\n"
        "Либо открой «❓ Помощь» или воспользуйся кнопками в меню."
    )
