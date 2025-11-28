"""Post Queue Manager for auto-posting system."""

import logging
from datetime import datetime
from typing import List, Optional
from sqlalchemy import select, update, delete
from sqlalchemy.exc import IntegrityError

from src.models.autopost import AutoPost, PostStatus
from src.database.autopost_db import autopost_db

logger = logging.getLogger(__name__)


class QueuedPost:
    """Queued post wrapper with additional metadata."""
    
    def __init__(self, post: AutoPost):
        self.post = post
        self.id = post.id
        self.channel_id = post.channel_id
        self.content = post.content
        self.status = post.status
        self.priority = post.priority
        self.scheduled_for = post.scheduled_for
        self.created_at = post.created_at
    
    def __repr__(self):
        return f"<QueuedPost(id='{self.id}', status='{self.status}', priority={self.priority})>"


class PostQueueManager:
    """Manager for post queue operations."""
    
    def __init__(self):
        """Initialize post queue manager."""
        pass
    
    async def add_to_queue(
        self,
        post: AutoPost,
        priority: int = 0
    ) -> str:
        """Add post to queue.
        
        Args:
            post: Post object to add
            priority: Priority level (higher = more important)
        
        Returns:
            Queue ID (post ID)
        
        Raises:
            RuntimeError: If database operation fails
        """
        try:
            post.priority = priority
            post.status = PostStatus.QUEUED.value
            
            async with autopost_db.session() as session:
                session.add(post)
                await session.commit()
                await session.refresh(post)
                
                logger.info(f"✅ Added post to queue: {post.id} (priority: {priority})")
                return post.id
                
        except Exception as e:
            logger.error(f"❌ Failed to add post to queue: {e}")
            raise RuntimeError(f"Failed to add post to queue: {e}")
    
    async def get_queue(
        self,
        channel_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[QueuedPost]:
        """Get posts from queue.
        
        Args:
            channel_id: Optional channel ID to filter by
            status: Optional status to filter by
            limit: Optional limit on number of posts
        
        Returns:
            List of queued posts
        """
        try:
            async with autopost_db.session() as session:
                query = select(AutoPost)
                
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
                
                if limit:
                    query = query.limit(limit)
                
                result = await session.execute(query)
                posts = result.scalars().all()
                
                return [QueuedPost(post) for post in posts]
                
        except Exception as e:
            logger.error(f"❌ Failed to get queue: {e}")
            return []
    
    async def approve_post(self, queue_id: str) -> bool:
        """Approve a post for publication.
        
        Args:
            queue_id: Post ID
        
        Returns:
            True if post was approved, False if not found
        """
        try:
            async with autopost_db.session() as session:
                result = await session.execute(
                    update(AutoPost)
                    .where(AutoPost.id == queue_id)
                    .values(status=PostStatus.APPROVED.value)
                )
                
                if result.rowcount > 0:
                    await session.commit()
                    logger.info(f"✅ Approved post: {queue_id}")
                    return True
                else:
                    logger.warning(f"⚠️ Post {queue_id} not found")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Failed to approve post {queue_id}: {e}")
            raise RuntimeError(f"Failed to approve post: {e}")
    
    async def edit_post(self, queue_id: str, content: str) -> bool:
        """Edit post content.
        
        Args:
            queue_id: Post ID
            content: New content
        
        Returns:
            True if post was edited, False if not found
        """
        try:
            async with autopost_db.session() as session:
                result = await session.execute(
                    update(AutoPost)
                    .where(AutoPost.id == queue_id)
                    .values(content=content)
                )
                
                if result.rowcount > 0:
                    await session.commit()
                    logger.info(f"✅ Edited post: {queue_id}")
                    return True
                else:
                    logger.warning(f"⚠️ Post {queue_id} not found")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Failed to edit post {queue_id}: {e}")
            raise RuntimeError(f"Failed to edit post: {e}")
    
    async def remove_from_queue(self, queue_id: str) -> bool:
        """Remove post from queue.
        
        Args:
            queue_id: Post ID
        
        Returns:
            True if post was removed, False if not found
        """
        try:
            async with autopost_db.session() as session:
                # Update status to cancelled instead of deleting
                result = await session.execute(
                    update(AutoPost)
                    .where(AutoPost.id == queue_id)
                    .values(status=PostStatus.CANCELLED.value)
                )
                
                if result.rowcount > 0:
                    await session.commit()
                    logger.info(f"✅ Removed post from queue: {queue_id}")
                    return True
                else:
                    logger.warning(f"⚠️ Post {queue_id} not found")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Failed to remove post {queue_id}: {e}")
            raise RuntimeError(f"Failed to remove post: {e}")
    
    async def get_next_post(self, channel_id: int) -> Optional[QueuedPost]:
        """Get next post to publish for a channel.
        
        Args:
            channel_id: Telegram channel ID
        
        Returns:
            Next queued post or None
        """
        try:
            async with autopost_db.session() as session:
                # Get highest priority approved post
                result = await session.execute(
                    select(AutoPost)
                    .where(
                        AutoPost.channel_id == channel_id,
                        AutoPost.status == PostStatus.APPROVED.value
                    )
                    .order_by(
                        AutoPost.priority.desc(),
                        AutoPost.created_at.asc()
                    )
                    .limit(1)
                )
                
                post = result.scalar_one_or_none()
                
                if post:
                    return QueuedPost(post)
                
                # If no approved posts, check for auto-publish posts
                result = await session.execute(
                    select(AutoPost)
                    .where(
                        AutoPost.channel_id == channel_id,
                        AutoPost.status == PostStatus.QUEUED.value
                    )
                    .order_by(
                        AutoPost.priority.desc(),
                        AutoPost.created_at.asc()
                    )
                    .limit(1)
                )
                
                post = result.scalar_one_or_none()
                return QueuedPost(post) if post else None
                
        except Exception as e:
            logger.error(f"❌ Failed to get next post for channel {channel_id}: {e}")
            return None
    
    async def get_post(self, queue_id: str) -> Optional[AutoPost]:
        """Get post by ID.
        
        Args:
            queue_id: Post ID
        
        Returns:
            Post object or None if not found
        """
        try:
            async with autopost_db.session() as session:
                result = await session.execute(
                    select(AutoPost).where(AutoPost.id == queue_id)
                )
                post = result.scalar_one_or_none()
                return post
                
        except Exception as e:
            logger.error(f"❌ Failed to get post {queue_id}: {e}")
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
            published_at: Optional publication timestamp
        
        Returns:
            True if status was updated, False if not found
        """
        try:
            async with autopost_db.session() as session:
                values = {"status": status.value}
                
                if published_at:
                    values["published_at"] = published_at
                
                result = await session.execute(
                    update(AutoPost)
                    .where(AutoPost.id == queue_id)
                    .values(**values)
                )
                
                if result.rowcount > 0:
                    await session.commit()
                    logger.info(f"✅ Updated post status: {queue_id} -> {status.value}")
                    return True
                else:
                    logger.warning(f"⚠️ Post {queue_id} not found")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Failed to update post status {queue_id}: {e}")
            raise RuntimeError(f"Failed to update post status: {e}")
    
    async def count_queue(
        self,
        channel_id: Optional[int] = None,
        status: Optional[str] = None
    ) -> int:
        """Count posts in queue.
        
        Args:
            channel_id: Optional channel ID to filter by
            status: Optional status to filter by
        
        Returns:
            Number of posts in queue
        """
        try:
            posts = await self.get_queue(channel_id=channel_id, status=status)
            return len(posts)
            
        except Exception as e:
            logger.error(f"❌ Failed to count queue: {e}")
            return 0
