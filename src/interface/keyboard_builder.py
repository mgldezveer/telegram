"""Keyboard builder for creating inline and reply keyboards."""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class ButtonConfig:
    """Configuration for a button."""
    text: str
    callback_data: Optional[str] = None
    url: Optional[str] = None
    emoji: Optional[str] = None


class KeyboardBuilder:
    """Builder for creating Telegram keyboards."""
    
    def build_main_menu(self) -> InlineKeyboardMarkup:
        """Build main menu keyboard.
        
        Returns:
            InlineKeyboardMarkup with main menu buttons
        """
        keyboard = [
            [
                InlineKeyboardButton("📊 Каналы", callback_data="menu:channels"),
                InlineKeyboardButton("✍️ Контент", callback_data="menu:content")
            ],
            [
                InlineKeyboardButton("📈 Аналитика", callback_data="menu:analytics"),
                InlineKeyboardButton("⚙️ Настройки", callback_data="menu:settings")
            ],
            [
                InlineKeyboardButton("⚡ Сгенерировать", callback_data="quick:generate"),
                InlineKeyboardButton("📊 Статус", callback_data="quick:status")
            ],
            [
                InlineKeyboardButton("❓ Помощь", callback_data="help:main")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def build_channel_list(self, channels: list, page: int = 0, per_page: int = 5) -> InlineKeyboardMarkup:
        """Build channel list keyboard with pagination.
        
        Args:
            channels: List of channel objects
            page: Current page number
            per_page: Items per page
            
        Returns:
            InlineKeyboardMarkup with channel list
        """
        keyboard = []
        
        # Calculate pagination
        start = page * per_page
        end = start + per_page
        page_channels = channels[start:end]
        total_pages = (len(channels) + per_page - 1) // per_page
        
        # Add channel buttons
        for channel in page_channels:
            keyboard.append([
                InlineKeyboardButton(
                    f"📺 {channel.name}",
                    callback_data=f"channel:{channel.id}:dashboard"
                )
            ])
        
        # Add pagination if needed
        if total_pages > 1:
            nav_buttons = []
            if page > 0:
                nav_buttons.append(
                    InlineKeyboardButton("◀️ Назад", callback_data=f"channels:page:{page-1}")
                )
            nav_buttons.append(
                InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="noop")
            )
            if page < total_pages - 1:
                nav_buttons.append(
                    InlineKeyboardButton("Вперёд ▶️", callback_data=f"channels:page:{page+1}")
                )
            keyboard.append(nav_buttons)
        
        # Add action buttons
        keyboard.append([
            InlineKeyboardButton("➕ Добавить канал", callback_data="channel:add")
        ])
        keyboard.append([
            InlineKeyboardButton("⬅️ Назад", callback_data="menu:main")
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    def build_channel_dashboard(self, channel) -> InlineKeyboardMarkup:
        """Build channel dashboard keyboard.
        
        Args:
            channel: Channel object
            
        Returns:
            InlineKeyboardMarkup with dashboard actions
        """
        keyboard = [
            [
                InlineKeyboardButton("✍️ Создать пост", callback_data=f"generate:{channel.id}"),
                InlineKeyboardButton("📅 Расписание", callback_data=f"schedule:{channel.id}")
            ],
            [
                InlineKeyboardButton("⚙️ Настроить", callback_data=f"channel:{channel.id}:config"),
                InlineKeyboardButton("📊 Аналитика", callback_data=f"analytics:{channel.id}")
            ],
            [
                InlineKeyboardButton("🗑️ Удалить", callback_data=f"channel:{channel.id}:delete")
            ],
            [
                InlineKeyboardButton("⬅️ К списку", callback_data="menu:channels")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def build_confirmation(self, action: str, data: str, description: str = "") -> InlineKeyboardMarkup:
        """Build confirmation dialog keyboard.
        
        Args:
            action: Action to confirm
            data: Data associated with action
            description: Optional description
            
        Returns:
            InlineKeyboardMarkup with Yes/No buttons
        """
        keyboard = [
            [
                InlineKeyboardButton("✅ Да", callback_data=f"confirm:{action}:{data}"),
                InlineKeyboardButton("❌ Нет", callback_data=f"cancel:{action}:{data}")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def build_content_menu(self) -> InlineKeyboardMarkup:
        """Build content menu keyboard.
        
        Returns:
            InlineKeyboardMarkup with content options
        """
        keyboard = [
            [
                InlineKeyboardButton("✍️ Сгенерировать", callback_data="content:generate")
            ],
            [
                InlineKeyboardButton("📅 Запланировать", callback_data="content:schedule")
            ],
            [
                InlineKeyboardButton("📝 Просмотр постов", callback_data="content:view")
            ],
            [
                InlineKeyboardButton("⬅️ Назад", callback_data="menu:main")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def build_analytics_menu(self, channels: list) -> InlineKeyboardMarkup:
        """Build analytics menu with channel selection.
        
        Args:
            channels: List of channel objects
            
        Returns:
            InlineKeyboardMarkup with channel selection
        """
        keyboard = []
        
        for channel in channels:
            keyboard.append([
                InlineKeyboardButton(
                    f"📊 {channel.name}",
                    callback_data=f"analytics:{channel.id}"
                )
            ])
        
        keyboard.append([
            InlineKeyboardButton("⬅️ Назад", callback_data="menu:main")
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    def build_settings_menu(self) -> InlineKeyboardMarkup:
        """Build settings menu keyboard.
        
        Returns:
            InlineKeyboardMarkup with settings categories
        """
        keyboard = [
            [
                InlineKeyboardButton("📅 Частота публикаций", callback_data="settings:frequency")
            ],
            [
                InlineKeyboardButton("🎨 Стиль контента", callback_data="settings:style")
            ],
            [
                InlineKeyboardButton("🔔 Уведомления", callback_data="settings:notifications")
            ],
            [
                InlineKeyboardButton("🌐 Язык", callback_data="settings:language")
            ],
            [
                InlineKeyboardButton("⬅️ Назад", callback_data="menu:main")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def build_theme_selection(self) -> InlineKeyboardMarkup:
        """Build theme selection keyboard.
        
        Returns:
            InlineKeyboardMarkup with theme options
        """
        keyboard = [
            [
                InlineKeyboardButton("💻 Технологии", callback_data="theme:tech"),
                InlineKeyboardButton("🎨 Дизайн", callback_data="theme:design")
            ],
            [
                InlineKeyboardButton("📱 Мобильные", callback_data="theme:mobile"),
                InlineKeyboardButton("🚀 Стартапы", callback_data="theme:startup")
            ],
            [
                InlineKeyboardButton("✏️ Своя тема...", callback_data="theme:custom")
            ],
            [
                InlineKeyboardButton("❌ Отмена", callback_data="cancel:generation")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def build_post_preview_actions(self, post_id: int) -> InlineKeyboardMarkup:
        """Build post preview action buttons.
        
        Args:
            post_id: ID of the post
            
        Returns:
            InlineKeyboardMarkup with action buttons
        """
        keyboard = [
            [
                InlineKeyboardButton("✅ Опубликовать", callback_data=f"post:{post_id}:publish"),
                InlineKeyboardButton("✏️ Редактировать", callback_data=f"post:{post_id}:edit")
            ],
            [
                InlineKeyboardButton("🔄 Перегенерировать", callback_data=f"post:{post_id}:regenerate"),
                InlineKeyboardButton("❌ Отменить", callback_data=f"post:{post_id}:discard")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def build_pagination(self, page: int, total_pages: int, prefix: str) -> InlineKeyboardMarkup:
        """Build pagination keyboard.
        
        Args:
            page: Current page number
            total_pages: Total number of pages
            prefix: Callback data prefix
            
        Returns:
            InlineKeyboardMarkup with pagination buttons
        """
        keyboard = []
        nav_buttons = []
        
        if page > 0:
            nav_buttons.append(
                InlineKeyboardButton("◀️", callback_data=f"{prefix}:page:{page-1}")
            )
        
        nav_buttons.append(
            InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="noop")
        )
        
        if page < total_pages - 1:
            nav_buttons.append(
                InlineKeyboardButton("▶️", callback_data=f"{prefix}:page:{page+1}")
            )
        
        keyboard.append(nav_buttons)
        return InlineKeyboardMarkup(keyboard)
    
    def build_back_button(self, callback_data: str = "menu:main") -> InlineKeyboardMarkup:
        """Build simple back button.
        
        Args:
            callback_data: Callback data for back button
            
        Returns:
            InlineKeyboardMarkup with back button
        """
        keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data=callback_data)]]
        return InlineKeyboardMarkup(keyboard)
