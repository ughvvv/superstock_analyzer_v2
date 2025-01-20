"""Financial data collection package.

This package provides tools for collecting and analyzing financial data from various sources.
It includes specialized collectors for different types of financial statements, data processors,
and caching mechanisms.
"""

from .financial_collector import FinancialCollector
from .collectors.income_collector import IncomeCollector
from .collectors.balance_sheet_collector import BalanceSheetCollector
from .collectors.cash_flow_collector import CashFlowCollector
from .processors.data_validator import FinancialDataValidator
from .processors.growth_calculator import GrowthCalculator
from .cache.cache_manager import CacheManager

__all__ = [
    'FinancialCollector',
    'IncomeCollector',
    'BalanceSheetCollector',
    'CashFlowCollector',
    'FinancialDataValidator',
    'GrowthCalculator',
    'CacheManager'
]

# Version of the financial package
__version__ = '2.0.0'

# Package metadata
__author__ = 'Blake Cole'
__description__ = 'Financial data collection and analysis tools'

# Configuration defaults
DEFAULT_CACHE_DIR = 'cache'
DEFAULT_TTL = 3600  # 1 hour in seconds

# API configuration
API_BASE_URL = 'https://financialmodelingprep.com/api/v3'
API_RATE_LIMIT = 300  # requests per minute
API_TIMEOUT = 30  # seconds

# Batch processing configuration
BATCH_SIZE = 5
BATCH_DELAY = 1  # seconds between batches

# Data validation thresholds
VALIDATION_THRESHOLDS = {
    'growth_rate_max': 10.0,  # 1000% maximum growth rate
    'ratio_max': 10.0,        # Maximum for most financial ratios
    'working_capital_delta': 1.0,  # Maximum allowed difference in working capital calculation
    'balance_sheet_delta': 1.0     # Maximum allowed difference in balance sheet equation
}

# Growth calculation settings
GROWTH_SETTINGS = {
    'min_periods': 4,         # Minimum periods needed for growth calculation
    'trend_threshold': 0.5,   # Threshold for determining trend direction
    'volatility_penalty': 0.3 # Weight of volatility penalty in growth quality
}

def create_collector(api_key: str, cache_dir: str = DEFAULT_CACHE_DIR) -> FinancialCollector:
    """Create a new instance of FinancialCollector.
    
    This is the recommended way to instantiate a collector, as it ensures proper
    initialization and configuration.
    
    Args:
        api_key: API key for Financial Modeling Prep
        cache_dir: Directory for caching data (default: 'cache')
        
    Returns:
        Configured FinancialCollector instance
    """
    return FinancialCollector(api_key=api_key, cache_dir=cache_dir)

def get_version() -> str:
    """Get the current version of the financial package.
    
    Returns:
        Version string
    """
    return __version__

def get_config() -> dict:
    """Get the current configuration settings.
    
    Returns:
        Dictionary containing all configuration settings
    """
    return {
        'cache_dir': DEFAULT_CACHE_DIR,
        'ttl': DEFAULT_TTL,
        'api': {
            'base_url': API_BASE_URL,
            'rate_limit': API_RATE_LIMIT,
            'timeout': API_TIMEOUT
        },
        'batch': {
            'size': BATCH_SIZE,
            'delay': BATCH_DELAY
        },
        'validation': VALIDATION_THRESHOLDS,
        'growth': GROWTH_SETTINGS
    }
