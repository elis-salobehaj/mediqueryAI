"""
Tests for chat history automatic deletion based on retention hours.
"""
import time
import os
import pytest
from services.chat_history import chat_history, RETENTION_HOURS

@pytest.fixture
def clean_history(monkeypatch):
    """Ensure a clean slate for history tests."""
    test_db = "test_deletion.db"
    if os.path.exists(test_db):
        os.remove(test_db)
    
    monkeypatch.setattr(chat_history, "db_path", test_db)
    chat_history._init_db()
    
    yield chat_history
    
    if os.path.exists(test_db):
        os.remove(test_db)

def test_auto_deletion(clean_history):
    """Test that old threads and messages are automatically deleted."""
    user_id = "test_deletion_user"
    
    # 1. Add a recent thread
    recent_thread_id = chat_history.create_thread(user_id, "Recent Thread")
    chat_history.add_message(recent_thread_id, "user", "Recent message")
    
    # 2. Add an old thread (expired)
    old_thread_id = chat_history.create_thread(user_id, "Old Thread")
    chat_history.add_message(old_thread_id, "user", "Old message")
    
    # Manually backdate the old thread in the database
    old_timestamp = time.time() - (RETENTION_HOURS + 1) * 3600  # 1 hour past retention
    
    conn = chat_history._get_conn()
    cursor = conn.cursor()
    cursor.execute("UPDATE threads SET updated_at = ? WHERE id = ?", (old_timestamp, old_thread_id))
    cursor.execute("UPDATE messages SET timestamp = ? WHERE thread_id = ?", (old_timestamp, old_thread_id))
    conn.commit()
    conn.close()
    
    # Verify both exist
    assert len(chat_history.get_user_threads(user_id)) == 2
    
    # 3. Run pruning
    chat_history.prune_old_messages()
    
    # 4. Check results
    threads = chat_history.get_user_threads(user_id)
    assert len(threads) == 1
    assert threads[0]['id'] == recent_thread_id
    
    # Verify old messages are gone
    old_messages = chat_history.get_thread_messages(old_thread_id)
    assert len(old_messages) == 0
    
    # Verify recent messages remain
    recent_messages = chat_history.get_thread_messages(recent_thread_id)
    assert len(recent_messages) == 1
