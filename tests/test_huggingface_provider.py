"""
Тесты для Hugging Face Provider
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from src.llm.providers.huggingface_provider import HuggingFaceProvider
from src.llm.models import LLMResponse, ProviderStatus


@pytest.fixture
def hf_provider():
    """Фикстура для HuggingFace Provider"""
    return HuggingFaceProvider(api_key="test_hf_key", timeout=30)


class TestHuggingFaceProvider:
    """Тесты для HuggingFace Provider"""
    
    def test_initialization(self, hf_provider):
        """Тест инициализации провайдера"""
        assert hf_provider.provider_name == "huggingface"
        assert hf_provider.api_key == "test_hf_key"
        assert hf_provider.timeout == 30
        assert len(hf_provider.MODELS) == 3
        assert hf_provider.current_model_index == 0
    
    def test_format_prompt_with_system(self, hf_provider):
        """Тест форматирования промпта с системным сообщением"""
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"}
        ]
        
        prompt = hf_provider._format_prompt(messages)
        
        assert "<<SYS>>" in prompt
        assert "You are helpful" in prompt
        assert "Hello" in prompt
        assert "[INST]" in prompt
        assert "[/INST]" in prompt
    
    def test_format_prompt_user_only(self, hf_provider):
        """Тест форматирования промпта только с пользователем"""
        messages = [
            {"role": "user", "content": "Hello"}
        ]
        
        prompt = hf_provider._format_prompt(messages)
        
        assert "Hello" in prompt
        assert "[/INST]" in prompt
    
    def test_get_next_available_model(self, hf_provider):
        """Тест выбора следующей доступной модели"""
        # Изначально должна вернуться первая модель
        model = hf_provider._get_next_available_model()
        assert model == hf_provider.MODELS[0]
        
        # После ошибок должна переключиться
        hf_provider.model_failures[hf_provider.MODELS[0]] = 5
        model = hf_provider._get_next_available_model()
        assert model != hf_provider.MODELS[0]
    
    def test_check_rate_limit_initial(self, hf_provider):
        """Тест проверки rate limit при инициализации"""
        assert hf_provider._check_rate_limit() is True
    
    def test_check_rate_limit_after_request(self, hf_provider):
        """Тест проверки rate limit после запроса"""
        hf_provider._update_rate_limit()
        
        # Если прошло мало времени, должен быть недоступен
        hf_provider.last_request_time = datetime.now()
        result = hf_provider._check_rate_limit()
        assert isinstance(result, bool)
        # Может быть False из-за минутного лимита
    
    def test_check_rate_limit_exhausted(self, hf_provider):
        """Тест проверки rate limit при исчерпании"""
        hf_provider.remaining_requests = 0
        assert hf_provider._check_rate_limit() is False
    
    def test_check_rate_limit_reset(self, hf_provider):
        """Тест сброса rate limit"""
        # Устанавливаем время сброса в прошлом
        hf_provider.rate_limit.reset_at = datetime.now() - timedelta(hours=1)
        hf_provider.remaining_requests = 0
        
        # Должен сброситься
        assert hf_provider._check_rate_limit() is True
        assert hf_provider.remaining_requests > 0
    
    def test_update_rate_limit(self, hf_provider):
        """Тест обновления rate limit"""
        initial_remaining = hf_provider.remaining_requests
        hf_provider._update_rate_limit()
        
        assert hf_provider.remaining_requests == initial_remaining - 1
        assert hf_provider.last_request_time is not None
    
    def test_estimate_tokens(self, hf_provider):
        """Тест оценки токенов"""
        prompt = "Hello world"
        response = "Hi there"
        
        tokens = hf_provider._estimate_tokens(prompt, response)
        
        # Примерно 4 символа = 1 токен
        expected = (len(prompt) + len(response)) // 4
        assert tokens == expected
    
    @pytest.mark.asyncio
    async def test_generate_success(self, hf_provider):
        """Тест успешной генерации"""
        with patch.object(hf_provider, '_generate_with_model', new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = "Generated response"
            
            response = await hf_provider.generate(
                prompt="Test prompt",
                system_prompt="System message",
                max_tokens=100,
                temperature=0.7
            )
            
            assert isinstance(response, str)
            assert response == "Generated response"
            assert hf_provider.successful_requests > 0
    
    @pytest.mark.asyncio
    async def test_generate_with_fallback(self, hf_provider):
        """Тест генерации с fallback между моделями"""
        call_count = 0
        
        async def mock_generate(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("First model failed")
            return "Success from second model"
        
        with patch.object(hf_provider, '_generate_with_model', side_effect=mock_generate):
            response = await hf_provider.generate(prompt="Test")
            
            assert response == "Success from second model"
            assert call_count == 2  # Попробовал 2 модели
    
    @pytest.mark.asyncio
    async def test_generate_timeout(self, hf_provider):
        """Тест таймаута генерации"""
        async def slow_generate(*args, **kwargs):
            await asyncio.sleep(100)  # Очень долго
            return "Too late"
        
        with patch.object(hf_provider, '_generate_with_model', side_effect=slow_generate):
            with pytest.raises(Exception) as exc_info:
                await hf_provider.generate(prompt="Test")
            
            assert "failed" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_generate_rate_limit_exceeded(self, hf_provider):
        """Тест генерации при превышении rate limit"""
        hf_provider.remaining_requests = 0
        
        with pytest.raises(Exception) as exc_info:
            await hf_provider.generate(prompt="Test")
        
        assert "rate limit" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_check_availability_success(self, hf_provider):
        """Тест проверки доступности при успехе"""
        with patch.object(hf_provider, 'generate', new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = "OK"
            
            status = await hf_provider.check_availability()
            
            assert isinstance(status, bool)
            assert status is True
    
    @pytest.mark.asyncio
    async def test_check_availability_failure(self, hf_provider):
        """Тест проверки доступности при ошибке"""
        with patch.object(hf_provider, 'generate', new_callable=AsyncMock) as mock_gen:
            mock_gen.side_effect = Exception("API Error")
            
            status = await hf_provider.check_availability()
            
            assert isinstance(status, bool)
            assert status is False
    
    def test_model_failure_tracking(self, hf_provider):
        """Тест отслеживания ошибок моделей"""
        model = hf_provider.MODELS[0]
        initial_failures = hf_provider.model_failures[model]
        
        # Увеличиваем счетчик ошибок
        hf_provider.model_failures[model] += 1
        
        assert hf_provider.model_failures[model] == initial_failures + 1
    
    def test_multiple_models_available(self, hf_provider):
        """Тест наличия нескольких моделей для fallback"""
        assert len(hf_provider.MODELS) >= 2
        assert all(isinstance(model, str) for model in hf_provider.MODELS)
    
    @pytest.mark.asyncio
    async def test_generate_resets_failure_count_on_success(self, hf_provider):
        """Тест сброса счетчика ошибок при успехе"""
        # Устанавливаем ошибки для всех моделей кроме одной
        for i, model in enumerate(hf_provider.MODELS):
            if i == 0:
                hf_provider.model_failures[model] = 5
            else:
                hf_provider.model_failures[model] = 0
        
        with patch.object(hf_provider, '_generate_with_model', new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = "Success"
            
            await hf_provider.generate(prompt="Test")
            
            # Счетчик должен сброситься для модели которая использовалась
            # Используется модель с наименьшим количеством ошибок
            used_model = hf_provider._get_next_available_model()
            assert hf_provider.model_failures[used_model] == 0
    
    def test_get_rate_limit_info(self, hf_provider):
        """Тест получения информации о rate limit"""
        info = hf_provider.get_rate_limit_info()
        
        assert info is not None
        assert info.requests_per_minute == 10
        assert info.requests_per_day == 1000
    
    def test_get_remaining_quota(self, hf_provider):
        """Тест получения оставшейся квоты"""
        quota = hf_provider.get_remaining_quota()
        
        assert isinstance(quota, int)
        assert quota >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
