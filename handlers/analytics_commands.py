# handlers/analytics_commands.py
"""
Telegram bot handlers for analytics with chart generation
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server use
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import io
import os
from pathlib import Path

from analytics.token_analytics import TokenAnalytics
from analytics.transfers_analytics import TransfersAnalytics
from utils.graph_helper import CachedGraphClient
from config import Config

# Initialize clients
graph_client = CachedGraphClient(
    endpoint=Config.UNISWAP_V3_SUBGRAPH,
    cache_enabled=True,
    cache_ttl_minutes=5
)

token_analytics = TokenAnalytics(graph_client=graph_client)

transfers_analytics = TransfersAnalytics(
    rpc_url=Config.RPC_URL,
    subgraph_client=graph_client
)


async def analytics_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler for /analytics command
    Usage: /analytics <token_address> [days]
    
    Generates comprehensive analytics with charts:
    - Price history chart
    - Volume chart
    - Top traders analysis
    """
    if not context.args:
        await update.message.reply_text(
            "📊 *Token Analytics*\n\n"
            "Usage: `/analytics <token_address> [days]`\n\n"
            "Example:\n"
            "`/analytics 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2 7`\n\n"
            "Get comprehensive analytics with charts for any token.\n"
            "Default: 7 days of data",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    token_address = context.args[0]
    days = int(context.args[1]) if len(context.args) > 1 else 7
    
    # Validate address
    if not token_address.startswith('0x') or len(token_address) != 42:
        await update.message.reply_text("❌ Invalid token address format")
        return
    
    # Send processing message
    processing_msg = await update.message.reply_text(
        "⏳ Generating analytics...\n"
        "This may take a moment."
    )
    
    try:
        # 1. Get token info
        token_info = token_analytics.get_token_info(token_address)
        symbol = token_info['symbol']
        name = token_info['name']
        
        # 2. Get price history
        price_df = token_analytics.get_price_history(token_address, days=days)
        
        if price_df.empty:
            await processing_msg.edit_text(
                f"❌ No data available for this token.\n"
                f"Token may not be traded on Uniswap V3."
            )
            return
        
        # 3. Get 24h volume
        volume_24h = token_analytics.get_token_volume_24h(token_address)
        
        # 4. Get top traders
        top_traders = token_analytics.get_top_traders(token_address, limit=10)
        
        # 5. Generate charts
        chart_path = _generate_analytics_chart(price_df, symbol, days)
        
        # 6. Prepare summary text
        current_price = price_df['price_usd'].iloc[-1]
        first_price = price_df['price_usd'].iloc[0]
        price_change = ((current_price - first_price) / first_price) * 100
        high_price = price_df['high'].max()
        low_price = price_df['low'].min()
        total_volume = price_df['volume_usd'].sum()
        
        summary = f"📊 *{symbol} Analytics* ({days} days)\n\n"
        summary += f"*Token Info:*\n"
        summary += f"Name: {name}\n"
        summary += f"Symbol: {symbol}\n"
        summary += f"Address: `{token_address[:10]}...{token_address[-8:]}`\n\n"
        
        summary += f"*Price Statistics:*\n"
        summary += f"Current: ${current_price:,.4f}\n"
        summary += f"Change: {price_change:+.2f}%\n"
        summary += f"High: ${high_price:,.4f}\n"
        summary += f"Low: ${low_price:,.4f}\n\n"
        
        summary += f"*Volume:*\n"
        summary += f"24h: ${volume_24h:,.2f}\n"
        summary += f"{days}d Total: ${total_volume:,.2f}\n\n"
        
        if top_traders:
            summary += f"*Top 3 Traders (7d):*\n"
            for i, trader in enumerate(top_traders[:3], 1):
                summary += f"{i}. `{trader['address'][:10]}...`\n"
                summary += f"   Volume: ${trader['total_volume_usd']:,.0f} ({trader['trade_count']} trades)\n"
        
        # 7. Send chart
        with open(chart_path, 'rb') as photo:
            await update.message.reply_photo(
                photo=photo,
                caption=summary,
                parse_mode=ParseMode.MARKDOWN
            )
        
        # 8. Add action buttons
        keyboard = [
            [
                InlineKeyboardButton("🔄 Refresh", callback_data=f"analytics_{token_address}_{days}"),
                InlineKeyboardButton("📈 More Days", callback_data=f"analytics_{token_address}_30")
            ],
            [
                InlineKeyboardButton("👥 All Traders", callback_data=f"traders_{token_address}"),
                InlineKeyboardButton("📊 Volume Detail", callback_data=f"volume_{token_address}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "What would you like to see next?",
            reply_markup=reply_markup
        )
        
        # 9. Clean up
        await processing_msg.delete()
        os.remove(chart_path)
        
    except Exception as e:
        await processing_msg.edit_text(
            f"❌ Error generating analytics:\n`{str(e)}`",
            parse_mode=ParseMode.MARKDOWN
        )


async def wallet_report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler for /wallet_report command
    Usage: /wallet_report <wallet_address> [token_address] [days]
    
    Generates comprehensive wallet report with:
    - Transfer history
    - Balance analysis
    - Activity charts
    - Top counterparties
    """
    if not context.args:
        await update.message.reply_text(
            "💼 *Wallet Report*\n\n"
            "Usage: `/wallet_report <wallet> [token] [days]`\n\n"
            "Examples:\n"
            "`/wallet_report 0x742d35...f44e`\n"
            "`/wallet_report 0x742d35...f44e 0xA0b869...eB48 30`\n\n"
            "Generate detailed wallet activity report with charts.",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    wallet_address = context.args[0]
    token_address = context.args[1] if len(context.args) > 1 else Config.get_token_address('USDC')
    days = int(context.args[2]) if len(context.args) > 2 else 30
    
    # Validate addresses
    if not wallet_address.startswith('0x') or len(wallet_address) != 42:
        await update.message.reply_text("❌ Invalid wallet address format")
        return
    
    # Send processing message
    processing_msg = await update.message.reply_text(
        "⏳ Generating wallet report...\n"
        "Analyzing transfer history and generating charts.\n"
        "This may take up to a minute for large wallets."
    )
    
    try:
        # 1. Get token info
        token_info = token_analytics.get_token_info(token_address)
        symbol = token_info['symbol']
        
        # 2. Get transfer summary
        summary = transfers_analytics.get_transfer_summary(
            token_address=token_address,
            wallet_address=wallet_address,
            days=days
        )
        
        transfers = summary['transfers']
        stats = summary['stats']
        
        if not transfers:
            await processing_msg.edit_text(
                f"❌ No {symbol} transfers found for this wallet in the last {days} days."
            )
            return
        
        # 3. Generate charts
        chart_path = _generate_wallet_chart(transfers, wallet_address, symbol, days)
        
        # 4. Analyze counterparties
        from collections import Counter
        senders = Counter()
        receivers = Counter()
        
        for t in transfers:
            if t['to'].lower() == wallet_address.lower():
                senders[t['from']] += t['value']
            else:
                receivers[t['to']] += t['value']
        
        top_senders = senders.most_common(3)
        top_receivers = receivers.most_common(3)
        
        # 5. Prepare report
        report = f"💼 *Wallet Report* ({days} days)\n\n"
        report += f"*Wallet:*\n`{wallet_address}`\n\n"
        report += f"*Token:* {symbol}\n\n"
        
        report += f"*Activity Summary:*\n"
        report += f"├ Total Transfers: {stats['total_transfers']}\n"
        report += f"├ Received: {stats['received_count']} transfers\n"
        report += f"├ Sent: {stats['sent_count']} transfers\n"
        report += f"└ Unique Addresses: {stats['unique_counterparties']}\n\n"
        
        report += f"*Balance Changes:*\n"
        report += f"├ Total Received: {stats['total_received']:,.2f} {symbol}\n"
        report += f"├ Total Sent: {stats['total_sent']:,.2f} {symbol}\n"
        report += f"└ Net Change: {stats['net_change']:+,.2f} {symbol}\n\n"
        
        if top_senders:
            report += f"*Top Senders:*\n"
            for i, (addr, amount) in enumerate(top_senders, 1):
                report += f"{i}. `{addr[:10]}...` ({amount:,.2f} {symbol})\n"
            report += "\n"
        
        if top_receivers:
            report += f"*Top Receivers:*\n"
            for i, (addr, amount) in enumerate(top_receivers, 1):
                report += f"{i}. `{addr[:10]}...` ({amount:,.2f} {symbol})\n"
        
        # 6. Calculate activity metrics
        if stats['total_transfers'] > 0:
            avg_per_day = stats['total_transfers'] / days
            report += f"\n*Activity Metrics:*\n"
            report += f"├ Avg transfers/day: {avg_per_day:.1f}\n"
            
            if stats['received_count'] > 0:
                avg_received = stats['total_received'] / stats['received_count']
                report += f"├ Avg received/transfer: {avg_received:,.2f} {symbol}\n"
            
            if stats['sent_count'] > 0:
                avg_sent = stats['total_sent'] / stats['sent_count']
                report += f"└ Avg sent/transfer: {avg_sent:,.2f} {symbol}\n"
        
        # 7. Add timestamps
        if stats['first_transfer']:
            first_date = datetime.fromisoformat(stats['first_transfer']['datetime']).strftime('%Y-%m-%d')
            last_date = datetime.fromisoformat(stats['last_transfer']['datetime']).strftime('%Y-%m-%d')
            report += f"\n*Period:*\n"
            report += f"First: {first_date}\n"
            report += f"Last: {last_date}\n"
        
        # 8. Send chart
        with open(chart_path, 'rb') as photo:
            await update.message.reply_photo(
                photo=photo,
                caption=report,
                parse_mode=ParseMode.MARKDOWN
            )
        
        # 9. Add action buttons
        keyboard = [
            [
                InlineKeyboardButton("🔄 Refresh", callback_data=f"wallet_{wallet_address}_{token_address}_{days}"),
                InlineKeyboardButton("📅 More Days", callback_data=f"wallet_{wallet_address}_{token_address}_90")
            ],
            [
                InlineKeyboardButton("📝 Recent Transfers", callback_data=f"recent_{wallet_address}_{token_address}"),
                InlineKeyboardButton("💾 Export CSV", callback_data=f"export_{wallet_address}_{token_address}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "Additional options:",
            reply_markup=reply_markup
        )
        
        # 10. Clean up
        await processing_msg.delete()
        os.remove(chart_path)
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        await processing_msg.edit_text(
            f"❌ Error generating wallet report:\n`{str(e)}`",
            parse_mode=ParseMode.MARKDOWN
        )
        print(f"Wallet report error: {error_details}")


def _generate_analytics_chart(df, symbol: str, days: int) -> str:
    """
    Generate analytics chart with price and volume
    
    Returns:
        Path to saved chart image
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), height_ratios=[2, 1])
    
    # Price chart
    ax1.plot(df['timestamp'], df['price_usd'], linewidth=2, color='#2962FF', label='Price')
    ax1.fill_between(df['timestamp'], df['low'], df['high'], alpha=0.2, color='#2962FF')
    ax1.set_ylabel('Price (USD)', fontsize=12, fontweight='bold')
    ax1.set_title(f'{symbol} Price & Volume ({days} days)', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # Format price axis
    current_price = df['price_usd'].iloc[-1]
    if current_price < 0.01:
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:.6f}'))
    elif current_price < 1:
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:.4f}'))
    else:
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.2f}'))
    
    # Volume chart
    colors = ['#4CAF50' if df['price_usd'].iloc[i] >= df['price_usd'].iloc[i-1] 
              else '#F44336' if i > 0 else '#4CAF50' for i in range(len(df))]
    ax2.bar(df['timestamp'], df['volume_usd'], color=colors, alpha=0.7)
    ax2.set_ylabel('Volume (USD)', fontsize=12, fontweight='bold')
    ax2.set_xlabel('Date', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='y')
    
    # Format volume axis
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1e6:.1f}M' if x >= 1e6 else f'${x/1e3:.1f}K'))
    
    # Format x-axis
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
    
    plt.tight_layout()
    
    # Save to file
    chart_path = f'/tmp/analytics_{symbol}_{int(datetime.now().timestamp())}.png'
    plt.savefig(chart_path, dpi=100, bbox_inches='tight')
    plt.close()
    
    return chart_path


