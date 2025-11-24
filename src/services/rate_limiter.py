"""Rate limiter service using token bucket algorithm."""

import logging
import time
from collections import defaultdict
from typing import Dict, Tuple

logger = logging.getLogger(__name__)


class RateLimiter:
    """Token bucket rate limiter.
    
    Implements token bucket algorithm for rate limiting user actions.
    """
    
    def __init__(self, max_requests: int = 5, window_seconds: int = 60):
        """Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        
        # Store: user_id -> (tokens, last_refill_time)
        self._buckets: Dict[int, Tuple[float, float]] = defaultdict(
            lambda: (float(max_requests), time.time())
        )
        
        logger.info(f"Rate limiter initialized: {max_requests} requests per {window_seconds}s")
    
    def is_allowed(self, user_id: int, cost: float = 1.0) -> bool:
        """Check if request is allowed for user.
        
        Args:
            user_id: User ID
            cost: Cost of this request in tokens (default 1.0)
            
        Returns:
            True if request is allowed, False if rate limited
        """
        now = time.time()
        tokens, last_refill = self._buckets[user_id]
        
        # Calculate tokens to add based on time elapsed
        elapsed = now - last_refill
        refill_rate = self.max_requests / self.window_seconds
        tokens_to_add = elapsed * refill_rate
        
        # Refill tokens (capped at max)
        tokens = min(self.max_requests, tokens + tokens_to_add)
        
        # Check if enough tokens
        if tokens >= cost:
            # Consume tokens
            tokens -= cost
            self._buckets[user_id] = (tokens, now)
            logger.debug(f"User {user_id}: request allowed, {tokens:.2f} tokens remaining")
            return True
        else:
            # Rate limited
            self._buckets[user_id] = (tokens, now)
            logger.warning(f"User {user_id}: rate limited, {tokens:.2f} tokens available")
            return False
    
    def get_remaining_tokens(self, user_id: int) -> float:
        """Get remaining tokens for user.
        
        Args:
            user_id: User ID
            
        Returns:
            Number of remaining tokens
        """
        now = time.time()
        tokens, last_refill = self._buckets[user_id]
        
        # Calculate current tokens
        elapsed = now - last_refill
        refill_rate = self.max_requests / self.window_seconds
        tokens_to_add = elapsed * refill_rate
        
        current_tokens = min(self.max_requests, tokens + tokens_to_add)
        return current_tokens
    
    def get_wait_time(self, user_id: int, cost: float = 1.0) -> float:
        """Get time to wait before next request is allowed.
        
        Args:
            user_id: User ID
            cost: Cost of next request in tokens
            
        Returns:
            Seconds to wait (0 if request would be allowed now)
        """
        remaining = self.get_remaining_tokens(user_id)
        
        if remaining >= cost:
            return 0.0
        
        # Calculate time needed to refill
        tokens_needed = cost - remaining
        refill_rate = self.max_requests / self.window_seconds
        wait_time = tokens_needed / refill_rate
        
        return wait_time
    
    def reset(self, user_id: int) -> None:
        """Reset rate limit for user.
        
        Args:
            user_id: User ID
        """
        if user_id in self._buckets:
            del self._buckets[user_id]
            logger.info(f"Rate limit reset for user {user_id}")
    
    def clear_all(self) -> None:
        """Clear all rate limit data."""
        self._buckets.clear()
        logger.info("All rate limit data cleared")


class ActionRateLimiter:
    """Rate limiter for different action types.
    
    Allows different rate limits for different actions.
    """
    
    def __init__(self):
        """Initialize action rate limiter."""
        self._limiters: Dict[str, RateLimiter] = {
            'quick_action': RateLimiter(max_requests=5, window_seconds=60),  # 5 per minute
            'button_click': RateLimiter(max_requests=30, window_seconds=60),  # 30 per minute
            'content_generation': RateLimiter(max_requests=10, window_seconds=300),  # 10 per 5 min
            'channel_operation': RateLimiter(max_requests=20, window_seconds=60),  # 20 per minute
        }
        logger.info("Action rate limiter initialized")
    
    def is_allowed(self, user_id: int, action: str) -> bool:
        """Check if action is allowed for user.
        
        Args:
            user_id: User ID
            action: Action type
            
        Returns:
            True if allowed, False if rate limited
        """
        limiter = self._limiters.get(action)
        
        if not limiter:
            logger.warning(f"Unknown action type: {action}, allowing by default")
            return True
        
        return limiter.is_allowed(user_id)
    
    def get_wait_time(self, user_id: int, action: str) -> float:
        """Get wait time for action.
        
        Args:
            user_id: User ID
            action: Action type
            
        Returns:
            Seconds to wait
        """
        limiter = self._limiters.get(action)
        
        if not limiter:
            return 0.0
        
        return limiter.get_wait_time(user_id)
    
    def reset(self, user_id: int, action: str = None) -> None:
        """Reset rate limit for user.
        
        Args:
            user_id: User ID
            action: Action type (None to reset all)
        """
        if action:
            limiter = self._limiters.get(action)
            if limiter:
                limiter.reset(user_id)
        else:
            for limiter in self._limiters.values():
                limiter.reset(user_id)
