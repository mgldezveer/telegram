# Примеры использования

## Базовые сценарии

### 1. Регистрация канала

```python
# Через команду бота
/register -1001234567890 "Технологический блог"

# Программно
from src.services.channel_manager import ChannelManager, ChannelConfig

config = ChannelConfig(
    name="Технологический блог",
    posting_frequency=3,
    optimal_times=["09:00", "14:00", "19:00"],
    themes=["технологии", "ИИ", "программирование"],
    style_tone="professional",
    style_length="medium",
    emoji_usage=True,
    hashtag_count=3
)

channel = await channel_manager.register_channel(-1001234567890, config)
```

### 2. Генерация контента

```python
from src.services.content_generator import ContentGenerator, ContentStyle
from src.config import config

# Генератор автоматически использует настройки из config
generator = ContentGenerator()

# Проверить текущего AI провайдера
print(f"Using AI provider: {config.ai.provider}")
print(f"Model: {config.ai.model}")
print(f"Temperature: {config.ai.temperature}")

# Простая генерация
style = ContentStyle(
    tone="professional",
    length="medium",
    emoji_usage=True
)

post = await generator.generate_post(
    theme="искусственный интеллект",
    style=style,
    channel_id=1
)

print(post.content)
```

### 3. Оптимизация контента

```python
from src.services.content_optimizer import ContentOptimizer

optimizer = ContentOptimizer()

# Оптимизировать пост
optimized_post = await optimizer.optimize(post)

# Проверить engagement score
score = await optimizer.analyze_engagement(post)
print(f"Engagement score: {score.score:.2f}")
print(f"Recommendations: {score.recommendations}")

# Сгенерировать хэштеги
hashtags = await optimizer.generate_hashtags(post.content)
print(f"Hashtags: {hashtags}")
```

### 4. Планирование публикации

```python
from src.services.scheduler_service import SchedulerService
from datetime import datetime, timedelta

scheduler = SchedulerService()

# Запланировать на оптимальное время
scheduled = await scheduler.schedule_post(post, channel)
print(f"Scheduled for: {scheduled.scheduled_time}")

# Запланировать на конкретное время
specific_time = datetime.now() + timedelta(hours=2)
scheduled = await scheduler.schedule_post(post, channel, specific_time)
```

### 5. Публикация с retry

```python
from src.services.publishing_service import PublishingService

publishing = PublishingService(channel_manager)

# Опубликовать с автоматическими повторами
result = await publishing.publish_with_retry(post, channel)

if result.success:
    print(f"Published! Message ID: {result.message_id}")
else:
    print(f"Failed: {result.error}")
```

## Продвинутые сценарии

### 6. Аналитика и отчеты

```python
from src.services.analytics_engine import AnalyticsEngine, TimePeriod
from datetime import datetime, timedelta

analytics = AnalyticsEngine()

# Создать отчет за неделю
period = TimePeriod(
    start=datetime.now() - timedelta(days=7),
    end=datetime.now()
)

report = await analytics.get_performance_report(
    channel_id=1,
    period=period,
    posts=channel_posts
)

print(f"Total posts: {report.total_posts}")
print(f"Total views: {report.total_views}")
print(f"Avg engagement: {report.avg_engagement_rate:.2%}")

# Анализ паттернов
patterns = await analytics.analyze_patterns(channel_id=1, posts=channel_posts)
print(f"Best posting times: {patterns.best_posting_times}")

# Получить рекомендации
recommendations = await analytics.get_recommendations(
    channel_id=1,
    patterns=patterns,
    recent_performance=0.03
)

for rec in recommendations:
    print(f"[{rec.priority}] {rec.description}")
```

### 7. Контроль качества

```python
from src.services.quality_control import QualityControl

qc = QualityControl()

# Проверить качество
result = await qc.check_quality(post)

if result.passed:
    print(f"Quality check passed! Score: {result.score:.2f}")
else:
    print(f"Quality issues found:")
    for issue in result.issues:
        print(f"  - {issue}")
    
    # Отклонить и запросить новую генерацию
    await qc.reject_and_regenerate(post, "Quality issues")
```

### 8. Обработка ошибок

```python
from src.services.error_handler import ErrorHandler, ErrorCategory

error_handler = ErrorHandler()

try:
    post = await generator.generate_post(theme, style, channel_id)
except Exception as e:
    # Обработать ошибку
    recovered = await error_handler.handle_error(
        error=e,
        category=ErrorCategory.GENERATION,
        component="ContentGenerator",
        details={"theme": theme, "channel_id": channel_id}
    )
    
    if not recovered:
        # Критическая ошибка
        await error_handler.handle_critical_failure(
            error=e,
            component="ContentGenerator"
        )
```

### 9. Работа с кэшем

```python
from src.cache import cache

# Подключиться к Redis
await cache.connect()

# Сохранить в кэш
await cache.set("channel:1:config", channel_config, ttl=3600)

# Получить из кэша
config = await cache.get("channel:1:config")

# Проверить существование
exists = await cache.exists("channel:1:config")

# Удалить из кэша
await cache.delete("channel:1:config")

# Закрыть соединение
await cache.close()
```

### 10. Фоновые задачи с Celery

