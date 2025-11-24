# Help System

## Help Categories

```python
HELP_CATEGORIES = {
    'getting_started': {
        'title': '🚀 Getting Started',
        'description': 'Learn the basics',
        'commands': ['/start', '/help', '/settings']
    },
    'features': {
        'title': '✨ Features',
        'description': 'Explore bot features',
        'commands': ['/search', '/stats', '/profile']
    },
    'support': {
        'title': '💬 Support',
        'description': 'Get help',
        'commands': ['/feedback', '/contact', '/faq']
    }
}
```

## Help Menu

```python
async def help_command(update, context):
    """Show help menu."""
    keyboard = [
        [InlineKeyboardButton(
            cat['title'],
            callback_data=f"help_{cat_id}"
        )]
        for cat_id, cat in HELP_CATEGORIES.items()
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "📚 Help Menu\n\nChoose a category:",
        reply_markup=reply_markup
    )
```

## Category Details

```python
async def help_category_callback(update, context):
    """Show category details."""
    query = update.callback_query
    category_id = query.data.split('_')[1]
    category = HELP_CATEGORIES[category_id]
    
    message = f"{category['title']}\n\n"
    message += f"{category['description']}\n\n"
    message += "Commands:\n"
    message += "\n".join(category['commands'])
    
    keyboard = [[InlineKeyboardButton("« Back", callback_data="help_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, reply_markup=reply_markup)
```

## FAQ System

```python
FAQ = {
    'how_to_start': {
        'question': 'How do I start using the bot?',
        'answer': 'Simply send /start command to begin!'
    },
    'pricing': {
        'question': 'Is the bot free?',
        'answer': 'Yes, basic features are free. Premium features require subscription.'
    }
}

async def faq_command(update, context):
    """Show FAQ."""
    keyboard = [
        [InlineKeyboardButton(faq['question'], callback_data=f"faq_{faq_id}")]
        for faq_id, faq in FAQ.items()
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "❓ Frequently Asked Questions:",
        reply_markup=reply_markup
    )
```
