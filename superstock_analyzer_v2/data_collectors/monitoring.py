"""Simple monitoring system for data collection pipeline."""

import logging
import time
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class PipelineMonitor:
    """Basic monitor for data collection pipeline performance."""
    
    def __init__(self):
        """Initialize pipeline monitor."""
        self.api_latencies: Dict[str, float] = {}  # endpoint -> avg latency
        self.error_counts: Dict[str, int] = {}     # component -> error count
        self.validation_counts = {
            'success': 0,
            'failure': 0
        }
        self.start_time = datetime.now()
        
        # Basic thresholds
        self.thresholds = {
            'api_latency': 5.0,    # seconds
            'error_rate': 0.3,     # 30%
            'validation_rate': 0.3  # 30% failure rate
        }

    def record_api_latency(self, endpoint: str, latency: float):
        """Record API request latency."""
        current_avg = self.api_latencies.get(endpoint, 0)
        count = 1 if endpoint not in self.api_latencies else 2
        self.api_latencies[endpoint] = (current_avg + latency) / count
        
        if latency > self.thresholds['api_latency']:
            logger.warning(f"High latency for {endpoint}: {latency:.2f}s")

    def record_error(self, component: str):
        """Record error occurrence."""
        self.error_counts[component] = self.error_counts.get(component, 0) + 1
        
        # Calculate error rate for component
        total_ops = sum(self.error_counts.values())
        if total_ops > 0:
            error_rate = self.error_counts[component] / total_ops
            if error_rate > self.thresholds['error_rate']:
                logger.warning(f"High error rate in {component}: {error_rate:.1%}")

    def record_validation(self, is_valid: bool):
        """Record data validation result."""
        if is_valid:
            self.validation_counts['success'] += 1
        else:
            self.validation_counts['failure'] += 1
            
        # Calculate validation failure rate
        total = sum(self.validation_counts.values())
        if total > 0:
            failure_rate = self.validation_counts['failure'] / total
            if failure_rate > self.thresholds['validation_rate']:
                logger.warning(f"High validation failure rate: {failure_rate:.1%}")

    def get_status_report(self) -> Dict:
        """Generate basic status report."""
        total_validations = sum(self.validation_counts.values())
        validation_rate = (
            self.validation_counts['success'] / total_validations 
            if total_validations > 0 else 0
        )
        
        return {
            'uptime': str(datetime.now() - self.start_time),
            'api_latencies': {
                endpoint: f"{latency:.2f}s"
                for endpoint, latency in self.api_latencies.items()
            },
            'error_counts': dict(self.error_counts),
            'validation_success_rate': f"{validation_rate:.1%}"
        }

    def log_status(self):
        """Log current status."""
        status = self.get_status_report()
        
        logger.info("=== Pipeline Status Report ===")
        logger.info(f"Uptime: {status['uptime']}")
        
        logger.info("API Latencies:")
        for endpoint, latency in status['api_latencies'].items():
            logger.info(f"  {endpoint}: {latency}")
            
        logger.info("Error Counts:")
        for component, count in status['error_counts'].items():
            logger.info(f"  {component}: {count}")
            
        logger.info(f"Validation Success Rate: {status['validation_success_rate']}")
