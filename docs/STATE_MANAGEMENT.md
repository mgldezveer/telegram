# State Management

## Overview

The bot uses a comprehensive state management system to track user sessions, navigation history, and conversation states. The system includes automatic cleanup of expired data to prevent memory leaks.

## Components

### StateManager

Manages user session data with automatic expiration and cleanup.

**Features:**
- Session timeout (default: 1 hour)
- Automatic cleanup task (runs every 5 minutes)
- Activity-based session extension
- Manual session clearing

**Usage:**

```python
from src.services.state_manager import StateManager

# Initialize
state_manager = StateManager(
    session_timeout=3600,  # 1 hour
    cleanup_interval=300   # 5 minutes
)

# Start automatic cleanup
await state_manager.start_cleanup_task()

# Store state
await state_manager.set_state(user_id, 'key', 'value')

# Retrieve state
value = await state_manager.get_state(user_id, 'key', default=None)

# Check if session is active
is_active = await state_manager.is_session_active(user_id)

# Clear specific session
await state_manager.clear_session(user_id)

# Stop cleanup task
await state_manager.stop_cleanup_task()
```

### NavigationHistory

Tracks user navigation through menus for back button functionality.

**Features:**
- Maximum history size (default: 10 entries)
- History timeout (default: 1 hour)
- Automatic cleanup of old histories
- Duplicate prevention

**Usage:**

```python
from src.services.state_manager import NavigationHistory

# Initialize
nav_history = NavigationHistory(
    max_history=10,
    history_timeout=3600
)

# Push menu to history
await nav_history.push(user_id, 'main_menu')

# Get previous menu
previous = await nav_history.get_previous(user_id)

# Pop last menu
last_menu = await nav_history.pop(user_id)

# Clear history
await nav_history.clear(user_id)
```

### ConversationManager

Manages multi-step conversations with automatic timeout handling and seamless menu navigation.

**Features:**
- Conversation timeout (default: 5 minutes)
- Automatic conversation tracking
- Timeout notifications
- Cleanup of expired conversations
- Mixed handler support (CallbackQuery + MessageHandler)
- Automatic menu restoration after conversation completion or cancellation

**Usage:**

```python
from src.interface.conversation_manager import ConversationManager

# Initialize
conv_manager = ConversationManager(bot_controller=controller)

# Track conversation
conv_manager.track_conversation(user_id, 'channel_registration')

# End conversation
conv_manager.end_conversation(user_id)

# Cleanup expired conversations
cleaned = await conv_manager.cleanup_expired_conversations(context)

# Get active count
count = conv_manager.get_active_conversations_count()
```

**Navigation Flow:**

After conversation completion or cancellation, the system automatically:
1. Ends the conversation state
2. Displays appropriate confirmation message
3. Restores the relevant menu (e.g., channels menu after channel registration)
4. Ensures smooth user experience without manual navigation

**Technical Details:**

All conversation handlers use `per_message=False` configuration to properly handle mixed handler types:
- Entry points use `CallbackQueryHandler` (button clicks)
- State handlers use `MessageHandler` (text input)

This ensures conversations work correctly when transitioning from callback queries to message-based input.

## Automatic Cleanup

The system includes automatic cleanup mechanisms to prevent memory leaks:

### Session Cleanup

- Runs every 5 minutes (configurable)
- Removes sessions inactive for more than 1 hour
- Logs cleanup statistics

### Navigation History Cleanup

- Triggered on new navigation events
- Removes histories inactive for more than 1 hour
- Maintains maximum history size per user

### Conversation Cleanup

- Conversations timeout after 5 minutes of inactivity
- Users receive timeout notification
- Conversation data is automatically cleared

## Configuration

### Environment Variables

```bash
# Session timeout in seconds (default: 3600)
SESSION_TIMEOUT=3600

# Cleanup interval in seconds (default: 300)
CLEANUP_INTERVAL=300

# Navigation history timeout in seconds (default: 3600)
HISTORY_TIMEOUT=3600

# Conversation timeout in seconds (default: 300)
CONVERSATION_TIMEOUT=300
```

### Code Configuration

```python
# In BotController initialization
self.state_manager = StateManager(
    session_timeout=3600,      # 1 hour
    cleanup_interval=300       # 5 minutes
)

self.navigation_history = NavigationHistory(
    max_history=10,
    history_timeout=3600       # 1 hour
)

self.conversation_manager = ConversationManager(
    bot_controller=self
)
# Conversation timeout set in ConversationManager.__init__
```

## Monitoring

### Session Statistics

```python
# Get active session count
active_count = await state_manager.get_active_sessions_count()

# Check if specific session is active
is_active = await state_manager.is_session_active(user_id)
```

### Conversation Statistics

```python
# Get active conversation count
conv_count = conv_manager.get_active_conversations_count()
```

### Cleanup Logs

The cleanup system logs important events:

```
INFO - State cleanup task started
INFO - Cleanup completed. Active sessions: 42
INFO - Cleaned up expired session for user 123456
INFO - Cleaned up old navigation history for user 789012
INFO - Cleaned up expired conversation for user 345678
```

## Best Practices

1. **Always start cleanup task on bot startup:**
   ```python
   await state_manager.start_cleanup_task()
   ```

2. **Always stop cleanup task on bot shutdown:**
   ```python
   await state_manager.stop_cleanup_task()
   ```

3. **Use appropriate timeouts:**
   - Short timeouts (5 minutes) for conversations
   - Medium timeouts (1 hour) for sessions
   - Long timeouts (24 hours) for persistent data

4. **Monitor cleanup statistics:**
   - Check logs for cleanup frequency
   - Monitor active session counts
   - Alert on unusual patterns

5. **Handle cleanup gracefully:**
   - Notify users of timeouts
   - Provide easy recovery options
   - Save important data before cleanup

## Troubleshooting

### High Memory Usage

If memory usage is high:

1. Check active session count
2. Reduce session timeout
3. Increase cleanup frequency
4. Check for memory leaks in session data

### Frequent Timeouts

If users experience frequent timeouts:

1. Increase session timeout
2. Check activity tracking
3. Verify cleanup interval
4. Review user activity patterns

### Cleanup Not Running

If cleanup doesn't run:

1. Verify cleanup task is started
2. Check for exceptions in logs
3. Verify asyncio event loop is running
4. Check cleanup interval configuration

### Conversation Handler Issues

If conversations don't work properly with mixed handlers:

1. Verify `per_message=False` is set in ConversationHandler
2. Check that entry points use CallbackQueryHandler
3. Ensure state handlers use MessageHandler
4. Review logs for handler conflicts
5. Confirm conversation timeout is appropriate

## Testing

Run state cleanup tests:

```bash
python -m pytest tests/test_state_cleanup.py -v
```

Tests cover:
- Session expiration and cleanup
- Activity-based timeout extension
- Navigation history cleanup
- Cleanup task lifecycle
- Manual cleanup operations
