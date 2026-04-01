"""Тесты для расчётов сервиса аналитики: сводка, месячный отчёт, анализ трат и данные дашборда."""
# flake8: noqa: E402
# pyright: reportMissingImports=false

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "services" / "analytics-service"))

from app.reports import dashboard_payload, monthly_report_payload, render_daily_text, render_monthly_report_text, summary_report, spending_analysis_payload # type: ignore[import-not-found]


def test_summary_report_calculates_totals_and_balance():
    """Проверяет, что сводный отчёт правильно считает доходы, расходы и баланс."""
    operations = [
        {"type": "income", "amount": 1000, "category": "Зарплата"},
        {"type": "expense", "amount": 200, "category": "Еда"},
        {"type": "expense", "amount": 300, "category": "Транспорт"},
    ]

    result = summary_report(operations)

    assert result["income_total"] == 1000.0
    assert result["expense_total"] == 500.0
    assert result["balance"] == 500.0
    assert len(result["top_categories"]) == 2


def test_summary_report_empty_operations():
    """Проверяет сводный отчёт для пустого списка операций."""
    result = summary_report([])

    assert result["income_total"] == 0.0
    assert result["expense_total"] == 0.0
    assert result["balance"] == 0.0
    assert result["top_categories"] == []


def test_render_daily_text_contains_main_fields():
    """Проверяет, что текст дневной сводки содержит ключевые поля."""
    report = {
        "income_total": 1000.0,
        "expense_total": 250.0,
        "balance": 750.0,
        "top_categories": [{"category": "Еда", "amount": 250.0}],
    }

    text = render_daily_text("2025-12-13", report)

    assert "2025-12-13" in text
    assert "Доходы: 1000.0" in text
    assert "Расходы: 250.0" in text
    assert "Баланс: 750.0" in text
    assert "Еда" in text



def test_render_monthly_report_text_contains_key_sections():
    """Проверяет, что текст ежемесячного отчёта содержит основные разделы."""
    current_ops = [
        {"type": "income", "amount": 1000, "category": "Зарплата", "user_telegram_id": 1, "occurred_at": "2026-03-01"},
        {"type": "expense", "amount": 300, "category": "Еда", "user_telegram_id": 1, "occurred_at": "2026-03-02"},
    ]
    previous_ops = [
        {"type": "expense", "amount": 200, "category": "Еда", "user_telegram_id": 1, "occurred_at": "2026-02-02"},
    ]
    payload = monthly_report_payload(current_ops, previous_ops, 2026, 3)
    text = render_monthly_report_text(payload)
    assert "Ежемесячный отчёт" in text
    assert "Топ категорий" in text
    assert "По участникам" in text



def test_spending_analysis_mentions_growth_and_user():
    """Проверяет, что анализ трат упоминает рост расходов и вклад пользователя."""
    current_ops = [
        {"type": "expense", "amount": 900, "category": "Еда", "user_username": "nikol", "user_telegram_id": 1, "occurred_at": "2026-03-02"},
        {"type": "expense", "amount": 1200, "category": "Транспорт", "user_username": "roma", "user_telegram_id": 2, "occurred_at": "2026-03-03"},
        {"type": "income", "amount": 5000, "category": "Зарплата", "user_username": "nikol", "user_telegram_id": 1, "occurred_at": "2026-03-01"},
    ]
    previous_ops = [
        {"type": "expense", "amount": 500, "category": "Еда", "user_username": "nikol", "user_telegram_id": 1, "occurred_at": "2026-02-02"},
    ]
    payload = spending_analysis_payload(current_ops, previous_ops)
    assert "AI-анализ трат" in payload["text"]
    assert "Расходы выросли" in payload["text"]
    assert "@roma" in payload["text"] or "@nikol" in payload["text"]


def test_dashboard_payload_builds_timeline_and_recent():
    """Проверяет сборку таймлайна и списка последних операций для дашборда."""
    ops = [
        {"id": 1, "type": "expense", "amount": 300, "category": "Еда", "occurred_at": "2026-03-29", "user_telegram_id": 1},
        {"id": 2, "type": "income", "amount": 1000, "category": "Зарплата", "occurred_at": "2026-03-30", "user_telegram_id": 1},
        {"id": 3, "type": "expense", "amount": 150, "category": "Транспорт", "occurred_at": "2026-03-30", "user_telegram_id": 1},
    ]
    payload = dashboard_payload(ops, days=7)
    assert "summary" in payload
    assert len(payload["timeline"]) == 7
    assert payload["recent_operations"][0]["id"] == 3


def test_spending_analysis_detects_anomalies_and_recurring():
    """Проверяет, что анализ трат находит аномальные и повторяющиеся расходы."""
    current_ops = [
        {"type": "expense", "amount": 3000, "category": "Подписки", "comment": "Spotify", "user_username": "nikol", "user_telegram_id": 1, "occurred_at": "2026-03-02"},
        {"type": "expense", "amount": 15000, "category": "Техника", "comment": "iPhone", "user_username": "nikol", "user_telegram_id": 1, "occurred_at": "2026-03-03"},
        {"type": "expense", "amount": 1200, "category": "Еда", "comment": "Pizza", "user_username": "nikol", "user_telegram_id": 1, "occurred_at": "2026-03-04"},
    ]
    previous_ops = [
        {"type": "expense", "amount": 2900, "category": "Подписки", "comment": "Spotify", "user_username": "nikol", "user_telegram_id": 1, "occurred_at": "2026-02-03"},
        {"type": "expense", "amount": 900, "category": "Еда", "comment": "Pizza", "user_username": "nikol", "user_telegram_id": 1, "occurred_at": "2026-02-04"},
    ]
    payload = spending_analysis_payload(current_ops, previous_ops, year=2026, month=3, limits=[{"label": "Месячный лимит", "percent_used": 82}])
    assert payload["anomalies"]
    assert payload["recurring"]
    assert "Риск по лимитам" in payload["text"]
