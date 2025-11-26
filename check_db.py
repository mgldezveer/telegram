"""Check database channels."""

import asyncio
import logging
from src.database.autopost_db import autopost_db
from src.models.autopost import AutoPostChannel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def check_channels():
    """Check channels in database."""
    try:
        await autopost_db.initialize()
        
        async with autopost_db.session() as session:
            from sqlalchemy import select
            result = await session.execute(select(AutoPostChannel))
            channels = result.scalars().all()
            
            logger.info(f"Found {len(channels)} channels:")
            for channel in channels:
                logger.info(f"  ID: {channel.id}, Name: {channel.name}, Active: {channel.is_active}")
                logger.info(f"  Settings: {channel.settings}")
        
    except Exception as e:
        logger.error(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(check_channels())
