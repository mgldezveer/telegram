# Docker Compose Setup

## Complete docker-compose.yml

```yaml
version: '3.8'

services:
  bot:
    build: .
    container_name: telegram-bot
    restart: unless-stopped
    env_file: .env
    depends_on:
      - db
      - redis
    volumes:
      - ./logs:/app/logs
      - ./uploads:/app/uploads
    networks:
      - bot-network

  db:
    image: postgres:15-alpine
    container_name: bot-postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - bot-network
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    container_name: bot-redis
    restart: unless-stopped
    volumes:
      - redis_data:/data
    networks:
      - bot-network
    ports:
      - "6379:6379"

  nginx:
    image: nginx:alpine
    container_name: bot-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./certs:/etc/nginx/certs
    depends_on:
      - bot
    networks:
      - bot-network

volumes:
  postgres_data:
  redis_data:

networks:
  bot-network:
    driver: bridge
```

## Multi-Stage Dockerfile

```dockerfile
# Build stage
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.11-slim

WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .

ENV PATH=/root/.local/bin:$PATH

CMD ["python", "main.py"]
```
