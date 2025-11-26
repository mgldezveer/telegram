# AI Content Bot for Telegram

> 🇷🇺 [Русская версия](БЫСТРЫЙ_СТАРТ.md) | 🇬🇧 English version below

An AI-powered Telegram bot that automates channel management and content creation. The bot autonomously generates, optimizes, and publishes high-quality posts to Telegram channels, ensuring consistent content delivery and stable operation.

## Features

- **Automated Content Generation**: AI-powered content creation using LLM APIs (OpenAI/Claude)
- **Interactive Bot Interface**: Intuitive button-based interface with inline keyboards and menus
- **Vibe Coding System**: Multi-role content generation with 6 specialized perspectives (Main Brain, PRD, Architect, Code, Debug, Child)
- **Content Optimization**: Automatic enhancement for engagement, readability, and hashtag generation
- **Intelligent Scheduling**: Optimal posting times based on audience activity patterns
- **Multi-Channel Management**: Handle multiple channels simultaneously with isolated queues
- **Performance Analytics**: Track views, reactions, and engagement metrics with reporting
- **Quality Control**: Content validation, brand consistency checks, and safety filters
- **Reliable Operation**: Error handling, retry logic, and graceful recovery mechanisms
- **Admin Controls**: Configuration commands and interactive menus for customizing bot behavior

## Architecture

The system follows a modular, event-driven architecture with these core components:

- **Bot Controller**: Main entry point, handles Telegram API interactions
- **Content Generation Engine**: AI-powered content creation
- **Content Optimizer**: Post enhancement and quality validation
- **Scheduler Service**: Intelligent posting time management
- **Channel Manager**: Multi-channel operations and permissions
- **Analytics Engine**: Performance tracking and reporting
- **State Manager**: User session and navigation state management
- **Storage Layer**: PostgreSQL for data, Redis for caching

## Technology Stack

- **Bot Framework**: python-telegram-bot (v20+)
- **AI Integration**: Groq API (Qwen 2.5 72B) or OpenAI API
- **Database**: PostgreSQL for structured data, Redis for caching
- **Task Queue**: Celery with Redis broker for background jobs
- **Scheduling**: APScheduler for time-based operations
- **Monitoring**: Prometheus metrics + Grafana dashboards
- **Deployment**: Docker + Docker Compose

## Prerequisites

- **Python 3.10+** (Python 3.11+ recommended, Python 3.9 and below are deprecated)
- PostgreSQL 15+ (optional, SQLite used by default)
- **Redis 7+** (optional but recommended for caching and performance)
- Docker and Docker Compose (for deployment)
- Telegram Bot Token (from @BotFather)
- Groq API Key (recommended) or OpenAI API Key

**Important Notes:**
- **Python Version:** Python 3.10 or higher is required. Python 3.9 and below are no longer supported. The bot validates your Python version at startup and displays clear warnings if an upgrade is needed.
- **Redis:** While optional, Redis is highly recommended for production use to enable response caching and reduce API costs. If Redis is unavailable, the bot automatically falls back to in-memory caching with automatic reconnection attempts.
- **Windows Users:** The bot automatically configures UTF-8 encoding for proper display of international characters (including Cyrillic) in logs and console output.

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/mgldezveer/telegram.git
cd telegram
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Bot Configuration (Required)
TELEGRAM_BOT_TOKEN=your_bot_token_here
ADMIN_IDS=123456789,987654321

# AI Provider (Required - choose one)
# For Groq (recommended - free tier available)
GROQ_API_KEY=your_groq_api_key
# OR for OpenAI
OPENAI_API_KEY=your_openai_api_key

# AI Model Configuration (Optional)
AI_MODEL=qwen-2.5-72b-instruct  # Default for Groq, or gpt-4 for OpenAI
AI_TEMPERATURE=0.7              # Range: 0.0-2.0, default: 0.7
AI_MAX_TOKENS=1000              # Default: 1000

# Database (Optional - defaults to SQLite)
DATABASE_URL=postgresql://user:password@localhost:5432/botdb
DB_POOL_SIZE=10                 # Default: 10
DB_ECHO=false                   # Set to true for SQL query logging

# Redis (Recommended for production)
# Redis is used for caching LLM responses and session management
# If Redis is unavailable, the bot will fall back to in-memory caching
REDIS_URL=redis://localhost:6379/0
REDIS_HOST=localhost            # Default: localhost
REDIS_PORT=6379                 # Default: 6379
REDIS_PASSWORD=                 # Optional: Redis password
REDIS_DB=0                      # Default: 0
REDIS_MAX_CONNECTIONS=50        # Default: 50

