"""Auto-posting services."""

from src.services.autopost.channel_manager import (
    AutoPostChannelManager,
    ChannelConfig,
    PermissionStatus
)
from src.services.autopost.content_generator import (
    AutoPostContentGenerator,
    ContentStyle
)
from src.services.autopost.scheduler import (
    AutoPostScheduler,
    ScheduleConfig
)
from src.services.autopost.queue_manager import (
    AutoPostQueueManager,
    QueuedPost
)
from src.services.autopost.publishing import (
    AutoPostPublisher,
    PublishResult
)

__all__ = [
    'AutoPostChannelManager',
    'ChannelConfig',
    'PermissionStatus',
    'AutoPostContentGenerator',
    'ContentStyle',
    'AutoPostScheduler',
    'ScheduleConfig',
    'AutoPostQueueManager',
    'QueuedPost',
    'AutoPostPublisher',
    'PublishResult',
]
