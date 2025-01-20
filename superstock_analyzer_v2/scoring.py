from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union, Any
import pandas as pd
import numpy as np
from scipy import stats
import scipy.stats as stats
from scipy.stats import percentileofscore
import logging
import json

@dataclass
class StockScore:
    symbol: str
    total_score: float
    fundamental_score: float
    technical_score: float
    qualitative_score: float
    bonus_points: float
    analysis_date: datetime
    key_metrics: Dict
    catalysts: List[str]
    risks: List[str]
    passed_threshold: bool
    gpt_insights: Dict

# Fundamental Factors (45 Points)
FUNDAMENTAL_METRICS = [
    # Earnings Quality (18 points)
    ('growth_metrics.quarterly.sequential_earnings_growth', 6, 0, 100),  # Sequential quarterly growth
    ('growth_metrics.annual.sustainable_earnings_growth', 6, 0, 100),    # Sustainable growth
    ('growth_metrics.quarterly.upcoming_comparisons', 4, -100, 100),     # Easy upcoming comparisons
    ('growth_metrics.operating_leverage', 2, 0, 100),                    # Operating leverage

    # Financial Health (17 points)
    ('financial_ratios.peRatioTTM', 4, 0, 10),                          # P/E under 10
    ('financial_ratios.debtToEquityTTM', 3, 0, 0.75),                   # Low debt levels
    ('financial_ratios.debtServiceCoverage', 3, 1, 5),                  # Debt service coverage
    ('financial_ratios.workingCapitalTrend', 3, 0, 100),                # Improving working capital
    ('financial_ratios.cashFlowToDebtRatio', 2, 0.5, 2),               # Strong cash flow
    ('growth_metrics.backlog_growth', 2, 0, 100),                       # Growing backlog

    # Company Structure (10 points)
    ('market_data.float', 4, 4e6, 8e6),                                # Low float (4-8M shares)
    ('market_data.marketCap', 3, 5e6, 250e6),                          # Market cap under $250M
    ('management_metrics.conservative_style', 3, 0, 1)                  # Conservative management
]

# Technical Factors (25 Points)
TECHNICAL_METRICS = [
    # Base Formation (10 points)
    ('base_pattern.development', 4, 0, 1),                             # Strong base development
    ('base_pattern.volume_pattern', 3, 0, 1),                         # Low volume during base
    ('base_pattern.price_tightness', 3, 0, 1),                        # Tight price range

    # Breakout Quality (8 points)
    ('breakout.volume_expansion', 3, 1.5, 5),                         # Volume expansion
    ('breakout.ma30_crossover', 3, 0, 1),                            # Break above 30-week MA
    ('breakout.angle', 2, 30, 60),                                    # ~45-degree price movement

    # Relative Strength (7 points)
    ('market_context.relative_strength_rank', 3, 90, 100),            # Top 10% relative strength
    ('market_context.industry_rank', 2, 90, 100),                     # Strong industry rank
    ('market_context.accumulation', 2, 0, 1)                          # Strong accumulation
]

# Qualitative Factors (30 Points)
QUALITATIVE_METRICS = [
    # Super Theme (12 points)
    ('theme.uniqueness', 5, 0, 1),                                    # Unique/emerging theme
    ('theme.competition', 4, 0, 1),                                   # Limited competition
    ('theme.market_appreciation', 3, 0, 1),                           # Market under-appreciation

    # Insider Activity (10 points)
    ('insider.executive_buying', 4, 0, 1),                            # Multiple C-level buying
    ('insider.purchase_size', 3, 0, 1),                               # Size relative to salary
    ('insider.timing', 3, 0, 1),                                      # Timing of purchases

    # Management Quality (8 points)
    ('management.execution', 3, 0, 1),                                # Track record
    ('management.communication', 3, 0, 1),                            # Conservative style
    ('management.dilution', 2, 0, 1)                                  # Limited dilution
]

