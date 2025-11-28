# Multi-stage build for Telegram Bot

# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --user --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY src/ ./src/
COPY run.py .
COPY run_autopost.py .
COPY init_db.py .
COPY init_autopost_db.py .
COPY check_db.py .
COPY check_setup.py .
COPY check_tasks.py .
COPY clean_channels.py .
COPY sync_channel_stats.py .
COPY alembic.ini .
COPY .env.example .env
COPY settings.json .

# Set Python path
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app

# Create logs directory
RUN mkdir -p logs

# Expose monitoring port
EXPOSE 9090

# Run bot
CMD ["python", "run.py"]
