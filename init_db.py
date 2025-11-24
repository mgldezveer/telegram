#!/usr/bin/env python3
"""
Инициализация базы данных
Создает все необходимые таблицы
"""
import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine
from src.config import config
from src.models.base import Base
from src.models.channel import Channel
from src.models.post import Post
from src.models.metrics import Metrics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def init_database():
    """Создание всех таблиц в базе данных"""
    logger.info("Initializing database...")
    
    # Создаем движок
    engine = create_async_engine(
        config.database.url,
        echo=config.database.echo
    )
    
    try:
        # Создаем все таблицы
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("✅ Database initialized successfully!")
        logger.info(f"Tables created: {', '.join(Base.metadata.tables.keys())}")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
        raise
    finally:
        await engine.dispose()

async def check_database():
    """Проверка существующих таблиц"""
    logger.info("Checking database...")
    
    engine = create_async_engine(config.database.url)
    
    try:
        async with engine.begin() as conn:
            # Проверяем существование таблиц
            result = await conn.run_sync(
                lambda sync_conn: sync_conn.dialect.has_table(sync_conn, "channels")
            )
            
            if result:
                logger.info("✅ Database already initialized")
                return True
            else:
                logger.info("⚠️  Database not initialized")
                return False
                
    except Exception as e:
        logger.error(f"❌ Failed to check database: {e}")
        return False
    finally:
        await engine.dispose()

async def main():
    """Главная функция"""
    print("🗄️  Database Initialization")
    print("-" * 50)
    
    # Проверяем существующую БД
    exists = await check_database()
    
    if exists:
        response = input("\nDatabase already exists. Recreate? (yes/no): ")
        if response.lower() != 'yes':
            print("Skipping initialization.")
            return
    
    # Инициализируем БД
    await init_database()
    print("\n✅ Database is ready!")

if __name__ == "__main__":
    asyncio.run(main())
