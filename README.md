# AI Content Bot for Telegram

> 🇷🇺 [Русская версия](БЫСТРЫЙ_СТАРТ.md) | 🇬🇧 English version below

An AI-powered Telegram bot that automates channel management and content creation. The bot autonomously generates, optimizes, and publishes high-quality posts to Telegram channels, ensuring consistent content delivery and stable operation.

## Features

- **Automated Content Generation**: AI-powered content creation using LLM APIs (OpenAI/Claude)
- **Interactive Bot Interface**: Intuitive button-based interface with inline keyboards and menus
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

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker and Docker Compose (for deployment)
- Telegram Bot Token (from @BotFather)
- Groq API Key (recommended) or OpenAI API Key

**Note for Windows users:** The bot automatically configures UTF-8 encoding for proper display of international characters (including Cyrillic) in logs and console output.

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

# Redis (Optional - defaults to localhost)
REDIS_URL=redis://localhost:6379/0
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

### 5. Test Bot Connection (Optional but Recommended)

```bash
# Quick test to verify bot token and connectivity
python test_bot.py
```

Send `/start` or `/test` to your bot in Telegram to confirm it's working.

### 6. Initialize Database

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

The callback routing system automatically handles button clicks and routes them to the appropriate handlers based on callback data patterns (e.g., `menu:main`, `channel:123:dashboard`, `quick:generate`).

**Implementation Status**: The interface is 100% complete (26/26 main tasks). All core components including menus, routing, formatting, pagination, channel management, content generation with post viewing/editing, analytics, settings, scheduling (fully integrated), and state management with automatic cleanup are fully functional and production-ready. Optional work includes comprehensive property-based testing.

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

### Quick Actions

From the main menu, you can:
- **⚡ Generate Now** - Instantly generate content with default settings
- **📊 View Status** - Check system status and resource usage
- **📊 Channels** - Manage your channels with interactive buttons
- **✍️ Content** - Create, schedule, and manage posts
- **📈 Analytics** - View performance metrics and reports
- **⚙️ Settings** - Configure bot behavior with interactive toggles

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
│   │   ├── handlers/       # Command and message handlers
│   │   ├── middleware/     # Middleware components
│   │   └── utils/          # Utility functions
│   ├── services/           # Business logic
│   │   ├── content_generator.py
│   │   ├── content_optimizer.py
│   │   ├── scheduler_service.py
│   │   ├── channel_manager.py
│   │   └── analytics_engine.py
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

## Troubleshooting

### Bot Not Responding

1. Check bot token is correct in `.env`
2. Verify bot is running: `docker-compose ps`
3. Check logs: `docker-compose logs bot`
4. Verify network connectivity

### Content Generation Failures

1. Check AI API status and rate limits
2. Verify API key validity
3. Review error logs for patterns
4. Check fallback provider configuration

### Publishing Delays

1. Check Telegram API status
2. Verify channel permissions
3. Review scheduler queue status
4. Check for rate limiting

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

### Technical Documentation
- 🚢 **[Deployment Guide](DEPLOYMENT.md)** - Production deployment instructions
- 🧪 **[Testing Guide](TESTING.md)** - How to test the bot thoroughly
- 📊 **[Project Summary](PROJECT_SUMMARY.md)** - Technical overview and architecture
- 📝 **[Specification](/.kiro/specs/ai-content-bot/)** - Complete spec documents (requirements, design, tasks)
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
