"""Metrics repository."""

from typing import Optional
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
