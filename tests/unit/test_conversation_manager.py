"""Unit tests for ConversationManager."""

import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from datetime import datetime, timedelta
from telegram import Update, CallbackQuery, Message, Chat, User
from telegram.ext import ContextTypes, ConversationHandler

from src.interface.conversation_manager import (
    ConversationManager,
    CHANNEL_ID,
    CHANNEL_NAME,
    CUSTOM_THEME,
    EDIT_POST_CONTENT
)


@pytest.fixture
def conversation_manager():
    """Create ConversationManager instance."""
    bot_controller = Mock()
    return ConversationManager(bot_controller=bot_controller)


@pytest.fixture
def mock_update():
    """Create mock Update object."""
    update = Mock(spec=Update)
    update.effective_user = Mock(spec=User)
    update.effective_user.id = 12345
    update.effective_chat = Mock(spec=Chat)
    update.effective_chat.id = 67890
    return update


@pytest.fixture
def mock_context():
    """Create mock Context object."""
    context = Mock(spec=ContextTypes.DEFAULT_TYPE)
    context.user_data = {}
    context.bot = AsyncMock()
    return context


class TestConversationManagerInit:
    """Test ConversationManager initialization."""
    
    def test_init_with_bot_controller(self):
        """Test initialization with bot controller."""
        bot_controller = Mock()
        manager = ConversationManager(bot_controller=bot_controller)
        
        assert manager.bot_controller == bot_controller
        assert manager.conversation_timeout == timedelta(minutes=5)
        assert manager._active_conversations == {}
    
    def test_init_without_bot_controller(self):
        """Test initialization without bot controller."""
        manager = ConversationManager()
        
        assert manager.bot_controller is None
        assert isinstance(manager._active_conversations, dict)



class TestHandlerCreation:
    """Test conversation handler creation."""
    
    def test_create_custom_theme_handler(self, conversation_manager):
        """Test custom theme handler creation."""
        handler = conversation_manager.create_custom_theme_handler()
        
        assert isinstance(handler, ConversationHandler)
        assert handler.name == 'custom_theme'
        assert CUSTOM_THEME in handler.states
    
    def test_create_channel_registration_handler(self, conversation_manager):
        """Test channel registration handler creation."""
        handler = conversation_manager.create_channel_registration_handler()
        
        assert isinstance(handler, ConversationHandler)
        assert handler.name == 'channel_registration'
        assert CHANNEL_ID in handler.states
        assert CHANNEL_NAME in handler.states
    
    def test_create_edit_post_handler(self, conversation_manager):
        """Test edit post handler creation."""
        handler = conversation_manager.create_edit_post_handler()
        
        assert isinstance(handler, ConversationHandler)
        assert handler.name == 'edit_post'
        assert EDIT_POST_CONTENT in handler.states


@pytest.mark.asyncio
class TestChannelRegistration:
    """Test channel registration conversation flow."""
    
    async def test_start_channel_registration(self, conversation_manager, mock_update, mock_context):
        """Test starting channel registration."""
        # Setup
        mock_query = AsyncMock(spec=CallbackQuery)
        mock_update.callback_query = mock_query
        
        # Execute
        result = await conversation_manager.start_channel_registration(mock_update, mock_context)
        
        # Assert
        assert result == CHANNEL_ID
        mock_query.answer.assert_called_once()
        mock_query.edit_message_text.assert_called_once()
        assert 'conversation_start' in mock_context.user_data
        assert mock_context.user_data['conversation_type'] == 'channel_registration'

    
    async def test_receive_channel_id_valid(self, conversation_manager, mock_update, mock_context):
        """Test receiving valid channel ID."""
        # Setup
        mock_message = AsyncMock(spec=Message)
        mock_message.text = "-1001234567890"
        mock_message.reply_text = AsyncMock()
        mock_update.message = mock_message
        
        mock_chat = Mock()
        mock_chat.title = "Test Channel"
        
        mock_member = Mock()
        mock_member.status = "administrator"
        
        mock_context.bot.get_chat = AsyncMock(return_value=mock_chat)
        mock_context.bot.get_chat_member = AsyncMock(return_value=mock_member)
        mock_context.bot.id = 123
        
        # Execute
        result = await conversation_manager.receive_channel_id(mock_update, mock_context)
        
        # Assert
        assert result == CHANNEL_NAME
        assert mock_context.user_data['new_channel_id'] == -1001234567890
        assert mock_context.user_data['new_channel_title'] == "Test Channel"
    
    async def test_receive_channel_id_invalid_format(self, conversation_manager, mock_update, mock_context):
        """Test receiving invalid channel ID format."""
        # Setup
        mock_message = AsyncMock(spec=Message)
        mock_message.text = "invalid_id"
        mock_message.reply_text = AsyncMock()
        mock_update.message = mock_message
        
        # Execute
        result = await conversation_manager.receive_channel_id(mock_update, mock_context)
        
        # Assert
        assert result == CHANNEL_ID  # Stay in same state
        mock_message.reply_text.assert_called_once()
        assert "❌" in mock_message.reply_text.call_args[0][0]

    
    async def test_receive_channel_id_bot_not_admin(self, conversation_manager, mock_update, mock_context):
        """Test receiving channel ID where bot is not admin."""
        # Setup
        mock_message = AsyncMock(spec=Message)
        mock_message.text = "-1001234567890"
        mock_message.reply_text = AsyncMock()
        mock_update.message = mock_message
        
        mock_chat = Mock()
        mock_chat.title = "Test Channel"
        
        mock_member = Mock()
        mock_member.status = "member"  # Not admin
        
        mock_context.bot.get_chat = AsyncMock(return_value=mock_chat)
        mock_context.bot.get_chat_member = AsyncMock(return_value=mock_member)
        mock_context.bot.id = 123
        
        # Execute
        result = await conversation_manager.receive_channel_id(mock_update, mock_context)
        
        # Assert
        assert result == CHANNEL_ID
        assert "не является администратором" in mock_message.reply_text.call_args[0][0]
    
    async def test_receive_channel_name_valid(self, conversation_manager, mock_update, mock_context):
        """Test receiving valid channel name."""
        # Setup
        mock_message = AsyncMock(spec=Message)
        mock_message.text = "My Test Channel"
        mock_message.reply_text = AsyncMock()
        mock_update.message = mock_message
        
        mock_context.user_data['new_channel_id'] = -1001234567890
        mock_context.user_data['new_channel_title'] = "Test Channel"
        
        # Mock channel manager
        mock_channel_manager = AsyncMock()
        mock_channel = Mock()
        mock_channel_manager.register_channel = AsyncMock(return_value=mock_channel)
        conversation_manager.bot_controller.channel_manager = mock_channel_manager
        
        # Mock menu system
        mock_menu_system = AsyncMock()
        mock_menu_system.show_channels_menu = AsyncMock()
        conversation_manager.bot_controller.menu_system = mock_menu_system
        
        # Execute
        result = await conversation_manager.receive_channel_name(mock_update, mock_context)
        
        # Assert
        assert result == ConversationHandler.END
        mock_channel_manager.register_channel.assert_called_once()
        mock_menu_system.show_channels_menu.assert_called_once()
        assert 'new_channel_id' not in mock_context.user_data
        assert 'new_channel_title' not in mock_context.user_data


