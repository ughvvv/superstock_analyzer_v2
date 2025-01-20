import logging
import asyncio
from typing import Dict, List, Optional, Any
import aiohttp
from datetime import datetime

from .collectors.income_collector import IncomeCollector
from .collectors.balance_sheet_collector import BalanceSheetCollector
from .collectors.cash_flow_collector import CashFlowCollector
from .processors.data_validator import FinancialDataValidator
from .processors.growth_calculator import GrowthCalculator
from .cache.cache_manager import CacheManager

logger = logging.getLogger(__name__)

class FinancialCollector:
    """Coordinates collection and processing of all financial data."""
    
    def __init__(self, api_key: str, cache_dir: str = 'cache'):
        """Initialize the financial collector.
        
        Args:
            api_key: API key for Financial Modeling Prep
            cache_dir: Directory for caching data
        """
        self.api_key = api_key
        self._session = None
        self.cache_manager = CacheManager(cache_dir)
        
        # Initialize specialized collectors
        self.income_collector = None
        self.balance_sheet_collector = None
        self.cash_flow_collector = None
        
        # Initialize processors
        self.validator = FinancialDataValidator()
        self.growth_calculator = GrowthCalculator()
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()
        
    async def initialize(self):
        """Initialize async resources."""
        if not self._session:
            self._session = aiohttp.ClientSession()
            
            # Initialize collectors with shared session
            self.income_collector = IncomeCollector(self.api_key, self._session)
            self.balance_sheet_collector = BalanceSheetCollector(self.api_key, self._session)
            self.cash_flow_collector = CashFlowCollector(self.api_key, self._session)
            
    async def cleanup(self):
        """Cleanup async resources."""
        if self._session:
            await self._session.close()
            self._session = None
            
    async def get_financial_data(self, symbol: str) -> Dict:
        """Get comprehensive financial data for a symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dictionary containing all financial data
        """
        try:
            # Check cache first
            cached_data = self.cache_manager.get(symbol, 'metrics')
            if cached_data:
                logger.info(f"Using cached financial data for {symbol}")
                return cached_data
                
            # Initialize if needed
            if not self._session:
                await self.initialize()
                
            # Collect data from all sources concurrently
            income_task = self.income_collector.get_income_statements(symbol)
            balance_sheet_task = self.balance_sheet_collector.get_balance_sheets(symbol)
            cash_flow_task = self.cash_flow_collector.get_cash_flows(symbol)
            
            statements = await asyncio.gather(
                income_task,
                balance_sheet_task,
                cash_flow_task
            )
            
            income_stmts, balance_sheets, cash_flows = statements
            
            # Process and validate each type of statement
            processed_data = {
                'income_statement': self.income_collector.process_statements(income_stmts),
                'balance_sheet': self.balance_sheet_collector.process_statements(balance_sheets),
                'cash_flow': self.cash_flow_collector.process_statements(cash_flows)
            }
            
            # Validate processed data
            if not all([
                self.validator.validate_income_statement(processed_data['income_statement']),
                self.validator.validate_balance_sheet(processed_data['balance_sheet']),
                self.validator.validate_cash_flow(processed_data['cash_flow'])
            ]):
                logger.error(f"Data validation failed for {symbol}")
                return {}
                
            # Calculate growth metrics
            growth_metrics = {
                'revenue': self.growth_calculator.calculate_growth_metrics(income_stmts, 'revenue'),
                'earnings': self.growth_calculator.calculate_growth_metrics(income_stmts, 'netIncome'),
                'operating_income': self.growth_calculator.calculate_growth_metrics(income_stmts, 'operatingIncome'),
                'free_cash_flow': self.growth_calculator.calculate_growth_metrics(cash_flows, 'freeCashFlow')
            }
            
            # Analyze growth quality
            growth_quality = {
                metric: self.growth_calculator.analyze_growth_quality(metrics)
                for metric, metrics in growth_metrics.items()
            }
            
            # Combine all data
            financial_data = {
                'statements': processed_data,
                'growth_metrics': growth_metrics,
                'growth_quality': growth_quality,
                'metadata': {
                    'timestamp': datetime.now().isoformat(),
                    'symbol': symbol
                }
            }
            
            # Cache the results
            self.cache_manager.set(symbol, 'metrics', financial_data)
            
            return financial_data
            
        except Exception as e:
            logger.error(f"Error getting financial data for {symbol}: {str(e)}")
            return {}
            
    async def get_batch_financial_data(self, symbols: List[str]) -> Dict[str, Dict]:
        """Get financial data for multiple symbols.
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            Dictionary mapping symbols to their financial data
        """
        try:
            # Process symbols in batches to avoid overwhelming the API
            batch_size = 5
            results = {}
            
            for i in range(0, len(symbols), batch_size):
                batch = symbols[i:i + batch_size]
                batch_tasks = [self.get_financial_data(symbol) for symbol in batch]
                batch_results = await asyncio.gather(*batch_tasks)
                
                results.update(dict(zip(batch, batch_results)))
                
                # Add a small delay between batches
                if i + batch_size < len(symbols):
                    await asyncio.sleep(1)
                    
            return results
            
        except Exception as e:
            logger.error(f"Error in batch processing: {str(e)}")
            return {}
            
    def get_cache_stats(self) -> Dict:
        """Get cache statistics.
        
        Returns:
            Dictionary containing cache statistics
        """
        return self.cache_manager.get_stats()
        
    async def cleanup_cache(self) -> int:
        """Clean up expired cache entries.
        
        Returns:
            Number of entries removed
        """
        return self.cache_manager.cleanup_expired()
