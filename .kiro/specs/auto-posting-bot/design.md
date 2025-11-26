# Design Document - Auto-Posting Bot

## Overview

Система автоматической публикации контента в Telegram каналы представляет собой комплексное решение для автономной генерации и публикации постов. Система использует LLM для создания уникального контента, планировщик для автоматической публикации по расписанию, и предоставляет полный набор инструментов для управления каналами, контентом и аналитикой.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Telegram Bot API                         │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                  Bot Controller                              │
│  - Command Handlers                                          │
│  - Callback Routing                                          │
│  - Admin Authorization                                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
┌───────▼────────┐ ┌──▼──────────┐ ┌▼────────────────┐
│ Channel Manager│ │Content Gen  │ │ Scheduler       │
│ - Add/Remove   │ │ - LLM       │ │ - Cron Jobs     │
│ - Permissions  │ │ - Templates │ │ - Time Slots    │
│ - Settings     │ │ - Styles    │ │ - Random        │
└───────┬────────┘ └──┬──────────┘ └┬────────────────┘
        │              │              │
        │      ┌───────▼──────────────▼────┐
        │      │   Post Queue Manager      │
        │      │   - Queue Storage         │
        │      │   - Moderation            │
        │      │   - Priority              │
        │      └───────┬───────────────────┘
        │              │
        └──────────────▼───────────────────┐
                 Publishing Service         │
                 - Telegram API             │
                 - Retry Logic              │
                 - Error Handling           │
                 └────────────┬─────────────┘
                              │
                 ┌────────────▼─────────────┐
                 │   Analytics Engine       │
                 │   - Statistics           │
                 │   - Reports              │
                 │   - Metrics              │
                 └──────────────────────────┘
```

### Component Interaction Flow

1. **Scheduler** триггерит создание поста по расписанию
2. **Content Generator** использует LLM для генерации контента
3. **Post Queue Manager** добавляет пост в очередь
4. **Publishing Service** публикует пост в канал
5. **Analytics Engine** записывает метрики публикации

## Components and Interfaces

### 1. Channel Manager

**Responsibilities:**
- Управление каналами (добавление, удаление, обновление)
- Проверка прав бота в каналах
- Хранение настроек каналов

**Interface:**
```python
class ChannelManager:
    async def add_channel(self, channel_id: int, config: ChannelConfig) -> Channel
    async def remove_channel(self, channel_id: int) -> bool
    async def get_channel(self, channel_id: int) -> Optional[Channel]
    async def list_channels(self, active_only: bool = True) -> List[Channel]
    async def update_settings(self, channel_id: int, settings: dict) -> bool
    async def check_permissions(self, channel_id: int) -> PermissionStatus
```

### 2. Content Generator

**Responsibilities:**
- Генерация контента через LLM
- Применение шаблонов и стилей
- Форматирование постов

**Interface:**
```python
class ContentGenerator:
    async def generate_post(
        self,
        theme: str,
        style: ContentStyle,
        template: Optional[str] = None
    ) -> Post
    
    async def apply_template(self, content: str, template: str) -> str
    async def format_post(self, post: Post) -> str
```

### 3. Scheduler Service

**Responsibilities:**
- Управление расписанием публикаций
- Триггеринг создания постов
- Поддержка различных режимов (фиксированное время, случайные интервалы)

**Interface:**
```python
class SchedulerService:
    async def add_schedule(
        self,
        channel_id: int,
        schedule: ScheduleConfig
    ) -> str  # schedule_id
    
    async def remove_schedule(self, schedule_id: str) -> bool
    async def get_next_run_time(self, schedule_id: str) -> datetime
    async def trigger_post_creation(self, channel_id: int) -> None
