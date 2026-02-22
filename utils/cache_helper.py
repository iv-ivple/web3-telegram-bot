# utils/cache_helper.py
"""
Enhanced caching system with compression, size limits, and cleanup
"""
import json
import hashlib
import gzip
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class QueryCache:
    """
    File-based query cache with automatic cleanup and compression
    """
    
    def __init__(
        self,
        cache_dir: str = "cache",
        ttl_minutes: int = 5,
        max_cache_size_mb: int = 100,
        compress: bool = True,
        cleanup_on_init: bool = True
    ):
        """
        Initialize QueryCache
        
        Args:
            cache_dir: Directory to store cache files
            ttl_minutes: Time-to-live for cache entries in minutes
            max_cache_size_mb: Maximum cache directory size in MB
            compress: Enable gzip compression for cache files
            cleanup_on_init: Clean expired entries on initialization
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True, parents=True)
        self.ttl = timedelta(minutes=ttl_minutes)
        self.max_cache_size_bytes = max_cache_size_mb * 1024 * 1024
        self.compress = compress
        
        # Statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'writes': 0,
            'expired': 0,
            'errors': 0
        }
        
        if cleanup_on_init:
            self.cleanup_expired()
    
    def _get_cache_key(self, query: str, variables: Optional[Dict] = None) -> str:
        """
        Generate cache key from query and variables
        
        Args:
            query: GraphQL query string
            variables: Query variables
            
        Returns:
            MD5 hash as cache key
        """
        content = query.strip()
        if variables:
            content += json.dumps(variables, sort_keys=True)
        return hashlib.md5(content.encode()).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """Get file path for cache key"""
        extension = '.json.gz' if self.compress else '.json'
        return self.cache_dir / f"{cache_key}{extension}"
    
    def get(self, query: str, variables: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """
        Get cached result if fresh
        
        Args:
            query: GraphQL query string
            variables: Query variables
            
        Returns:
            Cached result or None if not found/expired
        """
        try:
            cache_key = self._get_cache_key(query, variables)
            cache_file = self._get_cache_path(cache_key)
            
            if not cache_file.exists():
                self.stats['misses'] += 1
                return None
            
            # Check if expired
            modified_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
            if datetime.now() - modified_time > self.ttl:
                self.stats['expired'] += 1
                cache_file.unlink()  # Delete expired file
                return None
            
            # Read cached data
            if self.compress:
                with gzip.open(cache_file, 'rt', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            
            self.stats['hits'] += 1
            logger.debug(f"Cache hit: {cache_key}")
            return data
            
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Cache read error: {str(e)}")
            return None
    
    def set(self, query: str, result: Dict[str, Any], variables: Optional[Dict] = None):
        """
        Cache query result
        
        Args:
            query: GraphQL query string
            result: Query result to cache
            variables: Query variables
        """
        try:
            cache_key = self._get_cache_key(query, variables)
            cache_file = self._get_cache_path(cache_key)
            
            # Write to cache
            if self.compress:
                with gzip.open(cache_file, 'wt', encoding='utf-8') as f:
                    json.dump(result, f)
            else:
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2)
            
            self.stats['writes'] += 1
            logger.debug(f"Cache write: {cache_key}")
            
            # Check size limits
            self._enforce_size_limit()
            
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Cache write error: {str(e)}")
    
    def delete(self, query: str, variables: Optional[Dict] = None) -> bool:
        """
        Delete specific cache entry
        
        Args:
            query: GraphQL query string
            variables: Query variables
            
        Returns:
            True if deleted, False if not found
        """
        try:
            cache_key = self._get_cache_key(query, variables)
            cache_file = self._get_cache_path(cache_key)
            
            if cache_file.exists():
                cache_file.unlink()
                logger.debug(f"Cache deleted: {cache_key}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Cache delete error: {str(e)}")
            return False
    
    def clear(self):
        """Clear all cache entries"""
        try:
            for cache_file in self.cache_dir.glob('*'):
                if cache_file.is_file():
                    cache_file.unlink()
            logger.info("Cache cleared")
        except Exception as e:
            logger.error(f"Cache clear error: {str(e)}")
    
    def cleanup_expired(self) -> int:
        """
        Remove expired cache entries
        
        Returns:
            Number of entries removed
        """
        removed = 0
        try:
            now = datetime.now()
            
            for cache_file in self.cache_dir.glob('*'):
                if not cache_file.is_file():
                    continue
                
                modified_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
                if now - modified_time > self.ttl:
                    cache_file.unlink()
                    removed += 1
            
            if removed > 0:
                logger.info(f"Cleaned up {removed} expired cache entries")
                
        except Exception as e:
            logger.error(f"Cache cleanup error: {str(e)}")
        
        return removed
    
    def _enforce_size_limit(self):
        """Remove oldest entries if cache exceeds size limit"""
        try:
            total_size = sum(f.stat().st_size for f in self.cache_dir.glob('*') if f.is_file())
            
            if total_size <= self.max_cache_size_bytes:
                return
            
            # Get all files sorted by modification time (oldest first)
            files = sorted(
                [f for f in self.cache_dir.glob('*') if f.is_file()],
                key=lambda f: f.stat().st_mtime
            )
            
            # Remove oldest files until under limit
            removed = 0
            for cache_file in files:
                if total_size <= self.max_cache_size_bytes:
                    break
                
                file_size = cache_file.stat().st_size
                cache_file.unlink()
                total_size -= file_size
                removed += 1
            
            if removed > 0:
                logger.info(f"Removed {removed} old cache entries to enforce size limit")
                
        except Exception as e:
            logger.error(f"Size limit enforcement error: {str(e)}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache statistics
        """
        stats = self.stats.copy()
        
        # Calculate hit rate
        total_reads = stats['hits'] + stats['misses']
        if total_reads > 0:
            stats['hit_rate'] = (stats['hits'] / total_reads) * 100
        else:
            stats['hit_rate'] = 0.0
        
        # Calculate cache size
        try:
            cache_files = list(self.cache_dir.glob('*'))
            stats['entry_count'] = len([f for f in cache_files if f.is_file()])
            stats['size_bytes'] = sum(
                f.stat().st_size for f in cache_files if f.is_file()
            )
            stats['size_mb'] = stats['size_bytes'] / (1024 * 1024)
        except Exception as e:
            logger.error(f"Error calculating cache stats: {str(e)}")
            stats['entry_count'] = 0
            stats['size_bytes'] = 0
            stats['size_mb'] = 0.0
        
        return stats
    
    def reset_stats(self):
        """Reset statistics counters"""
        self.stats = {
            'hits': 0,
            'misses': 0,
            'writes': 0,
            'expired': 0,
            'errors': 0
        }


