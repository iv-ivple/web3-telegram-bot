"""
Database management for tracked wallets.
Uses SQLite (you know this from Week 6!).
"""
import sqlite3
from datetime import datetime
from typing import List, Optional

class Database:
    """Database handler for bot data."""
    
    def __init__(self, db_path: str):
        """Initialize database connection."""
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Create tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tracked_wallets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    wallet_address TEXT NOT NULL,
                    label TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_balance REAL,
                    UNIQUE(user_id, wallet_address)
                )
            """)
            conn.commit()
    
    def add_tracked_wallet(
        self,
        user_id: int,
        wallet_address: str,
        label: Optional[str] = None
    ) -> bool:
        """Add a wallet to tracking list."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO tracked_wallets (user_id, wallet_address, label)
                    VALUES (?, ?, ?)
                    """,
                    (user_id, wallet_address, label)
                )
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False  # Already tracking
    
    def get_tracked_wallets(self, user_id: int) -> List[dict]:
        """Get all tracked wallets for a user."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT * FROM tracked_wallets
                WHERE user_id = ?
                ORDER BY created_at DESC
                """,
                (user_id,)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def remove_tracked_wallet(self, user_id: int, wallet_address: str) -> bool:
        """Remove a wallet from tracking."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                DELETE FROM tracked_wallets
                WHERE user_id = ? AND wallet_address = ?
                """,
                (user_id, wallet_address)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def update_last_balance(
        self,
        user_id: int,
        wallet_address: str,
        balance: float
    ):
        """Update the last known balance for a wallet."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                UPDATE tracked_wallets
                SET last_balance = ?
                WHERE user_id = ? AND wallet_address = ?
                """,
                (balance, user_id, wallet_address)
            )
            conn.commit()

# Global database instance
from config import Config
db = Database(Config.DATABASE_PATH)
