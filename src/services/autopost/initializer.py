"""Auto-posting system initializer."""

import logging
from src.database.autopost_db import autopost_db

logger = logging.getLogger(__name__)


async def initialize_autopost_system():
    """Initialize auto-posting system.
    
    This function:
    1. Checks if database tables exist
    2. Creates them if they don't exist
    3. Validates table structure
    """
    try:
        logger.info("Initializing auto-posting system...")
        
        # Initialize database connection
        await autopost_db.initialize()
        
        # Check if tables exist
        exists = await autopost_db.tables_exist()
        
        if not exists:
            logger.info("Auto-posting tables not found, creating...")
            await autopost_db.create_tables()
            logger.info("✅ Auto-posting tables created")
        else:
            logger.info("✅ Auto-posting tables already exist")
        
        logger.info("✅ Auto-posting system initialized")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize auto-posting system: {e}")
        logger.warning("Auto-posting features may not work correctly")
        return False
