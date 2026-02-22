# analytics/transfers_analytics.py
"""
Hybrid transfer analytics combining RPC calls and subgraph queries.
Provides comprehensive token transfer tracking.
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from web3 import Web3
from web3.exceptions import Web3Exception
import json
from collections import defaultdict

class TransfersAnalytics:
    """
    Hybrid approach for getting token transfers:
    - RPC: Recent, real-time data directly from blockchain
    - Subgraph: Historical data, faster for large ranges
    """
    
    def __init__(self, rpc_url: str, subgraph_client=None):
        """
        Initialize with RPC endpoint and optional subgraph client
        
        Args:
            rpc_url: Ethereum RPC endpoint (e.g., Infura, Alchemy)
            subgraph_client: Optional GraphClient for historical queries
        """
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.subgraph_client = subgraph_client
        
        # ERC20 Transfer event signature
        # Transfer(address indexed from, address indexed to, uint256 value)
        self.TRANSFER_EVENT_SIGNATURE = self.w3.keccak(text="Transfer(address,address,uint256)").hex()
        
        # Standard ERC20 ABI for transfers
        self.ERC20_ABI = json.loads('''[
            {
                "anonymous": false,
                "inputs": [
                    {"indexed": true, "name": "from", "type": "address"},
                    {"indexed": true, "name": "to", "type": "address"},
                    {"indexed": false, "name": "value", "type": "uint256"}
                ],
                "name": "Transfer",
                "type": "event"
            },
            {
                "constant": true,
                "inputs": [],
                "name": "decimals",
                "outputs": [{"name": "", "type": "uint8"}],
                "type": "function"
            },
            {
                "constant": true,
                "inputs": [],
                "name": "symbol",
                "outputs": [{"name": "", "type": "string"}],
                "type": "function"
            },
            {
                "constant": true,
                "inputs": [],
                "name": "name",
                "outputs": [{"name": "", "type": "string"}],
                "type": "function"
            }
        ]''')
    
    def get_transfers_hybrid(
        self,
        token_address: str,
        wallet_address: Optional[str] = None,
        from_block: Optional[int] = None,
        to_block: Optional[int] = None,
        max_blocks: int = 10000,
        use_subgraph: bool = True
    ) -> List[Dict]:
        """
        Hybrid method to get token transfers using both RPC and subgraph.
        
        Strategy:
        1. For recent data (last ~1000 blocks): Use RPC for real-time accuracy
        2. For historical data: Use subgraph for speed and efficiency
        3. Merge and deduplicate results
        
        Args:
            token_address: Token contract address
            wallet_address: Optional filter for specific wallet
            from_block: Starting block number (default: 1000 blocks ago)
            to_block: Ending block number (default: latest)
            max_blocks: Maximum block range for RPC queries (default: 10000)
            use_subgraph: Whether to use subgraph for historical data
            
        Returns:
            List of transfer events with: from, to, value, block_number, tx_hash, timestamp
        """
        try:
            # Get current block
            current_block = self.w3.eth.block_number
            
            # Set defaults
            if to_block is None:
                to_block = current_block
            if from_block is None:
                from_block = max(0, to_block - 1000)  # Default to last 1000 blocks
            
            # Determine strategy based on block range
            block_range = to_block - from_block
            
            if block_range <= max_blocks:
                # Small range: Use RPC only
                print(f"Using RPC only (range: {block_range} blocks)")
                return self._get_transfers_rpc(
                    token_address, 
                    wallet_address, 
                    from_block, 
                    to_block
                )
            
            elif use_subgraph and self.subgraph_client:
                # Large range: Combine subgraph (historical) + RPC (recent)
                print(f"Using hybrid approach (range: {block_range} blocks)")
                
                # Define cutoff: last 1000 blocks via RPC
                rpc_cutoff = current_block - 1000
                
                # Get historical via subgraph
                historical_transfers = []
                if from_block < rpc_cutoff:
                    print(f"Fetching historical data via subgraph (blocks {from_block} to {rpc_cutoff})")
                    historical_transfers = self._get_transfers_subgraph(
                        token_address,
                        wallet_address,
                        from_block,
                        rpc_cutoff
                    )
                
                # Get recent via RPC
                recent_transfers = []
                if to_block > rpc_cutoff:
                    print(f"Fetching recent data via RPC (blocks {rpc_cutoff} to {to_block})")
                    recent_transfers = self._get_transfers_rpc(
                        token_address,
                        wallet_address,
                        rpc_cutoff,
                        to_block
                    )
                
                # Merge and deduplicate
                all_transfers = self._merge_transfers(historical_transfers, recent_transfers)
                return all_transfers
            
            else:
                # No subgraph available: chunk RPC queries
                print(f"Using chunked RPC queries (range: {block_range} blocks)")
                return self._get_transfers_rpc_chunked(
                    token_address,
                    wallet_address,
                    from_block,
                    to_block,
                    max_blocks
                )
                
        except Exception as e:
            print(f"Error in get_transfers_hybrid: {e}")
            return []
    
    def _get_transfers_rpc(
        self,
        token_address: str,
        wallet_address: Optional[str] = None,
        from_block: int = 0,
        to_block: Optional[int] = None
    ) -> List[Dict]:
        """
        Get transfers directly from RPC using eth_getLogs
        
        Args:
            token_address: Token contract address
            wallet_address: Optional wallet to filter
            from_block: Starting block
            to_block: Ending block
            
        Returns:
            List of transfer events
        """
        try:
            token_address = self.w3.to_checksum_address(token_address)
            
            # Build filter parameters
            filter_params = {
                'fromBlock': from_block,
                'toBlock': to_block or 'latest',
                'address': token_address,
                'topics': [self.TRANSFER_EVENT_SIGNATURE]
            }
            
            # Add wallet filter if specified
            if wallet_address:
                wallet_address = self.w3.to_checksum_address(wallet_address)
                # Pad address to 32 bytes (64 hex chars)
                padded_wallet = '0x' + wallet_address[2:].zfill(64)
                
                # Filter for transfers FROM or TO the wallet
                # Note: We can't filter both in one query, so we'll filter after
                filter_params['topics'].append(None)  # This allows any from/to
            
            # Get logs
            logs = self.w3.eth.get_logs(filter_params)
            
            # Get token info for decimals
            token_contract = self.w3.eth.contract(address=token_address, abi=self.ERC20_ABI)
            try:
                decimals = token_contract.functions.decimals().call()
                symbol = token_contract.functions.symbol().call()
            except:
                decimals = 18
                symbol = "UNKNOWN"
            
            # Parse logs
            transfers = []
            for log in logs:
                try:
                    # Decode transfer event
                    from_addr = self.w3.to_checksum_address('0x' + log['topics'][1].hex()[26:])
                    to_addr = self.w3.to_checksum_address('0x' + log['topics'][2].hex()[26:])
                    value_raw = int(log['data'].hex(), 16)
                    value = value_raw / (10 ** decimals)
                    
                    # Filter by wallet if specified
                    if wallet_address and wallet_address not in [from_addr, to_addr]:
                        continue
                    
                    # Get block timestamp
                    block = self.w3.eth.get_block(log['blockNumber'])
                    timestamp = block['timestamp']
                    
                    transfer = {
                        'from': from_addr,
                        'to': to_addr,
                        'value': value,
                        'value_raw': value_raw,
                        'decimals': decimals,
                        'symbol': symbol,
                        'block_number': log['blockNumber'],
                        'tx_hash': log['transactionHash'].hex(),
                        'log_index': log['logIndex'],
                        'timestamp': timestamp,
                        'datetime': datetime.fromtimestamp(timestamp).isoformat()
                    }
                    
                    transfers.append(transfer)
                    
                except Exception as e:
                    print(f"Error parsing log: {e}")
                    continue
            
            return transfers
            
        except Exception as e:
            print(f"Error in RPC transfer query: {e}")
            return []
    
    def _get_transfers_rpc_chunked(
        self,
        token_address: str,
        wallet_address: Optional[str],
        from_block: int,
        to_block: int,
        chunk_size: int = 10000
    ) -> List[Dict]:
        """
        Get transfers using chunked RPC queries for large block ranges
        
        Args:
            token_address: Token contract address
            wallet_address: Optional wallet filter
            from_block: Starting block
            to_block: Ending block
            chunk_size: Size of each chunk
            
        Returns:
            Combined list of transfers
        """
        all_transfers = []
        current_from = from_block
        
        while current_from < to_block:
            current_to = min(current_from + chunk_size, to_block)
            
            print(f"Fetching blocks {current_from} to {current_to}...")
            chunk_transfers = self._get_transfers_rpc(
                token_address,
                wallet_address,
                current_from,
                current_to
            )
            
            all_transfers.extend(chunk_transfers)
            current_from = current_to + 1
        
        return all_transfers
    
    def _get_transfers_subgraph(
        self,
        token_address: str,
        wallet_address: Optional[str],
        from_block: int,
        to_block: int
    ) -> List[Dict]:
        """
        Get transfers from subgraph (e.g., Uniswap, custom indexer)
        
        Args:
            token_address: Token contract address
            wallet_address: Optional wallet filter
            from_block: Starting block
            to_block: Ending block
            
        Returns:
            List of transfer events
        """
        if not self.subgraph_client:
            return []
        
        try:
            # Build GraphQL query
            wallet_filter = ""
            if wallet_address:
                wallet_filter = f'''
                or: [
                    {{ from: "{wallet_address.lower()}" }},
                    {{ to: "{wallet_address.lower()}" }}
                ]
                '''
            
            query = f"""
            {{
              transfers(
                first: 1000,
                orderBy: blockNumber,
                orderDirection: asc,
                where: {{
                  token: "{token_address.lower()}",
                  blockNumber_gte: {from_block},
                  blockNumber_lte: {to_block}
                  {wallet_filter}
                }}
              ) {{
                id
                from
                to
                value
                blockNumber
                timestamp
                transaction {{
                  id
                }}
              }}
            }}
            """
            
            result = self.subgraph_client.query(query)
            
            if 'data' not in result or 'transfers' not in result['data']:
                return []
            
            # Convert to standard format
            transfers = []
            for t in result['data']['transfers']:
                transfers.append({
                    'from': self.w3.to_checksum_address(t['from']),
                    'to': self.w3.to_checksum_address(t['to']),
                    'value': float(t['value']),
                    'value_raw': int(float(t['value']) * 1e18),  # Approximate
                    'decimals': 18,  # Default, should fetch from contract
                    'symbol': 'TOKEN',
                    'block_number': int(t['blockNumber']),
                    'tx_hash': t['transaction']['id'],
                    'timestamp': int(t['timestamp']),
                    'datetime': datetime.fromtimestamp(int(t['timestamp'])).isoformat(),
                    'source': 'subgraph'
                })
            
            return transfers
            
        except Exception as e:
            print(f"Error in subgraph transfer query: {e}")
            return []
    
    def _merge_transfers(
        self,
        historical: List[Dict],
        recent: List[Dict]
    ) -> List[Dict]:
        """
        Merge and deduplicate transfer lists from different sources
        
        Args:
            historical: Transfers from subgraph
            recent: Transfers from RPC
            
        Returns:
            Deduplicated and sorted list
        """
        # Use tx_hash + log_index as unique key
        seen = set()
        merged = []
        
        for transfer in historical + recent:
            key = f"{transfer['tx_hash']}_{transfer.get('log_index', 0)}"
            if key not in seen:
                seen.add(key)
                merged.append(transfer)
        
        # Sort by block number and log index
        merged.sort(key=lambda x: (x['block_number'], x.get('log_index', 0)))
        
        return merged
    
    def analyze_transfers(self, transfers: List[Dict], wallet_address: str) -> Dict:
        """
        Analyze transfers for a specific wallet
        
        Args:
            transfers: List of transfer events
            wallet_address: Wallet to analyze
            
        Returns:
            Dict with statistics
        """
        wallet_address = self.w3.to_checksum_address(wallet_address)
        
        stats = {
            'total_transfers': 0,
            'received_count': 0,
            'sent_count': 0,
            'total_received': 0.0,
            'total_sent': 0.0,
            'net_change': 0.0,
            'unique_counterparties': set(),
            'first_transfer': None,
            'last_transfer': None
        }
        
        for transfer in transfers:
            if transfer['to'] == wallet_address:
                # Received
                stats['received_count'] += 1
                stats['total_received'] += transfer['value']
                stats['unique_counterparties'].add(transfer['from'])
                
            elif transfer['from'] == wallet_address:
                # Sent
                stats['sent_count'] += 1
                stats['total_sent'] += transfer['value']
                stats['unique_counterparties'].add(transfer['to'])
            
            stats['total_transfers'] += 1
            
            # Track first and last
            if stats['first_transfer'] is None:
                stats['first_transfer'] = transfer
            stats['last_transfer'] = transfer
        
        stats['net_change'] = stats['total_received'] - stats['total_sent']
        stats['unique_counterparties'] = len(stats['unique_counterparties'])
        
        return stats
    
    def get_transfer_summary(
        self,
        token_address: str,
        wallet_address: str,
        days: int = 30
    ) -> Dict:
        """
        Get a complete transfer summary for a wallet
        
        Args:
            token_address: Token contract address
            wallet_address: Wallet to analyze
            days: Number of days to analyze
            
        Returns:
            Complete summary with transfers and statistics
        """
        # Calculate block range (approximate: 1 block per 12 seconds)
        blocks_per_day = int(24 * 60 * 60 / 12)
        from_block = self.w3.eth.block_number - (blocks_per_day * days)
        
        # Get transfers
        transfers = self.get_transfers_hybrid(
            token_address=token_address,
            wallet_address=wallet_address,
            from_block=from_block
        )
        
        # Analyze
        stats = self.analyze_transfers(transfers, wallet_address)
        
        return {
            'transfers': transfers,
            'stats': stats,
            'period_days': days,
            'total_transfers': len(transfers)
        }
