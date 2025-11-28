"""
Content Quality Analyzer Service

This module provides functionality for automated content quality checking.
It includes methods for checking uniqueness, relevance, readability,
brand compliance, engagement potential, and integration with moderation systems.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from textstat import flesch_reading_ease, flesch_kincaid_grade, \
    automated_readability_index, syllable_count, lexicon_count
from collections import Counter
import requests
import asyncio
from concurrent.futures import ThreadPoolExecutor


class ContentQualityAnalyzer:
    """
    Класс для автоматической проверки качества контента.
    """
    
    def __init__(self, brand_guidelines: Optional[Dict[str, Any]] = None, 
                 moderation_api_url: Optional[str] = None,
                 moderation_api_key: Optional[str] = None):
        """
        Инициализирует ContentQualityAnalyzer.
        
        Args:
            brand_guidelines: Словарь с корпоративными стандартами и брендовыми требованиями
            moderation_api_url: URL API для модерации контента
            moderation_api_key: API ключ для доступа к системе модерации
        """
        self.brand_guidelines = brand_guidelines or {}
        self.moderation_api_url = moderation_api_url
        self.moderation_api_key = moderation_api_key
        self.logger = logging.getLogger(__name__)
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Проверка уникальности - будем использовать простой алгоритм для примера
        # В реальной системе можно интегрировать с внешними сервисами проверки уникальности
        self.uniqueness_threshold = 0.8  # 80% уникальности как порог
    
    def check_uniqueness_and_relevance(self, content: str, 
                                     reference_texts: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Проверяет уникальность и релевантность контента.
        
        Args:
            content: Текст для проверки
            reference_texts: Список эталонных текстов для сравнения
            
        Returns:
            Словарь с результатами проверки уникальности и релевантности
        """
        if not content:
            return {
                'uniqueness_score': 0.0,
                'relevance_score': 0.0,
                'is_unique': False,
                'is_relevant': False,
                'details': 'Content is empty'
            }
        
        # Проверка уникальности
        uniqueness_score = self._calculate_uniqueness_score(content, reference_texts)
        
        # Проверка релевантности (пока простая реализация)
        relevance_score = self._calculate_relevance_score(content)
        
        is_unique = uniqueness_score >= self.uniqueness_threshold
        is_relevant = relevance_score >= 0.5  # Порог релевантности 50%
        
        return {
            'uniqueness_score': uniqueness_score,
            'relevance_score': relevance_score,
            'is_unique': is_unique,
            'is_relevant': is_relevant,
            'details': f'Uniqueness: {uniqueness_score:.2f}, Relevance: {relevance_score:.2f}'
        }
    
    def analyze_readability_and_structure(self, content: str) -> Dict[str, Any]:
        """
        Анализирует читаемость и структуру текста.
        
        Args:
            content: Текст для анализа
            
        Returns:
            Словарь с результатами анализа читаемости и структуры
        """
        if not content:
            return {
                'readability_score': 0.0,
                'flesch_reading_ease': 0.0,
                'flesch_kincaid_grade': 0.0,
                'automated_readability_index': 0.0,
                'sentence_count': 0,
                'word_count': 0,
                'paragraph_count': 0,
                'structure_analysis': {}
            }
        
        # Вычисление метрик читаемости
        flesch_ease = flesch_reading_ease(content)
        flesch_grade = flesch_kincaid_grade(content)
        ari = automated_readability_index(content)
        
        # Подсчет слов, предложений и абзацев
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]
        sentence_count = len(sentences)
        
        word_count = lexicon_count(content, removepunct=True)
        
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        paragraph_count = len(paragraphs)
        
        # Оценка читаемости (чем выше - тем лучше)
        # Flesch Reading Ease: 0-100 (90-100: очень легко, 0-30: очень сложно)
        readability_score = max(0, min(100, flesch_ease)) / 100.0
        
        # Анализ структуры
        structure_analysis = self._analyze_text_structure(content)
        
        return {
            'readability_score': readability_score,
            'flesch_reading_ease': flesch_ease,
            'flesch_kincaid_grade': flesch_grade,
            'automated_readability_index': ari,
            'sentence_count': sentence_count,
            'word_count': word_count,
            'paragraph_count': paragraph_count,
            'structure_analysis': structure_analysis
        }
    
    def check_brand_compliance(self, content: str) -> Dict[str, Any]:
        """
        Проверяет соответствие контента бренду и корпоративным стандартам.
        
        Args:
            content: Текст для проверки
            
        Returns:
            Словарь с результатами проверки соответствия бренду
        """
        if not content or not self.brand_guidelines:
            return {
                'compliance_score': 0.0 if self.brand_guidelines else 1.0,
                'compliant': not bool(self.brand_guidelines),
                'violations': [],
                'suggestions': []
            }
        
        violations = []
        suggestions = []
        
        # Проверка на запрещенные слова
        if 'forbidden_words' in self.brand_guidelines:
            forbidden = self.brand_guidelines['forbidden_words']
            found_forbidden = [word for word in forbidden if word.lower() in content.lower()]
            if found_forbidden:
                violations.append(f'Found forbidden words: {found_forbidden}')
        
        # Проверка на обязательные слова/фразы
        if 'required_keywords' in self.brand_guidelines:
            required = self.brand_guidelines['required_keywords']
            missing_required = [word for word in required if word.lower() not in content.lower()]
            if missing_required:
                suggestions.append(f'Missing required keywords: {missing_required}')
        
        # Проверка тональности
        if 'tone' in self.brand_guidelines:
            tone = self.brand_guidelines['tone']
            tone_compliance = self._check_tone_compliance(content, tone)
            if not tone_compliance['compliant']:
                violations.append(f'Tone violation: {tone_compliance["reason"]}')
        
        # Проверка длины
        if 'max_length' in self.brand_guidelines:
            max_len = self.brand_guidelines['max_length']
            if len(content) > max_len:
                violations.append(f'Content exceeds maximum length of {max_len} characters')
        
        # Проверка формата
        if 'format_requirements' in self.brand_guidelines:
            format_reqs = self.brand_guidelines['format_requirements']
            format_compliance = self._check_format_compliance(content, format_reqs)
            if not format_compliance['compliant']:
                violations.extend(format_compliance['violations'])
        
        compliance_score = max(0, 1 - (len(violations) / max(1, len(self.brand_guidelines.keys()))))
        is_compliant = len(violations) == 0
        
        return {
            'compliance_score': compliance_score,
            'compliant': is_compliant,
            'violations': violations,
            'suggestions': suggestions
        }
    
    def evaluate_engagement_potential(self, content: str) -> Dict[str, Any]:
        """
        Оценивает потенциальную вовлеченность контента.
        
        Args:
            content: Текст для оценки
            
        Returns:
            Словарь с результатами оценки потенциальной вовлеченности
        """
        if not content:
            return {
                'engagement_score': 0.0,
                'factors': {},
                'prediction': 'Low'
            }
        
        # Подсчет различных факторов, влияющих на вовлеченность
        factors = {}
        
        # Наличие призывов к действию
        cta_patterns = [
            r'\b(попробуйте|попробуй|купи|закажи|подпишитесь|подпишись|узнайте|узнай|перейдите|перейди)\b',
            r'\b(только сегодня|ограниченное время|специальное предложение)\b',
            r'\b(нажмите|кликните|сылка|читать далее)\b'
        ]
        cta_count = sum(1 for pattern in cta_patterns for _ in re.findall(pattern, content, re.IGNORECASE))
        factors['call_to_action_count'] = cta_count
        
        # Наличие эмоциональных слов
        emotional_words = [
            'новинка', 'уникальный', 'лучший', 'эксклюзив', 'бесплатно',
            'скидка', 'распродажа', 'ограничено', 'только', 'эксклюзивно',
            'революционный', 'инновационный', 'эффективный', 'мощный'
        ]
        emotional_count = sum(1 for word in emotional_words if word.lower() in content.lower())
        factors['emotional_word_count'] = emotional_count
        
        # Наличие вопросов
        question_count = len(re.findall(r'[?]', content))
        factors['question_count'] = question_count
        
        # Длина контента (оптимальная длина для вовлеченности)
        content_length = len(content)
        if 100 <= content_length <= 500:
            length_score = 1.0
        elif 50 <= content_length <= 1000:
            length_score = 0.8
        else:
            length_score = 0.5
        factors['length_score'] = length_score
        
        # Наличие хэштегов
        hashtag_count = len(re.findall(r'#\w+', content))
        factors['hashtag_count'] = hashtag_count
        
        # Наличие упоминаний (@)
        mention_count = len(re.findall(r'@\w+', content))
        factors['mention_count'] = mention_count
        
        # Наличие эмодзи
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # эмоции
            "\U0001F300-\U0001F5FF"  # символы и объекты
            "\U0001F680-\U0001F6FF"  # транспорт и символы
            "\U0001F1E0-\U0001F1FF"  # флаги
            "\U00002500-\U00002BEF"  # различные символы
            "\U00002702-\U0027B0"
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "\U0001f926-\U001f937"
            "\U00010000-\U0010ffff"
            "\u2640-\u2642"
            "\u2600-\u2B55"
            "\u200d"
            "\u23cf"
            "\u23e9"
            "\u231a"
            "\ufe0f"
            "\u3030"
            "]+", re.UNICODE
        )
        emoji_count = len(emoji_pattern.findall(content))
        factors['emoji_count'] = emoji_count
        
        # Вычисление общего балла вовлеченности
        engagement_score = self._calculate_engagement_score(factors)
        
        # Определение прогноза вовлеченности
        if engagement_score >= 0.8:
            prediction = 'High'
        elif engagement_score >= 0.5:
            prediction = 'Medium'
        else:
            prediction = 'Low'
        
        return {
            'engagement_score': engagement_score,
            'factors': factors,
            'prediction': prediction
        }
    
    async def integrate_with_moderation_system(self, content: str, 
                                             content_type: str = 'text') -> Dict[str, Any]:
        """
        Интеграция с системой модерации для проверки контента.
        
        Args:
            content: Контент для проверки
            content_type: Тип контента ('text', 'image', 'video')
            
        Returns:
            Словарь с результатами проверки в системе модерации
        """
        if not self.moderation_api_url:
            return {
                'moderation_passed': True,
                'moderation_result': 'No moderation system configured',
                'details': 'Content passed by default as no moderation system is configured'
            }
        
        try:
            headers = {
                'Authorization': f'Bearer {self.moderation_api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'content': content,
                'type': content_type,
                'source': 'telegram_bot'
            }
            
            # Выполняем запрос к системе модерации
            loop = asyncio.get_event_loop()
            moderation_result = await loop.run_in_executor(
                self.executor,
                lambda: requests.post(
                    self.moderation_api_url,
                    json=payload,
                    headers=headers
                )
            )
            
            if moderation_result.status_code == 200:
                result = moderation_result.json()
                
                return {
                    'moderation_passed': result.get('is_approved', True),
                    'moderation_result': result,
                    'details': 'Successfully checked with moderation system'
                }
            else:
                self.logger.error(f"Moderation API error: {moderation_result.status_code} - {moderation_result.text}")
                return {
                    'moderation_passed': False,
                    'moderation_result': None,
                    'details': f'Moderation API error: {moderation_result.status_code}'
                }
                
        except Exception as e:
            self.logger.error(f"Error during moderation check: {str(e)}")
            return {
                'moderation_passed': False,
                'moderation_result': None,
                'details': f'Error during moderation check: {str(e)}'
            }
    
    def _calculate_uniqueness_score(self, content: str, 
                                  reference_texts: Optional[List[str]] = None) -> float:
        """
        Вычисляет оценку уникальности контента.
        
        Args:
            content: Текст для проверки
            reference_texts: Список эталонных текстов для сравнения
            
        Returns:
            Оценка уникальности (0.0 - 1.0)
        """
        if not reference_texts:
            return 1.0  # Если нет эталонных текстов, считаем уникальным
        
        content_words = set(content.lower().split())
        min_similarity = 1.0
        
        for ref_text in reference_texts:
            ref_words = set(ref_text.lower().split())
            
            # Вычисляем коэффициент Жаккара
            intersection = len(content_words.intersection(ref_words))
            union = len(content_words.union(ref_words))
            
            if union > 0:
                similarity = intersection / union
                min_similarity = min(min_similarity, similarity)
        
        # Возвращаем оценку уникальности (1 - минимальное сходство)
        return 1.0 - min_similarity
    
    def _calculate_relevance_score(self, content: str) -> float:
        """
        Вычисляет оценку релевантности контента.
        
        Args:
            content: Текст для проверки
            
        Returns:
            Оценка релевантности (0.0 - 1.0)
        """
        # Простая реализация: проверяем наличие ключевых слов
        # В реальной системе можно использовать NLP для семантического анализа
        if not content:
            return 0.0
        
        # Пример ключевых слов (в реальной системе это может быть передано параметром)
        relevant_keywords = [
            'новый', 'современный', 'эффективный', 'качественный', 'уникальный',
            'инновационный', 'популярный', 'проверенный', 'надежный', 'лучший'
        ]
        
        content_lower = content.lower()
        found_keywords = [kw for kw in relevant_keywords if kw in content_lower]
        
        # Простая оценка: отношение найденных ключевых слов к общему числу
        # В реальной системе можно использовать более сложные алгоритмы
        relevance_score = min(1.0, len(found_keywords) / max(1, len(relevant_keywords) / 10))
        
        return relevance_score
    
    def _analyze_text_structure(self, content: str) -> Dict[str, Any]:
        """
        Анализирует структуру текста.
        
        Args:
            content: Текст для анализа
            
        Returns:
            Словарь с результатами анализа структуры
        """
        # Подсчет заголовков (предполагаем, что заголовки начинаются с # или имеют формат "Заголовок:")
        headers = re.findall(r'^(#+\s+.*?|.*?:)$', content, re.MULTILINE)
        
        # Подсчет списков
        list_items = re.findall(r'^\s*[\*\-\d]\.\s+', content, re.MULTILINE)
        
        # Подсчет изображений (предполагаем формат ![alt](url))
        images = re.findall(r'!\[.*?\]\(.*?\)', content)
        
        # Подсчет ссылок
        links = re.findall(r'\[.*?\]\(.*?\)', content)
        
        # Анализ длины предложений
        sentences = re.split(r'[.!?]+', content)
        sentence_lengths = [len(s.split()) for s in sentences if s.strip()]
        avg_sentence_length = sum(sentence_lengths) / len(sentence_lengths) if sentence_lengths else 0
        
        return {
            'header_count': len(headers),
            'list_item_count': len(list_items),
            'image_count': len(images),
            'link_count': len(links),
            'avg_sentence_length': avg_sentence_length,
            'has_structure': len(headers) > 0 or len(list_items) > 0
        }
    
    def _check_tone_compliance(self, content: str, required_tone: str) -> Dict[str, Any]:
        """
        Проверяет соответствие тональности контента.
        
        Args:
            content: Текст для проверки
            required_tone: Требуемая тональность ('formal', 'informal', 'friendly', etc.)
            
        Returns:
            Словарь с результатами проверки тональности
        """
        # Простая проверка на основе ключевых слов и фраз
        tone_indicators = {
            'formal': {
                'positive': [
                    r'уважаемые', r'почтительно', r'с уважением', r'в связи с тем',
                    r'в целях', r'в рамках', r'в соответствии с', r'на основании'
                ],
                'negative': [
                    r'ну', r'вот', r'как бы', r'типа', r'короче', r'ну типа'
                ]
            },
            'informal': {
                'positive': [
                    r'привет', r'прив', r'всем привет', r'рады видеть',
                    r'давайте', r'ну что', r'ладно', r'ага', r'ого', r'вау'
                ],
                'negative': [
                    r'уведомляем', r'информируем', r'в связи с', r'в целях'
                ]
            },
            'friendly': {
                'positive': [
                    r'друзья', r'подписчики', r'рады', r'вместе', r'вместе с вами',
                    r'ваш', r'с вами', r'для вас', r'спасибо', r'благодарим'
                ],
                'negative': [
                    r'обязательно', r'необходимо', r'требуется', r'следует'
                ]
            }
        }
        
        if required_tone not in tone_indicators:
            return {'compliant': True, 'reason': f'Unknown tone: {required_tone}'}
        
        content_lower = content.lower()
        positive_matches = sum(1 for pattern in tone_indicators[required_tone]['positive'] 
                              for _ in re.findall(pattern, content_lower))
        negative_matches = sum(1 for pattern in tone_indicators[required_tone]['negative'] 
                              for _ in re.findall(pattern, content_lower))
        
        # Если есть много негативных индикаторов и мало позитивных - тон не соблюден
        if negative_matches > positive_matches and negative_matches > 0:
            return {
                'compliant': False, 
                'reason': f'Tone mismatch: found {negative_matches} inappropriate indicators'
            }
        
        return {'compliant': True, 'reason': 'Tone is appropriate'}
    
    def _check_format_compliance(self, content: str, format_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Проверяет соответствие формату.
        
        Args:
            content: Текст для проверки
            format_requirements: Требования к формату
            
        Returns:
            Словарь с результатами проверки формата
        """
        violations = []
        
        # Проверка на наличие обязательных элементов
        if 'required_elements' in format_requirements:
            for element in format_requirements['required_elements']:
                if element == 'hashtag' and not re.search(r'#\w+', content):
                    violations.append(f'Missing required element: {element}')
                elif element == 'mention' and not re.search(r'@\w+', content):
                    violations.append(f'Missing required element: {element}')
                elif element == 'link' and not re.search(r'https?://', content):
                    violations.append(f'Missing required element: {element}')
        
        # Проверка структуры
        if 'structure' in format_requirements:
            structure = format_requirements['structure']
            if structure == 'header_content_footer':
                lines = content.strip().split('\n')
                if len(lines) < 3:
                    violations.append('Content does not follow header-content-footer structure')
        
        # Проверка максимальной длины
        if 'max_length' in format_requirements:
            max_len = format_requirements['max_length']
            if len(content) > max_len:
                violations.append(f'Content exceeds maximum length of {max_len} characters')
        
        return {
            'compliant': len(violations) == 0,
            'violations': violations
        }
    
    def _calculate_engagement_score(self, factors: Dict[str, Any]) -> float:
        """
        Вычисляет общий балл вовлеченности на основе факторов.
        
        Args:
            factors: Словарь с факторами вовлеченности
            
        Returns:
            Общий балл вовлеченности (0.0 - 1.0)
        """
        # Веса для различных факторов
        weights = {
            'call_to_action_count': 0.15,
            'emotional_word_count': 0.15,
            'question_count': 0.1,
            'length_score': 0.15,
            'hashtag_count': 0.1,
            'mention_count': 0.1,
            'emoji_count': 0.1
        }
        
        # Нормализуем значения факторов к диапазону 0-1
        normalized_factors = {}
        
        # Нормализация количественных факторов (пока просто делим на 10 для простоты)
        for key, value in factors.items():
            if key in ['call_to_action_count', 'emotional_word_count', 'question_count', 
                      'hashtag_count', 'mention_count', 'emoji_count']:
                normalized_factors[key] = min(1.0, value / 10.0)  # Нормализуем к 0-1
            elif key == 'length_score':
                normalized_factors[key] = value  # Уже нормализовано
        
        # Вычисляем взвешенную сумму
        engagement_score = 0.0
        for factor, weight in weights.items():
            factor_value = normalized_factors.get(factor, 0.0)
            engagement_score += factor_value * weight
        
        # Ограничиваем результат диапазоном 0-1
        return max(0.0, min(1.0, engagement_score))


# Пример использования
if __name__ == "__main__":
    # Пример корпоративных стандартов
    brand_guidelines = {
        'forbidden_words': ['плохой', 'ужасный', 'никогда'],
        'required_keywords': ['качество', 'инновации'],
        'tone': 'friendly',
        'max_length': 1000,
        'format_requirements': {
            'required_elements': ['hashtag'],
            'structure': 'header_content_footer'
        }
    }
    
    # Создаем анализатор
    analyzer = ContentQualityAnalyzer(
        brand_guidelines=brand_guidelines,
        moderation_api_url='https://example.com/api/moderate',
        moderation_api_key='your-api-key'
    )
    
    # Пример контента для анализа
    sample_content = """
    Привет, друзья! Мы рады представить вам наш новый продукт - инновационное решение для вашего бизнеса.
    #новинка #инновации #качество
    """
    
    # Выполняем проверки
    print("Проверка уникальности и релевантности:")
    uniqueness_result = analyzer.check_uniqueness_and_relevance(sample_content)
    print(uniqueness_result)
    
    print("\nАнализ читаемости и структуры:")
    readability_result = analyzer.analyze_readability_and_structure(sample_content)
    print(readability_result)
    
    print("\nПроверка соответствия бренду:")
    brand_result = analyzer.check_brand_compliance(sample_content)
    print(brand_result)
    
    print("\nОценка потенциальной вовлеченности:")
    engagement_result = analyzer.evaluate_engagement_potential(sample_content)
    print(engagement_result)