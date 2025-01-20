import logging
from typing import Dict
import aiohttp
from datetime import datetime
from .base import FinancialDataFetcher

logger = logging.getLogger(__name__)

class FinancialStatement(FinancialDataFetcher):
    """Base class for financial statements."""
    
    @property
    def additional_params(self) -> Dict:
        """Add required year and period parameters."""
        return {
            'year': str(datetime.now().year - 1),  # Use previous year to ensure data availability
            'period': 'annual'  # Using annual data for more complete picture
        }


class IncomeStatement(FinancialStatement):
    """Handler for income statement data."""
    
    @property
    def endpoint(self) -> str:
        return "income-statement-bulk"


class BalanceSheet(FinancialStatement):
    """Handler for balance sheet data."""
    
    @property
    def endpoint(self) -> str:
        return "balance-sheet-statement-bulk"


class CashFlow(FinancialStatement):
    """Handler for cash flow statement data."""
    
    @property
    def endpoint(self) -> str:
        return "cash-flow-statement-bulk"
