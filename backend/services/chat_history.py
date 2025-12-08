import sqlite3
import json
import time
import os
import uuid
from typing import List, Dict, Optional

# Get retention hours from environment variable, default to 24 hours
RETENTION_HOURS = int(os.getenv('CHAT_HISTORY_RETENTION_HOURS', '24'))

class ChatHistoryService:
    def __init__(self, db_path: str = "chat_history.db"):
        # Ensure data directory exists
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.db_path = os.path.join(base_dir, "data", db_path)
        self._init_db()

    def _get_conn(self):
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def _init_db(self):
        """Creates the messages table if not exists."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp REAL NOT NULL,
                metadata TEXT
            )
        """)
        conn.commit()
        conn.close()

    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """Adds a message to the history."""
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            msg_id = str(uuid.uuid4())
            timestamp = time.time()
            meta_json = json.dumps(metadata) if metadata else None
            
            cursor.execute(
                "INSERT INTO messages (id, role, content, timestamp, metadata) VALUES (?, ?, ?, ?, ?)",
                (msg_id, role, content, timestamp, meta_json)
            )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"ERROR: Failed to save message: {e}")
            # Do not raise, just log. This prevents the whole query from failing if history fails.
            pass

    def get_recent_messages(self, hours: int = None) -> List[Dict]:
        """Retrieves messages from the last N hours."""
        if hours is None:
            hours = RETENTION_HOURS
        
        conn = self._get_conn()
        cursor = conn.cursor()
        
        cutoff = time.time() - (hours * 3600)
        
        cursor.execute(
            "SELECT id, role, content, timestamp, metadata FROM messages WHERE timestamp > ? ORDER BY timestamp ASC",
            (cutoff,)
        )
        
        rows = cursor.fetchall()
        conn.close()
        
        messages = []
        for row in rows:
            messages.append({
                "id": row[0],
                "role": row[1], # 'user' or 'bot' (mapped from sender)
                "text": row[2],
                "timestamp": row[3],
                "meta": json.loads(row[4]) if row[4] else {}
            })
        return messages

    def prune_old_messages(self, hours: int = None):
        """Deletes messages older than N hours."""
        if hours is None:
            hours = RETENTION_HOURS
        
        conn = self._get_conn()
        cursor = conn.cursor()
        cutoff = time.time() - (hours * 3600)
        cursor.execute("DELETE FROM messages WHERE timestamp < ?", (cutoff,))
        conn.commit()
        conn.close()

# Singleton
chat_history = ChatHistoryService()
