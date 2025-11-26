"""Script to clean up inaccessible channels from database."""

import asyncio
import logging
from src.database.autopost_db import autopost_db
from src.models.autopost import AutoPostChannel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def clean_channels():
    """Remove all channels from database."""
    try:
        # Initialize database
        await autopost_db.initialize()
        
        # Get all channels
        async with autopost_db.session() as session:
            from sqlalchemy import select
            result = await session.execute(select(AutoPostChannel))
            channels = result.scalars().all()
            
            logger.info(f"Found {len(channels)} channels in database")
            
            for channel in channels:
                logger.info(f"Channel ID: {channel.id}, Telegram ID: {channel.telegram_id}, Name: {channel.name}")
            
            # Ask for confirmation
            print("\n⚠️  Do you want to delete ALL channels? (yes/no): ", end="")
            confirm = input().strip().lower()
            
            if confirm == 'yes':
                from sqlalchemy import delete
                await session.execute(delete(AutoPostChannel))
                await session.commit()
                logger.info("✅ All channels deleted successfully")
            else:
                logger.info("❌ Operation cancelled")
        
    except Exception as e:
        logger.error(f"Error cleaning channels: {e}")


if __name__ == "__main__":
    asyncio.run(clean_channels())
