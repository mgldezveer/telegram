# Migration Guide

## Database Migrations

### Using Alembic

```bash
# Initialize Alembic
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Add new column"

# Apply migration
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Migration Script Example

```python
"""Add user preferences

Revision ID: abc123
Create Date: 2024-01-01 12:00:00
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('users',
        sa.Column('preferences', sa.JSON(), nullable=True)
    )

def downgrade():
    op.drop_column('users', 'preferences')
```

## Version Upgrades

### From v1 to v2

1. Backup database
2. Update dependencies
3. Run migrations
4. Update configuration
5. Test thoroughly
6. Deploy

## Data Migration

```python
async def migrate_user_data():
    """Migrate user data to new format."""
    users = await db.get_all_users()
    
    for user in users:
        # Transform data
        new_data = transform_user_data(user)
        
        # Update user
        await db.update_user(user.id, new_data)
    
    logger.info(f"Migrated {len(users)} users")
```
