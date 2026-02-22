# analytics/token_analytics_cached.py
"""
TokenAnalytics with integrated caching support
"""
from utils.graph_helper import GraphClient, CachedGraphClient
from datetime import datetime, timedelta
import pandas as pd
from typing import List, Dict, Optional

class TokenAnalytics:
    """
    Token analytics with automatic caching and rate limiting
    """
    
    def __init__(
        self,
        subgraph_url: Optional[str] = None,
        graph_client: Optional[GraphClient] = None,
        enable_cache: bool = True,
        cache_ttl_minutes: int = 5
    ):
        """
        Initialize TokenAnalytics
        
        Args:
            subgraph_url: Subgraph endpoint URL (if graph_client not provided)
            graph_client: Pre-configured GraphClient instance
            enable_cache: Enable caching (only if creating new client)
            cache_ttl_minutes: Cache TTL (only if creating new client)
        """
        if graph_client:
            # Use provided client
            self.client = graph_client
        elif subgraph_url:
            # Create new cached client
            if enable_cache:
                self.client = CachedGraphClient(
                    endpoint=subgraph_url,
                    cache_enabled=True,
                    cache_ttl_minutes=cache_ttl_minutes,
                    rate_limit_per_second=10.0
                )
            else:
                self.client = GraphClient(
                    endpoint=subgraph_url,
                    cache_enabled=False
                )
        else:
            raise ValueError("Must provide either subgraph_url or graph_client")
    
    def get_token_volume_24h(self, token_address: str) -> float:
        """
        Get 24h trading volume for a token
        
        Uses cache with 5-minute TTL for volume queries
        """
        timestamp_24h_ago = int((datetime.now() - timedelta(days=1)).timestamp())
        
        query = """
        {
          swaps(
            where: {
              timestamp_gte: %d,
              token0: "%s"
            }
          ) {
            amountUSD
          }
        }
        """ % (timestamp_24h_ago, token_address.lower())
        
        # Use custom TTL if CachedGraphClient
        if isinstance(self.client, CachedGraphClient):
            result = self.client.query_with_custom_ttl(query, query_type='volume')
        else:
            result = self.client.query(query)
        
        swaps = result['data']['swaps']
        total_volume = sum(float(swap['amountUSD']) for swap in swaps)
        return total_volume
    
    def get_token_info(self, token_address: str) -> Dict:
        """
        Get basic token information (symbol, name, decimals)
        
        This data rarely changes, so cache for 24 hours
        """
        query = """
        {
          token(id: "%s") {
            symbol
            name
            decimals
            derivedETH
          }
        }
        """ % token_address.lower()
        
        # Use long cache for token info
        if isinstance(self.client, CachedGraphClient):
            result = self.client.query_with_custom_ttl(query, query_type='token_info')
        else:
            result = self.client.query(query)
        
        token_data = result['data']['token']
        
        return {
            'symbol': token_data['symbol'],
            'name': token_data['name'],
            'decimals': int(token_data['decimals']),
            'price_eth': float(token_data['derivedETH'])
        }
    
    def get_price_history(self, token_address: str, days: int = 7) -> pd.DataFrame:
        """
        Get historical price data for a token
        
        Historical data is immutable, so cache for 6 hours
        """
        timestamp_start = int((datetime.now() - timedelta(days=days)).timestamp())
        
        query = """
        {
          tokenDayDatas(
            first: %d,
            orderBy: date,
            orderDirection: desc,
            where: {
              token: "%s",
              date_gte: %d
            }
          ) {
            date
            priceUSD
            volumeUSD
            open
            high
            low
            close
          }
        }
        """ % (days, token_address.lower(), timestamp_start)
        
        try:
            # Use historical cache TTL
            if isinstance(self.client, CachedGraphClient):
                result = self.client.query_with_custom_ttl(query, query_type='historical')
            else:
                result = self.client.query(query)
            
            day_data = result['data']['tokenDayDatas']
            
            if not day_data:
                return self._get_current_price_fallback(token_address)
            
            df = pd.DataFrame(day_data)
            df['timestamp'] = pd.to_datetime(df['date'], unit='s')
            df['date'] = df['timestamp'].dt.date
            df['price_usd'] = df['priceUSD'].astype(float)
            df['volume_usd'] = df['volumeUSD'].astype(float)
            df['open'] = df['open'].astype(float)
            df['high'] = df['high'].astype(float)
            df['low'] = df['low'].astype(float)
            df['close'] = df['close'].astype(float)
            df = df.sort_values('timestamp')
            df = df[['timestamp', 'date', 'price_usd', 'volume_usd', 'open', 'high', 'low', 'close']]
            
            return df
            
        except Exception as e:
            print(f"Error fetching price history: {e}")
            return pd.DataFrame()
    
    def _get_current_price_fallback(self, token_address: str) -> pd.DataFrame:
        """Fallback method to get current price"""
        query = """
        {
          token(id: "%s") {
            derivedETH
            tokenDayData(first: 1, orderBy: date, orderDirection: desc) {
              priceUSD
            }
          }
        }
        """ % token_address.lower()
        
        try:
            # Current price uses short cache
            if isinstance(self.client, CachedGraphClient):
                result = self.client.query_with_custom_ttl(query, query_type='current_price')
            else:
                result = self.client.query(query)
            
            token_data = result['data']['token']
            
            if token_data and token_data.get('tokenDayData'):
                price = float(token_data['tokenDayData'][0]['priceUSD'])
                now = datetime.now()
                
                return pd.DataFrame([{
                    'timestamp': now,
                    'date': now.date(),
                    'price_usd': price,
                    'volume_usd': 0.0,
                    'open': price,
                    'high': price,
                    'low': price,
                    'close': price
                }])
        except Exception as e:
            print(f"Error in fallback price fetch: {e}")
        
        return pd.DataFrame()
    
    def get_top_traders(self, token_address: str, limit: int = 10) -> List[Dict]:
        """
        Get top traders for a token by total volume traded
        
        Uses default cache TTL
        """
        timestamp_7d_ago = int((datetime.now() - timedelta(days=7)).timestamp())
        
        query = """
        {
          swaps(
            first: 1000,
            orderBy: timestamp,
            orderDirection: desc,
            where: {
              timestamp_gte: %d,
              or: [
                { token0: "%s" },
                { token1: "%s" }
              ]
            }
          ) {
            origin
            amountUSD
            amount0
            amount1
            token0 {
              id
            }
            token1 {
              id
            }
          }
        }
        """ % (timestamp_7d_ago, token_address.lower(), token_address.lower())
        
        try:
            result = self.client.query(query)
            swaps = result['data']['swaps']
            
            if not swaps:
                return []
            
            from collections import defaultdict
            trader_stats = defaultdict(lambda: {
                'total_volume_usd': 0.0,
                'trade_count': 0,
                'buy_volume_usd': 0.0,
                'sell_volume_usd': 0.0
            })
            
            for swap in swaps:
                trader = swap['origin']
                volume = float(swap['amountUSD'])
                
                trader_stats[trader]['total_volume_usd'] += volume
                trader_stats[trader]['trade_count'] += 1
                
                token0_id = swap['token0']['id'].lower()
                is_token0 = token0_id == token_address.lower()
                amount0 = float(swap['amount0'])
                amount1 = float(swap['amount1'])
                
                if is_token0:
                    if amount0 > 0:
                        trader_stats[trader]['sell_volume_usd'] += volume
                    else:
                        trader_stats[trader]['buy_volume_usd'] += volume
                else:
                    if amount1 > 0:
                        trader_stats[trader]['sell_volume_usd'] += volume
                    else:
                        trader_stats[trader]['buy_volume_usd'] += volume
            
            top_traders = []
            for address, stats in trader_stats.items():
                top_traders.append({
                    'address': address,
                    'total_volume_usd': round(stats['total_volume_usd'], 2),
                    'trade_count': stats['trade_count'],
                    'buy_volume_usd': round(stats['buy_volume_usd'], 2),
                    'sell_volume_usd': round(stats['sell_volume_usd'], 2)
                })
            
            top_traders.sort(key=lambda x: x['total_volume_usd'], reverse=True)
            return top_traders[:limit]
            
        except Exception as e:
            print(f"Error fetching top traders: {e}")
            return []
    
    def get_client_stats(self) -> Dict:
        """
        Get GraphClient statistics
        
        Returns:
            Dictionary with client and cache statistics
        """
        stats = self.client.get_stats()
        
        if hasattr(self.client, 'cache') and self.client.cache:
            cache_stats = self.client.cache.get_stats()
            stats['cache'] = cache_stats
        
        return stats
    
    def clear_cache(self):
        """Clear all cached queries"""
        if hasattr(self.client, 'clear_cache'):
            self.client.clear_cache()
            print("Cache cleared")
        else:
            print("Client does not support caching")


