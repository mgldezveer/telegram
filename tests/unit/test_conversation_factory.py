"""Unit tests for ConversationHandler factory."""

import pytest
from telegram.ext import (
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)
from src.interface.conversation_factory import ConversationHandlerFactory


# Dummy handlers for testing
async def dummy_handler(update, context):
    """Dummy handler function."""
    pass


class TestConversationHandlerFactory:
    """Test ConversationHandlerFactory functionality."""
    
    def test_create_handler_basic(self):
        """Test creating basic handler without callbacks."""
        handler = ConversationHandlerFactory.create_handler(
            name='test_handler',
            entry_points=[CommandHandler('start', dummy_handler)],
            states={
                0: [MessageHandler(filters.TEXT, dummy_handler)]
            },
            fallbacks=[CommandHandler('cancel', dummy_handler)]
        )
        
        assert isinstance(handler, ConversationHandler)
        assert handler.name == 'test_handler'
        assert handler.per_message is False  # No callbacks, so False
    
    def test_create_handler_with_callback_in_states(self):
        """Test handler with CallbackQueryHandler in states."""
        handler = ConversationHandlerFactory.create_handler(
            name='test_callback',
            entry_points=[CommandHandler('start', dummy_handler)],
            states={
                0: [CallbackQueryHandler(dummy_handler, pattern='^test$')]
            },
            fallbacks=[CommandHandler('cancel', dummy_handler)]
        )
        
        assert isinstance(handler, ConversationHandler)
        assert handler.per_message is True  # Auto-detected callback
    
    def test_create_handler_with_callback_in_entry_points(self):
        """Test handler with CallbackQueryHandler in entry points."""
        handler = ConversationHandlerFactory.create_handler(
            name='test_entry_callback',
            entry_points=[CallbackQueryHandler(dummy_handler, pattern='^start$')],
            states={
                0: [MessageHandler(filters.TEXT, dummy_handler)]
            },
            fallbacks=[CommandHandler('cancel', dummy_handler)]
        )
        
        assert isinstance(handler, ConversationHandler)
        assert handler.per_message is True  # Auto-detected callback in entry
    
    def test_create_handler_explicit_per_message_true(self):
        """Test handler with explicit per_message=True."""
        handler = ConversationHandlerFactory.create_handler(
            name='test_explicit_true',
            entry_points=[CommandHandler('start', dummy_handler)],
            states={
                0: [MessageHandler(filters.TEXT, dummy_handler)]
            },
            fallbacks=[CommandHandler('cancel', dummy_handler)],
            per_message=True
        )
        
        assert handler.per_message is True
    
    def test_create_handler_explicit_per_message_false(self):
        """Test handler with explicit per_message=False."""
        handler = ConversationHandlerFactory.create_handler(
            name='test_explicit_false',
            entry_points=[CommandHandler('start', dummy_handler)],
            states={
                0: [MessageHandler(filters.TEXT, dummy_handler)]
            },
            fallbacks=[CommandHandler('cancel', dummy_handler)],
            per_message=False
        )
        
        assert handler.per_message is False
    
    def test_create_handler_mixed_handlers(self):
        """Test handler with mixed handler types including callbacks."""
        handler = ConversationHandlerFactory.create_handler(
            name='test_mixed',
            entry_points=[CommandHandler('start', dummy_handler)],
            states={
                0: [
                    MessageHandler(filters.TEXT, dummy_handler),
                    CallbackQueryHandler(dummy_handler, pattern='^btn$')
                ],
                1: [MessageHandler(filters.TEXT, dummy_handler)]
            },
            fallbacks=[CommandHandler('cancel', dummy_handler)]
        )
        
        assert handler.per_message is True  # Has callback in states
    
    def test_create_handler_with_timeout(self):
        """Test handler with conversation timeout."""
        handler = ConversationHandlerFactory.create_handler(
            name='test_timeout',
            entry_points=[CommandHandler('start', dummy_handler)],
            states={
                0: [MessageHandler(filters.TEXT, dummy_handler)]
            },
            fallbacks=[CommandHandler('cancel', dummy_handler)],
            conversation_timeout=300.0
        )
        
        assert handler.conversation_timeout == 300.0
    
    def test_create_handler_with_per_chat_per_user(self):
        """Test handler with per_chat and per_user settings."""
        handler = ConversationHandlerFactory.create_handler(
            name='test_per_settings',
            entry_points=[CommandHandler('start', dummy_handler)],
            states={
                0: [MessageHandler(filters.TEXT, dummy_handler)]
            },
            fallbacks=[CommandHandler('cancel', dummy_handler)],
            per_chat=True,
            per_user=True
        )
        
        assert handler.per_chat is True
        assert handler.per_user is True
    
    def test_create_handler_with_allow_reentry(self):
        """Test handler with allow_reentry setting."""
        handler = ConversationHandlerFactory.create_handler(
            name='test_reentry',
            entry_points=[CommandHandler('start', dummy_handler)],
            states={
                0: [MessageHandler(filters.TEXT, dummy_handler)]
            },
            fallbacks=[CommandHandler('cancel', dummy_handler)],
            allow_reentry=True
        )
        
        assert handler.allow_reentry is True
    
    def test_validate_handler_config_empty_entry_points(self):
        """Test validation with empty entry points."""
        warnings = ConversationHandlerFactory.validate_handler_config(
            name='test',
            entry_points=[],
            states={0: [MessageHandler(filters.TEXT, dummy_handler)]},
            fallbacks=[CommandHandler('cancel', dummy_handler)],
            per_message=False
        )
        
        assert len(warnings) > 0
        assert any('entry points' in w.lower() for w in warnings)
    
    def test_validate_handler_config_empty_states(self):
        """Test validation with empty states."""
        warnings = ConversationHandlerFactory.validate_handler_config(
            name='test',
            entry_points=[CommandHandler('start', dummy_handler)],
            states={},
            fallbacks=[CommandHandler('cancel', dummy_handler)],
            per_message=False
        )
        
        assert len(warnings) > 0
        assert any('states' in w.lower() for w in warnings)
    
    def test_validate_handler_config_empty_fallbacks(self):
        """Test validation with empty fallbacks."""
        warnings = ConversationHandlerFactory.validate_handler_config(
            name='test',
            entry_points=[CommandHandler('start', dummy_handler)],
            states={0: [MessageHandler(filters.TEXT, dummy_handler)]},
            fallbacks=[],
            per_message=False
        )
        
        assert len(warnings) > 0
        assert any('fallbacks' in w.lower() for w in warnings)
    
    def test_validate_handler_config_callback_without_per_message(self):
        """Test validation warns about callback without per_message."""
        warnings = ConversationHandlerFactory.validate_handler_config(
            name='test',
            entry_points=[CommandHandler('start', dummy_handler)],
            states={
                0: [CallbackQueryHandler(dummy_handler, pattern='^test$')]
            },
            fallbacks=[CommandHandler('cancel', dummy_handler)],
            per_message=False
        )
        
        assert len(warnings) > 0
        assert any('per_message=false' in w.lower() for w in warnings)
        assert any('callbackqueryhandler' in w.lower() for w in warnings)
    
    def test_validate_handler_config_valid(self):
        """Test validation with valid configuration."""
        warnings = ConversationHandlerFactory.validate_handler_config(
            name='test',
            entry_points=[CommandHandler('start', dummy_handler)],
            states={
                0: [CallbackQueryHandler(dummy_handler, pattern='^test$')]
            },
            fallbacks=[CommandHandler('cancel', dummy_handler)],
            per_message=True
        )
        
        # Should have no warnings (or only non-critical ones)
        critical_warnings = [w for w in warnings if 'per_message' in w.lower()]
        assert len(critical_warnings) == 0
    
    def test_has_callback_handlers_detection(self):
        """Test callback handler detection in states."""
        # With callback
        states_with_callback = {
            0: [CallbackQueryHandler(dummy_handler, pattern='^test$')]
        }
        assert ConversationHandlerFactory._has_callback_handlers(states_with_callback)
        
        # Without callback
        states_without_callback = {
            0: [MessageHandler(filters.TEXT, dummy_handler)]
        }
        assert not ConversationHandlerFactory._has_callback_handlers(states_without_callback)
        
        # Mixed
        states_mixed = {
            0: [
                MessageHandler(filters.TEXT, dummy_handler),
                CallbackQueryHandler(dummy_handler, pattern='^test$')
            ]
        }
        assert ConversationHandlerFactory._has_callback_handlers(states_mixed)
    
    def test_check_entry_points_detection(self):
        """Test callback handler detection in entry points."""
        # With callback
        entry_with_callback = [
            CallbackQueryHandler(dummy_handler, pattern='^start$')
        ]
        assert ConversationHandlerFactory._check_entry_points(entry_with_callback)
        
        # Without callback
        entry_without_callback = [
            CommandHandler('start', dummy_handler)
        ]
        assert not ConversationHandlerFactory._check_entry_points(entry_without_callback)
        
        # Mixed
        entry_mixed = [
            CommandHandler('start', dummy_handler),
            CallbackQueryHandler(dummy_handler, pattern='^start$')
        ]
        assert ConversationHandlerFactory._check_entry_points(entry_mixed)
    
    def test_multiple_states_with_callbacks(self):
        """Test handler with callbacks in multiple states."""
        handler = ConversationHandlerFactory.create_handler(
            name='test_multi_state',
            entry_points=[CommandHandler('start', dummy_handler)],
            states={
                0: [CallbackQueryHandler(dummy_handler, pattern='^step1$')],
                1: [MessageHandler(filters.TEXT, dummy_handler)],
                2: [CallbackQueryHandler(dummy_handler, pattern='^step3$')]
            },
            fallbacks=[CommandHandler('cancel', dummy_handler)]
        )
        
        assert handler.per_message is True
    
    def test_handler_name_preserved(self):
        """Test that handler name is preserved."""
        test_name = 'my_custom_handler'
        handler = ConversationHandlerFactory.create_handler(
            name=test_name,
            entry_points=[CommandHandler('start', dummy_handler)],
            states={
                0: [MessageHandler(filters.TEXT, dummy_handler)]
            },
            fallbacks=[CommandHandler('cancel', dummy_handler)]
        )
        
        assert handler.name == test_name


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
