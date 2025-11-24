# API Versioning

## Version in URL

```python
from fastapi import FastAPI

app = FastAPI()

@app.post('/api/v1/webhook')
async def webhook_v1(request: Request):
    """Version 1 webhook endpoint."""
    pass

@app.post('/api/v2/webhook')
async def webhook_v2(request: Request):
    """Version 2 webhook endpoint."""
    pass
```

## Version in Header

```python
@app.post('/webhook')
async def webhook(request: Request):
    version = request.headers.get('API-Version', 'v1')
    
    if version == 'v1':
        return await process_v1(request)
    elif version == 'v2':
        return await process_v2(request)
```

## Deprecation Warnings

```python
import warnings

def deprecated_function():
    warnings.warn(
        "This function is deprecated. Use new_function() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    # Old implementation
```

## Backward Compatibility

```python
async def handle_update(update: dict, version: str = 'v1'):
    """Handle update with version compatibility."""
    if version == 'v1':
        # Transform to v2 format
        update = transform_v1_to_v2(update)
    
    # Process with v2 logic
    await process_update_v2(update)
```
