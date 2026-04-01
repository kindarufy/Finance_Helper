"""FastAPI-приложение финансового сервиса с маршрутами для пользователей, операций, лимитов и импортов."""
from datetime import date

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import crud, models, schemas
from .db import get_db
from .security import require_internal_key

app = FastAPI(title="Finance Service", version="0.8-release-stage12-13")


@app.get("/health", response_model=schemas.Health)
def health():
    """Возвращает ответ для проверки, что финансовый сервис работает."""
    return schemas.Health()


def _raise_from_value_error(exc: ValueError) -> None:
    """Преобразует ValueError бизнес-логики в HTTP-ошибку с нужным статусом."""
    detail = str(exc)
    status = 400
    if detail in {"user_not_found", "workspace_not_found", "category_not_found", "op_not_found", "member_user_not_found"}:
        status = 404
    elif detail in {"member_identifier_invalid"}:
        status = 400
    elif detail in {"workspace_access_denied", "workspace_readonly", "owner_required"}:
        status = 403
    elif detail in {"alias_conflict", "category_name_conflict"}:
        status = 409
    raise HTTPException(status_code=status, detail=detail)


def _user_out(user: models.User) -> schemas.UserOut:
    """Преобразует ORM-модель пользователя в схему ответа."""
    return schemas.UserOut(
        telegram_id=user.telegram_id,
        username=user.username,
        daily_limit=float(user.daily_limit) if user.daily_limit is not None else None,
        notify_enabled=bool(user.notify_enabled),
        base_currency=user.base_currency,
        timezone=user.timezone,
        active_workspace_id=user.active_workspace_id,
    )


def _category_out(c: models.Category) -> schemas.CategoryOut:
    """Преобразует ORM-модель категории в схему ответа."""
    return schemas.CategoryOut(
        id=c.id,
        workspace_id=c.workspace_id,
        name=c.name,
        type=c.type,
        emoji=c.emoji,
        is_archived=c.is_archived,
    )


def _operation_out(db: Session, op: models.Operation, category_name: str | None = None) -> schemas.OperationOut:
    """Преобразует ORM-модель операции в схему ответа."""
    subject = db.get(models.User, op.user_id)
    actor = db.get(models.User, op.created_by_user_id)
    if category_name is None and op.category_id:
        category_name = db.scalar(select(models.Category.name).where(models.Category.id == op.category_id))
    return schemas.OperationOut(
        id=op.id,
        workspace_id=op.workspace_id,
        user_telegram_id=subject.telegram_id if subject else None,
        actor_telegram_id=actor.telegram_id if actor else None,
        user_username=subject.username if subject else None,
        actor_username=actor.username if actor else None,
        type=op.type.value if hasattr(op.type, "value") else str(op.type),
        amount=float(op.amount),
        currency=op.currency,
        category=category_name,
        comment=op.comment,
        source=op.source,
        occurred_at=op.occurred_at,
    )


@app.post("/users/upsert", dependencies=[Depends(require_internal_key)], response_model=schemas.UserOut)
def upsert_user(payload: schemas.UserUpsertIn, db: Session = Depends(get_db)):
    """Создаёт или обновляет пользователя."""
    user = crud.upsert_user(db, payload.telegram_id, payload.username)
    return _user_out(user)


@app.post("/users/setlimit", dependencies=[Depends(require_internal_key)], response_model=schemas.UserOut)
def set_limit(payload: schemas.SetLimitIn, db: Session = Depends(get_db)):
    """Устанавливает лимит."""
    try:
        user = crud.set_daily_limit(db, payload.telegram_id, payload.daily_limit)
    except ValueError as exc:
        _raise_from_value_error(exc)
    return _user_out(user)


@app.get("/workspaces", dependencies=[Depends(require_internal_key)], response_model=list[schemas.WorkspaceOut])
def workspaces(telegram_id: int = Query(...), db: Session = Depends(get_db)):
    """Возвращает список пространств пользователя."""
    try:
        items = crud.list_workspaces(db, telegram_id)
        requester = crud.get_user(db, telegram_id)
    except ValueError as exc:
        _raise_from_value_error(exc)

    owner_ids = {item.owner_user_id for item in items}
    owners = {user.id: user.telegram_id for user in db.scalars(select(models.User).where(models.User.id.in_(owner_ids))).all()}
    active_id = requester.active_workspace_id if requester else None
    return [
        schemas.WorkspaceOut(
            id=item.id,
            name=item.name,
            type=item.type,
            base_currency=item.base_currency,
            owner_telegram_id=owners.get(item.owner_user_id, telegram_id),
            is_archived=item.is_archived,
            my_role=crud._membership_for_user(db, item.id, requester.id).role if requester else None,
            is_active=item.id == active_id,
        )
        for item in items
    ]


