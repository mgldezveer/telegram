"""Initialize auto-posting database."""

import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def init_db(force: bool = False):
    """Initialize database tables.
    
    Args:
        force: If True, recreate tables even if they exist
    """
    from src.database.autopost_db import autopost_db
    
    try:
        logger.info("Initializing auto-posting database...")
        
        # Initialize connection
        await autopost_db.initialize()
        
        # Check if tables exist
        exists = await autopost_db.tables_exist()
        
        if exists and not force:
            logger.info("✅ Database tables already exist and are valid")
            logger.info("Use --force flag to recreate tables")
        else:
            # Create tables
            await autopost_db.create_tables(force=force)
            logger.info("✅ Auto-posting database initialized successfully!")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
        raise
    finally:
        await autopost_db.close()


if __name__ == "__main__":
    import sys
    force = "--force" in sys.argv or "-f" in sys.argv
    asyncio.run(init_db(force=force))
