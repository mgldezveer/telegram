#!/usr/bin/env python3
"""
Test script to verify that all service files are properly updated and can be imported.
"""

import sys
import os
from pathlib import Path

# Add the telegram/src directory to the path so we can import modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_service_imports():
    """Test that all service modules can be imported."""
    print("Testing service module imports...")
    
    # Test individual service imports
    service_modules = [
        "src.services.alerting_service",
        "src.services.analytics_engine",
        "src.services.channel_manager",
        "src.services.content_optimizer",
        "src.services.content_source_manager",
        "src.services.content_source_manager_improved",
        "src.services.enhanced_content_generator",
        "src.services.enhanced_error_handler",
        "src.services.enhanced_publishing_service",
        "src.services.enhanced_scheduler",
        "src.services.health_check",
        "src.services.post_queue_manager",
        "src.services.quality_control",
        "src.services.rate_limiter",
        "src.services.settings_storage",
        "src.services.telegram_rate_limiter",
        "src.services.telegram_stats_parser",
        "src.services.telethon_stats_parser",
        "src.services.autopost.channel_manager",
        "src.services.autopost.content_generator",
        "src.services.autopost.initializer",
        "src.services.autopost.publishing",
        "src.services.autopost.queue_manager",
        "src.services.autopost.scheduler"
    ]
    
    failed_imports = []
    successful_imports = []
    
    for module_name in service_modules:
        try:
            __import__(module_name)
            print(f"[SUCCESS] Successfully imported: {module_name}")
            successful_imports.append(module_name)
        except Exception as e:
            print(f"[FAILED] Failed to import: {module_name} - {str(e)}")
            failed_imports.append((module_name, str(e)))
    
    print(f"\nSummary: {len(successful_imports)} successful, {len(failed_imports)} failed")
    
    if failed_imports:
        print("\nFailed imports:")
        for module, error in failed_imports:
            print(f"  - {module}: {error}")
        return False
    
    return True

def test_utils_imports():
    """Test that all utility modules can be imported."""
    print("\nTesting utility module imports...")
    
    # Test individual utility imports
    util_modules = [
        "src.utils.version_checker"
    ]
    
    failed_imports = []
    successful_imports = []
    
    for module_name in util_modules:
        try:
            __import__(module_name)
            print(f"[SUCCESS] Successfully imported: {module_name}")
            successful_imports.append(module_name)
        except Exception as e:
            print(f"[FAILED] Failed to import: {module_name} - {str(e)}")
            failed_imports.append((module_name, str(e)))
    
    print(f"\nSummary: {len(successful_imports)} successful, {len(failed_imports)} failed")
    
    if failed_imports:
        print("\nFailed imports:")
        for module, error in failed_imports:
            print(f"  - {module}: {error}")
        return False
    
    return True

def test_version_checker():
    """Test the version checker functionality."""
    print("\nTesting version checker functionality...")
    
    try:
        from src.utils.version_checker import PythonVersionChecker
        
        checker = PythonVersionChecker()
        result = checker.check_version()
        
        print(f"Python version check result: {result.message}")
        print(f"Current version: {result.current_version}")
        print(f"Is compatible: {result.is_compatible}")
        print(f"Severity: {result.severity}")
        
        # Test the version checker's ability to provide version info
        version_info = checker.get_version_info()
        print(f"Version info: {version_info['version']}")
        
        return True
    except Exception as e:
        print(f"[FAILED] Failed to test version checker: {str(e)}")
        return False

if __name__ == "__main__":
    print("Testing updated services and utilities...")
    
    # Test service imports
    services_ok = test_service_imports()
    
    # Test utility imports
    utils_ok = test_utils_imports()
    
    # Test version checker functionality
    version_ok = test_version_checker()
    
    if services_ok and utils_ok and version_ok:
        print("\n[SUCCESS] All tests passed! Services and utilities are properly updated and functional.")
        sys.exit(0)
    else:
        print("\n[FAILED] Some tests failed.")
        sys.exit(1)