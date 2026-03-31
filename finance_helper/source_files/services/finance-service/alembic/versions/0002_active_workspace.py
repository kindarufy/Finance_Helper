
"""add active workspace to users

Revision ID: 0002_active_workspace
Revises: 0001_release_foundation
Create Date: 2026-03-30
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_active_workspace"
down_revision = "0001_release_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Выполняет действие «upgrade» в рамках логики Finance Helper."""
    op.add_column("users", sa.Column("active_workspace_id", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_users_active_workspace_id"), "users", ["active_workspace_id"], unique=False)
    op.create_foreign_key(
        "fk_users_active_workspace_id_workspaces",
        "users",
        "workspaces",
        ["active_workspace_id"],
        ["id"],
    )


def downgrade() -> None:
    """Выполняет действие «downgrade» в рамках логики Finance Helper."""
    op.drop_constraint("fk_users_active_workspace_id_workspaces", "users", type_="foreignkey")
    op.drop_index(op.f("ix_users_active_workspace_id"), table_name="users")
    op.drop_column("users", "active_workspace_id")
