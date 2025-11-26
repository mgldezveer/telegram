"""Sync channel statistics from Telegram using Telethon."""

import asyncio
import os
from dotenv import load_dotenv
from src.services.telethon_stats_parser import TelethonStatsParser
from src.models import get_session, Channel
from sqlalchemy import select

load_dotenv()


async def sync_all_channels():
    """Sync statistics for all active channels."""
    # Get Telethon credentials
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    
    if not api_id or not api_hash:
        print("❌ Error: TELEGRAM_API_ID and TELEGRAM_API_HASH must be set in .env")
        print("\n📝 To get these credentials:")
        print("1. Go to https://my.telegram.org/apps")
        print("2. Log in with your phone number")
        print("3. Create a new application")
        print("4. Copy API ID and API Hash to your .env file")
        return
    
    try:
        api_id = int(api_id)
    except ValueError:
        print("❌ Error: TELEGRAM_API_ID must be a number")
        return
    
    print("🔄 Initializing Telethon client...")
    parser = TelethonStatsParser(api_id, api_hash)
    
    try:
        # Get all active channels from database
        async for session in get_session():
            result = await session.execute(
                select(Channel).where(Channel.active == True)
            )
            channels = result.scalars().all()
            
            if not channels:
                print("❌ No active channels found in database")
                print("💡 Add a channel first using the bot")
                break
            
            print(f"\n📊 Found {len(channels)} active channel(s)\n")
            
            for channel in channels:
                print(f"{'='*60}")
                print(f"📢 Channel: {channel.name}")
                print(f"🆔 Telegram ID: {channel.telegram_id}")
                print(f"{'='*60}\n")
                
                # Try to get channel username
                # Note: telegram_id might be numeric ID, need username for Telethon
                channel_username = str(channel.telegram_id)
                
                if channel_username.startswith('-100'):
                    # It's a channel ID, try to convert
                    print(f"⚠️  Channel ID detected: {channel_username}")
                    print(f"💡 For best results, store channel username (@channel) in database")
                    # Remove -100 prefix for Telethon
                    channel_username = channel_username.replace('-100', '')
                
                try:
                    # Sync posts and metrics
                    print(f"🔄 Syncing posts from Telegram...")
                    synced = await parser.sync_channel_posts_to_db(
                        channel.id,
                        channel_username,
                        period_days=30
                    )
                    
                    if synced > 0:
                        print(f"✅ Synced {synced} posts with real statistics!")
                        
                        # Get and display stats
                        stats = await parser.get_channel_stats(channel_username, period_days=30)
                        
                        if not stats.get('no_data'):
                            print(f"\n📈 Statistics:")
                            print(f"   👥 Members: {stats.get('member_count', 'N/A')}")
                            print(f"   📝 Posts: {stats['total_posts']}")
                            print(f"   👁️  Views: {stats['views']:,}")
                            print(f"   ❤️  Reactions: {stats['reactions']:,}")
                            print(f"   📤 Shares: {stats['shares']:,}")
                            print(f"   📊 Engagement: {stats['engagement_rate']:.2f}%")
                            print(f"   📈 Growth: {stats['growth']:+.1f}%")
                            print(f"   ⏰ Best time: {stats['best_time']}")
                    else:
                        print(f"⚠️  No posts synced")
                    
                except Exception as e:
                    print(f"❌ Error syncing channel: {e}")
                
                print()
            
            break  # Exit after first session
        
        print("\n✅ Sync completed!")
        print("📊 You can now view real statistics in the bot")
        
    finally:
        await parser.stop()


if __name__ == "__main__":
    print("🚀 Telegram Channel Statistics Sync")
    print("=" * 60)
    print()
    asyncio.run(sync_all_channels())
