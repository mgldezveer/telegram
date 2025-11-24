# Callback Data Patterns

## Simple Callback Data

```python
keyboard = [
    [InlineKeyboardButton("Option 1", callback_data="opt1")],
    [InlineKeyboardButton("Option 2", callback_data="opt2")]
]

async def callback_handler(update, context):
    query = update.callback_query
    
    if query.data == "opt1":
        await query.edit_message_text("You chose option 1")
    elif query.data == "opt2":
        await query.edit_message_text("You chose option 2")
```

## Structured Callback Data

```python
import json

def create_callback_data(action: str, **kwargs) -> str:
    """Create structured callback data."""
    data = {'action': action, **kwargs}
    return json.dumps(data)

def parse_callback_data(data: str) -> dict:
    """Parse structured callback data."""
    return json.loads(data)

# Usage
keyboard = [
    [InlineKeyboardButton(
        "Delete Item",
        callback_data=create_callback_data('delete', item_id=123)
    )],
    [InlineKeyboardButton(
        "Edit Item",
        callback_data=create_callback_data('edit', item_id=123)
    )]
]

async def callback_handler(update, context):
    query = update.callback_query
    data = parse_callback_data(query.data)
    
    if data['action'] == 'delete':
        await delete_item(data['item_id'])
    elif data['action'] == 'edit':
        await edit_item(data['item_id'])
```

## Pagination Callback

```python
def create_pagination_keyboard(page: int, total_pages: int):
    """Create pagination keyboard."""
    keyboard = []
    
    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton("◀️ Prev", callback_data=f"page:{page-1}")
        )
    
    nav_buttons.append(
        InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="noop")
    )
    
    if page < total_pages - 1:
        nav_buttons.append(
            InlineKeyboardButton("Next ▶️", callback_data=f"page:{page+1}")
        )
    
    keyboard.append(nav_buttons)
    return InlineKeyboardMarkup(keyboard)
```

## Callback Data Limits

```python
# Callback data is limited to 64 bytes
# For large data, use a reference system

class CallbackDataManager:
    def __init__(self):
        self.storage = {}
        self.counter = 0
    
    def store(self, data: dict) -> str:
        """Store data and return reference."""
        ref = f"ref_{self.counter}"
        self.storage[ref] = data
        self.counter += 1
        return ref
    
    def retrieve(self, ref: str) -> dict:
        """Retrieve data by reference."""
        return self.storage.get(ref)

callback_manager = CallbackDataManager()
```
