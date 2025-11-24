# Deployment Guidelines

## Deployment Options

### 1. Polling Mode (Simple)

Run bot continuously, polling for updates:

```python
app.run_polling()
```

Pros: Simple, works anywhere
Cons: Less efficient, requires constant connection

### 2. Webhook Mode (Production)

Receive updates via HTTP webhook:

```python
app.run_webhook(
    listen="0.0.0.0",
    port=8443,
    url_path="webhook",
    webhook_url=f"{WEBHOOK_URL}/webhook"
)
```

Pros: Efficient, scalable
Cons: Requires HTTPS, public URL

## Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  bot:
    build: .
    env_file: .env
    restart: unless-stopped
    depends_on:
      - db
  
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: botdb
      POSTGRES_USER: botuser
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

## Systemd Service (Linux)

```ini
# /etc/systemd/system/telegram-bot.service
[Unit]
Description=Telegram Bot
After=network.target

[Service]
Type=simple
User=botuser
WorkingDirectory=/opt/telegram-bot
Environment="PATH=/opt/telegram-bot/venv/bin"
ExecStart=/opt/telegram-bot/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## Health Checks

Implement health check endpoint:

```python
from aiohttp import web

async def health_check(request):
    return web.Response(text="OK", status=200)

app = web.Application()
app.router.add_get('/health', health_check)
```

## Monitoring

- Log all errors and exceptions
- Monitor bot uptime
- Track message processing time
- Set up alerts for failures
- Monitor resource usage (CPU, memory)

## Backup Strategy

- Regular database backups
- Store backups securely
- Test restore procedures
- Keep configuration in version control
