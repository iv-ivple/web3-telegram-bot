# Web3 Telegram Bot

A Telegram bot for interacting with Ethereum blockchain - check balances, gas prices, token prices, and track wallets.

## Features

✅ Check ETH balances
✅ Get current gas prices
✅ Fetch token prices from DEXs
✅ Track multiple wallets
✅ Inline keyboards for quick actions
✅ Rate limiting and error handling

## Commands

- `/start` - Welcome message and bot introduction
- `/help` - Show all available commands
- `/balance <address>` - Check ETH balance
- `/gas` - Get current gas prices
- `/price <token>` - Get token price (ETH, BTC, USDC, etc.)
- `/track <address> [label]` - Add wallet to tracking
- `/mywallets` - Show all tracked wallets
- `/untrack <address>` - Stop tracking wallet

## Setup

### Prerequisites

- Python 3.10+
- Telegram account
- Ethereum RPC endpoint (Infura/Alchemy)

### Installation

1. Clone repository:
```bash
git clone <your-repo>
cd telegram-web3-bot
```

2. Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env with your values
```

5. Run the bot:
```bash
python bot.py
```

## Configuration

Required environment variables in `.env`:
```env
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
RPC_URL=your_ethereum_rpc_url
ADMIN_USER_ID=your_telegram_user_id
```

## Project Structure
telegram-web3-bot/
├── bot.py                 # Main bot application
├── config.py              # Configuration management
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (not committed)
├── handlers/
│   ├── basic.py          # Basic commands (/start, /help)
│   ├── blockchain.py     # Blockchain commands
│   └── callbacks.py      # Inline keyboard handlers
├── utils/
│   ├── web3_helper.py    # Web3 utilities
│   ├── validators.py     # Input validation
│   ├── database.py       # Database management
│   └── rate_limiter.py   # Rate limiting
├── data/
│   └── bot_data.db       # SQLite database
└── tests/
└── test_bot.py       # Unit tests

## Development

Run tests:
```bash
pytest tests/
```

Check code style:
```bash
flake8 .
black .
```

## Security

- Bot token is stored in environment variables
- Input validation on all user inputs
- Rate limiting to prevent abuse
- SQL injection prevention with parameterized queries

## License

MIT

## Contact

Iv Ple - @ivivple
