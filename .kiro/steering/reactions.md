# Message Reactions

## Set Reaction

```python
from telegram import ReactionTypeEmoji

async def react_to_message(bot, chat_id: int, message_id: int):
    """React to a message."""
    await bot.set_message_reaction(
        chat_id=chat_id,
        message_id=message_id,
        reaction=[ReactionTypeEmoji(emoji="👍")]
    )
```

## Multiple Reactions

```python
async def add_multiple_reactions(bot, chat_id: int, message_id: int):
    """Add multiple reactions."""
    reactions = [
        ReactionTypeEmoji(emoji="👍"),
        ReactionTypeEmoji(emoji="❤️"),
        ReactionTypeEmoji(emoji="🔥")
    ]
    
    await bot.set_message_reaction(
        chat_id=chat_id,
        message_id=message_id,
        reaction=reactions
    )
```

## Remove Reactions

```python
async def remove_reactions(bot, chat_id: int, message_id: int):
    """Remove all reactions."""
    await bot.set_message_reaction(
        chat_id=chat_id,
        message_id=message_id,
        reaction=[]
    )
```

## Reaction Handler

```python
async def reaction_handler(update, context):
    """Handle message reaction updates."""
    reaction = update.message_reaction
    
    logger.info(f"User {reaction.user.id} reacted to message {reaction.message_id}")
    logger.info(f"New reactions: {reaction.new_reaction}")
    logger.info(f"Old reactions: {reaction.old_reaction}")

from telegram.ext import MessageReactionHandler
app.add_handler(MessageReactionHandler(reaction_handler))
```
