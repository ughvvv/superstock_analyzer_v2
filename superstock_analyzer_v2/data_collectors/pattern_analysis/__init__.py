"""Pattern analysis package.

This package provides tools for analyzing technical patterns in financial data.
It includes specialized analyzers for different pattern types, technical indicators,
and utility functions for pattern detection and analysis.
"""

from .analyzers.base_pattern import BasePattern, PatternMetrics, PatternAnalyzer
from .analyzers.base_formation import BaseFormationAnalyzer, BaseFormationProperties, BaseFormationSignals
from .calculators.technical_indicators import TechnicalIndicators, IndicatorConfig
from .utils.pattern_utils import PatternUtils, PriceLevel, VolumeProfile

__all__ = [
    'BasePattern',
    'PatternMetrics',
    'PatternAnalyzer',
    'BaseFormationAnalyzer',
    'BaseFormationProperties',
    'BaseFormationSignals',
    'TechnicalIndicators',
    'IndicatorConfig',
    'PatternUtils',
    'PriceLevel',
    'VolumeProfile'
]

# Version of the pattern analysis package
__version__ = '2.0.0'

# Package metadata
__author__ = 'Blake Cole'
__description__ = 'Technical pattern analysis tools'

# Configuration defaults
DEFAULT_CONFIG = {
    'base_pattern': {
        'min_base_length': 20,
        'max_base_depth': 0.3,
        'min_touches': 3,
        'resistance_threshold': 0.02,
        'support_threshold': 0.02
    },
    'volume_pattern': {
        'min_contraction': 0.5,
        'min_consistency': 0.7,
        'volume_threshold': 1.5
    },
    'scoring_weights': {
        'price_tightness_weight': 30,
        'volume_pattern_weights': {
            'contraction': 25,
            'expansion': 15,
            'neutral': 10
        },
        'consolidation_weight': 25,
        'depth_weight': 20
    }
}

# Technical indicator settings
INDICATOR_SETTINGS = {
    'sma_periods': [10, 20, 50, 200],
    'ema_periods': [9, 21],
    'rsi_period': 14,
    'macd_periods': (12, 26, 9),
    'bb_period': 20,
    'bb_std': 2.0,
    'atr_period': 14
}

# Pattern detection thresholds
PATTERN_THRESHOLDS = {
    'price_level': {
        'touch_threshold': 0.02,
        'min_touches': 3,
        'strength_threshold': 0.7
    },
    'consolidation': {
        'range_threshold': 0.3,
        'tightness_threshold': 0.7,
        'min_duration': 20
    },
    'breakout': {
        'volume_threshold': 1.5,
        'price_threshold': 0.02,
        'confirmation_period': 3
    }
}

def create_analyzer(config: dict = None) -> BaseFormationAnalyzer:
    """Create a new instance of BaseFormationAnalyzer.
    
    This is the recommended way to instantiate a pattern analyzer, as it ensures
    proper initialization and configuration.
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        Configured BaseFormationAnalyzer instance
    """
    return BaseFormationAnalyzer(config or DEFAULT_CONFIG)

def create_indicator_calculator(config: dict = None) -> TechnicalIndicators:
    """Create a new instance of TechnicalIndicators.
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        Configured TechnicalIndicators instance
    """
    indicator_config = IndicatorConfig(**{
        **INDICATOR_SETTINGS,
        **(config or {})
    })
    return TechnicalIndicators(indicator_config)

def get_version() -> str:
    """Get the current version of the pattern analysis package.
    
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
        'default_config': DEFAULT_CONFIG,
        'indicator_settings': INDICATOR_SETTINGS,
        'pattern_thresholds': PATTERN_THRESHOLDS
    }
