import logging
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime
import os
from openai import OpenAI
import json
import tiktoken
import time
from functools import wraps

def log_step(func):
    """Decorator to log function entry, exit, and execution time."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(__name__)
        start_time = time.time()
        
        logger.info(f"Starting {func.__name__}")
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"Completed {func.__name__} in {execution_time:.2f} seconds")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Failed {func.__name__} after {execution_time:.2f} seconds: {str(e)}")
            raise
    return wrapper

class ReportGenerator:
    """Generate reports from market analysis results with AI-powered insights."""
    
    def __init__(self, output_dir: str = "reports", api_key: Optional[str] = None, use_ai: bool = True):
        """Initialize the report generator."""
        self.logger = logging.getLogger(__name__)
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.use_ai = use_ai
        
        # Initialize OpenAI client with API key if AI is enabled
        if self.use_ai:
            if api_key:
                self.client = OpenAI(api_key=api_key)
            else:
                self.client = OpenAI()  # Will use OPENAI_API_KEY environment variable
                
            self.encoding = tiktoken.get_encoding("cl100k_base")
        
    def _validate_data(self, df: pd.DataFrame) -> List[str]:
        """Validate the input data and return list of any issues."""
        issues = []
        
        # Check for required columns
        required_columns = ['symbol', 'total_score']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            issues.append(f"Missing required columns: {missing_columns}")
            
        # Check for data quality
        if df['total_score'].isna().any():
            issues.append("Found missing values in total_score column")
            
        # Check for duplicate symbols
        if df.index.duplicated().any():
            issues.append("Found duplicate stock symbols")
            
        # Log data statistics
        self.logger.info(f"Data validation stats:")
        self.logger.info(f"Total rows: {len(df)}")
        self.logger.info(f"Unique symbols: {df.index.nunique()}")
        self.logger.info(f"Score range: {df['total_score'].min():.2f} to {df['total_score'].max():.2f}")
        
        return issues
        
    @log_step
    def _count_tokens(self, text: str) -> int:
        """Count the number of tokens in a text string."""
        if self.use_ai:
            return len(self.encoding.encode(text))
        else:
            return 0
        
    @log_step
    def _generate_ai_insights(self, df: pd.DataFrame, top_n: int = 5) -> str:
        """Generate AI-powered insights from the analysis results."""
        try:
            if self.use_ai:
                self.logger.info(f"Generating AI insights for top {top_n} stocks")
                
                # Prepare data for AI analysis
                top_stocks = df.head(top_n).to_dict('records')
                sector_dist = df['sector'].value_counts().to_dict() if 'sector' in df.columns else {}
                
                # First, get individual stock analyses
                stock_analyses = []
                for idx, stock in enumerate(top_stocks, 1):
                    self.logger.info(f"Analyzing stock {idx}/{top_n}: {stock.get('symbol', 'Unknown')}")
                    
                    stock_prompt = f"""Analyze this stock opportunity in detail:
                    Stock Data: {json.dumps(stock, indent=2)}
                    
                    Please provide:
                    1. Company Overview
                    2. Key Metrics Analysis
                    3. Technical Indicators
                    4. Risk Assessment
                    5. Investment Thesis
                    """
                    
                    prompt_tokens = self._count_tokens(stock_prompt)
                    self.logger.debug(f"Stock analysis prompt tokens: {prompt_tokens}")
                    
                    stock_response = self.client.chat.completions.create(
                        model="gpt-4o",  # Using the latest GPT-4o model
                        messages=[{"role": "user", "content": stock_prompt}],
                        temperature=0.7
                    )
                    
                    response_tokens = self._count_tokens(stock_response.choices[0].message.content)
                    self.logger.debug(f"Stock analysis response tokens: {response_tokens}")
                    
                    stock_analysis = f"""
                    ===== {stock.get('symbol', 'Unknown')} Analysis =====
                    {stock_response.choices[0].message.content}
                    """
                    stock_analyses.append(stock_analysis)
                    
                    self.logger.info(f"Completed analysis for {stock.get('symbol', 'Unknown')}")
                
                # Then, get overall market analysis
                self.logger.info("Generating market overview")
                market_prompt = f"""Provide a market overview based on this data:
                Sector Distribution: {json.dumps(sector_dist, indent=2)}
                
                Please provide:
                1. Market Trends
                2. Sector Performance
                3. Market Opportunities
                4. Risk Factors
                """
                
                prompt_tokens = self._count_tokens(market_prompt)
                self.logger.debug(f"Market overview prompt tokens: {prompt_tokens}")
                
                market_response = self.client.chat.completions.create(
                    model="gpt-4o",  # Using the latest GPT-4o model
                    messages=[{"role": "user", "content": market_prompt}],
                    temperature=0.7
                )
                
                response_tokens = self._count_tokens(market_response.choices[0].message.content)
                self.logger.debug(f"Market overview response tokens: {response_tokens}")
                
                # Combine all insights
                full_analysis = f"""
                ======= Market Overview =======
                {market_response.choices[0].message.content}
                
                ======= Individual Stock Analyses =======
                {"".join(stock_analyses)}
                
                ======= Investment Summary =======
                Top {top_n} stocks have been analyzed based on our proprietary scoring model.
                Please review individual analyses for specific opportunities and risks.
                """
                
                total_tokens = self._count_tokens(full_analysis)
                self.logger.info(f"Total analysis tokens: {total_tokens}")
                
                return full_analysis
                
            else:
                return "AI insights generation is disabled."
            
        except Exception as e:
            self.logger.error(f"Error generating AI insights: {str(e)}", exc_info=True)
            return "AI insights generation failed. Please check the logs for details."
    
    @log_step
    def generate_report(
        self,
        scored_stocks: List[Dict],
        financial_data: Dict,
        technical_data: Dict,
        quotes: List[Dict]
    ) -> None:
        """Generate a comprehensive analysis report."""
        try:
            # Create DataFrame from scored stocks
            df = pd.DataFrame([
                {
                    'symbol': score['symbol'],
                    'total_score': score['total_score'],
                    'fundamental_score': score['fundamental_score'],
                    'technical_score': score['technical_score'],
                    'qualitative_score': score['qualitative_score'],
                    'bonus_points': score['bonus_points'],
                    'passed_threshold': score['passed_threshold'],
                    'key_metrics': score['key_metrics'],
                    'catalysts': score['catalysts'],
                    'risks': score['risks']
                }
                for score in scored_stocks
            ])
            
            # Sort by total score descending
            df = df.sort_values('total_score', ascending=False)
            
            # Validate the data
            issues = self._validate_data(df)
            if issues:
                for issue in issues:
                    self.logger.warning(f"Data validation issue: {issue}")
                    
            # Generate insights for top stocks
            insights = self._generate_ai_insights(df)
            
            # Create the report
            report_time = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_file = os.path.join(self.output_dir, f'superstock_report_{report_time}.html')
            
            # Generate HTML report
            html_content = f"""
            <html>
            <head>
                <title>Superstock Analysis Report - {datetime.now().strftime('%Y-%m-%d')}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    h1, h2 {{ color: #2c3e50; }}
                    .insights {{ background: #f8f9fa; padding: 15px; border-radius: 5px; }}
                    table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    th {{ background-color: #f2f2f2; }}
                    tr:nth-child(even) {{ background-color: #f9f9f9; }}
                    .metrics {{ margin: 10px 0; }}
                    .catalysts, .risks {{ color: #666; margin: 5px 0; }}
                </style>
            </head>
            <body>
                <h1>Superstock Analysis Report</h1>
                <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                
                <h2>AI Market Insights</h2>
                <div class="insights">
                    {insights}
                </div>
                
                <h2>Top Stocks</h2>
                <table>
                    <tr>
                        <th>Symbol</th>
                        <th>Total Score</th>
                        <th>Fundamental</th>
                        <th>Technical</th>
                        <th>Qualitative</th>
                        <th>Key Metrics</th>
                        <th>Catalysts</th>
                        <th>Risks</th>
                    </tr>
            """
            
            # Add rows for each stock
            for _, row in df.iterrows():
                metrics_html = "<br>".join([f"{k}: {v}" for k, v in row['key_metrics'].items()])
                catalysts_html = "<br>".join(row['catalysts'])
                risks_html = "<br>".join(row['risks'])
                
                html_content += f"""
                    <tr>
                        <td>{row['symbol']}</td>
                        <td>{row['total_score']:.2f}</td>
                        <td>{row['fundamental_score']:.2f}</td>
                        <td>{row['technical_score']:.2f}</td>
                        <td>{row['qualitative_score']:.2f}</td>
                        <td class="metrics">{metrics_html}</td>
                        <td class="catalysts">{catalysts_html}</td>
                        <td class="risks">{risks_html}</td>
                    </tr>
                """
                
            html_content += """
                </table>
            </body>
            </html>
            """
            
            # Write the report
            with open(report_file, 'w') as f:
                f.write(html_content)
                
            self.logger.info(f"Report generated successfully: {report_file}")
            print(f"\nReport generated: {report_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to generate report: {str(e)}")
            raise

    def _print_summary_stats(self, df: pd.DataFrame) -> None:
        """Print summary statistics of the analysis results."""
        try:
            self.logger.info("\nAnalysis Summary:")
            self.logger.info(f"Total stocks analyzed: {len(df)}")
            
            if 'total_score' in df.columns:
                self.logger.info(f"Score Statistics:")
                self.logger.info(f"Average Score: {df['total_score'].mean():.2f}")
                self.logger.info(f"Median Score: {df['total_score'].median():.2f}")
                self.logger.info(f"Max Score: {df['total_score'].max():.2f}")
                self.logger.info(f"Min Score: {df['total_score'].min():.2f}")
            
            if 'sector' in df.columns:
                sector_counts = df['sector'].value_counts()
                self.logger.info("\nSector Distribution:")
                for sector, count in sector_counts.items():
                    self.logger.info(f"{sector}: {count}")
                    
            if 'market_cap' in df.columns:
                self.logger.info("\nMarket Cap Distribution:")
                df['market_cap_category'] = pd.cut(df['market_cap'], 
                                                 bins=[0, 300e6, 2e9, 10e9, float('inf')],
                                                 labels=['Small', 'Mid', 'Large', 'Mega'])
                cap_dist = df['market_cap_category'].value_counts()
                for cap, count in cap_dist.items():
                    self.logger.info(f"{cap}: {count}")
            
        except Exception as e:
            self.logger.error(f"Error printing summary stats: {str(e)}")
