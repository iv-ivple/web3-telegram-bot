"""
Configuration management for the Telegram bot.
Loads environment variables and provides centralized config access.
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Bot configuration from environment variables."""
    
    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    ADMIN_USER_ID = os.getenv('ADMIN_USER_ID')
    
    # Blockchain
    RPC_URL = os.getenv('RPC_URL')
    ETHERSCAN_API_KEY = os.getenv('ETHERSCAN_API_KEY', '')
    
    # Database
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'data/bot_data.db')
    
    # Validation
    @classmethod
    def validate(cls):
        """Validate required configuration."""
        if not cls.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN not set in .env")
        if not cls.RPC_URL:
            raise ValueError("RPC_URL not set in .env")
        return True

# Validate on import
Config.validate()
