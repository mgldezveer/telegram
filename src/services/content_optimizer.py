"""Content optimization service."""

import logging
import re
from typing import Optional
from dataclasses import dataclass
from src.models import Post

logger = logging.getLogger(__name__)


@dataclass
class EngagementScore:
    """Engagement potential score."""
    score: float  # 0.0 to 1.0
    readability: float
    engagement_potential: float
    recommendations: list[str]


class ContentOptimizer:
    """Content optimization and enhancement service."""
    
    def __init__(self):
        self.max_hashtags = 10
        self.min_readability_score = 0.6
    
    async def optimize(self, post: Post) -> Post:
        """Optimize post content."""
        logger.info(f"Optimizing post {post.id}")
        
        # Analyze content
        score = await self.analyze_engagement(post)
        
        # Apply improvements based on score
        if score.score < 0.7:
            post = await self._enhance_content(post, score.recommendations)
        
        # Generate hashtags if needed
        if not post.hashtags or len(post.hashtags) == 0:
            post.hashtags = await self.generate_hashtags(post.content)
        
        # Validate media if present
        if post.media_url:
            is_valid = await self.validate_media(post.media_url, post.media_type)
            if not is_valid:
                logger.warning(f"Media validation failed for post {post.id}")
                post.media_url = None
                post.media_type = None
        
        logger.info(f"Post {post.id} optimized successfully")
        return post
    
    async def analyze_engagement(self, post: Post) -> EngagementScore:
        """Analyze content for engagement potential."""
        content = post.content
        
        # Calculate readability (simplified)
        readability = self._calculate_readability(content)
        
        # Calculate engagement potential
        engagement = self._calculate_engagement_potential(content)
        
        # Overall score
        score = (readability + engagement) / 2
        
        # Generate recommendations
        recommendations = []
        if readability < 0.6:
            recommendations.append("Simplify language for better readability")
        if engagement < 0.6:
            recommendations.append("Add more engaging elements (questions, calls-to-action)")
        if len(content) < 50:
            recommendations.append("Content is too short, consider expanding")
        
        return EngagementScore(
            score=score,
            readability=readability,
            engagement_potential=engagement,
            recommendations=recommendations
        )
    
    async def generate_hashtags(self, content: str, max_count: int = 5) -> list[str]:
        """Generate relevant hashtags from content."""
        logger.info("Generating hashtags")
        
        # Extract keywords (simplified approach)
        words = re.findall(r'\b[a-zA-Zа-яА-Я]{4,}\b', content.lower())
        
        # Remove common words
        stop_words = {'this', 'that', 'with', 'from', 'have', 'been', 'were', 'their',
                     'это', 'для', 'как', 'что', 'или', 'быть', 'был', 'была'}
        keywords = [w for w in words if w not in stop_words]
        
        # Count frequency
        word_freq = {}
        for word in keywords:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Get top keywords
        top_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:max_count]
        
        # Create hashtags
        hashtags = [f"#{word.capitalize()}" for word, _ in top_keywords]
        
        logger.info(f"Generated {len(hashtags)} hashtags")
        return hashtags
    
    async def validate_media(self, media_url: str, media_type: Optional[str]) -> bool:
        """Validate media quality and format."""
        logger.info(f"Validating media: {media_url}")
        
        # Check URL format
        if not media_url.startswith(('http://', 'https://')):
            logger.warning("Invalid media URL format")
            return False
        
        # Check media type
        valid_types = ['image/jpeg', 'image/png', 'image/gif', 'video/mp4']
        if media_type and media_type not in valid_types:
            logger.warning(f"Unsupported media type: {media_type}")
            return False
        
        # In production, would check file size, dimensions, etc.
        return True
    
    def _calculate_readability(self, content: str) -> float:
        """Calculate readability score (simplified)."""
        # Count sentences
        sentences = len(re.findall(r'[.!?]+', content))
        if sentences == 0:
            sentences = 1
        
        # Count words
        words = len(content.split())
        
        # Average words per sentence
        avg_words = words / sentences
        
        # Simple readability score (ideal: 15-20 words per sentence)
        if avg_words < 10:
            return 0.7
        elif avg_words <= 20:
            return 1.0
        elif avg_words <= 30:
            return 0.8
        else:
            return 0.5
    
    def _calculate_engagement_potential(self, content: str) -> float:
        """Calculate engagement potential score."""
        score = 0.5  # Base score
        
        # Check for questions
        if '?' in content:
            score += 0.2
        
        # Check for emojis
        emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F1E0-\U0001F1FF"  # flags
            "]+", flags=re.UNICODE)
        if emoji_pattern.search(content):
            score += 0.1
        
        # Check for call-to-action words
        cta_words = ['узнать', 'подписаться', 'читать', 'смотреть', 'learn', 'discover', 'join', 'read']
        if any(word in content.lower() for word in cta_words):
            score += 0.2
        
        return min(score, 1.0)
    
    async def _enhance_content(self, post: Post, recommendations: list[str]) -> Post:
        """Enhance content based on recommendations."""
        logger.info(f"Enhancing content with {len(recommendations)} recommendations")
        
        # In a real implementation, this would use AI to improve content
        # For now, we just log the recommendations
        for rec in recommendations:
            logger.info(f"Recommendation: {rec}")
        
        return post
