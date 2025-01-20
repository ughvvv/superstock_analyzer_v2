import os
import time
import logging
import requests
from typing import Dict, Optional, Union, List, Any
from .logging_config import configure_logging
from .rate_limiter import RateLimiter
import aiohttp
import asyncio

# Configure logging
configure_logging()
logger = logging.getLogger(__name__)

class BaseCollector:
    """Base class for data collectors with essential functionality."""
    
    def __init__(self, api_key: str):
        """Initialize the base collector."""
        self.api_key = api_key
        self.base_url = "https://financialmodelingprep.com/api/v3"
        self.timeout = 30
        self.max_retries = 3
        self.session = None
        
        # Initialize rate limiter with default values
        self.rate_limiter = RateLimiter(requests_per_minute=30, burst_limit=5)
        
        # Basic cache setup
        self.cache_dir = 'cache'
        os.makedirs(self.cache_dir, exist_ok=True)
        self.cache = {}

    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_session()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
        
    async def _ensure_session(self):
        """Ensure we have a valid session."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout))
        return self.session

    async def make_request(self, endpoint: str, params: Dict = None, session: Optional[aiohttp.ClientSession] = None) -> Optional[Union[Dict, List]]:
        """Make a request to FMP API with rate limiting and retries."""
        try:
            # Prepare parameters
            full_params = params.copy() if params else {}
            full_params['apikey'] = self.api_key

            # Construct URL
            url = f"{self.base_url}/{endpoint.lstrip('/')}"

            # Use provided session or ensure one exists
            if session is None:
                session = await self._ensure_session()

            # Make request with retries
            for attempt in range(self.max_retries):
                try:
                    # Wait for rate limit
                    await self.rate_limiter.wait_if_needed()
                    
                    async with session.get(url, params=full_params) as response:
                        if response.status == 200:
                            data = await response.json()
                            return self._clean_response(data)
                            
                        elif response.status == 429:  # Too Many Requests
                            if attempt < self.max_retries - 1:
                                await asyncio.sleep(60)  # Wait a minute before retry
                                continue
                            
                        elif response.status == 403:  # Forbidden
                            logger.error("API key invalid or expired")
                            return None
                            
                        else:
                            logger.warning(f"Request failed: {response.status}")
                            if attempt < self.max_retries - 1:
                                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                                continue
                            return None
                            
                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    logger.warning(f"Request failed: {str(e)}")
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    return None
                    
        except Exception as e:
            logger.error(f"Error in make_request: {str(e)}")
            return None

    async def process_batch(self, symbols: List[str], process_func) -> List:
        """Process a batch of symbols with basic concurrency."""
        tasks = []
        for symbol in symbols:
            task = asyncio.create_task(process_func(symbol))
            tasks.append(task)
        return await asyncio.gather(*tasks, return_exceptions=True)

    def _clean_response(self, data: Union[Dict, List]) -> Union[Dict, List]:
        """Clean response data by removing null values."""
        if isinstance(data, list):
            return [item for item in data if item is not None]
        elif isinstance(data, dict):
            return {k: v for k, v in data.items() if v is not None}
        return data

    async def close(self):
        """Close the aiohttp session."""
        if self.session:
            await self.session.close()
            self.session = None

    def get_from_cache(self, key: str) -> Optional[Union[Dict, List]]:
        """Get data from cache."""
        return self.cache.get(key)
        
    def save_to_cache(self, key: str, data: Union[Dict, List]) -> None:
        """Save data to cache."""
        self.cache[key] = data
