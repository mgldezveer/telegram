"""Callback router for handling button clicks."""

import logging
from typing import Dict, Callable, Optional
from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime

logger = logging.getLogger(__name__)


class CallbackRouter:
    """Router for callback queries from inline keyboards."""
    
    def __init__(self):
        """Initialize callback router."""
        self.handlers: Dict[str, Callable] = {}
        self.metrics = {
            'total_callbacks': 0,
            'successful_callbacks': 0,
            'failed_callbacks': 0,
            'last_callback_time': None
        }
    
    def register(self, pattern: str, handler: Callable):
        """Register a callback handler.
        
        Args:
            pattern: Callback data pattern (e.g., "menu", "channel")
            handler: Async handler function
        """
        if not pattern:
            raise ValueError("Pattern cannot be empty")
        
        if not callable(handler):
            raise ValueError(f"Handler for pattern '{pattern}' must be callable")
        
        self.handlers[pattern] = handler
        logger.debug(f"Registered handler for pattern: {pattern}")
    
    async def route_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Route callback query to appropriate handler.
        
        Args:
            update: Telegram update object
            context: Callback context
        """
        # Update metrics
        self.metrics['total_callbacks'] += 1
        self.metrics['last_callback_time'] = datetime.now()
        
        query = update.callback_query
        
        if not query:
            logger.warning("No callback query in update")
            self.metrics['failed_callbacks'] += 1
            return
        
        # Log callback info
        user_id = update.effective_user.id
        callback_data = query.data
        logger.info(f"Callback from user {user_id}: {callback_data}")
        
        # Answer callback query immediately to remove loading state
        try:
            await query.answer()
        except Exception as e:
            logger.warning(f"Failed to answer callback query: {e}")
        
        # Validate callback data
        if not callback_data:
            logger.error("Empty callback data")
            self.metrics['failed_callbacks'] += 1
            try:
                await query.edit_message_text("❌ Ошибка: пустые данные команды")
            except:
                pass
            return
        
        # Parse callback data
        parsed = self.parse_callback_data(callback_data)
        
        if not parsed:
            logger.error(f"Failed to parse callback data: {callback_data}")
            self.metrics['failed_callbacks'] += 1
            try:
                await query.edit_message_text("❌ Ошибка обработки команды")
            except:
                pass
            return
        
        action = parsed['action']
        
        # Handle noop action
        if action == 'noop':
            logger.debug("Noop action, ignoring")
            return
        
        # Find handler
        handler = self.handlers.get(action)
        
        if not handler:
            logger.warning(f"No handler found for action: {action}")
            self.metrics['failed_callbacks'] += 1
            try:
                await query.edit_message_text(
                    f"❌ Команда не поддерживается: {action}\n\n"
                    f"Попробуйте вернуться в главное меню"
                )
            except:
                pass
            return
        
        # Store parsed data in context
        context.user_data['callback_data'] = parsed
        context.user_data['last_callback_action'] = action
        context.user_data['last_callback_time'] = datetime.now()
        
        try:
            # Call handler
            logger.debug(f"Calling handler for action: {action}")
            await handler(update, context)
            self.metrics['successful_callbacks'] += 1
            logger.debug(f"Handler completed successfully for action: {action}")
            
        except Exception as e:
            logger.exception(f"Error in callback handler for {action}: {e}")
            self.metrics['failed_callbacks'] += 1
            
            # Try to show error message
            try:
                error_msg = (
                    f"❌ Произошла ошибка при обработке команды\n\n"
                    f"<b>Действие:</b> {action}\n"
                    f"<b>Ошибка:</b> {str(e)[:100]}\n\n"
                    f"Попробуйте позже или обратитесь к администратору"
                )
                await query.edit_message_text(error_msg, parse_mode='HTML')
            except:
                # If we can't edit the message, try sending a new one
                try:
                    await query.message.reply_text(
                        "❌ Произошла критическая ошибка. Попробуйте /start",
                        parse_mode='HTML'
                    )
                except:
                    logger.error("Failed to send error message to user")
    
    def get_metrics(self) -> dict:
        """Get router metrics.
        
        Returns:
            Dictionary with metrics
        """
        success_rate = 0
        if self.metrics['total_callbacks'] > 0:
            success_rate = (self.metrics['successful_callbacks'] / 
                          self.metrics['total_callbacks'] * 100)
        
        return {
            **self.metrics,
            'success_rate': success_rate,
            'registered_handlers': len(self.handlers)
        }
    
    def parse_callback_data(self, data: str) -> Optional[Dict]:
        """Parse callback data string.
        
        Format: action:param1:param2:...
        
        Args:
            data: Callback data string
            
        Returns:
            Dictionary with parsed data or None
        """
        if not data:
            return None
        
        # Handle special cases
        if data == "noop":
            return {'action': 'noop'}
        
        parts = data.split(':')
        
        if len(parts) < 1:
            return None
        
        parsed = {
            'action': parts[0],
            'params': parts[1:] if len(parts) > 1 else []
        }
        
        # Parse specific patterns
        if parsed['action'] == 'menu':
            parsed['menu'] = parts[1] if len(parts) > 1 else 'main'
        
        elif parsed['action'] == 'channel':
            if len(parts) >= 2:
                parsed['channel_id'] = int(parts[1])
            if len(parts) >= 3:
                parsed['subaction'] = parts[2]
        
        elif parsed['action'] == 'generate':
            if len(parts) >= 2:
                parsed['channel_id'] = int(parts[1])
            if len(parts) >= 3:
                parsed['theme'] = parts[2]
        
        elif parsed['action'] == 'post':
            if len(parts) >= 2:
                parsed['post_id'] = int(parts[1])
            if len(parts) >= 3:
                parsed['subaction'] = parts[2]
        
        elif parsed['action'] == 'confirm':
            if len(parts) >= 2:
                parsed['confirm_action'] = parts[1]
            if len(parts) >= 3:
                parsed['confirm_data'] = ':'.join(parts[2:])
        
        elif parsed['action'] == 'cancel':
            if len(parts) >= 2:
                parsed['cancel_action'] = parts[1]
            if len(parts) >= 3:
                parsed['cancel_data'] = ':'.join(parts[2:])
        
        elif parsed['action'] == 'analytics':
            if len(parts) >= 2:
                parsed['channel_id'] = int(parts[1])
        
        elif parsed['action'] == 'schedule':
            if len(parts) >= 2:
                parsed['channel_id'] = int(parts[1])
        
        elif parsed['action'] == 'theme':
            if len(parts) >= 2:
                parsed['theme'] = parts[1]
        
        elif parsed['action'] == 'quick':
            if len(parts) >= 2:
                parsed['quick_action'] = parts[1]
        
        elif parsed['action'] == 'settings':
            if len(parts) >= 2:
                parsed['setting'] = parts[1]
        
        elif parsed['action'] == 'help':
            if len(parts) >= 2:
                parsed['help_context'] = parts[1]
        
        elif parsed['action'] == 'content':
            if len(parts) >= 2:
                parsed['content_action'] = parts[1]
        
        return parsed
    
    def create_callback_data(self, action: str, **params) -> str:
        """Create callback data string.
        
        Args:
            action: Action name
            **params: Additional parameters
            
        Returns:
            Formatted callback data string
            
        Raises:
            ValueError: If callback data exceeds 64 bytes
        """
        if not action:
            raise ValueError("Action cannot be empty")
        
        parts = [action]
        
        # Add parameters in order
        if 'menu' in params:
            parts.append(params['menu'])
        
        if 'channel_id' in params:
            parts.append(str(params['channel_id']))
        
        if 'subaction' in params:
            parts.append(params['subaction'])
        
        if 'post_id' in params:
            parts.append(str(params['post_id']))
        
        if 'theme' in params:
            parts.append(params['theme'])
        
        if 'page' in params:
            parts.append('page')
            parts.append(str(params['page']))
        
        # Add any remaining params
        for key, value in params.items():
            if key not in ['menu', 'channel_id', 'subaction', 'post_id', 'theme', 'page']:
                parts.append(str(value))
        
        callback_data = ':'.join(parts)
        
        # Telegram callback data limit is 64 bytes
        byte_length = len(callback_data.encode('utf-8'))
        if byte_length > 64:
            error_msg = f"Callback data exceeds 64 bytes ({byte_length}): {callback_data}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        return callback_data
    
    def validate_callback_data(self, data: str) -> bool:
        """Validate callback data format.
        
        Args:
            data: Callback data string
            
        Returns:
            True if valid, False otherwise
        """
        if not data:
            return False
        
        # Check length
        if len(data.encode('utf-8')) > 64:
            logger.warning(f"Callback data too long: {len(data.encode('utf-8'))} bytes")
            return False
        
        # Check format
        if ':' not in data and data != 'noop':
            logger.warning(f"Invalid callback data format: {data}")
            return False
        
        return True
