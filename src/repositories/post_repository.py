"""Post repository."""

from typing import Optional, List
from datetime import datetime
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from src.models import Post, PostStatus


class PostRepository:
    """Repository for Post operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, post: Post) -> Post:
        """Create a new post."""
        self.session.add(post)
        await self.session.commit()
        await self.session.refresh(post)
        return post
    
    async def get_by_id(self, post_id: int) -> Optional[Post]:
        """Get post by ID."""
        result = await self.session.execute(
            select(Post).where(Post.id == post_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_channel(self, channel_id: int, status: Optional[PostStatus] = None) -> List[Post]:
        """Get posts by channel."""
        query = select(Post).where(Post.channel_id == channel_id)
        if status:
            query = query.where(Post.status == status)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_scheduled(self, before: datetime) -> List[Post]:
        """Get scheduled posts before a certain time."""
        result = await self.session.execute(
            select(Post).where(
                Post.status == PostStatus.SCHEDULED,
                Post.scheduled_for <= before
            )
        )
        return list(result.scalars().all())
    
    async def update_status(self, post_id: int, status: PostStatus, published_at: Optional[datetime] = None) -> None:
        """Update post status."""
        values = {"status": status}
        if published_at:
            values["published_at"] = published_at
        
        await self.session.execute(
            update(Post).where(Post.id == post_id).values(**values)
        )
        await self.session.commit()
    
    async def delete(self, post_id: int) -> None:
        """Delete a post."""
        await self.session.execute(
            delete(Post).where(Post.id == post_id)
        )
        await self.session.commit()
    
    async def get_count_by_status(self, channel_id: int, status: PostStatus) -> int:
        """Get count of posts by channel and status."""
        result = await self.session.execute(
            select(Post.id)
            .where(Post.channel_id == channel_id, Post.status == status)
        )
        return len(result.scalars().all())
    
    async def get_all_by_status(self, status: PostStatus) -> List[Post]:
        """Get all posts with specific status."""
        result = await self.session.execute(
            select(Post).where(Post.status == status)
        )
        return list(result.scalars().all())