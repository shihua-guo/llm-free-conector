from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Channel(Base):
    __tablename__ = "channels"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    external_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), default="")
    channel_type: Mapped[str] = mapped_column(String(128), default="")
    status: Mapped[str] = mapped_column(String(64), default="")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    raw: Mapped[dict] = mapped_column(JSONB, default=dict)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ProviderModel(Base):
    __tablename__ = "provider_models"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    model_name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    capability: Mapped[str] = mapped_column(String(64), index=True)
    family: Mapped[str] = mapped_column(String(128), default="")
    source: Mapped[str] = mapped_column(String(128), default="newapi")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    default_priority: Mapped[int] = mapped_column(Integer, default=1000, index=True)
    manual_priority: Mapped[int | None] = mapped_column(Integer, index=True)
    raw: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ChannelModel(Base):
    __tablename__ = "channel_models"
    __table_args__ = (
        UniqueConstraint("channel_external_id", "model_name", name="uq_channel_model"),
        Index("ix_channel_models_model_enabled", "model_name", "enabled"),
    )

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    channel_external_id: Mapped[str] = mapped_column(
        String(128), ForeignKey("channels.external_id", ondelete="CASCADE"), index=True
    )
    model_name: Mapped[str] = mapped_column(
        String(255), ForeignKey("provider_models.model_name", ondelete="CASCADE"), index=True
    )
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    raw: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class InvocationAttempt(Base):
    __tablename__ = "invocation_attempts"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    request_id: Mapped[str] = mapped_column(String(64), index=True)
    requested_model: Mapped[str] = mapped_column(String(255), index=True)
    routed_model: Mapped[str] = mapped_column(String(255), index=True)
    capability: Mapped[str] = mapped_column(String(64), index=True)
    status_code: Mapped[int | None] = mapped_column(Integer)
    success: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    error: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
