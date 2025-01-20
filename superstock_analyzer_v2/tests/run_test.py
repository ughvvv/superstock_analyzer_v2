import os
import sys
import asyncio
from pathlib import Path

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

# Import the test module
from tests.test_earnings_analysis import main

def get_api_keys():
    """Get API keys from the user."""
    fmp_key = input("Enter your Financial Modeling Prep (FMP) API key: ")
    openai_key = input("Enter your OpenAI API key: ")
    return fmp_key, openai_key

async def run_tests():
    # Get API keys
    fmp_key, openai_key = get_api_keys()
    
    # Set environment variables
    os.environ['FMP_API_KEY'] = fmp_key
    os.environ['OPENAI_API_KEY'] = openai_key
    
    # Run the test
    await main()

if __name__ == "__main__":
    asyncio.run(run_tests())
