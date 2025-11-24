# File Storage

## Local File Storage

```python
import os
from pathlib import Path

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

async def save_file(file_id: str, context, user_id: int):
    file = await context.bot.get_file(file_id)
    
    # Create user directory
    user_dir = UPLOAD_DIR / str(user_id)
    user_dir.mkdir(exist_ok=True)
    
    # Save file
    file_path = user_dir / f"{file_id}.jpg"
    await file.download_to_drive(file_path)
    
    return file_path
```

## Cloud Storage (S3)

```python
import boto3
from botocore.exceptions import ClientError

s3_client = boto3.client('s3')
BUCKET_NAME = 'telegram-bot-files'

async def upload_to_s3(file_path: str, object_name: str):
    try:
        s3_client.upload_file(file_path, BUCKET_NAME, object_name)
        return f"https://{BUCKET_NAME}.s3.amazonaws.com/{object_name}"
    except ClientError as e:
        logger.error(f"S3 upload failed: {e}")
        return None

async def download_from_s3(object_name: str, file_path: str):
    try:
        s3_client.download_file(BUCKET_NAME, object_name, file_path)
        return file_path
    except ClientError as e:
        logger.error(f"S3 download failed: {e}")
        return None
```

## File Metadata

```python
class FileMetadata(Base):
    __tablename__ = 'files'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    file_id = Column(String(255), nullable=False)
    file_type = Column(String(50))
    file_size = Column(Integer)
    storage_url = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
```

## File Handler

```python
async def handle_document(update, context):
    document = update.message.document
    user_id = update.effective_user.id
    
    # Download file
    file = await context.bot.get_file(document.file_id)
    local_path = await file.download_to_drive(f"temp_{document.file_id}")
    
    # Upload to cloud
    cloud_url = await upload_to_s3(local_path, f"{user_id}/{document.file_id}")
    
    # Save metadata
    metadata = FileMetadata(
        user_id=user_id,
        file_id=document.file_id,
        file_type=document.mime_type,
        file_size=document.file_size,
        storage_url=cloud_url
    )
    await db.add_file(metadata)
    
    # Clean up
    os.remove(local_path)
    
    await update.message.reply_text("File saved successfully")
```
