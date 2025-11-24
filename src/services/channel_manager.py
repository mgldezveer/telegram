"""Channel management service."""

import logging
from typing import Optional
from datetime import datetime
from dataclasses import dataclass
from telegram import Bot
from telegram.error import TelegramError
from src.models import Channel, Post, PostStatus
from src.config import config

logger = logging.getLogger(__name__)


@dataclass
class ChannelConfig:
    """Channel configuration."""
    name: str
    posting_frequency: int = 3
    optimal_times: list[str] = None
    themes: list[str] = None
    style_tone: str = "professional"
    style_length: str = "medium"
    emoji_usage: bool = True
    hashtag_count: int = 3
    media_preference: str = "text"


@dataclass
class PublishResult:
    """Result of post publication."""
    success: bool
    message_id: Optional[int] = None
    error: Optional[str] = None


class ChannelManager:
    """Manager for channel operations and publishing."""
    
    def __init__(self, bot: Bot):
        self.bot = bot
        self.content_queues: dict[int, list[Post]] = {}
    
    async def register_channel(
        self,
        telegram_id: int,
        channel_config: ChannelConfig
    ) -> Channel:
        """Register a new channel."""
        logger.info(f"Registering channel {telegram_id}: {channel_config.name}")
        
        from src.models.base import async_session_maker
        from src.repositories.channel_repository import ChannelRepository
        
        async with async_session_maker() as session:
            channel_repo = ChannelRepository(session)
            
            # Check if channel already exists
            existing = await channel_repo.get_by_telegram_id(telegram_id)
            
            if existing:
                logger.info(f"Channel {telegram_id} already exists, updating")
                # Update existing channel
                await channel_repo.update(
                    existing.id,
                    name=channel_config.name,
                    posting_frequency=channel_config.posting_frequency,
                    optimal_times=channel_config.optimal_times or [],
                    themes=channel_config.themes or [],
                    style_tone=channel_config.style_tone,
                    style_length=channel_config.style_length,
                    emoji_usage=channel_config.emoji_usage,
                    hashtag_count=channel_config.hashtag_count,
                    media_preference=channel_config.media_preference,
                    active=True
                )
                channel = await channel_repo.get_by_id(existing.id)
            else:
                # Create new channel
                channel = Channel(
                    telegram_id=telegram_id,
                    name=channel_config.name,
                    posting_frequency=channel_config.posting_frequency,
                    optimal_times=channel_config.optimal_times or [],
                    themes=channel_config.themes or [],
                    style_tone=channel_config.style_tone,
                    style_length=channel_config.style_length,
                    emoji_usage=channel_config.emoji_usage,
                    hashtag_count=channel_config.hashtag_count,
                    media_preference=channel_config.media_preference,
                    active=True
                )
                
                # Save to database
                channel = await channel_repo.create(channel)
            
            # Initialize content queue
            self.content_queues[telegram_id] = []
            
            logger.info(f"Channel {telegram_id} registered successfully")
            return channel
    
    async def publish_post(self, post: Post, channel: Channel) -> PublishResult:
        """Publish a post to a channel."""
        logger.info(f"Publishing post {post.id} to channel {channel.telegram_id}")
        
        try:
            # Prepare message text
            message_text = post.content
            
            # Add hashtags
            if post.hashtags:
                message_text += "\n\n" + " ".join(post.hashtags)
            
            # Send message
            if post.media_url:
                # Send with media
                if post.media_type and post.media_type.startswith('image'):
                    message = await self.bot.send_photo(
                        chat_id=channel.telegram_id,
                        photo=post.media_url,
                        caption=message_text
                    )
                elif post.media_type and post.media_type.startswith('video'):
                    message = await self.bot.send_video(
                        chat_id=channel.telegram_id,
                        video=post.media_url,
                        caption=message_text
                    )
                else:
                    # Fallback to text
                    message = await self.bot.send_message(
                        chat_id=channel.telegram_id,
                        text=message_text
                    )
            else:
                # Send text only
                message = await self.bot.send_message(
                    chat_id=channel.telegram_id,
                    text=message_text
                )
            
            logger.info(f"Post {post.id} published successfully, message_id: {message.message_id}")
            
            return PublishResult(
                success=True,
                message_id=message.message_id
            )
            
        except TelegramError as e:
            logger.error(f"Failed to publish post {post.id}: {e}")
            return PublishResult(
                success=False,
                error=str(e)
            )
        except Exception as e:
            logger.error(f"Unexpected error publishing post {post.id}: {e}")
            return PublishResult(
                success=False,
                error=str(e)
            )
    
    async def get_channel_info(self, telegram_id: int) -> dict:
        """Get channel information from Telegram."""
        try:
            chat = await self.bot.get_chat(telegram_id)
            return {
                'id': chat.id,
                'title': chat.title,
                'type': chat.type,
                'username': chat.username,
                'description': chat.description
            }
        except TelegramError as e:
            logger.error(f"Failed to get channel info for {telegram_id}: {e}")
            return {}
    
    async def remove_channel(self, channel_id: int, telegram_id: int):
        """Remove and archive a channel."""
        logger.info(f"Removing channel {channel_id}")
        
        from src.models.base import async_session_maker
        from src.repositories.channel_repository import ChannelRepository
        
        async with async_session_maker() as session:
            channel_repo = ChannelRepository(session)
            
            # Archive channel in database
            await channel_repo.archive(channel_id)
        
        # Remove from content queues
        if telegram_id in self.content_queues:
            del self.content_queues[telegram_id]
        
        logger.info(f"Channel {channel_id} removed and archived")
    
    async def add_to_queue(self, channel_id: int, post: Post):
        """Add post to channel's content queue."""
        if channel_id not in self.content_queues:
            self.content_queues[channel_id] = []
        
        self.content_queues[channel_id].append(post)
        logger.info(f"Added post {post.id} to queue for channel {channel_id}")
    
    async def get_queue(self, channel_id: int) -> list[Post]:
        """Get channel's content queue."""
        return self.content_queues.get(channel_id, [])
    
    async def update_permissions(self, channel_id: int, permissions: dict):
        """Update channel permissions."""
        logger.info(f"Updating permissions for channel {channel_id}")
        # In production, this would update actual Telegram permissions
        # For now, just log the change
    
    async def get_all_channels(self) -> list[Channel]:
        """Get all registered channels.
        
        Returns:
            List of all registered channels
        """
        from src.models.base import async_session_maker
        from src.repositories.channel_repository import ChannelRepository
        
        try:
            async with async_session_maker() as session:
                repo = ChannelRepository(session)
                channels = await repo.get_all_active()
                logger.info(f"Retrieved {len(channels)} active channels")
                return channels
        except Exception as e:
            logger.error(f"Error getting all channels: {e}")
            return []
