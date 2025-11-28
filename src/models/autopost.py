"""Unified auto-posting models extending the base models."""

from datetime import datetime
from enum import Enum
from typing import Optional, List
from sqlalchemy import String, Integer, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.models.base import Base
from src.models.post import Post, PostStatus


class ScheduleMode(str, Enum):
    """Schedule mode enumeration."""
    FIXED = "fixed"
    RANDOM = "random"
    INTERVAL = "interval"


class AutoPostSchedule(Base):
    """Auto-posting schedule model."""
    __tablename__ = 'autopost_schedules'
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # UUID
    channel_id: Mapped[int] = mapped_column(Integer, ForeignKey('channels.id'), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Schedule configuration stored as JSON
    config: Mapped[dict] = mapped_column(JSON, nullable=False)
    # {
    #   "mode": "fixed",
    #   "time_slots": ["09:0", "15:00", "21:00"],
    #   "days_of_week": [0, 1, 2, 3, 4],  # Monday-Friday
    #   "random_range": [30, 120]  # minutes
    # }
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_run: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    next_run: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    channel: Mapped["Channel"] = relationship("Channel", back_populates="autopost_schedules")
    
    def __repr__(self):
        return f"<AutoPostSchedule(id='{self.id}', channel_id={self.channel_id}, active={self.is_active})>"


class AutoPostPublication(Base):
    """Publication record model."""
    __tablename__ = 'autopost_publications'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    channel_id: Mapped[int] = mapped_column(Integer, ForeignKey('channels.id'), nullable=False)
    post_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('posts.id'), nullable=True)
    
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Error information
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Telegram message ID (if published successfully)
    telegram_message_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Relationships
    channel: Mapped["Channel"] = relationship("Channel", back_populates="posts")  # Using posts as placeholder
    post: Mapped[Optional["Post"]] = relationship("Post", back_populates="autopost_publications")
    
    def __repr__(self):
        return f"<AutoPostPublication(id={self.id}, channel_id={self.channel_id}, status='{self.status}')>"


class ContentSource(Base):
    """Content source model (RSS, topics, files)."""
    __tablename__ = 'content_sources'
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # UUID
    channel_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('channels.id'), nullable=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False)  # rss, topics, file
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    
    # Source data stored as JSON
    data: Mapped[dict] = mapped_column(JSON, nullable=False)
    # For RSS: {"url": "https://..."}
    # For topics: {"topics": ["topic1", "topic2"]}
    # For file: {"path": "/path/to/file", "format": "json"}
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_used: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    use_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    channel: Mapped[Optional["Channel"]] = relationship("Channel", back_populates="content_sources")
    
    def __repr__(self):
        return f"<ContentSource(id='{self.id}', type='{self.type}', name='{self.name}')>"