# Интеграция с API социальных сетей

## Обзор

Класс `SocialMediaAPISourceManager` предоставляет возможность интеграции с API различных социальных сетей (Twitter, Facebook, Instagram, LinkedIn) для получения и обработки контента.

## Установка зависимостей

Для работы с API социальных сетей добавьте следующие зависимости:

```bash
pip install tweepy facebook-sdk
```

Или установите все зависимости из файла `requirements.txt`:

```bash
pip install -r requirements.txt
```

## Конфигурация

Для использования API социальных сетей необходимо настроить соответствующие переменные окружения в файле `.env`:

```env
# Twitter API Configuration
TWITTER_API_KEY=your_twitter_api_key_here
TWITTER_API_SECRET=your_twitter_api_secret_here
TWITTER_ACCESS_TOKEN=your_twitter_access_token_here
TWITTER_ACCESS_TOKEN_SECRET=your_twitter_access_token_secret_here

# Facebook API Configuration
FACEBOOK_ACCESS_TOKEN=your_facebook_access_token_here
FACEBOOK_PAGE_ID=your_facebook_page_id_here

# Instagram API Configuration
INSTAGRAM_ACCESS_TOKEN=your_instagram_access_token_here
INSTAGRAM_ACCOUNT_ID=your_instagram_account_id_here

# LinkedIn API Configuration
LINKEDIN_ACCESS_TOKEN=your_linkedin_access_token_here
LINKEDIN_ORGANIZATION_ID=your_linkedin_organization_id_here
```

## Использование

### Инициализация менеджера

```python
from src.services.content_source_manager_improved import SocialMediaAPISourceManager

# Создание экземпляра менеджера
manager = SocialMediaAPISourceManager(alert_manager=alert_manager)
```

### Инициализация клиентов API

#### Twitter

```python
await manager.init_twitter_client(
    api_key=os.getenv('TWITTER_API_KEY'),
    api_secret=os.getenv('TWITTER_API_SECRET'),
    access_token=os.getenv('TWITTER_ACCESS_TOKEN'),
    access_token_secret=os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
)
```

#### Facebook

```python
await manager.init_facebook_client(
    access_token=os.getenv('FACEBOOK_ACCESS_TOKEN'),
    page_id=os.getenv('FACEBOOK_PAGE_ID')
)
```

#### Instagram

```python
await manager.init_instagram_client(
    access_token=os.getenv('INSTAGRAM_ACCESS_TOKEN'),
    instagram_account_id=os.getenv('INSTAGRAM_ACCOUNT_ID')
)
```

#### LinkedIn

```python
await manager.init_linkedin_client(
    access_token=os.getenv('LINKEDIN_ACCESS_TOKEN')
)
```

### Получение и обработка контента

#### Получение постов из Twitter

```python
# Получение последних постов
twitter_posts = await manager.get_twitter_posts('username', count=10)

# Обработка постов для извлечения контента
processed_posts = await manager._process_twitter_posts(twitter_posts)
```

#### Получение постов из Facebook

```python
# Получение последних постов
facebook_posts = await manager.get_facebook_posts(os.getenv('FACEBOOK_PAGE_ID'), count=10)

# Обработка постов для извлечения контента
processed_posts = await manager._process_facebook_posts(facebook_posts)
```

#### Получение постов из Instagram

```python
# Получение последних постов
instagram_posts = await manager.get_instagram_posts(os.getenv('INSTAGRAM_ACCOUNT_ID'), count=10)

# Обработка постов для извлечения контента
processed_posts = await manager._process_instagram_posts(instagram_posts)
```

#### Получение постов из LinkedIn

```python
# Получение последних постов
linkedin_posts = await manager.get_linkedin_posts(os.getenv('LINKEDIN_ORGANIZATION_ID'), count=10)

# Обработка постов для извлечения контента
processed_posts = await manager._process_linkedin_posts(linkedin_posts)
```

## Методы класса

### `__init__(self, alert_manager=None)`

Инициализирует менеджер API социальных сетей.

### `init_twitter_client(self, api_key, api_secret, access_token, access_token_secret)`

Инициализирует клиент Twitter API.

### `init_facebook_client(self, access_token, page_id=None)`

Инициализирует клиент Facebook API.

### `init_instagram_client(self, access_token, instagram_account_id)`

Инициализирует клиент Instagram API.

### `init_linkedin_client(self, access_token)`

Инициализирует клиент LinkedIn API.

### `get_twitter_posts(self, username, count=10)`

Получает последние посты из Twitter аккаунта.

### `get_facebook_posts(self, page_id, count=10)`

Получает последние посты из Facebook страницы.

### `get_instagram_posts(self, instagram_account_id, count=10)`

Получает последние посты из Instagram аккаунта.

### `get_linkedin_posts(self, organization_id, count=10)`

Получает последние посты из LinkedIn организации.

### `_process_twitter_posts(self, posts)`

Обрабатывает посты Twitter для извлечения контента.

### `_process_facebook_posts(self, posts)`

Обрабатывает посты Facebook для извлечения контента.

### `_process_instagram_posts(self, posts)`

Обрабатывает посты Instagram для извлечения контента.

### `_process_linkedin_posts(self, posts)`

Обрабатывает посты LinkedIn для извлечения контента.

## Пример полного использования

```python
import asyncio
import os
from dotenv import load_dotenv

from src.services.content_source_manager_improved import SocialMediaAPISourceManager

async def main():
    # Загружаем переменные окружения
    load_dotenv()
    
    # Создаем менеджер
    manager = SocialMediaAPISourceManager()
    
    # Инициализация Twitter клиента
    await manager.init_twitter_client(
        api_key=os.getenv('TWITTER_API_KEY'),
        api_secret=os.getenv('TWITTER_API_SECRET'),
        access_token=os.getenv('TWITTER_ACCESS_TOKEN'),
        access_token_secret=os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
    )
    
    # Получение и обработка постов
    twitter_posts = await manager.get_twitter_posts('username', count=5)
    processed_posts = await manager._process_twitter_posts(twitter_posts)
    
    for post in processed_posts:
        print(f"Content: {post['content'][:100]}...")

if __name__ == "__main__":
    asyncio.run(main())
```

## Обработка ошибок

Класс включает в себя комплексную систему логирования и обработки ошибок. При возникновении ошибок они будут записаны в лог и, при наличии `alert_manager`, отправлены соответствующие уведомления.

## Метрики

При включении Prometheus метрик система будет отслеживать:

- Время выполнения операций получения контента
- Количество ошибок при получении данных
- Статусы различных социальных сетей