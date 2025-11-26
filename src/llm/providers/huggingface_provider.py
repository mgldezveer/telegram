"""
Hugging Face Provider для LLM интеграции.
Использует Hugging Face Inference API с бесплатными моделями.
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from huggingface_hub import InferenceClient
from huggingface_hub.utils import HfHubHTTPError

from ..base_provider import BaseLLMProvider
from ..models import LLMResponse, ProviderStatus, RateLimitInfo

logger = logging.getLogger(__name__)


class HuggingFaceProvider(BaseLLMProvider):
    """
    Hugging Face Provider с поддержкой бесплатных моделей.
    
    Особенности:
    - Использует бесплатный Inference API
    - Поддержка нескольких моделей с fallback
    - Обработка медленных ответов
    - Автоматическое переключение моделей при недоступности
    """
    
    # Список моделей в порядке приоритета
    MODELS = [
        "mistralai/Mixtral-8x7B-Instruct-v0.1",  # Основная модель
        "mistralai/Mistral-7B-Instruct-v0.2",    # Fallback 1
        "meta-llama/Llama-2-7b-chat-hf",         # Fallback 2
    ]
    
    def __init__(self, api_key: str, model: str = None, timeout: int = 60):
        """
        Инициализация Hugging Face Provider.
        
        Args:
            api_key: Hugging Face API токен
            model: Название модели (опционально, используется первая из списка)
            timeout: Таймаут запроса в секундах (по умолчанию 60)
        """
        # Используем первую модель из списка если не указана
        if model is None:
            model = self.MODELS[0]
        
        super().__init__(api_key, model)
        self.timeout = timeout
        self.client = InferenceClient(token=api_key)
        self.current_model_index = 0
        self.model_failures: Dict[str, int] = {model: 0 for model in self.MODELS}
        self.last_request_time: Optional[datetime] = None
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        
        # Rate limiting для бесплатного tier
        self.rate_limit = RateLimitInfo(
            requests_per_minute=10,
            requests_per_day=1000,
            current_usage=0,
            reset_at=datetime.now() + timedelta(days=1)
        )
        self.remaining_requests = 1000
        
        logger.info(f"HuggingFace Provider initialized with {len(self.MODELS)} models")
    
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Генерация текста с использованием Hugging Face моделей.
        
        Args:
            prompt: Пользовательский промпт
            max_tokens: Максимальное количество токенов
            temperature: Температура генерации (0.0-1.0)
            system_prompt: Системный промпт (опционально)
            **kwargs: Дополнительные параметры
            
        Returns:
            Сгенерированный текст
            
        Raises:
            Exception: При ошибке генерации после всех попыток
        """
        start_time = datetime.now()
        self.total_requests += 1
        
        # Проверка rate limit
        if not self._check_rate_limit():
            self.failed_requests += 1
            raise Exception("Rate limit exceeded for Hugging Face API")
        
        # Формирование сообщений
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Попытка генерации с fallback между моделями
        last_error = None
        for attempt in range(len(self.MODELS)):
            model = self._get_next_available_model()
            
            try:
                logger.info(f"Attempting generation with model: {model}")
                
                # Генерация с таймаутом
                response = await asyncio.wait_for(
                    self._generate_with_model(model, messages, max_tokens, temperature),
                    timeout=self.timeout
                )
                
                # Успешная генерация - сброс счетчика ошибок
                self.model_failures[model] = 0
                self.successful_requests += 1
                
                # Обновление rate limit
                self._update_rate_limit()
                
                return response
                
            except asyncio.TimeoutError:
                logger.warning(f"Timeout for model {model}, trying next model")
                self.model_failures[model] += 1
                last_error = f"Timeout after {self.timeout}s"
                
            except HfHubHTTPError as e:
                logger.warning(f"HTTP error for model {model}: {e}")
                self.model_failures[model] += 1
                last_error = str(e)
                
                # Если модель недоступна (503), сразу переключаемся
                if "503" in str(e):
                    continue
                    
            except Exception as e:
                logger.error(f"Error with model {model}: {e}")
                self.model_failures[model] += 1
                last_error = str(e)
        
        # Все модели не сработали
        self.failed_requests += 1
        raise Exception(f"All Hugging Face models failed. Last error: {last_error}")
    
    async def _generate_with_model(
        self,
        model: str,
        messages: list,
        max_tokens: int,
        temperature: float
    ) -> str:
        """
        Генерация с конкретной моделью.
        
        Args:
            model: Название модели
            messages: Список сообщений
            max_tokens: Максимальное количество токенов
            temperature: Температура генерации
            
        Returns:
            Сгенерированный текст
        """
        # Формирование промпта для модели
        prompt = self._format_prompt(messages)
        
        # Вызов API в отдельном потоке (т.к. библиотека синхронная)
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self.client.text_generation(
                prompt,
                model=model,
                max_new_tokens=max_tokens,
                temperature=temperature,
                return_full_text=False
            )
        )
        
        return response.strip()
    
    def _format_prompt(self, messages: list) -> str:
        """
        Форматирование промпта для Hugging Face моделей.
        
        Args:
            messages: Список сообщений
            
        Returns:
            Отформатированный промпт
        """
        formatted = ""
        
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            
            if role == "system":
                formatted += f"<s>[INST] <<SYS>>\n{content}\n<</SYS>>\n\n"
            elif role == "user":
                if formatted and not formatted.endswith("[INST] "):
                    formatted += f"[INST] {content} [/INST]"
                else:
                    formatted += f"{content} [/INST]"
            elif role == "assistant":
                formatted += f"{content}</s><s>"
        
        return formatted
    
    def _get_next_available_model(self) -> str:
        """
        Получение следующей доступной модели.
        
        Returns:
            Название модели
        """
        # Сортировка моделей по количеству ошибок
        sorted_models = sorted(
            self.MODELS,
            key=lambda m: self.model_failures[m]
        )
        
        return sorted_models[0]
    
    def _check_rate_limit(self) -> bool:
        """
        Проверка rate limit.
        
        Returns:
            True если можно делать запрос
        """
        now = datetime.now()
        
        # Сброс счетчика если прошел день
        if now > self.rate_limit.reset_at:
            self.remaining_requests = self.rate_limit.requests_per_day
            self.rate_limit.reset_at = now + timedelta(days=1)
            self.rate_limit.current_usage = 0
        
        # Проверка минутного лимита
        if self.last_request_time:
            time_since_last = (now - self.last_request_time).total_seconds()
            if time_since_last < 6:  # 10 запросов в минуту = 1 запрос в 6 секунд
                return False
        
        return self.remaining_requests > 0
    
    def _update_rate_limit(self):
        """Обновление информации о rate limit."""
        self.remaining_requests -= 1
        self.rate_limit.current_usage += 1
        self.last_request_time = datetime.now()
    
    def _estimate_tokens(self, prompt: str, response: str) -> int:
        """
        Оценка количества использованных токенов.
        
        Args:
            prompt: Промпт
            response: Ответ
            
        Returns:
            Примерное количество токенов
        """
        # Грубая оценка: ~4 символа = 1 токен
        total_chars = len(prompt) + len(response)
        return total_chars // 4
    
    async def check_availability(self) -> bool:
        """
        Проверка доступности провайдера.
        
        Returns:
            True если провайдер доступен
        """
        try:
            # Пробуем простой запрос
            test_response = await self.generate(
                prompt="Say 'OK'",
                max_tokens=10,
                temperature=0.1
            )
            return True
            
        except Exception as e:
            logger.error(f"Hugging Face availability check failed: {e}")
            return False
    
    def get_rate_limit_info(self) -> RateLimitInfo:
        """
        Получение информации о rate limit.
        
        Returns:
            RateLimitInfo с текущими лимитами
        """
        return self.rate_limit
    
    def get_remaining_quota(self) -> int:
        """
        Получение оставшейся квоты запросов.
        
        Returns:
            Количество оставшихся запросов
        """
        return self.remaining_requests
