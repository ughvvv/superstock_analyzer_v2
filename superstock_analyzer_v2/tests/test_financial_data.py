import sys
import os
import logging
from pprint import pprint
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_collectors.financial.collector import FinancialDataCollector
import pytest

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_financial_data():
    """Test the financial data collector with a few well-known stocks."""
    # Initialize the collector
    api_key = os.getenv('FMP_API_KEY')
    if not api_key:
        pytest.skip("FMP_API_KEY not set")
        
    collector = FinancialDataCollector(api_key=api_key)
    
    # Test symbols
    test_symbols = ['AAPL', 'MSFT', 'GOOGL']
    
    for symbol in test_symbols:
        logger.info(f"\nTesting financial data collection for {symbol}")
        
        # Get financial data
        financial_data = collector.get_financial_data(symbol)
        
        # Check if we got data
        if not financial_data:
            logger.error(f"Failed to get any financial data for {symbol}")
            continue
            
        # Check for required fields
        required_fields = [
            'dcf_valuations',
            'financial_ratios',
            'key_metrics',
            'income_statement',
            'balance_sheet',
            'cash_flow',
            'stock_price',
            'stock_quote',
            'analyst_estimates',
            'earnings_surprises',
            'growth_metrics'
        ]
        
        missing_fields = [field for field in required_fields if field not in financial_data]
        if missing_fields:
            logger.error(f"Missing required fields for {symbol}: {missing_fields}")
        else:
            logger.info(f"All required fields present for {symbol}")
        
        # Check growth metrics specifically
        growth_metrics = financial_data.get('growth_metrics', {})
        if growth_metrics:
            logger.info("Growth metrics found:")
            pprint(growth_metrics)
        else:
            logger.error("No growth metrics found")
            
        # Print some key financial metrics for verification
        if financial_data:
            logger.info(f"\nKey metrics for {symbol}:")
            try:
                price = financial_data['stock_price'].get('price', 'N/A')
                pe_ratio = financial_data['financial_ratios'].get('peRatio', 'N/A')
                revenue = financial_data['income_statement'].get('revenue', 'N/A')
                net_income = financial_data['income_statement'].get('netIncome', 'N/A')
                
                logger.info(f"Current Price: ${price}")
                logger.info(f"P/E Ratio: {pe_ratio}")
                logger.info(f"Revenue: ${revenue:,.2f}" if isinstance(revenue, (int, float)) else f"Revenue: {revenue}")
                logger.info(f"Net Income: ${net_income:,.2f}" if isinstance(net_income, (int, float)) else f"Net Income: {net_income}")
            except Exception as e:
                logger.error(f"Error printing metrics: {str(e)}")

if __name__ == "__main__":
    test_financial_data()
