import logging
from typing import Dict, List, Optional, Any, Union
import aiohttp
import asyncio
from datetime import datetime, timedelta
import numpy as np

from .statements import IncomeStatement, BalanceSheet, CashFlow
from .metrics import KeyMetrics, FinancialRatios
from .utils import validate_financial_data, calculate_growth_metrics

logger = logging.getLogger(__name__)

class FinancialDataCollector:
    """Collector for financial data from Financial Modeling Prep API."""
    
    def __init__(self, api_key: str):
        """Initialize the collector with API key."""
        self.api_key = api_key
        self._session = None
        self.base_url = "https://financialmodelingprep.com/api/v3"
        self.timeout = aiohttp.ClientTimeout(total=30)
        self.retry_delay = 1.0
        self.max_retries = 3
        self.max_delay = 30
        
        # Cache settings
        self.cache = {}
        self.cache_duration = timedelta(minutes=5)
        
    @property
    async def session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self.timeout)
        return self._session

    async def close(self):
        """Close the aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def get_financials_async(self, symbol: str) -> Optional[Dict]:
        """Get financial data for a symbol with proper structure."""
        try:
            # Check cache first
            cached_data = self._get_from_cache(symbol)
            if cached_data:
                return cached_data

            # Initialize data structure matching scorer expectations
            financial_data = {
                'growth_metrics': {
                    'quarterly': {},
                    'annual': {}
                },
                'financial_ratios': {},
                'financial_scores': {},
                'profitability': {},
                'working_capital_trend': {},
                'operating_leverage': {}
            }

            async with await self.session as session:
                # Fetch each type of data
                endpoints = [
                    ('income-statement', 8),
                    ('balance-sheet-statement', 8),
                    ('cash-flow-statement', 8),
                    ('key-metrics', 8),
                    ('ratios', 8)
                ]

                for endpoint, limit in endpoints:
                    data = await self._make_request(
                        session,
                        f"{self.base_url}/{endpoint}/{symbol}",
                        {'limit': limit, 'apikey': self.api_key}
                    )

                    if not data or not isinstance(data, list):
                        logger.warning(f"Missing or invalid {endpoint} data for {symbol}")
                        continue

                    # Sort statements by date
                    data.sort(key=lambda x: x['date'], reverse=True)

                    # Process different statement types
                    if endpoint == 'income-statement':
                        financial_data.update(self._process_income_statement(data))
                    elif endpoint == 'balance-sheet-statement':
                        financial_data.update(self._process_balance_sheet(data))
                    elif endpoint == 'cash-flow-statement':
                        financial_data.update(self._process_cash_flow(data))
                    elif endpoint == 'key-metrics':
                        financial_data['financial_ratios'].update(self._process_key_metrics(data))
                    elif endpoint == 'ratios':
                        financial_data['financial_ratios'].update(self._process_ratios(data))

                # Calculate comprehensive metrics
                if self._validate_financial_data(financial_data):
                    financial_data['growth_metrics'] = self._calculate_growth_metrics(financial_data)
                    financial_data['financial_scores'] = self._calculate_financial_scores(financial_data)
                    financial_data['working_capital_trend'] = self._calculate_working_capital_trend(financial_data)
                    financial_data['operating_leverage'] = self._calculate_operating_leverage(financial_data)
                    
                    # Cache valid data
                    self._add_to_cache(symbol, financial_data)
                    return financial_data
                else:
                    logger.warning(f"Invalid financial data structure for {symbol}")
                    return None

        except Exception as e:
            logger.error(f"Error getting financials for {symbol}: {str(e)}")
            return None
        finally:
            await self.close()

    def _process_income_statement(self, statements: List[Dict]) -> Dict:
        """Process income statement data."""
        try:
            if not statements:
                return {}

            latest = statements[0]
            year_ago = statements[4] if len(statements) > 4 else None

            return {
                'revenue': float(latest.get('revenue', 0)),
                'netIncome': float(latest.get('netIncome', 0)),
                'operatingIncome': float(latest.get('operatingIncome', 0)),
                'grossProfit': float(latest.get('grossProfit', 0)),
                'revenue_growth': (
                    (float(latest.get('revenue', 0)) - float(year_ago.get('revenue', 0))) / 
                    float(year_ago.get('revenue', 1)) if year_ago else 0
                ),
                'earnings_growth': (
                    (float(latest.get('netIncome', 0)) - float(year_ago.get('netIncome', 0))) / 
                    float(year_ago.get('netIncome', 1)) if year_ago else 0
                )
            }
        except Exception as e:
            logger.error(f"Error processing income statement: {str(e)}")
            return {}

    def _process_balance_sheet(self, statements: List[Dict]) -> Dict:
        """Process balance sheet data."""
        try:
            if not statements:
                return {}

            latest = statements[0]
            return {
                'totalAssets': float(latest.get('totalAssets', 0)),
                'totalLiabilities': float(latest.get('totalLiabilities', 0)),
                'totalCurrentAssets': float(latest.get('totalCurrentAssets', 0)),
                'totalCurrentLiabilities': float(latest.get('totalCurrentLiabilities', 0)),
                'longTermDebt': float(latest.get('longTermDebt', 0))
            }
        except Exception as e:
            logger.error(f"Error processing balance sheet: {str(e)}")
            return {}

    def _process_cash_flow(self, statements: List[Dict]) -> Dict:
        """Process cash flow statement data."""
        try:
            if not statements:
                return {}

            latest = statements[0]
            return {
                'operatingCashFlow': float(latest.get('operatingCashFlow', 0)),
                'capitalExpenditure': float(latest.get('capitalExpenditure', 0)),
                'freeCashFlow': float(latest.get('freeCashFlow', 0))
            }
        except Exception as e:
            logger.error(f"Error processing cash flow: {str(e)}")
            return {}

    def _process_key_metrics(self, metrics: List[Dict]) -> Dict:
        """Process key metrics data."""
        try:
            if not metrics:
                return {}

            latest = metrics[0]
            return {
                'peRatioTTM': float(latest.get('peRatioTTM', 0)),
                'pbRatioTTM': float(latest.get('pbRatioTTM', 0)),
                'debtToEquityTTM': float(latest.get('debtToEquityTTM', 0)),
                'currentRatioTTM': float(latest.get('currentRatioTTM', 0)),
                'quickRatioTTM': float(latest.get('quickRatioTTM', 0))
            }
        except Exception as e:
            logger.error(f"Error processing key metrics: {str(e)}")
            return {}

    def _process_ratios(self, ratios: List[Dict]) -> Dict:
        """Process financial ratios data."""
        try:
            if not ratios:
                return {}

            latest = ratios[0]
            return {
                'returnOnEquityTTM': float(latest.get('returnOnEquityTTM', 0)),
                'returnOnAssetsTTM': float(latest.get('returnOnAssetsTTM', 0)),
                'grossProfitMarginTTM': float(latest.get('grossProfitMarginTTM', 0)),
                'operatingProfitMarginTTM': float(latest.get('operatingProfitMarginTTM', 0)),
                'netProfitMarginTTM': float(latest.get('netProfitMarginTTM', 0))
            }
        except Exception as e:
            logger.error(f"Error processing ratios: {str(e)}")
            return {}

    async def _make_request(self, session: aiohttp.ClientSession, url: str, params: Dict) -> Optional[List[Dict]]:
        """Make a rate-limited request to FMP API with retries."""
        for attempt in range(self.max_retries):
            try:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 429:  # Rate limit
                        delay = self.retry_delay * (2 ** attempt)
                        await asyncio.sleep(min(delay, self.max_delay))
                        continue
                    else:
                        logger.error(f"Request failed: {response.status}")
                        return None
            except Exception as e:
                logger.error(f"Request error: {str(e)}")
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    await asyncio.sleep(min(delay, self.max_delay))
                    continue
                return None
        return None

    def _validate_financial_data(self, data: Dict) -> bool:
        """Validate financial data structure and values."""
        try:
            if not isinstance(data, dict):
                return False

            # Check required sections
            required_sections = [
                'growth_metrics', 'financial_ratios', 'financial_scores',
                'profitability', 'working_capital_trend', 'operating_leverage'
            ]
            if not all(section in data for section in required_sections):
                return False

            # Validate growth metrics structure
            growth_metrics = data.get('growth_metrics', {})
            if not all(period in growth_metrics for period in ['quarterly', 'annual']):
                return False

            # Validate financial ratios
            ratios = data.get('financial_ratios', {})
            required_ratios = [
                'debtToEquityTTM', 'currentRatioTTM', 'quickRatioTTM',
                'returnOnEquityTTM', 'returnOnAssetsTTM'
            ]
            if not all(ratio in ratios for ratio in required_ratios):
                return False

            return True

        except Exception as e:
            logger.error(f"Error validating financial data: {str(e)}")
            return False

    def _add_to_cache(self, symbol: str, data: Dict) -> None:
        """Add data to cache with timestamp."""
        self.cache[symbol] = {
            'data': data,
            'timestamp': datetime.now()
        }

    def _get_from_cache(self, symbol: str) -> Optional[Dict]:
        """Get data from cache if available and not expired."""
        cached = self.cache.get(symbol)
        if cached:
            if datetime.now() - cached['timestamp'] < self.cache_duration:
                return cached['data']
            else:
                del self.cache[symbol]
        return None
