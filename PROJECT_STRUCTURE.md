# Project Structure

Complete file structure of AI Content Bot project.

## Root Directory

```
telegram/
├── 📄 Configuration Files
│   ├── .env                      # Environment variables (your secrets)
│   ├── .env.example              # Environment template
│   ├── .gitignore                # Git ignore rules
│   ├── alembic.ini               # Database migration config
│   ├── docker-compose.yml        # Docker orchestration
│   ├── Dockerfile                # Docker image definition
│   ├── prometheus.yml            # Monitoring configuration
│   ├── requirements.txt          # Python dependencies
│   ├── requirements-dev.txt      # Development dependencies
│   └── Makefile                  # Build automation
│
├── 📚 Documentation
│   ├── README.md                 # Main documentation
│   ├── START.md                  # Quick start guide
│   ├── QUICKSTART.md             # Detailed usage guide
│   ├── DEPLOYMENT.md             # Production deployment
│   ├── TESTING.md                # Testing guide
│   ├── FAQ.md                    # Frequently asked questions
│   ├── EXAMPLES.md               # Usage examples
│   ├── CHEATSHEET.md             # Quick reference
│   ├── CONTRIBUTING.md           # Contribution guidelines
│   ├── CHANGELOG.md              # Version history
│   ├── PROJECT_SUMMARY.md        # Technical overview
│   ├── PROJECT_STATUS.md         # Implementation status
│   ├── PROJECT_STRUCTURE.md      # This file
│   └── LICENSE                   # MIT License
│
├── 🛠️ Utility Scripts
│   ├── run.py                    # Quick start script
│   ├── run.py                      # Quick start script (polling mode)
├── run.bat                   # Windows batch script
│   ├── check_setup.py            # Setup verification
│   └── init_db.py                # Database initialization
│
├── 📁 Source Code (src/)
├── 🧪 Tests (tests/)
├── ⚙️ Kiro Config (.kiro/)
└── 🔧 Git (.git/)
```

## Source Code Structure (src/)

```
src/
├── __init__.py                   # Package initialization
├── main.py                       # Application entry point
├── config.py                     # Configuration management
├── cache.py                      # Redis caching utilities
├── tasks.py                      # Celery background tasks
├── logging_config.py             # Logging configuration
├── monitoring.py                 # Prometheus monitoring
│
├── 🤖 bot/                       # Telegram Bot Layer
│   ├── __init__.py
│   └── controller.py             # Bot commands and handlers
│
├── 🎨 interface/                 # User Interface Layer
│   ├── __init__.py
│   ├── keyboard_builder.py       # Inline keyboard creation
│   ├── callback_router.py        # Button click routing
│   ├── menu_system.py            # Menu navigation logic
│   ├── message_formatter.py      # Message formatting
│   ├── channel_interface.py      # Channel management UI
│   ├── content_interface.py      # Content generation UI
│   ├── analytics_interface.py    # Analytics dashboard UI
│   ├── settings_interface.py     # Settings configuration UI
│   ├── schedule_interface.py     # Scheduling UI
│   ├── conversation_manager.py   # Multi-step conversations
│   └── validators.py             # Input validation
│
├── 💼 services/                  # Business Logic Layer
│   ├── __init__.py
│   ├── content_generator.py      # AI content generation
│   ├── content_optimizer.py      # Content enhancement
│   ├── scheduler_service.py      # Post scheduling
│   ├── channel_manager.py        # Channel operations
│   ├── publishing_service.py     # Post publishing
│   ├── analytics_engine.py       # Performance analytics
│   ├── quality_control.py        # Content validation
│   ├── error_handler.py          # Error handling
│   ├── state_manager.py          # Session & navigation state
│   ├── rate_limiter.py           # Rate limiting
│   └── settings_storage.py       # Settings persistence
│
├── 🗄️ models/                    # Database Models
│   ├── __init__.py
│   ├── base.py                   # Base model class
│   ├── channel.py                # Channel model
│   ├── post.py                   # Post model
│   └── metrics.py                # Metrics model
│
└── 📊 repositories/              # Data Access Layer
    ├── __init__.py
    ├── channel_repository.py     # Channel data access
    ├── post_repository.py        # Post data access
    └── metrics_repository.py     # Metrics data access
```

