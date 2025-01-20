"""Essential validation for batch data collection."""

import logging
from typing import Dict, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Simple validation result."""
    is_valid: bool
    errors: List[str]

class BatchValidator:
    """Essential validator for batch data collection."""
    
    def __init__(self):
        """Initialize validator with essential thresholds."""
        # Essential required fields only
        self.required_fields = {
            'market_data': ['symbol', 'price', 'volume'],
            'financial_data': ['revenue', 'earnings']
        }
        
        # Basic value ranges
        self.value_ranges = {
            'price': (0.01, 1000000),  # $0.01 to $1M
            'volume': (1000, 1000000000)  # 1K to 1B
        }

    def validate_market_data(self, data: Dict) -> ValidationResult:
        """Validate market data with essential checks."""
        errors = []
        
        # Check required fields
        if not data:
            return ValidationResult(is_valid=False, errors=["No data provided"])
            
        missing_fields = [
            field for field in self.required_fields['market_data']
            if field not in data or data[field] is None
        ]
        if missing_fields:
            errors.append(f"Missing required fields: {missing_fields}")
            return ValidationResult(is_valid=False, errors=errors)
            
        try:
            # Essential range validations
            price = float(data.get('price', 0))
            if not self.value_ranges['price'][0] <= price <= self.value_ranges['price'][1]:
                errors.append(f"Price {price} outside valid range")
                
            volume = int(data.get('volume', 0))
            if not self.value_ranges['volume'][0] <= volume <= self.value_ranges['volume'][1]:
                errors.append(f"Volume {volume} outside valid range")
                
        except (ValueError, TypeError) as e:
            errors.append(f"Invalid data format: {str(e)}")
            
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )

    def validate_financial_data(self, data: Dict) -> ValidationResult:
        """Validate financial data with essential checks."""
        errors = []
        
        # Check required fields
        if not data:
            return ValidationResult(is_valid=False, errors=["No data provided"])
            
        missing_fields = [
            field for field in self.required_fields['financial_data']
            if field not in data or data[field] is None
        ]
        if missing_fields:
            errors.append(f"Missing required fields: {missing_fields}")
            return ValidationResult(is_valid=False, errors=errors)
            
        try:
            # Basic value validation - ensure positive numbers
            for field in self.required_fields['financial_data']:
                value = float(data.get(field, 0))
                if value < 0:
                    errors.append(f"Negative value for {field}: {value}")
                    
        except (ValueError, TypeError) as e:
            errors.append(f"Invalid data format: {str(e)}")
            
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )

    def log_validation_error(self, symbol: str, result: ValidationResult):
        """Log validation errors for a symbol."""
        if not result.is_valid:
            logger.error(f"Validation failed for {symbol}:")
            for error in result.errors:
                logger.error(f"  - {error}")
