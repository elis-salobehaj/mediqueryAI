import logging
import os
import sqlite3
import datetime
import secrets
from jose import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from typing import Optional, Dict

from config import settings

# Configuration
JWT_SECRET_KEY = settings.jwt_secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

ph = PasswordHasher()
logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self, db_path: str = "users.db"):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.db_path = os.path.join(base_dir, "data", db_path)
        self._init_db()

    def _get_conn(self):
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def _init_db(self):
        """Creates users table."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                hashed_password TEXT NOT NULL,
                full_name TEXT,
                email TEXT,
                disabled INTEGER DEFAULT 0
            )
        """)
        # Create default admin if not exists
        cursor.execute("SELECT username FROM users WHERE username = 'admin'")
        if not cursor.fetchone():
            hashed = ph.hash("admin")
            cursor.execute(
                "INSERT INTO users (username, hashed_password, full_name, email) VALUES (?, ?, ?, ?)",
                ("admin", hashed, "System Admin", "admin@mediquery.ai")
            )
            logger.info("Created default 'admin' user with password 'admin'")
        
        conn.commit()
        conn.close()

    def get_user(self, username: str) -> Optional[Dict]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT username, hashed_password, full_name, email, disabled FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                "username": row[0],
                "hashed_password": row[1],
                "full_name": row[2],
                "email": row[3],
                "disabled": bool(row[4])
            }
        return None

    def create_user(self, username, password, full_name=None, email=None):
        hashed = ph.hash(password)
        conn = self._get_conn()
        try:
            conn.execute(
                "INSERT INTO users (username, hashed_password, full_name, email) VALUES (?, ?, ?, ?)",
                (username, hashed, full_name, email)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
            
    def create_guest_user(self):
        """Creates a temporary guest user."""
        import uuid
        guest_id = f"guest_{uuid.uuid4().hex[:8]}"
        password = secrets.token_urlsafe(16)
        # Guests don't need a real password but we set one
        self.create_user(guest_id, password, "Guest User", None)
        return guest_id

    def verify_password(self, plain_password, hashed_password):
        try:
            return ph.verify(hashed_password, plain_password)
        except VerifyMismatchError:
            return False

    def create_access_token(self, data: dict, expires_delta: Optional[datetime.timedelta] = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.datetime.now(datetime.UTC) + expires_delta
        else:
            expire = datetime.datetime.now(datetime.UTC) + datetime.timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

auth_service = AuthService()
