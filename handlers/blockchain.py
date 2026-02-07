"""
Blockchain-related command handlers.
Implements /balance, /gas, /price, /track commands.
"""
from functools import wraps
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from utils.web3_helper import web3_helper
from utils.validators import Validators
from utils.database import db
from utils.rate_limiter import rate_limiter

def rate_limited(func):
    """Decorator to add rate limiting to commands."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        
        if not rate_limiter.is_allowed(user_id):
            wait_time = rate_limiter.get_wait_time(user_id)
            await update.message.reply_text(
                f"⏳ Rate limit exceeded. Please wait {wait_time} seconds."
            )
            return
        
        return await func(update, context)
    
    return wrapper

@rate_limited
async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /balance command with inline keyboard."""
    if not context.args:
        await update.message.reply_text(
            "⚠️ Please provide an address.\n\n"
            "Usage: /balance 0xADDRESS"
        )
        return
    
    address = context.args[0]
    is_valid, error_msg = Validators.validate_eth_address(address)
    if not is_valid:
        await update.message.reply_text(f"❌ Invalid address: {error_msg}")
        return
    
    processing_msg = await update.message.reply_text("🔍 Fetching balance...")
    
    try:
        balance = web3_helper.get_eth_balance(address)
        
        # Create inline keyboard with action buttons
        keyboard = [
            [
                InlineKeyboardButton("🔄 Refresh", callback_data=f"refresh_balance:{address}"),
                InlineKeyboardButton("📊 Track", callback_data=f"track_wallet:{address}")
            ],
            [
                InlineKeyboardButton("🔗 View on Etherscan", url=f"https://etherscan.io/address/{address}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        response = f"""
💰 **Balance Report**

**Address:** `{address[:6]}...{address[-4:]}`
**Balance:** {Validators.format_eth_amount(balance)} ETH

_Click buttons below for actions_
"""
        
        await processing_msg.edit_text(
            response,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
    except Exception as e:
        await processing_msg.edit_text(f"❌ Error: {str(e)}")

@rate_limited
async def gas_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler for /gas command.
    
    Returns current gas prices for slow/average/fast transactions.
    """
    processing_msg = await update.message.reply_text("⛽ Fetching gas prices...")
    
    try:
        gas_prices = web3_helper.get_gas_prices()
        
        response = f"""
⛽ **Current Gas Prices**

🐌 **Slow:** {gas_prices['slow']:.2f} Gwei
   _~10-15 minutes_

⚡ **Average:** {gas_prices['average']:.2f} Gwei
   _~3-5 minutes_

🚀 **Fast:** {gas_prices['fast']:.2f} Gwei
   _~30-60 seconds_

📊 **Base Fee:** {gas_prices['base_fee']:.2f} Gwei

💡 **Tip:** Use slow gas for non-urgent transactions to save money!
"""
        
        await processing_msg.edit_text(response, parse_mode='Markdown')
        
    except Exception as e:
        await processing_msg.edit_text(
            f"❌ Error fetching gas prices: {str(e)}"
        )

@rate_limited
async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler for /price command.
    
    Usage: /price <token_symbol>
    Returns: Current token price from DEX
    """
    if not context.args:
        await update.message.reply_text(
            "⚠️ Please provide a token symbol.\n\n"
            "Usage: /price <symbol>\n"
            "Example: /price ETH\n\n"
            "Supported: ETH, BTC, USDC, USDT, DAI, UNI, LINK"
        )
        return
    
    symbol = context.args[0]
    processing_msg = await update.message.reply_text(f"💱 Fetching {symbol.upper()} price...")
    
    try:
        price_data = web3_helper.get_token_price(symbol)
        
        # Format change with emoji
        change = price_data['change_24h']
        change_emoji = "📈" if change > 0 else "📉" if change < 0 else "➡️"
        change_text = f"+{change:.2f}%" if change > 0 else f"{change:.2f}%"
        
        response = f"""
💱 **{price_data['symbol']} Price**

**Current Price:** ${price_data['price']:,.2f}

**24h Change:** {change_emoji} {change_text}

**Market Cap:** ${price_data['market_cap']:,.0f}

_Data from CoinGecko_
"""
        
        await processing_msg.edit_text(response, parse_mode='Markdown')
        
    except Exception as e:
        await processing_msg.edit_text(
            f"❌ Error fetching price: {str(e)}"
        )

@rate_limited
async def track_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler for /track command.
    
    Usage: /track <address> [label]
    Adds wallet to monitoring list.
    """
    if not context.args:
        await update.message.reply_text(
            "⚠️ Please provide an address to track.\n\n"
            "Usage: /track <address> [optional_label]\n"
            "Example: /track 0xd8dA6BF... MyWallet\n\n"
            "Use /mywallets to see all tracked wallets"
        )
        return
    
    address = context.args[0]
    label = ' '.join(context.args[1:]) if len(context.args) > 1 else None
    
    # Validate address
    is_valid, error_msg = Validators.validate_eth_address(address)
    if not is_valid:
        await update.message.reply_text(f"❌ Invalid address: {error_msg}")
        return
    
    user_id = update.effective_user.id
    
    # Add to database
    success = db.add_tracked_wallet(user_id, address, label)
    
    if success:
        # Get current balance
        try:
            balance = web3_helper.get_eth_balance(address)
            db.update_last_balance(user_id, address, balance)
            
            response = f"""
✅ **Wallet Added to Tracking**

**Address:** `{address[:10]}...{address[-8:]}`
**Label:** {label or 'No label'}
**Current Balance:** {Validators.format_eth_amount(balance)} ETH

Use /mywallets to see all tracked wallets.
"""
        except Exception as e:
            response = f"""
✅ **Wallet Added to Tracking**

**Address:** `{address[:10]}...{address[-8:]}`
**Label:** {label or 'No label'}

⚠️ Could not fetch initial balance: {str(e)}
"""
        
        await update.message.reply_text(response, parse_mode='Markdown')
    else:
        await update.message.reply_text(
            "⚠️ You're already tracking this wallet!\n"
            "Use /mywallets to see all tracked wallets."
        )

async def my_wallets_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show all wallets being tracked by this user."""
    user_id = update.effective_user.id
    wallets = db.get_tracked_wallets(user_id)
    
    if not wallets:
        await update.message.reply_text(
            "📭 You're not tracking any wallets yet.\n\n"
            "Use /track <address> to start monitoring a wallet!"
        )
        return
    
    response = "👛 **Your Tracked Wallets**\n\n"
    
    for wallet in wallets:
        address = wallet['wallet_address']
        label = wallet['label'] or 'No label'
        balance = wallet['last_balance']
        balance_text = f"{balance:.4f} ETH" if balance else "Unknown"
        
        response += f"""
**{label}**
`{address[:10]}...{address[-8:]}`
Balance: {balance_text}
---
"""
    
    response += "\n💡 Use /untrack <address> to stop tracking a wallet"
    
    await update.message.reply_text(response, parse_mode='Markdown')

async def untrack_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove a wallet from tracking."""
    if not context.args:
        await update.message.reply_text(
            "Usage: /untrack <address>\n"
            "Use /mywallets to see tracked wallets"
        )
        return
    
    address = context.args[0]
    user_id = update.effective_user.id
    
    success = db.remove_tracked_wallet(user_id, address)
    
    if success:
        await update.message.reply_text(
            f"✅ Stopped tracking `{address[:10]}...{address[-8:]}`",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            "⚠️ Wallet not found in your tracking list"
        )
