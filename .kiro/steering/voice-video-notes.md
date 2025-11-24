# Voice & Video Notes

## Send Voice Message

```python
async def send_voice(update, context):
    """Send voice message."""
    with open('voice.ogg', 'rb') as voice:
        await update.message.reply_voice(
            voice=voice,
            duration=10,  # seconds
            caption="Voice message"
        )
```

## Send Video Note

```python
async def send_video_note(update, context):
    """Send video note (round video)."""
    with open('video_note.mp4', 'rb') as video:
        await update.message.reply_video_note(
            video_note=video,
            duration=5,
            length=240  # diameter in pixels
        )
```

## Receive Voice

```python
async def voice_handler(update, context):
    """Handle voice messages."""
    voice = update.message.voice
    
    logger.info(f"Voice duration: {voice.duration}s")
    logger.info(f"File size: {voice.file_size} bytes")
    
    # Download voice
    file = await context.bot.get_file(voice.file_id)
    await file.download_to_drive(f'voice_{voice.file_id}.ogg')
    
    # Transcribe voice (if you have speech-to-text)
    text = await transcribe_audio(f'voice_{voice.file_id}.ogg')
    await update.message.reply_text(f"You said: {text}")

app.add_handler(MessageHandler(filters.VOICE, voice_handler))
```

## Receive Video Note

```python
async def video_note_handler(update, context):
    """Handle video notes."""
    video_note = update.message.video_note
    
    logger.info(f"Video note duration: {video_note.duration}s")
    
    # Download video note
    file = await context.bot.get_file(video_note.file_id)
    await file.download_to_drive(f'video_note_{video_note.file_id}.mp4')

app.add_handler(MessageHandler(filters.VIDEO_NOTE, video_note_handler))
```
