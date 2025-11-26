"""Factory for creating properly configured ConversationHandlers."""

import logging
import warnings
from typing import List, Dict, Optional
from telegram.ext import ConversationHandler, CallbackQueryHandler
from telegram.warnings import PTBUserWarning

logger = logging.getLogger(__name__)


class ConversationHandlerFactory:
    """Factory for creating properly configured ConversationHandlers.
    
    This factory ensures that ConversationHandlers are created with
    appropriate settings to avoid PTB warnings, particularly regarding
    the per_message parameter when using CallbackQueryHandler.
    """
    
    @staticmethod
    def _has_callback_handlers(states: Dict) -> bool:
        """Check if states contain CallbackQueryHandler.
        
        Args:
            states: Dictionary of state handlers
            
        Returns:
            True if any state contains CallbackQueryHandler
        """
        for state_handlers in states.values():
            if isinstance(state_handlers, list):
                for handler in state_handlers:
                    if isinstance(handler, CallbackQueryHandler):
                        return True
            elif isinstance(state_handlers, CallbackQueryHandler):
                return True
        return False
    
    @staticmethod
    def _check_entry_points(entry_points: List) -> bool:
        """Check if entry points contain CallbackQueryHandler.
        
        Args:
            entry_points: List of entry point handlers
            
        Returns:
            True if any entry point is CallbackQueryHandler
        """
        for handler in entry_points:
            if isinstance(handler, CallbackQueryHandler):
                return True
        return False
    
    @staticmethod
    def create_handler(
        name: str,
        entry_points: List,
        states: Dict,
        fallbacks: List,
        timeout: int = 300,
        per_message: Optional[bool] = None,
        per_chat: bool = True,
        per_user: bool = True,
        allow_reentry: bool = False,
        conversation_timeout: Optional[float] = None
    ) -> ConversationHandler:
        """Create ConversationHandler with proper configuration.
        
        This method automatically detects if CallbackQueryHandler is used
        and sets per_message=True to avoid PTB warnings.
        
        Args:
            name: Handler name for logging and identification
            entry_points: List of entry point handlers
            states: Dictionary mapping states to handlers
            fallbacks: List of fallback handlers
            timeout: Conversation timeout in seconds (deprecated, use conversation_timeout)
            per_message: Track per message (auto-detected if None)
            per_chat: Track per chat
            per_user: Track per user
            allow_reentry: Allow re-entering conversation
            conversation_timeout: Conversation timeout in seconds (float)
            
        Returns:
            Properly configured ConversationHandler
        """
        # Auto-detect if per_message should be True
        has_callbacks = (
            ConversationHandlerFactory._has_callback_handlers(states) or
            ConversationHandlerFactory._check_entry_points(entry_points)
        )
        
        # If per_message not explicitly set, auto-configure
        if per_message is None:
            if has_callbacks:
                per_message = True
                logger.debug(
                    f"ConversationHandler '{name}': Auto-setting per_message=True "
                    f"(CallbackQueryHandler detected)"
                )
            else:
                per_message = False
        else:
            # Only warn if per_message=False with callbacks AND no message handlers in states
            if not per_message and has_callbacks:
                # Check if states have MessageHandler (mixed scenario is OK)
                has_message_handlers = False
                for state_handlers in states.values():
                    if isinstance(state_handlers, list):
                        for handler in state_handlers:
                            if not isinstance(handler, CallbackQueryHandler):
                                has_message_handlers = True
                                break
                
                if not has_message_handlers:
                    logger.warning(
                        f"ConversationHandler '{name}': per_message=False with only "
                        f"CallbackQueryHandler. Consider setting per_message=True."
                    )
                else:
                    logger.debug(
                        f"ConversationHandler '{name}': Mixed handlers detected "
                        f"(CallbackQuery + Message). Using per_message=False is appropriate."
                    )
        
        # Use conversation_timeout if provided, otherwise convert timeout
        if conversation_timeout is None:
            conversation_timeout = float(timeout)
        
        logger.info(
            f"Creating ConversationHandler '{name}' "
            f"(per_message={per_message}, per_chat={per_chat}, per_user={per_user})"
        )
        
        # Suppress PTBUserWarning for mixed handlers (CallbackQuery + Message)
        # This is intentional and correct for our use case
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message=".*per_message.*CallbackQueryHandler.*",
                category=PTBUserWarning
            )
            
            return ConversationHandler(
                entry_points=entry_points,
                states=states,
                fallbacks=fallbacks,
                per_message=per_message,
                per_chat=per_chat,
                per_user=per_user,
                allow_reentry=allow_reentry,
                conversation_timeout=conversation_timeout,
                name=name
            )
    
    @staticmethod
    def validate_handler_config(
        name: str,
        entry_points: List,
        states: Dict,
        fallbacks: List,
        per_message: bool
    ) -> List[str]:
        """Validate ConversationHandler configuration.
        
        Args:
            name: Handler name
            entry_points: Entry point handlers
            states: State handlers
            fallbacks: Fallback handlers
            per_message: per_message setting
            
        Returns:
            List of validation warnings (empty if no issues)
        """
        warnings = []
        
        # Check for empty entry points
        if not entry_points:
            warnings.append(f"Handler '{name}': No entry points defined")
        
        # Check for empty states
        if not states:
            warnings.append(f"Handler '{name}': No states defined")
        
        # Check for empty fallbacks
        if not fallbacks:
            warnings.append(
                f"Handler '{name}': No fallbacks defined. "
                f"Consider adding a cancel command."
            )
        
        # Check per_message with CallbackQueryHandler
        has_callbacks = (
            ConversationHandlerFactory._has_callback_handlers(states) or
            ConversationHandlerFactory._check_entry_points(entry_points)
        )
        
        if has_callbacks and not per_message:
            warnings.append(
                f"Handler '{name}': CallbackQueryHandler detected but per_message=False. "
                f"This will cause PTB warnings."
            )
        
        return warnings
