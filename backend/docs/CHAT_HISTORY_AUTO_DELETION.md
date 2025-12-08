# Chat History Auto-Deletion

## Overview
The chat history system automatically deletes expired messages based on the configured retention period.

## Configuration
Set the retention period in `backend/.env`:
```bash
CHAT_HISTORY_RETENTION_HOURS=24  # Default: 24 hours (1 day)
```

### Examples:
- `24` = 1 day
- `48` = 2 days  
- `72` = 3 days
- `168` = 7 days (1 week)

## How It Works

### 1. Startup Pruning
When the backend starts, it immediately deletes all messages older than the configured retention period.

### 2. Periodic Pruning
A background task runs every hour to automatically delete expired messages.

### 3. Manual Pruning
You can also manually trigger pruning:
```python
from services.chat_history import chat_history
chat_history.prune_old_messages()
```

## Implementation Details

### Files Modified:
- `backend/.env` - Configuration variable
- `backend/services/chat_history.py` - Pruning logic
- `backend/main.py` - Background task scheduler

### Background Task:
```python
async def prune_history_periodically():
    """Runs every hour to delete expired messages."""
    while True:
        await asyncio.sleep(3600)  # 1 hour
        chat_history.prune_old_messages()
```

## Testing
Run the test script to verify auto-deletion:
```bash
cd backend
venv\Scripts\python tests/test_auto_deletion.py
```

## Logs
Check the backend logs for pruning activity:
- Startup: `"Chat history pruned on startup."`
- Periodic: `"Periodic chat history pruning completed."`
- Errors: `"Periodic history pruning failed: {error}"`
