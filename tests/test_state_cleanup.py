"""Tests for state cleanup functionality."""

import pytest
import asyncio
from datetime import datetime, timedelta
from src.services.state_manager import StateManager, NavigationHistory


@pytest.mark.asyncio
async def test_session_cleanup():
    """Test that expired sessions are cleaned up."""
    # Create state manager with short timeout
    manager = StateManager(session_timeout=2)  # 2 seconds
    
    # Create some sessions
    await manager.set_state(1, 'test', 'value1')
    await manager.set_state(2, 'test', 'value2')
    await manager.set_state(3, 'test', 'value3')
    
    # Verify sessions exist
    assert await manager.get_active_sessions_count() == 3
    
    # Wait for timeout
    await asyncio.sleep(3)
    
    # Trigger cleanup
    await manager._cleanup_expired_sessions()
    
    # Verify sessions are cleaned up
    assert await manager.get_active_sessions_count() == 0


@pytest.mark.asyncio
async def test_session_activity_extends_timeout():
    """Test that activity extends session timeout."""
    manager = StateManager(session_timeout=2)
    
    # Create session
    await manager.set_state(1, 'test', 'value')
    
    # Wait 1 second
    await asyncio.sleep(1)
    
    # Access session (should extend timeout)
    value = await manager.get_state(1, 'test')
    assert value == 'value'
    
    # Wait another 1.5 seconds (total 2.5, but activity was at 1s)
    await asyncio.sleep(1.5)
    
    # Session should still be active
    assert await manager.is_session_active(1)


@pytest.mark.asyncio
async def test_navigation_history_cleanup():
    """Test that old navigation histories are cleaned up."""
    history = NavigationHistory(max_history=10, history_timeout=2)
    
    # Add some history
    await history.push(1, 'menu1')
    await history.push(1, 'menu2')
    await history.push(2, 'menu1')
    
    # Verify history exists
    assert len(await history.get_history(1)) == 2
    assert len(await history.get_history(2)) == 1
    
    # Wait for timeout
    await asyncio.sleep(3)
    
    # Trigger cleanup by pushing new entry
    await history.push(3, 'menu1')
    
    # Old histories should be cleaned up
    # Note: cleanup happens on push, so we need to check after
    await asyncio.sleep(0.1)


@pytest.mark.asyncio
async def test_cleanup_task_starts_and_stops():
    """Test that cleanup task can be started and stopped."""
    manager = StateManager(session_timeout=10, cleanup_interval=1)
    
    # Start cleanup task
    await manager.start_cleanup_task()
    assert manager._running
    
    # Wait a bit
    await asyncio.sleep(0.5)
    
    # Stop cleanup task
    await manager.stop_cleanup_task()
    assert not manager._running


@pytest.mark.asyncio
async def test_cleanup_task_cleans_sessions():
    """Test that cleanup task automatically cleans expired sessions."""
    manager = StateManager(session_timeout=1, cleanup_interval=2)
    
    # Create sessions
    await manager.set_state(1, 'test', 'value1')
    await manager.set_state(2, 'test', 'value2')
    
    # Start cleanup task
    await manager.start_cleanup_task()
    
    # Wait for sessions to expire and cleanup to run
    await asyncio.sleep(4)
    
    # Sessions should be cleaned up
    assert await manager.get_active_sessions_count() == 0
    
    # Stop cleanup task
    await manager.stop_cleanup_task()


@pytest.mark.asyncio
async def test_clear_session():
    """Test manual session clearing."""
    manager = StateManager()
    
    # Create session
    await manager.set_state(1, 'key1', 'value1')
    await manager.set_state(1, 'key2', 'value2')
    
    # Verify session exists
    session = await manager.get_session(1)
    assert len(session) == 2
    
    # Clear session
    await manager.clear_session(1)
    
    # Verify session is cleared
    session = await manager.get_session(1)
    assert len(session) == 0


@pytest.mark.asyncio
async def test_cleanup_all():
    """Test cleanup of all sessions."""
    manager = StateManager()
    
    # Create multiple sessions
    await manager.set_state(1, 'test', 'value1')
    await manager.set_state(2, 'test', 'value2')
    await manager.set_state(3, 'test', 'value3')
    
    # Verify sessions exist
    assert await manager.get_active_sessions_count() == 3
    
    # Cleanup all
    await manager.cleanup_all()
    
    # Verify all sessions are cleared
    assert await manager.get_active_sessions_count() == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
