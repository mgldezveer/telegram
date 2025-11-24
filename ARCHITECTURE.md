# Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Telegram API                             │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Bot Controller                              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Command Handlers:                                        │  │
│  │  /start, /help, /add_channel, /generate, /schedule, etc. │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Service Layer                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Content    │  │   Content    │  │  Scheduler   │         │
│  │  Generator   │→ │  Optimizer   │→ │   Service    │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│         │                  │                  │                  │
│         ▼                  ▼                  ▼                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Channel    │  │  Publishing  │  │  Analytics   │         │
│  │   Manager    │  │   Service    │  │   Engine     │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│         │                  │                  │                  │
│         ▼                  ▼                  ▼                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Quality    │  │    Error     │  │              │         │
│  │   Control    │  │   Handler    │  │              │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Repository Layer                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Channel    │  │     Post     │  │   Metrics    │         │
│  │  Repository  │  │  Repository  │  │  Repository  │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Data Layer                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  PostgreSQL  │  │    Redis     │  │    Celery    │         │
│  │   Database   │  │    Cache     │  │  Task Queue  │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    External Services                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Groq API   │  │  Prometheus  │  │   Telegram   │         │
│  │  (Qwen 2.5)  │  │  Monitoring  │  │   Channels   │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

## Component Interaction Flow

### Content Generation Flow

```
User Command (/generate)
    │
    ▼
Bot Controller
    │
    ▼
Content Generator ──→ Groq API (AI)
    │                      │
    │◄─────────────────────┘
    ▼
Content Optimizer
    │
    ▼
Quality Control
    │
    ▼
Post Repository ──→ Database
    │
    ▼
Response to User
```

### Publishing Flow

```
Scheduled Time
    │
    ▼
Scheduler Service
    │
    ▼
Channel Manager ──→ Check Permissions
    │
    ▼
Publishing Service
    │
    ├──→ Telegram API ──→ Channel
    │         │
    │         ▼
    │    Success/Failure
    │         │
    ▼         ▼
Error Handler (if failed)
    │
    ├──→ Retry Logic
    │
    ▼
Analytics Engine ──→ Metrics Repository
```

## Data Flow

```
┌──────────┐
│   User   │
└────┬─────┘
     │ Commands
     ▼
┌──────────┐     ┌──────────┐     ┌──────────┐
│   Bot    │────→│ Services │────→│   Data   │
│Controller│     │  Layer   │     │  Layer   │
└────┬─────┘     └────┬─────┘     └────┬─────┘
     │                │                 │
     │ Responses      │ Results         │ Stored
     ▼                ▼                 ▼
┌──────────┐     ┌──────────┐     ┌──────────┐
│   User   │     │   Cache  │     │ Database │
└──────────┘     └──────────┘     └──────────┘
```

## Service Dependencies

```
Content Generator
    ├── Depends on: Groq API
    └── Used by: Bot Controller

Content Optimizer
    ├── Depends on: Content Generator
    └── Used by: Bot Controller

Scheduler Service
    ├── Depends on: Post Repository
    └── Used by: Celery Tasks

Channel Manager
    ├── Depends on: Channel Repository, async_session_maker
    ├── Uses: Repository pattern for data access
    └── Used by: Publishing Service, Bot Controller

Publishing Service
    ├── Depends on: Channel Manager, Telegram API
    └── Used by: Scheduler Service

Analytics Engine
    ├── Depends on: Metrics Repository
    └── Used by: Bot Controller

Quality Control
    ├── Depends on: Configuration
    └── Used by: Content Optimizer

Error Handler
    ├── Depends on: Logging
    └── Used by: All Services
```

## Database Schema

```
┌─────────────────┐
│    channels     │
├─────────────────┤
│ id (PK)         │
│ telegram_id     │
│ name            │
│ category        │
│ settings (JSON) │
│ active          │
│ created_at      │
│ updated_at      │
└────────┬────────┘
         │
         │ 1:N
         │
         ▼
┌─────────────────┐
│      posts      │
├─────────────────┤
│ id (PK)         │
│ channel_id (FK) │
│ title           │
│ content         │
│ hashtags        │
│ status          │
│ scheduled_time  │
│ published_at    │
│ created_at      │
└────────┬────────┘
         │
         │ 1:N
         │
         ▼
┌─────────────────┐
│     metrics     │
├─────────────────┤
│ id (PK)         │
│ channel_id (FK) │
│ post_id (FK)    │
│ views           │
│ reactions       │
│ engagement_rate │
│ created_at      │
└─────────────────┘
```

## Repository Pattern

The application uses the Repository pattern for data access, providing a clean separation between business logic and data access:

```
Service Layer (ChannelManager)
    │
    ▼
Repository Layer (ChannelRepository)
    │
    ├─→ get_all_active()
    ├─→ get_by_telegram_id()
    ├─→ create()
    ├─→ update()
    └─→ delete()
    │
    ▼
Database (SQLAlchemy ORM)
    │
    ▼
PostgreSQL/SQLite
```

