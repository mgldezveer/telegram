"""Модели для источников социальных сетей и веб-скрапинга."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import String, Integer, Boolean, DateTime, Text, JSON, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.models.base import Base


class SocialMediaSource(Base):
    """Модель для источников социальных сетей (Twitter, Facebook, Instagram, LinkedIn)."""
    __tablename__ = 'social_media_sources'
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # UUID
    channel_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('channels.id'), nullable=True)
    platform: Mapped[str] = mapped_column(String(20), nullable=False)  # twitter, facebook, instagram, linkedin
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    
    # Configuration data stored as JSON
    config: Mapped[dict] = mapped_column(JSON, nullable=False)
    # For Twitter: {"api_key": "...", "api_secret": "...", "access_token": "...", "access_token_secret": "...", "account": "..."}
    # For Facebook: {"access_token": "...", "page_id": "..."}
    # For Instagram: {"access_token": "...", "account_id": "..."}
    # For LinkedIn: {"access_token": "...", "organization_id": "..."}
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_used: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_post_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # ID последнего поста
    use_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    channel: Mapped[Optional["Channel"]] = relationship("Channel", back_populates="social_media_sources")
    
    def __repr__(self):
        return f"<SocialMediaSource(id='{self.id}', platform='{self.platform}', name='{self.name}')>"


class WebScrapingSource(Base):
    """Модель для источников веб-скрапинга."""
    __tablename__ = 'web_scraping_sources'
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # UUID
    channel_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('channels.id'), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    
    # Configuration data stored as JSON
    config: Mapped[dict] = mapped_column(JSON, nullable=False)
    # {"url": "...", "selector": "...", "type": "rss|html|json", "headers": {}, "scraping_method": "beautifulsoup|selenium"}
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_used: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_scraped_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    use_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    channel: Mapped[Optional["Channel"]] = relationship("Channel", back_populates="web_scraping_sources")
    
    def __repr__(self):
        return f"<WebScrapingSource(id='{self.id}', name='{self.name}')>"


class ContentQuality(Base):
    """Модель для хранения результатов анализа качества контента."""
    __tablename__ = 'content_quality'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    post_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)  # ID поста
    content: Mapped[str] = mapped_column(Text, nullable=False)
    score: Mapped[float] = mapped_column(Integer, nullable=False)  # 0-100
    issues: Mapped[dict] = mapped_column(JSON, nullable=True) # Словарь проблем
    is_compliant: Mapped[bool] = mapped_column(Boolean, default=True)  # Соответствует ли требованиям
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<ContentQuality(post_id='{self.post_id}', score={self.score}, compliant={self.is_compliant})>"


class EngagementMetrics(Base):
    """Модель для хранения метрик вовлеченности."""
    __tablename__ = 'engagement_metrics'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    channel_id: Mapped[int] = mapped_column(Integer, ForeignKey('channels.id'), nullable=False)
    post_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)  # ID поста
    message_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # ID сообщения в Telegram
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Метрики
    views: Mapped[int] = mapped_column(Integer, default=0)
    likes: Mapped[int] = mapped_column(Integer, default=0)
    shares: Mapped[int] = mapped_column(Integer, default=0)
    comments: Mapped[int] = mapped_column(Integer, default=0)
    clicks: Mapped[int] = mapped_column(Integer, default=0)
    reach: Mapped[int] = mapped_column(Integer, default=0)
    
    # Дополнительные метрики
    engagement_rate: Mapped[float] = mapped_column(Float, default=0.0)
    ctr: Mapped[float] = mapped_column(Float, default=0.0)  # Click-through rate
    
    def __repr__(self):
        return f"<EngagementMetrics(post_id='{self.post_id}', channel_id={self.channel_id}, views={self.views})>"


class AnalyticsSchedule(Base):
    """Модель для аналитики расписания."""
    __tablename__ = 'analytics_schedules'
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # UUID
    channel_id: Mapped[int] = mapped_column(Integer, ForeignKey('channels.id'), nullable=False)
    schedule_type: Mapped[str] = mapped_column(String(50), nullable=False)  # analytics_based, ab_testing
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Configuration data stored as JSON
    config: Mapped[dict] = mapped_column(JSON, nullable=False)
    # For AnalyticsBased: {"metric": "engagement_rate", "min_value": 0.05, "max_posts_per_day": 5}
    # For A/B Testing: {"test_group": "A", "variant": "title_style", "sample_size": 1000}
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_run: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    next_run: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    channel: Mapped["Channel"] = relationship("Channel", back_populates="analytics_schedules")
    
    def __repr__(self):
        return f"<AnalyticsSchedule(id='{self.id}', type='{self.schedule_type}', channel_id={self.channel_id})>"