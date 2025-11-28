"""Integration tests for auto-posting system."""
import asyncio
import pytest
import os
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from sqlalchemy import select

from src.services.autopost.scheduler import AutoPostScheduler, ScheduleConfig, ScheduleMode
from src.services.autopost.publishing import AutoPostPublisher, PublishResult
from src.services.autopost.content_generator import AutoPostContentGenerator
from src.services.autopost.queue_manager import AutoPostQueueManager
from src.services.telegram_analytics_connector import TelegramAnalyticsConnector, EngagementMetrics
from src.models.autopost import AutoPost, AutoPostSchedule, PostStatus
from src.database.autopost_db import autopost_db


class TestAutoPostIntegration:
    """Integration tests for the auto-posting system components."""
    
    @pytest.fixture
    async def setup_scheduler(self):
        """Setup scheduler for testing."""
        scheduler = AutoPostScheduler()
        await scheduler.start()
        yield scheduler
        await scheduler.stop()
    
    @pytest.fixture
    async def setup_publisher(self):
        """Setup publisher for testing."""
        # Mock Telegram bot
        bot = AsyncMock()
        bot.send_message = AsyncMock(return_value=MagicMock(message_id=12345))
        publisher = AutoPostPublisher(bot)
        return publisher
    
    @pytest.fixture
    async def setup_content_generator(self):
        """Setup content generator for testing."""
        generator = AutoPostContentGenerator()
        return generator
    
    @pytest.fixture
    async def setup_queue_manager(self):
        """Setup queue manager for testing."""
        queue_manager = AutoPostQueueManager()
        return queue_manager
    
    @pytest.fixture
    async def setup_analytics_connector(self):
        """Setup analytics connector for testing."""
        # Mock bot token for testing
        connector = TelegramAnalyticsConnector(bot_token="test_token")
        return connector
    
    @pytest.mark.asyncio
    async def test_complete_autopost_workflow(self, setup_scheduler, setup_publisher, setup_content_generator, setup_queue_manager):
        """Test complete auto-posting workflow with all components working together."""
        scheduler = setup_scheduler
        publisher = setup_publisher
        generator = setup_content_generator
        queue_manager = setup_queue_manager
        
        # Create a test channel
        channel_id = 123456789
        
        # Create schedule configuration
        schedule_config = ScheduleConfig(
            channel_id=channel_id,
            mode=ScheduleMode.FIXED,
            time_slots=["12:00"],
            days_of_week=[0, 1, 2, 3, 4, 5, 6]  # All days
        )
        
        # Add schedule
        schedule_id = await scheduler.add_schedule(channel_id, schedule_config)
        assert schedule_id is not None
        
        # Register callback for the scheduler to trigger post creation
        async def post_creation_callback(channel_id):
            # Generate content
            content = await generator.generate_post_content("Test topic", "Test channel")
            assert content is not None
            
            # Create post object
            post = AutoPost(
                id="test_post_1",
                channel_id=channel_id,
                content=content,
                status=PostStatus.PENDING.value,
                created_at=datetime.utcnow()
            )
            
            # Add to queue
            await queue_manager.add_to_queue(post)
            
            # Publish from queue
            queued_post = await queue_manager.get_next_post(channel_id)
            if queued_post:
                result = await publisher.publish_post(queued_post)
                assert result.success is True
        
        scheduler.register_callback(schedule_id, post_creation_callback)
        
        # Verify schedule was added to database
        async with autopost_db.session() as session:
            result = await session.execute(
                select(AutoPostSchedule).where(AutoPostSchedule.id == schedule_id)
            )
            db_schedule = result.scalar_one_or_none()
            assert db_schedule is not None
            assert db_schedule.channel_id == channel_id
            assert db_schedule.is_active is True
        
        # Test the complete workflow by manually triggering
        await scheduler.trigger_post_creation(channel_id)
        
        # Verify post was created and published
        async with autopost_db.session() as session:
            result = await session.execute(
                select(AutoPost).where(AutoPost.channel_id == channel_id)
            )
            posts = result.scalars().all()
            assert len(posts) >= 1
            assert posts[0].status == PostStatus.PUBLISHED.value
    
    @pytest.mark.asyncio
    async def test_scheduler_publisher_integration(self, setup_scheduler, setup_publisher):
        """Test integration between scheduler and publisher."""
        scheduler = setup_scheduler
        publisher = setup_publisher
        
        # Mock publisher to simulate successful publishing
        publisher.publish_post = AsyncMock(return_value=PublishResult(success=True, message_id=12345))
        
        # Create test post
        test_post = AutoPost(
            id="integration_test_post",
            channel_id=987654321,
            content="Test content for integration",
            status=PostStatus.PENDING.value,
            created_at=datetime.utcnow()
        )
        
        # Create schedule
        schedule_config = ScheduleConfig(
            channel_id=test_post.channel_id,
            mode=ScheduleMode.RANDOM,
            random_range=(1, 5)  # 1-5 minutes
        )
        
        schedule_id = await scheduler.add_schedule(test_post.channel_id, schedule_config)
        
        # Register callback that publishes the test post
        async def publish_callback(channel_id):
            result = await publisher.publish_post(test_post)
            assert result.success is True
        
        scheduler.register_callback(schedule_id, publish_callback)
        
        # Trigger the schedule
        await scheduler.trigger_post_creation(test_post.channel_id)
        
        # Verify publisher was called
        publisher.publish_post.assert_called_once_with(test_post)
    
    @pytest.mark.asyncio
    async def test_content_generator_scheduler_integration(self, setup_scheduler, setup_content_generator, setup_publisher):
        """Test integration between content generator, scheduler and publisher."""
        scheduler = setup_scheduler
        generator = setup_content_generator
        publisher = setup_publisher
        
        # Mock publisher
        publisher.publish_post = AsyncMock(return_value=PublishResult(success=True, message_id=12345))
        
        channel_id = 111222333
        
        # Create schedule
        schedule_config = ScheduleConfig(
            channel_id=channel_id,
            mode=ScheduleMode.FIXED,
            time_slots=["10:30"]
        )
        
        schedule_id = await scheduler.add_schedule(channel_id, schedule_config)
        
        # Register callback that generates content and publishes
        async def generate_and_publish_callback(channel_id):
            # Generate content
            content = await generator.generate_post_content("Technology news", "Tech channel")
            assert content is not None
            assert len(content) > 0
            
            # Create post
            post = AutoPost(
                id=f"gen_post_{datetime.utcnow().timestamp()}",
                channel_id=channel_id,
                content=content,
                status=PostStatus.PENDING.value,
                created_at=datetime.utcnow()
            )
            
            # Publish post
            result = await publisher.publish_post(post)
            assert result.success is True
        
        scheduler.register_callback(schedule_id, generate_and_publish_callback)
        
        # Trigger the schedule
        await scheduler.trigger_post_creation(channel_id)
        
        # Verify publisher was called
        assert publisher.publish_post.called
        assert len(publisher.publish_post.call_args_list) == 1
        
        # Verify the content was generated properly
        published_post = publisher.publish_post.call_args[0][0]
        assert isinstance(published_post, AutoPost)
        assert len(published_post.content) > 0
    
    @pytest.mark.asyncio
    async def test_queue_manager_scheduler_integration(self, setup_scheduler, setup_queue_manager, setup_publisher):
        """Test integration between queue manager, scheduler and publisher."""
        scheduler = setup_scheduler
        queue_manager = setup_queue_manager
        publisher = setup_publisher
        
        # Mock publisher
        publisher.publish_post = AsyncMock(return_value=PublishResult(success=True, message_id=12345))
        
        channel_id = 444555666
        
        # Create schedule
        schedule_config = ScheduleConfig(
            channel_id=channel_id,
            mode=ScheduleMode.INTERVAL,
            time_slots=["2"]  # Every 2 hours
        )
        
        schedule_id = await scheduler.add_schedule(channel_id, schedule_config)
        
        # Register callback that uses queue manager
        async def queue_and_publish_callback(channel_id):
            # Create multiple test posts
            for i in range(3):
                post = AutoPost(
                    id=f"queued_post_{i}_{datetime.utcnow().timestamp()}",
                    channel_id=channel_id,
                    content=f"Test content {i}",
                    status=PostStatus.PENDING.value,
                    created_at=datetime.utcnow()
                )
                
                # Add to queue
                await queue_manager.add_to_queue(post)
            
            # Process queue
            while True:
                queued_post = await queue_manager.get_next_post(channel_id)
                if queued_post is None:
                    break
                
                result = await publisher.publish_post(queued_post)
                assert result.success is True
                
                # Mark as processed
                await queue_manager.mark_as_processed(queued_post.id)
        
        scheduler.register_callback(schedule_id, queue_and_publish_callback)
        
        # Trigger the schedule
        await scheduler.trigger_post_creation(channel_id)
        
        # Verify all posts were published
        assert publisher.publish_post.call_count == 3
        
        # Verify queue is empty
        queued_post = await queue_manager.get_next_post(channel_id)
        assert queued_post is None
    
    @pytest.mark.asyncio
    async def test_error_handling_in_full_workflow(self, setup_scheduler, setup_publisher, setup_content_generator):
        """Test error handling throughout the full workflow."""
        scheduler = setup_scheduler
        publisher = setup_publisher
        generator = setup_content_generator
        
        # Mock publisher to simulate failure
        publisher.publish_post = AsyncMock(return_value=PublishResult(success=False, error="Test error"))
        
        channel_id = 777888999
        
        # Create schedule
        schedule_config = ScheduleConfig(
            channel_id=channel_id,
            mode=ScheduleMode.FIXED,
            time_slots=["14:00"]
        )
        
        schedule_id = await scheduler.add_schedule(channel_id, schedule_config)
        
        # Register callback that handles errors gracefully
        async def error_handling_callback(channel_id):
            try:
                # Generate content
                content = await generator.generate_post_content("Error test", "Test channel")
                
                # Create post
                post = AutoPost(
                    id="error_test_post",
                    channel_id=channel_id,
                    content=content,
                    status=PostStatus.PENDING.value,
                    created_at=datetime.utcnow()
                )
                
                # Publish post (will fail)
                result = await publisher.publish_post(post)
                
                # Verify failure was handled
                assert result.success is False
                assert result.error == "Test error"
                
                # Update post status in DB
                async with autopost_db.session() as session:
                    post.status = PostStatus.FAILED.value
                    session.add(post)
                    await session.commit()
                    
            except Exception as e:
                # Error should be caught and handled
                assert str(e) != "Test error"  # Should be handled internally
        
        scheduler.register_callback(schedule_id, error_handling_callback)
        
        # Trigger the schedule
        await scheduler.trigger_post_creation(channel_id)
        
        # Verify error was handled properly
        publisher.publish_post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_multiple_channels_concurrent_workflow(self, setup_scheduler, setup_publisher, setup_content_generator):
        """Test concurrent workflows for multiple channels."""
        scheduler = setup_scheduler
        publisher = setup_publisher
        generator = setup_content_generator
        
        # Mock publisher
        publisher.publish_post = AsyncMock(return_value=PublishResult(success=True, message_id=12345))
        
        # Create multiple channels
        channels = [11111111, 22222, 33333333]
        
        # Create schedules for each channel
        schedule_ids = []
        for channel_id in channels:
            schedule_config = ScheduleConfig(
                channel_id=channel_id,
                mode=ScheduleMode.RANDOM,
                random_range=(1, 3)
            )
            
            schedule_id = await scheduler.add_schedule(channel_id, schedule_config)
            schedule_ids.append(schedule_id)
        
        # Register callbacks for each channel
        for i, channel_id in enumerate(channels):
            async def create_callback(ch_id, idx):
                async def callback(channel_id):
                    # Generate content
                    content = await generator.generate_post_content(f"Channel {idx} content", f"Channel_{idx}")
                    
                    # Create post
                    post = AutoPost(
                        id=f"multi_post_{idx}_{datetime.utcnow().timestamp()}",
                        channel_id=ch_id,
                        content=content,
                        status=PostStatus.PENDING.value,
                        created_at=datetime.utcnow()
                    )
                    
                    # Publish post
                    result = await publisher.publish_post(post)
                    assert result.success is True
                
                return callback
            
            callback = await create_callback(channel_id, i)
            scheduler.register_callback(schedule_ids[i], callback)
        
        # Trigger all schedules concurrently
        tasks = []
        for channel_id in channels:
            task = asyncio.create_task(scheduler.trigger_post_creation(channel_id))
            tasks.append(task)
        
        # Wait for all tasks to complete
        await asyncio.gather(*tasks)
        
        # Verify all posts were published
        assert publisher.publish_post.call_count == len(channels)
    
    async def test_analytics_integration(self, setup_analytics_connector):
        """Test integration with analytics system."""
        connector = setup_analytics_connector
        
        # Mock the session and make_request methods
        with patch.object(connector, '_make_request', new_callable=AsyncMock) as mock_request:
            # Mock response for get_channel_info
            mock_request.return_value = {
                "ok": True,
                "result": {
                    "id": 123456789,
                    "title": "Test Channel",
                    "username": "test_channel",
                    "members_count": 1000
                }
            }
            
            # Test getting channel info
            channel_info = await connector.get_channel_info("test_channel")
            assert channel_info.get("title") == "Test Channel"
            assert channel_info.get("members_count") == 100
            
            # Test engagement metrics
            mock_request.return_value = {
                "ok": True,
                "result": {
                    "views": 500,
                    "reactions": 50,
                    "shares": 25,
                    "comments": 10
                }
            }
            
            start_date = datetime.utcnow() - timedelta(days=7)
            end_date = datetime.utcnow()
            
            engagement = await connector.get_engagement_metrics("test_channel", start_date, end_date)
            assert isinstance(engagement, EngagementMetrics)
            assert engagement.views == 500
            assert engagement.reactions == 50
            assert engagement.shares == 25
            assert engagement.comments == 10


