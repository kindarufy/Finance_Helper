"""Модуль сервиса аналитики Finance Helper."""
from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from statistics import median
from typing import Any


def _user_label(op: dict[str, Any]) -> str:
    """Выполняет действие «user label» в рамках логики Finance Helper."""
    username = op.get("user_username")
    if username:
        return f"@{username}"
    tg = op.get("user_telegram_id")
    return str(tg if tg is not None else "unknown")


def _normalized_comment(op: dict[str, Any]) -> str:
    """Выполняет действие «normalized comment» в рамках логики Finance Helper."""
    raw = str(op.get("merchant") or op.get("comment") or "").strip().lower()
    return " ".join(raw.split())


def _month_key(op: dict[str, Any]) -> str:
    """Выполняет действие «month key» в рамках логики Finance Helper."""
    value = str(op.get("occurred_at") or "")
    return value[:7] if len(value) >= 7 else value


def _month_length(year: int, month: int) -> int:
    """Выполняет действие «month length» в рамках логики Finance Helper."""
    start, end = month_bounds(year, month)
    return (end - start).days + 1


def _category_totals(ops: list[dict[str, Any]]) -> dict[str, float]:
    """Выполняет действие «category totals» в рамках логики Finance Helper."""
    result: dict[str, float] = defaultdict(float)
    for op in ops:
        if op.get("type") == "expense":
            result[op.get("category") or "Без категории"] += float(op.get("amount") or 0)
    return dict(result)


