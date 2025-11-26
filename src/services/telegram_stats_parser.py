"""Service for parsing real statistics from Telegram channels."""

import logging
from datetime import datetime, timedelta
from typing import Optional
from telegram import Bot
from telegram.error import TelegramError
from src.models import get_session, Post, Metrics, PostStatus, Channel

logger = logging.getLogger(__name__)


class TelegramStatsParser:
    """Parser for getting real statistics from Telegram channels."""
    
    def __init__(self, bot: Bot):
        """Initialize parser.
        
        Args:
            bot: Telegram bot instance
        """
        self.bot = bot
    
    async def parse_channel_stats(
        self,
        channel_id: int,
        period_start: datetime,
        period_end: datetime
    ) -> dict:
        """Parse real statistics from Telegram channel.
        
        Args:
            channel_id: Database channel ID
            period_start: Start of period
            period_end: End of period
            
        Returns:
            Dictionary with real statistics
        """
        logger.info(f"Parsing stats for channel {channel_id} from {period_start} to {period_end}")
        
        try:
            async for session in get_session():
                # Get channel from database
                from sqlalchemy import select
                result = await session.execute(
                    select(Channel).where(Channel.id == channel_id)
                )
                channel = result.scalar_one_or_none()
                
                if not channel:
                    logger.error(f"Channel {channel_id} not found in database")
                    return {'no_data': True}
                
                telegram_channel_id = channel.telegram_id
                
                # Get channel info from Telegram
                try:
                    chat = await self.bot.get_chat(telegram_channel_id)
                    logger.info(f"Got chat info for {chat.title}")
                except TelegramError as e:
                    logger.error(f"Failed to get chat info: {e}")
                    return {'no_data': True, 'error': 'Нет доступа к каналу'}
                
                # Get published posts from database for this period
                posts_query = (
                    select(Post)
                    .where(Post.channel_id == channel_id)
                    .where(Post.status == PostStatus.PUBLISHED)
                    .where(Post.published_at >= period_start)
                    .where(Post.published_at <= period_end)
                )
                posts_result = await session.execute(posts_query)
                posts = posts_result.scalars().all()
                
                if not posts:
                    logger.info(f"No published posts found for channel {channel_id}")
                    return {'no_data': True, 'message': 'Нет опубликованных постов за период'}
                
                # Parse stats for each post
                total_views = 0
                total_reactions = 0
                total_shares = 0
                posts_with_stats = []
                
                for post in posts:
                    # Try to get message from Telegram
                    # Note: Bot API doesn't provide view counts for channel posts
                    # We can only get this if bot is admin with proper permissions
                    
                    # For now, we'll use data from our database if it exists
                    if post.metrics:
                        total_views += post.metrics.views
                        total_reactions += post.metrics.reactions
                        total_shares += post.metrics.shares
                        
                        posts_with_stats.append({
                            'post_id': post.id,
                            'views': post.metrics.views,
                            'reactions': post.metrics.reactions,
                            'shares': post.metrics.shares,
                            'engagement_rate': post.metrics.engagement_rate * 100,
                            'published_at': post.published_at.isoformat() if post.published_at else None
                        })
                
                if not posts_with_stats:
                    logger.info(f"No metrics found for posts in channel {channel_id}")
                    return {
                        'no_data': True,
                        'message': 'Статистика еще не собрана. Добавьте метрики к постам.'
                    }
                
                # Calculate totals
                total_posts = len(posts)
                total_engagement = total_reactions + total_shares
                engagement_rate = (total_engagement / total_views * 100) if total_views > 0 else 0
                
                # Sort by engagement
                posts_with_stats.sort(key=lambda x: x['engagement_rate'], reverse=True)
                top_posts = posts_with_stats[:5]
                
                # Calculate growth
                previous_period_start = period_start - (period_end - period_start)
                previous_query = (
                    select(Post)
                    .where(Post.channel_id == channel_id)
                    .where(Post.status == PostStatus.PUBLISHED)
                    .where(Post.published_at >= previous_period_start)
                    .where(Post.published_at < period_start)
                )
                previous_result = await session.execute(previous_query)
                previous_posts = len(previous_result.scalars().all())
                
                growth = 0.0
                if previous_posts > 0:
                    growth = ((total_posts - previous_posts) / previous_posts) * 100
                
                # Find best posting time
                best_hour = 18  # Default
                if posts_with_stats:
                    hour_engagement = {}
                    for post_stat in posts_with_stats:
                        for post in posts:
                            if post.id == post_stat['post_id'] and post.published_at:
                                hour = post.published_at.hour
                                if hour not in hour_engagement:
                                    hour_engagement[hour] = []
                                hour_engagement[hour].append(post_stat['engagement_rate'])
                    
                    if hour_engagement:
                        avg_by_hour = {
                            hour: sum(rates) / len(rates)
                            for hour, rates in hour_engagement.items()
                        }
                        best_hour = max(avg_by_hour.items(), key=lambda x: x[1])[0]
                
                best_time = f"{best_hour:02d}:00-{(best_hour+2):02d}:00"
                
                logger.info(
                    f"Parsed stats for channel {channel_id}: "
                    f"{total_posts} posts, {total_views} views, {engagement_rate:.2f}% engagement"
                )
                
                result = {
                    'channel_name': channel.name,
                    'views': total_views,
                    'reactions': total_reactions,
                    'shares': total_shares,
                    'comments': 0,  # Not available via Bot API
                    'engagement_rate': engagement_rate,
                    'total_posts': total_posts,
                    'growth': growth,
                    'best_time': best_time,
                    'top_posts': top_posts,
                    'member_count': chat.member_count if hasattr(chat, 'member_count') else None
                }
                
                break  # Exit after first session
                
            return result
            
        except Exception as e:
            logger.error(f"Error parsing channel stats: {e}", exc_info=True)
            return {'no_data': True, 'error': str(e)}
    
    async def update_post_metrics_from_telegram(
        self,
        channel_id: int,
        post_id: int,
        telegram_message_id: int
    ) -> bool:
        """Update post metrics from Telegram.
        
        Note: Telegram Bot API doesn't provide view counts for regular bots.
        This would require using MTProto API or having admin access.
        
        Args:
            channel_id: Database channel ID
            post_id: Database post ID
            telegram_message_id: Telegram message ID
            
        Returns:
            True if updated successfully
        """
        logger.info(f"Attempting to update metrics for post {post_id}")
        
        try:
            async for session in get_session():
                # Get channel
                from sqlalchemy import select
                result = await session.execute(
                    select(Channel).where(Channel.id == channel_id)
                )
                channel = result.scalar_one_or_none()
                
                if not channel:
                    return False
                
                # Note: Bot API doesn't provide view counts
                # You would need to use Telethon or Pyrogram for this
                logger.warning(
                    "View count updates require MTProto API (Telethon/Pyrogram). "
                    "Bot API doesn't provide this data."
                )
                
                break
                
            return False
            
        except Exception as e:
            logger.error(f"Error updating post metrics: {e}")
            return False
