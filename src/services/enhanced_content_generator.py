"""Улучшенный генератор контента с поддержкой кэширования."""

import logging
import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from src.models.autopost import AutoPost, PostStatus
from src.cache import cache

logger = logging.getLogger(__name__)


@dataclass
class ContentStyle:
    """Content style configuration."""
    tone: str = "professional" # professional, casual, humorous, formal
    length: str = "medium"  # short, medium, long
    format: str = "news" # news, tips, story, announcement
    keywords: List[str] = None
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tone": self.tone,
            "length": self.length,
            "format": self.format,
            "keywords": self.keywords
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContentStyle':
        """Create from dictionary."""
        return cls(
            tone=data.get("tone", "professional"),
            length=data.get("length", "medium"),
            format=data.get("format", "news"),
            keywords=data.get("keywords", [])
        )


class EnhancedContentGenerator:
    """Улучшенный генератор контента с поддержкой кэширования."""
    
    def __init__(self, llm_manager=None, cache_ttl: int = 3600):  # 1 hour default TTL
        """Initialize enhanced content generator.
        
        Args:
            llm_manager: LLM manager instance for content generation
            cache_ttl: Time-to-live for cached content in seconds
        """
        self.llm_manager = llm_manager
        self.cache_ttl = cache_ttl
        self._templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, str]:
        """Load content templates."""
        return {
            "news": """Создай новостной пост на тему: {theme}

Стиль: {tone}
Длина: {length}
Ключевые слова: {keywords}

Требования:
- Информативный и актуальный контент
- Четкая структура с заголовком
- Факты и данные
- Призыв к действию в конце

Формат: Telegram пост с эмодзи""",
            
            "tips": """Создай пост с полезными советами на тему: {theme}

Стиль: {tone}
Длина: {length}
Ключевые слова: {keywords}

Требования:
- 3-5 практических советов
- Простой и понятный язык
- Примеры применения
- Мотивирующий тон

Формат: Telegram пост с эмодзи и нумерацией""",
            
            "story": """Создай увлекательную историю на тему: {theme}

Стиль: {tone}
Длина: {length}
Ключевые слова: {keywords}

Требования:
- Захватывающее начало
- Развитие сюжета
- Эмоциональная составляющая
- Вывод или мораль

Формат: Telegram пост с эмодзи""",
            
            "announcement": """Создай объявление на тему: {theme}

Стиль: {tone}
Длина: {length}
Ключевые слова: {keywords}

Требования:
- Четкая и краткая информация
- Важные детали (дата, время, место)
- Призыв к действию
- Контактная информация

Формат: Telegram пост с эмодзи"""
        }
    
    def _generate_cache_key(self, theme: str, style: ContentStyle, template: Optional[str] = None) -> str:
        """Generate cache key based on generation parameters.
        
        Args:
            theme: Post theme/topic
            style: Content style configuration
            template: Optional custom template
            
        Returns:
            Cache key string
        """
        # Create a unique key based on all parameters
        key_data = {
            "theme": theme,
            "style": style.to_dict(),
            "template": template or "default"
        }
        
        # Create hash from the key data
        key_str = json.dumps(key_data, sort_keys=True)
        hash_obj = hashlib.md5(key_str.encode())
        return f"content_gen:{hash_obj.hexdigest()}"
    
    async def generate_post(
        self,
        theme: str,
        style: ContentStyle,
        template: Optional[str] = None,
        channel_id: Optional[int] = None
    ) -> AutoPost:
        """Generate a post using LLM with caching support.
        
        Args:
            theme: Post theme/topic
            style: Content style configuration
            template: Optional custom template
            channel_id: Optional channel ID for the post
        
        Returns:
            Generated post object
        
        Raises:
            RuntimeError: If generation fails
        """
        # Generate cache key
        cache_key = self._generate_cache_key(theme, style, template)
        
        try:
            # Try to get from cache first
            cached_result = await cache.get(cache_key)
            if cached_result:
                logger.info(f"✅ Content retrieved from cache: {cache_key[:8]}...")
                
                # Deserialize cached post
                cached_data = json.loads(cached_result)
                post = AutoPost(
                    id=cached_data['id'],
                    channel_id=cached_data['channel_id'],
                    content=cached_data['content'],
                    status=cached_data['status'],
                    theme=cached_data['theme'],
                    style=cached_data['style'],
                    hashtags=cached_data['hashtags'],
                    created_at=datetime.fromisoformat(cached_data['created_at'])
                )
                
                # Update the cached item's TTL
                await cache.set(cache_key, cached_result, self.cache_ttl)
                
                return post
            
            # Generate content if not in cache
            content = await self._generate_content(theme, style, template)
            
            # Extract hashtags
            hashtags = self._extract_hashtags(content, style.keywords)
            
            # Create post object
            post = AutoPost(
                id=f"gen_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(theme)[:8]}",
                channel_id=channel_id,
                content=content,
                status=PostStatus.DRAFT.value,
                theme=theme,
                style=style.to_dict(),
                hashtags=hashtags,
                created_at=datetime.utcnow()
            )
            
            # Cache the result
            post_data = {
                'id': post.id,
                'channel_id': post.channel_id,
                'content': post.content,
                'status': post.status,
                'theme': post.theme,
                'style': post.style,
                'hashtags': post.hashtags,
                'created_at': post.created_at.isoformat()
            }
            
            await cache.set(cache_key, json.dumps(post_data), self.cache_ttl)
            
            logger.info(f"✅ Generated and cached post: {post.id} (theme: {theme})")
            return post
            
        except Exception as e:
            logger.error(f"❌ Failed to generate post: {e}")
            raise RuntimeError(f"Failed to generate post: {e}")
    
    async def _generate_content(
        self,
        theme: str,
        style: ContentStyle,
        template: Optional[str] = None
    ) -> str:
        """Generate content using LLM.
        
        Args:
            theme: Post theme/topic
            style: Content style configuration
            template: Optional custom template
        
        Returns:
            Generated content text
        """
        # Get template
        if template:
            prompt_template = template
        else:
            prompt_template = self._templates.get(style.format, self._templates["news"])
        
        # Format prompt
        prompt = prompt_template.format(
            theme=theme,
            tone=style.tone,
            length=self._get_length_description(style.length),
            keywords=", ".join(style.keywords) if style.keywords else "нет"
        )
        
        # Generate content using LLM
        if self.llm_manager:
            try:
                # LLM Manager returns string directly
                content = await self.llm_manager.generate(
                    prompt=prompt,
                    max_tokens=self._get_max_tokens(style.length),
                    temperature=0.7
                )
                
                if not content or len(content.strip()) == 0:
                    raise ValueError("Empty content generated")
                
                logger.info(f"✅ LLM generated {len(content)} characters")
                return content
                
            except Exception as e:
                logger.error(f"❌ LLM generation failed: {e}")
                # Fallback to template-based content
                return self._generate_fallback_content(theme, style)
        else:
            # No LLM manager, use fallback
            logger.warning("⚠️ No LLM manager provided, using fallback content")
            return self._generate_fallback_content(theme, style)
    
    def _generate_fallback_content(self, theme: str, style: ContentStyle) -> str:
        """Generate fallback content when LLM is unavailable.
        
        Args:
            theme: Post theme/topic
            style: Content style configuration
        
        Returns:
            Fallback content text
        """
        emoji_map = {
            "news": "📰",
            "tips": "💡",
            "story": "📖",
            "announcement": "📢"
        }
        
        emoji = emoji_map.get(style.format, "📝")
        
        content = f"""{emoji} {theme}

Это автоматически сгенерированный пост на тему "{theme}".

Стиль: {style.tone}
Формат: {style.format}

#автопост #контент"""
        
        if style.keywords:
            content += "\n" + " ".join(f"#{kw.replace(' ', '_')}" for kw in style.keywords)
        
        return content
    
    def _get_length_description(self, length: str) -> str:
        """Get length description for prompt.
        
        Args:
            length: Length code (short, medium, long)
        
        Returns:
            Length description
        """
        descriptions = {
            "short": "короткий (до 500 символов)",
            "medium": "средний (500-1000 символов)",
            "long": "длинный (1000-2000 символов)"
        }
        return descriptions.get(length, descriptions["medium"])
    
    def _get_max_tokens(self, length: str) -> int:
        """Get max tokens for length.
        
        Args:
            length: Length code (short, medium, long)
        
        Returns:
            Max tokens
        """
        tokens = {
            "short": 300,
            "medium": 600,
            "long": 1200
        }
        return tokens.get(length, 600)
    
    def _extract_hashtags(self, content: str, keywords: List[str]) -> List[str]:
        """Extract hashtags from content and keywords.
        
        Args:
            content: Post content
            keywords: Keywords to include
        
        Returns:
            List of hashtags
        """
        hashtags = []
        
        # Extract existing hashtags from content
        import re
        found_tags = re.findall(r'#\w+', content)
        hashtags.extend(found_tags)
        
        # Add keyword-based hashtags
        for keyword in keywords:
            tag = f"#{keyword.replace(' ', '_').lower()}"
            if tag not in hashtags:
                hashtags.append(tag)
        
        return hashtags[:10]  # Limit to 10 hashtags
    
    async def apply_template(self, content: str, template: str) -> str:
        """Apply template to content.
        
        Args:
            content: Original content
            template: Template string with {content} placeholder
        
        Returns:
            Formatted content
        """
        try:
            return template.format(content=content)
        except Exception as e:
            logger.error(f"❌ Failed to apply template: {e}")
            return content
    
    async def format_post(self, post: AutoPost) -> str:
        """Format post for publishing.
        
        Args:
            post: Post object
        
        Returns:
            Formatted post text
        """
        content = post.content
        
        # Add hashtags if not already in content
        if post.hashtags:
            existing_tags = set(tag.lower() for tag in post.hashtags if tag in content)
            new_tags = [tag for tag in post.hashtags if tag.lower() not in existing_tags]
            
            if new_tags:
                content += "\n\n" + " ".join(new_tags)
        
        return content
    
    def set_llm_manager(self, llm_manager):
        """Set LLM manager instance.
        
        Args:
            llm_manager: LLM manager instance
        """
        self.llm_manager = llm_manager
        logger.info("✅ LLM manager set for content generator")
    
    async def clear_cache(self):
        """Clear all cached content generation results."""
        # Delete all keys with the content_gen prefix
        keys = await cache.keys("content_gen:*")
        for key in keys:
            await cache.delete(key)
        logger.info(f"✅ Cleared {len(keys)} cached content generation results")
    
    async def get_cache_stats(self) -> dict:
        """Get cache statistics for content generation.
        
        Returns:
            Dictionary with cache statistics
        """
        keys = await cache.keys("content_gen:*")
        return {
            'cached_generations': len(keys),
            'cache_ttl': self.cache_ttl
        }