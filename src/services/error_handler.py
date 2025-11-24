"""Error handling and recovery service."""

import logging
import asyncio
import psutil
from typing import Optional, Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorCategory(Enum):
    """Error categories."""
    GENERATION = "generation"
    PUBLISHING = "publishing"
    STORAGE = "storage"
    SCHEDULING = "scheduling"
    NETWORK = "network"
    UNKNOWN = "unknown"


@dataclass
class ErrorContext:
    """Error context information."""
    category: ErrorCategory
    error: Exception
    timestamp: datetime
    component: str
    details: dict


class ErrorHandler:
    """Centralized error handling and recovery."""
    
    def __init__(self):
        self.error_log: list[ErrorContext] = []
        self.recovery_attempts: dict[str, int] = {}
        self.max_recovery_attempts = 3
        self.resource_threshold = 0.8  # 80% usage threshold
    
    async def handle_error(
        self,
        error: Exception,
        category: ErrorCategory,
        component: str,
        details: Optional[dict] = None
    ) -> bool:
        """Handle error with appropriate recovery strategy."""
        context = ErrorContext(
            category=category,
            error=error,
            timestamp=datetime.utcnow(),
            component=component,
            details=details or {}
        )
        
        # Log error
        await self._log_error(context)
        
        # Attempt recovery
        if await self._should_attempt_recovery(context):
            return await self._attempt_recovery(context)
        
        return False
    
    async def handle_critical_failure(
        self,
        error: Exception,
        component: str,
        recovery_func: Optional[Callable] = None
    ):
        """Handle critical failure with recovery attempt."""
        logger.critical(f"Critical failure in {component}: {error}")
        
        if recovery_func:
            try:
                logger.info(f"Attempting graceful recovery for {component}")
                await recovery_func()
                logger.info(f"Recovery successful for {component}")
            except Exception as e:
                logger.error(f"Recovery failed for {component}: {e}")
                # Notify admins
                await self._notify_admins(component, error)
        else:
            await self._notify_admins(component, error)
    
    async def check_resources(self) -> dict:
        """Check system resource usage."""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        resources = {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'disk_percent': disk.percent,
            'memory_available_mb': memory.available / (1024 * 1024)
        }
        
        # Check if throttling needed
        if (cpu_percent > self.resource_threshold * 100 or
            memory.percent > self.resource_threshold * 100):
            logger.warning(f"High resource usage detected: {resources}")
            await self._throttle_operations()
        
        return resources
    
    async def graceful_shutdown(self, pending_operations: list):
        """Perform graceful shutdown."""
        logger.info("Initiating graceful shutdown")
        
        # Wait for pending operations
        if pending_operations:
            logger.info(f"Waiting for {len(pending_operations)} pending operations")
            try:
                await asyncio.gather(*pending_operations, return_exceptions=True)
                logger.info("All pending operations completed")
            except Exception as e:
                logger.error(f"Error during shutdown: {e}")
        
        logger.info("Graceful shutdown complete")
    
    async def _log_error(self, context: ErrorContext):
        """Log error with full context."""
        self.error_log.append(context)
        
        logger.error(
            f"Error in {context.component} ({context.category.value}): "
            f"{type(context.error).__name__}: {context.error}",
            extra={
                'category': context.category.value,
                'component': context.component,
                'details': context.details,
                'timestamp': context.timestamp.isoformat()
            }
        )
    
    async def _should_attempt_recovery(self, context: ErrorContext) -> bool:
        """Determine if recovery should be attempted."""
        key = f"{context.component}:{context.category.value}"
        attempts = self.recovery_attempts.get(key, 0)
        
        return attempts < self.max_recovery_attempts
    
    async def _attempt_recovery(self, context: ErrorContext) -> bool:
        """Attempt to recover from error."""
        key = f"{context.component}:{context.category.value}"
        self.recovery_attempts[key] = self.recovery_attempts.get(key, 0) + 1
        
        logger.info(f"Attempting recovery for {key} (attempt {self.recovery_attempts[key]})")
        
        try:
            if context.category == ErrorCategory.NETWORK:
                # Wait and retry
                await asyncio.sleep(5)
                return True
            elif context.category == ErrorCategory.STORAGE:
                # Check storage and cleanup if needed
                await self._cleanup_storage()
                return True
            else:
                # Generic recovery
                await asyncio.sleep(2)
                return True
        except Exception as e:
            logger.error(f"Recovery attempt failed: {e}")
            return False
    
    async def _throttle_operations(self):
        """Throttle operations to reduce resource usage."""
        logger.warning("Throttling operations due to high resource usage")
        # In production, would implement actual throttling
        await asyncio.sleep(1)
    
    async def _cleanup_storage(self):
        """Cleanup storage to free space."""
        logger.info("Performing storage cleanup")
        # In production, would implement actual cleanup
        pass
    
    async def _notify_admins(self, component: str, error: Exception):
        """Notify administrators about critical error."""
        logger.critical(f"Notifying admins about critical error in {component}")
        # In production, would send actual notifications
