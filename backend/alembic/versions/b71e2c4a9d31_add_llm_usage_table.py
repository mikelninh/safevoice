"""add_llm_usage_table

Revision ID: b71e2c4a9d31
Revises: 1aacd6c576ec
Create Date: 2026-05-18

Adds the `llm_usage` table — one row per LLM call routed through
`app.services.llm_gateway`. Captures token counts and estimated cost so a
cross-project dashboard (SafeVoice + GitLaw) can aggregate spend.

Idempotent — uses CREATE IF NOT EXISTS via inspector check, matching the
style of 1aacd6c576ec.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "b71e2c4a9d31"
down_revision: Union[str, Sequence[str], None] = "1aacd6c576ec"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(name: str) -> bool:
    bind = op.get_bind()
    return sa.inspect(bind).has_table(name)


def upgrade() -> None:
    if not _has_table("llm_usage"):
        op.create_table(
            "llm_usage",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("ts", sa.DateTime(), nullable=False),
            sa.Column("case_id", sa.String(), sa.ForeignKey("cases.id"), nullable=True),
            sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("route", sa.String(), nullable=False),
            sa.Column("model", sa.String(), nullable=False),
            sa.Column(
                "prompt_tokens", sa.Integer(), nullable=False, server_default="0"
            ),
            sa.Column(
                "completion_tokens", sa.Integer(), nullable=False, server_default="0"
            ),
            sa.Column("total_tokens", sa.Integer(), nullable=False, server_default="0"),
            sa.Column(
                "estimated_cost_usd", sa.Float(), nullable=False, server_default="0"
            ),
            sa.Column("request_id", sa.String(), nullable=False),
        )
        op.create_index("ix_llm_usage_ts", "llm_usage", ["ts"])
        op.create_index("ix_llm_usage_case_id", "llm_usage", ["case_id"])
        op.create_index("ix_llm_usage_user_id", "llm_usage", ["user_id"])
        op.create_index("ix_llm_usage_route", "llm_usage", ["route"])
        op.create_index("ix_llm_usage_model", "llm_usage", ["model"])
        op.create_index("ix_llm_usage_request_id", "llm_usage", ["request_id"])


def downgrade() -> None:
    if _has_table("llm_usage"):
        for ix in (
            "ix_llm_usage_request_id",
            "ix_llm_usage_model",
            "ix_llm_usage_route",
            "ix_llm_usage_user_id",
            "ix_llm_usage_case_id",
            "ix_llm_usage_ts",
        ):
            try:
                op.drop_index(ix, table_name="llm_usage")
            except Exception:
                pass
        op.drop_table("llm_usage")
