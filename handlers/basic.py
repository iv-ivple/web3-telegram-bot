"""
Basic bot command handlers.
Handles /start, /help, and general user interactions.
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler for /start command.
    
    This is the first command users will interact with.
    Should be welcoming and explain what the bot can do.
    """
    user = update.effective_user
    welcome_message = f"""
👋 Welcome {user.mention_html()}, 

I'm your personal Web3 assistant! Here's what I can do:

📊 <b>Available Commands:</b>
/balance &lt;address&gt; - Check ETH balance
/gas - Get current gas prices
/price &lt;token&gt; - Get token price
/track &lt;address&gt; - Monitor a wallet
/help - Show this help message

📰 <b>Getting Started:</b>
Try: <code>/balance 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045</code>

💡 <b>Tips:</b>
- All addresses must start with 0x
- Commands are case-insensitive
- Use /help anytime for assistance
"""
    
    await update.message.reply_html(welcome_message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /help command."""
    help_text = """
📖 <b>Command Reference</b>

🔹 /balance &lt;address&gt;
Check ETH balance for any Ethereum address
Example: <code>/balance 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045</code>

🔹 /gas
Get current network gas prices (slow/average/fast)

🔹 /price &lt;token&gt;
Get current token price from DEXs
Example: <code>/price ETH</code> or <code>/price USDC</code>

🔹 /track &lt;address&gt;
Monitor wallet for activity (coming soon!)

🔹 /help
Show this help message

❓ <b>Need Help?</b>
Contact: @YourUsername
"""
    
    await update.message.reply_html(help_text)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comprehensive error handler.
    Logs errors and provides user-friendly messages.
    """
    import traceback
    from telegram.error import TelegramError
    from config import Config
    
    # Log the error
    logger = logging.getLogger(__name__)
    logger.error("Exception while handling an update:", exc_info=context.error)
    
    # Extract error information
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = ''.join(tb_list)
    
    # User-friendly error messages
    error_messages = {
        'BadRequest': "⚠️ Invalid request. Please check your input and try again.",
        'Unauthorized': "⚠️ Bot token is invalid. Please contact support.",
        'Forbidden': "⚠️ I don't have permission to do that.",
        'NetworkError': "⚠️ Network error. Please try again in a moment.",
        'TimedOut': "⚠️ Request timed out. Please try again.",
    }
    
    # Get error type
    error_type = type(context.error).__name__
    user_message = error_messages.get(error_type, "⚠️ An unexpected error occurred.")
    
    # Send message to user
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(
                f"{user_message}\n\n"
                "If this persists, please contact support."
            )
        except:
            pass  # Can't send message to user
    
    # Optionally send error to admin
    if hasattr(Config, 'ADMIN_USER_ID') and Config.ADMIN_USER_ID:
        try:
            await context.bot.send_message(
                chat_id=Config.ADMIN_USER_ID,
                text=f"⚠️ Error occurred:\n\n{error_type}\n\n{str(context.error)[:500]}"
            )
        except:
            pass
