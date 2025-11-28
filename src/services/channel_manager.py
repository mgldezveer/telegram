"""Channel Manager service for auto-posting system."""

import logging
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import select, update, delete
from sqlalchemy.exc import IntegrityError

from src.models.autopost import AutoPostChannel, PostStatus
from src.database.autopost_db import autopost_db

logger = logging.getLogger(__name__)


class ChannelSettings:
    """Channel settings data class."""
    
    def __init__(
        self,
        auto_publish: bool = True,
        require_moderation: bool = False,
        default_style: str = "professional",
        default_language: str = "ru",
        post_frequency: int = 3
    ):
        self.auto_publish = auto_publish
        self.require_moderation = require_moderation
        self.default_style = default_style
        self.default_language = default_language
        self.post_frequency = post_frequency
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "auto_publish": self.auto_publish,
            "require_moderation": self.require_moderation,
            "default_style": self.default_style,
            "default_language": self.default_language,
            "post_frequency": self.post_frequency
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChannelSettings':
        """Create from dictionary."""
        return cls(
            auto_publish=data.get("auto_publish", True),
            require_moderation=data.get("require_moderation", False),
            default_style=data.get("default_style", "professional"),
            default_language=data.get("default_language", "ru"),
            post_frequency=data.get("post_frequency", 3)
        )


class PermissionStatus:
    """Permission status data class."""
    
    def __init__(
        self,
        can_post: bool = False,
        is_admin: bool = False,
        error_message: Optional[str] = None
    ):
        self.can_post = can_post
        self.is_admin = is_admin
        self.error_message = error_message
    
    @property
    def is_valid(self) -> bool:
        """Check if permissions are valid."""
        return self.can_post and self.is_admin


