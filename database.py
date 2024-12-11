import sqlite3
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from contextlib import contextmanager

class Database:
    """
    Manages database operations for the CDP agent system.
    """
    def __init__(self, db_path: str = 'cdp_agent.db'):
        self.db_path = db_path
        self.initialize_database()

    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections.
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

    def initialize_database(self) -> None:
        """
        Initializes the database with required tables.
        """
        with self.get_connection() as conn:
            # Transactions table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    wallet_address TEXT,
                    operation_type TEXT,
                    network TEXT,
                    status TEXT,
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

            # Wallets table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS wallets (
                    address TEXT PRIMARY KEY,
                    network TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_active DATETIME,
                    balance TEXT,
                    tokens TEXT,
                    metadata TEXT
                )
            """)

            # Metrics table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    operation_type TEXT,
                    duration_ms INTEGER,
                    success BOOLEAN,
                    error_type TEXT,
                    details TEXT
                )
            """)

    def record_transaction(self, transaction_data: Dict[str, Any]) -> int:
        """Records a blockchain transaction."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO transactions (
                    wallet_address, operation_type, network, status,
                    tx_hash, block_number, gas_used, amount,
                    token_address, recipient_address, details, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(transaction_data.get('wallet_address', '')),
                str(transaction_data.get('operation_type', '')),
                str(transaction_data.get('network', '')),
                str(transaction_data.get('status', '')),
                str(transaction_data.get('tx_hash', '')),
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
        """Updates wallet information."""
        with self.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO wallets (
                    address, network, last_active, balance, tokens, metadata
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                str(wallet_data.get('address', '')),
                str(wallet_data.get('network', '')),
                datetime.now().isoformat(),
                json.dumps(wallet_data.get('balance', {})),
                json.dumps(wallet_data.get('tokens', [])),
                json.dumps(wallet_data.get('metadata', {}))
            ))

    def record_metric(self, metric_data: Dict[str, Any]) -> None:
        """Records performance metrics."""
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO performance_metrics (
                    operation_type, duration_ms, success, error_type, details
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                str(metric_data.get('operation_type', '')),
                metric_data.get('duration_ms', 0),
                bool(metric_data.get('success', False)),
                str(metric_data.get('error_type', '')),
                json.dumps(metric_data.get('details', {}))
            ))

    def get_transaction_history(
        self,
        wallet_address: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Gets transaction history."""
        with self.get_connection() as conn:
            query = "SELECT * FROM transactions"
            params = []
            
            if wallet_address:
                query += " WHERE wallet_address = ?"
                params.append(wallet_address)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor = conn.execute(query, params)
            return [dict(zip([column[0] for column in cursor.description], row)) 
                   for row in cursor.fetchall()]

    def get_wallet_details(self, address: str) -> Optional[Dict[str, Any]]:
        """Gets wallet details."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM wallets WHERE address = ?",
                (address,)
            )
            row = cursor.fetchone()
            if row:
                column_names = [column[0] for column in cursor.description]
                result = dict(zip(column_names, row))
                result['balance'] = json.loads(result.get('balance', '{}'))
                result['tokens'] = json.loads(result.get('tokens', '[]'))
                result['metadata'] = json.loads(result.get('metadata', '{}'))
                return result
            return None
    def save_wallet_data(self, wallet_data: Dict[str, Any]) -> None:
        """Saves wallet data to the database."""
        try:
            # If parsing JSON string
            if isinstance(wallet_data, str):
                try:
                    wallet_json = json.loads(wallet_data)
                except json.JSONDecodeError:
                    raise DatabaseError("Invalid JSON in wallet data")
            else:
                wallet_json = wallet_data

            # Extract address or use default_address_id
            address = wallet_json.get('address') or wallet_json.get('default_address_id')
            if not address:
                raise DatabaseError("No valid address found in wallet data")

            with self.get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO wallets 
                    (address, network, created_at, balance, tokens, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    address,  # Address
                    wallet_json.get('network', 'base-sepolia'),  # Network
                    datetime.now().isoformat(),  # Created at
                    json.dumps(wallet_json.get('balance', {})),  # Balance
                    json.dumps(wallet_json.get('tokens', [])),  # Tokens
                    json.dumps(wallet_json)  # Full metadata
                ))
        except Exception as e:
            raise DatabaseError(f"Failed to save wallet data: {str(e)}")

class DatabaseError(Exception):
    """Custom exception for database-related errors."""
    pass