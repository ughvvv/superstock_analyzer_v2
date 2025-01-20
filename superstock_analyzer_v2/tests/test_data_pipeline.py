"""Test suite for enhanced data collection pipeline."""

import pytest
import asyncio
from unittest.mock import Mock, patch
import aiohttp
from datetime import datetime, timedelta

from data_collectors.market_data_collector import MarketDataCollector
from data_collectors.data_validator import DataValidator
from data_collectors.circuit_breaker import CircuitBreakerManager, CircuitBreakerError
from data_collectors.cache_manager import TieredCache
from data_collectors.monitoring import PipelineMonitor, MetricsCollector

# Test data
VALID_STOCK_DATA = {
    'symbol': 'AAPL',
    'price': 150.0,
    'volume': 1000000,
    'marketCap': 2.5e9,
    'timestamp': datetime.now().isoformat()
}

INVALID_STOCK_DATA = {
    'symbol': 'INVALID',
    'price': -1,
    'volume': 0,
    'marketCap': 1000
}

@pytest.fixture
def market_collector():
    """Create market data collector instance."""
    return MarketDataCollector('test_api_key')

@pytest.fixture
def validator():
    """Create data validator instance."""
    return DataValidator()

@pytest.fixture
def circuit_breaker():
    """Create circuit breaker instance."""
    return CircuitBreakerManager()

@pytest.fixture
def cache():
    """Create cache instance."""
    return TieredCache('test_cache')

@pytest.fixture
def monitor():
    """Create pipeline monitor instance."""
    return PipelineMonitor()

class TestDataValidation:
    """Test data validation functionality."""
    
    def test_valid_market_data(self, validator):
        """Test validation of valid market data."""
        result = validator.validate_market_data(VALID_STOCK_DATA)
        assert result.is_valid
        assert not result.errors
        assert result.confidence_score > 0.8
        
    def test_invalid_market_data(self, validator):
        """Test validation of invalid market data."""
        result = validator.validate_market_data(INVALID_STOCK_DATA)
        assert not result.is_valid
        assert len(result.errors) > 0
        assert result.confidence_score < 0.5
        
    def test_data_freshness(self, validator):
        """Test data freshness validation."""
        stale_data = VALID_STOCK_DATA.copy()
        stale_data['timestamp'] = (
            datetime.now() - timedelta(minutes=30)
        ).isoformat()
        
        result = validator.validate_market_data(stale_data)
        assert not result.is_valid
        assert any('stale' in error.lower() for error in result.errors)

class TestCircuitBreaker:
    """Test circuit breaker functionality."""
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_trip(self, circuit_breaker):
        """Test circuit breaker tripping on failures."""
        endpoint = "test_endpoint"
        breaker = circuit_breaker.get_breaker(endpoint)
        
        # Simulate failures
        for _ in range(5):
            breaker.on_failure()
            
        assert not breaker.can_execute()
        
    @pytest.mark.asyncio
    async def test_circuit_breaker_recovery(self, circuit_breaker):
        """Test circuit breaker recovery."""
        endpoint = "test_endpoint"
        breaker = circuit_breaker.get_breaker(endpoint)
        
        # Trip the breaker
        for _ in range(5):
            breaker.on_failure()
            
        # Simulate timeout
        breaker.last_failure_time -= 61  # Past recovery timeout
        
        assert breaker.can_execute()
        
        # Successful calls should reset the breaker
        for _ in range(3):
            breaker.on_success()
            
        assert breaker.state.value == "CLOSED"

class TestCaching:
    """Test caching functionality."""
    
    def test_cache_operations(self, cache):
        """Test basic cache operations."""
        # Test set and get
        cache.set("test_key", VALID_STOCK_DATA)
        cached_data = cache.get("test_key")
        assert cached_data == VALID_STOCK_DATA
        
        # Test expiration
        cache.ttl_config['market'] = 1  # Set TTL to 1 second
        cache.set("expire_key", VALID_STOCK_DATA)
        import time
        time.sleep(1.1)
        expired_data = cache.get("expire_key")
        assert expired_data is None
        
    def test_cache_eviction(self, cache):
        """Test cache eviction."""
        # Fill cache beyond max size
        cache.max_memory_entries = 2
        for i in range(3):
            cache.set(f"key_{i}", VALID_STOCK_DATA)
            
        # Verify least accessed entry was evicted
        assert len(cache.memory_cache) == 2

class TestMonitoring:
    """Test monitoring functionality."""
    
    def test_metric_collection(self, monitor):
        """Test metric collection and alerting."""
        # Record some metrics
        monitor.record_api_latency("test_endpoint", 1.0)
        monitor.record_error("test_component", "test_error")
        monitor.record_validation("market_data", True)
        
        # Get metrics report
        report = monitor.get_metrics_report()
        
        assert "api_latencies" in report
        assert "error_rates" in report
        assert "validation_rates" in report
        
    def test_alert_generation(self, monitor):
        """Test alert generation."""
        # Trigger alert with high latency
        monitor.record_api_latency("test_endpoint", 5.0)  # Above threshold
        
        assert len(monitor.alerts) > 0
        assert monitor.alerts[-1]['type'] == 'API_LATENCY'

@pytest.mark.asyncio
class TestIntegration:
    """Integration tests for the complete pipeline."""
    
    async def test_market_data_collection(self, market_collector, monkeypatch):
        """Test complete market data collection process."""
        # Mock API response
        async def mock_get(*args, **kwargs):
            return Mock(
                status=200,
                json=Mock(return_value=[VALID_STOCK_DATA])
            )
            
        monkeypatch.setattr(aiohttp.ClientSession, "get", mock_get)
        
        # Test data collection
        data = await market_collector.get_market_data("AAPL")
        assert data is not None
        assert data['symbol'] == 'AAPL'
        
        # Verify cache
        cached_data = market_collector.cache.get("market_data_AAPL")
        assert cached_data == data
        
        # Verify monitoring
        assert len(market_collector.validator.validation_stats['total_validations']) > 0
        
    async def test_error_handling(self, market_collector, monkeypatch):
        """Test error handling in the pipeline."""
        # Mock API failure
        async def mock_get(*args, **kwargs):
            raise aiohttp.ClientError()
            
        monkeypatch.setattr(aiohttp.ClientSession, "get", mock_get)
        
        # Test error handling
        with pytest.raises(CircuitBreakerError):
            await market_collector.get_market_data("AAPL")
            
        # Verify circuit breaker tripped
        breaker = market_collector.circuit_breaker.get_breaker("market_data")
        assert not breaker.can_execute()
