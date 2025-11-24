# Code Style Guidelines

## Python Style

- Follow PEP 8 conventions
- Use 4 spaces for indentation
- Maximum line length: 88 characters (Black formatter standard)
- Use type hints for function signatures
- Use docstrings for all public functions and classes

## Naming Conventions

- Classes: `PascalCase`
- Functions/methods: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Private methods: prefix with `_`

## Formatting

- Use Black for automatic code formatting
- Use isort for import sorting
- Run flake8 for linting

## Example

```python
from typing import Optional

class TelegramHandler:
    """Handles Telegram bot interactions."""
    
    def process_message(self, message: str) -> Optional[str]:
        """Process incoming message and return response."""
        return self._generate_response(message)
    
    def _generate_response(self, message: str) -> str:
        """Generate response based on message content."""
        pass
```
