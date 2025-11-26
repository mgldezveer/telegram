"""Python version checker for ensuring compatibility."""

import sys
import logging
from dataclasses import dataclass
from typing import Tuple

logger = logging.getLogger(__name__)


@dataclass
class VersionCheckResult:
    """Result of Python version check.
    
    Attributes:
        is_compatible: Whether Python version meets minimum requirements
        current_version: Current Python version tuple (major, minor, micro)
        message: Human-readable message about version status
        severity: Severity level ('ok', 'warning', 'error')
    """
    is_compatible: bool
    current_version: Tuple[int, int, int]
    message: str
    severity: str  # 'ok', 'warning', 'error'


class PythonVersionChecker:
    """Check and validate Python version compatibility."""
    
    MINIMUM_VERSION = (3, 10)
    RECOMMENDED_VERSION = (3, 11)
    MAXIMUM_TESTED_VERSION = (3, 12)
    
    @classmethod
    def check_version(cls) -> VersionCheckResult:
        """Check current Python version against requirements.
        
        Returns:
            VersionCheckResult with compatibility status and message
        """
        current = sys.version_info[:3]
        return cls.check_version_tuple(current)
    
    @classmethod
    def check_version_tuple(cls, version: Tuple[int, ...]) -> VersionCheckResult:
        """Check specific version tuple against requirements.
        
        Args:
            version: Python version tuple (major, minor, micro)
            
        Returns:
            VersionCheckResult with compatibility status and message
        """
        # Ensure we have at least (major, minor, micro)
        if len(version) < 3:
            version = tuple(list(version) + [0] * (3 - len(version)))
        
        version = version[:3]  # Only use major, minor, micro
        major, minor, micro = version
        
        # Check if version is below minimum
        if (major, minor) < cls.MINIMUM_VERSION:
            return VersionCheckResult(
                is_compatible=False,
                current_version=version,
                message=(
                    f"❌ Python {major}.{minor}.{micro} is not supported. "
                    f"Minimum required version is Python {cls.MINIMUM_VERSION[0]}.{cls.MINIMUM_VERSION[1]}. "
                    f"Please upgrade to Python {cls.RECOMMENDED_VERSION[0]}.{cls.RECOMMENDED_VERSION[1]} or higher."
                ),
                severity='error'
            )
        
        # Check if version is at minimum but below recommended
        if (major, minor) == cls.MINIMUM_VERSION:
            return VersionCheckResult(
                is_compatible=True,
                current_version=version,
                message=(
                    f"⚠️  Python {major}.{minor}.{micro} meets minimum requirements. "
                    f"However, Python {cls.RECOMMENDED_VERSION[0]}.{cls.RECOMMENDED_VERSION[1]} or higher is recommended "
                    f"for better performance and features."
                ),
                severity='warning'
            )
        
        # Check if version is above maximum tested
        if (major, minor) > cls.MAXIMUM_TESTED_VERSION:
            return VersionCheckResult(
                is_compatible=True,
                current_version=version,
                message=(
                    f"⚠️  Python {major}.{minor}.{micro} is newer than the maximum tested version "
                    f"(Python {cls.MAXIMUM_TESTED_VERSION[0]}.{cls.MAXIMUM_TESTED_VERSION[1]}). "
                    f"The bot should work but has not been fully tested with this version."
                ),
                severity='warning'
            )
        
        # Version is in the recommended range
        return VersionCheckResult(
            is_compatible=True,
            current_version=version,
            message=f"✅ Python {major}.{minor}.{micro} is fully supported.",
            severity='ok'
        )
    
    @classmethod
    def get_version_info(cls) -> dict:
        """Get detailed Python version information.
        
        Returns:
            Dictionary with version details
        """
        version_info = sys.version_info
        
        return {
            'version': f"{version_info.major}.{version_info.minor}.{version_info.micro}",
            'version_tuple': (version_info.major, version_info.minor, version_info.micro),
            'full_version': sys.version,
            'implementation': sys.implementation.name,
            'minimum_required': f"{cls.MINIMUM_VERSION[0]}.{cls.MINIMUM_VERSION[1]}",
            'recommended': f"{cls.RECOMMENDED_VERSION[0]}.{cls.RECOMMENDED_VERSION[1]}",
            'maximum_tested': f"{cls.MAXIMUM_TESTED_VERSION[0]}.{cls.MAXIMUM_TESTED_VERSION[1]}"
        }
    
    @classmethod
    def log_version_check(cls) -> VersionCheckResult:
        """Check version and log appropriate message.
        
        Returns:
            VersionCheckResult
        """
        result = cls.check_version()
        
        if result.severity == 'error':
            logger.error(result.message)
        elif result.severity == 'warning':
            logger.warning(result.message)
        else:
            logger.info(result.message)
        
        return result
    
    @classmethod
    def ensure_compatible_version(cls) -> None:
        """Check version and exit if incompatible.
        
        Raises:
            SystemExit: If Python version is below minimum requirement
        """
        result = cls.check_version()
        
        if not result.is_compatible:
            logger.error(result.message)
            logger.error("Exiting due to incompatible Python version")
            sys.exit(1)
        elif result.severity == 'warning':
            logger.warning(result.message)
        else:
            logger.info(result.message)
