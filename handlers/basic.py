"""
Basic bot command handlers.
Handles /start, /help, and general user interactions.
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

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

I'm your *Crypto Analytics Bot*! Here's what I can do:

📊 <b>Analytics & Charts:</b>
/analytics &lt;token&gt; [days] - Token analytics with charts
/wallet_report &lt;wallet&gt; [token] [days] - Wallet activity report

💰 <b>Blockchain Basics:</b>
/balance &lt;address&gt; - Check ETH balance
/gas - Get current gas prices
/price &lt;token&gt; - Get token price

👀 <b>Wallet Tracking:</b>
/track &lt;address&gt; [name] - Monitor a wallet
/mywallets - List tracked wallets
/help - Show full command guide

📰 <b>Quick Start:</b>
Try: <code>/analytics 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2 7</code>

💡 <b>Tips:</b>
- All addresses must start with 0x
- Use /help for detailed examples
"""
    
    await update.message.reply_html(welcome_message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    
    help_text = """
📚 *Bot Commands Guide*

━━━━━━━━━━━━━━━━━━━━━━━
📊 *ANALYTICS & CHARTS*
━━━━━━━━━━━━━━━━━━━━━━━

`/analytics <token> [days]`
Generate comprehensive token analytics with price & volume charts
Example: `/analytics 0xC02a...Cc2 7`

`/wallet_report <wallet> [token] [days]`
Generate wallet activity report with transfer charts
Example: `/wallet_report 0x742d...f44e`

━━━━━━━━━━━━━━━━━━━━━━━
💰 *BLOCKCHAIN BASICS*
━━━━━━━━━━━━━━━━━━━━━━━

`/balance <address>`
Check ETH balance for any address

`/price <token_symbol>`
Get current token price
Example: `/price ETH`

`/gas`
Check current Ethereum gas prices

━━━━━━━━━━━━━━━━━━━━━━━
👀 *WALLET TRACKING*
━━━━━━━━━━━━━━━━━━━━━━━

`/track <address> [name]`
Start tracking a wallet

`/untrack <address>`
Stop tracking a wallet

`/mywallets`
List all your tracked wallets

━━━━━━━━━━━━━━━━━━━━━━━
💡 *TIPS*
━━━━━━━━━━━━━━━━━━━━━━━

- Use short addresses: `0x742d...f44e`
- Default analysis period: 7 days
- Charts auto-generate for analytics
- Click buttons for more options

━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    await update.message.reply_text(
        help_text,
        parse_mode=ParseMode.MARKDOWN
    )

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
