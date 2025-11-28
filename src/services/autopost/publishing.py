"""Publishing Service for auto-posting system with error resilience."""

import logging
import asyncio
import traceback
from typing import Optional, List, Dict, Any
from datetime import datetime
from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.error import TelegramError, RetryAfter, TimedOut
from telegram.constants import ParseMode

from src.models.autopost import AutoPost, AutoPostPublication, PublishStatus, PostStatus
from src.database.autopost_db import autopost_db
from src.services.enhanced_error_handler import EnhancedErrorHandler, ErrorCategory
from src.services.enhanced_publishing_service import EnhancedPublishingService

logger = logging.getLogger(__name__)


class PublishResult:
    """Publication result."""
    
    def __init__(
        self,
        success: bool,
        message_id: Optional[int] = None,
        error: Optional[str] = None,
        retry_count: int = 0,
        rate_limited: bool = False
    ):
        self.success = success
        self.message_id = message_id
        self.error = error
        self.retry_count = retry_count
        self.rate_limited = rate_limited


class AutoPostPublisher:
    """Publisher for auto-posting with error resilience."""
    
    def __init__(self, bot: Bot, max_retries: int = 3):
        """Initialize publisher.
        
        Args:
            bot: Telegram bot instance
            max_retries: Maximum retry attempts
        """
        self.bot = bot
        self.max_retries = max_retries
        self.enhanced_publisher = EnhancedPublishingService(bot, max_retries=max_retries)
        self.error_handler = EnhancedErrorHandler(bot)
    
    async def publish_post(
        self,
        post: AutoPost,
        retry_count: int = 0
    ) -> PublishResult:
        """Publish post to channel with enhanced error handling.
        
        Args:
            post: Post to publish
            retry_count: Current retry count
            
        Returns:
            Publication result
        """
        try:
            logger.info(f"Publishing post {post.id} to channel {post.channel_id}")
            
            # Use the enhanced publisher for better error resilience
            result = await self.enhanced_publisher.publish_post(post, post.channel_id)
            
            # Update post status based on result
            if result.success:
                async with autopost_db.session() as session:
                    post.status = PostStatus.PUBLISHED.value
                    post.published_at = datetime.utcnow()
                    session.add(post)
                    await session.commit()
                
                logger.info(f"✅ Published post {post.id}, message_id: {result.message_id}")
            else:
                async with autopost_db.session() as session:
                    post.status = PostStatus.FAILED.value
                    session.add(post)
                    await session.commit()
                
                logger.error(f"❌ Failed to publish post {post.id}: {result.error_message}")
            
            # Return a compatible result
            return PublishResult(
                success=result.success,
                message_id=result.message_id,
                error=result.error_message,
                retry_count=result.retry_count,
                rate_limited=result.rate_limited
            )
            
        except Exception as e:
            logger.error(f"Unexpected error publishing post {post.id}: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Handle the error with our enhanced error handler
            await self.error_handler.handle_error(
                e,
                ErrorCategory.PUBLISHING,
                "autopost_publisher",
                {"post_id": post.id, "channel_id": post.channel_id}
            )
            
            # Record failure
            await self._record_publication(
                post.channel_id,
                post.id,
                PublishStatus.FAILED,
                error_message=str(e),
                retry_count=retry_count
            )
            
            # Update post status
            async with autopost_db.session() as session:
                post.status = PostStatus.FAILED.value
                session.add(post)
                await session.commit()
            
            return PublishResult(success=False, error=str(e), retry_count=retry_count)
    
    async def publish_with_media(
        self,
        post: AutoPost,
        media: List[dict]
    ) -> PublishResult:
        """Publish post with media using enhanced error handling.
        
        Args:
            post: Post to publish
            media: List of media items
            
        Returns:
            Publication result
        """
        try:
            logger.info(f"Publishing post {post.id} with media")
            
            # Convert media format for enhanced publisher
            from src.services.enhanced_publishing_service import Media
            enhanced_media = []
            for media_item in media:
                enhanced_media.append(Media(
                    type=media_item.get('type', 'photo'),
                    url=media_item['url'],
                    caption=media_item.get('caption')
                ))
            
            # Use the enhanced publisher for better error resilience
            result = await self.enhanced_publisher.publish_with_media(post, post.channel_id, enhanced_media)
            
            # Update post status based on result
            if result.success:
                async with autopost_db.session() as session:
                    post.status = PostStatus.PUBLISHED.value
                    post.published_at = datetime.utcnow()
                    session.add(post)
                    await session.commit()
                
                logger.info(f"✅ Published post {post.id} with media")
            else:
                async with autopost_db.session() as session:
                    post.status = PostStatus.FAILED.value
                    session.add(post)
                    await session.commit()
                
                logger.error(f"❌ Failed to publish post {post.id} with media: {result.error_message}")
            
            # Return a compatible result
            return PublishResult(
                success=result.success,
                message_id=result.message_id,
                error=result.error_message,
                retry_count=result.retry_count,
                rate_limited=result.rate_limited
            )
            
        except Exception as e:
            logger.error(f"Unexpected error publishing post {post.id} with media: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Handle the error with our enhanced error handler
            await self.error_handler.handle_error(
                e,
                ErrorCategory.PUBLISHING,
                "autopost_publisher",
                {"post_id": post.id, "channel_id": post.channel_id, "media_count": len(media)}
            )
            
            # Record failure
            await self._record_publication(
                post.channel_id,
                post.id,
                PublishStatus.FAILED,
                error_message=str(e)
            )
            
            return PublishResult(success=False, error=str(e))
    
    async def publish_poll(
        self,
        channel_id: int,
        question: str,
        options: List[str],
        is_anonymous: bool = True
    ) -> PublishResult:
        """Publish poll to channel using enhanced error handling.
        
        Args:
            channel_id: Channel ID
            question: Poll question
            options: Poll options
            is_anonymous: Whether poll is anonymous
            
        Returns:
            Publication result
        """
        try:
            logger.info(f"Publishing poll to channel {channel_id}")
            
            # Use the enhanced publisher for better error resilience
            result = await self.enhanced_publisher.publish_poll(
                question=question,
                options=options,
                channel_id=channel_id,
                is_quiz=False
            )
            
            logger.info(f"✅ Published poll to channel {channel_id}")
            
            # Return a compatible result
            return PublishResult(
                success=result.success,
                message_id=result.message_id,
                error=result.error_message,
                retry_count=result.retry_count,
                rate_limited=result.rate_limited
            )
            
        except Exception as e:
            logger.error(f"Unexpected error publishing poll to channel {channel_id}: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Handle the error with our enhanced error handler
            await self.error_handler.handle_error(
                e,
                ErrorCategory.PUBLISHING,
                "autopost_publisher",
                {"channel_id": channel_id, "poll_question": question}
            )
            
            # Record failure
            await self._record_publication(
                channel_id,
                None,
                PublishStatus.FAILED,
                error_message=str(e)
            )
            
            return PublishResult(success=False, error=str(e))
    
    def _format_content(self, post: AutoPost) -> str:
        """Format post content.
        
        Args:
            post: Post object
            
        Returns:
            Formatted content
        """
        content = post.content
        
        # Add hashtags if not in content
        if post.hashtags:
            hashtags_text = " ".join(post.hashtags)
            if hashtags_text not in content:
                content += f"\n\n{hashtags_text}"
        
        return content
    
    def _build_keyboard(self, buttons: List[dict]) -> InlineKeyboardMarkup:
        """Build inline keyboard.
        
        Args:
            buttons: List of button dicts
            
        Returns:
            Inline keyboard markup
        """
        keyboard = []
        row = []
        
        for button in buttons:
            btn = InlineKeyboardButton(
                text=button.get('text', 'Button'),
                url=button.get('url')
            )
            row.append(btn)
            
            # Max 2 buttons per row
            if len(row) >= 2:
                keyboard.append(row)
                row = []
        
        if row:
            keyboard.append(row)
        
        return InlineKeyboardMarkup(keyboard)
    
    async def _record_publication(
        self,
        channel_id: int,
        post_id: Optional[str],
        status: PublishStatus,
        telegram_message_id: Optional[int] = None,
        error_message: Optional[str] = None,
        retry_count: int = 0
    ):
        """Record publication in database.
        
        Args:
            channel_id: Channel ID
            post_id: Post ID
            status: Publication status
            telegram_message_id: Telegram message ID
            error_message: Error message if failed
            retry_count: Number of retries
        """
        async with autopost_db.session() as session:
            publication = AutoPostPublication(
                channel_id=channel_id,
                post_id=post_id,
                status=status.value,
                telegram_message_id=telegram_message_id,
                error_message=error_message,
                retry_count=retry_count,
                published_at=datetime.utcnow()
            )
            
            session.add(publication)
            await session.commit()
