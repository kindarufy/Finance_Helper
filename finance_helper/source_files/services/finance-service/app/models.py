"""Модуль финансового сервиса Finance Helper."""
from __future__ import annotations

from enum import Enum

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class OperationType(str, Enum):
    """Класс «OperationType» описывает состояние или структуру данных данного модуля."""
    income = "income"
    expense = "expense"


class WorkspaceType(str, Enum):
    """Класс «WorkspaceType» описывает состояние или структуру данных данного модуля."""
    personal = "personal"
    shared = "shared"
    trip = "trip"
    project = "project"


class MemberRole(str, Enum):
    """Класс «MemberRole» описывает состояние или структуру данных данного модуля."""
    owner = "owner"
    editor = "editor"
    viewer = "viewer"


class LimitPeriod(str, Enum):
    """Класс «LimitPeriod» описывает состояние или структуру данных данного модуля."""
    daily = "daily"
    monthly = "monthly"


class LimitScope(str, Enum):
    """Класс «LimitScope» описывает состояние или структуру данных данного модуля."""
    workspace = "workspace"
    user = "user"
    category = "category"


class ImportStatus(str, Enum):
    """Класс «ImportStatus» описывает состояние или структуру данных данного модуля."""
    uploaded = "uploaded"
    parsed = "parsed"
    confirmed = "confirmed"
    failed = "failed"


