# Async Best Practices - Краткая памятка

## ⚡ Быстрый чек-лист

### ✅ Всегда делайте:

```python
# 1. Используйте таймауты для I/O операций
async with asyncio.timeout(10.0):
    result = await external_api_call()

# 2. Параллелизуйте независимые операции
results = await asyncio.gather(
    operation1(),
    operation2(),
    operation3()
)

# 3. Обрабатывайте TimeoutError
try:
    async with asyncio.timeout(5.0):
        await slow_operation()
except asyncio.TimeoutError:
    logger.error("Operation timed out")
    # Обработка таймаута

# 4. Используйте async context managers
async with async_session_maker() as session:
    # Работа с БД
    pass  # Сессия автоматически закроется
```

### ❌ Никогда не делайте:

```python
# 1. НЕ используйте блокирующие операции
time.sleep(1)  # ❌ Блокирует event loop
await asyncio.sleep(1)  # ✅ Правильно

# 2. НЕ используйте синхронные библиотеки
requests.get(url)  # ❌ Блокирует
async with aiohttp.ClientSession() as session:
    await session.get(url)  # ✅ Правильно

# 3. НЕ забывайте await
result = async_function()  # ❌ Вернет coroutine
result = await async_function()  # ✅ Правильно

# 4. НЕ делайте последовательные await для независимых операций
a = await func1()  # ❌ Медленно
b = await func2()
# Вместо этого:
a, b = await asyncio.gather(func1(), func2())  # ✅ Быстро
```

## 🎯 Константы таймаутов

```python
# src/interface/conversation_manager.py
TELEGRAM_API_TIMEOUT = 10.0  # Telegram API вызовы
DATABASE_TIMEOUT = 5.0       # Операции с БД
HTTP_TIMEOUT = 15.0          # Внешние HTTP запросы
```

## 🔧 Паттерны использования

### Паттерн 1: Telegram API с таймаутом

```python
async def get_channel_safely(bot, channel_id):
    try:
        async with asyncio.timeout(TELEGRAM_API_TIMEOUT):
            return await bot.get_chat(channel_id)
    except asyncio.TimeoutError:
        logger.error(f"Timeout getting channel {channel_id}")
        raise
    except TelegramError as e:
        logger.error(f"Telegram error: {e}")
        raise
```

### Паттерн 2: БД операции с таймаутом

```python
async def get_post_safely(post_id):
    try:
        async with asyncio.timeout(DATABASE_TIMEOUT):
            async with async_session_maker() as session:
                repo = PostRepository(session)
                return await repo.get_by_id(post_id)
    except asyncio.TimeoutError:
        logger.error(f"Database timeout for post {post_id}")
        raise
```

### Паттерн 3: Параллельные операции

```python
async def check_channel_access(bot, channel_id):
    try:
        async with asyncio.timeout(TELEGRAM_API_TIMEOUT):
            # Параллельно получаем информацию о канале и правах бота
            chat, bot_member = await asyncio.gather(
                bot.get_chat(channel_id),
                bot.get_chat_member(channel_id, bot.id),
                return_exceptions=False
            )
            return chat, bot_member
    except asyncio.TimeoutError:
        logger.error("Timeout checking channel access")
        raise
```

### Паттерн 4: Retry с exponential backoff

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def resilient_api_call(url):
    async with asyncio.timeout(HTTP_TIMEOUT):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.json()
```

## 🐛 Частые ошибки

### Ошибка 1: Забытый await

```python
# ❌ Неправильно
result = async_function()  # Вернет <coroutine object>
print(result)  # <coroutine object async_function at 0x...>

# ✅ Правильно
result = await async_function()
print(result)  # Actual result
```

### Ошибка 2: Блокирующие операции

```python
# ❌ Неправильно - блокирует event loop
def process_data():
    time.sleep(5)  # Блокирует все!
    return data

# ✅ Правильно - не блокирует
async def process_data():
    await asyncio.sleep(5)  # Другие задачи могут выполняться
    return data
```

### Ошибка 3: Последовательные независимые операции

```python
# ❌ Неправильно - медленно (4 секунды)
user = await get_user(user_id)  # 2 секунды
posts = await get_posts(user_id)  # 2 секунды

