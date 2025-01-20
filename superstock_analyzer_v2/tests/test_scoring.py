import unittest
from datetime import datetime
from scoring import StockScorer, StockScore
import pandas as pd
import numpy as np

class TestStockScorer(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.scorer = StockScorer()
        
        # Sample fundamental data
        self.fundamental_data = {
            'growth_metrics': {
                'annual': {
                    'net_income_growth': 25.5,
                    'revenue_growth': 18.7,
                    'eps_growth': 22.3,
                }
            },
            'financial_scores': {
                'altmanZScore': 3.2,
                'piotroskiScore': 7
            },
            'financial_ratios': {
                'debtToEquityTTM': 0.8,
                'currentRatioTTM': 2.1,
                'quickRatioTTM': 1.8,
                'interestCoverageTTM': 12.5
            },
            'profitability': {
                'grossMarginTTM': 45.2,
                'netMarginTTM': 15.8,
                'operatingMarginTTM': 22.4,
                'roaTTM': 12.5,
                'roeTTM': 18.9,
                'returnOnTangibleAssetsTTM': 16.2
            }
        }
        
        # Sample technical data
        self.technical_data = {
            'daily': {
                'price_momentum': 0.75,
                'volume_trend': {'strength': 0.8},
                'indicators': {
                    'rsi14': 65.5,
                    'rsi14_1week': 58.2,
                    'rsi14_1month': 62.1,
                    'stddev10': 2.1,
                    'stddev20': 2.5,
                    'stddev10_1week': 1.8,
                    'stddev20_1week': 2.2,
                    'adx14': 28.5,
                    'sma20': 155.25,
                    'sma50': 148.75,
                    'sma200': 142.50,
                    'williams14': -25.5
                }
            },
            'market_context': {
                'relative_strength_rank': 85.5
            }
        }
        
        # Sample qualitative data
        self.qualitative_data = {
            'earnings_analysis': {
                'gpt_analysis': {
                    'sentiment': 0.75,
                    'future_outlook': 0.85,
                    'key_points': ['Strong growth', 'Market leader'],
                    'risks': ['Competition'],
                    'opportunities': ['Expansion']
                }
            },
            'company_profile': {
                'gpt_analysis': {
                    'competitive_position': 0.65,
                    'market_position': 0.78,
                    'strengths': ['Brand recognition', 'Technology leadership'],
                    'weaknesses': ['High operating costs', 'Regional concentration']
                }
            },
            'management_assessment': {
                'gpt_analysis': {
                    'overall_assessment': 0.82,
                    'execution_track_record': 0.75,
                    'strategic_vision': 0.85,
                    'leadership_quality': 'Strong'
                }
            }
        }

    def test_fundamental_score_calculation(self):
        """Test fundamental score calculation."""
        score_tuple = self.scorer.calculate_fundamental_score(self.fundamental_data)
        self.assertIsInstance(score_tuple, tuple)
        score, details = score_tuple
        self.assertIsInstance(score, float)
        self.assertIsInstance(details, dict)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 50)  # Max fundamental weight is 50

    def test_technical_score_calculation(self):
        """Test technical score calculation."""
        score_tuple = self.scorer.calculate_technical_score(self.technical_data)
        self.assertIsInstance(score_tuple, tuple)
        score, details = score_tuple
        self.assertIsInstance(score, float)
        self.assertIsInstance(details, dict)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 30)  # Max technical weight is 30

    def test_qualitative_score_calculation(self):
        """Test qualitative score calculation."""
        score_tuple = self.scorer.calculate_qualitative_score(self.qualitative_data)
        self.assertIsInstance(score_tuple, tuple)
        score, details = score_tuple
        self.assertIsInstance(score, float)
        self.assertIsInstance(details, dict)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 20)  # Max qualitative weight is 20

    def test_total_score_calculation(self):
        """Test total score calculation with all components."""
        stock_score = self.scorer.calculate_total_score(
            'AAPL',
            self.fundamental_data,
            self.technical_data,
            self.qualitative_data
        )
        
        self.assertIsInstance(stock_score, StockScore)
        self.assertGreaterEqual(stock_score.total_score, 0)
        self.assertLessEqual(stock_score.total_score, 100)
        self.assertTrue(hasattr(stock_score, 'gpt_insights'))

    def test_data_validation(self):
        """Test data validation functionality."""
        # Test with valid data
        self.assertTrue(self.scorer.validate_data_quality(self.fundamental_data, 'fundamental'))
        
        # Test with invalid data
        invalid_data = {
            'growth_metrics': {
                'annual': {
                    'net_income_growth': None,
                    'revenue_growth': float('nan'),
                }
            }
        }
        self.assertFalse(self.scorer.validate_data_quality(invalid_data, 'fundamental'))

    def test_market_context_update(self):
        """Test market context update functionality."""
        test_stocks = [
            {
                'symbol': 'AAPL',
                'fundamental_data': self.fundamental_data,
                'technical_data': self.technical_data,
                'company_profile': {'sector': 'Technology'}
            },
            {
                'symbol': 'GOOGL',
                'fundamental_data': {
                    'growth_metrics': {'annual': {'net_income_growth': 28.5}},
                    'financial_scores': {'altmanZScore': 3.5},
                    'profitability': {'roeTTM': 22.4}
                },
                'technical_data': self.technical_data,
                'company_profile': {'sector': 'Technology'}
            },
            {
                'symbol': 'MSFT',
                'fundamental_data': {
                    'growth_metrics': {'annual': {'net_income_growth': 32.1}},
                    'financial_scores': {'altmanZScore': 3.8},
                    'profitability': {'roeTTM': 25.7}
                },
                'technical_data': self.technical_data,
                'company_profile': {'sector': 'Technology'}
            }
        ]
        
        self.scorer.update_market_context(test_stocks)
        
        # Verify that market context has been updated
        self.assertIn('sector_data', self.scorer.market_context)
        self.assertIn('Technology', self.scorer.market_context['sector_data'])
        self.assertGreater(
            len(self.scorer.market_context['sector_data']['Technology']), 0
        )

    def test_empty_score_creation(self):
        """Test creation of empty score for invalid data."""
        empty_score = self.scorer._create_empty_score('AAPL')
        self.assertEqual(empty_score.symbol, 'AAPL')
        self.assertEqual(empty_score.total_score, 0)
        self.assertFalse(empty_score.passed_threshold)

    def test_string_data_handling(self):
        """Test handling of string data in scoring system."""
        # Test with string data (simulating API response)
        string_technical_data = '''{
            "daily": {
                "price_momentum": "0.75",
                "volume_trend": {"strength": "0.8"},
                "indicators": {
                    "rsi14": "65.5",
                    "rsi14_1week": "58.2",
                    "rsi14_1month": "62.1",
                    "stddev10": "2.1",
                    "stddev20": "2.5",
                    "stddev10_1week": "1.8",
                    "stddev20_1week": "2.2",
                    "adx14": "28.5",
                    "sma20": "155.25",
                    "sma50": "148.75",
                    "sma200": "142.50"
                }
            },
            "market_context": {
                "relative_strength_rank": "85.5"
            }
        }'''
        
        string_fundamental_data = '''{
            "growth_metrics": {
                "annual": {
                    "net_income_growth": "25.5",
                    "revenue_growth": "18.7",
                    "eps_growth": "22.3"
                }
            },
            "financial_scores": {
                "altmanZScore": "3.2",
                "piotroskiScore": "7"
            },
            "financial_ratios": {
                "debtToEquityTTM": "0.8",
                "currentRatioTTM": "2.1",
                "quickRatioTTM": "1.8",
                "interestCoverageTTM": "12.5"
            },
            "profitability": {
                "grossMarginTTM": "45.2",
                "netMarginTTM": "15.8",
                "operatingMarginTTM": "22.4",
                "roaTTM": "12.5",
                "roeTTM": "18.9",
                "returnOnTangibleAssetsTTM": "16.2"
            }
        }'''

        string_qualitative_data = '''{
            "earnings_analysis": {
                "gpt_analysis": {
                    "sentiment": "0.85",
                    "key_points": [
                        "Strong revenue growth",
                        "Improving margins",
                        "Positive market outlook"
                    ],
                    "risks": [
                        "Market competition",
                        "Supply chain challenges"
                    ],
                    "opportunities": [
                        "Market expansion",
                        "New product lines"
                    ]
                }
            },
            "company_profile": {
                "gpt_analysis": {
                    "competitive_position": "0.78",
                    "market_position": "Strong market leader",
                    "strengths": [
                        "Brand recognition",
                        "Technology leadership"
                    ],
                    "weaknesses": [
                        "High operating costs",
                        "Regional concentration"
                    ]
                }
            },
            "management_assessment": {
                "gpt_analysis": {
                    "overall_assessment": "0.82",
                    "leadership_quality": "Strong",
                    "execution_track_record": "Proven",
                    "strategic_vision": "Clear and achievable"
                }
            }
        }'''
        
        # Initialize market context with sample data
        sample_stocks = []
        for i in range(10):
            sample_stocks.append({
                'symbol': f'STOCK{i}',
                # Fundamental data
                'growth_metrics': {
                    'annual': {
                        'net_income_growth': 20 + i,
                        'revenue_growth': 15 + i,
                        'eps_growth': 18 + i
                    }
                },
                'financial_scores': {
                    'altmanZScore': 2.5 + i/10,
                    'piotroskiScore': 6 + i/10
                },
                'financial_ratios': {
                    'debtToEquityTTM': 0.5 + i/10,
                    'currentRatioTTM': 1.8 + i/10,
                    'quickRatioTTM': 1.5 + i/10,
                    'interestCoverageTTM': 10 + i
                },
                'profitability': {
                    'grossMarginTTM': 40 + i,
                    'netMarginTTM': 12 + i,
                    'operatingMarginTTM': 18 + i,
                    'roaTTM': 10 + i,
                    'roeTTM': 15 + i,
                    'returnOnTangibleAssetsTTM': 12 + i
                },
                # Technical data
                'daily': {
                    'price_momentum': 0.6 + i/10,
                    'volume_trend': {'strength': 0.7 + i/10},
                    'indicators': {
                        'rsi14': 55 + i,
                        'rsi14_1week': 52 + i,
                        'rsi14_1month': 58 + i,
                        'stddev10': 2.0 + i/10,
                        'stddev20': 2.2 + i/10,
                        'stddev10_1week': 1.8 + i/10,
                        'stddev20_1week': 2.0 + i/10,
                        'adx14': 25 + i,
                        'sma20': 150 + i,
                        'sma50': 145 + i,
                        'sma200': 140 + i
                    }
                },
                'market_context': {
                    'relative_strength_rank': 75 + i
                },
                # Qualitative data
                'earnings_analysis': {
                    'gpt_analysis': {
                        'sentiment': 0.7 + i/10,
                        'key_points': ['Strong growth', 'Market leader'],
                        'risks': ['Competition'],
                        'opportunities': ['Expansion']
                    }
                },
                'company_profile': {
                    'gpt_analysis': {
                        'competitive_position': 0.65 + i/10,
                        'market_position': 'Strong'
                    }
                },
                'management_assessment': {
                    'gpt_analysis': {
                        'overall_assessment': 0.75 + i/10,
                        'leadership_quality': 'Good'
                    }
                }
            })
        
        self.scorer.update_market_context(sample_stocks)
        
        # Test scoring with string data
        score = self.scorer.calculate_total_score(
            symbol="TEST",
            fundamental_data=string_fundamental_data,
            technical_data=string_technical_data,
            qualitative_data=string_qualitative_data
        )
        
        # Verify score was calculated successfully
        self.assertIsInstance(score, StockScore)
        self.assertGreater(score.total_score, 0)
        self.assertGreater(score.fundamental_score, 0)
        self.assertGreater(score.technical_score, 0)
        self.assertGreater(score.qualitative_score, 0)  # Now testing qualitative score
        
        # Print detailed score information for debugging
        print(f"\nTest Score Details:")
        print(f"Total Score: {score.total_score:.2f}")
        print(f"Fundamental Score: {score.fundamental_score:.2f}")
        print(f"Technical Score: {score.technical_score:.2f}")
        print(f"Qualitative Score: {score.qualitative_score:.2f}")
        print(f"Bonus Points: {score.bonus_points:.2f}")

if __name__ == '__main__':
    unittest.main()
