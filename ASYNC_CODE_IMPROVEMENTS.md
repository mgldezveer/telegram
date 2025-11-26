# Рекомендации по улучшению асинхронного кода

## Критические исправления

### 1. Добавить обработку CancelledError

```python
# В conversation_manager.py
async def receive_channel_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        async with asyncio.timeout(TELEGRAM_API_TIMEOUT):
            chat, bot_member = await asyncio.gather(
                context.bot.get_chat(channel_id),
                context.bot.get_chat_member(channel_id, context.bot.id)
            )
        # ... остальной код
    except asyncio.CancelledError:
        logger.warning(f"Operation cancelled for user {update.effective_user.id}")
        await update.message.reply_text("❌ Операция отменена", parse_mode='HTML')
        raise  # Важно пробросить дальше!
    except asyncio.TimeoutError:
        # ... существующая обработка
```

### 2. Оптимизировать последовательность сообщений

```python
# В conversation_manager.py, метод receive_channel_name()
# ВМЕСТО:
await update.message.reply_text("Возвращаюсь в меню каналов...")
await self.bot_controller.menu_system.show_channels_menu(update, context)

# ИСПОЛЬЗОВАТЬ:
await self.bot_controller.menu_system.show_channels_menu(update, context)
# Или с задержкой если нужно показать промежуточное сообщение:
await update.message.reply_text("Возвращаюсь в меню каналов...")
await asyncio.sleep(0.3)
await self.bot_controller.menu_system.show_channels_menu(update, context)
```

### 3. Исправить работу с БД сессиями

```python
# В start_edit_post()
async with asyncio.timeout(DATABASE_TIMEOUT):
    async with async_session_maker() as session:
        post_repo = PostRepository(session)
        post = await post_repo.get_by_id(post_id)
        
        if not post:
            await query.edit_message_text("❌ Пост не найден", parse_mode='HTML')
            return ConversationHandler.END
        
        # Загрузить ВСЕ нужные данные ДО закрытия сессии
        post_content = post.content
        post_channel_id = post.channel_id
        post_created_at = post.created_at

# Использовать загруженные данные
text = f"<b>Текущий контент:</b>\n{post_content}\n\n..."
```

## Оптимизации производительности

### 4. Параллелизация операций

```python
# В receive_channel_name()
async def receive_channel_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # ... валидация ...
    
    try:
        # Параллельная регистрация и отправка сообщения
        results = await asyncio.gather(
            self.bot_controller.channel_manager.register_channel(channel_id, channel_config),
            update.message.reply_text("⏳ Регистрирую канал...", parse_mode='HTML'),
            return_exceptions=True
        )
        
        channel = results[0]
        if isinstance(channel, Exception):
            raise channel
        
        # Показать успех
        await update.message.reply_text(success_text, parse_mode='HTML')
        await self.bot_controller.menu_system.show_channels_menu(update, context)
        
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text(f"❌ Ошибка: {e}", parse_mode='HTML')
```

### 5. Добавить кэширование

```python
# В menu_system.py
from datetime import datetime, timedelta

class MenuSystem:
    def __init__(self, bot_controller=None):
        self.keyboard_builder = KeyboardBuilder()
        self.formatter = MessageFormatter()
        self.bot_controller = bot_controller
        self._channels_cache = {}  # user_id -> (channels, timestamp)
        self._cache_ttl = timedelta(seconds=30)
    
    async def show_channels_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        
        # Проверить кэш
        if user_id in self._channels_cache:
            channels, timestamp = self._channels_cache[user_id]
            if datetime.now() - timestamp < self._cache_ttl:
                logger.debug(f"Using cached channels for user {user_id}")
            else:
                channels = await self._fetch_channels()
                self._channels_cache[user_id] = (channels, datetime.now())
        else:
            channels = await self._fetch_channels()
            self._channels_cache[user_id] = (channels, datetime.now())
        
        # ... остальной код
    
    async def _fetch_channels(self):
        """Fetch channels from manager."""
        if self.bot_controller and self.bot_controller.channel_manager:
            try:
                return await self.bot_controller.channel_manager.get_all_channels()
            except Exception as e:
                logger.error(f"Failed to get channels: {e}")
                return []
        return []
```