```

### 4. Post Queue Manager

**Responsibilities:**
- Управление очередью постов
- Модерация постов
- Приоритизация публикаций

**Interface:**
```python
class PostQueueManager:
    async def add_to_queue(self, post: Post, priority: int = 0) -> str  # queue_id
    async def get_queue(self, channel_id: Optional[int] = None) -> List[QueuedPost]
    async def approve_post(self, queue_id: str) -> bool
    async def edit_post(self, queue_id: str, content: str) -> bool
    async def remove_from_queue(self, queue_id: str) -> bool
    async def get_next_post(self, channel_id: int) -> Optional[QueuedPost]
```

### 5. Publishing Service

**Responsibilities:**
- Публикация постов в каналы
- Retry логика при ошибках
- Обработка различных типов контента

**Interface:**
```python
class PublishingService:
    async def publish_post(self, post: Post, channel_id: int) -> PublishResult
    async def publish_with_media(
        self,
        post: Post,
        channel_id: int,
        media: List[Media]
    ) -> PublishResult
    
    async def publish_poll(
        self,
        question: str,
        options: List[str],
        channel_id: int
    ) -> PublishResult
```

### 6. Content Source Manager

**Responsibilities:**
- Управление источниками контента (RSS, темы, файлы)
- Парсинг и импорт данных
- Приоритизация источников

**Interface:**
```python
class ContentSourceManager:
    async def add_rss_feed(self, url: str, priority: int = 0) -> str  # source_id
    async def add_topic_list(self, topics: List[str], priority: int = 0) -> str
    async def import_from_file(self, file_path: str) -> str
    async def get_next_content(self) -> Optional[ContentSource]
    async def activate_source(self, source_id: str) -> bool
```

### 7. Analytics Engine

**Responsibilities:**
- Сбор статистики публикаций
- Генерация отчетов
- Отслеживание метрик

**Interface:**
```python
class AnalyticsEngine:
    async def record_publication(
        self,
        channel_id: int,
        post_id: str,
        status: PublishStatus
    ) -> None
    
    async def get_statistics(
        self,
        channel_id: Optional[int] = None,
        period: TimePeriod = TimePeriod.WEEK
    ) -> Statistics
    
    async def generate_report(
        self,
        channel_id: Optional[int] = None
    ) -> Report
```

## Data Models

### Channel
```python
@dataclass
class Channel:
    id: int  # Telegram channel ID
    name: str
    is_active: bool
    created_at: datetime
    settings: ChannelSettings
    permissions: PermissionStatus
```

### ChannelSettings
```python
@dataclass
class ChannelSettings:
    auto_publish: bool = True
    require_moderation: bool = False
    default_style: str = "professional"
    default_language: str = "ru"
    post_frequency: int = 3  # posts per day
```

### Post
```python
@dataclass
class Post:
    id: str
    channel_id: int
    content: str
    media: List[Media] = field(default_factory=list)
    buttons: List[InlineButton] = field(default_factory=list)
    hashtags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    scheduled_for: Optional[datetime] = None
    status: PostStatus = PostStatus.DRAFT
```

### ScheduleConfig
```python
@dataclass
class ScheduleConfig:
    channel_id: int
    mode: ScheduleMode  # FIXED, RANDOM, INTERVAL
    time_slots: List[TimeSlot]
    days_of_week: List[int]  # 0-6 (Monday-Sunday)
    random_range: Optional[Tuple[int, int]] = None  # minutes
```

### ContentStyle
```python
@dataclass
class ContentStyle:
    tone: str  # professional, casual, humorous, formal
    length: str  # short, medium, long
    format: str  # news, tips, story, announcement
    keywords: List[str] = field(default_factory=list)
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Channel Registration Uniqueness
*For any* channel ID, when adding a channel to the system, the channel should be stored with a unique identifier and retrievable by that ID.
**Validates: Requirements 1.1**

### Property 2: Channel List Completeness
*For any* set of active channels, when requesting the channel list, all active channels should be returned with their current settings.
**Validates: Requirements 1.2**

### Property 3: Channel Deactivation Effect
*For any* channel, when deactivating it, all future scheduled publications for that channel should be cancelled.
**Validates: Requirements 1.3**

