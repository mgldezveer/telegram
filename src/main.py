"""Main entry point for AI Content Bot."""

import asyncio
import logging
from src.config import config
from src.logging_config import setup_logging
from src.bot.controller import BotController
from src.models import init_db
from src.cache import cache
from src.monitoring import start_monitoring_server
from src.utils.version_checker import PythonVersionChecker
from src.services.health_check import HealthCheckService

logger = logging.getLogger(__name__)


async def main():
    """Main application entry point."""
    monitoring_runner = None
    
    try:
        # Setup logging
        setup_logging(config.log_level)
        
        logger.info("=" * 50)
        logger.info("AI Content Bot Starting")
        logger.info("=" * 50)
        
        # Check Python version (critical)
        logger.info("Checking Python version...")
        version_result = PythonVersionChecker.log_version_check()
        if not version_result.is_compatible:
            logger.error("❌ Incompatible Python version, exiting")
            return
        
        # Initialize database
        logger.info("Initializing database...")
        try:
            await init_db()
            logger.info("✅ Database initialized")
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            raise
        
        # Connect to Redis with fallback
        logger.info("Connecting to cache...")
        try:
            connection_result = await cache.connect()
            
            if connection_result.backend == 'redis':
                logger.info(f"✅ {connection_result.message}")
            elif connection_result.backend == 'memory':
                logger.warning(f"⚠️  {connection_result.message}")
                logger.info("Starting Redis reconnection task...")
                await cache.start_reconnection_task()
                logger.info("✅ Reconnection task started")
            else:
                logger.error(f"❌ Cache initialization failed")
                
        except Exception as e:
            logger.error(f"❌ Cache connection error: {e}")
            if not cache.fallback_enabled:
                raise
        
        # Initialize health check service
        logger.info("Initializing health check service...")
        try:
            health_service = HealthCheckService(cache_service=cache)
            logger.info("✅ Health check service initialized")
        except Exception as e:
            logger.warning(f"⚠️  Health check service initialization failed: {e}")
            health_service = None
        
        # Start monitoring server
        logger.info("Starting monitoring server...")
        try:
            monitoring_runner = await start_monitoring_server(
                port=config.monitoring_port,
                health_service=health_service
            )
            logger.info(f"✅ Monitoring server started on port {config.monitoring_port}")
        except Exception as e:
            logger.warning(f"⚠️  Monitoring server not available: {e}")
            logger.warning("⚠️  Continuing without monitoring")
        
        # Create and start bot
        logger.info("Starting bot controller...")
        try:
            controller = BotController()
            logger.info("✅ Bot controller initialized")
        except Exception as e:
            logger.error(f"❌ Bot controller initialization failed: {e}")
            raise
        
        # Run bot
        logger.info("=" * 50)
        logger.info("✅ All systems initialized successfully")
        logger.info("=" * 50)
        await controller.start()
        
    except KeyboardInterrupt:
        logger.info("\n" + "=" * 50)
        logger.info("Received shutdown signal (Ctrl+C)")
        logger.info("=" * 50)
    except Exception as e:
        logger.error("=" * 50)
        logger.error(f"❌ Fatal error: {e}")
        logger.error("=" * 50)
        logger.exception("Full traceback:")
        raise
    finally:
        # Cleanup
        logger.info("=" * 50)
        logger.info("Shutting down gracefully...")
        logger.info("=" * 50)
        
        # Close cache
        try:
            await cache.close()
            logger.info("✅ Cache closed")
        except Exception as e:
            logger.error(f"Error closing cache: {e}")
        
        # Stop monitoring server
        if monitoring_runner:
            try:
                from src.monitoring import stop_monitoring_server
                await stop_monitoring_server(monitoring_runner)
                logger.info("✅ Monitoring server stopped")
            except Exception as e:
                logger.error(f"Error stopping monitoring: {e}")
        
        logger.info("=" * 50)
        logger.info("Shutdown complete")
        logger.info("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
