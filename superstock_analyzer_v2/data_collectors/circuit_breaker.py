"""Simple circuit breaker for API resilience."""

import time
import logging
from enum import Enum
from typing import Optional, Callable, Any
from functools import wraps

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "CLOSED"       # Normal operation
    OPEN = "OPEN"          # Failing, reject fast
    HALF_OPEN = "HALF_OPEN"  # Testing recovery

class CircuitBreaker:
    """Basic circuit breaker for API call protection."""
    
    def __init__(self, name: str = "default"):
        """Initialize circuit breaker with default settings."""
        self.name = name
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0
        
        # Configuration
        self.failure_threshold = 5  # Number of failures before opening
        self.recovery_timeout = 60  # Seconds to wait before recovery attempt
        self.half_open_success_required = 2  # Successes needed to close circuit
        self.successful_calls = 0
        
    def can_execute(self) -> bool:
        """Check if execution is allowed."""
        if self.state == CircuitState.CLOSED:
            return True
            
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                logger.info(f"[{self.name}] Circuit transitioning to HALF_OPEN state")
                self.state = CircuitState.HALF_OPEN
                self.successful_calls = 0
                return True
            return False
            
        # HALF_OPEN state
        return True
        
    def on_success(self):
        """Handle successful execution."""
        if self.state == CircuitState.HALF_OPEN:
            self.successful_calls += 1
            if self.successful_calls >= self.half_open_success_required:
                logger.info(f"[{self.name}] Circuit recovered, transitioning to CLOSED state")
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.successful_calls = 0
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0
            
    def on_failure(self):
        """Handle failed execution."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == CircuitState.HALF_OPEN or \
           (self.state == CircuitState.CLOSED and self.failure_count >= self.failure_threshold):
            logger.warning(f"[{self.name}] Circuit breaker tripped, transitioning to OPEN state")
            self.state = CircuitState.OPEN
            self.successful_calls = 0

def circuit_breaker(breaker: CircuitBreaker):
    """Decorator to apply circuit breaker to function."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            if not breaker.can_execute():
                logger.warning(f"[{breaker.name}] Circuit breaker preventing execution")
                raise CircuitBreakerError(f"Circuit breaker open for {breaker.name}")
                
            try:
                result = await func(*args, **kwargs)
                breaker.on_success()
                return result
            except Exception as e:
                breaker.on_failure()
                raise CircuitBreakerError(f"Call failed for {breaker.name}: {str(e)}")
                
        return wrapper
    return decorator

class CircuitBreakerError(Exception):
    """Exception raised when circuit breaker prevents execution."""
    pass
