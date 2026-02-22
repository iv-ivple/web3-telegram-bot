from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    """Bot configuration"""
    
    # Telegram Bot
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "your_bot_token_here")
    
    # The Graph endpoints
    UNISWAP_V3_SUBGRAPH = "https://gateway.thegraph.com/api/e37129ba152b5b20e957ea72fc445988/subgraphs/id/5zvR82QoaXYFyDEKLZ9t6v9adgnptxYpKpSbxtgVENFV"
    AAVE_V3_SUBGRAPH = "https://api.thegraph.com/subgraphs/name/aave/protocol-v3"
    
    # Your RPC for real-time data
    RPC_URL = os.getenv("RPC_URL", "https://mainnet.infura.io/v3/YOUR_PROJECT_ID")
    
    # Database path
    DATABASE_PATH = os.getenv("DATABASE_PATH", "bot_data.db")
    
    @classmethod
    def get_token_address(cls, symbol: str) -> str:
        """Get common token addresses"""
        COMMON_TOKENS = {
            'WETH': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
            'USDC': '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',
            'USDT': '0xdAC17F958D2ee523a2206206994597C13D831ec7',
            'DAI': '0x6B175474E89094C44Da98b954EedeAC495271d0F',
        }
        return COMMON_TOKENS.get(symbol.upper(), symbol)
    
    @classmethod
    def validate_config(cls):
        """Validate configuration"""
        errors = []
        
        if not cls.TELEGRAM_BOT_TOKEN or cls.TELEGRAM_BOT_TOKEN == "your_bot_token_here":
            errors.append("TELEGRAM_BOT_TOKEN not set in .env file")
        
        if not cls.RPC_URL or "YOUR_PROJECT_ID" in cls.RPC_URL:
            errors.append("RPC_URL not configured with real API key in .env file")
        
        if errors:
            print("⚠️  Configuration warnings:")
            for e in errors:
                print(f"  - {e}")
            print("\nThe bot may not work correctly without proper configuration.")
            print("Please check your .env file.\n")
        
        return True
