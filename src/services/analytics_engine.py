"""Analytics engine for tracking and analyzing post performance."""

import logging
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass
from src.models import Metrics, Post

logger = logging.getLogger(__name__)


@dataclass
class TimePeriod:
    """Time period for analytics."""
    start: datetime
    end: datetime


@dataclass
class Report:
    """Analytics report."""
    period: TimePeriod
    total_posts: int
    total_views: int
    total_engagement: int
    avg_engagement_rate: float
    top_posts: list[dict]


@dataclass
class EngagementPatterns:
    """Detected engagement patterns."""
    best_posting_times: list[str]
    best_content_types: list[str]
    avg_engagement_by_hour: dict[int, float]


@dataclass
class Recommendation:
    """Content strategy recommendation."""
    type: str
    description: str
    priority: str  # high, medium, low


class AnalyticsEngine:
    """Engine for tracking and analyzing post performance."""
    
    def __init__(self):
        self.performance_threshold = 0.05  # 5% engagement rate
    
    async def track_post(self, post_id: int, metrics: Metrics):
        """Track post performance metrics."""
        logger.info(f"Tracking metrics for post {post_id}")
        
        # Calculate engagement rate
        if metrics.views > 0:
            total_engagement = metrics.reactions + metrics.shares + metrics.comments
            metrics.engagement_rate = total_engagement / metrics.views
        else:
            metrics.engagement_rate = 0.0
        
        logger.info(f"Post {post_id} engagement rate: {metrics.engagement_rate:.2%}")
    
    async def get_performance_report(
        self,
        channel_id: int,
        period: TimePeriod,
        posts: list[Post]
    ) -> Report:
        """Generate performance report for a channel."""
        logger.info(f"Generating performance report for channel {channel_id}")
        
        # Filter posts by period
        period_posts = [
            p for p in posts
            if p.published_at and period.start <= p.published_at <= period.end
        ]
        
        # Calculate totals
        total_posts = len(period_posts)
        total_views = sum(p.metrics.views if p.metrics else 0 for p in period_posts)
        total_engagement = sum(
            (p.metrics.reactions + p.metrics.shares + p.metrics.comments)
            if p.metrics else 0
            for p in period_posts
        )
        
        # Calculate average engagement rate
        if total_views > 0:
            avg_engagement_rate = total_engagement / total_views
        else:
            avg_engagement_rate = 0.0
        
        # Get top posts
        top_posts = sorted(
            [p for p in period_posts if p.metrics],
            key=lambda p: p.metrics.engagement_rate,
            reverse=True
        )[:5]
        
        top_posts_data = [
            {
                'id': p.id,
                'content': p.content[:100],
                'views': p.metrics.views,
                'engagement_rate': p.metrics.engagement_rate
            }
            for p in top_posts
        ]
        
        report = Report(
            period=period,
            total_posts=total_posts,
            total_views=total_views,
            total_engagement=total_engagement,
            avg_engagement_rate=avg_engagement_rate,
            top_posts=top_posts_data
        )
        
        logger.info(f"Report generated: {total_posts} posts, {avg_engagement_rate:.2%} avg engagement")
        return report
    
    async def analyze_patterns(self, channel_id: int, posts: list[Post]) -> EngagementPatterns:
        """Analyze engagement patterns from historical data."""
        logger.info(f"Analyzing engagement patterns for channel {channel_id}")
        
        # Analyze posting times
        hour_engagement = {}
        for post in posts:
            if post.published_at and post.metrics:
                hour = post.published_at.hour
                if hour not in hour_engagement:
                    hour_engagement[hour] = []
                hour_engagement[hour].append(post.metrics.engagement_rate)
        
        # Calculate average engagement by hour
        avg_by_hour = {
            hour: sum(rates) / len(rates)
            for hour, rates in hour_engagement.items()
        }
        
        # Find best posting times (top 3 hours)
        best_hours = sorted(avg_by_hour.items(), key=lambda x: x[1], reverse=True)[:3]
        best_posting_times = [f"{hour:02d}:00" for hour, _ in best_hours]
        
        # Analyze content types (simplified)
        best_content_types = ["text", "image"]  # Placeholder
        
        patterns = EngagementPatterns(
            best_posting_times=best_posting_times,
            best_content_types=best_content_types,
            avg_engagement_by_hour=avg_by_hour
        )
        
        logger.info(f"Best posting times: {best_posting_times}")
        return patterns
    
    async def get_recommendations(
        self,
        channel_id: int,
        patterns: EngagementPatterns,
        recent_performance: float
    ) -> list[Recommendation]:
        """Generate recommendations based on patterns and performance."""
        logger.info(f"Generating recommendations for channel {channel_id}")
        
        recommendations = []
        
        # Check if performance is below threshold
        if recent_performance < self.performance_threshold:
            recommendations.append(Recommendation(
                type="performance",
                description=f"Engagement rate ({recent_performance:.2%}) is below target ({self.performance_threshold:.2%}). Consider adjusting content strategy.",
                priority="high"
            ))
        
        # Recommend optimal posting times
        if patterns.best_posting_times:
            recommendations.append(Recommendation(
                type="timing",
                description=f"Post at optimal times: {', '.join(patterns.best_posting_times)} for better engagement.",
                priority="medium"
            ))
        
        # Content type recommendations
        if patterns.best_content_types:
            recommendations.append(Recommendation(
                type="content",
                description=f"Focus on {', '.join(patterns.best_content_types)} content for better results.",
                priority="medium"
            ))
        
        logger.info(f"Generated {len(recommendations)} recommendations")
        return recommendations
    
    async def notify_low_performance(
        self,
        channel_id: int,
        post_id: int,
        engagement_rate: float,
        admin_ids: list[int]
    ):
        """Notify administrators about low performance."""
        if engagement_rate < self.performance_threshold:
            logger.warning(
                f"Low performance detected for post {post_id} in channel {channel_id}: "
                f"{engagement_rate:.2%} engagement rate"
            )
            # In production, would send notifications to admins
            # For now, just log
