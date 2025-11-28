"""Main entry point for Auto-Posting Bot."""

import asyncio
import logging
import os
from dotenv import load_dotenv

from src.bot.autopost_bot import AutoPostBot

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def main():
    """Main function."""
    # Get configuration from environment
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    admin_ids_str = os.getenv("ADMIN_IDS", "")
    
    if not token:
        logger.error("❌ TELEGRAM_BOT_TOKEN not set in environment")
        return
    
    # Parse admin IDs
    admin_ids = []
    if admin_ids_str:
        try:
            admin_ids = [int(id.strip()) for id in admin_ids_str.split(",")]
        except ValueError:
            logger.error("❌ Invalid ADMIN_IDS format")
            return
    
    if not admin_ids:
        logger.warning("⚠️ No admin IDs configured")
    
    # Create and start bot
    bot = AutoPostBot(token=token, admin_ids=admin_ids)
    
    try:
        await bot.start()
        
        # Keep running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("🛑 Received shutdown signal")
    finally:
        await bot.stop()


if __name__ == "__main__":
    asyncio.run(main())