# Example usage
if __name__ == "__main__":
    from utils.graph_helper import CachedGraphClient
    
    UNISWAP_V3_SUBGRAPH = "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3"
    
    # Method 1: Let TokenAnalytics create the client
    print("Method 1: Auto-create cached client")
    analytics1 = TokenAnalytics(
        subgraph_url=UNISWAP_V3_SUBGRAPH,
        enable_cache=True,
        cache_ttl_minutes=5
    )
    
    # Method 2: Provide custom client
    print("\nMethod 2: Provide custom client")
    custom_client = CachedGraphClient(
        endpoint=UNISWAP_V3_SUBGRAPH,
        cache_enabled=True,
        cache_ttl_minutes=10,
        rate_limit_per_second=5.0
    )
    analytics2 = TokenAnalytics(graph_client=custom_client)
    
    # Test with WETH
    WETH = "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
    
    print("\nFetching token info (will cache for 24h)...")
    info = analytics1.get_token_info(WETH)
    print(f"Token: {info['symbol']} - {info['name']}")
    
    print("\nFetching price history (will cache for 6h)...")
    df = analytics1.get_price_history(WETH, days=7)
    print(f"Got {len(df)} days of data")
    
    print("\nClient statistics:")
    stats = analytics1.get_client_stats()
    print(f"Total queries: {stats['total_queries']}")
    print(f"Cache hit rate: {stats['cache_hit_rate']:.1f}%")
