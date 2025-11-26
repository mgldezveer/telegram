# Implementation Plan: Free LLM Integration

## Overview

Реализация системы интеграции бесплатных LLM провайдеров с автоматическим управлением лимитами, кэшированием и fallback механизмом.

---

## Core Implementation Tasks

- [x] 1. Создать базовую архитектуру провайдеров



  - Создать абстрактный базовый класс `BaseLLMProvider`
  - Определить интерфейсы для всех провайдеров
  - Создать модели данных (`LLMResponse`, `ProviderStatus`, `RateLimitInfo`)
  - Настроить структуру директорий `src/llm/`
  - _Requirements: 1.1, 1.2_

- [ ]* 1.1 Написать unit тесты для базовых моделей
  - Тест создания `LLMResponse`
  - Тест валидации `ProviderStatus`
  - Тест сериализации моделей



  - _Requirements: 1.1_

- [ ] 2. Реализовать Groq Provider
  - Установить `groq` Python SDK
  - Создать класс `GroqProvider` наследующий `BaseLLMProvider`
  - Реализовать метод `generate()` с Llama 3 / Mixtral
  - Реализовать `check_availability()`
  - Добавить обработку ошибок и таймаутов
  - _Requirements: 2.1, 2.2, 2.4_

- [ ]* 2.1 Написать property тест для Groq генерации
  - **Property 1: Groq returns valid response**
  - **Validates: Requirements 2.4**

- [ ]* 2.2 Написать unit тесты для Groq Provider
  - Тест инициализации клиента

  - Тест форматирования запроса



  - Тест обработки ответа
  - Тест обработки ошибок
  - _Requirements: 2.1, 2.2_

- [ ] 3. Реализовать Google Gemini Provider
  - Установить `google-generativeai` SDK
  - Создать класс `GeminiProvider` наследующий `BaseLLMProvider`
  - Реализовать метод `generate()` с gemini-pro
  - Настроить safety settings
  - Добавить обработку дневных лимитов
  - _Requirements: 3.1, 3.2, 3.4_

- [x]* 3.1 Написать property тест для Gemini генерации

  - **Property 2: Gemini returns safe content**
  - **Validates: Requirements 3.5**




- [ ]* 3.2 Написать unit тесты для Gemini Provider
  - Тест инициализации клиента
  - Тест safety settings
  - Тест обработки лимитов
  - _Requirements: 3.1, 3.2_

- [ ] 4. Реализовать Hugging Face Provider
  - Установить `huggingface_hub` SDK
  - Создать класс `HuggingFaceProvider` наследующий `BaseLLMProvider`
  - Реализовать метод `generate()` с Mixtral
  - Добавить fallback на альтернативные модели
  - Обработать медленные ответы
  - _Requirements: 4.1, 4.2, 4.3, 4.4_




- [ ]* 4.1 Написать property тест для HF генерации
  - **Property 3: HF handles model unavailability**
  - **Validates: Requirements 4.3**

- [ ]* 4.2 Написать unit тесты для HF Provider
  - Тест выбора модели
  - Тест fallback логики
  - Тест кэширования
  - _Requirements: 4.1, 4.2_

- [ ] 5. Реализовать Rate Limit Manager
  - Создать класс `RateLimitManager`
  - Реализовать sliding window algorithm с Redis
  - Добавить методы `check_limit()` и `record_request()`
  - Реализовать автоматический reset счетчиков


  - Добавить методы получения статистики
  - _Requirements: 5.1, 5.2, 5.4, 5.5_

- [ ]* 5.1 Написать property тест для rate limiting
  - **Property 2: Rate limit enforcement**
  - **Validates: Requirements 5.2**

- [ ]* 5.2 Написать unit тесты для Rate Limit Manager
  - Тест sliding window
  - Тест reset логики
  - Тест статистики
  - _Requirements: 5.1, 5.2_

- [ ] 6. Реализовать Cache Service
  - Создать класс `CacheService` с Redis backend
  - Реализовать методы `get()` и `set()` с TTL
  - Добавить генерацию cache keys из промптов



  - Реализовать LRU eviction
  - Добавить опциональное семантическое кэширование
  - _Requirements: 6.1, 6.2, 6.3_

- [ ]* 6.1 Написать property тест для кэширования
  - **Property 3: Cache consistency**
  - **Validates: Requirements 6.1**

- [ ]* 6.2 Написать unit тесты для Cache Service
  - Тест cache hit/miss
  - Тест TTL expiration
  - Тест LRU eviction
  - Тест cache key generation
  - _Requirements: 6.1, 6.2_

- [ ] 7. Реализовать LLM Manager (Orchestrator)
  - Создать класс `LLMManager`
  - Реализовать логику выбора провайдера
  - Добавить fallback chain при ошибках
  - Интегрировать Rate Limit Manager
  - Интегрировать Cache Service
  - Реализовать метод `generate()` с полной логикой


  - _Requirements: 1.1, 1.3, 1.4, 7.1, 7.2, 7.3_

- [ ]* 7.1 Написать property тест для fallback chain


  - **Property 1: Provider fallback chain**
  - **Validates: Requirements 1.3**

- [ ]* 7.2 Написать property тест для retry логики
  - **Property 4: Retry with exponential backoff**
  - **Validates: Requirements 7.1**

- [ ]* 7.3 Написать property тест для provider switching
  - **Property 5: Provider switching on rate limit**
  - **Validates: Requirements 7.2**