@app.get("/workspaces/active", dependencies=[Depends(require_internal_key)], response_model=schemas.WorkspaceOut)
def active_workspace(telegram_id: int = Query(...), db: Session = Depends(get_db)):
    """Возвращает активное пространство пользователя."""
    try:
        item = crud.get_active_workspace(db, telegram_id)
        requester = crud.get_user(db, telegram_id)
        owner = db.get(models.User, item.owner_user_id)
    except ValueError as exc:
        _raise_from_value_error(exc)
    return schemas.WorkspaceOut(
        id=item.id,
        name=item.name,
        type=item.type,
        base_currency=item.base_currency,
        owner_telegram_id=owner.telegram_id if owner else telegram_id,
        is_archived=item.is_archived,
        my_role=crud._membership_for_user(db, item.id, requester.id).role if requester else None,
        is_active=True,
    )


@app.post("/workspaces/active", dependencies=[Depends(require_internal_key)], response_model=schemas.WorkspaceOut)
def set_active_workspace(payload: schemas.WorkspaceSetActiveIn, db: Session = Depends(get_db)):
    """Устанавливает активное пространство пользователя."""
    try:
        item = crud.set_active_workspace(db, payload.telegram_id, payload.workspace_id)
        requester = crud.get_user(db, payload.telegram_id)
        owner = db.get(models.User, item.owner_user_id)
    except ValueError as exc:
        _raise_from_value_error(exc)
    return schemas.WorkspaceOut(
        id=item.id,
        name=item.name,
        type=item.type,
        base_currency=item.base_currency,
        owner_telegram_id=owner.telegram_id if owner else payload.telegram_id,
        is_archived=item.is_archived,
        my_role=crud._membership_for_user(db, item.id, requester.id).role if requester else None,
        is_active=True,
    )


@app.post("/workspaces", dependencies=[Depends(require_internal_key)], response_model=schemas.WorkspaceOut)
def create_workspace(payload: schemas.WorkspaceCreateIn, db: Session = Depends(get_db)):
    """Создаёт пространство."""
    try:
        item = crud.create_workspace(db, payload.telegram_id, payload.name, payload.type, payload.base_currency)
        owner = db.get(models.User, item.owner_user_id)
        requester = crud.get_user(db, payload.telegram_id)
    except ValueError as exc:
        _raise_from_value_error(exc)

    return schemas.WorkspaceOut(
        id=item.id,
        name=item.name,
        type=item.type,
        base_currency=item.base_currency,
        owner_telegram_id=owner.telegram_id if owner else payload.telegram_id,
        is_archived=item.is_archived,
        my_role=crud._membership_for_user(db, item.id, requester.id).role if requester else None,
        is_active=(requester.active_workspace_id == item.id) if requester else False,
    )


@app.get("/workspaces/{workspace_id}/members", dependencies=[Depends(require_internal_key)], response_model=list[schemas.WorkspaceMemberOut])
def workspace_members(workspace_id: int, telegram_id: int = Query(...), db: Session = Depends(get_db)):
    """Возвращает участников пространства."""
    try:
        items = crud.list_workspace_members(db, telegram_id, workspace_id)
    except ValueError as exc:
        _raise_from_value_error(exc)
    return [schemas.WorkspaceMemberOut(telegram_id=item.user.telegram_id, username=item.user.username, role=item.role) for item in items]


@app.post("/workspaces/{workspace_id}/members", dependencies=[Depends(require_internal_key)], response_model=schemas.WorkspaceMemberOut)
def add_workspace_member(workspace_id: int, payload: schemas.WorkspaceMemberAddIn, db: Session = Depends(get_db)):
    """Добавляет участника пространства."""
    try:
        member_user = crud.resolve_user_by_identifier(db, payload.member_identifier)
        item = crud.add_workspace_member(
            db,
            workspace_id=workspace_id,
            owner_telegram_id=payload.telegram_id,
            member_telegram_id=member_user.telegram_id,
            role=payload.role,
        )
        db.refresh(item)
    except ValueError as exc:
        _raise_from_value_error(exc)
    return schemas.WorkspaceMemberOut(
        telegram_id=item.user.telegram_id,
        username=item.user.username,
        role=item.role,
    )


