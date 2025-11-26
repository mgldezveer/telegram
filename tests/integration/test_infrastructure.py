"""Integration tests for infrastructure improvements."""

import pytest
import asyncio
from src.cache.cache_service import CacheService
from src.utils.version_checker import PythonVersionChecker
from src.services.health_check import HealthCheckService


class TestCacheIntegration:
    """Integration tests for cache system."""
    
    @pytest.mark.asyncio
    async def test_cache_fallback_workflow(self):
        """Test complete fallback workflow."""
        cache = CacheService(fallback_enabled=True)
        
        # Force fallback by using invalid Redis URL
        import src.config as config_module
        original_url = config_module.config.redis.url
        config_module.config.redis.url = "redis://invalid:9999/0"
        
        try:
            # Connect (should fallback)
            result = await cache.connect()
            assert result.success
            assert result.backend == 'memory'
            
            # Perform operations
            await cache.set("test_key", "test_value")
            value = await cache.get("test_key")
            assert value == "test_value"
            
            # Check health
            health = await cache.health_check()
            assert health['backend'] == 'memory'
            assert health['fallback_active']
            
        finally:
            config_module.config.redis.url = original_url
            await cache.close()
    
    @pytest.mark.asyncio
    async def test_cache_operations_consistency(self):
        """Test cache operations are consistent across backends."""
        cache = CacheService(fallback_enabled=True)
        
        # Force fallback
        import src.config as config_module
        original_url = config_module.config.redis.url
        config_module.config.redis.url = "redis://invalid:9999/0"
        
        try:
            await cache.connect()
            
            # Test various operations
            test_data = {
                "string": "value",
                "number": 42,
                "list": [1, 2, 3],
                "dict": {"a": 1, "b": 2}
            }
            
            for key, value in test_data.items():
                await cache.set(key, value)
                retrieved = await cache.get(key)
                assert retrieved == value, f"Mismatch for {key}"
            
            # Test exists
            for key in test_data.keys():
                assert await cache.exists(key)
            
            # Test delete
            await cache.delete("string")
            assert not await cache.exists("string")
            
        finally:
            config_module.config.redis.url = original_url
            await cache.close()


class TestHealthCheckIntegration:
    """Integration tests for health check service."""
    
    @pytest.mark.asyncio
    async def test_health_check_with_cache(self):
        """Test health check integration with cache service."""
        cache = CacheService(fallback_enabled=True)
        
        # Force fallback
        import src.config as config_module
        original_url = config_module.config.redis.url
        config_module.config.redis.url = "redis://invalid:9999/0"
        
        try:
            await cache.connect()
            
            # Create health check service
            health_service = HealthCheckService(cache_service=cache)
            
            # Get health status
            status = await health_service.get_health_status()
            
            assert status.status in ('healthy', 'degraded', 'unhealthy')
            assert 'cache' in status.components
            
            cache_status = status.components['cache']
            assert cache_status.name == 'cache'
            assert cache_status.status in ('healthy', 'degraded', 'unhealthy')
            
        finally:
            config_module.config.redis.url = original_url
            await cache.close()
    
    @pytest.mark.asyncio
    async def test_health_check_redis_status(self):
        """Test Redis-specific health status."""
        cache = CacheService(fallback_enabled=True)
        
        # Force fallback
        import src.config as config_module
        original_url = config_module.config.redis.url
        config_module.config.redis.url = "redis://invalid:9999/0"
        
        try:
            await cache.connect()
            
            health_service = HealthCheckService(cache_service=cache)
            redis_status = await health_service.get_redis_status()
            
            assert 'available' in redis_status
            assert 'backend' in redis_status
            assert redis_status['backend'] == 'memory'
            assert not redis_status['available']
            
        finally:
            config_module.config.redis.url = original_url
            await cache.close()


class TestVersionCheckIntegration:
    """Integration tests for version checking."""
    
    def test_version_check_in_startup_flow(self):
        """Test version check as part of startup."""
        # Check version
        result = PythonVersionChecker.check_version()
        
        # Should return valid result
        assert result.is_compatible is not None
        assert result.current_version is not None
        assert result.message is not None
        assert result.severity in ('ok', 'warning', 'error')
        
        # Get version info
        info = PythonVersionChecker.get_version_info()
        assert 'version' in info
        assert 'minimum_required' in info


class TestStartupSequence:
    """Integration tests for startup sequence."""
    
    @pytest.mark.asyncio
    async def test_minimal_startup_components(self):
        """Test minimal startup with all components."""
        # 1. Version check
        version_result = PythonVersionChecker.check_version()
        assert version_result is not None
        
        # 2. Cache initialization
        cache = CacheService(fallback_enabled=True)
        
        # Force fallback for testing
        import src.config as config_module
        original_url = config_module.config.redis.url
        config_module.config.redis.url = "redis://invalid:9999/0"
        
        try:
            connection_result = await cache.connect()
            assert connection_result.success
            
            # 3. Health check initialization
            health_service = HealthCheckService(cache_service=cache)
            health_status = await health_service.get_health_status()
            assert health_status is not None
            
            # 4. Verify all components work together
            await cache.set("startup_test", "success")
            value = await cache.get("startup_test")
            assert value == "success"
            
        finally:
            config_module.config.redis.url = original_url
            await cache.close()


