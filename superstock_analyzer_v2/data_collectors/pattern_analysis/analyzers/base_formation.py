import logging
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from dataclasses import dataclass
from .base_pattern import BasePatternAnalyzer, BasePattern, PatternMetrics

logger = logging.getLogger(__name__)

@dataclass
class BaseFormationProperties:
    """Properties specific to base formations."""
    depth: float  # Maximum price decline from start
    width: int   # Number of days in formation
    height: float  # Price range within formation
    volume_contraction: float  # Degree of volume contraction
    price_tightness: float  # Measure of price consolidation
    breakout_potential: float  # Score indicating breakout likelihood

@dataclass
class BaseFormationSignals:
    """Trading signals for base formations."""
    entry_price: float
    stop_loss: float
    target_price: float
    risk_reward_ratio: float
    breakout_trigger: float

class BaseFormationAnalyzer(BasePatternAnalyzer):
    """Analyzer specifically for base formations."""
    
    def __init__(self, config: Dict = None):
        """Initialize the base formation analyzer.
        
        Args:
            config: Optional configuration dictionary
        """
        super().__init__(config)
        self.min_base_length = self.config.get('min_base_length', 20)
        self.max_base_depth = self.config.get('max_base_depth', 0.3)  # 30% maximum decline
        self.min_price_tightness = self.config.get('min_price_tightness', 0.7)
        self.min_volume_contraction = self.config.get('min_volume_contraction', 0.5)
        
    def analyze(self, data: pd.DataFrame) -> BasePattern:
        """Analyze price action for base pattern formation.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            BasePattern object containing analysis results
        """
        try:
            if not self._validate_input_data(data):
                return self._create_invalid_pattern()
                
            # Find potential base period
            base_period = self._find_base_period(data)
            if base_period is None:
                return self._create_invalid_pattern()
                
            # Extract base data
            base_data = data.iloc[base_period[0]:base_period[1]]
            
            # Calculate base properties
            properties = self._calculate_base_properties(base_data)
            
            # Calculate base metrics
            metrics = self._calculate_base_metrics(base_data)
            
            # Generate trading signals
            signals = self._generate_signals(base_data, properties)
            
            # Create pattern object
            pattern = BasePattern(
                is_valid=True,
                metrics=metrics,
                pattern_type='base_formation',
                sub_type=self._determine_base_type(properties),
                properties=properties.__dict__,
                signals=signals.__dict__
            )
            
            return pattern if self.validate(pattern) else self._create_invalid_pattern()
            
        except Exception as e:
            logger.error(f"Error analyzing base formation: {str(e)}")
            return self._create_invalid_pattern()
            
    def validate(self, pattern: BasePattern) -> bool:
        """Validate a detected base pattern.
        
        Args:
            pattern: BasePattern object to validate
            
        Returns:
            bool indicating if pattern is valid
        """
        try:
            if not pattern.properties:
                return False
                
            props = pattern.properties
            
            # Validate base dimensions
            if props['width'] < self.min_base_length:
                logger.debug(f"Base too short: {props['width']} days")
                return False
                
            if props['depth'] > self.max_base_depth:
                logger.debug(f"Base too deep: {props['depth']:.2%}")
                return False
                
            # Validate price action
            if props['price_tightness'] < self.min_price_tightness:
                logger.debug(f"Price action too loose: {props['price_tightness']:.2f}")
                return False
                
            # Validate volume
            if props['volume_contraction'] < self.min_volume_contraction:
                logger.debug(f"Insufficient volume contraction: {props['volume_contraction']:.2f}")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error validating base pattern: {str(e)}")
            return False
            
    def _find_base_period(self, data: pd.DataFrame) -> Optional[Tuple[int, int]]:
        """Find the most recent base pattern period.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            Tuple of (start_index, end_index) or None if no base found
        """
        try:
            # Calculate volatility
            data['atr'] = self._calculate_atr(data)
            data['volatility'] = data['atr'] / data['close']
            
            # Calculate volume moving averages
            data['vol_ma20'] = data['volume'].rolling(window=20).mean()
            
            # Look for periods of decreasing volatility and volume
            potential_bases = []
            
            for i in range(len(data) - self.min_base_length):
                window = data.iloc[i:i+self.min_base_length]
                
                # Check volatility contraction
                vol_start = window['volatility'].iloc[:5].mean()
                vol_end = window['volatility'].iloc[-5:].mean()
                vol_contraction = (vol_start - vol_end) / vol_start
                
                # Check volume contraction
                volume_start = window['volume'].iloc[:5].mean()
                volume_end = window['volume'].iloc[-5:].mean()
                volume_contraction = (volume_start - volume_end) / volume_start
                
                # Check price range
                price_range = (window['high'].max() - window['low'].min()) / window['low'].min()
                
                # Score the potential base
                score = (
                    vol_contraction * 0.4 +
                    volume_contraction * 0.3 +
                    (1 - min(price_range / self.max_base_depth, 1)) * 0.3
                )
                
                if score > 0.7:  # Minimum score threshold
                    potential_bases.append((i, i+self.min_base_length, score))
                    
            if not potential_bases:
                return None
                
            # Return the highest scoring base
            potential_bases.sort(key=lambda x: x[2], reverse=True)
            return potential_bases[0][:2]
            
        except Exception as e:
            logger.error(f"Error finding base period: {str(e)}")
            return None
            
    def _calculate_base_properties(self, data: pd.DataFrame) -> BaseFormationProperties:
        """Calculate properties specific to base formations.
        
        Args:
            data: DataFrame with base period data
            
        Returns:
            BaseFormationProperties object
        """
        try:
            # Calculate dimensions
            depth = (data['high'].max() - data['low'].min()) / data['high'].max()
            width = len(data)
            height = (data['high'].max() - data['low'].min()) / data['low'].mean()
            
            # Calculate volume contraction
            volume_start = data['volume'].iloc[:5].mean()
            volume_end = data['volume'].iloc[-5:].mean()
            volume_contraction = (volume_start - volume_end) / volume_start
            
            # Calculate price tightness
            price_tightness = 1 - (data['high'].std() / data['high'].mean())
            
            # Calculate breakout potential
            breakout_potential = self._calculate_breakout_potential(data)
            
            return BaseFormationProperties(
                depth=depth,
                width=width,
                height=height,
                volume_contraction=volume_contraction,
                price_tightness=price_tightness,
                breakout_potential=breakout_potential
            )
            
        except Exception as e:
            logger.error(f"Error calculating base properties: {str(e)}")
            return None
            
    def _calculate_breakout_potential(self, data: pd.DataFrame) -> float:
        """Calculate the potential for a breakout.
        
        Args:
            data: DataFrame with base period data
            
        Returns:
            float indicating breakout potential (0 to 1)
        """
        try:
            # Factors contributing to breakout potential
            factors = {
                'volume_contraction': 0.0,  # Higher is better
                'price_tightness': 0.0,     # Higher is better
                'support_tests': 0.0,       # More tests is better
                'resistance_proximity': 0.0  # Closer to resistance is better
            }
            
            # Volume contraction
            vol_start = data['volume'].iloc[:5].mean()
            vol_end = data['volume'].iloc[-5:].mean()
            factors['volume_contraction'] = min((vol_start - vol_end) / vol_start, 1)
            
            # Price tightness
            price_range = (data['high'].std() / data['high'].mean())
            factors['price_tightness'] = 1 - min(price_range * 5, 1)
            
            # Support tests
            support = data['low'].quantile(0.1)
            support_tests = sum(1 for x in data['low'] if abs(x - support) / support < 0.01)
            factors['support_tests'] = min(support_tests / 3, 1)
            
            # Resistance proximity
            resistance = data['high'].quantile(0.9)
            current_price = data['close'].iloc[-1]
            factors['resistance_proximity'] = 1 - min((resistance - current_price) / resistance, 1)
            
            # Calculate weighted score
            weights = {
                'volume_contraction': 0.3,
                'price_tightness': 0.3,
                'support_tests': 0.2,
                'resistance_proximity': 0.2
            }
            
            score = sum(factor * weights[name] for name, factor in factors.items())
            return score
            
        except Exception as e:
            logger.error(f"Error calculating breakout potential: {str(e)}")
            return 0.0
            
    def _generate_signals(self, data: pd.DataFrame, properties: BaseFormationProperties) -> BaseFormationSignals:
        """Generate trading signals for the base pattern.
        
        Args:
            data: DataFrame with base period data
            properties: BaseFormationProperties object
            
        Returns:
            BaseFormationSignals object
        """
        try:
            # Calculate key levels
            resistance = data['high'].quantile(0.9)
            support = data['low'].quantile(0.1)
            current_price = data['close'].iloc[-1]
            
            # Entry price is slightly above resistance
            entry_price = resistance * 1.02
            
            # Stop loss is slightly below support
            stop_loss = support * 0.98
            
            # Target is based on the pattern height
            pattern_height = resistance - support
            target_price = entry_price + (pattern_height * 2)
            
            # Calculate risk/reward
            risk = entry_price - stop_loss
            reward = target_price - entry_price
            risk_reward_ratio = reward / risk if risk != 0 else 0
            
            # Breakout trigger is between current price and resistance
            breakout_trigger = resistance * 1.01
            
            return BaseFormationSignals(
                entry_price=entry_price,
                stop_loss=stop_loss,
                target_price=target_price,
                risk_reward_ratio=risk_reward_ratio,
                breakout_trigger=breakout_trigger
            )
            
        except Exception as e:
            logger.error(f"Error generating signals: {str(e)}")
            return None
            
    def _determine_base_type(self, properties: BaseFormationProperties) -> str:
        """Determine the specific type of base formation.
        
        Args:
            properties: BaseFormationProperties object
            
        Returns:
            String indicating base type
        """
        try:
            # Classify based on properties
            if properties.width >= 40:
                return 'saucer'
            elif properties.price_tightness > 0.8:
                return 'tight'
            elif properties.depth < 0.15:
                return 'shallow'
            else:
                return 'standard'
                
        except Exception as e:
            logger.error(f"Error determining base type: {str(e)}")
            return 'unknown'
            
    def _create_invalid_pattern(self) -> BasePattern:
        """Create an invalid base pattern object."""
        return BasePattern(
            is_valid=False,
            metrics=None,
            pattern_type='base_formation',
            sub_type=None,
            properties=None,
            signals=None
        )
