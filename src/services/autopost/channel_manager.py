"""Channel Manager for auto-posting system."""

import logging
from typing import List, Optional, Dict
from datetime import datetime
from sqlalchemy import select, update, delete
from sqlalchemy.exc import IntegrityError
from telegram import Bot
from telegram.error import TelegramError

from src.models.autopost import AutoPostChannel, PostStatus
from src.database.autopost_db import autopost_db

logger = logging.getLogger(__name__)


class ChannelConfig:
    """Channel configuration."""
    
    def __init__(
        self,
        name: str,
        auto_publish: bool = True,
        require_moderation: bool = False,
        default_style: str = "professional",
        default_language: str = "ru",
        post_frequency: int = 3
    ):
        self.name = name
        self.auto_publish = auto_publish
        self.require_moderation = require_moderation
        self.default_style = default_style
        self.default_language = default_language
        self.post_frequency = post_frequency
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "auto_publish": self.auto_publish,
            "require_moderation": self.require_moderation,
            "default_style": self.default_style,
            "default_language": self.default_language,
            "post_frequency": self.post_frequency
        }


class PermissionStatus:
    """Channel permission status."""
    
    def __init__(
        self,
        has_access: bool,
        is_admin: bool = False,
        can_post: bool = False,
        error: Optional[str] = None
    ):
        self.has_access = has_access
        self.is_admin = is_admin
        self.can_post = can_post
        self.error = error
    
    def __repr__(self):
        return f"<PermissionStatus(access={self.has_access}, admin={self.is_admin}, post={self.can_post})>"


