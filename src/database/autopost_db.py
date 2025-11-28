"""Database connection and session management for autopost system with extended models support."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import QueuePool
from sqlalchemy import event, text
from src.config import config
from src.models.autopost import Base
from src.models.channel import Channel
from src.models.post import Post

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from src.config import config

logger = logging.getLogger(__name__)


class AutoPostDatabase:
    """Async database manager for autopost system."""
    
    def __init__(self, pool_size: int = 10, max_overflow: int = 20, pool_timeout: int = 30):
        """Initialize database connection."""
        self.engine = None
        self.session_factory = None
        self._initialized = False
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout
        self._connection_stats = {
            'total_connections': 0,
            'active_connections': 0,
            'cached_connections': 0
        }
    
    async def initialize(self):
        """Initialize database engine and session factory."""
        if self._initialized:
            return
        
        try:
            # Create async engine with optimized settings
            database_url = config.database.url
            
            # Convert sqlite:/// to sqlite+aiosqlite:///
            if database_url.startswith('sqlite:///'):
                database_url = database_url.replace('sqlite:///', 'sqlite+aiosqlite:///')
            
            # Connection arguments based on database type
            connect_args = {}
            if 'sqlite' in database_url:
                connect_args.update({
                    'check_same_thread': False,
                    'timeout': 30
                })
            elif 'postgresql' in database_url:
                connect_args.update({
                    'connect_timeout': 10,
                    'command_timeout': 30
                })
            
            self.engine = create_async_engine(
                database_url,
                echo=config.database.echo,
                poolclass=QueuePool,  # Use QueuePool instead of NullPool for better performance
                pool_size=self.pool_size,
                max_overflow=self.max_overflow,
                pool_timeout=self.pool_timeout,
                pool_recycle=3600,  # Recycle connections every hour
                pool_pre_ping=True,  # Verify connections before use
                future=True,
                connect_args=connect_args
            )
            
            # Add connection tracking for SQLite
            @event.listens_for(self.engine.sync_engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                if 'sqlite' in database_url:
                    cursor = dbapi_connection.cursor()
                    # Set optimizations for SQLite
                    cursor.execute("PRAGMA journal_mode=WAL")
                    cursor.execute("PRAGMA synchronous=NORMAL")
                    cursor.execute("PRAGMA cache_size=1000")
                    cursor.execute("PRAGMA temp_store=memory")
                    cursor.close()
            
            # Create session factory
            self.session_factory = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=False  # Disable autoflush for better performance
            )
            
            self._initialized = True
            logger.info(f"✅ AutoPost database initialized with pool size {self.pool_size}")
            
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
    
    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[AsyncSession, None]:
        """Get transaction context manager."""
        if not self._initialized:
            await self.initialize()
        
        async with self.session_factory() as session:
            async with session.begin():  # Start transaction
                try:
                    yield session
                except Exception as e:
                    logger.error(f"Transaction error: {e}")
                    raise  # Transaction will automatically rollback on exception
    
    async def tables_exist(self) -> bool:
        """Check if autopost tables exist.
        
        Returns:
            True if tables exist, False otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            from sqlalchemy import inspect
            
            async with self.engine.connect() as conn:
                # Check if main table exists
                if 'postgresql' in str(self.engine.url):
                    # PostgreSQL-specific query
                    result = await conn.execute(
                        text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'autopost_channels')")
                    )
                    exists = result.scalar()
                else:
                    # SQLite-specific query
                    result = await conn.execute(
                        text("SELECT name FROM sqlite_master WHERE type='table' AND name='autopost_channels'")
                    )
                    exists = result.fetchone() is not None
                
                if exists:
                    # Verify table has data structure (check columns)
                    if 'postgresql' in str(self.engine.url):
                        # PostgreSQL-specific query
                        result = await conn.execute(
                            text("SELECT column_name FROM information_schema.columns WHERE table_name = 'autopost_channels'")
                        )
                        columns = result.fetchall()
                        return len(columns) > 0
                    else:
                        # SQLite-specific query
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
            
            async with self.engine.begin() as conn:
                if force:
                    # Drop existing tables first
                    await conn.run_sync(Base.metadata.drop_all)
                    logger.info("Dropped existing tables")
                
                # Create tables with all models
                await conn.run_sync(Base.metadata.create_all)
            
            logger.info("✅ AutoPost tables created with extended models support")
            
        except Exception as e:
            logger.error(f"❌ Failed to create autopost tables: {e}")
            raise
    
    async def drop_tables(self):
        """Drop all tables (use with caution!)."""
        if not self._initialized:
            await self.initialize()
        
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
            
            logger.info("AutoPost tables dropped")
            
        except Exception as e:
            logger.error(f"Failed to drop autopost tables: {e}")
            raise
    
    async def get_pool_stats(self) -> dict:
        """Get connection pool statistics.
        
        Returns:
            Dictionary with pool statistics
        """
        if not self.engine:
            return {}
        
        pool = self.engine.pool
        return {
            'size': pool.size(),
            'checkedin': pool.checkedin(),
            'overflow': pool.overflow(),
            'connections': pool._connections,
            'timeout': pool._timeout
        }
    
    async def health_check(self) -> dict:
        """Check database connection health.
        
        Returns:
            Dictionary with health check results
        """
        try:
            async with self.session() as session:
                # Execute simple query to check connection
                if 'postgresql' in str(self.engine.url):
                    result = await session.execute(text("SELECT 1"))
                else:
                    result = await session.execute(text("SELECT 1"))
                is_healthy = result.scalar() == 1
                
                # Check if all required tables exist
                tables_exist = await self.tables_exist()
                
                pool_stats = await self.get_pool_stats()
                
                return {
                    'healthy': is_healthy,
                    'tables_exist': tables_exist,
                    'pool_stats': pool_stats,
                    'database_url': self.engine.url.render_as_string(hide_password=True) if self.engine else 'Not initialized'
                }
                
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                'healthy': False,
                'tables_exist': False,
                'error': str(e),
                'database_url': self.engine.url.render_as_string(hide_password=True) if self.engine else 'Not initialized'
            }


# Global database instance
autopost_db = AutoPostDatabase()
