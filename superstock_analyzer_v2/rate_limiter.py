import time
from datetime import datetime, timedelta
from typing import Dict, Optional
import threading
import json
import os

class RateLimiter:
    def __init__(self):
        """Initialize rate limiters for different APIs."""
        self._locks = {
            'yahoo': threading.Lock(),
            'nasdaq': threading.Lock(),
            'nyse': threading.Lock(),
            'sec': threading.Lock(),
            'fmp': threading.Lock()
        }
        
        # Track last request times
        self._last_request_time = {
            'yahoo': {},  # symbol -> last request time
            'nasdaq': datetime.min,
            'nyse': datetime.min,
            'sec': datetime.min,
            'fmp': datetime.min
        }
        
        # Configure rate limits
        self.YAHOO_LIMIT = 2000  # requests per hour per IP
        self.YAHOO_DELAY = 1.8  # seconds between requests
        self.NASDAQ_DELAY = 60  # 1 request per minute
        self.NYSE_DELAY = 30  # 1 request per 30 seconds
        self.SEC_DELAY = 0.1  # 10 requests per second per SEC guidelines
        self.FMP_MINUTE_LIMIT = 3000  # Updated to new limit
        self.FMP_DAILY_LIMIT = 100000  # Increased daily limit substantially
        self.FMP_DELAY = 60 / self.FMP_MINUTE_LIMIT  # seconds between requests
        
        # Track hourly Yahoo requests
        self._yahoo_request_count = 0
        self._yahoo_hour_start = datetime.now()

        # Track FMP requests
        self._fmp_minute_count = 0
        self._fmp_minute_start = datetime.now()
        self._fmp_daily_count = self._load_daily_count()
        self._fmp_day_start = datetime.now().date()

        # Exponential backoff settings
        self.initial_backoff = 1  # Start with 1 second
        self.max_backoff = 60     # Maximum backoff of 60 seconds
        self.backoff_factor = 2   # Double the backoff each time
        self._current_backoff = self.initial_backoff

        # Reserve fewer calls for initial quotes since we're using caching
        self.RESERVED_CALLS = 1000  # Increased from 50 due to higher limits

    def _load_daily_count(self) -> int:
        """Load the daily API call count from persistent storage."""
        try:
            if os.path.exists('api_counts.json'):
                with open('api_counts.json', 'r') as f:
                    data = json.load(f)
                    last_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
                    if last_date == datetime.now().date():
                        return data['count']
        except Exception:
            pass
        return 0

    def _save_daily_count(self) -> None:
        """Save the daily API call count to persistent storage."""
        try:
            with open('api_counts.json', 'w') as f:
                json.dump({
                    'date': self._fmp_day_start.strftime('%Y-%m-%d'),
                    'count': self._fmp_daily_count
                }, f)
        except Exception:
            pass

    def _wait_if_needed(self, api: str, symbol: Optional[str] = None, is_initial_quote: bool = False) -> bool:
        """
        Wait if necessary to comply with rate limits.
        Returns True if request can proceed, False if daily limit reached.
        """
        with self._locks[api]:
            now = datetime.now()
            
            if api == 'yahoo':
                # Reset hourly counter if needed
                if now - self._yahoo_hour_start > timedelta(hours=1):
                    self._yahoo_request_count = 0
                    self._yahoo_hour_start = now
                
                # Check hourly limit
                if self._yahoo_request_count >= self.YAHOO_LIMIT:
                    sleep_time = 3600 - (now - self._yahoo_hour_start).total_seconds()
                    if sleep_time > 0:
                        time.sleep(sleep_time)
                    self._yahoo_request_count = 0
                    self._yahoo_hour_start = datetime.now()
                
                # Check per-symbol delay
                if symbol:
                    last_request = self._last_request_time['yahoo'].get(symbol, datetime.min)
                    sleep_time = self.YAHOO_DELAY - (now - last_request).total_seconds()
                    if sleep_time > 0:
                        time.sleep(sleep_time)
                    self._last_request_time['yahoo'][symbol] = datetime.now()
                
                self._yahoo_request_count += 1
                return True
                
            elif api == 'nasdaq':
                last_request = self._last_request_time['nasdaq']
                sleep_time = self.NASDAQ_DELAY - (now - last_request).total_seconds()
                if sleep_time > 0:
                    time.sleep(sleep_time)
                self._last_request_time['nasdaq'] = datetime.now()
                return True
                
            elif api == 'nyse':
                last_request = self._last_request_time['nyse']
                sleep_time = self.NYSE_DELAY - (now - last_request).total_seconds()
                if sleep_time > 0:
                    time.sleep(sleep_time)
                self._last_request_time['nyse'] = datetime.now()
                return True
                
            elif api == 'sec':
                last_request = self._last_request_time['sec']
                sleep_time = self.SEC_DELAY - (now - last_request).total_seconds()
                if sleep_time > 0:
                    time.sleep(sleep_time)
                self._last_request_time['sec'] = datetime.now()
                return True

            elif api == 'fmp':
                # Check if we're on a new day
                current_date = now.date()
                if current_date != self._fmp_day_start:
                    self._fmp_daily_count = 0
                    self._fmp_day_start = current_date
                    self._save_daily_count()

                # Check daily limit with more conservative handling
                remaining_calls = self.FMP_DAILY_LIMIT - self._fmp_daily_count
                if remaining_calls <= self.RESERVED_CALLS:
                    return False

                # Reset minute counter if needed
                if now - self._fmp_minute_start > timedelta(minutes=1):
                    self._fmp_minute_count = 0
                    self._fmp_minute_start = now
                    self._current_backoff = self.initial_backoff  # Reset backoff on successful reset
                
                # Check minute limit with exponential backoff
                while self._fmp_minute_count >= self.FMP_MINUTE_LIMIT:
                    sleep_time = min(
                        self._current_backoff,
                        60 - (now - self._fmp_minute_start).total_seconds()
                    )
                    if sleep_time > 0:
                        time.sleep(sleep_time)
                    
                    # Update counters and check again
                    now = datetime.now()
                    if now - self._fmp_minute_start > timedelta(minutes=1):
                        self._fmp_minute_count = 0
                        self._fmp_minute_start = now
                        self._current_backoff = self.initial_backoff
                    else:
                        # Increase backoff if we're still rate limited
                        self._current_backoff = min(
                            self._current_backoff * self.backoff_factor,
                            self.max_backoff
                        )
                
                # Enforce minimum delay between requests
                last_request = self._last_request_time['fmp']
                sleep_time = self.FMP_DELAY - (now - last_request).total_seconds()
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
                # Update counters
                self._last_request_time['fmp'] = datetime.now()
                self._fmp_minute_count += 1
                self._fmp_daily_count += 1
                self._save_daily_count()
                
                return True

        return True

    def yahoo_wait(self, symbol: str) -> bool:
        """Rate limit Yahoo Finance API requests."""
        return self._wait_if_needed('yahoo', symbol)

    def nasdaq_wait(self) -> bool:
        """Rate limit NASDAQ FTP requests."""
        return self._wait_if_needed('nasdaq')

    def nyse_wait(self) -> bool:
        """Rate limit NYSE API requests."""
        return self._wait_if_needed('nyse')

    def sec_wait(self) -> bool:
        """Rate limit SEC API requests."""
        return self._wait_if_needed('sec')

    def fmp_wait(self, is_initial_quote: bool = False) -> bool:
        """
        Rate limit FMP API requests.
        Returns True if request can proceed, False if daily limit reached.
        """
        return self._wait_if_needed('fmp', is_initial_quote=is_initial_quote)

    def get_remaining_daily_calls(self) -> int:
        """Get remaining FMP API calls for the day."""
        return max(0, self.FMP_DAILY_LIMIT - self._fmp_daily_count)

    def get_reserved_calls(self) -> int:
        """Get number of reserved API calls."""
        return self.RESERVED_CALLS
