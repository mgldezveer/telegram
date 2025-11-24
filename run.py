#!/usr/bin/env python3
"""
Quick start script for AI Content Bot
Запускает бота в режиме polling (без webhook)
"""
import asyncio
import logging
from src.main import main

if __name__ == "__main__":
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    
    print("🚀 Starting AI Content Bot...")
    print("📝 Press Ctrl+C to stop")
    print("-" * 50)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise
