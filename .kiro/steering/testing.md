# Testing Guidelines

## Test Framework

- Use pytest for all tests
- Use pytest-asyncio for async tests
- Use pytest-mock for mocking

## Test Structure

```
tests/
├── unit/           # Unit tests
├── integration/    # Integration tests
└── conftest.py     # Shared fixtures
```

## Naming Conventions

- Test files: `test_*.py`
- Test functions: `test_<feature>_<scenario>()`
- Test classes: `Test<Feature>`

## Coverage

- Aim for 80%+ code coverage
- Run: `pytest --cov=src --cov-report=html`

## Example

```python
import pytest
from src.bot import TelegramBot

@pytest.fixture
def bot():
    return TelegramBot(token="test_token")

def test_message_handler_returns_response(bot):
    response = bot.handle_message("/start")
    assert response is not None
```