class StockScorer:
    """Score stocks based on fundamental, technical, and qualitative metrics."""
    def __init__(self):
        """Initialize scorer with methodology-aligned configuration."""
        self.config = {
            'fundamental_weight': 45,  # 45% per methodology
            'technical_weight': 25,    # 25% per methodology
            'qualitative_weight': 30,  # 30% per methodology
            'min_total_score': 70,     # Higher threshold for quality
            'min_fundamental_score': 35,  # 77.8% of 45 points
            'min_technical_score': 20,    # 80% of 25 points
            'min_data_quality': 0.8,      # Increased data quality requirement
            'bonus_cap': 10,              # Maximum bonus points
            'penalty_cap': -10            # Maximum penalty points
        }
        
        self.market_context = {
            'sector_data': {},
            'metric_stats': {}
        }
        
        self.logger = logging.getLogger(__name__)

    def calculate_piotroski_score(self, financials: Dict) -> int:
        """Calculate complete Piotroski F-Score (9 points)."""
        score = 0
        try:
            # Profitability Criteria (4 points)
            if financials.get('netIncome', 0) > 0:
                score += 1  # Positive net income
            if financials.get('operatingCashFlow', 0) > 0:
                score += 1  # Positive operating cash flow
            if financials.get('roa', 0) > financials.get('roa_prior', 0):
                score += 1  # Improving ROA
            if financials.get('operatingCashFlow', 0) > financials.get('netIncome', 0):
                score += 1  # Cash flow > Net Income

            # Leverage/Liquidity Criteria (3 points)
            if financials.get('longTermDebt', 0) < financials.get('longTermDebt_prior', 0):
                score += 1  # Decreasing long-term debt
            if financials.get('currentRatio', 0) > financials.get('currentRatio_prior', 0):
                score += 1  # Improving current ratio
            if financials.get('shares', 0) <= financials.get('shares_prior', 0):
                score += 1  # No dilution

            # Operating Efficiency Criteria (2 points)
            if financials.get('grossMargin', 0) > financials.get('grossMargin_prior', 0):
                score += 1  # Improving gross margin
            if financials.get('assetTurnover', 0) > financials.get('assetTurnover_prior', 0):
                score += 1  # Improving asset turnover

        except Exception as e:
            self.logger.error(f"Error calculating Piotroski F-Score: {str(e)}")

        return score

    def calculate_bonus_points(self, data: Dict) -> float:
        """Calculate bonus points (max 10 points)."""
        bonus = 0
        
        # No analyst coverage (+2)
        if data.get('analyst_coverage', 0) == 0:
            bonus += 2
            
        # No options listed (+2)
        if not data.get('has_options', False):
            bonus += 2
            
        # Game-changing catalyst (+3)
        if data.get('catalysts', {}).get('game_changing', False):
            bonus += 3
            
        # "Magic line" support (+2)
        if data.get('technical_data', {}).get('magic_line_support', False):
            bonus += 2
            
        # Exceptional accumulation (+1)
        if data.get('technical_data', {}).get('exceptional_accumulation', False):
            bonus += 1
            
        return min(bonus, self.config['bonus_cap'])

    def calculate_penalty_points(self, data: Dict) -> float:
        """Calculate penalty points (max -10 points)."""
        penalty = 0
        
        # Recent secondary offering (-5)
        if data.get('recent_offering', False):
            penalty -= 5
            
        # Excessive media coverage (-3)
        if data.get('media_coverage', {}).get('is_excessive', False):
            penalty -= 3
            
        # Overcrowded trade (-2)
        if data.get('market_sentiment', {}).get('is_overcrowded', False):
            penalty -= 2
            
        return max(penalty, self.config['penalty_cap'])

    def update_market_context(self, market_data: List[Dict]) -> None:
        """Update market context with sector data and metric statistics."""
        try:
            # Calculate sector performance
            sector_data = {}
            for stock in market_data:
                sector = stock.get('sector')
                if sector:
                    if sector not in sector_data:
                        sector_data[sector] = []
                    sector_data[sector].append(stock)
            
            # Calculate sector metrics
            for sector, stocks in sector_data.items():
                self.market_context['sector_data'][sector] = {
                    'count': len(stocks),
                    'avg_volume': np.mean([s.get('volume', 0) for s in stocks]),
                    'avg_market_cap': np.mean([s.get('marketCap', 0) for s in stocks]),
                    'avg_pe': np.mean([s.get('peRatio', 0) for s in stocks if s.get('peRatio', 0) > 0])
                }
            
            # Calculate market-wide metric statistics
            metrics = ['volume', 'marketCap', 'peRatio', 'price']
            for metric in metrics:
                values = [s.get(metric, 0) for s in market_data if s.get(metric, 0) > 0]
                if values:
                    self.market_context['metric_stats'][metric] = {
                        'mean': np.mean(values),
                        'median': np.median(values),
                        'std': np.std(values),
                        'percentiles': {
                            '25': np.percentile(values, 25),
                            '50': np.percentile(values, 50),
                            '75': np.percentile(values, 75),
                            '90': np.percentile(values, 90)
                        }
                    }
            
        except Exception as e:
            self.logger.error(f"Error updating market context: {str(e)}")

    def calculate_scores(self, data_list: List[Dict]) -> List[StockScore]:
        """Calculate scores for a list of stocks."""
        scores = []
        for data in data_list:
            try:
                # Extract required data
                fundamental_data = data.get('fundamental_data', {})
                technical_data = data.get('technical_data', {})
                qualitative_data = data.get('qualitative_data', {})
                
                # Calculate component scores
                fundamental_score = self._calculate_fundamental_score(fundamental_data)
                technical_score = self._calculate_technical_score(technical_data)
                qualitative_score = self._calculate_qualitative_score(qualitative_data)
                
                # Calculate bonus/penalty points
                bonus_points = self.calculate_bonus_points(data)
                penalty_points = self.calculate_penalty_points(data)
                
                # Create score object
                score = StockScore(
                    symbol=data['symbol'],
                    total_score=fundamental_score + technical_score + qualitative_score + bonus_points + penalty_points,
                    fundamental_score=fundamental_score,
                    technical_score=technical_score,
                    qualitative_score=qualitative_score,
                    bonus_points=bonus_points + penalty_points,
                    analysis_date=datetime.now(),
                    key_metrics=self._extract_key_metrics(data),
                    catalysts=self._extract_catalysts(data),
                    risks=self._extract_risks(data),
                    passed_threshold=fundamental_score >= self.config['min_fundamental_score'] and 
                                   technical_score >= self.config['min_technical_score'],
                    gpt_insights=self._extract_gpt_insights(data)
                )
                scores.append(score)
            except Exception as e:
                self.logger.error(f"Error scoring {data.get('symbol', 'Unknown')}: {str(e)}")
                scores.append(None)
        return scores

    def calculate_total_score(self, data: Dict) -> StockScore:
        """Calculate total score with proper weights and bonus/penalty points."""
        try:
            # Calculate component scores
            fundamental_score = self._calculate_fundamental_score(data)
            technical_score = self._calculate_technical_score(data)
            qualitative_score = self._calculate_qualitative_score(data)
            
            # Calculate weighted base score
            base_score = (
                fundamental_score * (self.config['fundamental_weight'] / 100) +
                technical_score * (self.config['technical_weight'] / 100) +
                qualitative_score * (self.config['qualitative_weight'] / 100)
            )
            
            # Add bonus/penalty points
            bonus_points = self.calculate_bonus_points(data)
            penalty_points = self.calculate_penalty_points(data)
            final_score = base_score + bonus_points + penalty_points
            
            # Create score object
            return StockScore(
                symbol=data['symbol'],
                total_score=final_score,
                fundamental_score=fundamental_score,
                technical_score=technical_score,
                qualitative_score=qualitative_score,
                bonus_points=bonus_points + penalty_points,
                analysis_date=datetime.now(),
                key_metrics=self._extract_key_metrics(data),
                catalysts=self._extract_catalysts(data),
                risks=self._extract_risks(data),
                passed_threshold=final_score >= self.config['min_total_score'],
                gpt_insights=self._extract_gpt_insights(data)
            )
            
        except Exception as e:
            self.logger.error(f"Error calculating total score: {str(e)}")
            return self._create_empty_score(data.get('symbol', 'UNKNOWN'))

    def _calculate_fundamental_score(self, data: Dict) -> float:
        """Calculate fundamental score using methodology-aligned metrics."""
        score = 0
        for metric, weight, min_val, max_val in FUNDAMENTAL_METRICS:
            value = self._get_nested_value(data, metric)
            if value is not None:
                normalized = self._normalize_value(value, min_val, max_val)
                score += normalized * weight
        return score

    def _calculate_technical_score(self, data: Dict) -> float:
        """Calculate technical score using methodology-aligned metrics."""
        score = 0
        for metric, weight, min_val, max_val in TECHNICAL_METRICS:
            value = self._get_nested_value(data, metric)
            if value is not None:
                normalized = self._normalize_value(value, min_val, max_val)
                score += normalized * weight
        return score

    def _calculate_qualitative_score(self, data: Dict) -> float:
        """Calculate qualitative score using methodology-aligned metrics."""
        score = 0
        for metric, weight, min_val, max_val in QUALITATIVE_METRICS:
            value = self._get_nested_value(data, metric)
            if value is not None:
                normalized = self._normalize_value(value, min_val, max_val)
                score += normalized * weight
        return score

    def _get_nested_value(self, data: Dict, key_path: str) -> Optional[Any]:
        """Get value from nested dictionary using dot notation."""
        try:
            value = data
            for key in key_path.split('.'):
                value = value.get(key, {})
            return value if value != {} else None
        except Exception:
            return None

    def _normalize_value(self, value: float, min_val: float, max_val: float) -> float:
        """Normalize value between 0 and 1."""
        try:
            if min_val == max_val:
                return 1.0 if value >= min_val else 0.0
            return max(0.0, min(1.0, (value - min_val) / (max_val - min_val)))
        except Exception:
            return 0.0

    def _extract_key_metrics(self, data: Dict) -> Dict:
        """Extract key metrics for score explanation."""
        return {
            'revenue_growth': data.get('growth_metrics', {}).get('revenue_growth'),
            'earnings_growth': data.get('growth_metrics', {}).get('earnings_growth'),
            'debt_to_equity': data.get('financial_ratios', {}).get('debtToEquityTTM'),
            'relative_strength': data.get('market_context', {}).get('relative_strength_rank'),
            'volume_trend': data.get('technical_data', {}).get('volume_trend')
        }

    def _extract_catalysts(self, data: Dict) -> List[str]:
        """Extract catalysts from data."""
        catalysts = data.get('catalysts', {}).get('list', [])
        return catalysts if isinstance(catalysts, list) else []

    def _extract_risks(self, data: Dict) -> List[str]:
        """Extract risks from data."""
        risks = data.get('risks', {}).get('list', [])
        return risks if isinstance(risks, list) else []

    def _extract_gpt_insights(self, data: Dict) -> Dict:
        """Extract GPT-generated insights."""
        return data.get('gpt_insights', {})

    def _create_empty_score(self, symbol: str) -> StockScore:
        """Create an empty score object for error cases."""
        return StockScore(
            symbol=symbol,
            total_score=0.0,
            fundamental_score=0.0,
            technical_score=0.0,
            qualitative_score=0.0,
            bonus_points=0.0,
            analysis_date=datetime.now(),
            key_metrics={},
            catalysts=[],
            risks=[],
            passed_threshold=False,
            gpt_insights={}
        )
