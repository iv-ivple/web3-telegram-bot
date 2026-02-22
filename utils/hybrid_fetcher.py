# utils/hybrid_fetcher.py
from web3 import Web3
from utils.graph_helper import GraphClient
from typing import List, Dict
import time

class HybridDataFetcher:
    def __init__(self, subgraph_url: str, rpc_url: str):
        self.graph = GraphClient(subgraph_url)
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
    
    def get_subgraph_latest_block(self) -> int:
        """Get the latest block indexed by subgraph"""
        query = """
        {
          _meta {
            block {
              number
            }
          }
        }
        """
        result = self.graph.query(query)
        return result['data']['_meta']['block']['number']
    
    def get_transfers_hybrid(self, token_address: str, 
                            from_block: int, to_block: int = None) -> List[Dict]:
        """
        Get transfers combining indexed + real-time data
        """
        latest_indexed = self.get_subgraph_latest_block()
        current_block = self.w3.eth.block_number
        
        if to_block is None:
            to_block = current_block
        
        results = []
        
        # Part 1: Get indexed data from The Graph
        if from_block < latest_indexed:
            indexed_end = min(to_block, latest_indexed)
            query = """
            {
              transfers(
                where: {
                  blockNumber_gte: %d,
                  blockNumber_lte: %d,
                  token: "%s"
                }
                orderBy: blockNumber
              ) {
                from
                to
                amount
                blockNumber
                timestamp
              }
            }
            """ % (from_block, indexed_end, token_address.lower())
            
            indexed_data = self.graph.query(query)
            results.extend(indexed_data['data']['transfers'])
        
        # Part 2: Get recent data from RPC
        if to_block > latest_indexed:
            rpc_start = max(from_block, latest_indexed + 1)
            # Fetch events using web3.py
            # (Implementation depends on your existing code)
            pass
        
        return results
