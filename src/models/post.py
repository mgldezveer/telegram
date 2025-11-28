"""Post model."""

from datetime import datetime
from enum import Enum
from typing import Optional
from sqlalchemy import String, Integer, Text, DateTime, JSON, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.models.base import Base


class PostStatus(str, Enum):
    """Unified post status enumeration."""
    DRAFT = "draft"
    VALIDATED = "validated"
    QUEUED = "queued"
    APPROVED = "approved"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"
    RETRYING = "retrying"


class PostType(str, Enum):
    """Post type enumeration."""
    MANUAL = "manual"
    AUTOMATED = "automated"


class Post(Base):
    """Unified post model supporting both manual and auto-posting."""
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
    post_type: Mapped[PostType] = mapped_column(
        SQLEnum(PostType),
        default=PostType.MANUAL,
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    scheduled_for: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Metadata for auto-posting
    autopost_id: Mapped[Optional[str]] = mapped_column(String(36))  # For linking to original autopost
    autopost_priority: Mapped[int] = mapped_column(Integer, default=0)
    autopost_source: Mapped[Optional[str]] = mapped_column(String(100))  # For content source
    
    # Media and formatting stored as JSON
    media_data: Mapped[list] = mapped_column(JSON, default=list)  # Extended media support
    buttons: Mapped[list] = mapped_column(JSON, default=list)  # Interactive buttons
    style_tone: Mapped[Optional[str]] = mapped_column(String(50))
    style_length: Mapped[Optional[str]] = mapped_column(String(50))
    theme: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Error information for failed posts
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Telegram message ID (if published successfully)
    telegram_message_id: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Relationships
    channel: Mapped["Channel"] = relationship("Channel", back_populates="posts")
    metrics: Mapped[Optional["Metrics"]] = relationship("Metrics", back_populates="post", uselist=False)
    autopost_publications: Mapped[list["AutoPostPublication"]] = relationship("AutoPostPublication", back_populates="post")
    
    def __repr__(self) -> str:
        return f"<Post(id={self.id}, channel_id={self.channel_id}, status={self.status}, type={self.post_type})>"