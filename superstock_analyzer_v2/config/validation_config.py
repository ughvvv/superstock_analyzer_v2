"""
Centralized configuration for data validation thresholds and parameters.
"""

# Market Data Thresholds
MARKET_THRESHOLDS = {
    'min_volume': 25000,          # Minimum daily trading volume
    'min_market_cap': 25e6,       # Minimum market cap ($25M)
    'max_market_cap': 10e9,       # Maximum market cap ($10B)
    'min_price': 1.0,             # Minimum stock price
    'min_earnings_growth': 0.15,  # Minimum earnings growth (15%)
    'max_debt_to_equity': 0.75,   # Maximum debt-to-equity ratio
    'min_relative_strength': 80   # Minimum relative strength percentile
}

# Data Quality Thresholds
DATA_QUALITY = {
    'min_price_history_days': 20,    # Minimum days of price history
    'min_volume_history_days': 20,   # Minimum days of volume history
    'min_financial_periods': 4,      # Minimum quarters of financial data
    'max_data_age_minutes': 15,      # Maximum age of market data
    'min_sentiment_score': 0.0,      # Minimum sentiment score
    'max_sentiment_score': 1.0       # Maximum sentiment score
}

# API Configuration
API_CONFIG = {
    'max_retries': 3,               # Maximum number of retry attempts
    'retry_delay': 1.0,             # Initial retry delay in seconds
    'max_delay': 30.0,              # Maximum retry delay in seconds
    'timeout': 30,                  # Request timeout in seconds
    'batch_size': 25,              # Optimal batch size for requests
    'max_requests_per_minute': 100  # Rate limit for API requests
}

# Cache Configuration
CACHE_CONFIG = {
    'market_data_ttl': 300,         # Market data cache TTL (5 minutes)
    'financial_data_ttl': 86400,    # Financial data cache TTL (24 hours)
    'technical_data_ttl': 3600,     # Technical data cache TTL (1 hour)
    'qualitative_data_ttl': 86400,  # Qualitative data cache TTL (24 hours)
    'max_cache_size': 1000,         # Maximum number of items in memory cache
    'cache_warm_threshold': 0.8     # Cache warming threshold (80% of max)
}

# Validation Requirements
REQUIRED_FIELDS = {
    'market_data': [
        'symbol',
        'price',
        'volume',
        'marketCap'
    ],
    'financial_data': [
        'revenue',
        'earnings',
        'assets',
        'liabilities'
    ],
    'technical_data': [
        'close_prices',
        'volumes',
        'indicators'
    ],
    'qualitative_data': [
        'sentiment_score',
        'key_points',
        'risks',
        'opportunities'
    ]
}

# Scoring Weights
SCORING_WEIGHTS = {
    'fundamental_factors': {
        'earnings_quality': 18,
        'financial_health': 17,
        'company_structure': 10
    },
    'technical_factors': {
        'base_formation': 10,
        'breakout_quality': 8,
        'relative_strength': 7
    },
    'qualitative_factors': {
        'super_theme': 12,
        'insider_activity': 10,
        'management_quality': 8
    }
}

# Error Recovery Configuration
ERROR_RECOVERY = {
    'max_batch_retries': 3,         # Maximum retries for batch operations
    'batch_backoff_factor': 2,      # Exponential backoff factor
    'circuit_breaker_threshold': 5,  # Failures before circuit breaker trips
    'circuit_breaker_timeout': 300   # Circuit breaker timeout (5 minutes)
}

# Monitoring Configuration
MONITORING = {
    'log_level': 'INFO',
    'metrics_collection_interval': 60,  # Collect metrics every minute
    'alert_thresholds': {
        'error_rate': 0.1,             # Alert if error rate exceeds 10%
        'api_latency': 2.0,            # Alert if API latency exceeds 2 seconds
        'validation_failure_rate': 0.2  # Alert if validation failures exceed 20%
    }
}