### Property 4: Settings Application
*For any* channel settings update, all posts created after the update should use the new settings.
**Validates: Requirements 1.4**

### Property 5: Permission Verification
*For any* channel being added, the system should verify bot permissions before allowing registration.
**Validates: Requirements 1.5**

### Property 6: Schedule Persistence
*For any* schedule configuration, when saved, it should be retrievable and match the original configuration.
**Validates: Requirements 2.1**

### Property 7: Scheduled Post Creation
*For any* active schedule, when the scheduled time arrives, a post should be automatically created and queued.
**Validates: Requirements 2.2**

### Property 8: Random Interval Bounds
*For any* random interval schedule, all generated publication times should fall within the specified range.
**Validates: Requirements 2.3**

### Property 9: Day of Week Filtering
*For any* schedule with specific days, posts should only be created on those days.
**Validates: Requirements 2.4**

### Property 10: Multiple Time Slots
*For any* channel with multiple time slots, each slot should trigger independent post creation.
**Validates: Requirements 2.5**

### Property 11: LLM Content Generation
*For any* post generation request, the system should invoke the LLM provider to create content.
**Validates: Requirements 3.1**

### Property 12: Theme-Based Generation
*For any* specified theme, the generated content should be relevant to that theme.
**Validates: Requirements 3.2**

### Property 13: Template Application
*For any* template and content, applying the template should structure the content according to the template format.
**Validates: Requirements 3.3**

### Property 14: Queue Addition
*For any* generated post, it should be added to the publication queue with a unique queue ID.
**Validates: Requirements 3.4**

### Property 15: Style Variation
*For any* two different content styles, the generated content should reflect the characteristics of each style.
**Validates: Requirements 3.5**

### Property 16: RSS Feed Parsing
*For any* valid RSS feed URL, the system should successfully parse and extract entries.
**Validates: Requirements 4.1**

### Property 17: Topic List Usage
*For any* list of topics, the system should use topics from the list for content generation.
**Validates: Requirements 4.2**

### Property 18: File Import Parsing
*For any* valid data file, the system should successfully import and parse the content.
**Validates: Requirements 4.3**

### Property 19: Source Activation
*For any* content source, when activated, it should be included in the pool of sources for content generation.
**Validates: Requirements 4.4**

### Property 20: Source Prioritization
*For any* set of sources with different priorities, higher priority sources should be selected more frequently.
**Validates: Requirements 4.5**

### Property 21: Queue Display Completeness
*For any* channel, when requesting the queue, all scheduled posts for that channel should be displayed.
**Validates: Requirements 5.1**

### Property 22: Post Edit Persistence
*For any* post in the queue, when edited, the changes should be saved and reflected in subsequent retrievals.
**Validates: Requirements 5.2**

### Property 23: Queue Removal Effect
*For any* post removed from the queue, it should not be published at its scheduled time.
**Validates: Requirements 5.3**

### Property 24: Approval Status
*For any* post, when approved, its status should change to approved and it should be eligible for publication.
**Validates: Requirements 5.4**

### Property 25: Auto-Publish Mode
*For any* channel with auto-publish enabled, posts should be published without requiring manual approval.
**Validates: Requirements 5.5**

### Property 26: Text Formatting Support
*For any* post with formatting markup, the published post should display the formatting correctly.
**Validates: Requirements 6.1**

### Property 27: Media Attachment
*For any* post with media configured, the published post should include the specified media files.
**Validates: Requirements 6.2**

### Property 28: Button and Link Support
*For any* post with buttons or links, they should be functional in the published post.
**Validates: Requirements 6.3**

### Property 29: Content Type Formatting
*For any* content type, the generated post should follow the format conventions for that type.
**Validates: Requirements 6.4**

### Property 30: Poll Creation
*For any* poll configuration, the system should create a valid Telegram poll with the specified options.
**Validates: Requirements 6.5**

### Property 31: Statistics Accuracy
*For any* time period, the statistics should accurately reflect the number of posts published in that period.
**Validates: Requirements 7.1**