def _generate_wallet_chart(transfers, wallet_address: str, symbol: str, days: int) -> str:
    """
    Generate wallet activity chart
    
    Returns:
        Path to saved chart image
    """
    # Convert to DataFrame for easier plotting
    import pandas as pd
    df = pd.DataFrame(transfers)
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
    df['date'] = df['timestamp'].dt.date
    
    # Separate incoming and outgoing
    df['direction'] = df.apply(
        lambda row: 'in' if row['to'].lower() == wallet_address.lower() else 'out',
        axis=1
    )
    
    # Daily aggregation
    daily_in = df[df['direction'] == 'in'].groupby('date')['value'].sum()
    daily_out = df[df['direction'] == 'out'].groupby('date')['value'].sum()
    
    # Create date range
    date_range = pd.date_range(
        start=df['date'].min(),
        end=df['date'].max(),
        freq='D'
    )
    daily_in = daily_in.reindex(date_range, fill_value=0)
    daily_out = daily_out.reindex(date_range, fill_value=0)
    
    # Plot
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), height_ratios=[2, 1])
    
    # Cumulative balance chart
    cumulative = (daily_in - daily_out).cumsum()
    ax1.fill_between(date_range, 0, cumulative, alpha=0.3, color='#2196F3')
    ax1.plot(date_range, cumulative, linewidth=2, color='#2196F3', label='Net Balance Change')
    ax1.set_ylabel(f'Cumulative {symbol}', fontsize=12, fontweight='bold')
    ax1.set_title(f'Wallet Activity Report ({days} days)', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    ax1.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
    
    # Daily transfer volume chart
    ax2.bar(date_range, daily_in, alpha=0.7, color='#4CAF50', label='Received')
    ax2.bar(date_range, -daily_out, alpha=0.7, color='#F44336', label='Sent')
    ax2.set_ylabel(f'{symbol} Volume', fontsize=12, fontweight='bold')
    ax2.set_xlabel('Date', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='y')
    ax2.legend()
    ax2.axhline(y=0, color='gray', linestyle='-', alpha=0.5)
    
    # Format x-axis
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
    
    plt.tight_layout()
    
    # Save to file
    chart_path = f'/tmp/wallet_{wallet_address[:10]}_{int(datetime.now().timestamp())}.png'
    plt.savefig(chart_path, dpi=100, bbox_inches='tight')
    plt.close()
    
    return chart_path


async def export_csv_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Export wallet transfers to CSV"""
    query = update.callback_query
    await query.answer()
    
    # Parse callback data
    parts = query.data.split('_')
    wallet_address = parts[1]
    token_address = parts[2]
    
    await query.message.reply_text("⏳ Generating CSV export...")
    
    try:
        # Get token info
        token_info = token_analytics.get_token_info(token_address)
        symbol = token_info['symbol']
        
        # Get transfers
        summary = transfers_analytics.get_transfer_summary(
            token_address=token_address,
            wallet_address=wallet_address,
            days=90
        )
        
        # Create CSV
        import csv
        csv_path = f'/tmp/transfers_{wallet_address[:10]}_{symbol}.csv'
        
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'timestamp', 'date', 'from', 'to', 'value', 'symbol', 
                'tx_hash', 'block_number'
            ])
            writer.writeheader()
            
            for t in summary['transfers']:
                writer.writerow({
                    'timestamp': t['timestamp'],
                    'date': t['datetime'],
                    'from': t['from'],
                    'to': t['to'],
                    'value': t['value'],
                    'symbol': t.get('symbol', symbol),
                    'tx_hash': t['tx_hash'],
                    'block_number': t['block_number']
                })
        
        # Send file
        with open(csv_path, 'rb') as f:
            await query.message.reply_document(
                document=f,
                filename=f'transfers_{symbol}_{wallet_address[:10]}.csv',
                caption=f"📊 Transfer history exported\n{len(summary['transfers'])} transfers"
            )
        
        os.remove(csv_path)
        
    except Exception as e:
        await query.message.reply_text(f"❌ Export failed: {str(e)}")