## Tests Structure (tests/)

```
tests/
├── __init__.py                   # Test package init
├── conftest.py                   # Pytest configuration (to be added)
├── test_content_generator.py    # Content generation tests (to be added)
├── test_scheduler.py             # Scheduling tests (to be added)
└── test_analytics.py             # Analytics tests (to be added)
```

## Kiro Configuration (.kiro/)

```
.kiro/
├── specs/                        # Feature specifications
│   └── ai-content-bot/
│       ├── requirements.md       # Requirements document
│       ├── design.md             # Design document
│       └── tasks.md              # Implementation tasks
│
├── steering/                     # Steering rules (guidance)
│   ├── webhooks.md
│   ├── security.md
│   ├── testing.md
│   └── ... (many more)
│
├── hooks/                        # Agent hooks
└── settings/                     # Kiro settings
```

## File Descriptions

### Configuration Files

| File | Purpose |
|------|---------|
| `.env` | Your secret configuration (tokens, API keys) |
| `.env.example` | Template for environment variables |
| `.gitignore` | Files to exclude from version control |
| `alembic.ini` | Database migration configuration |
| `docker-compose.yml` | Multi-container Docker application |
| `Dockerfile` | Docker image build instructions |
| `prometheus.yml` | Monitoring and metrics configuration |
| `requirements.txt` | Python production dependencies |
| `requirements-dev.txt` | Python development dependencies |
| `Makefile` | Automation commands (install, run, test) |

### Documentation Files

| File | Purpose |
|------|---------|
| `README.md` | Main project documentation |
| `START.md` | Quick start guide (5 minutes) |
| `QUICKSTART.md` | Detailed usage guide |
| `DEPLOYMENT.md` | Production deployment instructions |
| `TESTING.md` | Testing guide and checklist |
| `FAQ.md` | Frequently asked questions |
| `EXAMPLES.md` | Real-world usage examples |
| `CHEATSHEET.md` | Quick command reference |
| `CONTRIBUTING.md` | How to contribute to the project |
| `CHANGELOG.md` | Version history and changes |
| `PROJECT_SUMMARY.md` | Technical architecture overview |
| `PROJECT_STATUS.md` | Implementation status |
| `LICENSE` | MIT License terms |

### Utility Scripts

| File | Purpose |
|------|---------|
| `run.py` | Quick start script for the bot |
| `run.bat` | Windows batch script for easy startup |
| `check_setup.py` | Verify installation and configuration |
| `init_db.py` | Initialize database with tables |

### Source Code Files

#### Core Application
- `src/main.py` - Application entry point, starts the bot
- `src/config.py` - Configuration management with validation
- `src/cache.py` - Redis caching utilities
- `src/tasks.py` - Celery background tasks
- `src/logging_config.py` - Logging setup
- `src/monitoring.py` - Prometheus metrics

#### Bot Layer
- `src/bot/controller.py` - Telegram bot commands and handlers

#### Interface Layer
- `src/interface/keyboard_builder.py` - Inline keyboard creation
- `src/interface/callback_router.py` - Button click routing with pattern matching
- `src/interface/menu_system.py` - Menu navigation and display logic
- `src/interface/message_formatter.py` - Consistent message formatting

