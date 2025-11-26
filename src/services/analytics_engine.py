"""Analytics engine for tracking and analyzing post performance."""

import logging
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass
from src.models import Metrics, Post, PostStatus

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
    
    async def get_channel_analytics(
        self,
        channel_id: int,
        period_start: datetime,
        period_end: datetime,
        use_real_stats: bool = True
    ) -> dict:
        """Get analytics for a channel.
        
        Args:
            channel_id: ID of the channel
            period_start: Start of the period
            period_end: End of the period
            use_real_stats: Whether to fetch real stats from Telegram (requires Telethon)
            
        Returns:
            Dictionary with analytics data
        """
        logger.info(f"Getting analytics for channel {channel_id} from {period_start} to {period_end}")
        
        try:
            from sqlalchemy import select, func
            from src.models import Post, Metrics, get_session, Channel
            
            async for session in get_session():
                # Get all published posts in the period
                query = (
                    select(Post, Metrics)
                    .join(Metrics, Post.id == Metrics.post_id, isouter=True)
                    .where(Post.channel_id == channel_id)
                    .where(Post.status == PostStatus.PUBLISHED)
                    .where(Post.published_at >= period_start)
                    .where(Post.published_at <= period_end)
                )
                
                result = await session.execute(query)
                posts_with_metrics = result.all()
                
                if not posts_with_metrics:
                    logger.info(f"No published posts found for channel {channel_id} in period")
                    return {'no_data': True}
                
                # Calculate totals
                total_posts = len(posts_with_metrics)
                total_views = 0
                total_reactions = 0
                total_shares = 0
                total_comments = 0
                top_posts = []
                
                for post, metrics in posts_with_metrics:
                    if metrics:
                        total_views += metrics.views
                        total_reactions += metrics.reactions
                        total_shares += metrics.shares
                        total_comments += metrics.comments
                        
                        top_posts.append({
                            'post_id': post.id,
                            'views': metrics.views,
                            'engagement_rate': metrics.engagement_rate * 100,  # Convert to percentage
                            'published_at': post.published_at.isoformat() if post.published_at else None
                        })
                
                # Sort top posts by engagement rate
                top_posts.sort(key=lambda x: x['engagement_rate'], reverse=True)
                top_posts = top_posts[:5]  # Top 5
                
                # Calculate engagement rate
                total_engagement = total_reactions + total_shares + total_comments
                engagement_rate = (total_engagement / total_views * 100) if total_views > 0 else 0
                
                # Calculate growth (compare with previous period)
                previous_period_start = period_start - (period_end - period_start)
                previous_query = (
                    select(func.count(Post.id))
                    .where(Post.channel_id == channel_id)
                    .where(Post.status == PostStatus.PUBLISHED)
                    .where(Post.published_at >= previous_period_start)
                    .where(Post.published_at < period_start)
                )
                previous_result = await session.execute(previous_query)
                previous_posts = previous_result.scalar() or 0
                
                growth = 0.0
                if previous_posts > 0:
                    growth = ((total_posts - previous_posts) / previous_posts) * 100
                
                # Find best posting time (hour with highest avg engagement)
                best_hour = 18  # Default
                if posts_with_metrics:
                    hour_engagement = {}
                    for post, metrics in posts_with_metrics:
                        if post.published_at and metrics:
                            hour = post.published_at.hour
                            if hour not in hour_engagement:
                                hour_engagement[hour] = []
                            hour_engagement[hour].append(metrics.engagement_rate)
                    
                    if hour_engagement:
                        avg_by_hour = {
                            hour: sum(rates) / len(rates)
                            for hour, rates in hour_engagement.items()
                        }
                        best_hour = max(avg_by_hour.items(), key=lambda x: x[1])[0]
                
                best_time = f"{best_hour:02d}:00-{(best_hour+2):02d}:00"
                
                logger.info(
                    f"Analytics for channel {channel_id}: "
                    f"{total_posts} posts, {total_views} views, {engagement_rate:.2f}% engagement"
                )
                
                result = {
                    'views': total_views,
                    'reactions': total_reactions,
                    'shares': total_shares,
                    'comments': total_comments,
                    'engagement_rate': engagement_rate,
                    'total_posts': total_posts,
                    'growth': growth,
                    'best_time': best_time,
                    'top_posts': top_posts
                }
                
                break  # Exit after first session
                
            return result
            
        except Exception as e:
            logger.error(f"Error getting analytics for channel {channel_id}: {e}", exc_info=True)
            return {'no_data': True}
