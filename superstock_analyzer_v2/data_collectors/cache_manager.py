"""Simple cache manager with disk persistence."""

import os
import pickle
import logging
import time
from typing import Dict, Any, Optional, Union

logger = logging.getLogger(__name__)

class CacheEntry:
    """Cache entry with basic metadata."""
    
    def __init__(self, value: Any, ttl: int = 3600):  # Default 1 hour TTL
        """Initialize cache entry."""
        self.value = value
        self.created_at = time.time()
        self.ttl = ttl
        
    def is_expired(self) -> bool:
        """Check if entry has expired."""
        return time.time() > self.created_at + self.ttl

class CacheManager:
    """Simple cache manager with disk persistence."""
    
    def __init__(self, cache_dir: str):
        """Initialize cache manager.
        
        Args:
            cache_dir: Directory for disk cache
        """
        self.cache_dir = cache_dir
        self.memory_cache: Dict[str, CacheEntry] = {}
        
        # Ensure cache directory exists
        os.makedirs(cache_dir, exist_ok=True)
        
        # Basic TTL configuration (in seconds)
        self.ttl_config = {
            'market': 300,      # 5 minutes
            'financial': 3600,  # 1 hour
            'technical': 900,   # 15 minutes
            'default': 1800     # 30 minutes
        }
        
    def _get_ttl(self, key: str) -> int:
        """Get TTL based on cache key prefix."""
        if key.startswith('market_'):
            return self.ttl_config['market']
        elif key.startswith('financial_'):
            return self.ttl_config['financial']
        elif key.startswith('technical_'):
            return self.ttl_config['technical']
        return self.ttl_config['default']
        
    def _get_cache_path(self, key: str) -> str:
        """Get cache file path for key."""
        return os.path.join(self.cache_dir, f"{key}.pickle")
        
    def get_from_cache(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        # Check memory cache first
        if key in self.memory_cache:
            entry = self.memory_cache[key]
            if not entry.is_expired():
                return entry.value
            else:
                del self.memory_cache[key]
                
        # Check disk cache
        cache_path = self._get_cache_path(key)
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'rb') as f:
                    entry = pickle.load(f)
                if not entry.is_expired():
                    # Store in memory for faster subsequent access
                    self.memory_cache[key] = entry
                    return entry.value
                else:
                    # Remove expired cache file
                    os.remove(cache_path)
            except Exception as e:
                logger.warning(f"Error reading cache file {key}: {str(e)}")
                
        return None
        
    def cache_data(self, key: str, value: Any):
        """Cache data to both memory and disk."""
        ttl = self._get_ttl(key)
        entry = CacheEntry(value, ttl)
        
        # Update memory cache
        self.memory_cache[key] = entry
        
        # Write to disk cache
        cache_path = self._get_cache_path(key)
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(entry, f)
        except Exception as e:
            logger.warning(f"Error writing cache file {key}: {str(e)}")
            
    def clear_cache(self):
        """Clear all cache entries."""
        # Clear memory cache
        self.memory_cache.clear()
        
        # Clear disk cache
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.pickle'):
                    os.remove(os.path.join(self.cache_dir, filename))
        except Exception as e:
            logger.warning(f"Error clearing cache directory: {str(e)}")
            
    def remove_expired(self):
        """Remove expired cache entries."""
        # Clear expired memory cache entries
        expired_keys = [
            key for key, entry in self.memory_cache.items()
            if entry.is_expired()
        ]
        for key in expired_keys:
            del self.memory_cache[key]
            
        # Clear expired disk cache entries
        try:
            for filename in os.listdir(self.cache_dir):
                if not filename.endswith('.pickle'):
                    continue
                    
                filepath = os.path.join(self.cache_dir, filename)
                try:
                    with open(filepath, 'rb') as f:
                        entry = pickle.load(f)
                    if entry.is_expired():
                        os.remove(filepath)
                except Exception:
                    # Remove corrupt cache files
                    os.remove(filepath)
        except Exception as e:
            logger.warning(f"Error cleaning cache directory: {str(e)}")
