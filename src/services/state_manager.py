"""State management service for user sessions."""

import logging
import json
import asyncio
from typing import Any, Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class StateManager:
    """Manages user state and session data.
    
    Provides in-memory storage with optional Redis backend for production.
    """
    
    def __init__(self, session_timeout: int = 3600, cleanup_interval: int = 300):
        """Initialize state manager.
        
        Args:
            session_timeout: Session timeout in seconds (default 1 hour)
            cleanup_interval: Cleanup interval in seconds (default 5 minutes)
        """
        self.session_timeout = session_timeout
        self.cleanup_interval = cleanup_interval
        self._sessions: Dict[int, Dict[str, Any]] = {}
        self._last_activity: Dict[int, datetime] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False
        
        logger.info(f"State manager initialized with {session_timeout}s timeout, {cleanup_interval}s cleanup interval")
    
    async def get_state(self, user_id: int, key: str, default: Any = None) -> Any:
        """Get state value for user.
        
        Args:
            user_id: User ID
            key: State key
            default: Default value if not found
            
        Returns:
            State value or default
        """
        # Clean up expired sessions first
        await self._cleanup_expired_sessions()
        
        session = self._sessions.get(user_id, {})
        value = session.get(key, default)
        
        # Update last activity
        self._last_activity[user_id] = datetime.now()
        
        logger.debug(f"Get state for user {user_id}, key {key}: {value}")
        return value
    
    async def set_state(self, user_id: int, key: str, value: Any) -> None:
        """Set state value for user.
        
        Args:
            user_id: User ID
            key: State key
            value: State value
        """
        if user_id not in self._sessions:
            self._sessions[user_id] = {}
        
        self._sessions[user_id][key] = value
        self._last_activity[user_id] = datetime.now()
        
        logger.debug(f"Set state for user {user_id}, key {key}: {value}")
    
    async def delete_state(self, user_id: int, key: str) -> None:
        """Delete state value for user.
        
        Args:
            user_id: User ID
            key: State key
        """
        if user_id in self._sessions and key in self._sessions[user_id]:
            del self._sessions[user_id][key]
            logger.debug(f"Deleted state for user {user_id}, key {key}")
    
    async def get_session(self, user_id: int) -> Dict[str, Any]:
        """Get entire session for user.
        
        Args:
            user_id: User ID
            
        Returns:
            Session dictionary
        """
        await self._cleanup_expired_sessions()
        
        session = self._sessions.get(user_id, {})
        self._last_activity[user_id] = datetime.now()
        
        return session.copy()
    
    async def clear_session(self, user_id: int) -> None:
        """Clear entire session for user.
        
        Args:
            user_id: User ID
        """
        if user_id in self._sessions:
            del self._sessions[user_id]
        
        if user_id in self._last_activity:
            del self._last_activity[user_id]
        
        logger.info(f"Cleared session for user {user_id}")
    
    async def is_session_active(self, user_id: int) -> bool:
        """Check if user has active session.
        
        Args:
            user_id: User ID
            
        Returns:
            True if session is active
        """
        if user_id not in self._last_activity:
            return False
        
        last_activity = self._last_activity[user_id]
        timeout = timedelta(seconds=self.session_timeout)
        
        return datetime.now() - last_activity < timeout
    
    async def get_active_sessions_count(self) -> int:
        """Get count of active sessions.
        
        Returns:
            Number of active sessions
        """
        await self._cleanup_expired_sessions()
        return len(self._sessions)
    
    async def _cleanup_expired_sessions(self) -> None:
        """Clean up expired sessions."""
        now = datetime.now()
        timeout = timedelta(seconds=self.session_timeout)
        
        expired_users = [
            user_id for user_id, last_activity in self._last_activity.items()
            if now - last_activity > timeout
        ]
        
        for user_id in expired_users:
            if user_id in self._sessions:
                del self._sessions[user_id]
            del self._last_activity[user_id]
            logger.info(f"Cleaned up expired session for user {user_id}")
    
    async def cleanup_all(self) -> None:
        """Clean up all sessions."""
        count = len(self._sessions)
        self._sessions.clear()
        self._last_activity.clear()
        logger.info(f"Cleaned up all {count} sessions")
    
    async def start_cleanup_task(self) -> None:
        """Start automatic cleanup task."""
        if self._running:
            logger.warning("Cleanup task already running")
            return
        
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("Started automatic cleanup task")
    
    async def stop_cleanup_task(self) -> None:
        """Stop automatic cleanup task."""
        if not self._running:
            return
        
        self._running = False
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Stopped automatic cleanup task")
    
    async def _cleanup_loop(self) -> None:
        """Periodic cleanup loop."""
        logger.info(f"Cleanup loop started, running every {self.cleanup_interval}s")
        
        while self._running:
            try:
                await asyncio.sleep(self.cleanup_interval)
                
                if not self._running:
                    break
                
                # Clean up expired sessions
                await self._cleanup_expired_sessions()
                
                # Log statistics
                active_count = len(self._sessions)
                logger.info(f"Cleanup completed. Active sessions: {active_count}")
                
            except asyncio.CancelledError:
                logger.info("Cleanup loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}", exc_info=True)
                # Continue running despite errors
                await asyncio.sleep(60)  # Wait a bit before retrying