### 6. Connection pooling для БД

```python
# В src/models/base.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool, QueuePool

# Для production
engine = create_async_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,  # Базовый размер пула
    max_overflow=20,  # Дополнительные соединения при нагрузке
    pool_pre_ping=True,  # Проверка соединений перед использованием
    pool_recycle=3600,  # Переиспользование соединений (1 час)
    echo=False,
    connect_args={
        "timeout": 10,  # Таймаут подключения
        "command_timeout": 30  # Таймаут команд
    }
)

# Для тестов
# engine = create_async_engine(DATABASE_URL, poolclass=NullPool)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Важно для async!
    autoflush=False,
    autocommit=False
)
```

### 7. Graceful shutdown для cleanup

```python
# В conversation_manager.py
class ConversationManager:
    def __init__(self, bot_controller=None):
        # ... существующий код ...
        self._cleanup_task = None
    
    async def start_cleanup_task(self):
        """Start periodic cleanup of expired conversations."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            logger.info("Conversation cleanup task started")
    
    async def stop_cleanup_task(self):
        """Stop cleanup task gracefully."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
            logger.info("Conversation cleanup task stopped")
    
    async def _cleanup_loop(self):
        """Periodic cleanup loop."""
        try:
            while True:
                await asyncio.sleep(300)  # Каждые 5 минут
                cleaned = await self.cleanup_expired_conversations()
                if cleaned > 0:
                    logger.info(f"Cleaned {cleaned} expired conversations")
        except asyncio.CancelledError:
            logger.info("Cleanup loop cancelled")
            raise

# В bot_controller.py
async def start(self):
    # ... существующий код ...
    
    # Start conversation cleanup
    if self.conversation_manager:
        await self.conversation_manager.start_cleanup_task()
        logger.info("Conversation cleanup started")

async def stop(self):
    # ... существующий код ...
    
    # Stop conversation cleanup
    if self.conversation_manager:
        await self.conversation_manager.stop_cleanup_task()
        logger.info("Conversation cleanup stopped")
```

## Мониторинг и отладка

### 8. Добавить метрики производительности

```python
# В conversation_manager.py
import time

class ConversationManager:
    def __init__(self, bot_controller=None):
        # ... существующий код ...
        self._operation_times = []  # Для мониторинга
    
    async def receive_channel_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        start_time = time.time()
        
        try:
            # ... существующий код ...
            
        finally:
            duration = time.time() - start_time
            self._operation_times.append(('receive_channel_id', duration))
            
            if duration > 5.0:  # Предупреждение если > 5 сек
                logger.warning(f"Slow operation: receive_channel_id took {duration:.2f}s")
    
    def get_performance_stats(self):
        """Get performance statistics."""
        if not self._operation_times:
            return {}
        
        from collections import defaultdict
        stats = defaultdict(list)
        
        for op, duration in self._operation_times:
            stats[op].append(duration)
        
        return {
            op: {
                'count': len(times),
                'avg': sum(times) / len(times),
                'max': max(times),
                'min': min(times)
            }
            for op, times in stats.items()
        }
```

## Итоговый чеклист

- [x] Таймауты для всех внешних операций (Telegram API, БД)
- [ ] Обработка CancelledError во всех async функциях
- [ ] Connection pooling для БД
- [ ] Кэширование часто запрашиваемых данных
- [ ] Параллелизация независимых операций
- [ ] Graceful shutdown для фоновых задач
- [ ] Мониторинг производительности
- [ ] Правильная работа с БД сессиями (загрузка данных до закрытия)

## Приоритеты

1. **Критично**: Добавить обработку CancelledError
2. **Важно**: Исправить работу с БД сессиями
3. **Оптимизация**: Connection pooling и кэширование
4. **Мониторинг**: Метрики производительности
