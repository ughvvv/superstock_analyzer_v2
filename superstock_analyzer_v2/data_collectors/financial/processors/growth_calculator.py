import logging
from typing import Dict, List, Optional, Union
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)

class GrowthCalculator:
    """Calculates growth metrics across financial data."""
    
    @staticmethod
    def calculate_sequential_growth(values: List[float]) -> List[float]:
        """Calculate sequential (period-over-period) growth rates.
        
        Args:
            values: List of values in chronological order (oldest to newest)
            
        Returns:
            List of growth rates
        """
        try:
            if len(values) < 2:
                return []
                
            growth_rates = []
            for i in range(1, len(values)):
                if values[i-1] != 0:
                    growth = (values[i] - values[i-1]) / abs(values[i-1])
                    growth_rates.append(growth)
                else:
                    growth_rates.append(0.0)
                    
            return growth_rates
            
        except Exception as e:
            logger.error(f"Error calculating sequential growth: {str(e)}")
            return []
            
    @staticmethod
    def calculate_year_over_year_growth(
        values: List[float],
        periods_per_year: int = 4
    ) -> List[float]:
        """Calculate year-over-year growth rates.
        
        Args:
            values: List of values in chronological order (oldest to newest)
            periods_per_year: Number of periods in a year (e.g., 4 for quarterly)
            
        Returns:
            List of year-over-year growth rates
        """
        try:
            if len(values) < periods_per_year + 1:
                return []
                
            growth_rates = []
            for i in range(periods_per_year, len(values)):
                if values[i-periods_per_year] != 0:
                    growth = (values[i] - values[i-periods_per_year]) / abs(values[i-periods_per_year])
                    growth_rates.append(growth)
                else:
                    growth_rates.append(0.0)
                    
            return growth_rates
            
        except Exception as e:
            logger.error(f"Error calculating year-over-year growth: {str(e)}")
            return []
            
    @staticmethod
    def calculate_cagr(
        start_value: float,
        end_value: float,
        num_periods: float
    ) -> Optional[float]:
        """Calculate Compound Annual Growth Rate.
        
        Args:
            start_value: Initial value
            end_value: Final value
            num_periods: Number of periods (in years)
            
        Returns:
            CAGR as a float, or None if calculation fails
        """
        try:
            if start_value <= 0 or num_periods <= 0:
                return None
                
            return (end_value / start_value) ** (1 / num_periods) - 1
            
        except Exception as e:
            logger.error(f"Error calculating CAGR: {str(e)}")
            return None
            
    @staticmethod
    def calculate_growth_metrics(data: List[Dict], metric_key: str) -> Dict:
        """Calculate comprehensive growth metrics for a specific financial metric.
        
        Args:
            data: List of financial statements
            metric_key: Key for the metric to analyze
            
        Returns:
            Dictionary containing various growth metrics
        """
        try:
            if not data:
                return {}
                
            # Extract values and ensure they're floats
            values = [float(item.get(metric_key, 0)) for item in data]
            values.reverse()  # Convert to chronological order
            
            # Calculate various growth metrics
            sequential_growth = GrowthCalculator.calculate_sequential_growth(values)
            yoy_growth = GrowthCalculator.calculate_year_over_year_growth(values)
            
            # Calculate CAGR if we have enough data
            cagr = None
            if len(values) >= 8:  # At least 2 years of quarterly data
                start_value = values[0]
                end_value = values[-1]
                num_years = len(values) / 4  # Assuming quarterly data
                cagr = GrowthCalculator.calculate_cagr(start_value, end_value, num_years)
            
            # Calculate growth stability metrics
            growth_metrics = {
                'sequential_growth': {
                    'values': sequential_growth,
                    'mean': np.mean(sequential_growth) if sequential_growth else 0,
                    'std': np.std(sequential_growth) if sequential_growth else 0,
                    'median': np.median(sequential_growth) if sequential_growth else 0
                },
                'year_over_year_growth': {
                    'values': yoy_growth,
                    'mean': np.mean(yoy_growth) if yoy_growth else 0,
                    'std': np.std(yoy_growth) if yoy_growth else 0,
                    'median': np.median(yoy_growth) if yoy_growth else 0
                },
                'cagr': cagr,
                'stability_metrics': GrowthCalculator._calculate_stability_metrics(sequential_growth)
            }
            
            return growth_metrics
            
        except Exception as e:
            logger.error(f"Error calculating growth metrics: {str(e)}")
            return {}
            
    @staticmethod
    def _calculate_stability_metrics(growth_rates: List[float]) -> Dict:
        """Calculate metrics that indicate growth stability.
        
        Args:
            growth_rates: List of growth rates
            
        Returns:
            Dictionary containing stability metrics
        """
        try:
            if not growth_rates:
                return {}
                
            # Convert to numpy array for calculations
            rates = np.array(growth_rates)
            
            metrics = {
                'consistency': 0.0,  # Higher is better
                'volatility': 0.0,   # Lower is better
                'trend': 0.0         # Positive is better
            }
            
            # Calculate consistency (percentage of positive growth rates)
            positive_growth = np.sum(rates > 0)
            metrics['consistency'] = positive_growth / len(rates)
            
            # Calculate volatility (coefficient of variation)
            mean = np.mean(rates)
            std = np.std(rates)
            metrics['volatility'] = std / abs(mean) if mean != 0 else float('inf')
            
            # Calculate trend (linear regression slope)
            x = np.arange(len(rates))
            coefficients = np.polyfit(x, rates, 1)
            metrics['trend'] = coefficients[0]
            
            # Add trend strength (R-squared)
            y_pred = np.polyval(coefficients, x)
            ss_tot = np.sum((rates - np.mean(rates)) ** 2)
            ss_res = np.sum((rates - y_pred) ** 2)
            metrics['trend_strength'] = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating stability metrics: {str(e)}")
            return {}
            
    @staticmethod
    def analyze_growth_quality(metrics: Dict) -> Dict:
        """Analyze the quality of growth based on various metrics.
        
        Args:
            metrics: Dictionary of growth metrics
            
        Returns:
            Dictionary containing growth quality analysis
        """
        try:
            quality_scores = {
                'consistency': 0.0,
                'sustainability': 0.0,
                'momentum': 0.0,
                'overall': 0.0
            }
            
            # Analyze consistency
            stability = metrics.get('stability_metrics', {})
            consistency_score = stability.get('consistency', 0) * 0.7
            volatility_penalty = min(stability.get('volatility', float('inf')), 1) * 0.3
            quality_scores['consistency'] = max(0, consistency_score - volatility_penalty)
            
            # Analyze sustainability
            sequential = metrics.get('sequential_growth', {})
            yoy = metrics.get('year_over_year_growth', {})
            
            recent_growth = np.mean(sequential.get('values', [])[-4:]) if sequential.get('values') else 0
            long_term_growth = metrics.get('cagr', 0) or 0
            
            # Higher score if recent growth is supported by long-term trends
            if abs(recent_growth - long_term_growth) < 0.1:
                quality_scores['sustainability'] = 0.8
            elif abs(recent_growth - long_term_growth) < 0.2:
                quality_scores['sustainability'] = 0.6
            else:
                quality_scores['sustainability'] = 0.4
                
            # Analyze momentum
            trend = stability.get('trend', 0)
            trend_strength = stability.get('trend_strength', 0)
            
            quality_scores['momentum'] = max(0, min(1, (trend * 5 + 0.5))) * trend_strength
            
            # Calculate overall quality score
            weights = {
                'consistency': 0.4,
                'sustainability': 0.4,
                'momentum': 0.2
            }
            
            quality_scores['overall'] = sum(
                score * weights[metric]
                for metric, score in quality_scores.items()
                if metric != 'overall'
            )
            
            return quality_scores
            
        except Exception as e:
            logger.error(f"Error analyzing growth quality: {str(e)}")
            return {}
