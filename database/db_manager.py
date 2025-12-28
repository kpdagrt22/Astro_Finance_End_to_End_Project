# database/db_manager.py - Database Operations
import sqlite3
from datetime import datetime

class DatabaseManager:
    """Manage SQLite database"""
    
    def __init__(self):
        self.db_path = 'database/subscribers.db'
        self.initialize_db()
    
    def initialize_db(self):
        """Create tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscribers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_premium BOOLEAN DEFAULT 0,
            referral_code TEXT
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_subscriber(self, email):
        """Add new subscriber"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('INSERT INTO subscribers (email) VALUES (?)', (email,))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False  # Already exists
