# SSL/TLS for Webhooks

## Generate Self-Signed Certificate

```bash
openssl req -newkey rsa:2048 -sha256 -nodes \
  -keyout private.key -x509 -days 365 \
  -out cert.pem \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=yourdomain.com"
```

## Set Webhook with Certificate

```python
async def set_webhook_with_cert(bot):
    """Set webhook with SSL certificate."""
    with open('cert.pem', 'rb') as cert_file:
        await bot.set_webhook(
            url=f"{WEBHOOK_URL}/webhook",
            certificate=cert_file
        )
```

## Nginx SSL Configuration

```nginx
server {
    listen 443 ssl;
    server_name yourdomain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/private.key;
    
    location /webhook {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Let's Encrypt

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d yourdomain.com
```
