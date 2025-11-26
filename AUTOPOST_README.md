# Auto-Posting Bot - Руководство

## Описание

Система автоматической публикации контента в Telegram каналы с использованием LLM для генерации уникального контента.

## Возможности

✅ **Управление каналами**
- Добавление/удаление каналов
- Проверка прав бота
- Настройки для каждого канала

✅ **Генерация контента**
- Использование LLM (Groq/Gemini)
- Различные стили (новости, советы, истории)
- Автоматические хештеги
- Шаблоны контента

✅ **Расписание публикаций**
- Фиксированное время
- Случайные интервалы
- Дни недели
- Множественные слоты

✅ **Очередь постов**
- Приоритизация
- Модерация
- Редактирование
- Автопубликация

✅ **Публикация**
- Текст с форматированием
- Медиа (фото, видео)
- Кнопки и ссылки
- Опросы
- Retry логика

## Установка

### 1. Инициализация базы данных

```bash
python init_autopost_db.py
```

### 2. Настройка

Убедитесь, что в `.env` указаны:
```
TELEGRAM_BOT_TOKEN=your_token
ADMIN_IDS=your_user_id
GROQ_API_KEY=your_groq_key
```

### 3. Запуск бота

```bash
python run.py
```

## Использование

### Добавить канал

```
/autopost_add_channel -1001234567890 "Мой канал"
```

**Требования:**
- Бот должен быть администратором канала
- Бот должен иметь права на публикацию

### Настроить расписание

```
/autopost_schedule -1001234567890 09:00,15:00,21:00
```

Посты будут публиковаться в 9:00, 15:00 и 21:00 каждый день.

### Сгенерировать пост вручную

```
/autopost_generate -1001234567890 технологии
```

Пост будет сгенерирован и добавлен в очередь.

### Просмотр очереди

```
/autopost_queue
```

Или для конкретного канала:
```
/autopost_queue -1001234567890
```

### Список каналов

```
/autopost_list_channels
```

## Архитектура

```
┌─────────────────────────────────────────┐
│         Telegram Bot                     │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│      Auto-Post Controller                │
└──────────────┬──────────────────────────┘
               │
    ┌──────────┼──────────┐
    │          │          │
┌───▼────┐ ┌──▼──────┐ ┌▼────────┐
│Channel │ │Content  │ │Scheduler│
│Manager │ │Generator│ │Service  │
└───┬────┘ └──┬──────┘ └┬────────┘
    │          │          │
    └──────────▼──────────▼────────┐
         Post Queue Manager         │
         └──────────┬────────────────┘
                    │
         ┌──────────▼────────────┐
         │  Publishing Service   │
         └───────────────────────┘
```

## Компоненты

### 1. Channel Manager
- `src/services/autopost/channel_manager.py`
- Управление каналами
- Проверка прав

### 2. Content Generator
- `src/services/autopost/content_generator.py`
- Генерация через LLM
- Шаблоны и стили

### 3. Scheduler
- `src/services/autopost/scheduler.py`
- Расписание публикаций
- Триггеры

### 4. Queue Manager
- `src/services/autopost/queue_manager.py`
- Очередь постов
- Модерация

### 5. Publisher
- `src/services/autopost/publishing.py`
- Публикация в Telegram
- Retry логика

## Модели данных

### AutoPostChannel
- Информация о канале
- Настройки
- Статус

### AutoPost
- Контент поста
- Статус
- Медиа и кнопки

### AutoPostSchedule
- Конфигурация расписания
- Время следующего запуска

### AutoPostPublication
- История публикаций
- Статистика
- Ошибки

## Примеры использования

### Программный доступ

```python
from src.services.autopost import (
    AutoPostChannelManager,
    ChannelConfig,
    AutoPostContentGenerator,
    ContentStyle,
    AutoPostScheduler,
    ScheduleConfig
)

# Добавить канал
config = ChannelConfig(
    name="Мой канал",
    auto_publish=True,
    post_frequency=3
)
channel = await channel_manager.add_channel(-1001234567890, config)

# Сгенерировать пост
style = ContentStyle(
    tone="professional",
    length="medium",
    format="news"
)
post = await generator.generate_post("технологии", style, channel.id)

# Добавить расписание
schedule = ScheduleConfig(
    channel_id=channel.id,
    mode=ScheduleMode.FIXED,
    time_slots=["09:00", "15:00", "21:00"]
)
schedule_id = await scheduler.add_schedule(channel.id, schedule)
```

## Настройки канала

```python
settings = {
    "auto_publish": True,          # Автопубликация без модерации
    "require_moderation": False,   # Требовать одобрение
    "default_style": "professional", # Стиль по умолчанию
    "default_language": "ru",      # Язык
    "post_frequency": 3            # Постов в день
}
```

## Стили контента

- **professional** - Профессиональный тон
- **casual** - Неформальный
- **humorous** - Юмористический
- **formal** - Официальный

## Форматы контента

- **news** - Новости
- **tips** - Советы
- **story** - История
- **announcement** - Анонс

## Troubleshooting

### Бот не может публиковать

1. Проверьте, что бот - администратор канала
2. Проверьте права на публикацию
3. Используйте `/autopost_add_channel` для проверки прав

### Посты не генерируются

1. Проверьте наличие LLM API ключей
2. Проверьте логи: `logs/bot.log`
3. Попробуйте ручную генерацию: `/autopost_generate`

### Расписание не работает

1. Убедитесь, что scheduler запущен
2. Проверьте формат времени (HH:MM)
3. Проверьте дни недели (0-6)

## Команды

| Команда | Описание | Пример |
|---------|----------|--------|
| `/autopost_add_channel` | Добавить канал | `/autopost_add_channel -1001234567890 "Мой канал"` |
| `/autopost_list_channels` | Список каналов | `/autopost_list_channels` |
| `/autopost_generate` | Сгенерировать пост | `/autopost_generate -1001234567890 технологии` |
| `/autopost_queue` | Просмотр очереди | `/autopost_queue` или `/autopost_queue -1001234567890` |
| `/autopost_schedule` | Добавить расписание | `/autopost_schedule -1001234567890 09:00,15:00,21:00` |
| `/autopost_help` | Справка | `/autopost_help` |

**Примечание:** Все команды автопостинга доступны только администраторам, указанным в `ADMIN_IDS`.

## Лицензия

MIT License
