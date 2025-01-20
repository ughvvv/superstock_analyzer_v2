import os
import sys
import json
from typing import List, Dict
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_collectors.base_collector import BaseCollector

class MarketIndexTester(BaseCollector):
    def __init__(self, api_key: str = None):
        """Initialize with optional API key parameter."""
        if api_key:
            os.environ['FMP_API_KEY'] = api_key
        super().__init__()

    def get_all_indices(self) -> List[Dict]:
        """Get all available market indices."""
        try:
            response = self.make_fmp_request("quotes/index")
            if not response:
                print("Failed to get market indices - empty response from API")
                return []
            return response
        except Exception as e:
            print(f"Error getting market indices: {str(e)}")
            return []

    def analyze_indices(self):
        """Analyze and categorize available market indices."""
        indices = self.get_all_indices()
        
        if not indices:
            print("No indices found!")
            return
            
        # Group indices by common prefixes/categories
        categories = {
            'S&P': [],
            'RUSSELL': [],
            'DOW': [],
            'NASDAQ': [],
            'OTHER': []
        }
        
        for idx in indices:
            name = idx.get('name', '').upper()
            symbol = idx.get('symbol', '')
            price = idx.get('price', 0)
            change = idx.get('changesPercentage', 0)
            
            if 'S&P' in name or 'SPX' in name:
                categories['S&P'].append((name, symbol, price, change))
            elif 'RUSSELL' in name:
                categories['RUSSELL'].append((name, symbol, price, change))
            elif 'DOW' in name or 'DJI' in name:
                categories['DOW'].append((name, symbol, price, change))
            elif 'NASDAQ' in name:
                categories['NASDAQ'].append((name, symbol, price, change))
            else:
                categories['OTHER'].append((name, symbol, price, change))
        
        # Print findings
        print("\n=== Market Indices Analysis ===")
        print(f"Total indices found: {len(indices)}\n")
        
        for category, items in categories.items():
            if items:
                print(f"\n{category} Indices ({len(items)}):")
                print("-" * 100)
                for name, symbol, price, change in sorted(items):
                    print(f"Symbol: {symbol:10} | Price: {price:10.2f} | Change: {change:6.2f}% | Name: {name}")

def main():
    # Check for API key
    api_key = os.getenv('FMP_API_KEY')
    if not api_key:
        print("Error: FMP_API_KEY environment variable not found!")
        print("Please set the environment variable or provide the API key as an argument:")
        print("Example: FMP_API_KEY=your_key_here python test_market_indices.py")
        sys.exit(1)
    
    tester = MarketIndexTester()
    tester.analyze_indices()

if __name__ == "__main__":
    main()
