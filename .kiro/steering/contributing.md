# Contributing Guidelines

## How to Contribute

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write/update tests
5. Update documentation
6. Submit a pull request

## Development Setup

```bash
# Clone your fork
git clone https://github.com/your-username/telegram-bot.git
cd telegram-bot

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt -r requirements-dev.txt

# Run tests
pytest
```

## Code Style

- Follow PEP 8
- Use Black for formatting
- Use isort for imports
- Maximum line length: 88 characters
- Write docstrings for all functions

## Commit Messages

Follow conventional commits:

```
feat: add new command
fix: resolve database connection issue
docs: update README
test: add tests for user management
refactor: simplify error handling
```

## Pull Request Process

1. Update README if needed
2. Add tests for new features
3. Ensure all tests pass
4. Update CHANGELOG.md
5. Request review from maintainers

## Code Review

- Be respectful and constructive
- Focus on code, not the person
- Explain your reasoning
- Be open to feedback

## Reporting Bugs

Include:
- Bot version
- Python version
- Steps to reproduce
- Expected behavior
- Actual behavior
- Error messages/logs

## Feature Requests

- Describe the feature
- Explain use case
- Provide examples
- Consider implementation
