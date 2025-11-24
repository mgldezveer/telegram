# Internationalization (i18n)

## Language Support

Support multiple languages for bot messages:

```python
# locales/en.json
{
    "welcome": "Welcome to the bot!",
    "help": "Available commands:\n/start - Start the bot\n/help - Show this message",
    "error": "An error occurred. Please try again."
}

# locales/ru.json
{
    "welcome": "Добро пожаловать в бот!",
    "help": "Доступные команды:\n/start - Запустить бота\n/help - Показать это сообщение",
    "error": "Произошла ошибка. Пожалуйста, попробуйте снова."
}
```

## Translation Manager

```python
import json
from pathlib import Path

class Translator:
    def __init__(self, default_lang: str = "en"):
        self.default_lang = default_lang
        self.translations = {}
        self._load_translations()
    
    def _load_translations(self):
        locale_dir = Path("locales")
        for file in locale_dir.glob("*.json"):
            lang = file.stem
            with open(file, "r", encoding="utf-8") as f:
                self.translations[lang] = json.load(f)
    
    def get(self, key: str, lang: str = None) -> str:
        lang = lang or self.default_lang
        return self.translations.get(lang, {}).get(
            key,
            self.translations[self.default_lang].get(key, key)
        )

# Global translator instance
translator = Translator()
```

## Usage in Handlers

```python
async def start_command(update: Update, context):
    user_lang = update.effective_user.language_code or "en"
    welcome_msg = translator.get("welcome", user_lang)
    await update.message.reply_text(welcome_msg)
```

## User Language Detection

```python
def get_user_language(update: Update) -> str:
    """Get user's preferred language."""
    # Try to get from user settings
    user_lang = update.effective_user.language_code
    
    # Fallback to default
    supported_langs = ["en", "ru", "es", "de"]
    if user_lang not in supported_langs:
        user_lang = "en"
    
    return user_lang
```

## Best Practices

- Store user language preference in database
- Provide language selection command
- Use placeholders for dynamic content
- Keep translations in sync across languages
- Use professional translation services for production
- Test with different languages and character sets
