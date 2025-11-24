"""Tests for callback router."""

import pytest
from src.interface.callback_router import CallbackRouter


class TestCallbackRouter:
    """Test callback router functionality."""
    
    def test_parse_callback_data_menu(self):
        """Test parsing menu callback data."""
        router = CallbackRouter()
        
        # Test menu navigation
        parsed = router.parse_callback_data("menu:channels")
        assert parsed is not None
        assert parsed['action'] == 'menu'
        assert parsed['menu'] == 'channels'
    
    def test_parse_callback_data_channel(self):
        """Test parsing channel callback data."""
        router = CallbackRouter()
        
        # Test channel dashboard
        parsed = router.parse_callback_data("channel:123:dashboard")
        assert parsed is not None
        assert parsed['action'] == 'channel'
        assert parsed['channel_id'] == 123
        assert parsed['subaction'] == 'dashboard'
    
    def test_parse_callback_data_noop(self):
        """Test parsing noop callback data."""
        router = CallbackRouter()
        
        parsed = router.parse_callback_data("noop")
        assert parsed is not None
        assert parsed['action'] == 'noop'
    
    def test_parse_callback_data_invalid(self):
        """Test parsing invalid callback data."""
        router = CallbackRouter()
        
        # Empty data
        parsed = router.parse_callback_data("")
        assert parsed is None
        
        # None data
        parsed = router.parse_callback_data(None)
        assert parsed is None
    
    def test_create_callback_data(self):
        """Test creating callback data."""
        router = CallbackRouter()
        
        # Simple action
        data = router.create_callback_data("menu", menu="main")
        assert data == "menu:main"
        
        # Channel action
        data = router.create_callback_data("channel", channel_id=123, subaction="dashboard")
        assert data == "channel:123:dashboard"
    
    def test_create_callback_data_length_limit(self):
        """Test callback data length validation."""
        router = CallbackRouter()
        
        # Should raise error if too long
        with pytest.raises(ValueError):
            router.create_callback_data(
                "action",
                param1="a" * 30,
                param2="b" * 30
            )
    
    def test_validate_callback_data(self):
        """Test callback data validation."""
        router = CallbackRouter()
        
        # Valid data
        assert router.validate_callback_data("menu:main") is True
        assert router.validate_callback_data("noop") is True
        
        # Invalid data
        assert router.validate_callback_data("") is False
        assert router.validate_callback_data("a" * 100) is False
    
    def test_register_handler(self):
        """Test handler registration."""
        router = CallbackRouter()
        
        async def test_handler(update, context):
            pass
        
        # Should register successfully
        router.register("test", test_handler)
        assert "test" in router.handlers
        
        # Should raise error for empty pattern
        with pytest.raises(ValueError):
            router.register("", test_handler)
        
        # Should raise error for non-callable handler
        with pytest.raises(ValueError):
            router.register("test2", "not_callable")
    
    def test_metrics(self):
        """Test metrics tracking."""
        router = CallbackRouter()
        
        metrics = router.get_metrics()
        assert 'total_callbacks' in metrics
        assert 'successful_callbacks' in metrics
        assert 'failed_callbacks' in metrics
        assert 'success_rate' in metrics
        assert 'registered_handlers' in metrics
        assert metrics['registered_handlers'] == 0
