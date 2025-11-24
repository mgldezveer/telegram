"""Celery tasks for background processing."""

import logging
from celery import Celery
from src.config import config

logger = logging.getLogger(__name__)

# Create Celery app
celery_app = Celery(
    'ai_content_bot',
    broker=config.redis.url,
    backend=config.redis.url
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    worker_prefetch_multiplier=1,
)


@celery_app.task(name='generate_content')
def generate_content_task(channel_id: int, theme: str, style: dict):
    """Background task for content generation."""
    logger.info(f"Starting content generation task for channel {channel_id}")
    
    try:
        # In production, would call actual generation service
        # For now, just log
        logger.info(f"Generated content for theme: {theme}")
        return {'status': 'success', 'channel_id': channel_id}
    except Exception as e:
        logger.error(f"Content generation task failed: {e}")
        raise


@celery_app.task(name='publish_post')
def publish_post_task(post_id: int, channel_id: int):
    """Background task for post publishing."""
    logger.info(f"Starting publish task for post {post_id}")
    
    try:
        # In production, would call actual publishing service
        logger.info(f"Published post {post_id} to channel {channel_id}")
        return {'status': 'success', 'post_id': post_id}
    except Exception as e:
        logger.error(f"Publish task failed: {e}")
        raise


@celery_app.task(name='collect_metrics')
def collect_metrics_task(post_id: int):
    """Background task for metrics collection."""
    logger.info(f"Collecting metrics for post {post_id}")
    
    try:
        # In production, would collect actual metrics
        logger.info(f"Metrics collected for post {post_id}")
        return {'status': 'success', 'post_id': post_id}
    except Exception as e:
        logger.error(f"Metrics collection task failed: {e}")
        raise
