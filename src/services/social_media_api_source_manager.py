"""Менеджер источников социальных сетей с интеграцией с API Twitter, Facebook, Instagram и LinkedIn."""

import logging
import uuid
import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
import aiohttp
from sqlalchemy import select, update

from src.models.social_media_source import SocialMediaSource
from src.database.autopost_db import autopost_db


@dataclass
class SocialMediaPost:
    """Пост из социальной сети."""
    id: str
    platform: str
    content: str
    author: str
    timestamp: datetime
    media_urls: List[str] = None
    likes_count: int = 0
    shares_count: int = 0
    comments_count: int = 0
    url: str = None


class SocialMediaAPISourceManager:
    """Менеджер источников социальных сетей с интеграцией с API Twitter, Facebook, Instagram и LinkedIn."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.session = None
        self.platform_handlers = {
            'twitter': self._fetch_twitter_posts,
            'facebook': self._fetch_facebook_posts,
            'instagram': self._fetch_instagram_posts,
            'linkedin': self._fetch_linkedin_posts
        }
    
    async def initialize(self):
        """Инициализировать асинхронную сессию."""
        self.session = aiohttp.ClientSession()
    
    async def close(self):
        """Закрыть асинхронную сессию."""
        if self.session:
            await self.session.close()
    
    async def add_twitter_source(
        self, 
        name: str, 
        api_key: str, 
        api_secret: str, 
        access_token: str, 
        access_token_secret: str, 
        account: str,
        channel_id: Optional[int] = None,
        priority: int = 0
    ) -> str:
        """Добавить источник Twitter.
        
        Args:
            name: Название источника
            api_key: Ключ API Twitter
            api_secret: Секретный ключ API Twitter
            access_token: Токен доступа
            access_token_secret: Секретный токен доступа
            account: Имя аккаунта Twitter
            channel_id: ID канала (опционально)
            priority: Приоритет источника
            
        Returns:
            ID созданного источника
        """
        try:
            source_id = str(uuid.uuid4())
            async with autopost_db.session() as session:
                source = SocialMediaSource(
                    id=source_id,
                    channel_id=channel_id,
                    platform="twitter",
                    name=name,
                    is_active=True,
                    priority=priority,
                    config={
                        "api_key": api_key,
                        "api_secret": api_secret,
                        "access_token": access_token,
                        "access_token_secret": access_token_secret,
                        "account": account
                    },
                    created_at=datetime.utcnow()
                )
                session.add(source)
                await session.commit()
                
                self.logger.info(f"✅ Added Twitter source: {name}")
                return source_id
        except Exception as e:
            self.logger.error(f"❌ Failed to add Twitter source: {e}")
            raise
    
    async def add_facebook_source(
        self,
        name: str,
        access_token: str,
        page_id: str,
        channel_id: Optional[int] = None,
        priority: int = 0
    ) -> str:
        """Добавить источник Facebook.
        
        Args:
            name: Название источника
            access_token: Токен доступа к Facebook
            page_id: ID страницы Facebook
            channel_id: ID канала (опционально)
            priority: Приоритет источника
            
        Returns:
            ID созданного источника
        """
        try:
            source_id = str(uuid.uuid4())
            async with autopost_db.session() as session:
                source = SocialMediaSource(
                    id=source_id,
                    channel_id=channel_id,
                    platform="facebook",
                    name=name,
                    is_active=True,
                    priority=priority,
                    config={
                        "access_token": access_token,
                        "page_id": page_id
                    },
                    created_at=datetime.utcnow()
                )
                session.add(source)
                await session.commit()
                
                self.logger.info(f"✅ Added Facebook source: {name}")
                return source_id
        except Exception as e:
            self.logger.error(f"❌ Failed to add Facebook source: {e}")
            raise
    
    async def add_instagram_source(
        self,
        name: str,
        access_token: str,
        account_id: str,
        channel_id: Optional[int] = None,
        priority: int = 0
    ) -> str:
        """Добавить источник Instagram.
        
        Args:
            name: Название источника
            access_token: Токен доступа к Instagram
            account_id: ID аккаунта Instagram
            channel_id: ID канала (опционально)
            priority: Приоритет источника
            
        Returns:
            ID созданного источника
        """
        try:
            source_id = str(uuid.uuid4())
            async with autopost_db.session() as session:
                source = SocialMediaSource(
                    id=source_id,
                    channel_id=channel_id,
                    platform="instagram",
                    name=name,
                    is_active=True,
                    priority=priority,
                    config={
                        "access_token": access_token,
                        "account_id": account_id
                    },
                    created_at=datetime.utcnow()
                )
                session.add(source)
                await session.commit()
                
                self.logger.info(f"✅ Added Instagram source: {name}")
                return source_id
        except Exception as e:
            self.logger.error(f"❌ Failed to add Instagram source: {e}")
            raise
    
    async def add_linkedin_source(
        self,
        name: str,
        access_token: str,
        organization_id: str,
        channel_id: Optional[int] = None,
        priority: int = 0
    ) -> str:
        """Добавить источник LinkedIn.
        
        Args:
            name: Название источника
            access_token: Токен доступа к LinkedIn
            organization_id: ID организации LinkedIn
            channel_id: ID канала (опционально)
            priority: Приоритет источника
            
        Returns:
            ID созданного источника
        """
        try:
            source_id = str(uuid.uuid4())
            async with autopost_db.session() as session:
                source = SocialMediaSource(
                    id=source_id,
                    channel_id=channel_id,
                    platform="linkedin",
                    name=name,
                    is_active=True,
                    priority=priority,
                    config={
                        "access_token": access_token,
                        "organization_id": organization_id
                    },
                    created_at=datetime.utcnow()
                )
                session.add(source)
                await session.commit()
                
                self.logger.info(f"✅ Added LinkedIn source: {name}")
                return source_id
        except Exception as e:
            self.logger.error(f"❌ Failed to add LinkedIn source: {e}")
            raise
    
    async def get_next_content(self, platform: str = None) -> Optional[SocialMediaPost]:
        """Получить следующий контент из источников социальных сетей.
        
        Args:
            platform: Платформа для фильтрации (опционально)
            
        Returns:
            Пост из социальной сети или None
        """
        try:
            async with autopost_db.session() as session:
                query = select(SocialMediaSource).where(SocialMediaSource.is_active == True)
                if platform:
                    query = query.where(SocialMediaSource.platform == platform)
                
                result = await session.execute(
                    query.order_by(
                        SocialMediaSource.priority.desc(), 
                        SocialMediaSource.use_count.asc()
                    ).limit(1)
                )
                source = result.scalar_one_or_none()
                
                if not source:
                    return None
                
                # Обновить использование
                source.use_count += 1
                source.last_used = datetime.utcnow()
                await session.commit()
                
                # Получить посты из соответствующей платформы
                if source.platform in self.platform_handlers:
                    posts = await self.platform_handlers[source.platform](source)
                    if posts:
                        # Вернуть первый пост
                        return posts[0]
                
                return None
        except Exception as e:
            self.logger.error(f"❌ Failed to get next content: {e}")
            return None
    
    async def _fetch_twitter_posts(self, source: SocialMediaSource) -> List[SocialMediaPost]:
        """Получить посты из Twitter.
        
        Args:
            source: Источник Twitter
            
        Returns:
            Список постов
        """
        try:
            # В реальной реализации здесь будет вызов Twitter API v2
            # Пока что возвращаем заглушку
            config = source.config
            headers = {
                "Authorization": f"Bearer {config['access_token']}",
                "User-Agent": "v2RecentSearchPython"
            }
            
            # URL для получения твитов пользователя (заменить на нужный эндпоинт)
            url = f"https://api.twitter.com/2/users/by/username/{config['account']}"
            
            # Заглушка - в реальности нужно получить ID пользователя, а затем его твиты
            # url = f"https://api.twitter.com/2/users/{user_id}/tweets"
            
            # Пока возвращаем тестовые данные
            return [
                SocialMediaPost(
                    id="test_twitter_post_1",
                    platform="twitter",
                    content="Тестовый твит для проверки интеграции",
                    author=config['account'],
                    timestamp=datetime.utcnow(),
                    likes_count=10,
                    shares_count=2,
                    comments_count=1,
                    url="https://twitter.com/test/status/1234567890"
                )
            ]
        except Exception as e:
            self.logger.error(f"❌ Failed to fetch Twitter posts: {e}")
            return []
    
    async def _fetch_facebook_posts(self, source: SocialMediaSource) -> List[SocialMediaPost]:
        """Получить посты из Facebook.
        
        Args:
            source: Источник Facebook
            
        Returns:
            Список постов
        """
        try:
            # В реальной реализации здесь будет вызов Facebook Graph API
            # Пока что возвращаем заглушку
            config = source.config
            url = f"https://graph.facebook.com/v18.0/{config['page_id']}/posts"
            params = {
                "access_token": config['access_token'],
                "fields": "id,message,created_time,likes.summary(true),comments.summary(true),shares"
            }
            
            # Пока возвращаем тестовые данные
            return [
                SocialMediaPost(
                    id="test_facebook_post_1",
                    platform="facebook",
                    content="Тестовый пост Facebook для проверки интеграции",
                    author=config['page_id'],
                    timestamp=datetime.utcnow(),
                    likes_count=25,
                    shares_count=5,
                    comments_count=3,
                    url=f"https://facebook.com/{config['page_id']}/posts/123456"
                )
            ]
        except Exception as e:
            self.logger.error(f"❌ Failed to fetch Facebook posts: {e}")
            return []
    
    async def _fetch_instagram_posts(self, source: SocialMediaSource) -> List[SocialMediaPost]:
        """Получить посты из Instagram.
        
        Args:
            source: Источник Instagram
            
        Returns:
            Список постов
        """
        try:
            # В реальной реализации здесь будет вызов Instagram Basic Display API
            # Пока что возвращаем заглушку
            config = source.config
            url = f"https://graph.instagram.com/v18.0/{config['account_id']}/media"
            params = {
                "access_token": config['access_token'],
                "fields": "id,caption,media_type,media_url,permalink,timestamp,like_count,comments_count"
            }
            
            # Пока возвращаем тестовые данные
            return [
                SocialMediaPost(
                    id="test_instagram_post_1",
                    platform="instagram",
                    content="Тестовый пост Instagram для проверки интеграции",
                    author=config['account_id'],
                    timestamp=datetime.utcnow(),
                    likes_count=42,
                    shares_count=7,
                    comments_count=5,
                    url="https://instagram.com/p/ABC123/"
                )
            ]
        except Exception as e:
            self.logger.error(f"❌ Failed to fetch Instagram posts: {e}")
            return []
    
    async def _fetch_linkedin_posts(self, source: SocialMediaSource) -> List[SocialMediaPost]:
        """Получить посты из LinkedIn.
        
        Args:
            source: Источник LinkedIn
            
        Returns:
            Список постов
        """
        try:
            # В реальной реализации здесь будет вызов LinkedIn Marketing API
            # Пока что возвращаем заглушку
            config = source.config
            headers = {
                "Authorization": f"Bearer {config['access_token']}",
                "X-Restli-Protocol-Version": "2.0.0",
                "LinkedIn-Version": "202306"
            }
            
            url = f"https://api.linkedin.com/rest/socialActions"
            params = {
                "q": "author",
                "author": f"urn:li:organization:{config['organization_id']}"
            }
            
            # Пока возвращаем тестовые данные
            return [
                SocialMediaPost(
                    id="test_linkedin_post_1",
                    platform="linkedin",
                    content="Тестовый пост LinkedIn для проверки интеграции",
                    author=config['organization_id'],
                    timestamp=datetime.utcnow(),
                    likes_count=18,
                    shares_count=3,
                    comments_count=2,
                    url="https://linkedin.com/posts/test"
                )
            ]
        except Exception as e:
            self.logger.error(f"❌ Failed to fetch LinkedIn posts: {e}")
            return []
    
    async def update_source_status(self, source_id: str, is_active: bool) -> bool:
        """Обновить статус источника.
        
        Args:
            source_id: ID источника
            is_active: Новый статус
            
        Returns:
            True если успешно обновлено
        """
        try:
            async with autopost_db.session() as session:
                result = await session.execute(
                    update(SocialMediaSource)
                    .where(SocialMediaSource.id == source_id)
                    .values(is_active=is_active)
                )
                await session.commit()
                return result.rowcount > 0
        except Exception as e:
            self.logger.error(f"❌ Failed to update source status: {e}")
            return False