class TestExternalAPIIntegration:
    """Integration tests for external API integrations."""
    
    @pytest.mark.asyncio
    async def test_telegram_analytics_connector_full_integration(self):
        """Test full integration with Telegram Analytics API."""
        # Mock bot token for testing
        connector = TelegramAnalyticsConnector(bot_token="test_token")
        
        # Test connection
        await connector.connect()
        assert connector.session is not None
        
        try:
            # Mock the _make_request method to simulate API responses
            with patch.object(connector, '_make_request', new_callable=AsyncMock) as mock_request:
                # Simulate successful API response
                mock_request.return_value = {
                    "ok": True,
                    "result": {
                        "id": 123456789,
                        "title": "Test Analytics Channel",
                        "username": "test_analytics_channel",
                        "type": "channel",
                        "members_count": 5000
                    }
                }
                
                # Test get_channel_info
                channel_info = await connector.get_channel_info("test_analytics_channel")
                assert channel_info.get("title") == "Test Analytics Channel"
                assert channel_info.get("members_count") == 5000
                
                # Test engagement metrics
                mock_request.return_value = {
                    "ok": True,
                    "result": {
                        "views": 1250,
                        "reactions": 125,
                        "shares": 62,
                        "comments": 25,
                        "reach": 2500,
                        "impressions": 2000
                    }
                }
                
                start_date = datetime.utcnow() - timedelta(days=1)
                end_date = datetime.utcnow()
                
                engagement = await connector.get_engagement_metrics(
                    "test_analytics_channel",
                    start_date,
                    end_date
                )
                assert isinstance(engagement, EngagementMetrics)
                assert engagement.views == 1250
                assert engagement.reactions == 125
                assert engagement.shares == 62
                assert engagement.comments == 25
                assert engagement.reach == 2500
                assert engagement.impressions == 200
                
                # Test post metrics
                mock_request.return_value = {
                    "ok": True,
                    "result": [
                        {"post_id": 1, "views": 100, "reactions": 10},
                        {"post_id": 2, "views": 150, "reactions": 15}
                    ]
                }
                
                post_metrics = await connector.get_post_metrics("test_analytics_channel", [1, 2])
                assert len(post_metrics) == 2
                assert isinstance(post_metrics[1], EngagementMetrics)
                
        finally:
            await connector.disconnect()
            assert connector.session is None
    
    @pytest.mark.asyncio
    async def test_telegram_analytics_error_handling(self):
        """Test error handling in Telegram Analytics connector."""
        connector = TelegramAnalyticsConnector(bot_token="test_token")
        
        await connector.connect()
        
        try:
            # Mock the _make_request method to simulate API errors
            with patch.object(connector, '_make_request', new_callable=AsyncMock) as mock_request:
                # Simulate API error
                mock_request.side_effect = Exception("API Error")
                
                # Test get_channel_info error handling
                channel_info = await connector.get_channel_info("test_channel")
                assert channel_info == {}
                
                # Test engagement metrics error handling
                start_date = datetime.utcnow() - timedelta(days=1)
                end_date = datetime.utcnow()
                
                engagement = await connector.get_engagement_metrics(
                    "test_channel",
                    start_date,
                    end_date
                )
                assert isinstance(engagement, EngagementMetrics)
                assert engagement.views == 0
                assert engagement.reactions == 0
                
                # Test post metrics error handling
                post_metrics = await connector.get_post_metrics("test_channel", [1, 2])
                assert len(post_metrics) == 2
                for metrics in post_metrics.values():
                    assert isinstance(metrics, EngagementMetrics)
                    assert metrics.views == 0
        
        finally:
            await connector.disconnect()
    
    @pytest.mark.asyncio
    async def test_analytics_data_processing_integration(self):
        """Test analytics data processing and normalization."""
        connector = TelegramAnalyticsConnector(bot_token="test_token")
        
        # Test data processing
        raw_data = {
            'views': 1000,
            'reactions': 100,
            'shares': 50,
            'comments': 25,
            'reach': 2000,
            'impressions': 1500,
            'saves': 10,
            'forwards': 30,
            'engagement_rate': 0.1
        }
        
        normalized_data = await connector.process_and_normalize_data(raw_data)
        
        # Verify normalized data structure
        assert 'timestamp' in normalized_data
        assert 'metrics' in normalized_data
        assert 'engagement' in normalized_data
        assert 'period' in normalized_data
        
        metrics = normalized_data['metrics']
        engagement = normalized_data['engagement']
        
        assert metrics['views'] == 1000
        assert metrics['reactions'] == 100
        assert metrics['shares'] == 50
        assert engagement['total'] == 130  # reactions + forwards
        
        # Test engagement rate calculation
        expected_rate = (engagement['total'] / metrics['impressions']) * 10 if metrics['impressions'] > 0 else 0.0
        assert engagement['rate'] == expected_rate
    
    @pytest.mark.asyncio
    async def test_analytics_database_integration(self):
        """Test integration between analytics and database."""
        connector = TelegramAnalyticsConnector(bot_token="test_token")
        
        # Mock data for integration test
        normalized_data = {
            'metrics': {
                'views': 500,
                'reactions': 50,
                'shares': 25,
                'comments': 10,
                'reach': 1000,
                'impressions': 800,
                'saves': 5,
                'forwards': 15
            },
            'engagement': {
                'rate': 0.08125,  # (50+15)/800 * 10
                'total': 65
            },
            'period': {
                'start': (datetime.utcnow() - timedelta(days=1)).isoformat(),
                'end': datetime.utcnow().isoformat()
            }
        }
        
        # Test integration with metrics system
        with patch('src.services.telegram_analytics_connector.get_session') as mock_session:
            # Create a mock async session
            async_mock_session = AsyncMock()
            mock_session.return_value.__aenter__.return_value = async_mock_session
            mock_session.return_value.__aexit__.return_value = None
            
            # Mock the metrics repository
            with patch('src.services.telegram_analytics_connector.MetricsRepository') as mock_repo_class:
                mock_repo = AsyncMock()
                mock_repo_class.return_value = mock_repo
                mock_repo.get_by_post_id.return_value = None  # No existing metrics
                mock_repo.create.return_value = None
                
                # Mock SQLAlchemy select query
                with patch('src.services.telegram_analytics_connector.select') as mock_select:
                    with patch('src.services.telegram_analytics_connector.Post') as mock_post_model:
                        # Mock the query execution
                        mock_result = AsyncMock()
                        mock_result.scalars.return_value.all.return_value = [
                            MagicMock(id=1),
                            MagicMock(id=2)
                        ]
                        
                        async_mock_session.execute.return_value = mock_result
                        
                        # Test integration
                        success = await connector.integrate_with_metrics_system(123, normalized_data)
                        assert success is True
                        
                        # Verify the repository methods were called
                        assert mock_repo.create.call_count == 2  # For each post
                        
                        # Check that create was called with correct parameters
                        calls = mock_repo.create.call_args_list
                        for call in calls:
                            metrics_obj = call[0][0]
                            assert metrics_obj.views in [250, 250]  # 500/2
                            assert metrics_obj.reactions in [25, 25]  # 50/2
                            assert metrics_obj.shares in [12, 13]  # 25/2 (rounded)
    
    @pytest.mark.asyncio
    async def test_analytics_sync_functionality(self):
        """Test analytics sync functionality."""
        connector = TelegramAnalyticsConnector(bot_token="test_token")
        
        # Mock all required methods
        with patch.object(connector, 'get_engagement_metrics') as mock_get_engagement:
            with patch.object(connector, 'process_and_normalize_data') as mock_process:
                with patch.object(connector, 'integrate_with_metrics_system') as mock_integrate:
                    # Mock return values
                    mock_get_engagement.return_value = EngagementMetrics(
                        views=1000,
                        reactions=100,
                        shares=50,
                        comments=25,
                        engagement_rate=0.1
                    )
                    mock_process.return_value = {"normalized": "data"}
                    mock_integrate.return_value = True
                    
                    # Test sync
                    result = await connector.sync_channel_analytics("test_channel", 123, 7)
                    assert result is True
                    
                    # Verify all methods were called
                    mock_get_engagement.assert_called_once()
                    mock_process.assert_called_once()
                    mock_integrate.assert_called_once()


