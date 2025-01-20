"""Essential market data collector for MVP."""

import logging
import asyncio
import aiohttp
from typing import List, Dict, Optional
from .base_collector import BaseCollector
from .data_validator import DataValidator
from .circuit_breaker import CircuitBreaker

logger = logging.getLogger(__name__)

class MarketDataCollector(BaseCollector):
    """Basic collector for market data."""
    
    def __init__(self, api_key: str):
        """Initialize the market data collector."""
        super().__init__(api_key)
        
        # Initialize components
        self.validator = DataValidator()
        self._market_breaker = CircuitBreaker("market_data")
        
        # Basic configuration
        self.chunk_size = 25  # Process 25 symbols at a time
        
        # Target exchanges (main US exchanges)
        self.target_exchanges = {'NYSE', 'NASDAQ'}
        
        # Default configuration
        self.config = {
            'min_market_cap': 5e6,      # $5M minimum
            'max_market_cap': 250e6,    # $250M maximum
            'min_price': 1.0,           # $1 minimum price
            'min_volume': 100000,       # Base minimum volume
        }
        
    def update_config(self, new_config: dict) -> None:
        """Update collector configuration."""
        self.config.update(new_config)
        
    async def get_market_symbols(self) -> List[Dict]:
        """Get list of market symbols."""
        try:
            all_stocks = []
            
            # Get NASDAQ stocks
            nasdaq_stocks = await self.make_request("symbol/NASDAQ")
            if nasdaq_stocks:
                all_stocks.extend(nasdaq_stocks)
                logger.info(f"Found {len(nasdaq_stocks)} NASDAQ stocks")
            
            # Get NYSE stocks
            nyse_stocks = await self.make_request("symbol/NYSE")
            if nyse_stocks:
                all_stocks.extend(nyse_stocks)
                logger.info(f"Found {len(nyse_stocks)} NYSE stocks")
            
            # Basic filtering
            filtered_stocks = [
                stock for stock in all_stocks
                if isinstance(stock, dict) and
                stock.get('exchangeShortName') in self.target_exchanges and
                stock.get('type', '').lower() == 'stock'
            ]
            
            logger.info(f"Filtered to {len(filtered_stocks)} stocks")
            return filtered_stocks
            
        except Exception as e:
            logger.error(f"Error getting market symbols: {str(e)}")
            return []
            
    async def get_initial_quotes_async(self) -> List[Dict]:
        """Get initial quotes for filtering."""
        try:
            logger.info("Fetching initial stock quotes...")
            
            # Get stock list
            stock_list = await self.make_request('stock/list')
            if not stock_list:
                logger.error("Empty stock list returned from API")
                return []
            
            # Basic filtering
            filtered_stocks = [
                stock for stock in stock_list
                if isinstance(stock, dict) and
                stock.get('exchangeShortName') in self.target_exchanges and
                stock.get('type', '').lower() == 'stock'
            ]
            
            logger.info(f"Found {len(filtered_stocks)} stocks to analyze")
            
            # Process in batches
            all_quotes = []
            async with aiohttp.ClientSession() as session:
                for i in range(0, len(filtered_stocks), self.chunk_size):
                    batch = filtered_stocks[i:i + self.chunk_size]
                    symbols = [stock['symbol'] for stock in batch]
                    symbols_str = ','.join(symbols)
                    
                    try:
                        quotes = await self.make_request(
                            f"quote/{symbols_str}",
                            session=session
                        )
                        
                        if quotes:
                            # Basic validation
                            valid_quotes = [
                                quote for quote in quotes
                                if self.validator.validate_market_data(quote).is_valid
                            ]
                            all_quotes.extend(valid_quotes)
                            
                    except Exception as e:
                        logger.error(f"Error processing batch: {str(e)}")
                        continue
                    
                    await asyncio.sleep(0.1)  # Small delay between batches
            
            logger.info(f"Found {len(all_quotes)} valid quotes")
            return all_quotes
            
        except Exception as e:
            logger.error(f"Error in get_initial_quotes: {str(e)}")
            return []
            
    async def get_market_data(self, symbol: str, session: Optional[aiohttp.ClientSession] = None) -> Optional[Dict]:
        """Get market data for a symbol."""
        try:
            # Check cache first
            cached_data = self.get_from_cache(f"market_data_{symbol}")
            if cached_data:
                return cached_data
            
            # Get fresh data
            data = await self.make_request(f"quote/{symbol}", session=session)
            
            if data and isinstance(data, list) and len(data) > 0:
                quote = data[0]
                
                # Validate data
                if self.validator.validate_market_data(quote).is_valid:
                    # Cache valid data
                    self.save_to_cache(f"market_data_{symbol}", quote)
                    return quote
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting market data for {symbol}: {str(e)}")
            return None
