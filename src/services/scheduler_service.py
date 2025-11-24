"""Scheduling service for post management."""

import logging
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from src.models import Post, PostStatus, Channel
from src.config import config

logger = logging.getLogger(__name__)


@dataclass
class ScheduledPost:
    """Scheduled post information."""
    post: Post
    scheduled_time: datetime


class SchedulerService:
    """Service for scheduling and managing post publication."""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler(timezone=config.scheduler.timezone)
        self.scheduled_posts: dict[int, ScheduledPost] = {}
    
    def start(self):
        """Start the scheduler."""
        logger.info("Starting scheduler service")
        self.scheduler.start()
    
    def stop(self):
        """Stop the scheduler."""
        logger.info("Stopping scheduler service")
        self.scheduler.shutdown()
    
    async def schedule_post(
        self,
        post: Post,
        channel: Channel,
        scheduled_time: Optional[datetime] = None
    ) -> ScheduledPost:
        """Schedule a post for publication."""
        if not scheduled_time:
            scheduled_time = await self.get_optimal_time(channel)
        
        # Check for conflicts
        if await self._has_conflict(channel.id, scheduled_time):
            logger.warning(f"Scheduling conflict detected for channel {channel.id}")
            # Adjust time by 5 minutes
            scheduled_time = scheduled_time + timedelta(minutes=5)
        
        # Update post
        post.scheduled_for = scheduled_time
        post.status = PostStatus.SCHEDULED
        
        # Store scheduled post
        scheduled_post = ScheduledPost(post=post, scheduled_time=scheduled_time)
        self.scheduled_posts[post.id] = scheduled_post
        
        logger.info(f"Post {post.id} scheduled for {scheduled_time}")
        return scheduled_post
    
    async def get_optimal_time(self, channel: Channel) -> datetime:
        """Calculate optimal posting time based on channel configuration."""
        now = datetime.utcnow()
        
        # If channel has optimal times configured, use them
        if channel.optimal_times:
            # Find next optimal time
            current_time = now.time()
            for time_str in channel.optimal_times:
                hour, minute = map(int, time_str.split(':'))
                optimal_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                if optimal_time > now:
                    return optimal_time
            
            # If no time today, use first time tomorrow
            hour, minute = map(int, channel.optimal_times[0].split(':'))
            return (now + timedelta(days=1)).replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # Default: distribute posts evenly throughout the day
        posts_per_day = channel.posting_frequency
        hours_between = 24 // posts_per_day
        
        # Find next posting slot
        next_hour = ((now.hour // hours_between) + 1) * hours_between
        if next_hour >= 24:
            next_hour = 0
            now = now + timedelta(days=1)
        
        return now.replace(hour=next_hour, minute=0, second=0, microsecond=0)
    
    async def get_pending_posts(self) -> list[ScheduledPost]:
        """Get all pending scheduled posts."""
        now = datetime.utcnow()
        pending = [
            sp for sp in self.scheduled_posts.values()
            if sp.scheduled_time <= now and sp.post.status == PostStatus.SCHEDULED
        ]
        return pending
    
    async def cancel_scheduled(self, post_id: int) -> bool:
        """Cancel a scheduled post."""
        if post_id in self.scheduled_posts:
            del self.scheduled_posts[post_id]
            logger.info(f"Cancelled scheduled post {post_id}")
            return True
        return False
    
    async def update_frequency(self, channel_id: int, new_frequency: int):
        """Update posting frequency for a channel."""
        logger.info(f"Updating posting frequency for channel {channel_id} to {new_frequency}")
        # In production, this would reschedule all pending posts for this channel
        # For now, just log the change
    
    async def _has_conflict(self, channel_id: int, scheduled_time: datetime) -> bool:
        """Check if there's a scheduling conflict."""
        # Check if any post for this channel is scheduled within 5 minutes
        for sp in self.scheduled_posts.values():
            if sp.post.channel_id == channel_id:
                time_diff = abs((sp.scheduled_time - scheduled_time).total_seconds())
                if time_diff < 300:  # 5 minutes
                    return True
        return False