# Scheduling (Optional)
DEFAULT_POSTING_FREQUENCY=3     # Posts per day, default: 3
TIMEZONE=UTC                    # Default: UTC

# Webhook (Optional - for production)
WEBHOOK_URL=https://yourdomain.com

# Logging (Optional)
LOG_LEVEL=INFO                  # DEBUG, INFO, WARNING, ERROR, CRITICAL
DEBUG=false                     # Set to true for debug mode
```

### 5. Set Up Redis (Recommended)

Redis is optional but highly recommended for production use. It provides caching for LLM responses, reducing API costs and improving performance.

**Key Features:**
- ✅ Automatic fallback to in-memory cache if Redis is unavailable
- ✅ Automatic reconnection every 60 seconds when Redis becomes available
- ✅ Seamless data migration from memory to Redis on reconnect
- ✅ No downtime - bot continues working without Redis

**Windows:**
```bash
# Option 1: Using Chocolatey
choco install redis-64

# Option 2: Using WSL2
wsl --install
wsl
sudo apt-get update
sudo apt-get install redis-server
redis-server

# Option 3: Using Docker (Recommended)
docker run -d -p 6379:6379 --name redis redis:7-alpine
```

**Linux:**
```bash
sudo apt-get update
sudo apt-get install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

**macOS:**
```bash
brew install redis
brew services start redis
```

**Docker (All platforms):**
```bash
docker run -d -p 6379:6379 --name redis redis:7-alpine
```

**Verify Redis is running:**
```bash
redis-cli ping
# Should return: PONG
```

**What happens without Redis:**
- ⚠️ Bot uses in-memory cache (limited to 1000 entries)
- ⚠️ Cache is lost on restart
- ⚠️ Higher API costs (no persistent caching)
- ✅ Bot continues to function normally
- ✅ Automatic reconnection attempts every 60 seconds

For detailed Redis setup instructions, see [docs/REDIS_SETUP.md](docs/REDIS_SETUP.md).

### 6. Test Bot Connection (Optional but Recommended)

```bash
# Quick test to verify bot token and connectivity
python test_bot.py
```

Send `/start` or `/test` to your bot in Telegram to confirm it's working.

### 7. Initialize Database

```bash
# Initialize database tables
python init_db.py
```

## Usage

### Quick Test

Test bot connectivity first:

```bash
python test_bot.py
```

This lightweight script verifies your bot token and Telegram connection without requiring database or AI services.

### Development Mode

```bash
# Quick start (recommended)
python run.py

# Or directly
python -m src.main
```

### Production Deployment with Docker

```bash
docker-compose up -d
```

## Bot Interface

### Interactive Menus

The bot provides an intuitive button-based interface for easy management, implemented through five core components:

- **KeyboardBuilder** (`src/interface/keyboard_builder.py`): Creates inline and reply keyboards for all bot interactions
- **CallbackRouter** (`src/interface/callback_router.py`): Routes button clicks to appropriate handlers with pattern matching
- **MenuSystem** (`src/interface/menu_system.py`): Manages menu navigation and display logic
- **MessageFormatter** (`src/interface/message_formatter.py`): Formats messages with consistent styling and emojis
- **ChannelInterface** (`src/interface/channel_interface.py`): Handles channel management interactions (in progress)
- **VibeCodingInterface** (`src/interface/vibe_coding_interface.py`): Manages vibe coding menu and content generation

The callback routing system automatically handles button clicks and routes them to the appropriate handlers based on callback data patterns (e.g., `menu:main`, `channel:123:dashboard`, `quick:generate`, `vibe:full`, `vibe:role:main_brain`).

**Implementation Status**: ✅ **COMPLETE** - The interface is 100% functional and production-ready. All core components including menus, routing, formatting, pagination, channel management, content generation with post viewing/editing, analytics, settings, scheduling, and state management with automatic cleanup are fully implemented. Optional property-based testing tasks remain for enhanced test coverage.

#### Available Menus

- **Main Menu**: Quick access to Channels, Content, Analytics, and Settings
- **Channel Dashboard**: View and manage individual channels with one-tap actions
- **Content Generation**: Step-by-step content creation with preview and editing
- **Analytics View**: Visual performance metrics with emoji indicators
- **Settings Panel**: Interactive configuration with toggle buttons and presets

