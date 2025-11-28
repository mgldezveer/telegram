# Docker commands for Telegram Bot

# Build services
build:
	docker-compose build

# Start services in background
up:
	docker-compose up -d

# Start all services (including autopost) in background
start:
	docker-compose up -d

# Stop all services
stop:
	docker-compose down

# Start services in foreground
run:
	docker-compose up

# View logs
logs:
	docker-compose logs -f

# View specific service logs
logs-bot:
	docker-compose logs -f bot

logs-autopost:
	docker-compose logs -f autopost

logs-db:
	docker-compose logs -f db

logs-redis:
	docker-compose logs -f redis

# Execute command in bot container
exec-bot:
	docker-compose exec bot bash

# Execute command in autopost container
exec-autopost:
	docker-compose exec autopost bash

# Initialize database
init-db:
	docker-compose exec bot python init_db.py

# Initialize autopost database
init-autopost-db:
	docker-compose exec bot python init_autopost_db.py

# Check database
check-db:
	docker-compose exec bot python check_db.py

# Check setup
check-setup:
	docker-compose exec bot python check_setup.py

# Clean channels
clean-channels:
	docker-compose exec bot python clean_channels.py

# Restart services
restart:
	docker-compose restart

# Remove containers and volumes
clean:
	docker-compose down -v

# Remove containers, volumes and rebuild
rebuild: clean build start

.PHONY: build up start stop run logs logs-bot logs-autopost exec-bot exec-autopost init-db check-db check-setup clean-channels restart clean rebuild