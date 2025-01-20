import unittest
from datetime import datetime, timedelta
from data_collectors.news_insider_collector import NewsInsiderCollector
import os
from dotenv import load_dotenv
from unittest.mock import patch, MagicMock
import requests

class TestNewsInsiderCollector(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures before running tests."""
        load_dotenv()
        cls.api_key = os.getenv('FMP_API_KEY')
        cls.collector = NewsInsiderCollector(cls.api_key)
        
        # Sample data for testing
        cls.sample_insider_trades = [
            {
                'symbol': 'AAPL',
                'transactionDate': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                'transactionType': 'P-Purchase',
                'securitiesTransacted': 1000,
                'price': 150.0,
                'reportingName': 'John Doe',
                'typeOfOwner': 'Director'
            },
            {
                'symbol': 'AAPL',
                'transactionDate': (datetime.now() - timedelta(days=45)).strftime('%Y-%m-%d'),
                'transactionType': 'S-Sale',
                'securitiesTransacted': 2000,
                'price': 155.0,
                'reportingName': 'Jane Smith',
                'typeOfOwner': 'Officer'
            },
            {
                'symbol': 'AAPL',
                'transactionDate': (datetime.now() - timedelta(days=15)).strftime('%Y-%m-%d'),
                'transactionType': 'P-Purchase',
                'securitiesTransacted': 5000,
                'price': 160.0,
                'reportingName': 'Bob Wilson',
                'typeOfOwner': 'Director'
            }
        ]
        
        cls.sample_news = [
            {
                'title': 'Apple Announces New Product',
                'text': 'Apple Inc. announced a revolutionary new product today...',
                'publishedDate': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'site': 'TechNews',
                'url': 'https://technews.com/article1',
                'symbol': 'AAPL'
            },
            {
                'title': 'Apple Q4 Earnings',
                'text': 'Apple reports strong Q4 earnings with record revenue...',
                'publishedDate': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S'),
                'site': 'FinanceNews',
                'url': 'https://financenews.com/article2',
                'symbol': 'AAPL'
            }
        ]

    def test_insider_data_analysis(self):
        """Test insider trading pattern analysis."""
        analysis = self.collector._analyze_insider_patterns(self.sample_insider_trades)
        
        # Check analysis structure
        self.assertIsInstance(analysis, dict)
        self.assertIn('recent_activity', analysis)
        self.assertIn('buy_sell_ratio', analysis)
        self.assertIn('significant_trades', analysis)
        self.assertIn('trend', analysis)
        self.assertIn('summary', analysis)
        
        # Check summary calculations
        summary = analysis['summary']
        self.assertEqual(summary['total_transactions'], 3)
        self.assertEqual(summary['buy_count'], 2)
        self.assertEqual(summary['sell_count'], 1)
        
        # Verify significant trades detection
        self.assertTrue(any(trade['securitiesTransacted'] * trade['price'] >= 100000 
                          for trade in analysis['significant_trades']))

    def test_live_insider_data(self):
        """Test live insider data retrieval for a known stock."""
        symbol = 'AAPL'
        data = self.collector.get_insider_data(symbol)
        
        # Check data structure
        self.assertIsInstance(data, dict)
        self.assertIn('transactions', data)
        self.assertIn('statistics', data)
        self.assertIn('analysis', data)
        
        # Verify transactions are properly filtered
        if data['transactions']:
            for transaction in data['transactions']:
                self.assertIn('transactionDate', transaction)
                self.assertIn('transactionType', transaction)
                self.assertIn('securitiesTransacted', transaction)
                
                # Verify date is within last 6 months
                tx_date = datetime.strptime(transaction['transactionDate'], '%Y-%m-%d')
                self.assertLessEqual(tx_date, datetime.now())
                self.assertGreaterEqual(
                    tx_date, 
                    datetime.now() - timedelta(days=180)
                )

    def test_live_news_data(self):
        """Test live news data retrieval for a known stock."""
        symbol = 'AAPL'
        data = self.collector.get_news(symbol)
        
        # Check data structure
        self.assertIsInstance(data, dict)
        self.assertIn('articles', data)
        self.assertIn('press_releases', data)
        
        # Verify articles are properly filtered
        if data['articles']:
            for article in data['articles']:
                self.assertIn('publishedDate', article)
                self.assertIn('title', article)
                self.assertIn('text', article)
                
                # Verify date is within last 6 months
                pub_date = datetime.strptime(article['publishedDate'], '%Y-%m-%d %H:%M:%S')
                now = datetime.now()
                six_months_ago = now - timedelta(days=180)
                
                # Add 24 hours buffer to account for timezone differences
                buffer_time = now + timedelta(hours=24)
                self.assertLessEqual(pub_date, buffer_time, 
                    f"Article date {pub_date} should be before or equal to current time (with buffer) {buffer_time}")
                self.assertGreaterEqual(pub_date, six_months_ago,
                    f"Article date {pub_date} should be after or equal to six months ago {six_months_ago}")

    def test_cache_functionality(self):
        """Test caching functionality for both news and insider data."""
        symbol = 'AAPL'
        
        # First call should hit the API
        first_news = self.collector.get_news(symbol)
        first_insider = self.collector.get_insider_data(symbol)
        
        # Second call should hit the cache
        second_news = self.collector.get_news(symbol)
        second_insider = self.collector.get_insider_data(symbol)
        
        # Data should be identical
        self.assertEqual(first_news, second_news)
        self.assertEqual(first_insider, second_insider)

    def test_error_handling(self):
        """Test error handling for invalid symbols and API errors."""
        # Test with invalid symbol
        invalid_symbol = 'INVALID123'
        news_data = self.collector.get_news(invalid_symbol)
        insider_data = self.collector.get_insider_data(invalid_symbol)
        
        # Should return empty data structures, not raise exceptions
        self.assertEqual(news_data['articles'], [])
        self.assertEqual(news_data['press_releases'], [])
        self.assertEqual(insider_data['transactions'], [])
        self.assertEqual(insider_data['statistics'], [])
        
        # Test with empty data
        analysis = self.collector._analyze_insider_patterns([])
        self.assertEqual(analysis['recent_activity'], 'none')
        self.assertEqual(analysis['buy_sell_ratio'], 0)
        self.assertEqual(analysis['significant_trades'], [])

    def test_malformed_insider_data(self):
        """Test handling of malformed insider trading data."""
        malformed_trades = [
            # Missing required fields
            {
                'symbol': 'AAPL',
                'transactionDate': datetime.now().strftime('%Y-%m-%d')
                # Missing transactionType, securitiesTransacted, price
            },
            # Invalid date format
            {
                'symbol': 'AAPL',
                'transactionDate': '2024/12/17',  # Wrong format
                'transactionType': 'P-Purchase',
                'securitiesTransacted': 1000,
                'price': 150.0
            },
            # Invalid numeric values
            {
                'symbol': 'AAPL',
                'transactionDate': datetime.now().strftime('%Y-%m-%d'),
                'transactionType': 'P-Purchase',
                'securitiesTransacted': 'invalid',
                'price': 'not_a_number'
            },
            # Unknown transaction type
            {
                'symbol': 'AAPL',
                'transactionDate': datetime.now().strftime('%Y-%m-%d'),
                'transactionType': 'UNKNOWN',
                'securitiesTransacted': 1000,
                'price': 150.0
            }
        ]
        
        # Test analysis of malformed data
        analysis = self.collector._analyze_insider_patterns(malformed_trades)
        
        # Should still return valid analysis structure
        self.assertIsInstance(analysis, dict)
        self.assertIn('recent_activity', analysis)
        self.assertIn('buy_sell_ratio', analysis)
        self.assertEqual(analysis['summary']['total_transactions'], 0)
        self.assertEqual(analysis['summary']['buy_count'], 0)
        self.assertEqual(analysis['summary']['sell_count'], 0)

    def test_edge_case_dates(self):
        """Test handling of edge case dates in news and insider data."""
        edge_case_dates = [
            # Future date
            {
                'symbol': 'AAPL',
                'transactionDate': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
                'transactionType': 'P-Purchase',
                'securitiesTransacted': 1000,
                'price': 150.0
            },
            # Exactly 6 months ago
            {
                'symbol': 'AAPL',
                'transactionDate': (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d'),
                'transactionType': 'P-Purchase',
                'securitiesTransacted': 1000,
                'price': 150.0
            },
            # Just over 6 months ago
            {
                'symbol': 'AAPL',
                'transactionDate': (datetime.now() - timedelta(days=181)).strftime('%Y-%m-%d'),
                'transactionType': 'P-Purchase',
                'securitiesTransacted': 1000,
                'price': 150.0
            }
        ]
        
        # Test date filtering
        analysis = self.collector._analyze_insider_patterns(edge_case_dates)
        self.assertLessEqual(analysis['summary']['total_transactions'], 2)  # Should only include current and 6-month-ago trades

    def test_api_error_handling(self):
        """Test handling of various API error scenarios."""
        from unittest.mock import patch
        
        # Test API error
        with patch.object(self.collector, 'make_fmp_request', return_value=[]):
            # Should handle API errors gracefully
            news_data = self.collector.get_news('AAPL')
            self.assertIsInstance(news_data, dict)
            self.assertIn('articles', news_data)
            self.assertIn('press_releases', news_data)
            self.assertEqual(news_data['articles'], [])
            self.assertEqual(news_data['press_releases'], [])
            
            insider_data = self.collector.get_insider_data('AAPL')
            self.assertIsInstance(insider_data, dict)
            self.assertIn('transactions', insider_data)
            self.assertIn('statistics', insider_data)
            self.assertEqual(insider_data['transactions'], [])
            self.assertEqual(insider_data['statistics'], [])
            
            # Verify error is handled in analysis
            analysis = insider_data.get('analysis', {})
            self.assertEqual(analysis.get('recent_activity', ''), 'none')
            self.assertEqual(analysis.get('buy_sell_ratio', -1), 0)
            self.assertEqual(len(analysis.get('significant_trades', [])), 0)
            
        # Test request exception
        def raise_exception(*args, **kwargs):
            raise requests.exceptions.RequestException("Test error")
            
        with patch.object(self.collector, 'make_fmp_request', side_effect=raise_exception):
            news_data = self.collector.get_news('AAPL')
            self.assertEqual(news_data['articles'], [])
            self.assertEqual(news_data['press_releases'], [])
            
            insider_data = self.collector.get_insider_data('AAPL')
            self.assertEqual(insider_data['transactions'], [])
            self.assertEqual(insider_data['statistics'], [])

    def test_extreme_values(self):
        """Test handling of extreme values in insider trading data."""
        extreme_trades = [
            # Very large transaction
            {
                'symbol': 'AAPL',
                'transactionDate': datetime.now().strftime('%Y-%m-%d'),
                'transactionType': 'P-Purchase',
                'securitiesTransacted': 1000000,
                'price': 1000000.0
            },
            # Very small transaction
            {
                'symbol': 'AAPL',
                'transactionDate': datetime.now().strftime('%Y-%m-%d'),
                'transactionType': 'S-Sale',
                'securitiesTransacted': 0.1,
                'price': 0.01
            },
            # Zero values
            {
                'symbol': 'AAPL',
                'transactionDate': datetime.now().strftime('%Y-%m-%d'),
                'transactionType': 'P-Purchase',
                'securitiesTransacted': 0,
                'price': 0.0
            }
        ]
        
        analysis = self.collector._analyze_insider_patterns(extreme_trades)
        self.assertIsInstance(analysis, dict)
        self.assertIn('significant_trades', analysis)
        # Very large transaction should be marked as significant
        self.assertGreaterEqual(len(analysis['significant_trades']), 1)

    def test_concurrent_requests(self):
        """Test handling of concurrent API requests."""
        import asyncio
        import concurrent.futures
        
        async def fetch_data():
            symbols = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'META']
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                # Create tasks for both news and insider data
                tasks = []
                for symbol in symbols:
                    tasks.append(executor.submit(self.collector.get_news, symbol))
                    tasks.append(executor.submit(self.collector.get_insider_data, symbol))
                
                # Wait for all tasks to complete
                results = [future.result() for future in concurrent.futures.as_completed(tasks)]
                return results
        
        # Run concurrent requests
        results = asyncio.run(fetch_data())
        
        # Verify all requests completed successfully
        self.assertEqual(len(results), 10)  # 5 symbols * 2 requests each
        for result in results:
            self.assertIsInstance(result, dict)
            self.assertTrue(any(key in result for key in ['articles', 'transactions']))

    def test_empty_response_handling(self):
        """Test handling of empty API responses."""
        # Test with a symbol that's likely to have no recent insider activity
        symbol = 'UNKNOWN123'  # Non-existent symbol
        
        # Should handle empty responses gracefully
        news_data = self.collector.get_news(symbol)
        self.assertEqual(news_data['articles'], [])
        self.assertEqual(news_data['press_releases'], [])
        
        insider_data = self.collector.get_insider_data(symbol)
        analysis = insider_data['analysis']
        
        # Verify empty analysis structure
        self.assertEqual(analysis['recent_activity'], 'none')
        self.assertEqual(analysis['buy_sell_ratio'], 0)
        self.assertEqual(len(analysis['significant_trades']), 0)
        self.assertEqual(analysis['trend'], 'neutral')

if __name__ == '__main__':
    unittest.main()