### Bot Commands

#### User Commands

- `/start` - Initialize the bot and show interactive main menu
- `/help` - Display available commands and usage information

#### Admin Commands

- `/status` - View current operational metrics and bot status
- `/config <setting> <value>` - Configure bot behavior (also available via Settings menu)
  - `frequency <number>` - Set posting frequency (posts per day)
  - `theme <theme>` - Specify content theme
- `/stop` - Emergency stop - pause all operations immediately

#### Auto-Posting Commands (Admin Only)

- `/autopost_add_channel <channel_id> <name>` - Add channel for auto-posting
- `/autopost_list_channels` - List all auto-posting channels
- `/autopost_generate <channel_id> <theme>` - Generate post for specific channel
- `/autopost_queue [channel_id]` - View post queue (optionally filtered by channel)
- `/autopost_schedule <channel_id> <time_slots>` - Add posting schedule (e.g., 09:00,15:00,21:00)
- `/autopost_help` - Show auto-posting help and available commands

### Quick Actions

From the main menu, you can:
- **⚡ Generate Now** - Instantly generate content with default settings
- **📊 View Status** - Check system status and resource usage
- **📊 Channels** - Manage your channels with interactive buttons
- **✍️ Content** - Create, schedule, and manage posts
- **📈 Analytics** - View performance metrics and reports
- **⚙️ Settings** - Configure bot behavior with interactive toggles
- **🎨 Vibe Coding** - Access multi-role content generation system

## Channel Management

### Adding a Channel

#### Via Interactive Menu (Recommended)
1. Send `/start` to open the main menu
2. Click **📊 Channels** button
3. Click **➕ Add Channel** button
4. Follow the step-by-step prompts to enter channel ID and name
5. The bot will confirm registration

#### Via Command
1. Add the bot as an administrator to your Telegram channel
2. Use `/register <channel_id> <name>` command
3. The bot will confirm registration

### Channel Dashboard

Each channel has an interactive dashboard showing:
- 📈 Real-time statistics (views, engagement, posts)
- ⚡ Quick actions (Create Post, Schedule, Configure, Analytics)
- 📊 Performance indicators with emoji feedback
- ⚙️ One-tap configuration access

### Channel Configuration

Configure channels through the interactive Settings menu or commands:
- Posting frequency and optimal times
- Content style and tone (professional, casual, humorous)
- Content themes
- Media preferences
- Quality thresholds
- Notification preferences

## Content Generation

### Interactive Content Creation

1. Click **✍️ Content** from the main menu
2. Select **Generate** to start content creation
3. Choose your target channel from the list
4. Select a theme or enter a custom topic
5. Preview the generated content
6. Choose to **Publish**, **Edit**, or **Discard**

The bot generates content based on:
- Configured themes and topics
- Channel-specific style guidelines
- Audience engagement patterns
- Brand consistency requirements

### Content Optimization

All generated content is automatically:
- Analyzed for readability and engagement potential
- Enhanced with relevant hashtags
- Validated for quality and appropriateness
- Checked for brand consistency

### Scheduling Posts

Use the interactive scheduler to plan content:
1. Navigate to **Content** → **Schedule**
2. View upcoming scheduled posts
3. Click **Add Schedule** to create new scheduled post
4. Select date and time with inline buttons
5. Choose channel and content
6. Confirm scheduling with preview

## Vibe Coding System

### What is Vibe Coding?

Vibe Coding is a multi-role content generation approach that creates comprehensive solutions by viewing problems through 6 specialized perspectives:

1. **🧠 Main Brain** - High-level vision and strategic goals
2. **📋 PRD** - Detailed product requirements and acceptance criteria
3. **🏗️ Architect** - Technical architecture and design patterns
4. **💻 Code** - Implementation and best practices
5. **🐛 Debug** - Testing, validation, and quality assurance
6. **👶 Child** - Simple explanations accessible to everyone

### Using Vibe Coding

Access the Vibe Coding menu from the main menu:

1. Click **🎨 Vibe Coding** button
2. Choose an option:
   - **🎯 Full Workflow** - Generate content from all 6 roles sequentially
   - **🧠 By Role** - Select a specific role for targeted generation
   - **✏️ Change Topic** - Switch between predefined topics or enter custom ones

### Available Topics

- 🤖 Telegram Bot Development
- 🌐 Web Application Development
- 📱 Mobile App Development
- 🎮 Game Development
- 🔧 API Service Development