```python
from src.tasks import generate_content_task, publish_post_task

# Запустить генерацию в фоне
task = generate_content_task.delay(
    channel_id=1,
    theme="технологии",
    style={"tone": "professional", "length": "medium"}
)

# Проверить статус
print(f"Task ID: {task.id}")
print(f"Status: {task.status}")

# Дождаться результата
result = task.get(timeout=60)
print(f"Result: {result}")

# Запустить публикацию
publish_task = publish_post_task.delay(post_id=123, channel_id=1)
```

## Интеграция с внешними системами

### 11. Webhook для уведомлений

```python
from aiohttp import web

async def webhook_handler(request):
    """Обработчик webhook для внешних уведомлений."""
    data = await request.json()
    
    # Обработать событие
    if data['event'] == 'new_post_needed':
        channel_id = data['channel_id']
        theme = data['theme']
        
        # Сгенерировать и опубликовать
        post = await generator.generate_post(theme, style, channel_id)
        post = await optimizer.optimize(post)
        await publishing.publish_with_retry(post, channel)
    
    return web.json_response({'status': 'ok'})

# Добавить маршрут
app.router.add_post('/webhook', webhook_handler)
```

### 12. API для внешнего управления

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class GenerateRequest(BaseModel):
    channel_id: int
    theme: str
    style: dict

@app.post("/api/generate")
async def api_generate(request: GenerateRequest):
    """API endpoint для генерации контента."""
    try:
        style = ContentStyle(**request.style)
        post = await generator.generate_post(
            request.theme,
            style,
            request.channel_id
        )
        
        return {
            "status": "success",
            "post_id": post.id,
            "content": post.content
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/status/{channel_id}")
async def api_status(channel_id: int):
    """Получить статус канала."""
    channel = await channel_repo.get_by_id(channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    return {
        "channel_id": channel.id,
        "name": channel.name,
        "active": channel.active,
        "posting_frequency": channel.posting_frequency
    }
```

## Кастомизация

### 13. Собственный генератор контента

```python
from src.services.content_generator import ContentGenerator

class CustomContentGenerator(ContentGenerator):
    """Кастомный генератор с дополнительной логикой."""
    
    async def generate_post(self, theme, style, channel_id):
        # Добавить предобработку
        theme = self._preprocess_theme(theme)
        
        # Вызвать базовый генератор
        post = await super().generate_post(theme, style, channel_id)
        
        # Добавить постобработку
        post = self._postprocess_post(post)
        
        return post
    
    def _preprocess_theme(self, theme):
        # Ваша логика
        return theme.lower().strip()
    
    def _postprocess_post(self, post):
        # Добавить подпись
        post.content += "\n\n📱 Подписывайтесь на наш канал!"
        return post
```

### 14. Кастомный оптимизатор

```python
from src.services.content_optimizer import ContentOptimizer

class CustomOptimizer(ContentOptimizer):
    """Оптимизатор с дополнительными проверками."""
    
    async def optimize(self, post):
        # Базовая оптимизация
        post = await super().optimize(post)
        
        # Добавить эмодзи если их нет
        if not self._has_emoji(post.content):
            post.content = self._add_emoji(post.content)
        
        # Проверить длину
        if len(post.content) < 100:
            post.content = await self._expand_content(post.content)
        
        return post
    
    def _has_emoji(self, text):
        import re
        emoji_pattern = re.compile("[\U0001F600-\U0001F64F]")
        return bool(emoji_pattern.search(text))
```

## Тестирование

### 15. Unit тесты

```python
import pytest
from src.services.content_generator import ContentGenerator

@pytest.mark.asyncio
async def test_content_generation():
    generator = ContentGenerator()
    
    post = await generator.generate_post(
        theme="тестирование",
        style=ContentStyle(),
        channel_id=1
    )
    
    assert post is not None
    assert len(post.content) > 0
    assert post.channel_id == 1

@pytest.mark.asyncio
async def test_content_validation():
    generator = ContentGenerator()
    
    # Валидный контент
    result = generator.validate_content("Это тестовый пост")
    assert result.valid is True
    
    # Слишком короткий
    result = generator.validate_content("Hi")
    assert result.valid is False
    assert "too short" in result.errors[0].lower()
```

### 16. Integration тесты

```python
@pytest.mark.asyncio
async def test_full_workflow():
    """Тест полного цикла: генерация -> оптимизация -> публикация."""
    
    # Генерация
    post = await generator.generate_post("тест", style, 1)
    assert post.status == PostStatus.DRAFT
    
    # Оптимизация
    post = await optimizer.optimize(post)
    assert len(post.hashtags) > 0
    
    # Планирование
    scheduled = await scheduler.schedule_post(post, channel)
    assert scheduled.scheduled_time is not None
    
    # Публикация
    result = await publishing.publish_with_retry(post, channel)
    assert result.success is True
```

## Мониторинг и отладка

### 17. Логирование

```python
import logging

# Настроить логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Использовать в коде
logger.info("Starting content generation")
logger.warning("Low engagement detected")
logger.error("Failed to publish post", exc_info=True)
```

### 18. Метрики

```python
from src.monitoring import (
    posts_generated,
    posts_published,
    generation_duration,
    track_generation_time
)

# Использовать декоратор
@track_generation_time
async def generate_content():
    # Ваш код
    pass

# Или вручную
posts_generated.inc()
generation_duration.observe(2.5)
```

Эти примеры покрывают основные сценарии использования бота. Для более детальной информации см. документацию в `.kiro/specs/ai-content-bot/`.
