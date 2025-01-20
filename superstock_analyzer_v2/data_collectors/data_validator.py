from dataclasses import dataclass
from typing import List, Dict, Optional, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Basic validation result."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]

class DataValidator:
    """Simple data validator focusing on essential checks."""

    def __init__(self):
        """Initialize the data validator with basic thresholds."""
        # Basic market thresholds
        self.market_thresholds = {
            'min_volume': 100000,
            'min_market_cap': 1000000,  # $1M
            'min_price': 1.0,
            'min_earnings_growth': 0.15  # 15%
        }
        
        # Required fields for each data type
        self.required_fields = {
            'market_data': ['symbol', 'price', 'volume', 'marketCap'],
            'financial_data': ['revenue', 'earnings_growth', 'debt_to_equity'],
            'technical_data': ['close_prices', 'volumes', 'relative_strength']
        }

    def _check_required_fields(self, data: Dict, data_type: str) -> List[str]:
        """Check if all required fields are present."""
        if not data:
            return ["No data provided"]
            
        missing = [f for f in self.required_fields.get(data_type, [])
                  if f not in data or data[f] is None]
        return [f"Missing required fields: {missing}"] if missing else []

    def _validate_numeric(self, value: Any, field: str, min_value: Optional[float] = None) -> List[str]:
        """Basic numeric validation."""
        if not isinstance(value, (int, float)):
            return [f"{field} must be numeric"]
        if min_value is not None and value < min_value:
            return [f"{field} ({value}) below minimum threshold ({min_value})"]
        return []

    def validate_market_data(self, data: Dict) -> ValidationResult:
        """Validate market data with basic checks."""
        errors = []
        warnings = []
        
        # Check required fields
        errors.extend(self._check_required_fields(data, 'market_data'))
        if errors:
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings)

        # Basic numeric validations
        errors.extend(self._validate_numeric(
            data.get('volume', 0), 'Volume', 
            self.market_thresholds['min_volume']
        ))
        errors.extend(self._validate_numeric(
            data.get('marketCap', 0), 'Market Cap', 
            self.market_thresholds['min_market_cap']
        ))
        errors.extend(self._validate_numeric(
            data.get('price', 0), 'Price',
            self.market_thresholds['min_price']
        ))

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    def validate_financial_data(self, data: Dict) -> ValidationResult:
        """Validate financial data with basic checks."""
        errors = []
        warnings = []
        
        # Check required fields
        errors.extend(self._check_required_fields(data, 'financial_data'))
        if errors:
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings)

        # Basic validations
        if data.get('revenue', 0) <= 0:
            warnings.append("Revenue is non-positive")
            
        if data.get('earnings_growth', 0) < self.market_thresholds['min_earnings_growth']:
            warnings.append(f"Earnings growth below {self.market_thresholds['min_earnings_growth']:.1%}")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    def validate_technical_data(self, data: Dict) -> ValidationResult:
        """Validate technical data with basic checks."""
        errors = []
        warnings = []
        
        # Check required fields
        errors.extend(self._check_required_fields(data, 'technical_data'))
        if errors:
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings)

        # Basic validations
        if not data.get('close_prices', []):
            errors.append("No price history available")
        if not data.get('volumes', []):
            errors.append("No volume history available")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    def log_validation_result(self, symbol: str, result: ValidationResult, data_type: str):
        """Simple logging of validation results."""
        if not result.is_valid:
            logger.error(f"[{symbol}] {data_type} validation failed:")
            for error in result.errors:
                logger.error(f"[{symbol}] Error: {error}")
        if result.warnings:
            logger.warning(f"[{symbol}] {data_type} validation warnings:")
            for warning in result.warnings:
                logger.warning(f"[{symbol}] Warning: {warning}")
