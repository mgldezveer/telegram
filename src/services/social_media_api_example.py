"""Пример использования SocialMediaAPISourceManager."""

import asyncio
import os
from dotenv import load_dotenv

from src.services.content_source_manager_improved import SocialMediaAPISourceManager

# Загружаем переменные окружения
load_dotenv()

async def main():
    """Пример использования SocialMediaAPISourceManager."""
    # Создаем менеджер
    manager = SocialMediaAPISourceManager()
    
    # Пример инициализации Twitter клиента (требуются действительные ключи)
    # await manager.init_twitter_client(
    #     api_key=os.getenv('TWITTER_API_KEY'),
    #     api_secret=os.getenv('TWITTER_API_SECRET'),
    #     access_token=os.getenv('TWITTER_ACCESS_TOKEN'),
    #     access_token_secret=os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
    # )
    # 
    # Получение постов из Twitter
    # twitter_posts = await manager.get_twitter_posts('username', count=5)
    # processed_twitter_posts = await manager._process_twitter_posts(twitter_posts)
    # print(f"Получено {len(processed_twitter_posts)} обработанных постов из Twitter")
    
    # Пример инициализации Facebook клиента (требуются действительные ключи)
    # await manager.init_facebook_client(
    #     access_token=os.getenv('FACEBOOK_ACCESS_TOKEN'),
    #     page_id=os.getenv('FACEBOOK_PAGE_ID')
    # )
    # 
    # # Получение постов из Facebook
    # facebook_posts = await manager.get_facebook_posts(os.getenv('FACEBOOK_PAGE_ID'), count=5)
    # processed_facebook_posts = await manager._process_facebook_posts(facebook_posts)
    # print(f"Получено {len(processed_facebook_posts)} обработанных постов из Facebook")
    
    # Пример инициализации Instagram клиента (требуются действительные ключи)
    # await manager.init_instagram_client(
    #     access_token=os.getenv('INSTAGRAM_ACCESS_TOKEN'),
    #     instagram_account_id=os.getenv('INSTAGRAM_ACCOUNT_ID')
    # )
    # 
    # # Получение постов из Instagram
    # instagram_posts = await manager.get_instagram_posts(os.getenv('INSTAGRAM_ACCOUNT_ID'), count=5)
    # processed_instagram_posts = await manager._process_instagram_posts(instagram_posts)
    # print(f"Получено {len(processed_instagram_posts)} обработанных постов из Instagram")
    
    # Пример инициализации LinkedIn клиента (требуются действительные ключи)
    # await manager.init_linkedin_client(
    #     access_token=os.getenv('LINKEDIN_ACCESS_TOKEN')
    # )
    # 
    # # Получение постов из LinkedIn
    # linkedin_posts = await manager.get_linkedin_posts(os.getenv('LINKEDIN_ORGANIZATION_ID'), count=5)
    # processed_linkedin_posts = await manager._process_linkedin_posts(linkedin_posts)
    # print(f"Получено {len(processed_linkedin_posts)} обработанных постов из LinkedIn")
    
    print("Пример использования SocialMediaAPISourceManager завершен")

if __name__ == "__main__":
    asyncio.run(main())