For detailed guidance, see [Vibe Coding Guide](VIBE_CODING_GUIDE.md) and [Quick Start](VIBE_QUICK_START.md).

## Analytics and Monitoring

### Interactive Analytics Dashboard

Access analytics through the **📈 Analytics** menu:
1. Select a channel to view metrics
2. See performance indicators with emoji feedback:
   - 👁️ Views and reach
   - ❤️ Engagement rate
   - 📝 Total posts
   - 🔥 Top performing posts
3. Request detailed reports with one click
4. View trends and recommendations

### Performance Metrics

The bot tracks:
- Post views and reach
- Reactions and engagement rate
- Shares and comments
- Optimal posting times
- Content performance patterns

### Reports

Generate performance reports via:
- Interactive Analytics menu (recommended)
- `/status` command for quick system overview

Reports include visualizations and recommendations for improving content strategy.

## Error Handling

The bot implements robust error handling:

- **Retry Logic**: Exponential backoff for transient failures (up to 3 attempts)
- **Fallback Mechanisms**: Alternative AI providers, cached content
- **Graceful Recovery**: Automatic recovery from critical failures
- **Admin Notifications**: Immediate alerts for critical errors

## Testing

### Run Unit Tests

```bash
pytest tests/unit/
```

### Run Property-Based Tests

```bash
pytest tests/property/
```

### Run Integration Tests

```bash
pytest tests/integration/
```

### Check Code Coverage

```bash
pytest --cov=src --cov-report=html
```

## Monitoring

### Prometheus Metrics (Optional)

Access metrics at: `http://localhost:9090` (when monitoring is enabled)

**Note**: Monitoring is optional. The bot will run without it in development mode. If port 9090 is unavailable, the bot continues normally without metrics collection.

Key metrics (when enabled):
- Content generation latency
- Publishing success rate
- API error rates
- Database query performance
- Memory and CPU usage

To enable monitoring:
1. Ensure port 9090 is available
2. Set `MONITORING_PORT=9090` in `.env` (optional, defaults to 9090)
3. Restart the bot

### Grafana Dashboards (Optional)

Access dashboards at: `http://localhost:3000` (when configured)

Pre-configured dashboards for:
- Bot performance overview
- Content generation metrics
- Channel activity
- Error rates and alerts

## Project Structure

```
telegram-bot/
├── src/
│   ├── bot/
│   │   ├── controller.py   # Main bot controller with all integrations
│   │   ├── handlers/       # Command and message handlers
│   │   ├── middleware/     # Middleware components
│   │   └── utils/          # Utility functions
│   ├── services/           # Business logic
│   │   ├── content_generator.py
│   │   ├── content_optimizer.py
│   │   ├── scheduler_service.py
│   │   ├── channel_manager.py
│   │   ├── analytics_engine.py
│   │   └── vibe_coding_engine.py  # Vibe coding system
│   ├── interface/          # User interface components
│   │   ├── menu_system.py
│   │   ├── callback_router.py
│   │   ├── channel_interface.py
│   │   ├── content_interface.py
│   │   ├── analytics_interface.py
│   │   ├── settings_interface.py
│   │   ├── schedule_interface.py
│   │   └── vibe_coding_interface.py  # Vibe coding UI
│   ├── models/             # Data models
│   └── config.py           # Configuration
├── tests/
│   ├── unit/
│   ├── property/
│   └── integration/
├── docs/
├── .env.example
├── requirements.txt
├── docker-compose.yml
├── VIBE_CODING_GUIDE.md    # Vibe coding documentation
├── VIBE_QUICK_START.md     # Vibe coding quick start
└── main.py
```

## Security

- API keys stored in environment variables
- Admin-only commands require authentication
- Content moderation before publishing
- Rate limiting on configuration changes
- Encrypted database connections

## Backup and Maintenance

### Automated Backups

Daily database backups are configured automatically. Backups are retained for 30 days.

### Manual Backup

```bash
pg_dump -h localhost -U username -d botdb -f backup.sql
```

### Restore from Backup

```bash
psql -h localhost -U username -d botdb -f backup.sql
```

## Health Monitoring

The bot provides a comprehensive health check endpoint to monitor system status:

```bash
# Check overall health
curl http://localhost:9090/health

# Response includes:
# - Bot status
# - Database connectivity
# - Redis connectivity (connected/fallback mode)
# - Cache mode (redis/memory)
# - Python version
# - Uptime
# - Component health details
```

