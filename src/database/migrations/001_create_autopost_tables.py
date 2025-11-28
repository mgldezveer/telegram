"""Create autopost tables migration."""

import logging
from sqlalchemy import text

logger = logging.getLogger(__name__)


def upgrade(connection):
    """Create autopost tables."""
    
    # Create autopost_channels table
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS autopost_channels (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            settings JSON DEFAULT '{}'
        )
    """))
    
    # Create autopost_posts table
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS autopost_posts (
            id TEXT PRIMARY KEY,
            channel_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            status TEXT DEFAULT 'draft',
            media JSON DEFAULT '[]',
            buttons JSON DEFAULT '[]',
            hashtags JSON DEFAULT '[]',
            theme TEXT,
            style JSON DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            scheduled_for TIMESTAMP,
            published_at TIMESTAMP,
            priority INTEGER DEFAULT 0,
            FOREIGN KEY (channel_id) REFERENCES autopost_channels(id)
        )
    """))
    
    # Create autopost_schedules table
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS autopost_schedules (
            id TEXT PRIMARY KEY,
            channel_id INTEGER NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            config JSON NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_run TIMESTAMP,
            next_run TIMESTAMP,
            FOREIGN KEY (channel_id) REFERENCES autopost_channels(id)
        )
    """))
    
    # Create autopost_publications table
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS autopost_publications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id INTEGER NOT NULL,
            post_id TEXT,
            status TEXT NOT NULL,
            published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            error_message TEXT,
            retry_count INTEGER DEFAULT 0,
            telegram_message_id INTEGER,
            FOREIGN KEY (channel_id) REFERENCES autopost_channels(id),
            FOREIGN KEY (post_id) REFERENCES autopost_posts(id)
        )
    """))
    
    # Create content_sources table
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS content_sources (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            name TEXT NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            priority INTEGER DEFAULT 0,
            data JSON NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_used TIMESTAMP,
            use_count INTEGER DEFAULT 0
        )
    """))
    
    # Create indexes
    connection.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_autopost_posts_channel
        ON autopost_posts(channel_id)
    """))
    
    connection.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_autopost_posts_status
        ON autopost_posts(status)
    """))
    
    connection.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_autopost_posts_scheduled
        ON autopost_posts(scheduled_for)
    """))
    
    connection.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_autopost_schedules_channel
        ON autopost_schedules(channel_id)
    """))
    
    connection.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_autopost_publications_channel
        ON autopost_publications(channel_id)
    """))
    
    connection.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_content_sources_active
        ON content_sources(is_active, priority)
    """))
    
    logger.info("✅ Auto-post tables created successfully")


def downgrade(connection):
    """Drop autopost tables."""
    connection.execute(text("DROP TABLE IF EXISTS autopost_publications"))
    connection.execute(text("DROP TABLE IF EXISTS autopost_schedules"))
    connection.execute(text("DROP TABLE IF EXISTS autopost_posts"))
    connection.execute(text("DROP TABLE IF EXISTS autopost_channels"))
    connection.execute(text("DROP TABLE IF EXISTS content_sources"))
    
    logger.info("✅ Auto-post tables dropped successfully")
