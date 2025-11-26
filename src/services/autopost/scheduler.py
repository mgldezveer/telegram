"""Scheduler Service for auto-posting system."""

import logging
import uuid
import asyncio
from typing import Optional, List, Callable
from datetime import datetime, timedelta, time
from random import randint
from sqlalchemy import select

from src.models.autopost import AutoPostSchedule, ScheduleMode
from src.database.autopost_db import autopost_db

logger = logging.getLogger(__name__)


class ScheduleConfig:
    """Schedule configuration."""
    
    def __init__(
        self,
        channel_id: int,
        mode: ScheduleMode = ScheduleMode.FIXED,
        time_slots: Optional[List[str]] = None,
        days_of_week: Optional[List[int]] = None,
        random_range: Optional[tuple] = None
    ):
        self.channel_id = channel_id
        self.mode = mode
        self.time_slots = time_slots or []
        self.days_of_week = days_of_week or list(range(7))  # All days
        self.random_range = random_range  # (min_minutes, max_minutes)
    
    def to_dict(self):
        return {
            "mode": self.mode.value,
            "time_slots": self.time_slots,
            "days_of_week": self.days_of_week,
            "random_range": self.random_range
        }


class AutoPostScheduler:
    """Scheduler for auto-posting."""
    
    def __init__(self):
        """Initialize scheduler."""
        self.running = False
        self.task = None
        self.callbacks = {}  # schedule_id -> callback
    
    async def add_schedule(
        self,
        channel_id: int,
        schedule: ScheduleConfig
    ) -> str:
        """Add new schedule.
        
        Args:
            channel_id: Channel ID
            schedule: Schedule configuration
            
        Returns:
            Schedule ID
        """
        logger.info(f"Adding schedule for channel {channel_id}")
        
        schedule_id = str(uuid.uuid4())
        
        async with autopost_db.session() as session:
            # Calculate next run time
            next_run = self._calculate_next_run(schedule)
            
            # Create schedule
            db_schedule = AutoPostSchedule(
                id=schedule_id,
                channel_id=channel_id,
                is_active=True,
                config=schedule.to_dict(),
                next_run=next_run
            )
            
            session.add(db_schedule)
            await session.commit()
        
        logger.info(f"✅ Added schedule {schedule_id}, next run: {next_run}")
        return schedule_id
    
    async def remove_schedule(self, schedule_id: str) -> bool:
        """Remove schedule.
        
        Args:
            schedule_id: Schedule ID
            
        Returns:
            True if removed
        """
        logger.info(f"Removing schedule {schedule_id}")
        
        async with autopost_db.session() as session:
            result = await session.execute(
                select(AutoPostSchedule).where(AutoPostSchedule.id == schedule_id)
            )
            schedule = result.scalar_one_or_none()
            
            if not schedule:
                return False
            
            schedule.is_active = False
            await session.commit()
        
        # Remove callback
        if schedule_id in self.callbacks:
            del self.callbacks[schedule_id]
        
        logger.info(f"✅ Removed schedule {schedule_id}")
        return True
    
    async def get_next_run_time(self, schedule_id: str) -> Optional[datetime]:
        """Get next run time for schedule.
        
        Args:
            schedule_id: Schedule ID
            
        Returns:
            Next run datetime or None
        """
        async with autopost_db.session() as session:
            result = await session.execute(
                select(AutoPostSchedule).where(AutoPostSchedule.id == schedule_id)
            )
            schedule = result.scalar_one_or_none()
            
            if schedule:
                return schedule.next_run
            return None
    
    def register_callback(self, schedule_id: str, callback: Callable):
        """Register callback for schedule trigger.
        
        Args:
            schedule_id: Schedule ID
            callback: Async callback function
        """
        self.callbacks[schedule_id] = callback
    
    async def trigger_post_creation(self, channel_id: int):
        """Trigger post creation for channel.
        
        Args:
            channel_id: Channel ID
        """
        logger.info(f"Triggering post creation for channel {channel_id}")
        
        # Find callback for this channel's schedules
        async with autopost_db.session() as session:
            result = await session.execute(
                select(AutoPostSchedule).where(
                    AutoPostSchedule.channel_id == channel_id,
                    AutoPostSchedule.is_active == True
                )
            )
            schedules = result.scalars().all()
            
            for schedule in schedules:
                if schedule.id in self.callbacks:
                    try:
                        await self.callbacks[schedule.id](channel_id)
                    except Exception as e:
                        logger.error(f"Callback failed for schedule {schedule.id}: {e}")
    
    def _calculate_next_run(self, schedule: ScheduleConfig) -> datetime:
        """Calculate next run time.
        
        Args:
            schedule: Schedule configuration
            
        Returns:
            Next run datetime
        """
        now = datetime.now()
        
        if schedule.mode == ScheduleMode.FIXED:
            return self._calculate_fixed_next_run(now, schedule)
        elif schedule.mode == ScheduleMode.RANDOM:
            return self._calculate_random_next_run(now, schedule)
        elif schedule.mode == ScheduleMode.INTERVAL:
            return self._calculate_interval_next_run(now, schedule)
        
        return now + timedelta(hours=1)  # Default
    
    def _calculate_fixed_next_run(self, now: datetime, schedule: ScheduleConfig) -> datetime:
        """Calculate next run for fixed schedule."""
        if not schedule.time_slots:
            return now + timedelta(hours=1)
        
        # Parse time slots
        times = []
        for slot in schedule.time_slots:
            try:
                hour, minute = map(int, slot.split(':'))
                times.append(time(hour, minute))
            except:
                continue
        
        if not times:
            return now + timedelta(hours=1)
        
        # Find next valid time
        for days_ahead in range(8):  # Check next 7 days
            check_date = now.date() + timedelta(days=days_ahead)
            
            # Check if day is allowed
            if check_date.weekday() not in schedule.days_of_week:
                continue
            
            for t in sorted(times):
                next_time = datetime.combine(check_date, t)
                if next_time > now:
                    return next_time
        
        return now + timedelta(days=1)
    
    def _calculate_random_next_run(self, now: datetime, schedule: ScheduleConfig) -> datetime:
        """Calculate next run for random schedule."""
        if not schedule.random_range:
            return now + timedelta(hours=1)
        
        min_minutes, max_minutes = schedule.random_range
        random_minutes = randint(min_minutes, max_minutes)
        
        next_time = now + timedelta(minutes=random_minutes)
        
        # Check if day is allowed
        while next_time.weekday() not in schedule.days_of_week:
            next_time += timedelta(days=1)
        
        return next_time
    
    def _calculate_interval_next_run(self, now: datetime, schedule: ScheduleConfig) -> datetime:
        """Calculate next run for interval schedule."""
        # Use first time slot as interval in hours
        if schedule.time_slots:
            try:
                interval_hours = int(schedule.time_slots[0])
                return now + timedelta(hours=interval_hours)
            except:
                pass
        
        return now + timedelta(hours=1)
    
    async def start(self):
        """Start scheduler loop."""
        if self.running:
            return
        
        self.running = True
        self.task = asyncio.create_task(self._scheduler_loop())
        logger.info("✅ Scheduler started")
    
    async def stop(self):
        """Stop scheduler loop."""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("Scheduler stopped")
    
    async def _scheduler_loop(self):
        """Main scheduler loop."""
        while self.running:
            try:
                await self._check_schedules()
                await asyncio.sleep(60)  # Check every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
                await asyncio.sleep(60)
    
    async def _check_schedules(self):
        """Check and trigger due schedules."""
        now = datetime.now()
        
        async with autopost_db.session() as session:
            result = await session.execute(
                select(AutoPostSchedule).where(
                    AutoPostSchedule.is_active == True,
                    AutoPostSchedule.next_run <= now
                )
            )
            due_schedules = result.scalars().all()
            
            for schedule in due_schedules:
                try:
                    # Trigger post creation
                    await self.trigger_post_creation(schedule.channel_id)
                    
                    # Update schedule
                    config = ScheduleConfig(
                        channel_id=schedule.channel_id,
                        mode=ScheduleMode(schedule.config['mode']),
                        time_slots=schedule.config.get('time_slots'),
                        days_of_week=schedule.config.get('days_of_week'),
                        random_range=schedule.config.get('random_range')
                    )
                    
                    schedule.last_run = now
                    schedule.next_run = self._calculate_next_run(config)
                    
                    await session.commit()
                    
                    logger.info(f"✅ Triggered schedule {schedule.id}, next run: {schedule.next_run}")
                    
                except Exception as e:
                    logger.error(f"Failed to process schedule {schedule.id}: {e}")
