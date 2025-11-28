"""
Изолированные тесты интеграции AIErrorAnalyzer с LLM системой
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
from typing import Dict, List, Any


def test_ai_error_analyzer_integration():
    """Основной тест интеграции AIErrorAnalyzer с LLM системой"""
    
    # Создаем mock для всех зависимостей
    with patch('src.ai.error_analyzer.LLMManager') as mock_llm_manager, \
         patch('src.ai.error_analyzer.RealtimeErrorDetector') as mock_error_detector, \
         patch('src.ai.error_analyzer.EnhancedErrorHandler') as mock_error_handler:
        
        # Настраиваем mock объекты
        mock_llm = Mock()
        mock_llm.get_primary_model = Mock()
        mock_llm_model = Mock()
        mock_llm_model.generate_text = AsyncMock(return_value='{"causes": ["Test cause"], "fix_description": "Fix the issue", "fix_steps": ["Step 1", "Step 2"], "potential_causes": ["Cause 1"], "prevention_tips": ["Tip 1"]}')
        mock_llm.get_primary_model.return_value = mock_llm_model
        
        mock_llm_manager_instance = Mock()
        mock_llm_manager.return_value = mock_llm_manager_instance
        mock_llm_manager_instance.get_primary_model.return_value = mock_llm_model
        
        mock_error_detector_instance = Mock()
        mock_error_detector.return_value = mock_error_detector_instance
        
        mock_error_handler_instance = Mock()
        mock_error_handler.return_value = mock_error_handler_instance
        
        # Импортируем AIErrorAnalyzer после настройки mock
        from src.ai.error_analyzer import AIErrorAnalyzer
        
        # Создаем экземпляр анализатора
        analyzer = AIErrorAnalyzer(mock_llm_manager_instance, mock_error_detector_instance)
        
        # Тестируем основные методы
        test_errors = [
            {
                'message': 'KeyError: "key_name"',
                'location': 'telegram/src/services/example_service.py:25',
                'timestamp': '2023-10-01T10:00:00Z',
                'traceback': 'Traceback (most recent call last):\n  File "telegram/src/services/example_service.py", line 25, in example_function\n    value = some_dict["key_name"]\nKeyError: "key_name"'
            }
        ]
        
        # Тестируем анализ ошибок
        analyzed_errors = analyzer.analyze_errors(test_errors)
        assert len(analyzed_errors) == 1
        assert 'original_error' in analyzed_errors[0]
        assert 'type' in analyzed_errors[0]
        
        # Тестируем генерацию рекомендаций
        with patch.object(analyzer, '_generate_structured_recommendations_with_llm', 
                         return_value={
                             'fix_description': 'Fix the issue',
                             'fix_steps': ['Step 1', 'Step 2'],
                             'potential_causes': ['Cause 1'],
                             'prevention_tips': ['Tip 1']
                         }):
            updated_errors = analyzer.generate_fix_recommendations(analyzed_errors)
            assert len(updated_errors) == 1
            assert 'suggested_fix' in updated_errors[0]
        
        # Тестируем классификацию сложности
        classified_errors = analyzer.classify_fix_complexity(updated_errors)
        assert len(classified_errors) == 1
        assert 'complexity' in classified_errors[0]
        
        # Тестируем генерацию патчей
        patched_errors = analyzer.generate_safe_patches(classified_errors)
        assert len(patched_errors) == 1
        assert 'patch' in patched_errors[0]
        
        print("Все тесты интеграции прошли успешно!")
        return True


def test_ai_error_analyzer_methods():
    """Тесты отдельных методов AIErrorAnalyzer"""
    
    # Создаем mock для зависимостей
    with patch('src.ai.error_analyzer.LLMManager') as mock_llm_manager, \
         patch('src.ai.error_analyzer.RealtimeErrorDetector') as mock_error_detector:
        
        # Настраиваем mock
        mock_llm = Mock()
        mock_llm.get_primary_model = Mock()
        mock_llm_model = Mock()
        mock_llm_model.generate_text = AsyncMock(return_value='{"causes": ["Test cause"]}')
        mock_llm.get_primary_model.return_value = mock_llm_model
        
        mock_llm_manager_instance = Mock()
        mock_llm_manager.return_value = mock_llm_manager_instance
        mock_llm_manager_instance.get_primary_model.return_value = mock_llm_model
        
        mock_error_detector_instance = Mock()
        mock_error_detector.return_value = mock_error_detector_instance
        
        from src.ai.error_analyzer import AIErrorAnalyzer
        
        analyzer = AIErrorAnalyzer(mock_llm_manager_instance, mock_error_detector_instance)
        
        # Тестируем _get_error_context
        error = {
            'location': 'test_module.py:10',
            'function': 'test_function',
            'module': 'test_module',
            'timestamp': '2023-10-01T10:00:00Z',
            'user_context': 'test_user_context'
        }
        context = analyzer._get_error_context(error)
        assert 'Местоположение: test_module.py:10' in context
        assert 'Функция: test_function' in context
        
        # Тестируем _ai_classify_error_type
        error_with_keyerror = {
            'message': 'KeyError: "test_key"',
            'traceback': 'KeyError in some_file.py'
        }
        error_type = analyzer._ai_classify_error_type(error_with_keyerror)
        assert error_type == 'key_error'
        
        # Тестируем _ai_assess_severity
        severity = analyzer._ai_assess_severity(error_with_keyerror)
        assert severity in ['low', 'medium', 'high', 'critical']
        
        # Тестируем _ai_identify_causes
        causes = analyzer._ai_identify_causes(error_with_keyerror)
        assert isinstance(causes, list)
        
        print("Тесты отдельных методов прошли успешно!")
        return True


if __name__ == "__main__":
    try:
        test_ai_error_analyzer_integration()
        test_ai_error_analyzer_methods()
        print("Все тесты интеграции AIErrorAnalyzer с LLM системой успешно пройдены!")
    except Exception as e:
        print(f"Ошибка при выполнении тестов: {e}")
        import traceback
        traceback.print_exc()