# Web3 Telegram Bot with Advanced Analytics 📊

A comprehensive Telegram bot for interacting with Ethereum blockchain featuring real-time analytics, beautiful charts, wallet tracking, and token insights powered by The Graph and RPC providers.

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![Telegram](https://img.shields.io/badge/telegram-bot-blue.svg)
![Web3](https://img.shields.io/badge/web3-ethereum-purple.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## ✨ Features

### 📊 Analytics & Visualization
✅ **Token Analytics** - Comprehensive token analysis with price/volume charts  
✅ **Price History** - Historical OHLC data with customizable timeframes  
✅ **Volume Analysis** - Trading volume breakdowns and trends  
✅ **Top Traders** - Identify and analyze top market participants  
✅ **Beautiful Charts** - Auto-generated matplotlib charts with professional styling  

### 💼 Wallet Intelligence
✅ **Wallet Reports** - Complete activity reports with visual analytics  
✅ **Transfer Tracking** - Hybrid RPC/Subgraph transfer history  
✅ **Balance Changes** - Cumulative balance tracking over time  
✅ **Counterparty Analysis** - Top senders/receivers identification  
✅ **CSV Export** - Download complete transfer history  

### ⛓️ Blockchain Basics
✅ **Balance Checking** - Real-time ETH balance queries  
✅ **Gas Prices** - Current Ethereum gas prices  
✅ **Token Prices** - DEX price lookups  
✅ **Wallet Tracking** - Monitor multiple wallets  

### 🚀 Performance & UX
✅ **Intelligent Caching** - GraphQL query caching for speed  
✅ **Rate Limiting** - Automatic API rate management  
✅ **Interactive Buttons** - Inline keyboards for exploration  
✅ **Error Handling** - Comprehensive error management  

## 📱 Commands

### Analytics Commands
```
/analytics <token_address> [days]
Generate comprehensive token analytics with charts
Example: /analytics 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2 7

/wallet_report <wallet_address> [token_address] [days]
Create wallet activity report with transfer charts
Example: /wallet_report 0x742d35Cc6634C0532925a3b844Bc454e4438f44e

/analyze <token_address>
Alias for /analytics
```

### Blockchain Commands
```
/balance <address>
Check ETH balance for any address
Example: /balance 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045

/gas
Get current Ethereum gas prices

/price <token>
Get token price from DEX
Example: /price ETH
```

### Wallet Tracking
```
/track <address> [label]
Add wallet to tracking list
Example: /track 0x742d35... MyWallet

/mywallets
Show all tracked wallets with quick actions

/untrack <address>
Remove wallet from tracking
```

### Utility Commands
```
/start
Welcome message and quick start guide

/help
Comprehensive command documentation
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Telegram account
- Ethereum RPC endpoint (Infura/Alchemy)
- The Graph API key (optional, for better rate limits)

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/web3-telegram-bot.git
cd web3-telegram-bot
```

2. **Create virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables:**
```bash
cp .env.example .env
# Edit .env with your API keys
```

Required in `.env`:
```env
# Telegram Bot Token (from @BotFather)
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# Ethereum RPC URL (Infura/Alchemy/QuickNode)
RPC_URL=https://mainnet.infura.io/v3/YOUR_PROJECT_ID

# The Graph API Key (optional)
GRAPH_API_KEY=your_graph_api_key

# Optional: Admin user ID for error notifications
ADMIN_USER_ID=123456789
```

5. **Run the bot:**
```bash
python bot_updated.py
```

You should see:
```
============================================================
🤖 Telegram Crypto Analytics Bot
============================================================
Features enabled:
  ✓ Basic blockchain commands
  ✓ Wallet tracking
  ✓ Token analytics with charts
  ✓ Wallet reports with charts
  ✓ Transfer history
  ✓ CSV export
============================================================
Bot started successfully!
```

## 📚 Usage Examples

### Example 1: Token Analytics

**Command:**
```
/analytics 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2 7
```

**Output:**
- 📊 Beautiful chart with price history and volume
- 💰 Current price, 7-day high/low, price change %
- 📈 24h and 7-day volume statistics
- 👥 Top 3 traders by volume
- 🔘 Interactive buttons: Refresh, More Days, All Traders, Volume Detail

### Example 2: Wallet Report

**Command:**
```
/wallet_report 0x742d35Cc6634C0532925a3b844Bc454e4438f44e 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48 30
```

**Output:**
- 📊 Activity chart showing cumulative balance over time
- 📈 Daily transfer volume visualization
- 📋 Transfer statistics (received, sent, net change)
- 👥 Top senders and receivers
- 📊 Activity metrics (avg transfers/day)
- 💾 CSV export button

### Example 3: Balance Check

**Command:**
```
/balance 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045
```

**Output:**
```
💰 Balance for 0xd8dA6BF2...A96045
Balance: 1,234.5678 ETH
USD Value: $4,567,890.12
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Telegram User                        │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Telegram Bot API (python-telegram-bot)     │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
┌──────────────────┐    ┌──────────────────┐
│  Basic Handlers  │    │Analytics Handlers│
│  - Start/Help    │    │  - Token Analytics│
│  - Balance       │    │  - Wallet Reports│
│  - Gas/Price     │    │  - Chart Gen     │
└────────┬─────────┘    └────────┬─────────┘
         │                       │
         │                       ▼
         │              ┌──────────────────┐
         │              │  Token Analytics │
         │              │  - GraphQL Client│
         │              │  - Cache Layer   │
         │              └────────┬─────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌──────────────────┐
│   Web3 (RPC)    │    │   The Graph API  │
│   - Balances    │    │   - Price Data   │
│   - Transfers   │    │   - Volume       │
│   - Gas Prices  │    │   - Swaps        │
└─────────────────┘    └──────────────────┘
         │                       │
         └───────────┬───────────┘
                     ▼
            ┌──────────────────┐
            │   Ethereum       │
            │   Mainnet        │
            └──────────────────┘
```

## 📁 Project Structure

```
web3-telegram-bot/
├── bot_updated.py              # Main bot application
├── config.py                   # Configuration management
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (not committed)
├── .env.example               # Environment template
├── README.md                   # This file
│
├── handlers/
│   ├── __init__.py
│   ├── basic.py               # Basic commands (/start, /help)
│   ├── blockchain.py          # Blockchain commands (/balance, /gas)
│   ├── callbacks.py           # Inline keyboard handlers
│   ├── analytics_commands.py  # Analytics commands (NEW)
│   └── analytics_callbacks.py # Analytics button handlers (NEW)
│
├── analytics/
│   ├── __init__.py
│   ├── token_analytics.py     # Token analysis with GraphQL (NEW)
│   └── transfers_analytics.py # Transfer tracking (RPC/Subgraph) (NEW)
│
├── utils/
│   ├── __init__.py
│   ├── web3_helper.py         # Web3 utilities
│   ├── graph_helper.py        # GraphQL client with caching (NEW)
│   ├── cache_helper.py        # Cache implementation (NEW)
│   ├── validators.py          # Input validation
│   ├── database.py            # Database management
│   └── rate_limiter.py        # Rate limiting
│
├── cache/                      # Cache directory (auto-created)
│   └── *.json.gz              # Cached GraphQL queries
│
├── data/
│   └── bot_data.db            # SQLite database
│
├── docs/                       # Documentation (NEW)
│   ├── GRAPHQL_QUERIES.md     # GraphQL query documentation
│   ├── SETUP_GUIDE.md         # Detailed setup instructions
│   ├── EXAMPLES.md            # Usage examples with screenshots
│   └── ARCHITECTURE.md        # Architecture details
│
└── tests/
    ├── test_bot.py
    ├── test_analytics.py       # Analytics tests (NEW)
    └── test_graphql.py         # GraphQL tests (NEW)
```

## 🔧 Configuration

### Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `TELEGRAM_BOT_TOKEN` | Yes | Bot token from @BotFather | `1234567890:ABC...` |
| `RPC_URL` | Yes | Ethereum RPC endpoint | `https://mainnet.infura.io/v3/...` |
| `GRAPH_API_KEY` | No | The Graph API key for higher rate limits | `abc123...` |
| `DATABASE_PATH` | No | SQLite database path | `bot_data.db` (default) |
| `CACHE_ENABLED` | No | Enable query caching | `true` (default) |
| `CACHE_TTL` | No | Cache TTL in minutes | `5` (default) |
| `ADMIN_USER_ID` | No | Telegram user ID for error notifications | `123456789` |

### API Keys

**Telegram Bot Token:**
1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot` and follow instructions
3. Copy the token

**Ethereum RPC:**
- [Infura](https://infura.io) - 100,000 requests/day free
- [Alchemy](https://alchemy.com) - 300M compute units/month free
- [QuickNode](https://quicknode.com) - Free tier available

**The Graph API:**
1. Go to [The Graph Studio](https://thegraph.com/studio/)
2. Sign in and create an API key
3. Free tier available

## 📊 GraphQL Queries Used

The bot uses The Graph Protocol to query Uniswap V3 data efficiently.

### Token Information Query
```graphql
{
  token(id: "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2") {
    symbol
    name
    decimals
    derivedETH
  }
}
```

### Price History Query
```graphql
{
  tokenDayDatas(
    first: 7,
    orderBy: date,
    orderDirection: desc,
    where: {
      token: "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
      date_gte: 1708214400
    }
  ) {
    date
    priceUSD
    volumeUSD
    open
    high
    low
    close
  }
}
```

### Top Traders Query
```graphql
{
  swaps(
    first: 1000,
    orderBy: timestamp,
    orderDirection: desc,
    where: {
      timestamp_gte: 1708214400,
      or: [
        { token0: "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2" },
        { token1: "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2" }
      ]
    }
  ) {
    origin
    amountUSD
    amount0
    amount1
    token0 { id }
    token1 { id }
  }
}
```

For complete GraphQL documentation, see [docs/GRAPHQL_QUERIES.md](docs/GRAPHQL_QUERIES.md)

## 🎨 Chart Generation

Charts are generated using matplotlib with custom styling:

**Features:**
- Professional color schemes
- Auto-formatted axes (K/M notation)
- High/low shading
- Volume bars color-coded by price movement
- Saved as PNG at 100 DPI
- Auto-cleanup after sending

**Example:**
```python
# Price chart with volume
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
ax1.plot(df['timestamp'], df['price_usd'], linewidth=2, color='#2962FF')
ax2.bar(df['timestamp'], df['volume_usd'], color=colors, alpha=0.7)
```

## 🔐 Security

- ✅ Bot token stored in environment variables
- ✅ Input validation on all user inputs
- ✅ Rate limiting to prevent abuse
- ✅ SQL injection prevention with parameterized queries
- ✅ No sensitive data in logs
- ✅ API keys never exposed to users
- ✅ Error messages don't leak system information

## 🚀 Performance Optimizations

### Caching Strategy
```python
# Different cache TTLs based on data volatility
Token Info:        24 hours  (rarely changes)
Historical Data:   6 hours   (immutable once created)
Current Price:     1 minute  (changes frequently)
Volume Data:       5 minutes (updates moderately)
```

### Rate Limiting
```python
# Automatic rate limiting per provider
Infura:  100,000 requests/day → ~10 req/sec
Alchemy: 300M compute units/month → ~660 req/sec
```

### Query Optimization
- Chunked RPC queries for large block ranges
- Hybrid RPC/Subgraph strategy for transfers
- Automatic deduplication of results
- Batch queries where possible

## 🧪 Testing

Run tests:
```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/test_analytics.py -v

# With coverage
pytest --cov=. tests/
```

Code quality:
```bash
# Linting
flake8 .

# Formatting
black .

# Type checking
mypy .
```

## 📈 Roadmap

### v2.1 (Current)
- [x] Token analytics with charts
- [x] Wallet activity reports
- [x] GraphQL caching
- [x] CSV export
- [x] Interactive buttons

### v2.2 (Planned)
- [ ] Price alerts and notifications
- [ ] Portfolio tracking
- [ ] Multi-chain support (Polygon, Arbitrum)
- [ ] Historical portfolio snapshots
- [ ] Gas price notifications

### v3.0 (Future)
- [ ] NFT analytics
- [ ] DeFi protocol integration
- [ ] Social trading features
- [ ] AI-powered insights
- [ ] Mobile app companion

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

Please ensure:
- Code follows PEP 8 style guide
- All tests pass
- New features include tests
- Documentation is updated

## 📝 Changelog

### v2.1.0 (2026-02-22)
**Added:**
- Token analytics with price/volume charts
- Wallet activity reports with transfer visualization
- GraphQL client with intelligent caching
- Top traders analysis
- CSV export functionality
- Interactive button callbacks
- Hybrid RPC/Subgraph transfer tracking

**Changed:**
- Updated to The Graph V2 endpoints
- Improved error handling and logging
- Enhanced command help documentation

**Fixed:**
- Rate limiting issues with RPC providers
- Memory leaks in chart generation
- Cache invalidation bugs

### v2.0.0 (2026-01-15)
- Initial release with basic blockchain commands
- Wallet tracking
- Balance checking
- Gas prices

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) - Telegram Bot API wrapper
- [web3.py](https://github.com/ethereum/web3.py) - Ethereum Python library
- [The Graph](https://thegraph.com/) - Decentralized indexing protocol
- [matplotlib](https://matplotlib.org/) - Python plotting library
- [pandas](https://pandas.pydata.org/) - Data analysis library

## 📧 Contact

**Developer:** Iv Ple  
**Telegram:** [@ivivple](https://t.me/ivivple)  
**Issues:** [GitHub Issues](https://github.com/yourusername/web3-telegram-bot/issues)

## ⭐ Star History

If you find this project useful, please consider giving it a star!

---

Made with ❤️ for the Ethereum community
