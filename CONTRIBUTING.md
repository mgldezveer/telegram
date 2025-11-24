# Contributing to AI Content Bot

First off, thank you for considering contributing to AI Content Bot! 🎉

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When creating a bug report, include:

- **Clear title and description**
- **Steps to reproduce** the issue
- **Expected behavior** vs actual behavior
- **Screenshots** if applicable
- **Environment details** (OS, Python version, etc.)
- **Log output** (sanitize any sensitive data)

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, include:

- **Clear title and description**
- **Use case** - why is this enhancement useful?
- **Proposed solution** - how should it work?
- **Alternatives considered**
- **Additional context** (mockups, examples, etc.)

### Pull Requests

1. **Fork the repository** and create your branch from `main`
2. **Make your changes** following our coding standards
3. **Add tests** if applicable
4. **Update documentation** if needed
5. **Ensure tests pass** and code is formatted
6. **Submit a pull request**

## Development Setup

### Prerequisites

- Python 3.11+
- Git
- PostgreSQL (optional, for testing)
- Redis (optional, for testing)

### Setup Steps

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/telegram.git
cd telegram

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Copy environment file
cp .env.example .env
# Edit .env with your test credentials

# Initialize database
python init_db.py

# Run tests
pytest tests/ -v
```

## Coding Standards

### Python Style Guide

We follow [PEP 8](https://pep8.org/) with some modifications:

- **Line length**: 100 characters (not 79)
- **Indentation**: 4 spaces (no tabs)
- **Quotes**: Double quotes for strings
- **Imports**: Organized with `isort`

### Code Formatting

We use these tools:

```bash
# Format code
black src/

# Sort imports
isort src/

# Check style
flake8 src/

# Type checking
mypy src/
```

### Naming Conventions

- **Classes**: `PascalCase` (e.g., `ContentGenerator`)
- **Functions/Methods**: `snake_case` (e.g., `generate_content`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRIES`)
- **Private methods**: `_leading_underscore` (e.g., `_validate_input`)

### Documentation

- **Docstrings**: Use Google style docstrings
- **Type hints**: Required for all function signatures
- **Comments**: Explain "why", not "what"

Example:

```python
async def generate_content(
    self,
    category: str,
    topic: str,
    language: str = "en"
) -> Dict[str, Any]:
    """Generate AI-powered content for a given topic.
    
    Args:
        category: Content category (e.g., "tech", "business")
        topic: Specific topic to write about
        language: Target language code (default: "en")
        
    Returns:
        Dictionary containing generated content with keys:
        - title: Post title
        - content: Main content body
        - hashtags: List of relevant hashtags
        
    Raises:
        AIProviderError: If AI API call fails
        ValidationError: If input validation fails
    """
    # Implementation
```

## Testing

### Writing Tests

- **Unit tests**: Test individual functions/methods
- **Integration tests**: Test component interactions
- **Property tests**: Test invariants (if applicable)

Example test:

```python
import pytest
from src.services.content_generator import ContentGenerator

@pytest.mark.asyncio
async def test_generate_content_returns_valid_structure():
    """Test that generated content has required fields."""
    generator = ContentGenerator()
    
    result = await generator.generate_content(
        category="tech",
        topic="AI trends"
    )
    
    assert "title" in result
    assert "content" in result
    assert "hashtags" in result
    assert len(result["hashtags"]) > 0
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_content_generator.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run only fast tests (skip slow integration tests)
pytest tests/ -m "not slow"
```

## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples

```
feat(generator): add support for custom AI models

Allow users to specify custom AI models in configuration.
This enables using fine-tuned models for specific use cases.

Closes #123
```

```
fix(scheduler): handle timezone conversion correctly

Fixed bug where scheduled posts were published at wrong time
due to incorrect timezone handling.

Fixes #456
```

## Pull Request Process

1. **Update documentation** if you're changing functionality
2. **Add tests** for new features
3. **Update CHANGELOG.md** with your changes
4. **Ensure CI passes** (all tests, linting, type checking)
5. **Request review** from maintainers
6. **Address feedback** promptly
7. **Squash commits** if requested

### PR Title Format

Use the same format as commit messages:

```
feat(component): brief description
```

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
How has this been tested?

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] All tests pass
- [ ] No new warnings
```

## Project Structure

```
telegram/
├── src/
│   ├── bot/              # Bot controller and handlers
│   ├── services/         # Business logic services
│   ├── models/           # Database models
│   ├── repositories/     # Data access layer
│   ├── config.py         # Configuration management
│   └── main.py           # Application entry point
├── tests/                # Test files
├── docs/                 # Additional documentation
├── .env.example          # Environment template
├── requirements.txt      # Production dependencies
├── requirements-dev.txt  # Development dependencies
└── README.md            # Main documentation
```

## Adding New Features

### 1. Plan Your Feature

- Create an issue describing the feature
- Discuss approach with maintainers
- Get approval before starting work

### 2. Implement the Feature

- Create a new branch: `git checkout -b feat/your-feature`
- Write code following our standards
- Add tests for your feature
- Update documentation

### 3. Submit for Review

- Push your branch
- Create a pull request
- Respond to review feedback
- Merge when approved

## Code Review Guidelines

### For Reviewers

- Be respectful and constructive
- Focus on code, not the person
- Explain your reasoning
- Suggest improvements, don't demand
- Approve when satisfied

### For Contributors

- Don't take feedback personally
- Ask questions if unclear
- Make requested changes promptly
- Thank reviewers for their time

## Community Guidelines

### Be Respectful

- Use welcoming and inclusive language
- Respect differing viewpoints
- Accept constructive criticism gracefully
- Focus on what's best for the community

### Be Professional

- Keep discussions on-topic
- Avoid personal attacks
- Don't spam or self-promote
- Follow the code of conduct

## Getting Help

- 📖 Read the [documentation](README.md)
- ❓ Check the [FAQ](FAQ.md)
- 💬 Ask in GitHub Discussions
- 🐛 Report bugs via Issues

## Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Credited in documentation

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to AI Content Bot! 🚀
