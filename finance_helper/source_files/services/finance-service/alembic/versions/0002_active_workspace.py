
"""Миграция Alembic, которая добавляет пользователю поле активного пространства."""

from alembic import op
import sqlalchemy as sa


revision = "0002_active_workspace"
down_revision = "0001_release_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Добавляет пользователю ссылку на активное пространство."""
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
    """Удаляет поле активного пространства у пользователя."""
    op.drop_constraint("fk_users_active_workspace_id_workspaces", "users", type_="foreignkey")
    op.drop_index(op.f("ix_users_active_workspace_id"), table_name="users")
    op.drop_column("users", "active_workspace_id")
