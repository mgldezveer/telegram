# Common Regex Patterns

## Email Validation

```python
import re

EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

def is_valid_email(email: str) -> bool:
    return bool(re.match(EMAIL_PATTERN, email))
```

## URL Extraction

```python
URL_PATTERN = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'

def extract_urls(text: str) -> list[str]:
    return re.findall(URL_PATTERN, text)
```

## Phone Number

```python
PHONE_PATTERN = r'\+?[1-9]\d{1,14}'

def extract_phone_numbers(text: str) -> list[str]:
    return re.findall(PHONE_PATTERN, text)
```

## Hashtag Extraction

```python
HASHTAG_PATTERN = r'#\w+'

def extract_hashtags(text: str) -> list[str]:
    return re.findall(HASHTAG_PATTERN, text)
```

## Mention Extraction

```python
MENTION_PATTERN = r'@\w+'

def extract_mentions(text: str) -> list[str]:
    return re.findall(MENTION_PATTERN, text)
```

## Command Pattern

```python
COMMAND_PATTERN = r'^/(\w+)(?:@(\w+))?(?:\s+(.+))?$'

def parse_command(text: str) -> tuple:
    match = re.match(COMMAND_PATTERN, text)
    if match:
        command, bot_username, args = match.groups()
        return command, bot_username, args
    return None, None, None
```
