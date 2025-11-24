# Git Workflow

## Branch Strategy

- `main` - production-ready code
- `develop` - integration branch
- `feature/*` - new features
- `bugfix/*` - bug fixes
- `hotfix/*` - urgent production fixes

## Commit Messages

Follow conventional commits format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Examples:
- `feat(bot): add command handler for /help`
- `fix(api): handle timeout errors properly`
- `docs(readme): update installation instructions`

## Pull Requests

- Create PR from feature branch to develop
- Require at least one review
- Ensure all tests pass
- Update documentation if needed

## Workflow

1. Create feature branch: `git checkout -b feature/new-command`
2. Make changes and commit
3. Push and create PR
4. After review, merge to develop
5. Periodically merge develop to main
