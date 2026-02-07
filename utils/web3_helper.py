"""
Web3 utility functions for blockchain interactions.
Leverages your previous web3.py experience from Weeks 2-5.
"""
import requests
from web3 import Web3
from config import Config

class Web3Helper:
    """Helper class for Web3 operations."""
    
    def __init__(self):
        """Initialize Web3 connection."""
        self.w3 = Web3(Web3.HTTPProvider(Config.RPC_URL))
        if not self.w3.is_connected():
            raise ConnectionError("Failed to connect to Ethereum node")
    
    def get_eth_balance(self, address: str) -> float:
        """
        Get ETH balance for an address.
        
        Args:
            address: Ethereum address (0x...)
            
        Returns:
            Balance in ETH (float)
        """
        try:
            # Convert to checksum address
            checksum_address = self.w3.to_checksum_address(address)
            # Get balance in Wei
            balance_wei = self.w3.eth.get_balance(checksum_address)
            # Convert to ETH
            balance_eth = self.w3.from_wei(balance_wei, 'ether')
            return float(balance_eth)
        except Exception as e:
            raise ValueError(f"Error fetching balance: {str(e)}")
    
    def get_gas_prices(self) -> dict:
        """
        Get current gas prices in Gwei.
        
        Returns:
            Dict with slow, average, fast gas prices
        """
        try:
            # Get latest base fee
            latest_block = self.w3.eth.get_block('latest')
            base_fee = latest_block.get('baseFeePerGas', 0)
            
            # Get suggested priority fee
            max_priority_fee = self.w3.eth.max_priority_fee
            
            # Calculate gas prices for different speeds
            # Slow: base + (priority fee * 0.5) - cheaper, slower
            # Average: base + suggested priority - normal speed
            # Fast: base + (priority fee * 2.0) - more expensive, faster
            
            slow = self.w3.from_wei(base_fee + int(max_priority_fee * 0.5), 'gwei')
            average = self.w3.from_wei(base_fee + max_priority_fee, 'gwei')
            fast = self.w3.from_wei(base_fee + int(max_priority_fee * 2.0), 'gwei')
            
            return {
                'slow': float(slow),
                'average': float(average),
                'fast': float(fast),
                'base_fee': float(self.w3.from_wei(base_fee, 'gwei'))
            }
        except Exception as e:
            raise ValueError(f"Error fetching gas prices: {str(e)}")
    
    def get_token_price(self, symbol: str) -> dict:
        """
        Get token price from CoinGecko API.
        
        Args:
            symbol: Token symbol (ETH, BTC, etc.)
            
        Returns:
            Dict with price data
        """
        # Map common symbols to CoinGecko IDs
        symbol_map = {
            'ETH': 'ethereum',
            'BTC': 'bitcoin',
            'USDC': 'usd-coin',
            'USDT': 'tether',
            'DAI': 'dai',
            'WETH': 'weth',
            'UNI': 'uniswap',
            'LINK': 'chainlink'
        }
        
        symbol_upper = symbol.upper()
        coin_id = symbol_map.get(symbol_upper, symbol.lower())
        
        try:
            url = f"https://api.coingecko.com/api/v3/simple/price"
            params = {
                'ids': coin_id,
                'vs_currencies': 'usd',
                'include_24hr_change': 'true',
                'include_market_cap': 'true'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if coin_id not in data:
                raise ValueError(f"Token '{symbol}' not found")
            
            token_data = data[coin_id]
            
            return {
                'symbol': symbol_upper,
                'price': token_data['usd'],
                'change_24h': token_data.get('usd_24h_change', 0),
                'market_cap': token_data.get('usd_market_cap', 0)
            }
            
        except requests.RequestException as e:
            raise ValueError(f"Error fetching price data: {str(e)}")
    
    def is_valid_address(self, address: str) -> bool:
        """Check if address is valid Ethereum address."""
        return self.w3.is_address(address)
    
    def get_latest_block(self) -> int:
        """Get latest block number."""
        return self.w3.eth.block_number

# Global instance
web3_helper = Web3Helper()
