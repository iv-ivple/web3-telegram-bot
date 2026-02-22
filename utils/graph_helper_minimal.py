# utils/graph_helper.py - Minimal working version
"""
Minimal GraphQL client - enough to make the bot run
For full version with caching, see graph_helper.py in outputs folder
"""
import requests
from typing import Dict, Optional, Any

class GraphClient:
    """Basic GraphQL client without caching"""
    
    def __init__(
        self,
        endpoint: str,
        cache_enabled: bool = False,
        cache_ttl_minutes: int = 5,
        cache_dir: str = "cache",
        rate_limit_per_second: float = 10.0,
        max_retries: int = 3,
        timeout: int = 30
    ):
        """Initialize GraphQL client"""
        self.endpoint = endpoint
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Stats tracking
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
        """Execute GraphQL query"""
        self.stats['total_queries'] += 1
        variables = variables or {}
        
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
            
            response.raise_for_status()
            data = response.json()
            
            # Check for GraphQL errors
            if 'errors' in data:
                error_messages = [e.get('message', str(e)) for e in data['errors']]
                raise Exception(f"GraphQL errors: {'; '.join(error_messages)}")
            
            return data
            
        except Exception as e:
            self.stats['failed_queries'] += 1
            raise Exception(f"Query failed: {str(e)}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics"""
        stats = self.stats.copy()
        
        # Calculate rates
        if stats['total_queries'] > 0:
            stats['success_rate'] = (
                (stats['total_queries'] - stats['failed_queries']) / stats['total_queries']
            ) * 100
        else:
            stats['success_rate'] = 100.0
        
        stats['cache_hit_rate'] = 0.0  # No cache in minimal version
        
        return stats
    
    def clear_cache(self, query: Optional[str] = None, variables: Optional[Dict] = None):
        """Placeholder - no cache in minimal version"""
        pass
    
    def health_check(self) -> bool:
        """Check if endpoint is accessible"""
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
        except:
            return False


class CachedGraphClient(GraphClient):
    """
    Cached version - in minimal version, just inherits from GraphClient
    For full caching support, use the complete version from outputs folder
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize - same as GraphClient for minimal version"""
        super().__init__(*args, **kwargs)
    
    def query_with_custom_ttl(
        self,
        query: str,
        variables: Optional[Dict] = None,
        query_type: str = 'default'
    ) -> Dict[str, Any]:
        """Query with custom TTL - just calls regular query in minimal version"""
        return self.query(query, variables)
