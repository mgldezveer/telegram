# AI Content Bot - Cheat Sheet

## Quick Commands

### Setup
```bash
python check_setup.py          # Check configuration
python init_db.py               # Initialize database
python run.py                   # Start bot (quick start)
```

### Windows Quick Start
```bash
run.bat                         # Does everything automatically
```

### Make Commands
```bash
make check                      # Check setup
make init                       # Init database
make run                        # Run bot
make clean                      # Clean temp files
```

## Bot Commands

### Basic
```
/start                          # Start bot
/help                           # Show help
/status                         # Bot status
```

### Channel Management
```
/add_channel @channel tech      # Add channel with category
/list_channels                  # List all channels
/remove_channel 1               # Remove channel by ID
```

### Content Generation
```
/generate tech "AI trends"      # Generate English content
/generate tech "Тренды ИИ"      # Generate Russian content
/generate_batch tech 5          # Generate 5 posts
```

### Scheduling
```
/schedule 1 14:00               # Schedule for today 14:00
/schedule 1 tomorrow 10:00      # Schedule for tomorrow
/schedule 1 +2h                 # Schedule in 2 hours
/list_scheduled                 # List scheduled posts
```

### Analytics
```
/analytics 1                    # Channel analytics
/stats                          # Bot statistics
/top_posts 1                    # Top posts for channel
```

### Admin
```
/config frequency 3             # Set posting frequency
/config timezone UTC            # Set timezone
/theme AI and technology        # Set content theme
/broadcast "message"            # Send to all channels
```

## Configuration (.env)

### Required
```bash
TELEGRAM_BOT_TOKEN=your_token
GROQ_API_KEY=your_key
ADMIN_IDS=your_user_id
```

### Optional
```bash
AI_MODEL=qwen-2.5-72b-instruct
AI_TEMPERATURE=0.7
DATABASE_URL=sqlite:///bot.db
REDIS_URL=redis://localhost:6379/0
LOG_LEVEL=INFO
```

## Database Queries

### SQLite
```bash
# View channels
sqlite3 bot.db "SELECT * FROM channels;"

# View posts
sqlite3 bot.db "SELECT id, title, status FROM posts;"

# View metrics
sqlite3 bot.db "SELECT * FROM metrics ORDER BY created_at DESC LIMIT 10;"

# Delete channel
sqlite3 bot.db "DELETE FROM channels WHERE id=1;"
```

## Docker Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f bot

# Restart bot
docker-compose restart bot

# Stop all
docker-compose down

# Rebuild
docker-compose up -d --build
```

## Monitoring

### Health Check
```bash
curl http://localhost:9090/health
```

### Metrics
```bash
curl http://localhost:9090/metrics
```

### Logs
```bash
# Docker
docker-compose logs -f bot

# Local
tail -f bot.log
```

## Troubleshooting

### Bot not responding
```bash
# Check if running
ps aux | grep python

# Check logs
docker-compose logs bot

# Restart
docker-compose restart bot
```

### Database issues
```bash
# Reinitialize
python init_db.py

# Or delete and recreate
rm bot.db
python init_db.py
```

### AI generation fails
```bash
# Check API key
echo $GROQ_API_KEY

# Test API
curl https://api.groq.com/openai/v1/models \
  -H "Authorization: Bearer $GROQ_API_KEY"
```

## Common Workflows

### Add Channel and Generate Content
```
1. /add_channel @mychannel tech
2. /generate tech "Latest AI news"
3. /schedule 1 14:00
```

### Batch Content Generation
```
1. /generate_batch tech 10
2. /list_scheduled
3. /analytics 1
```

### Daily Routine
```
1. /status                      # Check bot health
2. /analytics 1                 # Check performance
3. /generate_batch tech 3       # Generate daily content
4. Schedule posts throughout day
```

## File Structure

```
telegram/
├── src/
│   ├── bot/controller.py       # Bot commands
│   ├── services/               # Business logic
│   ├── models/                 # Database models
│   └── config.py               # Configuration
├── .env                        # Your config
├── run.py                      # Start script
├── check_setup.py              # Setup checker
└── init_db.py                  # DB initializer
```

## API Endpoints

### Groq API
```python
# Models
qwen-2.5-72b-instruct          # Best quality
llama-3.1-70b-versatile        # Fast
mixtral-8x7b-32768             # Long context
```

### Telegram Bot API
```
https://api.telegram.org/bot<TOKEN>/METHOD
```

## Python Quick Reference

### Import Bot
```python
from src.bot.controller import TelegramBot
from src.config import config
```

### Generate Content Programmatically
```python
from src.services.content_generator import ContentGenerator

generator = ContentGenerator()
content = await generator.generate_content(
    category="tech",
    topic="AI trends"
)
```

### Access Database
```python
from src.repositories.channel_repository import ChannelRepository

repo = ChannelRepository()
channels = await repo.get_all()
```

## Environment Variables

```bash
# Set temporarily (Linux/Mac)
export TELEGRAM_BOT_TOKEN="your_token"

# Set temporarily (Windows)
set TELEGRAM_BOT_TOKEN=your_token

# Set permanently - add to .env file
```

## Testing

### Quick Test
```bash
python check_setup.py
```

### Full Test
```bash
pytest tests/ -v
```

### Test Coverage
```bash
pytest --cov=src --cov-report=html
```

## Performance Tips

1. **Use Redis** for caching
2. **Use PostgreSQL** for production
3. **Enable Celery** for background tasks
4. **Set up monitoring** with Prometheus
5. **Use webhook** instead of polling

## Security Checklist

- [ ] Change default passwords
- [ ] Use environment variables for secrets
- [ ] Enable HTTPS for webhook
- [ ] Restrict admin access
- [ ] Regular backups
- [ ] Update dependencies
- [ ] Monitor logs

## Useful Links

- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Groq Documentation](https://console.groq.com/docs)
- [Python Telegram Bot](https://python-telegram-bot.org/)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org/)

## Quick Fixes

### Reset Everything
```bash
docker-compose down -v
rm bot.db
python init_db.py
docker-compose up -d
```

### Update Bot
```bash
git pull
pip install -r requirements.txt
docker-compose up -d --build
```

### Backup Database
```bash
# SQLite
cp bot.db bot.db.backup

# PostgreSQL
docker-compose exec db pg_dump -U botuser ai_content_bot > backup.sql
```

---

**Pro Tip:** Keep this file open in a separate terminal for quick reference! 🚀
