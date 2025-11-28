"""Улучшенный репозиторий постов с кэшированием и оптимизациями."""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import select, update, delete, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text
from src.models import Post, PostStatus
from src.cache import cache
import json
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class EnhancedPostRepository:
    """Улучшенный репозиторий для операций с постами с кэшированием и оптимизациями."""
    
    def __init__(self, session: AsyncSession, cache_ttl: int = 300, max_retries: int = 3):  # 5 minutes default TTL
        self.session = session
        self.cache_ttl = cache_ttl
        self.max_retries = max_retries
    
    def _get_cache_key(self, entity: str, id: str) -> str:
        """Получить ключ кэша для сущности.
        
        Args:
            entity: Тип сущности (post, channel, etc.)
            id: ID сущности
            
        Returns:
            Ключ кэша
        """
        return f"repo:{entity}:{id}"
    
    def _get_list_cache_key(self, entity: str, **kwargs) -> str:
        """Получить ключ кэша для списка сущностей.
        
        Args:
            entity: Тип сущности
            **kwargs: Параметры фильтрации
            
        Returns:
            Ключ кэша
        """
        params = "_".join(f"{k}_{v}" for k, v in sorted(kwargs.items()))
        return f"repo:list:{entity}:{params}" if params else f"repo:list:{entity}:all"
    
    async def create(self, post: Post) -> Post:
        """Создать новый пост с инвалидацией кэша.
        
        Args:
            post: Объект поста для создания
            
        Returns:
            Созданный объект поста
        """
        self.session.add(post)
        await self.session.commit()
        await self.session.refresh(post)
        
        # Инвалидировать кэш связанных списков
        await cache.delete(self._get_list_cache_key("post", channel_id=post.channel_id))
        await cache.delete(self._get_list_cache_key("post", status=post.status.value))
        await cache.delete(self._get_list_cache_key("post", channel_id=post.channel_id, status=post.status.value))
        
        logger.info(f"✅ Created post {post.id} in channel {post.channel_id}")
        return post
    
    async def get_by_id(self, post_id: int) -> Optional[Post]:
        """Получить пост по ID с кэшированием.
        
        Args:
            post_id: ID поста
            
        Returns:
            Объект поста или None
        """
        cache_key = self._get_cache_key("post", str(post_id))
        
        # Попробовать получить из кэша
        cached_post = await cache.get(cache_key)
        if cached_post:
            # В текущей реализации десериализация Post из кэша требует дополнительной логики
            # Пока возвращаем None и загружаем из БД
            pass
        
        # Загрузить из БД
        result = await self.session.execute(
            select(Post).where(Post.id == post_id)
        )
        post = result.scalar_one_or_none()
        
        if post:
            # Кэшировать результат
            post_data = {
                'id': post.id,
                'channel_id': post.channel_id,
                'title': post.title,
                'content': post.content,
                'hashtags': post.hashtags,
                'status': post.status.value,
                'scheduled_for': post.scheduled_for.isoformat() if post.scheduled_for else None,
                'published_at': post.published_at.isoformat() if post.published_at else None,
                'created_at': post.created_at.isoformat()
            }
            await cache.set(cache_key, post_data, self.cache_ttl)
        
        return post
    
    async def get_by_channel(self, channel_id: int, status: Optional[PostStatus] = None) -> List[Post]:
        """Получить посты по каналу с кэшированием.
        
        Args:
            channel_id: ID канала
            status: Статус постов (опционально)
            
        Returns:
            Список постов
        """
        cache_key = self._get_list_cache_key("post", channel_id=channel_id, status=status.value if status else "all")
        
        # Попробовать получить из кэша
        cached_posts = await cache.get(cache_key)
        if cached_posts:
            # В текущей реализации десериализация списка Post из кэша требует дополнительной логики
            # Пока возвращаем None и загружаем из БД
            pass
        
        # Загрузить из БД
        query = select(Post).where(Post.channel_id == channel_id)
        if status:
            query = query.where(Post.status == status)
        
        result = await self.session.execute(query)
        posts = list(result.scalars().all())
        
        # Кэшировать результат
        posts_data = []
        for post in posts:
            posts_data.append({
                'id': post.id,
                'channel_id': post.channel_id,
                'title': post.title,
                'content': post.content,
                'hashtags': post.hashtags,
                'status': post.status.value,
                'scheduled_for': post.scheduled_for.isoformat() if post.scheduled_for else None,
                'published_at': post.published_at.isoformat() if post.published_at else None,
                'created_at': post.created_at.isoformat()
            })
        
        await cache.set(cache_key, posts_data, self.cache_ttl)
        
        return posts
    
    async def get_scheduled(self, before: datetime) -> List[Post]:
        """Получить запланированные посты до определенного времени с кэшированием.
        
        Args:
            before: Время, до которого запланированы посты
            
        Returns:
            Список запланированных постов
        """
        cache_key = self._get_list_cache_key("post", scheduled_before=before.isoformat(), status="scheduled")
        
        # Попробовать получить из кэша
        cached_posts = await cache.get(cache_key)
        if cached_posts:
            # В текущей реализации десериализация списка Post из кэша требует дополнительной логики
            # Пока возвращаем None и загружаем из БД
            pass
        
        # Загрузить из БД
        result = await self.session.execute(
            select(Post).where(
                Post.status == PostStatus.SCHEDULED,
                Post.scheduled_for <= before
            ).order_by(Post.scheduled_for) # Добавим сортировку для предсказуемости
        )
        posts = list(result.scalars().all())
        
        # Кэшировать результат
        posts_data = []
        for post in posts:
            posts_data.append({
                'id': post.id,
                'channel_id': post.channel_id,
                'title': post.title,
                'content': post.content,
                'hashtags': post.hashtags,
                'status': post.status.value,
                'scheduled_for': post.scheduled_for.isoformat() if post.scheduled_for else None,
                'published_at': post.published_at.isoformat() if post.published_at else None,
                'created_at': post.created_at.isoformat()
            })
        
        await cache.set(cache_key, posts_data, self.cache_ttl)
        
        return posts
    
    async def update_status(self, post_id: int, status: PostStatus, published_at: Optional[datetime] = None) -> None:
        """Обновить статус поста с инвалидацией кэша.
        
        Args:
            post_id: ID поста
            status: Новый статус
            published_at: Время публикации (опционально)
        """
        values = {"status": status}
        if published_at:
            values["published_at"] = published_at
        
        await self.session.execute(
            update(Post).where(Post.id == post_id).values(**values)
        )
        await self.session.commit()
        
        # Инвалидировать кэш
        cache_key = self._get_cache_key("post", str(post_id))
        await cache.delete(cache_key)
        
        # Также инвалидировать связанные списки
        result = await self.session.execute(
            select(Post).where(Post.id == post_id)
        )
        post = result.scalar_one_or_none()
        if post:
            await cache.delete(self._get_list_cache_key("post", channel_id=post.channel_id))
            await cache.delete(self._get_list_cache_key("post", status=status.value))
            await cache.delete(self._get_list_cache_key("post", channel_id=post.channel_id, status=status.value))
        
        logger.info(f"✅ Updated post {post_id} status to {status.value}")
    
    async def delete(self, post_id: int) -> None:
        """Удалить пост с инвалидацией кэша.
        
        Args:
            post_id: ID поста для удаления
        """
        # Получить пост перед удалением для инвалидации кэша
        result = await self.session.execute(
            select(Post).where(Post.id == post_id)
        )
        post = result.scalar_one_or_none()
        
        await self.session.execute(
            delete(Post).where(Post.id == post_id)
        )
        await self.session.commit()
        
        # Инвалидировать кэш
        cache_key = self._get_cache_key("post", str(post_id))
        await cache.delete(cache_key)
        
        # Также инвалидировать связанные списки
        if post:
            await cache.delete(self._get_list_cache_key("post", channel_id=post.channel_id))
            await cache.delete(self._get_list_cache_key("post", status=post.status.value))
            await cache.delete(self._get_list_cache_key("post", channel_id=post.channel_id, status=post.status.value))
        
        logger.info(f"✅ Deleted post {post_id}")
    
    async def batch_update_status(self, post_ids: List[int], status: PostStatus, published_at: Optional[datetime] = None) -> int:
        """Массовое обновление статусов постов.
        
        Args:
            post_ids: Список ID постов
            status: Новый статус
            published_at: Время публикации (опционально)
            
        Returns:
            Количество обновленных постов
        """
        if not post_ids:
            return 0
        
        values = {"status": status}
        if published_at:
            values["published_at"] = published_at
        
        result = await self.session.execute(
            update(Post)
            .where(Post.id.in_(post_ids))
            .values(**values)
        )
        await self.session.commit()
        
        rows_affected = result.rowcount
        
        # Инвалидировать кэш для каждого поста
        for post_id in post_ids:
            cache_key = self._get_cache_key("post", str(post_id))
            await cache.delete(cache_key)
        
        # Инвалидировать связанные списки
        await cache.delete(self._get_list_cache_key("post", status=status.value))
        
        logger.info(f"✅ Batch updated {rows_affected} posts to status {status.value}")
        return rows_affected
    
    async def get_count_by_channel_and_status(self, channel_id: int, status: PostStatus) -> int:
        """Получить количество постов по каналу и статусу.
        
        Args:
            channel_id: ID канала
            status: Статус постов
            
        Returns:
            Количество постов
        """
        cache_key = self._get_list_cache_key("post_count", channel_id=channel_id, status=status.value)
        
        cached_count = await cache.get(cache_key)
        if cached_count is not None:
            return int(cached_count)
        
        result = await self.session.execute(
            select(Post).where(
                Post.channel_id == channel_id,
                Post.status == status
            )
        )
        posts = result.scalars().all()
        count = len(posts)
        
        # Кэшировать результат на короткое время
        await cache.set(cache_key, count, self.cache_ttl // 2)
        
        return count
    
    async def get_recent_posts(self, limit: int = 10) -> List[Post]:
        """Получить недавние посты.
        
        Args:
            limit: Количество постов для возврата
            
        Returns:
            Список недавних постов
        """
        cache_key = self._get_list_cache_key("post", recent=limit)
        
        # Попробовать получить из кэша
        cached_posts = await cache.get(cache_key)
        if cached_posts:
            # В текущей реализации десериализация списка Post из кэша требует дополнительной логики
            # Пока возвращаем None и загружаем из БД
            pass
        
        result = await self.session.execute(
            select(Post)
            .order_by(Post.created_at.desc())
            .limit(limit)
        )
        posts = list(result.scalars().all())
        
        # Кэшировать результат
        posts_data = []
        for post in posts:
            posts_data.append({
                'id': post.id,
                'channel_id': post.channel_id,
                'title': post.title,
                'content': post.content,
                'hashtags': post.hashtags,
                'status': post.status.value,
                'scheduled_for': post.scheduled_for.isoformat() if post.scheduled_for else None,
                'published_at': post.published_at.isoformat() if post.published_at else None,
                'created_at': post.created_at.isoformat()
            })
        
        await cache.set(cache_key, posts_data, self.cache_ttl)
        
        return posts
    
    async def get_posts_stats(self, channel_id: Optional[int] = None) -> Dict[str, Any]:
        """Получить статистику по постам.
        
        Args:
            channel_id: ID канала (опционально)
            
        Returns:
            Словарь со статистикой
        """
        cache_key = self._get_list_cache_key("post_stats", channel_id=channel_id or "all")
        
        # Попробовать получить из кэша
        cached_stats = await cache.get(cache_key)
        if cached_stats:
            return cached_stats
        
        # Построить общий запрос для получения статистики
        query = select(
            func.count(Post.id).label('total_posts'),
            func.sum(
                case(
                    (Post.status == PostStatus.PUBLISHED, 1),
                    else_=0
                )
            ).label('published_posts'),
            func.sum(
                case(
                    (Post.status == PostStatus.SCHEDULED, 1),
                    else_=0
                )
            ).label('scheduled_posts'),
            func.sum(
                case(
                    (Post.status == PostStatus.DRAFT, 1),
                    else_=0
                )
            ).label('draft_posts'),
            func.sum(
                case(
                    (Post.status == PostStatus.FAILED, 1),
                    else_=0
                )
            ).label('failed_posts')
        )
        
        if channel_id:
            query = query.where(Post.channel_id == channel_id)
        
        result = await self.session.execute(query)
        row = result.fetchone()
        
        stats = {
            'total_posts': row[0] or 0,
            'published_posts': row[1] or 0,
            'scheduled_posts': row[2] or 0,
            'draft_posts': row[3] or 0,
            'failed_posts': row[4] or 0
        }
        
        # Кэшировать результат на короткое время
        await cache.set(cache_key, stats, self.cache_ttl // 2)
        
        return stats
    
    async def get_channel_activity_stats(self, channel_id: int, days: int = 7) -> Dict[str, Any]:
        """Получить статистику активности канала за последние N дней.
        
        Args:
            channel_id: ID канала
            days: Количество дней для анализа (по умолчанию 7)
            
        Returns:
            Словарь со статистикой активности
        """
        cache_key = self._get_list_cache_key("channel_activity", channel_id=channel_id, days=days)
        
        # Попробовать получить из кэша
        cached_stats = await cache.get(cache_key)
        if cached_stats:
            return cached_stats
        
        since_date = datetime.utcnow() - timedelta(days=days)
        
        # Получить количество опубликованных постов по дням
        daily_query = select(
            func.date(Post.published_at).label('date'),
            func.count(Post.id).label('count')
        ).where(
            and_(
                Post.channel_id == channel_id,
                Post.status == PostStatus.PUBLISHED,
                Post.published_at >= since_date
            )
        ).group_by(func.date(Post.published_at)).order_by(func.date(Post.published_at))
        
        result = await self.session.execute(daily_query)
        daily_stats = [{'date': str(row[0]), 'count': row[1]} for row in result.fetchall()]
        
        # Общая статистика
        total_query = select(
            func.count(Post.id).label('total_published'),
            func.avg(func.extract('epoch', Post.published_at - Post.created_at)).label('avg_creation_time')
        ).where(
            and_(
                Post.channel_id == channel_id,
                Post.status == PostStatus.PUBLISHED,
                Post.published_at >= since_date
            )
        )
        
        result = await self.session.execute(total_query)
        row = result.fetchone()
        
        stats = {
            'channel_id': channel_id,
            'days_analyzed': days,
            'period_start': since_date.isoformat(),
            'daily_stats': daily_stats,
            'total_published': row[0] or 0,
            'avg_creation_time_seconds': row[1] or 0
        }
        
        # Кэшировать результат на короткое время
        await cache.set(cache_key, stats, self.cache_ttl // 3)
        
        return stats