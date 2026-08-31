"""Initial schema with pgvector extension."""

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "schemes",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("name", sa.String(512), nullable=False),
        sa.Column("short_description", sa.Text(), nullable=False),
        sa.Column("full_description", sa.Text(), nullable=False),
        sa.Column(
            "government_level",
            sa.Enum("central", "state", "both", name="government_level"),
            nullable=False,
        ),
        sa.Column("ministry", sa.String(256)),
        sa.Column("category", sa.String(128), nullable=False),
        sa.Column("applicable_states", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("benefits", sa.JSON(), nullable=False),
        sa.Column("required_documents", sa.JSON(), nullable=False),
        sa.Column("application_process", sa.Text(), nullable=False),
        sa.Column("application_url", sa.String(1024)),
        sa.Column("official_source_url", sa.String(1024), nullable=False),
        sa.Column("keywords", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("verified_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_schemes_name", "schemes", ["name"])
    op.create_index("ix_schemes_category", "schemes", ["category"])
    op.create_index("ix_schemes_is_active", "schemes", ["is_active"])

    op.create_table(
        "eligibility_rules",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("scheme_id", sa.String(32), sa.ForeignKey("schemes.id", ondelete="CASCADE")),
        sa.Column("field", sa.String(64), nullable=False),
        sa.Column("operator", sa.String(16), nullable=False),
        sa.Column("value", sa.JSON(), nullable=False),
        sa.Column("is_required", sa.Boolean(), default=True),
        sa.Column("description", sa.Text()),
    )
    op.create_index("ix_eligibility_rules_scheme_id", "eligibility_rules", ["scheme_id"])

    op.create_table(
        "scheme_documents",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("scheme_id", sa.String(32), sa.ForeignKey("schemes.id", ondelete="CASCADE")),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), default=0),
        sa.Column("source_url", sa.String(1024), nullable=False),
        sa.Column("embedding", Vector(1536)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_scheme_documents_scheme_id", "scheme_documents", ["scheme_id"])

    op.create_table(
        "query_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("user_query", sa.Text(), nullable=False),
        sa.Column("extracted_profile", sa.JSON()),
        sa.Column("recommendations", sa.JSON()),
        sa.Column("response_text", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("query_sessions")
    op.drop_table("scheme_documents")
    op.drop_table("eligibility_rules")
    op.drop_table("schemes")
    op.execute("DROP TYPE IF EXISTS government_level")
