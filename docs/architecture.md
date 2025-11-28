# Архитектура Telegram-бота

## Обзор

Telegram-бот представляет собой приложение с модульной архитектурой, разработанное для автоматизации публикаций в каналах, обработки команд пользователей, интеграции с LLM и аналитики. Приложение использует компонентный подход с четким разделением ответственности между модулями и поддерживает расширяемую систему плагинов.

## Структура проекта

```
telegram/
├── src/
│   ├── bot/                 # Компоненты бота
│   ├── cache/               # Система кэширования
│   ├── database/            # Работа с базой данных
│   ├── interface/           # Интерфейсы взаимодействия
│   ├── llm/                 # Интеграция с LLM
│   ├── models/              # Модели данных
│   ├── monitoring/          # Мониторинг
│   ├── repositories/        # Репозитории
│   ├── services/            # Бизнес-логика
│   └── utils/               # Утилиты
├── docs/                    # Документация
├── tests/                   # Тесты
├── requirements.txt         # Зависимости
├── run.py                   # Точка входа
├── run_autopost.py          # Точка входа для autopost
├── docker-compose.yml       # Конфигурация Docker
├── Dockerfile               # Dockerfile
└── .env.example             # Пример переменных окружения
```

## Основные компоненты

### 1. Bot (src/bot/)

Компонент бота отвечает за обработку команд и сообщений от пользователей. Включает в себя:

- `controller.py` - основной контроллер бота
- `enhanced_controller.py` - расширенный контроллер с дополнительными возможностями и Redis-бэкендом для состояния
- `handlers/` - обработчики команд (autopost, llm)
- `handlers/autopost_commands.py` - команды автопостинга
- `handlers/llm_commands.py` - команды управления LLM

### 2. Cache (src/cache/)

Система кэширования предоставляет несколько уровней хранения данных:

- `memory_cache.py` - кэш в памяти
- `redis_cache.py` - кэш с использованием Redis
- `multi_level_cache.py` - многоуровневый кэш
- `cache_service.py` - сервис кэширования
- `i_cache.py` - интерфейс кэширования
- `redis_config.py` - конфигурация Redis
- `exceptions.py` - исключения кэширования

### 3. Database (src/database/)

Работа с базой данных включает:

- `autopost_db.py` - база данных для autopost функциональности
- `enhanced_db.py` - расширенная система работы с базой данных
- `migrations/` - миграции базы данных (001_create_autopost_tables.py)

### 4. Interface (src/interface/)

Интерфейсные компоненты обеспечивают взаимодействие с пользователем:

- `callback_router.py` - маршрутизатор callback'ов
- `conversation_manager.py` - управление диалогами
- `keyboard_builder.py` - построитель клавиатур
- `menu_system.py` - система меню
- `message_formatter.py` - форматирование сообщений
- `schedule_interface.py` - интерфейс расписания
- `settings_interface.py` - интерфейс настроек
- `analytics_interface.py` - интерфейс аналитики
- `channel_interface.py` - интерфейс каналов
- `content_interface.py` - интерфейс контента
- `conversation_factory.py` - фабрика диалогов
- `validators.py` - валидаторы пользовательского ввода

### 5. LLM (src/llm/)

Интеграция с языковыми моделями:

- `llm_manager.py` - менеджер LLM
- `providers/` - провайдеры (Gemini, Groq, HuggingFace)
- `dashboard.py` - дашборд для LLM
- `metrics.py` - метрики использования LLM
- `base_provider.py` - базовый класс провайдера
- `cache_service.py` - кэширование LLM
- `config.py` - конфигурация LLM
- `models.py` - модели LLM
- `rate_limit_manager.py` - ограничение частоты запросов к LLM
- `status_checker.py` - проверка статуса провайдеров

### 6. Models (src/models/)

Модели данных:

- `channel.py` - модель канала
- `post.py` - модель поста
- `autopost.py` - модель autopost
- `metrics.py` - модель метрик
- `base.py` - базовая модель

### 7. Repositories (src/repositories/)

Репозитории для работы с сущностями:

- `channel_repository.py` - репозиторий каналов
- `post_repository.py` - репозиторий постов
- `metrics_repository.py` - репозиторий метрик
- `enhanced_post_repository.py` - расширенный репозиторий постов

### 8. Services (src/services/)

Бизнес-логика приложения:

- `channel_manager.py` - управление каналами
- `analytics_engine.py` - движок аналитики
- `content_optimizer.py` - оптимизация контента
- `enhanced_scheduler.py` - расписания
- `enhanced_error_handler.py` - обработка ошибок
- `rate_limiter.py` - ограничение частоты запросов
- `settings_storage.py` - хранение настроек
- `telegram_rate_limiter.py` - ограничение запросов к Telegram API
- `telegram_stats_parser.py` - парсер статистики Telegram
- `telethon_stats_parser.py` - парсер статистики через Telethon
- `enhanced_content_generator.py` - генератор контента
- `enhanced_publishing_service.py` - сервис публикации
- `enhanced_state_manager.py` - менеджер состояния
- `quality_control.py` - контроль качества
- `post_queue_manager.py` - менеджер очереди постов
- `content_source_manager.py` - менеджер источников контента
- `content_source_manager_improved.py` - улучшенный менеджер источников
- `health_check.py` - проверка состояния системы
- `alerting_service.py` - сервис уведомлений

### 9. Auto-posting services (src/services/autopost/)

Специализированные сервисы для автопостинга:

- `channel_manager.py` - менеджер каналов автопостинга
- `content_generator.py` - генератор контента для автопостинга
- `initializer.py` - инициализатор автопостинга
- `publishing.py` - публикация автопостинга
- `queue_manager.py` - менеджер очереди автопостинга
- `scheduler.py` - планировщик автопостинга

### 10. Utils (src/utils/)

Утилиты:

- `version_checker.py` - проверка версии

## Конфигурация

Конфигурация приложения управляется через файл `settings.json` и переменные окружения из файла `.env`. Поддерживается настройка:

- Telegram API токена
- ID администраторов
- Базы данных
- Redis
- Провайдеров LLM
- Настроек кэширования
- Настроек лимитов

## Мониторинг и логирование

Приложение включает в себя систему мониторинга и логирования:

- `logging_config.py` - конфигурация логирования
- `logging_config_improved.py` - улучшенная конфигурация логирования
- `enhanced_monitoring.py` - расширенный мониторинг
- `health_check.py` - проверка состояния системы

## Взаимодействие компонентов

Архитектура приложения построена на принципах слабой связанности и модульности:

1. **Bot Controller** - координирует работу всех компонентов
2. **LLM Manager** - предоставляет доступ к различным провайдерам LLM с возможностью резервирования
3. **Auto-posting система** - обеспечивает автоматическую генерацию и публикацию контента
4. **Interface компоненты** - обеспечивают удобное взаимодействие с пользователем через меню и кнопки
5. **Analytics Engine** - собирает и анализирует статистику публикаций
6. **Cache система** - обеспечивает эффективное кэширование данных и результатов LLM
7. **Database layer** - предоставляет абстракцию доступа к данным

## Масштабируемость

Приложение спроектировано с учетом масштабируемости:

- Поддержка Redis для распределенного кэширования и хранения состояния
- Многоуровневая архитектура с возможностью горизонтального масштабирования
- Поддержка нескольких провайдеров LLM с автоматическим резервированием
- Механизмы ограничения частоты запросов для предотвращения перегрузки
- Асинхронная архитектура для эффективной обработки запросов