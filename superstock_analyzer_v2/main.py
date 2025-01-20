import os
import time
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set, Tuple
import pandas as pd
from dotenv import load_dotenv
import logging
import pickle
from pathlib import Path
from tqdm import tqdm
import concurrent.futures
import asyncio
import aiohttp

from data_collectors.technical_data_collector import TechnicalDataCollector
from data_collectors.financial.collector import FinancialDataCollector
from data_collectors.market_data_collector import MarketDataCollector
from data_collectors.pattern_analyzer import PatternAnalyzer
from scoring import StockScore, StockScorer
from report_generator import ReportGenerator

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class SuperstockAnalyzer:
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the Superstock Analyzer."""
        # Initialize logger
        self.logger = logging.getLogger(__name__)
        
        # Validate environment variables
        self._validate_environment()

        # Initialize configuration with updated thresholds
        self.config = config or {
            'output_dir': 'reports',
            'cache_dir': 'cache',
            'state_file': 'analysis_state.json',
            'min_market_cap': 5e6,      # $5M minimum per methodology
            'max_market_cap': 250e6,    # $250M maximum per methodology
            'min_price': 1.0,           # $1 minimum price
            'min_volume': 100000,       # Base minimum volume
            'min_volume_factor': 500000, # Factor for dynamic volume calculation
            'max_requests_per_minute': 3000,
            'request_timeout': int(os.getenv('REQUEST_TIMEOUT_SECONDS', '60')),
            'batch_size': 25,           # Increased for better throughput
            'max_symbols': 2000,        # Increased to cover more stocks
            'max_workers': 10,          # Increased for better parallelization
            'max_retries': 5,
            'retry_delay': 1,
            'max_delay': 30,
            # Quantitative thresholds per methodology
            'min_fundamental_score_for_qualitative': 35,  # 77.8% of 45 points
            'min_technical_score_for_qualitative': 20,    # 80% of 25 points
            'min_earnings_growth': 0.15,                  # 15% minimum
            'max_debt_to_equity': 0.75,                   # 75% maximum
            'min_relative_strength_rank': 80              # Top 20%
        }

        # Create necessary directories
        os.makedirs(self.config['output_dir'], exist_ok=True)
        os.makedirs(self.config['cache_dir'], exist_ok=True)

        # Initialize API keys
        self.fmp_api_key = os.getenv('FMP_API_KEY')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        
        if not self.fmp_api_key:
            raise ValueError("FMP_API_KEY environment variable not found")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable not found")

        # Initialize components with proper API keys
        self.technical_data_collector = TechnicalDataCollector(api_key=self.fmp_api_key)
        self.financial_data_collector = FinancialDataCollector(api_key=self.fmp_api_key)
        self.market_data_collector = MarketDataCollector(api_key=self.fmp_api_key)
        
        # Update market data collector with config
        self.market_data_collector.update_config(self.config)
        
        self.pattern_analyzer = PatternAnalyzer()
        self.scorer = StockScorer()
        self.report_generator = ReportGenerator(
            output_dir=self.config['output_dir'],
            api_key=self.openai_api_key
        )

        # Setup proxy if configured
        if os.getenv('HTTP_PROXY') or os.getenv('HTTPS_PROXY'):
            self._setup_proxy()

    async def collect_market_data_batch(self, quotes_batch: List[Dict]) -> List[Dict]:
        """Collect market data for a batch of stocks concurrently."""
        tasks = []
        results = []
        retry_queue = []
        max_retries = self.config.get('max_retries', 5)
        retry_delay = self.config.get('retry_delay', 1)
        
        async with aiohttp.ClientSession() as session:
            for quote in quotes_batch:
                task = asyncio.create_task(
                    self._collect_with_retry(
                        quote,
                        max_retries=max_retries,
                        retry_delay=retry_delay,
                        session=session
                    )
                )
                tasks.append(task)
            
            completed_tasks = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in completed_tasks:
                if isinstance(result, Exception):
                    self.logger.error(f"Error collecting market data: {str(result)}")
                    continue
                if result:
                    results.append(result)
        
        return results

    async def _collect_with_retry(self, quote: Dict, max_retries: int, retry_delay: float, session) -> Optional[Dict]:
        """Helper method to retry failed requests with exponential backoff."""
        retries = 0
        while retries < max_retries:
            try:
                return await self.market_data_collector.get_market_data(quote['symbol'], session=session)
            except Exception as e:
                retries += 1
                if retries == max_retries:
                    self.logger.error(f"Failed to collect data for {quote['symbol']} after {max_retries} retries: {str(e)}")
                    return None
                wait_time = retry_delay * (2 ** (retries - 1))  # Exponential backoff
                self.logger.warning(f"Retry {retries}/{max_retries} for {quote['symbol']} after {wait_time}s")
                await asyncio.sleep(wait_time)

    async def collect_single_stock_data(self, symbol: str, quote: Dict) -> Optional[Dict]:
        """Collect all data for a single stock with comprehensive validation."""
        try:
            # Validate quote data first
            if not self._validate_quote_data(quote):
                self.logger.warning(f"Invalid quote data for {symbol}")
                return None

            # Get financial and technical data concurrently
            financials_task = asyncio.create_task(
                self.financial_data_collector.get_financials_async(symbol)
            )
            technical_task = asyncio.create_task(
                self.technical_data_collector.get_technical_data_batch_async([symbol])
            )
            
            # Wait for both tasks to complete
            financials, technical_data = await asyncio.gather(financials_task, technical_task)
            
            # Validate financial data
            if not self._validate_financial_data(financials):
                self.logger.warning(f"Invalid or incomplete financial data for {symbol}")
                return None
            
            # Validate technical data
            if not technical_data or not isinstance(technical_data, dict) or symbol not in technical_data:
                self.logger.warning(f"Missing technical data for {symbol}")
                return None
                
            tech_data = technical_data[symbol]
            if not self._validate_technical_data(tech_data):
                self.logger.warning(f"Invalid or incomplete technical data for {symbol}")
                return None
            
            # Construct standardized data structure
            stock_data = {
                'symbol': symbol,
                'quote': quote,
                'financials': {
                    'growth_metrics': financials.get('growth_metrics', {}),
                    'financial_ratios': financials.get('financial_ratios', {}),
                    'financial_scores': financials.get('financial_scores', {}),
                    'profitability': financials.get('profitability', {}),
                    'working_capital_trend': financials.get('working_capital_trend', {}),
                    'operating_leverage': financials.get('operating_leverage', {})
                },
                'technical_data': {
                    'indicators': tech_data.get('technical_indicators', {}),
                    'price': tech_data.get('price'),
                    'volume': tech_data.get('volume')
                }
            }
            
            # Final validation of complete data structure
            if self._validate_stock_data(stock_data):
                return stock_data
            else:
                self.logger.warning(f"Final validation failed for {symbol}")
                return None
        except Exception as e:
            self.logger.error(f"Error collecting data for {symbol}: {str(e)}")
            return None

    async def analyze_market(self) -> List[Dict]:
        """Analyze the entire market using Jesse Stine's Superstock methodology."""
        try:
            self.logger.info("\n📊 Starting market analysis...")
            stats = {
                'total': 0,
                'passed_initial': 0,
                'complete_data': 0,
                'passed_scoring': 0
            }

            # Stage 1: Get Initial Universe of Stocks
            self.logger.info("\n🌎 Stage 1: Getting Initial Universe")
            initial_quotes = await self.market_data_collector.get_initial_quotes_async()
            if not initial_quotes:
                self.logger.error("Failed to get initial quotes")
                return []

            # Stage 2: Apply Initial Filters
            self.logger.info("\n🔍 Stage 2: Applying Initial Filters")
            filtered_quotes = []
            stats['total'] = len(initial_quotes)

            for quote in initial_quotes:
                try:
                    processed_quote = self.market_data_collector.process_quote(quote)
                    if not processed_quote:
                        continue
                    filtered_quotes.append(processed_quote)
                    stats['passed_initial'] += 1
                except Exception as e:
                    self.logger.error(f"Error processing quote: {str(e)}")

            # Log filtering statistics
            self.logger.info("\nFiltering Statistics:")
            self.logger.info(f"Total Quotes: {stats['total']:,}")
            self.logger.info(f"Passed Initial Filtering: {stats['passed_initial']:,}")

            # Stage 3: Collect All Data for Percentile Analysis
            self.logger.info("\n📊 Stage 3: Data Collection for Market Context")
            market_data = []
            batch_size = self.config['batch_size']

            # Process stocks in batches
            for i in range(0, len(filtered_quotes), batch_size):
                batch = filtered_quotes[i:i + batch_size]
                self.logger.info(f"Processing batch {i//batch_size + 1} of {(len(filtered_quotes) + batch_size - 1)//batch_size}")

                # Collect data for the batch concurrently
                batch_results = await self.collect_market_data_batch(batch)

                # Filter out None results and add to market_data
                valid_results = [r for r in batch_results if r is not None]
                market_data.extend(valid_results)
                stats['complete_data'] += len(valid_results)

                self.logger.info(f"Batch complete: {len(valid_results)} valid results")

            self.logger.info(f"Collected market data for {len(market_data)} stocks")

            # Stage 4: Update Market Context and Score Stocks
            self.logger.info("\n📈 Stage 4: Percentile Analysis and Scoring")
            if not market_data:
                self.logger.error("No valid market data to analyze")
                return []
                
            # Validate and standardize market data before updating context
            validated_market_data = []
            for data in market_data:
                try:
                    if not self._validate_stock_data(data):
                        self.logger.warning(f"Invalid data structure for {data.get('symbol', 'UNKNOWN')}")
                        continue
                    validated_market_data.append(data)
                except Exception as e:
                    self.logger.error(f"Error validating market data: {str(e)}")
                    continue

            if not validated_market_data:
                self.logger.error("No valid market data after validation")
                return []

            self.scorer.update_market_context(validated_market_data)
            scored_stocks = []

            for data in validated_market_data:
                try:
                    symbol = data['symbol']
                    
                    # Prepare standardized data for scoring
                    score_data = {
                        'symbol': symbol,
                        'financials': data['financials'],
                        'technical_data': data['technical_data'],
                        'quote': data['quote']
                    }
                    
                    # Calculate scores
                    fundamental_score = self.scorer.calculate_fundamental_score(score_data)
                    technical_score = self.scorer.calculate_technical_score(score_data)
                    
                    # Check if stock passes quantitative thresholds
                    passes_thresholds, failures = self._passes_quantitative_thresholds(
                        symbol, fundamental_score, technical_score,
                        data['financials'], data['technical_data'], data['quote']
                    )
                    
                    if not passes_thresholds:
                        self.logger.debug(f"Stock {symbol} failed thresholds: {', '.join(failures)}")
                        continue
                        
                    # Create a proper StockScore object
                    score = StockScore(
                        symbol=symbol,
                        total_score=(fundamental_score + technical_score) / 2,
                        fundamental_score=fundamental_score,
                        technical_score=technical_score,
                        qualitative_score=0.0,  # Default to 0 for now
                        bonus_points=0.0,  # Default to 0 for now
                        analysis_date=datetime.now(),
                        key_metrics=data['financials'].get('financial_ratios', {}),
                        catalysts=[],  # Empty list for now
                        risks=[],  # Empty list for now
                        passed_threshold=True,
                        gpt_insights={}
                    )
                    
                    # Add score to data and append to results
                    data['scores'] = score.__dict__
                    scored_stocks.append(data)
                    stats['passed_scoring'] += 1
                    self.logger.debug(f"Successfully scored {symbol}")
                    
                except Exception as e:
                    self.logger.error(f"Error scoring {data.get('symbol', 'Unknown')}: {str(e)}")

            # Sort stocks by final score
            scored_stocks.sort(key=lambda x: x['scores']['final'], reverse=True)

            # Log final statistics
            self.logger.info("\nAnalysis Statistics:")
            self.logger.info(f"Total Stocks: {stats['total']:,}")
            self.logger.info(f"Passed Initial Filtering: {stats['passed_initial']:,}")
            self.logger.info(f"Complete Data Available: {stats['complete_data']:,}")
            self.logger.info(f"Passed Final Scoring: {stats['passed_scoring']:,}")

            # Generate report
            if scored_stocks:
                # Extract and convert scores to dictionaries for the report generator
                score_list = []
                for stock in scored_stocks:
                    if 'scores' in stock:
                        score = stock['scores']
                        if isinstance(score, StockScore):
                            score_list.append({
                                'symbol': score.symbol,
                                'total_score': score.total_score,
                                'fundamental_score': score.fundamental_score,
                                'technical_score': score.technical_score,
                                'qualitative_score': score.qualitative_score,
                                'bonus_points': score.bonus_points,
                                'passed_threshold': score.passed_threshold,
                                'key_metrics': score.key_metrics,
                                'catalysts': score.catalysts,
                                'risks': score.risks
                            })
                if score_list:
                    self.report_generator.generate_report(
                        scored_stocks=score_list,
                        financial_data={},  # Empty dict as placeholder
                        technical_data={},  # Empty dict as placeholder
                        quotes=[]  # Empty list as placeholder
                    )

            return scored_stocks

        except Exception as e:
            self.logger.error(f"Critical error during market analysis: {str(e)}")
            raise

    def _validate_quote_data(self, quote: Dict) -> bool:
        """Validate quote data structure and values."""
        try:
            if not isinstance(quote, dict):
                return False

            required_fields = ['symbol', 'price', 'volume', 'market_cap']
            if not all(field in quote for field in required_fields):
                return False

            # Validate numeric values
            try:
                price = float(quote['price'])
                volume = int(quote['volume'])
                market_cap = float(quote['market_cap'])
                
                if price <= 0 or volume <= 0 or market_cap <= 0:
                    return False
                    
            except (ValueError, TypeError):
                return False

            return True

        except Exception as e:
            self.logger.error(f"Error validating quote data: {str(e)}")
            return False

    def _validate_financial_data(self, data: Dict) -> bool:
        """Validate financial data structure and required metrics."""
        try:
            if not isinstance(data, dict):
                return False

            # Check required sections
            required_sections = [
                'growth_metrics', 'financial_ratios', 'financial_scores',
                'profitability', 'working_capital_trend', 'operating_leverage'
            ]
            if not all(section in data for section in required_sections):
                return False

            # Validate growth metrics structure
            growth_metrics = data.get('growth_metrics', {})
            if not all(period in growth_metrics for period in ['quarterly', 'annual']):
                return False

            # Validate financial ratios
            ratios = data.get('financial_ratios', {})
            required_ratios = [
                'debtToEquityTTM', 'currentRatioTTM', 'quickRatioTTM',
                'returnOnEquityTTM', 'returnOnAssetsTTM'
            ]
            if not all(ratio in ratios for ratio in required_ratios):
                return False

            return True

        except Exception as e:
            self.logger.error(f"Error validating financial data: {str(e)}")
            return False

    def _validate_technical_data(self, data: Dict) -> bool:
        """Validate technical data structure and required indicators."""
        try:
            if not isinstance(data, dict):
                return False

            # Check required fields
            if 'technical_indicators' not in data:
                return False

            # Validate technical indicators
            indicators = data['technical_indicators']
            required_indicators = ['sma20', 'sma50', 'sma200', 'rsi14']
            if not all(ind in indicators for ind in required_indicators):
                return False

            # Validate numeric values
            for value in indicators.values():
                if not isinstance(value, (int, float)) or pd.isna(value):
                    return False

            return True

        except Exception as e:
            self.logger.error(f"Error validating technical data: {str(e)}")
            return False

    def _validate_stock_data(self, data: Dict) -> bool:
        """Validate complete stock data structure."""
        try:
            if not isinstance(data, dict):
                return False

            # Check required top-level sections
            required_sections = ['symbol', 'quote', 'financials', 'technical_data']
            if not all(section in data for section in required_sections):
                return False

            # Validate each section
            if not self._validate_quote_data(data['quote']):
                return False

            if not self._validate_financial_data(data['financials']):
                return False

            if not self._validate_technical_data(data['technical_data']):
                return False

            return True

        except Exception as e:
            self.logger.error(f"Error validating stock data: {str(e)}")
            return False

    def _validate_environment(self) -> None:
        """Validate required environment variables are set."""
        required_vars = ['OPENAI_API_KEY', 'FMP_API_KEY']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            raise EnvironmentError(
                f"Missing required environment variables: {', '.join(missing_vars)}\n"
                "Please set these variables in your .env file."
            )

        optional_apis = {
            'ALPHA_VANTAGE_API_KEY': 'Alpha Vantage',
            'FINNHUB_API_KEY': 'Finnhub'
        }
        
        for key, name in optional_apis.items():
            if not os.getenv(key):
                self.logger.warning(f"{name} API key not found. Some features may be limited.")

    def _setup_proxy(self) -> None:
        """Configure proxy settings if provided in environment."""
        os.environ['HTTP_PROXY'] = os.getenv('HTTP_PROXY', '')
        os.environ['HTTPS_PROXY'] = os.getenv('HTTPS_PROXY', '')
        os.environ['REQUESTS_CA_BUNDLE'] = os.getenv('SSL_CERT_FILE', '')
        self.logger.info("Proxy configuration applied")

    def _passes_quantitative_thresholds(
        self,
        symbol: str,
        fundamental_score: float,
        technical_score: float,
        financials: Dict,
        technical_data: Dict,
        quote: Dict
    ) -> Tuple[bool, List[str]]:
        """Apply quantitative thresholds before proceeding to qualitative analysis."""
        failures = []
        
        # Market cap check
        market_cap = quote.get('marketCap', 0)
        if market_cap < self.config['min_market_cap']:
            failures.append(f"Market cap {market_cap:,.0f} < {self.config['min_market_cap']:,.0f}")
            
        # Price check
        price = quote.get('price', 0)
        if price < self.config['min_price']:
            failures.append(f"Price ${price:.2f} < ${self.config['min_price']:.2f}")
            
        # Volume check
        volume = quote.get('volume', 0)
        if volume < self.config['min_volume']:
            failures.append(f"Volume {volume:,} < {self.config['min_volume']:,}")
            
        # Fundamental score check
        if fundamental_score < self.config['min_fundamental_score_for_qualitative']:
            failures.append(f"Low fundamental score {fundamental_score:.1f} < {self.config['min_fundamental_score_for_qualitative']}")
            
        # Technical score check
        if technical_score < self.config['min_technical_score_for_qualitative']:
            failures.append(f"Low technical score {technical_score:.2f} < {self.config['min_technical_score_for_qualitative']}")
            
        # Earnings growth check
        growth = financials.get('growth_metrics', {}).get('annual', {}).get('net_income_growth', 0)
        if growth < self.config['min_earnings_growth']:
            failures.append(f"Low earnings growth {growth:.1%} < {self.config['min_earnings_growth']:.1%}")
            
        # Debt to equity check
        debt_equity = financials.get('financial_ratios', {}).get('debtToEquityTTM', float('inf'))
        if debt_equity > self.config['max_debt_to_equity']:
            failures.append(f"High debt/equity {debt_equity:.1f} > {self.config['max_debt_to_equity']:.1f}")
            
        # Relative strength check
        rs_rank = technical_data.get('market_context', {}).get('relative_strength_rank', 0)
        if rs_rank < self.config['min_relative_strength_rank']:
            failures.append(f"Low RS rank {rs_rank:.1f} < {self.config['min_relative_strength_rank']}")
            
        # Log all failures for this stock
        if failures:
            self.logger.info(f"Stock {symbol} failed thresholds: {', '.join(failures)}")
        else:
            self.logger.info(f"Stock {symbol} passed all quantitative thresholds")
            
        return len(failures) == 0, failures

