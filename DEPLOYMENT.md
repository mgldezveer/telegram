# Руководство по развертыванию

## Быстрый старт с Docker

### 1. Подготовка

```bash
# Клонируйте репозиторий
git clone https://github.com/mgldezveer/telegram.git
cd telegram

# Создайте .env файл
cp .env.example .env
```

### 2. Настройка переменных окружения

Отредактируйте `.env` и укажите:

```bash
# Обязательные параметры
TELEGRAM_BOT_TOKEN=ваш_токен_от_BotFather
ADMIN_IDS=ваш_telegram_id

# AI провайдер (выберите один - обязательно):
GROQ_API_KEY=ваш_ключ_Groq
# ИЛИ
OPENAI_API_KEY=ваш_ключ_OpenAI

# AI конфигурация (опционально)
AI_MODEL=qwen-2.5-72b-instruct  # Для Groq, или gpt-4 для OpenAI
AI_TEMPERATURE=0.7              # Креативность: 0.0-2.0
AI_MAX_TOKENS=1000              # Максимальная длина ответа

# База данных (опционально)
DATABASE_URL=postgresql://botuser:changeme@db:5432/ai_content_bot
DB_POOL_SIZE=10
DB_ECHO=false

# Redis (опционально)
REDIS_URL=redis://redis:6379/0
REDIS_MAX_CONNECTIONS=50

# Планирование (опционально)
DEFAULT_POSTING_FREQUENCY=3     # Постов в день
TIMEZONE=UTC

# Логирование (опционально)
LOG_LEVEL=INFO
DEBUG=false
```

### 3. Запуск

```bash
# Запустите все сервисы
docker-compose up -d

# Проверьте статус
docker-compose ps

# Просмотр логов
docker-compose logs -f bot
```

### 4. Проверка работы

```bash
# Health check
curl http://localhost:9090/health

# Метрики Prometheus
curl http://localhost:9090/metrics
```

## Развертывание на сервере

### Требования к серверу

- Ubuntu 20.04+ / Debian 11+
- 2+ CPU cores
- 4+ GB RAM
- 20+ GB disk space
- Docker и Docker Compose установлены

### Установка Docker

```bash
# Обновите систему
sudo apt update && sudo apt upgrade -y

# Установите Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Установите Docker Compose
sudo apt install docker-compose-plugin

# Добавьте пользователя в группу docker
sudo usermod -aG docker $USER
```

### Настройка firewall

```bash
# Откройте необходимые порты
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 9090/tcp  # Monitoring
sudo ufw enable
```

### Автозапуск при перезагрузке

```bash
# Создайте systemd service
sudo nano /etc/systemd/system/ai-content-bot.service
```

Содержимое файла:

```ini
[Unit]
Description=AI Content Bot
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/ai-content-bot
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

Активируйте сервис:

```bash
sudo systemctl enable ai-content-bot
sudo systemctl start ai-content-bot
```

## Мониторинг

### Prometheus

Доступен на `http://your-server:9091`

### Grafana (опционально)

Добавьте в `docker-compose.yml`:

```yaml
grafana:
  image: grafana/grafana:latest
  container_name: bot-grafana
  restart: unless-stopped
  ports:
    - "3000:3000"
  environment:
    - GF_SECURITY_ADMIN_PASSWORD=admin
  volumes:
    - grafana_data:/var/lib/grafana
  networks:
    - bot-network
```

## Резервное копирование

### Автоматическое резервное копирование

Создайте скрипт `/opt/backup-bot.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/opt/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Создайте директорию для бэкапов
mkdir -p $BACKUP_DIR

# Бэкап базы данных
docker exec bot-postgres pg_dump -U botuser ai_content_bot > $BACKUP_DIR/db_$DATE.sql

# Удалите старые бэкапы (старше 30 дней)
find $BACKUP_DIR -name "db_*.sql" -mtime +30 -delete

echo "Backup completed: $BACKUP_DIR/db_$DATE.sql"
```

Добавьте в crontab:

```bash
# Ежедневный бэкап в 2:00
0 2 * * * /opt/backup-bot.sh
```

### Восстановление из бэкапа

```bash
# Остановите бота
docker-compose down

# Восстановите базу данных
cat backup.sql | docker exec -i bot-postgres psql -U botuser ai_content_bot

# Запустите бота
docker-compose up -d
```

## Обновление

### Обновление кода

```bash
# Остановите бота
docker-compose down

# Получите последние изменения
git pull origin main

# Пересоберите образы
docker-compose build

# Запустите обновленную версию
docker-compose up -d
```

### Обновление зависимостей

```bash
# Обновите requirements.txt
pip install --upgrade -r requirements.txt

# Пересоберите образ
docker-compose build bot
docker-compose up -d bot
```

## Масштабирование

### Горизонтальное масштабирование

Для увеличения производительности можно запустить несколько worker'ов:

```bash
docker-compose up -d --scale celery-worker=3
```

### Вертикальное масштабирование

Увеличьте ресурсы в `docker-compose.yml`:

```yaml
bot:
  deploy:
    resources:
      limits:
        cpus: '2'
        memory: 4G
      reservations:
        cpus: '1'
        memory: 2G
```

## Безопасность

### SSL/TLS

Для production рекомендуется использовать Nginx с Let's Encrypt:

```bash
# Установите Certbot
sudo apt install certbot python3-certbot-nginx

# Получите сертификат
sudo certbot --nginx -d your-domain.com
```

### Обновление секретов

```bash
# Сгенерируйте новые пароли
openssl rand -base64 32

# Обновите .env
nano .env

# Перезапустите сервисы
docker-compose restart
```

## Troubleshooting

### Бот не запускается

```bash
# Проверьте логи
docker-compose logs bot

# Проверьте конфигурацию
docker-compose config

# Проверьте переменные окружения
docker-compose exec bot env | grep TELEGRAM
```

### Проблемы с AI API

```bash
# Проверьте что ключ правильный в .env
cat .env | grep API_KEY

# Проверьте логи для ошибок API
docker-compose logs bot | grep -i "api"

# Убедитесь что у вас есть доступ к выбранному провайдеру
# Groq: https://console.groq.com
# OpenAI: https://platform.openai.com
```

### Проблемы с базой данных

```bash
# Проверьте статус PostgreSQL
docker-compose exec db pg_isready

# Подключитесь к базе данных
docker-compose exec db psql -U botuser ai_content_bot

# Проверьте таблицы
\dt
```

### Проблемы с Redis

```bash
# Проверьте Redis
docker-compose exec redis redis-cli ping

# Очистите кэш
docker-compose exec redis redis-cli FLUSHALL
```

## Мониторинг производительности

### Метрики системы

```bash
# CPU и память
docker stats

# Использование диска
df -h

# Логи в реальном времени
docker-compose logs -f --tail=100
```

### Алерты

Настройте Alertmanager для уведомлений:

```yaml
# alertmanager.yml
route:
  receiver: 'telegram'

receivers:
  - name: 'telegram'
    telegram_configs:
      - bot_token: 'YOUR_BOT_TOKEN'
        chat_id: YOUR_CHAT_ID
```

## Поддержка

При возникновении проблем:

1. Проверьте логи: `docker-compose logs`
2. Проверьте health check: `curl http://localhost:9090/health`
3. Создайте issue на GitHub с описанием проблемы
