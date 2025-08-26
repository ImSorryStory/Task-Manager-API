from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# ревизия
revision = "0001_create_tasks"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "tasks",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.String(length=2000), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
    )
    op.create_index("ix_tasks_status_title", "tasks", ["status", "title"])
    op.create_index(op.f("ix_tasks_title"), "tasks", ["title"])
    op.create_index(op.f("ix_tasks_status"), "tasks", ["status"])


def downgrade():
    op.drop_index(op.f("ix_tasks_status"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_title"), table_name="tasks")
    op.drop_index("ix_tasks_status_title", table_name="tasks")
    op.drop_table("tasks")