async def main():
    """Main function to run the stock analysis."""
    try:
        # Initialize analyzer
        analyzer = SuperstockAnalyzer()
        logger.info("Starting stock analysis...")

        # Stage 1: Get initial market data with timeout and retries
        logger.info("\n📊 Stage 1: Collecting Initial Market Data")
        max_retries = 3
        retry_delay = 5
        initial_quotes = None
        
        for retry in range(max_retries):
            try:
                initial_quotes = await asyncio.wait_for(
                    analyzer.market_data_collector.get_initial_quotes_async(),
                    timeout=120  # 120 second timeout
                )
                
                if initial_quotes:
                    logger.info(f"Found {len(initial_quotes)} stocks in initial scan")
                    break
                    
                logger.warning(f"Empty response on attempt {retry + 1}/{max_retries}")
                if retry < max_retries - 1:
                    await asyncio.sleep(retry_delay * (2 ** retry))  # Exponential backoff
                    
            except asyncio.TimeoutError:
                logger.warning(f"Timeout on attempt {retry + 1}/{max_retries}")
                if retry < max_retries - 1:
                    await asyncio.sleep(retry_delay * (2 ** retry))
            except Exception as e:
                logger.error(f"Error on attempt {retry + 1}/{max_retries}: {str(e)}")
                if retry < max_retries - 1:
                    await asyncio.sleep(retry_delay * (2 ** retry))
                    
        if not initial_quotes:
            logger.error("Failed to get initial quotes after all retries")
            return
        
        # Process in optimized batches with semaphore for concurrency control
        batch_size = analyzer.config['batch_size']
        max_concurrent_batches = 5  # Limit concurrent batch processing
        semaphore = asyncio.Semaphore(max_concurrent_batches)
        
        all_stock_data = []
        failed_symbols = set()
        
        async def process_batch(batch: List[Dict]) -> None:
            """Process a batch of stocks with semaphore control."""
            async with semaphore:
                try:
                    # Collect and analyze batch
                    batch_data = await analyzer.collect_market_data_batch(batch)
                    
                    # Process each stock in batch
                    for stock_data in batch_data:
                        if not stock_data:
                            continue
                            
                        try:
                            symbol = stock_data.get('symbol')
                            if not symbol:
                                continue
                                
                            # Validate stock data structure
                            if not analyzer._validate_stock_data(stock_data):
                                logger.warning(f"Invalid data structure for {symbol}")
                                failed_symbols.add(symbol)
                                continue
                                
                            # Prepare standardized data for scoring
                            score_data = {
                                'symbol': symbol,
                                'financials': stock_data['financials'],
                                'technical_data': stock_data['technical_data'],
                                'quote': stock_data['quote']
                            }
                            
                            # Calculate scores
                            fundamental_score = analyzer.scorer.calculate_fundamental_score(score_data)
                            technical_score = analyzer.scorer.calculate_technical_score(score_data)
                            
                            # Check if stock passes quantitative thresholds
                            passes_thresholds, failures = analyzer._passes_quantitative_thresholds(
                                symbol, fundamental_score, technical_score,
                                stock_data['financials'], stock_data['technical_data'], stock_data['quote']
                            )
                            
                            if not passes_thresholds:
                                logger.debug(f"Stock {symbol} failed thresholds: {', '.join(failures)}")
                                continue
                                
                            # Create StockScore object
                            score = StockScore(
                                symbol=symbol,
                                total_score=(fundamental_score + technical_score) / 2,
                                fundamental_score=fundamental_score,
                                technical_score=technical_score,
                                qualitative_score=0.0,
                                bonus_points=0.0,
                                analysis_date=datetime.now(),
                                key_metrics=stock_data['financials'].get('financial_ratios', {}),
                                catalysts=[],
                                risks=[],
                                passed_threshold=True,
                                gpt_insights={}
                            )
                            
                            # Add score and append to results
                            stock_data['scores'] = score.__dict__
                            all_stock_data.append(stock_data)
                            logger.debug(f"Successfully processed {symbol}")
                                
                        except Exception as e:
                            logger.error(f"Error scoring {stock_data.get('symbol', 'unknown')}: {str(e)}")
                            failed_symbols.add(stock_data.get('symbol', 'unknown'))
                            
                except Exception as e:
                    logger.error(f"Error processing batch: {str(e)}")
                    for quote in batch:
                        failed_symbols.add(quote.get('symbol', 'unknown'))
        
        # Create batches and process them concurrently
        batches = [initial_quotes[i:i + batch_size] for i in range(0, len(initial_quotes), batch_size)]
        
        with tqdm(total=len(initial_quotes), desc="Analyzing Stocks") as pbar:
            # Process batches concurrently with progress tracking
            tasks = []
            for batch in batches:
                task = asyncio.create_task(process_batch(batch))
                tasks.append(task)
                
            # Wait for all batches to complete
            for task in asyncio.as_completed(tasks):
                try:
                    await task
                    pbar.update(batch_size)
                except Exception as e:
                    logger.error(f"Task failed: {str(e)}")
                    
        # Generate report
        if all_stock_data:
            logger.info(f"\n📝 Generating report for {len(all_stock_data)} stocks")
            # Extract and convert scores to dictionaries for the report generator
            score_list = []
            for stock in all_stock_data:
                if 'scores' in stock:
                    score = stock['scores']
                    if isinstance(score, StockScore):
                        score_list.append({
                            'symbol': score.symbol,
                            'total_score': score.total_score,
                            'fundamental_score': score.fundamental_score,
                            'technical_score': score.technical_score,
                            'qualitative_score': score.qualitative_score,
                            'bonus_points': score.bonus_points,
                            'passed_threshold': score.passed_threshold,
                            'key_metrics': score.key_metrics,
                            'catalysts': score.catalysts,
                            'risks': score.risks
                        })
            if score_list:
                analyzer.report_generator.generate_report(
                    scored_stocks=score_list,
                    financial_data={},  # Empty dict as placeholder
                    technical_data={},  # Empty dict as placeholder
                    quotes=[]  # Empty list as placeholder
                )
            logger.info("✅ Analysis completed successfully!")
        else:
            logger.error("❌ No stocks passed analysis criteria")
            
    except Exception as e:
        logger.error(f"❌ Analysis failed: {str(e)}")
    
if __name__ == "__main__":
    # Set up asyncio policy for Windows if needed
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # Run the main async function
    asyncio.run(main())
