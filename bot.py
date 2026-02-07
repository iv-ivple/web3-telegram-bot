"""
Main bot application.
Sets up handlers and starts the bot using polling.
"""
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

from config import Config
from handlers.basic import start_command, help_command, error_handler
from handlers.callbacks import button_callback

from handlers.blockchain import (
    balance_command,
    gas_command,
    price_command,
    track_command,
    my_wallets_command,
    untrack_command
)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Start the bot."""
    application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
    
    # Basic commands
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    
    # Blockchain commands
    application.add_handler(CommandHandler("balance", balance_command))
    application.add_handler(CommandHandler("gas", gas_command))
    application.add_handler(CommandHandler("price", price_command))
    application.add_handler(CommandHandler("track", track_command))
    application.add_handler(CommandHandler("mywallets", my_wallets_command))
    application.add_handler(CommandHandler("untrack", untrack_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Error handler
    application.add_error_handler(error_handler)
    
    logger.info("Bot started successfully!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
