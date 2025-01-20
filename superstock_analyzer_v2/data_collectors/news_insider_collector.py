import logging
from typing import List, Dict, Any
from .base_collector import BaseCollector
from datetime import datetime, timedelta
import requests

logger = logging.getLogger(__name__)

class NewsInsiderCollector(BaseCollector):
    def __init__(self, api_key: str):
        """Initialize the NewsInsiderCollector."""
        super().__init__(api_key)

    def get_insider_data(self, symbol: str) -> Dict:
        """Get quantitative insider trading data for a symbol."""
        try:
            # Try to get from cache first
            cache_key = self._make_cache_key("insider_trading", {"symbol": symbol})
            cached_data = self.cache_manager.get_from_cache(cache_key) if hasattr(self, 'cache_manager') else None
            if cached_data:
                return cached_data
            
            # Get insider transactions
            insider_trades = self.make_fmp_request(
                "v4/insider-trading",
                params={"symbol": symbol, "limit": 100}  # Increased limit
            )
            
            # Get insider statistics
            insider_stats = self.make_fmp_request(
                "v4/insider-roaster-statistic",
                params={"symbol": symbol}
            )
            
            # Ensure we have lists
            insider_trades = insider_trades if isinstance(insider_trades, list) else []
            insider_stats = insider_stats if isinstance(insider_stats, list) else []
            
            # Filter out old transactions (older than 6 months)
            cutoff_date = datetime.now() - timedelta(days=180)
            
            def is_recent(item):
                try:
                    date_str = item.get('transactionDate', '')
                    if not date_str:
                        return False
                    tx_date = datetime.strptime(date_str, '%Y-%m-%d')
                    return tx_date >= cutoff_date
                except (ValueError, TypeError):
                    return False
            
            insider_trades = [tx for tx in insider_trades if is_recent(tx)]
            
            # Analyze insider trading patterns
            trading_analysis = self._analyze_insider_patterns(insider_trades)
            
            # Combine quantitative insider data
            insider_data = {
                'transactions': insider_trades,
                'statistics': insider_stats,
                'analysis': trading_analysis
            }
            
            # Cache the results
            if hasattr(self, 'cache_manager') and any(insider_data.values()):
                self.cache_manager.save_to_cache(cache_key, insider_data)
            
            return insider_data
            
        except Exception as e:
            logger.error(f"Error getting insider data for {symbol}: {str(e)}")
            return {
                'transactions': [],
                'statistics': [],
                'analysis': {}
            }

    def get_news(self, symbol: str) -> Dict:
        """Get news data for a symbol."""
        try:
            # Try to get from cache first
            cache_key = self._make_cache_key("stock_news", {"symbol": symbol})
            cached_data = self.cache_manager.get_from_cache(cache_key) if hasattr(self, 'cache_manager') else None
            if cached_data:
                return cached_data
            
            # Get news articles
            news = self.make_fmp_request(
                "v3/stock_news",
                params={"symbol": symbol, "limit": 100}  # Increased limit
            )
            
            # Get press releases
            press_releases = self.make_fmp_request(
                "v3/press-releases",
                params={"symbol": symbol, "limit": 50}
            )
            
            # Ensure we have lists
            news = news if isinstance(news, list) else []
            press_releases = press_releases if isinstance(press_releases, list) else []
            
            # Filter out old articles (older than 6 months)
            cutoff_date = datetime.now() - timedelta(days=180)
            
            def is_recent(item):
                try:
                    date_str = item.get('publishedDate', '')
                    if not date_str:
                        return False
                    pub_date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                    return pub_date >= cutoff_date
                except (ValueError, TypeError):
                    return False
            
            news = [article for article in news if is_recent(article)]
            press_releases = [pr for pr in press_releases if is_recent(pr)]
            
            # Combine news data
            news_data = {
                'articles': news,
                'press_releases': press_releases
            }
            
            # Cache the results
            if hasattr(self, 'cache_manager') and any(news_data.values()):
                self.cache_manager.save_to_cache(cache_key, news_data)
            
            return news_data
            
        except Exception as e:
            logger.error(f"Error getting news data for {symbol}: {str(e)}")
            return {
                'articles': [],
                'press_releases': []
            }

    def _make_cache_key(self, base_key: str, params: Dict) -> str:
        """Create a cache key from base key and parameters."""
        param_str = '_'.join(f"{k}:{v}" for k, v in sorted(params.items()) if isinstance(v, (str, int, float)))
        return f"{base_key}_{param_str}"

    def make_fmp_request(self, endpoint: str, params: Dict = None) -> Any:
        """Make a request to the FMP API with caching."""
        try:
            params = params or {}
            params['apikey'] = self.api_key
            
            # Create cache key
            cache_key = self._make_cache_key(endpoint, params)
            
            # Try to get from cache
            if hasattr(self, 'cache_manager'):
                cached_data = self.cache_manager.get_from_cache(cache_key)
                if cached_data is not None:
                    return cached_data
            
            # Make the request
            url = f"{self.base_url}/{endpoint}"
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Cache the response if it's not empty
            if hasattr(self, 'cache_manager') and data:
                self.cache_manager.save_to_cache(cache_key, data)
            
            return data
            
        except Exception as e:
            logger.error(f"Error in FMP request to {endpoint}: {str(e)}")
            return []
            
    def _analyze_insider_patterns(self, transactions: List[Dict]) -> Dict:
        """Analyze quantitative insider trading patterns and trends."""
        try:
            if not transactions:
                return {
                    'recent_activity': 'none',
                    'buy_sell_ratio': 0,
                    'significant_trades': [],
                    'trend': 'neutral',
                    'summary': {
                        'total_transactions': 0,
                        'buy_count': 0,
                        'sell_count': 0,
                        'total_buy_value': 0,
                        'total_sell_value': 0,
                        'average_buy_value': 0,
                        'average_sell_value': 0
                    }
                }

            # Initialize counters
            buys = 0
            sells = 0
            total_buy_value = 0
            total_sell_value = 0
            significant_trades = []

            # Analyze last 3 months of transactions
            cutoff_date = datetime.now() - timedelta(days=90)
            recent_transactions = [
                t for t in transactions 
                if datetime.strptime(t.get('transactionDate', '1900-01-01'), '%Y-%m-%d') > cutoff_date
            ]

            for trade in recent_transactions:
                try:
                    price = float(trade.get('price', 0) or 0)
                    shares = float(trade.get('securitiesTransacted', 0) or 0)
                    value = price * shares
                    
                    if trade.get('transactionType') == 'P-Purchase':
                        buys += 1
                        total_buy_value += value
                        if value >= 100000:  # Significant purchase threshold
                            significant_trades.append(trade)
                    elif trade.get('transactionType') == 'S-Sale':
                        sells += 1
                        total_sell_value += value
                        if value >= 1000000:  # Significant sale threshold
                            significant_trades.append(trade)
                except (ValueError, TypeError):
                    continue

            # Determine activity level
            if buys + sells == 0:
                recent_activity = 'none'
            elif total_buy_value > total_sell_value * 1.5:
                recent_activity = 'heavy_buying'
            elif total_sell_value > total_buy_value * 1.5:
                recent_activity = 'heavy_selling'
            elif buys > sells:
                recent_activity = 'moderate_buying'
            elif sells > buys:
                recent_activity = 'moderate_selling'
            else:
                recent_activity = 'neutral'

            # Determine trend
            if len(recent_transactions) >= 10:
                first_half = recent_transactions[:len(recent_transactions)//2]
                second_half = recent_transactions[len(recent_transactions)//2:]
                
                first_half_buys = sum(1 for t in first_half if t.get('transactionType') == 'P-Purchase')
                second_half_buys = sum(1 for t in second_half if t.get('transactionType') == 'P-Purchase')
                
                if second_half_buys > first_half_buys * 1.5:
                    trend = 'increasing_buys'
                elif first_half_buys > second_half_buys * 1.5:
                    trend = 'decreasing_buys'
                else:
                    trend = 'stable'
            else:
                trend = 'insufficient_data'

            return {
                'recent_activity': recent_activity,
                'buy_sell_ratio': (total_buy_value / total_sell_value) if total_sell_value > 0 else float('inf'),
                'significant_trades': sorted(significant_trades, 
                                          key=lambda x: float(x.get('price', 0) or 0) * float(x.get('securitiesTransacted', 0) or 0),
                                          reverse=True)[:5],
                'trend': trend,
                'summary': {
                    'total_transactions': buys + sells,
                    'buy_count': buys,
                    'sell_count': sells,
                    'total_buy_value': total_buy_value,
                    'total_sell_value': total_sell_value,
                    'average_buy_value': total_buy_value / buys if buys > 0 else 0,
                    'average_sell_value': total_sell_value / sells if sells > 0 else 0
                }
            }

        except Exception as e:
            logger.error(f"Error analyzing insider patterns: {str(e)}")
            return {
                'recent_activity': 'error',
                'buy_sell_ratio': 0,
                'significant_trades': [],
                'trend': 'error',
                'summary': {
                    'total_transactions': 0,
                    'buy_count': 0,
                    'sell_count': 0,
                    'total_buy_value': 0,
                    'total_sell_value': 0,
                    'average_buy_value': 0,
                    'average_sell_value': 0
                }
            }
