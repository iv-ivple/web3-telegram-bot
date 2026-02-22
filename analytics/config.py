from dotenv import load_dotenv
import os

load_dotenv()

# The Graph endpoints
UNISWAP_V3_SUBGRAPH = "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3"
AAVE_V3_SUBGRAPH = "https://api.thegraph.com/subgraphs/name/aave/protocol-v3"

# Your RPC for real-time data
RPC_URL = os.getenv("RPC_URL")