### Property 32: Publication Recording
*For any* published post, the system should record the publication time and status.
**Validates: Requirements 7.2**

### Property 33: Channel Report Accuracy
*For any* channel, the report should include accurate statistics for that channel only.
**Validates: Requirements 7.3**

### Property 34: Error Logging
*For any* publication error, the error should be logged with timestamp and error details.
**Validates: Requirements 7.4**

### Property 35: Success Rate Tracking
*For any* channel, the system should track the ratio of successful to failed publications.
**Validates: Requirements 7.5**

### Property 36: Admin Authorization
*For any* admin command, the system should verify that the user is an authorized administrator.
**Validates: Requirements 8.1**

### Property 37: Command Execution
*For any* valid command, the system should execute the corresponding action.
**Validates: Requirements 8.2**

### Property 38: Parameter Request
*For any* command missing required parameters, the system should prompt for the missing data.
**Validates: Requirements 8.3**

### Property 39: Command Confirmation
*For any* successfully executed command, the system should send a confirmation message.
**Validates: Requirements 8.4**

### Property 40: Inline Button Support
*For any* menu or interface, inline buttons should be properly formatted and functional.
**Validates: Requirements 8.5**

### Property 41: Retry Logic
*For any* failed publication, the system should retry up to the configured maximum number of attempts.
**Validates: Requirements 9.1**

### Property 42: Retry Limit Notification
*For any* publication that fails after maximum retries, an admin notification should be sent.
**Validates: Requirements 9.2**

### Property 43: Channel Suspension
*For any* channel that becomes unavailable, publications to that channel should be paused.
**Validates: Requirements 9.3**

### Property 44: Permission Loss Notification
*For any* channel where the bot loses permissions, an admin notification should be sent.
**Validates: Requirements 9.4**

### Property 45: Error Log Completeness
*For any* error that occurs, it should be logged with sufficient detail for debugging.
**Validates: Requirements 9.5**

### Property 46: Content Length Control
*For any* specified content length, the generated content should approximately match that length.
**Validates: Requirements 10.1**

### Property 47: Tone Application
*For any* specified tone, the generated content should reflect that tone in its language and style.
**Validates: Requirements 10.2**

### Property 48: Keyword Inclusion
*For any* set of keywords, all keywords should appear in the generated content.
**Validates: Requirements 10.3**

### Property 49: Language Consistency
*For any* specified language, all generated content should be in that language.
**Validates: Requirements 10.4**

### Property 50: Template Prompt Usage
*For any* content type, the system should use the appropriate prompt template for that type.
**Validates: Requirements 10.5**

## Error Handling

### Error Categories

1. **Telegram API Errors**
   - Rate limiting
   - Permission errors
   - Network timeouts
   - Invalid channel IDs

2. **LLM Generation Errors**
   - API failures
   - Timeout errors
   - Invalid responses
   - Rate limits

3. **Database Errors**
   - Connection failures
   - Query errors
   - Data integrity violations

4. **Scheduling Errors**
   - Invalid cron expressions
   - Timezone issues
   - Overlapping schedules

### Error Handling Strategy

```python
class ErrorHandler:
    async def handle_telegram_error(self, error: TelegramError) -> ErrorAction
    async def handle_llm_error(self, error: LLMError) -> ErrorAction
    async def handle_database_error(self, error: DatabaseError) -> ErrorAction
    async def notify_admin(self, error: Error, context: dict) -> None
```

### Retry Strategy

- **Exponential Backoff**: 2^n seconds (max 5 retries)
- **Circuit Breaker**: Pause channel after 3 consecutive failures
- **Fallback**: Use cached content or skip publication

## Testing Strategy

### Unit Testing

**Test Coverage:**
- Channel management operations
- Content generation with mocked LLM
- Schedule parsing and validation
- Queue operations
- Permission checking logic

**Example Unit Tests:**
```python
def test_add_channel_creates_unique_id()
def test_schedule_validates_time_slots()
def test_queue_maintains_priority_order()
def test_permission_check_detects_missing_rights()
```

