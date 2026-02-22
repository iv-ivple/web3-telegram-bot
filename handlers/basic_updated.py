# handlers/basic.py (UPDATED)
"""
Basic bot handlers including updated help with analytics
"""
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
import logging

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    user = update.effective_user
    
    welcome_message = f"""
👋 Welcome {user.mention_markdown_v2()}\\!

I'm your *Crypto Analytics Bot* 🤖

I can help you:
📊 Analyze tokens with beautiful charts
💼 Track wallet activity
📈 Monitor transfers
💰 Check balances & prices
⛽ Get gas prices

Use /help to see all commands\\!
"""
    
    await update.message.reply_text(
        welcome_message,
        parse_mode=ParseMode.MARKDOWN_V2
    )


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
Example: `/wallet_report 0x742d...f44e 0xA0b8...eB48 30`

━━━━━━━━━━━━━━━━━━━━━━━
💰 *BLOCKCHAIN BASICS*
━━━━━━━━━━━━━━━━━━━━━━━

`/balance <address>`
Check ETH balance for any address

`/price <token_symbol>`
Get current token price
Example: `/price ETH` or `/price BTC`

`/gas`
Check current Ethereum gas prices

━━━━━━━━━━━━━━━━━━━━━━━
👀 *WALLET TRACKING*
━━━━━━━━━━━━━━━━━━━━━━━

`/track <address> [name]`
Start tracking a wallet
Example: `/track 0x742d...f44e MyWallet`

`/untrack <address>`
Stop tracking a wallet

`/mywallets`
List all your tracked wallets

━━━━━━━━━━━━━━━━━━━━━━━
💡 *TIPS*
━━━━━━━━━━━━━━━━━━━━━━━

• Use short addresses: `0x742d...f44e`
• Default analysis period: 7 days
• Charts auto-generate for analytics
• Click buttons for more options
• Export data to CSV available

━━━━━━━━━━━━━━━━━━━━━━━
🔗 *QUICK EXAMPLES*
━━━━━━━━━━━━━━━━━━━━━━━

Analyze WETH for 30 days:
`/analytics 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2 30`

Get wallet USDC report:
`/wallet_report 0x742d35Cc6634C0532925a3b844Bc454e4438f44e 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48`

Check Vitalik's balance:
`/balance 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045`

━━━━━━━━━━━━━━━━━━━━━━━

Need help? Just ask!
"""
    
    await update.message.reply_text(
        help_text,
        parse_mode=ParseMode.MARKDOWN
    )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors caused by updates."""
    logger.error(f"Update {update} caused error {context.error}")
    
    # Notify user
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "❌ An error occurred while processing your request.\n"
            "Please try again or use /help for command info."
        )
