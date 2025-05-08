# Copyright ©️ 2025 THEETOX
"""
Database Module
Handles database operations for storing coin information.
"""

import os
import sqlite3
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Database file path
DB_PATH = os.path.join(os.path.dirname(__file__), '../../database/memecoin.db')

def setup_database():
    """
    Set up the database and create tables if they don't exist.
    """
    try:
        # Ensure the database directory exists
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        
        # Connect to database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Create coins table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS coins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            symbol TEXT NOT NULL,
            supply INTEGER NOT NULL,
            logo_path TEXT NOT NULL,
            contract_address TEXT NOT NULL,
            ref_id TEXT NOT NULL,
            trading_enabled BOOLEAN DEFAULT 0,
            cmc_submitted BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create transactions table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            coin_id INTEGER NOT NULL,
            tx_type TEXT NOT NULL,
            tx_hash TEXT NOT NULL,
            amount REAL NOT NULL,
            status TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (coin_id) REFERENCES coins (id)
        )
        ''')
        
        # Commit changes and close connection
        conn.commit()
        conn.close()
        
        logger.info("Database setup complete")
        
    except Exception as e:
        logger.error(f"Error setting up database: {e}")

def add_new_coin(user_id, name, symbol, supply, logo_path, contract_address, ref_id, trading_enabled=False):
    """
    Add a new coin to the database.
    
    Args:
        user_id: The Telegram user ID
        name: The name of the coin
        symbol: The symbol of the coin
        supply: The total supply of the coin
        logo_path: The path to the logo file
        contract_address: The contract address
        ref_id: The reference ID
        trading_enabled: Whether trading is enabled
        
    Returns:
        The coin ID if successful, None otherwise
    """
    try:
        # Connect to database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Insert new coin
        cursor.execute('''
        INSERT INTO coins (user_id, name, symbol, supply, logo_path, contract_address, ref_id, trading_enabled)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, name, symbol, supply, logo_path, contract_address, ref_id, trading_enabled))
        
        # Get the coin ID
        coin_id = cursor.lastrowid
        
        # Commit changes and close connection
        conn.commit()
        conn.close()
        
        logger.info(f"Added new coin {name} ({symbol}) for user {user_id}")
        return coin_id
        
    except Exception as e:
        logger.error(f"Error adding new coin: {e}")
        return None

def get_user_coin(user_id):
    """
    Get a user's coin from the database.
    
    Args:
        user_id: The Telegram user ID
        
    Returns:
        The coin data as a dictionary if found, None otherwise
    """
    try:
        # Connect to database
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        cursor = conn.cursor()
        
        # Get the user's coin
        cursor.execute('''
        SELECT * FROM coins WHERE user_id = ? ORDER BY created_at DESC LIMIT 1
        ''', (user_id,))
        
        # Fetch the result
        row = cursor.fetchone()
        
        # Close connection
        conn.close()
        
        if row:
            return dict(row)
        else:
            return None
        
    except Exception as e:
        logger.error(f"Error getting user coin: {e}")
        return None

def update_coin_status(user_id, contract_address, trading_enabled=None, cmc_submitted=None):
    """
    Update a coin's status in the database.
    
    Args:
        user_id: The Telegram user ID
        contract_address: The contract address
        trading_enabled: Whether trading is enabled
        cmc_submitted: Whether the coin has been submitted to CMC
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Connect to database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Build the update query
        query = "UPDATE coins SET "
        params = []
        
        if trading_enabled is not None:
            query += "trading_enabled = ?, "
            params.append(trading_enabled)
        
        if cmc_submitted is not None:
            query += "cmc_submitted = ?, "
            params.append(cmc_submitted)
        
        # Remove the trailing comma and space
        query = query.rstrip(", ")
        
        # Add the WHERE clause
        query += " WHERE user_id = ? AND contract_address = ?"
        params.extend([user_id, contract_address])
        
        # Execute the update
        cursor.execute(query, params)
        
        # Commit changes and close connection
        conn.commit()
        conn.close()
        
        logger.info(f"Updated coin status for user {user_id}, contract {contract_address}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating coin status: {e}")
        return False

def add_transaction(user_id, coin_id, tx_type, tx_hash, amount, status):
    """
    Add a new transaction to the database.
    
    Args:
        user_id: The Telegram user ID
        coin_id: The coin ID
        tx_type: The transaction type (unlock, cmc, etc.)
        tx_hash: The transaction hash
        amount: The transaction amount
        status: The transaction status
        
    Returns:
        The transaction ID if successful, None otherwise
    """
    try:
        # Connect to database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Insert new transaction
        cursor.execute('''
        INSERT INTO transactions (user_id, coin_id, tx_type, tx_hash, amount, status)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, coin_id, tx_type, tx_hash, amount, status))
        
        # Get the transaction ID
        tx_id = cursor.lastrowid
        
        # Commit changes and close connection
        conn.commit()
        conn.close()
        
        logger.info(f"Added new transaction {tx_hash} for user {user_id}")
        return tx_id
        
    except Exception as e:
        logger.error(f"Error adding new transaction: {e}")
        return None
