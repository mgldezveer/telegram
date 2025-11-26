"""Post Queue Manager for auto-posting system."""

import logging
from typing import List, Optional
from datetime import datetime
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

from src.models.autopost import AutoPost, PostStatus, AutoPostChannel
from src.database.autopost_db import autopost_db

logger = logging.getLogger(__name__)


class QueuedPost:
    """Queued post wrapper."""
    
    def __init__(self, post: AutoPost, channel: Optional[AutoPostChannel] = None):
        self.post = post
        self.channel = channel
    
    @property
    def id(self):
        return self.post.id
    
    @property
    def channel_id(self):
        return self.post.channel_id
    
    @property
    def content(self):
        return self.post.content
    
    @property
    def status(self):
        return self.post.status
    
    @property
    def scheduled_for(self):
        return self.post.scheduled_for
    
    @property
    def priority(self):
        return self.post.priority


class AutoPostQueueManager:
    """Manager for post queue."""
    
    def __init__(self):
        """Initialize queue manager."""
        pass
    
    async def add_to_queue(
        self,
        post: AutoPost,
        priority: int = 0
    ) -> str:
        """Add post to queue.
        
        Args:
            post: Post object
            priority: Queue priority (higher = more important)
            
        Returns:
            Queue ID (post ID)
        """
        logger.info(f"Adding post {post.id} to queue")
        
        async with autopost_db.session() as session:
            # Set post status and priority
            post.status = PostStatus.QUEUED.value
            post.priority = priority
            
            session.add(post)
            await session.commit()
        
        logger.info(f"✅ Added post {post.id} to queue with priority {priority}")
        return post.id
    
    async def get_queue(
        self,
        channel_id: Optional[int] = None,
        status: Optional[str] = None
    ) -> List[QueuedPost]:
        """Get posts from queue.
        
        Args:
            channel_id: Filter by channel ID
            status: Filter by status
            
        Returns:
            List of queued posts
        """
        async with autopost_db.session() as session:
            query = select(AutoPost).options(selectinload(AutoPost.channel))
            
            # Apply filters
            if channel_id is not None:
                query = query.where(AutoPost.channel_id == channel_id)
            
            if status:
                query = query.where(AutoPost.status == status)
            else:
                # Default: show queued and approved posts
                query = query.where(
                    AutoPost.status.in_([
                        PostStatus.QUEUED.value,
                        PostStatus.APPROVED.value
                    ])
                )
            
            # Order by priority (desc) and created_at (asc)
            query = query.order_by(
                AutoPost.priority.desc(),
                AutoPost.created_at.asc()
            )
            
            result = await session.execute(query)
            posts = result.scalars().all()
            
            return [QueuedPost(post, post.channel) for post in posts]
    
    async def approve_post(self, queue_id: str) -> bool:
        """Approve post for publication.
        
        Args:
            queue_id: Post ID
            
        Returns:
            True if approved
        """
        logger.info(f"Approving post {queue_id}")
        
        async with autopost_db.session() as session:
            result = await session.execute(
                select(AutoPost).where(AutoPost.id == queue_id)
            )
            post = result.scalar_one_or_none()
            
            if not post:
                logger.warning(f"Post {queue_id} not found")
                return False
            
            post.status = PostStatus.APPROVED.value
            await session.commit()
        
        logger.info(f"✅ Approved post {queue_id}")
        return True
    
    async def edit_post(self, queue_id: str, content: str) -> bool:
        """Edit post content.
        
        Args:
            queue_id: Post ID
            content: New content
            
        Returns:
            True if edited
        """
        logger.info(f"Editing post {queue_id}")
        
        async with autopost_db.session() as session:
            result = await session.execute(
                select(AutoPost).where(AutoPost.id == queue_id)
            )
            post = result.scalar_one_or_none()
            
            if not post:
                logger.warning(f"Post {queue_id} not found")
                return False
            
            post.content = content
            await session.commit()
        
        logger.info(f"✅ Edited post {queue_id}")
        return True
    
    async def remove_from_queue(self, queue_id: str) -> bool:
        """Remove post from queue.
        
        Args:
            queue_id: Post ID
            
        Returns:
            True if removed
        """
        logger.info(f"Removing post {queue_id} from queue")
        
        async with autopost_db.session() as session:
            result = await session.execute(
                select(AutoPost).where(AutoPost.id == queue_id)
            )
            post = result.scalar_one_or_none()
            
            if not post:
                logger.warning(f"Post {queue_id} not found")
                return False
            
            post.status = PostStatus.CANCELLED.value
            await session.commit()
        
        logger.info(f"✅ Removed post {queue_id} from queue")
        return True
    
    async def get_next_post(self, channel_id: int) -> Optional[QueuedPost]:
        """Get next post for channel.
        
        Args:
            channel_id: Channel ID
            
        Returns:
            Next queued post or None
        """
        async with autopost_db.session() as session:
            # Get channel settings
            result = await session.execute(
                select(AutoPostChannel).where(AutoPostChannel.id == channel_id)
            )
            channel = result.scalar_one_or_none()
            
            if not channel or not channel.is_active:
                return None
            
            settings = channel.settings or {}
            require_moderation = settings.get('require_moderation', False)
            
            # Build query
            query = select(AutoPost).where(
                AutoPost.channel_id == channel_id
            )
            
            if require_moderation:
                # Only approved posts
                query = query.where(AutoPost.status == PostStatus.APPROVED.value)
            else:
                # Queued or approved posts
                query = query.where(
                    AutoPost.status.in_([
                        PostStatus.QUEUED.value,
                        PostStatus.APPROVED.value
                    ])
                )
            
            # Order by priority and creation time
            query = query.order_by(
                AutoPost.priority.desc(),
                AutoPost.created_at.asc()
            ).limit(1)
            
            result = await session.execute(query)
            post = result.scalar_one_or_none()
            
            if post:
                return QueuedPost(post, channel)
            return None
    
    async def get_post(self, queue_id: str) -> Optional[QueuedPost]:
        """Get post by ID.
        
        Args:
            queue_id: Post ID
            
        Returns:
            Queued post or None
        """
        async with autopost_db.session() as session:
            result = await session.execute(
                select(AutoPost)
                .options(selectinload(AutoPost.channel))
                .where(AutoPost.id == queue_id)
            )
            post = result.scalar_one_or_none()
            
            if post:
                return QueuedPost(post, post.channel)
            return None
    
    async def update_post_status(
        self,
        queue_id: str,
        status: PostStatus,
        published_at: Optional[datetime] = None
    ) -> bool:
        """Update post status.
        
        Args:
            queue_id: Post ID
            status: New status
            published_at: Publication timestamp
            
        Returns:
            True if updated
        """
        async with autopost_db.session() as session:
            result = await session.execute(
                select(AutoPost).where(AutoPost.id == queue_id)
            )
            post = result.scalar_one_or_none()
            
            if not post:
                return False
            
            post.status = status.value
            if published_at:
                post.published_at = published_at
            
            await session.commit()
        
        return True
