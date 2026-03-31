"""Модуль автоматических тестов проекта Finance Helper."""
# flake8: noqa: E402
# pyright: reportMissingImports=false

from datetime import date
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "services" / "bot-service"))

from app.utils import (
    infer_default_category,
    parse_add_command,
    parse_natural_operation,
    parse_report,
    parse_statement_file,
    parse_user_date,
)


def test_parse_add_command_expense_success():
    """Проверяет сценарий «parse add command expense success»."""
    result = parse_add_command("/add 500 расход Еда обед")
    assert result == (500.0, "expense", "Еда", "обед")


def test_parse_add_command_income_success():
    """Проверяет сценарий «parse add command income success»."""
    result = parse_add_command("/add 30000 доход Зарплата основная")
    assert result == (30000.0, "income", "Зарплата", "основная")


def test_parse_add_command_invalid_amount():
    """Проверяет сценарий «parse add command invalid amount»."""
    result = parse_add_command("/add abc расход Еда")
    assert result is None


def test_parse_add_command_negative_amount():
    """Проверяет сценарий «parse add command negative amount»."""
    result = parse_add_command("/add -100 расход Еда")
    assert result is None


def test_parse_add_command_invalid_type():
    """Проверяет сценарий «parse add command invalid type»."""
    result = parse_add_command("/add 500 перевод Еда")
    assert result is None


def test_parse_report_success():
    """Проверяет сценарий «parse report success»."""
    result = parse_report("/report 2025-12-01 2025-12-31")
    assert result == ("2025-12-01", "2025-12-31")


def test_parse_report_invalid_format():
    """Проверяет сценарий «parse report invalid format»."""
    result = parse_report("/report 2025/12/01 2025/12/31")
    assert result is None


def test_parse_natural_operation_expense_with_relative_date():
    """Проверяет сценарий «parse natural operation expense with relative date»."""
    parsed = parse_natural_operation("1500 такси вчера", today=date(2026, 3, 30))
    assert parsed == {
        "amount": 1500.0,
        "op_type": "expense",
        "currency": "RUB",
        "occurred_at": date(2026, 3, 29),
        "raw_text": "1500 такси вчера",
        "description": "такси",
    }


def test_parse_natural_operation_income_with_plus():
    """Проверяет сценарий «parse natural operation income with plus»."""
    parsed = parse_natural_operation("+30000 зарплата", today=date(2026, 3, 30))
    assert parsed["amount"] == 30000.0
    assert parsed["op_type"] == "income"
    assert parsed["currency"] == "RUB"
    assert parsed["description"] == "зарплата"


def test_parse_natural_operation_with_currency_and_iso_date():
    """Проверяет сценарий «parse natural operation with currency and iso date»."""
    parsed = parse_natural_operation("799 usd iphone 2026-03-28", today=date(2026, 3, 30))
    assert parsed["currency"] == "USD"
    assert parsed["occurred_at"] == date(2026, 3, 28)
    assert parsed["description"] == "iphone"


def test_parse_user_date_today_short_ru_formats():
    """Проверяет сценарий «parse user date today short ru formats»."""
    today = date(2026, 3, 30)
    assert parse_user_date("сегодня", today=today) == date(2026, 3, 30)
    assert parse_user_date("вчера", today=today) == date(2026, 3, 29)
    assert parse_user_date("позавчера", today=today) == date(2026, 3, 28)
    assert parse_user_date("3 дня назад", today=today) == date(2026, 3, 27)
    assert parse_user_date("28.03", today=today) == date(2026, 3, 28)
    assert parse_user_date("28.03.2026", today=today) == date(2026, 3, 28)


def test_parse_user_date_invalid_returns_none():
    """Проверяет сценарий «parse user date invalid returns none»."""
    assert parse_user_date("32.03.2026", today=date(2026, 3, 30)) is None
    assert parse_user_date("не дата", today=date(2026, 3, 30)) is None


def test_infer_default_category():
    """Проверяет сценарий «infer default category»."""
    assert infer_default_category("пицца и кофе", "expense") == "Еда"
    assert infer_default_category("зарплата за март", "income") == "Зарплата"



def test_parse_statement_file_csv():
    """Проверяет сценарий «parse statement file csv»."""
    csv_data = (
        "date;debit;credit;currency;description\n"
        "2026-03-28;1500;;RUB;Taxi\n"
        "2026-03-29;;30000;RUB;Salary\n"
    ).encode("utf-8")
    rows, summary = parse_statement_file("statement.csv", csv_data)
    assert len(rows) == 2
    assert rows[0]["type"] == "expense"
    assert rows[1]["type"] == "income"
    assert summary["expenses"] == 1
    assert summary["incomes"] == 1


def test_parse_natural_operation_with_short_ru_date():
    """Проверяет сценарий «parse natural operation with short ru date»."""
    parsed = parse_natural_operation("900 кино 28.03", today=date(2026, 3, 30))
    assert parsed["occurred_at"] == date(2026, 3, 28)
    assert parsed["description"] == "кино"


def test_parse_statement_file_xlsx(tmp_path):
    """Проверяет сценарий «parse statement file xlsx»."""
    openpyxl = pytest.importorskip("openpyxl")
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["date", "amount", "currency", "description"])
    ws.append(["2026-03-28", -990, "RUB", "Coffee"])
    ws.append(["2026-03-29", 12000, "RUB", "Salary"])
    target = tmp_path / "statement.xlsx"
    wb.save(target)
    rows, summary = parse_statement_file(target.name, target.read_bytes())
    assert len(rows) == 2
    assert summary["rows"] == 2
    assert summary["expenses"] == 1
    assert summary["incomes"] == 1



def test_statement_debit_credit_csv(tmp_path):
    """Проверяет сценарий «statement debit credit csv»."""
    csv_data = (
        "date;debit;credit;currency;description\n"
        "2026-03-28;1500;;RUB;Taxi\n"
        "2026-03-29;;30000;RUB;Salary\n"
    ).encode("utf-8")
    rows, summary = parse_statement_file("statement.csv", csv_data)
    assert rows[0]["type"] == "expense"
    assert rows[1]["type"] == "income"
    assert summary["rows"] == 2
