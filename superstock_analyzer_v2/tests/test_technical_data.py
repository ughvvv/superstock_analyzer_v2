import os
import sys
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from data_collectors.technical_data_collector import TechnicalDataCollector
from data_collectors.market_data_collector import MarketDataCollector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_technical_data_collection():
    """Test the technical data collection process."""
    try:
        # Load environment variables
        load_dotenv()
        api_key = os.getenv('FMP_API_KEY')
        if not api_key:
            raise ValueError("FMP_API_KEY not found in environment variables")

        # Initialize collectors
        market_collector = MarketDataCollector(api_key)
        technical_collector = TechnicalDataCollector(api_key)

        # Get a small sample of stocks for testing
        print("\n🔍 Getting initial stock universe...")
        initial_quotes = await market_collector.get_initial_quotes_async()
        
        if not initial_quotes:
            raise ValueError("Failed to get initial quotes")

        # Convert initial_quotes to list if it's a dictionary
        if isinstance(initial_quotes, dict):
            quotes_list = [{'symbol': symbol, **data} for symbol, data in initial_quotes.items()]
        else:
            quotes_list = initial_quotes

        # Take a small sample for testing
        test_quotes = quotes_list[:5]
        test_symbols = [quote['symbol'] for quote in test_quotes]
        print(f"\n📊 Testing with symbols: {', '.join(test_symbols)}")

        # Collect technical data
        print("\n📈 Collecting technical data...")
        technical_data = {}
        
        try:
            # Get technical data for all symbols at once
            technical_data = await technical_collector.get_technical_data_batch_async(test_symbols)
            
            if technical_data:
                print(f"\n✅ Successfully collected technical data")
                
                # Print summary for each symbol
                for symbol in test_symbols:
                    if symbol in technical_data:
                        data = technical_data[symbol]
                        print(f"\n📊 {symbol} Technical Data:")
                        
                        # Print key technical indicators
                        indicators = data.get('indicators', {})
                        print(f"RSI (14): {indicators.get('rsi14', 'N/A')}")
                        print(f"ADX (14): {indicators.get('adx14', 'N/A')}")
                        print(f"SMA (20): {indicators.get('sma20', 'N/A')}")
                        print(f"SMA (50): {indicators.get('sma50', 'N/A')}")
                        print(f"Volume: {data.get('volume', 'N/A')}")
                        
                        # Validate data structure
                        missing_indicators = []
                        required_indicators = ['rsi14', 'adx14', 'sma20', 'sma50', 'ema9']
                        
                        for indicator in required_indicators:
                            if indicator not in indicators:
                                missing_indicators.append(indicator)
                        
                        if missing_indicators:
                            print(f"⚠️ Missing indicators: {', '.join(missing_indicators)}")
                    else:
                        print(f"❌ No data found for {symbol}")
            else:
                print("❌ Failed to get technical data")
                
        except Exception as e:
            print(f"❌ Error collecting technical data: {str(e)}")

        # Print summary
        print("\n📊 Test Summary:")
        print(f"Total symbols tested: {len(test_symbols)}")
        print(f"Successful collections: {len(technical_data)}")
        print(f"Failed collections: {len(test_symbols) - len(technical_data)}")

    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
    finally:
        # Clean up
        await technical_collector.close()
        await market_collector.close()

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_technical_data_collection())