### Property-Based Testing

**Framework**: Use `hypothesis` for Python property-based testing

**Configuration**: Each property test should run minimum 100 iterations

**Property Test Examples:**
```python
# Property 1: Channel Registration Uniqueness
@given(channel_id=integers(), config=channel_configs())
async def test_channel_registration_uniqueness(channel_id, config):
    """
    Feature: auto-posting-bot, Property 1: Channel Registration Uniqueness
    """
    channel = await channel_manager.add_channel(channel_id, config)
    retrieved = await channel_manager.get_channel(channel_id)
    assert retrieved is not None
    assert retrieved.id == channel_id

# Property 8: Random Interval Bounds
@given(
    min_interval=integers(min_value=1, max_value=60),
    max_interval=integers(min_value=61, max_value=120)
)
async def test_random_interval_bounds(min_interval, max_interval):
    """
    Feature: auto-posting-bot, Property 8: Random Interval Bounds
    """
    schedule = ScheduleConfig(
        mode=ScheduleMode.RANDOM,
        random_range=(min_interval, max_interval)
    )
    for _ in range(100):
        next_time = scheduler.calculate_next_run(schedule)
        interval = (next_time - datetime.now()).total_seconds() / 60
        assert min_interval <= interval <= max_interval
```

### Integration Testing

**Test Scenarios:**
- End-to-end post creation and publication
- Multi-channel scheduling
- Error recovery and retry logic
- Admin command workflows

### Testing Requirements

- Property-based tests MUST be tagged with: `**Feature: auto-posting-bot, Property {number}: {property_text}**`
- Each correctness property MUST be implemented by a SINGLE property-based test
- Property tests MUST run minimum 100 iterations
- Unit tests complement property tests by covering specific examples and edge cases

## Security Considerations

1. **Admin Authorization**: All admin commands must verify user ID against admin list
2. **Channel Permissions**: Verify bot has necessary permissions before operations
3. **Input Validation**: Sanitize all user inputs to prevent injection attacks
4. **Rate Limiting**: Implement rate limiting for API calls and user actions
5. **Secure Storage**: Store sensitive data (API keys) encrypted

## Performance Considerations

1. **Async Operations**: All I/O operations should be asynchronous
2. **Connection Pooling**: Use connection pools for database and HTTP clients
3. **Caching**: Cache channel settings and frequently accessed data
4. **Batch Operations**: Batch database writes when possible
5. **Resource Limits**: Set limits on queue size and concurrent operations

## Deployment

### Environment Variables
```
TELEGRAM_BOT_TOKEN=<bot_token>
ADMIN_IDS=<comma_separated_ids>
DATABASE_URL=<database_connection_string>
LLM_PROVIDER=groq
GROQ_API_KEY=<api_key>
MAX_RETRIES=3
RETRY_DELAY=5
```

### Database Schema
```sql
CREATE TABLE channels (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    settings JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE posts (
    id TEXT PRIMARY KEY,
    channel_id INTEGER,
    content TEXT,
    status TEXT,
    scheduled_for TIMESTAMP,
    published_at TIMESTAMP,
    FOREIGN KEY (channel_id) REFERENCES channels(id)
);

CREATE TABLE schedules (
    id TEXT PRIMARY KEY,
    channel_id INTEGER,
    config JSON,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (channel_id) REFERENCES channels(id)
);

CREATE TABLE publications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id INTEGER,
    post_id TEXT,
    status TEXT,
    published_at TIMESTAMP,
    error_message TEXT,
    FOREIGN KEY (channel_id) REFERENCES channels(id)
);
```

## Future Enhancements

1. **AI-Powered Analytics**: Use ML to optimize posting times
2. **Multi-Language Support**: Automatic translation for multiple languages
3. **Content Recommendations**: AI suggestions for trending topics
4. **A/B Testing**: Test different content styles and measure engagement
5. **Advanced Scheduling**: ML-based optimal time prediction
