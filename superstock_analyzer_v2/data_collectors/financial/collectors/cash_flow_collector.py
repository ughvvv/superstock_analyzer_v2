import logging
from typing import Dict, List, Optional
import aiohttp
from datetime import datetime

logger = logging.getLogger(__name__)

class CashFlowCollector:
    """Collector specifically for cash flow statement data."""
    
    def __init__(self, api_key: str, session: Optional[aiohttp.ClientSession] = None):
        """Initialize the cash flow collector.
        
        Args:
            api_key: API key for Financial Modeling Prep
            session: Optional aiohttp session for making requests
        """
        self.api_key = api_key
        self._session = session
        self.base_url = "https://financialmodelingprep.com/api/v3"
        
    async def get_cash_flows(self, symbol: str, limit: int = 8) -> List[Dict]:
        """Retrieve cash flow statements for a symbol.
        
        Args:
            symbol: Stock symbol
            limit: Number of statements to retrieve (default: 8 quarters)
            
        Returns:
            List of cash flow statements sorted by date (most recent first)
        """
        try:
            url = f"{self.base_url}/cash-flow-statement/{symbol}"
            params = {
                'limit': limit,
                'apikey': self.api_key
            }
            
            async with self._session.get(url, params=params) as response:
                if response.status != 200:
                    logger.error(f"Error fetching cash flows for {symbol}: {response.status}")
                    return []
                    
                statements = await response.json()
                if not isinstance(statements, list):
                    logger.error(f"Invalid cash flow data for {symbol}")
                    return []
                
                # Sort statements by date
                statements.sort(key=lambda x: x['date'], reverse=True)
                return statements
                
        except Exception as e:
            logger.error(f"Error retrieving cash flows for {symbol}: {str(e)}")
            return []
            
    def process_statements(self, statements: List[Dict]) -> Dict:
        """Process cash flow statements into a structured format.
        
        Args:
            statements: List of cash flow statements
            
        Returns:
            Dictionary containing processed cash flow metrics
        """
        try:
            if not statements:
                return {}

            latest = statements[0]
            previous = statements[1] if len(statements) > 1 else None

            processed = {
                'operating_activities': {
                    'net_cash': float(latest.get('netCashProvidedByOperatingActivities', 0)),
                    'net_income': float(latest.get('netIncome', 0)),
                    'depreciation': float(latest.get('depreciationAndAmortization', 0)),
                    'working_capital_changes': float(latest.get('changeInWorkingCapital', 0))
                },
                'investing_activities': {
                    'net_cash': float(latest.get('netCashUsedForInvestingActivites', 0)),
                    'capex': float(latest.get('capitalExpenditure', 0)),
                    'acquisitions': float(latest.get('acquisitionsNet', 0)),
                    'investments': float(latest.get('investmentsInPropertyPlantAndEquipment', 0))
                },
                'financing_activities': {
                    'net_cash': float(latest.get('netCashUsedProvidedByFinancingActivities', 0)),
                    'debt_repayment': float(latest.get('debtRepayment', 0)),
                    'share_repurchase': float(latest.get('commonStockRepurchased', 0)),
                    'dividends_paid': float(latest.get('dividendsPaid', 0))
                },
                'free_cash_flow': {
                    'current': float(latest.get('freeCashFlow', 0)),
                    'change': 0.0  # Will be calculated if previous data available
                }
            }

            # Calculate free cash flow change if previous data available
            if previous:
                prev_fcf = float(previous.get('freeCashFlow', 0))
                current_fcf = processed['free_cash_flow']['current']
                
                if prev_fcf != 0:
                    processed['free_cash_flow']['change'] = (
                        (current_fcf - prev_fcf) / abs(prev_fcf)
                    )

            # Calculate key metrics
            processed['metrics'] = self._calculate_metrics(latest)
            
            # Add quarterly trend data
            processed['quarterly_data'] = [
                {
                    'date': stmt.get('date'),
                    'operating_cash_flow': float(stmt.get('netCashProvidedByOperatingActivities', 0)),
                    'free_cash_flow': float(stmt.get('freeCashFlow', 0)),
                    'capex': float(stmt.get('capitalExpenditure', 0))
                }
                for stmt in statements[:4]  # Last 4 quarters
            ]
            
            return processed
            
        except Exception as e:
            logger.error(f"Error processing cash flow statements: {str(e)}")
            return {}
            
    def _calculate_metrics(self, statement: Dict) -> Dict:
        """Calculate key cash flow metrics.
        
        Args:
            statement: Single cash flow statement
            
        Returns:
            Dictionary containing calculated metrics
        """
        try:
            operating_cash_flow = float(statement.get('netCashProvidedByOperatingActivities', 0))
            net_income = float(statement.get('netIncome', 0))
            total_assets = float(statement.get('totalAssets', 0))
            capex = float(statement.get('capitalExpenditure', 0))
            revenue = float(statement.get('totalRevenue', 0))
            
            metrics = {
                'operating_cash_flow_ratio': (
                    operating_cash_flow / revenue if revenue != 0 else 0
                ),
                'cash_flow_coverage': (
                    operating_cash_flow / abs(capex) if capex != 0 else 0
                ),
                'cash_flow_to_income': (
                    operating_cash_flow / net_income if net_income != 0 else 0
                ),
                'cash_return_on_assets': (
                    operating_cash_flow / total_assets if total_assets != 0 else 0
                )
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating cash flow metrics: {str(e)}")
            return {}
            
    def analyze_trends(self, statements: List[Dict]) -> Dict:
        """Analyze cash flow trends over time.
        
        Args:
            statements: List of cash flow statements
            
        Returns:
            Dictionary containing trend analysis
        """
        try:
            if len(statements) < 4:  # Need at least 4 quarters for trend analysis
                return {}
                
            trends = {
                'operating_cash_flow': [],
                'free_cash_flow': [],
                'capex': [],
                'financing_activities': []
            }
            
            # Calculate quarter-over-quarter changes
            for i in range(len(statements) - 1):
                current = statements[i]
                previous = statements[i + 1]
                
                # Calculate growth rates
                for metric, current_key, prev_key in [
                    ('operating_cash_flow', 'netCashProvidedByOperatingActivities', 'netCashProvidedByOperatingActivities'),
                    ('free_cash_flow', 'freeCashFlow', 'freeCashFlow'),
                    ('capex', 'capitalExpenditure', 'capitalExpenditure'),
                    ('financing_activities', 'netCashUsedProvidedByFinancingActivities', 'netCashUsedProvidedByFinancingActivities')
                ]:
                    current_value = float(current.get(current_key, 0))
                    prev_value = float(previous.get(prev_key, 0))
                    
                    if prev_value != 0:
                        growth = (current_value - prev_value) / abs(prev_value)
                        trends[metric].append(growth)
            
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
            logger.error(f"Error analyzing cash flow trends: {str(e)}")
            return {}
