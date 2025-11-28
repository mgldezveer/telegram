"""Content Source Manager with improved logging and monitoring."""

import logging
import uuid
import json
import asyncio
import feedparser
import aiofiles
import time
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from functools import wraps
from sqlalchemy import select, update, delete, func

# Import для веб-скрепинга
try:
    import requests
    from bs4 import BeautifulSoup
    BEAUTIFULSOUP_AVAILABLE = True
except ImportError:
    BEAUTIFULSOUP_AVAILABLE = False
    BeautifulSoup = None

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.firefox.options import Options as FirefoxOptions
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    webdriver = None
    By = None
    WebDriverWait = None
    EC = None

import logging
import uuid
import json
import asyncio
import feedparser
import aiofiles
import time
from datetime import datetime
from typing import List, Optional, Dict, Any
from functools import wraps
from sqlalchemy import select, update, delete, func

from src.models.autopost import ContentSource
from src.database.autopost_db import autopost_db

# Try to import social media API libraries (optional)
try:
    import tweepy
    TWITTER_AVAILABLE = True
except ImportError:
    TWITTER_AVAILABLE = False
    tweepy = None

try:
    import facebook
    FACEBOOK_AVAILABLE = True
except ImportError:
    FACEBOOK_AVAILABLE = False
    facebook = None

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    requests = None

# Try to import Prometheus metrics (optional)
try:
    from prometheus_client import Counter, Histogram, Gauge
    METRICS_ENABLED = True
    
    # Metrics
    content_sources_total = Counter(
        'content_sources_total',
        'Total number of content sources',
        ['source_type', 'status']
    )
    
    content_fetch_duration = Histogram(
        'content_fetch_duration_seconds',
        'Time spent fetching content',
        ['source_type'],
        buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
    )
    
    active_content_sources = Gauge(
        'active_content_sources',
        'Number of active content sources',
        ['source_type']
    )
    
    rss_fetch_errors = Counter(
        'rss_fetch_errors_total',
        'Total RSS fetch errors',
        ['error_type']
    )
except ImportError:
    METRICS_ENABLED = False

logger = logging.getLogger(__name__)

# Constants
DEFAULT_PRIORITY = 0
RSS_FETCH_TIMEOUT = 10  # seconds
SLOW_OPERATION_THRESHOLD = 5.0  # seconds


