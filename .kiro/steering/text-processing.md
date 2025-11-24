# Text Processing

## Text Cleaning

```python
import re

def clean_text(text: str) -> str:
    """Clean and normalize text."""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters
    text = re.sub(r'[^\w\s.,!?-]', '', text)
    
    return text.strip()
```

## Word Count

```python
def count_words(text: str) -> dict:
    """Count words in text."""
    words = text.lower().split()
    word_count = {}
    
    for word in words:
        word = re.sub(r'[^\w]', '', word)
        if word:
            word_count[word] = word_count.get(word, 0) + 1
    
    return word_count
```

## Text Summary

```python
def summarize_text(text: str, max_length: int = 100) -> str:
    """Create text summary."""
    if len(text) <= max_length:
        return text
    
    # Simple truncation with ellipsis
    return text[:max_length-3] + '...'
```

## Keyword Extraction

```python
from collections import Counter

def extract_keywords(text: str, top_n: int = 5) -> list[str]:
    """Extract top keywords from text."""
    # Remove common words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at'}
    
    words = text.lower().split()
    words = [w for w in words if w not in stop_words and len(w) > 3]
    
    counter = Counter(words)
    return [word for word, count in counter.most_common(top_n)]
```

## Text Translation

```python
# Using googletrans library
from googletrans import Translator

translator = Translator()

async def translate_text(text: str, dest_lang: str = 'en') -> str:
    """Translate text to target language."""
    result = translator.translate(text, dest=dest_lang)
    return result.text
```
