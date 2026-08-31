import enum
from datetime import datetime
from typing import Any
from uuid import uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.database import Base


class GovernmentLevel(str, enum.Enum):
    CENTRAL = "central"
    STATE = "state"
    BOTH = "both"


class EligibilityStatus(str, enum.Enum):
    LIKELY_ELIGIBLE = "likely_eligible"
    POSSIBLY_ELIGIBLE = "possibly_eligible"
    NOT_ELIGIBLE = "not_eligible"
    INSUFFICIENT_INFO = "insufficient_info"


class Scheme(Base):
    __tablename__ = "schemes"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    short_description: Mapped[str] = mapped_column(Text, nullable=False)
    full_description: Mapped[str] = mapped_column(Text, nullable=False)
    government_level: Mapped[GovernmentLevel] = mapped_column(
        Enum(GovernmentLevel, name="government_level"),
        nullable=False,
    )
    ministry: Mapped[str | None] = mapped_column(String(256))
    category: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    applicable_states: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        default=list,
    )
    benefits: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    required_documents: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    application_process: Mapped[str] = mapped_column(Text, nullable=False)
    application_url: Mapped[str | None] = mapped_column(String(1024))
    official_source_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    keywords: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    eligibility_rules: Mapped[list["EligibilityRule"]] = relationship(
        back_populates="scheme",
        cascade="all, delete-orphan",
    )
    documents: Mapped[list["SchemeDocument"]] = relationship(
        back_populates="scheme",
        cascade="all, delete-orphan",
    )


class EligibilityRule(Base):
    __tablename__ = "eligibility_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scheme_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("schemes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    field: Mapped[str] = mapped_column(String(64), nullable=False)
    operator: Mapped[str] = mapped_column(String(16), nullable=False)
    value: Mapped[Any] = mapped_column(JSON, nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, default=True)
    description: Mapped[str | None] = mapped_column(Text)

    scheme: Mapped["Scheme"] = relationship(back_populates="eligibility_rules")


class SchemeDocument(Base):
    __tablename__ = "scheme_documents"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    scheme_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("schemes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, default=0)
    source_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    scheme: Mapped["Scheme"] = relationship(back_populates="documents")


class QuerySession(Base):
    __tablename__ = "query_sessions"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    user_query: Mapped[str] = mapped_column(Text, nullable=False)
    extracted_profile: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    recommendations: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON)
    response_text: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
