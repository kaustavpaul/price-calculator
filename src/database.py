import sqlite3
import pandas as pd
import streamlit as st
from typing import Dict, List, Optional, Tuple, Any

DB_NAME = 'price_calculator.db'

def get_db_connection() -> Optional[sqlite3.Connection]:
    """Get a connection to the SQLite database."""
    try:
        return sqlite3.connect(DB_NAME)
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return None

def init_database() -> bool:
    """Initialize the SQLite database with required tables."""
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS items (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    category TEXT DEFAULT 'Uncategorized',
                    price REAL NOT NULL,
                    price_currency TEXT NOT NULL,
                    additional_cost REAL NOT NULL DEFAULT 0.0,
                    additional_cost_currency TEXT,
                    shipping REAL NOT NULL,
                    shipping_currency TEXT NOT NULL,
                    delivery_charge_us REAL NOT NULL DEFAULT 15.0,
                    marketing_budget REAL NOT NULL DEFAULT 0.0,
                    import_cost REAL NOT NULL,
                    import_currency TEXT NOT NULL,
                    margin REAL NOT NULL,
                    margin_type TEXT NOT NULL,
                    final_currency TEXT NOT NULL,
                    final_price REAL NOT NULL,
                    final_price_usd REAL NOT NULL DEFAULT 0.0,
                    final_inr_with_budget_and_margin REAL NOT NULL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Migration: add category if missing
            cursor.execute("PRAGMA table_info(items)")
            columns = [column[1] for column in cursor.fetchall()]
            if 'category' not in columns:
                cursor.execute('ALTER TABLE items ADD COLUMN category TEXT DEFAULT "Uncategorized"')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY,
                    tax_rate REAL NOT NULL DEFAULT 8.25,
                    usd_to_inr_rate REAL NOT NULL DEFAULT 83.25,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('SELECT COUNT(*) FROM settings')
            if cursor.fetchone()[0] == 0:
                cursor.execute('INSERT INTO settings (id, tax_rate, usd_to_inr_rate) VALUES (1, 8.25, 83.25)')
            conn.commit()
        return True
    except Exception as e:
        st.error(f"Database initialization error: {e}")
        return False

def get_settings() -> Dict[str, float]:
    """Retrieve settings from DB."""
    try:
        with get_db_connection() as conn:
            if conn is None: return {'tax_rate': 8.25, 'usd_to_inr_rate': 83.25}
            df = pd.read_sql_query('SELECT * FROM settings WHERE id = 1', conn)
            if df.empty: return {'tax_rate': 8.25, 'usd_to_inr_rate': 83.25}
            return {
                'tax_rate': float(df.iloc[0]['tax_rate']),
                'usd_to_inr_rate': float(df.iloc[0]['usd_to_inr_rate'])
            }
    except Exception as e:
        st.error(f"Error getting settings: {e}")
        return {'tax_rate': 8.25, 'usd_to_inr_rate': 83.25}

def update_settings(tax_rate: float, usd_to_inr_rate: float) -> bool:
    """Update settings in DB."""
    try:
        with get_db_connection() as conn:
            if conn is None: return False
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE settings SET tax_rate = ?, usd_to_inr_rate = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE id = 1
            ''', (tax_rate, usd_to_inr_rate))
            conn.commit()
        return True
    except Exception as e:
        st.error(f"Error updating settings: {e}")
        return False

def get_all_items() -> pd.DataFrame:
    """Get all items from DB."""
    try:
        with get_db_connection() as conn:
            if conn is None: return pd.DataFrame()
            return pd.read_sql_query('SELECT * FROM items ORDER BY created_at DESC', conn)
    except Exception as e:
        st.error(f"Error getting items: {e}")
        return pd.DataFrame()

def add_item(item_data: Dict[str, Any]) -> bool:
    """Add a new item to DB."""
    try:
        with get_db_connection() as conn:
            if conn is None: return False
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO items (
                    id, name, category, price, price_currency, additional_cost, additional_cost_currency,
                    shipping, shipping_currency, delivery_charge_us, marketing_budget,
                    import_cost, import_currency, margin, margin_type, final_currency,
                    final_price, final_price_usd, final_inr_with_budget_and_margin, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', (
                item_data['id'], item_data['name'], item_data['category'], item_data['price'], item_data['price_currency'],
                item_data['additional_cost'], item_data['additional_cost_currency'],
                item_data['shipping'], item_data['shipping_currency'], item_data['delivery_charge_us'], item_data['marketing_budget'],
                item_data['import_cost'], item_data['import_currency'], item_data['margin'], item_data['margin_type'],
                item_data['final_currency'], item_data['final_price'], item_data['final_price_usd'], item_data['final_inr_with_budget_and_margin']
            ))
            conn.commit()
        return True
    except Exception as e:
        st.error(f"Error adding item: {e}")
        return False

def update_item_field(item_id: str, field: str, value: Any) -> bool:
    """Update a single field for an item."""
    try:
        with get_db_connection() as conn:
            if conn is None: return False
            cursor = conn.cursor()
            cursor.execute(f'UPDATE items SET {field} = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?', (value, item_id))
            conn.commit()
        return True
    except Exception as e:
        st.error(f"Error updating field: {e}")
        return False

def delete_item(item_id: str) -> bool:
    """Delete an item by ID."""
    try:
        with get_db_connection() as conn:
            if conn is None: return False
            cursor = conn.cursor()
            cursor.execute('DELETE FROM items WHERE id = ?', (item_id,))
            conn.commit()
        return True
    except Exception as e:
        st.error(f"Error deleting item: {e}")
        return False

def clear_all_items() -> bool:
    """Clear all items."""
    try:
        with get_db_connection() as conn:
            if conn is None: return False
            cursor = conn.cursor()
            cursor.execute('DELETE FROM items')
            conn.commit()
        return True
    except Exception as e:
        st.error(f"Error clearing items: {e}")
        return False
