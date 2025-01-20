# Financial Data Collection Package

## Overview

This package provides a comprehensive solution for collecting and analyzing financial data from Financial Modeling Prep API. It has been refactored to follow SOLID principles and improve maintainability through specialized modules.

## Structure

```
financial/
├── collectors/
│   ├── income_collector.py      # Income statement collection
│   ├── balance_sheet_collector.py # Balance sheet collection
│   └── cash_flow_collector.py   # Cash flow statement collection
├── processors/
│   ├── data_validator.py        # Data validation logic
│   └── growth_calculator.py     # Growth metrics calculation
├── cache/
│   └── cache_manager.py         # Caching mechanism
├── financial_collector.py       # Main coordinator
└── __init__.py                 # Package interface
```

## Usage

### Basic Usage

```python
from data_collectors.financial import create_collector

# Create a collector instance
collector = create_collector(api_key='your_api_key')

# Get financial data for a single symbol
async with collector as c:
    data = await c.get_financial_data('AAPL')

# Get financial data for multiple symbols
async with collector as c:
    data = await c.get_batch_financial_data(['AAPL', 'GOOGL', 'MSFT'])
```

### Using Individual Components

```python
from data_collectors.financial import (
    IncomeCollector,
    BalanceSheetCollector,
    CashFlowCollector,
    FinancialDataValidator,
    GrowthCalculator
)

# Use specialized collectors
income_collector = IncomeCollector(api_key='your_api_key')
balance_collector = BalanceSheetCollector(api_key='your_api_key')
cash_flow_collector = CashFlowCollector(api_key='your_api_key')

# Use data processors
validator = FinancialDataValidator()
growth_calc = GrowthCalculator()
```

## Features

### Data Collection
- Specialized collectors for different financial statements
- Concurrent data fetching
- Automatic retry mechanism
- Rate limiting handling

### Data Processing
- Comprehensive data validation
- Growth metrics calculation
- Growth quality analysis
- Trend detection

### Caching
- Efficient caching mechanism
- Configurable TTL
- Cache statistics
- Automatic cleanup of expired entries

## Configuration

Configuration can be accessed and modified through the package interface:

```python
from data_collectors.financial import get_config

# Get current configuration
config = get_config()

# Configuration includes:
# - Cache settings
# - API settings
# - Batch processing settings
# - Validation thresholds
# - Growth calculation settings
```

## Data Validation

The package includes comprehensive validation of financial data:

- Income statement validation
- Balance sheet equation checking
- Cash flow statement validation
- Growth rate reasonableness checks
- Ratio range validation

## Growth Analysis

Growth metrics are calculated and analyzed across multiple dimensions:

- Sequential growth
- Year-over-year growth
- CAGR calculation
- Growth quality assessment
- Trend analysis

## Caching

The caching system provides:

- Separate caches for different data types
- Automatic cache invalidation
- Cache statistics tracking
- Configurable TTL per data type
- Disk-based persistence

## Error Handling

The package implements comprehensive error handling:

- Detailed logging
- Graceful degradation
- Automatic retries
- Rate limit handling
- Invalid data detection

## Best Practices

1. Always use the collector as an async context manager:
```python
async with create_collector(api_key='your_api_key') as collector:
    data = await collector.get_financial_data('AAPL')
```

2. Use batch processing for multiple symbols:
```python
async with create_collector(api_key='your_api_key') as collector:
    data = await collector.get_batch_financial_data(['AAPL', 'GOOGL'])
```

3. Check cache statistics periodically:
```python
stats = collector.get_cache_stats()
print(f"Cache hit rate: {stats['hit_rate']}")
```

4. Clean up expired cache entries regularly:
```python
removed = await collector.cleanup_cache()
print(f"Removed {removed} expired entries")
```

## Contributing

When contributing to this package:

1. Follow the existing module structure
2. Add appropriate validation and error handling
3. Include comprehensive logging
4. Add tests for new functionality
5. Update documentation as needed

## Testing

Tests are located in the `tests/` directory. Run tests using:

```bash
pytest tests/test_financial_data.py
```

## Version History

- 2.0.0: Major refactor into specialized modules
- 1.0.0: Initial monolithic implementation
