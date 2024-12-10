import sqlite3
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from contextlib import contextmanager

class Database:
    """
    Manages database operations for the CDP agent system.
    Handles transaction records, wallet data, and performance metrics.
    """
    def __init__(self, db_path: str = 'cdp_agent.db'):
        self.db_path = db_path
        self.initialize_database()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # This allows us to access columns by name
        return conn

    def initialize_database(self) -> None:
        """
        Initializes the database with required tables for tracking transactions,
        wallet operations, and performance metrics.
        """
        with self.get_connection() as conn:
            # Transactions table for blockchain operations
            conn.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    wallet_address TEXT NOT NULL,
                    operation_type TEXT NOT NULL,
                    network TEXT NOT NULL,
                    status TEXT NOT NULL,
                    tx_hash TEXT,
                    block_number INTEGER,
                    gas_used REAL,
                    amount REAL,
                    token_address TEXT,
                    recipient_address TEXT,
                    details TEXT,
                    error_message TEXT
                )
            """)

            # Wallet data table for storing wallet information
            conn.execute("""
                CREATE TABLE IF NOT EXISTS wallets (
                    address TEXT PRIMARY KEY,
                    network TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_active DATETIME,
                    balance TEXT,
                    tokens TEXT,
                    metadata TEXT
                )
            """)

            # Performance metrics table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    operation_type TEXT NOT NULL,
                    duration_ms INTEGER,
                    success BOOLEAN,
                    error_type TEXT,
                    details TEXT
                )
            """)

    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections ensuring proper resource handling.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise DatabaseError(f"Database operation failed: {str(e)}")
        finally:
            conn.close()

    def record_transaction(self, transaction_data: Dict[str, Any]) -> int:
        """Records a blockchain transaction with complete details.
        Returns the ID of the inserted record."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO transactions (
                    wallet_address, operation_type, network, status,
                    tx_hash, block_number, gas_used, amount,
                    token_address, recipient_address, details, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                transaction_data.get('wallet_address'),
                transaction_data.get('operation_type'),
                transaction_data.get('network'),
                transaction_data.get('status'),
                transaction_data.get('tx_hash'),
                transaction_data.get('block_number'),
                transaction_data.get('gas_used'),
                transaction_data.get('amount'),
                transaction_data.get('token_address'),
                transaction_data.get('recipient_address'),
                json.dumps(transaction_data.get('details', {})),
                transaction_data.get('error_message')
            ))
            return cursor.lastrowid

    def update_wallet(self, wallet_data: Dict[str, Any]) -> None:
        """
        Updates or creates a wallet record with current information.
        """
        with self.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO wallets (
                    address, network, last_active, balance, tokens, metadata
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                wallet_data['address'],
                wallet_data['network'],
                datetime.now().isoformat(),
                json.dumps(wallet_data.get('balance', {})),
                json.dumps(wallet_data.get('tokens', [])),
                json.dumps(wallet_data.get('metadata', {}))
            ))

    def record_metric(self, metric_data: Dict[str, Any]) -> None:
        """
        Records performance metrics for operation analysis.
        """
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO performance_metrics (
                    operation_type, duration_ms, success, error_type, details
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                metric_data['operation_type'],
                metric_data['duration_ms'],
                metric_data['success'],
                metric_data.get('error_type'),
                json.dumps(metric_data.get('details', {}))
            ))

    def get_transaction_history(
        self,
        wallet_address: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Retrieves transaction history with optional wallet filtering.
        """
        with self.get_connection() as conn:
            query = "SELECT * FROM transactions"
            params = []
            
            if wallet_address:
                query += " WHERE wallet_address = ?"
                params.append(wallet_address)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def save_wallet_data(self, wallet_data: Dict[str, Any]) -> None:
        """
        Saves wallet data to the database.
        """
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO wallets (address, network, created_at, balance, tokens, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                wallet_data['address'],
                wallet_data['network'],
                datetime.now().isoformat(),
                json.dumps(wallet_data.get('balance', {})),
                json.dumps(wallet_data.get('tokens', [])),
                json.dumps(wallet_data.get('metadata', {}))
            ))

    def get_wallet_details(self, address: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves detailed wallet information.
        """
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM wallets WHERE address = ?",
                (address,)
            )
            row = cursor.fetchone()
            if row:
                return {
                    "address": row["address"],
                    "network": row["network"],
                    "created_at": row["created_at"],
                    "balance": json.loads(row["balance"]),
                    "tokens": json.loads(row["tokens"]),
                    "metadata": json.loads(row["metadata"])
                }
            return None

    def get_performance_metrics(
        self,
        operation_type: Optional[str] = None,
        time_range_hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Retrieves performance metrics for analysis.
        """
        with self.get_connection() as conn:
            query = """
                SELECT * FROM performance_metrics
                WHERE timestamp >= datetime('now', ?)
            """
            params = [f'-{time_range_hours} hours']
            
            if operation_type:
                query += " AND operation_type = ?"
                params.append(operation_type)
            
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

class DatabaseError(Exception):
    """Custom exception for database-related errors."""
    pass