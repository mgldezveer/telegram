"""Улучшенная система работы с базой данных с оптимизациями производительности."""

import logging
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import QueuePool
from sqlalchemy import event, text
from src.config import config
from src.cache import cache

logger = logging.getLogger(__name__)


class EnhancedDatabase:
    """Улучшенный менеджер базы данных с оптимизациями производительности."""
    
    def __init__(self, pool_size: int = 20, max_overflow: int = 30, pool_timeout: int = 30):
        """Инициализировать улучшенный менеджер базы данных.
        
        Args:
            pool_size: Размер пула подключений
            max_overflow: Максимальное количество дополнительных подключений
            pool_timeout: Таймаут ожидания подключения
        """
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
        """Инициализировать улучшенный движок базы данных и фабрику сессий."""
        if self._initialized:
            return
        
        try:
            # Создать асинхронный движок с оптимизациями
            database_url = config.database.url
            
            # Преобразовать URL для SQLite если необходимо
            if database_url.startswith('sqlite:///'):
                database_url = database_url.replace('sqlite:///', 'sqlite+aiosqlite:///')
            
            # Параметры подключения в зависимости от типа БД
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
                poolclass=QueuePool,  # Используем QueuePool вместо NullPool
                pool_size=self.pool_size,
                max_overflow=self.max_overflow,
                pool_timeout=self.pool_timeout,
                pool_recycle=3600, # Пересоздавать соединения каждые час
                pool_pre_ping=True,  # Проверять соединения перед использованием
                future=True,
                connect_args=connect_args
            )
            
            # Создать фабрику сессий с оптимизациями
            self.session_factory = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=False  # Отключить автоподтверждение изменений
            )
            
            # Добавить отслеживание соединений
            @event.listens_for(self.engine.sync_engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                if 'sqlite' in database_url:
                    cursor = dbapi_connection.cursor()
                    # Установить оптимизации для SQLite
                    cursor.execute("PRAGMA journal_mode=WAL")
                    cursor.execute("PRAGMA synchronous=NORMAL")
                    cursor.execute("PRAGMA cache_size=10000")
                    cursor.execute("PRAGMA temp_store=memory")
                    cursor.close()
            
            self._initialized = True
            logger.info(f"✅ Enhanced database initialized with pool size {self.pool_size}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize enhanced database: {e}")
            raise
    
    async def close(self):
        """Закрыть соединение с базой данных."""
        if self.engine:
            await self.engine.dispose()
            self._initialized = False
            logger.info("Enhanced database connection closed")
    
    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Получить контекстный менеджер сессии базы данных."""
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
        """Получить контекстный менеджер транзакции."""
        if not self._initialized:
            await self.initialize()
        
        async with self.session_factory() as session:
            async with session.begin():  # Начать транзакцию
                try:
                    yield session
                except Exception as e:
                    logger.error(f"Transaction error: {e}")
                    raise # Транзакция автоматически откатится при исключении
    
    async def get_pool_stats(self) -> dict:
        """Получить статистику пула подключений.
        
        Returns:
            Словарь со статистикой пула
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
    
    async def clear_cache(self):
        """Очистить кэш, связанный с базой данных."""
        # Удалить все ключи, связанные с репозиторием
        repo_keys = await cache.keys("repo:*")
        for key in repo_keys:
            await cache.delete(key)
        
        logger.info(f"✅ Cleared {len(repo_keys)} cached repository entries")
    
    async def health_check(self) -> dict:
        """Проверить здоровье соединения с базой данных.
        
        Returns:
            Словарь с результатами проверки
        """
        try:
            async with self.session() as session:
                # Выполнить простой запрос для проверки соединения
                if 'postgresql' in str(self.engine.url):
                    result = await session.execute(text("SELECT 1"))
                else:
                    result = await session.execute(text("SELECT 1"))
                is_healthy = result.scalar() == 1
                
                pool_stats = await self.get_pool_stats()
                
                return {
                    'healthy': is_healthy,
                    'pool_stats': pool_stats,
                    'database_url': self.engine.url.render_as_string(hide_password=True) if self.engine else 'Not initialized'
                }
                
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                'healthy': False,
                'error': str(e),
                'database_url': self.engine.url.render_as_string(hide_password=True) if self.engine else 'Not initialized'
            }
    
    async def start_periodic_health_check(self, interval: int = 300):
        """Запустить периодическую проверку здоровья базы данных.
        
        Args:
            interval: Интервал проверки в секундах
        """
        async def health_check_loop():
            while self._initialized:
                try:
                    health = await self.health_check()
                    if not health['healthy']:
                        logger.warning(f"Database health check failed: {health['error']}")
                    else:
                        logger.debug("Database health check passed")
                except Exception as e:
                    logger.error(f"Unexpected error during health check: {e}")
                
                await asyncio.sleep(interval)
        
        self._health_check_task = asyncio.create_task(health_check_loop())
        logger.info(f"Periodic health check started with interval {interval}s")
    
    async def stop_periodic_health_check(self):
        """Остановить периодическую проверку здоровья."""
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
            self._health_check_task = None
            logger.info("Periodic health check stopped")
    
    async def execute_raw_sql(self, sql: str, params: Optional[dict] = None) -> list:
        """Выполнить произвольный SQL-запрос.
        
        Args:
            sql: SQL-запрос для выполнения
            params: Параметры запроса
            
        Returns:
            Результаты запроса виде списка словарей
        """
        if not self._initialized:
            await self.initialize()
        
        async with self.session() as session:
            try:
                result = await session.execute(text(sql), params or {})
                if result.returns_rows:
                    # Преобразовать результат в список словарей
                    rows = []
                    for row in result.fetchall():
                        row_dict = {}
                        for idx, column in enumerate(result.keys()):
                            row_dict[column] = row[idx]
                        rows.append(row_dict)
                    return rows
                else:
                    await session.commit()
                    return []
            except Exception as e:
                await session.rollback()
                logger.error(f"Raw SQL execution error: {e}")
                raise


# Глобальный экземпляр улучшенной базы данных
enhanced_db = EnhancedDatabase()