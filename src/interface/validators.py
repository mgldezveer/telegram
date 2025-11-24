"""Input validation utilities for bot interface."""

import re
from typing import Tuple, Optional
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of validation."""
    is_valid: bool
    error_message: Optional[str] = None
    sanitized_value: Optional[any] = None


class InputValidator:
    """Validator for user input."""
    
    @staticmethod
    def validate_channel_id(channel_id_str: str) -> ValidationResult:
        """Validate Telegram channel ID.
        
        Args:
            channel_id_str: Channel ID as string
            
        Returns:
            ValidationResult with validation status
        """
        # Remove whitespace
        channel_id_str = channel_id_str.strip()
        
        # Check if it's a number
        try:
            channel_id = int(channel_id_str)
        except ValueError:
            return ValidationResult(
                is_valid=False,
                error_message=(
                    "ID канала должен быть числом\n\n"
                    "Пример: <code>-1001234567890</code>"
                )
            )
        
        # Channel IDs should be negative for channels/supergroups
        if channel_id >= 0:
            return ValidationResult(
                is_valid=False,
                error_message=(
                    "ID канала должен быть отрицательным числом\n\n"
                    "Пример: <code>-1001234567890</code>"
                )
            )
        
        # Check reasonable range (Telegram IDs are typically 10-13 digits)
        if channel_id < -10000000000000 or channel_id > -100:
            return ValidationResult(
                is_valid=False,
                error_message=(
                    "ID канала имеет неверный формат\n\n"
                    "Убедитесь, что вы скопировали правильный ID"
                )
            )
        
        return ValidationResult(
            is_valid=True,
            sanitized_value=channel_id
        )
    
    @staticmethod
    def validate_channel_name(name: str) -> ValidationResult:
        """Validate channel name.
        
        Args:
            name: Channel name
            
        Returns:
            ValidationResult with validation status
        """
        # Remove leading/trailing whitespace
        name = name.strip()
        
        # Check length
        if len(name) < 2:
            return ValidationResult(
                is_valid=False,
                error_message="Название должно содержать минимум 2 символа"
            )
        
        if len(name) > 100:
            return ValidationResult(
                is_valid=False,
                error_message="Название должно содержать максимум 100 символов"
            )
        
        # Check for invalid characters (allow most Unicode, but not control characters)
        if any(ord(c) < 32 for c in name):
            return ValidationResult(
                is_valid=False,
                error_message="Название содержит недопустимые символы"
            )
        
        return ValidationResult(
            is_valid=True,
            sanitized_value=name
        )
    
    @staticmethod
    def validate_theme(theme: str) -> ValidationResult:
        """Validate content theme.
        
        Args:
            theme: Theme text
            
        Returns:
            ValidationResult with validation status
        """
        # Remove leading/trailing whitespace
        theme = theme.strip()
        
        # Check length
        if len(theme) < 3:
            return ValidationResult(
                is_valid=False,
                error_message="Тема должна содержать минимум 3 символа"
            )
        
        if len(theme) > 200:
            return ValidationResult(
                is_valid=False,
                error_message="Тема должна содержать максимум 200 символов"
            )
        
        # Check for spam patterns (excessive repetition)
        if re.search(r'(.)\1{10,}', theme):
            return ValidationResult(
                is_valid=False,
                error_message="Тема содержит слишком много повторяющихся символов"
            )
        
        return ValidationResult(
            is_valid=True,
            sanitized_value=theme
        )
    
    @staticmethod
    def validate_posting_frequency(frequency_str: str) -> ValidationResult:
        """Validate posting frequency setting.
        
        Args:
            frequency_str: Frequency as string
            
        Returns:
            ValidationResult with validation status
        """
        # Remove whitespace
        frequency_str = frequency_str.strip()
        
        # Check if it's a number
        try:
            frequency = int(frequency_str)
        except ValueError:
            return ValidationResult(
                is_valid=False,
                error_message="Частота должна быть числом от 1 до 24"
            )
        
        # Check range (1-24 posts per day)
        if frequency < 1 or frequency > 24:
            return ValidationResult(
                is_valid=False,
                error_message=(
                    "Частота должна быть от 1 до 24 постов в день\n\n"
                    "Рекомендуется: 2-5 постов в день"
                )
            )
        
        return ValidationResult(
            is_valid=True,
            sanitized_value=frequency
        )
    
    @staticmethod
    def validate_content_style(style: str) -> ValidationResult:
        """Validate content style setting.
        
        Args:
            style: Style name
            
        Returns:
            ValidationResult with validation status
        """
        # Normalize
        style = style.strip().lower()
        
        # Valid styles
        valid_styles = ['professional', 'casual', 'humorous', 'профессиональный', 'неформальный', 'юмористический']
        
        if style not in valid_styles:
            return ValidationResult(
                is_valid=False,
                error_message=(
                    "Неверный стиль контента\n\n"
                    "Доступные стили:\n"
                    "• Профессиональный\n"
                    "• Неформальный\n"
                    "• Юмористический"
                )
            )
        
        # Map Russian to English
        style_map = {
            'профессиональный': 'professional',
            'неформальный': 'casual',
            'юмористический': 'humorous'
        }
        
        normalized_style = style_map.get(style, style)
        
        return ValidationResult(
            is_valid=True,
            sanitized_value=normalized_style
        )
    
    @staticmethod
    def sanitize_text_input(text: str, max_length: int = 1000) -> str:
        """Sanitize general text input.
        
        Args:
            text: Input text
            max_length: Maximum allowed length
            
        Returns:
            Sanitized text
        """
        # Remove leading/trailing whitespace
        text = text.strip()
        
        # Remove control characters except newlines and tabs
        text = ''.join(c for c in text if ord(c) >= 32 or c in '\n\t')
        
        # Limit length
        if len(text) > max_length:
            text = text[:max_length]
        
        # Normalize whitespace (replace multiple spaces with single space)
        text = re.sub(r' +', ' ', text)
        
        return text
    
    @staticmethod
    def validate_user_id(user_id: any) -> ValidationResult:
        """Validate Telegram user ID.
        
        Args:
            user_id: User ID (int or str)
            
        Returns:
            ValidationResult with validation status
        """
        try:
            if isinstance(user_id, str):
                user_id = int(user_id)
            
            # User IDs should be positive
            if user_id <= 0:
                return ValidationResult(
                    is_valid=False,
                    error_message="ID пользователя должен быть положительным числом"
                )
            
            # Check reasonable range
            if user_id > 10000000000:
                return ValidationResult(
                    is_valid=False,
                    error_message="ID пользователя имеет неверный формат"
                )
            
            return ValidationResult(
                is_valid=True,
                sanitized_value=user_id
            )
        
        except (ValueError, TypeError):
            return ValidationResult(
                is_valid=False,
                error_message="ID пользователя должен быть числом"
            )


class SecurityValidator:
    """Validator for security-related checks."""
    
    @staticmethod
    def check_spam_patterns(text: str) -> bool:
        """Check if text contains spam patterns.
        
        Args:
            text: Text to check
            
        Returns:
            True if spam detected, False otherwise
        """
        # Check for excessive URLs
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        urls = re.findall(url_pattern, text)
        if len(urls) > 3:
            return True
        
        # Check for excessive mentions
        mentions = re.findall(r'@\w+', text)
        if len(mentions) > 5:
            return True
        
        # Check for excessive hashtags
        hashtags = re.findall(r'#\w+', text)
        if len(hashtags) > 10:
            return True
        
        # Check for excessive repetition
        if re.search(r'(.{3,})\1{3,}', text):
            return True
        
        # Check for excessive caps
        if len(text) > 20:
            caps_ratio = sum(1 for c in text if c.isupper()) / len(text)
            if caps_ratio > 0.7:
                return True
        
        return False
    
    @staticmethod
    def sanitize_html(text: str) -> str:
        """Sanitize HTML to prevent injection.
        
        Args:
            text: Text that may contain HTML
            
        Returns:
            Sanitized text
        """
        # Escape HTML special characters
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        text = text.replace('"', '&quot;')
        text = text.replace("'", '&#x27;')
        
        return text
