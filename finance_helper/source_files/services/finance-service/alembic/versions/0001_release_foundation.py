"""Миграция Alembic, которая создаёт базовую структуру таблиц релизной версии Finance Helper."""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0001_release_foundation"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Создаёт таблицы и перечисления, необходимые для релизной версии Finance Helper."""
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(length=128), nullable=True),
        sa.Column("daily_limit", sa.Numeric(12, 2), nullable=True),
        sa.Column("notify_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("base_currency", sa.String(length=8), nullable=False, server_default="RUB"),
        sa.Column("timezone", sa.String(length=64), nullable=False, server_default="Europe/Moscow"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("telegram_id"),
    )
    op.create_index(op.f("ix_users_telegram_id"), "users", ["telegram_id"], unique=False)

    op.create_table(
        "workspaces",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("owner_user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("type", sa.Enum("personal", "shared", "trip", "project", name="workspace_type", native_enum=False), nullable=False),
        sa.Column("base_currency", sa.String(length=8), nullable=False, server_default="RUB"),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_workspaces_owner_user_id"), "workspaces", ["owner_user_id"], unique=False)

    op.create_table(
        "workspace_members",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("workspace_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.Enum("owner", "editor", "viewer", name="member_role", native_enum=False), nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workspace_id", "user_id", name="uq_workspace_member"),
    )
    op.create_index(op.f("ix_workspace_members_workspace_id"), "workspace_members", ["workspace_id"], unique=False)
    op.create_index(op.f("ix_workspace_members_user_id"), "workspace_members", ["user_id"], unique=False)

    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("workspace_id", sa.Integer(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("type", sa.Enum("income", "expense", name="operation_type", native_enum=False), nullable=False),
        sa.Column("emoji", sa.String(length=16), nullable=True),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workspace_id", "type", "name", name="uq_workspace_category_name"),
    )
    op.create_index(op.f("ix_categories_workspace_id"), "categories", ["workspace_id"], unique=False)
    op.create_index(op.f("ix_categories_name"), "categories", ["name"], unique=False)

    op.create_table(
        "category_aliases",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("workspace_id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("alias", sa.String(length=64), nullable=False),
        sa.Column("normalized_alias", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"]),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workspace_id", "normalized_alias", name="uq_workspace_alias"),
    )
    op.create_index(op.f("ix_category_aliases_workspace_id"), "category_aliases", ["workspace_id"], unique=False)
    op.create_index(op.f("ix_category_aliases_category_id"), "category_aliases", ["category_id"], unique=False)

    op.create_table(
        "receipt_uploads",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("workspace_id", sa.Integer(), nullable=False),
        sa.Column("uploaded_by_user_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.Enum("uploaded", "parsed", "confirmed", "failed", name="import_status", native_enum=False), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=True),
        sa.Column("telegram_file_id", sa.String(length=255), nullable=True),
        sa.Column("storage_path", sa.String(length=255), nullable=True),
        sa.Column("parsed_total", sa.Numeric(12, 2), nullable=True),
        sa.Column("parsed_currency", sa.String(length=8), nullable=True),
        sa.Column("parsed_merchant", sa.String(length=255), nullable=True),
        sa.Column("parsed_date", sa.Date(), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["uploaded_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_receipt_uploads_workspace_id"), "receipt_uploads", ["workspace_id"], unique=False)
    op.create_index(op.f("ix_receipt_uploads_uploaded_by_user_id"), "receipt_uploads", ["uploaded_by_user_id"], unique=False)

    op.create_table(
        "statement_imports",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("workspace_id", sa.Integer(), nullable=False),
        sa.Column("uploaded_by_user_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.Enum("uploaded", "parsed", "confirmed", "failed", name="statement_import_status", native_enum=False), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=True),
        sa.Column("file_type", sa.String(length=32), nullable=True),
        sa.Column("imported_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("skipped_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("summary_text", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["uploaded_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_statement_imports_workspace_id"), "statement_imports", ["workspace_id"], unique=False)
    op.create_index(op.f("ix_statement_imports_uploaded_by_user_id"), "statement_imports", ["uploaded_by_user_id"], unique=False)

    op.create_table(
        "operations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("workspace_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("type", sa.Enum("income", "expense", name="operation_type_value", native_enum=False), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False, server_default="RUB"),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.Column("source", sa.String(length=64), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("merchant", sa.String(length=255), nullable=True),
        sa.Column("external_ref", sa.String(length=255), nullable=True),
        sa.Column("is_imported", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("receipt_upload_id", sa.Integer(), nullable=True),
        sa.Column("statement_import_id", sa.Integer(), nullable=True),
        sa.Column("occurred_at", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"]),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["receipt_upload_id"], ["receipt_uploads.id"]),
        sa.ForeignKeyConstraint(["statement_import_id"], ["statement_imports.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_operations_workspace_id"), "operations", ["workspace_id"], unique=False)
    op.create_index(op.f("ix_operations_user_id"), "operations", ["user_id"], unique=False)
    op.create_index(op.f("ix_operations_created_by_user_id"), "operations", ["created_by_user_id"], unique=False)

    op.create_table(
        "budget_limits",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("workspace_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.Column("scope", sa.Enum("workspace", "user", "category", name="limit_scope", native_enum=False), nullable=False),
        sa.Column("period", sa.Enum("daily", "monthly", name="limit_period", native_enum=False), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False, server_default="RUB"),
        sa.Column("notify_at_50", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("notify_at_80", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("notify_at_100", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_budget_limits_workspace_id"), "budget_limits", ["workspace_id"], unique=False)
    op.create_index(op.f("ix_budget_limits_user_id"), "budget_limits", ["user_id"], unique=False)
    op.create_index(op.f("ix_budget_limits_category_id"), "budget_limits", ["category_id"], unique=False)

    op.create_table(
        "report_schedules",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("workspace_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("frequency", sa.String(length=32), nullable=False, server_default="monthly"),
        sa.Column("day_of_month", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("send_time", sa.String(length=5), nullable=False, server_default="09:00"),
        sa.Column("timezone", sa.String(length=64), nullable=False, server_default="Europe/Moscow"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_report_schedules_workspace_id"), "report_schedules", ["workspace_id"], unique=False)
    op.create_index(op.f("ix_report_schedules_user_id"), "report_schedules", ["user_id"], unique=False)


def downgrade() -> None:
    """Откатывает базовую миграцию релизной версии."""
    op.drop_index(op.f("ix_report_schedules_user_id"), table_name="report_schedules")
    op.drop_index(op.f("ix_report_schedules_workspace_id"), table_name="report_schedules")
    op.drop_table("report_schedules")

    op.drop_index(op.f("ix_budget_limits_category_id"), table_name="budget_limits")
    op.drop_index(op.f("ix_budget_limits_user_id"), table_name="budget_limits")
    op.drop_index(op.f("ix_budget_limits_workspace_id"), table_name="budget_limits")
    op.drop_table("budget_limits")

    op.drop_index(op.f("ix_operations_created_by_user_id"), table_name="operations")
    op.drop_index(op.f("ix_operations_user_id"), table_name="operations")
    op.drop_index(op.f("ix_operations_workspace_id"), table_name="operations")
    op.drop_table("operations")

    op.drop_index(op.f("ix_statement_imports_uploaded_by_user_id"), table_name="statement_imports")
    op.drop_index(op.f("ix_statement_imports_workspace_id"), table_name="statement_imports")
    op.drop_table("statement_imports")

    op.drop_index(op.f("ix_receipt_uploads_uploaded_by_user_id"), table_name="receipt_uploads")
    op.drop_index(op.f("ix_receipt_uploads_workspace_id"), table_name="receipt_uploads")
    op.drop_table("receipt_uploads")

    op.drop_index(op.f("ix_category_aliases_category_id"), table_name="category_aliases")
    op.drop_index(op.f("ix_category_aliases_workspace_id"), table_name="category_aliases")
    op.drop_table("category_aliases")

    op.drop_index(op.f("ix_categories_name"), table_name="categories")
    op.drop_index(op.f("ix_categories_workspace_id"), table_name="categories")
    op.drop_table("categories")

    op.drop_index(op.f("ix_workspace_members_user_id"), table_name="workspace_members")
    op.drop_index(op.f("ix_workspace_members_workspace_id"), table_name="workspace_members")
    op.drop_table("workspace_members")

    op.drop_index(op.f("ix_workspaces_owner_user_id"), table_name="workspaces")
    op.drop_table("workspaces")

    op.drop_index(op.f("ix_users_telegram_id"), table_name="users")
    op.drop_table("users")
