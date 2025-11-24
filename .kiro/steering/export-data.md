# Data Export

## Export User Data

```python
import json
import csv
from io import StringIO, BytesIO

async def export_user_data(user_id: int) -> dict:
    """Export all user data."""
    user = await db.get_user(user_id)
    messages = await db.get_user_messages(user_id)
    settings = await db.get_user_settings(user_id)
    
    return {
        'user': {
            'id': user.telegram_id,
            'username': user.username,
            'created_at': user.created_at.isoformat()
        },
        'messages': [
            {'text': m.text, 'date': m.created_at.isoformat()}
            for m in messages
        ],
        'settings': settings
    }
```

## Export to JSON

```python
async def export_to_json(update, context):
    """Export user data as JSON."""
    data = await export_user_data(update.effective_user.id)
    
    json_data = json.dumps(data, indent=2)
    bio = BytesIO(json_data.encode('utf-8'))
    bio.name = 'user_data.json'
    
    await update.message.reply_document(
        document=bio,
        filename='user_data.json',
        caption="Your data export"
    )
```

## Export to CSV

```python
async def export_to_csv(data: list[dict]) -> BytesIO:
    """Export data to CSV."""
    output = StringIO()
    
    if data:
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    
    bio = BytesIO(output.getvalue().encode('utf-8'))
    bio.seek(0)
    return bio
```

## GDPR Compliance

```python
async def delete_user_data(user_id: int):
    """Delete all user data (GDPR right to be forgotten)."""
    await db.delete_user_messages(user_id)
    await db.delete_user_settings(user_id)
    await db.delete_user(user_id)
```
