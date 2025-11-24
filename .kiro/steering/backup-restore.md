# Backup & Restore

## Database Backup

```python
import subprocess
from datetime import datetime

def backup_database():
    """Create database backup."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f"backup_{timestamp}.sql"
    
    # PostgreSQL backup
    subprocess.run([
        'pg_dump',
        '-h', 'localhost',
        '-U', 'username',
        '-d', 'database_name',
        '-f', backup_file
    ])
    
    return backup_file
```

## Automated Backups

```python
async def schedule_backups(context):
    """Schedule daily backups."""
    context.job_queue.run_daily(
        backup_job,
        time=datetime.time(hour=2, minute=0),
        name='daily_backup'
    )

async def backup_job(context):
    """Perform backup."""
    backup_file = backup_database()
    
    # Upload to cloud storage
    await upload_to_s3(backup_file, f"backups/{backup_file}")
    
    # Notify admins
    for admin_id in config.bot.admin_ids:
        await context.bot.send_message(
            chat_id=admin_id,
            text=f"✅ Backup completed: {backup_file}"
        )
```

## Restore Database

```python
def restore_database(backup_file: str):
    """Restore database from backup."""
    subprocess.run([
        'psql',
        '-h', 'localhost',
        '-U', 'username',
        '-d', 'database_name',
        '-f', backup_file
    ])
```
