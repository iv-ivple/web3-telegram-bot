# bot.py
"""
Main bot application with analytics integration.
Sets up handlers and starts the bot using polling.
"""
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

from config import Config

# Import existing handlers
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

# Import new analytics handlers
from handlers.analytics_commands import (
    analytics_command,
    wallet_report_command
)

from handlers.analytics_callbacks import analytics_callback_handler

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Start the bot with all features enabled."""
    
    # Validate configuration
    try:
        Config.validate_config()
        logger.info("Configuration validated successfully")
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return
    
    # Create application
    application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
    
    # ==========================================
    # BASIC COMMANDS
    # ==========================================
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    
    # ==========================================
    # BLOCKCHAIN COMMANDS
    # ==========================================
    application.add_handler(CommandHandler("balance", balance_command))
    application.add_handler(CommandHandler("gas", gas_command))
    application.add_handler(CommandHandler("price", price_command))
    application.add_handler(CommandHandler("track", track_command))
    application.add_handler(CommandHandler("mywallets", my_wallets_command))
    application.add_handler(CommandHandler("untrack", untrack_command))
    
    # ==========================================
    # ANALYTICS COMMANDS (NEW!)
    # ==========================================
    application.add_handler(CommandHandler("analytics", analytics_command))
    application.add_handler(CommandHandler("wallet_report", wallet_report_command))
    
    # Alternative command names
    application.add_handler(CommandHandler("analyze", analytics_command))
    application.add_handler(CommandHandler("report", wallet_report_command))
    application.add_handler(CommandHandler("wallet", wallet_report_command))
    
    # ==========================================
    # CALLBACK HANDLERS
    # ==========================================
    # Analytics callbacks (should be registered first for priority)
    application.add_handler(CallbackQueryHandler(
        analytics_callback_handler,
        pattern='^(analytics|traders|volume|wallet|recent|export)_'
    ))
    
    # General callbacks
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # ==========================================
    # ERROR HANDLER
    # ==========================================
    application.add_error_handler(error_handler)
    
    # ==========================================
    # STARTUP
    # ==========================================
    logger.info("=" * 60)
    logger.info("🤖 Telegram Crypto Analytics Bot")
    logger.info("=" * 60)
    logger.info("Features enabled:")
    logger.info("  ✓ Basic blockchain commands")
    logger.info("  ✓ Wallet tracking")
    logger.info("  ✓ Token analytics with charts")
    logger.info("  ✓ Wallet reports with charts")
    logger.info("  ✓ Transfer history")
    logger.info("  ✓ CSV export")
    logger.info("=" * 60)
    logger.info("Bot started successfully!")
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 60)
    
    # Start polling
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
