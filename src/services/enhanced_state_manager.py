"""Улучшенный менеджер состояний с поддержкой Redis и памяти."""

import logging
import json
import asyncio
from typing import Any, Dict, Optional
from datetime import datetime, timedelta
from src.cache import cache

logger = logging.getLogger(__name__)


class EnhancedStateManager:
    """Улучшенный менеджер состояний с поддержкой Redis и памяти.
    
    Использует мультиуровневый кэш для хранения сессий пользователей.
    """
    
    def __init__(self, session_timeout: int = 3600, cleanup_interval: int = 300):
        """Инициализация улучшенного менеджера состояний.
        
        Args:
            session_timeout: Время жизни сессии в секундах (по умолчанию 1 час)
            cleanup_interval: Интервал очистки в секундах (по умолчанию 5 минут)
        """
        self.session_timeout = session_timeout
        self.cleanup_interval = cleanup_interval
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False
        
        logger.info(f"Enhanced state manager initialized with {session_timeout}s timeout")
    
    def _get_session_key(self, user_id: int) -> str:
        """Получить ключ для сессии пользователя."""
        return f"session:{user_id}"
    
    def _get_history_key(self, user_id: int) -> str:
        """Получить ключ для истории навигации пользователя."""
        return f"history:{user_id}"
    
    async def get_state(self, user_id: int, key: str, default: Any = None) -> Any:
        """Получить значение состояния для пользователя.
        
        Args:
            user_id: ID пользователя
            key: Ключ состояния
            default: Значение по умолчанию, если ключ не найден
            
        Returns:
            Значение состояния или значение по умолчанию
        """
        session_key = self._get_session_key(user_id)
        session_data = await cache.get(session_key)
        
        if session_data is None:
            # Если данных нет в кэше, возвращаем пустой словарь
            session_data = {}
        elif isinstance(session_data, str):
            # Если данные в виде строки, десериализуем
            try:
                session_data = json.loads(session_data)
            except json.JSONDecodeError:
                session_data = {}
        
        value = session_data.get(key, default)
        
        # Обновляем время жизни сессии
        await cache.set(session_key, session_data, self.session_timeout)
        
        logger.debug(f"Get state for user {user_id}, key {key}: {value}")
        return value
    
    async def set_state(self, user_id: int, key: str, value: Any) -> None:
        """Установить значение состояния для пользователя.
        
        Args:
            user_id: ID пользователя
            key: Ключ состояния
            value: Значение состояния
        """
        session_key = self._get_session_key(user_id)
        session_data = await cache.get(session_key)
        
        if session_data is None:
            session_data = {}
        elif isinstance(session_data, str):
            try:
                session_data = json.loads(session_data)
            except json.JSONDecodeError:
                session_data = {}
        
        session_data[key] = value
        
        await cache.set(session_key, session_data, self.session_timeout)
        logger.debug(f"Set state for user {user_id}, key {key}: {value}")
    
    async def delete_state(self, user_id: int, key: str) -> None:
        """Удалить значение состояния для пользователя.
        
        Args:
            user_id: ID пользователя
            key: Ключ состояния
        """
        session_key = self._get_session_key(user_id)
        session_data = await cache.get(session_key)
        
        if session_data is None:
            session_data = {}
        elif isinstance(session_data, str):
            try:
                session_data = json.loads(session_data)
            except json.JSONDecodeError:
                session_data = {}
        
        if key in session_data:
            del session_data[key]
            await cache.set(session_key, session_data, self.session_timeout)
            logger.debug(f"Deleted state for user {user_id}, key {key}")
    
    async def get_session(self, user_id: int) -> Dict[str, Any]:
        """Получить всю сессию для пользователя.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Словарь сессии
        """
        session_key = self._get_session_key(user_id)
        session_data = await cache.get(session_key)
        
        if session_data is None:
            session_data = {}
        elif isinstance(session_data, str):
            try:
                session_data = json.loads(session_data)
            except json.JSONDecodeError:
                session_data = {}
        
        # Обновляем время жизни сессии
        await cache.set(session_key, session_data, self.session_timeout)
        
        return session_data.copy()
    
    async def clear_session(self, user_id: int) -> None:
        """Очистить всю сессию для пользователя.
        
        Args:
            user_id: ID пользователя
        """
        session_key = self._get_session_key(user_id)
        await cache.delete(session_key)
        logger.info(f"Cleared session for user {user_id}")
    
    async def is_session_active(self, user_id: int) -> bool:
        """Проверить, активна ли сессия пользователя.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            True, если сессия активна
        """
        session_key = self._get_session_key(user_id)
        return await cache.exists(session_key)
    
    async def get_active_sessions_count(self) -> int:
        """Получить количество активных сессий.
        
        Returns:
            Количество активных сессий
        """
        # Находим все ключи сессий
        session_keys = await cache.keys("session:*")
        return len(session_keys)
    
    async def push_to_history(self, user_id: int, menu: str) -> None:
        """Добавить меню в историю навигации.
        
        Args:
            user_id: ID пользователя
            menu: Идентификатор меню
        """
        history_key = self._get_history_key(user_id)
        history_data = await cache.get(history_key)
        
        if history_data is None:
            history_data = []
        elif isinstance(history_data, str):
            try:
                history_data = json.loads(history_data)
            except json.JSONDecodeError:
                history_data = []
        
        # Не добавляем дубликаты подряд
        if not history_data or history_data[-1] != menu:
            history_data.append(menu)
            
            # Ограничиваем размер истории
            if len(history_data) > 10:  # по умолчанию максимум 10 элементов
                history_data = history_data[-10:]
        
        await cache.set(history_key, history_data, self.session_timeout)
        logger.debug(f"Pushed menu '{menu}' to history for user {user_id}")
    
    async def pop_from_history(self, user_id: int) -> Optional[str]:
        """Извлечь последнее меню из истории навигации.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Последнее меню или None
        """
        history_key = self._get_history_key(user_id)
        history_data = await cache.get(history_key)
        
        if history_data is None:
            history_data = []
        elif isinstance(history_data, str):
            try:
                history_data = json.loads(history_data)
            except json.JSONDecodeError:
                history_data = []
        
        if history_data:
            menu = history_data.pop()
            await cache.set(history_key, history_data, self.session_timeout)
            logger.debug(f"Popped menu '{menu}' from history for user {user_id}")
            return menu
        
        return None
    
    async def get_previous_menu(self, user_id: int) -> Optional[str]:
        """Получить предыдущее меню без удаления.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Предыдущее меню или None
        """
        history_key = self._get_history_key(user_id)
        history_data = await cache.get(history_key)
        
        if history_data is None:
            history_data = []
        elif isinstance(history_data, str):
            try:
                history_data = json.loads(history_data)
            except json.JSONDecodeError:
                history_data = []
        
        if len(history_data) >= 2:
            return history_data[-2]
        
        return None
    
    async def get_history(self, user_id: int) -> list:
        """Получить полную историю навигации для пользователя.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Список идентификаторов меню
        """
        history_key = self._get_history_key(user_id)
        history_data = await cache.get(history_key)
        
        if history_data is None:
            history_data = []
        elif isinstance(history_data, str):
            try:
                history_data = json.loads(history_data)
            except json.JSONDecodeError:
                history_data = []
        
        return history_data.copy()
    
    async def clear_history(self, user_id: int) -> None:
        """Очистить историю навигации для пользователя.
        
        Args:
            user_id: ID пользователя
        """
        history_key = self._get_history_key(user_id)
        await cache.delete(history_key)
        logger.debug(f"Cleared history for user {user_id}")
    
    async def cleanup_user_data(self, user_id: int) -> None:
        """Очистить все данные пользователя (сессия и история).
        
        Args:
            user_id: ID пользователя
        """
        await self.clear_session(user_id)
        await self.clear_history(user_id)
    
    async def cleanup_all(self) -> None:
        """Очистить все данные всех пользователей."""
        # Удаляем все ключи, связанные сессиями историей
        session_keys = await cache.keys("session:*")
        history_keys = await cache.keys("history:*")
        
        all_keys = session_keys + history_keys
        
        for key in all_keys:
            await cache.delete(key)
        
        logger.info(f"Cleaned up all {len(all_keys)} user data entries")
    
    async def get_cache_stats(self) -> dict:
        """Получить статистику кэша.
        
        Returns:
            Словарь со статистикой
        """
        if hasattr(cache, 'is_redis_available'):
            redis_available = cache.is_redis_available()
        else:
            redis_available = False
            
        session_keys = await cache.keys("session:*")
        history_keys = await cache.keys("history:*")
        
        stats = {
            'redis_available': redis_available,
            'total_sessions': len(session_keys),
            'total_histories': len(history_keys),
            'total_user_data': len(session_keys) + len(history_keys)
        }
        
        return stats