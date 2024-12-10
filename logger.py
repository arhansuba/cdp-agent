import os
import json
import sqlite3
from datetime import datetime
from typing import Dict, Any, Optional
from contextlib import contextmanager

class TransactionLogger:
    """
    Handles logging of blockchain transactions and agent operations.
    Stores logs in both SQLite database and text file formats.
    """

    def __init__(self, db_path: str = 'transactions.db', log_dir: str = 'logs'):
        self.db_path = db_path
        self.log_dir = log_dir
        self._initialize_logging()

    def _initialize_logging(self) -> None:
        """Initialize database tables and log directory."""
        # Create logs directory if it doesn't exist
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

        # Initialize database
        with self._get_db_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    operation_type TEXT NOT NULL,
                    network TEXT NOT NULL,
                    wallet_address TEXT NOT NULL,
                    status TEXT NOT NULL,
                    tx_hash TEXT,
                    block_number INTEGER,
                    gas_used INTEGER,
                    error_message TEXT,
                    details TEXT
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    event_type TEXT NOT NULL,
                    wallet_address TEXT NOT NULL,
                    details TEXT,
                    status TEXT
                )
            """)

    @contextmanager
    def _get_db_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def log_transaction(
        self,
        operation_type: str,
        network: str,
        wallet_address: str,
        status: str,
        tx_hash: Optional[str] = None,
        block_number: Optional[int] = None,
        gas_used: Optional[int] = None,
        error_message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log a blockchain transaction with detailed information.
        """
        with self._get_db_connection() as conn:
            conn.execute("""
                INSERT INTO transactions (
                    operation_type, network, wallet_address, status,
                    tx_hash, block_number, gas_used, error_message, details
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                operation_type, network, wallet_address, status,
                tx_hash, block_number, gas_used, error_message,
                json.dumps(details) if details else None
            ))

        # Also write to text log file
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'operation_type': operation_type,
            'network': network,
            'wallet_address': wallet_address,
            'status': status,
            'tx_hash': tx_hash,
            'block_number': block_number,
            'gas_used': gas_used,
            'error_message': error_message,
            'details': details
        }
        
        self._write_to_log_file('transactions.log', log_entry)

    def log_agent_event(
        self,
        event_type: str,
        wallet_address: str,
        details: Optional[Dict[str, Any]] = None,
        status: Optional[str] = None
    ) -> None:
        """
        Log agent-related events and operations.
        """
        with self._get_db_connection() as conn:
            conn.execute("""
                INSERT INTO agent_events (
                    event_type, wallet_address, details, status
                ) VALUES (?, ?, ?, ?)
            """, (
                event_type,
                wallet_address,
                json.dumps(details) if details else None,
                status
            ))

        # Write to agent events log file
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'wallet_address': wallet_address,
            'details': details,
            'status': status
        }
        
        self._write_to_log_file('agent_events.log', log_entry)

    def _write_to_log_file(self, filename: str, log_entry: Dict[str, Any]) -> None:
        """Write a log entry to the specified log file."""
        log_path = os.path.join(self.log_dir, filename)
        with open(log_path, 'a') as f:
            f.write(f"{json.dumps(log_entry)}\n")

    def get_transaction_history(
        self,
        wallet_address: Optional[str] = None,
        limit: int = 100
    ) -> list:
        """
        Retrieve transaction history with optional filtering by wallet address.
        """
        with self._get_db_connection() as conn:
            query = "SELECT * FROM transactions"
            params = []
            
            if wallet_address:
                query += " WHERE wallet_address = ?"
                params.append(wallet_address)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_agent_events(
        self,
        wallet_address: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100
    ) -> list:
        """
        Retrieve agent events with optional filtering.
        """
        with self._get_db_connection() as conn:
            query = "SELECT * FROM agent_events"
            params = []
            conditions = []
            
            if wallet_address:
                conditions.append("wallet_address = ?")
                params.append(wallet_address)
            
            if event_type:
                conditions.append("event_type = ?")
                params.append(event_type)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]