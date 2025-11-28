"""Telegram Analytics Connector for integration with Telegram Analytics API."""

import logging
import aiohttp
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.metrics import Metrics
from src.repositories.metrics_repository import MetricsRepository
from src.models import get_session, Post


@dataclass
class EngagementMetrics:
    """Data class for engagement metrics."""
    views: int = 0
    reactions: int = 0
    shares: int = 0
    comments: int = 0
    engagement_rate: float = 0.0
    reach: int = 0
    impressions: int = 0
    saves: int = 0
    forwards: int = 0


class TelegramAnalyticsConnector:
    """Connector for Telegram Analytics API integration."""
    
    def __init__(self, bot_token: str, api_base_url: str = "https://api.telegram.org/bot"):
        """Initialize the connector.
        
        Args:
            bot_token: Telegram bot token for API authentication
            api_base_url: Base URL for Telegram API (default: official API)
        """
        self.bot_token = bot_token
        self.api_base_url = f"{api_base_url}{bot_token}"
        self.session: Optional[aiohttp.ClientSession] = None
        self.logger = logging.getLogger(__name__)
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
        
    async def connect(self):
        """Establish connection to Telegram Analytics API."""
        if self.session is None:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={
                    "Content-Type": "application/json",
                }
            )
        self.logger.info("Telegram Analytics Connector initialized")
        
    async def disconnect(self):
        """Close connection to Telegram Analytics API."""
        if self.session:
            await self.session.close()
            self.session = None
        self.logger.info("Telegram Analytics Connector disconnected")
        
    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make request to Telegram API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            data: Request payload
            
        Returns:
            API response as dictionary
        """
        if not self.session:
            raise RuntimeError("Connector not connected. Call connect() first.")
            
        url = f"{self.api_base_url}/{endpoint}"
        
        try:
            if method.upper() == "GET":
                async with self.session.get(url, params=data) as response:
                    result = await response.json()
            elif method.upper() == "POST":
                async with self.session.post(url, json=data) as response:
                    result = await response.json()
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
                
            if not result.get("ok"):
                error_description = result.get("description", "Unknown error")
                self.logger.error(f"API request failed: {error_description}")
                raise Exception(f"Telegram API error: {error_description}")
                
            return result
            
        except aiohttp.ClientError as e:
            self.logger.error(f"HTTP request failed: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Request failed: {e}")
            raise
            
    async def get_channel_info(self, channel_username: str) -> Dict[str, Any]:
        """Get basic channel information.
        
        Args:
            channel_username: Channel username without @ symbol
            
        Returns:
            Channel information dictionary
        """
        # Note: Telegram Bot API doesn't provide detailed analytics directly
        # This is a workaround to get basic info
        try:
            result = await self._make_request(
                "GET",
                "getChat",
                {"chat_id": f"@{channel_username}"}
            )
            return result.get("result", {})
        except Exception as e:
            self.logger.error(f"Error getting channel info: {e}")
            return {}
    
    async def get_engagement_metrics(
        self,
        channel_username: str,
        period_start: datetime,
        period_end: datetime
    ) -> EngagementMetrics:
        """Get engagement metrics from Telegram Analytics.
        
        Args:
            channel_username: Channel username without @ symbol
            period_start: Start of the period to analyze
            period_end: End of the period to analyze
            
        Returns:
            EngagementMetrics object with analytics data
        """
        self.logger.info(
            f"Getting engagement metrics for @{channel_username} "
            f"from {period_start} to {period_end}"
        )
        
        # Note: Official Telegram Analytics API is not accessible via Bot API
        # This implementation uses Telethon MTProto API to get real statistics
        # For true Analytics API integration, special access from Telegram is required
        try:
            # For now, we'll implement a fallback that uses Telethon if available
            # or return placeholder data if only Bot API is available
            from src.services.telethon_stats_parser import TelethonStatsParser
            from src.config import config
            
            # Check if we have Telethon credentials
            api_id = getattr(config, 'telegram_api_id', None) or getattr(config, 'TELEGRAM_API_ID', None)
            api_hash = getattr(config, 'telegram_api_hash', None) or getattr(config, 'TELEGRAM_API_HASH', None)
            
            if api_id and api_hash:
                # Use Telethon to get real stats
                parser = TelethonStatsParser(api_id, api_hash)
                stats = await parser.get_channel_stats(
                    channel_username,
                    (period_end - period_start).days
                )
                
                if not stats.get('no_data'):
                    return EngagementMetrics(
                        views=stats.get('views', 0),
                        reactions=stats.get('reactions', 0),
                        shares=stats.get('shares', 0),
                        comments=stats.get('comments', 0),
                        engagement_rate=stats.get('engagement_rate', 0.0),
                        reach=stats.get('member_count', 0),  # Approximation
                        impressions=stats.get('views', 0),  # Approximation
                        saves=0,  # Not available via Telethon
                        forwards=stats.get('shares', 0)
                    )
            
            # If Telethon is not available, return placeholder data
            # In a real implementation, this would connect to Telegram Analytics API
            self.logger.warning(
                "Telethon credentials not available, returning placeholder metrics. "
                "For real analytics, you need Telegram Analytics API access or Telethon credentials."
            )
            return EngagementMetrics()
            
        except Exception as e:
            self.logger.error(f"Error getting engagement metrics: {e}")
            return EngagementMetrics()
    
    async def get_post_metrics(self, channel_username: str, post_ids: List[int]) -> Dict[int, EngagementMetrics]:
        """Get metrics for specific posts.
        
        Args:
            channel_username: Channel username without @ symbol
            post_ids: List of post IDs to get metrics for
            
        Returns:
            Dictionary mapping post IDs to their metrics
        """
        self.logger.info(f"Getting metrics for posts {post_ids} in @{channel_username}")
        
        try:
            # Use Telethon to get real post metrics if available
            from src.config import config
            api_id = getattr(config, 'telegram_api_id', None) or getattr(config, 'TELEGRAM_API_ID', None)
            api_hash = getattr(config, 'telegram_api_hash', None) or getattr(config, 'TELEGRAM_API_HASH', None)
            
            if api_id and api_hash:
                from src.services.telethon_stats_parser import TelethonStatsParser
                parser = TelethonStatsParser(api_id, api_hash)
                
                # Get channel posts and sync metrics
                synced_count = await parser.sync_channel_posts_to_db(
                    0,  # We don't have channel ID here
                    channel_username,
                    7  # Last 7 days
                )
                
                self.logger.info(f"Synced {synced_count} posts for metrics")
                
                # Return placeholder for now - in real implementation would fetch from Analytics API
                result = {}
                for post_id in post_ids:
                    result[post_id] = EngagementMetrics()
                return result
            else:
                # Return placeholder data
                result = {}
                for post_id in post_ids:
                    result[post_id] = EngagementMetrics()
                return result
                
        except Exception as e:
            self.logger.error(f"Error getting post metrics: {e}")
            result = {}
            for post_id in post_ids:
                result[post_id] = EngagementMetrics()
            return result
    
    async def process_and_normalize_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process and normalize raw analytics data.
        
        Args:
            raw_data: Raw data from Telegram Analytics API
            
        Returns:
            Normalized data in standard format
        """
        self.logger.info("Processing and normalizing analytics data")
        
        # Normalize the data structure
        normalized = {
            'timestamp': datetime.utcnow().isoformat(),
            'metrics': {
                'views': raw_data.get('views', 0),
                'reactions': raw_data.get('reactions', 0),
                'shares': raw_data.get('forwards', 0) or raw_data.get('shares', 0),
                'comments': raw_data.get('comments', 0),
                'reach': raw_data.get('reach', raw_data.get('member_count', 0)),
                'impressions': raw_data.get('impressions', raw_data.get('views', 0)),
                'saves': raw_data.get('saves', 0),
                'forwards': raw_data.get('forwards', 0),
            },
            'engagement': {
                'rate': raw_data.get('engagement_rate', 0.0),
                'total': raw_data.get('reactions', 0) + raw_data.get('forwards', 0),
            },
            'period': {
                'start': raw_data.get('period_start', datetime.utcnow().isoformat()),
                'end': raw_data.get('period_end', datetime.utcnow().isoformat()),
            }
        }
        
        # Calculate derived metrics
        metrics = normalized['metrics']
        engagement = normalized['engagement']
        
        if metrics['impressions'] > 0:
            engagement['rate'] = (engagement['total'] / metrics['impressions']) * 10
        else:
            engagement['rate'] = 0.0
            
        return normalized
    
    async def integrate_with_metrics_system(self, channel_id: int, normalized_data: Dict[str, Any]) -> bool:
        """Integrate normalized data with existing metrics system.
        
        Args:
            channel_id: Database channel ID
            normalized_data: Normalized analytics data
            
        Returns:
            True if integration was successful
        """
        self.logger.info(f"Integrating analytics data for channel {channel_id}")
        
        try:
            # Get database session
            async for session in get_session():
                # Create metrics repository
                metrics_repo = MetricsRepository(session)
                
                # Get all published posts for this channel in the specified period
                from sqlalchemy import select
                from src.models import Post, PostStatus
                
                period_start = normalized_data.get('period', {}).get('start')
                period_end = normalized_data.get('period', {}).get('end')
                
                # Parse dates if they're strings
                if isinstance(period_start, str):
                    period_start = datetime.fromisoformat(period_start.replace('Z', '+00:00'))
                if isinstance(period_end, str):
                    period_end = datetime.fromisoformat(period_end.replace('Z', '+00:00'))
                
                # Get posts published in the period
                posts_query = select(Post).where(
                    Post.channel_id == channel_id,
                    Post.status == PostStatus.PUBLISHED
                )
                
                if period_start and period_end:
                    posts_query = posts_query.where(
                        Post.published_at >= period_start,
                        Post.published_at <= period_end
                    )
                
                result = await session.execute(posts_query)
                posts = result.scalars().all()
                
                # Calculate average metrics per post if we have multiple posts
                if posts:
                    avg_views_per_post = normalized_data['metrics']['views'] / len(posts) if len(posts) > 0 else 0
                    avg_reactions_per_post = normalized_data['metrics']['reactions'] / len(posts) if len(posts) > 0 else 0
                    avg_shares_per_post = normalized_data['metrics']['shares'] / len(posts) if len(posts) > 0 else 0
                    
                    # Update metrics for each post
                    for post in posts:
                        # Check if metrics already exist for this post
                        existing_metrics = await metrics_repo.get_by_post_id(post.id)
                        
                        if existing_metrics:
                            # Update existing metrics
                            await metrics_repo.update(
                                post_id=post.id,
                                views=int(avg_views_per_post),
                                reactions=int(avg_reactions_per_post),
                                shares=int(avg_shares_per_post),
                                engagement_rate=normalized_data['engagement']['rate']
                            )
                        else:
                            # Create new metrics
                            new_metrics = Metrics(
                                post_id=post.id,
                                views=int(avg_views_per_post),
                                reactions=int(avg_reactions_per_post),
                                shares=int(avg_shares_per_post),
                                comments=normalized_data['metrics']['comments'] // len(posts) if len(posts) > 0 else 0,
                                engagement_rate=normalized_data['engagement']['rate']
                            )
                            await metrics_repo.create(new_metrics)
                
                # Commit the transaction
                await session.commit()
                
                self.logger.info(
                    f"Successfully integrated analytics for channel {channel_id}: "
                    f"{len(posts)} posts updated with metrics"
                )
                
                return True
                
        except Exception as e:
            self.logger.error(f"Error integrating with metrics system: {e}")
            return False
    
    async def sync_channel_analytics(
        self,
        channel_username: str,
        channel_id: int,
        days_back: int = 30
    ) -> bool:
        """Sync channel analytics to the database.
        
        Args:
            channel_username: Channel username without @ symbol
            channel_id: Database channel ID
            days_back: Number of days to sync analytics for
            
        Returns:
            True if sync was successful
        """
        self.logger.info(f"Syncing analytics for @{channel_username} (channel {channel_id})")
        
        try:
            # Calculate date range
            period_end = datetime.utcnow()
            period_start = period_end - timedelta(days=days_back)
            
            # Get engagement metrics
            engagement_metrics = await self.get_engagement_metrics(
                channel_username,
                period_start,
                period_end
            )
            
            # Create normalized data
            raw_data = {
                'views': engagement_metrics.views,
                'reactions': engagement_metrics.reactions,
                'shares': engagement_metrics.shares,
                'comments': engagement_metrics.comments,
                'engagement_rate': engagement_metrics.engagement_rate,
                'reach': engagement_metrics.reach,
                'impressions': engagement_metrics.impressions,
                'saves': engagement_metrics.saves,
                'forwards': engagement_metrics.forwards,
                'period_start': period_start.isoformat(),
                'period_end': period_end.isoformat(),
            }
            
            # Process and normalize data
            normalized_data = await self.process_and_normalize_data(raw_data)
            
            # Integrate with metrics system
            success = await self.integrate_with_metrics_system(channel_id, normalized_data)
            
            if success:
                self.logger.info(f"Successfully synced analytics for channel {channel_id}")
                return True
            else:
                self.logger.error(f"Failed to integrate analytics for channel {channel_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error syncing channel analytics: {e}")
            return False