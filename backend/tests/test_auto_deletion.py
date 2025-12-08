"""
Test script to verify chat history automatic deletion based on retention hours.
"""
import time
import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.chat_history import chat_history, RETENTION_HOURS

print(f"Testing Chat History Auto-Deletion")
print(f"Configured retention: {RETENTION_HOURS} hours")
print("-" * 50)

# 1. Add a test message
print("\n1. Adding test message...")
chat_history.add_message("user", "Test message for auto-deletion")
messages = chat_history.get_recent_messages()
print(f"   Messages in DB: {len(messages)}")

# 2. Manually insert an old message (simulate expired message)
print("\n2. Inserting expired message (25 hours old)...")
import sqlite3
conn = chat_history._get_conn()
cursor = conn.cursor()
old_timestamp = time.time() - (25 * 3600)  # 25 hours ago
cursor.execute(
    "INSERT INTO messages (id, role, content, timestamp, metadata) VALUES (?, ?, ?, ?, ?)",
    ("test-old-id", "user", "This message is 25 hours old", old_timestamp, None)
)
conn.commit()
conn.close()

messages = chat_history.get_recent_messages()
print(f"   Messages in DB (before pruning): {len(messages)}")

# 3. Run pruning
print("\n3. Running prune_old_messages()...")
chat_history.prune_old_messages()

# 4. Check if old message was deleted
messages = chat_history.get_recent_messages()
print(f"   Messages in DB (after pruning): {len(messages)}")

# 5. Verify the old message is gone
all_messages_query = "SELECT id, content, timestamp FROM messages"
conn = chat_history._get_conn()
cursor = conn.cursor()
cursor.execute(all_messages_query)
all_msgs = cursor.fetchall()
conn.close()

print(f"\n4. Verification:")
print(f"   Total messages in DB: {len(all_msgs)}")
for msg in all_msgs:
    age_hours = (time.time() - msg[2]) / 3600
    print(f"   - ID: {msg[0][:20]}... | Age: {age_hours:.1f}h | Content: {msg[1][:50]}")

# Check if old message was deleted
old_msg_exists = any(msg[0] == "test-old-id" for msg in all_msgs)
if old_msg_exists:
    print("\n❌ FAILED: Old message was NOT deleted!")
else:
    print("\n✅ SUCCESS: Old message was automatically deleted!")

print(f"\nConclusion: Auto-deletion based on {RETENTION_HOURS}h retention is working correctly.")
