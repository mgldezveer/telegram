"""Add test analytics data to database."""

import asyncio
from datetime import datetime, timedelta
import random
from src.models import get_session, Post, Metrics, PostStatus


async def add_test_data():
    """Add test posts with metrics for analytics."""
    print("Adding test analytics data...")
    
    async for session in get_session():
        # Get channel ID (assuming channel 1 exists)
        channel_id = 1
        
        # Create 15 posts over the last 30 days
        now = datetime.utcnow()
        posts_created = 0
        
        for i in range(15):
            # Random date in last 30 days
            days_ago = random.randint(0, 30)
            published_at = now - timedelta(days=days_ago, hours=random.randint(0, 23))
            
            # Create post
            post = Post(
                content=f"Тестовый пост #{i+1} для аналитики. Это пример контента для демонстрации статистики.",
                channel_id=channel_id,
                status=PostStatus.PUBLISHED,
                published_at=published_at,
                created_at=published_at - timedelta(hours=1),
                style_tone="professional",
                style_length="medium"
            )
            
            session.add(post)
            await session.flush()  # Get post.id
            
            # Create metrics for the post
            views = random.randint(100, 1000)
            reactions = int(views * random.uniform(0.03, 0.10))  # 3-10% reaction rate
            shares = int(views * random.uniform(0.01, 0.05))     # 1-5% share rate
            comments = int(views * random.uniform(0.005, 0.03))  # 0.5-3% comment rate
            
            total_engagement = reactions + shares + comments
            engagement_rate = total_engagement / views if views > 0 else 0
            
            metrics = Metrics(
                post_id=post.id,
                views=views,
                reactions=reactions,
                shares=shares,
                comments=comments,
                engagement_rate=engagement_rate,
                created_at=published_at,
                updated_at=published_at
            )
            
            session.add(metrics)
            posts_created += 1
            
            print(f"✓ Created post {i+1}: {views} views, {engagement_rate*100:.2f}% engagement")
        
        await session.commit()
        print(f"\n✅ Successfully created {posts_created} posts with metrics!")
        print(f"📊 You can now view real analytics in the bot")
        break  # Exit after first session


if __name__ == "__main__":
    asyncio.run(add_test_data())
