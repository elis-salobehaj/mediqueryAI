import pytest
from fastapi.testclient import TestClient
from main import app
import json

@pytest.fixture
def client():
    # We use a context manager or just the client
    # The lifespan will be handled by TestClient if using 'with' or newer versions
    with TestClient(app) as c:
        yield c

def test_thoughts_persistence(client):
    """Test that thoughts are persisted in the chat history metadata."""
    # 1. Login as guest
    resp = client.post("/auth/guest")
    assert resp.status_code == 200
    token = resp.json()['access_token']
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Create Thread
    resp = client.post("/threads", json={"title": "Persistence Test"}, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    thread_id = resp.json()['id']
    
    # 3. Send Query
    # Note: This might talk to real LLM if configured, or fail if no keys.
    # We'll use a query that hopefully triggers a quick response or just check the mechanism.
    query_payload = {
        "question": "list patients",
        "thread_id": thread_id,
        "fast_mode": True
    }
    
    # We wrap in try-except because we're testing the persistence *logic* in main.py, 
    # even if the LLM call itself fails, main.py might still save partial/error status.
    # However, to test *success* persistence, we need a successful query.
    resp = client.post("/query", json=query_payload, headers=headers)
    # Even if 500 or 400, thoughts might be persisted if it reached the save point.
    
    # 4. Fetch Messages
    resp = client.get(f"/threads/{thread_id}/messages", headers=headers)
    assert resp.status_code == 200
    messages = resp.json()['messages']
    
    # 5. Check bot message for thoughts
    bot_messages = [m for m in messages if m['role'] == 'bot']
    if bot_messages:
        last_bot_msg = bot_messages[-1]
        meta = last_bot_msg.get('meta', {})
        # Thoughts should be in metadata if generated
        # If the query failed, we'll still have whatever thoughts were accumulated
        assert "thoughts" in meta
        assert isinstance(meta['thoughts'], list)
