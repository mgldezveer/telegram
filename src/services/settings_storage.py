"""Settings storage service."""

import logging
import json
from typing import Any, Dict
from pathlib import Path

logger = logging.getLogger(__name__)


class SettingsStorage:
    """Persistent settings storage using JSON file.
    
    Settings are saved to a JSON file and loaded on startup.
    """
    
    def __init__(self, storage_file: str = "settings.json"):
        """Initialize settings storage.
        
        Args:
            storage_file: Path to settings file
        """
        self.storage_file = Path(storage_file)
        self._default_settings = {
            # Default settings
            'posting_frequency': 3,
            'content_style': 'professional',
            'notify_success': True,
            'notify_errors': True,
            'notify_analytics': False
        }
        
        # Load settings from file or use defaults
        self._settings = self._load_settings()
        logger.info("Settings storage initialized with defaults")
    
    async def get(self, key: str, default: Any = None) -> Any:
        """Get setting value.
        
        Args:
            key: Setting key
            default: Default value if not found
            
        Returns:
            Setting value or default
        """
        value = self._settings.get(key, default)
        logger.debug(f"Get setting {key}={value}")
        return value
    
    async def set(self, key: str, value: Any) -> None:
        """Set setting value.
        
        Args:
            key: Setting key
            value: Setting value
        """
        self._settings[key] = value
        self._save_settings()
        logger.info(f"Set setting {key}={value}")
    
    async def delete(self, key: str) -> None:
        """Delete setting.
        
        Args:
            key: Setting key
        """
        if key in self._settings:
            del self._settings[key]
            self._save_settings()
            logger.info(f"Deleted setting {key}")
    
    async def get_all(self) -> Dict[str, Any]:
        """Get all settings.
        
        Returns:
            Dictionary of all settings
        """
        return self._settings.copy()
    
    async def clear(self) -> None:
        """Clear all settings (reset to defaults)."""
        self._settings = self._default_settings.copy()
        self._save_settings()
        logger.info("Settings cleared and reset to defaults")
    
    def _load_settings(self) -> Dict[str, Any]:
        """Load settings from file.
        
        Returns:
            Settings dictionary
        """
        if self.storage_file.exists():
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                logger.info(f"Loaded settings from {self.storage_file}")
                # Merge with defaults to ensure all keys exist
                merged = self._default_settings.copy()
                merged.update(settings)
                return merged
            except Exception as e:
                logger.error(f"Error loading settings: {e}")
                return self._default_settings.copy()
        else:
            logger.info("No settings file found, using defaults")
            return self._default_settings.copy()
    
    def _save_settings(self) -> None:
        """Save settings to file."""
        try:
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, indent=2, ensure_ascii=False)
            logger.debug(f"Saved settings to {self.storage_file}")
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
