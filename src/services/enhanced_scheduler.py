"""Улучшенный планировщик задач с оптимизациями производительности."""

import logging
import uuid
import asyncio
from typing import Optional, List, Callable, Dict, Tuple
from datetime import datetime, timedelta, time
from random import randint
from sqlalchemy import select
from dataclasses import dataclass

from src.models.autopost import AutoPostSchedule, ScheduleMode
from src.models.metrics import Metrics
from src.database.autopost_db import autopost_db
from src.cache import cache
from src.repositories.metrics_repository import MetricsRepository

logger = logging.getLogger(__name__)


@dataclass
class ScheduleConfig:
    """Конфигурация расписания."""
    
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
        self.days_of_week = days_of_week or list(range(7))  # Все дни
        self.random_range = random_range  # (min_minutes, max_minutes)
    
    def to_dict(self):
        return {
            "mode": self.mode.value,
            "time_slots": self.time_slots,
            "days_of_week": self.days_of_week,
            "random_range": self.random_range
        }


class EnhancedScheduler:
    """Улучшенный планировщик для автопостинга с оптимизациями производительности."""
    
    def __init__(self, check_interval: int = 60, cache_ttl: int = 300):
        """Инициализировать планировщик.
        
        Args:
            check_interval: Интервал проверки расписания в секундах
            cache_ttl: Время жизни кэша в секундах
        """
        self.running = False
        self.task = None
        self.callbacks: Dict[str, Callable] = {}  # schedule_id -> callback
        self.check_interval = check_interval
        self.cache_ttl = cache_ttl
        self._last_check_time = datetime.min
        self._active_schedules_cache = None
        self._cache_last_update = datetime.min


