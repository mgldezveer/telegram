# Redis Setup Guide

This guide explains how to install and configure Redis for the AI Content Bot on Windows.

## Overview

Redis is used for caching LLM responses and session data. The bot includes automatic fallback to in-memory caching if Redis is unavailable, so Redis is **optional** for development but **recommended** for production.

## Installation Options

### Option 1: WSL (Windows Subsystem for Linux) - Recommended

This is the recommended approach as it provides the official Redis experience.

#### Step 1: Install WSL

```powershell
# Run in PowerShell as Administrator
wsl --install
```

Restart your computer after installation.

#### Step 2: Install Redis in WSL

```bash
# Open WSL terminal
wsl

# Update package list
sudo apt update

# Install Redis
sudo apt install redis-server -y

# Verify installation
redis-server --version
```

#### Step 3: Start Redis

```bash
# Start Redis server
sudo service redis-server start

# Check status
sudo service redis-server status

# Test connection
redis-cli ping
# Should return: PONG
```

#### Step 4: Configure Redis to Start Automatically

```bash
# Edit Redis configuration
sudo nano /etc/redis/redis.conf

# Find and change:
# supervised no
# to:
# supervised systemd

# Restart Redis
sudo service redis-server restart
```

#### Step 5: Connect from Windows

Redis in WSL is accessible from Windows at `localhost:6379` or `127.0.0.1:6379`.

Test connection from Windows PowerShell:
```powershell
# Install redis-cli for Windows (optional)
# Or use the bot's health check endpoint
curl http://localhost:9090/health
```

---

### Option 2: Docker - Easy Setup

Docker provides an isolated Redis instance that's easy to manage.

#### Step 1: Install Docker Desktop

Download and install from: https://www.docker.com/products/docker-desktop/

#### Step 2: Run Redis Container

```powershell
# Run Redis in Docker
docker run -d `
  --name redis `
  -p 6379:6379 `
  -v redis_data:/data `
  redis:7-alpine redis-server --appendonly yes

# Check if running
docker ps

# View logs
docker logs redis

# Test connection
docker exec -it redis redis-cli ping
# Should return: PONG
```

#### Step 3: Manage Redis Container

```powershell
# Stop Redis
docker stop redis

# Start Redis
docker start redis

# Remove Redis (data persists in volume)
docker rm redis

# Remove Redis and data
docker rm redis
docker volume rm redis_data
```

---

### Option 3: Memurai - Windows Native

Memurai is a Windows-native Redis-compatible server.

#### Step 1: Download Memurai

Download from: https://www.memurai.com/get-memurai

#### Step 2: Install

Run the installer and follow the setup wizard.

#### Step 3: Start Memurai

Memurai runs as a Windows service and starts automatically.

```powershell
# Check service status
Get-Service Memurai

# Start service
Start-Service Memurai

# Stop service
Stop-Service Memurai
```

#### Step 4: Test Connection

```powershell
# Memurai includes redis-cli
memurai-cli ping
# Should return: PONG
```

---

## Configuration

### Environment Variables

Create or update your `.env` file:

```bash
# Redis Configuration
REDIS_URL=redis://localhost:6379/0
REDIS_MAX_CONNECTIONS=10
REDIS_SOCKET_TIMEOUT=5
REDIS_SOCKET_CONNECT_TIMEOUT=5
REDIS_RETRY_ON_TIMEOUT=true
REDIS_HEALTH_CHECK_INTERVAL=30

# Optional: Redis password
# REDIS_PASSWORD=your_password_here

# Optional: Redis database number (0-15)
# REDIS_DB=0
```

### Redis URL Format

```
redis://[password@]host[:port][/database]
```

Examples:
- `redis://localhost:6379/0` - Local Redis, database 0
- `redis://:mypassword@localhost:6379/0` - With password
- `redis://192.168.1.100:6379/1` - Remote Redis, database 1
- `rediss://secure-redis.example.com:6380/0` - SSL/TLS connection

---

## Verification

### Check Bot Connection

1. Start the bot:
```powershell
python run.py
```

2. Look for these log messages:
```
✅ Connected to Redis successfully
```

Or if Redis is unavailable:
```
⚠️  Using memory cache (Redis unavailable)
✅ Reconnection task started
```

### Check Health Endpoint

```powershell
# Check health status
curl http://localhost:9090/health
```

