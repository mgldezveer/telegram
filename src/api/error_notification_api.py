"""Система передачи информации об ошибках через API/MCP для Telegram-бота."""
import asyncio
import json
import logging
import traceback
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any, Set
from enum import Enum

import aiohttp
from aiohttp import web, WSMsgType
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.monitoring.realtime_error_detector import (
    RealtimeErrorDetector, 
    ErrorEvent, 
    PerformanceAnomaly, 
    ErrorPriority, 
    ErrorType, 
    AnomalyType,
    realtime_error_detector
)
from src.monitoring.enhanced_monitoring import enhanced_monitoring


# Модели данных для API
class ErrorEventModel(BaseModel):
    """Модель для события ошибки."""
    timestamp: str
    error_type: str
    priority: str
    component: str
    message: str
    traceback_info: Optional[str] = None
    user_id: Optional[str] = None
    chat_id: Optional[str] = None
    command: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None


class PerformanceAnomalyModel(BaseModel):
    """Модель для события аномалии производительности."""
    timestamp: str
    anomaly_type: str
    component: str
    metric_name: str
    current_value: float
    threshold_value: float
    severity: str
    description: str
    extra_data: Optional[Dict[str, Any]] = None


class ErrorNotificationAPI:
    """Система передачи информации об ошибках через API/MCP."""
    
    def __init__(self, 
                 rest_api_port: int = 8001, 
                 websocket_port: int = 8002,
                 mcp_port: int = 8003):
        self.rest_api_port = rest_api_port
        self.websocket_port = websocket_port
        self.mcp_port = mcp_port
        
        # FastAPI приложение для REST API
        self.rest_app = FastAPI(
            title="Error Notification API",
            description="API для получения информации об ошибках в Telegram-боте",
            version="1.0.0"
        )
        
        # aiohttp приложение для WebSocket
        self.ws_app = web.Application()
        
        # Список активных WebSocket соединений
        self.active_connections: Set[WebSocket] = set()
        self.active_ws_connections: Set[web.WebSocketResponse] = set()
        
        # MCP сервер (реализация через aiohttp)
        self.mcp_app = web.Application()
        
        # Логгер
        self.logger = logging.getLogger(__name__)
        
        # Детектор ошибок
        self.error_detector = realtime_error_detector
        
        # Запуск серверов
        self._setup_rest_api()
        self._setup_websocket_api()
        self._setup_mcp_server()
    
    def _setup_rest_api(self):
        """Настроить REST API endpoints."""
        
        @self.rest_app.post("/errors", response_model=ErrorEventModel)
        async def receive_error(error_data: ErrorEventModel):
            """Получить информацию об ошибке через REST API."""
            try:
                # Преобразовать полученные данные в ErrorEvent
                error_event = ErrorEvent(
                    timestamp=datetime.fromisoformat(error_data.timestamp),
                    error_type=ErrorType(error_data.error_type),
                    priority=ErrorPriority(error_data.priority),
                    component=error_data.component,
                    message=error_data.message,
                    traceback_info=error_data.traceback_info,
                    user_id=error_data.user_id,
                    chat_id=error_data.chat_id,
                    command=error_data.command,
                    extra_data=error_data.extra_data
                )
                
                # Добавить в буфер детектора ошибок
                self.error_detector.error_buffer.append(error_event)
                
                # Обновить статистику
                self.error_detector.component_error_counts[error_event.component][error_event.error_type.value] += 1
                self.error_detector.component_error_timers[error_event.component].append(error_event.timestamp.timestamp())
                
                # Отправить уведомление
                self.error_detector._send_notification(error_event)
                
                # Записать в лог
                self.error_detector._log_error_event(error_event)
                
                # Отследить в системе мониторинга
                enhanced_monitoring.track_error(
                    component=error_event.component,
                    error_type=error_event.error_type.value,
                    severity=error_event.priority.value,
                    error_category='exception'
                )
                
                return error_data
            except Exception as e:
                self.logger.error(f"Error processing received error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.rest_app.get("/errors/statistics")
        async def get_error_statistics():
            """Получить статистику по ошибкам."""
            try:
                stats = self.error_detector.get_error_statistics()
                return JSONResponse(content=stats)
            except Exception as e:
                self.logger.error(f"Error getting statistics: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.rest_app.get("/errors/recent")
        async def get_recent_errors(limit: int = 10):
            """Получить последние ошибки."""
            try:
                recent_errors = list(self.error_detector.error_buffer)[-limit:]
                result = []
                for error in recent_errors:
                    result.append({
                        'timestamp': error.timestamp.isoformat(),
                        'error_type': error.error_type.value,
                        'priority': error.priority.value,
                        'component': error.component,
                        'message': error.message,
                        'traceback_info': error.traceback_info,
                        'user_id': error.user_id,
                        'chat_id': error.chat_id,
                        'command': error.command,
                        'extra_data': error.extra_data
                    })
                return JSONResponse(content=result)
            except Exception as e:
                self.logger.error(f"Error getting recent errors: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.rest_app.get("/anomalies/recent")
        async def get_recent_anomalies(limit: int = 10):
            """Получить последние аномалии производительности."""
            try:
                recent_anomalies = list(self.error_detector.performance_buffer)[-limit:]
                result = []
                for anomaly in recent_anomalies:
                    result.append({
                        'timestamp': anomaly.timestamp.isoformat(),
                        'anomaly_type': anomaly.anomaly_type.value,
                        'component': anomaly.component,
                        'metric_name': anomaly.metric_name,
                        'current_value': anomaly.current_value,
                        'threshold_value': anomaly.threshold_value,
                        'severity': anomaly.severity.value,
                        'description': anomaly.description,
                        'extra_data': anomaly.extra_data
                    })
                return JSONResponse(content=result)
            except Exception as e:
                self.logger.error(f"Error getting recent anomalies: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    
    def _setup_websocket_api(self):
        """Настроить WebSocket API для уведомлений в реальном времени."""
        
        async def websocket_handler(request):
            """Обработчик WebSocket соединений."""
            ws = web.WebSocketResponse()
            await ws.prepare(request)
            
            self.active_ws_connections.add(ws)
            self.logger.info(f"WebSocket connection established. Active connections: {len(self.active_ws_connections)}")
            
            try:
                # Отправить приветственное сообщение
                await ws.send_str(json.dumps({
                    'type': 'connection_established',
                    'message': 'WebSocket connection to error notification system established',
                    'timestamp': datetime.utcnow().isoformat()
                }))
                
                # Ожидать сообщения (в реальном приложении можно принимать команды)
                async for msg in ws:
                    if msg.type == WSMsgType.TEXT:
                        try:
                            data = json.loads(msg.data)
                            # Обработать команды от клиента
                            command = data.get('command')
                            if command == 'get_stats':
                                stats = self.error_detector.get_error_statistics()
                                await ws.send_str(json.dumps({
                                    'type': 'stats',
                                    'data': stats,
                                    'timestamp': datetime.utcnow().isoformat()
                                }))
                        except json.JSONDecodeError:
                            await ws.send_str(json.dumps({
                                'type': 'error',
                                'message': 'Invalid JSON received'
                            }))
                    elif msg.type == WSMsgType.ERROR:
                        self.logger.error(f"WebSocket connection closed with exception {ws.exception()}")
                        break
            finally:
                self.active_ws_connections.discard(ws)
                self.logger.info(f"WebSocket connection closed. Active connections: {len(self.active_ws_connections)}")
            
            return ws
        
        # Добавить маршрут для WebSocket
        self.ws_app.router.add_get('/ws', websocket_handler)
        
        # Добавить обработчик для отправки уведомлений
        async def send_notification_to_websockets(notification_data: Dict[str, Any]):
            """Отправить уведомление всем активным WebSocket соединениям."""
            if not self.active_ws_connections:
                return
            
            message = json.dumps(notification_data)
            disconnected = []
            
            for ws in self.active_ws_connections.copy():
                try:
                    await ws.send_str(message)
                except Exception as e:
                    self.logger.error(f"Error sending WebSocket message: {e}")
                    disconnected.append(ws)
            
            # Удалить отключенные соединения
            for ws in disconnected:
                self.active_ws_connections.discard(ws)
        
        # Настроить callback для уведомлений
        self.error_detector.notification_callback = self._create_notification_callback(send_notification_to_websockets)
    
    def _create_notification_callback(self, ws_sender: Callable):
        """Создать callback для отправки уведомлений."""
        async def notification_callback(error_event: ErrorEvent):
            """Отправить уведомление об ошибке через WebSocket."""
            notification_data = {
                'type': 'error_notification',
                'data': {
                    'timestamp': error_event.timestamp.isoformat(),
                    'error_type': error_event.error_type.value,
                    'priority': error_event.priority.value,
                    'component': error_event.component,
                    'message': error_event.message,
                    'user_id': error_event.user_id,
                    'chat_id': error_event.chat_id,
                    'command': error_event.command,
                    'extra_data': error_event.extra_data
                },
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Отправить через WebSocket
            await ws_sender(notification_data)
        
        return notification_callback
    
    def _setup_mcp_server(self):
        """Настроить MCP сервер для взаимодействия с внешними инструментами."""
        
        async def mcp_handler(request):
            """Обработчик запросов к MCP серверу."""
            if request.method == 'POST':
                try:
                    data = await request.json()
                    
                    # Определить тип команды
                    command = data.get('command')
                    
                    if command == 'send_error':
                        # Обработка команды отправки ошибки
                        error_data = data.get('data', {})
                        result = await self._handle_send_error_command(error_data)
                        return web.json_response({'status': 'success', 'result': result})
                    
                    elif command == 'get_statistics':
                        # Обработка команды получения статистики
                        stats = self.error_detector.get_error_statistics()
                        return web.json_response({'status': 'success', 'data': stats})
                    
                    elif command == 'get_recent_errors':
                        # Обработка команды получения последних ошибок
                        limit = data.get('limit', 10)
                        recent_errors = list(self.error_detector.error_buffer)[-limit:]
                        result = []
                        for error in recent_errors:
                            result.append({
                                'timestamp': error.timestamp.isoformat(),
                                'error_type': error.error_type.value,
                                'priority': error.priority.value,
                                'component': error.component,
                                'message': error.message,
                                'traceback_info': error.traceback_info,
                                'user_id': error.user_id,
                                'chat_id': error.chat_id,
                                'command': error.command,
                                'extra_data': error.extra_data
                            })
                        return web.json_response({'status': 'success', 'data': result})
                    
                    elif command == 'reset_statistics':
                        # Обработка команды сброса статистики
                        self.error_detector.reset_statistics()
                        return web.json_response({'status': 'success', 'message': 'Statistics reset'})
                    
                    else:
                        return web.json_response({'status': 'error', 'message': f'Unknown command: {command}'}, status=400)
                
                except Exception as e:
                    self.logger.error(f"MCP handler error: {e}")
                    return web.json_response({'status': 'error', 'message': str(e)}, status=500)
            
            else:
                return web.json_response({'status': 'error', 'message': 'Only POST requests are allowed'}, status=405)
        
        # Добавить маршрут для MCP
        self.mcp_app.router.add_post('/mcp', mcp_handler)
    
    async def _handle_send_error_command(self, error_data: Dict[str, Any]):
        """Обработать команду отправки ошибки через MCP."""
        try:
            # Создать ErrorEvent из полученных данных
            error_event = ErrorEvent(
                timestamp=datetime.fromisoformat(error_data.get('timestamp', datetime.utcnow().isoformat())),
                error_type=ErrorType(error_data.get('error_type', 'unknown')),
                priority=ErrorPriority(error_data.get('priority', 'low')),
                component=error_data.get('component', 'unknown'),
                message=error_data.get('message', ''),
                traceback_info=error_data.get('traceback_info'),
                user_id=error_data.get('user_id'),
                chat_id=error_data.get('chat_id'),
                command=error_data.get('command'),
                extra_data=error_data.get('extra_data')
            )
            
            # Добавить в буфер детектора ошибок
            self.error_detector.error_buffer.append(error_event)
            
            # Обновить статистику
            self.error_detector.component_error_counts[error_event.component][error_event.error_type.value] += 1
            self.error_detector.component_error_timers[error_event.component].append(error_event.timestamp.timestamp())
            
            # Отправить уведомление
            self.error_detector._send_notification(error_event)
            
            # Записать в лог
            self.error_detector._log_error_event(error_event)
            
            # Отследить в системе мониторинга
            enhanced_monitoring.track_error(
                component=error_event.component,
                error_type=error_event.error_type.value,
                severity=error_event.priority.value,
                error_category='exception'
            )
            
            return {'message': 'Error processed successfully', 'error_id': str(error_event.timestamp)}
        except Exception as e:
            self.logger.error(f"Error processing send_error command: {e}")
            raise
    
    async def start_servers(self):
        """Запустить все серверы."""
        # Запустить детектор ошибок
        await self.error_detector.start()
        
        # Запустить REST API сервер
        from uvicorn import Config, Server
        rest_config = Config(
            self.rest_app,
            host="0.0.0.0",
            port=self.rest_api_port,
            log_level="info"
        )
        self.rest_server = Server(rest_config)
        
        # Запустить WebSocket сервер
        ws_runner = web.AppRunner(self.ws_app)
        await ws_runner.setup()
        ws_site = web.TCPSite(ws_runner, '0.0.0.0', self.websocket_port)
        await ws_site.start()
        
        # Запустить MCP сервер
        mcp_runner = web.AppRunner(self.mcp_app)
        await mcp_runner.setup()
        mcp_site = web.TCPSite(mcp_runner, '0.0.0.0', self.mcp_port)
        await mcp_site.start()
        
        self.logger.info(f"Error Notification API started:")
        self.logger.info(f"  REST API: http://0.0.0:{self.rest_api_port}")
        self.logger.info(f"  WebSocket: ws://0.0.0.0:{self.websocket_port}/ws")
        self.logger.info(f"  MCP Server: http://0.0.0.0:{self.mcp_port}/mcp")
        
        # Запустить REST сервер в отдельной задаче
        asyncio.create_task(self.rest_server.serve())
    
    async def stop_servers(self):
        """Остановить все серверы."""
        # Остановить детектор ошибок
        await self.error_detector.stop()
        
        # Закрыть WebSocket соединения
        for ws in self.active_ws_connections.copy():
            await ws.close(code=1001, message='Server shutdown')
        
        # Закрыть REST сервер
        if hasattr(self, 'rest_server'):
            self.rest_server.should_exit = True


# Глобальный экземпляр API
error_notification_api = ErrorNotificationAPI()