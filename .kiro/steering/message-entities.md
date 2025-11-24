# Message Entities

## Parse Entities

```python
async def parse_entities(update, context):
    """Parse message entities."""
    if update.message.entities:
        for entity in update.message.entities:
            text = update.message.text[entity.offset:entity.offset + entity.length]
            
            if entity.type == 'mention':
                logger.info(f"Mention: {text}")
            elif entity.type == 'hashtag':
                logger.info(f"Hashtag: {text}")
            elif entity.type == 'url':
                logger.info(f"URL: {text}")
            elif entity.type == 'email':
                logger.info(f"Email: {text}")
            elif entity.type == 'bot_command':
                logger.info(f"Command: {text}")
```

## Extract URLs

```python
def extract_urls(message) -> list[str]:
    """Extract all URLs from message."""
    urls = []
    
    if message.entities:
        for entity in message.entities:
            if entity.type in ['url', 'text_link']:
                if entity.type == 'url':
                    url = message.text[entity.offset:entity.offset + entity.length]
                else:
                    url = entity.url
                urls.append(url)
    
    return urls
```

## Extract Mentions

```python
def extract_mentions(message) -> list[str]:
    """Extract all mentions from message."""
    mentions = []
    
    if message.entities:
        for entity in message.entities:
            if entity.type == 'mention':
                mention = message.text[entity.offset:entity.offset + entity.length]
                mentions.append(mention)
            elif entity.type == 'text_mention':
                mentions.append(entity.user.username or entity.user.first_name)
    
    return mentions
```

## Extract Hashtags

```python
def extract_hashtags(message) -> list[str]:
    """Extract all hashtags from message."""
    hashtags = []
    
    if message.entities:
        for entity in message.entities:
            if entity.type == 'hashtag':
                tag = message.text[entity.offset:entity.offset + entity.length]
                hashtags.append(tag)
    
    return hashtags
```