class InMemoryCache:
    """
    Simple in-memory cache for short-lived data
    """
    
    def __init__(self, ttl_seconds: int = 60):
        """
        Initialize in-memory cache
        
        Args:
            ttl_seconds: Time-to-live in seconds
        """
        self.cache = {}
        self.ttl = timedelta(seconds=ttl_seconds)
    
    def _get_cache_key(self, query: str, variables: Optional[Dict] = None) -> str:
        """Generate cache key"""
        content = query.strip()
        if variables:
            content += json.dumps(variables, sort_keys=True)
        return hashlib.md5(content.encode()).hexdigest()
    
    def get(self, query: str, variables: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """Get cached result"""
        key = self._get_cache_key(query, variables)
        
        if key not in self.cache:
            return None
        
        data, timestamp = self.cache[key]
        
        # Check if expired
        if datetime.now() - timestamp > self.ttl:
            del self.cache[key]
            return None
        
        return data
    
    def set(self, query: str, result: Dict[str, Any], variables: Optional[Dict] = None):
        """Set cached result"""
        key = self._get_cache_key(query, variables)
        self.cache[key] = (result, datetime.now())
    
    def clear(self):
        """Clear all cache entries"""
        self.cache.clear()
    
    def cleanup_expired(self) -> int:
        """Remove expired entries"""
        now = datetime.now()
        expired_keys = [
            key for key, (_, timestamp) in self.cache.items()
            if now - timestamp > self.ttl
        ]
        
        for key in expired_keys:
            del self.cache[key]
        
        return len(expired_keys)