@app.get("/categories", dependencies=[Depends(require_internal_key)], response_model=list[schemas.CategoryOut])
def categories(
    telegram_id: int = Query(...),
    workspace_id: int | None = Query(None),
    category_type: models.OperationType | None = Query(None),
    include_archived: bool = Query(False),
    db: Session = Depends(get_db),
):
    """Возвращает категории пространства."""
    try:
        cats = crud.list_categories(db, telegram_id, workspace_id, category_type, include_archived)
    except ValueError as exc:
        _raise_from_value_error(exc)
    return [_category_out(c) for c in cats]


@app.post("/categories", dependencies=[Depends(require_internal_key)], response_model=schemas.CategoryOut)
def create_category(payload: schemas.CategoryCreateIn, db: Session = Depends(get_db)):
    """Создаёт категорию."""
    try:
        c = crud.create_category(
            db,
            telegram_id=payload.telegram_id,
            workspace_id=payload.workspace_id,
            name=payload.name,
            category_type=payload.type,
            emoji=payload.emoji,
        )
    except ValueError as exc:
        _raise_from_value_error(exc)
    return _category_out(c)


@app.patch("/categories/{category_id}", dependencies=[Depends(require_internal_key)], response_model=schemas.CategoryOut)
def update_category(category_id: int, payload: schemas.CategoryUpdateIn, db: Session = Depends(get_db)):
    """Обновляет категорию."""
    try:
        c = crud.update_category(db, payload.telegram_id, category_id, payload.name, payload.emoji, payload.is_archived)
    except ValueError as exc:
        _raise_from_value_error(exc)
    return _category_out(c)


@app.get("/categories/{category_id}/aliases", dependencies=[Depends(require_internal_key)], response_model=list[schemas.CategoryAliasOut])
def category_aliases(category_id: int, telegram_id: int = Query(...), db: Session = Depends(get_db)):
    """Возвращает ключевые слова выбранной категории."""
    try:
        items = crud.list_aliases(db, telegram_id, category_id)
    except ValueError as exc:
        _raise_from_value_error(exc)
    return [schemas.CategoryAliasOut(id=item.id, category_id=item.category_id, alias=item.alias, normalized_alias=item.normalized_alias) for item in items]


@app.post("/categories/{category_id}/aliases", dependencies=[Depends(require_internal_key)], response_model=schemas.CategoryAliasOut)
def create_alias(category_id: int, payload: schemas.CategoryAliasCreateIn, db: Session = Depends(get_db)):
    """Создаёт ключевое слово категории."""
    try:
        item = crud.create_alias(db, payload.telegram_id, category_id, payload.alias)
    except ValueError as exc:
        _raise_from_value_error(exc)
    return schemas.CategoryAliasOut(id=item.id, category_id=item.category_id, alias=item.alias, normalized_alias=item.normalized_alias)


@app.delete("/aliases/{alias_id}", dependencies=[Depends(require_internal_key)], response_model=schemas.DeleteResult)
def delete_alias(alias_id: int, telegram_id: int = Query(...), db: Session = Depends(get_db)):
    """Удаляет ключевое слово категории."""
    try:
        deleted = crud.delete_alias(db, telegram_id, alias_id)
    except ValueError as exc:
        _raise_from_value_error(exc)
    return schemas.DeleteResult(deleted=deleted)


@app.post("/categories/match", dependencies=[Depends(require_internal_key)], response_model=schemas.CategoryMatchOut)
def match_category(payload: schemas.CategoryMatchIn, db: Session = Depends(get_db)):
    """Подбирает категорию по тексту операции и алиасам."""
    try:
        category = crud.match_category(db, payload.telegram_id, payload.workspace_id, payload.text, payload.type)
    except ValueError as exc:
        _raise_from_value_error(exc)
    if not category:
        return schemas.CategoryMatchOut(matched=False, category=None, reason="no_match")
    return schemas.CategoryMatchOut(matched=True, category=_category_out(category), reason="matched")