class AnalyticsBasedScheduler(EnhancedScheduler):
    """Планировщик на основе аналитики с возможностью адаптивного изменения расписания."""
    
    def __init__(self, check_interval: int = 60, cache_ttl: int = 300):
        """Инициализировать планировщик на основе аналитики.
        
        Args:
            check_interval: Интервал проверки расписания в секундах
            cache_ttl: Время жизни кэша в секундах
        """
        super().__init__(check_interval, cache_ttl)
        self.ab_testing_enabled = True
        self.current_experiment_id = None
        self.experiment_data = {}
        
    async def collect_engagement_metrics(self, channel_id: int) -> Dict:
        """Собрать и проанализировать метрики вовлеченности для канала.
        
        Args:
            channel_id: ID канала
            
        Returns:
            Словарь с метриками вовлеченности
        """
        async with autopost_db.session() as session:
            metrics_repo = MetricsRepository(session)
            channel_metrics = await metrics_repo.get_by_channel(channel_id)
            
            if not channel_metrics:
                return {
                    'total_posts': 0,
                    'avg_views': 0,
                    'avg_reactions': 0,
                    'avg_shares': 0,
                    'avg_comments': 0,
                    'avg_engagement_rate': 0.0,
                    'peak_engagement_time': None,
                    'engagement_by_hour': {},
                    'engagement_by_day': {}
                }
            
            total_posts = len(channel_metrics)
            avg_views = sum(m.views for m in channel_metrics) / total_posts
            avg_reactions = sum(m.reactions for m in channel_metrics) / total_posts
            avg_shares = sum(m.shares for m in channel_metrics) / total_posts
            avg_comments = sum(m.comments for m in channel_metrics) / total_posts
            avg_engagement_rate = sum(m.engagement_rate for m in channel_metrics) / total_posts
            
            # Сбор метрик по времени публикации
            engagement_by_hour = {}
            engagement_by_day = {}
            
            for metric in channel_metrics:
                post = metric.post
                if post and post.scheduled_at:
                    hour = post.scheduled_at.hour
                    day = post.scheduled_at.weekday()
                    
                    if hour not in engagement_by_hour:
                        engagement_by_hour[hour] = {'views': 0, 'engagement': 0, 'count': 0}
                    engagement_by_hour[hour]['views'] += metric.views
                    engagement_by_hour[hour]['engagement'] += metric.engagement_rate
                    engagement_by_hour[hour]['count'] += 1
                    
                    if day not in engagement_by_day:
                        engagement_by_day[day] = {'views': 0, 'engagement': 0, 'count': 0}
                    engagement_by_day[day]['views'] += metric.views
                    engagement_by_day[day]['engagement'] += metric.engagement_rate
                    engagement_by_day[day]['count'] += 1
            
            # Найти пиковое время вовлеченности
            peak_hour = None
            max_engagement = 0
            for hour, data in engagement_by_hour.items():
                avg_engagement = data['engagement'] / data['count'] if data['count'] > 0 else 0
                if avg_engagement > max_engagement:
                    max_engagement = avg_engagement
                    peak_hour = hour
            
            return {
                'total_posts': total_posts,
                'avg_views': avg_views,
                'avg_reactions': avg_reactions,
                'avg_shares': avg_shares,
                'avg_comments': avg_comments,
                'avg_engagement_rate': avg_engagement_rate,
                'peak_engagement_time': peak_hour,
                'engagement_by_hour': engagement_by_hour,
                'engagement_by_day': engagement_by_day
            }
    
    async def determine_optimal_posting_time(self, channel_id: int) -> Tuple[time, int]:
        """Определить оптимальное время для публикаций на основе метрик.
        
        Args:
            channel_id: ID канала
            
        Returns:
            Кортеж (оптимальное время, день недели)
        """
        metrics = await self.collect_engagement_metrics(channel_id)
        
        # Найти час с максимальной средней вовлеченностью
        optimal_hour = metrics['peak_engagement_time']
        if optimal_hour is None:
            # Если нет данных, использовать стандартное время
            optimal_hour = 12  # 12:00
        
        # Найти день с максимальной вовлеченностью
        optimal_day = 0  # по умолчанию - понедельник
        max_engagement = 0
        for day, data in metrics['engagement_by_day'].items():
            avg_engagement = data['engagement'] / data['count'] if data['count'] > 0 else 0
            if avg_engagement > max_engagement:
                max_engagement = avg_engagement
                optimal_day = day
        
        return time(optimal_hour, 0), optimal_day
    
    async def setup_ab_testing(self, channel_id: int, test_configs: List[ScheduleConfig]) -> str:
        """Настроить A/B тестирование различных стратегий публикации.
        
        Args:
            channel_id: ID канала
            test_configs: Список конфигураций для тестирования
            
        Returns:
            ID эксперимента
        """
        experiment_id = str(uuid.uuid4())
        
        # Сохранить конфигурации эксперимента
        self.experiment_data[experiment_id] = {
            'channel_id': channel_id,
            'configs': test_configs,
            'start_time': datetime.now(),
            'results': {}
        }
        
        self.current_experiment_id = experiment_id
        
        # Создать расписания для каждой конфигурации
        for i, config in enumerate(test_configs):
            config.channel_id = channel_id
            schedule_id = await self.add_schedule(channel_id, config)
            self.experiment_data[experiment_id]['results'][schedule_id] = {
                'config_index': i,
                'performance_metrics': []
            }
        
        return experiment_id
    
    async def update_schedule_based_on_metrics(self, channel_id: int) -> bool:
        """Адаптивно изменить расписание на основе метрик.
        
        Args:
            channel_id: ID канала
            
        Returns:
            True если расписание было обновлено
        """
        # Получить оптимальное время для публикации
        optimal_time, optimal_day = await self.determine_optimal_posting_time(channel_id)
        
        # Найти текущие расписания для канала
        async with autopost_db.session() as session:
            result = await session.execute(
                select(AutoPostSchedule).where(
                    AutoPostSchedule.channel_id == channel_id,
                    AutoPostSchedule.is_active == True
                )
            )
            schedules = result.scalars().all()
        
        if not schedules:
            return False
        
        # Обновить расписания с новым оптимальным временем
        for schedule in schedules:
            config = ScheduleConfig(
                channel_id=channel_id,
                mode=ScheduleMode.FIXED,
                time_slots=[f"{optimal_time.hour:02d}:{optimal_time.minute:02d}"],
                days_of_week=[optimal_day]
            )
            
            schedule.config = config.to_dict()
            schedule.next_run = self._calculate_next_run(config)
            
            session.add(schedule)
        
        await session.commit()
        return True
    
    async def predict_post_effectiveness(self, channel_id: int, scheduled_time: datetime) -> Dict:
        """Прогнозировать эффективность публикации.
        
        Args:
            channel_id: ID канала
            scheduled_time: Время запланированной публикации
            
        Returns:
            Словарь с прогнозируемыми метриками
        """
        # Собрать исторические метрики
        historical_metrics = await self.collect_engagement_metrics(channel_id)
        
        # Вычислить прогноз на основе исторических данных
        base_engagement = historical_metrics['avg_engagement_rate']
        
        # Получить влияние времени публикации
        hour_factor = 1.0
        if scheduled_time.hour in historical_metrics['engagement_by_hour']:
            hour_data = historical_metrics['engagement_by_hour'][scheduled_time.hour]
            avg_hour_engagement = hour_data['engagement'] / hour_data['count'] if hour_data['count'] > 0 else base_engagement
            hour_factor = avg_hour_engagement / base_engagement if base_engagement > 0 else 1.0
        
        day_factor = 1.0
        day_of_week = scheduled_time.weekday()
        if day_of_week in historical_metrics['engagement_by_day']:
            day_data = historical_metrics['engagement_by_day'][day_of_week]
            avg_day_engagement = day_data['engagement'] / day_data['count'] if day_data['count'] > 0 else base_engagement
            day_factor = avg_day_engagement / base_engagement if base_engagement > 0 else 1.0
        
        # Прогнозировать метрики
        predicted_engagement = base_engagement * hour_factor * day_factor
        predicted_views = historical_metrics['avg_views'] * hour_factor * day_factor
        predicted_reactions = historical_metrics['avg_reactions'] * hour_factor * day_factor
        predicted_shares = historical_metrics['avg_shares'] * hour_factor * day_factor
        predicted_comments = historical_metrics['avg_comments'] * hour_factor * day_factor
        
        return {
            'predicted_engagement_rate': predicted_engagement,
            'predicted_views': predicted_views,
            'predicted_reactions': predicted_reactions,
            'predicted_shares': predicted_shares,
            'predicted_comments': predicted_comments,
            'confidence_level': 0.7  # Уровень достоверности прогноза
        }
    
    async def add_schedule(
        self,
        channel_id: int,
        schedule: ScheduleConfig
    ) -> str:
        """Добавить новое расписание.
        
        Args:
            channel_id: ID канала
            schedule: Конфигурация расписания
            
        Returns:
            ID расписания
        """
        logger.info(f"Adding schedule for channel {channel_id}")
        
        schedule_id = str(uuid.uuid4())
        
        async with autopost_db.session() as session:
            # Рассчитать время следующего запуска
            next_run = self._calculate_next_run(schedule)
            
            # Создать расписание
            db_schedule = AutoPostSchedule(
                id=schedule_id,
                channel_id=channel_id,
                is_active=True,
                config=schedule.to_dict(),
                next_run=next_run
            )
            
            session.add(db_schedule)
            await session.commit()
        
        # Инвалидировать кэш активных расписаний
        await self._invalidate_schedules_cache()
        
        logger.info(f"✅ Added schedule {schedule_id}, next run: {next_run}")
        return schedule_id
    
    async def remove_schedule(self, schedule_id: str) -> bool:
        """Удалить расписание.
        
        Args:
            schedule_id: ID расписания
            
        Returns:
            True если удалено
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
        
        # Удалить коллбэк
        if schedule_id in self.callbacks:
            del self.callbacks[schedule_id]
        
        # Инвалидировать кэш активных расписаний
        await self._invalidate_schedules_cache()
        
        logger.info(f"✅ Removed schedule {schedule_id}")
        return True
    
    async def get_next_run_time(self, schedule_id: str) -> Optional[datetime]:
        """Получить время следующего запуска для расписания.
        
        Args:
            schedule_id: ID расписания
            
        Returns:
            Время следующего запуска или None
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
        """Зарегистрировать коллбэк для триггера расписания.
        
        Args:
            schedule_id: ID расписания
            callback: Асинхронная функция коллбэка
        """
        self.callbacks[schedule_id] = callback
    
    async def trigger_post_creation(self, channel_id: int):
        """Триггер создания поста для канала.
        
        Args:
            channel_id: ID канала
        """
        logger.info(f"Triggering post creation for channel {channel_id}")
        
        # Найти коллбэки для расписаний этого канала
        schedules = await self._get_active_schedules_for_channel(channel_id)
        
        for schedule in schedules:
            if schedule.id in self.callbacks:
                try:
                    await self.callbacks[schedule.id](channel_id)
                except Exception as e:
                    logger.error(f"Callback failed for schedule {schedule.id}: {e}")
    
    def _calculate_next_run(self, schedule: ScheduleConfig) -> datetime:
        """Рассчитать время следующего запуска.
        
        Args:
            schedule: Конфигурация расписания
            
        Returns:
            Время следующего запуска
        """
        now = datetime.now()
        
        if schedule.mode == ScheduleMode.FIXED:
            return self._calculate_fixed_next_run(now, schedule)
        elif schedule.mode == ScheduleMode.RANDOM:
            return self._calculate_random_next_run(now, schedule)
        elif schedule.mode == ScheduleMode.INTERVAL:
            return self._calculate_interval_next_run(now, schedule)
        
        return now + timedelta(hours=1)  # По умолчанию
    
    def _calculate_fixed_next_run(self, now: datetime, schedule: ScheduleConfig) -> datetime:
        """Рассчитать следующий запуск для фиксированного расписания."""
        if not schedule.time_slots:
            return now + timedelta(hours=1)
        
        # Парсить временные слоты
        times = []
        for slot in schedule.time_slots:
            try:
                hour, minute = map(int, slot.split(':'))
                times.append(time(hour, minute))
            except:
                continue
        
        if not times:
            return now + timedelta(hours=1)
        
        # Найти следующее подходящее время
        for days_ahead in range(8):  # Проверить следующие 7 дней
            check_date = now.date() + timedelta(days=days_ahead)
            
            # Проверить, разрешен ли день
            if check_date.weekday() not in schedule.days_of_week:
                continue
            
            for t in sorted(times):
                next_time = datetime.combine(check_date, t)
                if next_time > now:
                    return next_time
        
        return now + timedelta(days=1)
    
    def _calculate_random_next_run(self, now: datetime, schedule: ScheduleConfig) -> datetime:
        """Рассчитать следующий запуск для случайного расписания."""
        if not schedule.random_range:
            return now + timedelta(hours=1)
        
        min_minutes, max_minutes = schedule.random_range
        random_minutes = randint(min_minutes, max_minutes)
        
        next_time = now + timedelta(minutes=random_minutes)
        
        # Проверить, разрешен ли день
        while next_time.weekday() not in schedule.days_of_week:
            next_time += timedelta(days=1)
        
        return next_time
    
    def _calculate_interval_next_run(self, now: datetime, schedule: ScheduleConfig) -> datetime:
        """Рассчитать следующий запуск для интервального расписания."""
        # Использовать первый временной слот как интервал в часах
        if schedule.time_slots:
            try:
                interval_hours = int(schedule.time_slots[0])
                return now + timedelta(hours=interval_hours)
            except:
                pass
        
        return now + timedelta(hours=1)
    
    async def start(self):
        """Запустить цикл планировщика."""
        if self.running:
            return
        
        self.running = True
        self.task = asyncio.create_task(self._scheduler_loop())
        logger.info("✅ Enhanced scheduler started")
    
    async def stop(self):
        """Остановить цикл планировщика."""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("Enhanced scheduler stopped")
    
    async def _scheduler_loop(self):
        """Основной цикл планировщика."""
        while self.running:
            try:
                await self._check_schedules()
                await asyncio.sleep(self.check_interval)  # Проверять с настраиваемым интервалом
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Enhanced scheduler loop error: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def _check_schedules(self):
        """Проверить и запустить просроченные расписания."""
        now = datetime.now()
        
        # Получить активные расписания с кэшированием
        due_schedules = await self._get_due_schedules(now)
        
        for schedule in due_schedules:
            try:
                # Запустить создание поста
                await self.trigger_post_creation(schedule.channel_id)
                
                # Обновить расписание
                config = ScheduleConfig(
                    channel_id=schedule.channel_id,
                    mode=ScheduleMode(schedule.config['mode']),
                    time_slots=schedule.config.get('time_slots'),
                    days_of_week=schedule.config.get('days_of_week'),
                    random_range=schedule.config.get('random_range')
                )
                
                schedule.last_run = now
                schedule.next_run = self._calculate_next_run(config)
                
                # Обновить в базе данных
                async with autopost_db.session() as session:
                    session.add(schedule)
                    await session.commit()
                
                logger.info(f"✅ Triggered schedule {schedule.id}, next run: {schedule.next_run}")
                
            except Exception as e:
                logger.error(f"Failed to process schedule {schedule.id}: {e}")
    
    async def _get_due_schedules(self, now: datetime) -> List[AutoPostSchedule]:
        """Получить просроченные расписания с кэшированием.
        
        Args:
            now: Текущее время
            
        Returns:
            Список просроченных расписаний
        """
        # Получить активные расписания с кэшированием
        all_active_schedules = await self._get_active_schedules()
        
        # Отфильтровать просроченные
        due_schedules = [
            schedule for schedule in all_active_schedules
            if schedule.next_run <= now
        ]
        
        return due_schedules
    
    async def _get_active_schedules(self) -> List[AutoPostSchedule]:
        """Получить активные расписания с кэшированием.
        
        Returns:
            Список активных расписаний
        """
        cache_key = "active_schedules_cache"
        
        # Попробовать получить из кэша
        cached_data = await cache.get(cache_key)
        if cached_data:
            # Временно возвращаем пустой список, так как десериализация 
            # AutoPostSchedule из кэша требует дополнительной логики
            pass
        
        # Загрузить из базы данных
        async with autopost_db.session() as session:
            result = await session.execute(
                select(AutoPostSchedule).where(
                    AutoPostSchedule.is_active == True
                )
            )
            schedules = result.scalars().all()
        
        # Кэшировать результат
        # Для простоты не кэшируем сложные объекты, а просто обновляем внутренний кэш
        self._active_schedules_cache = schedules
        self._cache_last_update = datetime.now()
        
        # Установить в кэш простую информацию для быстрой проверки
        schedule_info = [
            {
                'id': s.id,
                'channel_id': s.channel_id,
                'next_run': s.next_run.isoformat(),
                'config': s.config
            } for s in schedules
        ]
        await cache.set(cache_key, schedule_info, self.cache_ttl)
        
        return schedules
    
    async def _get_active_schedules_for_channel(self, channel_id: int) -> List[AutoPostSchedule]:
        """Получить активные расписания для конкретного канала.
        
        Args:
            channel_id: ID канала
            
        Returns:
            Список активных расписаний для канала
        """
        all_schedules = await self._get_active_schedules()
        return [s for s in all_schedules if s.channel_id == channel_id]
    
    async def _invalidate_schedules_cache(self):
        """Инвалидировать кэш активных расписаний."""
        await cache.delete("active_schedules_cache")
        self._active_schedules_cache = None
        self._cache_last_update = datetime.min
    
    async def get_scheduler_stats(self) -> dict:
        """Получить статистику планировщика.
        
        Returns:
            Словарь со статистикой
        """
        active_schedules = await self._get_active_schedules()
        
        return {
            'running': self.running,
            'total_active_schedules': len(active_schedules),
            'check_interval': self.check_interval,
            'cache_ttl': self.cache_ttl,
            'last_cache_update': self._cache_last_update.isoformat() if self._cache_last_update != datetime.min else None
        }