#### Services (Business Logic)
- `src/services/content_generator.py` - AI-powered content creation
- `src/services/content_optimizer.py` - Content enhancement and optimization
- `src/services/scheduler_service.py` - Intelligent post scheduling
- `src/services/channel_manager.py` - Multi-channel management
- `src/services/publishing_service.py` - Reliable post publishing
- `src/services/analytics_engine.py` - Performance tracking
- `src/services/quality_control.py` - Content validation
- `src/services/error_handler.py` - Error handling and recovery
- `src/services/state_manager.py` - User session and navigation state management
- `src/services/rate_limiter.py` - Rate limiting and throttling
- `src/services/settings_storage.py` - User settings persistence

#### Models (Database)
- `src/models/base.py` - Base model with common functionality
- `src/models/channel.py` - Channel data model
- `src/models/post.py` - Post data model
- `src/models/metrics.py` - Metrics data model

#### Repositories (Data Access)
- `src/repositories/channel_repository.py` - Channel database operations
- `src/repositories/post_repository.py` - Post database operations
- `src/repositories/metrics_repository.py` - Metrics database operations

## File Count Summary

| Category | Count |
|----------|-------|
| Documentation | 13 files |
| Configuration | 10 files |
| Source Code | 27 files |
| Utility Scripts | 4 files |
| Tests | 1 file (more to be added) |
| **Total** | **55+ files** |

## Lines of Code

| Component | Approximate LOC |
|-----------|----------------|
| Services | ~2,000 |
| Models & Repositories | ~800 |
| Bot Controller | ~500 |
| Interface Layer | ~600 |
| Configuration & Utils | ~400 |
| Documentation | ~3,000 |
| **Total** | **~7,300+ lines** |

## Key Directories

### Production Code
- `src/` - All application source code
- `src/bot/` - Telegram bot interface
- `src/interface/` - User interface components (keyboards, menus, routing)
- `src/services/` - Core business logic
- `src/models/` - Database models
- `src/repositories/` - Data access layer

### Configuration
- `.kiro/` - Kiro AI assistant configuration
- `.kiro/specs/` - Feature specifications
- `.kiro/steering/` - Development guidance

### Infrastructure
- Docker files for containerization
- Prometheus for monitoring
- Alembic for database migrations

## Dependencies

### Production Dependencies (requirements.txt)
- `python-telegram-bot` - Telegram Bot API
- `groq` - Groq AI API client
- `sqlalchemy` - Database ORM
- `asyncpg` - PostgreSQL async driver
- `redis` - Redis client
- `celery` - Task queue
- `prometheus-client` - Metrics
- `python-dotenv` - Environment variables
- `aiohttp` - Async HTTP client

### Development Dependencies (requirements-dev.txt)
- `pytest` - Testing framework
- `pytest-asyncio` - Async test support
- `pytest-cov` - Code coverage
- `black` - Code formatter
- `flake8` - Linter
- `mypy` - Type checker
- `isort` - Import sorter

## Database Schema

### Tables
1. **channels** - Channel information
   - id, telegram_id, name, category, settings, etc.

2. **posts** - Generated posts
   - id, channel_id, title, content, status, etc.

3. **metrics** - Performance metrics
   - id, channel_id, post_id, views, engagement, etc.

## Docker Services

When running with Docker Compose:

1. **bot** - Main bot application
2. **db** - PostgreSQL database
3. **redis** - Redis cache
4. **celery** - Background worker
5. **prometheus** - Monitoring (optional)

## Environment Variables

See `.env.example` for complete list. Key variables:

- `TELEGRAM_BOT_TOKEN` - Bot authentication
- `GROQ_API_KEY` - AI API access
- `ADMIN_IDS` - Admin user IDs
- `DATABASE_URL` - Database connection
- `REDIS_URL` - Redis connection

## Next Steps

1. **For Users**: Start with [START.md](START.md)
2. **For Developers**: Read [CONTRIBUTING.md](CONTRIBUTING.md)
3. **For Deployment**: Follow [DEPLOYMENT.md](DEPLOYMENT.md)

---

**Last Updated**: 2024-01-XX  
**Project Version**: 1.0.0  
**Total Files**: 51+  
**Total Lines**: 6,700+
