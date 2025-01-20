import logging
from typing import Dict, List, Optional
import aiohttp
from datetime import datetime

logger = logging.getLogger(__name__)

class BalanceSheetCollector:
    """Collector specifically for balance sheet data."""
    
    def __init__(self, api_key: str, session: Optional[aiohttp.ClientSession] = None):
        """Initialize the balance sheet collector.
        
        Args:
            api_key: API key for Financial Modeling Prep
            session: Optional aiohttp session for making requests
        """
        self.api_key = api_key
        self._session = session
        self.base_url = "https://financialmodelingprep.com/api/v3"
        
    async def get_balance_sheets(self, symbol: str, limit: int = 8) -> List[Dict]:
        """Retrieve balance sheets for a symbol.
        
        Args:
            symbol: Stock symbol
            limit: Number of statements to retrieve (default: 8 quarters)
            
        Returns:
            List of balance sheets sorted by date (most recent first)
        """
        try:
            url = f"{self.base_url}/balance-sheet-statement/{symbol}"
            params = {
                'limit': limit,
                'apikey': self.api_key
            }
            
            async with self._session.get(url, params=params) as response:
                if response.status != 200:
                    logger.error(f"Error fetching balance sheets for {symbol}: {response.status}")
                    return []
                    
                statements = await response.json()
                if not isinstance(statements, list):
                    logger.error(f"Invalid balance sheet data for {symbol}")
                    return []
                
                # Sort statements by date
                statements.sort(key=lambda x: x['date'], reverse=True)
                return statements
                
        except Exception as e:
            logger.error(f"Error retrieving balance sheets for {symbol}: {str(e)}")
            return []
            
    def process_statements(self, statements: List[Dict]) -> Dict:
        """Process balance sheets into a structured format.
        
        Args:
            statements: List of balance sheets
            
        Returns:
            Dictionary containing processed balance sheet metrics
        """
        try:
            if not statements:
                return {}

            latest = statements[0]
            previous = statements[1] if len(statements) > 1 else None

            processed = {
                'assets': {
                    'total': float(latest.get('totalAssets', 0)),
                    'current': float(latest.get('totalCurrentAssets', 0)),
                    'cash': float(latest.get('cashAndCashEquivalents', 0)),
                    'inventory': float(latest.get('inventory', 0)),
                    'receivables': float(latest.get('netReceivables', 0))
                },
                'liabilities': {
                    'total': float(latest.get('totalLiabilities', 0)),
                    'current': float(latest.get('totalCurrentLiabilities', 0)),
                    'long_term_debt': float(latest.get('longTermDebt', 0)),
                    'accounts_payable': float(latest.get('accountPayables', 0))
                },
                'equity': {
                    'total': float(latest.get('totalStockholdersEquity', 0)),
                    'retained_earnings': float(latest.get('retainedEarnings', 0))
                },
                'working_capital': {
                    'current': float(latest.get('totalCurrentAssets', 0)) - float(latest.get('totalCurrentLiabilities', 0)),
                    'change': 0.0  # Will be calculated if previous data available
                }
            }

            # Calculate working capital change if previous data available
            if previous:
                prev_working_capital = (
                    float(previous.get('totalCurrentAssets', 0)) - 
                    float(previous.get('totalCurrentLiabilities', 0))
                )
                current_working_capital = processed['working_capital']['current']
                
                if prev_working_capital != 0:
                    processed['working_capital']['change'] = (
                        (current_working_capital - prev_working_capital) / abs(prev_working_capital)
                    )

            # Calculate key ratios
            processed['ratios'] = self._calculate_ratios(latest)
            
            # Add quarterly trend data
            processed['quarterly_data'] = [
                {
                    'date': stmt.get('date'),
                    'total_assets': float(stmt.get('totalAssets', 0)),
                    'total_liabilities': float(stmt.get('totalLiabilities', 0)),
                    'total_equity': float(stmt.get('totalStockholdersEquity', 0)),
                    'working_capital': float(stmt.get('totalCurrentAssets', 0)) - float(stmt.get('totalCurrentLiabilities', 0))
                }
                for stmt in statements[:4]  # Last 4 quarters
            ]
            
            return processed
            
        except Exception as e:
            logger.error(f"Error processing balance sheets: {str(e)}")
            return {}
            
    def _calculate_ratios(self, statement: Dict) -> Dict:
        """Calculate key balance sheet ratios.
        
        Args:
            statement: Single balance sheet statement
            
        Returns:
            Dictionary containing calculated ratios
        """
        try:
            total_assets = float(statement.get('totalAssets', 0))
            current_assets = float(statement.get('totalCurrentAssets', 0))
            current_liabilities = float(statement.get('totalCurrentLiabilities', 0))
            total_liabilities = float(statement.get('totalLiabilities', 0))
            inventory = float(statement.get('inventory', 0))
            equity = float(statement.get('totalStockholdersEquity', 0))
            
            ratios = {
                'current_ratio': (
                    current_assets / current_liabilities if current_liabilities != 0 else 0
                ),
                'quick_ratio': (
                    (current_assets - inventory) / current_liabilities if current_liabilities != 0 else 0
                ),
                'debt_to_equity': (
                    total_liabilities / equity if equity != 0 else 0
                ),
                'asset_turnover': (
                    float(statement.get('totalRevenue', 0)) / total_assets if total_assets != 0 else 0
                ),
                'equity_multiplier': (
                    total_assets / equity if equity != 0 else 0
                )
            }
            
            return ratios
            
        except Exception as e:
            logger.error(f"Error calculating balance sheet ratios: {str(e)}")
            return {}
            
    def analyze_trends(self, statements: List[Dict]) -> Dict:
        """Analyze balance sheet trends over time.
        
        Args:
            statements: List of balance sheet statements
            
        Returns:
            Dictionary containing trend analysis
        """
        try:
            if len(statements) < 4:  # Need at least 4 quarters for trend analysis
                return {}
                
            trends = {
                'asset_growth': [],
                'liability_growth': [],
                'equity_growth': [],
                'working_capital_trend': []
            }
            
            # Calculate quarter-over-quarter changes
            for i in range(len(statements) - 1):
                current = statements[i]
                previous = statements[i + 1]
                
                # Calculate growth rates
                for metric, current_value, prev_value in [
                    ('asset_growth', current.get('totalAssets', 0), previous.get('totalAssets', 0)),
                    ('liability_growth', current.get('totalLiabilities', 0), previous.get('totalLiabilities', 0)),
                    ('equity_growth', current.get('totalStockholdersEquity', 0), previous.get('totalStockholdersEquity', 0))
                ]:
                    if float(prev_value) != 0:
                        growth = (float(current_value) - float(prev_value)) / float(prev_value)
                        trends[metric].append(growth)
                        
                # Calculate working capital trend
                current_wc = float(current.get('totalCurrentAssets', 0)) - float(current.get('totalCurrentLiabilities', 0))
                prev_wc = float(previous.get('totalCurrentAssets', 0)) - float(previous.get('totalCurrentLiabilities', 0))
                
                if prev_wc != 0:
                    wc_change = (current_wc - prev_wc) / abs(prev_wc)
                    trends['working_capital_trend'].append(wc_change)
            
            # Calculate trend strengths
            trend_strength = {}
            for metric, values in trends.items():
                if values:
                    # Positive trend if more than 50% of changes are positive
                    positive_changes = sum(1 for v in values if v > 0)
                    trend_strength[metric] = {
                        'direction': 'positive' if positive_changes > len(values) / 2 else 'negative',
                        'consistency': positive_changes / len(values) if positive_changes > len(values) / 2 else (len(values) - positive_changes) / len(values)
                    }
            
            return {
                'quarterly_changes': trends,
                'trend_strength': trend_strength
            }
            
        except Exception as e:
            logger.error(f"Error analyzing balance sheet trends: {str(e)}")
            return {}
