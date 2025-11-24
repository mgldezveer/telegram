# Multi-Language Support

## Language Detection

```python
def detect_user_language(update: Update) -> str:
    """Detect user's preferred language."""
    # Try Telegram language
    if update.effective_user.language_code:
        lang = update.effective_user.language_code[:2]
        if lang in SUPPORTED_LANGUAGES:
            return lang
    
    # Check database
    user = await db.get_user(update.effective_user.id)
    if user and user.language_code:
        return user.language_code
    
    # Default
    return 'en'

SUPPORTED_LANGUAGES = ['en', 'ru', 'es', 'de', 'fr', 'it', 'pt']
```

## Language Switcher

```python
async def language_command(update, context):
    """Show language selection menu."""
    keyboard = [
        [
            InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
            InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")
        ],
        [
            InlineKeyboardButton("🇪🇸 Español", callback_data="lang_es"),
            InlineKeyboardButton("🇩🇪 Deutsch", callback_data="lang_de")
        ],
        [
            InlineKeyboardButton("🇫🇷 Français", callback_data="lang_fr"),
            InlineKeyboardButton("🇮🇹 Italiano", callback_data="lang_it")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🌍 Choose your language:",
        reply_markup=reply_markup
    )

async def language_callback(update, context):
    """Handle language selection."""
    query = update.callback_query
    lang = query.data.split('_')[1]
    
    # Save to database
    await db.update_user_language(query.from_user.id, lang)
    
    await query.answer()
    await query.edit_message_text(
        i18n.get('language_changed', lang)
    )
```

## Pluralization

```python
def pluralize(count: int, forms: dict, lang: str = 'en') -> str:
    """Handle pluralization for different languages."""
    if lang == 'en':
        if count == 1:
            return forms['one']
        return forms['other']
    
    elif lang == 'ru':
        if count % 10 == 1 and count % 100 != 11:
            return forms['one']
        elif count % 10 in [2, 3, 4] and count % 100 not in [12, 13, 14]:
            return forms['few']
        else:
            return forms['many']
    
    return forms['other']

# Usage
forms = {
    'one': '{count} message',
    'few': '{count} messages',
    'many': '{count} messages',
    'other': '{count} messages'
}
text = pluralize(5, forms, 'en').format(count=5)
```
