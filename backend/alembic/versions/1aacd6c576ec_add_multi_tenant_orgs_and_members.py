"""add_multi_tenant_orgs_and_members

Revision ID: 1aacd6c576ec
Revises:
Create Date: 2026-04-12

Adds multi-tenancy:
  - New `orgs` table
  - New `org_members` junction table
  - `cases.org_id`, `cases.assigned_to`, `cases.visibility` columns

Handles two starting states:
  1. Fresh DB — creates all tables
  2. Existing DB (from create_all) — idempotent CREATE IF NOT EXISTS
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "1aacd6c576ec"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(name: str) -> bool:
    bind = op.get_bind()
    return sa.inspect(bind).has_table(name)


def _has_column(table: str, column: str) -> bool:
    bind = op.get_bind()
    cols = [c["name"] for c in sa.inspect(bind).get_columns(table)]
    return column in cols


def upgrade() -> None:
    # ── orgs table ──
    if not _has_table("orgs"):
        op.create_table(
            "orgs",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("slug", sa.String(), nullable=False, unique=True),
            sa.Column("display_name", sa.String(), nullable=False),
            sa.Column("contact_email", sa.String(), nullable=True),
            sa.Column("settings_json", sa.Text(), nullable=True, server_default="{}"),
            sa.Column("status", sa.String(), nullable=True, server_default="active"),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.Column("deleted_at", sa.DateTime(), nullable=True),
        )
        op.create_index("ix_orgs_slug", "orgs", ["slug"], unique=True)

    # ── org_members junction table ──
    if not _has_table("org_members"):
        op.create_table(
            "org_members",
            sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), primary_key=True),
            sa.Column("org_id", sa.String(), sa.ForeignKey("orgs.id"), primary_key=True),
            sa.Column("role", sa.String(), nullable=False, server_default="caseworker"),
            sa.Column("joined_at", sa.DateTime(), nullable=True),
            sa.Column("invited_by", sa.String(), sa.ForeignKey("users.id"), nullable=True),
        )
        op.create_index("ix_org_members_org_id", "org_members", ["org_id"])
        op.create_index("ix_org_members_user_id", "org_members", ["user_id"])

    # ── cases new columns ──
    # Use batch mode for SQLite compatibility
    with op.batch_alter_table("cases") as batch:
        if not _has_column("cases", "org_id"):
            batch.add_column(sa.Column("org_id", sa.String(), nullable=True))
        if not _has_column("cases", "assigned_to"):
            batch.add_column(sa.Column("assigned_to", sa.String(), nullable=True))
        if not _has_column("cases", "visibility"):
            batch.add_column(sa.Column("visibility", sa.String(), nullable=True, server_default="private"))

    # Backfill visibility for existing rows (NULL → 'private')
    op.execute("UPDATE cases SET visibility = 'private' WHERE visibility IS NULL")

    # FKs via batch (skip if already present — we're idempotent)
    with op.batch_alter_table("cases") as batch:
        try:
            batch.create_foreign_key("fk_cases_org", "orgs", ["org_id"], ["id"])
        except Exception:
            pass
        try:
            batch.create_foreign_key("fk_cases_assignee", "users", ["assigned_to"], ["id"])
        except Exception:
            pass


def downgrade() -> None:
    with op.batch_alter_table("cases") as batch:
        try:
            batch.drop_constraint("fk_cases_assignee", type_="foreignkey")
        except Exception:
            pass
        try:
            batch.drop_constraint("fk_cases_org", type_="foreignkey")
        except Exception:
            pass
        if _has_column("cases", "visibility"):
            batch.drop_column("visibility")
        if _has_column("cases", "assigned_to"):
            batch.drop_column("assigned_to")
        if _has_column("cases", "org_id"):
            batch.drop_column("org_id")

    if _has_table("org_members"):
        op.drop_index("ix_org_members_user_id", table_name="org_members")
        op.drop_index("ix_org_members_org_id", table_name="org_members")
        op.drop_table("org_members")

    if _has_table("orgs"):
        op.drop_index("ix_orgs_slug", table_name="orgs")
        op.drop_table("orgs")
