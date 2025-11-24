# Media Handling

## Sending Photos

```python
async def send_photo(update, context):
    # From file
    with open('photo.jpg', 'rb') as photo:
        await update.message.reply_photo(photo, caption="Photo caption")
    
    # From URL
    await update.message.reply_photo(
        photo="https://example.com/image.jpg",
        caption="Photo from URL"
    )
```

## Receiving Photos

```python
async def photo_handler(update, context):
    photo = update.message.photo[-1]  # Highest resolution
    file = await context.bot.get_file(photo.file_id)
    await file.download_to_drive('received_photo.jpg')
```

## Sending Documents

```python
async def send_document(update, context):
    with open('document.pdf', 'rb') as doc:
        await update.message.reply_document(
            document=doc,
            filename="report.pdf",
            caption="Monthly report"
        )
```

## Sending Audio/Video

```python
# Audio
await update.message.reply_audio(audio=open('song.mp3', 'rb'))

# Video
await update.message.reply_video(video=open('video.mp4', 'rb'))

# Voice
await update.message.reply_voice(voice=open('voice.ogg', 'rb'))
```

## Media Groups

```python
from telegram import InputMediaPhoto

media_group = [
    InputMediaPhoto(open('photo1.jpg', 'rb')),
    InputMediaPhoto(open('photo2.jpg', 'rb')),
    InputMediaPhoto(open('photo3.jpg', 'rb'))
]
await update.message.reply_media_group(media=media_group)
```
