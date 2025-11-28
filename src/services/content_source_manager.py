"""Content Source Manager for auto-posting system."""

import logging
import uuid
import json
import asyncio
import feedparser
import aiofiles
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import select, update, delete

from src.models.autopost import ContentSource
from src.database.autopost_db import autopost_db

logger = logging.getLogger(__name__)

# Constants
DEFAULT_PRIORITY = 0
RSS_FETCH_TIMEOUT = 10  # seconds


class ContentSourceManager:
    """Manager for content sources (RSS, topics, files)."""
    
    async def add_rss_feed(self, url: str, name: str, priority: int = DEFAULT_PRIORITY) -> str:
        """Add RSS feed as content source.
        
        Args:
            url: RSS feed URL
            name: Name for this content source
            priority: Priority level (higher = more important)
            
        Returns:
            Source ID (UUID string)
            
        Raises:
            ValueError: If RSS feed is invalid
            asyncio.TimeoutError: If feed fetch times out
        """
        try:
            # Validate RSS feed (run in executor to avoid blocking)
            async with asyncio.timeout(RSS_FETCH_TIMEOUT):
                loop = asyncio.get_event_loop()
                feed = await loop.run_in_executor(None, feedparser.parse, url)
                
            if feed.bozo:
                raise ValueError(f"Invalid RSS feed: {url}")
            
            source_id = str(uuid.uuid4())
            async with autopost_db.session() as session:
                source = ContentSource(
                    id=source_id,
                    type="rss",
                    name=name,
                    is_active=True,
                    priority=priority,
                    data={"url": url},
                    created_at=datetime.utcnow()
                )
                session.add(source)
                await session.commit()
                
                logger.info(f"✅ Added RSS feed: {name}")
                return source_id
        except Exception as e:
            logger.error(f"❌ Failed to add RSS feed: {e}")
            raise
    
    async def add_topic_list(self, topics: List[str], name: str, priority: int = DEFAULT_PRIORITY) -> str:
        """Add topic list as content source.
        
        Args:
            topics: List of topic strings
            name: Name for this content source
            priority: Priority level (higher = more important)
            
        Returns:
            Source ID (UUID string)
            
        Raises:
            ValueError: If topics list is empty
        """
        if not topics:
            raise ValueError("Topics list cannot be empty")
        try:
            source_id = str(uuid.uuid4())
            async with autopost_db.session() as session:
                source = ContentSource(
                    id=source_id,
                    type="topics",
                    name=name,
                    is_active=True,
                    priority=priority,
                    data={"topics": topics},
                    created_at=datetime.utcnow()
                )
                session.add(source)
                await session.commit()
                
                logger.info(f"✅ Added topic list: {name} ({len(topics)} topics)")
                return source_id
        except Exception as e:
            logger.error(f"❌ Failed to add topic list: {e}")
            raise
    
    async def import_from_file(self, file_path: str, name: str, priority: int = DEFAULT_PRIORITY) -> str:
        """Import content from file.
        
        Args:
            file_path: Path to JSON file containing content
            name: Name for this content source
            priority: Priority level (higher = more important)
            
        Returns:
            Source ID (UUID string)
            
        Raises:
            FileNotFoundError: If file doesn't exist
            json.JSONDecodeError: If file contains invalid JSON
        """
        try:
            # Use async file I/O
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                data = json.loads(content)
            
            source_id = str(uuid.uuid4())
            async with autopost_db.session() as session:
                source = ContentSource(
                    id=source_id,
                    type="file",
                    name=name,
                    is_active=True,
                    priority=priority,
                    data={"path": file_path, "content": data},
                    created_at=datetime.utcnow()
                )
                session.add(source)
                await session.commit()
                
                logger.info(f"✅ Imported from file: {name}")
                return source_id
        except FileNotFoundError:
            logger.error(f"❌ File not found: {file_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON in file {file_path}: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Failed to import from file: {e}")
            raise
    
    async def get_next_content(self) -> Optional[Dict[str, Any]]:
        """Get next content from sources based on priority."""
        try:
            async with autopost_db.session() as session:
                result = await session.execute(
                    select(ContentSource)
                    .where(ContentSource.is_active == True)
                    .order_by(ContentSource.priority.desc(), ContentSource.use_count.asc())
                    .limit(1)
                )
                source = result.scalar_one_or_none()
                
                if not source:
                    return None
                
                # Update usage in same transaction
                source.use_count += 1
                source.last_used = datetime.utcnow()
                await session.commit()
                
                return await self._extract_content(source)
        except Exception as e:
            logger.error(f"❌ Failed to get next content: {e}")
            return None
    
    async def activate_source(self, source_id: str) -> bool:
        """Activate a content source."""
        try:
            async with autopost_db.session() as session:
                result = await session.execute(
                    update(ContentSource)
                    .where(ContentSource.id == source_id)
                    .values(is_active=True)
                )
                await session.commit()
                return result.rowcount > 0
        except Exception as e:
            logger.error(f"❌ Failed to activate source: {e}")
            return False
    
    async def _extract_content(self, source: ContentSource) -> Dict[str, Any]:
        """Extract content from source.
        
        Args:
            source: ContentSource object
            
        Returns:
            Dictionary with extracted content
        """
        try:
            if source.type == "rss":
                return await self._extract_rss_content(source)
            elif source.type == "topics":
                return self._extract_topic_content(source)
            elif source.type == "file":
                return self._extract_file_content(source)
            else:
                logger.warning(f"⚠️ Unknown source type: {source.type}")
                return {"type": "unknown", "content": ""}
        except Exception as e:
            logger.error(f"❌ Failed to extract content from {source.name}: {e}")
            return {"type": "error", "content": "", "error": str(e)}
    
    async def _extract_rss_content(self, source: ContentSource) -> Dict[str, Any]:
        """Extract content from RSS feed."""
        try:
            async with asyncio.timeout(RSS_FETCH_TIMEOUT):
                loop = asyncio.get_event_loop()
                feed = await loop.run_in_executor(None, feedparser.parse, source.data["url"])
                
            if feed.entries:
                entry = feed.entries[0]
                return {
                    "type": "rss",
                    "title": entry.get("title", ""),
                    "description": entry.get("description", ""),
                    "link": entry.get("link", "")
                }
            else:
                logger.warning(f"⚠️ No entries in RSS feed: {source.data['url']}")
                return {"type": "rss", "content": ""}
        except asyncio.TimeoutError:
            logger.error(f"❌ RSS feed timeout: {source.data['url']}")
            return {"type": "error", "content": "", "error": "timeout"}
    
    def _extract_topic_content(self, source: ContentSource) -> Dict[str, Any]:
        """Extract content from topic list."""
        import random
        topics = source.data.get("topics", [])
        if topics:
            return {"type": "topic", "topic": random.choice(topics)}
        return {"type": "topic", "content": ""}
    
    def _extract_file_content(self, source: ContentSource) -> Dict[str, Any]:
        """Extract content from file source."""
        content = source.data.get("content", {})
        if isinstance(content, list) and content:
            import random
            return {"type": "file", "content": random.choice(content)}
        elif isinstance(content, dict):
            return {"type": "file", **content}
        return {"type": "file", "content": ""}
