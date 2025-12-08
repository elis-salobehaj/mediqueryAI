import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    print("Attempting to import ChatHistoryService...")
    from services.chat_history import chat_history
    print("Import successful.")
    
    print("Attempting to add message...")
    chat_history.add_message("user", "Test Debug Message")
    print("Message added.")
    
    print("Attempting to fetch messages...")
    msgs = chat_history.get_recent_messages()
    print(f"Fetched {len(msgs)} messages.")
    print("Top message:", msgs[0] if msgs else "None")
    
except Exception as e:
    print(f"CRITICAL FAILURE: {e}")
    import traceback
    traceback.print_exc()
