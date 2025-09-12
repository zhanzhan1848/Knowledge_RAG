# -*- coding: utf-8 -*-
"""
数据库健康监控模块

提供数据库连接状态监控、健康检查、故障检测、
自动恢复和告警通知功能。

Author: Knowledge RAG System
Date: 2025-01-16
"""

import os
import asyncio
import logging
import time
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import json
from .postgres_config import postgres_manager
from .neo4j_config import neo4j_manager
from .redis_config import redis_manager

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    """健康状态枚举"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

@dataclass
class HealthCheckResult:
    """
    健康检查结果
    """
    service: str
    status: HealthStatus
    response_time: float
    timestamp: datetime
    message: str = ""
    details: Dict[str, Any] = None
    error: Optional[str] = None

@dataclass
class ServiceMetrics:
    """
    服务性能指标
    """
    service: str
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    disk_usage: float = 0.0
    connection_count: int = 0
    active_queries: int = 0
    avg_response_time: float = 0.0
    error_rate: float = 0.0
    uptime: float = 0.0

class DatabaseHealthMonitor:
    """
    数据库健康监控器
    
    提供数据库服务的健康检查、性能监控、故障检测和自动恢复功能。
    """
    
    def __init__(self):
        """初始化健康监控器"""
        self.check_interval = int(os.getenv('HEALTH_CHECK_INTERVAL', 30))  # 检查间隔（秒）
        self.alert_threshold = int(os.getenv('ALERT_THRESHOLD', 3))  # 连续失败次数阈值
        self.recovery_attempts = int(os.getenv('RECOVERY_ATTEMPTS', 3))  # 自动恢复尝试次数
        
        # 健康检查历史
        self.health_history: Dict[str, List[HealthCheckResult]] = {}
        self.failure_counts: Dict[str, int] = {}
        self.last_alerts: Dict[str, datetime] = {}
        
        # 监控任务
        self.monitoring_task: Optional[asyncio.Task] = None
        self.is_monitoring = False
        
        # 告警回调函数
        self.alert_callbacks: List[Callable] = []
        
    async def initialize(self):
        """
        初始化健康监控器
        """
        # 初始化服务健康历史
        services = ['postgresql', 'neo4j', 'redis']
        for service in services:
            self.health_history[service] = []
            self.failure_counts[service] = 0
        
        # 启动监控任务
        await self.start_monitoring()
        
        logger.info("数据库健康监控器初始化完成")
    
    async def start_monitoring(self):
        """
        启动健康监控
        """
        if self.is_monitoring:
            logger.warning("健康监控已在运行")
            return
        
        self.is_monitoring = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("健康监控已启动")
    
    async def stop_monitoring(self):
        """
        停止健康监控
        """
        self.is_monitoring = False
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("健康监控已停止")
    
    async def _monitoring_loop(self):
        """
        监控循环
        """
        while self.is_monitoring:
            try:
                # 执行健康检查
                await self._perform_health_checks()
                
                # 等待下次检查
                await asyncio.sleep(self.check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"监控循环错误: {e}")
                await asyncio.sleep(5)  # 错误后短暂等待
    
    async def _perform_health_checks(self):
        """
        执行所有服务的健康检查
        """
        # 并发执行健康检查
        tasks = [
            self._check_postgresql_health(),
            self._check_neo4j_health(),
            self._check_redis_health()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理检查结果
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"健康检查异常: {result}")
            elif isinstance(result, HealthCheckResult):
                await self._process_health_result(result)
    
    async def _check_postgresql_health(self) -> HealthCheckResult:
        """
        检查PostgreSQL健康状态
        
        Returns:
            HealthCheckResult: 健康检查结果
        """
        start_time = time.time()
        
        try:
            # 检查连接
            is_connected = await postgres_manager.check_connection()
            
            if not is_connected:
                return HealthCheckResult(
                    service="postgresql",
                    status=HealthStatus.CRITICAL,
                    response_time=time.time() - start_time,
                    timestamp=datetime.now(),
                    message="无法连接到PostgreSQL",
                    error="Connection failed"
                )
            
            # 执行简单查询测试
            async with postgres_manager.get_session() as session:
                result = await session.execute(text("SELECT 1 as test"))
                test_result = result.scalar()
                
                if test_result != 1:
                    raise Exception("查询测试失败")
            
            # 获取连接池信息
            connection_info = await postgres_manager.get_connection_info()
            
            response_time = time.time() - start_time
            
            # 判断健康状态
            status = HealthStatus.HEALTHY
            message = "PostgreSQL运行正常"
            
            if response_time > 2.0:
                status = HealthStatus.WARNING
                message = f"PostgreSQL响应较慢: {response_time:.3f}s"
            elif response_time > 5.0:
                status = HealthStatus.CRITICAL
                message = f"PostgreSQL响应严重超时: {response_time:.3f}s"
            
            return HealthCheckResult(
                service="postgresql",
                status=status,
                response_time=response_time,
                timestamp=datetime.now(),
                message=message,
                details=connection_info
            )
            
        except Exception as e:
            return HealthCheckResult(
                service="postgresql",
                status=HealthStatus.CRITICAL,
                response_time=time.time() - start_time,
                timestamp=datetime.now(),
                message=f"PostgreSQL健康检查失败: {str(e)}",
                error=str(e)
            )
    
    async def _check_neo4j_health(self) -> HealthCheckResult:
        """
        检查Neo4j健康状态
        
        Returns:
            HealthCheckResult: 健康检查结果
        """
        start_time = time.time()
        
        try:
            # 检查连接
            is_connected = await neo4j_manager.check_connection()
            
            if not is_connected:
                return HealthCheckResult(
                    service="neo4j",
                    status=HealthStatus.CRITICAL,
                    response_time=time.time() - start_time,
                    timestamp=datetime.now(),
                    message="无法连接到Neo4j",
                    error="Connection failed"
                )
            
            # 执行简单查询测试
            result = await neo4j_manager.execute_query("RETURN 1 as test")
            
            if not result or result[0].get('test') != 1:
                raise Exception("查询测试失败")
            
            response_time = time.time() - start_time
            
            # 判断健康状态
            status = HealthStatus.HEALTHY
            message = "Neo4j运行正常"
            
            if response_time > 3.0:
                status = HealthStatus.WARNING
                message = f"Neo4j响应较慢: {response_time:.3f}s"
            elif response_time > 8.0:
                status = HealthStatus.CRITICAL
                message = f"Neo4j响应严重超时: {response_time:.3f}s"
            
            return HealthCheckResult(
                service="neo4j",
                status=status,
                response_time=response_time,
                timestamp=datetime.now(),
                message=message
            )
            
        except Exception as e:
            return HealthCheckResult(
                service="neo4j",
                status=HealthStatus.CRITICAL,
                response_time=time.time() - start_time,
                timestamp=datetime.now(),
                message=f"Neo4j健康检查失败: {str(e)}",
                error=str(e)
            )
    
    async def _check_redis_health(self) -> HealthCheckResult:
        """
        检查Redis健康状态
        
        Returns:
            HealthCheckResult: 健康检查结果
        """
        start_time = time.time()
        
        try:
            # 检查连接
            is_connected = await redis_manager.check_connection()
            
            if not is_connected:
                return HealthCheckResult(
                    service="redis",
                    status=HealthStatus.CRITICAL,
                    response_time=time.time() - start_time,
                    timestamp=datetime.now(),
                    message="无法连接到Redis",
                    error="Connection failed"
                )
            
            # 执行PING测试
            test_key = f"health_check_{int(time.time())}"
            await redis_manager.set_cache(test_key, "test", ttl=10)
            test_value = await redis_manager.get_cache(test_key)
            
            if test_value != "test":
                raise Exception("读写测试失败")
            
            # 清理测试数据
            await redis_manager.delete_cache(test_key)
            
            response_time = time.time() - start_time
            
            # 获取Redis信息
            redis_info = await redis_manager.get_stats()
            
            # 判断健康状态
            status = HealthStatus.HEALTHY
            message = "Redis运行正常"
            
            if response_time > 1.0:
                status = HealthStatus.WARNING
                message = f"Redis响应较慢: {response_time:.3f}s"
            elif response_time > 3.0:
                status = HealthStatus.CRITICAL
                message = f"Redis响应严重超时: {response_time:.3f}s"
            
            return HealthCheckResult(
                service="redis",
                status=status,
                response_time=response_time,
                timestamp=datetime.now(),
                message=message,
                details=redis_info
            )
            
        except Exception as e:
            return HealthCheckResult(
                service="redis",
                status=HealthStatus.CRITICAL,
                response_time=time.time() - start_time,
                timestamp=datetime.now(),
                message=f"Redis健康检查失败: {str(e)}",
                error=str(e)
            )
    
    async def _process_health_result(self, result: HealthCheckResult):
        """
        处理健康检查结果
        
        Args:
            result: 健康检查结果
        """
        service = result.service
        
        # 添加到历史记录
        if service not in self.health_history:
            self.health_history[service] = []
        
        self.health_history[service].append(result)
        
        # 保留最近100条记录
        if len(self.health_history[service]) > 100:
            self.health_history[service] = self.health_history[service][-100:]
        
        # 更新失败计数
        if result.status in [HealthStatus.CRITICAL, HealthStatus.WARNING]:
            self.failure_counts[service] = self.failure_counts.get(service, 0) + 1
        else:
            self.failure_counts[service] = 0
        
        # 检查是否需要告警
        if self.failure_counts[service] >= self.alert_threshold:
            await self._send_alert(result)
        
        # 尝试自动恢复
        if result.status == HealthStatus.CRITICAL:
            await self._attempt_recovery(service)
        
        # 记录日志
        if result.status == HealthStatus.HEALTHY:
            logger.debug(f"{service} 健康检查通过: {result.message}")
        elif result.status == HealthStatus.WARNING:
            logger.warning(f"{service} 健康检查警告: {result.message}")
        else:
            logger.error(f"{service} 健康检查失败: {result.message}")
    
    async def _send_alert(self, result: HealthCheckResult):
        """
        发送告警通知
        
        Args:
            result: 健康检查结果
        """
        service = result.service
        
        # 检查告警频率限制（避免频繁告警）
        now = datetime.now()
        last_alert = self.last_alerts.get(service)
        
        if last_alert and (now - last_alert).total_seconds() < 300:  # 5分钟内不重复告警
            return
        
        self.last_alerts[service] = now
        
        alert_data = {
            'service': service,
            'status': result.status.value,
            'message': result.message,
            'timestamp': result.timestamp.isoformat(),
            'failure_count': self.failure_counts[service],
            'response_time': result.response_time,
            'error': result.error
        }
        
        # 调用告警回调函数
        for callback in self.alert_callbacks:
            try:
                await callback(alert_data)
            except Exception as e:
                logger.error(f"告警回调执行失败: {e}")
        
        # 记录告警到Redis（如果可用）
        if redis_manager._is_connected:
            try:
                await redis_manager.set_cache(
                    f"alert:{service}:{int(time.time())}",
                    alert_data,
                    ttl=86400,  # 24小时
                    db=redis_manager.metrics_db
                )
            except Exception as e:
                logger.warning(f"记录告警到Redis失败: {e}")
        
        logger.critical(f"数据库服务告警: {service} - {result.message}")
    
    async def _attempt_recovery(self, service: str):
        """
        尝试自动恢复服务
        
        Args:
            service: 服务名称
        """
        logger.info(f"尝试自动恢复服务: {service}")
        
        try:
            if service == "postgresql":
                await postgres_manager.reconnect()
            elif service == "neo4j":
                await neo4j_manager.reconnect()
            elif service == "redis":
                await redis_manager.reconnect()
            
            logger.info(f"服务 {service} 自动恢复尝试完成")
            
        except Exception as e:
            logger.error(f"服务 {service} 自动恢复失败: {e}")
    
    # ==================== 公共API ====================
    
    def add_alert_callback(self, callback: Callable):
        """
        添加告警回调函数
        
        Args:
            callback: 告警回调函数
        """
        self.alert_callbacks.append(callback)
    
    async def get_health_status(self) -> Dict[str, Any]:
        """
        获取所有服务的健康状态
        
        Returns:
            Dict[str, Any]: 健康状态信息
        """
        status = {
            'timestamp': datetime.now().isoformat(),
            'services': {},
            'overall_status': HealthStatus.HEALTHY.value
        }
        
        for service, history in self.health_history.items():
            if not history:
                service_status = {
                    'status': HealthStatus.UNKNOWN.value,
                    'message': '暂无健康检查数据',
                    'last_check': None,
                    'failure_count': 0
                }
            else:
                latest = history[-1]
                service_status = {
                    'status': latest.status.value,
                    'message': latest.message,
                    'last_check': latest.timestamp.isoformat(),
                    'response_time': latest.response_time,
                    'failure_count': self.failure_counts.get(service, 0),
                    'details': latest.details
                }
                
                # 更新整体状态
                if latest.status == HealthStatus.CRITICAL:
                    status['overall_status'] = HealthStatus.CRITICAL.value
                elif latest.status == HealthStatus.WARNING and status['overall_status'] != HealthStatus.CRITICAL.value:
                    status['overall_status'] = HealthStatus.WARNING.value
            
            status['services'][service] = service_status
        
        return status
    
    async def get_service_metrics(self, service: str, hours: int = 24) -> Dict[str, Any]:
        """
        获取服务性能指标
        
        Args:
            service: 服务名称
            hours: 统计时间范围（小时）
            
        Returns:
            Dict[str, Any]: 服务性能指标
        """
        if service not in self.health_history:
            return {'error': f'未找到服务 {service} 的健康检查数据'}
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_checks = [
            check for check in self.health_history[service]
            if check.timestamp > cutoff_time
        ]
        
        if not recent_checks:
            return {'error': f'指定时间范围内没有 {service} 的健康检查数据'}
        
        # 计算指标
        response_times = [check.response_time for check in recent_checks]
        healthy_checks = [check for check in recent_checks if check.status == HealthStatus.HEALTHY]
        
        import statistics
        
        return {
            'service': service,
            'time_range_hours': hours,
            'total_checks': len(recent_checks),
            'healthy_checks': len(healthy_checks),
            'availability': len(healthy_checks) / len(recent_checks) * 100,
            'avg_response_time': statistics.mean(response_times),
            'max_response_time': max(response_times),
            'min_response_time': min(response_times),
            'current_status': recent_checks[-1].status.value,
            'current_failure_count': self.failure_counts.get(service, 0)
        }
    
    async def force_health_check(self, service: str = None) -> Dict[str, Any]:
        """
        强制执行健康检查
        
        Args:
            service: 指定服务名称，None表示检查所有服务
            
        Returns:
            Dict[str, Any]: 健康检查结果
        """
        if service:
            if service == "postgresql":
                result = await self._check_postgresql_health()
            elif service == "neo4j":
                result = await self._check_neo4j_health()
            elif service == "redis":
                result = await self._check_redis_health()
            else:
                return {'error': f'未知服务: {service}'}
            
            await self._process_health_result(result)
            return asdict(result)
        else:
            await self._perform_health_checks()
            return await self.get_health_status()

# 全局健康监控器实例
health_monitor = DatabaseHealthMonitor()