import logging
from typing import Dict
import aiohttp
from datetime import datetime
from .base import FinancialDataFetcher

logger = logging.getLogger(__name__)

class MetricsFetcher(FinancialDataFetcher):
    """Base class for metrics that return CSV data."""
    
    @property
    def response_type(self) -> str:
        return "csv"
    
    @property
    def additional_params(self) -> Dict:
        return {
            'datatype': 'csv'  # Explicitly request CSV format
        }


class KeyMetrics(MetricsFetcher):
    """Handler for key metrics TTM data."""
    
    @property
    def endpoint(self) -> str:
        return "key-metrics-ttm-bulk"


class FinancialRatios(MetricsFetcher):
    """Handler for financial ratios data."""
    
    @property
    def endpoint(self) -> str:
        return "ratios-bulk"
        
    @property
    def additional_params(self) -> Dict:
        """Add required year and period parameters."""
        return {
            'year': str(datetime.now().year - 1),  # Use previous year to ensure data availability
            'period': 'annual'
        }
