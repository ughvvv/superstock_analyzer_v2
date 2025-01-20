import asyncio
import logging
from datetime import datetime, timedelta
from collections import deque
from threading import Lock
from .logging_config import configure_logging

# Configure logging
configure_logging()
logger = logging.getLogger(__name__)

class RateLimiter:
    """Manages API request rate limiting with basic burst protection."""
    
    def __init__(self, requests_per_minute: int = 30, burst_limit: int = 5):
        self.requests_per_minute = requests_per_minute
        self.burst_limit = burst_limit
        self.request_times = deque()
        self.lock = Lock()
        
    async def wait_if_needed(self) -> None:
        """Wait if necessary to comply with rate limits."""
        try:
            with self.lock:
                now = datetime.now()
                
                # Remove old requests (older than 1 minute)
                while self.request_times and (now - self.request_times[0]) > timedelta(minutes=1):
                    self.request_times.popleft()
                
                # Check if we're at the rate limit
                if len(self.request_times) >= self.requests_per_minute:
                    # Calculate wait time until oldest request expires
                    wait_time = (self.request_times[0] + timedelta(minutes=1) - now).total_seconds()
                    if wait_time > 0:
                        logger.warning(f"Rate limit reached, waiting {wait_time:.2f} seconds")
                        await asyncio.sleep(wait_time)
                
                # Check burst limit (requests in last second)
                recent_requests = sum(1 for t in self.request_times 
                                   if (now - t).total_seconds() <= 1)
                if recent_requests >= self.burst_limit:
                    logger.warning("Burst limit reached, adding delay")
                    await asyncio.sleep(1)
                
                # Add current request
                self.request_times.append(now)
                
        except Exception as e:
            logger.error(f"Error in rate limiter: {str(e)}")
            raise

    def get_remaining_requests(self) -> int:
        """Get number of remaining requests for the current minute."""
        try:
            with self.lock:
                now = datetime.now()
                
                # Remove old requests
                while self.request_times and (now - self.request_times[0]) > timedelta(minutes=1):
                    self.request_times.popleft()
                
                return max(0, self.requests_per_minute - len(self.request_times))
                
        except Exception as e:
            logger.error(f"Error getting remaining requests: {str(e)}")
            return 0

    def update_limits(self, requests_per_minute: int, burst_limit: int) -> None:
        """Update rate limits."""
        try:
            with self.lock:
                self.requests_per_minute = requests_per_minute
                self.burst_limit = burst_limit
                logger.debug(f"Updated rate limits: {requests_per_minute} rpm, {burst_limit} burst")
                
        except Exception as e:
            logger.error(f"Error updating rate limits: {str(e)}")
            raise
