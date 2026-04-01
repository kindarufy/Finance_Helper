"""Pydantic-схемы запросов и ответов финансового сервиса."""
from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

from .models import ImportStatus, LimitPeriod, LimitScope, MemberRole, OperationType, WorkspaceType


class Health(BaseModel):
    """Схема ответа health-эндпоинта."""
    status: str = "ok"


class UserUpsertIn(BaseModel):
    """Входная схема для создания или обновления пользователя."""
    telegram_id: int
    username: str | None = None


class UserOut(BaseModel):
    """Выходная схема с данными пользователя."""
    telegram_id: int
    username: str | None
    daily_limit: float | None
    notify_enabled: bool
    base_currency: str | None = None
    timezone: str | None = None
    active_workspace_id: int | None = None


class SetLimitIn(BaseModel):
    """Входная схема для установки дневного лимита пользователя."""
    telegram_id: int
    daily_limit: float = Field(gt=0)


class WorkspaceCreateIn(BaseModel):
    """Входная схема для создания нового пространства."""
    telegram_id: int
    name: str = Field(min_length=1, max_length=128)
    type: WorkspaceType = WorkspaceType.shared
    base_currency: str = Field(default="RUB", min_length=3, max_length=8)


class WorkspaceOut(BaseModel):
    """Выходная схема с данными пространства."""
    id: int
    name: str
    type: WorkspaceType
    base_currency: str
    owner_telegram_id: int
    is_archived: bool
    my_role: MemberRole | None = None
    is_active: bool = False


class WorkspaceMemberAddIn(BaseModel):
    """Входная схема для добавления участника в пространство."""
    telegram_id: int
    member_identifier: str
    role: MemberRole = MemberRole.editor


class WorkspaceMemberUpdateIn(BaseModel):
    """Входная схема для изменения роли участника пространства."""
    telegram_id: int
    role: MemberRole


class WorkspaceMemberOut(BaseModel):
    """Выходная схема с данными участника пространства."""
    telegram_id: int
    username: str | None
    role: MemberRole


class WorkspaceSetActiveIn(BaseModel):
    """Входная схема для выбора активного пространства."""
    telegram_id: int
    workspace_id: int


class CategoryCreateIn(BaseModel):
    """Входная схема для создания категории."""
    telegram_id: int
    workspace_id: int | None = None
    name: str = Field(min_length=1, max_length=64)
    type: OperationType
    emoji: str | None = Field(default=None, max_length=16)


class CategoryUpdateIn(BaseModel):
    """Входная схема для обновления категории."""
    telegram_id: int
    name: str | None = Field(default=None, min_length=1, max_length=64)
    emoji: str | None = Field(default=None, max_length=16)
    is_archived: bool | None = None


class CategoryOut(BaseModel):
    """Выходная схема с данными категории."""
    id: int
    workspace_id: int
    name: str
    type: OperationType
    emoji: str | None
    is_archived: bool


class CategoryAliasCreateIn(BaseModel):
    """Входная схема для добавления ключевого слова категории."""
    telegram_id: int
    alias: str = Field(min_length=1, max_length=64)


class CategoryAliasDeleteIn(BaseModel):
    """Входная схема для удаления ключевого слова категории."""
    telegram_id: int


class CategoryAliasOut(BaseModel):
    """Выходная схема с данными ключевого слова категории."""
    id: int
    category_id: int
    alias: str
    normalized_alias: str


class CategoryMatchIn(BaseModel):
    """Входная схема для подбора категории по тексту."""
    telegram_id: int
    workspace_id: int | None = None
    text: str = Field(min_length=1, max_length=255)
    type: OperationType


class CategoryMatchOut(BaseModel):
    """Выходная схема с результатом подбора категории."""
    matched: bool
    category: CategoryOut | None = None
    reason: str | None = None


class OperationCreateIn(BaseModel):
    """Входная схема для создания операции."""
    telegram_id: int
    workspace_id: int | None = None
    user_telegram_id: int | None = None
    actor_telegram_id: int | None = None
    type: Literal["income", "expense"]
    amount: float = Field(gt=0)
    currency: str = Field(default="RUB", min_length=3, max_length=8)
    category: str | None = None
    comment: str | None = None
    source: str | None = None
    merchant: str | None = None
    external_ref: str | None = None
    is_imported: bool = False
    receipt_upload_id: int | None = None
    statement_import_id: int | None = None
    occurred_at: date | None = None


class OperationOut(BaseModel):
    """Выходная схема с данными операции."""
    id: int
    workspace_id: int
    user_telegram_id: int | None = None
    actor_telegram_id: int | None = None
    user_username: str | None = None
    actor_username: str | None = None
    type: str
    amount: float
    currency: str
    category: str | None = None
    comment: str | None = None
    source: str | None = None
    occurred_at: date


class OperationUpdateIn(BaseModel):
    """Входная схема для изменения операции."""
    telegram_id: int
    workspace_id: int | None = None
    amount: float | None = Field(default=None, gt=0)
    currency: str | None = Field(default=None, min_length=3, max_length=8)
    comment: str | None = None
    category: str | None = None
    occurred_at: date | None = None


