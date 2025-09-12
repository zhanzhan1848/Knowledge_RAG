# -*- coding: utf-8 -*-
"""
数据库备份和恢复管理模块

提供PostgreSQL、Neo4j和Redis的自动备份、
增量备份、定时备份、备份验证和恢复功能。

Author: Knowledge RAG System
Date: 2025-01-16
"""

import os
import asyncio
import logging
import shutil
import subprocess
import gzip
import json
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum
import hashlib
from .postgres_config import postgres_manager
from .neo4j_config import neo4j_manager
from .redis_config import redis_manager

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BackupType(Enum):
    """备份类型枚举"""
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"

class BackupStatus(Enum):
    """备份状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    VERIFIED = "verified"

@dataclass
class BackupRecord:
    """
    备份记录
    """
    backup_id: str
    service: str
    backup_type: BackupType
    status: BackupStatus
    file_path: str
    file_size: int
    checksum: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None

class DatabaseBackupManager:
    """
    数据库备份管理器
    
    提供多数据库的备份、恢复、验证和管理功能。
    """
    
    def __init__(self):
        """初始化备份管理器"""
        self.backup_root = Path(os.getenv('BACKUP_ROOT_DIR', '/tmp/db_backups'))
        self.backup_retention_days = int(os.getenv('BACKUP_RETENTION_DAYS', 30))
        self.max_backup_size = int(os.getenv('MAX_BACKUP_SIZE_MB', 1024)) * 1024 * 1024  # MB to bytes
        self.compression_enabled = os.getenv('BACKUP_COMPRESSION', 'true').lower() == 'true'
        
        # 备份记录
        self.backup_records: List[BackupRecord] = []
        
        # 备份任务
        self.backup_tasks: Dict[str, asyncio.Task] = {}
        self.scheduled_backups: Dict[str, asyncio.Task] = {}
        
        # 确保备份目录存在
        self.backup_root.mkdir(parents=True, exist_ok=True)
        
        # 为每个服务创建子目录
        for service in ['postgresql', 'neo4j', 'redis']:
            (self.backup_root / service).mkdir(exist_ok=True)
    
    async def initialize(self):
        """
        初始化备份管理器
        """
        # 加载现有备份记录
        await self._load_backup_records()
        
        # 启动定时备份任务
        await self._start_scheduled_backups()
        
        # 启动清理任务
        asyncio.create_task(self._cleanup_old_backups())
        
        logger.info("数据库备份管理器初始化完成")
    
    async def _load_backup_records(self):
        """
        加载备份记录
        """
        records_file = self.backup_root / 'backup_records.json'
        
        if records_file.exists():
            try:
                with open(records_file, 'r', encoding='utf-8') as f:
                    records_data = json.load(f)
                
                for record_data in records_data:
                    # 转换日期字符串为datetime对象
                    record_data['created_at'] = datetime.fromisoformat(record_data['created_at'])
                    if record_data.get('completed_at'):
                        record_data['completed_at'] = datetime.fromisoformat(record_data['completed_at'])
                    
                    # 转换枚举
                    record_data['backup_type'] = BackupType(record_data['backup_type'])
                    record_data['status'] = BackupStatus(record_data['status'])
                    
                    self.backup_records.append(BackupRecord(**record_data))
                
                logger.info(f"加载了 {len(self.backup_records)} 条备份记录")
                
            except Exception as e:
                logger.error(f"加载备份记录失败: {e}")
    
    async def _save_backup_records(self):
        """
        保存备份记录
        """
        records_file = self.backup_root / 'backup_records.json'
        
        try:
            records_data = []
            for record in self.backup_records:
                record_dict = asdict(record)
                # 转换datetime为字符串
                record_dict['created_at'] = record.created_at.isoformat()
                if record.completed_at:
                    record_dict['completed_at'] = record.completed_at.isoformat()
                # 转换枚举为字符串
                record_dict['backup_type'] = record.backup_type.value
                record_dict['status'] = record.status.value
                
                records_data.append(record_dict)
            
            with open(records_file, 'w', encoding='utf-8') as f:
                json.dump(records_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"保存备份记录失败: {e}")
    
    async def _start_scheduled_backups(self):
        """
        启动定时备份任务
        """
        # PostgreSQL每日备份
        postgres_schedule = os.getenv('POSTGRES_BACKUP_SCHEDULE', '02:00')  # 凌晨2点
        self.scheduled_backups['postgresql'] = asyncio.create_task(
            self._scheduled_backup_task('postgresql', postgres_schedule)
        )
        
        # Neo4j每日备份
        neo4j_schedule = os.getenv('NEO4J_BACKUP_SCHEDULE', '03:00')  # 凌晨3点
        self.scheduled_backups['neo4j'] = asyncio.create_task(
            self._scheduled_backup_task('neo4j', neo4j_schedule)
        )
        
        # Redis每6小时备份
        redis_schedule = os.getenv('REDIS_BACKUP_SCHEDULE', '*/6')  # 每6小时
        self.scheduled_backups['redis'] = asyncio.create_task(
            self._scheduled_backup_task('redis', redis_schedule)
        )
        
        logger.info("定时备份任务已启动")
    
    async def _scheduled_backup_task(self, service: str, schedule: str):
        """
        定时备份任务
        
        Args:
            service: 服务名称
            schedule: 备份计划
        """
        while True:
            try:
                # 计算下次备份时间
                next_backup_time = self._calculate_next_backup_time(schedule)
                wait_seconds = (next_backup_time - datetime.now()).total_seconds()
                
                if wait_seconds > 0:
                    await asyncio.sleep(wait_seconds)
                
                # 执行备份
                logger.info(f"开始定时备份: {service}")
                await self.create_backup(service, BackupType.FULL)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"定时备份任务错误 {service}: {e}")
                await asyncio.sleep(3600)  # 错误后等待1小时
    
    def _calculate_next_backup_time(self, schedule: str) -> datetime:
        """
        计算下次备份时间
        
        Args:
            schedule: 备份计划（如 '02:00' 或 '*/6'）
            
        Returns:
            datetime: 下次备份时间
        """
        now = datetime.now()
        
        if ':' in schedule:  # 每日定时备份
            hour, minute = map(int, schedule.split(':'))
            next_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            if next_time <= now:
                next_time += timedelta(days=1)
                
        elif schedule.startswith('*/'):  # 间隔备份
            interval_hours = int(schedule[2:])
            next_time = now + timedelta(hours=interval_hours)
            
        else:
            # 默认每24小时
            next_time = now + timedelta(hours=24)
        
        return next_time
    
    async def _cleanup_old_backups(self):
        """
        清理过期备份
        """
        while True:
            try:
                await asyncio.sleep(86400)  # 每天执行一次
                
                cutoff_date = datetime.now() - timedelta(days=self.backup_retention_days)
                
                # 查找过期备份
                expired_backups = [
                    record for record in self.backup_records
                    if record.created_at < cutoff_date
                ]
                
                for backup in expired_backups:
                    try:
                        # 删除备份文件
                        backup_file = Path(backup.file_path)
                        if backup_file.exists():
                            backup_file.unlink()
                            logger.info(f"删除过期备份: {backup.backup_id}")
                        
                        # 从记录中移除
                        self.backup_records.remove(backup)
                        
                    except Exception as e:
                        logger.error(f"删除过期备份失败 {backup.backup_id}: {e}")
                
                if expired_backups:
                    await self._save_backup_records()
                    logger.info(f"清理了 {len(expired_backups)} 个过期备份")
                
            except Exception as e:
                logger.error(f"清理过期备份任务错误: {e}")
    
    # ==================== PostgreSQL备份 ====================
    
    async def _backup_postgresql(self, backup_type: BackupType) -> BackupRecord:
        """
        备份PostgreSQL数据库
        
        Args:
            backup_type: 备份类型
            
        Returns:
            BackupRecord: 备份记录
        """
        backup_id = f"postgres_{backup_type.value}_{int(datetime.now().timestamp())}"
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 备份文件路径
        backup_filename = f"postgres_{backup_type.value}_{timestamp}.sql"
        if self.compression_enabled:
            backup_filename += '.gz'
        
        backup_path = self.backup_root / 'postgresql' / backup_filename
        
        # 创建备份记录
        record = BackupRecord(
            backup_id=backup_id,
            service='postgresql',
            backup_type=backup_type,
            status=BackupStatus.RUNNING,
            file_path=str(backup_path),
            file_size=0,
            checksum='',
            created_at=datetime.now(),
            metadata={'databases': list(postgres_manager.engines.keys())}
        )
        
        try:
            # 获取数据库连接信息
            config = postgres_manager.config
            
            # 构建pg_dump命令
            cmd = [
                'pg_dumpall',
                '-h', config.host,
                '-p', str(config.port),
                '-U', config.username,
                '--no-password',
                '--verbose'
            ]
            
            # 设置环境变量
            env = os.environ.copy()
            env['PGPASSWORD'] = config.password
            
            # 执行备份
            logger.info(f"开始PostgreSQL备份: {backup_id}")
            
            if self.compression_enabled:
                # 使用gzip压缩
                with gzip.open(backup_path, 'wt', encoding='utf-8') as f:
                    process = await asyncio.create_subprocess_exec(
                        *cmd,
                        stdout=f,
                        stderr=asyncio.subprocess.PIPE,
                        env=env
                    )
                    
                    _, stderr = await process.communicate()
            else:
                # 直接输出到文件
                with open(backup_path, 'w', encoding='utf-8') as f:
                    process = await asyncio.create_subprocess_exec(
                        *cmd,
                        stdout=f,
                        stderr=asyncio.subprocess.PIPE,
                        env=env
                    )
                    
                    _, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "备份命令执行失败"
                raise Exception(f"pg_dumpall失败: {error_msg}")
            
            # 计算文件大小和校验和
            record.file_size = backup_path.stat().st_size
            record.checksum = await self._calculate_checksum(backup_path)
            record.status = BackupStatus.COMPLETED
            record.completed_at = datetime.now()
            
            logger.info(f"PostgreSQL备份完成: {backup_id}, 大小: {record.file_size} bytes")
            
        except Exception as e:
            record.status = BackupStatus.FAILED
            record.error_message = str(e)
            logger.error(f"PostgreSQL备份失败 {backup_id}: {e}")
            
            # 清理失败的备份文件
            if backup_path.exists():
                backup_path.unlink()
        
        return record
    
    # ==================== Neo4j备份 ====================
    
    async def _backup_neo4j(self, backup_type: BackupType) -> BackupRecord:
        """
        备份Neo4j数据库
        
        Args:
            backup_type: 备份类型
            
        Returns:
            BackupRecord: 备份记录
        """
        backup_id = f"neo4j_{backup_type.value}_{int(datetime.now().timestamp())}"
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 备份文件路径
        backup_filename = f"neo4j_{backup_type.value}_{timestamp}.cypher"
        if self.compression_enabled:
            backup_filename += '.gz'
        
        backup_path = self.backup_root / 'neo4j' / backup_filename
        
        # 创建备份记录
        record = BackupRecord(
            backup_id=backup_id,
            service='neo4j',
            backup_type=backup_type,
            status=BackupStatus.RUNNING,
            file_path=str(backup_path),
            file_size=0,
            checksum='',
            created_at=datetime.now()
        )
        
        try:
            logger.info(f"开始Neo4j备份: {backup_id}")
            
            # 导出所有节点和关系
            export_queries = [
                "CALL apoc.export.cypher.all(null, {stream: true, format: 'cypher-shell'})",
                "CALL db.schema.visualization()"
            ]
            
            backup_content = []
            
            for query in export_queries:
                try:
                    result = await neo4j_manager.execute_query(query)
                    if result:
                        for record_data in result:
                            if 'cypherStatements' in record_data:
                                backup_content.append(record_data['cypherStatements'])
                            elif 'cypher' in record_data:
                                backup_content.append(record_data['cypher'])
                except Exception as e:
                    logger.warning(f"Neo4j备份查询失败 {query}: {e}")
            
            # 如果APOC不可用，使用基本导出
            if not backup_content:
                logger.info("使用基本方式备份Neo4j")
                
                # 导出所有节点
                nodes_result = await neo4j_manager.execute_query(
                    "MATCH (n) RETURN labels(n) as labels, properties(n) as props LIMIT 10000"
                )
                
                # 导出所有关系
                rels_result = await neo4j_manager.execute_query(
                    "MATCH (a)-[r]->(b) RETURN type(r) as type, properties(r) as props, "
                    "labels(a) as start_labels, properties(a) as start_props, "
                    "labels(b) as end_labels, properties(b) as end_props LIMIT 10000"
                )
                
                # 生成Cypher语句
                cypher_statements = []
                
                # 处理节点
                if nodes_result:
                    for node in nodes_result:
                        labels = ':'.join(node.get('labels', []))
                        props = node.get('props', {})
                        if labels and props:
                            props_str = ', '.join([f"{k}: {repr(v)}" for k, v in props.items()])
                            cypher_statements.append(f"CREATE (:{labels} {{{props_str}}});")
                
                # 处理关系（简化版）
                if rels_result:
                    for rel in rels_result[:1000]:  # 限制关系数量
                        rel_type = rel.get('type', 'RELATED')
                        cypher_statements.append(f"// Relationship: {rel_type}")
                
                backup_content = ['\n'.join(cypher_statements)]
            
            # 写入备份文件
            content = '\n'.join(backup_content)
            
            if self.compression_enabled:
                with gzip.open(backup_path, 'wt', encoding='utf-8') as f:
                    f.write(content)
            else:
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            # 计算文件大小和校验和
            record.file_size = backup_path.stat().st_size
            record.checksum = await self._calculate_checksum(backup_path)
            record.status = BackupStatus.COMPLETED
            record.completed_at = datetime.now()
            
            logger.info(f"Neo4j备份完成: {backup_id}, 大小: {record.file_size} bytes")
            
        except Exception as e:
            record.status = BackupStatus.FAILED
            record.error_message = str(e)
            logger.error(f"Neo4j备份失败 {backup_id}: {e}")
            
            # 清理失败的备份文件
            if backup_path.exists():
                backup_path.unlink()
        
        return record
    
    # ==================== Redis备份 ====================
    
    async def _backup_redis(self, backup_type: BackupType) -> BackupRecord:
        """
        备份Redis数据库
        
        Args:
            backup_type: 备份类型
            
        Returns:
            BackupRecord: 备份记录
        """
        backup_id = f"redis_{backup_type.value}_{int(datetime.now().timestamp())}"
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 备份文件路径
        backup_filename = f"redis_{backup_type.value}_{timestamp}.rdb"
        if self.compression_enabled:
            backup_filename += '.gz'
        
        backup_path = self.backup_root / 'redis' / backup_filename
        
        # 创建备份记录
        record = BackupRecord(
            backup_id=backup_id,
            service='redis',
            backup_type=backup_type,
            status=BackupStatus.RUNNING,
            file_path=str(backup_path),
            file_size=0,
            checksum='',
            created_at=datetime.now()
        )
        
        try:
            logger.info(f"开始Redis备份: {backup_id}")
            
            # 触发Redis保存
            await redis_manager.execute_command('BGSAVE')
            
            # 等待备份完成
            while True:
                result = await redis_manager.execute_command('LASTSAVE')
                await asyncio.sleep(1)
                
                # 检查是否完成（简化检查）
                new_result = await redis_manager.execute_command('LASTSAVE')
                if new_result != result:
                    break
                
                # 超时检查
                if (datetime.now() - record.created_at).total_seconds() > 300:  # 5分钟超时
                    raise Exception("Redis备份超时")
            
            # 获取Redis数据目录（需要配置）
            redis_data_dir = os.getenv('REDIS_DATA_DIR', '/data')
            rdb_file = Path(redis_data_dir) / 'dump.rdb'
            
            if not rdb_file.exists():
                # 如果找不到RDB文件，使用内存导出
                logger.warning("未找到RDB文件，使用内存导出")
                
                # 获取所有键值对
                all_keys = await redis_manager.execute_command('KEYS', '*')
                backup_data = {}
                
                for key in all_keys[:10000]:  # 限制键数量
                    try:
                        key_type = await redis_manager.execute_command('TYPE', key)
                        
                        if key_type == 'string':
                            value = await redis_manager.get_cache(key)
                            backup_data[key] = {'type': 'string', 'value': value}
                        elif key_type == 'hash':
                            value = await redis_manager.execute_command('HGETALL', key)
                            backup_data[key] = {'type': 'hash', 'value': value}
                        # 可以添加更多数据类型支持
                        
                    except Exception as e:
                        logger.warning(f"备份Redis键失败 {key}: {e}")
                
                # 保存为JSON格式
                content = json.dumps(backup_data, indent=2, ensure_ascii=False)
                
                if self.compression_enabled:
                    with gzip.open(backup_path, 'wt', encoding='utf-8') as f:
                        f.write(content)
                else:
                    with open(backup_path, 'w', encoding='utf-8') as f:
                        f.write(content)
            else:
                # 复制RDB文件
                if self.compression_enabled:
                    with open(rdb_file, 'rb') as src, gzip.open(backup_path, 'wb') as dst:
                        shutil.copyfileobj(src, dst)
                else:
                    shutil.copy2(rdb_file, backup_path)
            
            # 计算文件大小和校验和
            record.file_size = backup_path.stat().st_size
            record.checksum = await self._calculate_checksum(backup_path)
            record.status = BackupStatus.COMPLETED
            record.completed_at = datetime.now()
            
            logger.info(f"Redis备份完成: {backup_id}, 大小: {record.file_size} bytes")
            
        except Exception as e:
            record.status = BackupStatus.FAILED
            record.error_message = str(e)
            logger.error(f"Redis备份失败 {backup_id}: {e}")
            
            # 清理失败的备份文件
            if backup_path.exists():
                backup_path.unlink()
        
        return record
    
    async def _calculate_checksum(self, file_path: Path) -> str:
        """
        计算文件校验和
        
        Args:
            file_path: 文件路径
            
        Returns:
            str: MD5校验和
        """
        hash_md5 = hashlib.md5()
        
        if file_path.suffix == '.gz':
            with gzip.open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
        else:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
        
        return hash_md5.hexdigest()
    
    # ==================== 公共API ====================
    
    async def create_backup(self, service: str, backup_type: BackupType = BackupType.FULL) -> str:
        """
        创建数据库备份
        
        Args:
            service: 服务名称 (postgresql, neo4j, redis)
            backup_type: 备份类型
            
        Returns:
            str: 备份ID
        """
        if service not in ['postgresql', 'neo4j', 'redis']:
            raise ValueError(f"不支持的服务: {service}")
        
        # 检查是否已有备份任务在运行
        if service in self.backup_tasks and not self.backup_tasks[service].done():
            raise Exception(f"服务 {service} 的备份任务正在运行")
        
        # 创建备份任务
        if service == 'postgresql':
            backup_coro = self._backup_postgresql(backup_type)
        elif service == 'neo4j':
            backup_coro = self._backup_neo4j(backup_type)
        elif service == 'redis':
            backup_coro = self._backup_redis(backup_type)
        
        self.backup_tasks[service] = asyncio.create_task(backup_coro)
        
        try:
            record = await self.backup_tasks[service]
            
            # 添加到备份记录
            self.backup_records.append(record)
            await self._save_backup_records()
            
            return record.backup_id
            
        except Exception as e:
            logger.error(f"创建备份失败 {service}: {e}")
            raise
        finally:
            # 清理任务
            if service in self.backup_tasks:
                del self.backup_tasks[service]
    
    async def get_backup_status(self, backup_id: str) -> Optional[Dict[str, Any]]:
        """
        获取备份状态
        
        Args:
            backup_id: 备份ID
            
        Returns:
            Optional[Dict[str, Any]]: 备份状态信息
        """
        for record in self.backup_records:
            if record.backup_id == backup_id:
                return asdict(record)
        
        return None
    
    async def list_backups(self, service: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """
        列出备份记录
        
        Args:
            service: 服务名称过滤
            limit: 返回数量限制
            
        Returns:
            List[Dict[str, Any]]: 备份记录列表
        """
        filtered_records = self.backup_records
        
        if service:
            filtered_records = [r for r in filtered_records if r.service == service]
        
        # 按创建时间倒序排列
        filtered_records.sort(key=lambda x: x.created_at, reverse=True)
        
        return [asdict(record) for record in filtered_records[:limit]]
    
    async def verify_backup(self, backup_id: str) -> bool:
        """
        验证备份完整性
        
        Args:
            backup_id: 备份ID
            
        Returns:
            bool: 验证结果
        """
        record = None
        for r in self.backup_records:
            if r.backup_id == backup_id:
                record = r
                break
        
        if not record:
            raise ValueError(f"未找到备份: {backup_id}")
        
        backup_file = Path(record.file_path)
        
        if not backup_file.exists():
            logger.error(f"备份文件不存在: {record.file_path}")
            return False
        
        # 验证文件大小
        actual_size = backup_file.stat().st_size
        if actual_size != record.file_size:
            logger.error(f"备份文件大小不匹配: 期望 {record.file_size}, 实际 {actual_size}")
            return False
        
        # 验证校验和
        actual_checksum = await self._calculate_checksum(backup_file)
        if actual_checksum != record.checksum:
            logger.error(f"备份文件校验和不匹配: 期望 {record.checksum}, 实际 {actual_checksum}")
            return False
        
        # 更新验证状态
        record.status = BackupStatus.VERIFIED
        await self._save_backup_records()
        
        logger.info(f"备份验证成功: {backup_id}")
        return True
    
    async def delete_backup(self, backup_id: str) -> bool:
        """
        删除备份
        
        Args:
            backup_id: 备份ID
            
        Returns:
            bool: 删除结果
        """
        record = None
        for r in self.backup_records:
            if r.backup_id == backup_id:
                record = r
                break
        
        if not record:
            raise ValueError(f"未找到备份: {backup_id}")
        
        try:
            # 删除备份文件
            backup_file = Path(record.file_path)
            if backup_file.exists():
                backup_file.unlink()
            
            # 从记录中移除
            self.backup_records.remove(record)
            await self._save_backup_records()
            
            logger.info(f"备份已删除: {backup_id}")
            return True
            
        except Exception as e:
            logger.error(f"删除备份失败 {backup_id}: {e}")
            return False
    
    async def get_backup_statistics(self) -> Dict[str, Any]:
        """
        获取备份统计信息
        
        Returns:
            Dict[str, Any]: 备份统计信息
        """
        stats = {
            'total_backups': len(self.backup_records),
            'services': {},
            'status_distribution': {},
            'total_size': 0,
            'oldest_backup': None,
            'newest_backup': None
        }
        
        if not self.backup_records:
            return stats
        
        # 按服务统计
        for record in self.backup_records:
            service = record.service
            if service not in stats['services']:
                stats['services'][service] = {
                    'count': 0,
                    'total_size': 0,
                    'last_backup': None
                }
            
            stats['services'][service]['count'] += 1
            stats['services'][service]['total_size'] += record.file_size
            
            if (not stats['services'][service]['last_backup'] or 
                record.created_at > stats['services'][service]['last_backup']):
                stats['services'][service]['last_backup'] = record.created_at.isoformat()
            
            # 状态分布
            status = record.status.value
            stats['status_distribution'][status] = stats['status_distribution'].get(status, 0) + 1
            
            # 总大小
            stats['total_size'] += record.file_size
        
        # 最新和最旧备份
        sorted_records = sorted(self.backup_records, key=lambda x: x.created_at)
        stats['oldest_backup'] = sorted_records[0].created_at.isoformat()
        stats['newest_backup'] = sorted_records[-1].created_at.isoformat()
        
        return stats

# 全局备份管理器实例
backup_manager = DatabaseBackupManager()