"""add_agent_runs_and_tool_calls

Revision ID: c8a3f2e7d4b9
Revises: b71e2c4a9d31
Create Date: 2026-05-19

Adds `agent_runs` (one row per agent invocation) and `tool_calls`
(one row per tool execution inside a run) for the agent-loop introduced
in services/agent_loop.py.

Also adds `agent_run_id` to `llm_usage` so the cost dashboard can
aggregate one agent run as a single line item across its 6-7 LLM hops.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "c8a3f2e7d4b9"
down_revision: Union[str, Sequence[str], None] = "b71e2c4a9d31"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(name: str) -> bool:
    bind = op.get_bind()
    return sa.inspect(bind).has_table(name)


def _has_column(table: str, column: str) -> bool:
    bind = op.get_bind()
    cols = {c["name"] for c in sa.inspect(bind).get_columns(table)}
    return column in cols


def upgrade() -> None:
    if not _has_table("agent_runs"):
        op.create_table(
            "agent_runs",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("agent_name", sa.String(), nullable=False),
            sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("case_id", sa.String(), sa.ForeignKey("cases.id"), nullable=True),
            sa.Column("status", sa.String(), nullable=False, server_default="running"),
            sa.Column("input_json", sa.Text(), nullable=False),
            sa.Column("output_json", sa.Text(), nullable=True),
            sa.Column(
                "total_iterations", sa.Integer(), nullable=False, server_default="0"
            ),
            sa.Column("total_cost_usd", sa.Float(), nullable=False, server_default="0"),
            sa.Column("error", sa.Text(), nullable=True),
            sa.Column("started_at", sa.DateTime(), nullable=False),
            sa.Column("completed_at", sa.DateTime(), nullable=True),
        )
        op.create_index("ix_agent_runs_agent_name", "agent_runs", ["agent_name"])
        op.create_index("ix_agent_runs_user_id", "agent_runs", ["user_id"])
        op.create_index("ix_agent_runs_case_id", "agent_runs", ["case_id"])
        op.create_index("ix_agent_runs_status", "agent_runs", ["status"])

    if not _has_table("tool_calls"):
        op.create_table(
            "tool_calls",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column(
                "agent_run_id",
                sa.String(),
                sa.ForeignKey("agent_runs.id"),
                nullable=False,
            ),
            sa.Column("tool_name", sa.String(), nullable=False),
            sa.Column("input_json", sa.Text(), nullable=False),
            sa.Column("output_json", sa.Text(), nullable=True),
            sa.Column("input_hash", sa.String(), nullable=False),
            sa.Column("latency_ms", sa.Integer(), nullable=True, server_default="0"),
            sa.Column("cost_usd", sa.Float(), nullable=True, server_default="0"),
            sa.Column(
                "cached", sa.Boolean(), nullable=False, server_default=sa.text("false")
            ),
            sa.Column("error", sa.Text(), nullable=True),
            sa.Column("called_at", sa.DateTime(), nullable=False),
        )
        op.create_index("ix_tool_calls_agent_run_id", "tool_calls", ["agent_run_id"])
        op.create_index("ix_tool_calls_tool_name", "tool_calls", ["tool_name"])
        op.create_index("ix_tool_calls_input_hash", "tool_calls", ["input_hash"])

    if _has_table("llm_usage") and not _has_column("llm_usage", "agent_run_id"):
        op.add_column(
            "llm_usage",
            sa.Column(
                "agent_run_id",
                sa.String(),
                sa.ForeignKey("agent_runs.id"),
                nullable=True,
            ),
        )
        op.create_index("ix_llm_usage_agent_run_id", "llm_usage", ["agent_run_id"])


def downgrade() -> None:
    if _has_table("llm_usage") and _has_column("llm_usage", "agent_run_id"):
        try:
            op.drop_index("ix_llm_usage_agent_run_id", table_name="llm_usage")
        except Exception:
            pass
        op.drop_column("llm_usage", "agent_run_id")

    if _has_table("tool_calls"):
        for ix in (
            "ix_tool_calls_input_hash",
            "ix_tool_calls_tool_name",
            "ix_tool_calls_agent_run_id",
        ):
            try:
                op.drop_index(ix, table_name="tool_calls")
            except Exception:
                pass
        op.drop_table("tool_calls")

    if _has_table("agent_runs"):
        for ix in (
            "ix_agent_runs_status",
            "ix_agent_runs_case_id",
            "ix_agent_runs_user_id",
            "ix_agent_runs_agent_name",
        ):
            try:
                op.drop_index(ix, table_name="agent_runs")
            except Exception:
                pass
        op.drop_table("agent_runs")
