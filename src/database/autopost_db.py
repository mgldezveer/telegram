"""Database connection and session management for autopost system."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from src.config import config

logger = logging.getLogger(__name__)


class AutoPostDatabase:
    """Async database manager for autopost system."""
    
    def __init__(self):
        """Initialize database connection."""
        self.engine = None
        self.session_factory = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize database engine and session factory."""
        if self._initialized:
            return
        
        try:
            # Create async engine
            database_url = config.database.url
            
            # Convert sqlite:/// to sqlite+aiosqlite:///
            if database_url.startswith('sqlite:///'):
                database_url = database_url.replace('sqlite:///', 'sqlite+aiosqlite:///')
            
            self.engine = create_async_engine(
                database_url,
                echo=config.database.echo,
                poolclass=NullPool,  # Disable pooling for SQLite
                future=True
            )
            
            # Create session factory
            self.session_factory = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            self._initialized = True
            logger.info("✅ AutoPost database initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize autopost database: {e}")
            raise
    
    async def close(self):
        """Close database connection."""
        if self.engine:
            await self.engine.dispose()
            self._initialized = False
            logger.info("AutoPost database connection closed")
    
    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session context manager."""
        if not self._initialized:
            await self.initialize()
        
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"Database session error: {e}")
                raise
            finally:
                await session.close()
    
    async def tables_exist(self) -> bool:
        """Check if autopost tables exist.
        
        Returns:
            True if tables exist, False otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            from sqlalchemy import inspect, text
            
            async with self.engine.connect() as conn:
                # Check if main table exists
                result = await conn.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table' AND name='autopost_channels'")
                )
                exists = result.fetchone() is not None
                
                if exists:
                    # Verify table has data structure (check columns)
                    result = await conn.execute(
                        text("PRAGMA table_info(autopost_channels)")
                    )
                    columns = result.fetchall()
                    return len(columns) > 0
                
                return False
                
        except Exception as e:
            logger.debug(f"Error checking tables: {e}")
            return False
    
    async def create_tables(self, force: bool = False):
        """Create all tables if they don't exist.
        
        Args:
            force: If True, recreate tables even if they exist
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Check if tables already exist
            if not force:
                exists = await self.tables_exist()
                if exists:
                    logger.info("✅ AutoPost tables already exist, skipping creation")
                    return
            
            from src.models.autopost import Base
            
            async with self.engine.begin() as conn:
                if force:
                    # Drop existing tables first
                    await conn.run_sync(Base.metadata.drop_all)
                    logger.info("Dropped existing tables")
                
                # Create tables
                await conn.run_sync(Base.metadata.create_all)
            
            logger.info("✅ AutoPost tables created")
            
        except Exception as e:
            logger.error(f"❌ Failed to create autopost tables: {e}")
            raise
    
    async def drop_tables(self):
        """Drop all tables (use with caution!)."""
        if not self._initialized:
            await self.initialize()
        
        try:
            from src.models.autopost import Base
            
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
            
            logger.info("AutoPost tables dropped")
            
        except Exception as e:
            logger.error(f"Failed to drop autopost tables: {e}")
            raise


# Global database instance
autopost_db = AutoPostDatabase()