**Health Check Response Example (Redis Connected):**
```json
{
  "status": "healthy",
  "bot": "running",
  "database": "connected",
  "redis": "connected",
  "cache_mode": "redis",
  "python_version": "3.11.0",
  "uptime_seconds": 3600,
  "components": {
    "cache": {
      "status": "healthy",
      "type": "redis",
      "connected": true
    }
  }
}
```

**Health Check Response Example (Redis Unavailable):**
```json
{
  "status": "healthy",
  "bot": "running",
  "database": "connected",
  "redis": "disconnected",
  "cache_mode": "memory",
  "python_version": "3.11.0",
  "uptime_seconds": 3600,
  "components": {
    "cache": {
      "status": "degraded",
      "type": "memory",
      "connected": false,
      "reconnection_active": true
    }
  }
}
```

**Cache Status Indicators:**
- `redis` - Using Redis cache (optimal performance)
- `memory` - Using in-memory fallback cache (reduced performance)
- `reconnection_active` - Attempting to reconnect to Redis every 60 seconds

## Troubleshooting

### Python Version Warnings

**Warning:** "⚠️ Python 3.9 is deprecated. Please upgrade to Python 3.10 or higher for continued support."

**What this means:**
- Python 3.9 reached end-of-life and no longer receives security updates
- Some dependencies require Python 3.10+
- The bot will still run but with reduced support

**Solution:**
1. Check your Python version: `python --version`
2. Upgrade to Python 3.10, 3.11, or 3.12 (recommended)
3. Recreate virtual environment with new Python version:
   ```bash
   rm -rf venv
   python3.11 -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   pip install -r requirements.txt
   ```

**Supported Python Versions:**
- ✅ Python 3.12 - Fully supported (latest)
- ✅ Python 3.11 - Fully supported (recommended)
- ✅ Python 3.10 - Fully supported
- ⚠️ Python 3.9 - Deprecated (warning shown)
- ❌ Python 3.8 and below - Not supported

### Redis Connection Issues

**Warning:** "⚠️ Failed to connect to Redis. Using fallback in-memory cache. Will retry connection every 60 seconds."

**What this means:**
- Redis is not available or not configured
- Bot automatically switched to in-memory cache
- Bot will attempt to reconnect every 60 seconds
- No manual intervention required

**Causes and Solutions:**

1. **Redis not installed:**
   - Install Redis following the setup instructions above
   - Verify installation: `redis-cli ping`
   - See [docs/REDIS_SETUP.md](docs/REDIS_SETUP.md) for detailed guide

2. **Redis not running:**
   - Start Redis: `redis-server` (or `sudo systemctl start redis-server` on Linux)
   - Check status: `redis-cli ping` (should return PONG)
   - For Docker: `docker start redis`

3. **Wrong connection parameters:**
   - Verify `REDIS_URL` in `.env` file
   - Check host, port, and password settings
   - Default: `redis://localhost:6379/0`
   - Test connection: `redis-cli -h localhost -p 6379 ping`

4. **Firewall blocking connection:**
   - Check firewall rules
   - Ensure port 6379 is accessible
   - For Windows: Add firewall rule for port 6379

**Impact of running without Redis:**
- ⚠️ In-memory cache limited to 1000 entries (vs unlimited with Redis)
- ⚠️ Cache cleared on bot restart
- ⚠️ Higher API costs (no persistent caching)
- ⚠️ Slightly slower performance
- ✅ Bot continues to function normally
- ✅ Automatic reconnection when Redis becomes available
- ✅ Seamless migration from memory to Redis cache

**Monitoring Redis Status:**
```bash
# Check health endpoint
curl http://localhost:9090/health

# Look for:
# "cache_mode": "redis" (connected) or "memory" (fallback)
# "reconnection_active": true (attempting to reconnect)
```

### ConversationHandler Warnings

**Warning:** "PTBUserWarning: If 'per_message=False', 'CallbackQueryHandler' will not be tracked..."

**Status:** ✅ **RESOLVED** - This warning has been eliminated in the latest version.

**What was fixed:**
- Implemented automatic detection of CallbackQueryHandler in conversations
- All ConversationHandlers now use proper `per_message=True` configuration
- Factory pattern ensures consistent configuration across all handlers

**If you still see this warning:**
1. Update to the latest version: `git pull`
2. Restart the bot: `python run.py` or `docker-compose restart bot`
3. Check logs - warning should be gone
4. If warning persists, report as a bug

