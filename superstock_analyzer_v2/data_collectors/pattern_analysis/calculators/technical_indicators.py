import logging
from typing import Dict, List, Optional, Union
import pandas as pd
import numpy as np
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class IndicatorConfig:
    """Configuration for technical indicators."""
    sma_periods: List[int] = None  # Periods for Simple Moving Averages
    ema_periods: List[int] = None  # Periods for Exponential Moving Averages
    rsi_period: int = 14          # Period for RSI calculation
    macd_periods: tuple = (12, 26, 9)  # (Fast, Slow, Signal) periods for MACD
    bb_period: int = 20           # Period for Bollinger Bands
    bb_std: float = 2.0          # Standard deviations for Bollinger Bands
    atr_period: int = 14         # Period for Average True Range
    
    def __post_init__(self):
        """Set default values if none provided."""
        if self.sma_periods is None:
            self.sma_periods = [10, 20, 50, 200]
        if self.ema_periods is None:
            self.ema_periods = [9, 21]

class TechnicalIndicators:
    """Calculator for various technical indicators."""
    
    def __init__(self, config: IndicatorConfig = None):
        """Initialize the technical indicators calculator.
        
        Args:
            config: Optional configuration for indicators
        """
        self.config = config or IndicatorConfig()
        
    def calculate_all(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """Calculate all technical indicators.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            Dictionary mapping indicator names to their Series
        """
        try:
            indicators = {}
            
            # Moving Averages
            for period in self.config.sma_periods:
                indicators[f'sma_{period}'] = self.calculate_sma(data['close'], period)
            
            for period in self.config.ema_periods:
                indicators[f'ema_{period}'] = self.calculate_ema(data['close'], period)
            
            # Momentum Indicators
            indicators['rsi'] = self.calculate_rsi(data['close'])
            
            macd_data = self.calculate_macd(data['close'])
            indicators.update(macd_data)
            
            # Volatility Indicators
            bb_data = self.calculate_bollinger_bands(data['close'])
            indicators.update(bb_data)
            
            indicators['atr'] = self.calculate_atr(data)
            
            # Volume Indicators
            indicators['obv'] = self.calculate_obv(data)
            indicators['volume_sma'] = self.calculate_sma(data['volume'], 20)
            
            return indicators
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {str(e)}")
            return {}
            
    def calculate_sma(self, series: pd.Series, period: int) -> pd.Series:
        """Calculate Simple Moving Average.
        
        Args:
            series: Price series
            period: Moving average period
            
        Returns:
            Series containing SMA values
        """
        try:
            return series.rolling(window=period).mean()
        except Exception as e:
            logger.error(f"Error calculating SMA: {str(e)}")
            return pd.Series(index=series.index)
            
    def calculate_ema(self, series: pd.Series, period: int) -> pd.Series:
        """Calculate Exponential Moving Average.
        
        Args:
            series: Price series
            period: Moving average period
            
        Returns:
            Series containing EMA values
        """
        try:
            return series.ewm(span=period, adjust=False).mean()
        except Exception as e:
            logger.error(f"Error calculating EMA: {str(e)}")
            return pd.Series(index=series.index)
            
    def calculate_rsi(self, series: pd.Series) -> pd.Series:
        """Calculate Relative Strength Index.
        
        Args:
            series: Price series
            
        Returns:
            Series containing RSI values
        """
        try:
            period = self.config.rsi_period
            delta = series.diff()
            
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            return rsi
            
        except Exception as e:
            logger.error(f"Error calculating RSI: {str(e)}")
            return pd.Series(index=series.index)
            
    def calculate_macd(self, series: pd.Series) -> Dict[str, pd.Series]:
        """Calculate MACD (Moving Average Convergence Divergence).
        
        Args:
            series: Price series
            
        Returns:
            Dictionary containing MACD line, signal line, and histogram
        """
        try:
            fast_period, slow_period, signal_period = self.config.macd_periods
            
            fast_ema = self.calculate_ema(series, fast_period)
            slow_ema = self.calculate_ema(series, slow_period)
            
            macd_line = fast_ema - slow_ema
            signal_line = self.calculate_ema(macd_line, signal_period)
            histogram = macd_line - signal_line
            
            return {
                'macd': macd_line,
                'macd_signal': signal_line,
                'macd_hist': histogram
            }
            
        except Exception as e:
            logger.error(f"Error calculating MACD: {str(e)}")
            return {
                'macd': pd.Series(index=series.index),
                'macd_signal': pd.Series(index=series.index),
                'macd_hist': pd.Series(index=series.index)
            }
            
    def calculate_bollinger_bands(self, series: pd.Series) -> Dict[str, pd.Series]:
        """Calculate Bollinger Bands.
        
        Args:
            series: Price series
            
        Returns:
            Dictionary containing upper band, middle band, and lower band
        """
        try:
            period = self.config.bb_period
            std_dev = self.config.bb_std
            
            middle_band = self.calculate_sma(series, period)
            std = series.rolling(window=period).std()
            
            upper_band = middle_band + (std * std_dev)
            lower_band = middle_band - (std * std_dev)
            
            return {
                'bb_upper': upper_band,
                'bb_middle': middle_band,
                'bb_lower': lower_band
            }
            
        except Exception as e:
            logger.error(f"Error calculating Bollinger Bands: {str(e)}")
            return {
                'bb_upper': pd.Series(index=series.index),
                'bb_middle': pd.Series(index=series.index),
                'bb_lower': pd.Series(index=series.index)
            }
            
    def calculate_atr(self, data: pd.DataFrame) -> pd.Series:
        """Calculate Average True Range.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            Series containing ATR values
        """
        try:
            period = self.config.atr_period
            
            high = data['high']
            low = data['low']
            close = data['close']
            
            tr1 = high - low
            tr2 = abs(high - close.shift())
            tr3 = abs(low - close.shift())
            
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = tr.rolling(window=period).mean()
            
            return atr
            
        except Exception as e:
            logger.error(f"Error calculating ATR: {str(e)}")
            return pd.Series(index=data.index)
            
    def calculate_obv(self, data: pd.DataFrame) -> pd.Series:
        """Calculate On-Balance Volume.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            Series containing OBV values
        """
        try:
            close = data['close']
            volume = data['volume']
            
            obv = pd.Series(0, index=close.index)
            
            for i in range(1, len(close)):
                if close[i] > close[i-1]:
                    obv[i] = obv[i-1] + volume[i]
                elif close[i] < close[i-1]:
                    obv[i] = obv[i-1] - volume[i]
                else:
                    obv[i] = obv[i-1]
                    
            return obv
            
        except Exception as e:
            logger.error(f"Error calculating OBV: {str(e)}")
            return pd.Series(index=data.index)
            
    def calculate_momentum(self, series: pd.Series, period: int = 10) -> pd.Series:
        """Calculate momentum indicator.
        
        Args:
            series: Price series
            period: Momentum period
            
        Returns:
            Series containing momentum values
        """
        try:
            return series - series.shift(period)
        except Exception as e:
            logger.error(f"Error calculating momentum: {str(e)}")
            return pd.Series(index=series.index)
            
    def calculate_stochastic(self, data: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> Dict[str, pd.Series]:
        """Calculate Stochastic Oscillator.
        
        Args:
            data: DataFrame with OHLCV data
            k_period: Period for %K line
            d_period: Period for %D line
            
        Returns:
            Dictionary containing %K and %D values
        """
        try:
            low_min = data['low'].rolling(window=k_period).min()
            high_max = data['high'].rolling(window=k_period).max()
            
            k = 100 * ((data['close'] - low_min) / (high_max - low_min))
            d = k.rolling(window=d_period).mean()
            
            return {
                'stoch_k': k,
                'stoch_d': d
            }
            
        except Exception as e:
            logger.error(f"Error calculating Stochastic: {str(e)}")
            return {
                'stoch_k': pd.Series(index=data.index),
                'stoch_d': pd.Series(index=data.index)
            }
            
    def calculate_adx(self, data: pd.DataFrame, period: int = 14) -> Dict[str, pd.Series]:
        """Calculate Average Directional Index.
        
        Args:
            data: DataFrame with OHLCV data
            period: ADX period
            
        Returns:
            Dictionary containing ADX, +DI, and -DI values
        """
        try:
            high = data['high']
            low = data['low']
            close = data['close']
            
            # Calculate True Range
            tr1 = high - low
            tr2 = abs(high - close.shift())
            tr3 = abs(low - close.shift())
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            
            # Calculate Directional Movement
            up_move = high - high.shift()
            down_move = low.shift() - low
            
            pos_dm = ((up_move > down_move) & (up_move > 0)) * up_move
            neg_dm = ((down_move > up_move) & (down_move > 0)) * down_move
            
            # Calculate Smoothed Values
            tr14 = tr.rolling(window=period).sum()
            pos_dm14 = pos_dm.rolling(window=period).sum()
            neg_dm14 = neg_dm.rolling(window=period).sum()
            
            # Calculate Directional Indicators
            pos_di = 100 * (pos_dm14 / tr14)
            neg_di = 100 * (neg_dm14 / tr14)
            
            # Calculate ADX
            dx = 100 * abs(pos_di - neg_di) / (pos_di + neg_di)
            adx = dx.rolling(window=period).mean()
            
            return {
                'adx': adx,
                'pos_di': pos_di,
                'neg_di': neg_di
            }
            
        except Exception as e:
            logger.error(f"Error calculating ADX: {str(e)}")
            return {
                'adx': pd.Series(index=data.index),
                'pos_di': pd.Series(index=data.index),
                'neg_di': pd.Series(index=data.index)
            }
