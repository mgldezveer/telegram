# Subscription Model

## Subscription Tiers

```python
from enum import Enum
from datetime import datetime, timedelta

class SubscriptionTier(Enum):
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"

TIER_FEATURES = {
    SubscriptionTier.FREE: {
        'max_requests': 10,
        'features': ['basic_commands']
    },
    SubscriptionTier.BASIC: {
        'max_requests': 100,
        'features': ['basic_commands', 'analytics']
    },
    SubscriptionTier.PREMIUM: {
        'max_requests': 1000,
        'features': ['basic_commands', 'analytics', 'priority_support']
    }
}
```

## Subscription Model

```python
class Subscription(Base):
    __tablename__ = 'subscriptions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    tier = Column(String(50), default='free')
    start_date = Column(DateTime, default=datetime.utcnow)
    end_date = Column(DateTime)
    is_active = Column(Boolean, default=True)
```

## Check Subscription

```python
async def check_subscription(user_id: int) -> SubscriptionTier:
    """Check user's subscription tier."""
    sub = await db.get_subscription(user_id)
    
    if not sub or not sub.is_active:
        return SubscriptionTier.FREE
    
    if sub.end_date and datetime.utcnow() > sub.end_date:
        sub.is_active = False
        await db.update_subscription(sub)
        return SubscriptionTier.FREE
    
    return SubscriptionTier(sub.tier)
```

## Feature Gate

```python
def requires_subscription(tier: SubscriptionTier):
    def decorator(func):
        @wraps(func)
        async def wrapper(update, context, *args, **kwargs):
            user_tier = await check_subscription(update.effective_user.id)
            
            if user_tier.value < tier.value:
                await update.message.reply_text(
                    f"This feature requires {tier.value} subscription"
                )
                return
            
            return await func(update, context, *args, **kwargs)
        return wrapper
    return decorator

@requires_subscription(SubscriptionTier.PREMIUM)
async def premium_command(update, context):
    await update.message.reply_text("Premium feature!")
```