def log_performance(operation: str):
    """Decorator to log operation performance with metrics."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            operation_id = str(uuid.uuid4())[:8]
            
            logger.debug(
                f"Starting {operation}",
                extra={
                    'event': 'operation_start',
                    'operation': operation,
                    'operation_id': operation_id,
                    'args_count': len(args)
                }
            )
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                logger.info(
                    f"Completed {operation}",
                    extra={
                        'event': 'operation_complete',
                        'operation': operation,
                        'operation_id': operation_id,
                        'duration_ms': round(duration * 1000, 2),
                        'status': 'success'
                    }
                )
                
                # Alert if slow
                if duration > SLOW_OPERATION_THRESHOLD:
                    logger.warning(
                        f"Slow operation detected: {operation}",
                        extra={
                            'event': 'slow_operation',
                            'operation': operation,
                            'operation_id': operation_id,
                            'duration_ms': round(duration * 1000, 2),
                            'threshold_ms': SLOW_OPERATION_THRESHOLD * 1000
                        }
                    )
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"Failed {operation}",
                    extra={
                        'event': 'operation_failed',
                        'operation': operation,
                        'operation_id': operation_id,
                        'duration_ms': round(duration * 1000, 2),
                        'status': 'error',
                        'error_type': type(e).__name__
                    }
                )
                raise
        return wrapper
    return decorator


class ContentSourceManager:
    """Manager for content sources with comprehensive logging and monitoring."""
    
    def __init__(self, alert_manager=None):
        """Initialize content source manager.
        
        Args:
            alert_manager: Optional alert manager for critical events
        """
        self.alert_manager = alert_manager
        logger.info(
            "ContentSourceManager initialized",
            extra={
                'event': 'manager_init',
                'metrics_enabled': METRICS_ENABLED,
                'alerting_enabled': alert_manager is not None
            }
        )
    
    @log_performance("add_rss_feed")
    async def add_rss_feed(self, url: str, name: str, priority: int = DEFAULT_PRIORITY) -> str:
        """Add RSS feed as content source with comprehensive logging.
        
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
        logger.debug(
            "Adding RSS feed",
            extra={
                'event': 'add_rss_feed_start',
                'url': url,
                'name': name,
                'priority': priority
            }
        )
        
        try:
            # Validate RSS feed (run in executor to avoid blocking)
            async with asyncio.timeout(RSS_FETCH_TIMEOUT):
                loop = asyncio.get_event_loop()
                feed = await loop.run_in_executor(None, feedparser.parse, url)
                
            if feed.bozo:
                logger.warning(
                    "Invalid RSS feed format",
                    extra={
                        'event': 'rss_validation_failed',
                        'url': url,
                        'name': name,
                        'bozo_exception': str(feed.bozo_exception) if hasattr(feed, 'bozo_exception') else None
                    }
                )
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
            
            # Update metrics
            if METRICS_ENABLED:
                content_sources_total.labels(source_type='rss', status='success').inc()
                active_content_sources.labels(source_type='rss').inc()
            
            logger.info(
                "RSS feed added successfully",
                extra={
                    'event': 'rss_feed_added',
                    'source_id': source_id,
                    'source_name': name,
                    'source_type': 'rss',
                    'priority': priority,
                    'url': url,
                    'feed_entries_count': len(feed.entries) if feed.entries else 0
                }
            )
            
            return source_id
            
        except asyncio.TimeoutError:
            if METRICS_ENABLED:
                content_sources_total.labels(source_type='rss', status='error').inc()
                rss_fetch_errors.labels(error_type='timeout').inc()
            
            logger.exception(
                "RSS feed validation timeout",
                extra={
                    'event': 'rss_timeout',
                    'url': url,
                    'name': name,
                    'timeout_seconds': RSS_FETCH_TIMEOUT,
                    'error_type': 'timeout_error'
                }
            )
            
            if self.alert_manager:
                await self.alert_manager.send_alert(
                    level='error',
                    message='RSS feed validation timeout',
                    details={
                        'url': url,
                        'name': name,
                        'timeout': f'{RSS_FETCH_TIMEOUT}s'
                    }
                )
            raise
            
        except ValueError as e:
            if METRICS_ENABLED:
                content_sources_total.labels(source_type='rss', status='error').inc()
                rss_fetch_errors.labels(error_type='validation').inc()
            
            logger.exception(
                "RSS feed validation failed",
                extra={
                    'event': 'rss_validation_error',
                    'url': url,
                    'name': name,
                    'priority': priority,
                    'error_type': 'validation_error'
                }
            )
            raise
            
        except Exception as e:
            if METRICS_ENABLED:
                content_sources_total.labels(source_type='rss', status='error').inc()
                rss_fetch_errors.labels(error_type='unknown').inc()
            
            logger.exception(
                "Failed to add RSS feed",
                extra={
                    'event': 'rss_add_failed',
                    'url': url,
                    'name': name,
                    'priority': priority,
                    'error_type': type(e).__name__
                }
            )
            
            if self.alert_manager:
                await self.alert_manager.send_alert(
                    level='critical',
                    message='Failed to add RSS feed',
                    details={
                        'url': url,
                        'name': name,
                        'error': str(e),
                        'error_type': type(e).__name__
                    }
                )
            raise
    
    @log_performance("add_topic_list")
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
            logger.warning(
                "Empty topics list provided",
                extra={
                    'event': 'empty_topics_list',
                    'name': name
                }
            )
            raise ValueError("Topics list cannot be empty")
        
        logger.debug(
            "Adding topic list",
            extra={
                'event': 'add_topic_list_start',
                'name': name,
                'topics_count': len(topics),
                'priority': priority
            }
        )
        
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
            
            if METRICS_ENABLED:
                content_sources_total.labels(source_type='topics', status='success').inc()
                active_content_sources.labels(source_type='topics').inc()
            
            logger.info(
                "Topic list added successfully",
                extra={
                    'event': 'topic_list_added',
                    'source_id': source_id,
                    'source_name': name,
                    'source_type': 'topics',
                    'topics_count': len(topics),
                    'priority': priority
                }
            )
            
            return source_id
            
        except Exception as e:
            if METRICS_ENABLED:
                content_sources_total.labels(source_type='topics', status='error').inc()
            
            logger.exception(
                "Failed to add topic list",
                extra={
                    'event': 'topic_list_add_failed',
                    'name': name,
                    'topics_count': len(topics),
                    'error_type': type(e).__name__
                }
            )
            raise
    
    @log_performance("import_from_file")
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
        logger.debug(
            "Importing from file",
            extra={
                'event': 'import_file_start',
                'file_path': file_path,
                'name': name,
                'priority': priority
            }
        )
        
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
            
            if METRICS_ENABLED:
                content_sources_total.labels(source_type='file', status='success').inc()
                active_content_sources.labels(source_type='file').inc()
            
            logger.info(
                "File imported successfully",
                extra={
                    'event': 'file_imported',
                    'source_id': source_id,
                    'source_name': name,
                    'source_type': 'file',
                    'file_path': file_path,
                    'priority': priority,
                    'content_items': len(data) if isinstance(data, list) else 1
                }
            )
            
            return source_id
            
        except FileNotFoundError:
            if METRICS_ENABLED:
                content_sources_total.labels(source_type='file', status='error').inc()
            
            logger.exception(
                "File not found",
                extra={
                    'event': 'file_not_found',
                    'file_path': file_path,
                    'name': name,
                    'error_type': 'file_not_found'
                }
            )
            raise
            
        except json.JSONDecodeError as e:
            if METRICS_ENABLED:
                content_sources_total.labels(source_type='file', status='error').inc()
            
            logger.exception(
                "Invalid JSON in file",
                extra={
                    'event': 'invalid_json',
                    'file_path': file_path,
                    'name': name,
                    'error_line': e.lineno,
                    'error_column': e.colno,
                    'error_type': 'json_decode_error'
                }
            )
            raise
            
        except Exception as e:
            if METRICS_ENABLED:
                content_sources_total.labels(source_type='file', status='error').inc()
            
            logger.exception(
                "Failed to import from file",
                extra={
                    'event': 'file_import_failed',
                    'file_path': file_path,
                    'name': name,
                    'error_type': type(e).__name__
                }
            )
            raise
    
    @log_performance("get_next_content")
    async def get_next_content(self) -> Optional[Dict[str, Any]]:
        """Get next content from sources based on priority."""
        logger.debug("Getting next content", extra={'event': 'get_content_start'})
        
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
                    logger.warning(
                        "No active content sources available",
                        extra={'event': 'no_active_sources'}
                    )
                    return None
                
                # Update usage in same transaction
                source.use_count += 1
                source.last_used = datetime.utcnow()
                await session.commit()
                
                logger.debug(
                    "Selected content source",
                    extra={
                        'event': 'source_selected',
                        'source_id': source.id,
                        'source_name': source.name,
                        'source_type': source.type,
                        'priority': source.priority,
                        'use_count': source.use_count
                    }
                )
                
                content = await self._extract_content(source)
                
                logger.info(
                    "Content retrieved successfully",
                    extra={
                        'event': 'content_retrieved',
                        'source_id': source.id,
                        'source_type': source.type,
                        'content_type': content.get('type')
                    }
                )
                
                return content
                
        except Exception as e:
            logger.exception(
                "Failed to get next content",
                extra={
                    'event': 'get_content_failed',
                    'error_type': type(e).__name__
                }
            )
            return None
    
    async def activate_source(self, source_id: str) -> bool:
        """Activate a content source."""
        logger.debug(
            "Activating source",
            extra={
                'event': 'activate_source_start',
                'source_id': source_id
            }
        )
        
        try:
            async with autopost_db.session() as session:
                result = await session.execute(
                    update(ContentSource)
                    .where(ContentSource.id == source_id)
                    .values(is_active=True)
                )
                await session.commit()
                
                success = result.rowcount > 0
                
                if success:
                    logger.info(
                        "Source activated",
                        extra={
                            'event': 'source_activated',
                            'source_id': source_id
                        }
                    )
                else:
                    logger.warning(
                        "Source not found for activation",
                        extra={
                            'event': 'source_not_found',
                            'source_id': source_id
                        }
                    )
                
                return success
                
        except Exception as e:
            logger.exception(
                "Failed to activate source",
                extra={
                    'event': 'activate_failed',
                    'source_id': source_id,
                    'error_type': type(e).__name__
                }
            )
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of content source manager."""
        logger.debug("Running health check", extra={'event': 'health_check_start'})
        
        try:
            async with autopost_db.session() as session:
                # Check database connectivity
                await session.execute(select(ContentSource).limit(1))
                
                # Count active sources by type
                count_result = await session.execute(
                    select(
                        ContentSource.type,
                        func.count(ContentSource.id)
                    )
                    .where(ContentSource.is_active == True)
                    .group_by(ContentSource.type)
                )
                active_counts = dict(count_result.all())
                
                # Test RSS connectivity (sample)
                rss_sources = await session.execute(
                    select(ContentSource)
                    .where(ContentSource.type == 'rss', ContentSource.is_active == True)
                    .limit(1)
                )
                rss_source = rss_sources.scalar_one_or_none()
                
                rss_healthy = True
                if rss_source:
                    try:
                        async with asyncio.timeout(5):
                            loop = asyncio.get_event_loop()
                            feed = await loop.run_in_executor(
                                None, feedparser.parse, rss_source.data["url"]
                            )
                            rss_healthy = not feed.bozo
                    except:
                        rss_healthy = False
                
                health_status = {
                    'status': 'healthy',
                    'database': 'connected',
                    'active_sources': active_counts,
                    'rss_connectivity': 'healthy' if rss_healthy else 'degraded',
                    'metrics_enabled': METRICS_ENABLED,
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                logger.info(
                    "Health check completed",
                    extra={
                        'event': 'health_check_complete',
                        **health_status
                    }
                )
                
                return health_status
                
        except Exception as e:
            logger.exception(
                "Health check failed",
                extra={
                    'event': 'health_check_failed',
                    'error_type': type(e).__name__
                }
            )
            return {
                'status': 'unhealthy',
                'error': str(e),
                'error_type': type(e).__name__,
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def _extract_content(self, source: ContentSource) -> Dict[str, Any]:
        """Extract content from source."""
        start_time = time.time()
        
        try:
            if source.type == "rss":
                content = await self._extract_rss_content(source)
            elif source.type == "topics":
                content = self._extract_topic_content(source)
            elif source.type == "file":
                content = self._extract_file_content(source)
            else:
                logger.warning(
                    "Unknown source type",
                    extra={
                        'event': 'unknown_source_type',
                        'source_id': source.id,
                        'source_type': source.type
                    }
                )
                return {"type": "unknown", "content": ""}
            
            duration = time.time() - start_time
            if METRICS_ENABLED:
                content_fetch_duration.labels(source_type=source.type).observe(duration)
            
            return content
            
        except Exception as e:
            logger.exception(
                "Failed to extract content",
                extra={
                    'event': 'extract_content_failed',
                    'source_id': source.id,
                    'source_name': source.name,
                    'source_type': source.type,
                    'error_type': type(e).__name__
                }
            )
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
                logger.warning(
                    "No entries in RSS feed",
                    extra={
                        'event': 'rss_no_entries',
                        'source_id': source.id,
                        'url': source.data['url']
                    }
                )
                return {"type": "rss", "content": ""}
                
        except asyncio.TimeoutError:
            if METRICS_ENABLED:
                rss_fetch_errors.labels(error_type='timeout').inc()
            
            logger.error(
                "RSS feed timeout",
                extra={
                    'event': 'rss_fetch_timeout',
                    'source_id': source.id,
                    'url': source.data['url'],
                    'timeout_seconds': RSS_FETCH_TIMEOUT
                }
            )
            return {"type": "error", "content": "", "error": "timeout"}
    
    def _extract_topic_content(self, source: ContentSource) -> Dict[str, Any]:
        """Extract content from topic list."""
        import random
        topics = source.data.get("topics", [])
        if topics:
            selected_topic = random.choice(topics)
            logger.debug(
                "Topic selected",
                extra={
                    'event': 'topic_selected',
                    'source_id': source.id,
                    'topic': selected_topic,
                    'total_topics': len(topics)
                }
            )
            return {"type": "topic", "topic": selected_topic}
        return {"type": "topic", "content": ""}
    
    def _extract_file_content(self, source: ContentSource) -> Dict[str, Any]:
        """Extract content from file source."""
        content = source.data.get("content", {})
        if isinstance(content, list) and content:
            import random
            selected = random.choice(content)
            logger.debug(
                "File content selected",
                extra={
                    'event': 'file_content_selected',
                    'source_id': source.id,
                    'total_items': len(content)
                }
            )
            return {"type": "file", "content": selected}
        elif isinstance(content, dict):
            return {"type": "file", **content}
        return {"type": "file", "content": ""}


class SocialMediaAPISourceManager:
    """Manager for social media API content sources with comprehensive logging and monitoring."""
    
    def __init__(self, alert_manager=None):
        """Initialize social media API source manager.
        
        Args:
            alert_manager: Optional alert manager for critical events
        """
        self.alert_manager = alert_manager
        self.twitter_client = None
        self.facebook_graph = None
        self.instagram_graph = None
        self.linkedin_headers = None
        
        logger.info(
            "SocialMediaAPISourceManager initialized",
            extra={
                'event': 'social_media_manager_init',
                'twitter_available': TWITTER_AVAILABLE,
                'facebook_available': FACEBOOK_AVAILABLE,
                'requests_available': REQUESTS_AVAILABLE,
                'alerting_enabled': alert_manager is not None
            }
        )
    
    @log_performance("init_twitter_client")
    async def init_twitter_client(self, api_key: str, api_secret: str, access_token: str, access_token_secret: str):
        """Initialize Twitter API client.
        
        Args:
            api_key: Twitter API key
            api_secret: Twitter API secret
            access_token: Twitter access token
            access_token_secret: Twitter access token secret
        """
        logger.debug(
            "Initializing Twitter client",
            extra={
                'event': 'init_twitter_start',
                'has_api_key': bool(api_key),
                'has_api_secret': bool(api_secret),
                'has_access_token': bool(access_token),
                'has_access_token_secret': bool(access_token_secret)
            }
        )
        
        if not TWITTER_AVAILABLE:
            logger.error(
                "Twitter library not available",
                extra={
                    'event': 'twitter_library_missing',
                    'error_type': 'import_error'
                }
            )
            raise ImportError("tweepy library is not installed. Please install it with 'pip install tweepy'")
        
        try:
            # Initialize Twitter API v2 client
            self.twitter_client = tweepy.Client(
                consumer_key=api_key,
                consumer_secret=api_secret,
                access_token=access_token,
                access_token_secret=access_token_secret
            )
            
            # Test authentication
            me = self.twitter_client.get_me()
            logger.info(
                "Twitter client initialized successfully",
                extra={
                    'event': 'twitter_client_init_success',
                    'user_id': me.data.id,
                    'username': me.data.username,
                    'display_name': me.data.name
                }
            )
            
        except Exception as e:
            logger.exception(
                "Failed to initialize Twitter client",
                extra={
                    'event': 'twitter_init_failed',
                    'error_type': type(e).__name__,
                    'error_message': str(e)
                }
            )
            
            if self.alert_manager:
                await self.alert_manager.send_alert(
                    level='error',
                    message='Failed to initialize Twitter client',
                    details={
                        'error': str(e),
                        'error_type': type(e).__name__
                    }
                )
            raise
    
    @log_performance("init_facebook_client")
    async def init_facebook_client(self, access_token: str, page_id: Optional[str] = None):
        """Initialize Facebook API client.
        
        Args:
            access_token: Facebook access token
            page_id: Optional Facebook page ID
        """
        logger.debug(
            "Initializing Facebook client",
            extra={
                'event': 'init_facebook_start',
                'has_access_token': bool(access_token),
                'page_id': page_id
            }
        )
        
        if not FACEBOOK_AVAILABLE:
            logger.error(
                "Facebook library not available",
                extra={
                    'event': 'facebook_library_missing',
                    'error_type': 'import_error'
                }
            )
            raise ImportError("facebook-sdk library is not installed. Please install it with 'pip install facebook-sdk'")
        
        try:
            self.facebook_graph = facebook.GraphAPI(access_token=access_token)
            
            # Test authentication
            user_info = self.facebook_graph.get_object('me', fields='id,name')
            logger.info(
                "Facebook client initialized successfully",
                extra={
                    'event': 'facebook_client_init_success',
                    'user_id': user_info['id'],
                    'user_name': user_info['name']
                }
            )
            
        except Exception as e:
            logger.exception(
                "Failed to initialize Facebook client",
                extra={
                    'event': 'facebook_init_failed',
                    'error_type': type(e).__name__,
                    'error_message': str(e)
                }
            )
            
            if self.alert_manager:
                await self.alert_manager.send_alert(
                    level='error',
                    message='Failed to initialize Facebook client',
                    details={
                        'error': str(e),
                        'error_type': type(e).__name__
                    }
                )
            raise
    
    @log_performance("init_instagram_client")
    async def init_instagram_client(self, access_token: str, instagram_account_id: str):
        """Initialize Instagram API client.
        
        Args:
            access_token: Instagram access token
            instagram_account_id: Instagram account ID
        """
        logger.debug(
            "Initializing Instagram client",
            extra={
                'event': 'init_instagram_start',
                'has_access_token': bool(access_token),
                'instagram_account_id': instagram_account_id
            }
        )
        
        if not REQUESTS_AVAILABLE:
            logger.error(
                "Requests library not available",
                extra={
                    'event': 'requests_library_missing',
                    'error_type': 'import_error'
                }
            )
            raise ImportError("requests library is not installed. Please install it with 'pip install requests'")
        
        try:
            # For Instagram, we use the Facebook Graph API
            self.instagram_graph = facebook.GraphAPI(access_token=access_token)
            
            # Test authentication
            account_info = self.instagram_graph.get_object(instagram_account_id, fields='id,username,name')
            logger.info(
                "Instagram client initialized successfully",
                extra={
                    'event': 'instagram_client_init_success',
                    'account_id': account_info['id'],
                    'username': account_info['username'],
                    'name': account_info.get('name', 'N/A')
                }
            )
            
        except Exception as e:
            logger.exception(
                "Failed to initialize Instagram client",
                extra={
                    'event': 'instagram_init_failed',
                    'error_type': type(e).__name__,
                    'error_message': str(e)
                }
            )
            
            if self.alert_manager:
                await self.alert_manager.send_alert(
                    level='error',
                    message='Failed to initialize Instagram client',
                    details={
                        'error': str(e),
                        'error_type': type(e).__name__
                    }
                )
            raise
    
    @log_performance("init_linkedin_client")
    async def init_linkedin_client(self, access_token: str):
        """Initialize LinkedIn API client.
        
        Args:
            access_token: LinkedIn access token
        """
        logger.debug(
            "Initializing LinkedIn client",
            extra={
                'event': 'init_linkedin_start',
                'has_access_token': bool(access_token)
            }
        )
        
        if not REQUESTS_AVAILABLE:
            logger.error(
                "Requests library not available",
                extra={
                    'event': 'requests_library_missing',
                    'error_type': 'import_error'
                }
            )
            raise ImportError("requests library is not installed. Please install it with 'pip install requests'")
        
        try:
            self.linkedin_headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
                'X-Restli-Protocol-Version': '2.0.0'
            }
            
            # Test authentication
            response = requests.get(
                'https://api.linkedin.com/v2/userinfo',
                headers=self.linkedin_headers
            )
            
            if response.status_code == 200:
                user_info = response.json()
                logger.info(
                    "LinkedIn client initialized successfully",
                    extra={
                        'event': 'linkedin_client_init_success',
                        'sub': user_info.get('sub'),
                        'name': user_info.get('name'),
                        'email': user_info.get('email')
                    }
                )
            else:
                logger.error(
                    "Failed to authenticate LinkedIn client",
                    extra={
                        'event': 'linkedin_auth_failed',
                        'status_code': response.status_code,
                        'response_text': response.text
                    }
                )
                raise Exception(f"LinkedIn authentication failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.exception(
                "Failed to initialize LinkedIn client",
                extra={
                    'event': 'linkedin_init_failed',
                    'error_type': type(e).__name__,
                    'error_message': str(e)
                }
            )
            
            if self.alert_manager:
                await self.alert_manager.send_alert(
                    level='error',
                    message='Failed to initialize LinkedIn client',
                    details={
                        'error': str(e),
                        'error_type': type(e).__name__
                    }
                )
            raise
    
    @log_performance("get_twitter_posts")
    async def get_twitter_posts(self, username: str, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent posts from a Twitter account.
        
        Args:
            username: Twitter username
            count: Number of posts to retrieve (default 10, max 100)
            
        Returns:
            List of Twitter posts
        """
        logger.debug(
            "Getting Twitter posts",
            extra={
                'event': 'get_twitter_posts_start',
                'username': username,
                'count': count
            }
        )
        
        if not self.twitter_client:
            logger.error(
                "Twitter client not initialized",
                extra={
                    'event': 'twitter_client_not_initialized',
                    'username': username
                }
            )
            raise ValueError("Twitter client not initialized. Call init_twitter_client first.")
        
        try:
            # Get user ID from username
            user = self.twitter_client.get_user(username=username)
            user_id = user.data.id
            
            # Get user's tweets
            tweets = self.twitter_client.get_users_tweets(
                id=user_id,
                max_results=min(count, 100),  # Twitter API limit is 100
                tweet_fields=['created_at', 'public_metrics', 'context_annotations', 'lang']
            )
            
            if not tweets.data:
                logger.warning(
                    "No tweets found for user",
                    extra={
                        'event': 'no_tweets_found',
                        'username': username
                    }
                )
                return []
            
            processed_tweets = []
            for tweet in tweets.data:
                processed_tweet = {
                    'id': tweet.id,
                    'text': tweet.text,
                    'created_at': tweet.created_at.isoformat() if tweet.created_at else None,
                    'author_username': username,
                    'author_id': user_id,
                    'public_metrics': tweet.public_metrics or {},
                    'lang': tweet.lang,
                    'source': 'twitter'
                }
                processed_tweets.append(processed_tweet)
                
                logger.debug(
                    "Processed Twitter post",
                    extra={
                        'event': 'twitter_post_processed',
                        'tweet_id': tweet.id,
                        'tweet_length': len(tweet.text)
                    }
                )
            
            logger.info(
                "Twitter posts retrieved successfully",
                extra={
                    'event': 'twitter_posts_retrieved',
                    'username': username,
                    'count': len(processed_tweets),
                    'requested_count': count
                }
            )
            
            return processed_tweets
            
        except Exception as e:
            logger.exception(
                "Failed to get Twitter posts",
                extra={
                    'event': 'get_twitter_posts_failed',
                    'username': username,
                    'error_type': type(e).__name__,
                    'error_message': str(e)
                }
            )
            
            if self.alert_manager:
                await self.alert_manager.send_alert(
                    level='error',
                    message='Failed to get Twitter posts',
                    details={
                        'username': username,
                        'error': str(e),
                        'error_type': type(e).__name__
                    }
                )
            raise
    
    @log_performance("get_facebook_posts")
    async def get_facebook_posts(self, page_id: str, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent posts from a Facebook page.
        
        Args:
            page_id: Facebook page ID
            count: Number of posts to retrieve (default 10)
            
        Returns:
            List of Facebook posts
        """
        logger.debug(
            "Getting Facebook posts",
            extra={
                'event': 'get_facebook_posts_start',
                'page_id': page_id,
                'count': count
            }
        )
        
        if not self.facebook_graph:
            logger.error(
                "Facebook client not initialized",
                extra={
                    'event': 'facebook_client_not_initialized',
                    'page_id': page_id
                }
            )
            raise ValueError("Facebook client not initialized. Call init_facebook_client first.")
        
        try:
            # Get page posts
            posts = self.facebook_graph.get_connections(
                id=page_id,
                connection_name='posts',
                fields='id,message,created_time,from,likes.summary(true),comments.summary(true),shares',
                limit=count
            )
            
            processed_posts = []
            for post in posts['data']:
                processed_post = {
                    'id': post['id'],
                    'message': post.get('message', ''),
                    'created_time': post.get('created_time'),
                    'from': post.get('from', {}),
                    'likes': post.get('likes', {}).get('summary', {}).get('total_count', 0) if 'likes' in post else 0,
                    'comments': post.get('comments', {}).get('summary', {}).get('total_count', 0) if 'comments' in post else 0,
                    'shares': post.get('shares', {}).get('count', 0) if 'shares' in post else 0,
                    'source': 'facebook'
                }
                processed_posts.append(processed_post)
                
                logger.debug(
                    "Processed Facebook post",
                    extra={
                        'event': 'facebook_post_processed',
                        'post_id': post['id'],
                        'message_length': len(post.get('message', ''))
                    }
                )
            
            logger.info(
                "Facebook posts retrieved successfully",
                extra={
                    'event': 'facebook_posts_retrieved',
                    'page_id': page_id,
                    'count': len(processed_posts),
                    'requested_count': count
                }
            )
            
            return processed_posts
            
        except Exception as e:
            logger.exception(
                "Failed to get Facebook posts",
                extra={
                    'event': 'get_facebook_posts_failed',
                    'page_id': page_id,
                    'error_type': type(e).__name__,
                    'error_message': str(e)
                }
            )
            
            if self.alert_manager:
                await self.alert_manager.send_alert(
                    level='error',
                    message='Failed to get Facebook posts',
                    details={
                        'page_id': page_id,
                        'error': str(e),
                        'error_type': type(e).__name__
                    }
                )
            raise
    
    @log_performance("get_instagram_posts")
    async def get_instagram_posts(self, instagram_account_id: str, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent posts from an Instagram account.
        
        Args:
            instagram_account_id: Instagram account ID
            count: Number of posts to retrieve (default 10)
            
        Returns:
            List of Instagram posts
        """
        logger.debug(
            "Getting Instagram posts",
            extra={
                'event': 'get_instagram_posts_start',
                'instagram_account_id': instagram_account_id,
                'count': count
            }
        )
        
        if not self.instagram_graph:
            logger.error(
                "Instagram client not initialized",
                extra={
                    'event': 'instagram_client_not_initialized',
                    'instagram_account_id': instagram_account_id
                }
            )
            raise ValueError("Instagram client not initialized. Call init_instagram_client first.")
        
        try:
            # Get Instagram media
            media = self.instagram_graph.get_connections(
                id=instagram_account_id,
                connection_name='media',
                fields='id,caption,media_type,media_url,permalink,timestamp,username,like_count',
                limit=count
            )
            
            processed_posts = []
            for item in media['data']:
                processed_post = {
                    'id': item['id'],
                    'caption': item.get('caption', ''),
                    'media_type': item.get('media_type', ''),
                    'media_url': item.get('media_url', ''),
                    'permalink': item.get('permalink', ''),
                    'timestamp': item.get('timestamp', ''),
                    'username': item.get('username', ''),
                    'like_count': item.get('like_count', 0),
                    'source': 'instagram'
                }
                processed_posts.append(processed_post)
                
                logger.debug(
                    "Processed Instagram post",
                    extra={
                        'event': 'instagram_post_processed',
                        'post_id': item['id'],
                        'caption_length': len(item.get('caption', ''))
                    }
                )
            
            logger.info(
                "Instagram posts retrieved successfully",
                extra={
                    'event': 'instagram_posts_retrieved',
                    'instagram_account_id': instagram_account_id,
                    'count': len(processed_posts),
                    'requested_count': count
                }
            )
            
            return processed_posts
            
        except Exception as e:
            logger.exception(
                "Failed to get Instagram posts",
                extra={
                    'event': 'get_instagram_posts_failed',
                    'instagram_account_id': instagram_account_id,
                    'error_type': type(e).__name__,
                    'error_message': str(e)
                }
            )
            
            if self.alert_manager:
                await self.alert_manager.send_alert(
                    level='error',
                    message='Failed to get Instagram posts',
                    details={
                        'instagram_account_id': instagram_account_id,
                        'error': str(e),
                        'error_type': type(e).__name__
                    }
                )
            raise
    
    @log_performance("get_linkedin_posts")
    async def get_linkedin_posts(self, organization_id: str, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent posts from a LinkedIn organization.
        
        Args:
            organization_id: LinkedIn organization ID
            count: Number of posts to retrieve (default 10)
            
        Returns:
            List of LinkedIn posts
        """
        logger.debug(
            "Getting LinkedIn posts",
            extra={
                'event': 'get_linkedin_posts_start',
                'organization_id': organization_id,
                'count': count
            }
        )
        
        if not self.linkedin_headers:
            logger.error(
                "LinkedIn client not initialized",
                extra={
                    'event': 'linkedin_client_not_initialized',
                    'organization_id': organization_id
                }
            )
            raise ValueError("LinkedIn client not initialized. Call init_linkedin_client first.")
        
        try:
            # LinkedIn API to get organization posts
            url = f"https://api.linkedin.com/v2/organizationPosts?q=organization&organization={organization_id}&count={count}"
            response = requests.get(url, headers=self.linkedin_headers)
            
            if response.status_code != 200:
                logger.error(
                    "Failed to get LinkedIn posts",
                    extra={
                        'event': 'linkedin_api_error',
                        'status_code': response.status_code,
                        'response_text': response.text
                    }
                )
                raise Exception(f"LinkedIn API error: {response.status_code} - {response.text}")
            
            data = response.json()
            posts = data.get('elements', [])
            
            processed_posts = []
            for post in posts:
                processed_post = {
                    'id': post.get('id', ''),
                    'author': post.get('actor', {}).get('entityUrn', ''),
                    'text': post.get('commentary', {}).get('text', {}).get('text', '') if 'commentary' in post else '',
                    'created_at': post.get('createdAt', ''),
                    'lifecycle_state': post.get('lifecycleState', ''),
                    'content': post.get('content', {}),
                    'source': 'linkedin'
                }
                processed_posts.append(processed_post)
                
                logger.debug(
                    "Processed LinkedIn post",
                    extra={
                        'event': 'linkedin_post_processed',
                        'post_id': post.get('id', ''),
                        'text_length': len(processed_post['text'])
                    }
                )
            
            logger.info(
                "LinkedIn posts retrieved successfully",
                extra={
                    'event': 'linkedin_posts_retrieved',
                    'organization_id': organization_id,
                    'count': len(processed_posts),
                    'requested_count': count
                }
            )
            
            return processed_posts
            
        except Exception as e:
            logger.exception(
                "Failed to get LinkedIn posts",
                extra={
                    'event': 'get_linkedin_posts_failed',
                    'organization_id': organization_id,
                    'error_type': type(e).__name__,
                    'error_message': str(e)
                }
            )
            
            if self.alert_manager:
                await self.alert_manager.send_alert(
                    level='error',
                    message='Failed to get LinkedIn posts',
                    details={
                        'organization_id': organization_id,
                        'error': str(e),
                        'error_type': type(e).__name__
                    }
                )
            raise
    
    async def _process_twitter_posts(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process Twitter posts for content extraction.
        
        Args:
            posts: List of Twitter posts to process
            
        Returns:
            List of processed posts with extracted content
        """
        logger.debug(
            "Processing Twitter posts",
            extra={
                'event': 'process_twitter_posts_start',
                'posts_count': len(posts)
            }
        )
        
        processed_posts = []
        for post in posts:
            try:
                # Extract text content from Twitter post
                text = post.get('text', '')
                
                # Clean up the text (remove URLs, mentions, etc.)
                import re
                clean_text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
                clean_text = re.sub(r'@\w+', '', clean_text)
                clean_text = re.sub(r'#\w+', '', clean_text)
                clean_text = clean_text.strip()
                
                processed_post = {
                    'id': post.get('id'),
                    'content': clean_text,
                    'original_post': post,
                    'type': 'social_media',
                    'source': 'twitter',
                    'author': post.get('author_username'),
                    'created_at': post.get('created_at'),
                    'metrics': {
                        'likes': post.get('public_metrics', {}).get('like_count', 0),
                        'retweets': post.get('public_metrics', {}).get('retweet_count', 0),
                        'replies': post.get('public_metrics', {}).get('reply_count', 0),
                        'quotes': post.get('public_metrics', {}).get('quote_count', 0)
                    }
                }
                
                processed_posts.append(processed_post)
                
                logger.debug(
                    "Processed Twitter post for content extraction",
                    extra={
                        'event': 'twitter_post_content_processed',
                        'post_id': post.get('id'),
                        'content_length': len(clean_text)
                    }
                )
                
            except Exception as e:
                logger.exception(
                    "Failed to process Twitter post",
                    extra={
                        'event': 'twitter_post_process_failed',
                        'post_id': post.get('id'),
                        'error_type': type(e).__name__
                    }
                )
                continue
        
        logger.info(
            "Twitter posts processed successfully",
            extra={
                'event': 'twitter_posts_processed',
                'processed_count': len(processed_posts),
                'original_count': len(posts)
            }
        )
        
        return processed_posts
    
    async def _process_facebook_posts(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process Facebook posts for content extraction.
        
        Args:
            posts: List of Facebook posts to process
            
        Returns:
            List of processed posts with extracted content
        """
        logger.debug(
            "Processing Facebook posts",
            extra={
                'event': 'process_facebook_posts_start',
                'posts_count': len(posts)
            }
        )
        
        processed_posts = []
        for post in posts:
            try:
                # Extract text content from Facebook post
                text = post.get('message', '')
                
                # Clean up the text
                import re
                clean_text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
                clean_text = clean_text.strip()
                
                processed_post = {
                    'id': post.get('id'),
                    'content': clean_text,
                    'original_post': post,
                    'type': 'social_media',
                    'source': 'facebook',
                    'author': post.get('from', {}).get('name'),
                    'created_at': post.get('created_time'),
                    'metrics': {
                        'likes': post.get('likes', 0),
                        'comments': post.get('comments', 0),
                        'shares': post.get('shares', 0)
                    }
                }
                
                processed_posts.append(processed_post)
                
                logger.debug(
                    "Processed Facebook post for content extraction",
                    extra={
                        'event': 'facebook_post_content_processed',
                        'post_id': post.get('id'),
                        'content_length': len(clean_text)
                    }
                )
                
            except Exception as e:
                logger.exception(
                    "Failed to process Facebook post",
                    extra={
                        'event': 'facebook_post_process_failed',
                        'post_id': post.get('id'),
                        'error_type': type(e).__name__
                    }
                )
                continue
        
        logger.info(
            "Facebook posts processed successfully",
            extra={
                'event': 'facebook_posts_processed',
                'processed_count': len(processed_posts),
                'original_count': len(posts)
            }
        )
        
        return processed_posts
    
    async def _process_instagram_posts(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process Instagram posts for content extraction.
        
        Args:
            posts: List of Instagram posts to process
            
        Returns:
            List of processed posts with extracted content
        """
        logger.debug(
            "Processing Instagram posts",
            extra={
                'event': 'process_instagram_posts_start',
                'posts_count': len(posts)
            }
        )
        
        processed_posts = []
        for post in posts:
            try:
                # Extract text content from Instagram post
                text = post.get('caption', '')
                
                # Clean up the text
                import re
                clean_text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
                clean_text = re.sub(r'@\w+', '', clean_text)
                clean_text = re.sub(r'#\w+', '', clean_text)
                clean_text = clean_text.strip()
                
                processed_post = {
                    'id': post.get('id'),
                    'content': clean_text,
                    'original_post': post,
                    'type': 'social_media',
                    'source': 'instagram',
                    'author': post.get('username'),
                    'created_at': post.get('timestamp'),
                    'media_url': post.get('media_url'),
                    'media_type': post.get('media_type'),
                    'metrics': {
                        'likes': post.get('like_count', 0)
                    }
                }
                
                processed_posts.append(processed_post)
                
                logger.debug(
                    "Processed Instagram post for content extraction",
                    extra={
                        'event': 'instagram_post_content_processed',
                        'post_id': post.get('id'),
                        'content_length': len(clean_text)
                    }
                )
                
            except Exception as e:
                logger.exception(
                    "Failed to process Instagram post",
                    extra={
                        'event': 'instagram_post_process_failed',
                        'post_id': post.get('id'),
                        'error_type': type(e).__name__
                    }
                )
                continue
        
        logger.info(
            "Instagram posts processed successfully",
            extra={
                'event': 'instagram_posts_processed',
                'processed_count': len(processed_posts),
                'original_count': len(posts)
            }
        )
        
        return processed_posts


class WebScrapingSourceManager:
    """Manager for web scraping content sources with support for both static and dynamic content."""
    
    def __init__(self, alert_manager=None, default_timeout=10, default_delay=1):
        """Initialize web scraping source manager.
        
        Args:
            alert_manager: Optional alert manager for critical events
            default_timeout: Default timeout for requests (in seconds)
            default_delay: Default delay between requests (in seconds)
        """
        self.alert_manager = alert_manager
        self.default_timeout = default_timeout
        self.default_delay = default_delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Configuration for different website types
        self.website_configs = {
            'news': {
                'selectors': {
                    'title': ['h1', '.headline', '.title', 'h2'],
                    'content': ['.article-body', '.content', '.post-content', 'article', '.entry-content'],
                    'date': ['.date', '.publish-date', '.timestamp', 'time'],
                    'author': ['.author', '.byline', '.writer']
                }
            },
            'blog': {
                'selectors': {
                    'title': ['h1', '.post-title', '.entry-title', 'h2'],
                    'content': ['.post-content', '.entry-content', '.blog-content', 'article', '.content'],
                    'date': ['.date', '.post-date', '.entry-date', 'time'],
                    'author': ['.author', '.byline', '.entry-author']
                }
            },
            'forum': {
                'selectors': {
                    'title': ['h1', '.topic-title', '.subject', 'h2'],
                    'content': ['.post-body', '.content', '.message', '.post-content'],
                    'date': ['.date', '.post-date', '.time', 'time'],
                    'author': ['.author', '.username', '.user', '.nickname']
                }
            }
        }
        
        logger.info(
            "WebScrapingSourceManager initialized",
            extra={
                'event': 'web_scraping_manager_init',
                'beautifulsoup_available': BEAUTIFULSOUP_AVAILABLE,
                'selenium_available': SELENIUM_AVAILABLE,
                'default_timeout': default_timeout,
                'default_delay': default_delay,
                'alerting_enabled': alert_manager is not None
            }
        )
    
    def _get_driver(self, browser='chrome', headless=True):
        """Initialize and return a Selenium WebDriver instance."""
        if not SELENIUM_AVAILABLE:
            logger.error(
                "Selenium is not available",
                extra={'event': 'selenium_not_available'}
            )
            raise ImportError("Selenium is not installed. Please install it with 'pip install selenium'")
        
        try:
            if browser.lower() == 'chrome':
                options = ChromeOptions()
                if headless:
                    options.add_argument('--headless')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--disable-gpu')
                options.add_argument('--window-size=1920,1080')
                driver = webdriver.Chrome(options=options)
            elif browser.lower() == 'firefox':
                options = FirefoxOptions()
                if headless:
                    options.add_argument('--headless')
                driver = webdriver.Firefox(options=options)
            else:
                raise ValueError(f"Unsupported browser: {browser}")
            
            logger.debug(
                "Selenium WebDriver initialized",
                extra={'event': 'webdriver_init', 'browser': browser, 'headless': headless}
            )
            return driver
        except Exception as e:
            logger.exception(
                "Failed to initialize Selenium WebDriver",
                extra={'event': 'webdriver_init_failed', 'browser': browser, 'error': str(e)}
            )
            raise
    
    def _normalize_content(self, content: str) -> str:
        """Normalize scraped content by cleaning up whitespace and special characters."""
        if not content:
            return ""
        
        # Remove extra whitespace and normalize line breaks
        import re
        content = re.sub(r'\s+', ' ', content)  # Replace multiple whitespaces with single space
        content = re.sub(r'\n+', '\n', content)  # Replace multiple newlines with single newline
        content = content.strip()  # Remove leading/trailing whitespace
        
        # Remove special characters that might cause issues
        content = content.replace('\x00', '').replace('\x01', '').replace('\x02', '')
        content = content.replace('\u200b', '')  # Zero-width space
        content = content.replace('\ufeff', '')  # Byte order mark
        
        return content
    
    def _detect_website_type(self, url: str) -> str:
        """Detect the type of website based on URL patterns."""
        url_lower = url.lower()
        
        # Check for common patterns
        if any(pattern in url_lower for pattern in ['news', 'newspaper', 'journal', 'times', 'post', 'tribune']):
            return 'news'
        elif any(pattern in url_lower for pattern in ['blog', 'wordpress', 'blogger', 'medium']):
            return 'blog'
        elif any(pattern in url_lower for pattern in ['forum', 'community', 'discuss', 'thread']):
            return 'forum'
        else:
            # Default to news if no specific pattern is found
            return 'news'
    
    def _find_elements_by_selectors(self, soup: BeautifulSoup, selectors: List[str]):
        """Find elements in soup using a list of selectors, returning the first match."""
        for selector in selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    return element
            except Exception as e:
                logger.debug(
                    f"Selector failed: {selector}",
                    extra={'event': 'selector_failed', 'selector': selector, 'error': str(e)}
                )
                continue
        return None
    
    @log_performance("scrape_static_content")
    async def scrape_static_content(self, url: str, selectors: Optional[Dict[str, List[str]]] = None,
                                    website_type: Optional[str] = None) -> Dict[str, Any]:
        """Scrape content from a static website using BeautifulSoup.
        
        Args:
            url: URL to scrape
            selectors: Optional custom selectors for content extraction
            website_type: Optional website type ('news', 'blog', 'forum')
            
        Returns:
            Dictionary with scraped content
        """
        logger.debug(
            "Starting static content scraping",
            extra={'event': 'scrape_static_start', 'url': url, 'selectors_provided': selectors is not None}
        )
        
        if not BEAUTIFULSOUP_AVAILABLE:
            logger.error(
                "BeautifulSoup is not available",
                extra={'event': 'beautifulsoup_not_available', 'url': url}
            )
            raise ImportError("BeautifulSoup is not installed. Please install it with 'pip install beautifulsoup4'")
        
        try:
            # Use asyncio to run requests in a thread pool
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, lambda: self.session.get(url, timeout=self.default_timeout))
            
            if response.status_code != 200:
                logger.warning(
                    "HTTP request failed",
                    extra={'event': 'http_request_failed', 'url': url, 'status_code': response.status_code}
                )
                return {"type": "error", "content": "", "error": f"HTTP {response.status_code}"}
            
            # Parse content with BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Determine website type if not provided
            if website_type is None:
                website_type = self._detect_website_type(url)
            
            # Use provided selectors or get from configuration based on website type
            if selectors is None:
                selectors = self.website_configs.get(website_type, {}).get('selectors', {})
            
            # Extract content using selectors
            title_element = self._find_elements_by_selectors(soup, selectors.get('title', []))
            content_element = self._find_elements_by_selectors(soup, selectors.get('content', []))
            date_element = self._find_elements_by_selectors(soup, selectors.get('date', []))
            author_element = self._find_elements_by_selectors(soup, selectors.get('author', []))
            
            # Extract text content
            title = title_element.get_text().strip() if title_element else ""
            content = content_element.get_text().strip() if content_element else ""
            date = date_element.get_text().strip() if date_element else ""
            author = author_element.get_text().strip() if author_element else ""
            
            # Normalize content
            content = self._normalize_content(content)
            title = self._normalize_content(title)
            
            # Extract all links from the page
            links = [a.get('href') for a in soup.find_all('a', href=True)]
            links = [link for link in links if link.startswith('http')]  # Only absolute URLs
            
            result = {
                "type": "web_scraping",
                "source_url": url,
                "website_type": website_type,
                "title": title,
                "content": content,
                "date": date,
                "author": author,
                "links": links,
                "scraping_method": "static"
            }
            
            logger.info(
                "Static content scraped successfully",
                extra={'event': 'scrape_static_success', 'url': url, 'content_length': len(content)}
            )
            
            return result
            
        except asyncio.TimeoutError:
            logger.error(
                "Request timeout during scraping",
                extra={'event': 'scraping_timeout', 'url': url, 'timeout': self.default_timeout}
            )
            return {"type": "error", "content": "", "error": "timeout"}
        except Exception as e:
            logger.exception(
                "Failed to scrape static content",
                extra={'event': 'scrape_static_failed', 'url': url, 'error_type': type(e).__name__}
            )
            return {"type": "error", "content": "", "error": str(e)}
    
    @log_performance("scrape_dynamic_content")
    async def scrape_dynamic_content(self, url: str, selectors: Optional[Dict[str, List[str]]] = None,
                                     website_type: Optional[str] = None, wait_selector: Optional[str] = None) -> Dict[str, Any]:
        """Scrape content from a dynamic website using Selenium.
        
        Args:
            url: URL to scrape
            selectors: Optional custom selectors for content extraction
            website_type: Optional website type ('news', 'blog', 'forum')
            wait_selector: Optional selector to wait for before scraping
            
        Returns:
            Dictionary with scraped content
        """
        logger.debug(
            "Starting dynamic content scraping",
            extra={'event': 'scrape_dynamic_start', 'url': url, 'selectors_provided': selectors is not None}
        )
        
        if not SELENIUM_AVAILABLE:
            logger.error(
                "Selenium is not available",
                extra={'event': 'selenium_not_available', 'url': url}
            )
            raise ImportError("Selenium is not installed. Please install it with 'pip install selenium'")
        
        driver = None
        try:
            # Initialize WebDriver
            driver = self._get_driver()
            driver.get(url)
            
            # Wait for specific element if provided
            if wait_selector:
                wait = WebDriverWait(driver, self.default_timeout)
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, wait_selector)))
            else:
                # Default wait for page to load
                await asyncio.sleep(2)
            
            # Get page source after JavaScript execution
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Determine website type if not provided
            if website_type is None:
                website_type = self._detect_website_type(url)
            
            # Use provided selectors or get from configuration based on website type
            if selectors is None:
                selectors = self.website_configs.get(website_type, {}).get('selectors', {})
            
            # Extract content using selectors
            title_element = self._find_elements_by_selectors(soup, selectors.get('title', []))
            content_element = self._find_elements_by_selectors(soup, selectors.get('content', []))
            date_element = self._find_elements_by_selectors(soup, selectors.get('date', []))
            author_element = self._find_elements_by_selectors(soup, selectors.get('author', []))
            
            # Extract text content
            title = title_element.get_text().strip() if title_element else ""
            content = content_element.get_text().strip() if content_element else ""
            date = date_element.get_text().strip() if date_element else ""
            author = author_element.get_text().strip() if author_element else ""
            
            # Normalize content
            content = self._normalize_content(content)
            title = self._normalize_content(title)
            
            # Extract all links from the page
            links = [a.get('href') for a in soup.find_all('a', href=True)]
            links = [link for link in links if link.startswith('http')]  # Only absolute URLs
            
            result = {
                "type": "web_scraping",
                "source_url": url,
                "website_type": website_type,
                "title": title,
                "content": content,
                "date": date,
                "author": author,
                "links": links,
                "scraping_method": "dynamic"
            }
            
            logger.info(
                "Dynamic content scraped successfully",
                extra={'event': 'scrape_dynamic_success', 'url': url, 'content_length': len(content)}
            )
            
            return result
            
        except Exception as e:
            logger.exception(
                "Failed to scrape dynamic content",
                extra={'event': 'scrape_dynamic_failed', 'url': url, 'error_type': type(e).__name__}
            )
            return {"type": "error", "content": "", "error": str(e)}
        finally:
            if driver:
                driver.quit()
                logger.debug("Selenium WebDriver closed", extra={'event': 'webdriver_closed'})
    
    @log_performance("scrape_content")
    async def scrape_content(self, url: str, selectors: Optional[Dict[str, List[str]]] = None,
                             website_type: Optional[str] = None, use_selenium: bool = False) -> Dict[str, Any]:
        """Scrape content from a website, automatically choosing the appropriate method.
        
        Args:
            url: URL to scrape
            selectors: Optional custom selectors for content extraction
            website_type: Optional website type ('news', 'blog', 'forum')
            use_selenium: Force use of Selenium even for static content
            
        Returns:
            Dictionary with scraped content
        """
        logger.debug(
            "Starting content scraping",
            extra={'event': 'scrape_start', 'url': url, 'use_selenium': use_selenium}
        )
        
        if use_selenium or not BEAUTIFULSOUP_AVAILABLE:
            return await self.scrape_dynamic_content(url, selectors, website_type)
        else:
            return await self.scrape_static_content(url, selectors, website_type)
    
    @log_performance("add_web_scraping_source")
    async def add_web_scraping_source(self, url: str, name: str, priority: int = DEFAULT_PRIORITY,
                                      selectors: Optional[Dict[str, List[str]]] = None,
                                      website_type: Optional[str] = None, use_selenium: bool = False) -> str:
        """Add a web scraping source to the database.
        
        Args:
            url: URL to scrape
            name: Name for this content source
            priority: Priority level (higher = more important)
            selectors: Optional custom selectors for content extraction
            website_type: Optional website type ('news', 'blog', 'forum')
            use_selenium: Whether to use Selenium for scraping
            
        Returns:
            Source ID (UUID string)
        """
        logger.debug(
            "Adding web scraping source",
            extra={'event': 'add_web_scraping_start', 'url': url, 'name': name, 'use_selenium': use_selenium}
        )
        
        try:
            source_id = str(uuid.uuid4())
            
            # Store source configuration in data field
            source_data = {
                "url": url,
                "selectors": selectors,
                "website_type": website_type,
                "use_selenium": use_selenium
            }
            
            async with autopost_db.session() as session:
                source = ContentSource(
                    id=source_id,
                    type="web_scraping",
                    name=name,
                    is_active=True,
                    priority=priority,
                    data=source_data,
                    created_at=datetime.utcnow()
                )
                session.add(source)
                await session.commit()
            
            if METRICS_ENABLED:
                content_sources_total.labels(source_type='web_scraping', status='success').inc()
                active_content_sources.labels(source_type='web_scraping').inc()
            
            logger.info(
                "Web scraping source added successfully",
                extra={'event': 'web_scraping_added', 'source_id': source_id, 'url': url, 'name': name}
            )
            
            return source_id
            
        except Exception as e:
            if METRICS_ENABLED:
                content_sources_total.labels(source_type='web_scraping', status='error').inc()
            
            logger.exception(
                "Failed to add web scraping source",
                extra={'event': 'web_scraping_add_failed', 'url': url, 'name': name, 'error_type': type(e).__name__}
            )
            raise
    
    
    async def _process_linkedin_posts(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process LinkedIn posts for content extraction.
        
        Args:
            posts: List of LinkedIn posts to process
            
        Returns:
            List of processed posts with extracted content
        """
        logger.debug(
            "Processing LinkedIn posts",
            extra={
                'event': 'process_linkedin_posts_start',
                'posts_count': len(posts)
            }
        )
        
        processed_posts = []
        for post in posts:
            try:
                # Extract text content from LinkedIn post
                text = post.get('text', '')
                
                # Clean up the text
                import re
                clean_text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
                clean_text = clean_text.strip()
                
                processed_post = {
                    'id': post.get('id'),
                    'content': clean_text,
                    'original_post': post,
                    'type': 'social_media',
                    'source': 'linkedin',
                    'author': post.get('author'),
                    'created_at': post.get('created_at'),
                    'content_details': post.get('content', {}),
                    'metrics': {
                        'lifecycle_state': post.get('lifecycle_state')
                    }
                }
                
                processed_posts.append(processed_post)
                
                logger.debug(
                    "Processed LinkedIn post for content extraction",
                    extra={
                        'event': 'linkedin_post_content_processed',
                        'post_id': post.get('id'),
                        'content_length': len(clean_text)
                    }
                )
                
            except Exception as e:
                logger.exception(
                    "Failed to process LinkedIn post",
                    extra={
                        'event': 'linkedin_post_process_failed',
                        'post_id': post.get('id'),
                        'error_type': type(e).__name__
                    }
                )
                continue
        
        logger.info(
            "LinkedIn posts processed successfully",
            extra={
                'event': 'linkedin_posts_processed',
                'processed_count': len(processed_posts),
                'original_count': len(posts)
            }
        )
        
        return processed_posts
