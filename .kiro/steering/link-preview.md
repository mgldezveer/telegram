# Link Preview Options

## Disable Link Preview

```python
async def send_without_preview(update, context):
    """Send message without link preview."""
    await update.message.reply_text(
        "Check out https://example.com",
        disable_web_page_preview=True
    )
```

## Custom Link Preview

```python
from telegram import LinkPreviewOptions

async def send_custom_preview(update, context):
    """Send with custom link preview."""
    preview_options = LinkPreviewOptions(
        is_disabled=False,
        url="https://example.com",
        prefer_small_media=True,
        prefer_large_media=False,
        show_above_text=False
    )
    
    await update.message.reply_text(
        "Custom preview: https://example.com",
        link_preview_options=preview_options
    )
```

## Preview Above Text

```python
async def preview_above(update, context):
    """Show preview above message text."""
    preview = LinkPreviewOptions(
        show_above_text=True
    )
    
    await update.message.reply_text(
        "Link with preview on top:\nhttps://example.com",
        link_preview_options=preview
    )
```