def _recurring_candidates(ops: list[dict[str, Any]], previous_ops: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Выполняет действие «recurring candidates» в рамках логики Finance Helper."""
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for op in [*ops, *previous_ops]:
        if op.get("type") != "expense":
            continue
        key = _normalized_comment(op)
        if not key:
            continue
        grouped[key].append(op)
    items: list[dict[str, Any]] = []
    for key, bucket in grouped.items():
        months = {_month_key(op) for op in bucket if _month_key(op)}
        if len(bucket) >= 2 and len(months) >= 2:
            sample = sorted(bucket, key=lambda item: (str(item.get("occurred_at")), float(item.get("amount") or 0)), reverse=True)[0]
            avg = sum(float(item.get("amount") or 0) for item in bucket) / len(bucket)
            items.append(
                {
                    "label": sample.get("merchant") or sample.get("comment") or key,
                    "category": sample.get("category") or "Без категории",
                    "avg_amount": round(avg, 2),
                    "occurrences": len(bucket),
                }
            )
    items.sort(key=lambda item: item["avg_amount"], reverse=True)
    return items[:5]


def _anomalies(expense_ops: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Выполняет действие «anomalies» в рамках логики Finance Helper."""
    if len(expense_ops) < 3:
        return []
    amounts = sorted(float(op.get("amount") or 0) for op in expense_ops)
    med = median(amounts)
    threshold = max(med * 2.2, med + 1000)
    result: list[dict[str, Any]] = []
    for op in sorted(expense_ops, key=lambda item: float(item.get("amount") or 0), reverse=True):
        amount = float(op.get("amount") or 0)
        if amount >= threshold:
            result.append(
                {
                    "amount": round(amount, 2),
                    "category": op.get("category") or "Без категории",
                    "occurred_at": str(op.get("occurred_at") or ""),
                    "label": op.get("merchant") or op.get("comment") or "крупная трата",
                }
            )
        if len(result) >= 3:
            break
    return result


def _forecast_month_end(current_total: float, year: int, month: int, today: date | None = None) -> dict[str, float]:
    """Выполняет действие «forecast month end» в рамках логики Finance Helper."""
    today = today or date.today()
    month_days = _month_length(year, month)
    elapsed = min(max(today.day, 1), month_days)
    projected = round((current_total / elapsed) * month_days, 2) if elapsed else round(current_total, 2)
    return {"elapsed_days": elapsed, "month_days": month_days, "projected_expense": projected}


def summary_report(ops: list[dict[str, Any]]) -> dict[str, Any]:
    """Выполняет действие «summary report» в рамках логики Finance Helper."""
    income = 0.0
    expense = 0.0
    by_cat: dict[str, float] = defaultdict(float)
    by_day: dict[str, float] = defaultdict(float)
    by_user: dict[str, float] = defaultdict(float)

    for op in ops:
        amt = float(op["amount"])
        if op["type"] == "income":
            income += amt
        else:
            expense += amt
            cat = op.get("category") or "Без категории"
            by_cat[cat] += amt
            by_day[str(op.get("occurred_at"))] += amt
            by_user[_user_label(op)] += amt

    top = sorted(by_cat.items(), key=lambda x: x[1], reverse=True)[:7]
    return {
        "income_total": round(income, 2),
        "expense_total": round(expense, 2),
        "balance": round(income - expense, 2),
        "top_categories": [
            {
                "category": c,
                "amount": round(a, 2),
                "share_percent": round((a / expense) * 100, 1) if expense else 0.0,
            }
            for c, a in top
        ],
        "expense_by_day": [{"date": d, "amount": round(a, 2)} for d, a in sorted(by_day.items())],
        "expense_by_user": [
            {
                "user": u,
                "amount": round(a, 2),
                "share_percent": round((a / expense) * 100, 1) if expense else 0.0,
            }
            for u, a in sorted(by_user.items(), key=lambda x: x[1], reverse=True)
        ],
        "operations_count": len(ops),
    }


def render_daily_text(date_str: str, report: dict[str, Any]) -> str:
    """Выполняет действие «render daily text» в рамках логики Finance Helper."""
    lines = [
        f"📊 Сводка за {date_str}",
        f"Доходы: {report['income_total']}",
        f"Расходы: {report['expense_total']}",
        f"Баланс: {report['balance']}",
        "",
        "Топ категорий:",
    ]
    if report["top_categories"]:
        for i, item in enumerate(report["top_categories"], 1):
            lines.append(f"{i}) {item['category']}: {item['amount']}")
    else:
        lines.append("— операций нет")
    return "\n".join(lines)


def month_bounds(year: int, month: int) -> tuple[date, date]:
    """Выполняет действие «month bounds» в рамках логики Finance Helper."""
    first = date(year, month, 1)
    next_first = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    return first, next_first - timedelta(days=1)


def monthly_report_payload(ops: list[dict[str, Any]], previous_ops: list[dict[str, Any]], year: int, month: int) -> dict[str, Any]:
    """Выполняет действие «monthly report payload» в рамках логики Finance Helper."""
    current = summary_report(ops)
    previous = summary_report(previous_ops)
    from_date, to_date = month_bounds(year, month)
    expense_delta = round(current["expense_total"] - previous["expense_total"], 2)
    income_delta = round(current["income_total"] - previous["income_total"], 2)
    days = max((to_date - from_date).days + 1, 1)
    expense_change_pct = round((expense_delta / previous["expense_total"]) * 100, 1) if previous["expense_total"] else None
    income_change_pct = round((income_delta / previous["income_total"]) * 100, 1) if previous["income_total"] else None
    forecast = _forecast_month_end(current["expense_total"], year, month)
    return {
        "year": year,
        "month": month,
        "date_from": from_date.isoformat(),
        "date_to": to_date.isoformat(),
        "income_total": current["income_total"],
        "expense_total": current["expense_total"],
        "balance": current["balance"],
        "expense_delta": expense_delta,
        "income_delta": income_delta,
        "expense_change_pct": expense_change_pct,
        "income_change_pct": income_change_pct,
        "avg_daily_expense": round(current["expense_total"] / days, 2),
        "avg_daily_income": round(current["income_total"] / days, 2),
        "top_categories": current["top_categories"],
        "expense_by_user": current["expense_by_user"],
        "forecast": forecast,
        "previous": previous,
    }


def render_monthly_report_text(payload: dict[str, Any]) -> str:
    """Выполняет действие «render monthly report text» в рамках логики Finance Helper."""
    month = int(payload["month"])
    year = int(payload["year"])
    lines = [
        f"📅 Ежемесячный отчёт за {month:02d}.{year}",
        "",
        f"➖ Расходы: {payload['expense_total']:.2f}",
        f"➕ Доходы: {payload['income_total']:.2f}",
        f"💰 Баланс: {payload['balance']:.2f}",
        "",
        f"Δ расходы к прошлому месяцу: {payload['expense_delta']:+.2f}" + (f" ({payload['expense_change_pct']:+.1f}%)" if payload.get("expense_change_pct") is not None else ""),
        f"Δ доходы к прошлому месяцу: {payload['income_delta']:+.2f}" + (f" ({payload['income_change_pct']:+.1f}%)" if payload.get("income_change_pct") is not None else ""),
        f"Средний расход в день: {payload['avg_daily_expense']:.2f}",
        f"Средний доход в день: {payload['avg_daily_income']:.2f}",
        f"Прогноз расходов к концу месяца: {payload['forecast']['projected_expense']:.2f}",
        "",
        "Топ категорий:",
    ]
    if payload.get("top_categories"):
        for item in payload["top_categories"]:
            lines.append(f"• {item['category']} — {item['amount']:.2f} ({item.get('share_percent', 0):.1f}%)")
    else:
        lines.append("• Нет расходов за период")
    users = payload.get("expense_by_user") or []
    if users:
        lines.extend(["", "По участникам:"])
        for item in users:
            lines.append(f"• {item['user']} — {item['amount']:.2f} ({item.get('share_percent', 0):.1f}%)")
    return "\n".join(lines)


def spending_analysis_payload(
    ops: list[dict[str, Any]],
    previous_ops: list[dict[str, Any]],
    *,
    year: int | None = None,
    month: int | None = None,
    limits: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Выполняет действие «spending analysis payload» в рамках логики Finance Helper."""
    current = summary_report(ops)
    previous = summary_report(previous_ops)
    insights: list[str] = []
    recommendations: list[str] = []

    cur_expense = current["expense_total"]
    prev_expense = previous["expense_total"]

    if cur_expense > prev_expense > 0:
        delta = cur_expense - prev_expense
        pct = round(delta / prev_expense * 100, 1)
        insights.append(f"Расходы выросли на {delta:.2f} ({pct}%) по сравнению с прошлым периодом.")
    elif prev_expense > cur_expense:
        delta = prev_expense - cur_expense
        pct = round(delta / prev_expense * 100, 1) if prev_expense else 0
        insights.append(f"Расходы снизились на {delta:.2f} ({pct}%) по сравнению с прошлым периодом.")
    else:
        insights.append("Расходы почти не изменились по сравнению с прошлым периодом.")

    if current["top_categories"]:
        top = current["top_categories"][0]
        insights.append(f"Главная категория расходов: {top['category']} ({top['amount']:.2f}, {top.get('share_percent', 0):.1f}% расходов).")
        recommendations.append(f"Проверь, можно ли оптимизировать траты в категории «{top['category']}».")

    expense_ops = [op for op in ops if op.get("type") == "expense"]
    if expense_ops:
        biggest = max(expense_ops, key=lambda op: float(op["amount"]))
        insights.append(
            f"Самая крупная трата: {float(biggest['amount']):.2f} в категории «{biggest.get('category') or 'Без категории'}» {str(biggest.get('occurred_at'))}."
        )

    user_breakdown = current.get("expense_by_user") or []
    if user_breakdown:
        lead = user_breakdown[0]
        insights.append(f"Больше всего расходов внёс участник {lead['user']} — {lead['amount']:.2f} ({lead.get('share_percent', 0):.1f}%).")
        if len(user_breakdown) > 1:
            recommendations.append("Сравни вклад участников по категориям и договоритесь, какие расходы взять под контроль вместе.")

    cur_by_cat = _category_totals(ops)
    prev_by_cat = _category_totals(previous_ops)
    growth_candidates: list[tuple[float, str]] = []
    for category, amount in cur_by_cat.items():
        delta = amount - prev_by_cat.get(category, 0.0)
        if delta > 0:
            growth_candidates.append((delta, category))
    if growth_candidates:
        growth_candidates.sort(reverse=True)
        delta, category = growth_candidates[0]
        insights.append(f"Больше всего выросла категория «{category}» (+{delta:.2f}).")

    anomalies = _anomalies(expense_ops)
    if anomalies:
        anomaly = anomalies[0]
        insights.append(f"Обнаружена нетипично крупная трата: {anomaly['amount']:.2f} — {anomaly['label']} ({anomaly['category']}).")
        recommendations.append("Проверь крупные разовые покупки: их удобнее выносить в отдельный план или лимит.")

    recurring = _recurring_candidates(ops, previous_ops)
    if recurring:
        first = recurring[0]
        insights.append(f"Похоже на регулярную трату: {first['label']} — в среднем {first['avg_amount']:.2f} ({first['occurrences']} повторов).")
        recommendations.append("Регулярные траты стоит вынести в отдельную категорию или контролировать через месячный лимит.")

    if year and month:
        forecast = _forecast_month_end(cur_expense, year, month)
        insights.append(f"Если текущий темп сохранится, к концу месяца расходы составят около {forecast['projected_expense']:.2f}.")

    high_limits = [item for item in (limits or []) if float(item.get("percent_used") or 0) >= 80]
    if high_limits:
        risky = sorted(high_limits, key=lambda item: float(item.get("percent_used") or 0), reverse=True)[0]
        insights.append(f"Риск по лимитам: «{risky.get('label', 'Лимит')}» уже использован на {risky.get('percent_used')}%.")
        recommendations.append("Чтобы не выйти за бюджет, лучше сократить траты в лимитах с загрузкой 80% и выше.")

    if current["balance"] < 0:
        recommendations.append("Баланс отрицательный — стоит сократить нерегулярные траты до конца месяца.")
    elif current["income_total"] > 0 and current["balance"] < current["income_total"] * 0.1:
        recommendations.append("Запас по балансу небольшой — имеет смысл временно ограничить необязательные покупки.")

    if not recommendations:
        recommendations.append("Сохраняй текущий темп — серьёзных признаков перерасхода не видно.")

    text_lines = ["📅 AI-анализ трат", ""]
    text_lines.extend(f"• {item}" for item in insights)
    text_lines.append("")
    text_lines.append("Рекомендации:")
    text_lines.extend(f"• {item}" for item in recommendations)

    return {
        "insights": insights,
        "recommendations": recommendations,
        "anomalies": anomalies,
        "recurring": recurring,
        "text": "\n".join(text_lines),
        "summary": current,
    }


def dashboard_payload(ops: list[dict[str, Any]], days: int = 30) -> dict[str, Any]:
    """Выполняет действие «dashboard payload» в рамках логики Finance Helper."""
    summary = summary_report(ops)
    today = date.today()
    start = today - timedelta(days=days - 1)
    by_day = {item["date"]: item["amount"] for item in summary["expense_by_day"]}
    timeline = []
    for i in range(days):
        cur = start + timedelta(days=i)
        timeline.append({"date": cur.isoformat(), "amount": round(float(by_day.get(cur.isoformat(), 0.0)), 2)})
    recent = sorted(ops, key=lambda op: (str(op.get("occurred_at")), int(op.get("id", 0))), reverse=True)[:10]
    return {"summary": summary, "timeline": timeline, "recent_operations": recent}
