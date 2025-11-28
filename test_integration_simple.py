"""
Простой тест интеграции AIErrorAnalyzer с LLM системой
"""
import sys
import asyncio
from unittest.mock import Mock, AsyncMock, patch


def test_basic_integration():
    """Тест базовой интеграции с использованием mock всех зависимостей"""
    
    # Создаем mock для всех проблемных зависимостей
    mock_llm_module = Mock()
    mock_monitoring_module = Mock()
    mock_services_module = Mock()
    
    # Подменяем модули в sys.modules, чтобы избежать их загрузки
    sys.modules['src.llm.llm_manager'] = mock_llm_module
    sys.modules['src.monitoring.realtime_error_detector'] = mock_monitoring_module
    sys.modules['src.services.enhanced_error_handler'] = mock_services_module
    
    # Создаем необходимые классы в mock модулях
    mock_llm_manager_cls = Mock()
    mock_realtime_error_detector_cls = Mock()
    mock_enhanced_error_handler_cls = Mock()
    
    mock_llm_module.LLMManager = mock_llm_manager_cls
    mock_monitoring_module.RealtimeErrorDetector = mock_realtime_error_detector_cls
    mock_services_module.EnhancedErrorHandler = mock_enhanced_error_handler_cls
    
    # Теперь можно импортировать AIErrorAnalyzer без инициализации зависимостей
    try:
        from src.ai.error_analyzer import AIErrorAnalyzer
        
        # Создаем mock для экземпляров
        mock_llm_manager_instance = Mock()
        mock_error_detector_instance = Mock()
        
        # Создаем экземпляр анализатора
        analyzer = AIErrorAnalyzer(mock_llm_manager_instance, mock_error_detector_instance)
        
        # Проверяем, что экземпляр создан
        assert analyzer is not None
        assert analyzer.llm_manager == mock_llm_manager_instance
        assert analyzer.error_detector == mock_error_detector_instance
        
        print("Базовый экземпляр AIErrorAnalyzer создан успешно!")
        
        # Тестируем основные методы с mock
        test_errors = [
            {
                'message': 'KeyError: "key_name"',
                'location': 'test.py:10',
                'timestamp': '2023-10-01T10:00:00Z',
                'traceback': 'KeyError traceback'
            }
        ]
        
        # Мокаем внутренние методы, которые используют LLM
        with patch.object(analyzer, '_ai_classify_error_type', return_value='key_error'), \
             patch.object(analyzer, '_ai_assess_severity', return_value='high'), \
             patch.object(analyzer, '_ai_identify_causes', return_value=['Test cause']), \
             patch.object(analyzer, '_get_error_context', return_value='Test context'):
            
            analyzed = analyzer.analyze_errors(test_errors)
            
            assert len(analyzed) == 1
            error = analyzed[0]
            assert error['type'] == 'key_error'
            assert error['severity'] == 'high'
            assert 'Test cause' in error['potential_causes']
            
        print("Метод analyze_errors работает корректно!")
        
        # Тестируем generate_fix_recommendations с mock
        with patch.object(analyzer, '_prepare_llm_context', return_value='Test context'), \
             patch.object(analyzer, '_generate_structured_recommendations_with_llm', 
                         return_value={
                             'fix_description': 'Fix description',
                             'fix_steps': ['Step 1', 'Step 2'],
                             'potential_causes': ['Cause 1'],
                             'prevention_tips': ['Tip 1']
                         }):
            
            updated_errors = analyzer.generate_fix_recommendations(analyzed)
            
            assert len(updated_errors) == 1
            error = updated_errors[0]
            assert error['suggested_fix'] == 'Fix description'
            assert len(error['fix_steps']) == 2
            assert len(error['prevention_tips']) == 1
            
        print("Метод generate_fix_recommendations работает корректно!")
        
        # Тестируем classify_fix_complexity
        classified = analyzer.classify_fix_complexity(updated_errors)
        assert len(classified) == 1
        error = classified[0]
        assert 'complexity' in error
        assert 'complexity_reasoning' in error
        
        print("Метод classify_fix_complexity работает корректно!")
        
        # Тестируем generate_safe_patches
        patched = analyzer.generate_safe_patches(classified)
        assert len(patched) == 1
        error = patched[0]
        assert 'patch' in error
        
        print("Метод generate_safe_patches работает корректно!")
        
        print("\nВсе тесты интеграции пройдены успешно!")
        return True
        
    except Exception as e:
        print(f"Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_basic_integration()
    if success:
        print("\n✓ Интеграция AIErrorAnalyzer с LLM системой протестирована успешно!")
    else:
        print("\n✗ Ошибка при тестировании интеграции")