**Benefits:**
- Separation of concerns
- Easier testing with mock repositories
- Consistent data access patterns
- Centralized query logic

## Technology Stack

### Backend
- **Language**: Python 3.11+
- **Framework**: python-telegram-bot v20+
- **ORM**: SQLAlchemy 2.0+
- **Async**: asyncio, aiohttp

### AI & ML
- **Provider**: Groq API
- **Model**: Qwen 2.5 72B Instruct
- **Alternative**: OpenAI GPT-4

### Data Storage
- **Database**: PostgreSQL 15+ (production) / SQLite (development)
- **Cache**: Redis 7+
- **Task Queue**: Celery with Redis broker

### Monitoring
- **Metrics**: Prometheus
- **Logging**: Python logging module
- **Health Checks**: Custom endpoints

### Deployment
- **Containerization**: Docker
- **Orchestration**: Docker Compose
- **Reverse Proxy**: Nginx (production)

## Scalability Considerations

### Horizontal Scaling
```
┌──────────┐     ┌──────────┐     ┌──────────┐
│  Bot 1   │     │  Bot 2   │     │  Bot 3   │
└────┬─────┘     └────┬─────┘     └────┬─────┘
     │                │                │
     └────────────────┼────────────────┘
                      │
                      ▼
              ┌──────────────┐
              │ Load Balancer│
              └──────┬───────┘
                     │
                     ▼
              ┌──────────────┐
              │   Database   │
              └──────────────┘
```

### Vertical Scaling
- Increase database connection pool
- Add more Celery workers
- Increase Redis memory
- Optimize queries with indexes

## Security Architecture

```
┌─────────────────────────────────────────┐
│         Security Layers                  │
├─────────────────────────────────────────┤
│ 1. Input Validation                     │
│    └─ Sanitize all user inputs          │
├─────────────────────────────────────────┤
│ 2. Authentication                       │
│    └─ Admin ID verification             │
├─────────────────────────────────────────┤
│ 3. Authorization                        │
│    └─ Command permission checks         │
├─────────────────────────────────────────┤
│ 4. Data Protection                      │
│    └─ Environment variables for secrets │
├─────────────────────────────────────────┤
│ 5. Rate Limiting                        │
│    └─ Prevent API abuse                 │
├─────────────────────────────────────────┤
│ 6. Error Handling                       │
│    └─ No sensitive data in errors       │
└─────────────────────────────────────────┘
```

## Deployment Architecture

### Development
```
Local Machine
    ├── Python Virtual Environment
    ├── SQLite Database
    ├── Redis (optional)
    └── Bot running in polling mode
```

### Production
```
Cloud Server (VPS/Cloud)
    ├── Docker Containers
    │   ├── Bot Container
    │   ├── PostgreSQL Container
    │   ├── Redis Container
    │   ├── Celery Worker Container
    │   └── Nginx Container
    ├── Webhook Mode
    ├── SSL/TLS Certificate
    └── Monitoring (Prometheus)
```

## Performance Optimization

### Caching Strategy
```
Request
    │
    ▼
Check Redis Cache
    │
    ├─→ Cache Hit ──→ Return Cached Data
    │
    └─→ Cache Miss
         │
         ▼
    Query Database
         │
         ▼
    Store in Cache
         │
         ▼
    Return Data
```

### Database Optimization
- Connection pooling (10 connections)
- Indexed columns (telegram_id, status, scheduled_time)
- Async queries with asyncpg
- Batch operations where possible

### API Rate Limiting
- Groq API: Respect rate limits
- Telegram API: Max 30 messages/second
- Retry with exponential backoff
- Queue management for bulk operations

## Monitoring & Observability

```
Application
    │
    ├──→ Logs ──→ File/Console
    │
    ├──→ Metrics ──→ Prometheus
    │                    │
    │                    ▼
    │               Grafana Dashboard
    │
    └──→ Health Checks ──→ /health endpoint
```

## Error Handling Strategy

```
Error Occurs
    │
    ▼
Error Handler
    │
    ├──→ Log Error (with context)
    │
    ├──→ Categorize Error
    │    ├─→ Recoverable
    │    │   └─→ Retry with backoff
    │    │
    │    └─→ Non-recoverable
    │        └─→ Alert admin
    │
    └──→ User-friendly message
```

## Future Architecture Enhancements

1. **Microservices**: Split into independent services
2. **Message Queue**: Add RabbitMQ for better task management
3. **CDN**: For media file distribution
4. **Load Balancer**: For multiple bot instances
5. **Database Replication**: Master-slave setup
6. **API Gateway**: Unified entry point
7. **Service Mesh**: For inter-service communication

---

**Architecture Version**: 1.0  
**Last Updated**: 2024-01-XX  
**Status**: Production Ready
