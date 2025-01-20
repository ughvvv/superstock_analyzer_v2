import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class FinancialDataValidator:
    """Validates financial data across all collectors."""
    
    @staticmethod
    def validate_income_statement(data: Dict) -> bool:
        """Validate income statement data structure and values.
        
        Args:
            data: Income statement data to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            # Check required fields
            required_fields = {
                'revenue', 'netIncome', 'operatingIncome', 'grossProfit',
                'revenue_growth', 'earnings_growth'
            }
            
            if not all(field in data for field in required_fields):
                logger.error("Missing required fields in income statement")
                return False
                
            # Validate value types and ranges
            for field in required_fields:
                value = data.get(field)
                if not isinstance(value, (int, float)):
                    logger.error(f"Invalid type for {field}: {type(value)}")
                    return False
                    
            # Validate growth rates are within reasonable bounds
            for field in ['revenue_growth', 'earnings_growth']:
                growth = data.get(field, 0)
                if abs(growth) > 10:  # More than 1000% growth is suspicious
                    logger.warning(f"Suspicious {field}: {growth}")
                    return False
                    
            return True
            
        except Exception as e:
            logger.error(f"Error validating income statement: {str(e)}")
            return False
            
    @staticmethod
    def validate_balance_sheet(data: Dict) -> bool:
        """Validate balance sheet data structure and values.
        
        Args:
            data: Balance sheet data to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            # Check required sections
            required_sections = {'assets', 'liabilities', 'equity', 'working_capital'}
            if not all(section in data for section in required_sections):
                logger.error("Missing required sections in balance sheet")
                return False
                
            # Validate assets = liabilities + equity
            total_assets = data['assets'].get('total', 0)
            total_liabilities = data['liabilities'].get('total', 0)
            total_equity = data['equity'].get('total', 0)
            
            # Allow for small rounding differences
            if abs(total_assets - (total_liabilities + total_equity)) > 1:
                logger.error("Balance sheet equation doesn't balance")
                return False
                
            # Validate working capital calculation
            current_assets = data['assets'].get('current', 0)
            current_liabilities = data['liabilities'].get('current', 0)
            working_capital = data['working_capital'].get('current', 0)
            
            if abs(working_capital - (current_assets - current_liabilities)) > 1:
                logger.error("Working capital calculation mismatch")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error validating balance sheet: {str(e)}")
            return False
            
    @staticmethod
    def validate_cash_flow(data: Dict) -> bool:
        """Validate cash flow statement data structure and values.
        
        Args:
            data: Cash flow data to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            # Check required sections
            required_sections = {
                'operating_activities', 'investing_activities',
                'financing_activities', 'free_cash_flow'
            }
            if not all(section in data for section in required_sections):
                logger.error("Missing required sections in cash flow statement")
                return False
                
            # Validate free cash flow calculation
            operating_cash = data['operating_activities'].get('net_cash', 0)
            capex = data['investing_activities'].get('capex', 0)
            reported_fcf = data['free_cash_flow'].get('current', 0)
            
            # Allow for small differences due to different calculation methods
            if abs((operating_cash + capex) - reported_fcf) > abs(reported_fcf * 0.1):
                logger.warning("Free cash flow calculation shows significant deviation")
                
            return True
            
        except Exception as e:
            logger.error(f"Error validating cash flow statement: {str(e)}")
            return False
            
    @staticmethod
    def validate_metrics(data: Dict) -> bool:
        """Validate financial metrics and ratios.
        
        Args:
            data: Financial metrics data to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            # Check common financial ratios are within reasonable ranges
            ratio_ranges = {
                'current_ratio': (0, 10),
                'quick_ratio': (0, 10),
                'debt_to_equity': (0, 10),
                'operating_cash_flow_ratio': (0, 5),
                'cash_flow_coverage': (0, 10)
            }
            
            for ratio, (min_val, max_val) in ratio_ranges.items():
                if ratio in data:
                    value = data[ratio]
                    if not isinstance(value, (int, float)):
                        logger.error(f"Invalid type for {ratio}: {type(value)}")
                        return False
                    if not min_val <= value <= max_val:
                        logger.warning(f"Suspicious {ratio} value: {value}")
                        
            return True
            
        except Exception as e:
            logger.error(f"Error validating metrics: {str(e)}")
            return False
            
    @staticmethod
    def validate_trends(data: Dict) -> bool:
        """Validate trend analysis data.
        
        Args:
            data: Trend analysis data to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            # Check required sections
            if 'quarterly_changes' not in data or 'trend_strength' not in data:
                logger.error("Missing required sections in trend analysis")
                return False
                
            # Validate trend strength values
            for metric, strength in data['trend_strength'].items():
                if 'direction' not in strength or 'consistency' not in strength:
                    logger.error(f"Missing required fields in trend strength for {metric}")
                    return False
                    
                # Validate consistency is between 0 and 1
                consistency = strength['consistency']
                if not isinstance(consistency, (int, float)) or not 0 <= consistency <= 1:
                    logger.error(f"Invalid consistency value for {metric}: {consistency}")
                    return False
                    
                # Validate direction is valid
                if strength['direction'] not in ['positive', 'negative']:
                    logger.error(f"Invalid direction for {metric}: {strength['direction']}")
                    return False
                    
            return True
            
        except Exception as e:
            logger.error(f"Error validating trends: {str(e)}")
            return False
            
    @staticmethod
    def validate_dates(statements: List[Dict]) -> bool:
        """Validate statement dates are sequential and properly formatted.
        
        Args:
            statements: List of financial statements to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            if not statements:
                return True
                
            # Check date format and sequence
            dates = []
            for stmt in statements:
                try:
                    date_str = stmt.get('date')
                    if not date_str:
                        logger.error("Missing date in statement")
                        return False
                        
                    date = datetime.strptime(date_str, '%Y-%m-%d')
                    dates.append(date)
                except ValueError:
                    logger.error(f"Invalid date format: {date_str}")
                    return False
                    
            # Verify dates are in descending order (most recent first)
            if dates != sorted(dates, reverse=True):
                logger.error("Statements are not in chronological order")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error validating dates: {str(e)}")
            return False
