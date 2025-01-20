import logging
from typing import Dict, List, Optional
import aiohttp
from datetime import datetime

logger = logging.getLogger(__name__)

class IncomeCollector:
    """Collector specifically for income statement data."""
    
    def __init__(self, api_key: str, session: Optional[aiohttp.ClientSession] = None):
        """Initialize the income collector.
        
        Args:
            api_key: API key for Financial Modeling Prep
            session: Optional aiohttp session for making requests
        """
        self.api_key = api_key
        self._session = session
        self.base_url = "https://financialmodelingprep.com/api/v3"
        
    async def get_income_statements(self, symbol: str, limit: int = 8) -> List[Dict]:
        """Retrieve income statements for a symbol.
        
        Args:
            symbol: Stock symbol
            limit: Number of statements to retrieve (default: 8 quarters)
            
        Returns:
            List of income statements sorted by date (most recent first)
        """
        try:
            url = f"{self.base_url}/income-statement/{symbol}"
            params = {
                'limit': limit,
                'apikey': self.api_key
            }
            
            async with self._session.get(url, params=params) as response:
                if response.status != 200:
                    logger.error(f"Error fetching income statements for {symbol}: {response.status}")
                    return []
                    
                statements = await response.json()
                if not isinstance(statements, list):
                    logger.error(f"Invalid income statement data for {symbol}")
                    return []
                
                # Sort statements by date
                statements.sort(key=lambda x: x['date'], reverse=True)
                return statements
                
        except Exception as e:
            logger.error(f"Error retrieving income statements for {symbol}: {str(e)}")
            return []
            
    def process_statements(self, statements: List[Dict]) -> Dict:
        """Process income statements into a structured format.
        
        Args:
            statements: List of income statements
            
        Returns:
            Dictionary containing processed income metrics
        """
        try:
            if not statements:
                return {}

            latest = statements[0]
            year_ago = statements[4] if len(statements) > 4 else None

            return {
                'revenue': float(latest.get('revenue', 0)),
                'netIncome': float(latest.get('netIncome', 0)),
                'operatingIncome': float(latest.get('operatingIncome', 0)),
                'grossProfit': float(latest.get('grossProfit', 0)),
                'revenue_growth': (
                    (float(latest.get('revenue', 0)) - float(year_ago.get('revenue', 0))) / 
                    float(year_ago.get('revenue', 1)) if year_ago else 0
                ),
                'earnings_growth': (
                    (float(latest.get('netIncome', 0)) - float(year_ago.get('netIncome', 0))) / 
                    float(year_ago.get('netIncome', 1)) if year_ago else 0
                ),
                'operating_metrics': {
                    'grossMargin': float(latest.get('grossProfitRatio', 0)),
                    'operatingMargin': float(latest.get('operatingIncomeRatio', 0)),
                    'netMargin': float(latest.get('netIncomeRatio', 0))
                },
                'quarterly_data': [
                    {
                        'date': stmt.get('date'),
                        'revenue': float(stmt.get('revenue', 0)),
                        'netIncome': float(stmt.get('netIncome', 0)),
                        'eps': float(stmt.get('eps', 0))
                    }
                    for stmt in statements[:4]  # Last 4 quarters
                ]
            }
            
        except Exception as e:
            logger.error(f"Error processing income statements: {str(e)}")
            return {}
            
    def calculate_growth_metrics(self, statements: List[Dict]) -> Dict:
        """Calculate detailed growth metrics from income statements.
        
        Args:
            statements: List of income statements
            
        Returns:
            Dictionary containing growth metrics
        """
        try:
            if len(statements) < 8:  # Need at least 8 quarters for proper analysis
                return {}
                
            metrics = {
                'quarterly': {},
                'annual': {}
            }
            
            # Calculate quarterly growth rates
            for i in range(len(statements) - 1):
                current = statements[i]
                previous = statements[i + 1]
                
                quarter = f"Q{i+1}"
                metrics['quarterly'][quarter] = {
                    'revenue_growth': (
                        (float(current.get('revenue', 0)) - float(previous.get('revenue', 0))) /
                        float(previous.get('revenue', 1))
                    ),
                    'earnings_growth': (
                        (float(current.get('netIncome', 0)) - float(previous.get('netIncome', 0))) /
                        float(previous.get('netIncome', 1))
                    ),
                    'operating_income_growth': (
                        (float(current.get('operatingIncome', 0)) - float(previous.get('operatingIncome', 0))) /
                        float(previous.get('operatingIncome', 1))
                    )
                }
            
            # Calculate annual metrics (using last 4 quarters vs previous 4 quarters)
            recent_4q = statements[:4]
            previous_4q = statements[4:8]
            
            if recent_4q and previous_4q:
                metrics['annual'] = {
                    'revenue_growth': (
                        (sum(float(q.get('revenue', 0)) for q in recent_4q) -
                         sum(float(q.get('revenue', 0)) for q in previous_4q)) /
                        sum(float(q.get('revenue', 1)) for q in previous_4q)
                    ),
                    'earnings_growth': (
                        (sum(float(q.get('netIncome', 0)) for q in recent_4q) -
                         sum(float(q.get('netIncome', 0)) for q in previous_4q)) /
                        sum(float(q.get('netIncome', 1)) for q in previous_4q)
                    ),
                    'operating_income_growth': (
                        (sum(float(q.get('operatingIncome', 0)) for q in recent_4q) -
                         sum(float(q.get('operatingIncome', 0)) for q in previous_4q)) /
                        sum(float(q.get('operatingIncome', 1)) for q in previous_4q)
                    )
                }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating growth metrics: {str(e)}")
            return {'quarterly': {}, 'annual': {}}
