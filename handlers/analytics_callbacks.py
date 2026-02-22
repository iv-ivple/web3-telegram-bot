# handlers/analytics_callbacks.py
"""
Callback handlers for analytics button interactions
"""
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from handlers.analytics_commands import (
    analytics_command,
    wallet_report_command,
    export_csv_callback
)


async def analytics_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle callbacks from analytics buttons
    
    Callback data formats:
    - analytics_{token_address}_{days}
    - traders_{token_address}
    - volume_{token_address}
    - wallet_{wallet_address}_{token_address}_{days}
    - recent_{wallet_address}_{token_address}
    - export_{wallet_address}_{token_address}
    """
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    
    # Parse callback type
    if callback_data.startswith('analytics_'):
        await _handle_analytics_refresh(query, context)
    
    elif callback_data.startswith('traders_'):
        await _handle_top_traders(query, context)
    
    elif callback_data.startswith('volume_'):
        await _handle_volume_detail(query, context)
    
    elif callback_data.startswith('wallet_'):
        await _handle_wallet_refresh(query, context)
    
    elif callback_data.startswith('recent_'):
        await _handle_recent_transfers(query, context)
    
    elif callback_data.startswith('export_'):
        await export_csv_callback(update, context)


async def _handle_analytics_refresh(query, context):
    """Refresh analytics data"""
    parts = query.data.split('_')
    token_address = parts[1]
    days = int(parts[2])
    
    # Simulate command with args
    context.args = [token_address, str(days)]
    
    # Create a mock update with the message
    mock_update = type('obj', (object,), {
        'message': query.message,
        'effective_user': query.from_user,
        'effective_chat': query.message.chat
    })()
    
    await query.message.reply_text("🔄 Refreshing analytics...")
    await analytics_command(mock_update, context)


async def _handle_top_traders(query, context):
    """Show detailed top traders list"""
    from analytics.token_analytics import TokenAnalytics
    from utils.graph_helper import CachedGraphClient
    from config import Config
    
    token_address = query.data.split('_')[1]
    
    await query.message.reply_text("⏳ Loading top traders...")
    
    try:
        graph_client = CachedGraphClient(
            endpoint=Config.UNISWAP_V3_SUBGRAPH,
            cache_enabled=True
        )
        analytics = TokenAnalytics(graph_client=graph_client)
        
        # Get token info
        token_info = analytics.get_token_info(token_address)
        symbol = token_info['symbol']
        
        # Get top 20 traders
        traders = analytics.get_top_traders(token_address, limit=20)
        
        if not traders:
            await query.message.reply_text("No trader data available")
            return
        
        response = f"👥 *Top 20 Traders - {symbol}*\n"
        response += f"_(Last 7 days)_\n\n"
        
        for i, trader in enumerate(traders, 1):
            response += f"*{i}. `{trader['address'][:10]}...{trader['address'][-8:]}`*\n"
            response += f"   💰 Volume: ${trader['total_volume_usd']:,.0f}\n"
            response += f"   📊 Trades: {trader['trade_count']}\n"
            response += f"   📈 Buy: ${trader['buy_volume_usd']:,.0f}\n"
            response += f"   📉 Sell: ${trader['sell_volume_usd']:,.0f}\n"
            
            # Calculate buy/sell ratio
            if trader['buy_volume_usd'] > 0:
                ratio = trader['sell_volume_usd'] / trader['buy_volume_usd']
                if ratio > 1.2:
                    response += f"   ⚠️ Net seller ({ratio:.1f}x)\n"
                elif ratio < 0.8:
                    response += f"   ✅ Net buyer ({1/ratio:.1f}x)\n"
            
            response += "\n"
            
            # Split message if too long
            if len(response) > 3500:
                await query.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)
                response = ""
        
        if response:
            await query.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)
    
    except Exception as e:
        await query.message.reply_text(f"❌ Error: {str(e)}")


async def _handle_volume_detail(query, context):
    """Show detailed volume breakdown"""
    from analytics.token_analytics import TokenAnalytics
    from utils.graph_helper import CachedGraphClient
    from config import Config
    import pandas as pd
    
    token_address = query.data.split('_')[1]
    
    await query.message.reply_text("⏳ Analyzing volume data...")
    
    try:
        graph_client = CachedGraphClient(
            endpoint=Config.UNISWAP_V3_SUBGRAPH,
            cache_enabled=True
        )
        analytics = TokenAnalytics(graph_client=graph_client)
        
        # Get token info
        token_info = analytics.get_token_info(token_address)
        symbol = token_info['symbol']
        
        # Get price history (30 days for volume analysis)
        df = analytics.get_price_history(token_address, days=30)
        
        if df.empty:
            await query.message.reply_text("No volume data available")
            return
        
        # Calculate metrics
        total_volume = df['volume_usd'].sum()
        avg_daily_volume = df['volume_usd'].mean()
        max_volume_day = df.loc[df['volume_usd'].idxmax()]
        
        # Get 24h volume
        volume_24h = analytics.get_token_volume_24h(token_address)
        
        # Volume trend
        recent_avg = df.tail(7)['volume_usd'].mean()
        older_avg = df.head(7)['volume_usd'].mean()
        trend = ((recent_avg - older_avg) / older_avg * 100) if older_avg > 0 else 0
        
        response = f"📊 *Volume Analysis - {symbol}*\n"
        response += f"_(Last 30 days)_\n\n"
        
        response += f"*Current Metrics:*\n"
        response += f"24h Volume: ${volume_24h:,.0f}\n"
        response += f"7d Avg: ${recent_avg:,.0f}\n"
        response += f"30d Avg: ${avg_daily_volume:,.0f}\n\n"
        
        response += f"*30-Day Statistics:*\n"
        response += f"Total Volume: ${total_volume:,.0f}\n"
        response += f"Peak Day: ${max_volume_day['volume_usd']:,.0f}\n"
        response += f"Peak Date: {max_volume_day['date']}\n\n"
        
        response += f"*Trend:*\n"
        if trend > 10:
            response += f"📈 Volume increasing ({trend:+.1f}%)\n"
        elif trend < -10:
            response += f"📉 Volume decreasing ({trend:+.1f}%)\n"
        else:
            response += f"➡️ Volume stable ({trend:+.1f}%)\n"
        
        # Volume distribution
        response += f"\n*Distribution:*\n"
        high_volume_days = len(df[df['volume_usd'] > avg_daily_volume * 1.5])
        low_volume_days = len(df[df['volume_usd'] < avg_daily_volume * 0.5])
        response += f"High volume days: {high_volume_days}\n"
        response += f"Low volume days: {low_volume_days}\n"
        
        await query.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)
    
    except Exception as e:
        await query.message.reply_text(f"❌ Error: {str(e)}")


async def _handle_wallet_refresh(query, context):
    """Refresh wallet report"""
    parts = query.data.split('_')
    wallet_address = parts[1]
    token_address = parts[2]
    days = int(parts[3])
    
    context.args = [wallet_address, token_address, str(days)]
    
    mock_update = type('obj', (object,), {
        'message': query.message,
        'effective_user': query.from_user,
        'effective_chat': query.message.chat
    })()
    
    await query.message.reply_text("🔄 Refreshing wallet report...")
    await wallet_report_command(mock_update, context)


async def _handle_recent_transfers(query, context):
    """Show recent transfers for a wallet"""
    from analytics.transfers_analytics import TransfersAnalytics
    from analytics.token_analytics import TokenAnalytics
    from utils.graph_helper import CachedGraphClient
    from config import Config
    
    parts = query.data.split('_')
    wallet_address = parts[1]
    token_address = parts[2]
    
    await query.message.reply_text("⏳ Loading recent transfers...")
    
    try:
        graph_client = CachedGraphClient(
            endpoint=Config.UNISWAP_V3_SUBGRAPH,
            cache_enabled=True
        )
        
        # Get token info
        token_analytics = TokenAnalytics(graph_client=graph_client)
        token_info = token_analytics.get_token_info(token_address)
        symbol = token_info['symbol']
        
        # Get recent transfers
        transfers_analytics = TransfersAnalytics(
            rpc_url=Config.RPC_URL,
            subgraph_client=graph_client
        )
        
        transfers = transfers_analytics.get_transfers_hybrid(
            token_address=token_address,
            wallet_address=wallet_address,
            use_subgraph=False  # Use RPC for recent
        )
        
        if not transfers:
            await query.message.reply_text("No recent transfers found")
            return
        
        # Show last 15 transfers
        recent = transfers[-15:]
        
        response = f"📝 *Recent Transfers - {symbol}*\n"
        response += f"Wallet: `{wallet_address[:10]}...{wallet_address[-8:]}`\n\n"
        
        for i, t in enumerate(reversed(recent), 1):
            # Determine direction
            if t['to'].lower() == wallet_address.lower():
                direction = "⬅️ IN"
                counterparty = t['from']
            else:
                direction = "➡️ OUT"
                counterparty = t['to']
            
            response += f"*{i}. {direction}* `{t['value']:.4f}` {symbol}\n"
            response += f"   {counterparty[:16]}...\n"
            response += f"   Block: {t['block_number']} • {t['datetime'][:10]}\n"
            
            # Add transaction link
            tx_hash = t['tx_hash']
            response += f"   [View TX](https://etherscan.io/tx/{tx_hash})\n\n"
            
            # Split if too long
            if len(response) > 3500:
                await query.message.reply_text(
                    response,
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True
                )
                response = ""
        
        if response:
            await query.message.reply_text(
                response,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True
            )
    
    except Exception as e:
        await query.message.reply_text(f"❌ Error: {str(e)}")