class TestAutoPostPerformance:
    """Performance tests for auto-posting system."""
    
    @pytest.mark.asyncio
    async def test_scheduler_performance(self):
        """Test scheduler performance with multiple schedules."""
        scheduler = AutoPostScheduler()
        await scheduler.start()
        
        try:
            # Create multiple schedules
            channel_ids = list(range(1000, 1010))  # 10 channels
            schedule_ids = []
            
            start_time = asyncio.get_event_loop().time()
            
            for channel_id in channel_ids:
                schedule_config = ScheduleConfig(
                    channel_id=channel_id,
                    mode=ScheduleMode.RANDOM,
                    random_range=(1, 10)
                )
                
                schedule_id = await scheduler.add_schedule(channel_id, schedule_config)
                schedule_ids.append(schedule_id)
            
            end_time = asyncio.get_event_loop().time()
            creation_time = end_time - start_time
            
            # Verify all schedules were created
            assert len(schedule_ids) == len(channel_ids)
            assert creation_time < 5.0  # Should complete within 5 seconds
            
            # Test trigger performance
            trigger_start = asyncio.get_event_loop().time()
            
            for channel_id in channel_ids:
                await scheduler.trigger_post_creation(channel_id)
            
            trigger_end = asyncio.get_event_loop().time()
            trigger_time = trigger_end - trigger_start
            
            assert trigger_time < 2.0  # Should trigger all in under 2 seconds
            
        finally:
            await scheduler.stop()
    
    @pytest.mark.asyncio
    async def test_publisher_performance(self):
        """Test publisher performance with multiple posts."""
        # Mock bot
        bot = AsyncMock()
        bot.send_message = AsyncMock(return_value=MagicMock(message_id=12345))
        
        publisher = AutoPostPublisher(bot)
        
        # Create multiple test posts
        posts = []
        for i in range(50):
            post = AutoPost(
                id=f"perf_test_post_{i}",
                channel_id=123456789,
                content=f"Performance test content {i}",
                status=PostStatus.PENDING.value,
                created_at=datetime.utcnow()
            )
            posts.append(post)
        
        # Measure publishing time
        start_time = asyncio.get_event_loop().time()
        
        publish_tasks = []
        for post in posts:
            task = asyncio.create_task(publisher.publish_post(post))
            publish_tasks.append(task)
        
        results = await asyncio.gather(*publish_tasks)
        
        end_time = asyncio.get_event_loop().time()
        publish_time = end_time - start_time
        
        # Verify all posts were published successfully
        assert len(results) == len(posts)
        for result in results:
            assert result.success is True
        
        # Should complete within reasonable time
        assert publish_time < 10.0  # 50 posts in under 10 seconds


if __name__ == "__main__":
    pytest.main([__file__, "-v"])