Response when Redis is connected:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00",
  "components": {
    "cache": {
      "status": "healthy",
      "message": "Redis connected (v7.0.0)",
      "details": {
        "backend": "redis",
        "redis_version": "7.0.0",
        "uptime_seconds": 3600,
        "connected_clients": 2
      }
    }
  }
}
```

Response when using fallback:
```json
{
  "status": "degraded",
  "components": {
    "cache": {
      "status": "degraded",
      "message": "Using memory cache fallback (Redis unavailable)",
      "details": {
        "backend": "memory",
        "total_keys": 42,
        "hit_rate": 85.5
      }
    }
  }
}
```

---

## Troubleshooting

### Redis Not Starting (WSL)

```bash
# Check Redis logs
sudo tail -f /var/log/redis/redis-server.log

# Check if port is in use
sudo netstat -tulpn | grep 6379

# Restart Redis
sudo service redis-server restart
```

### Connection Refused

**Problem**: Bot shows "Connection refused" error

**Solutions**:
1. Check if Redis is running:
   ```bash
   # WSL
   sudo service redis-server status
   
   # Docker
   docker ps | grep redis
   
   # Memurai
   Get-Service Memurai
   ```

2. Check firewall settings (Windows Firewall may block connections)

3. Verify Redis is listening on correct port:
   ```bash
   redis-cli -h localhost -p 6379 ping
   ```

### WSL Redis Not Accessible from Windows

**Problem**: Redis works in WSL but bot can't connect

**Solution**: Use WSL IP address instead of localhost

```bash
# Get WSL IP address
ip addr show eth0 | grep inet
```

Update `.env`:
```bash
REDIS_URL=redis://172.x.x.x:6379/0
```

### High Memory Usage

**Problem**: Redis using too much memory

**Solution**: Configure maxmemory in Redis config

```bash
# Edit Redis config
sudo nano /etc/redis/redis.conf

# Add or update:
maxmemory 256mb
maxmemory-policy allkeys-lru

# Restart Redis
sudo service redis-server restart
```

### Bot Works Without Redis

This is **normal behavior**! The bot automatically falls back to in-memory caching when Redis is unavailable. You'll see:

```
⚠️  Using memory cache (Redis unavailable)
✅ Reconnection task started
```

The bot will automatically reconnect to Redis when it becomes available.

---

## Production Recommendations

### Security

1. **Set a password**:
   ```bash
   # In redis.conf
   requirepass your_strong_password_here
   ```
   
   Update `.env`:
   ```bash
   REDIS_URL=redis://:your_strong_password_here@localhost:6379/0
   ```

2. **Bind to localhost only** (if Redis is on same machine):
   ```bash
   # In redis.conf
   bind 127.0.0.1 ::1
   ```

3. **Disable dangerous commands**:
   ```bash
   # In redis.conf
   rename-command FLUSHDB ""
   rename-command FLUSHALL ""
   rename-command CONFIG ""
   ```

### Performance

1. **Enable persistence**:
   ```bash
   # In redis.conf
   appendonly yes
   appendfsync everysec
   ```

2. **Set memory limits**:
   ```bash
   maxmemory 512mb
   maxmemory-policy allkeys-lru
   ```

3. **Optimize for your workload**:
   ```bash
   # For cache-heavy workload
   maxmemory-policy allkeys-lru
   
   # For session storage
   maxmemory-policy volatile-lru
   ```

### Monitoring

1. **Monitor Redis stats**:
   ```bash
   redis-cli info stats
   ```

2. **Check memory usage**:
   ```bash
   redis-cli info memory
   ```

3. **Monitor slow queries**:
   ```bash
   redis-cli slowlog get 10
   ```

---

## Docker Compose Integration

See the main `docker-compose.yml` for Redis integration with the bot.

---

## Additional Resources

- [Redis Official Documentation](https://redis.io/documentation)
- [Redis Commands Reference](https://redis.io/commands)
- [WSL Documentation](https://docs.microsoft.com/en-us/windows/wsl/)
- [Docker Documentation](https://docs.docker.com/)
- [Memurai Documentation](https://docs.memurai.com/)

---

## Quick Reference

### Common Commands

```bash
# WSL
sudo service redis-server start
sudo service redis-server stop
sudo service redis-server restart
sudo service redis-server status

# Docker
docker start redis
docker stop redis
docker restart redis
docker logs redis

# Redis CLI
redis-cli ping
redis-cli info
redis-cli monitor
redis-cli --stat
```

### Default Ports

- Redis: `6379`
- Bot Monitoring: `9090`

### Configuration Files

- WSL: `/etc/redis/redis.conf`
- Docker: Use volume mount or environment variables
- Memurai: `C:\Program Files\Memurai\memurai.conf`
