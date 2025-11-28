"""Analytics Engine for auto-posting system."""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from sqlalchemy import select, func

from src.models.autopost import AutoPostPublication, PublishStatus
from src.database.autopost_db import autopost_db

logger = logging.getLogger(__name__)


@dataclass
class Statistics:
    """Statistics data class."""
    total_posts: int = 0
    successful_posts: int = 0
    failed_posts: int = 0
    success_rate: float = 0.0
    avg_retry_count: float = 0.0
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None


class TimePeriod:
    """Time period enumeration."""
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    ALL = "all"


class AnalyticsEngine:
    """Engine for analytics and statistics."""
    
    async def record_publication(
        self,
        channel_id: int,
        post_id: str,
        status: PublishStatus
    ) -> None:
        """Record publication (already handled by PublishingService)."""
        pass  # Publications are recorded in PublishingService
    
    async def get_statistics(
        self,
        channel_id: Optional[int] = None,
        period: str = TimePeriod.WEEK
    ) -> Statistics:
        """Get statistics for channel or all channels."""
        try:
            # Calculate period
            end_date = datetime.utcnow()
            if period == TimePeriod.DAY:
                start_date = end_date - timedelta(days=1)
            elif period == TimePeriod.WEEK:
                start_date = end_date - timedelta(weeks=1)
            elif period == TimePeriod.MONTH:
                start_date = end_date - timedelta(days=30)
            else:
                start_date = datetime(2000, 1, 1)
            
            async with autopost_db.session() as session:
                query = select(AutoPostPublication).where(
                    AutoPostPublication.published_at >= start_date
                )
                
                if channel_id:
                    query = query.where(AutoPostPublication.channel_id == channel_id)
                
                result = await session.execute(query)
                publications = result.scalars().all()
                
                total = len(publications)
                successful = sum(1 for p in publications if p.status == PublishStatus.SUCCESS.value)
                failed = total - successful
                success_rate = (successful / total * 100) if total > 0 else 0.0
                avg_retry = sum(p.retry_count for p in publications) / total if total > 0 else 0.0
                
                return Statistics(
                    total_posts=total,
                    successful_posts=successful,
                    failed_posts=failed,
                    success_rate=success_rate,
                    avg_retry_count=avg_retry,
                    period_start=start_date,
                    period_end=end_date
                )
        except Exception as e:
            logger.error(f"❌ Failed to get statistics: {e}")
            return Statistics()
    
    async def generate_report(self, channel_id: Optional[int] = None) -> str:
        """Generate text report."""
        stats = await self.get_statistics(channel_id, TimePeriod.WEEK)
        
        report = f"""📊 **Отчет по публикациям**

📅 Период: {stats.period_start.strftime('%d.%m.%Y')} - {stats.period_end.strftime('%d.%m.%Y')}

📈 Статистика:
• Всего публикаций: {stats.total_posts}
• Успешных: {stats.successful_posts} ✅
• Неудачных: {stats.failed_posts} ❌
• Процент успеха: {stats.success_rate:.1f}%
• Среднее кол-во попыток: {stats.avg_retry_count:.1f}
"""
        return report
