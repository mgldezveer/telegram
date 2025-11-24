"""Quality control and content safety service."""

import logging
import re
from typing import Optional
from dataclasses import dataclass
from src.models import Post

logger = logging.getLogger(__name__)


@dataclass
class QualityCheckResult:
    """Result of quality check."""
    passed: bool
    issues: list[str]
    score: float  # 0.0 to 1.0


class QualityControl:
    """Service for content quality control and safety."""
    
    def __init__(self):
        self.min_quality_score = 0.7
        self.inappropriate_patterns = [
            r'\b(spam|scam|fake|fraud)\b',
            r'\b(buy now|click here|limited time)\b',
            r'(http://|https://)[^\s]+\.(ru|cn)',  # Suspicious domains
        ]
        self.template_versions: dict[str, int] = {}
    
    async def check_quality(self, post: Post) -> QualityCheckResult:
        """Perform comprehensive quality check."""
        logger.info(f"Performing quality check for post {post.id}")
        
        issues = []
        score = 1.0
        
        # Check content length
        if len(post.content) < 20:
            issues.append("Content too short")
            score -= 0.2
        elif len(post.content) > 4000:
            issues.append("Content too long")
            score -= 0.1
        
        # Check for inappropriate content
        if await self._is_inappropriate(post.content):
            issues.append("Inappropriate content detected")
            score -= 0.5
        
        # Check for spam patterns
        if await self._is_spam(post.content):
            issues.append("Spam patterns detected")
            score -= 0.4
        
        # Check brand consistency (simplified)
        if not await self._check_brand_consistency(post):
            issues.append("Brand consistency issues")
            score -= 0.2
        
        # Check grammar and spelling (simplified)
        grammar_score = await self._check_grammar(post.content)
        if grammar_score < 0.8:
            issues.append("Grammar or spelling issues")
            score -= 0.1
        
        passed = score >= self.min_quality_score
        
        result = QualityCheckResult(
            passed=passed,
            issues=issues,
            score=max(0.0, score)
        )
        
        logger.info(f"Quality check result: {'PASSED' if passed else 'FAILED'}, score: {score:.2f}")
        return result
    
    async def reject_and_regenerate(self, post: Post, reason: str) -> bool:
        """Reject inappropriate content and trigger regeneration."""
        logger.warning(f"Rejecting post {post.id}: {reason}")
        
        # Mark post as failed
        post.status = "rejected"
        
        # In production, would trigger regeneration
        # For now, just log
        logger.info(f"Regeneration triggered for post {post.id}")
        return True
    
    async def update_template(self, template_name: str, template_content: str) -> int:
        """Update content template and return new version."""
        current_version = self.template_versions.get(template_name, 0)
        new_version = current_version + 1
        
        self.template_versions[template_name] = new_version
        
        logger.info(f"Template '{template_name}' updated to version {new_version}")
        return new_version
    
    async def notify_admin(self, post_id: int, issues: list[str], admin_ids: list[int]):
        """Notify administrators about quality issues."""
        logger.warning(f"Notifying admins about quality issues in post {post_id}")
        
        for issue in issues:
            logger.warning(f"  - {issue}")
        
        # In production, would send actual notifications
        # For now, just log
    
    async def _is_inappropriate(self, content: str) -> bool:
        """Check for inappropriate content."""
        content_lower = content.lower()
        
        for pattern in self.inappropriate_patterns:
            if re.search(pattern, content_lower, re.IGNORECASE):
                logger.warning(f"Inappropriate pattern found: {pattern}")
                return True
        
        return False
    
    async def _is_spam(self, content: str) -> bool:
        """Check for spam patterns."""
        # Check for excessive capitalization
        if sum(1 for c in content if c.isupper()) / len(content) > 0.5:
            return True
        
        # Check for excessive punctuation
        if content.count('!') > 5 or content.count('?') > 5:
            return True
        
        # Check for repeated characters
        if re.search(r'(.)\1{4,}', content):
            return True
        
        return False
    
    async def _check_brand_consistency(self, post: Post) -> bool:
        """Check brand consistency."""
        # Simplified check - in production would check against brand guidelines
        # For now, just check if style is set
        return post.style_tone is not None
    
    async def _check_grammar(self, content: str) -> float:
        """Check grammar and spelling (simplified)."""
        # Simplified grammar check
        # In production, would use proper grammar checking library
        
        # Check for basic sentence structure
        sentences = re.split(r'[.!?]+', content)
        valid_sentences = sum(1 for s in sentences if len(s.strip()) > 5)
        
        if len(sentences) == 0:
            return 0.0
        
        return valid_sentences / len(sentences)
