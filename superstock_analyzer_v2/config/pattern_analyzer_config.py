from dataclasses import dataclass
from typing import Dict

@dataclass
class BasePatternConfig:
    """Configuration for base pattern detection."""
    min_base_length: int = 30        # Minimum days for base formation
    max_base_length: int = 90        # Maximum days for base formation
    max_base_depth: float = 0.30     # Maximum depth as percentage (30%)
    min_touches: int = 3             # Minimum support/resistance touches
    support_threshold: float = 0.02   # 2% threshold for support levels
    resistance_threshold: float = 0.02 # 2% threshold for resistance levels
    volume_decline_threshold: float = 0.5  # 50% volume decline required
    price_tightness_threshold: float = 0.7 # 70% minimum tightness
    consolidation_threshold: float = 0.6   # 60% minimum consolidation score

@dataclass
class VolumePatternConfig:
    """Configuration for volume pattern analysis."""
    contraction_threshold: float = 0.5  # 50% volume decline for contraction
    expansion_threshold: float = 2.0    # 100% volume increase for expansion
    ma_period: int = 20                 # Moving average period for volume
    min_quiet_days: int = 10            # Minimum days of low volume
    relative_volume_threshold: float = 1.5  # Threshold for relative volume

@dataclass
class ScoringWeights:
    """Weights for different components in scoring."""
    price_tightness_weight: float = 30.0  # 30% weight
    consolidation_weight: float = 25.0    # 25% weight
    depth_weight: float = 20.0            # 20% weight
    volume_pattern_weights: Dict[str, float] = None

    def __post_init__(self):
        if self.volume_pattern_weights is None:
            self.volume_pattern_weights = {
                'contraction': 25.0,  # 25% weight for volume contraction
                'expansion': 15.0,    # 15% weight for volume expansion
                'neutral': 5.0        # 5% weight for neutral pattern
            }

@dataclass
class BreakoutCriteria:
    """Criteria for breakout detection."""
    min_volume_expansion: float = 2.0    # Minimum volume increase
    min_price_move: float = 0.03        # Minimum 3% price move
    ma_crossover_required: bool = True   # Require moving average crossover
    min_rs_rank: int = 80               # Minimum relative strength rank
    consolidation_required: bool = True  # Require prior consolidation

DEFAULT_CONFIG = {
    'base_pattern': BasePatternConfig(),
    'volume_pattern': VolumePatternConfig(),
    'scoring_weights': ScoringWeights(),
    'breakout_criteria': BreakoutCriteria(),
    
    # Additional pattern requirements
    'min_price': 1.0,                    # Minimum price filter
    'min_volume': 100000,                # Minimum volume filter
    'min_market_cap': 5e6,               # $5M minimum market cap
    'max_market_cap': 250e6,             # $250M maximum market cap
    
    # Moving average settings
    'ma_periods': {
        'short': 20,                     # 20-day MA
        'medium': 50,                    # 50-day MA
        'long': 200                      # 200-day MA
    },
    
    # Volume analysis settings
    'volume_analysis': {
        'decline_threshold': 0.5,        # 50% volume decline
        'expansion_threshold': 2.0,      # 100% volume expansion
        'ma_period': 50,                 # 50-day volume MA
        'relative_volume_periods': [5, 20, 50]  # Periods for relative volume
    },
    
    # Support/Resistance settings
    'support_resistance': {
        'touch_threshold': 0.02,         # 2% threshold for touches
        'min_touches': 3,                # Minimum number of touches
        'cluster_threshold': 0.03,       # 3% threshold for price clusters
        'confirmation_period': 5         # Days to confirm level
    },
    
    # Breakout validation
    'breakout_validation': {
        'min_volume_expansion': 2.0,     # Minimum volume expansion
        'min_price_percent': 0.03,       # Minimum price movement
        'consolidation_required': True,   # Require prior consolidation
        'ma_crossover_required': True,   # Require MA crossover
        'min_rs_rank': 80               # Minimum relative strength rank
    },
    
    # Pattern quality thresholds
    'quality_thresholds': {
        'min_tightness': 0.7,           # Minimum price tightness
        'min_consolidation': 0.6,       # Minimum consolidation score
        'max_volatility': 0.02,         # Maximum volatility
        'min_accumulation': 0.6         # Minimum accumulation score
    }
}