### Bot Not Responding

1. Check bot token is correct in `.env`
2. Verify Python version is 3.10 or higher
3. Verify bot is running: `docker-compose ps`
4. Check logs: `docker-compose logs bot`
5. Verify network connectivity
6. Check Redis connectivity (if using)

### Content Generation Failures

1. Check AI API status and rate limits
2. Verify API key validity
3. Review error logs for patterns
4. Check fallback provider configuration
5. Verify Redis cache is working (check health endpoint)

### Publishing Delays

1. Check Telegram API status
2. Verify channel permissions
3. Review scheduler queue status
4. Check for rate limiting
5. Verify Redis connectivity for queue management

## Contributing

See [CONTRIBUTING.md](.kiro/steering/contributing.md) for contribution guidelines.

## Documentation

- [Requirements](.kiro/specs/ai-content-bot/requirements.md) - Detailed requirements specification
- [Design](.kiro/specs/ai-content-bot/design.md) - Architecture and design documentation
- [Tasks](.kiro/specs/ai-content-bot/tasks.md) - Implementation plan and progress
- [Steering Guides](.kiro/steering/) - Development guidelines and best practices

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Open an issue on GitHub
- Contact administrators listed in ADMIN_IDS

## Roadmap

- [ ] Multi-language content generation
- [ ] Advanced analytics with ML-based insights
- [ ] Custom content templates
- [ ] Integration with additional AI providers
- [ ] Web-based admin dashboard
- [ ] A/B testing for content optimization


## 📚 Documentation

> 📝 **Documentation Status**: Actively maintained and expanding. User guides and troubleshooting documentation are being enhanced with detailed interface navigation flows.

### Getting Started
- 🚀 **[Quick Start Guide](START.md)** - Get up and running in 5 minutes
- 📖 **[Detailed Guide](QUICKSTART.md)** - Complete usage guide with examples
- 📋 **[Cheat Sheet](CHEATSHEET.md)** - Quick reference for all commands
- 🎯 **[What's Next?](WHATS_NEXT.md)** - Your roadmap after setup

### User Guides (🆕 Enhanced)
- 📚 **[User Guide](docs/USER_GUIDE.md)** - Comprehensive interface navigation guide (Russian)
- 🔧 **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common problems and solutions (Russian)
- 💡 **[Examples](EXAMPLES.md)** - Real-world usage examples and workflows
- ❓ **[FAQ](FAQ.md)** - Frequently asked questions

### Vibe Coding Documentation (🆕)
- 🎨 **[Vibe Coding Guide](VIBE_CODING_GUIDE.md)** - Complete guide to the vibe coding system (Russian)
- 🚀 **[Vibe Quick Start](VIBE_QUICK_START.md)** - Get started with vibe coding in minutes (Russian)
- 🧪 **[Demo Script](demo_vibe_coding.py)** - Interactive demonstration
- ✅ **[Integration Tests](test_vibe_integration.py)** - Verify vibe coding functionality

### Technical Documentation
- 🚢 **[Deployment Guide](DEPLOYMENT.md)** - Production deployment instructions
- 🧪 **[Testing Guide](TESTING.md)** - How to test the bot thoroughly
- 📊 **[Project Summary](PROJECT_SUMMARY.md)** - Technical overview and architecture
- 📝 **[Specification](/.kiro/specs/ai-content-bot/)** - Complete spec documents (requirements, design, tasks)
- 🏗️ **[Infrastructure Improvements](docs/INFRASTRUCTURE_IMPROVEMENTS.md)** - Redis caching, Python 3.10+, and performance enhancements
- 🔴 **[Redis Setup Guide](docs/REDIS_SETUP.md)** - Complete Redis installation and configuration guide
- 📚 **[Documentation Index](INDEX.md)** - Complete index of all documentation
- 🎉 **[Thank You](THANK_YOU.md)** - Completion message and next steps

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) - Telegram Bot API wrapper
- [Groq](https://groq.com/) - Fast AI inference
- [Qwen](https://github.com/QwenLM/Qwen) - Powerful language model

## 📞 Support

- 📖 Check the [FAQ](FAQ.md) for common questions
- 🐛 Report bugs via [GitHub Issues](https://github.com/mgldezveer/telegram/issues)
- 💬 Join our Telegram support group (coming soon)

---

Made with ❤️ for automated content creation
