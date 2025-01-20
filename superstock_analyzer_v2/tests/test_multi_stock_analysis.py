import os
import sys
import json
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from data_collectors.qualitative_analysis import QualitativeAnalyzer
from data_collectors.news_insider_collector import NewsInsiderCollector

# Load environment variables
load_dotenv()

async def analyze_stock(symbol: str, news_collector: NewsInsiderCollector, qual_analyzer: QualitativeAnalyzer):
    """Analyze a single stock."""
    print(f"\nAnalyzing {symbol}...")
    
    # Get news and insider data
    news_data = await news_collector.get_news_data(symbol)
    insider_data = await news_collector.get_insider_data(symbol)
    
    print(f"Found {len(news_data.get('articles', []))} articles, "
          f"{len(news_data.get('press_releases', []))} press releases, "
          f"{len(insider_data)} insider transactions")
    
    # Get qualitative analysis
    qual_data = await qual_analyzer.get_qualitative_data(symbol)
    
    result = {
        'qualitative_analysis': qual_data,
        'data_sources': {
            'news_count': len(news_data.get('articles', [])),
            'press_releases_count': len(news_data.get('press_releases', [])),
            'insider_transactions_count': len(insider_data)
        }
    }
    
    print(f"✓ {symbol} analysis complete")
    return symbol, result

async def test_multiple_stocks():
    """Test qualitative analysis on multiple stocks."""
    # Initialize collectors
    api_key = os.getenv('FMP_API_KEY')
    if not api_key:
        raise ValueError("FMP_API_KEY not found in environment variables")
        
    openai_key = os.getenv('OPENAI_API_KEY')
    if not openai_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables")
    
    news_collector = NewsInsiderCollector(api_key)
    qual_analyzer = QualitativeAnalyzer()

    # List of diverse stocks to test
    stocks = [
        'AAPL',  # Tech
        'JPM',   # Banking
        'PFE',   # Healthcare
        'XOM',   # Energy
        'WMT',   # Retail
        'BA',    # Aerospace
        'TSLA',  # Auto
        'NVDA',  # Semiconductors
        'COST',  # Retail
        'META'   # Social Media
    ]

    # Create test results directory
    output_dir = os.path.join(project_root, 'test_results')
    os.makedirs(output_dir, exist_ok=True)
    
    # Analyze stocks concurrently
    tasks = [analyze_stock(symbol, news_collector, qual_analyzer) for symbol in stocks]
    results_list = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Convert results list to dictionary
    results = {}
    for result in results_list:
        if isinstance(result, Exception):
            symbol = result.__traceback__.tb_frame.f_locals['symbol']
            results[symbol] = {'error': str(result)}
        else:
            symbol, result = result
            results[symbol] = result
    
    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = os.path.join(output_dir, f'multi_stock_analysis_{timestamp}.json')
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to {output_file}")

if __name__ == '__main__':
    asyncio.run(test_multiple_stocks())