class ChannelManager:
    """Manager for auto-posting channels."""
    
    def __init__(self, bot=None):
        """Initialize channel manager.
        
        Args:
            bot: Telegram bot instance for permission checking
        """
        self.bot = bot
    
    async def add_channel(
        self,
        channel_id: int,
        name: str,
        settings: Optional[ChannelSettings] = None
    ) -> AutoPostChannel:
        """Add a new channel to the system.
        
        Args:
            channel_id: Telegram channel ID
            name: Channel name
            settings: Channel settings (optional)
        
        Returns:
            Created channel object
        
        Raises:
            ValueError: If channel already exists
            RuntimeError: If database operation fails
        """
        try:
            # Check if channel already exists
            existing = await self.get_channel(channel_id)
            if existing:
                raise ValueError(f"Channel {channel_id} already exists")
            
            # Create default settings if not provided
            if settings is None:
                settings = ChannelSettings()
            
            # Create channel
            async with autopost_db.session() as session:
                channel = AutoPostChannel(
                    id=channel_id,
                    name=name,
                    is_active=True,
                    settings=settings.to_dict(),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                session.add(channel)
                await session.commit()
                await session.refresh(channel)
                
                logger.info(f"✅ Added channel: {name} (ID: {channel_id})")
                return channel
                
        except IntegrityError as e:
            logger.error(f"❌ Channel {channel_id} already exists: {e}")
            raise ValueError(f"Channel {channel_id} already exists")
        except Exception as e:
            logger.error(f"❌ Failed to add channel {channel_id}: {e}")
            raise RuntimeError(f"Failed to add channel: {e}")
    
    async def remove_channel(self, channel_id: int) -> bool:
        """Remove (deactivate) a channel.
        
        Args:
            channel_id: Telegram channel ID
        
        Returns:
            True if channel was removed, False if not found
        """
        try:
            async with autopost_db.session() as session:
                # Update channel to inactive
                result = await session.execute(
                    update(AutoPostChannel)
                    .where(AutoPostChannel.id == channel_id)
                    .values(is_active=False, updated_at=datetime.utcnow())
                )
                
                if result.rowcount > 0:
                    await session.commit()
                    logger.info(f"✅ Deactivated channel: {channel_id}")
                    return True
                else:
                    logger.warning(f"⚠️ Channel {channel_id} not found")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Failed to remove channel {channel_id}: {e}")
            raise RuntimeError(f"Failed to remove channel: {e}")
    
    async def get_channel(self, channel_id: int) -> Optional[AutoPostChannel]:
        """Get channel by ID.
        
        Args:
            channel_id: Telegram channel ID
        
        Returns:
            Channel object or None if not found
        """
        try:
            async with autopost_db.session() as session:
                result = await session.execute(
                    select(AutoPostChannel).where(AutoPostChannel.id == channel_id)
                )
                channel = result.scalar_one_or_none()
                return channel
                
        except Exception as e:
            logger.error(f"❌ Failed to get channel {channel_id}: {e}")
            return None
    
    async def list_channels(self, active_only: bool = True) -> List[AutoPostChannel]:
        """List all channels.
        
        Args:
            active_only: If True, return only active channels
        
        Returns:
            List of channel objects
        """
        try:
            async with autopost_db.session() as session:
                query = select(AutoPostChannel)
                
                if active_only:
                    query = query.where(AutoPostChannel.is_active == True)
                
                query = query.order_by(AutoPostChannel.created_at.desc())
                
                result = await session.execute(query)
                channels = result.scalars().all()
                
                return list(channels)
                
        except Exception as e:
            logger.error(f"❌ Failed to list channels: {e}")
            return []
    
    async def update_settings(
        self,
        channel_id: int,
        settings: ChannelSettings
    ) -> bool:
        """Update channel settings.
        
        Args:
            channel_id: Telegram channel ID
            settings: New channel settings
        
        Returns:
            True if settings were updated, False if channel not found
        """
        try:
            async with autopost_db.session() as session:
                result = await session.execute(
                    update(AutoPostChannel)
                    .where(AutoPostChannel.id == channel_id)
                    .values(
                        settings=settings.to_dict(),
                        updated_at=datetime.utcnow()
                    )
                )
                
                if result.rowcount > 0:
                    await session.commit()
                    logger.info(f"✅ Updated settings for channel: {channel_id}")
                    return True
                else:
                    logger.warning(f"⚠️ Channel {channel_id} not found")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Failed to update settings for channel {channel_id}: {e}")
            raise RuntimeError(f"Failed to update settings: {e}")
    
    async def check_permissions(self, channel_id: int) -> PermissionStatus:
        """Check bot permissions in channel.
        
        Args:
            channel_id: Telegram channel ID
        
        Returns:
            Permission status object
        """
        if not self.bot:
            logger.warning("⚠️ Bot instance not provided, skipping permission check")
            return PermissionStatus(
                can_post=True,
                is_admin=True,
                error_message="Permission check skipped (no bot instance)"
            )
        
        try:
            # Get bot's member status in channel
            member = await self.bot.get_chat_member(channel_id, self.bot.id)
            
            # Check if bot is admin
            is_admin = member.status in ['creator', 'administrator']
            
            # Check if bot can post
            can_post = False
            if member.status == 'creator':
                can_post = True
            elif member.status == 'administrator':
                can_post = member.can_post_messages or member.can_edit_messages
            
            if is_admin and can_post:
                logger.info(f"✅ Bot has valid permissions in channel {channel_id}")
                return PermissionStatus(can_post=True, is_admin=True)
            else:
                error_msg = "Bot is not admin" if not is_admin else "Bot cannot post messages"
                logger.warning(f"⚠️ {error_msg} in channel {channel_id}")
                return PermissionStatus(
                    can_post=can_post,
                    is_admin=is_admin,
                    error_message=error_msg
                )
                
        except Exception as e:
            logger.error(f"❌ Failed to check permissions for channel {channel_id}: {e}")
            return PermissionStatus(
                can_post=False,
                is_admin=False,
                error_message=str(e)
            )
    
    async def get_settings(self, channel_id: int) -> Optional[ChannelSettings]:
        """Get channel settings.
        
        Args:
            channel_id: Telegram channel ID
        
        Returns:
            Channel settings or None if channel not found
        """
        channel = await self.get_channel(channel_id)
        if channel and channel.settings:
            return ChannelSettings.from_dict(channel.settings)
        return None
    
    async def activate_channel(self, channel_id: int) -> bool:
        """Activate a channel.
        
        Args:
            channel_id: Telegram channel ID
        
        Returns:
            True if channel was activated, False if not found
        """
        try:
            async with autopost_db.session() as session:
                result = await session.execute(
                    update(AutoPostChannel)
                    .where(AutoPostChannel.id == channel_id)
                    .values(is_active=True, updated_at=datetime.utcnow())
                )
                
                if result.rowcount > 0:
                    await session.commit()
                    logger.info(f"✅ Activated channel: {channel_id}")
                    return True
                else:
                    logger.warning(f"⚠️ Channel {channel_id} not found")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Failed to activate channel {channel_id}: {e}")
            raise RuntimeError(f"Failed to activate channel: {e}")
