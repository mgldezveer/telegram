# File Download

## Download File

```python
async def download_file(bot, file_id: str, destination: str):
    """Download file by file_id."""
    file = await bot.get_file(file_id)
    await file.download_to_drive(destination)
    return destination
```

## Download with Progress

```python
import aiofiles

async def download_with_progress(bot, file_id: str, destination: str):
    """Download file with progress tracking."""
    file = await bot.get_file(file_id)
    
    # Get file URL
    file_url = file.file_path
    
    async with aiohttp.ClientSession() as session:
        async with session.get(file_url) as response:
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            async with aiofiles.open(destination, 'wb') as f:
                async for chunk in response.content.iter_chunked(8192):
                    await f.write(chunk)
                    downloaded += len(chunk)
                    progress = (downloaded / total_size) * 100
                    logger.info(f"Download progress: {progress:.1f}%")
```

## Download to Memory

```python
async def download_to_memory(bot, file_id: str) -> bytes:
    """Download file to memory."""
    file = await bot.get_file(file_id)
    
    async with aiohttp.ClientSession() as session:
        async with session.get(file.file_path) as response:
            return await response.read()
```

## Get File Info

```python
async def get_file_info(bot, file_id: str):
    """Get file information without downloading."""
    file = await bot.get_file(file_id)
    
    info = {
        'file_id': file.file_id,
        'file_unique_id': file.file_unique_id,
        'file_size': file.file_size,
        'file_path': file.file_path
    }
    
    return info
```
