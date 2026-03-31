"""Модуль сервиса аналитики Finance Helper."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from io import BytesIO, StringIO

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import Response, StreamingResponse
from openpyxl import Workbook

from .client import fetch_due_report_schedules, fetch_limit_overview, fetch_operations, send_telegram_message
from .reports import (
    dashboard_payload,
    month_bounds,
    monthly_report_payload,
    render_daily_text,
    render_monthly_report_text,
    spending_analysis_payload,
    summary_report,
)
from .security import require_internal_key

app = FastAPI(title="Analytics & Notify Service", version="0.4-release-budgets-reports")
_scheduler: AsyncIOScheduler | None = None
_sent_schedule_keys: set[str] = set()


@app.get("/health")
def health():
    """Выполняет действие «health» в рамках логики Finance Helper."""
    return {"status": "ok"}


async def _fetch_ops(
    telegram_id: int,
    workspace_id: int | None,
    date_from: date | None,
    date_to: date | None,
    op_type: str | None = None,
    category_name: str | None = None,
    user_telegram_id: int | None = None,
    actor_telegram_id: int | None = None,
    search: str | None = None,
):
    """Выполняет действие «fetch ops» в рамках логики Finance Helper."""
    try:
        return await fetch_operations(
            telegram_id,
            workspace_id=workspace_id,
            date_from=date_from,
            date_to=date_to,
            op_type=op_type,
            category_name=category_name,
            user_telegram_id=user_telegram_id,
            actor_telegram_id=actor_telegram_id,
            search=search,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"finance_unavailable: {exc}")


def _previous_month(year: int | None = None, month: int | None = None) -> tuple[int, int]:
    """Выполняет действие «previous month» в рамках логики Finance Helper."""
    if year is not None and month is not None:
        return year, month
    today = date.today().replace(day=1)
    prev = today - timedelta(days=1)
    return prev.year, prev.month


@app.on_event("startup")
async def startup_event():
    """Выполняет действие «startup event» в рамках логики Finance Helper."""
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler(timezone="UTC")
        _scheduler.add_job(_run_due_monthly_reports_job, "interval", minutes=1, id="due-monthly-reports", replace_existing=True)
        _scheduler.start()


@app.on_event("shutdown")
async def shutdown_event():
    """Выполняет действие «shutdown event» в рамках логики Finance Helper."""
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None


async def _run_due_monthly_reports_job():
    """Выполняет действие «run due monthly reports job» в рамках логики Finance Helper."""
    now = datetime.utcnow().replace(second=0, microsecond=0)
    send_time = now.strftime("%H:%M")
    try:
        due = await fetch_due_report_schedules(run_date=now.date(), send_time=send_time)
    except Exception:
        return
    for item in due:
        key = f"{item['id']}:{now.date().isoformat()}:{send_time}"
        if key in _sent_schedule_keys:
            continue
        await _send_monthly_report(
            telegram_id=int(item["telegram_id"]),
            workspace_id=item.get("workspace_id"),
            year=None,
            month=None,
        )
        _sent_schedule_keys.add(key)


@app.get("/reports/summary", dependencies=[Depends(require_internal_key)])
async def report_summary(
    telegram_id: int = Query(...),
    workspace_id: int | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
):
    """Выполняет действие «report summary» в рамках логики Finance Helper."""
    ops = await _fetch_ops(telegram_id, workspace_id, date_from, date_to)
    return summary_report(ops)


@app.get("/reports/monthly", dependencies=[Depends(require_internal_key)])
async def report_monthly(
    telegram_id: int = Query(...),
    workspace_id: int | None = Query(None),
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
):
    """Выполняет действие «report monthly» в рамках логики Finance Helper."""
    start, end = month_bounds(year, month)
    prev_year, prev_month = (year - 1, 12) if month == 1 else (year, month - 1)
    prev_start, prev_end = month_bounds(prev_year, prev_month)
    ops = await _fetch_ops(telegram_id, workspace_id, start, end)
    prev_ops = await _fetch_ops(telegram_id, workspace_id, prev_start, prev_end)
    return monthly_report_payload(ops, prev_ops, year, month)


@app.get("/reports/monthly/text", dependencies=[Depends(require_internal_key)])
async def report_monthly_text(
    telegram_id: int = Query(...),
    workspace_id: int | None = Query(None),
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
):
    """Выполняет действие «report monthly text» в рамках логики Finance Helper."""
    payload = await report_monthly(telegram_id=telegram_id, workspace_id=workspace_id, year=year, month=month)
    return {"text": render_monthly_report_text(payload), "payload": payload}


@app.get("/analysis/spending", dependencies=[Depends(require_internal_key)])
async def spending_analysis(
    telegram_id: int = Query(...),
    workspace_id: int | None = Query(None),
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
):
    """Выполняет действие «spending analysis» в рамках логики Finance Helper."""
    start, end = month_bounds(year, month)
    prev_year, prev_month = (year - 1, 12) if month == 1 else (year, month - 1)
    prev_start, prev_end = month_bounds(prev_year, prev_month)
    ops = await _fetch_ops(telegram_id, workspace_id, start, end)
    prev_ops = await _fetch_ops(telegram_id, workspace_id, prev_start, prev_end)
    limit_items = await fetch_limit_overview(telegram_id=telegram_id, workspace_id=workspace_id, ref_date=end)
    return spending_analysis_payload(ops, prev_ops, year=year, month=month, limits=limit_items)


@app.get("/miniapp/dashboard", dependencies=[Depends(require_internal_key)])
async def miniapp_dashboard(
    telegram_id: int = Query(...),
    workspace_id: int | None = Query(None),
    days: int = Query(30, ge=7, le=365),
):
    """Выполняет действие «miniapp dashboard» в рамках логики Finance Helper."""
    end = date.today()
    start = end.fromordinal(end.toordinal() - days + 1)
    ops = await _fetch_ops(telegram_id, workspace_id, start, end)
    return dashboard_payload(ops, days=days)


@app.get("/miniapp/timeseries", dependencies=[Depends(require_internal_key)])
async def miniapp_timeseries(
    telegram_id: int = Query(...),
    workspace_id: int | None = Query(None),
    date_from: date = Query(...),
    date_to: date = Query(...),
):
    """Выполняет действие «miniapp timeseries» в рамках логики Finance Helper."""
    ops = await _fetch_ops(telegram_id, workspace_id, date_from, date_to)
    return dashboard_payload(ops, days=(date_to - date_from).days + 1)["timeline"]


@app.get("/limits/overview", dependencies=[Depends(require_internal_key)])
async def limits_overview(
    telegram_id: int = Query(...),
    workspace_id: int | None = Query(None),
    ref_date: date | None = Query(None),
):
    """Выполняет действие «limits overview» в рамках логики Finance Helper."""
    try:
        return await fetch_limit_overview(telegram_id=telegram_id, workspace_id=workspace_id, ref_date=ref_date)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"finance_unavailable: {exc}")


@app.get("/exports/csv", dependencies=[Depends(require_internal_key)])
async def export_csv(
    telegram_id: int = Query(...),
    workspace_id: int | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    op_type: str | None = Query(None),
):
    """Выполняет действие «export csv» в рамках логики Finance Helper."""
    ops = await _fetch_ops(telegram_id, workspace_id, date_from, date_to, op_type=op_type)
    buffer = StringIO()
    headers = [
        "id", "occurred_at", "type", "amount", "currency", "category", "comment",
        "user_telegram_id", "actor_telegram_id", "source", "workspace_id",
    ]
    buffer.write(",".join(headers) + "\n")
    for op in ops:
        row = [
            str(op.get("id", "")),
            str(op.get("occurred_at", "")),
            str(op.get("type", "")),
            str(op.get("amount", "")),
            str(op.get("currency", "")),
            str((op.get("category") or "").replace(",", " ")),
            str((op.get("comment") or "").replace(",", " ").replace("\n", " ")),
            str(op.get("user_telegram_id", "")),
            str(op.get("actor_telegram_id", "")),
            str(op.get("source", "")),
            str(op.get("workspace_id", "")),
        ]
        buffer.write(",".join(row) + "\n")
    data = buffer.getvalue().encode("utf-8-sig")
    return Response(
        content=data,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=finance_export.csv"},
    )


@app.get("/exports/xlsx", dependencies=[Depends(require_internal_key)])
async def export_xlsx(
    telegram_id: int = Query(...),
    workspace_id: int | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    op_type: str | None = Query(None),
):
    """Выполняет действие «export xlsx» в рамках логики Finance Helper."""
    ops = await _fetch_ops(telegram_id, workspace_id, date_from, date_to, op_type=op_type)
    wb = Workbook()
    ws = wb.active
    ws.title = "Operations"
    ws.append(["ID", "Date", "Type", "Amount", "Currency", "Category", "Comment", "User", "Actor", "Source", "Workspace"])
    for op in ops:
        ws.append([
            op.get("id"),
            op.get("occurred_at"),
            op.get("type"),
            float(op.get("amount", 0) or 0),
            op.get("currency"),
            op.get("category"),
            op.get("comment"),
            op.get("user_telegram_id"),
            op.get("actor_telegram_id"),
            op.get("source"),
            op.get("workspace_id"),
        ])
    stream = BytesIO()
    wb.save(stream)
    stream.seek(0)
    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=finance_export.xlsx"},
    )


@app.post("/notify/daily", dependencies=[Depends(require_internal_key)])
async def notify_daily(telegram_id: int = Query(...), workspace_id: int | None = Query(None)):
    """Выполняет действие «notify daily» в рамках логики Finance Helper."""
    today = date.today()
    ops = await _fetch_ops(telegram_id, workspace_id, today, today)
    rep = summary_report(ops)
    text = render_daily_text(today.isoformat(), rep)
    ok = await send_telegram_message(telegram_id, text)
    if not ok:
        return {"sent": False, "text": text}
    return {"sent": True}


async def _send_monthly_report(telegram_id: int, workspace_id: int | None, year: int | None, month: int | None) -> dict:
    """Отправляет данные, относящиеся к сценарию «monthly report»."""
    year, month = _previous_month(year, month)
    payload = await report_monthly(telegram_id=telegram_id, workspace_id=workspace_id, year=year, month=month)
    text = render_monthly_report_text(payload)
    ok = await send_telegram_message(telegram_id, text)
    return {"sent": ok, "text": text, "year": year, "month": month, "payload": payload}


@app.post("/notify/monthly", dependencies=[Depends(require_internal_key)])
async def notify_monthly(
    telegram_id: int = Query(...),
    workspace_id: int | None = Query(None),
    year: int | None = Query(None),
    month: int | None = Query(None),
):
    """Выполняет действие «notify monthly» в рамках логики Finance Helper."""
    return await _send_monthly_report(telegram_id=telegram_id, workspace_id=workspace_id, year=year, month=month)


@app.post("/notify/monthly/run-due", dependencies=[Depends(require_internal_key)])
async def notify_monthly_run_due(run_date: date | None = Query(None), send_time: str | None = Query(None)):
    """Выполняет действие «notify monthly run due» в рамках логики Finance Helper."""
    now = datetime.utcnow().replace(second=0, microsecond=0)
    current_date = run_date or now.date()
    current_send_time = send_time or now.strftime("%H:%M")
    due = await fetch_due_report_schedules(run_date=current_date, send_time=current_send_time)
    sent = []
    for item in due:
        key = f"{item['id']}:{current_date.isoformat()}:{current_send_time}"
        if key in _sent_schedule_keys:
            continue
        result = await _send_monthly_report(
            telegram_id=int(item["telegram_id"]),
            workspace_id=item.get("workspace_id"),
            year=None,
            month=None,
        )
        _sent_schedule_keys.add(key)
        sent.append({"schedule_id": item["id"], "telegram_id": item["telegram_id"], "sent": result["sent"]})
    return {"checked": len(due), "sent": sent}
