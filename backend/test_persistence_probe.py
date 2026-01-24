
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_persistence():
    # 1. Login/Guest
    print("1. Authenticating...")
    resp = requests.post(f"{BASE_URL}/auth/guest")
    if resp.status_code != 200:
        print(f"Auth failed: {resp.text}")
        return
    token = resp.json()['access_token']
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Create Thread
    print("2. Creating Thread...")
    resp = requests.post(f"{BASE_URL}/threads", json={"title": "Persistence Test"}, headers=headers)
    thread_id = resp.json()['id']
    print(f"Thread ID: {thread_id}")
    
    # 3. Send Query
    print("3. Sending Query...")
    # Using 'list patients' which should trigger SQL agent
    query_payload = {
        "question": "list patients",
        "thread_id": thread_id,
        "model_id": "simple", # or whatever
        "fast_mode": True # Fast mode to save time/tokens if logic permits
    }
    try:
        resp = requests.post(f"{BASE_URL}/query", json=query_payload, headers=headers)
        if resp.status_code != 200:
            print(f"Query failed: {resp.text}")
            # Even if it failed, check if 'thoughts' exist in error response meta
            # But usually we check persistence in *fetched* messages.
    except Exception as e:
        print(f"Query exception: {e}")

    # 4. Fetch Messages (Simulate Refresh)
    print("4. Fetching Messages (Simulating Refresh)...")
    resp = requests.get(f"{BASE_URL}/threads/{thread_id}/messages", headers=headers)
    messages = resp.json()['messages']
    
    # 5. Check for thoughts
    bot_messages = [m for m in messages if m['role'] == 'bot']
    if not bot_messages:
        print("No bot messages found!")
        return

    last_bot_msg = bot_messages[-1]
    print(f"Last Bot Message ID: {last_bot_msg.get('id')}")
    meta = last_bot_msg.get('metadata') or last_bot_msg.get('meta') or {}
    print(f"Metadata keys: {meta.keys()}")
    
    thoughts = meta.get('thoughts', [])
    print(f"Thoughts found: {len(thoughts)}")
    if thoughts:
        print("Thoughts Sample:", thoughts[:2])
    
    if len(thoughts) > 0:
        print("✅ SUCCESS: Thoughts are persisted.")
    else:
        print("❌ FAILURE: No thoughts found in metadata.")
        print("Full Meta:", json.dumps(meta, indent=2))

if __name__ == "__main__":
    test_persistence()
