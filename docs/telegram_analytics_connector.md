# Telegram Analytics Connector

## Обзор

`TelegramAnalyticsConnector` - это класс, предназначенный для интеграции с аналитикой Telegram. Он предоставляет возможность получения метрик вовлеченности, анализа постов и интеграции данных с существующей системой метрик. Класс реализует асинхронную работу и поддерживает контекстное управление.

## Назначение и возможности

Класс `TelegramAnalyticsConnector` решает следующие задачи:

1. **Получение метрик вовлеченности**: Извлечение данных о просмотрах, реакциях, репостах, комментариях и других метриках.
2. **Анализ постов**: Получение статистики по конкретным постам в канале.
3. **Нормализация данных**: Обработка и приведение полученных данных к стандартному формату.
4. **Интеграция с системой метрик**: Сохранение и обновление метрик в базе данных.
5. **Синхронизация аналитики**: Регулярная синхронизация аналитических данных с базой данных.

Важно отметить, что официальное API аналитики Telegram недоступно через Bot API. Класс использует альтернативный подход через Telethon (MTProto API) для получения реальных статистических данных.

## Основные методы

### `__init__(bot_token: str, api_base_url: str = "https://api.telegram.org/bot")`

Инициализирует соединение с Telegram API.

- **bot_token**: Токен бота для аутентификации в API Telegram
- **api_base_url**: Базовый URL для API Telegram (по умолчанию официальный API)
- **Возвращает**: Новый экземпляр `TelegramAnalyticsConnector`

### `connect()`

Асинхронно устанавливает соединение с API Telegram.

- **Возвращает**: `None`

### `disconnect()`

Асинхронно закрывает соединение с API Telegram.

- **Возвращает**: `None`

### `get_engagement_metrics(channel_username: str, period_start: datetime, period_end: datetime) -> EngagementMetrics`

Получает метрики вовлеченности для указанного канала за заданный период.

- **channel_username**: Имя пользователя канала без символа @
- **period_start**: Начало периода анализа
- **period_end**: Конец периода анализа
- **Возвращает**: Объект `EngagementMetrics` с данными аналитики

### `get_post_metrics(channel_username: str, post_ids: List[int]) -> Dict[int, EngagementMetrics]`

Получает метрики для конкретных постов в канале.

- **channel_username**: Имя пользователя канала без символа @
- **post_ids**: Список ID постов для получения метрик
- **Возвращает**: Словарь, сопоставляющий ID постов с их метриками

### `process_and_normalize_data(raw_data: Dict[str, Any]) -> Dict[str, Any]`

Обрабатывает и нормализует необработанные данные аналитики.

- **raw_data**: Необработанные данные из API аналитики Telegram
- **Возвращает**: Нормализованные данные в стандартном формате

### `integrate_with_metrics_system(channel_id: int, normalized_data: Dict[str, Any]) -> bool`

Интегрирует нормализованные данные с существующей системой метрик.

- **channel_id**: ID канала в базе данных
- **normalized_data**: Нормализованные аналитические данные
- **Возвращает**: `True`, если интеграция прошла успешно

### `sync_channel_analytics(channel_username: str, channel_id: int, days_back: int = 30) -> bool`

Синхронизирует аналитику канала с базой данных.

- **channel_username**: Имя пользователя канала без символа @
- **channel_id**: ID канала в базе данных
- **days_back**: Количество дней для синхронизации аналитики (по умолчанию 30)
- **Возвращает**: `True`, если синхронизация прошла успешно

## Класс EngagementMetrics

Класс данных для хранения метрик вовлеченности:

- **views**: Количество просмотров
- **reactions**: Количество реакций
- **shares**: Количество репостов
- **comments**: Количество комментариев
- **engagement_rate**: Процент вовлеченности
- **reach**: Охват (предполагаемое количество пользователей)
- **impressions**: Количество показов
- **saves**: Количество сохранений
- **forwards**: Количество пересылок

## Доступ к Telegram Analytics

Telegram предоставляет ограниченный доступ к аналитике через Bot API. Официальное API аналитики Telegram недоступно для большинства разработчиков. Для получения реальных статистических данных класс использует следующие альтернативы:

1. **Telethon (MTProto API)**: Для получения реальных статистических данных используется библиотека Telethon, которая работает с MTProto API Telegram. Для этого требуются API ID и API Hash, которые можно получить на my.telegram.org.

