"""Content Generator for auto-posting system."""

import logging
import uuid
from typing import Optional, Dict, List
from datetime import datetime

from src.llm.manager import LLMManager
from src.models.autopost import AutoPost, PostStatus

logger = logging.getLogger(__name__)


class ContentStyle:
    """Content style configuration."""
    
    def __init__(
        self,
        tone: str = "professional",
        length: str = "medium",
        format: str = "news",
        keywords: Optional[List[str]] = None
    ):
        self.tone = tone
        self.length = length
        self.format = format
        self.keywords = keywords or []
    
    def to_dict(self) -> Dict:
        return {
            "tone": self.tone,
            "length": self.length,
            "format": self.format,
            "keywords": self.keywords
        }


class AutoPostContentGenerator:
    """Content generator using LLM."""
    
    def __init__(self, llm_manager: Optional[LLMManager] = None):
        """Initialize content generator.
        
        Args:
            llm_manager: LLM Manager instance
        """
        self.llm_manager = llm_manager
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, str]:
        """Load content templates."""
        return {
            "news": """Создай новостной пост на тему: {theme}

Требования:
- Стиль: {tone}
- Длина: {length}
- Формат: новостная заметка
- Ключевые слова: {keywords}

Пост должен быть информативным и интересным для читателей.""",
            
            "tips": """Создай пост с полезными советами на тему: {theme}

Требования:
- Стиль: {tone}
- Длина: {length}
- Формат: список советов
- Ключевые слова: {keywords}

Пост должен содержать практические рекомендации.""",
            
            "story": """Создай пост-историю на тему: {theme}

Требования:
- Стиль: {tone}
- Длина: {length}
- Формат: повествование
- Ключевые слова: {keywords}

Пост должен быть увлекательным и эмоциональным.""",
            
            "announcement": """Создай пост-анонс на тему: {theme}

Требования:
- Стиль: {tone}
- Длина: {length}
- Формат: анонс
- Ключевые слова: {keywords}

Пост должен привлекать внимание и создавать интерес."""
        }
    
    async def generate_post(
        self,
        theme: str,
        style: ContentStyle,
        channel_id: int,
        template: Optional[str] = None
    ) -> AutoPost:
        """Generate post content.
        
        Args:
            theme: Post theme/topic
            style: Content style
            channel_id: Target channel ID
            template: Optional custom template
            
        Returns:
            Generated post object
        """
        logger.info(f"Generating post for channel {channel_id}, theme: {theme}")
        
        # Generate content
        content = await self._generate_content(theme, style, template)
        
        # Extract hashtags
        hashtags = self._extract_hashtags(content, style.keywords)
        
        # Create post object
        post = AutoPost(
            id=str(uuid.uuid4()),
            channel_id=channel_id,
            content=content,
            status=PostStatus.DRAFT.value,
            theme=theme,
            style=style.to_dict(),
            hashtags=hashtags,
            created_at=datetime.utcnow()
        )
        
        logger.info(f"✅ Generated post {post.id}")
        return post
    
    async def _generate_content(
        self,
        theme: str,
        style: ContentStyle,
        template: Optional[str] = None
    ) -> str:
        """Generate content using LLM.
        
        Args:
            theme: Content theme
            style: Content style
            template: Optional template
            
        Returns:
            Generated content text
        """
        # Build prompt
        if template:
            prompt = template
        else:
            template_key = style.format if style.format in self.templates else "news"
            prompt = self.templates[template_key]
        
        # Format prompt
        prompt = prompt.format(
            theme=theme,
            tone=style.tone,
            length=self._get_length_description(style.length),
            keywords=", ".join(style.keywords) if style.keywords else "нет"
        )
        
        # Generate with LLM
        if self.llm_manager:
            try:
                content = await self.llm_manager.generate(
                    prompt=prompt,
                    max_tokens=self._get_max_tokens(style.length),
                    temperature=0.7
                )
                return content.strip()
            except Exception as e:
                logger.error(f"LLM generation failed: {e}")
                return self._generate_fallback_content(theme, style)
        else:
            return self._generate_fallback_content(theme, style)
    
    def _get_length_description(self, length: str) -> str:
        """Get length description."""
        descriptions = {
            "short": "короткий (до 500 символов)",
            "medium": "средний (500-1000 символов)",
            "long": "длинный (1000-2000 символов)"
        }
        return descriptions.get(length, "средний")
    
    def _get_max_tokens(self, length: str) -> int:
        """Get max tokens for length."""
        tokens = {
            "short": 200,
            "medium": 400,
            "long": 800
        }
        return tokens.get(length, 400)
    
    def _generate_fallback_content(self, theme: str, style: ContentStyle) -> str:
        """Generate fallback content when LLM unavailable."""
        return f"""📢 {theme}

Это автоматически сгенерированный пост на тему "{theme}".

Стиль: {style.tone}
Формат: {style.format}

#автопост #контент"""
    
    def _extract_hashtags(self, content: str, keywords: List[str]) -> List[str]:
        """Extract or generate hashtags."""
        hashtags = []
        
        # Extract existing hashtags from content
        import re
        found_tags = re.findall(r'#\w+', content)
        hashtags.extend(found_tags)
        
        # Add keyword-based hashtags
        for keyword in keywords:
            tag = f"#{keyword.replace(' ', '_')}"
            if tag not in hashtags:
                hashtags.append(tag)
        
        return hashtags[:5]  # Limit to 5 hashtags
    
    async def apply_template(self, content: str, template: str) -> str:
        """Apply template to content.
        
        Args:
            content: Original content
            template: Template string
            
        Returns:
            Formatted content
        """
        try:
            return template.format(content=content)
        except Exception as e:
            logger.error(f"Template application failed: {e}")
            return content
    
    def format_post(self, post: AutoPost) -> str:
        """Format post for display.
        
        Args:
            post: Post object
            
        Returns:
            Formatted post text
        """
        text = post.content
        
        # Add hashtags if not already in content
        if post.hashtags:
            hashtags_text = " ".join(post.hashtags)
            if hashtags_text not in text:
                text += f"\n\n{hashtags_text}"
        
        return text
