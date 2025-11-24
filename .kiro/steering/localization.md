# Localization

## Locale Files Structure

```
locales/
├── en/
│   ├── messages.json
│   └── errors.json
├── ru/
│   ├── messages.json
│   └── errors.json
└── es/
    ├── messages.json
    └── errors.json
```

## Translation Manager

```python
import json
from pathlib import Path
from typing import Dict

class Localization:
    def __init__(self, default_lang: str = 'en'):
        self.default_lang = default_lang
        self.translations: Dict[str, Dict] = {}
        self._load_all()
    
    def _load_all(self):
        locale_dir = Path('locales')
        for lang_dir in locale_dir.iterdir():
            if lang_dir.is_dir():
                lang = lang_dir.name
                self.translations[lang] = {}
                
                for file in lang_dir.glob('*.json'):
                    with open(file, 'r', encoding='utf-8') as f:
                        category = file.stem
                        self.translations[lang][category] = json.load(f)
    
    def get(self, key: str, lang: str = None, **kwargs) -> str:
        lang = lang or self.default_lang
        category, msg_key = key.split('.', 1)
        
        text = (self.translations.get(lang, {})
                .get(category, {})
                .get(msg_key))
        
        if not text:
            text = (self.translations.get(self.default_lang, {})
                    .get(category, {})
                    .get(msg_key, key))
        
        return text.format(**kwargs) if kwargs else text

i18n = Localization()
```

## Usage in Handlers

```python
async def start_command(update, context):
    lang = update.effective_user.language_code or 'en'
    welcome = i18n.get('messages.welcome', lang, 
                       name=update.effective_user.first_name)
    await update.message.reply_text(welcome)
```

## Language Selection

```python
async def set_language_command(update, context):
    keyboard = [
        [InlineKeyboardButton("English", callback_data="lang_en")],
        [InlineKeyboardButton("Русский", callback_data="lang_ru")],
        [InlineKeyboardButton("Español", callback_data="lang_es")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Choose your language:",
        reply_markup=reply_markup
    )

async def language_callback(update, context):
    query = update.callback_query
    lang = query.data.split('_')[1]
    
    # Save to database
    await db.update_user_language(query.from_user.id, lang)
    
    await query.answer()
    await query.edit_message_text(
        i18n.get('messages.language_set', lang)
    )
```