class DeleteResult(BaseModel):
    """Схема ответа для успешного удаления сущности."""
    deleted: bool


class LimitCheckOut(BaseModel):
    """Схема результата проверки дневного лимита после добавления операции."""
    limit_exceeded: bool
    daily_limit: float | None
    day_expenses_total: float


class LimitAlertOut(BaseModel):
    """Схема уведомления о достижении порога бюджетного лимита."""
    limit_id: int
    scope: LimitScope
    period: LimitPeriod
    threshold: int
    amount: float
    spent: float
    remaining: float
    currency: str
    label: str


class BudgetLimitCreateIn(BaseModel):
    """Входная схема для создания бюджетного лимита."""
    telegram_id: int
    workspace_id: int | None = None
    scope: LimitScope
    period: LimitPeriod
    amount: float = Field(gt=0)
    currency: str = Field(default="RUB", min_length=3, max_length=8)
    user_telegram_id: int | None = None
    category_id: int | None = None
    notify_at_50: bool = True
    notify_at_80: bool = True
    notify_at_100: bool = True


class BudgetLimitOut(BaseModel):
    """Выходная схема с данными бюджетного лимита."""
    id: int
    workspace_id: int
    scope: LimitScope
    period: LimitPeriod
    amount: float
    currency: str
    user_telegram_id: int | None = None
    category_id: int | None = None
    is_active: bool


class BudgetLimitStatusOut(BaseModel):
    """Выходная схема со статусом использования бюджетного лимита."""
    id: int
    workspace_id: int
    scope: LimitScope
    period: LimitPeriod
    amount: float
    currency: str
    spent: float
    remaining: float
    percent_used: float
    user_telegram_id: int | None = None
    category_id: int | None = None
    category_name: str | None = None
    label: str
    is_active: bool


class ReportScheduleUpsertIn(BaseModel):
    """Входная схема для создания или обновления расписания отчёта."""
    telegram_id: int
    workspace_id: int | None = None
    user_telegram_id: int | None = None
    frequency: str = Field(default="monthly", max_length=32)
    day_of_month: int = Field(default=1, ge=1, le=31)
    send_time: str = Field(default="09:00", pattern=r"^\d{2}:\d{2}$")
    timezone: str = Field(default="Europe/Moscow", max_length=64)
    enabled: bool = True


class ReportScheduleOut(BaseModel):
    """Выходная схема с данными расписания отчёта."""
    id: int
    workspace_id: int
    user_telegram_id: int | None = None
    frequency: str
    day_of_month: int
    send_time: str
    timezone: str
    enabled: bool


class DueReportScheduleOut(BaseModel):
    """Выходная схема с расписанием отчёта, которое нужно отправить сейчас."""
    id: int
    workspace_id: int
    telegram_id: int
    frequency: str
    day_of_month: int
    send_time: str
    timezone: str
    enabled: bool


class ReceiptUploadCreateIn(BaseModel):
    """Входная схема для создания записи о загруженном чеке."""
    telegram_id: int
    workspace_id: int | None = None
    original_filename: str | None = None
    telegram_file_id: str | None = None
    storage_path: str | None = None


class ReceiptUploadOut(BaseModel):
    """Выходная схема с данными загруженного чека."""
    id: int
    workspace_id: int
    status: ImportStatus
    original_filename: str | None
    telegram_file_id: str | None
    storage_path: str | None
    parsed_total: float | None = None
    parsed_currency: str | None = None
    parsed_merchant: str | None = None
    parsed_date: date | None = None
    raw_text: str | None = None
    error_message: str | None = None


class ReceiptParseIn(BaseModel):
    """Входная схема для сохранения результата распознавания чека."""
    telegram_id: int
    parsed_total: float | None = Field(default=None, gt=0)
    parsed_currency: str | None = Field(default=None, min_length=3, max_length=8)
    parsed_merchant: str | None = None
    parsed_date: date | None = None
    raw_text: str | None = None
    error_message: str | None = None
    status: ImportStatus = ImportStatus.parsed


class ReceiptConfirmIn(BaseModel):
    """Входная схема для подтверждения операции по чеку."""
    telegram_id: int
    category: str | None = None
    comment: str | None = None
    currency: str | None = Field(default=None, min_length=3, max_length=8)
    amount: float | None = Field(default=None, gt=0)
    occurred_at: date | None = None


class StatementImportCreateIn(BaseModel):
    """Входная схема для создания записи импорта банковской выписки."""
    telegram_id: int
    workspace_id: int | None = None
    original_filename: str | None = None
    file_type: str | None = None
    summary_text: str | None = None


class StatementImportOut(BaseModel):
    """Выходная схема с данными импорта банковской выписки."""
    id: int
    workspace_id: int
    status: ImportStatus
    original_filename: str | None
    file_type: str | None
    imported_rows: int
    skipped_rows: int
    summary_text: str | None
    error_message: str | None = None


class StatementImportCompleteIn(BaseModel):
    """Входная схема для завершения импорта банковской выписки."""
    telegram_id: int
    imported_rows: int = Field(default=0, ge=0)
    skipped_rows: int = Field(default=0, ge=0)
    summary_text: str | None = None
    error_message: str | None = None
    status: ImportStatus = ImportStatus.confirmed
