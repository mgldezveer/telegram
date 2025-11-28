from sqlalchemy import Column, Integer, String, DateTime, JSON, Boolean, Text
from sqlalchemy.sql import func
from ..database.base import Base
from datetime import datetime


class EnhancedContentSource(Base):
    """
    Расширенная модель источника контента для системы автопостинга.
    Поддерживает различные типы источников: RSS, API социальных сетей,
    веб-скрепинг, файлы и другие.
    """
    __tablename__ = 'enhanced_content_sources'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    source_type = Column(String(50), nullable=False)  # 'rss', 'twitter_api', 'facebook_api', 'instagram_api', 'linkedin_api', 'web_scraping', 'file'
    source_config = Column(JSON, nullable=False)  # Конфигурация для конкретного типа источника
    is_active = Column(Boolean, default=True)
    last_fetch_time = Column(DateTime, default=func.now())
    next_fetch_time = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    fetch_interval = Column(Integer, default=3600)  # Интервал в секундах
    content_filter = Column(JSON)  # Фильтры для контента
    content_transformations = Column(JSON)  # Трансформации контента перед публикацией

    def __repr__(self):
        return f"<EnhancedContentSource(id={self.id}, name='{self.name}', type='{self.source_type}', is_active={self.is_active})>"

    def validate_config(self):
        """
        Проверяет валидность конфигурации источника в зависимости от типа
        """
        if self.source_type == 'rss':
            return 'url' in self.source_config
        elif self.source_type in ['twitter_api', 'facebook_api', 'instagram_api', 'linkedin_api']:
            required_fields = ['api_key', 'api_secret']
            return all(field in self.source_config for field in required_fields)
        elif self.source_type == 'web_scraping':
            return 'url' in self.source_config and 'selectors' in self.source_config
        elif self.source_type == 'file':
            return 'path' in self.source_config
        return False


class ContentModerationRecord(Base):
    """
    Модель для хранения записей модерации контента
    """
    __tablename__ = 'content_moderation_records'

    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(String(255), nullable=False)  # Уникальный ID контента
    source_id = Column(Integer, nullable=False)  # ID источника контента
    content_title = Column(String(500))
    content_body = Column(Text)
    moderation_status = Column(String(50), default='pending')  # 'pending', 'approved', 'rejected'
    moderation_result = Column(JSON)  # Результаты проверки качества, соответствия и т.д.
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    moderator_id = Column(Integer)  # ID модератора (если применимо)
    rejection_reason = Column(Text)  # Причина отклонения

    def __repr__(self):
        return f"<ContentModerationRecord(id={self.id}, content_id='{self.content_id}', status='{self.moderation_status}')>"


class EngagementMetrics(Base):
    """
    Модель для хранения метрик вовлеченности
    """
    __tablename__ = 'engagement_metrics'

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(String(255), nullable=False)  # ID поста в системе
    channel_id = Column(String(255), nullable=False)  # ID канала
    timestamp = Column(DateTime, default=func.now())
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    saves = Column(Integer, default=0)
    reach = Column(Integer, default=0)  # Охват
    impressions = Column(Integer, default=0)  # Показы
    ctr = Column(Integer, default=0)  # Click-through rate в промилле
    engagement_rate = Column(Integer, default=0)  # Вовлеченность в промилле
    source_type = Column(String(50))  # Тип источника контента
    content_category = Column(String(100))  # Категория контента

    def __repr__(self):
        return f"<EngagementMetrics(post_id='{self.post_id}', channel_id='{self.channel_id}', views={self.views}, likes={self.likes})>"


class MediaContent(Base):
    """
    Модель для хранения информации о мультимедийном контенте
    """
    __tablename__ = 'media_content'

    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(String(255), nullable=False)  # ID связанного контента
    media_type = Column(String(50), nullable=False)  # 'image', 'video', 'audio', 'document'
    media_url = Column(String(500))  # URL медиафайла
    local_path = Column(String(500))  # Локальный путь к файлу
    file_size = Column(Integer)  # Размер файла в байтах
    duration = Column(Integer)  # Длительность для аудио/видео в секундах
    width = Column(Integer)  # Ширина для изображений/видео
    height = Column(Integer)  # Высота для изображений/видео
    created_at = Column(DateTime, default=func.now())
    is_generated = Column(Boolean, default=False)  # Сгенерировано ли с помощью ИИ

    def __repr__(self):
        return f"<MediaContent(id={self.id}, content_id='{self.content_id}', type='{self.media_type}')>"