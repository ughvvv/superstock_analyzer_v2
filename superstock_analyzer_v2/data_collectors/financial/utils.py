import logging
from typing import Dict

logger = logging.getLogger(__name__)

def calculate_growth_metrics(income_data: Dict) -> Dict:
    """Calculate growth metrics from income statement data."""
    try:
        current_revenue = float(income_data.get('revenue', 0))
        prev_revenue = float(income_data.get('previousPeriodRevenue', 0))
        current_income = float(income_data.get('netIncome', 0))
        prev_income = float(income_data.get('previousPeriodNetIncome', 0))
        
        revenue_growth = ((current_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue else 0
        income_growth = ((current_income - prev_income) / prev_income * 100) if prev_income else 0
        
        return {
            'revenueGrowth': revenue_growth,
            'netIncomeGrowth': income_growth
        }
    except Exception as e:
        logger.error(f"Error calculating growth metrics: {str(e)}")
        return {}

def validate_financial_data(data: Dict, symbol: str) -> bool:
    """Validate that all required fields are present in the financial data."""
    try:
        # Log the data structure we received
        logger.info(f"Validating data for {symbol}. Keys present: {list(data.keys())}")
        
        # Check if we have any data at all
        if not data:
            logger.warning(f"No data received for {symbol}")
            return False
            
        # Simplified validation - just check if we have some basic fields
        required_fields = ['revenue', 'netIncome', 'totalAssets', 'operatingCashFlow']
        
        for field in required_fields:
            if field not in data:
                logger.warning(f"Missing {field} for {symbol}")
                return False
            
            value = data[field]
            if value is None or (isinstance(value, (int, float)) and not isinstance(value, bool) and value == 0):
                logger.warning(f"Invalid value for {field} for {symbol}: {value}")
                return False
                
        return True
        
    except Exception as e:
        logger.error(f"Error validating data for {symbol}: {str(e)}")
        return False
