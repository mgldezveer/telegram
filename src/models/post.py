"""Post model."""

from datetime import datetime
from enum import Enum
from typing import Optional
from sqlalchemy import String, Integer, Text, DateTime, JSON, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.models.base import Base


class PostStatus(str, Enum):
    """Post status enumeration."""
    DRAFT = "draft"
    VALIDATED = "validated"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"
    ARCHIVED = "archived"


class Post(Base):
    """Post model."""
    __tablename__ = "posts"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    media_url: Mapped[Optional[str]] = mapped_column(String(500))
    media_type: Mapped[Optional[str]] = mapped_column(String(50))
    hashtags: Mapped[list] = mapped_column(JSON, default=list)
    channel_id: Mapped[int] = mapped_column(Integer, ForeignKey("channels.id"), nullable=False)
    status: Mapped[PostStatus] = mapped_column(
        SQLEnum(PostStatus),
        default=PostStatus.DRAFT,
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    scheduled_for: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Metadata
    style_tone: Mapped[Optional[str]] = mapped_column(String(50))
    style_length: Mapped[Optional[str]] = mapped_column(String(50))
    theme: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Relationships
    channel: Mapped["Channel"] = relationship("Channel", back_populates="posts")
    metrics: Mapped[Optional["Metrics"]] = relationship("Metrics", back_populates="post", uselist=False)
    
    def __repr__(self) -> str:
        return f"<Post(id={self.id}, channel_id={self.channel_id}, status={self.status})>"
