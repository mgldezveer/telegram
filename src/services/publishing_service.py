"""Publishing service with retry logic."""

import logging
import asyncio
from datetime import datetime
from typing import Optional
from src.models import Post, PostStatus, Channel
from src.services.channel_manager import ChannelManager, PublishResult

logger = logging.getLogger(__name__)


class PublishingService:
    """Service for managing post publication with retry logic."""
    
    def __init__(self, channel_manager: ChannelManager):
        self.channel_manager = channel_manager
        self.max_retries = 3
        self.base_delay = 2  # seconds
    
    async def publish_with_retry(
        self,
        post: Post,
        channel: Channel
    ) -> PublishResult:
        """Publish post with exponential backoff retry."""
        logger.info(f"Publishing post {post.id} with retry logic")
        
        for attempt in range(self.max_retries):
            try:
                # Attempt to publish
                result = await self.channel_manager.publish_post(post, channel)
                
                if result.success:
                    # Update post status
                    await self._update_post_success(post, result.message_id)
                    return result
                else:
                    logger.warning(f"Publish attempt {attempt + 1} failed: {result.error}")
                    
                    if attempt < self.max_retries - 1:
                        # Calculate backoff delay
                        delay = self.base_delay * (2 ** attempt)
                        logger.info(f"Retrying in {delay} seconds...")
                        await asyncio.sleep(delay)
                    else:
                        # All retries exhausted
                        await self._update_post_failure(post, result.error)
                        return result
                        
            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
                
                if attempt < self.max_retries - 1:
                    delay = self.base_delay * (2 ** attempt)
                    await asyncio.sleep(delay)
                else:
                    await self._update_post_failure(post, str(e))
                    return PublishResult(success=False, error=str(e))
        
        # Should not reach here, but just in case
        return PublishResult(success=False, error="Max retries exceeded")
    
    async def _update_post_success(self, post: Post, message_id: Optional[int]):
        """Update post after successful publication."""
        post.status = PostStatus.PUBLISHED
        post.published_at = datetime.utcnow()
        
        logger.info(f"Post {post.id} published successfully at {post.published_at}")
    
    async def _update_post_failure(self, post: Post, error: str):
        """Update post after failed publication."""
        post.status = PostStatus.FAILED
        
        logger.error(f"Post {post.id} failed to publish after {self.max_retries} attempts: {error}")
