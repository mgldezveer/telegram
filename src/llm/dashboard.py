"""
LLM Metrics Dashboard
Web-интерфейс для просмотра метрик LLM системы
"""

import logging
from typing import Optional
from datetime import datetime

try:
    from aiohttp import web
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    web = None

from .metrics import get_metrics
from .config import get_config
from .status_checker import StatusChecker

logger = logging.getLogger(__name__)


class MetricsDashboard:
    """
    Web dashboard для метрик LLM
    
    Предоставляет:
    - /metrics - Prometheus метрики
    - /health - Health check endpoint
    - /dashboard - HTML dashboard с метриками
    - /api/stats - JSON API со статистикой
    """
    
    def __init__(self, host: str = '0.0.0.0', port: int = 8080):
        """
        Инициализация dashboard.
        
        Args:
            host: Хост для прослушивания
            port: Порт для прослушивания
        """
        if not AIOHTTP_AVAILABLE:
            raise ImportError(
                "aiohttp not installed. Install with: pip install aiohttp"
            )
        
        self.host = host
        self.port = port
        self.app = web.Application()
        self.runner: Optional[web.AppRunner] = None
        
        # Регистрация маршрутов
        self.app.router.add_get('/health', self.health_handler)
        self.app.router.add_get('/api/stats', self.stats_handler)
        self.app.router.add_get('/api/status', self.status_handler)
        self.app.router.add_get('/dashboard', self.dashboard_handler)
        self.app.router.add_get('/', self.dashboard_handler)
        
        # Prometheus метрики (если доступны)
        try:
            from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
            self.app.router.add_get('/metrics', self.prometheus_handler)
            logger.info("✅ Prometheus metrics endpoint enabled")
        except ImportError:
            logger.warning("⚠️ Prometheus client not available")
    
    async def health_handler(self, request):
        """Health check endpoint"""
        metrics = get_metrics()
        stats = metrics.get_statistics()
        
        # Проверка здоровья системы
        is_healthy = (
            stats['total_requests'] == 0 or
            stats['success_rate'] > 50.0
        )
        
        status = 200 if is_healthy else 503
        
        return web.json_response({
            'status': 'healthy' if is_healthy else 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'uptime_seconds': stats['uptime_seconds'],
            'total_requests': stats['total_requests'],
            'success_rate': stats['success_rate']
        }, status=status)
    
    async def stats_handler(self, request):
        """API endpoint для статистики"""
        metrics = get_metrics()
        stats = metrics.get_statistics()
        
        return web.json_response(stats)
    
    async def status_handler(self, request):
        """API endpoint для статуса провайдеров"""
        checker = StatusChecker()
        statuses = await checker.check_all_providers()
        
        return web.json_response({
            name: status.to_dict()
            for name, status in statuses.items()
        })
    
    async def dashboard_handler(self, request):
        """HTML dashboard"""
        metrics = get_metrics()
        dashboard_data = metrics.get_dashboard_data()
        config = get_config()
        
        html = self._generate_dashboard_html(dashboard_data, config)
        return web.Response(text=html, content_type='text/html')
    
    async def prometheus_handler(self, request):
        """Prometheus metrics endpoint"""
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
        
        metrics_output = generate_latest()
        return web.Response(
            body=metrics_output,
            content_type=CONTENT_TYPE_LATEST
        )
    
    def _generate_dashboard_html(self, data: dict, config) -> str:
        """Генерация HTML для dashboard"""
        
        # Форматирование провайдеров
        providers_html = ""
        for name, provider_data in data['providers'].items():
            providers_html += f"""
            <tr>
                <td>{name}</td>
                <td>{provider_data['requests']}</td>
                <td>{provider_data['errors']}</td>
                <td>{provider_data['error_rate']}</td>
            </tr>
            """
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>LLM Metrics Dashboard</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background: #f5f5f5;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                }}
                h1 {{
                    color: #333;
                    margin-bottom: 30px;
                }}
                .card {{
                    background: white;
                    border-radius: 8px;
                    padding: 20px;
                    margin-bottom: 20px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .card h2 {{
                    margin-top: 0;
                    color: #555;
                    font-size: 18px;
                }}
                .metrics-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 15px;
                    margin-bottom: 20px;
                }}
                .metric {{
                    background: #f8f9fa;
                    padding: 15px;
                    border-radius: 6px;
                }}
                .metric-label {{
                    font-size: 12px;
                    color: #666;
                    text-transform: uppercase;
                    margin-bottom: 5px;
                }}
                .metric-value {{
                    font-size: 24px;
                    font-weight: bold;
                    color: #333;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                }}
                th, td {{
                    padding: 12px;
                    text-align: left;
                    border-bottom: 1px solid #eee;
                }}
                th {{
                    background: #f8f9fa;
                    font-weight: 600;
                    color: #555;
                }}
                .status-badge {{
                    display: inline-block;
                    padding: 4px 8px;
                    border-radius: 4px;
                    font-size: 12px;
                    font-weight: 600;
                }}
                .status-enabled {{
                    background: #d4edda;
                    color: #155724;
                }}
                .status-disabled {{
                    background: #f8d7da;
                    color: #721c24;
                }}
                .refresh-btn {{
                    background: #007bff;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 6px;
                    cursor: pointer;
                    font-size: 14px;
                }}
                .refresh-btn:hover {{
                    background: #0056b3;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🤖 LLM Metrics Dashboard</h1>
                
                <div class="card">
                    <h2>📊 Overview</h2>
                    <div class="metrics-grid">
                        <div class="metric">
                            <div class="metric-label">Total Requests</div>
                            <div class="metric-value">{data['overview']['total_requests']}</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Success Rate</div>
                            <div class="metric-value">{data['overview']['success_rate']}</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Avg Response Time</div>
                            <div class="metric-value">{data['overview']['avg_response_time']}</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Uptime</div>
                            <div class="metric-value">{data['overview']['uptime']}</div>
                        </div>
                    </div>
                </div>
                
                <div class="card">
                    <h2>🔌 Providers</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>Provider</th>
                                <th>Requests</th>
                                <th>Errors</th>
                                <th>Error Rate</th>
                            </tr>
                        </thead>
                        <tbody>
                            {providers_html}
                        </tbody>
                    </table>
                </div>
                
                <div class="card">
                    <h2>💾 Cache</h2>
                    <div class="metrics-grid">
                        <div class="metric">
                            <div class="metric-label">Cache Hits</div>
                            <div class="metric-value">{data['cache']['hits']}</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Cache Misses</div>
                            <div class="metric-value">{data['cache']['misses']}</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Hit Rate</div>
                            <div class="metric-value">{data['cache']['hit_rate']}</div>
                        </div>
                    </div>
                </div>
                
                <div class="card">
                    <h2>🎯 Tokens</h2>
                    <div class="metrics-grid">
                        <div class="metric">
                            <div class="metric-label">Total Tokens</div>
                            <div class="metric-value">{data['tokens']['total']}</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Per Request</div>
                            <div class="metric-value">{data['tokens']['per_request']}</div>
                        </div>
                    </div>
                </div>
                
                <div class="card">
                    <h2>⚙️ Configuration</h2>
                    <p><strong>Default Provider:</strong> {config.default_provider}</p>
                    <p><strong>Fallback:</strong> {'✅ Enabled' if config.fallback_enabled else '❌ Disabled'}</p>
                    <p><strong>Cache:</strong> {'✅ Enabled' if config.cache_enabled else '❌ Disabled'}</p>
                    <p><strong>Rate Limiting:</strong> {'✅ Enabled' if config.rate_limit_enabled else '❌ Disabled'}</p>
                </div>
                
                <button class="refresh-btn" onclick="location.reload()">🔄 Refresh</button>
            </div>
            
            <script>
                // Auto-refresh every 30 seconds
                setTimeout(() => location.reload(), 30000);
            </script>
        </body>
        </html>
        """
        
        return html
    
    async def start(self):
        """Запуск dashboard сервера"""
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        
        site = web.TCPSite(self.runner, self.host, self.port)
        await site.start()
        
        logger.info(f"✅ Metrics dashboard started at http://{self.host}:{self.port}")
        logger.info(f"   - Dashboard: http://{self.host}:{self.port}/dashboard")
        logger.info(f"   - Health: http://{self.host}:{self.port}/health")
        logger.info(f"   - Stats API: http://{self.host}:{self.port}/api/stats")
        logger.info(f"   - Metrics: http://{self.host}:{self.port}/metrics")
    
    async def stop(self):
        """Остановка dashboard сервера"""
        if self.runner:
            await self.runner.cleanup()
            logger.info("Dashboard stopped")


# Для запуска из командной строки
if __name__ == "__main__":
    import asyncio
    
    async def main():
        dashboard = MetricsDashboard()
        await dashboard.start()
        
        print("Dashboard running. Press Ctrl+C to stop.")
        
        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            await dashboard.stop()
    
    asyncio.run(main())
