"""Channel model."""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Boolean, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.models.base import Base


class Channel(Base):
    """Channel model with support for both manual and auto-posting."""
    __tablename__ = "channels"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Configuration for auto-posting
    autopost_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    autopost_frequency: Mapped[int] = mapped_column(Integer, default=3)  # posts per day
    autopost_optimal_times: Mapped[list] = mapped_column(JSON, default=list)  # list of time strings
    autopost_themes: Mapped[list] = mapped_column(JSON, default=list)
    
    # Content style
    style_tone: Mapped[str] = mapped_column(String(50), default="professional")
    style_length: Mapped[str] = mapped_column(String(50), default="medium")
    emoji_usage: Mapped[bool] = mapped_column(Boolean, default=True)
    hashtag_count: Mapped[int] = mapped_column(Integer, default=3)
    media_preference: Mapped[str] = mapped_column(String(50), default="text")
    
    # Moderation settings
    require_moderation: Mapped[bool] = mapped_column(Boolean, default=True)
    auto_publish: Mapped[bool] = mapped_column(Boolean, default=False)
    default_language: Mapped[str] = mapped_column(String(10), default="ru")
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    archived_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Relationships
    posts: Mapped[list["Post"]] = relationship("Post", back_populates="channel")
    autopost_schedules: Mapped[list["AutoPostSchedule"]] = relationship("AutoPostSchedule", back_populates="channel")
    content_sources: Mapped[list["ContentSource"]] = relationship("ContentSource", back_populates="channel")
    
    def __repr__(self) -> str:
        return f"<Channel(id={self.id}, name={self.name}, active={self.active})>"