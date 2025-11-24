"""Content generation service using AI."""

import logging
import asyncio
from typing import Optional
from dataclasses import dataclass
from src.config import config
from src.models import Post, PostStatus

logger = logging.getLogger(__name__)


@dataclass
class ContentStyle:
    """Content style configuration."""
    tone: str = "professional"
    length: str = "medium"
    emoji_usage: bool = True
    hashtag_count: int = 3
    media_preference: str = "text"


@dataclass
class ValidationResult:
    """Content validation result."""
    valid: bool
    errors: list[str]
    warnings: list[str]


class ContentGenerator:
    """AI-powered content generator."""
    
    def __init__(self):
        # Initialize appropriate AI client
        if config.ai.provider == "groq":
            from groq import AsyncGroq
            self.client = AsyncGroq(api_key=config.ai.api_key)
        else:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=config.ai.api_key)
        
        self.provider = config.ai.provider
        self.max_retries = 3
        self.retry_delay = 2  # seconds
    
    async def generate_post(
        self,
        theme: str,
        style: ContentStyle,
        channel_id: int
    ) -> Post:
        """Generate a post with the given theme and style."""
        logger.info(f"Generating post for theme: {theme}, style: {style.tone}")
        
        prompt = self._build_prompt(theme, style)
        
        for attempt in range(self.max_retries):
            try:
                content = await self._call_ai(prompt)
                
                # Validate content
                validation = self.validate_content(content)
                if not validation.valid:
                    logger.warning(f"Generated content failed validation: {validation.errors}")
                    if attempt < self.max_retries - 1:
                        # Adjust prompt for retry
                        prompt = self._adjust_prompt_for_retry(prompt, validation.errors)
                        await asyncio.sleep(self.retry_delay * (2 ** attempt))
                        continue
                    else:
                        raise ValueError(f"Content validation failed after {self.max_retries} attempts")
                
                # Create post object
                post = Post(
                    content=content,
                    channel_id=channel_id,
                    status=PostStatus.DRAFT,
                    style_tone=style.tone,
                    style_length=style.length,
                    theme=theme
                )
                
                logger.info(f"Successfully generated post for channel {channel_id}")
                return post
                
            except Exception as e:
                logger.error(f"Generation attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))
                else:
                    raise
        
        raise RuntimeError("Failed to generate content after all retries")
    
    async def generate_with_template(
        self,
        template: str,
        params: dict,
        channel_id: int
    ) -> Post:
        """Generate content using a template."""
        logger.info(f"Generating post with template for channel {channel_id}")
        
        try:
            # Fill template with parameters
            content = template.format(**params)
            
            # Validate
            validation = self.validate_content(content)
            if not validation.valid:
                raise ValueError(f"Template content validation failed: {validation.errors}")
            
            post = Post(
                content=content,
                channel_id=channel_id,
                status=PostStatus.DRAFT
            )
            
            return post
            
        except Exception as e:
            logger.error(f"Template generation failed: {e}")
            raise
    
    def validate_content(self, content: str) -> ValidationResult:
        """Validate generated content."""
        errors = []
        warnings = []
        
        # Check minimum length
        if len(content) < 10:
            errors.append("Content too short (minimum 10 characters)")
        
        # Check maximum length (Telegram limit)
        if len(content) > 4096:
            errors.append("Content exceeds Telegram message limit (4096 characters)")
        
        # Check for empty content
        if not content.strip():
            errors.append("Content is empty")
        
        # Check for inappropriate patterns (basic)
        inappropriate_patterns = ["spam", "scam", "click here now"]
        for pattern in inappropriate_patterns:
            if pattern.lower() in content.lower():
                warnings.append(f"Potentially inappropriate content detected: {pattern}")
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def _build_prompt(self, theme: str, style: ContentStyle) -> str:
        """Build AI prompt based on theme and style."""
        length_guide = {
            "short": "1-2 sentences",
            "medium": "3-5 sentences",
            "long": "6-10 sentences"
        }
        
        emoji_instruction = "Use emojis appropriately" if style.emoji_usage else "Do not use emojis"
        
        prompt = f"""Create a {style.tone} social media post about {theme}.

Requirements:
- Length: {length_guide.get(style.length, '3-5 sentences')}
- Tone: {style.tone}
- {emoji_instruction}
- Make it engaging and informative
- Do not include hashtags in the main text

Write only the post content, nothing else."""
        
        return prompt
    
    def _adjust_prompt_for_retry(self, original_prompt: str, errors: list[str]) -> str:
        """Adjust prompt based on validation errors."""
        adjustments = "\n\nPrevious attempt had issues:\n"
        for error in errors:
            adjustments += f"- {error}\n"
        adjustments += "\nPlease fix these issues in your response."
        
        return original_prompt + adjustments
    
    async def _call_ai(self, prompt: str) -> str:
        """Call AI API to generate content."""
        try:
            response = await self.client.chat.completions.create(
                model=config.ai.model,
                messages=[
                    {"role": "system", "content": "You are a professional content creator for social media."},
                    {"role": "user", "content": prompt}
                ],
                temperature=config.ai.temperature,
                max_tokens=config.ai.max_tokens
            )
            
            content = response.choices[0].message.content.strip()
            return content
            
        except Exception as e:
            logger.error(f"AI API call failed: {e}")
            raise
