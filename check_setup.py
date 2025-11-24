#!/usr/bin/env python3
"""
Проверка установки и конфигурации бота
"""
import sys
import os
from pathlib import Path

def check_python_version():
    """Проверка версии Python"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print("❌ Python 3.11+ required")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True

def check_env_file():
    """Проверка .env файла"""
    if not Path(".env").exists():
        print("❌ .env file not found")
        return False
    print("✅ .env file exists")
    return True

def check_required_env_vars():
    """Проверка обязательных переменных окружения"""
    from dotenv import load_dotenv
    load_dotenv()
    
    required = [
        "TELEGRAM_BOT_TOKEN",
        "GROQ_API_KEY",
        "ADMIN_IDS"
    ]
    
    missing = []
    for var in required:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        print(f"❌ Missing environment variables: {', '.join(missing)}")
        return False
    
    print("✅ All required environment variables set")
    return True

def check_dependencies():
    """Проверка установленных зависимостей"""
    try:
        import telegram
        print(f"✅ python-telegram-bot {telegram.__version__}")
    except ImportError:
        print("❌ python-telegram-bot not installed")
        return False
    
    try:
        import groq
        print("✅ groq installed")
    except ImportError:
        print("❌ groq not installed")
        return False
    
    try:
        import sqlalchemy
        print(f"✅ sqlalchemy {sqlalchemy.__version__}")
    except ImportError:
        print("❌ sqlalchemy not installed")
        return False
    
    return True

def check_database():
    """Проверка базы данных"""
    db_path = Path("bot.db")
    if db_path.exists():
        print(f"✅ Database exists ({db_path.stat().st_size} bytes)")
    else:
        print("⚠️  Database will be created on first run")
    return True

def main():
    print("🔍 Checking AI Content Bot setup...")
    print("-" * 50)
    
    checks = [
        ("Python version", check_python_version),
        (".env file", check_env_file),
        ("Environment variables", check_required_env_vars),
        ("Dependencies", check_dependencies),
        ("Database", check_database),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append(result)
        except Exception as e:
            print(f"❌ {name}: {e}")
            results.append(False)
        print()
    
    print("-" * 50)
    if all(results):
        print("✅ All checks passed! Ready to run the bot.")
        print("\nTo start the bot, run:")
        print("  python run.py")
        return 0
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        print("\nTo install dependencies, run:")
        print("  pip install -r requirements.txt")
        return 1

if __name__ == "__main__":
    sys.exit(main())