class AutoPostChannelManager:
    """Manager for auto-posting channels."""
    
    def __init__(self, bot: Bot):
        """Initialize channel manager.
        
        Args:
            bot: Telegram bot instance
        """
        self.bot = bot
    
    async def add_channel(
        self,
        channel_id: int,
        config: ChannelConfig
    ) -> AutoPostChannel:
        """Add new channel for auto-posting.
        
        Args:
            channel_id: Telegram channel ID
            config: Channel configuration
            
        Returns:
            Created channel object
            
        Raises:
            ValueError: If channel already exists or permissions invalid
        """
        logger.info(f"Adding channel {channel_id}: {config.name}")
        
        # Check permissions first
        permissions = await self.check_permissions(channel_id)
        if not permissions.can_post:
            raise ValueError(
                f"Bot cannot post to channel {channel_id}: {permissions.error}"
            )
        
        async with autopost_db.session() as session:
            # Check if channel already exists
            result = await session.execute(
                select(AutoPostChannel).where(AutoPostChannel.id == channel_id)
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                if existing.is_active:
                    raise ValueError(f"Channel {channel_id} already exists")
                else:
                    # Reactivate existing channel
                    existing.is_active = True
                    existing.name = config.name
                    existing.settings = config.to_dict()
                    existing.updated_at = datetime.utcnow()
                    await session.commit()
                    logger.info(f"✅ Reactivated channel {channel_id}")
                    return existing
            
            # Create new channel
            channel = AutoPostChannel(
                id=channel_id,
                name=config.name,
                is_active=True,
                settings=config.to_dict()
            )
            
            session.add(channel)
            await session.commit()
            await session.refresh(channel)
            
            logger.info(f"✅ Added channel {channel_id}: {config.name}")
            return channel
    
    async def remove_channel(self, channel_id: int) -> bool:
        """Remove (deactivate) channel.
        
        Args:
            channel_id: Telegram channel ID
            
        Returns:
            True if channel was removed, False if not found
        """
        logger.info(f"Removing channel {channel_id}")
        
        async with autopost_db.session() as session:
            result = await session.execute(
                select(AutoPostChannel).where(AutoPostChannel.id == channel_id)
            )
            channel = result.scalar_one_or_none()
            
            if not channel:
                logger.warning(f"Channel {channel_id} not found")
                return False
            
            # Deactivate instead of delete to preserve history
            channel.is_active = False
            channel.updated_at = datetime.utcnow()
            
            # Cancel all queued posts for this channel
            from src.models.autopost import AutoPost
            await session.execute(
                update(AutoPost)
                .where(
                    AutoPost.channel_id == channel_id,
                    AutoPost.status.in_([PostStatus.DRAFT.value, PostStatus.QUEUED.value])
                )
                .values(status=PostStatus.CANCELLED.value)
            )
            
            await session.commit()
            logger.info(f"✅ Removed channel {channel_id}")
            return True
    
    async def get_channel(self, channel_id: int) -> Optional[AutoPostChannel]:
        """Get channel by ID.
        
        Args:
            channel_id: Telegram channel ID
            
        Returns:
            Channel object or None if not found
        """
        async with autopost_db.session() as session:
            result = await session.execute(
                select(AutoPostChannel).where(AutoPostChannel.id == channel_id)
            )
            return result.scalar_one_or_none()
    
    async def list_channels(self, active_only: bool = True) -> List[AutoPostChannel]:
        """List all channels.
        
        Args:
            active_only: If True, return only active channels
            
        Returns:
            List of channel objects
        """
        async with autopost_db.session() as session:
            query = select(AutoPostChannel)
            
            if active_only:
                query = query.where(AutoPostChannel.is_active == True)
            
            query = query.order_by(AutoPostChannel.created_at.desc())
            
            result = await session.execute(query)
            return list(result.scalars().all())
    
    async def update_settings(
        self,
        channel_id: int,
        settings: Dict
    ) -> bool:
        """Update channel settings.
        
        Args:
            channel_id: Telegram channel ID
            settings: New settings dictionary
            
        Returns:
            True if updated, False if channel not found
        """
        logger.info(f"Updating settings for channel {channel_id}")
        
        async with autopost_db.session() as session:
            result = await session.execute(
                select(AutoPostChannel).where(AutoPostChannel.id == channel_id)
            )
            channel = result.scalar_one_or_none()
            
            if not channel:
                logger.warning(f"Channel {channel_id} not found")
                return False
            
            # Merge new settings with existing
            current_settings = channel.settings or {}
            current_settings.update(settings)
            
            channel.settings = current_settings
            channel.updated_at = datetime.utcnow()
            
            await session.commit()
            logger.info(f"✅ Updated settings for channel {channel_id}")
            return True
    
    async def check_permissions(self, channel_id: int) -> PermissionStatus:
        """Check bot permissions in channel.
        
        Args:
            channel_id: Telegram channel ID
            
        Returns:
            Permission status object
        """
        try:
            # Get bot's member status in channel
            member = await self.bot.get_chat_member(channel_id, self.bot.id)
            
            # Check if bot is admin
            is_admin = member.status in ['creator', 'administrator']
            
            # Check posting permissions
            can_post = False
            if is_admin:
                # Administrators can post
                can_post = True
            elif member.status == 'member':
                # Regular members can post in public channels
                try:
                    chat = await self.bot.get_chat(channel_id)
                    can_post = chat.type == 'channel'
                except:
                    pass
            
            return PermissionStatus(
                has_access=True,
                is_admin=is_admin,
                can_post=can_post
            )
            
        except TelegramError as e:
            logger.error(f"Failed to check permissions for channel {channel_id}: {e}")
            return PermissionStatus(
                has_access=False,
                error=str(e)
            )
    
    async def get_channel_info(self, channel_id: int) -> Optional[Dict]:
        """Get channel information from Telegram or database.
        
        Args:
            channel_id: Telegram channel ID
            
        Returns:
            Channel info dictionary or None if error
        """
        try:
            # Try to get from Telegram first
            chat = await self.bot.get_chat(channel_id)
            return {
                'id': chat.id,
                'title': chat.title,
                'username': chat.username,
                'type': chat.type,
                'description': chat.description
            }
        except TelegramError as e:
            logger.warning(f"Cannot get channel info from Telegram for {channel_id}: {e}")
            
            # Fallback to database
            try:
                async with autopost_db.session() as session:
                    result = await session.execute(
                        select(AutoPostChannel).where(AutoPostChannel.id == channel_id)
                    )
                    channel = result.scalar_one_or_none()
                    
                    if channel:
                        logger.info(f"Using database info for channel {channel_id}")
                        return {
                            'id': channel.id,
                            'title': channel.name,
                            'username': None,
                            'type': 'channel',
                            'description': None,
                            'from_db': True  # Flag to indicate this is from DB
                        }
            except Exception as db_error:
                logger.error(f"Failed to get channel from database: {db_error}")
            
            return None
