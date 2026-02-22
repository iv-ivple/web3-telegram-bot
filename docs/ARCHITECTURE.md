# Architecture Documentation

## System Overview

The Web3 Telegram Bot is built with a modular architecture that separates concerns between user interface (Telegram), business logic (handlers), data fetching (analytics), and external APIs (The Graph, RPC providers).

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Telegram User                            │
│                    (Mobile/Desktop Client)                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ Commands & Interactions
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Telegram Bot API                             │
│                  (python-telegram-bot library)                   │
│                                                                   │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────────┐ │
│  │ Command Router │  │ Callback Router│  │  Error Handler   │ │
│  └────────┬───────┘  └────────┬───────┘  └────────┬─────────┘ │
└───────────┼──────────────────┼─────────────────────┼───────────┘
            │                  │                      │
            ▼                  ▼                      ▼
┌───────────────────────────────────────────────────────────────┐
│                         Handlers Layer                         │
│  ┌─────────────────┐  ┌──────────────────┐  ┌──────────────┐│
│  │  Basic Handlers │  │Analytics Handlers│  │Callback      ││
│  │  - /start       │  │  - /analytics    │  │Handlers      ││
│  │  - /help        │  │  - /wallet_report│  │  - Buttons   ││
│  │  - /balance     │  │  - Chart Gen     │  │  - Export    ││
│  │  - /gas         │  │  - CSV Export    │  │  - Refresh   ││
│  └─────────┬───────┘  └──────────┬───────┘  └──────┬───────┘│
└────────────┼──────────────────────┼──────────────────┼────────┘
             │                      │                  │
             ▼                      ▼                  ▼
┌────────────────────────────────────────────────────────────────┐
│                      Business Logic Layer                       │
│  ┌─────────────────┐  ┌──────────────────┐  ┌──────────────┐ │
│  │  Web3Helper     │  │ TokenAnalytics   │  │ Transfers    │ │
│  │  - Balance      │  │  - Price History │  │Analytics     │ │
│  │  - Gas Prices   │  │  - Volume Data   │  │  - RPC       │ │
│  │  - Validators   │  │  - Top Traders   │  │  - Subgraph  │ │
│  └────────┬────────┘  └──────────┬───────┘  └──────┬───────┘ │
└───────────┼──────────────────────┼──────────────────┼─────────┘
            │                      │                  │
            │                      ▼                  │
            │            ┌────────────────┐           │
            │            │ GraphClient    │           │
            │            │ (with caching) │           │
            │            └────────┬───────┘           │
            │                     │                   │
            ▼                     ▼                   ▼
┌────────────────────────────────────────────────────────────────┐
│                       External APIs Layer                       │
│  ┌─────────────────┐  ┌──────────────────┐  ┌──────────────┐ │
│  │   RPC Provider  │  │  The Graph API   │  │  Database    │ │
│  │  - Infura       │  │  - Uniswap V3    │  │  - SQLite    │ │
│  │  - Alchemy      │  │  - Subgraph      │  │  - Tracking  │ │
│  │  - eth_call     │  │  - GraphQL       │  │  - Cache     │ │
│  └────────┬────────┘  └──────────┬───────┘  └──────┬───────┘ │
└───────────┼──────────────────────┼──────────────────┼─────────┘
            │                      │                  │
            ▼                      ▼                  ▼
      ┌──────────────────────────────────────────────────┐
      │            Ethereum Mainnet                       │
      │  - Smart Contracts                               │
      │  - Token Balances                                │
      │  - Transaction History                           │
      └──────────────────────────────────────────────────┘
```

## Component Details

### 1. Telegram Bot Layer

**Purpose:** Handle all Telegram-specific functionality

**Components:**
- `Application` - Main bot application from python-telegram-bot
- `CommandHandler` - Routes commands to appropriate handlers
- `CallbackQueryHandler` - Handles inline button interactions
- `ErrorHandler` - Catches and logs errors

**Files:**
- `bot_updated.py` - Main entry point

**Key Features:**
- Async/await for non-blocking I/O
- Automatic polling for updates
- Built-in rate limiting
- Error recovery

### 2. Handlers Layer

**Purpose:** Process user commands and generate responses

#### Basic Handlers (`handlers/basic.py`)
```
/start  → Welcome message with command overview
/help   → Detailed command documentation
```

#### Blockchain Handlers (`handlers/blockchain.py`)
```
/balance → Web3Helper → RPC → ETH Balance
/gas     → Web3Helper → RPC → Gas Prices
/price   → Price API → Token Price
/track   → Database → Save Wallet
```

#### Analytics Handlers (`handlers/analytics_commands.py`)
```
/analytics      → TokenAnalytics → Generate Chart → Send Photo
/wallet_report  → TransfersAnalytics → Generate Chart → Send Photo
```

**Flow Example - `/analytics`:**
```
User sends: /analytics 0xC02a...Cc2 7

