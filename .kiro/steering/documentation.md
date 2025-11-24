# Documentation Standards

## Code Documentation

- All public APIs must have docstrings
- Use Google-style docstrings
- Include type hints in function signatures

## Project Documentation

- README.md - project overview, setup, usage
- CONTRIBUTING.md - contribution guidelines
- CHANGELOG.md - version history
- docs/ - detailed documentation

## Docstring Format

```python
def send_message(chat_id: int, text: str, parse_mode: str = "HTML") -> bool:
    """Send a message to a Telegram chat.
    
    Args:
        chat_id: Unique identifier for the target chat
        text: Text of the message to be sent
        parse_mode: Mode for parsing entities in the message text
        
    Returns:
        True if message was sent successfully, False otherwise
        
    Raises:
        TelegramAPIError: If the API request fails
    """
    pass
```

## README Structure

1. Project title and description
2. Features
3. Installation
4. Configuration
5. Usage examples
6. API documentation
7. Contributing
8. License