2. **Ограничения Bot API**: Через Bot API можно получить только базовую информацию о канале, но не детальную аналитику.

Для полноценной работы с аналитикой рекомендуется настроить учетные данные Telethon в конфигурации приложения.

## Примеры использования

### Базовое использование

```python
from datetime import datetime, timedelta
from src.services.telegram_analytics_connector import TelegramAnalyticsConnector

# Инициализация коннектора
connector = TelegramAnalyticsConnector("YOUR_BOT_TOKEN")

# Получение метрик вовлеченности
period_start = datetime.utcnow() - timedelta(days=7)
period_end = datetime.utcnow()

engagement_metrics = await connector.get_engagement_metrics(
    "channel_username",
    period_start,
    period_end
)

print(f"Просмотры: {engagement_metrics.views}")
print(f"Реакции: {engagement_metrics.reactions}")
print(f"Вовлеченность: {engagement_metrics.engagement_rate}%")
```

### Использование с контекстным менеджером

```python
from datetime import datetime, timedelta
from src.services.telegram_analytics_connector import TelegramAnalyticsConnector

async with TelegramAnalyticsConnector("YOUR_BOT_TOKEN") as connector:
    # Получение метрик для конкретных постов
    post_metrics = await connector.get_post_metrics(
        "channel_username",
        [1, 2, 3, 4, 5]
    )
    
    for post_id, metrics in post_metrics.items():
        print(f"Пост {post_id}: {metrics.views} просмотров")
```

### Синхронизация аналитики канала

```python
from src.services.telegram_analytics_connector import TelegramAnalyticsConnector

async with TelegramAnalyticsConnector("YOUR_BOT_TOKEN") as connector:
    # Синхронизация аналитики за последние 30 дней
    success = await connector.sync_channel_analytics(
        "channel_username",
        channel_id=123,  # ID канала в базе данных
        days_back=30
    )
    
    if success:
        print("Аналитика успешно синхронизирована")
    else:
        print("Ошибка синхронизации аналитики")
```

### Интеграция с системой метрик

```python
from src.services.telegram_analytics_connector import TelegramAnalyticsConnector

async with TelegramAnalyticsConnector("YOUR_BOT_TOKEN") as connector:
    # Получение необработанных данных
    raw_data = {
        'views': 1000,
        'reactions': 50,
        'shares': 25,
        'comments': 10,
        'engagement_rate': 7.5
    }
    
    # Нормализация данных
    normalized_data = await connector.process_and_normalize_data(raw_data)
    
    # Интеграция с системой метрик
    integration_success = await connector.integrate_with_metrics_system(
        channel_id=123,
        normalized_data=normalized_data
    )
    
    if integration_success:
        print("Данные успешно интегрированы с системой метрик")
    else:
        print("Ошибка интеграции с системой метрик")
```

## Интеграция с остальной системой

Класс `TelegramAnalyticsConnector` интегрируется с системой следующим образом:

1. **Связь с базой данных**: Использует `MetricsRepository` и модель `Metrics` для сохранения и получения аналитических данных.

2. **Связь с моделями**: Работает с моделями `Post` и `Channel` для сопоставления метрик с конкретными постами и каналами.

3. **Интеграция с Telethon**: Использует `TelethonStatsParser` для получения реальных статистических данных через MTProto API, когда это возможно.

4. **Совместимость с системой логирования**: Использует стандартную систему логирования приложения для отслеживания операций и ошибок.

5. **Асинхронная архитектура**: Совместим с асинхронной архитектурой приложения, используя `aiohttp` для HTTP-запросов и асинхронные сессии базы данных.

## Обработка ошибок

Класс включает в себя надежную обработку ошибок:

- Проверяет соединение перед выполнением запросов
- Обрабатывает ошибки API Telegram с соответствующими сообщениями
- Возвращает пустые метрики в случае ошибок вместо падения приложения
- Использует логирование для отслеживания проблем

## Требования к конфигурации

Для полной функциональности класса необходимы следующие параметры конфигурации:

- `TELEGRAM_BOT_TOKEN`: Токен бота для доступа к Bot API
- `TELEGRAM_API_ID`: API ID для доступа к MTProto API (для получения реальной аналитики)
- `TELEGRAM_API_HASH`: API Hash для доступа к MTProto API (для получения реальной аналитики)

Если учетные данные Telethon недоступны, класс будет использовать альтернативные методы или возвращать placeholder-данные.