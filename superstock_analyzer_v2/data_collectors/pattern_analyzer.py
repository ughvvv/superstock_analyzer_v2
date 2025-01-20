import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from config.pattern_analyzer_config import DEFAULT_CONFIG, BasePatternConfig, VolumePatternConfig, ScoringWeights
import talib

logger = logging.getLogger(__name__)

@dataclass
class BasePattern:
    """Data class representing a base pattern with its characteristics."""
    is_valid: bool
    is_ideal_base: bool
    length: int
    depth: float
    volume_pattern: str
    price_tightness: float
    support_level: float
    resistance_level: float
    consolidation_score: float
    breakout_potential: float
    candlestick_patterns: dict

class PatternAnalyzer:
    """Analyzes price patterns in financial data to identify bases and potential breakouts."""
    
    def __init__(self, config: Dict = None):
        """Initialize the PatternAnalyzer with configuration parameters.
        
        Args:
            config: Optional configuration dictionary. If None, uses DEFAULT_CONFIG.
        """
        config = config or DEFAULT_CONFIG
        self.base_config = config['base_pattern']
        self.volume_config = config['volume_pattern']
        self.scoring_weights = config['scoring_weights']
        
    def analyze_base_pattern(self, data: pd.DataFrame) -> BasePattern:
        """Analyze price action for base pattern formation.
        
        Args:
            data: DataFrame with OHLCV data.
            
        Returns:
            BasePattern object containing analysis results.
        """
        try:
            # Validate input data
            required_columns = {'open', 'high', 'low', 'close', 'volume'}
            if not all(col in data.columns for col in required_columns):
                logger.error(f"Missing required columns. Found: {data.columns.tolist()}")
                return self._create_invalid_base()

            if len(data) < self.base_config.min_base_length:
                logger.error(f"Insufficient data points. Found: {len(data)}, Required: {self.base_config.min_base_length}")
                return self._create_invalid_base()

            # Create a copy of the data to avoid modifying the original
            data = data.copy()
            
            # Ensure data types are correct for TA-Lib
            for col in ['open', 'high', 'low', 'close', 'volume']:
                data.loc[:, col] = data[col].astype('float64')
                
            # Log data types for debugging
            print("\n=== Data Types ===")
            print(data.dtypes)
            print("=================\n")
            
            # Log input data summary
            logger.debug("=== Input Data Summary ===")
            logger.debug(f"Data shape: {data.shape}")
            logger.debug(f"Date range: {data.index.min()} to {data.index.max()}")
            logger.debug(f"Volume range: {data['volume'].min():.0f} to {data['volume'].max():.0f}")
            logger.debug(f"Price range: {data['low'].min():.2f} to {data['high'].max():.2f}")
            logger.debug("=====================")

            # Check for candlestick patterns
            patterns = self._identify_candlestick_patterns(data)
            logger.debug(f"Identified candlestick patterns: {patterns}")

            base_period = self._find_base_period(data)
            if base_period is None:
                logger.error("No valid base period found")
                return self._create_invalid_base()

            logger.debug(f"Found base period: {base_period}")
            base_data = data.iloc[base_period[0]:base_period[1]]
            logger.debug(f"Base data shape: {base_data.shape}")

            # Calculate pattern characteristics
            depth = self._calculate_depth(base_data)
            price_tightness = self._calculate_price_tightness(base_data)
            support, resistance = self._find_support_resistance(base_data)
            consolidation_score = self._calculate_consolidation_score(base_data)
            candlestick_patterns = self._identify_candlestick_patterns(base_data)
            
            # Analyze volume pattern using full dataset
            volume_pattern = self._analyze_volume_pattern(data)
            
            # Calculate breakout potential
            breakout_potential = self._calculate_breakout_potential(
                base_data, 
                price_tightness, 
                volume_pattern,
                consolidation_score,
                depth,
                candlestick_patterns
            )
            
            # Determine if this is an ideal base pattern
            is_ideal = (
                volume_pattern == 'contraction' and
                price_tightness > 0.7 and
                breakout_potential > 0.7 and
                consolidation_score > 0.6
            )

            return BasePattern(
                is_valid=True,
                is_ideal_base=is_ideal,
                length=len(base_data),
                depth=depth,
                volume_pattern=volume_pattern,
                price_tightness=price_tightness,
                support_level=support,
                resistance_level=resistance,
                consolidation_score=consolidation_score,
                breakout_potential=breakout_potential,
                candlestick_patterns=candlestick_patterns
            )

        except Exception as e:
            logger.warning(f"Error analyzing base pattern: {str(e)}")
            return self._create_invalid_base()

    def _find_base_period(self, data: pd.DataFrame) -> Optional[Tuple[int, int]]:
        """Find the most recent base pattern period using advanced criteria."""
        try:
            logger.debug(f"Finding base period - Data shape: {data.shape}")
            
            # Minimum requirements
            min_length = max(self.base_config.min_base_length, 30)  # At least 30 days
            max_depth = self.base_config.max_base_depth
            min_touches = self.base_config.min_touches
            
            # Calculate technical indicators
            data['sma20'] = data['close'].rolling(window=20).mean()
            data['sma50'] = data['close'].rolling(window=50).mean()
            data['atr'] = self._calculate_atr(data)
            data['volume_ma20'] = data['volume'].rolling(window=20).mean()
            
            # Find potential base periods
            potential_bases = []
            
            for i in range(len(data) - min_length):
                window = data.iloc[i:i+min_length]
                
                # Check base criteria
                if self._meets_base_criteria(window):
                    # Calculate base quality score
                    quality_score = self._calculate_base_quality(window)
                    potential_bases.append((i, i+min_length, quality_score))
            
            if not potential_bases:
                logger.debug("No valid base patterns found")
                return None
                
            # Sort by quality score and recency (prefer more recent bases)
            potential_bases.sort(key=lambda x: (x[2], -x[0]), reverse=True)
            
            # Return the highest quality recent base
            start, end, score = potential_bases[0]
            logger.debug(f"Found base pattern: start={start}, end={end}, quality={score:.2f}")
            return start, end
            
        except Exception as e:
            logger.error(f"Error finding base period: {str(e)}")
            return None

    def _meets_base_criteria(self, data: pd.DataFrame) -> bool:
        """Check if a period meets base pattern criteria."""
        try:
            # Price criteria
            price_range = (data['high'].max() - data['low'].min()) / data['low'].min()
            if price_range > self.base_config.max_base_depth:
                return False
            
            # Volume criteria
            recent_volume = data['volume'].tail(5).mean()
            base_volume = data['volume'].mean()
            if recent_volume > base_volume * 1.5:  # Volume should be decreasing/stable
                return False
            
            # Support/Resistance criteria
            touches = self._count_support_resistance_touches(data)
            if touches < self.base_config.min_touches:
                return False
            
            # Moving average criteria
            last_close = data['close'].iloc[-1]
            last_sma20 = data['sma20'].iloc[-1]
            last_sma50 = data['sma50'].iloc[-1]
            
            # Price should be near moving averages in base
            if abs(last_close - last_sma20) / last_sma20 > 0.05:
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error checking base criteria: {str(e)}")
            return False

    def _calculate_base_quality(self, data: pd.DataFrame) -> float:
        """Calculate a quality score for a base pattern."""
        try:
            score = 0.0
            
            # Price tightness (30%)
            price_range = (data['high'].max() - data['low'].min()) / data['low'].min()
            tightness_score = 1.0 - min(price_range / self.base_config.max_base_depth, 1.0)
            score += tightness_score * 0.3
            
            # Volume pattern (30%)
            volume_trend = np.polyfit(range(len(data)), data['volume'], 1)[0]
            volume_score = 1.0 if volume_trend < 0 else 0.0  # Decreasing volume is good
            score += volume_score * 0.3
            
            # Support/Resistance quality (20%)
            touches = self._count_support_resistance_touches(data)
            touch_score = min(touches / self.base_config.min_touches, 1.0)
            score += touch_score * 0.2
            
            # Moving average alignment (20%)
            ma_score = self._calculate_ma_alignment_score(data)
            score += ma_score * 0.2
            
            return score
            
        except Exception as e:
            logger.error(f"Error calculating base quality: {str(e)}")
            return 0.0

    def _calculate_atr(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range."""
        try:
            tr1 = data['high'] - data['low']
            tr2 = abs(data['high'] - data['close'].shift())
            tr3 = abs(data['low'] - data['close'].shift())
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            return tr.rolling(window=period).mean()
        except Exception as e:
            logger.error(f"Error calculating ATR: {str(e)}")
            return pd.Series(index=data.index)

    def _count_support_resistance_touches(self, data: pd.DataFrame) -> int:
        """Count number of touches of support and resistance levels."""
        try:
            # Find potential support/resistance levels
            highs = data['high'].values
            lows = data['low'].values
            
            # Use kernel density estimation to find price clusters
            from scipy.stats import gaussian_kde
            prices = np.concatenate([highs, lows])
            kde = gaussian_kde(prices)
            
            # Find local maxima in density (price levels with many touches)
            x_grid = np.linspace(min(prices), max(prices), 100)
            density = kde(x_grid)
            from scipy.signal import find_peaks
            peaks, _ = find_peaks(density)
            
            # Count touches near these levels
            touches = 0
            for peak_price in x_grid[peaks]:
                # Count prices within 0.5% of level
                near_level = np.logical_or(
                    abs(highs - peak_price) / peak_price < 0.005,
                    abs(lows - peak_price) / peak_price < 0.005
                )
                touches += np.sum(near_level)
            
            return touches
            
        except Exception as e:
            logger.error(f"Error counting support/resistance touches: {str(e)}")
            return 0

    def _calculate_ma_alignment_score(self, data: pd.DataFrame) -> float:
        """Calculate score based on moving average alignment."""
        try:
            last_row = data.iloc[-1]
            sma20 = last_row['sma20']
            sma50 = last_row['sma50']
            close = last_row['close']
            
            # Perfect alignment: price ≈ SMA20 ≈ SMA50
            max_deviation = 0.05  # 5% maximum deviation
            
            price_to_sma20 = abs(close - sma20) / sma20
            sma20_to_sma50 = abs(sma20 - sma50) / sma50
            
            score = (
                (1 - min(price_to_sma20 / max_deviation, 1.0)) * 0.6 +
                (1 - min(sma20_to_sma50 / max_deviation, 1.0)) * 0.4
            )
            
            return score
            
        except Exception as e:
            logger.error(f"Error calculating MA alignment score: {str(e)}")
            return 0.0

    def _calculate_volatilities(self, data: pd.DataFrame) -> float:
        """Calculate volatility for a given window."""
        try:
            # Calculate true range
            tr1 = data['high'] - data['low']
            tr2 = abs(data['high'] - data['close'].shift())
            tr3 = abs(data['low'] - data['close'].shift())
            true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            
            # Calculate average true range as a percentage of price
            atr = true_range.mean()
            avg_price = data['close'].mean()
            return atr / avg_price
            
        except Exception as e:
            logger.error(f"Error calculating volatility: {str(e)}")
            return float('inf')

    def _find_support_resistance(self, data: pd.DataFrame) -> Tuple[float, float]:
        """Find support and resistance levels using price clusters."""
        try:
            highs = data['high'].values
            lows = data['low'].values
            
            resistance_clusters = self._find_clusters(highs, self.base_config.resistance_threshold)
            support_clusters = self._find_clusters(lows, self.base_config.support_threshold)
            
            return min(support_clusters), max(resistance_clusters)
            
        except Exception as e:
            logger.warning(f"Error finding support/resistance: {str(e)}")
            return data['low'].min(), data['high'].max()

    def _find_clusters(self, prices: np.ndarray, threshold: float) -> List[float]:
        """Find price clusters that meet minimum touch requirements."""
        clusters = []
        current_cluster = [prices[0]]
        
        for price in prices[1:]:
            if abs(price - np.mean(current_cluster)) / np.mean(current_cluster) <= threshold:
                current_cluster.append(price)
            else:
                if len(current_cluster) >= self.base_config.min_touches:
                    clusters.append(np.mean(current_cluster))
                current_cluster = [price]
        
        if len(current_cluster) >= self.base_config.min_touches:
            clusters.append(np.mean(current_cluster))
        
        return clusters if clusters else [np.mean(prices)]

    def _analyze_volume_pattern(self, data: pd.DataFrame) -> str:
        """Analyze volume patterns in the data."""
        try:
            if len(data) < 20:  # Need at least 20 days of data
                logger.debug(f"Insufficient data points: {len(data)}, need at least 20")
                return 'neutral'

            # Get recent and base periods
            split_point = len(data) // 2  # Split data in half
            recent_period = data.iloc[split_point:]  # Recent half
            base_period = data.iloc[:split_point]  # Base half

            # Calculate metrics
            recent_mean = recent_period['volume'].mean()
            recent_std = recent_period['volume'].std()
            base_mean = base_period['volume'].mean()
            base_std = base_period['volume'].std()

            logger.debug(f"Volume analysis metrics:")
            logger.debug(f"Recent mean: {recent_mean:.2f}, std: {recent_std:.2f}")
            logger.debug(f"Base mean: {base_mean:.2f}, std: {base_std:.2f}")
            logger.debug(f"Recent/Base ratio: {recent_mean/base_mean:.2f}")
            logger.debug(f"Recent/Base std ratio: {recent_std/base_std:.2f}")

            # Volume contraction: recent volume should be significantly lower with lower std dev
            if (recent_mean < base_mean * 0.5 and  # Recent volume at least 50% lower
                recent_std < base_std * 0.5):  # Recent std dev at least 50% lower
                logger.debug("Detected volume contraction pattern")
                return 'contraction'
            
            # Volume expansion: recent volume should be significantly higher
            if recent_mean > base_mean * 2.0:  # Recent volume at least 100% higher
                logger.debug("Detected volume expansion pattern")
                return 'expansion'

            logger.debug("No significant volume pattern detected, returning neutral")
            return 'neutral'

        except Exception as e:
            logger.error(f"Error analyzing volume pattern: {str(e)}")
            return 'neutral'

    def _calculate_price_tightness(self, data: pd.DataFrame) -> float:
        """Calculate price tightness within base."""
        try:
            tr1 = data['high'] - data['low']
            tr2 = abs(data['high'] - data['close'].shift())
            tr3 = abs(data['low'] - data['close'].shift())
            
            true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = true_range.mean()
            
            total_range = data['high'].max() - data['low'].min()
            avg_price = data['close'].mean()
            
            tightness = 1 - min((total_range / avg_price) / (atr * 4), 1)
            
            return tightness
            
        except Exception as e:
            logger.warning(f"Error calculating price tightness: {str(e)}")
            return 0.5

    def _calculate_depth(self, data: pd.DataFrame) -> float:
        """Calculate depth of the base pattern."""
        try:
            return (data['high'].max() - data['low'].min()) / data['low'].min()
        except Exception as e:
            logger.warning(f"Error calculating depth: {str(e)}")
            return 0.0

    def _calculate_consolidation_score(self, data: pd.DataFrame) -> float:
        """Calculate consolidation score based on price movement and volume."""
        try:
            # Calculate price movement score
            price_range = (data['high'].max() - data['low'].min()) / data['low'].min()
            price_score = 1.0 - min(price_range / 0.15, 1.0)  # Lower range is better, max acceptable range is 15%

            # Calculate volume trend score
            volume_trend = np.polyfit(range(len(data)), data['volume'], 1)[0]
            volume_score = 1.0 if volume_trend < 0 else 0.0  # Decreasing volume is good

            # Calculate volatility score
            volatility = data['close'].pct_change().std()
            volatility_score = 1.0 - min(volatility / 0.02, 1.0)  # Lower volatility is better, max acceptable is 2%

            # Combine scores with weights
            weights = {'price': 0.4, 'volume': 0.3, 'volatility': 0.3}
            total_score = (
                weights['price'] * price_score +
                weights['volume'] * volume_score +
                weights['volatility'] * volatility_score
            )

            return total_score
        except Exception as e:
            logger.warning(f"Error calculating consolidation score: {str(e)}")
            return 0.0

    def _analyze_consolidation(self, data: pd.DataFrame) -> float:
        """Analyze consolidation pattern quality."""
        try:
            closes = data['close']
            higher_lows = (closes > closes.shift()).sum() / len(closes)
            
            ranges = data['high'] - data['low']
            range_narrowing = ranges.tail(5).mean() < ranges.mean() * 1.1
            
            volume_trend = data['volume'].tail(5).mean() < data['volume'].mean() * 1.1
            
            score = (
                (higher_lows * 0.3) +
                (float(range_narrowing) * 0.35) +
                (float(volume_trend) * 0.35)
            )
            
            return score
            
        except Exception as e:
            logger.warning(f"Error analyzing consolidation: {str(e)}")
            return 0.5

    def _identify_candlestick_patterns(self, data: pd.DataFrame) -> Dict[str, float]:
        """Identify candlestick patterns using TA-Lib.
        
        Args:
            data: DataFrame with OHLCV data.
            
        Returns:
            Dictionary of identified patterns and their signals.
        """
        try:
            # Ensure data types are float64
            open_prices = data['open'].astype('float64').values
            high_prices = data['high'].astype('float64').values
            low_prices = data['low'].astype('float64').values
            close_prices = data['close'].astype('float64').values
            
            patterns = {}
            
            # Check for various candlestick patterns
            patterns['CDL_HAMMER'] = talib.CDLHAMMER(open_prices, high_prices, low_prices, close_prices)[-1]
            patterns['CDL_ENGULFING'] = talib.CDLENGULFING(open_prices, high_prices, low_prices, close_prices)[-1]
            patterns['CDL_MORNINGSTAR'] = talib.CDLMORNINGSTAR(open_prices, high_prices, low_prices, close_prices)[-1]
            
            # Log pattern detection results
            print("\n=== Candlestick Patterns ===")
            for pattern, value in patterns.items():
                print(f"{pattern}: {value}")
            print("=========================\n")
            
        except Exception as e:
            print(f"Error in candlestick pattern detection: {str(e)}")
            return {}
            
        return patterns

    def _calculate_breakout_potential(self, data: pd.DataFrame, 
                                    price_tightness: float,
                                    volume_pattern: str,
                                    consolidation_score: float,
                                    depth: float,
                                    candlestick_patterns: dict = None) -> float:
        """Calculate overall breakout potential score."""
        try:
            # Base score from existing metrics
            score = (
                price_tightness * self.scoring_weights.price_tightness_weight +
                self.scoring_weights.volume_pattern_weights.get(volume_pattern, 0) +
                consolidation_score * self.scoring_weights.consolidation_weight +
                (1 - min(depth, self.base_config.max_base_depth) / self.base_config.max_base_depth) * self.scoring_weights.depth_weight
            ) / 100.0

            # Adjust score based on candlestick patterns
            if candlestick_patterns:
                pattern_score = 0
                bullish_patterns = ['CDL_HAMMER', 'CDL_ENGULFING', 'CDL_MORNINGSTAR']
                bearish_patterns = []
                
                for pattern, signal in candlestick_patterns.items():
                    if pattern in bullish_patterns and signal > 0:
                        pattern_score += 0.1  # Increase score for bullish patterns
                    elif pattern in bearish_patterns and signal < 0:
                        pattern_score -= 0.1  # Decrease score for bearish patterns
                
                # Adjust final score while keeping it between 0 and 1
                score = max(0, min(1, score + pattern_score))

            return score
            
        except Exception as e:
            logger.warning(f"Error calculating breakout potential: {str(e)}")
            return 0.0

    def _create_invalid_base(self) -> BasePattern:
        """Create an invalid base pattern object with neutral defaults."""
        return BasePattern(
            is_valid=False,
            is_ideal_base=False,
            length=0,
            depth=0,
            volume_pattern='neutral',
            price_tightness=0.5,
            support_level=0,
            resistance_level=0,
            consolidation_score=0.5,
            breakout_potential=0.5,
            candlestick_patterns={}
        )
