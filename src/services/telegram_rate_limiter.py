"""Telegram API rate limiter."""

import logging
import time
import asyncio
from telegram.error import RetryAfter, NetworkError, TimedOut

logger = logging.getLogger(__name__)


class TelegramRateLimiter:
    """Rate limiter for Telegram API calls.
    
    Implements protection against Telegram's 30 messages/second limit
    and handles RetryAfter errors automatically.
    """
    
    def __init__(self, messages_per_second: int = 25):
        """Initialize rate limiter.
        
        Args:
            messages_per_second: Max messages per second (default 25, safe margin below 30)
        """
        self.messages_per_second = messages_per_second
        self.min_interval = 1.0 / messages_per_second
        self.last_send_time = 0
        self.lock = asyncio.Lock()
        
        logger.info(f"Telegram rate limiter initialized: {messages_per_second} msg/sec")
    
    async def throttle(self):
        """Throttle to respect rate limits."""
        async with self.lock:
            now = time.time()
            time_since_last = now - self.last_send_time
            
            if time_since_last < self.min_interval:
                wait_time = self.min_interval - time_since_last
                await asyncio.sleep(wait_time)
            
            self.last_send_time = time.time()
    
    async def send_message(self, bot, chat_id, text, **kwargs):
        """Send message with rate limiting and retry logic.
        
        Args:
            bot: Bot instance
            chat_id: Chat ID
            text: Message text
            **kwargs: Additional arguments for send_message
            
        Returns:
            Message object or None if failed
        """
        await self.throttle()
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                return await bot.send_message(chat_id, text, **kwargs)
            
            except RetryAfter as e:
                logger.warning(f"Rate limited by Telegram, waiting {e.retry_after}s")
                await asyncio.sleep(e.retry_after)
                continue
            
            except (NetworkError, TimedOut) as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(f"Network error, retrying in {wait_time}s: {e}")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.error(f"Failed after {max_retries} attempts: {e}")
                    return None
            
            except Exception as e:
                logger.error(f"Unexpected error sending message: {e}")
                return None
        
        return None
    
    async def edit_message_text(self, bot, chat_id, message_id, text, **kwargs):
        """Edit message with rate limiting.
        
        Args:
            bot: Bot instance
            chat_id: Chat ID
            message_id: Message ID
            text: New text
            **kwargs: Additional arguments
            
        Returns:
            Message object or None if failed
        """
        await self.throttle()
        
        try:
            return await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=text,
                **kwargs
            )
        except RetryAfter as e:
            logger.warning(f"Rate limited, waiting {e.retry_after}s")
            await asyncio.sleep(e.retry_after)
            return await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=text,
                **kwargs
            )
        except Exception as e:
            logger.error(f"Error editing message: {e}")
            return None
