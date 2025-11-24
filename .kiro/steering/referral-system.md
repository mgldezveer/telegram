# Referral System

## Referral Model

```python
class Referral(Base):
    __tablename__ = 'referrals'
    
    id = Column(Integer, primary_key=True)
    referrer_id = Column(Integer, nullable=False)
    referred_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    reward_claimed = Column(Boolean, default=False)
```

## Generate Referral Link

```python
def generate_referral_link(bot_username: str, user_id: int) -> str:
    """Generate referral link for user."""
    return f"https://t.me/{bot_username}?start=ref_{user_id}"
```

## Handle Referral

```python
async def handle_referral(referred_id: int, referrer_id: str):
    """Process referral."""
    try:
        referrer_id = int(referrer_id)
        
        # Check if already referred
        existing = await db.get_referral(referred_id)
        if existing:
            return
        
        # Create referral
        referral = Referral(
            referrer_id=referrer_id,
            referred_id=referred_id
        )
        await db.add_referral(referral)
        
        # Notify referrer
        await bot.send_message(
            chat_id=referrer_id,
            text="🎉 Someone used your referral link!"
        )
        
    except ValueError:
        pass
```

## Referral Stats

```python
async def get_referral_stats(user_id: int) -> dict:
    """Get user's referral statistics."""
    referrals = await db.get_user_referrals(user_id)
    
    return {
        'total_referrals': len(referrals),
        'active_referrals': len([r for r in referrals if r.is_active]),
        'rewards_earned': len([r for r in referrals if r.reward_claimed])
    }
```

## Referral Command

```python
async def referral_command(update, context):
    """Show referral information."""
    user_id = update.effective_user.id
    
    link = generate_referral_link(context.bot.username, user_id)
    stats = await get_referral_stats(user_id)
    
    message = f"""
🔗 Your Referral Link:
{link}

📊 Statistics:
Total referrals: {stats['total_referrals']}
Active: {stats['active_referrals']}
Rewards earned: {stats['rewards_earned']}
    """
    
    await update.message.reply_text(message)
```
