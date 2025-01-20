import os
import sys
import json
import asyncio
import aiohttp
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, List

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()

from data_collectors.qualitative_analysis import QualitativeAnalyzer

async def analyze_stock(analyzer: QualitativeAnalyzer, symbol: str) -> List[Dict]:
    """Analyze a single stock's earnings calls."""
    print(f"\nAnalyzing earnings calls for {symbol}...")
    
    try:
        # Get earnings transcripts with enhanced data
        transcripts = await analyzer._get_earnings_transcripts(symbol)
        
        if not transcripts:
            print(f"No transcripts found for {symbol}")
            return []
        
        # Analyze each transcript
        symbol_results = []
        for transcript in transcripts:
            print(f"Processing {symbol} - Q{transcript.get('quarter', 'N/A')} {transcript.get('year', 'N/A')}")
            
            try:
                analysis = await analyzer.analyze_earnings_call(transcript)
                if analysis:
                    if 'error' in analysis:
                        print(f"Error in analysis: {analysis['error']}")
                        continue
                        
                    symbol_results.append(analysis)
                    print(f"Successfully analyzed {symbol} - {analysis.get('quarter', 'N/A')}")
                    
                    # Print some key insights
                    if 'analysis' in analysis:
                        sentiment = analysis['analysis'].get('sentiment', 'N/A')
                        print(f"Sentiment: {sentiment}")
                        
                        # Print financial performance summary
                        fin_perf = analysis['analysis'].get('financial_performance', {})
                        if fin_perf:
                            print("Financial Performance:")
                            print(f"- Revenue: {fin_perf.get('revenue_analysis', 'N/A')}")
                            print(f"- Earnings: {fin_perf.get('earnings_analysis', 'N/A')}")
                            
            except Exception as e:
                print(f"Error analyzing transcript for {symbol}: {str(e)}")
                continue
        
        return symbol_results
        
    except Exception as e:
        print(f"Error analyzing {symbol}: {str(e)}")
        return []

async def main():
    """Test the enhanced earnings call analysis functionality."""
    # Test stocks with different characteristics
    test_stocks = [
        'NVDA',  # Test with one stock first
    ]
    
    results = {}
    
    try:
        # Initialize the analyzer with API key from environment and use as async context manager
        async with QualitativeAnalyzer(api_key=os.getenv('FMP_API_KEY')) as analyzer:
            # Create tasks for all stocks
            tasks = [analyze_stock(analyzer, symbol) for symbol in test_stocks]
            
            # Run all analyses concurrently
            stock_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Combine results
            for symbol, result in zip(test_stocks, stock_results):
                if isinstance(result, Exception):
                    print(f"Error analyzing {symbol}: {str(result)}")
                elif result:
                    results[symbol] = result
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path(__file__).parent.parent / "test_results"
        output_dir.mkdir(exist_ok=True)
        
        output_file = output_dir / f"earnings_analysis_{timestamp}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\nResults saved to: {output_file}")
        return results
        
    except Exception as e:
        print(f"Error in test execution: {str(e)}")
        return {}

if __name__ == "__main__":
    asyncio.run(main())