@pytest.mark.asyncio
class TestConversationControl:
    """Test conversation control methods."""
    
    async def test_cancel_conversation_with_callback(self, conversation_manager, mock_update, mock_context):
        """Test cancelling conversation via callback query."""
        # Setup
        mock_query = AsyncMock(spec=CallbackQuery)
        mock_query.edit_message_text = AsyncMock()
        mock_update.callback_query = mock_query
        mock_update.message = None
        
        mock_context.user_data['conversation_type'] = 'test_conversation'
        mock_context.user_data['new_channel_id'] = 123
        
        # Execute
        result = await conversation_manager.cancel_conversation(mock_update, mock_context)
        
        # Assert
        assert result == ConversationHandler.END
        mock_query.answer.assert_called_once()
        mock_query.edit_message_text.assert_called_once()
        assert 'new_channel_id' not in mock_context.user_data
        assert 'conversation_type' not in mock_context.user_data
    
    async def test_cancel_conversation_with_message(self, conversation_manager, mock_update, mock_context):
        """Test cancelling conversation via message."""
        # Setup
        mock_message = AsyncMock(spec=Message)
        mock_message.reply_text = AsyncMock()
        mock_update.message = mock_message
        mock_update.callback_query = None
        
        # Execute
        result = await conversation_manager.cancel_conversation(mock_update, mock_context)
        
        # Assert
        assert result == ConversationHandler.END
        mock_message.reply_text.assert_called_once()
    
    async def test_handle_conversation_timeout(self, conversation_manager, mock_update, mock_context):
        """Test handling conversation timeout."""
        # Setup
        mock_message = AsyncMock(spec=Message)
        mock_message.reply_text = AsyncMock()
        mock_update.message = mock_message
        
        mock_context.user_data['conversation_type'] = 'test'
        
        # Execute
        result = await conversation_manager.handle_conversation_timeout(mock_update, mock_context)
        
        # Assert
        assert result == ConversationHandler.END
        assert 'conversation_type' not in mock_context.user_data
        assert "Время ожидания истекло" in mock_message.reply_text.call_args[0][0]


class TestConversationTracking:
    """Test conversation tracking methods."""
    
    def test_track_conversation(self, conversation_manager):
        """Test tracking active conversation."""
        user_id = 12345
        conversation_type = 'channel_registration'
        
        conversation_manager.track_conversation(user_id, conversation_type)
        
        assert user_id in conversation_manager._active_conversations
        assert conversation_manager._active_conversations[user_id]['type'] == conversation_type
        assert 'start_time' in conversation_manager._active_conversations[user_id]
    
    def test_end_conversation(self, conversation_manager):
        """Test ending tracked conversation."""
        user_id = 12345
        conversation_manager._active_conversations[user_id] = {
            'type': 'test',
            'start_time': datetime.now()
        }
        
        conversation_manager.end_conversation(user_id)
        
        assert user_id not in conversation_manager._active_conversations
    
    def test_get_active_conversations_count(self, conversation_manager):
        """Test getting active conversations count."""
        conversation_manager._active_conversations = {
            1: {'type': 'test1'},
            2: {'type': 'test2'},
            3: {'type': 'test3'}
        }
        
        count = conversation_manager.get_active_conversations_count()
        
        assert count == 3


@pytest.mark.asyncio
class TestCleanup:
    """Test cleanup functionality."""
    
    async def test_cleanup_expired_conversations(self, conversation_manager):
        """Test cleaning up expired conversations."""
        # Setup expired conversation
        old_time = datetime.now() - timedelta(minutes=10)
        conversation_manager._active_conversations = {
            1: {'type': 'test1', 'start_time': old_time},
            2: {'type': 'test2', 'start_time': datetime.now()}
        }
        
        # Execute
        cleaned = await conversation_manager.cleanup_expired_conversations()
        
        # Assert
        assert cleaned == 1
        assert 1 not in conversation_manager._active_conversations
        assert 2 in conversation_manager._active_conversations


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
