# Webhook Configuration

## Setting Up Webhook

```python
from telegram.ext import Application

app = Application.builder().token(TOKEN).build()

# Set webhook
await app.bot.set_webhook(
    url=f"{WEBHOOK_URL}/webhook",
    allowed_updates=["message", "callback_query"]
)

# Run webhook
app.run_webhook(
    listen="0.0.0.0",
    port=8443,
    url_path="webhook",
    webhook_url=f"{WEBHOOK_URL}/webhook",
    cert="cert.pem"  # Optional SSL certificate
)
```

## Flask Integration

```python
from flask import Flask, request
from telegram import Update

app = Flask(__name__)
bot_app = Application.builder().token(TOKEN).build()

@app.route('/webhook', methods=['POST'])
async def webhook():
    update = Update.de_json(request.get_json(), bot_app.bot)
    await bot_app.process_update(update)
    return 'OK'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8443)
```

## FastAPI Integration

```python
from fastapi import FastAPI, Request
from telegram import Update

app = FastAPI()
bot_app = Application.builder().token(TOKEN).build()

@app.post('/webhook')
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, bot_app.bot)
    await bot_app.process_update(update)
    return {'status': 'ok'}
```

## Webhook Security

- Use HTTPS only
- Validate webhook secret token
- Whitelist Telegram IP ranges
- Use SSL certificates
