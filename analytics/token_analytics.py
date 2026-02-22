# analytics/token_analytics.py
from utils.graph_helper import GraphClient
from datetime import datetime, timedelta
import pandas as pd
from typing import List, Dict
from collections import defaultdict

class TokenAnalytics:
    def __init__(self, subgraph_url=None, graph_client=None):
        """
        Initialize TokenAnalytics
        
        Args:
            subgraph_url: Subgraph endpoint URL
            graph_client: Pre-configured GraphClient instance
        """
        if graph_client:
            self.client = graph_client
        elif subgraph_url:
            from utils.graph_helper import GraphClient
            self.client = GraphClient(subgraph_url)
        else:
            from utils.graph_helper import GraphClient
            from config import Config
            self.client = GraphClient(Config.UNISWAP_V3_SUBGRAPH)

    def get_token_info(self, token_address: str) -> Dict:
        """
        Get basic token information (symbol, name, decimals)
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
        
        result = self.client.query(query)
        token_data = result['data']['token']
        
        return {
            'symbol': token_data['symbol'],
            'name': token_data['name'],
            'decimals': int(token_data['decimals']),
            'price_eth': float(token_data['derivedETH'])
        }
    
    def get_token_volume_24h(self, token_address: str) -> float:
        """Get 24h trading volume for a token"""
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
        
        result = self.client.query(query)
        swaps = result['data']['swaps']
        
        total_volume = sum(float(swap['amountUSD']) for swap in swaps)
        return total_volume
    
    def get_price_history(self, token_address: str, days: int = 7) -> pd.DataFrame:
        """
        Get historical price data for a token
        
        Args:
            token_address: The token contract address
            days: Number of days of history to fetch (default: 7)
            
        Returns:
            DataFrame with columns: timestamp, date, price_usd, volume_usd
        """
        timestamp_start = int((datetime.now() - timedelta(days=days)).timestamp())
        
        # Query token day data which contains daily OHLC and volume
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
            result = self.client.query(query)
            day_data = result['data']['tokenDayDatas']
            
            if not day_data:
                # If no day data available, try to get current price from pools
                return self._get_current_price_fallback(token_address)
            
            # Convert to DataFrame
            df = pd.DataFrame(day_data)
            
            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['date'], unit='s')
            df['date'] = df['timestamp'].dt.date
            
            # Convert price and volume to float
            df['price_usd'] = df['priceUSD'].astype(float)
            df['volume_usd'] = df['volumeUSD'].astype(float)
            df['open'] = df['open'].astype(float)
            df['high'] = df['high'].astype(float)
            df['low'] = df['low'].astype(float)
            df['close'] = df['close'].astype(float)
            
            # Sort by date ascending
            df = df.sort_values('timestamp')
            
            # Select relevant columns
            df = df[['timestamp', 'date', 'price_usd', 'volume_usd', 'open', 'high', 'low', 'close']]
            
            return df
            
        except Exception as e:
            print(f"Error fetching price history: {e}")
            return pd.DataFrame()
    
    def _get_current_price_fallback(self, token_address: str) -> pd.DataFrame:
        """
        Fallback method to get current price from pool data if no historical data exists
        
        Args:
            token_address: The token contract address
            
        Returns:
            DataFrame with current price data
        """
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
        
        Args:
            token_address: The token contract address
            limit: Number of top traders to return (default: 10)
            
        Returns:
            List of dicts containing trader info: address, total_volume_usd, trade_count, 
            buy_volume_usd, sell_volume_usd
        """
        # We need to query swaps and aggregate by origin (trader address)
        # Note: This queries recent swaps (last 7 days) due to potential data size
        timestamp_7d_ago = int((datetime.now() - timedelta(days=7)).timestamp())
        
        # Query swaps where the token is either token0 or token1
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
            
            # Aggregate by trader
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
                
                # Determine if buy or sell based on token position
                token0_id = swap['token0']['id'].lower()
                is_token0 = token0_id == token_address.lower()
                
                amount0 = float(swap['amount0'])
                amount1 = float(swap['amount1'])
                
                # If token is token0 and amount0 is positive, it's a sell
                # If token is token0 and amount0 is negative, it's a buy
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
            
            # Convert to list and sort by total volume
            top_traders = []
            for address, stats in trader_stats.items():
                top_traders.append({
                    'address': address,
                    'total_volume_usd': round(stats['total_volume_usd'], 2),
                    'trade_count': stats['trade_count'],
                    'buy_volume_usd': round(stats['buy_volume_usd'], 2),
                    'sell_volume_usd': round(stats['sell_volume_usd'], 2)
                })
            
            # Sort by total volume and return top N
            top_traders.sort(key=lambda x: x['total_volume_usd'], reverse=True)
            
            return top_traders[:limit]
            
        except Exception as e:
            print(f"Error fetching top traders: {e}")
            return []
    
    def get_trader_pnl(self, trader_address: str, token_address: str) -> Dict:
        """
        Calculate approximate PnL for a specific trader on a token
        
        Args:
            trader_address: The trader's wallet address
            token_address: The token contract address
            
        Returns:
            Dict with pnl_usd, total_bought, total_sold, avg_buy_price, avg_sell_price
        """
        timestamp_30d_ago = int((datetime.now() - timedelta(days=30)).timestamp())
        
        query = """
        {
          swaps(
            first: 1000,
            where: {
              origin: "%s",
              timestamp_gte: %d,
              or: [
                { token0: "%s" },
                { token1: "%s" }
              ]
            }
          ) {
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
        """ % (trader_address.lower(), timestamp_30d_ago, 
               token_address.lower(), token_address.lower())
        
        try:
            result = self.client.query(query)
            swaps = result['data']['swaps']
            
            total_bought_usd = 0.0
            total_sold_usd = 0.0
            
            for swap in swaps:
                volume = float(swap['amountUSD'])
                token0_id = swap['token0']['id'].lower()
                is_token0 = token0_id == token_address.lower()
                
                amount0 = float(swap['amount0'])
                
                if is_token0:
                    if amount0 > 0:
                        total_sold_usd += volume
                    else:
                        total_bought_usd += volume
                else:
                    amount1 = float(swap['amount1'])
                    if amount1 > 0:
                        total_sold_usd += volume
                    else:
                        total_bought_usd += volume
            
            pnl_usd = total_sold_usd - total_bought_usd
            
            return {
                'pnl_usd': round(pnl_usd, 2),
                'total_bought_usd': round(total_bought_usd, 2),
                'total_sold_usd': round(total_sold_usd, 2),
                'trade_count': len(swaps)
            }
            
        except Exception as e:
            print(f"Error calculating trader PnL: {e}")
            return {
                'pnl_usd': 0.0,
                'total_bought_usd': 0.0,
                'total_sold_usd': 0.0,
                'trade_count': 0
            }