@app.post("/operations", dependencies=[Depends(require_internal_key)])
def create_operation(payload: schemas.OperationCreateIn, db: Session = Depends(get_db)):
    """Создаёт операцию."""
    try:
        op = crud.create_operation(
            db=db,
            telegram_id=payload.telegram_id,
            workspace_id=payload.workspace_id,
            op_type=payload.type,
            amount=payload.amount,
            currency=payload.currency,
            category=payload.category,
            comment=payload.comment,
            source=payload.source,
            occurred_at=payload.occurred_at,
            user_telegram_id=payload.user_telegram_id,
            actor_telegram_id=payload.actor_telegram_id,
            merchant=payload.merchant,
            external_ref=payload.external_ref,
            is_imported=payload.is_imported,
            receipt_upload_id=payload.receipt_upload_id,
            statement_import_id=payload.statement_import_id,
        )
    except ValueError as exc:
        _raise_from_value_error(exc)

    limit_out = None
    limit_alerts: list[dict] = []
    if payload.type == "expense":
        total, user = crud.daily_expense_total(db, payload.telegram_id, payload.occurred_at or date.today(), payload.workspace_id)
        limit_out = schemas.LimitCheckOut(
            limit_exceeded=bool(user.daily_limit is not None and float(total) > float(user.daily_limit)),
            daily_limit=float(user.daily_limit) if user.daily_limit is not None else None,
            day_expenses_total=float(total),
        ).model_dump()
        limit_alerts = [schemas.LimitAlertOut(**item).model_dump() for item in crud.evaluate_limit_alerts_for_operation(db, op)]

    return {"operation": _operation_out(db, op).model_dump(), "limit": limit_out, "limit_alerts": limit_alerts}


