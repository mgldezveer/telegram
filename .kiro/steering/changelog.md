# Changelog

## Version Format

Follow Semantic Versioning (SemVer): MAJOR.MINOR.PATCH

- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes

## Changelog Template

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- New features that have been added

### Changed
- Changes in existing functionality

### Deprecated
- Features that will be removed in upcoming releases

### Removed
- Features that have been removed

### Fixed
- Bug fixes

### Security
- Security fixes

## [1.0.0] - 2024-01-01

### Added
- Initial release
- Basic bot commands
- Database integration
- User management

### Fixed
- Fixed memory leak in session management
```

## Automated Changelog

```python
# Generate changelog from git commits
import subprocess

def generate_changelog(from_tag: str, to_tag: str):
    """Generate changelog from git commits."""
    cmd = [
        'git', 'log',
        f'{from_tag}..{to_tag}',
        '--pretty=format:- %s (%h)',
        '--no-merges'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout
```