# ✅ Правильно - быстро (2 секунды)
user, posts = await asyncio.gather(
    get_user(user_id),
    get_posts(user_id)
)
```

### Ошибка 4: Незакрытые ресурсы

```python
# ❌ Неправильно - может не закрыться при ошибке
session = aiohttp.ClientSession()
response = await session.get(url)
await session.close()

# ✅ Правильно - гарантированно закроется
async with aiohttp.ClientSession() as session:
    async with session.get(url) as response:
        data = await response.json()
```

## 📊 Мониторинг производительности

```python
import time
import functools

def async_timer(func):
    """Декоратор для измерения времени выполнения async функций."""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            result = await func(*args, **kwargs)
            elapsed = time.perf_counter() - start
            logger.info(f"{func.__name__} completed in {elapsed:.2f}s")
            return result
        except Exception as e:
            elapsed = time.perf_counter() - start
            logger.error(f"{func.__name__} failed after {elapsed:.2f}s: {e}")
            raise
    return wrapper

# Использование
@async_timer
async def slow_operation():
    await asyncio.sleep(2)
    return "done"
```

## 🚀 Оптимизация производительности

### 1. Connection Pooling для БД

```python
# src/models/base.py
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,        # Размер пула
    max_overflow=10,     # Дополнительные соединения
    pool_timeout=30,     # Таймаут получения соединения
    pool_recycle=3600    # Переиспользование соединений
)
```

### 2. Кэширование

```python
from functools import lru_cache

class AsyncCache:
    def __init__(self, ttl=300):
        self._cache = {}
        self._ttl = ttl
    
    async def get_or_set(self, key, factory):
        if key in self._cache:
            value, timestamp = self._cache[key]
            if time.time() - timestamp < self._ttl:
                return value
        
        value = await factory()
        self._cache[key] = (value, time.time())
        return value
```

### 3. Batch операции

```python
# ❌ Медленно - N запросов
for post_id in post_ids:
    post = await get_post(post_id)
    process(post)

# ✅ Быстро - 1 запрос
posts = await get_posts_batch(post_ids)
for post in posts:
    process(post)
```

## 🔍 Отладка

```python
# Включить debug логи для asyncio
import logging
logging.getLogger('asyncio').setLevel(logging.DEBUG)

# Проверить незавершенные задачи
import asyncio
pending = [task for task in asyncio.all_tasks() if not task.done()]
print(f"Pending tasks: {len(pending)}")
for task in pending:
    print(f"  - {task.get_name()}: {task.get_coro()}")
```

## 🗣️ ConversationHandler с Mixed Handlers

### Правильная конфигурация

```python
from telegram.ext import ConversationHandler, CallbackQueryHandler, MessageHandler

# ✅ Правильно - per_message=False для mixed handlers
handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(start_conversation, pattern='^action:')
    ],
    states={
        STATE_INPUT: [
            MessageHandler(filters.TEXT, receive_input)
        ]
    },
    fallbacks=[
        CommandHandler('cancel', cancel),
        CallbackQueryHandler(cancel, pattern='^cancel:')
    ],
    per_message=False,  # Важно! Для mixed handlers
    conversation_timeout=300
)
```

### Почему per_message=False?

- **Entry points** используют `CallbackQueryHandler` (клики по кнопкам)
- **State handlers** используют `MessageHandler` (текстовый ввод)
- `per_message=False` обеспечивает правильную работу при переходе от callback к message

### Когда использовать per_message=True?

```python
# per_message=True - только для inline режима
# Когда все handlers работают с одним типом update
handler = ConversationHandler(
    entry_points=[MessageHandler(filters.TEXT, start)],
    states={
        STATE: [MessageHandler(filters.TEXT, process)]
    },
    fallbacks=[CommandHandler('cancel', cancel)],
    per_message=True  # Только message handlers
)
```

## 📚 Дополнительные ресурсы

- [Async Patterns Guide](https://docs.python.org/3/library/asyncio-task.html)
- [Common Pitfalls](https://docs.python-telegram-bot.org/en/stable/asyncio.html)
- [Performance Tips](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [ConversationHandler Docs](https://docs.python-telegram-bot.org/en/stable/telegram.ext.conversationhandler.html)

---

**Помните:** Async код должен быть быстрым, надежным и предсказуемым!
