"""Main entry point for AI Content Bot."""

import asyncio
import logging
from src.config import config
from src.logging_config import setup_logging
from src.bot.controller import BotController
from src.models import init_db
from src.cache import cache
from src.monitoring import start_monitoring_server

logger = logging.getLogger(__name__)


async def main():
    """Main application entry point."""
    # Setup logging
    setup_logging(config.log_level)
    
    logger.info("=" * 50)
    logger.info("AI Content Bot Starting")
    logger.info("=" * 50)
    
    try:
        # Initialize database
        logger.info("Initializing database...")
        await init_db()
        
        # Connect to Redis (optional for local development)
        logger.info("Connecting to Redis...")
        try:
            await cache.connect()
            logger.info("✅ Redis connected")
        except Exception as e:
            logger.warning(f"⚠️  Redis not available: {e}")
            logger.warning("⚠️  Running without cache (development mode)")
        
        # Start monitoring server (optional)
        logger.info("Starting monitoring server...")
        try:
            monitoring_runner = await start_monitoring_server(
                port=config.monitoring_port
            )
            logger.info("✅ Monitoring server started")
        except Exception as e:
            logger.warning(f"⚠️  Monitoring server not available: {e}")
            logger.warning("⚠️  Running without monitoring (development mode)")
        
        # Create and start bot
        logger.info("Starting bot controller...")
        controller = BotController()
        
        # Run bot
        await controller.start()
        
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        raise
    finally:
        # Cleanup
        logger.info("Shutting down...")
        await cache.close()
        logger.info("Shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())