1. analytics_command() triggered
2. Validate token address
3. Send "⏳ Generating..." message
4. Call token_analytics.get_token_info()
5. Call token_analytics.get_price_history(days=7)
6. Call token_analytics.get_token_volume_24h()
7. Call token_analytics.get_top_traders()
8. Generate chart with _generate_analytics_chart()
9. Send photo with chart + statistics
10. Add interactive buttons
11. Delete "generating" message
12. Clean up temporary chart file
```

### 3. Analytics Layer

#### TokenAnalytics (`analytics/token_analytics.py`)

**Purpose:** Fetch and process token data from The Graph

**Methods:**
```python
get_token_info(address)           # Symbol, name, decimals
get_price_history(address, days)  # OHLC data
get_token_volume_24h(address)     # 24h volume
get_top_traders(address, limit)   # Most active traders
```

**Data Flow:**
```
TokenAnalytics → GraphClient → The Graph API → Parse → Cache → Return
```

**Caching:**
```python
Token Info:     24 hours (rarely changes)
Price History:  6 hours  (immutable historical data)
Current Price:  1 minute (volatile)
Volume:         5 minutes
```

#### TransfersAnalytics (`analytics/transfers_analytics.py`)

**Purpose:** Fetch token transfer data using hybrid approach

**Strategy:**
```
┌─────────────────────────────────────────────────┐
│              Transfer Query Strategy             │
├─────────────────────────────────────────────────┤
│                                                  │
│  Block Range < 10k blocks                       │
│  └─→ Use RPC only (fast for small ranges)       │
│                                                  │
│  Block Range > 10k blocks                       │
│  ├─→ Historical: Subgraph (fast, indexed)       │
│  └─→ Recent: RPC (real-time, accurate)          │
│                                                  │
│  No Subgraph Available                          │
│  └─→ Chunked RPC queries (with rate limiting)   │
│                                                  │
└─────────────────────────────────────────────────┘
```

**Methods:**
```python
get_transfers_hybrid()      # Smart query selection
get_transfer_summary()      # Complete wallet analysis
analyze_transfers()         # Statistics calculation
```

### 4. Data Access Layer

#### GraphClient (`utils/graph_helper.py`)

**Purpose:** GraphQL client with caching and retry logic

**Features:**
- Query caching with configurable TTL
- Automatic retry with exponential backoff
- Rate limiting per provider
- Error handling and logging
- Health checks

**Architecture:**
```
┌─────────────────────────────────────────────┐
│           GraphClient Request                │
└───────────────┬─────────────────────────────┘
                │
                ▼
        ┌──────────────┐
        │ Check Cache  │
        └──────┬───────┘
               │
        ┌──────┴──────┐
        │             │
    Hit │             │ Miss
        │             │
        ▼             ▼
┌─────────────┐  ┌────────────────┐
│Return Cached│  │  Rate Limiter  │
│   Result    │  └────────┬───────┘
└─────────────┘           │
                          ▼
                  ┌───────────────┐
                  │  HTTP Request │
                  │  to The Graph │
                  └───────┬───────┘
                          │
                  ┌───────┴───────┐
                  │               │
              Success             Fail
                  │               │
                  ▼               ▼
          ┌──────────────┐  ┌───────────┐
          │  Parse JSON  │  │   Retry   │
          │  Save Cache  │  │ (3 times) │
          │  Return Data │  └───────────┘
          └──────────────┘
```

**Cache Storage:**
```
cache/
├── a1b2c3d4...json.gz    # Compressed queries
├── e5f6g7h8...json.gz
└── ...

