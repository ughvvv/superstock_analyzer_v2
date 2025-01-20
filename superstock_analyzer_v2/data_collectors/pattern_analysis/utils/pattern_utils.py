import logging
from typing import Dict, List, Optional, Tuple, Union
import pandas as pd
import numpy as np
from scipy import stats
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class PriceLevel:
    """Represents a significant price level."""
    price: float
    strength: float  # 0 to 1, indicating level strength
    touches: int    # Number of times price touched this level
    type: str      # 'support' or 'resistance'
    date_range: Tuple[pd.Timestamp, pd.Timestamp]

@dataclass
class VolumeProfile:
    """Represents volume characteristics."""
    average_volume: float
    volume_trend: float  # -1 to 1, indicating trend direction and strength
    relative_volume: float  # Current volume relative to average
    accumulation: bool  # True if showing accumulation characteristics

class PatternUtils:
    """Utility functions for pattern analysis."""
    
    @staticmethod
    def find_price_levels(data: pd.DataFrame, window: int = 20, threshold: float = 0.02) -> List[PriceLevel]:
        """Find significant price levels using kernel density estimation.
        
        Args:
            data: DataFrame with OHLCV data
            window: Rolling window for level detection
            threshold: Price proximity threshold for level touches
            
        Returns:
            List of PriceLevel objects
        """
        try:
            levels = []
            
            # Combine highs and lows for level detection
            prices = pd.concat([data['high'], data['low']])
            
            # Use KDE to find price clusters
            kde = stats.gaussian_kde(prices)
            price_range = np.linspace(prices.min(), prices.max(), 100)
            density = kde(price_range)
            
            # Find local maxima in density (potential levels)
            peaks = PatternUtils._find_peaks(density)
            potential_levels = price_range[peaks]
            
            for price in potential_levels:
                # Count touches
                touches = sum(
                    1 for x in prices
                    if abs(x - price) / price < threshold
                )
                
                # Determine if support or resistance
                price_data = data[
                    (data['high'] >= price * (1 - threshold)) &
                    (data['low'] <= price * (1 + threshold))
                ]
                
                if len(price_data) < 3:
                    continue
                    
                # Calculate level strength based on touches and bounces
                strength = min(touches / 5, 1.0)  # Cap at 1.0
                
                # Determine level type
                closes_above = (data['close'] > price).sum()
                closes_below = (data['close'] < price).sum()
                level_type = 'resistance' if closes_below > closes_above else 'support'
                
                levels.append(PriceLevel(
                    price=price,
                    strength=strength,
                    touches=touches,
                    type=level_type,
                    date_range=(data.index[0], data.index[-1])
                ))
                
            return sorted(levels, key=lambda x: x.strength, reverse=True)
            
        except Exception as e:
            logger.error(f"Error finding price levels: {str(e)}")
            return []
            
    @staticmethod
    def analyze_volume_profile(data: pd.DataFrame, window: int = 20) -> VolumeProfile:
        """Analyze volume characteristics.
        
        Args:
            data: DataFrame with OHLCV data
            window: Rolling window for volume analysis
            
        Returns:
            VolumeProfile object
        """
        try:
            # Calculate average volume
            avg_volume = data['volume'].rolling(window=window).mean().iloc[-1]
            
            # Calculate volume trend
            volume_trend = PatternUtils._calculate_trend_strength(data['volume'])
            
            # Calculate relative volume
            relative_volume = data['volume'].iloc[-1] / avg_volume
            
            # Detect accumulation
            price_trend = PatternUtils._calculate_trend_strength(data['close'])
            volume_price_correlation = data['volume'].corr(data['close'])
            accumulation = (
                price_trend > 0 and
                volume_trend > 0 and
                volume_price_correlation > 0.3
            )
            
            return VolumeProfile(
                average_volume=avg_volume,
                volume_trend=volume_trend,
                relative_volume=relative_volume,
                accumulation=accumulation
            )
            
        except Exception as e:
            logger.error(f"Error analyzing volume profile: {str(e)}")
            return None
            
    @staticmethod
    def calculate_volatility_profile(data: pd.DataFrame, window: int = 20) -> Dict[str, float]:
        """Calculate volatility characteristics.
        
        Args:
            data: DataFrame with OHLCV data
            window: Rolling window for volatility calculation
            
        Returns:
            Dictionary containing volatility metrics
        """
        try:
            # Calculate returns
            returns = data['close'].pct_change()
            
            # Calculate various volatility metrics
            profile = {
                'daily_volatility': returns.std(),
                'rolling_volatility': returns.rolling(window=window).std().iloc[-1],
                'high_low_volatility': ((data['high'] - data['low']) / data['close']).mean(),
                'volatility_trend': PatternUtils._calculate_trend_strength(
                    returns.rolling(window=window).std()
                )
            }
            
            return profile
            
        except Exception as e:
            logger.error(f"Error calculating volatility profile: {str(e)}")
            return {}
            
    @staticmethod
    def detect_consolidation(data: pd.DataFrame, window: int = 20) -> Dict[str, float]:
        """Detect and measure price consolidation.
        
        Args:
            data: DataFrame with OHLCV data
            window: Rolling window for consolidation detection
            
        Returns:
            Dictionary containing consolidation metrics
        """
        try:
            # Calculate price range
            high_low_range = (data['high'] - data['low']) / data['close']
            avg_range = high_low_range.rolling(window=window).mean()
            
            # Calculate range contraction
            range_contraction = (
                avg_range.iloc[0] - avg_range.iloc[-1]
            ) / avg_range.iloc[0] if avg_range.iloc[0] != 0 else 0
            
            # Calculate price tightness
            price_std = data['close'].rolling(window=window).std()
            price_mean = data['close'].rolling(window=window).mean()
            tightness = 1 - (price_std / price_mean)
            
            return {
                'range_contraction': range_contraction,
                'price_tightness': tightness.iloc[-1],
                'avg_range': avg_range.iloc[-1],
                'is_consolidating': range_contraction > 0.3 and tightness.iloc[-1] > 0.7
            }
            
        except Exception as e:
            logger.error(f"Error detecting consolidation: {str(e)}")
            return {}
            
    @staticmethod
    def _find_peaks(data: np.ndarray, min_distance: int = 5) -> np.ndarray:
        """Find peaks in a 1D array.
        
        Args:
            data: 1D numpy array
            min_distance: Minimum distance between peaks
            
        Returns:
            Array of peak indices
        """
        peaks = []
        for i in range(1, len(data) - 1):
            if data[i] > data[i-1] and data[i] > data[i+1]:
                peaks.append(i)
                
        # Filter peaks by minimum distance
        if len(peaks) > 1:
            filtered_peaks = [peaks[0]]
            for peak in peaks[1:]:
                if peak - filtered_peaks[-1] >= min_distance:
                    filtered_peaks.append(peak)
            peaks = filtered_peaks
            
        return np.array(peaks)
        
    @staticmethod
    def _calculate_trend_strength(series: pd.Series) -> float:
        """Calculate trend strength (-1 to 1).
        
        Args:
            series: Data series
            
        Returns:
            float indicating trend strength and direction
        """
        try:
            x = np.arange(len(series))
            slope, _, r_value, _, _ = stats.linregress(x, series)
            
            # Normalize slope and combine with R-squared
            normalized_slope = np.arctan(slope) / (np.pi/2)  # Maps to [-1, 1]
            r_squared = r_value ** 2
            
            return normalized_slope * r_squared
            
        except Exception as e:
            logger.error(f"Error calculating trend strength: {str(e)}")
            return 0.0
            
    @staticmethod
    def calculate_momentum_profile(data: pd.DataFrame, window: int = 20) -> Dict[str, float]:
        """Calculate momentum characteristics.
        
        Args:
            data: DataFrame with OHLCV data
            window: Rolling window for momentum calculation
            
        Returns:
            Dictionary containing momentum metrics
        """
        try:
            # Calculate returns
            returns = data['close'].pct_change()
            
            # Calculate momentum metrics
            momentum = returns.rolling(window=window).sum()
            
            # Calculate rate of change
            roc = (data['close'] - data['close'].shift(window)) / data['close'].shift(window)
            
            return {
                'momentum': momentum.iloc[-1],
                'momentum_trend': PatternUtils._calculate_trend_strength(momentum),
                'rate_of_change': roc.iloc[-1],
                'acceleration': momentum.diff().iloc[-1]
            }
            
        except Exception as e:
            logger.error(f"Error calculating momentum profile: {str(e)}")
            return {}
            
    @staticmethod
    def analyze_price_action(data: pd.DataFrame, window: int = 20) -> Dict[str, Any]:
        """Analyze recent price action characteristics.
        
        Args:
            data: DataFrame with OHLCV data
            window: Rolling window for analysis
            
        Returns:
            Dictionary containing price action analysis
        """
        try:
            recent_data = data.tail(window)
            
            # Calculate basic statistics
            stats = {
                'avg_body_size': abs(recent_data['close'] - recent_data['open']).mean(),
                'avg_upper_wick': (recent_data['high'] - recent_data[['open', 'close']].max(axis=1)).mean(),
                'avg_lower_wick': (recent_data[['open', 'close']].min(axis=1) - recent_data['low']).mean(),
                'body_to_wick_ratio': abs(recent_data['close'] - recent_data['open']).mean() / 
                                    ((recent_data['high'] - recent_data['low']).mean() or 1)
            }
            
            # Analyze candlestick patterns
            bullish_candles = sum(recent_data['close'] > recent_data['open'])
            bearish_candles = sum(recent_data['close'] < recent_data['open'])
            
            patterns = {
                'bullish_ratio': bullish_candles / window,
                'average_gain': recent_data[recent_data['close'] > recent_data['open']]['close'].pct_change().mean(),
                'average_loss': recent_data[recent_data['close'] < recent_data['open']]['close'].pct_change().mean(),
                'momentum_building': bullish_candles > bearish_candles and 
                                   stats['avg_body_size'] > stats['avg_body_size'].shift(1).mean()
            }
            
            return {
                'statistics': stats,
                'patterns': patterns
            }
            
        except Exception as e:
            logger.error(f"Error analyzing price action: {str(e)}")
            return {}
