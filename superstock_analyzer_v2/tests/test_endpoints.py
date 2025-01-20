import os
from dotenv import load_dotenv
import sys
import requests
import logging
from datetime import datetime

# Load environment variables from .env.test file
load_dotenv('tests/.env.test')

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get API key from environment
FMP_API_KEY = os.getenv('FMP_API_KEY')
if not FMP_API_KEY:
    raise ValueError("FMP_API_KEY environment variable is required")

# Test configuration
TEST_SYMBOL = 'AAPL'  # Using AAPL as test symbol for better data coverage
BASE_URL = 'https://financialmodelingprep.com/api'  # Remove v3 since we need to support both v3 and v4

def test_endpoint(endpoint, params=None):
    """Test a specific FMP endpoint."""
    try:
        url = f"{BASE_URL}/{endpoint}"
        if not params:
            params = {}
        params['apikey'] = FMP_API_KEY
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Handle different response formats
        record_count = 0
        if isinstance(data, list):
            record_count = len(data)
        elif isinstance(data, dict):
            if 'historical' in data:
                record_count = {'historical': len(data['historical'])}
            else:
                record_count = 1
        
        endpoint_name = endpoint.split('?')[0].split('/')[-1]
        logger.info(f"\nTesting {endpoint_name} endpoint...")
        logger.info(f"✅ {endpoint_name} endpoint working")
        
        if isinstance(record_count, dict):
            logger.info(f"   Received data with {len(record_count)} fields")
        else:
            logger.info(f"   Received {record_count} records")
            
        return True
    except Exception as e:
        logger.error(f"❌ Error testing {endpoint}: {str(e)}")
        return False

def main():
    # Test cases for each collector
    test_cases = [
        # Market Data Collector endpoints
        ("v3/symbol/NASDAQ", "NASDAQ Symbols"),
        ("v3/symbol/NYSE", "NYSE Symbols"),
        ("v3/quote/META", "Quote Data"),
        ("v3/stock/list", "Stock List"),
        
        # Financial Data Collector endpoints
        ("v3/income-statement/META?period=annual", "Income Statement"),
        ("v3/balance-sheet-statement/META?period=annual", "Balance Sheet"),
        ("v3/cash-flow-statement/META?period=annual", "Cash Flow"),
        ("v3/key-metrics/META?period=annual", "Key Metrics"),
        ("v3/ratios/META?period=annual", "Financial Ratios"),
        
        # Technical Data Collector endpoints
        ("v3/technical_indicator/1day/META?type=sma&period=20", "Technical Indicators"),
        ("v3/historical-price-full/META", "Historical Prices"),
        
        # News & Insider Collector endpoints
        ("v4/stock_news?tickers=AAPL", "Stock News"),
        ("v4/insider-trading?symbol=AAPL&limit=100&from=2023-01-01&to=2024-12-07", "Insider Trading"),
        ("v4/insider-roaster-statistic?symbol=AAPL", "Insider Statistics"),
        
        # Company Profile endpoints
        ("v3/profile/META", "Company Profile"),
        ("v3/market-capitalization/META", "Market Cap"),
        ("v3/enterprise-values/META", "Enterprise Value")
    ]
    
    results = []
    for endpoint, description in test_cases:
        success = test_endpoint(endpoint)
        
        result = {
            'endpoint': endpoint,
            'description': description,
            'success': success,
            'data': None,
            'error': None
        }
        results.append(result)
        
    # Print summary
    print("\n=== Endpoint Test Summary ===")
    success_count = sum(1 for r in results if r['success'])
    print(f"Total endpoints tested: {len(results)}")
    print(f"Successful: {success_count}")
    print(f"Failed: {len(results) - success_count}")
    
    # Print failed endpoints
    if len(results) - success_count > 0:
        print("\nFailed endpoints:")
        for result in results:
            if not result['success']:
                print(f"- {result['description']}")

if __name__ == "__main__":
    main()
