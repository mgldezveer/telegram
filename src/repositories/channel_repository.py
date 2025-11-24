"""Channel repository."""

from typing import Optional
from datetime import datetime
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from src.models import Channel


class ChannelRepository:
    """Repository for Channel operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, channel: Channel) -> Channel:
        """Create a new channel."""
        self.session.add(channel)
        await self.session.commit()
        await self.session.refresh(channel)
        return channel
    
    async def get_by_id(self, channel_id: int) -> Optional[Channel]:
        """Get channel by ID."""
        result = await self.session.execute(
            select(Channel).where(Channel.id == channel_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_telegram_id(self, telegram_id: int) -> Optional[Channel]:
        """Get channel by Telegram ID."""
        result = await self.session.execute(
            select(Channel).where(Channel.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()
    
    async def get_all_active(self) -> list[Channel]:
        """Get all active channels."""
        result = await self.session.execute(
            select(Channel).where(Channel.active == True)
        )
        return list(result.scalars().all())
    
    async def update(self, channel_id: int, **kwargs) -> None:
        """Update channel."""
        kwargs["updated_at"] = datetime.utcnow()
        await self.session.execute(
            update(Channel).where(Channel.id == channel_id).values(**kwargs)
        )
        await self.session.commit()
    
    async def archive(self, channel_id: int) -> None:
        """Archive a channel."""
        await self.session.execute(
            update(Channel).where(Channel.id == channel_id).values(
                active=False,
                archived_at=datetime.utcnow()
            )
        )
        await self.session.commit()
