"""Publishing Service for auto-posting system."""

import logging
import asyncio
from typing import Optional, List
from datetime import datetime
from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.error import TelegramError
from telegram.constants import ParseMode

from src.models.autopost import AutoPost, AutoPostPublication, PublishStatus, PostStatus
from src.database.autopost_db import autopost_db

logger = logging.getLogger(__name__)


class PublishResult:
    """Publication result."""
    
    def __init__(
        self,
        success: bool,
        message_id: Optional[int] = None,
        error: Optional[str] = None
    ):
        self.success = success
        self.message_id = message_id
        self.error = error


class AutoPostPublisher:
    """Publisher for auto-posting."""
    
    def __init__(self, bot: Bot, max_retries: int = 3):
        """Initialize publisher.
        
        Args:
            bot: Telegram bot instance
            max_retries: Maximum retry attempts
        """
        self.bot = bot
        self.max_retries = max_retries
    
    async def publish_post(
        self,
        post: AutoPost,
        retry_count: int = 0
    ) -> PublishResult:
        """Publish post to channel.
        
        Args:
            post: Post to publish
            retry_count: Current retry count
            
        Returns:
            Publication result
        """
        logger.info(f"Publishing post {post.id} to channel {post.channel_id}")
        
        try:
            # Format content
            content = self._format_content(post)
            
            # Build keyboard if buttons exist
            reply_markup = None
            if post.buttons:
                reply_markup = self._build_keyboard(post.buttons)
            
            # Send message
            message = await self.bot.send_message(
                chat_id=post.channel_id,
                text=content,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup
            )
            
            # Record publication
            await self._record_publication(
                post.channel_id,
                post.id,
                PublishStatus.SUCCESS,
                message.message_id
            )
            
            # Update post status
            async with autopost_db.session() as session:
                post.status = PostStatus.PUBLISHED.value
                post.published_at = datetime.utcnow()
                session.add(post)
                await session.commit()
            
            logger.info(f"✅ Published post {post.id}, message_id: {message.message_id}")
            return PublishResult(success=True, message_id=message.message_id)
            
        except TelegramError as e:
            logger.error(f"Failed to publish post {post.id}: {e}")
            
            # Retry logic
            if retry_count < self.max_retries:
                logger.info(f"Retrying post {post.id} (attempt {retry_count + 1}/{self.max_retries})")
                
                # Exponential backoff
                await asyncio.sleep(2 ** retry_count)
                
                return await self.publish_post(post, retry_count + 1)
            
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
            
            return PublishResult(success=False, error=str(e))
    
    async def publish_with_media(
        self,
        post: AutoPost,
        media: List[dict]
    ) -> PublishResult:
        """Publish post with media.
        
        Args:
            post: Post to publish
            media: List of media items
            
        Returns:
            Publication result
        """
        logger.info(f"Publishing post {post.id} with media")
        
        try:
            content = self._format_content(post)
            
            # Send based on media type
            if len(media) == 1:
                # Single media
                media_item = media[0]
                media_type = media_item.get('type', 'photo')
                
                if media_type == 'photo':
                    message = await self.bot.send_photo(
                        chat_id=post.channel_id,
                        photo=media_item['url'],
                        caption=content,
                        parse_mode=ParseMode.HTML
                    )
                elif media_type == 'video':
                    message = await self.bot.send_video(
                        chat_id=post.channel_id,
                        video=media_item['url'],
                        caption=content,
                        parse_mode=ParseMode.HTML
                    )
                else:
                    # Fallback to text
                    message = await self.bot.send_message(
                        chat_id=post.channel_id,
                        text=content,
                        parse_mode=ParseMode.HTML
                    )
            else:
                # Media group
                from telegram import InputMediaPhoto, InputMediaVideo
                
                media_group = []
                for i, item in enumerate(media[:10]):  # Max 10 items
                    media_type = item.get('type', 'photo')
                    caption = content if i == 0 else None
                    
                    if media_type == 'photo':
                        media_group.append(
                            InputMediaPhoto(media=item['url'], caption=caption)
                        )
                    elif media_type == 'video':
                        media_group.append(
                            InputMediaVideo(media=item['url'], caption=caption)
                        )
                
                messages = await self.bot.send_media_group(
                    chat_id=post.channel_id,
                    media=media_group
                )
                message = messages[0] if messages else None
            
            if message:
                await self._record_publication(
                    post.channel_id,
                    post.id,
                    PublishStatus.SUCCESS,
                    message.message_id
                )
                
                async with autopost_db.session() as session:
                    post.status = PostStatus.PUBLISHED.value
                    post.published_at = datetime.utcnow()
                    session.add(post)
                    await session.commit()
                
                logger.info(f"✅ Published post {post.id} with media")
                return PublishResult(success=True, message_id=message.message_id)
            
            return PublishResult(success=False, error="No message returned")
            
        except TelegramError as e:
            logger.error(f"Failed to publish post {post.id} with media: {e}")
            
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
        """Publish poll to channel.
        
        Args:
            channel_id: Channel ID
            question: Poll question
            options: Poll options
            is_anonymous: Whether poll is anonymous
            
        Returns:
            Publication result
        """
        logger.info(f"Publishing poll to channel {channel_id}")
        
        try:
            message = await self.bot.send_poll(
                chat_id=channel_id,
                question=question,
                options=options,
                is_anonymous=is_anonymous
            )
            
            await self._record_publication(
                channel_id,
                None,
                PublishStatus.SUCCESS,
                message.message_id
            )
            
            logger.info(f"✅ Published poll to channel {channel_id}")
            return PublishResult(success=True, message_id=message.message_id)
            
        except TelegramError as e:
            logger.error(f"Failed to publish poll: {e}")
            
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
