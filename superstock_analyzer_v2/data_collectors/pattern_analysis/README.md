# Pattern Analysis Package

## Overview

This package provides a comprehensive solution for analyzing technical patterns in financial data. It has been refactored to follow SOLID principles and improve maintainability through specialized modules.

## Structure

```
pattern_analysis/
├── analyzers/
│   ├── base_pattern.py      # Base pattern analysis interfaces
│   └── base_formation.py    # Base pattern implementation
├── calculators/
│   └── technical_indicators.py  # Technical indicator calculations
├── utils/
│   └── pattern_utils.py     # Common pattern analysis utilities
└── __init__.py             # Package interface
```

## Usage

### Basic Usage

```python
from data_collectors.pattern_analysis import create_analyzer, create_indicator_calculator

# Create pattern analyzer
analyzer = create_analyzer()

# Create indicator calculator
calculator = create_indicator_calculator()

# Analyze patterns in data
pattern = analyzer.analyze(data)

# Calculate technical indicators
indicators = calculator.calculate_all(data)
```

### Using Individual Components

```python
from data_collectors.pattern_analysis import (
    BaseFormationAnalyzer,
    TechnicalIndicators,
    PatternUtils,
    IndicatorConfig
)

# Configure and use technical indicators
config = IndicatorConfig(
    sma_periods=[10, 20, 50],
    rsi_period=14
)
calculator = TechnicalIndicators(config)

# Use pattern utilities
levels = PatternUtils.find_price_levels(data)
volume_profile = PatternUtils.analyze_volume_profile(data)
```

## Features

### Pattern Analysis
- Base pattern detection and analysis
- Support and resistance level identification
- Volume pattern analysis
- Consolidation detection

### Technical Indicators
- Moving averages (SMA, EMA)
- Momentum indicators (RSI, MACD)
- Volatility indicators (Bollinger Bands, ATR)
- Volume indicators (OBV)

### Pattern Utilities
- Price level detection
- Volume profile analysis
- Volatility analysis
- Momentum analysis
- Price action analysis

## Configuration

Configuration can be accessed and modified through the package interface:

```python
from data_collectors.pattern_analysis import get_config

# Get current configuration
config = get_config()

# Configuration includes:
# - Base pattern settings
# - Technical indicator settings
# - Pattern detection thresholds
```

## Pattern Detection

The package includes comprehensive pattern detection capabilities:

### Base Patterns
- Minimum length requirements
- Depth analysis
- Volume characteristics
- Price tightness measurement
- Breakout potential calculation

### Price Levels
- Support and resistance detection
- Level strength calculation
- Touch point analysis
- Date range tracking

### Volume Analysis
- Average volume calculation
- Volume trend detection
- Relative volume analysis
- Accumulation/distribution detection

## Technical Analysis

The technical analysis components provide:

### Indicator Calculation
- Configurable periods
- Multiple timeframe support
- Comprehensive indicator suite
- Efficient calculation methods

### Pattern Validation
- Data structure validation
- Value range checking
- Pattern requirement verification
- Signal confirmation

## Best Practices

1. Use factory functions for creating analyzers:
```python
from data_collectors.pattern_analysis import create_analyzer

analyzer = create_analyzer(config={
    'base_pattern': {
        'min_base_length': 20,
        'max_base_depth': 0.3
    }
})
```

2. Configure technical indicators appropriately:
```python
from data_collectors.pattern_analysis import create_indicator_calculator

calculator = create_indicator_calculator({
    'sma_periods': [10, 20, 50, 200],
    'rsi_period': 14
})
```

3. Use pattern utilities for common operations:
```python
from data_collectors.pattern_analysis import PatternUtils

levels = PatternUtils.find_price_levels(data)
consolidation = PatternUtils.detect_consolidation(data)
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
pytest tests/test_pattern_analyzer.py
```

## Version History

- 2.0.0: Major refactor into specialized modules
- 1.0.0: Initial monolithic implementation
