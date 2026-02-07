"""
Callback query handlers for inline keyboard buttons.
"""
from telegram import Update
from telegram.ext import ContextTypes

from utils.web3_helper import web3_helper
from utils.validators import Validators
from utils.database import db

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button presses from inline keyboards."""
    query = update.callback_query
    await query.answer()  # Acknowledge the button press
    
    # Parse callback data
    action, data = query.data.split(':', 1)
    
    if action == 'refresh_balance':
        # Refresh balance
        address = data
        try:
            balance = web3_helper.get_eth_balance(address)
            
            response = f"""
💰 **Balance Report** _(refreshed)_

**Address:** `{address[:6]}...{address[-4:]}`
**Balance:** {Validators.format_eth_amount(balance)} ETH

_Last updated: just now_
"""
            # Keep the same keyboard
            await query.edit_message_text(
                response,
                parse_mode='Markdown',
                reply_markup=query.message.reply_markup
            )
        except Exception as e:
            await query.edit_message_text(f"❌ Error refreshing: {str(e)}")
    
    elif action == 'track_wallet':
        # Quick-add to tracking
        address = data
        user_id = update.effective_user.id
        
        success = db.add_tracked_wallet(user_id, address)
        
        if success:
            await query.answer("✅ Added to tracking!", show_alert=True)
        else:
            await query.answer("⚠️ Already tracking this wallet", show_alert=True)
