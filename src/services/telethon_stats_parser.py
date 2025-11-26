"""Real statistics parser using Telethon (MTProto API)."""

import logging
from datetime import datetime, timedelta
from typing import Optional
from telethon import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.errors import ChannelPrivateError, ChatAdminRequiredError
from src.models import get_session, Post, Metrics, PostStatus, Channel
from src.config import config

logger = logging.getLogger(__name__)


class TelethonStatsParser:
    """Parser for real Telegram channel statistics using MTProto."""
    
    def __init__(self, api_id: int, api_hash: str, session_name: str = "bot_stats"):
        """Initialize Telethon client.
        
        Args:
            api_id: Telegram API ID (get from my.telegram.org)
            api_hash: Telegram API Hash
            session_name: Session file name
        """
        self.client = TelegramClient(session_name, api_id, api_hash)
        self._started = False
    
    async def start(self):
        """Start Telethon client."""
        if not self._started:
            await self.client.start()
            self._started = True
            logger.info("Telethon client started")
    
    async def stop(self):
        """Stop Telethon client."""
        if self._started:
            await self.client.disconnect()
            self._started = False
            logger.info("Telethon client stopped")
    
    async def get_channel_stats(
        self,
        channel_username: str,
        period_days: int = 30
    ) -> dict:
        """Get real statistics from Telegram channel.
        
        Args:
            channel_username: Channel username (without @)
            period_days: Number of days to analyze
            
        Returns:
            Dictionary with real statistics
        """
        logger.info(f"Getting stats for @{channel_username} for last {period_days} days")
        
        try:
            await self.start()
            
            # Get channel entity
            try:
                channel = await self.client.get_entity(channel_username)
            except (ChannelPrivateError, ValueError) as e:
                logger.error(f"Cannot access channel @{channel_username}: {e}")
                return {
                    'no_data': True,
                    'error': 'Канал недоступен или приватный'
                }
            
            # Get full channel info
            try:
                full_channel = await self.client(GetFullChannelRequest(channel))
                member_count = full_channel.full_chat.participants_count
            except ChatAdminRequiredError:
                member_count = None
                logger.warning("Cannot get member count - admin rights required")
            
            # Get messages from last N days
            period_start = datetime.now() - timedelta(days=period_days)
            
            messages = []
            offset_id = 0
            limit = 100
            
            while True:
                history = await self.client(GetHistoryRequest(
                    peer=channel,
                    offset_id=offset_id,
                    offset_date=None,
                    add_offset=0,
                    limit=limit,
                    max_id=0,
                    min_id=0,
                    hash=0
                ))
                
                if not history.messages:
                    break
                
                for message in history.messages:
                    if message.date < period_start:
                        break
                    messages.append(message)
                
                # Check if we've gone back far enough
                if history.messages[-1].date < period_start:
                    break
                
                offset_id = history.messages[-1].id
                
                # Limit to prevent too many requests
                if len(messages) >= 500:
                    break
            
            # Filter messages within period
            messages = [m for m in messages if m.date >= period_start]
            
            if not messages:
                return {
                    'no_data': True,
                    'message': f'Нет постов за последние {period_days} дней'
                }
            
            # Calculate statistics
            total_posts = len(messages)
            total_views = sum(m.views or 0 for m in messages)
            total_forwards = sum(m.forwards or 0 for m in messages)
            total_reactions = 0
            
            # Count reactions
            for message in messages:
                if hasattr(message, 'reactions') and message.reactions:
                    for reaction in message.reactions.results:
                        total_reactions += reaction.count
            
            # Calculate engagement
            total_engagement = total_reactions + total_forwards
            engagement_rate = (total_engagement / total_views * 100) if total_views > 0 else 0
            
            # Get top posts
            top_posts = []
            for message in sorted(messages, key=lambda m: m.views or 0, reverse=True)[:5]:
                msg_reactions = 0
                if hasattr(message, 'reactions') and message.reactions:
                    msg_reactions = sum(r.count for r in message.reactions.results)
                
                msg_engagement = msg_reactions + (message.forwards or 0)
                msg_engagement_rate = (msg_engagement / message.views * 100) if message.views else 0
                
                top_posts.append({
                    'message_id': message.id,
                    'views': message.views or 0,
                    'reactions': msg_reactions,
                    'forwards': message.forwards or 0,
                    'engagement_rate': msg_engagement_rate,
                    'date': message.date.isoformat(),
                    'text': message.text[:100] if message.text else '[Media]'
                })
            
            # Find best posting time
            hour_stats = {}
            for message in messages:
                hour = message.date.hour
                if hour not in hour_stats:
                    hour_stats[hour] = {'views': 0, 'count': 0}
                hour_stats[hour]['views'] += message.views or 0
                hour_stats[hour]['count'] += 1
            
            # Calculate average views per hour
            avg_views_by_hour = {
                hour: stats['views'] / stats['count']
                for hour, stats in hour_stats.items()
            }
            
            best_hour = max(avg_views_by_hour.items(), key=lambda x: x[1])[0] if avg_views_by_hour else 18
            best_time = f"{best_hour:02d}:00-{(best_hour+2):02d}:00"
            
            # Calculate growth (compare with previous period)
            previous_period_start = period_start - timedelta(days=period_days)
            previous_messages = [m for m in messages if previous_period_start <= m.date < period_start]
            previous_posts = len(previous_messages)
            
            growth = 0.0
            if previous_posts > 0:
                growth = ((total_posts - previous_posts) / previous_posts) * 100
            
            logger.info(
                f"Stats for @{channel_username}: "
                f"{total_posts} posts, {total_views} views, {engagement_rate:.2f}% engagement"
            )
            
            return {
                'channel_username': channel_username,
                'member_count': member_count,
                'views': total_views,
                'reactions': total_reactions,
                'shares': total_forwards,
                'comments': 0,  # Would need to check replies
                'engagement_rate': engagement_rate,
                'total_posts': total_posts,
                'growth': growth,
                'best_time': best_time,
                'top_posts': top_posts,
                'period_days': period_days
            }
            
        except Exception as e:
            logger.error(f"Error getting channel stats: {e}", exc_info=True)
            return {'no_data': True, 'error': str(e)}
    
    async def sync_channel_posts_to_db(
        self,
        channel_id: int,
        channel_username: str,
        period_days: int = 30
    ) -> int:
        """Sync channel posts and their metrics to database.
        
        Args:
            channel_id: Database channel ID
            channel_username: Telegram channel username
            period_days: Days to sync
            
        Returns:
            Number of posts synced
        """
        logger.info(f"Syncing posts for channel {channel_id} (@{channel_username})")
        
        try:
            await self.start()
            
            # Get channel
            channel = await self.client.get_entity(channel_username)
            
            # Get messages
            period_start = datetime.now() - timedelta(days=period_days)
            messages = []
            offset_id = 0
            
            while True:
                history = await self.client(GetHistoryRequest(
                    peer=channel,
                    offset_id=offset_id,
                    offset_date=None,
                    add_offset=0,
                    limit=100,
                    max_id=0,
                    min_id=0,
                    hash=0
                ))
                
                if not history.messages:
                    break
                
                for message in history.messages:
                    if message.date < period_start:
                        break
                    messages.append(message)
                
                if history.messages[-1].date < period_start:
                    break
                
                offset_id = history.messages[-1].id
                
                if len(messages) >= 200:
                    break
            
            # Save to database
            synced_count = 0
            
            async for session in get_session():
                from sqlalchemy import select
                
                for message in messages:
                    # Check if post already exists
                    result = await session.execute(
                        select(Post).where(
                            Post.channel_id == channel_id,
                            Post.content == (message.text or '')[:500]
                        )
                    )
                    existing_post = result.scalar_one_or_none()
                    
                    if not existing_post:
                        # Create new post
                        post = Post(
                            content=message.text or '[Media content]',
                            channel_id=channel_id,
                            status=PostStatus.PUBLISHED,
                            published_at=message.date,
                            created_at=message.date
                        )
                        session.add(post)
                        await session.flush()
                        post_id = post.id
                    else:
                        post_id = existing_post.id
                    
                    # Create or update metrics
                    result = await session.execute(
                        select(Metrics).where(Metrics.post_id == post_id)
                    )
                    existing_metrics = result.scalar_one_or_none()
                    
                    msg_reactions = 0
                    if hasattr(message, 'reactions') and message.reactions:
                        msg_reactions = sum(r.count for r in message.reactions.results)
                    
                    views = message.views or 0
                    forwards = message.forwards or 0
                    engagement = msg_reactions + forwards
                    engagement_rate = (engagement / views) if views > 0 else 0
                    
                    if existing_metrics:
                        # Update
                        existing_metrics.views = views
                        existing_metrics.reactions = msg_reactions
                        existing_metrics.shares = forwards
                        existing_metrics.engagement_rate = engagement_rate
                        existing_metrics.updated_at = datetime.utcnow()
                    else:
                        # Create
                        metrics = Metrics(
                            post_id=post_id,
                            views=views,
                            reactions=msg_reactions,
                            shares=forwards,
                            comments=0,
                            engagement_rate=engagement_rate
                        )
                        session.add(metrics)
                    
                    synced_count += 1
                
                await session.commit()
                break
            
            logger.info(f"Synced {synced_count} posts for channel {channel_id}")
            return synced_count
            
        except Exception as e:
            logger.error(f"Error syncing posts: {e}", exc_info=True)
            return 0
