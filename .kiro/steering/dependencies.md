# Dependency Management

## Python Dependencies

Use `requirements.txt` for production dependencies and `requirements-dev.txt` for development dependencies.

## Core Dependencies

```
python-telegram-bot>=20.0
python-dotenv>=1.0.0
aiohttp>=3.9.0
```

## Development Dependencies

```
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
black>=23.0.0
flake8>=6.0.0
isort>=5.12.0
mypy>=1.5.0
```

## Installation

```bash
# Production
pip install -r requirements.txt

# Development
pip install -r requirements.txt -r requirements-dev.txt
```

## Virtual Environment

Always use virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

## Updating Dependencies

- Review updates regularly
- Test thoroughly before updating major versions
- Pin versions for production stability
- Use `pip freeze > requirements.txt` to lock versions
