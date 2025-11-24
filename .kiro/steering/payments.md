# Payment Integration

## Payment Provider Setup

Configure payment provider token from BotFather:
- `/mybots` → Select bot → Payments

## Sending Invoice

```python
from telegram import LabeledPrice

async def send_invoice(update, context):
    await update.message.reply_invoice(
        title="Product Name",
        description="Product description",
        payload="product_payload",
        provider_token=PAYMENT_PROVIDER_TOKEN,
        currency="USD",
        prices=[
            LabeledPrice("Item 1", 1000),  # Amount in cents
            LabeledPrice("Tax", 200)
        ],
        start_parameter="payment-start",
        photo_url="https://example.com/product.jpg"
    )
```

## Pre-Checkout Handler

```python
async def precheckout_callback(update, context):
    query = update.pre_checkout_query
    # Validate order
    if query.invoice_payload == "product_payload":
        await query.answer(ok=True)
    else:
        await query.answer(ok=False, error_message="Invalid order")
```

## Successful Payment Handler

```python
async def successful_payment(update, context):
    payment = update.message.successful_payment
    await update.message.reply_text(
        f"Payment received: {payment.total_amount} {payment.currency}"
    )
    # Process order
    process_order(payment.invoice_payload)
```

## Register Handlers

```python
from telegram.ext import PreCheckoutQueryHandler

app.add_handler(PreCheckoutQueryHandler(precheckout_callback))
app.add_handler(MessageHandler(
    filters.SUCCESSFUL_PAYMENT,
    successful_payment
))
```
