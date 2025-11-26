"""Database models for auto-posting system."""

from datetime import datetime
from enum import Enum
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class PostStatus(str, Enum):
    """Post status enumeration."""
    DRAFT = "draft"
    QUEUED = "queued"
    APPROVED = "approved"
    PUBLISHED = "published"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScheduleMode(str, Enum):
    """Schedule mode enumeration."""
    FIXED = "fixed"
    RANDOM = "random"
    INTERVAL = "interval"


class PublishStatus(str, Enum):
    """Publication status enumeration."""
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"


class AutoPostChannel(Base):
    """Auto-posting channel model."""
    __tablename__ = 'autopost_channels'
    
    id = Column(Integer, primary_key=True)  # Telegram channel ID
    name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Settings stored as JSON
    settings = Column(JSON, default={})
    # {
    #   "auto_publish": true,
    #   "require_moderation": false,
    #   "default_style": "professional",
    #   "default_language": "ru",
    #   "post_frequency": 3
    # }
    
    # Relationships
    posts = relationship("AutoPost", back_populates="channel", cascade="all, delete-orphan")
    schedules = relationship("AutoPostSchedule", back_populates="channel", cascade="all, delete-orphan")
    publications = relationship("AutoPostPublication", back_populates="channel", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<AutoPostChannel(id={self.id}, name='{self.name}', active={self.is_active})>"


class AutoPost(Base):
    """Auto-post model."""
    __tablename__ = 'autopost_posts'
    
    id = Column(String(36), primary_key=True)  # UUID
    channel_id = Column(Integer, ForeignKey('autopost_channels.id'), nullable=False)
    content = Column(Text, nullable=False)
    status = Column(String(20), default=PostStatus.DRAFT.value)
    
    # Media and formatting stored as JSON
    media = Column(JSON, default=[])
    # [{"type": "photo", "url": "...", "caption": "..."}]
    
    buttons = Column(JSON, default=[])
    # [{"text": "Click", "url": "https://..."}]
    
    hashtags = Column(JSON, default=[])
    # ["#tech", "#news"]
    
    # Metadata
    theme = Column(String(255))
    style = Column(JSON, default={})
    # {"tone": "professional", "length": "medium", "format": "news"}
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    scheduled_for = Column(DateTime, nullable=True)
    published_at = Column(DateTime, nullable=True)
    
    # Priority for queue ordering
    priority = Column(Integer, default=0)
    
    # Relationships
    channel = relationship("AutoPostChannel", back_populates="posts")
    publications = relationship("AutoPostPublication", back_populates="post", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<AutoPost(id='{self.id}', channel_id={self.channel_id}, status='{self.status}')>"


class AutoPostSchedule(Base):
    """Auto-posting schedule model."""
    __tablename__ = 'autopost_schedules'
    
    id = Column(String(36), primary_key=True)  # UUID
    channel_id = Column(Integer, ForeignKey('autopost_channels.id'), nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Schedule configuration stored as JSON
    config = Column(JSON, nullable=False)
    # {
    #   "mode": "fixed",
    #   "time_slots": ["09:00", "15:00", "21:00"],
    #   "days_of_week": [0, 1, 2, 3, 4],  # Monday-Friday
    #   "random_range": [30, 120]  # minutes
    # }
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    last_run = Column(DateTime, nullable=True)
    next_run = Column(DateTime, nullable=True)
    
    # Relationships
    channel = relationship("AutoPostChannel", back_populates="schedules")
    
    def __repr__(self):
        return f"<AutoPostSchedule(id='{self.id}', channel_id={self.channel_id}, active={self.is_active})>"


class AutoPostPublication(Base):
    """Publication record model."""
    __tablename__ = 'autopost_publications'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_id = Column(Integer, ForeignKey('autopost_channels.id'), nullable=False)
    post_id = Column(String(36), ForeignKey('autopost_posts.id'), nullable=True)
    
    status = Column(String(20), nullable=False)
    published_at = Column(DateTime, default=datetime.utcnow)
    
    # Error information
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    
    # Telegram message ID (if published successfully)
    telegram_message_id = Column(Integer, nullable=True)
    
    # Relationships
    channel = relationship("AutoPostChannel", back_populates="publications")
    post = relationship("AutoPost", back_populates="publications")
    
    def __repr__(self):
        return f"<AutoPostPublication(id={self.id}, channel_id={self.channel_id}, status='{self.status}')>"


class ContentSource(Base):
    """Content source model (RSS, topics, files)."""
    __tablename__ = 'content_sources'
    
    id = Column(String(36), primary_key=True)  # UUID
    type = Column(String(20), nullable=False)  # rss, topics, file
    name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=0)
    
    # Source data stored as JSON
    data = Column(JSON, nullable=False)
    # For RSS: {"url": "https://..."}
    # For topics: {"topics": ["topic1", "topic2"]}
    # For file: {"path": "/path/to/file", "format": "json"}
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime, nullable=True)
    use_count = Column(Integer, default=0)
    
    def __repr__(self):
        return f"<ContentSource(id='{self.id}', type='{self.type}', name='{self.name}')>"
