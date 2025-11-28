"""Metrics repository."""

from typing import Optional, List
from datetime import datetime
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from src.models import Metrics


class MetricsRepository:
    """Repository for Metrics operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, metrics: Metrics) -> Metrics:
        """Create new metrics."""
        self.session.add(metrics)
        await self.session.commit()
        await self.session.refresh(metrics)
        return metrics
    
    async def get_by_post_id(self, post_id: int) -> Optional[Metrics]:
        """Get metrics by post ID."""
        result = await self.session.execute(
            select(Metrics).where(Metrics.post_id == post_id)
        )
        return result.scalar_one_or_none()
    
    async def update(self, post_id: int, **kwargs) -> None:
        """Update metrics."""
        await self.session.execute(
            update(Metrics).where(Metrics.post_id == post_id).values(**kwargs)
        )
        await self.session.commit()
    
    async def get_by_channel(self, channel_id: int) -> List[Metrics]:
        """Get metrics for all posts in a channel."""
        result = await self.session.execute(
            select(Metrics)
            .join(Metrics.post)
            .where(Metrics.post.channel_id == channel_id)
        )
        return list(result.scalars().all())
    
    async def get_recent_metrics(self, limit: int = 10) -> List[Metrics]:
        """Get recent metrics."""
        result = await self.session.execute(
            select(Metrics)
            .order_by(Metrics.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())