- [ ]* 7.4 Написать unit тесты для LLM Manager
  - Тест выбора провайдера
  - Тест fallback логики
  - Тест интеграции с cache
  - Тест интеграции с rate limiter
  - _Requirements: 1.1, 1.3, 7.1_

- [ ] 8. Реализовать конфигурацию и управление
  - Создать класс `LLMConfig` для загрузки настроек
  - Добавить валидацию API ключей при старте
  - Реализовать приоритизацию провайдеров
  - Добавить команду проверки статуса провайдеров
  - Создать `.env.example` с примерами настроек
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ]* 8.1 Написать property тест для конфигурации
  - **Property 7: Configuration validation**
  - **Validates: Requirements 8.4**

- [ ]* 8.2 Написать unit тесты для конфигурации
  - Тест загрузки из env
  - Тест валидации ключей
  - Тест приоритизации
  - _Requirements: 8.1, 8.2_




- [ ] 9. Реализовать мониторинг и метрики
  - Создать класс `LLMMetrics` для сбора метрик
  - Добавить Prometheus метрики (requests, latency, errors)
  - Реализовать методы получения статистики
  - Создать dashboard endpoint для метрик
  - Добавить логирование всех операций

  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [ ]* 9.1 Написать property тест для метрик
  - **Property 8: Metrics recording**
  - **Validates: Requirements 9.1, 9.2, 9.3**

- [ ]* 9.2 Написать unit тесты для метрик
  - Тест записи метрик



  - Тест агрегации
  - Тест экспорта в Prometheus
  - _Requirements: 9.1, 9.2_

- [ ] 10. Интегрировать с Vibe Coding Engine
  - Обновить `VibeCodingEngine` для использования `LLMManager`
  - Заменить mock генерацию на реальные LLM вызовы
  - Добавить индикаторы загрузки в интерфейс
  - Обработать ошибки генерации в UI
  - Добавить сохранение истории генераций
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [ ]* 10.1 Написать property тест для vibe coding интеграции
  - **Property 9: Vibe coding integration**
  - **Validates: Requirements 10.1**

- [ ]* 10.2 Написать integration тест для vibe coding
  - Тест генерации всех 6 ролей
  - Тест форматирования для Telegram
  - Тест обработки ошибок
  - _Requirements: 10.1, 10.2, 10.3_




- [ ] 11. Создать CLI команды для управления
  - Добавить команду `/llm_status` для проверки провайдеров
  - Добавить команду `/llm_stats` для статистики
  - Добавить команду `/llm_switch <provider>` для ручного переключения
  - Добавить команду `/llm_cache_clear` для очистки кэша
  - Ограничить команды только для администраторов
  - _Requirements: 8.5, 9.4_

- [ ]* 11.1 Написать unit тесты для CLI команд
  - Тест каждой команды
  - Тест admin проверки
  - Тест форматирования вывода
  - _Requirements: 8.5_

- [ ] 12. Checkpoint - Тестирование базовой функциональности
  - Убедиться что все провайдеры инициализируются
  - Проверить работу fallback механизма
  - Проверить кэширование
  - Проверить rate limiting
  - Запросить обратную связь от пользователя

- [ ] 13. Оптимизация и улучшения
  - Оптимизировать промпты для экономии токенов
  - Добавить batch обработку запросов
  - Улучшить семантическое кэширование
  - Оптимизировать выбор провайдера по скорости
  - _Requirements: 6.4_

- [ ]* 13.1 Написать performance тесты
  - Тест скорости кэша
  - Тест времени генерации
  - Тест throughput
  - _Requirements: 6.4_

- [ ] 14. Создать документацию
  - Написать README для LLM интеграции
  - Документировать получение API ключей
  - Создать troubleshooting guide
  - Добавить примеры использования
  - Документировать метрики и мониторинг
  - _Requirements: 8.1_

- [ ] 15. Финальное тестирование
  - Запустить все unit тесты
  - Запустить все property тесты
  - Запустить integration тесты
  - Протестировать с реальными API
  - Проверить все 6 ролей вайбкодинга
  - Убедиться что все работает без ошибок

---

## Implementation Summary

### Приоритет задач

**Высокий приоритет (MVP):**
- Задачи 1-7: Базовая архитектура и основные провайдеры
- Задача 10: Интеграция с вайбкодингом
- Задача 12: Checkpoint тестирование

**Средний приоритет:**
- Задача 8: Конфигурация
- Задача 9: Мониторинг
- Задача 11: CLI команды

**Низкий приоритет:**
- Задача 13: Оптимизация
- Задача 14: Документация

### Технологический стек

**Основные библиотеки:**
- `groq` - Groq API client
- `google-generativeai` - Google Gemini API
- `huggingface_hub` - Hugging Face Inference API
- `redis` - Кэширование и rate limiting
- `prometheus-client` - Метрики

**Дополнительные:**
- `tenacity` - Retry логика
- `pydantic` - Валидация данных
- `asyncio` - Асинхронность

### Ожидаемые результаты

После завершения реализации:
- ✅ 3 бесплатных LLM провайдера работают
- ✅ Автоматическое переключение при лимитах
- ✅ Кэширование снижает запросы на 30%+
- ✅ Вайбкодинг использует реальный AI
- ✅ Полный мониторинг и метрики
- ✅ Надежная обработка ошибок

### Следующие шаги после завершения

1. Протестировать с реальными пользователями
2. Собрать метрики использования
3. Оптимизировать на основе данных
4. Добавить дополнительные провайдеры при необходимости
5. Рассмотреть fine-tuning для специфических задач
