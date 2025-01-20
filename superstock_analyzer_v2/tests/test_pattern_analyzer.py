import unittest
import pandas as pd
import numpy as np
from data_collectors.pattern_analyzer import PatternAnalyzer, BasePattern
from config.pattern_analyzer_config import BasePatternConfig, VolumePatternConfig, ScoringWeights

class TestPatternAnalyzer(unittest.TestCase):
    def setUp(self):
        """Set up test cases."""
        self.analyzer = PatternAnalyzer()
        
        # Create sample data for a typical base pattern
        dates = pd.date_range(start='2024-01-01', periods=50)
        self.base_data = pd.DataFrame({
            'date': dates,
            'open': [100.0] * 50,
            'high': [105.0] * 50,
            'low': [95.0] * 50,
            'close': [100.0] * 50,
            'volume': [1000000.0 + i * 1000 for i in range(50)]  # Slightly increasing volume
        })
        self.base_data.set_index('date', inplace=True)
        
        # Log test data setup
        print("\n=== Test Data Setup ===")
        print(f"Data shape: {self.base_data.shape}")
        print(f"Columns: {self.base_data.columns.tolist()}")
        print(f"Index: {type(self.base_data.index)}")
        print(f"First few rows:\n{self.base_data.head()}")
        print("====================\n")
        
    def test_invalid_data(self):
        """Test handling of invalid or insufficient data."""
        # Test with empty DataFrame
        empty_data = pd.DataFrame()
        pattern = self.analyzer.analyze_base_pattern(empty_data)
        self.assertFalse(pattern.is_valid)
        
        # Test with insufficient data points
        short_data = self.base_data.head(5)
        pattern = self.analyzer.analyze_base_pattern(short_data)
        self.assertFalse(pattern.is_valid)
        
    def test_ideal_base_pattern(self):
        """Test ideal base pattern detection."""
        data = self.base_data.copy()

        # Create an ideal base pattern:
        # 1. Earlier higher volatility with downward trend
        data.iloc[-50:-30, data.columns.get_loc('close')] = np.linspace(120, 100, 20)  # Downward trend
        data.iloc[-50:-30, data.columns.get_loc('high')] = data.iloc[-50:-30]['close'] + 5  # Add volatility
        data.iloc[-50:-30, data.columns.get_loc('low')] = data.iloc[-50:-30]['close'] - 5
        
        # 2. Tight consolidation in recent period
        data.iloc[-30:, data.columns.get_loc('close')] = np.random.uniform(98, 102, 30)  # Tight range
        data.iloc[-30:, data.columns.get_loc('high')] = data.iloc[-30:]['close'] + 1  # Low volatility
        data.iloc[-30:, data.columns.get_loc('low')] = data.iloc[-30:]['close'] - 1

        # 3. Volume contraction in recent period
        data.iloc[-50:-30, data.columns.get_loc('volume')] = np.random.randint(1500000, 2500000, 20)  # Higher earlier volume
        data.iloc[-30:, data.columns.get_loc('volume')] = np.random.randint(400000, 450000, 30)  # Lower recent volume

        pattern = self.analyzer.analyze_base_pattern(data)
        
        # Verify the pattern
        self.assertTrue(pattern.is_valid)
        self.assertTrue(pattern.is_ideal_base)
        self.assertEqual(pattern.volume_pattern, 'contraction')
        self.assertGreater(pattern.price_tightness, 0.7)  # Expect high tightness
        self.assertGreater(pattern.breakout_potential, 0.7)  # Expect high potential
        
    def test_volume_patterns(self):
        """Test different volume patterns."""
        data = self.base_data.copy()
        base_volume = data['volume'].mean()

        # Test volume contraction
        # Create a pattern where recent volume has very low standard deviation
        data.iloc[-30:-10, data.columns.get_loc('volume')] = np.random.randint(1500000, 2500000, 20)  # Higher base volume with variation
        data.iloc[-10:, data.columns.get_loc('volume')] = np.random.randint(400000, 450000, 10)  # Much lower recent volume with low std

        # Set up price data for a valid base pattern
        data.iloc[-30:, data.columns.get_loc('close')] = np.random.uniform(98, 102, 30)  # Tight range
        data.iloc[-30:, data.columns.get_loc('high')] = data.iloc[-30:]['close'] + 1  # Low volatility
        data.iloc[-30:, data.columns.get_loc('low')] = data.iloc[-30:]['close'] - 1

        pattern = self.analyzer.analyze_base_pattern(data)
        self.assertEqual(pattern.volume_pattern, 'contraction')

        # Test volume expansion
        data.iloc[-30:-10, data.columns.get_loc('volume')] = np.random.randint(400000, 450000, 20)  # Lower base volume
        data.iloc[-10:, data.columns.get_loc('volume')] = np.random.randint(1500000, 2500000, 10)  # Higher recent volume

        pattern = self.analyzer.analyze_base_pattern(data)
        self.assertEqual(pattern.volume_pattern, 'expansion')

        # Test neutral volume
        data.iloc[-30:, data.columns.get_loc('volume')] = np.random.randint(900000, 1100000, 30)  # Similar volumes throughout

        pattern = self.analyzer.analyze_base_pattern(data)
        self.assertEqual(pattern.volume_pattern, 'neutral')
        
    def test_support_resistance(self):
        """Test support and resistance level detection."""
        data = self.base_data.copy()
        
        # Create clear support level at 95
        data.iloc[20:30, data.columns.get_loc('low')] = 95.0
        data.iloc[35:45, data.columns.get_loc('low')] = 95.0
        
        # Create clear resistance level at 105
        data.iloc[20:30, data.columns.get_loc('high')] = 105.0
        data.iloc[35:45, data.columns.get_loc('high')] = 105.0
        
        pattern = self.analyzer.analyze_base_pattern(data)
        
        self.assertAlmostEqual(pattern.support_level, 95.0, delta=1)
        self.assertAlmostEqual(pattern.resistance_level, 105.0, delta=1)
        
    def test_breakout_potential_scoring(self):
        """Test breakout potential scoring with different scenarios."""
        # Test high potential setup
        data = self.base_data.copy()
        data.iloc[25:, data.columns.get_loc('high')] = 102.0  # Tight range
        data.iloc[25:, data.columns.get_loc('low')] = 98.0
        data.iloc[25:, data.columns.get_loc('volume')] = data.iloc[25:, data.columns.get_loc('volume')] * 0.8  # Declining volume
        
        high_potential = self.analyzer.analyze_base_pattern(data)
        
        # Test low potential setup
        data = self.base_data.copy()
        data.iloc[25:, data.columns.get_loc('high')] = 110.0  # Wide range
        data.iloc[25:, data.columns.get_loc('low')] = 90.0
        data.iloc[25:, data.columns.get_loc('volume')] = data.iloc[25:, data.columns.get_loc('volume')] * 1.5  # Increasing volume
        
        low_potential = self.analyzer.analyze_base_pattern(data)
        
        self.assertGreater(high_potential.breakout_potential, low_potential.breakout_potential)
        
    def test_consolidation_analysis(self):
        """Test consolidation pattern quality analysis."""
        data = self.base_data.copy()
        
        # Create a good consolidation pattern
        data.iloc[25:, data.columns.get_loc('high')] = 102.0
        data.iloc[25:, data.columns.get_loc('low')] = 98.0
        data.iloc[25:, data.columns.get_loc('close')] = data.iloc[25:, data.columns.get_loc('close')].rolling(window=3).mean()  # Smooth price action
        data.iloc[40:, data.columns.get_loc('volume')] = data.iloc[40:, data.columns.get_loc('volume')] * 0.8  # Declining volume
        
        pattern = self.analyzer.analyze_base_pattern(data)
        self.assertGreater(pattern.consolidation_score, 0.6)
        
    def test_candlestick_patterns(self):
        """Test candlestick pattern recognition."""
        data = self.base_data.copy()
        
        # Create a bullish engulfing pattern
        # Day 1: Bearish candle
        data.iloc[-2, data.columns.get_loc('open')] = 105.0
        data.iloc[-2, data.columns.get_loc('high')] = 106.0
        data.iloc[-2, data.columns.get_loc('low')] = 94.0
        data.iloc[-2, data.columns.get_loc('close')] = 95.0
        
        # Day 2: Bullish engulfing candle
        data.iloc[-1, data.columns.get_loc('open')] = 94.0
        data.iloc[-1, data.columns.get_loc('high')] = 106.0
        data.iloc[-1, data.columns.get_loc('low')] = 94.0
        data.iloc[-1, data.columns.get_loc('close')] = 106.0
        
        pattern = self.analyzer.analyze_base_pattern(data)
        
        # Check if bullish engulfing pattern was detected
        self.assertIn('CDL_ENGULFING', pattern.candlestick_patterns)
        self.assertEqual(pattern.candlestick_patterns['CDL_ENGULFING'], 100)  # Bullish signal
        
        # Verify that the breakout potential is increased due to bullish pattern
        self.assertGreater(pattern.breakout_potential, 0.5)

    def test_multiple_patterns(self):
        """Test detection of multiple candlestick patterns."""
        data = self.base_data.copy()
        
        # Create a morning star pattern (3-day bullish reversal)
        # Day 1: Large bearish candle
        data.iloc[-3, data.columns.get_loc('open')] = 105.0
        data.iloc[-3, data.columns.get_loc('high')] = 106.0
        data.iloc[-3, data.columns.get_loc('low')] = 94.0
        data.iloc[-3, data.columns.get_loc('close')] = 95.0
        
        # Day 2: Small doji with gap down
        data.iloc[-2, data.columns.get_loc('open')] = 94.5
        data.iloc[-2, data.columns.get_loc('high')] = 95.0
        data.iloc[-2, data.columns.get_loc('low')] = 94.0
        data.iloc[-2, data.columns.get_loc('close')] = 94.5
        
        # Day 3: Large bullish candle with gap up
        data.iloc[-1, data.columns.get_loc('open')] = 95.5
        data.iloc[-1, data.columns.get_loc('high')] = 105.0
        data.iloc[-1, data.columns.get_loc('low')] = 95.0
        data.iloc[-1, data.columns.get_loc('close')] = 104.0
        
        pattern = self.analyzer.analyze_base_pattern(data)
        
        # Check for morning star pattern
        self.assertIn('CDL_MORNINGSTAR', pattern.candlestick_patterns)
        self.assertGreater(pattern.candlestick_patterns['CDL_MORNINGSTAR'], 0)  # Bullish signal

    def test_custom_config(self):
        """Test analyzer with custom configuration."""
        custom_config = {
            'base_pattern': BasePatternConfig(
                min_base_length=15,
                max_base_depth=0.20
            ),
            'volume_pattern': VolumePatternConfig(
                contraction_threshold=0.7
            ),
            'scoring_weights': ScoringWeights(
                price_tightness_weight=30.0
            )
        }
        
        analyzer = PatternAnalyzer(config=custom_config)
        pattern = analyzer.analyze_base_pattern(self.base_data)
        self.assertTrue(pattern.is_valid)

if __name__ == '__main__':
    unittest.main()
