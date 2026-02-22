# utils/graph_helper.py
"""
Enhanced GraphQL client with caching, rate limiting, and error handling
"""
import requests
import time
import logging
from typing import Dict, Optional, Any
from datetime import datetime, timedelta

from utils.cache_helper import QueryCache

logger = logging.getLogger(__name__)


class GraphClientError(Exception):
    """Custom exception for GraphClient errors"""
    pass


class RateLimitError(GraphClientError):
    """Raised when rate limit is exceeded"""
    pass


class GraphClient:
    """
    GraphQL client with built-in caching, rate limiting, and retry logic
    """
    
    def __init__(
        self,
        endpoint: str,
        cache_enabled: bool = True,
        cache_ttl_minutes: int = 5,
        cache_dir: str = "cache",
        rate_limit_per_second: float = 10.0,
        max_retries: int = 3,
        timeout: int = 30
    ):
        """
        Initialize GraphClient
        
        Args:
            endpoint: GraphQL endpoint URL
            cache_enabled: Enable query caching
            cache_ttl_minutes: Cache time-to-live in minutes
            cache_dir: Directory for cache files
            rate_limit_per_second: Maximum requests per second
            max_retries: Maximum retry attempts for failed requests
            timeout: Request timeout in seconds
        """
        self.endpoint = endpoint
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Caching
        self.cache_enabled = cache_enabled
        if cache_enabled:
            self.cache = QueryCache(cache_dir=cache_dir, ttl_minutes=cache_ttl_minutes)
        else:
            self.cache = None
        
        # Rate limiting
        self.rate_limit_per_second = rate_limit_per_second
        self.min_request_interval = 1.0 / rate_limit_per_second if rate_limit_per_second > 0 else 0
        self.last_request_time = 0
        
        # Statistics
        self.stats = {
            'total_queries': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'failed_queries': 0,
            'retry_count': 0
        }
    
    def query(
        self,
        query: str,
        variables: Optional[Dict] = None,
        use_cache: bool = True,
        retry_on_error: bool = True
    ) -> Dict[str, Any]:
        """
        Execute GraphQL query with caching and retry logic
        
        Args:
            query: GraphQL query string
            variables: Query variables
            use_cache: Whether to use cache for this query
            retry_on_error: Whether to retry on failure
            
        Returns:
            Query result as dictionary
            
        Raises:
            GraphClientError: On query failure after retries
        """
        self.stats['total_queries'] += 1
        variables = variables or {}
        
        # Check cache first
        if self.cache_enabled and use_cache:
            cached_result = self.cache.get(query, variables)
            if cached_result is not None:
                self.stats['cache_hits'] += 1
                logger.debug(f"Cache hit for query: {query[:50]}...")
                return cached_result
            self.stats['cache_misses'] += 1
        
        # Execute query with retry logic
        max_attempts = self.max_retries if retry_on_error else 1
        last_error = None
        
        for attempt in range(max_attempts):
            try:
                # Rate limiting
                self._enforce_rate_limit()
                
                # Make request
                result = self._execute_request(query, variables)
                
                # Cache successful result
                if self.cache_enabled and use_cache and result:
                    self.cache.set(query, result, variables)
                
                return result
                
            except RateLimitError:
                # Don't retry rate limit errors, just wait
                raise
                
            except Exception as e:
                last_error = e
                self.stats['retry_count'] += 1
                
                if attempt < max_attempts - 1:
                    # Exponential backoff
                    wait_time = (2 ** attempt) * 1.0
                    logger.warning(
                        f"Query failed (attempt {attempt + 1}/{max_attempts}), "
                        f"retrying in {wait_time}s: {str(e)}"
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(f"Query failed after {max_attempts} attempts: {str(e)}")
        
        # All retries failed
        self.stats['failed_queries'] += 1
        raise GraphClientError(f"Query failed after {max_attempts} attempts: {str(last_error)}")
    
    def _execute_request(self, query: str, variables: Dict) -> Dict[str, Any]:
        """
        Execute the actual HTTP request
        
        Args:
            query: GraphQL query string
            variables: Query variables
            
        Returns:
            Response data
            
        Raises:
            GraphClientError: On request failure
        """
        headers = {
            'Content-Type': 'application/json',
        }
        
        payload = {
            'query': query,
            'variables': variables
        }
        
        try:
            response = requests.post(
                self.endpoint,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            
            # Check for HTTP errors
            if response.status_code == 429:
                raise RateLimitError("Rate limit exceeded")
            
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            
            # Check for GraphQL errors
            if 'errors' in data:
                error_messages = [e.get('message', str(e)) for e in data['errors']]
                raise GraphClientError(f"GraphQL errors: {'; '.join(error_messages)}")
            
            return data
            
        except requests.exceptions.Timeout:
            raise GraphClientError(f"Request timeout after {self.timeout}s")
        except requests.exceptions.RequestException as e:
            raise GraphClientError(f"Request failed: {str(e)}")
        except ValueError as e:
            raise GraphClientError(f"Invalid JSON response: {str(e)}")
    
    def _enforce_rate_limit(self):
        """Enforce rate limiting between requests"""
        if self.min_request_interval > 0:
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            
            if time_since_last < self.min_request_interval:
                wait_time = self.min_request_interval - time_since_last
                logger.debug(f"Rate limiting: waiting {wait_time:.3f}s")
                time.sleep(wait_time)
            
            self.last_request_time = time.time()
    
    def clear_cache(self, query: Optional[str] = None, variables: Optional[Dict] = None):
        """
        Clear cache
        
        Args:
            query: Specific query to clear (None = clear all)
            variables: Query variables for specific query
        """
        if not self.cache_enabled:
            logger.warning("Cache is not enabled")
            return
        
        if query is None:
            # Clear all cache
            import shutil
            shutil.rmtree(self.cache.cache_dir)
            self.cache.cache_dir.mkdir(exist_ok=True)
            logger.info("Cleared all cache")
        else:
            # Clear specific query
            cache_key = self.cache._get_cache_key(query, variables or {})
            cache_file = self.cache.cache_dir / f"{cache_key}.json"
            if cache_file.exists():
                cache_file.unlink()
                logger.info(f"Cleared cache for query: {query[:50]}...")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get client statistics
        
        Returns:
            Dictionary with statistics
        """
        stats = self.stats.copy()
        
        # Calculate cache hit rate
        total_cacheable = stats['cache_hits'] + stats['cache_misses']
        if total_cacheable > 0:
            stats['cache_hit_rate'] = (stats['cache_hits'] / total_cacheable) * 100
        else:
            stats['cache_hit_rate'] = 0.0
        
        # Calculate success rate
        if stats['total_queries'] > 0:
            stats['success_rate'] = (
                (stats['total_queries'] - stats['failed_queries']) / stats['total_queries']
            ) * 100
        else:
            stats['success_rate'] = 100.0
        
        return stats
    
    def reset_stats(self):
        """Reset statistics counters"""
        self.stats = {
            'total_queries': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'failed_queries': 0,
            'retry_count': 0
        }
        logger.info("Statistics reset")
    
    def batch_query(
        self,
        queries: list[tuple[str, Optional[Dict]]],
        use_cache: bool = True,
        delay_between: float = 0.0
    ) -> list[Dict[str, Any]]:
        """
        Execute multiple queries in batch
        
        Args:
            queries: List of (query, variables) tuples
            use_cache: Whether to use cache
            delay_between: Additional delay between queries (seconds)
            
        Returns:
            List of results in same order
        """
        results = []
        
        for i, (query, variables) in enumerate(queries):
            logger.info(f"Executing batch query {i + 1}/{len(queries)}")
            
            try:
                result = self.query(query, variables, use_cache=use_cache)
                results.append(result)
            except Exception as e:
                logger.error(f"Batch query {i + 1} failed: {str(e)}")
                results.append({'error': str(e)})
            
            # Additional delay if specified
            if delay_between > 0 and i < len(queries) - 1:
                time.sleep(delay_between)
        
        return results
    
    def health_check(self) -> bool:
        """
        Check if the GraphQL endpoint is accessible
        
        Returns:
            True if healthy, False otherwise
        """
        test_query = """
        {
            __schema {
                queryType {
                    name
                }
            }
        }
        """
        
        try:
            result = self.query(test_query, use_cache=False, retry_on_error=False)
            return 'data' in result
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False


class CachedGraphClient(GraphClient):
    """
    GraphClient with aggressive caching for specific query types
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize with longer default cache TTL"""
        if 'cache_ttl_minutes' not in kwargs:
            kwargs['cache_ttl_minutes'] = 15  # 15 minutes default
        super().__init__(*args, **kwargs)
        
        # Custom TTLs for different query types
        self.custom_ttls = {
            'token_info': timedelta(hours=24),      # Token info changes rarely
            'historical': timedelta(hours=6),        # Historical data is immutable
            'current_price': timedelta(minutes=1),   # Prices change quickly
            'volume': timedelta(minutes=5),          # Volume updates moderately
        }
    
    def query_with_custom_ttl(
        self,
        query: str,
        variables: Optional[Dict] = None,
        query_type: str = 'default'
    ) -> Dict[str, Any]:
        """
        Query with custom TTL based on query type
        
        Args:
            query: GraphQL query
            variables: Query variables
            query_type: Type of query for TTL selection
            
        Returns:
            Query result
        """
        # Temporarily adjust TTL if custom type specified
        original_ttl = self.cache.ttl if self.cache else None
        
        if self.cache and query_type in self.custom_ttls:
            self.cache.ttl = self.custom_ttls[query_type]
        
        try:
            result = self.query(query, variables)
            return result
        finally:
            # Restore original TTL
            if self.cache and original_ttl:
                self.cache.ttl = original_ttl
