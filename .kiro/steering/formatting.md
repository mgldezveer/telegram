# Message Formatting

## HTML Formatting

```python
text = """
<b>Bold text</b>
<i>Italic text</i>
<u>Underlined text</u>
<s>Strikethrough text</s>
<code>Monospace code</code>
<pre>Pre-formatted code block</pre>
<a href="https://example.com">Link</a>
"""
await update.message.reply_text(text, parse_mode='HTML')
```

## Markdown Formatting

```python
text = """
*Bold text*
_Italic text_
`Monospace code`
```Code block```
[Link](https://example.com)
"""
await update.message.reply_text(text, parse_mode='MarkdownV2')
```

## Escaping Special Characters

```python
from telegram.helpers import escape_markdown

user_input = "User's text with * and _"
safe_text = escape_markdown(user_input, version=2)
await update.message.reply_text(safe_text, parse_mode='MarkdownV2')
```

## Mentions

```python
# Mention user by ID
text = f'<a href="tg://user?id={user_id}">User</a>'
await update.message.reply_text(text, parse_mode='HTML')

# Mention by username
text = '@username'
await update.message.reply_text(text)
```

## Long Messages

```python
def split_message(text: str, max_length: int = 4096) -> list[str]:
    """Split long message into chunks."""
    return [text[i:i+max_length] for i in range(0, len(text), max_length)]

async def send_long_message(update, context, text):
    for chunk in split_message(text):
        await update.message.reply_text(chunk)
```