class User(Base):
    """Класс «User» описывает состояние или структуру данных данного модуля."""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(128), nullable=True)
    daily_limit: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    notify_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    base_currency: Mapped[str] = mapped_column(String(8), default="RUB", nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), default="Europe/Moscow", nullable=False)
    active_workspace_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("workspaces.id"), nullable=True, index=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

    created_workspaces: Mapped[list["Workspace"]] = relationship(
        back_populates="owner",
        foreign_keys="Workspace.owner_user_id",
    )
    active_workspace: Mapped["Workspace | None"] = relationship(
        foreign_keys=[active_workspace_id],
        post_update=True,
    )
    memberships: Mapped[list["WorkspaceMember"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    created_categories: Mapped[list["Category"]] = relationship(
        back_populates="created_by_user",
        foreign_keys="Category.created_by_user_id",
    )
    operations_as_subject: Mapped[list["Operation"]] = relationship(
        back_populates="subject_user",
        foreign_keys="Operation.user_id",
    )
    operations_as_creator: Mapped[list["Operation"]] = relationship(
        back_populates="created_by_user",
        foreign_keys="Operation.created_by_user_id",
    )


class Workspace(Base):
    """Класс «Workspace» описывает состояние или структуру данных данного модуля."""
    __tablename__ = "workspaces"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    owner_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    type: Mapped[WorkspaceType] = mapped_column(
        SAEnum(WorkspaceType, name="workspace_type", native_enum=False),
        default=WorkspaceType.personal,
        nullable=False,
    )
    base_currency: Mapped[str] = mapped_column(String(8), default="RUB", nullable=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

    owner: Mapped["User"] = relationship(back_populates="created_workspaces", foreign_keys=[owner_user_id])
    members: Mapped[list["WorkspaceMember"]] = relationship(back_populates="workspace", cascade="all, delete-orphan")
    categories: Mapped[list["Category"]] = relationship(back_populates="workspace", cascade="all, delete-orphan")
    operations: Mapped[list["Operation"]] = relationship(back_populates="workspace", cascade="all, delete-orphan")
    limits: Mapped[list["BudgetLimit"]] = relationship(back_populates="workspace", cascade="all, delete-orphan")
    report_schedules: Mapped[list["ReportSchedule"]] = relationship(
        back_populates="workspace",
        cascade="all, delete-orphan",
    )
    receipt_uploads: Mapped[list["ReceiptUpload"]] = relationship(
        back_populates="workspace",
        cascade="all, delete-orphan",
    )
    statement_imports: Mapped[list["StatementImport"]] = relationship(
        back_populates="workspace",
        cascade="all, delete-orphan",
    )


class WorkspaceMember(Base):
    """Класс «WorkspaceMember» описывает состояние или структуру данных данного модуля."""
    __tablename__ = "workspace_members"
    __table_args__ = (UniqueConstraint("workspace_id", "user_id", name="uq_workspace_member"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    workspace_id: Mapped[int] = mapped_column(Integer, ForeignKey("workspaces.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    role: Mapped[MemberRole] = mapped_column(
        SAEnum(MemberRole, name="member_role", native_enum=False),
        default=MemberRole.owner,
        nullable=False,
    )
    joined_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

    workspace: Mapped["Workspace"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship(back_populates="memberships")


class Category(Base):
    """Класс «Category» описывает состояние или структуру данных данного модуля."""
    __tablename__ = "categories"
    __table_args__ = (UniqueConstraint("workspace_id", "type", "name", name="uq_workspace_category_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    workspace_id: Mapped[int] = mapped_column(Integer, ForeignKey("workspaces.id"), nullable=False, index=True)
    created_by_user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    type: Mapped[OperationType] = mapped_column(
        SAEnum(OperationType, name="operation_type", native_enum=False),
        nullable=False,
    )
    emoji: Mapped[str | None] = mapped_column(String(16), nullable=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

    workspace: Mapped["Workspace"] = relationship(back_populates="categories")
    created_by_user: Mapped["User | None"] = relationship(back_populates="created_categories")
    aliases: Mapped[list["CategoryAlias"]] = relationship(back_populates="category", cascade="all, delete-orphan")
    operations: Mapped[list["Operation"]] = relationship(back_populates="category")
    limits: Mapped[list["BudgetLimit"]] = relationship(back_populates="category")


class CategoryAlias(Base):
    """Класс «CategoryAlias» описывает состояние или структуру данных данного модуля."""
    __tablename__ = "category_aliases"
    __table_args__ = (UniqueConstraint("workspace_id", "normalized_alias", name="uq_workspace_alias"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    workspace_id: Mapped[int] = mapped_column(Integer, ForeignKey("workspaces.id"), nullable=False, index=True)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey("categories.id"), nullable=False, index=True)
    alias: Mapped[str] = mapped_column(String(64), nullable=False)
    normalized_alias: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

    category: Mapped["Category"] = relationship(back_populates="aliases")


class ReceiptUpload(Base):
    """Класс «ReceiptUpload» описывает состояние или структуру данных данного модуля."""
    __tablename__ = "receipt_uploads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    workspace_id: Mapped[int] = mapped_column(Integer, ForeignKey("workspaces.id"), nullable=False, index=True)
    uploaded_by_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    status: Mapped[ImportStatus] = mapped_column(
        SAEnum(ImportStatus, name="import_status", native_enum=False),
        default=ImportStatus.uploaded,
        nullable=False,
    )
    original_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    telegram_file_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    storage_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    parsed_total: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    parsed_currency: Mapped[str | None] = mapped_column(String(8), nullable=True)
    parsed_merchant: Mapped[str | None] = mapped_column(String(255), nullable=True)
    parsed_date: Mapped[str | None] = mapped_column(Date, nullable=True)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
    confirmed_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)

    workspace: Mapped["Workspace"] = relationship(back_populates="receipt_uploads")


class StatementImport(Base):
    """Класс «StatementImport» описывает состояние или структуру данных данного модуля."""
    __tablename__ = "statement_imports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    workspace_id: Mapped[int] = mapped_column(Integer, ForeignKey("workspaces.id"), nullable=False, index=True)
    uploaded_by_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    status: Mapped[ImportStatus] = mapped_column(
        SAEnum(ImportStatus, name="statement_import_status", native_enum=False),
        default=ImportStatus.uploaded,
        nullable=False,
    )
    original_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    imported_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    skipped_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    summary_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
    confirmed_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)

    workspace: Mapped["Workspace"] = relationship(back_populates="statement_imports")
    operations: Mapped[list["Operation"]] = relationship(back_populates="statement_import")


class Operation(Base):
    """Класс «Operation» описывает состояние или структуру данных данного модуля."""
    __tablename__ = "operations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    workspace_id: Mapped[int] = mapped_column(Integer, ForeignKey("workspaces.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_by_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    type: Mapped[OperationType] = mapped_column(
        SAEnum(OperationType, name="operation_type_value", native_enum=False),
        nullable=False,
    )
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="RUB", nullable=False)
    category_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("categories.id"), nullable=True)
    source: Mapped[str | None] = mapped_column(String(64), nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    merchant: Mapped[str | None] = mapped_column(String(255), nullable=True)
    external_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_imported: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    receipt_upload_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("receipt_uploads.id"), nullable=True)
    statement_import_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("statement_imports.id"), nullable=True)
    occurred_at: Mapped[str] = mapped_column(Date, nullable=False)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

    workspace: Mapped["Workspace"] = relationship(back_populates="operations")
    subject_user: Mapped["User"] = relationship(back_populates="operations_as_subject", foreign_keys=[user_id])
    created_by_user: Mapped["User"] = relationship(
        back_populates="operations_as_creator",
        foreign_keys=[created_by_user_id],
    )
    category: Mapped["Category | None"] = relationship(back_populates="operations")
    statement_import: Mapped["StatementImport | None"] = relationship(back_populates="operations")


class BudgetLimit(Base):
    """Класс «BudgetLimit» описывает состояние или структуру данных данного модуля."""
    __tablename__ = "budget_limits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    workspace_id: Mapped[int] = mapped_column(Integer, ForeignKey("workspaces.id"), nullable=False, index=True)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    category_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("categories.id"), nullable=True, index=True)
    scope: Mapped[LimitScope] = mapped_column(
        SAEnum(LimitScope, name="limit_scope", native_enum=False),
        nullable=False,
    )
    period: Mapped[LimitPeriod] = mapped_column(
        SAEnum(LimitPeriod, name="limit_period", native_enum=False),
        nullable=False,
    )
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="RUB", nullable=False)
    notify_at_50: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notify_at_80: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notify_at_100: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

    workspace: Mapped["Workspace"] = relationship(back_populates="limits")
    category: Mapped["Category | None"] = relationship(back_populates="limits")


class ReportSchedule(Base):
    """Класс «ReportSchedule» описывает состояние или структуру данных данного модуля."""
    __tablename__ = "report_schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    workspace_id: Mapped[int] = mapped_column(Integer, ForeignKey("workspaces.id"), nullable=False, index=True)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    frequency: Mapped[str] = mapped_column(String(32), default="monthly", nullable=False)
    day_of_month: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    send_time: Mapped[str] = mapped_column(String(5), default="09:00", nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), default="Europe/Moscow", nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

    workspace: Mapped["Workspace"] = relationship(back_populates="report_schedules")
