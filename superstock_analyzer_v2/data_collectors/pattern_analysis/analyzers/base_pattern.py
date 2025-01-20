import logging
from typing import Dict, List, Optional, Protocol
from dataclasses import dataclass
from datetime import datetime
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class PatternMetrics:
    """Base metrics for any pattern analysis."""
    start_date: datetime
    end_date: datetime
    length: int
    confidence: float
    score: float
    volume_profile: Dict[str, float]
    price_levels: Dict[str, float]

@dataclass
class BasePattern:
    """Base class for all pattern types."""
    is_valid: bool
    metrics: PatternMetrics
    pattern_type: str
    sub_type: Optional[str] = None
    properties: Dict = None
    signals: Dict = None

class PatternAnalyzer(Protocol):
    """Protocol defining the interface for pattern analyzers."""
    
    def analyze(self, data: pd.DataFrame) -> BasePattern:
        """Analyze data for pattern formation.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            BasePattern object containing analysis results
        """
        ...
        
    def validate(self, pattern: BasePattern) -> bool:
        """Validate a detected pattern.
        
        Args:
            pattern: BasePattern object to validate
            
        Returns:
            bool indicating if pattern is valid
        """
        ...

class BasePatternAnalyzer:
    """Base class for implementing pattern analyzers."""
    
    def __init__(self, config: Dict = None):
        """Initialize the pattern analyzer.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        
    def _validate_input_data(self, data: pd.DataFrame) -> bool:
        """Validate input data requirements.
        
        Args:
            data: DataFrame to validate
            
        Returns:
            bool indicating if data is valid
        """
        try:
            # Check required columns
            required_columns = {'open', 'high', 'low', 'close', 'volume'}
            if not all(col in data.columns for col in required_columns):
                logger.error(f"Missing required columns. Found: {data.columns.tolist()}")
                return False
                
            # Check data types
            expected_types = {
                'open': np.floating,
                'high': np.floating,
                'low': np.floating,
                'close': np.floating,
                'volume': np.floating
            }
            
            for col, expected_type in expected_types.items():
                if not np.issubdtype(data[col].dtype, expected_type):
                    logger.error(f"Invalid type for {col}: {data[col].dtype}")
                    return False
                    
            # Check for minimum data points
            min_points = self.config.get('min_data_points', 20)
            if len(data) < min_points:
                logger.error(f"Insufficient data points. Found: {len(data)}, Required: {min_points}")
                return False
                
            # Check for missing values
            if data[list(required_columns)].isnull().any().any():
                logger.error("Data contains missing values")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error validating input data: {str(e)}")
            return False
            
    def _calculate_base_metrics(self, data: pd.DataFrame) -> PatternMetrics:
        """Calculate base metrics for pattern analysis.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            PatternMetrics object
        """
        try:
            # Calculate basic metrics
            start_date = data.index[0]
            end_date = data.index[-1]
            length = len(data)
            
            # Calculate volume profile
            volume_profile = {
                'avg_volume': data['volume'].mean(),
                'volume_trend': self._calculate_volume_trend(data),
                'volume_consistency': self._calculate_volume_consistency(data)
            }
            
            # Calculate price levels
            price_levels = {
                'support': self._find_support_level(data),
                'resistance': self._find_resistance_level(data),
                'pivot': self._find_pivot_points(data)
            }
            
            # Calculate pattern confidence and score
            confidence = self._calculate_confidence(data)
            score = self._calculate_score(data)
            
            return PatternMetrics(
                start_date=start_date,
                end_date=end_date,
                length=length,
                confidence=confidence,
                score=score,
                volume_profile=volume_profile,
                price_levels=price_levels
            )
            
        except Exception as e:
            logger.error(f"Error calculating base metrics: {str(e)}")
            return None
            
    def _calculate_volume_trend(self, data: pd.DataFrame) -> float:
        """Calculate volume trend strength.
        
        Args:
            data: DataFrame with volume data
            
        Returns:
            float indicating trend strength (-1 to 1)
        """
        try:
            x = np.arange(len(data))
            y = data['volume'].values
            slope, _ = np.polyfit(x, y, 1)
            return slope / data['volume'].mean()  # Normalize slope
            
        except Exception as e:
            logger.error(f"Error calculating volume trend: {str(e)}")
            return 0.0
            
    def _calculate_volume_consistency(self, data: pd.DataFrame) -> float:
        """Calculate volume consistency score.
        
        Args:
            data: DataFrame with volume data
            
        Returns:
            float indicating consistency (0 to 1)
        """
        try:
            volume_mean = data['volume'].mean()
            volume_std = data['volume'].std()
            cv = volume_std / volume_mean if volume_mean != 0 else float('inf')
            return 1 / (1 + cv)  # Convert to 0-1 score
            
        except Exception as e:
            logger.error(f"Error calculating volume consistency: {str(e)}")
            return 0.0
            
    def _find_support_level(self, data: pd.DataFrame) -> float:
        """Find key support level.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            float indicating support price level
        """
        try:
            # Use recent lows to find support
            recent_lows = data['low'].tail(10).values
            return np.percentile(recent_lows, 10)
            
        except Exception as e:
            logger.error(f"Error finding support level: {str(e)}")
            return data['low'].min()
            
    def _find_resistance_level(self, data: pd.DataFrame) -> float:
        """Find key resistance level.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            float indicating resistance price level
        """
        try:
            # Use recent highs to find resistance
            recent_highs = data['high'].tail(10).values
            return np.percentile(recent_highs, 90)
            
        except Exception as e:
            logger.error(f"Error finding resistance level: {str(e)}")
            return data['high'].max()
            
    def _find_pivot_points(self, data: pd.DataFrame) -> Dict[str, float]:
        """Calculate pivot points.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            Dictionary containing pivot levels
        """
        try:
            last_day = data.iloc[-1]
            pivot = (last_day['high'] + last_day['low'] + last_day['close']) / 3
            
            return {
                'pivot': pivot,
                'r1': 2 * pivot - last_day['low'],
                's1': 2 * pivot - last_day['high']
            }
            
        except Exception as e:
            logger.error(f"Error calculating pivot points: {str(e)}")
            return {'pivot': 0.0, 'r1': 0.0, 's1': 0.0}
            
    def _calculate_confidence(self, data: pd.DataFrame) -> float:
        """Calculate pattern confidence score.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            float indicating confidence (0 to 1)
        """
        try:
            # This should be implemented by specific pattern analyzers
            return 0.5
            
        except Exception as e:
            logger.error(f"Error calculating confidence: {str(e)}")
            return 0.0
            
    def _calculate_score(self, data: pd.DataFrame) -> float:
        """Calculate overall pattern score.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            float indicating pattern score (0 to 1)
        """
        try:
            # This should be implemented by specific pattern analyzers
            return 0.5
            
        except Exception as e:
            logger.error(f"Error calculating score: {str(e)}")
            return 0.0
