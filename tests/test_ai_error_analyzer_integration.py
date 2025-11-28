"""
Тесты интеграции AIErrorAnalyzer с LLM системой
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from typing import Dict, List, Any

from src.ai.error_analyzer import AIErrorAnalyzer
from src.llm.llm_manager import LLMManager, create_llm_manager_from_env
from src.monitoring.realtime_error_detector import RealtimeErrorDetector, ErrorEvent, ErrorType, ErrorPriority


class TestAIErrorAnalyzerIntegration:
    """Тесты интеграции AIErrorAnalyzer с LLM системой"""
    
    @pytest.fixture
    def llm_manager(self):
        """Фикстура для LLMManager"""
        # Создаем фиктивный провайдер для тестирования
        mock_provider = Mock()
        mock_provider.model = "test-model"
        mock_provider.generate = AsyncMock(return_value='{"causes": ["Test cause"]}')
        
        manager = LLMManager(providers=[mock_provider])
        return manager
    
    @pytest.fixture
    def error_detector(self):
        """Фикстура для RealtimeErrorDetector"""
        detector = RealtimeErrorDetector()
        return detector
    
    @pytest.fixture
    def ai_error_analyzer(self, llm_manager, error_detector):
        """Фикстура для AIErrorAnalyzer"""
        return AIErrorAnalyzer(llm_manager, error_detector)
    
    def test_analyze_errors_integration(self, ai_error_analyzer):
        """Тест интеграции метода analyze_errors с LLM системой"""
        # Подготовка тестовых данных
        test_errors = [
            {
                'message': 'KeyError: "key_name"',
                'location': 'telegram/src/services/example_service.py:25',
                'timestamp': '2023-10-01T10:00:00Z',
                'traceback': 'Traceback (most recent call last):\n  File "telegram/src/services/example_service.py", line 25, in example_function\n    value = some_dict["key_name"]\nKeyError: "key_name"'
            }
        ]
        
        # Вызов метода
        analyzed_errors = ai_error_analyzer.analyze_errors(test_errors)
        
        # Проверки
        assert len(analyzed_errors) == 1
        analyzed_error = analyzed_errors[0]
        
        # Проверяем, что ошибка была проанализирована
        assert 'original_error' in analyzed_error
        assert 'context' in analyzed_error
        assert 'type' in analyzed_error
        assert 'severity' in analyzed_error
        assert 'potential_causes' in analyzed_error
        
        # Проверяем, что тип ошибки определен корректно
        assert analyzed_error['type'] in ['key_error', 'unknown_error']
        
        # Проверяем, что критичность определена
        assert analyzed_error['severity'] in ['low', 'medium', 'high', 'critical']
        
        # Проверяем, что контекст сформирован
        assert isinstance(analyzed_error['context'], str)
    
    def test_generate_fix_recommendations_integration(self, ai_error_analyzer):
        """Тест интеграции метода generate_fix_recommendations с LLM системой"""
        # Подготовка данных (уже проанализированные ошибки)
        analyzed_errors = [
            {
                'original_error': {
                    'message': 'KeyError: "key_name"',
                    'location': 'telegram/src/services/example_service.py:25',
                    'timestamp': '2023-10-01T10:00:00Z',
                    'traceback': 'Traceback (most recent call last):\n  File "telegram/src/services/example_service.py", line 25, in example_function\n    value = some_dict["key_name"]\nKeyError: "key_name"'
                },
                'context': 'Местоположение: telegram/src/services/example_service.py:25',
                'type': 'key_error',
                'severity': 'high',
                'potential_causes': ['Test cause'],
                'timestamp': '2023-10-01T10:00:00Z',
                'location': 'telegram/src/services/example_service.py:25',
                'traceback': 'Traceback (most recent call last):\n  File "telegram/src/services/example_service.py", line 25, in example_function\n    value = some_dict["key_name"]\nKeyError: "key_name"',
                'suggested_fix': None,
                'fix_steps': [],
                'prevention_tips': [],
                'complexity': None,
                'patch': None
            }
        ]
        
        # Вызов метода
        updated_errors = ai_error_analyzer.generate_fix_recommendations(analyzed_errors)
        
        # Проверки
        assert len(updated_errors) == 1
        updated_error = updated_errors[0]
        
        # Проверяем, что рекомендации были сгенерированы
        assert 'suggested_fix' in updated_error
        assert 'fix_steps' in updated_error
        assert 'prevention_tips' in updated_error
        
        # Проверяем, что значения были обновлены
        assert updated_error['suggested_fix'] is not None
        assert isinstance(updated_error['fix_steps'], list)
        assert isinstance(updated_error['prevention_tips'], list)
    
    def test_classify_fix_complexity_integration(self, ai_error_analyzer):
        """Тест интеграции метода classify_fix_complexity с LLM системой"""
        # Подготовка данных (ошибки с рекомендациями)
        errors_with_recommendations = [
            {
                'original_error': {
                    'message': 'KeyError: "key_name"',
                    'location': 'telegram/src/services/example_service.py:25',
                    'timestamp': '2023-10-01T10:00Z',
                    'traceback': 'Traceback (most recent call last):\n  File "telegram/src/services/example_service.py", line 25, in example_function\n    value = some_dict["key_name"]\nKeyError: "key_name"'
                },
                'context': 'Местоположение: telegram/src/services/example_service.py:25',
                'type': 'key_error',
                'severity': 'high',
                'potential_causes': ['Test cause'],
                'timestamp': '2023-10-01T10:00Z',
                'location': 'telegram/src/services/example_service.py:25',
                'traceback': 'Traceback (most recent call last):\n File "telegram/src/services/example_service.py", line 25, in example_function\n    value = some_dict["key_name"]\nKeyError: "key_name"',
                'suggested_fix': 'Add key existence check',
                'fix_steps': ['Check if key exists', 'Handle missing key case'],
                'prevention_tips': ['Use dict.get() method'],
                'complexity': None,
                'patch': None
            }
        ]
        
        # Вызов метода
        classified_errors = ai_error_analyzer.classify_fix_complexity(errors_with_recommendations)
        
        # Проверки
        assert len(classified_errors) == 1
        classified_error = classified_errors[0]
        
        # Проверяем, что сложность была классифицирована
        assert 'complexity' in classified_error
        assert 'complexity_reasoning' in classified_error
        
        # Проверяем, что сложность имеет допустимое значение
        assert classified_error['complexity'] in ['low', 'medium', 'high', 'critical', 'unknown']
        assert isinstance(classified_error['complexity_reasoning'], str)
    
    def test_generate_safe_patches_integration(self, ai_error_analyzer):
        """Тест интеграции метода generate_safe_patches с LLM системой"""
        # Подготовка данных (ошибки с классификацией сложности)
        classified_errors = [
            {
                'original_error': {
                    'message': 'KeyError: "key_name"',
                    'location': 'telegram/src/services/example_service.py:25',
                    'timestamp': '2023-10-01T10:00Z',
                    'traceback': 'Traceback (most recent call last):\n  File "telegram/src/services/example_service.py", line 25, in example_function\n    value = some_dict["key_name"]\nKeyError: "key_name"'
                },
                'context': 'Местоположение: telegram/src/services/example_service.py:25',
                'type': 'key_error',
                'severity': 'high',
                'potential_causes': ['Test cause'],
                'timestamp': '2023-10-01T10:00:00Z',
                'location': 'telegram/src/services/example_service.py:25',
                'traceback': 'Traceback (most recent call last):\n  File "telegram/src/services/example_service.py", line 25, in example_function\n    value = some_dict["key_name"]\nKeyError: "key_name"',
                'suggested_fix': 'Add key existence check',
                'fix_steps': ['Check if key exists', 'Handle missing key case'],
                'prevention_tips': ['Use dict.get() method'],
                'complexity': 'medium',
                'complexity_reasoning': 'Requires code changes',
                'patch': None
            }
        ]
        
        # Вызов метода
        patched_errors = ai_error_analyzer.generate_safe_patches(classified_errors)
        
        # Проверки
        assert len(patched_errors) == 1
        patched_error = patched_errors[0]
        
        # Проверяем, что патч был сгенерирован (или хотя бы попытка была)
        assert 'patch' in patched_error
        # Патч может быть None, если не удалось сгенерировать, но поле должно присутствовать
    
    @pytest.mark.asyncio
    async def test_full_integration_with_real_llm_manager(self):
        """Полная интеграция с реальным LLMManager (опционально, может быть пропущена)"""
        # Этот тест можно пропустить, если нет настроенных API-ключей
        try:
            # Создаем настоящий LLMManager (требует настройки .env файла)
            llm_manager = create_llm_manager_from_env()
            error_detector = RealtimeErrorDetector()
            analyzer = AIErrorAnalyzer(llm_manager, error_detector)
            
            # Подготовка тестовой ошибки
            test_errors = [
                {
                    'message': 'KeyError: "test_key"',
                    'location': 'test_module.py:10',
                    'timestamp': datetime.utcnow().isoformat(),
                    'traceback': 'Traceback (most recent call last):\n  File "test_module.py", line 10, in test_function\n    value = some_dict["test_key"]\nKeyError: "test_key"'
                }
            ]
            
            # Полный цикл анализа
            analyzed_errors = analyzer.analyze_errors(test_errors)
            errors_with_recommendations = analyzer.generate_fix_recommendations(analyzed_errors)
            classified_errors = analyzer.classify_fix_complexity(errors_with_recommendations)
            patched_errors = analyzer.generate_safe_patches(classified_errors)
            
            # Проверки
            assert len(patched_errors) == 1
            final_error = patched_errors[0]
            
            # Проверяем, что все этапы были выполнены
            assert 'type' in final_error
            assert 'suggested_fix' in final_error
            assert 'complexity' in final_error
            assert 'patch' in final_error
            
            # Закрываем менеджер
            await llm_manager.close()
            
        except ValueError:
            # Пропускаем тест, если LLM не настроен
            pytest.skip("LLM not configured (no API keys found)")
    
    def test_error_handling_in_integration(self, ai_error_analyzer):
        """Тест обработки ошибок в интеграции"""
        # Подготовка некорректных данных
        malformed_errors = [
            {
                'message': 'Test error without proper structure',
                # Намеренно пропущены некоторые поля
            }
        ]
        
        # Проверяем, что анализ ошибок не падает при некорректных данных
        analyzed_errors = ai_error_analyzer.analyze_errors(malformed_errors)
        
        # Должна быть хотя бы частичная обработка
        assert len(analyzed_errors) == 1
        error = analyzed_errors[0]
        assert 'original_error' in error
        assert error['original_error'] == malformed_errors[0]
    
    def test_ai_classification_with_llm_integration(self, ai_error_analyzer):
        """Тест AI-классификации с использованием LLM"""
        # Подготовка ошибки для классификации
        test_error = {
            'message': 'TypeError: unsupported operand type(s)',
            'location': 'test_module.py:15',
            'traceback': 'Traceback (most recent call last):\n  File "test_module.py", line 15, in test_function\n    result = "string" + 5\nTypeError: unsupported operand type(s)'
        }
        
        # Вызов внутреннего метода классификации
        error_type = ai_error_analyzer._ai_classify_error_type(test_error)
        
        # Проверяем, что тип ошибки определен
        assert isinstance(error_type, str)
        assert error_type in ['type_error', 'unknown_error']
    
    def test_severity_assessment_with_llm_integration(self, ai_error_analyzer):
        """Тест оценки критичности с использованием LLM"""
        # Подготовка ошибки для оценки критичности
        test_error = {
            'message': 'ConnectionError: Failed to connect to database',
            'location': 'database_module.py:20',
            'traceback': 'Traceback (most recent call last):\n File "database_module.py", line 20, in connect\n    connection = create_connection()\nConnectionError: Failed to connect to database'
        }
        
        # Вызов внутреннего метода оценки критичности
        severity = ai_error_analyzer._ai_assess_severity(test_error)
        
        # Проверяем, что критичность определена
        assert isinstance(severity, str)
        assert severity in ['low', 'medium', 'high', 'critical']
    
    def test_causes_identification_with_llm_integration(self, ai_error_analyzer):
        """Тест идентификации причин с использованием LLM"""
        # Подготовка ошибки для определения причин
        test_error = {
            'message': 'AttributeError: \'NoneType\' object has no attribute \'method\'',
            'location': 'service_module.py:30',
            'traceback': 'Traceback (most recent call last):\n  File "service_module.py", line 30, in process\n    result = obj.method()\nAttributeError: \'NoneType\' object has no attribute \'method\''
        }
        
        # Вызов внутреннего метода определения причин
        causes = ai_error_analyzer._ai_identify_causes(test_error)
        
        # Проверяем, что возвращается список причин
        assert isinstance(causes, list)
        assert len(causes) >= 0  # Может быть пустым в случае ошибки, но не должен быть None
    
    def test_get_error_context(self, ai_error_analyzer):
        """Тест получения контекста ошибки"""
        # Подготовка тестовой ошибки
        test_error = {
            'location': 'test_module.py:10',
            'function': 'test_function',
            'module': 'test_module',
            'timestamp': '2023-10-01T10:00:00Z',
            'user_context': 'test_user_context'
        }
        
        # Вызов метода получения контекста
        context = ai_error_analyzer._get_error_context(test_error)
        
        # Проверки
        assert isinstance(context, str)
        assert 'Местоположение: test_module.py:10' in context
        assert 'Функция: test_function' in context
        assert 'Модуль: test_module' in context
        assert 'Время: 2023-10-01T10:00:00Z' in context
        assert 'Контекст пользователя: test_user_context' in context
    
    def test_classify_with_llm_method(self, ai_error_analyzer):
        """Тест внутреннего метода классификации с LLM"""
        # Подготовка тестовой ошибки
        test_error = {
            'message': 'SyntaxError: invalid syntax',
            'location': 'test_module.py:5',
            'traceback': 'SyntaxError: invalid syntax in test_module.py'
        }
        
        # Вызов внутреннего метода классификации
        error_type = ai_error_analyzer._classify_with_llm(test_error)
        
        # Проверки
        assert isinstance(error_type, str)
        # Должен вернуть один из допустимых типов ошибок
        valid_types = {
            'key_error', 'type_error', 'name_error', 'attribute_error',
            'value_error', 'index_error', 'connection_error', 'timeout_error',
            'database_error', 'permission_error', 'import_error',
            'syntax_error', 'indentation_error', 'eof_error', 'unknown_error'
        }
        assert error_type in valid_types
    
    def test_assess_severity_with_llm_method(self, ai_error_analyzer):
        """Тест внутреннего метода оценки критичности с LLM"""
        # Подготовка тестовой ошибки
        test_error = {
            'message': 'ValueError: invalid value',
            'location': 'critical_module.py:100',
            'traceback': 'ValueError: invalid value in critical_module.py'
        }
        
        # Вызов внутреннего метода оценки критичности
        severity = ai_error_analyzer._assess_severity_with_llm(test_error)
        
        # Проверки
        assert isinstance(severity, str)
        assert severity in ['low', 'medium', 'high', 'critical']
    
    def test_prepare_llm_context(self, ai_error_analyzer):
        """Тест подготовки контекста для LLM"""
        # Подготовка тестовой ошибки
        test_error = {
            'type': 'key_error',
            'severity': 'high',
            'location': 'test_module.py:20',
            'original_error': {
                'message': 'KeyError: "missing_key"',
                'traceback': 'Traceback: KeyError in test_module.py'
            },
            'context': 'Test context'
        }
        
        # Вызов метода подготовки контекста
        context = ai_error_analyzer._prepare_llm_context(test_error)
        
        # Проверки
        assert isinstance(context, str)
        assert 'key_error' in context
        assert 'high' in context
        assert 'test_module.py:20' in context
        assert 'KeyError: "missing_key"' in context
        assert 'Test context' in context
    
    def test_determine_complexity_method(self, ai_error_analyzer):
        """Тест метода определения сложности"""
        # Подготовка тестовой ошибки
        test_error = {
            'severity': 'high',
            'type': 'key_error',
            'fix_steps': ['Step 1', 'Step 2', 'Step 3'],
            'original_error': {
                'traceback': 'database connection error'
            },
            'location': 'main_module.py:50'
        }
        
        # Вызов метода определения сложности
        complexity = ai_error_analyzer._determine_complexity(test_error)
        
        # Проверки
        assert isinstance(complexity, str)
        assert complexity in ['low', 'medium', 'high', 'critical']
    
    def test_determine_complexity_with_reasoning_method(self, ai_error_analyzer):
        """Тест метода определения сложности с обоснованием"""
        # Подготовка тестовой ошибки
        test_error = {
            'severity': 'high',
            'type': 'database_error',
            'fix_steps': ['Step 1', 'Step 2', 'Step 3', 'Step 4', 'Step 5'],
            'original_error': {
                'traceback': 'database connection error'
            },
            'location': 'main_module.py:50'
        }
        
        # Вызов метода определения сложности с обоснованием
        result = ai_error_analyzer._determine_complexity_with_reasoning(test_error)
        
        # Проверки
        assert isinstance(result, dict)
        assert 'level' in result
        assert 'reasoning' in result
        assert result['level'] in ['low', 'medium', 'high', 'critical']
        assert isinstance(result['reasoning'], str)
    
    def test_get_code_context_method(self, ai_error_analyzer):
        """Тест метода получения контекста кода"""
        # Подготовка тестовых строк файла
        file_lines = [
            "def test_function():\n",
            "    x = 1\n",
            "    y = 2\n",
            "    result = x + y\n",
            "    return result\n"
        ]
        
        # Вызов метода получения контекста кода
        context = ai_error_analyzer._get_code_context(file_lines, 3, context_size=2)
        
        # Проверки
        assert isinstance(context, str)
        assert ">>>    3:     y = 2" in context  # Текущая строка отмечена >>>
        assert "    2:     x = 1" in context    # Предыдущая строка
        assert "    4:     result = x + y" in context  # Следующая строка
    
    def test_validate_patch_method(self, ai_error_analyzer):
        """Тест метода проверки патча"""
        # Подготовка тестового патча и строк файла
        test_patch = {
            'original_line_number': 2,
            'original_content': '    x = 1\n',
            'replacement_content': '    x = 1  # Fixed value\n',
            'file_path': 'test.py'
        }
        
        file_lines = [
            "def test_function():\n",
            "    x = 1\n",
            "    return x\n"
        ]
        
        # Вызов метода проверки патча
        is_valid = ai_error_analyzer._validate_patch(test_patch, file_lines, 2)
        
        # Проверки
        assert isinstance(is_valid, bool)
    
    def test_create_code_fix_suggestions_method(self, ai_error_analyzer):
        """Тест метода создания предложений по исправлению кода"""
        # Подготовка тестовой ошибки и строк файла
        test_error = {
            'type': 'key_error',
            'suggested_fix': 'Check key exists before accessing'
        }
        
        file_lines = [
            "def test_function():\n",
            "    some_dict = {}\n",
            "    value = some_dict['key']\n",
            "    return value\n"
        ]
        
        # Вызов метода создания предложений
        suggestions = ai_error_analyzer._create_code_fix_suggestions(test_error, file_lines, 3)
        
        # Проверки
        assert isinstance(suggestions, list)
        # Проверяем, что есть предложение для KeyError
        key_check_suggestions = [s for s in suggestions if s['type'] == 'key_check']
        assert len(key_check_suggestions) > 0
    
    def test_generate_structured_recommendations_with_llm_method(self, ai_error_analyzer):
        """Тест метода генерации структурированных рекомендаций с LLM"""
        # Подготовка контекста
        context = """
        Проанализируйте следующую ошибку и предложите рекомендации по её исправлению:
        
        Тип ошибки: key_error
        Уровень критичности: high
        Местоположение: test_module.py:25
        Сообщение об ошибке: KeyError: "missing_key"
        """
        
        # Вызов метода генерации рекомендаций
        recommendations = ai_error_analyzer._generate_structured_recommendations_with_llm(context)
        
        # Проверки
        assert isinstance(recommendations, dict)
        assert 'fix_description' in recommendations
        assert 'fix_steps' in recommendations
        assert 'potential_causes' in recommendations
        assert 'prevention_tips' in recommendations
        assert isinstance(recommendations['fix_steps'], list)
        assert isinstance(recommendations['potential_causes'], list)
        assert isinstance(recommendations['prevention_tips'], list)


# Дополнительные тесты для проверки взаимодействия с реальными компонентами LLM
class TestRealLLMIntegration:
    """Тесты с реальными компонентами LLM (требуют настройки API-ключей)"""
    
    @pytest.mark.integration
    def test_real_llm_integration(self):
        """Тест с реальным LLM (требует настройки .env)"""
        try:
            # Пытаемся создать настоящий LLMManager
            llm_manager = create_llm_manager_from_env()
            error_detector = RealtimeErrorDetector()
            analyzer = AIErrorAnalyzer(llm_manager, error_detector)
            
            # Тестовая ошибка
            test_error = {
                'message': 'KeyError: "important_key"',
                'location': 'critical_module.py:100',
                'traceback': 'Traceback (most recent call last):\n  File "critical_module.py", line 100, in important_function\n    value = data["important_key"]\nKeyError: "important_key"'
            }
            
            # Тестируем анализ ошибки
            analyzed = analyzer.analyze_errors([test_error])
            assert len(analyzed) == 1
            
            # Проверяем, что тип ошибки правильно определен
            assert analyzed[0]['type'] == 'key_error'
            
            # Закрываем ресурсы
            asyncio.run(llm_manager.close())
            
        except ValueError:
            # Пропускаем тест, если API-ключи не настроены
            pytest.skip("Real LLM not configured - set up .env file with API keys")
    
    def test_multiple_error_types_with_real_llm(self):
        """Тест нескольких типов ошибок с реальным LLM (опционально)"""
        try:
            llm_manager = create_llm_manager_from_env()
            error_detector = RealtimeErrorDetector()
            analyzer = AIErrorAnalyzer(llm_manager, error_detector)
            
            # Разные типы ошибок
            test_errors = [
                {
                    'message': 'KeyError: "missing_key"',
                    'location': 'module1.py:10',
                    'traceback': 'KeyError traceback'
                },
                {
                    'message': 'TypeError: unsupported operand type',
                    'location': 'module2.py:20',
                    'traceback': 'TypeError traceback'
                },
                {
                    'message': 'AttributeError: object has no attribute',
                    'location': 'module3.py:30',
                    'traceback': 'AttributeError traceback'
                }
            ]
            
            # Анализируем все ошибки
            analyzed = analyzer.analyze_errors(test_errors)
            assert len(analyzed) == 3
            
            # Проверяем, что каждый тип ошибки определен
            error_types = [err['type'] for err in analyzed]
            assert 'key_error' in error_types
            assert 'type_error' in error_types
            assert 'attribute_error' in error_types
            
            # Закрываем ресурсы
            asyncio.run(llm_manager.close())
            
        except ValueError:
            # Пропускаем тест, если API-ключи не настроены
            pytest.skip("Real LLM not configured - set up .env file with API keys")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])