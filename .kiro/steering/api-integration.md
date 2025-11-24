# External API Integration

## HTTP Client Setup

```python
import aiohttp
from typing import Optional

class APIClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers={'Authorization': f'Bearer {self.api_key}'}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get(self, endpoint: str, params: dict = None):
        url = f"{self.base_url}/{endpoint}"
        async with self.session.get(url, params=params) as response:
            response.raise_for_status()
            return await response.json()
    
    async def post(self, endpoint: str, data: dict):
        url = f"{self.base_url}/{endpoint}"
        async with self.session.post(url, json=data) as response:
            response.raise_for_status()
            return await response.json()
```

## Usage Example

```python
async def fetch_weather(city: str):
    async with APIClient(WEATHER_API_URL, WEATHER_API_KEY) as client:
        data = await client.get('weather', params={'city': city})
        return data

async def weather_command(update, context):
    if not context.args:
        await update.message.reply_text("Usage: /weather <city>")
        return
    
    city = " ".join(context.args)
    
    try:
        weather = await fetch_weather(city)
        text = f"Weather in {city}:\n{weather['description']}\nTemp: {weather['temp']}°C"
        await update.message.reply_text(text)
    except Exception as e:
        logger.error(f"Weather API error: {e}")
        await update.message.reply_text("Failed to fetch weather")
```

## Rate Limiting

```python
from asyncio import Semaphore

class RateLimitedClient(APIClient):
    def __init__(self, *args, max_concurrent: int = 5, **kwargs):
        super().__init__(*args, **kwargs)
        self.semaphore = Semaphore(max_concurrent)
    
    async def get(self, endpoint: str, params: dict = None):
        async with self.semaphore:
            return await super().get(endpoint, params)
```

## Retry Logic

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def fetch_with_retry(url: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response.raise_for_status()
            return await response.json()
```
