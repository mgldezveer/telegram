"""
Модуль для анализа ошибок с использованием ИИ
"""
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

from ..llm.llm_manager import LLMManager
from ..monitoring.realtime_error_detector import RealtimeErrorDetector
from ..services.enhanced_error_handler import EnhancedErrorHandler


class AIErrorAnalyzer:
    """
    Класс для анализа ошибок с использованием ИИ
    """
    
    def __init__(self, llm_manager: LLMManager, error_detector: RealtimeErrorDetector):
        """
        Инициализация анализатора ошибок
        
        Args:
            llm_manager: Менеджер LLM для генерации рекомендаций
            error_detector: Детектор ошибок для получения информации об ошибках
        """
        self.llm_manager = llm_manager
        self.error_detector = error_detector
        self.error_handler = EnhancedErrorHandler()
        self.logger = logging.getLogger(__name__)
        
    def analyze_errors(self, errors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Анализ полученных ошибок от системы обнаружения с использованием ИИ
        
        Args:
            errors: Список ошибок для анализа
            
        Returns:
            Список проанализированных ошибок с дополнительной информацией
        """
        analyzed_errors = []
        
        for error in errors:
            try:
                # Получаем контекст ошибки
                error_context = self._get_error_context(error)
                
                # Используем ИИ для более точной классификации типа ошибки
                error_type = self._ai_classify_error_type(error)
                
                # Используем ИИ для оценки критичности ошибки
                severity = self._ai_assess_severity(error)
                
                # Используем ИИ для определения потенциальных причин
                potential_causes = self._ai_identify_causes(error)
                
                # Формируем анализированную ошибку
                analyzed_error = {
                    'original_error': error,
                    'context': error_context,
                    'type': error_type,
                    'severity': severity,
                    'potential_causes': potential_causes,
                    'timestamp': error.get('timestamp', ''),
                    'location': error.get('location', ''),
                    'traceback': error.get('traceback', ''),
                    'suggested_fix': None,
                    'fix_steps': [],
                    'prevention_tips': [],
                    'complexity': None,
                    'patch': None
                }
                
                analyzed_errors.append(analyzed_error)
                
            except Exception as e:
                self.logger.error(f"Ошибка при анализе ошибки: {e}", exc_info=True)
                # Добавляем ошибку с минимальной информацией
                analyzed_errors.append({
                    'original_error': error,
                    'context': 'Ошибка при анализе',
                    'type': 'analysis_error',
                    'severity': 'high',
                    'potential_causes': ['Не удалось проанализировать ошибку'],
                    'timestamp': error.get('timestamp', ''),
                    'location': error.get('location', ''),
                    'traceback': error.get('traceback', ''),
                    'suggested_fix': 'Не удалось проанализировать ошибку',
                    'fix_steps': [],
                    'prevention_tips': [],
                    'complexity': 'unknown',
                    'patch': None
                })
        
        return analyzed_errors
    
    def generate_fix_recommendations(self, analyzed_errors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Генерация рекомендаций по исправлению ошибок с использованием LLM
        
        Args:
            analyzed_errors: Список проанализированных ошибок
            
        Returns:
            Список ошибок с добавленными структурированными рекомендациями
        """
        updated_errors = []
        
        for error in analyzed_errors:
            try:
                # Подготавливаем контекст для LLM
                llm_context = self._prepare_llm_context(error)
                
                # Генерируем структурированные рекомендации с помощью LLM
                fix_recommendations = self._generate_structured_recommendations_with_llm(llm_context)
                
                # Обновляем ошибку с рекомендациями
                error['suggested_fix'] = fix_recommendations.get('fix_description', 'Не удалось сформулировать рекомендации')
                error['fix_steps'] = fix_recommendations.get('fix_steps', [])
                error['potential_causes'] = fix_recommendations.get('potential_causes', error['potential_causes'])
                error['prevention_tips'] = fix_recommendations.get('prevention_tips', [])
                
                updated_errors.append(error)
                
            except Exception as e:
                self.logger.error(f"Ошибка при генерации рекомендаций: {e}", exc_info=True)
                error['suggested_fix'] = 'Не удалось сгенерировать рекомендации'
                error['fix_steps'] = []
                error['prevention_tips'] = []
                updated_errors.append(error)
        
        return updated_errors
    
    def classify_fix_complexity(self, errors_with_recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Классификация сложности исправления ошибок
        
        Args:
            errors_with_recommendations: Список ошибок с рекомендациями
            
        Returns:
            Список ошибок с классификацией сложности и обоснованием
        """
        classified_errors = []
        
        for error in errors_with_recommendations:
            try:
                # Определяем сложность на основе различных факторов
                complexity_result = self._determine_complexity_with_reasoning(error)
                
                # Обновляем ошибку с информацией о сложности и обоснованием
                error['complexity'] = complexity_result['level']
                error['complexity_reasoning'] = complexity_result['reasoning']
                
                classified_errors.append(error)
                
            except Exception as e:
                self.logger.error(f"Ошибка при определении сложности: {e}", exc_info=True)
                error['complexity'] = 'unknown'
                error['complexity_reasoning'] = 'Не удалось определить сложность из-за ошибки при анализе'
                classified_errors.append(error)
        
        return classified_errors
    
    def generate_safe_patches(self, classified_errors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Формирование безопасных патчей для кода
        
        Args:
            classified_errors: Список ошибок с классификацией сложности
            
        Returns:
            Список ошибок с безопасными патчами
        """
        patched_errors = []
        
        for error in classified_errors:
            try:
                # Генерируем безопасный патч на основе ошибки и рекомендаций
                patch = self._generate_safe_patch(error)
                
                # Обновляем ошибку с патчем
                error['patch'] = patch
                
                patched_errors.append(error)
                
            except Exception as e:
                self.logger.error(f"Ошибка при генерации патча: {e}", exc_info=True)
                error['patch'] = None
                patched_errors.append(error)
        
        return patched_errors
    
    def _get_error_context(self, error: Dict[str, Any]) -> str:
        """
        Получение контекста ошибки
        
        Args:
            error: Ошибка для анализа
            
        Returns:
            Контекст ошибки
        """
        context_parts = []
        
        if 'location' in error:
            context_parts.append(f"Местоположение: {error['location']}")
        
        if 'function' in error:
            context_parts.append(f"Функция: {error['function']}")
        
        if 'module' in error:
            context_parts.append(f"Модуль: {error['module']}")
        
        if 'timestamp' in error:
            context_parts.append(f"Время: {error['timestamp']}")
        
        if 'user_context' in error:
            context_parts.append(f"Контекст пользователя: {error['user_context']}")
        
        return "\n".join(context_parts) if context_parts else "Контекст не доступен"
    
    def _ai_classify_error_type(self, error: Dict[str, Any]) -> str:
        """
        Классификация типа ошибки с использованием ИИ
        
        Args:
            error: Ошибка для классификации
            
        Returns:
            Тип ошибки
        """
        error_message = error.get('message', '').lower()
        traceback = error.get('traceback', '').lower()
        location = error.get('location', '').lower()
        
        # Проверяем на основе сообщения об ошибке
        if 'keyerror' in error_message or 'keyerror' in traceback:
            return 'key_error'
        elif 'typeerror' in error_message or 'typeerror' in traceback:
            return 'type_error'
        elif 'nameerror' in error_message or 'nameerror' in traceback:
            return 'name_error'
        elif 'attributeerror' in error_message or 'attributeerror' in traceback:
            return 'attribute_error'
        elif 'valueerror' in error_message or 'valueerror' in traceback:
            return 'value_error'
        elif 'indexerror' in error_message or 'indexerror' in traceback:
            return 'index_error'
        elif 'connection' in error_message or 'connection' in traceback:
            return 'connection_error'
        elif 'timeout' in error_message or 'timeout' in traceback:
            return 'timeout_error'
        elif 'database' in error_message or 'database' in traceback:
            return 'database_error'
        elif 'permission' in error_message or 'permission' in traceback:
            return 'permission_error'
        elif 'import' in error_message or 'import' in traceback:
            return 'import_error'
        elif 'syntax' in error_message or 'syntax' in traceback:
            return 'syntax_error'
        elif 'indentation' in error_message or 'indentation' in traceback:
            return 'indentation_error'
        elif 'eof' in error_message or 'eof' in traceback:
            return 'eof_error'
        else:
            # Используем LLM для более сложной классификации
            return self._classify_with_llm(error)
    
    def _classify_error_type(self, error: Dict[str, Any]) -> str:
        """
        Классификация типа ошибки (старый метод для совместимости)
        
        Args:
            error: Ошибка для классификации
            
        Returns:
            Тип ошибки
        """
        return self._ai_classify_error_type(error)
    
    def _ai_assess_severity(self, error: Dict[str, Any]) -> str:
        """
        Оценка критичности ошибки с использованием ИИ
        
        Args:
            error: Ошибка для оценки
            
        Returns:
            Уровень критичности ('low', 'medium', 'high', 'critical')
        """
        error_type = self._ai_classify_error_type(error)
        error_message = error.get('message', '').lower()
        traceback = error.get('traceback', '').lower()
        location = error.get('location', '').lower()
        
        # Определяем критичность на основе типа ошибки и дополнительного контекста
        critical_types = ['connection_error', 'database_error', 'permission_error']
        high_types = ['timeout_error', 'key_error', 'type_error']
        
        if error_type in critical_types:
            return 'critical'
        elif error_type in high_types:
            return 'high'
        elif 'memory' in error_message or 'memory' in traceback:
            return 'critical'
        elif 'assertion' in error_message or 'assertion' in traceback:
            return 'high'
        elif 'main' in location or 'core' in location or 'auth' in location:
            # Ошибки в критических компонентах системы
            return 'high'
        else:
            # Используем LLM для более точной оценки критичности
            return self._assess_severity_with_llm(error)
    
    def _assess_severity(self, error: Dict[str, Any]) -> str:
        """
        Оценка критичности ошибки (старый метод для совместимости)
        
        Args:
            error: Ошибка для оценки
            
        Returns:
            Уровень критичности ('low', 'medium', 'high', 'critical')
        """
        return self._ai_assess_severity(error)
    
    def _ai_identify_causes(self, error: Dict[str, Any]) -> List[str]:
        """
        Определение потенциальных причин ошибки с использованием ИИ
        
        Args:
            error: Ошибка для анализа
            
        Returns:
            Список потенциальных причин
        """
        try:
            # Подготавливаем контекст для LLM
            context = f"""
            Проанализируйте следующую ошибку и определите возможные причины её возникновения:
            
            Тип ошибки: {self._ai_classify_error_type(error)}
            Сообщение об ошибке: {error.get('message', '')}
            Трассировка стека: {error.get('traceback', '')}
            Местоположение: {error.get('location', '')}
            
            Пожалуйста, перечислите возможные причины возникновения этой ошибки.
            Ответьте в формате JSON списка строк с причинами.
            """
            
            # Получаем модель LLM
            model = self.llm_manager.get_primary_model()
            
            # Генерируем список причин
            response = model.generate_text(
                prompt=context,
                max_tokens=150,
                temperature=0.5,
                response_format={"type": "json_object"}
            )
            
            # Парсим JSON-ответ
            import json
            result = json.loads(response.strip())
            
            # Возвращаем список причин или пустой список в случае ошибки
            return result.get('causes', []) if isinstance(result, dict) else result if isinstance(result, list) else []
            
        except Exception as e:
            self.logger.error(f"Ошибка при определении причин ошибки: {e}", exc_info=True)
            # Возвращаем общие причины в случае ошибки
            return self._get_default_causes(error)
    
    def _get_default_causes(self, error: Dict[str, Any]) -> List[str]:
        """
        Получение стандартных причин для ошибки
        
        Args:
            error: Ошибка для анализа
            
        Returns:
            Список стандартных причин
        """
        error_type = self._ai_classify_error_type(error)
        
        default_causes = {
            'key_error': [
                'Попытка доступа к несуществующему ключу в словаре',
                'Ошибка в написании ключа',
                'Отсутствие проверки наличия ключа'
            ],
            'type_error': [
                'Передача значения неправильного типа в функцию',
                'Попытка выполнения операции над несовместимыми типами',
                'Неправильная аннотация типов'
            ],
            'attribute_error': [
                'Попытка доступа к несуществующему атрибуту объекта',
                'Объект не поддерживает запрашиваемый атрибут',
                'Ошибка в написании названия атрибута'
            ],
            'connection_error': [
                'Проблемы с сетевым подключением',
                'Сервер недоступен',
                'Временный сбой соединения'
            ],
            'database_error': [
                'Проблемы с подключением к базе данных',
                'Ошибки в SQL-запросах',
                'Нарушение целостности данных'
            ]
        }
        
        return default_causes.get(error_type, ['Неизвестная причина', 'Требуется дополнительный анализ'])
    
    def _classify_with_llm(self, error: Dict[str, Any]) -> str:
        """
        Классификация ошибки с использованием LLM
        
        Args:
            error: Ошибка для классификации
            
        Returns:
            Тип ошибки
        """
        try:
            # Подготавливаем контекст для LLM
            context = f"""
            Классифицируйте следующую ошибку по её типу:
            
            Сообщение об ошибке: {error.get('message', '')}
            Трассировка стека: {error.get('traceback', '')}
            Местоположение: {error.get('location', '')}
            
            Возможные типы ошибок: key_error, type_error, name_error, attribute_error,
            value_error, index_error, connection_error, timeout_error, database_error,
            permission_error, import_error, syntax_error, indentation_error, eof_error, unknown_error
            
            Ответьте одной строкой с типом ошибки.
            """
            
            # Получаем модель LLM
            model = self.llm_manager.get_primary_model()
            
            # Генерируем классификацию
            response = model.generate_text(
                prompt=context,
                max_tokens=20,
                temperature=0.1
            )
            
            # Очищаем ответ
            error_type = response.strip().lower()
            
            # Проверяем, является ли ответ допустимым типом ошибки
            valid_types = {
                'key_error', 'type_error', 'name_error', 'attribute_error',
                'value_error', 'index_error', 'connection_error', 'timeout_error',
                'database_error', 'permission_error', 'import_error',
                'syntax_error', 'indentation_error', 'eof_error', 'unknown_error'
            }
            
            return error_type if error_type in valid_types else 'unknown_error'
            
        except Exception as e:
            self.logger.error(f"Ошибка при классификации с помощью LLM: {e}", exc_info=True)
            return 'unknown_error'
    
    def _assess_severity_with_llm(self, error: Dict[str, Any]) -> str:
        """
        Оценка критичности ошибки с использованием LLM
        
        Args:
            error: Ошибка для оценки
            
        Returns:
            Уровень критичности ('low', 'medium', 'high', 'critical')
        """
        try:
            # Подготавливаем контекст для LLM
            context = f"""
            Оцените критичность следующей ошибки:
            
            Тип ошибки: {self._ai_classify_error_type(error)}
            Сообщение об ошибке: {error.get('message', '')}
            Трассировка стека: {error.get('traceback', '')}
            Местоположение: {error.get('location', '')}
            Контекст ошибки: {self._get_error_context(error)}
            
            Возможные уровни критичности: low, medium, high, critical
            
            Ответьте одной строкой с уровнем критичности.
            """
            
            # Получаем модель LLM
            model = self.llm_manager.get_primary_model()
            
            # Генерируем оценку критичности
            response = model.generate_text(
                prompt=context,
                max_tokens=10,
                temperature=0.1
            )
            
            # Очищаем ответ
            severity = response.strip().lower()
            
            # Проверяем, является ли ответ допустимым уровнем критичности
            valid_levels = {'low', 'medium', 'high', 'critical'}
            
            return severity if severity in valid_levels else 'medium'
            
        except Exception as e:
            self.logger.error(f"Ошибка при оценке критичности с помощью LLM: {e}", exc_info=True)
            return 'medium'
    
    def _prepare_llm_context(self, error: Dict[str, Any]) -> str:
        """
        Подготовка контекста для LLM
        
        Args:
            error: Ошибка для генерации рекомендаций
            
        Returns:
            Контекст для LLM
        """
        context = f"""
        Проанализируйте следующую ошибку и предложите рекомендации по её исправлению:

        Тип ошибки: {error.get('type', 'unknown')}
        Уровень критичности: {error.get('severity', 'unknown')}
        Местоположение: {error.get('location', 'unknown')}
        Сообщение об ошибке: {error.get('original_error', {}).get('message', '')}
        Трассировка стека: {error.get('original_error', {}).get('traceback', '')}
        Контекст ошибки: {error.get('context', '')}

        Пожалуйста, предложите:
        1. Возможные причины возникновения ошибки
        2. Пошаговые инструкции по её исправлению
        3. Рекомендации по предотвращению подобных ошибок в будущем
        """
        
        return context
    
    def _determine_complexity(self, error: Dict[str, Any]) -> str:
        """
        Определение сложности исправления ошибки
        
        Args:
            error: Ошибка для анализа
            
        Returns:
            Сложность исправления ('low', 'medium', 'high', 'critical')
        """
        result = self._determine_complexity_with_reasoning(error)
        return result['level']

    def _determine_complexity_with_reasoning(self, error: Dict[str, Any]) -> Dict[str, str]:
        """
        Определение сложности исправления ошибки с обоснованием
        
        Args:
            error: Ошибка для анализа
            
        Returns:
            Словарь с уровнем сложности и обоснованием {'level': str, 'reasoning': str}
        """
        severity = error.get('severity', 'unknown')
        error_type = error.get('type', 'unknown')
        fix_steps_count = len(error.get('fix_steps', []))
        traceback = error.get('original_error', {}).get('traceback', '')
        location = error.get('location', '')
        
        # Определяем сложность на основе критичности, типа ошибки и количества шагов для исправления
        if severity == 'critical':
            level = 'high'
            reasoning = f"Ошибка имеет критический уровень серьезности ({severity}). Требуется немедленное внимание."
        elif severity == 'high':
            if error_type in ['connection_error', 'database_error']:
                level = 'high'
                reasoning = f"Ошибка типа {error_type} с высоким уровнем серьезности. Может потребовать изменения конфигурации или архитектуры системы."
            else:
                level = 'medium'
                reasoning = f"Ошибка имеет высокий уровень серьезности ({severity}) и тип {error_type}."
        elif severity == 'medium':
            # Если требуется много шагов для исправления, сложность может быть выше
            if fix_steps_count > 3:
                level = 'medium'
                reasoning = f"Ошибка средней серьезности с {fix_steps_count} шагами для исправления. Требует нескольких изменений в коде."
            else:
                level = 'low'
                reasoning = f"Ошибка средней серьезности с небольшим количеством шагов для исправления ({fix_steps_count})."
        else:  # low severity
            if fix_steps_count > 5:
                level = 'medium'
                reasoning = f"Ошибка низкой серьезности, но с {fix_steps_count} шагами для исправления. Требует значительных изменений в коде."
            else:
                level = 'low'
                reasoning = f"Ошибка низкой серьезности с небольшим количеством шагов для исправления ({fix_steps_count})."
        
        # Дополнительные проверки для повышения сложности
        if 'main' in location or 'core' in location or 'auth' in location:
            # Ошибки в критических компонентах системы
            level = 'high' if level != 'low' else 'medium'
            reasoning += f" Ошибка находится в критическом компоненте системы ({location}), что увеличивает сложность."
        
        if 'database' in traceback.lower() or 'connection' in traceback.lower():
            if level != 'high':
                level = 'medium'
            reasoning += " Трассировка стека содержит упоминания базы данных или соединения, что усложняет диагностику."
        
        # Проверяем количество шагов в рекомендациях
        if fix_steps_count > 7:
            level = 'high'
            reasoning += f" Количество шагов для исправления ({fix_steps_count}) превышает порог сложности."
        elif fix_steps_count > 4:
            level = 'medium' if level != 'high' else level
            reasoning += f" Количество шагов для исправления ({fix_steps_count}) указывает на среднюю сложность."
        
        return {'level': level, 'reasoning': reasoning}
    
    def _generate_safe_patch(self, error: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Генерация безопасного патча для кода
        
        Args:
            error: Ошибка с информацией для генерации патча
            
        Returns:
            Безопасный патч или None, если не удалось сгенерировать
        """
        try:
            # Проверяем, есть ли файл и строка для патча
            location = error.get('location', '')
            if not location:
                return None
            
            # Извлекаем путь к файлу и номер строки
            file_path = None
            line_number = None
            
            # Предполагаем формат "путь/к/файлу:номер_строки"
            if ':' in location:
                parts = location.split(':')
                if len(parts) >= 2:
                    file_path = parts[0]
                    try:
                        line_number = int(parts[1])
                    except ValueError:
                        pass
            
            if not file_path:
                return None
            
            # Проверяем, существует ли файл
            path_obj = Path(file_path)
            if not path_obj.exists():
                return None
            
            # Читаем содержимое файла
            with open(path_obj, 'r', encoding='utf-8') as f:
                file_lines = f.readlines()
            
            # Получаем строку с ошибкой
            error_line = file_lines[line_number - 1].strip() if line_number and line_number <= len(file_lines) else ''
            
            # Генерируем патч с использованием LLM
            patch = self._generate_patch_with_llm(error, file_path, line_number, error_line, file_lines)
            
            # Проверяем корректность патча
            if self._validate_patch(patch, file_lines, line_number):
                return patch
            else:
                # Если патч не проходит проверку, возвращаем базовый патч
                return {
                    'file_path': file_path,
                    'original_line_number': line_number,
                    'original_content': error_line,
                    'suggested_fix': error.get('suggested_fix', ''),
                    'recommendations': self._create_code_fix_suggestions(error, file_lines, line_number),
                    'validation_status': 'failed',
                    'patch_generation_method': 'basic_recommendations'
                }
            
        except Exception as e:
            self.logger.error(f"Ошибка при генерации патча: {e}", exc_info=True)
            return None

    def _generate_patch_with_llm(self, error: Dict[str, Any], file_path: str, line_number: Optional[int],
                                 error_line: str, file_lines: List[str]) -> Dict[str, Any]:
        """
        Генерация патча с использованием LLM
        
        Args:
            error: Ошибка с информацией
            file_path: Путь к файлу
            line_number: Номер строки с ошибкой
            error_line: Содержимое строки с ошибкой
            file_lines: Все строки файла
            
        Returns:
            Сгенерированный патч
        """
        try:
            # Подготавливаем контекст для LLM
            context = f"""
            Проанализируйте следующую ошибку и сгенерируйте безопасный патч для её исправления:
            
            Тип ошибки: {error.get('type', 'unknown')}
            Уровень критичности: {error.get('severity', 'unknown')}
            Местоположение: {error.get('location', 'unknown')}
            Сообщение об ошибке: {error.get('original_error', {}).get('message', '')}
            Трассировка стека: {error.get('original_error', {}).get('traceback', '')}
            Контекст ошибки: {error.get('context', '')}
            Рекомендации по исправлению: {error.get('suggested_fix', '')}
            Шаги для исправления: {error.get('fix_steps', [])}
            
            Текущий код (строка {line_number}):
            {error_line}
            
            Контекст кода (окружающие строки):
            {self._get_code_context(file_lines, line_number)}
            
            Пожалуйста, сгенерируйте безопасный патч в формате JSON со следующими полями:
            {{
              "file_path": "путь к файлу",
              "original_line_number": "номер оригинальной строки",
              "original_content": "оригинальное содержимое строки",
              "replacement_content": "новое содержимое строки для замены",
              "before_context": "контекст перед изменением (3-5 строк)",
              "after_context": "контекст после изменения (3-5 строк)",
              "change_description": "описание изменений",
              "safety_notes": "замечания о безопасности изменений",
              "validation_status": "pending",
              "patch_generation_method": "llm_generated"
            }}
            """
            
            # Получаем модель LLM
            model = self.llm_manager.get_primary_model()
            
            # Генерируем патч
            response = model.generate_text(
                prompt=context,
                max_tokens=800,
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
            # Парсим JSON-ответ
            import json
            patch = json.loads(response.strip())
            
            # Добавляем дополнительную информацию
            patch['file_path'] = file_path
            patch['original_line_number'] = line_number
            patch['original_content'] = error_line
            patch['patch_generation_method'] = 'llm_generated'
            patch['validation_status'] = 'pending'
            
            return patch
            
        except Exception as e:
            self.logger.error(f"Ошибка при генерации патча с помощью LLM: {e}", exc_info=True)
            # Возвращаем базовый патч в случае ошибки
            return {
                'file_path': file_path,
                'original_line_number': line_number,
                'original_content': error_line,
                'suggested_fix': error.get('suggested_fix', ''),
                'recommendations': self._create_code_fix_suggestions(error, file_lines, line_number),
                'validation_status': 'failed',
                'patch_generation_method': 'basic_recommendations'
            }

    def _get_code_context(self, file_lines: List[str], line_number: Optional[int], context_size: int = 3) -> str:
        """
        Получение контекста кода вокруг указанной строки
        
        Args:
            file_lines: Все строки файла
            line_number: Номер строки
            context_size: Размер контекста (количество строк до и после)
            
        Returns:
            Контекст кода
        """
        if not line_number or line_number > len(file_lines) or line_number <= 0:
            return ""
        
        start = max(0, line_number - 1 - context_size)
        end = min(len(file_lines), line_number + context_size)
        
        context_lines = []
        for i in range(start, end):
            line_num = i + 1
            marker = ">>> " if line_num == line_number else "    "
            context_lines.append(f"{marker}{line_num:4d}: {file_lines[i].rstrip()}")
        
        return "\n".join(context_lines)

    def _validate_patch(self, patch: Optional[Dict[str, Any]], file_lines: List[str], line_number: Optional[int]) -> bool:
        """
        Проверка корректности патча
        
        Args:
            patch: Патч для проверки
            file_lines: Оригинальные строки файла
            line_number: Номер строки для проверки
            
        Returns:
            True если патч корректен
        """
        if not patch:
            return False
        
        try:
            # Проверяем, что патч содержит необходимые поля
            required_fields = ['original_line_number', 'original_content', 'replacement_content']
            for field in required_fields:
                if field not in patch:
                    self.logger.warning(f"Поле {field} отсутствует в патче")
                    return False
            
            # Проверяем, что номер строки совпадает
            if patch['original_line_number'] != line_number:
                self.logger.warning("Номер строки в патче не совпадает с ожидаемым")
                return False
            
            # Проверяем, что оригинальное содержимое совпадает
            expected_original = file_lines[line_number - 1].strip() if line_number and line_number <= len(file_lines) else ''
            if patch['original_content'].strip() != expected_original.strip():
                self.logger.warning("Оригинальное содержимое в патче не совпадает с файлом")
                return False
            
            # Проверяем, что заменяемое содержимое не пустое (если это не удаление)
            if 'replacement_content' in patch and patch['replacement_content'] is not None:
                # Проверяем синтаксис Python если это Python файл
                if patch['file_path'].endswith('.py'):
                    try:
                        import ast
                        # Проверяем синтаксис заменяемого содержимого
                        ast.parse(patch['replacement_content'])
                    except SyntaxError:
                        self.logger.warning("Синтаксическая ошибка в заменяемом содержимом")
                        return False
            
            # Проверяем, что патч не вносит потенциально опасные изменения
            if 'replacement_content' in patch:
                dangerous_patterns = [
                    'import os', 'import subprocess', 'exec(', 'eval(', '__import__',
                    'open(', 'write(', 'remove(', 'rmdir(', 'system('
                ]
                replacement_content = patch['replacement_content'].lower()
                for pattern in dangerous_patterns:
                    if pattern in replacement_content:
                        self.logger.warning(f"Обнаружен потенциально опасный паттерн: {pattern}")
                        return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка при проверке патча: {e}", exc_info=True)
            return False

    def _apply_patch_safely(self, patch: Dict[str, Any], backup: bool = True) -> bool:
        """
        Безопасное применение патча к файлу
        
        Args:
            patch: Патч для применения
            backup: Создавать ли резервную копию
            
        Returns:
            True если патч успешно применен
        """
        try:
            file_path = Path(patch['file_path'])
            
            # Проверяем существование файла
            if not file_path.exists():
                self.logger.error(f"Файл не существует: {file_path}")
                return False
            
            # Создаем резервную копию если нужно
            if backup:
                backup_path = file_path.with_suffix(file_path.suffix + '.bak')
                import shutil
                shutil.copy2(file_path, backup_path)
                self.logger.info(f"Создана резервная копия: {backup_path}")
            
            # Читаем оригинальный файл
            with open(file_path, 'r', encoding='utf-8') as f:
                file_lines = f.readlines()
            
            # Проверяем, что номер строки в пределах файла
            line_number = patch['original_line_number']
            if line_number <= 0 or line_number > len(file_lines):
                self.logger.error(f"Номер строки вне диапазона: {line_number}")
                return False
            
            # Проверяем, что оригинальное содержимое совпадает
            expected_original = patch['original_content']
            actual_original = file_lines[line_number - 1]
            if actual_original.strip() != expected_original.strip():
                self.logger.error("Оригинальное содержимое не совпадает с ожидаемым")
                return False
            
            # Применяем изменение
            replacement_content = patch['replacement_content']
            # Сохраняем отступы оригинальной строки
            original_line = file_lines[line_number - 1]
            leading_whitespace = len(original_line) - len(original_line.lstrip())
            indented_replacement = ' ' * leading_whitespace + replacement_content.lstrip()
            
            # Заменяем строку
            file_lines[line_number - 1] = indented_replacement + '\n'
            
            # Записываем измененный файл
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(file_lines)
            
            self.logger.info(f"Патч успешно применен к {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка при применении патча: {e}", exc_info=True)
            return False
    
    def _create_code_fix_suggestions(self, error: Dict[str, Any], file_lines: List[str], line_number: Optional[int]) -> List[Dict[str, str]]:
        """
        Создание предложений по исправлению кода
        
        Args:
            error: Ошибка с информацией
            file_lines: Строки файла
            line_number: Номер строки с ошибкой
            
        Returns:
            Список предложений по исправлению
        """
        suggestions = []
        
        if not line_number or line_number > len(file_lines) or line_number <= 0:
            return suggestions
        
        # Получаем строку с ошибкой
        error_line = file_lines[line_number - 1].strip()
        
        # Определяем возможные исправления на основе типа ошибки
        error_type = error.get('type', 'unknown')
        
        if error_type == 'key_error':
            # Для KeyError предлагаем добавить проверку ключа
            suggestion = {
                'type': 'key_check',
                'description': 'Добавить проверку существования ключа перед доступом',
                'code_example': f"if 'key_name' in dict_object:\n    value = dict_object['key_name']\nelse:\n    value = default_value"
            }
            suggestions.append(suggestion)
        
        elif error_type == 'type_error':
            # Для TypeError предлагаем проверку типа
            suggestion = {
                'type': 'type_check',
                'description': 'Добавить проверку типа перед операцией',
                'code_example': f"if isinstance(variable, expected_type):\n    # выполнить операцию\n    pass\nelse:\n    # обработка ошибки типа"
            }
            suggestions.append(suggestion)
        
        elif error_type == 'attribute_error':
            # Для AttributeError предлагаем проверку атрибута
            suggestion = {
                'type': 'attribute_check',
                'description': 'Добавить проверку существования атрибута перед доступом',
                'code_example': f"if hasattr(object, 'attribute_name'):\n    value = object.attribute_name\nelse:\n    value = default_value"
            }
            suggestions.append(suggestion)
        
        # Добавляем общие рекомендации
        general_suggestion = {
            'type': 'general',
            'description': 'Общие рекомендации по исправлению',
            'code_example': error.get('suggested_fix', '')
        }
        suggestions.append(general_suggestion)
        
        return suggestions
    
    def _generate_structured_recommendations_with_llm(self, context: str) -> Dict[str, Any]:
        """
        Генерация структурированных рекомендаций с помощью LLM
        
        Args:
            context: Контекст для генерации
            
        Returns:
            Словарь с структурированными рекомендациями
        """
        try:
            # Получаем модель LLM
            model = self.llm_manager.get_primary_model()
            
            # Подготовим промпт для генерации структурированного ответа
            structured_prompt = f"""
            {context}
            
            Пожалуйста, предоставьте ответ в формате JSON со следующими полями:
            {{
              "fix_description": "Краткое описание способа исправления ошибки",
              "fix_steps": ["Шаг 1", "Шаг 2", "Шаг 3", ...],
              "potential_causes": ["Причина 1", "Причина 2", ...],
              "prevention_tips": ["Совет 1", "Совет 2", ...]
            }}
            
            Ответ должен быть на русском языке и содержать конкретные рекомендации по устранению ошибки.
            """
            
            # Генерируем структурированные рекомендации
            response = model.generate_text(
                prompt=structured_prompt,
                max_tokens=500,
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            # Парсим JSON-ответ
            import json
            result = json.loads(response.strip())
            
            # Возвращаем результат или пустую структуру в случае ошибки
            return {
                'fix_description': result.get('fix_description', ''),
                'fix_steps': result.get('fix_steps', []),
                'potential_causes': result.get('potential_causes', []),
                'prevention_tips': result.get('prevention_tips', [])
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка при генерации структурированных рекомендаций с помощью LLM: {e}", exc_info=True)
            return {
                'fix_description': 'Не удалось сгенерировать рекомендации с помощью LLM',
                'fix_steps': [],
                'potential_causes': [],
                'prevention_tips': []
            }


# Пример использования
if __name__ == "__main__":
    # Инициализация компонентов
    llm_manager = LLMManager()
    error_detector = RealtimeErrorDetector()
    
    # Создание анализатора
    analyzer = AIErrorAnalyzer(llm_manager, error_detector)
    
    # Пример ошибки для тестирования
    sample_error = {
        'message': 'KeyError: "key_name"',
        'location': 'telegram/src/services/example_service.py:25',
        'timestamp': '2023-10-01T10:00:00Z',
        'traceback': 'Traceback (most recent call last):\\n  File "telegram/src/services/example_service.py", line 25, in example_function\\n    value = some_dict["key_name"]\\nKeyError: "key_name"'
    }
    
    # Анализ ошибки
    analyzed = analyzer.analyze_errors([sample_error])
    with_recommendations = analyzer.generate_fix_recommendations(analyzed)
    classified = analyzer.classify_fix_complexity(with_recommendations)
    with_patches = analyzer.generate_safe_patches(classified)
    
    # Вывод результата
    result = with_patches[0]
    print("=== Результат анализа ошибки ===")
    print(f"Тип ошибки: {result['type']}")
    print(f"Критичность: {result['severity']}")
    print(f"Рекомендация по исправлению: {result['suggested_fix']}")
    print(f"Шаги для исправления: {result['fix_steps']}")
    print(f"Советы по предотвращению: {result['prevention_tips']}")
    print(f"Потенциальные причины: {result['potential_causes']}")
    print(f"Сложность исправления: {result['complexity']}")
    print(f"Обоснование сложности: {result['complexity_reasoning']}")
    
    # Выводим полный результат в формате JSON
    print("\n=== Полный результат ===")
    print(json.dumps(result, indent=2, ensure_ascii=False))