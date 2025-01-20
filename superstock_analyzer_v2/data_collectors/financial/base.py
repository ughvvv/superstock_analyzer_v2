import logging
import asyncio
from typing import Dict, Optional, Any, Union, List
import aiohttp
from abc import ABC, abstractmethod
import csv
from io import StringIO
from datetime import datetime

logger = logging.getLogger(__name__)

class FinancialDataFetcher(ABC):
    """Base class for financial data fetching with rate limiting and retries."""
    
    def __init__(self, session: aiohttp.ClientSession, api_key: str):
        self.session = session
        self.api_key = api_key
        self._last_request_time = 0
        self._min_request_interval = 0.25  # 250ms between requests
        self._max_retries = 3
        self._retry_delay = 1.0  # Start with 1 second delay
        
    @property
    @abstractmethod
    def endpoint(self) -> str:
        """Return the API endpoint for this data type."""
        pass
        
    @property
    def additional_params(self) -> Dict[str, Any]:
        """Return additional parameters needed for the request."""
        return {}
        
    async def _wait_for_rate_limit(self):
        """Ensure we don't exceed rate limits."""
        now = asyncio.get_event_loop().time()
        time_since_last = now - self._last_request_time
        if time_since_last < self._min_request_interval:
            await asyncio.sleep(self._min_request_interval - time_since_last)
        self._last_request_time = asyncio.get_event_loop().time()
        
    def _process_csv_response(self, csv_text: str, symbols: List[str]) -> Dict[str, Dict]:
        """Process CSV response into dictionary of company data."""
        try:
            logger.info(f"Processing CSV response for {self.endpoint}")
            # First check if we got valid CSV data
            if not csv_text or ',' not in csv_text:
                logger.error(f"Invalid CSV response from {self.endpoint}: {csv_text[:100]}")
                return {}
                
            reader = csv.DictReader(StringIO(csv_text))
            data = {}
            symbol_set = set(symbols)  # Convert to set for faster lookups
            
            # Log the first row to see the structure
            rows = list(reader)
            if rows:
                logger.info(f"CSV columns for {self.endpoint}: {list(rows[0].keys())}")
            else:
                logger.warning(f"No rows in CSV response for {self.endpoint}")
                return {}
            
            for row in rows:
                symbol = row.get('symbol')
                if symbol in symbol_set:
                    if symbol not in data:
                        data[symbol] = {}
                    # Remove symbol from row to avoid duplication
                    row_copy = row.copy()
                    row_copy.pop('symbol', None)
                    data[symbol].update(row_copy)
            
            logger.info(f"Found data for {len(data)} symbols in {self.endpoint}")
            return data
            
        except Exception as e:
            logger.error(f"Error processing CSV response: {str(e)}")
            return {}
        
    async def get_bulk_data(self, symbols: Union[List[str], str]) -> Dict[str, Dict]:
        """Fetch bulk data and filter for requested symbols after receiving."""
        # Convert string of symbols to list if necessary
        if isinstance(symbols, str):
            symbols = [s.strip() for s in symbols.split(',')]
            
        params = {
            'apikey': self.api_key,
            **self.additional_params
        }
        
        url = f"https://financialmodelingprep.com/api/v4/{self.endpoint}"
        logger.info(f"Making request to {url}")
        
        for attempt in range(self._max_retries):
            try:
                await self._wait_for_rate_limit()
                
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        text = await response.text()
                        logger.info(f"Got successful response from {self.endpoint}")
                        return self._process_csv_response(text, symbols)
                    elif response.status == 429:  # Too Many Requests
                        retry_after = float(response.headers.get('Retry-After', self._retry_delay))
                        logger.warning(f"Rate limited, waiting {retry_after}s before retry")
                        await asyncio.sleep(retry_after)
                        self._retry_delay *= 2  # Exponential backoff
                    elif response.status == 400:
                        error_text = await response.text()
                        logger.error(f"Bad request for {self.endpoint}: {error_text}")
                        return {}
                    else:
                        error_text = await response.text()
                        logger.error(f"Error fetching {self.endpoint}: {response.status}, Response: {error_text}")
                        await asyncio.sleep(self._retry_delay)
                        
            except Exception as e:
                logger.error(f"Error fetching bulk data for {self.endpoint}: {str(e)}")
                await asyncio.sleep(self._retry_delay)
                
            if attempt < self._max_retries - 1:  # Don't log on last attempt
                logger.info(f"Retrying {self.endpoint} (attempt {attempt + 2}/{self._max_retries})")
                
        return {}
