"""Тесты текстов интерфейса Telegram-бота."""
# flake8: noqa: E402
# pyright: reportMissingImports=false

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / 'services' / 'bot-service'))

from app import ux  # type: ignore[import-not-found]


def test_welcome_text_contains_main_positioning():
    """Проверяет, что приветственный текст содержит основное позиционирование бота."""
    text = ux.welcome_text('Николь')
    assert 'Finance Helper' in text
    assert 'Telegram-бот' in text
    assert 'совместных финансов' in text


def test_onboarding_mentions_key_flows():
    """Проверяет, что онбординг описывает ключевые сценарии работы."""
    text = ux.onboarding_text()
    assert 'Категории' in text
    assert 'Лимиты и бюджеты' in text
    assert 'Mini App' in text


def test_examples_text_contains_income_and_expense_examples():
    """Проверяет, что блок примеров содержит примеры доходов и расходов."""
    text = ux.examples_text()
    assert '700 пицца' in text
    assert '+30000 зарплата' in text
    assert '799 usd iphone 2026-03-28' in text


def test_help_text_lists_core_sections_and_commands():
    """Проверяет, что справка перечисляет основные разделы и команды."""
    text = ux.help_text()
    assert 'CSV/XLSX' in text
    assert 'совместные бюджеты' in text.lower()
    assert '/start' in text
    assert '/open' in text


def test_unknown_input_text_gives_generic_examples():
    """Проверяет, что ответ на непонятный ввод предлагает общие примеры."""
    text = ux.unknown_input_text('абракадабра')
    assert '700 пицца' in text
    assert '❓ Помощь' in text


def test_bot_commands_include_menu_and_examples():
    """Проверяет, что список команд содержит меню и примеры."""
    commands = {item['command'] for item in ux.BOT_COMMANDS}
    assert {'start', 'help', 'examples', 'add', 'report', 'daily', 'open'} <= commands
