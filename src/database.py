import sqlite3
import pandas as pd
from sqlalchemy import create_engine, text

DB_PATH = 'compactDocu.db'
ENGINE = create_engine(f'sqlite:///{DB_PATH}')

def init_db():
    """Initializes the database with required tables."""
    with ENGINE.connect() as conn:
        # Table for Waste/By-product Disposal (부산물 매각 및 폐기물 처리)
        conn.execute(text('''
            CREATE TABLE IF NOT EXISTS disposal_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_date DATE,
                vendor TEXT,
                item TEXT,
                unit TEXT,
                unit_price REAL,
                quantity REAL,
                amount REAL,
                category TEXT,
                vehicle TEXT,
                manager TEXT,
                note TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        '''))
        
        # Table for Gate Pass (반출증)
        conn.execute(text('''
            CREATE TABLE IF NOT EXISTS gate_pass_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_date DATE,
                vendor TEXT,
                content TEXT,
                quantity REAL,
                note TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        '''))

def get_connection():
    """Returns a raw SQLite connection."""
    return sqlite3.connect(DB_PATH)

def save_dataframe(df, table_name):
    """Saves a Pandas DataFrame to the database."""
    # Get actual table columns from DB
    try:
        # Read 0 rows to get columns
        existing_cols = pd.read_sql(f"SELECT * FROM {table_name} LIMIT 0", ENGINE).columns.tolist()
        
        # Filter DF columns to keep only those that exist in the table
        cols_to_keep = [c for c in df.columns if c in existing_cols]
        df = df[cols_to_keep]
        
        df.to_sql(table_name, ENGINE, if_exists='append', index=False)
    except Exception as e:
        print(f"Error saving to {table_name}: {e}")
        raise e

def load_data(table_name):
    """Loads data from a table into a DataFrame."""
    return pd.read_sql(f"SELECT * FROM {table_name} ORDER BY transaction_date DESC", ENGINE)

def clear_table(table_name):
    """Clears all data from a table."""
    with ENGINE.connect() as conn:
        conn.execute(text(f"DELETE FROM {table_name}"))
        conn.commit()
