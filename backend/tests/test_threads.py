import pytest
from services.chat_history import chat_history
import time
import os

TEST_DB = "test_chat.db"

@pytest.fixture(autouse=True)
def setup_teardown(monkeypatch):
    """Fixture to ensure each test uses a clean test database and restores state."""
    # Setup
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    
    # Store original path
    original_path = chat_history.db_path
    
    # Patch the singleton instance
    monkeypatch.setattr(chat_history, "db_path", TEST_DB)
    
    # Re-initialize DB tables for the test DB
    chat_history._init_db()
    
    yield
    
    # Teardown
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

def test_create_thread():
    user_id = "test_user"
    thread_id = chat_history.create_thread(user_id, "Test Thread")
    assert thread_id is not None
    
    threads = chat_history.get_user_threads(user_id)
    assert len(threads) == 1
    assert threads[0]['title'] == "Test Thread"
    assert threads[0]['id'] == thread_id

def test_add_message_to_thread():
    user_id = "test_user"
    thread_id = chat_history.create_thread(user_id, "Message Thread")
    
    chat_history.add_message(thread_id, "user", "Hello")
    chat_history.add_message(thread_id, "bot", "Hi there")
    
    messages = chat_history.get_thread_messages(thread_id)
    assert len(messages) == 2
    assert messages[0]['text'] == "Hello"
    assert messages[1]['text'] == "Hi there"

def test_update_thread():
    user_id = "test_user"
    thread_id = chat_history.create_thread(user_id, "Old Title")
    
    # Rename
    chat_history.update_thread(thread_id, title="New Title")
    threads = chat_history.get_user_threads(user_id)
    assert threads[0]['title'] == "New Title"
    assert threads[0]['pinned'] is False
    
    # Pin
    chat_history.update_thread(thread_id, pinned=True)
    threads = chat_history.get_user_threads(user_id)
    assert threads[0]['pinned'] is True

def test_delete_thread():
    user_id = "test_user"
    thread_id = chat_history.create_thread(user_id, "To Delete")
    
    chat_history.add_message(thread_id, "user", "msg")
    
    chat_history.delete_thread(thread_id)
    
    threads = chat_history.get_user_threads(user_id)
    assert len(threads) == 0
    
    # Verify messages deleted (cascade or manual)
    messages = chat_history.get_thread_messages(thread_id)
    assert len(messages) == 0
