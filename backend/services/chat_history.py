import logging
import sqlite3
import json
import time
import os
import uuid
from typing import List, Dict, Optional

from config import settings

logger = logging.getLogger(__name__)

# Get retention hours from centralized settings
RETENTION_HOURS = settings.chat_history_retention_hours

class ChatHistoryService:
    def __init__(self, db_path: str = "chat_history.db"):
        # Ensure data directory exists
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.db_path = os.path.join(base_dir, "data", db_path)
        self._init_db()

    def _get_conn(self):
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def _init_db(self):
        """Creates the threads and messages tables if not exists."""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        # Threads Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS threads (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                title TEXT,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                pinned BOOLEAN DEFAULT 0
            )
        """)

        # Messages Table (Expanded schema)
        # Note: In a real migration we'd alter table, but here we rebuild given dev environment
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                thread_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp REAL NOT NULL,
                metadata TEXT,
                FOREIGN KEY(thread_id) REFERENCES threads(id) ON DELETE CASCADE
            )
        """)
        
        conn.commit()
        conn.close()

    # --- Thread Management ---

    def create_thread(self, user_id: str, title: str = "New Chat") -> str:
        """Creates a new thread and returns its ID."""
        thread_id = str(uuid.uuid4())
        now = time.time()
        
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO threads (id, user_id, title, created_at, updated_at, pinned) VALUES (?, ?, ?, ?, ?, ?)",
            (thread_id, user_id, title, now, now, 0)
        )
        conn.commit()
        conn.close()
        return thread_id

    def get_user_threads(self, user_id: str) -> List[Dict]:
        """Returns all threads for a user, ordered by pinned then recency."""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, title, updated_at, pinned 
            FROM threads 
            WHERE user_id = ? 
            ORDER BY pinned DESC, updated_at DESC
        """, (user_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {"id": r[0], "title": r[1], "updated_at": r[2], "pinned": bool(r[3])} 
            for r in rows
        ]

    def update_thread(self, thread_id: str, title: str = None, pinned: bool = None):
        """Updates thread title or pinned status."""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if title is not None:
            updates.append("title = ?")
            params.append(title)
        
        if pinned is not None:
            updates.append("pinned = ?")
            params.append(1 if pinned else 0)
            
        updates.append("updated_at = ?")
        params.append(time.time())
        
        params.append(thread_id)
        
        if updates:
            sql = f"UPDATE threads SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(sql, tuple(params))
            conn.commit()
            
        conn.close()

    def delete_thread(self, thread_id: str):
        """Deletes a thread and its messages."""
        conn = self._get_conn()
        cursor = conn.cursor()
        # Message deletion handled by FK CASCADE if supported, but let's be safe
        cursor.execute("DELETE FROM messages WHERE thread_id = ?", (thread_id,))
        cursor.execute("DELETE FROM threads WHERE id = ?", (thread_id,))
        conn.commit()
        conn.close()

    # --- Message Management ---

    def add_message(self, thread_id: str, role: str, content: str, metadata: Optional[Dict] = None):
        """Adds a message to a specific thread."""
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            msg_id = str(uuid.uuid4())
            timestamp = time.time()
            meta_json = json.dumps(metadata) if metadata else None
            
            cursor.execute(
                "INSERT INTO messages (id, thread_id, role, content, timestamp, metadata) VALUES (?, ?, ?, ?, ?, ?)",
                (msg_id, thread_id, role, content, timestamp, meta_json)
            )
            
            # Update thread timestamp
            cursor.execute("UPDATE threads SET updated_at = ? WHERE id = ?", (timestamp, thread_id))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to save message: {e}")
            pass

    def get_thread_messages(self, thread_id: str) -> List[Dict]:
        """Retrieves all messages for a thread."""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id, role, content, timestamp, metadata FROM messages WHERE thread_id = ? ORDER BY timestamp ASC",
            (thread_id,)
        )
        
        rows = cursor.fetchall()
        conn.close()
        
        messages = []
        for row in rows:
            messages.append({
                "id": row[0],
                "role": row[1], # 'user' or 'bot'
                "text": row[2],
                "timestamp": row[3],
                "meta": json.loads(row[4]) if row[4] else {}
            })
        return messages

    # Keeping for compatibility if needed, but prunes messages directly
    def prune_old_messages(self, hours: int = None):
        """Deletes threads older than N hours."""
        if hours is None:
            hours = RETENTION_HOURS
        
        conn = self._get_conn()
        cursor = conn.cursor()
        cutoff = time.time() - (hours * 3600)
        
        # Get old threads
        cursor.execute("SELECT id FROM threads WHERE updated_at < ? AND pinned = 0", (cutoff,))
        old_threads = [r[0] for r in cursor.fetchall()]
        
        for tid in old_threads:
            cursor.execute("DELETE FROM messages WHERE thread_id = ?", (tid,))
            cursor.execute("DELETE FROM threads WHERE id = ?", (tid,))
            
        conn.commit()
        conn.close()

# Singleton
chat_history = ChatHistoryService()