@app.get("/operations", dependencies=[Depends(require_internal_key)])
def list_ops(
    telegram_id: int = Query(...),
    workspace_id: int | None = Query(None),
    limit: int = Query(10, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    op_type: str | None = Query(None),
    category_id: int | None = Query(None),
    category_name: str | None = Query(None),
    user_telegram_id: int | None = Query(None),
    actor_telegram_id: int | None = Query(None),
    search: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """Возвращает список: операции."""
    try:
        rows = crud.list_operations(
            db,
            telegram_id,
            workspace_id=workspace_id,
            limit=limit,
            offset=offset,
            date_from=date_from,
            date_to=date_to,
            op_type=op_type,
            category_id=category_id,
            category_name=category_name,
            user_telegram_id=user_telegram_id,
            actor_telegram_id=actor_telegram_id,
            search=search,
        )
    except ValueError as exc:
        _raise_from_value_error(exc)

    items = [_operation_out(db, op, cat_name).model_dump() for op, cat_name, _subject_tg, _actor_tg in rows]
    return {"items": items, "count": len(items)}


@app.patch("/operations/{op_id}", dependencies=[Depends(require_internal_key)], response_model=schemas.OperationOut)
def update_op(op_id: int, payload: schemas.OperationUpdateIn, db: Session = Depends(get_db)):
    """Обновляет операцию."""
    try:
        op = crud.update_operation(
            db=db,
            telegram_id=payload.telegram_id,
            op_id=op_id,
            amount=payload.amount,
            currency=payload.currency,
            comment=payload.comment,
            category=payload.category,
            occurred_at=payload.occurred_at,
        )
    except ValueError as exc:
        _raise_from_value_error(exc)
    return _operation_out(db, op)


@app.delete("/operations/{op_id}", dependencies=[Depends(require_internal_key)], response_model=schemas.DeleteResult)
def delete_op(op_id: int, telegram_id: int = Query(...), db: Session = Depends(get_db)):
    """Удаляет операцию."""
    try:
        deleted = crud.delete_operation(db, telegram_id, op_id)
    except ValueError as exc:
        _raise_from_value_error(exc)
    return schemas.DeleteResult(deleted=deleted)


@app.get("/limits", dependencies=[Depends(require_internal_key)], response_model=list[schemas.BudgetLimitOut])
def limits(telegram_id: int = Query(...), workspace_id: int | None = Query(None), db: Session = Depends(get_db)):
    """Возвращает список лимитов для пользователя или пространства."""
    try:
        items = crud.list_budget_limits(db, telegram_id, workspace_id)
    except ValueError as exc:
        _raise_from_value_error(exc)
    out = []
    for item in items:
        user_tg = db.get(models.User, item.user_id).telegram_id if item.user_id else None
        out.append(
            schemas.BudgetLimitOut(
                id=item.id,
                workspace_id=item.workspace_id,
                scope=item.scope,
                period=item.period,
                amount=float(item.amount),
                currency=item.currency,
                user_telegram_id=user_tg,
                category_id=item.category_id,
                is_active=item.is_active,
            )
        )
    return out


@app.get("/limits/overview", dependencies=[Depends(require_internal_key)], response_model=list[schemas.BudgetLimitStatusOut])
def limits_overview(telegram_id: int = Query(...), workspace_id: int | None = Query(None), ref_date: date | None = Query(None), db: Session = Depends(get_db)):
    """Возвращает сводку по использованию лимитов."""
    try:
        items = crud.get_budget_limits_overview(db, telegram_id, workspace_id, ref_date)
    except ValueError as exc:
        _raise_from_value_error(exc)
    return [schemas.BudgetLimitStatusOut(**item) for item in items]


@app.post("/limits", dependencies=[Depends(require_internal_key)], response_model=schemas.BudgetLimitOut)
def create_limit(payload: schemas.BudgetLimitCreateIn, db: Session = Depends(get_db)):
    """Создаёт лимит."""
    try:
        item = crud.create_or_update_budget_limit(
            db,
            telegram_id=payload.telegram_id,
            workspace_id=payload.workspace_id,
            scope=payload.scope,
            period=payload.period,
            amount=payload.amount,
            currency=payload.currency,
            user_telegram_id=payload.user_telegram_id,
            category_id=payload.category_id,
            notify_at_50=payload.notify_at_50,
            notify_at_80=payload.notify_at_80,
            notify_at_100=payload.notify_at_100,
        )
    except ValueError as exc:
        _raise_from_value_error(exc)
    user_tg = db.get(models.User, item.user_id).telegram_id if item.user_id else None
    return schemas.BudgetLimitOut(
        id=item.id,
        workspace_id=item.workspace_id,
        scope=item.scope,
        period=item.period,
        amount=float(item.amount),
        currency=item.currency,
        user_telegram_id=user_tg,
        category_id=item.category_id,
        is_active=item.is_active,
    )


@app.get("/report-schedules", dependencies=[Depends(require_internal_key)], response_model=list[schemas.ReportScheduleOut])
def report_schedules(telegram_id: int = Query(...), workspace_id: int | None = Query(None), db: Session = Depends(get_db)):
    """Возвращает расписания автоматических отчётов."""
    try:
        items = crud.list_report_schedules(db, telegram_id, workspace_id)
    except ValueError as exc:
        _raise_from_value_error(exc)
    out = []
    for item in items:
        user_tg = db.get(models.User, item.user_id).telegram_id if item.user_id else None
        out.append(
            schemas.ReportScheduleOut(
                id=item.id,
                workspace_id=item.workspace_id,
                user_telegram_id=user_tg,
                frequency=item.frequency,
                day_of_month=item.day_of_month,
                send_time=item.send_time,
                timezone=item.timezone,
                enabled=item.enabled,
            )
        )
    return out


@app.post("/report-schedules", dependencies=[Depends(require_internal_key)], response_model=schemas.ReportScheduleOut)
def create_report_schedule(payload: schemas.ReportScheduleUpsertIn, db: Session = Depends(get_db)):
    """Создаёт расписание отчёта."""
    try:
        item = crud.upsert_report_schedule(
            db,
            telegram_id=payload.telegram_id,
            workspace_id=payload.workspace_id,
            user_telegram_id=payload.user_telegram_id,
            frequency=payload.frequency,
            day_of_month=payload.day_of_month,
            send_time=payload.send_time,
            timezone=payload.timezone,
            enabled=payload.enabled,
        )
    except ValueError as exc:
        _raise_from_value_error(exc)
    user_tg = db.get(models.User, item.user_id).telegram_id if item.user_id else None
    return schemas.ReportScheduleOut(
        id=item.id,
        workspace_id=item.workspace_id,
        user_telegram_id=user_tg,
        frequency=item.frequency,
        day_of_month=item.day_of_month,
        send_time=item.send_time,
        timezone=item.timezone,
        enabled=item.enabled,
    )


@app.get("/report-schedules/due", dependencies=[Depends(require_internal_key)], response_model=list[schemas.DueReportScheduleOut])
def due_report_schedules(run_date: date = Query(...), send_time: str = Query(..., pattern=r"^\d{2}:\d{2}$"), db: Session = Depends(get_db)):
    """Возвращает расписания отчётов, которые нужно отправить сейчас."""
    items = crud.list_due_report_schedules(db, run_date=run_date, send_time=send_time)
    return [schemas.DueReportScheduleOut(**item) for item in items]


def _receipt_out(item: models.ReceiptUpload) -> schemas.ReceiptUploadOut:
    """Преобразует ORM-модель чека в схему ответа."""
    return schemas.ReceiptUploadOut(
        id=item.id,
        workspace_id=item.workspace_id,
        status=item.status,
        original_filename=item.original_filename,
        telegram_file_id=item.telegram_file_id,
        storage_path=item.storage_path,
        parsed_total=float(item.parsed_total) if item.parsed_total is not None else None,
        parsed_currency=item.parsed_currency,
        parsed_merchant=item.parsed_merchant,
        parsed_date=item.parsed_date,
        raw_text=item.raw_text,
        error_message=item.error_message,
    )


def _statement_import_out(item: models.StatementImport) -> schemas.StatementImportOut:
    """Преобразует ORM-модель импорта выписки в схему ответа."""
    return schemas.StatementImportOut(
        id=item.id,
        workspace_id=item.workspace_id,
        status=item.status,
        original_filename=item.original_filename,
        file_type=item.file_type,
        imported_rows=item.imported_rows,
        skipped_rows=item.skipped_rows,
        summary_text=item.summary_text,
        error_message=item.error_message,
    )


@app.post("/receipts", dependencies=[Depends(require_internal_key)], response_model=schemas.ReceiptUploadOut)
def create_receipt(payload: schemas.ReceiptUploadCreateIn, db: Session = Depends(get_db)):
    """Создаёт чек."""
    try:
        item = crud.create_receipt_upload(
            db,
            telegram_id=payload.telegram_id,
            workspace_id=payload.workspace_id,
            original_filename=payload.original_filename,
            telegram_file_id=payload.telegram_file_id,
            storage_path=payload.storage_path,
        )
    except ValueError as exc:
        _raise_from_value_error(exc)
    return _receipt_out(item)


@app.post("/receipts/{receipt_id}/parse", dependencies=[Depends(require_internal_key)], response_model=schemas.ReceiptUploadOut)
def parse_receipt(receipt_id: int, payload: schemas.ReceiptParseIn, db: Session = Depends(get_db)):
    """Сохраняет результат распознавания загруженного чека."""
    try:
        item = crud.update_receipt_upload(
            db,
            telegram_id=payload.telegram_id,
            receipt_id=receipt_id,
            parsed_total=payload.parsed_total,
            parsed_currency=payload.parsed_currency,
            parsed_merchant=payload.parsed_merchant,
            parsed_date=payload.parsed_date,
            raw_text=payload.raw_text,
            error_message=payload.error_message,
            status=payload.status,
        )
    except ValueError as exc:
        _raise_from_value_error(exc)
    return _receipt_out(item)


@app.post("/receipts/{receipt_id}/confirm", dependencies=[Depends(require_internal_key)])
def confirm_receipt(receipt_id: int, payload: schemas.ReceiptConfirmIn, db: Session = Depends(get_db)):
    """Подтверждает чек."""
    try:
        op = crud.confirm_receipt_upload(
            db,
            telegram_id=payload.telegram_id,
            receipt_id=receipt_id,
            category=payload.category,
            comment=payload.comment,
            currency=payload.currency,
            amount=payload.amount,
            occurred_at=payload.occurred_at,
        )
    except ValueError as exc:
        _raise_from_value_error(exc)
    return {"operation": _operation_out(db, op).model_dump()}


@app.post("/statement-imports", dependencies=[Depends(require_internal_key)], response_model=schemas.StatementImportOut)
def create_statement_import(payload: schemas.StatementImportCreateIn, db: Session = Depends(get_db)):
    """Создаёт запись о загрузке банковской выписки."""
    try:
        item = crud.create_statement_import(
            db,
            telegram_id=payload.telegram_id,
            workspace_id=payload.workspace_id,
            original_filename=payload.original_filename,
            file_type=payload.file_type,
            summary_text=payload.summary_text,
        )
    except ValueError as exc:
        _raise_from_value_error(exc)
    return _statement_import_out(item)


@app.post("/statement-imports/{import_id}/complete", dependencies=[Depends(require_internal_key)], response_model=schemas.StatementImportOut)
def complete_statement_import(import_id: int, payload: schemas.StatementImportCompleteIn, db: Session = Depends(get_db)):
    """Завершает импорт банковской выписки и сохраняет итоговый статус."""
    try:
        item = crud.finalize_statement_import(
            db,
            telegram_id=payload.telegram_id,
            import_id=import_id,
            imported_rows=payload.imported_rows,
            skipped_rows=payload.skipped_rows,
            summary_text=payload.summary_text,
            error_message=payload.error_message,
            status=payload.status,
        )
    except ValueError as exc:
        _raise_from_value_error(exc)
    return _statement_import_out(item)
