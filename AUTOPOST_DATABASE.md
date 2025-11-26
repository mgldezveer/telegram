# База данных автопостинга

## Автоматическая инициализация

База данных автопостинга **автоматически инициализируется** при запуске бота.

### Как это работает:

1. При запуске бота система проверяет наличие таблиц
2. Если таблицы не существуют - создает их автоматически
3. Если таблицы уже существуют - пропускает создание

**Вам не нужно вручную инициализировать базу данных!**

## Ручная инициализация (опционально)

Если вы хотите вручную управлять базой данных:

### Проверка существования таблиц

```bash
python init_autopost_db.py
```

Вывод если таблицы существуют:
```
✅ Database tables already exist and are valid
Use --force flag to recreate tables
```

### Пересоздание таблиц

```bash
python init_autopost_db.py --force
```

Или:
```bash
python init_autopost_db.py -f
```

**⚠️ Внимание:** Это удалит все данные!

## Структура базы данных

### Таблицы:

1. **autopost_channels** - Каналы для автопостинга
   - id (INTEGER) - ID канала Telegram
   - name (TEXT) - Название
   - is_active (BOOLEAN) - Активен ли
   - settings (JSON) - Настройки
   - created_at, updated_at (TIMESTAMP)

2. **autopost_posts** - Посты
   - id (TEXT) - UUID
   - channel_id (INTEGER) - ID канала
   - content (TEXT) - Контент
   - status (TEXT) - Статус (draft, queued, approved, published, failed)
   - media, buttons, hashtags (JSON)
   - theme, style (TEXT/JSON)
   - created_at, scheduled_for, published_at (TIMESTAMP)
   - priority (INTEGER)

3. **autopost_schedules** - Расписания
   - id (TEXT) - UUID
   - channel_id (INTEGER) - ID канала
   - is_active (BOOLEAN)
   - config (JSON) - Конфигурация расписания
   - created_at, last_run, next_run (TIMESTAMP)

4. **autopost_publications** - История публикаций
   - id (INTEGER) - Автоинкремент
   - channel_id (INTEGER)
   - post_id (TEXT)
   - status (TEXT) - success, failed, retrying
   - telegram_message_id (INTEGER)
   - error_message (TEXT)
   - retry_count (INTEGER)
   - published_at (TIMESTAMP)

5. **content_sources** - Источники контента
   - id (TEXT) - UUID
   - type (TEXT) - rss, topics, file
   - name (TEXT)
   - is_active (BOOLEAN)
   - priority (INTEGER)
   - data (JSON)
   - created_at, last_used (TIMESTAMP)
   - use_count (INTEGER)

## Проверка состояния

### Через Python

```python
from src.database.autopost_db import autopost_db

# Проверить существование таблиц
exists = await autopost_db.tables_exist()
print(f"Tables exist: {exists}")
```

### Через SQLite CLI

```bash
sqlite3 bot.db

# Список таблиц
.tables

# Структура таблицы
.schema autopost_channels

# Количество записей
SELECT COUNT(*) FROM autopost_channels;
```

## Миграции

При обновлении структуры таблиц:

1. Сделайте резервную копию:
   ```bash
   copy bot.db bot.db.backup
   ```

2. Пересоздайте таблицы:
   ```bash
   python init_autopost_db.py --force
   ```

## Резервное копирование

### Создать бэкап

```bash
# Windows
copy bot.db backups\bot_backup_%date%.db

# Linux/Mac
cp bot.db backups/bot_backup_$(date +%Y%m%d).db
```

### Восстановить из бэкапа

```bash
# Windows
copy backups\bot_backup_20241126.db bot.db

# Linux/Mac
cp backups/bot_backup_20241126.db bot.db
```

## Очистка данных

### Удалить все посты

```python
from src.database.autopost_db import autopost_db
from sqlalchemy import delete
from src.models.autopost import AutoPost

async with autopost_db.session() as session:
    await session.execute(delete(AutoPost))
    await session.commit()
```

### Удалить старые публикации

```python
from datetime import datetime, timedelta

cutoff = datetime.utcnow() - timedelta(days=30)

async with autopost_db.session() as session:
    await session.execute(
        delete(AutoPostPublication).where(
            AutoPostPublication.published_at < cutoff
        )
    )
    await session.commit()
```

## Troubleshooting

### Таблицы не создаются

1. Проверьте права доступа к файлу bot.db
2. Проверьте наличие aiosqlite: `pip install aiosqlite`
3. Попробуйте пересоздать: `python init_autopost_db.py --force`

### Ошибка "database is locked"

SQLite не поддерживает множественные записи одновременно:
1. Убедитесь, что бот не запущен дважды
2. Закройте все соединения с базой
3. Перезапустите бот

### Повреждение базы данных

```bash
# Проверка целостности
sqlite3 bot.db "PRAGMA integrity_check;"

# Восстановление из бэкапа
copy backups\bot_backup_latest.db bot.db
```

## Мониторинг

### Размер базы данных

```bash
# Windows
dir bot.db

# Linux/Mac
ls -lh bot.db
```

### Статистика таблиц

```sql
-- Количество каналов
SELECT COUNT(*) FROM autopost_channels WHERE is_active = 1;

-- Количество постов в очереди
SELECT COUNT(*) FROM autopost_posts WHERE status IN ('queued', 'approved');

-- Статистика публикаций за последние 7 дней
SELECT 
    DATE(published_at) as date,
    COUNT(*) as count,
    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful
FROM autopost_publications
WHERE published_at >= datetime('now', '-7 days')
GROUP BY DATE(published_at);
```

## Производительность

### Индексы

Система автоматически создает индексы для:
- autopost_posts(channel_id)
- autopost_posts(status)
- autopost_posts(scheduled_for)
- autopost_schedules(channel_id)
- autopost_publications(channel_id)
- content_sources(is_active, priority)

### Оптимизация

```sql
-- Очистка и оптимизация
VACUUM;
ANALYZE;
```

## Безопасность

1. **Регулярные бэкапы** - делайте бэкапы перед важными операциями
2. **Права доступа** - ограничьте доступ к bot.db
3. **Не храните чувствительные данные** - API ключи только в .env
4. **Мониторинг** - следите за размером базы данных

## Лимиты SQLite

- Максимальный размер базы: 281 TB
- Максимальный размер строки: 1 GB
- Максимальное количество столбцов: 2000
- Максимальное количество таблиц: не ограничено

Для большинства ботов SQLite более чем достаточно!
