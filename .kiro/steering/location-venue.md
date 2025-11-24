# Location & Venue

## Send Location

```python
async def send_location(update, context):
    """Send location."""
    await update.message.reply_location(
        latitude=40.7128,
        longitude=-74.0060
    )
```

## Send Live Location

```python
async def send_live_location(update, context):
    """Send live location that updates."""
    message = await update.message.reply_location(
        latitude=40.7128,
        longitude=-74.0060,
        live_period=900  # 15 minutes
    )
    
    # Store message to update later
    context.user_data['live_location_msg'] = message.message_id
```

## Update Live Location

```python
async def update_live_location(bot, chat_id: int, message_id: int, lat: float, lon: float):
    """Update live location."""
    await bot.edit_message_live_location(
        chat_id=chat_id,
        message_id=message_id,
        latitude=lat,
        longitude=lon
    )
```

## Stop Live Location

```python
async def stop_live_location(bot, chat_id: int, message_id: int):
    """Stop live location updates."""
    await bot.stop_message_live_location(
        chat_id=chat_id,
        message_id=message_id
    )
```

## Send Venue

```python
async def send_venue(update, context):
    """Send venue information."""
    await update.message.reply_venue(
        latitude=40.7580,
        longitude=-73.9855,
        title="Times Square",
        address="Manhattan, NY 10036, USA",
        foursquare_id="4bd7e8e0f964a520f4941fe3"  # Optional
    )
```

## Receive Location

```python
async def location_handler(update, context):
    """Handle received location."""
    location = update.message.location
    
    logger.info(f"Received location: {location.latitude}, {location.longitude}")
    
    # Process location
    nearby = await find_nearby_places(location.latitude, location.longitude)
    await update.message.reply_text(f"Found {len(nearby)} places nearby")

app.add_handler(MessageHandler(filters.LOCATION, location_handler))
```
