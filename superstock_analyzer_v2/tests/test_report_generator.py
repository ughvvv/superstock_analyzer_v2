import unittest
from datetime import datetime
from report_generator import ReportGenerator
import os
import shutil
import tempfile

class TestReportGenerator(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for test reports
        self.test_dir = tempfile.mkdtemp()
        self.report_generator = ReportGenerator(output_dir=self.test_dir, use_ai=False)

    def tearDown(self):
        # Remove the temporary directory after tests
        shutil.rmtree(self.test_dir)

    def test_report_generation(self):
        """Test basic report generation functionality."""
        # Sample test data
        scored_stocks = [
            {
                'symbol': 'AAPL',
                'total_score': 85.5,
                'fundamental_score': 42.5,
                'technical_score': 25.5,
                'qualitative_score': 15.5,
                'bonus_points': 2.0,
                'passed_threshold': True,
                'key_metrics': {
                    'pe_ratio': '25.5',
                    'revenue_growth': '15.2%',
                    'profit_margin': '21.5%'
                },
                'catalysts': ['Strong product pipeline', 'Market expansion'],
                'risks': ['Supply chain constraints', 'Market competition']
            },
            {
                'symbol': 'MSFT',
                'total_score': 82.0,
                'fundamental_score': 41.0,
                'technical_score': 24.5,
                'qualitative_score': 14.5,
                'bonus_points': 2.0,
                'passed_threshold': True,
                'key_metrics': {
                    'pe_ratio': '28.3',
                    'revenue_growth': '18.5%',
                    'profit_margin': '35.2%'
                },
                'catalysts': ['Cloud growth', 'AI initiatives'],
                'risks': ['Regulatory concerns', 'Competition in cloud']
            }
        ]

        financial_data = {
            'AAPL': {'metrics': {'revenue': 1000000000}},
            'MSFT': {'metrics': {'revenue': 900000000}}
        }

        technical_data = {
            'AAPL': {'indicators': {'rsi': 65}},
            'MSFT': {'indicators': {'rsi': 58}}
        }

        quotes = [
            {'symbol': 'AAPL', 'price': 150.0},
            {'symbol': 'MSFT', 'price': 280.0}
        ]

        # Generate report
        self.report_generator.generate_report(
            scored_stocks=scored_stocks,
            financial_data=financial_data,
            technical_data=technical_data,
            quotes=quotes
        )

        # Check if report file was created
        report_files = os.listdir(self.test_dir)
        self.assertTrue(any(f.startswith('superstock_report_') for f in report_files))
        
        # Get the report file
        report_file = next(f for f in report_files if f.startswith('superstock_report_'))
        report_path = os.path.join(self.test_dir, report_file)
        
        # Check if report file exists and has content
        self.assertTrue(os.path.exists(report_path))
        with open(report_path, 'r') as f:
            content = f.read()
            
        # Check for key elements in the report
        self.assertIn('Superstock Analysis Report', content)
        self.assertIn('AAPL', content)
        self.assertIn('MSFT', content)
        self.assertIn('85.50', content)  # AAPL total score
        self.assertIn('82.00', content)  # MSFT total score
        self.assertIn('Strong product pipeline', content)
        self.assertIn('Cloud growth', content)

    def test_empty_data_handling(self):
        """Test report generation with empty data."""
        with self.assertRaises(Exception):
            self.report_generator.generate_report(
                scored_stocks=[],
                financial_data={},
                technical_data={},
                quotes=[]
            )

if __name__ == '__main__':
    unittest.main()