Format: MD5(query + variables) + .json.gz
```

#### Web3Helper (`utils/web3_helper.py`)

**Purpose:** Direct blockchain interactions

**Methods:**
```python
get_balance(address)       # ETH balance
get_gas_prices()          # Current gas
validate_address(addr)    # Checksumming
```

### 5. Storage Layer

#### Database (`utils/database.py`)

**Schema:**
```sql
CREATE TABLE tracked_wallets (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    wallet_address TEXT NOT NULL,
    label TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_user_wallets ON tracked_wallets(user_id);
```

**Usage:**
```python
db.add_wallet(user_id, address, label)
db.get_user_wallets(user_id)
db.remove_wallet(user_id, address)
```

#### Cache (`cache/`)

**File-based caching:**
```python
cache_helper.py:
  - QueryCache class
  - File-based storage
  - GZIP compression
  - Automatic cleanup
  - Size limits (100MB default)
```

## Data Flow Examples

### Example 1: /analytics Command

```
┌──────┐     ┌─────────┐     ┌──────────┐     ┌───────┐     ┌─────────┐
│ User │────>│ Telegram│────>│ Handler  │────>│Graph  │────>│The Graph│
└──────┘     └─────────┘     └──────────┘     │Client │     └─────────┘
   │              │                 │          └───┬───┘           │
   │              │                 │              │               │
   │         /analytics              │         Check Cache         │
   │         0xC02a...               │              │               │
   │              │                 │          Cache Miss          │
   │              │                 │              │               │
   │              │                 │          Query API           │
   │              │                 │              │<──────────────┤
   │              │                 │              │    JSON Data  │
   │              │                 │          Save Cache          │
   │              │                 │<─────────────┤               │
   │              │                 │  Return Data                 │
   │              │             Generate                            │
   │              │              Chart                              │
   │              │                 │                               │
   │              │<────────────────┤                               │
   │              │  Send Chart +                                   │
   │<─────────────┤  Statistics                                     │
   │   📊 Chart   │                                                 │
   │   💰 Stats   │                                                 │
   │   🔘 Buttons │                                                 │
   └──────────────┘                                                 │
```

### Example 2: /wallet_report Command

```
┌──────┐     ┌─────────┐     ┌──────────┐     ┌─────────┐     ┌──────┐
│ User │────>│Telegram │────>│ Handler  │────>│Transfers│────>│ RPC  │
└──────┘     └─────────┘     └──────────┘     │Analytics│     └──────┘
   │              │                 │          └────┬────┘         │
   │              │                 │               │              │
   │      /wallet_report             │          Strategy          │
   │      0x742d...                  │           Select            │
   │              │                 │               │              │
   │              │                 │      ┌────────┴────────┐     │
   │              │                 │      │                 │     │
   │              │                 │  Recent (RPC)   Historical   │
   │              │                 │      │         (Subgraph)    │
   │              │                 │      │                 │     │
   │              │                 │      ▼                 ▼     │
   │              │                 │  eth_getLogs      GraphQL   │
   │              │                 │      │                 │     │
   │              │                 │<─────┴─────────────────┘     │
   │              │                 │    Merged Results            │
   │              │             Analyze                             │
   │              │            Transfers                            │
   │              │             Generate                            │
   │              │              Chart                              │
   │              │<────────────────┤                               │
   │<─────────────┤  Send Chart +                                   │
   │   📊 Activity│  Statistics                                     │
   │   💼 Report  │  + Export CSV                                   │
   └──────────────┘                                                 │
```

## Scalability Considerations

### Current Architecture
- Single-process Python application
- File-based caching
- SQLite database
- Polling for updates

### Scaling Strategy

**Phase 1 (Current): < 100 users**
```
✓ File-based cache
✓ SQLite database
✓ Single bot instance
✓ Polling mode
```

**Phase 2: 100-1000 users**
```
→ Redis for caching
→ PostgreSQL database
→ Multiple bot instances with load balancer
→ Webhook mode
```

**Phase 3: 1000+ users**
```
→ Microservices architecture
→ Message queue (RabbitMQ/Kafka)
→ Distributed caching
→ Database replication
→ CDN for chart images
```

### Performance Optimization

**Current Bottlenecks:**
1. Chart generation (~500ms)
2. RPC queries for large ranges (~2s)
3. No horizontal scaling

**Optimizations Applied:**
- Query result caching (80% hit rate)
- Chart caching (not yet implemented)
- Rate limiting to prevent abuse
- Async I/O for non-blocking operations

## Security Architecture

```
┌─────────────────────────────────────────────────────┐
│               Security Layers                        │
├─────────────────────────────────────────────────────┤
│                                                      │
│  1. Input Validation                                │
│     └─→ Address validation (checksumming)           │
│     └─→ Command parameter validation                │
│     └─→ SQL injection prevention                    │
│                                                      │
│  2. Authentication                                  │
│     └─→ Telegram user ID verification               │
│     └─→ Bot token validation                        │
│                                                      │
│  3. Rate Limiting                                   │
│     └─→ API rate limiting (per provider)            │
│     └─→ User command rate limiting                  │
│     └─→ Per-IP rate limiting (future)               │
│                                                      │
│  4. Data Protection                                 │
│     └─→ Environment variables for secrets           │
│     └─→ No sensitive data in logs                   │
│     └─→ Encrypted database (future)                 │
│                                                      │
│  5. Error Handling                                  │
│     └─→ No system info in error messages            │
│     └─→ Comprehensive logging                       │
│     └─→ Automatic error recovery                    │
│                                                      │
└─────────────────────────────────────────────────────┘
```

## Technology Stack

```
┌─────────────────────────────────────────┐
│         Technology Stack                │
├─────────────────────────────────────────┤
│                                          │
│  Language: Python 3.10+                 │
│                                          │
│  Framework:                             │
│    └─→ python-telegram-bot 21.0         │
│                                          │
│  Blockchain:                            │
│    └─→ web3.py 6.15                     │
│                                          │
│  Data:                                  │
│    ├─→ pandas 2.2                       │
│    ├─→ SQLite 3                         │
│    └─→ Redis (planned)                  │
│                                          │
│  Visualization:                         │
│    ├─→ matplotlib 3.8                   │
│    └─→ numpy 1.26                       │
│                                          │
│  APIs:                                  │
│    ├─→ The Graph (GraphQL)              │
│    ├─→ Infura/Alchemy (RPC)             │
│    └─→ Telegram Bot API                 │
│                                          │
│  DevOps:                                │
│    ├─→ python-dotenv                    │
│    ├─→ pytest                           │
│    └─→ systemd (deployment)             │
│                                          │
└─────────────────────────────────────────┘
```

## Deployment Architecture

```
┌─────────────────────────────────────────────┐
│         Production Deployment                │
├─────────────────────────────────────────────┤
│                                              │
│  ┌──────────────────────────────────────┐  │
│  │        Linux Server (Ubuntu 24)      │  │
│  │                                      │  │
│  │  ┌────────────────────────────────┐ │  │
│  │  │      Systemd Service           │ │  │
│  │  │  bot.service                   │ │  │
│  │  │    │                           │ │  │
│  │  │    ├─→ Auto-restart            │ │  │
│  │  │    ├─→ Logging                 │ │  │
│  │  │    └─→ Resource limits         │ │  │
│  │  └────────────┬───────────────────┘ │  │
│  │               │                     │  │
│  │               ▼                     │  │
│  │  ┌────────────────────────────────┐ │  │
│  │  │     Python Virtual Env         │ │  │
│  │  │  ├─→ Isolated dependencies     │ │  │
│  │  │  └─→ bot_updated.py            │ │  │
│  │  └────────────┬───────────────────┘ │  │
│  │               │                     │  │
│  │               ▼                     │  │
│  │  ┌────────────────────────────────┐ │  │
│  │  │    File System                 │ │  │
│  │  │  ├─→ /cache (compressed)       │ │  │
│  │  │  ├─→ /data (SQLite DB)         │ │  │
│  │  │  └─→ /tmp (charts)             │ │  │
│  │  └────────────────────────────────┘ │  │
│  │                                      │  │
│  └──────────────────────────────────────┘  │
│                                              │
│  External Services:                         │
│  ├─→ Telegram Bot API (HTTPS)               │
│  ├─→ The Graph API (HTTPS)                  │
│  └─→ Infura/Alchemy RPC (HTTPS)             │
│                                              │
└─────────────────────────────────────────────┘
```

---

## Future Architecture Improvements

1. **Microservices** - Split into chart service, analytics service, bot service
2. **Message Queue** - RabbitMQ for async processing
3. **Redis** - Distributed caching
4. **Docker** - Containerization
5. **Kubernetes** - Orchestration
6. **CDN** - Chart image delivery
7. **WebSocket** - Real-time updates
8. **GraphQL Gateway** - Unified API layer

---

Last Updated: 2026-02-22