class NavigationHistory:
    """Manages navigation history for users."""
    
    def __init__(self, max_history: int = 10, history_timeout: int = 3600):
        """Initialize navigation history.
        
        Args:
            max_history: Maximum history entries per user
            history_timeout: History timeout in seconds (default 1 hour)
        """
        self.max_history = max_history
        self.history_timeout = history_timeout
        self._history: Dict[int, list] = {}
        self._last_access: Dict[int, datetime] = {}
        
        logger.info(f"Navigation history initialized with max {max_history} entries, {history_timeout}s timeout")
    
    async def push(self, user_id: int, menu: str) -> None:
        """Push menu to history.
        
        Args:
            user_id: User ID
            menu: Menu identifier
        """
        # Clean up old histories first
        await self._cleanup_old_histories()
        
        if user_id not in self._history:
            self._history[user_id] = []
        
        history = self._history[user_id]
        
        # Don't add duplicate consecutive entries
        if history and history[-1] == menu:
            return
        
        history.append(menu)
        
        # Limit history size
        if len(history) > self.max_history:
            history.pop(0)
        
        # Update last access time
        self._last_access[user_id] = datetime.now()
        
        logger.debug(f"Pushed menu '{menu}' to history for user {user_id}")
    
    async def pop(self, user_id: int) -> Optional[str]:
        """Pop last menu from history.
        
        Args:
            user_id: User ID
            
        Returns:
            Last menu or None
        """
        if user_id not in self._history or not self._history[user_id]:
            return None
        
        menu = self._history[user_id].pop()
        logger.debug(f"Popped menu '{menu}' from history for user {user_id}")
        
        return menu
    
    async def get_previous(self, user_id: int) -> Optional[str]:
        """Get previous menu without removing it.
        
        Args:
            user_id: User ID
            
        Returns:
            Previous menu or None
        """
        if user_id not in self._history or len(self._history[user_id]) < 2:
            return None
        
        return self._history[user_id][-2]
    
    async def clear(self, user_id: int) -> None:
        """Clear history for user.
        
        Args:
            user_id: User ID
        """
        if user_id in self._history:
            del self._history[user_id]
            logger.debug(f"Cleared history for user {user_id}")
    
    async def get_history(self, user_id: int) -> list:
        """Get full history for user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of menu identifiers
        """
        # Update last access time
        if user_id in self._history:
            self._last_access[user_id] = datetime.now()
        
        return self._history.get(user_id, []).copy()
    
    async def _cleanup_old_histories(self) -> None:
        """Clean up old navigation histories."""
        now = datetime.now()
        timeout = timedelta(seconds=self.history_timeout)
        
        old_users = [
            user_id for user_id, last_access in self._last_access.items()
            if now - last_access > timeout
        ]
        
        for user_id in old_users:
            if user_id in self._history:
                del self._history[user_id]
            del self._last_access[user_id]
            logger.debug(f"Cleaned up old navigation history for user {user_id}")
    
    async def cleanup_all(self) -> None:
        """Clean up all navigation histories."""
        count = len(self._history)
        self._history.clear()
        self._last_access.clear()
        logger.info(f"Cleaned up all {count} navigation histories")
