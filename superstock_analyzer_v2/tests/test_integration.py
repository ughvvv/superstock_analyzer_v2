import os
import unittest
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv
from typing import Dict

from data_collectors.market_data_collector import MarketDataCollector
from data_collectors.financial.collector import FinancialDataCollector
from data_collectors.technical_data_collector import TechnicalDataCollector
from data_collectors.qualitative_analysis import QualitativeAnalyzer
from scoring import StockScorer

# Configure logging
logging.basicConfig(level=logging.INFO)

class TestIntegrationAnalysis(unittest.IsolatedAsyncioTestCase):
    """Integration tests for the stock analysis pipeline."""
    
    logger = logging.getLogger(__name__)
    TEST_SIZE = 10  # Number of stocks to test
    
    @classmethod
    async def asyncSetUp(cls):
        """Set up test fixtures before each test."""
        # Get API key from environment
        cls.api_key = os.getenv('FMP_API_KEY')
        if not cls.api_key:
            pytest.skip("FMP_API_KEY not set")

        # Initialize collectors
        cls.market_data = MarketDataCollector(api_key=cls.api_key)
        cls.financial_data = FinancialDataCollector(api_key=cls.api_key)
        cls.technical_data = TechnicalDataCollector(api_key=cls.api_key)
        cls.qualitative_data = QualitativeAnalyzer(api_key=cls.api_key)
        cls.scorer = StockScorer()

        # Test symbols (well-known stocks)
        cls.test_symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META']

    @classmethod
    async def asyncTearDown(cls):
        """Clean up after all tests."""
        try:
            if hasattr(cls.market_data, 'session') and cls.market_data.session:
                await cls.market_data.close()
        except Exception as e:
            cls.logger.error(f"Error in teardown: {str(e)}")

    async def analyze_stock(self, symbol: str) -> Dict:
        """Analyze a single stock."""
        try:
            # Get market data
            market_data = await self.market_data.get_market_data([symbol])
            if not market_data:
                return {'symbol': symbol, 'error': f'No market data available for {symbol}'}

            # Get financial data
            financial_data = await self.financial_data.get_financial_data(symbol)
            if not financial_data:
                return {'symbol': symbol, 'error': f'No financial data available for {symbol}'}

            # Get technical data
            technical_data = await self.technical_data.get_technical_data(symbol)
            if not technical_data:
                return {'symbol': symbol, 'error': f'No technical data available for {symbol}'}

            # Score the stock
            score = self.scorer.calculate_total_score(
                symbol=symbol,
                fundamental_data=financial_data,
                technical_data=technical_data,
                qualitative_data=None  # Skip qualitative for tests
            )

            return {
                'symbol': symbol,
                'score': score.total_score,
                'fundamental_score': score.fundamental_score,
                'technical_score': score.technical_score,
                'market_data': market_data,
                'financial_data': financial_data,
                'technical_data': technical_data
            }

        except Exception as e:
            self.logger.error(f"Error analyzing {symbol}: {str(e)}")
            return {'symbol': symbol, 'error': str(e)}

    async def test_full_analysis_pipeline(self):
        """Test the full analysis pipeline with multiple stocks."""
        test_start = datetime.now()
        self.logger.info(f"Starting full pipeline test with {min(10, len(self.test_symbols))} stocks")
        
        # Get test symbols
        symbols = self.test_symbols
        if not symbols:
            self.fail("No test symbols available")
        
        # Run analysis
        results = []
        tasks = [self.analyze_stock(symbol) for symbol in symbols[:min(10, len(symbols))]]
        results = await asyncio.gather(*tasks)
        
        # Calculate success rate
        successful = sum(1 for r in results if 'error' not in r)
        success_rate = (successful / len(results)) * 100
        
        # Log results
        for result in results:
            if 'error' in result:
                self.logger.warning(f"Analysis failed for {result['symbol']}: {result['error']}")
        
        self.logger.info(f"Analysis pipeline success rate: {success_rate:.2f}%")
        
        # Assert minimum success rate
        min_success_rate = 80
        self.assertGreaterEqual(
            success_rate,
            min_success_rate,
            f"Success rate {success_rate:.2f}% below minimum threshold of {min_success_rate}%"
        )
        
        # Check scores for successful analyses
        for result in results:
            if 'error' not in result:
                self.assertIsNotNone(result['score'])
                self.assertTrue(0 <= result['score'] <= 100)
        
        test_duration = datetime.now() - test_start
        self.logger.info(f"Test duration: {test_duration}")

    async def test_data_consistency(self):
        """Test consistency of data across multiple runs."""
        test_start = datetime.now()
        symbol = 'AAPL'
        runs = 3
        
        self.logger.info(f"Testing data consistency for {symbol} with {runs} runs")
        
        results = []
        tasks = [self.analyze_stock(symbol) for _ in range(runs)]
        results = await asyncio.gather(*tasks)
        
        # Get base result for comparison
        base_result = results[0]
        if 'error' in base_result:
            self.fail(f"Base run failed: {base_result['error']}")
        
        # Compare subsequent runs to base
        for i, result in enumerate(results[1:], 1):
            if 'error' in result:
                self.fail(f"Run {i} failed: {result['error']}")
            
            # Compare key metrics
            self.assertEqual(
                base_result['market_data'].get('symbol'),
                result['market_data'].get('symbol'),
                f"Symbol mismatch in run {i}"
            )
            
            # Compare scores within tolerance
            self.assertAlmostEqual(
                base_result['score'],
                result['score'],
                delta=5,  # Allow 5% variation
                msg=f"Score variation too high in run {i}"
            )
        
        test_duration = datetime.now() - test_start
        self.logger.info(f"Test duration: {test_duration}")

if __name__ == '__main__':
    unittest.main()
