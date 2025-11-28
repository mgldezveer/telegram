"""Улучшенный сервис публикации с продвинутым rate limiting."""

import logging
import asyncio
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Callable, Union
from dataclasses import dataclass
from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.error import TelegramError, RetryAfter, TimedOut
from telegram.constants import ParseMode

from src.models.autopost import AutoPost, AutoPostPublication, PublishStatus, PostStatus
from src.database.autopost_db import autopost_db
from src.cache import cache
from src.services.alerting_service import AlertingService, AlertSeverity
from src.monitoring.enhanced_monitoring import enhanced_monitoring
from src.services.enhanced_error_handler import EnhancedErrorHandler, ErrorCategory

logger = logging.getLogger(__name__)


@dataclass
class Media:
    """Медиа вложение."""
    type: str  # photo, video, document
    url: str
    caption: Optional[str] = None


@dataclass
class PublishResult:
    """Результат публикации."""
    success: bool
    message_id: Optional[int] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    rate_limited: bool = False


class EnhancedPublishingService:
    """Улучшенный сервис публикации с продвинутым rate limiting."""
    
    def __init__(
        self, 
        bot: Bot, 
        max_retries: int = 3, 
        retry_delay: int = 5,
        rate_limit_per_second: float = 25.0, # Telegram API limit is ~30 msg/sec
        rate_limit_window: int = 1,  # 1 second window
        channel_specific_limits: Optional[Dict[int, float]] = None
    ):
        """Инициализировать улучшенный сервис публикации.
        
        Args:
            bot: Экземпляр Telegram бота
            max_retries: Максимальное количество попыток
            retry_delay: Базовая задержка между попытками в секундах
            rate_limit_per_second: Максимальное количество сообщений в секунду
            rate_limit_window: Время окна ограничения в секундах
            channel_specific_limits: Ограничения для конкретных каналов
        """
        self.bot = bot
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.rate_limit_per_second = rate_limit_per_second
        self.rate_limit_window = rate_limit_window
        self.channel_specific_limits = channel_specific_limits or {}
        
        # Для отслеживания rate limit
        self._requests: Dict[str, List[datetime]] = {}  # channel_id -> timestamps
        self._lock = asyncio.Lock()
    
    def _get_channel_rate_limit(self, channel_id: int) -> float:
        """Получить ограничение для конкретного канала.
        
        Args:
            channel_id: ID канала
            
        Returns:
            Ограничение в сообщениях в секунду
        """
        return self.channel_specific_limits.get(channel_id, self.rate_limit_per_second)
    
    async def _check_rate_limit(self, channel_id: int) -> bool:
        """Проверить, превышено ли ограничение запросов для канала.
        
        Args:
            channel_id: ID канала
            
        Returns:
            True если можно отправлять, False если превышено
        """
        async with self._lock:
            now = datetime.now()
            channel_limit = self._get_channel_rate_limit(channel_id)
            max_requests = int(channel_limit * self.rate_limit_window)
            
            # Получить историю запросов для канала
            channel_key = str(channel_id)
            if channel_key not in self._requests:
                self._requests[channel_key] = []
            
            # Удалить устаревшие записи
            self._requests[channel_key] = [
                ts for ts in self._requests[channel_key]
                if now - ts < timedelta(seconds=self.rate_limit_window)
            ]
            
            # Проверить, можно ли отправить
            if len(self._requests[channel_key]) >= max_requests:
                return False
            
            # Записать текущий запрос
            self._requests[channel_key].append(now)
            return True
    
    async def _wait_for_rate_limit(self, channel_id: int) -> bool:
        """Дождаться, пока не будет доступно место под запрос.
        
        Args:
            channel_id: ID канала
            
        Returns:
            True если можно отправлять, False если таймаут
        """
        timeout = 60  # 60 секунд таймаута
        start_time = datetime.now()
        
        while (datetime.now() - start_time).total_seconds() < timeout:
            if await self._check_rate_limit(channel_id):
                return True
            await asyncio.sleep(0.1)
        
        return False
    
    async def publish_post(
        self,
        post: AutoPost,
        channel_id: int
    ) -> PublishResult:
        """Опубликовать пост в канал с продвинутым rate limiting.
        
        Args:
            post: Объект поста для публикации
            channel_id: ID канала Telegram
            
        Returns:
            Результат публикации
        """
        retry_count = 0
        last_error = None
        
        while retry_count <= self.max_retries:
            try:
                # Проверить rate limit
                if not await self._wait_for_rate_limit(channel_id):
                    error_msg = f"Rate limit timeout for channel {channel_id}"
                    logger.warning(f"⚠️ {error_msg}")
                    
                    await self._record_publication(
                        channel_id=channel_id,
                        post_id=post.id,
                        status=PublishStatus.FAILED,
                        error_message=error_msg,
                        retry_count=retry_count,
                        rate_limited=True
                    )
                    
                    return PublishResult(
                        success=False,
                        error_message=error_msg,
                        retry_count=retry_count,
                        rate_limited=True
                    )
                
                # Форматировать контент
                content = self._format_content(post)
                
                # Создать клавиатуру если есть кнопки
                reply_markup = None
                if post.buttons:
                    reply_markup = self._create_keyboard(post.buttons)
                
                # Отправить сообщение
                message = await self.bot.send_message(
                    chat_id=channel_id,
                    text=content,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup,
                    disable_web_page_preview=False
                )
                
                # Записать успешную публикацию
                await self._record_publication(
                    channel_id=channel_id,
                    post_id=post.id,
                    status=PublishStatus.SUCCESS,
                    telegram_message_id=message.message_id,
                    retry_count=retry_count
                )
                
                logger.info(f"✅ Published post {post.id} to channel {channel_id}")
                
                return PublishResult(
                    success=True,
                    message_id=message.message_id,
                    retry_count=retry_count
                )
                
            except RetryAfter as e:
                # Превышено ограничение частоты, ждать и повторить
                wait_time = e.retry_after
                logger.warning(f"⚠️ Rate limit hit, waiting {wait_time}s before retry")
                await asyncio.sleep(wait_time)
                retry_count += 1
                last_error = str(e)
                
            except TimedOut as e:
                # Таймаут, повторить с экспоненциальной задержкой
                wait_time = self.retry_delay * (2 ** retry_count)
                logger.warning(f"⚠️ Timeout, waiting {wait_time}s before retry")
                await asyncio.sleep(wait_time)
                retry_count += 1
                last_error = str(e)
                
            except TelegramError as e:
                # Другие ошибки Telegram
                logger.error(f"❌ Telegram error publishing post {post.id}: {e}")
                
                # Записать неудачную публикацию
                await self._record_publication(
                    channel_id=channel_id,
                    post_id=post.id,
                    status=PublishStatus.FAILED,
                    error_message=str(e),
                    retry_count=retry_count
                )
                
                return PublishResult(
                    success=False,
                    error_message=str(e),
                    retry_count=retry_count
                )
                
            except Exception as e:
                # Неожиданные ошибки
                logger.error(f"❌ Unexpected error publishing post {post.id}: {e}")
                
                await self._record_publication(
                    channel_id=channel_id,
                    post_id=post.id,
                    status=PublishStatus.FAILED,
                    error_message=str(e),
                    retry_count=retry_count
                )
                
                return PublishResult(
                    success=False,
                    error_message=str(e),
                    retry_count=retry_count
                )
        
        # Превышено максимальное количество попыток
        logger.error(f"❌ Max retries exceeded for post {post.id}")
        
        await self._record_publication(
            channel_id=channel_id,
            post_id=post.id,
            status=PublishStatus.FAILED,
            error_message=f"Max retries exceeded: {last_error}",
            retry_count=retry_count
        )
        
        return PublishResult(
            success=False,
            error_message=f"Max retries exceeded: {last_error}",
            retry_count=retry_count
        )
    
    async def publish_with_media(
        self,
        post: AutoPost,
        channel_id: int,
        media: List[Media]
    ) -> PublishResult:
        """Опубликовать пост с медиа вложениями.
        
        Args:
            post: Объект поста для публикации
            channel_id: ID канала Telegram
            media: Список медиа вложений
            
        Returns:
            Результат публикации
        """
        try:
            # Проверить rate limit
            if not await self._wait_for_rate_limit(channel_id):
                error_msg = f"Rate limit timeout for channel {channel_id} (media)"
                logger.warning(f"⚠️ {error_msg}")
                
                await self._record_publication(
                    channel_id=channel_id,
                    post_id=post.id,
                    status=PublishStatus.FAILED,
                    error_message=error_msg,
                    rate_limited=True
                )
                
                return PublishResult(
                    success=False,
                    error_message=error_msg,
                    rate_limited=True
                )
            
            content = self._format_content(post)
            reply_markup = None
            
            if post.buttons:
                reply_markup = self._create_keyboard(post.buttons)
            
            # Обработать одиночное медиа
            if len(media) == 1:
                media_item = media[0]
                
                if media_item.type == "photo":
                    message = await self.bot.send_photo(
                        chat_id=channel_id,
                        photo=media_item.url,
                        caption=content,
                        parse_mode=ParseMode.HTML,
                        reply_markup=reply_markup
                    )
                elif media_item.type == "video":
                    message = await self.bot.send_video(
                        chat_id=channel_id,
                        video=media_item.url,
                        caption=content,
                        parse_mode=ParseMode.HTML,
                        reply_markup=reply_markup
                    )
                elif media_item.type == "document":
                    message = await self.bot.send_document(
                        chat_id=channel_id,
                        document=media_item.url,
                        caption=content,
                        parse_mode=ParseMode.HTML,
                        reply_markup=reply_markup
                    )
                else:
                    raise ValueError(f"Unsupported media type: {media_item.type}")
                
                await self._record_publication(
                    channel_id=channel_id,
                    post_id=post.id,
                    status=PublishStatus.SUCCESS,
                    telegram_message_id=message.message_id
                )
                
                return PublishResult(success=True, message_id=message.message_id)
            
            # Обработать группу медиа (несколько медиа)
            else:
                # Для групп медиа отправить как альбом
                # Примечание: у групп медиа нет поддержки inline кнопок
                logger.warning("⚠️ Media groups don't support inline buttons")
                
                # Отправить группу медиа
                from telegram import InputMediaPhoto, InputMediaVideo
                
                media_group = []
                for i, media_item in enumerate(media):
                    caption = content if i == 0 else None
                    
                    if media_item.type == "photo":
                        media_group.append(
                            InputMediaPhoto(media=media_item.url, caption=caption)
                        )
                    elif media_item.type == "video":
                        media_group.append(
                            InputMediaVideo(media=media_item.url, caption=caption)
                        )
                
                messages = await self.bot.send_media_group(
                    chat_id=channel_id,
                    media=media_group
                )
                
                await self._record_publication(
                    channel_id=channel_id,
                    post_id=post.id,
                    status=PublishStatus.SUCCESS,
                    telegram_message_id=messages[0].message_id
                )
                
                return PublishResult(success=True, message_id=messages[0].message_id)
                
        except Exception as e:
            logger.error(f"❌ Failed to publish post with media: {e}")
            
            await self._record_publication(
                channel_id=channel_id,
                post_id=post.id,
                status=PublishStatus.FAILED,
                error_message=str(e)
            )
            
            return PublishResult(success=False, error_message=str(e))
    
    async def publish_poll(
        self,
        question: str,
        options: List[str],
        channel_id: int,
        is_quiz: bool = False,
        correct_option_id: Optional[int] = None
    ) -> PublishResult:
        """Опубликовать опрос или викторину.
        
        Args:
            question: Вопрос опроса
            options: Список вариантов
            channel_id: ID канала Telegram
            is_quiz: Является ли викториной (с правильным ответом)
            correct_option_id: Индекс правильного ответа (для викторин)
            
        Returns:
            Результат публикации
        """
        try:
            # Проверить rate limit
            if not await self._wait_for_rate_limit(channel_id):
                error_msg = f"Rate limit timeout for channel {channel_id} (poll)"
                logger.warning(f"⚠️ {error_msg}")
                
                await self._record_publication(
                    channel_id=channel_id,
                    post_id=None,  # У опросов нет ID поста
                    status=PublishStatus.FAILED,
                    error_message=error_msg,
                    rate_limited=True
                )
                
                return PublishResult(
                    success=False,
                    error_message=error_msg,
                    rate_limited=True
                )
            
            poll_type = "quiz" if is_quiz else "regular"
            
            message = await self.bot.send_poll(
                chat_id=channel_id,
                question=question,
                options=options,
                is_anonymous=True,
                type=poll_type,
                correct_option_id=correct_option_id if is_quiz else None
            )
            
            await self._record_publication(
                channel_id=channel_id,
                post_id=None,  # У опросов нет ID поста
                status=PublishStatus.SUCCESS,
                telegram_message_id=message.message_id
            )
            
            logger.info(f"✅ Published {poll_type} to channel {channel_id}")
            
            return PublishResult(success=True, message_id=message.message_id)
            
        except Exception as e:
            logger.error(f"❌ Failed to publish poll: {e}")
            
            await self._record_publication(
                channel_id=channel_id,
                post_id=None,
                status=PublishStatus.FAILED,
                error_message=str(e)
            )
            
            return PublishResult(success=False, error_message=str(e))
    
    def _format_content(self, post: AutoPost) -> str:
        """Форматировать контент поста для публикации.
        
        Args:
            post: Объект поста
            
        Returns:
            Форматированный контент
        """
        content = post.content
        
        # Добавить хэштеги если их нет в контенте
        if post.hashtags:
            existing_tags = set(tag.lower() for tag in post.hashtags if tag in content)
            new_tags = [tag for tag in post.hashtags if tag.lower() not in existing_tags]
            
            if new_tags:
                content += "\n\n" + " ".join(new_tags)
        
        return content
    
    def _create_keyboard(self, buttons: List[Dict[str, str]]) -> InlineKeyboardMarkup:
        """Создать inline клавиатуру из данных кнопок.
        
        Args:
            buttons: Список словарей кнопок с ключами 'text' и 'url'
            
        Returns:
            Inline клавиатура
        """
        keyboard = []
        
        for button in buttons:
            keyboard.append([
                InlineKeyboardButton(
                    text=button.get("text", "Button"),
                    url=button.get("url", "https://telegram.org")
                )
            ])
        
        return InlineKeyboardMarkup(keyboard)
    
    async def _record_publication(
        self,
        channel_id: int,
        post_id: Optional[str],
        status: PublishStatus,
        telegram_message_id: Optional[int] = None,
        error_message: Optional[str] = None,
        retry_count: int = 0,
        rate_limited: bool = False
    ) -> None:
        """Записать публикацию в базу данных.
        
        Args:
            channel_id: ID канала Telegram
            post_id: ID поста (опционально)
            status: Статус публикации
            telegram_message_id: ID сообщения Telegram (при успехе)
            error_message: Сообщение об ошибке (при неудаче)
            retry_count: Количество повторов
            rate_limited: Превышено ли ограничение частоты
        """
        try:
            async with autopost_db.session() as session:
                publication = AutoPostPublication(
                    channel_id=channel_id,
                    post_id=post_id,
                    status=status.value,
                    published_at=datetime.utcnow(),
                    telegram_message_id=telegram_message_id,
                    error_message=error_message,
                    retry_count=retry_count,
                    rate_limited=rate_limited
                )
                
                session.add(publication)
                await session.commit()
                
        except Exception as e:
            logger.error(f"❌ Failed to record publication: {e}")
    
    async def get_channel_stats(self, channel_id: int) -> dict:
        """Получить статистику по каналу.
        
        Args:
            channel_id: ID канала
            
        Returns:
            Словарь со статистикой
        """
        async with self._lock:
            now = datetime.now()
            channel_key = str(channel_id)
            
            if channel_key not in self._requests:
                recent_requests = 0
            else:
                # Подсчитать запросы за последнюю секунду
                recent_requests = len([
                    ts for ts in self._requests[channel_key]
                    if now - ts < timedelta(seconds=1)
                ])
            
            channel_limit = self._get_channel_rate_limit(channel_id)
            
            return {
                'channel_id': channel_id,
                'requests_last_second': recent_requests,
                'rate_limit_per_second': channel_limit,
                'remaining_requests': max(0, int(channel_limit) - recent_requests),
                'is_rate_limited': recent_requests >= channel_limit
            }
    
    async def reset_channel_stats(self, channel_id: int):
        """Сбросить статистику для канала.
        
        Args:
            channel_id: ID канала
        """
        async with self._lock:
            channel_key = str(channel_id)
            if channel_key in self._requests:
                del self._requests[channel_key]