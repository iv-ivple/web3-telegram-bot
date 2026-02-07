"""
Simple rate limiting to prevent abuse.
"""
from datetime import datetime, timedelta
from collections import defaultdict

class RateLimiter:
    """Rate limit users to prevent spam."""
    
    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Max requests per window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window = timedelta(seconds=window_seconds)
        self.requests = defaultdict(list)
    
    def is_allowed(self, user_id: int) -> bool:
        """
        Check if user is allowed to make a request.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            True if allowed, False if rate limited
        """
        now = datetime.now()
        
        # Clean old requests
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id]
            if now - req_time < self.window
        ]
        
        # Check if under limit
        if len(self.requests[user_id]) < self.max_requests:
            self.requests[user_id].append(now)
            return True
        
        return False
    
    def get_wait_time(self, user_id: int) -> int:
        """Get seconds until user can make another request."""
        if not self.requests[user_id]:
            return 0
        
        oldest = min(self.requests[user_id])
        wait = (oldest + self.window - datetime.now()).total_seconds()
        return max(0, int(wait))

# Global rate limiter
rate_limiter = RateLimiter(max_requests=20, window_seconds=60)
