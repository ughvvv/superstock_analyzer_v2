"""Essential technical data collector for MVP."""

import logging
import numpy as np
from typing import Dict, Optional, List
import asyncio
import aiohttp
from .base_collector import BaseCollector
from .circuit_breaker import CircuitBreaker, circuit_breaker

logger = logging.getLogger(__name__)

class TechnicalDataCollector(BaseCollector):
    """Basic collector for technical indicators."""
    
    def __init__(self, api_key: str):
        """Initialize the technical data collector."""
        super().__init__(api_key)
        self.technical_breaker = CircuitBreaker("technical_data")
        
        # Essential technical indicators for MVP
        self.indicators = {
            'sma': {'periods': [20, 50, 200]},  # Key moving averages
            'rsi': {'period': 14},              # Basic momentum
        }
        
        # Batch processing configuration
        self.batch_size = 25

    @circuit_breaker
    async def get_technical_data_batch(self, symbols: List[str]) -> Dict[str, Dict]:
        """Get essential technical data for multiple symbols."""
        results = {}
        
        try:
            # Split symbols into manageable batches
            symbol_batches = [symbols[i:i + self.batch_size] 
                            for i in range(0, len(symbols), self.batch_size)]
            
            async with aiohttp.ClientSession() as session:
                for batch in symbol_batches:
                    symbols_str = ','.join(batch)
                    batch_results = {symbol: {'technical_indicators': {}} 
                                   for symbol in batch}
                    
                    try:
                        # Get basic price data
                        quote_data = await self.make_request(
                            f"quote-short/{symbols_str}",
                            session=session
                        )
                        
                        if quote_data:
                            for quote in quote_data:
                                symbol = quote.get('symbol')
                                if symbol in batch_results:
                                    batch_results[symbol].update({
                                        'price': float(quote.get('price', 0) or 0),
                                        'volume': int(quote.get('volume', 0) or 0)
                                    })
                        
                        # Get essential technical indicators
                        # SMA
                        for period in self.indicators['sma']['periods']:
                            data = await self.make_request(
                                f"technical_indicator/daily/sma",
                                session=session,
                                params={'symbol': symbols_str, 'period': period}
                            )
                            if data:
                                for item in data:
                                    symbol = item.get('symbol')
                                    if symbol in batch_results:
                                        value = float(item.get('value', 0) or 0)
                                        batch_results[symbol]['technical_indicators'][f'sma{period}'] = value
                            
                            await asyncio.sleep(0.1)  # Rate limiting
                        
                        # RSI
                        rsi_data = await self.make_request(
                            f"technical_indicator/daily/rsi",
                            session=session,
                            params={'symbol': symbols_str, 'period': self.indicators['rsi']['period']}
                        )
                        if rsi_data:
                            for item in rsi_data:
                                symbol = item.get('symbol')
                                if symbol in batch_results:
                                    value = float(item.get('value', 0) or 0)
                                    batch_results[symbol]['technical_indicators'][f'rsi14'] = value
                        
                        # Validate and store results
                        for symbol, data in batch_results.items():
                            if self._validate_technical_data(data):
                                results[symbol] = data
                                self.save_to_cache(f"technical_{symbol}", data)
                        
                    except Exception as e:
                        logger.error(f"Error processing batch: {str(e)}")
                        continue
                    
                    await asyncio.sleep(1)  # Batch delay
            
            return results
            
        except Exception as e:
            logger.error(f"Error in get_technical_data_batch: {str(e)}")
            return {}

    def _validate_technical_data(self, data: Dict) -> bool:
        """Validate essential technical data."""
        try:
            if not isinstance(data, dict):
                return False
                
            # Check basic price data
            if not all(key in data for key in ['price', 'volume']):
                return False
                
            # Check essential indicators
            indicators = data.get('technical_indicators', {})
            required_indicators = ['sma20', 'sma50', 'sma200', 'rsi14']
            
            if not all(ind in indicators for ind in required_indicators):
                return False
                
            # Validate numeric values
            for value in indicators.values():
                if not isinstance(value, (int, float)) or np.isnan(value):
                    return False
                    
            return True
            
        except Exception as e:
            logger.error(f"Error validating technical data: {str(e)}")
            return False

    async def get_technical_data(self, symbol: str) -> Optional[Dict]:
        """Get technical data for a single symbol."""
        try:
            # Check cache first
            cached_data = self.get_from_cache(f"technical_{symbol}")
            if cached_data:
                return cached_data
            
            # Get fresh data
            result = await self.get_technical_data_batch([symbol])
            return result.get(symbol)
            
        except Exception as e:
            logger.error(f"Error getting technical data for {symbol}: {str(e)}")
            return None
