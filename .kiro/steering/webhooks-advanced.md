# Advanced Webhook Features

## Webhook with Secret Token

```python
import hmac
import hashlib

WEBHOOK_SECRET = "your_secret_token"

def verify_webhook(request_data: bytes, signature: str) -> bool:
    """Verify webhook signature."""
    expected = hmac.new(
        WEBHOOK_SECRET.encode(),
        request_data,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)

@app.post('/webhook')
async def webhook(request: Request):
    signature = request.headers.get('X-Telegram-Bot-Api-Secret-Token')
    body = await request.body()
    
    if not verify_webhook(body, signature):
        return {'error': 'Invalid signature'}, 403
    
    data = await request.json()
    update = Update.de_json(data, bot_app.bot)
    await bot_app.process_update(update)
    return {'status': 'ok'}
```

## Load Balancing

```python
# Use multiple webhook endpoints
WEBHOOK_URLS = [
    "https://server1.example.com/webhook",
    "https://server2.example.com/webhook",
    "https://server3.example.com/webhook"
]

# Distribute load based on user_id
def get_webhook_url(user_id: int) -> str:
    index = user_id % len(WEBHOOK_URLS)
    return WEBHOOK_URLS[index]
```

## Webhook Health Check

```python
@app.get('/health')
async def health_check():
    """Health check endpoint."""
    try:
        # Check bot connection
        me = await bot.get_me()
        
        # Check database
        await db.ping()
        
        return {
            'status': 'healthy',
            'bot': me.username,
            'timestamp': datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e)
        }, 500
```

## Webhook Metrics

```python
from prometheus_client import Counter, Histogram

webhook_requests = Counter('webhook_requests_total', 'Total webhook requests')
webhook_duration = Histogram('webhook_duration_seconds', 'Webhook processing time')

@app.post('/webhook')
@webhook_duration.time()
async def webhook(request: Request):
    webhook_requests.inc()
    # Process webhook
    pass
```
