import asyncio
import logging
from datetime import datetime
from typing import List, Dict
import json
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from data_collectors.qualitative_analysis import QualitativeAnalyzer
from data_collectors.news_insider_collector import NewsInsiderCollector

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_qualitative_analysis():
    """Test qualitative analysis on a diverse set of stocks."""
    # Test stocks (mix of tech, growth, value, and recent newsmakers)
    test_stocks = [
        "NVDA",  # NVIDIA - AI leader
        "MSFT",  # Microsoft - Large tech
        "TSLA",  # Tesla - High volatility
        "AAPL",  # Apple - Consumer tech
        "META",  # Meta - Recent rebound
        "AMD",   # AMD - Semiconductor
        "PLTR",  # Palantir - AI/Growth
        "CRWD",  # CrowdStrike - Cybersecurity
        "SNOW",  # Snowflake - Cloud/Growth
        "ARM",   # ARM Holdings - Recent IPO
    ]
    
    # Initialize collectors
    fmp_api_key = os.getenv('FMP_API_KEY')
    if not fmp_api_key:
        raise ValueError("FMP_API_KEY environment variable is required")
    
    news_collector = NewsInsiderCollector(fmp_api_key)
    qualitative_analyzer = QualitativeAnalyzer()
    
    # Create results directory if it doesn't exist
    results_dir = "test_results"
    os.makedirs(results_dir, exist_ok=True)
    
    results = {}
    
    for symbol in test_stocks:
        try:
            logger.info(f"\nAnalyzing {symbol}...")
            
            # Collect documents
            documents = {
                'articles': news_collector.get_news(symbol).get('articles', []),
                'press_releases': news_collector.get_news(symbol).get('press_releases', []),
                'insider_data': news_collector.get_insider_data(symbol),
                'earnings_calls': []  # We'll need to implement earnings call collection
            }
            
            # Run qualitative analysis
            analysis = qualitative_analyzer.analyze_documents(symbol, documents)
            
            # Store results
            results[symbol] = {
                'timestamp': datetime.now().isoformat(),
                'analysis': analysis,
                'document_counts': {
                    'articles': len(documents['articles']),
                    'press_releases': len(documents['press_releases']),
                    'earnings_calls': len(documents['earnings_calls'])
                }
            }
            
            # Save individual result
            with open(f"{results_dir}/{symbol}_analysis.json", 'w') as f:
                json.dump(results[symbol], f, indent=2)
            
            logger.info(f"{symbol} Analysis Complete:")
            logger.info(f"Overall Sentiment: {analysis['overall_sentiment']}")
            logger.info(f"Number of Key Insights: {len(analysis['key_insights'])}")
            logger.info(f"Document Counts: {results[symbol]['document_counts']}")
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {str(e)}")
            results[symbol] = {'error': str(e)}
    
    # Save combined results
    with open(f"{results_dir}/combined_analysis.json", 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    print("\nAnalysis Summary:")
    print("-" * 50)
    for symbol, result in results.items():
        if 'error' in result:
            print(f"{symbol}: Error - {result['error']}")
        else:
            analysis = result['analysis']
            print(f"\n{symbol}:")
            print(f"Sentiment: {analysis['overall_sentiment']}")
            print(f"Key Insights: {len(analysis['key_insights'])}")
            print(f"Documents Analyzed: {result['document_counts']}")

if __name__ == "__main__":
    asyncio.run(test_qualitative_analysis())
