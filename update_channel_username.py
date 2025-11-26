"""Update channel to use username instead of numeric ID."""

import asyncio
from src.models import get_session, Channel
from sqlalchemy import select


async def update_channel():
    """Update channel telegram_id to username."""
    print("🔄 Updating channel...")
    
    channel_username = input("Enter channel username (e.g., @mychannel or mychannel): ").strip()
    
    if not channel_username:
        print("❌ Username is required")
        return
    
    # Remove @ if present
    if channel_username.startswith('@'):
        channel_username = channel_username[1:]
    
    async for session in get_session():
        # Get first channel
        result = await session.execute(
            select(Channel).where(Channel.active == True)
        )
        channel = result.scalar_one_or_none()
        
        if not channel:
            print("❌ No active channels found")
            break
        
        print(f"\n📢 Current channel: {channel.name}")
        print(f"🆔 Current ID: {channel.telegram_id}")
        print(f"🔄 Updating to: @{channel_username}")
        
        # Update telegram_id to username
        channel.telegram_id = channel_username
        await session.commit()
        
        print(f"✅ Channel updated successfully!")
        print(f"\n💡 Now you can run: python sync_channel_stats.py")
        
        break


if __name__ == "__main__":
    asyncio.run(update_channel())