class TestCacheReconnection:
    """Integration tests for cache reconnection logic."""
    
    @pytest.mark.asyncio
    async def test_reconnection_task_creation(self):
        """Test that reconnection task is created."""
        cache = CacheService(fallback_enabled=True, reconnect_interval=5)
        
        # Force fallback
        import src.config as config_module
        original_url = config_module.config.redis.url
        config_module.config.redis.url = "redis://invalid:9999/0"
        
        try:
            result = await cache.connect()
            assert result.backend == 'memory'
            
            # Start reconnection task
            await cache.start_reconnection_task()
            
            # Task should be created
            assert cache._reconnect_task is not None
            
            # Wait a bit to ensure task is running
            await asyncio.sleep(0.1)
            
            # Task should not be done (it runs in loop)
            assert not cache._reconnect_task.done()
            
        finally:
            config_module.config.redis.url = original_url
            await cache.close()


class TestConversationHandlerIntegration:
    """Integration tests for ConversationHandler factory."""
    
    def test_factory_creates_valid_handlers(self):
        """Test that factory creates valid ConversationHandlers."""
        from src.interface.conversation_factory import ConversationHandlerFactory
        from telegram.ext import CommandHandler, MessageHandler, CallbackQueryHandler, filters
        
        async def dummy_handler(update, context):
            pass
        
        # Create handler with callbacks
        handler = ConversationHandlerFactory.create_handler(
            name='test_integration',
            entry_points=[CallbackQueryHandler(dummy_handler, pattern='^start$')],
            states={
                0: [MessageHandler(filters.TEXT, dummy_handler)],
                1: [CallbackQueryHandler(dummy_handler, pattern='^next$')]
            },
            fallbacks=[CommandHandler('cancel', dummy_handler)],
            conversation_timeout=300.0
        )
        
        # Verify handler is properly configured
        assert handler.name == 'test_integration'
        assert handler.per_message is True  # Auto-detected
        assert handler.conversation_timeout == 300.0
        assert len(handler.entry_points) == 1
        assert len(handler.states) == 2
        assert len(handler.fallbacks) == 1


class TestEndToEndScenarios:
    """End-to-end integration tests."""
    
    @pytest.mark.asyncio
    async def test_complete_cache_lifecycle(self):
        """Test complete cache lifecycle from start to finish."""
        cache = CacheService(fallback_enabled=True)
        
        # Force fallback
        import src.config as config_module
        original_url = config_module.config.redis.url
        config_module.config.redis.url = "redis://invalid:9999/0"
        
        try:
            # 1. Connect
            result = await cache.connect()
            assert result.success
            
            # 2. Store data
            test_data = {
                "user:1": {"name": "Alice", "score": 100},
                "user:2": {"name": "Bob", "score": 200},
                "config": {"theme": "dark", "lang": "en"}
            }
            
            for key, value in test_data.items():
                await cache.set(key, value, ttl=60)
            
            # 3. Retrieve data
            for key, expected_value in test_data.items():
                value = await cache.get(key)
                assert value == expected_value
            
            # 4. Check health
            health = await cache.health_check()
            assert health['healthy']
            assert health['backend'] == 'memory'
            
            # 5. Get stats
            stats = cache.get_stats()
            assert stats is not None
            assert stats.backend == 'memory'
            assert stats.total_keys >= len(test_data)
            
            # 6. Cleanup
            for key in test_data.keys():
                await cache.delete(key)
            
        finally:
            config_module.config.redis.url = original_url
            await cache.close()
    
    @pytest.mark.asyncio
    async def test_health_monitoring_workflow(self):
        """Test complete health monitoring workflow."""
        cache = CacheService(fallback_enabled=True)
        
        # Force fallback
        import src.config as config_module
        original_url = config_module.config.redis.url
        config_module.config.redis.url = "redis://invalid:9999/0"
        
        try:
            # Setup
            await cache.connect()
            health_service = HealthCheckService(cache_service=cache)
            
            # Get overall health
            status = await health_service.get_health_status()
            assert status.status in ('healthy', 'degraded', 'unhealthy')
            
            # Get Redis-specific status
            redis_status = await health_service.get_redis_status()
            assert not redis_status['available']
            assert redis_status['fallback_active']
            
            # Get service info
            service_info = health_service.get_service_info()
            assert 'uptime_seconds' in service_info
            assert 'check_count' in service_info
            
            # Convert to dict for API response
            status_dict = status.to_dict()
            assert 'status' in status_dict
            assert 'timestamp' in status_dict
            assert 'components' in status_dict
            
        finally:
            config_module.config.redis.url = original_url
            await cache.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
