# -*- coding: utf-8 -*-
"""
数据库迁移脚本和版本管理模块

提供数据库schema版本管理、迁移脚本执行、
回滚功能和迁移历史跟踪。

Author: Knowledge RAG System
Date: 2025-01-16
"""

import os
import asyncio
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path
import hashlib
import json
from sqlalchemy import text, MetaData, Table, Column, String, DateTime, Integer, Text
from sqlalchemy.ext.asyncio import AsyncSession
from .postgres_config import postgres_manager

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MigrationManager:
    """
    数据库迁移管理器
    
    管理数据库schema版本、执行迁移脚本和跟踪迁移历史。
    """
    
    def __init__(self, migration_dir: str = "migrations"):
        """初始化迁移管理器"""
        self.migration_dir = Path(migration_dir)
        self.migration_dir.mkdir(exist_ok=True)
        
        # 迁移历史表名
        self.migration_table = "schema_migrations"
        
        # 支持的数据库
        self.databases = [
            'knowledge_rag',
            'auth_db', 
            'document_db',
            'vector_db',
            'knowledge_graph_db'
        ]
    
    async def initialize(self):
        """
        初始化迁移管理器
        """
        # 为每个数据库创建迁移历史表
        for db_name in self.databases:
            await self._create_migration_table(db_name)
        
        logger.info("迁移管理器初始化完成")
    
    async def _create_migration_table(self, database_name: str):
        """
        创建迁移历史表
        
        Args:
            database_name: 数据库名称
        """
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {self.migration_table} (
            id SERIAL PRIMARY KEY,
            version VARCHAR(255) NOT NULL UNIQUE,
            name VARCHAR(255) NOT NULL,
            checksum VARCHAR(64) NOT NULL,
            executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            execution_time INTEGER,
            success BOOLEAN DEFAULT TRUE,
            error_message TEXT
        );
        
        CREATE INDEX IF NOT EXISTS idx_schema_migrations_version 
        ON {self.migration_table}(version);
        """
        
        try:
            async with postgres_manager.get_session(database_name) as session:
                await session.execute(text(create_table_sql))
                await session.commit()
            logger.info(f"迁移历史表创建成功: {database_name}.{self.migration_table}")
        except Exception as e:
            logger.error(f"创建迁移历史表失败 {database_name}: {e}")
            raise
    
    def create_migration(self, name: str, database: str = "knowledge_rag") -> str:
        """
        创建新的迁移文件
        
        Args:
            name: 迁移名称
            database: 目标数据库
            
        Returns:
            str: 迁移文件路径
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        version = f"{timestamp}_{name}"
        
        # 创建数据库特定的迁移目录
        db_migration_dir = self.migration_dir / database
        db_migration_dir.mkdir(exist_ok=True)
        
        migration_file = db_migration_dir / f"{version}.sql"
        
        # 创建迁移文件模板
        template = f"""-- Migration: {name}
-- Database: {database}
-- Created: {datetime.now().isoformat()}
-- Version: {version}

-- ================================
-- UP Migration
-- ================================

-- 在此处添加你的迁移SQL语句
-- 例如：
-- CREATE TABLE example_table (
--     id SERIAL PRIMARY KEY,
--     name VARCHAR(255) NOT NULL,
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );

-- ================================
-- DOWN Migration (回滚)
-- ================================

-- 在此处添加回滚SQL语句
-- 例如：
-- DROP TABLE IF EXISTS example_table;
"""
        
        migration_file.write_text(template, encoding='utf-8')
        logger.info(f"迁移文件创建成功: {migration_file}")
        
        return str(migration_file)
    
    def _calculate_checksum(self, content: str) -> str:
        """
        计算迁移文件校验和
        
        Args:
            content: 文件内容
            
        Returns:
            str: MD5校验和
        """
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def _parse_migration_file(self, file_path: Path) -> Dict[str, str]:
        """
        解析迁移文件
        
        Args:
            file_path: 迁移文件路径
            
        Returns:
            Dict[str, str]: 包含up和down SQL的字典
        """
        content = file_path.read_text(encoding='utf-8')
        
        # 分离UP和DOWN迁移
        up_start = content.find("-- UP Migration")
        down_start = content.find("-- DOWN Migration")
        
        if up_start == -1:
            up_sql = content
            down_sql = ""
        else:
            if down_start == -1:
                up_sql = content[up_start:]
                down_sql = ""
            else:
                up_sql = content[up_start:down_start]
                down_sql = content[down_start:]
        
        # 清理SQL语句（移除注释行）
        def clean_sql(sql: str) -> str:
            lines = sql.split('\n')
            cleaned_lines = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith('--'):
                    cleaned_lines.append(line)
            return '\n'.join(cleaned_lines)
        
        return {
            'up': clean_sql(up_sql),
            'down': clean_sql(down_sql),
            'checksum': self._calculate_checksum(content)
        }
    
    async def get_pending_migrations(self, database_name: str) -> List[Dict[str, Any]]:
        """
        获取待执行的迁移
        
        Args:
            database_name: 数据库名称
            
        Returns:
            List[Dict[str, Any]]: 待执行的迁移列表
        """
        # 获取已执行的迁移
        executed_migrations = await self._get_executed_migrations(database_name)
        executed_versions = {m['version'] for m in executed_migrations}
        
        # 扫描迁移文件
        db_migration_dir = self.migration_dir / database_name
        if not db_migration_dir.exists():
            return []
        
        pending_migrations = []
        
        for migration_file in sorted(db_migration_dir.glob("*.sql")):
            version = migration_file.stem
            
            if version not in executed_versions:
                migration_data = self._parse_migration_file(migration_file)
                pending_migrations.append({
                    'version': version,
                    'name': version.split('_', 1)[1] if '_' in version else version,
                    'file_path': str(migration_file),
                    'checksum': migration_data['checksum'],
                    'up_sql': migration_data['up'],
                    'down_sql': migration_data['down']
                })
        
        return pending_migrations
    
    async def _get_executed_migrations(self, database_name: str) -> List[Dict[str, Any]]:
        """
        获取已执行的迁移
        
        Args:
            database_name: 数据库名称
            
        Returns:
            List[Dict[str, Any]]: 已执行的迁移列表
        """
        try:
            async with postgres_manager.get_session(database_name) as session:
                result = await session.execute(
                    text(f"SELECT * FROM {self.migration_table} ORDER BY executed_at")
                )
                
                migrations = []
                for row in result:
                    migrations.append({
                        'id': row.id,
                        'version': row.version,
                        'name': row.name,
                        'checksum': row.checksum,
                        'executed_at': row.executed_at,
                        'execution_time': row.execution_time,
                        'success': row.success,
                        'error_message': row.error_message
                    })
                
                return migrations
        except Exception as e:
            logger.error(f"获取已执行迁移失败 {database_name}: {e}")
            return []
    
    async def execute_migration(self, migration: Dict[str, Any], database_name: str) -> bool:
        """
        执行单个迁移
        
        Args:
            migration: 迁移信息
            database_name: 数据库名称
            
        Returns:
            bool: 执行是否成功
        """
        start_time = datetime.now()
        
        try:
            async with postgres_manager.get_session(database_name) as session:
                # 执行迁移SQL
                if migration['up_sql'].strip():
                    await session.execute(text(migration['up_sql']))
                
                # 记录迁移历史
                execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
                
                await session.execute(
                    text(f"""
                    INSERT INTO {self.migration_table} 
                    (version, name, checksum, executed_at, execution_time, success)
                    VALUES (:version, :name, :checksum, :executed_at, :execution_time, :success)
                    """),
                    {
                        'version': migration['version'],
                        'name': migration['name'],
                        'checksum': migration['checksum'],
                        'executed_at': start_time,
                        'execution_time': execution_time,
                        'success': True
                    }
                )
                
                await session.commit()
                
            logger.info(f"迁移执行成功: {database_name}.{migration['version']} ({execution_time}ms)")
            return True
            
        except Exception as e:
            # 记录失败的迁移
            try:
                async with postgres_manager.get_session(database_name) as session:
                    execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
                    
                    await session.execute(
                        text(f"""
                        INSERT INTO {self.migration_table} 
                        (version, name, checksum, executed_at, execution_time, success, error_message)
                        VALUES (:version, :name, :checksum, :executed_at, :execution_time, :success, :error_message)
                        """),
                        {
                            'version': migration['version'],
                            'name': migration['name'],
                            'checksum': migration['checksum'],
                            'executed_at': start_time,
                            'execution_time': execution_time,
                            'success': False,
                            'error_message': str(e)
                        }
                    )
                    await session.commit()
            except:
                pass
            
            logger.error(f"迁移执行失败: {database_name}.{migration['version']}: {e}")
            return False
    
    async def migrate(self, database_name: str = None, target_version: str = None) -> Dict[str, Any]:
        """
        执行数据库迁移
        
        Args:
            database_name: 数据库名称，None表示所有数据库
            target_version: 目标版本，None表示最新版本
            
        Returns:
            Dict[str, Any]: 迁移结果
        """
        databases = [database_name] if database_name else self.databases
        results = {}
        
        for db_name in databases:
            logger.info(f"开始迁移数据库: {db_name}")
            
            try:
                pending_migrations = await self.get_pending_migrations(db_name)
                
                if target_version:
                    # 过滤到目标版本
                    pending_migrations = [
                        m for m in pending_migrations 
                        if m['version'] <= target_version
                    ]
                
                executed_count = 0
                failed_count = 0
                
                for migration in pending_migrations:
                    success = await self.execute_migration(migration, db_name)
                    if success:
                        executed_count += 1
                    else:
                        failed_count += 1
                        break  # 遇到失败就停止
                
                results[db_name] = {
                    'success': failed_count == 0,
                    'executed': executed_count,
                    'failed': failed_count,
                    'total_pending': len(pending_migrations)
                }
                
                logger.info(f"数据库迁移完成: {db_name}, 执行: {executed_count}, 失败: {failed_count}")
                
            except Exception as e:
                logger.error(f"数据库迁移失败: {db_name}: {e}")
                results[db_name] = {
                    'success': False,
                    'error': str(e)
                }
        
        return results
    
    async def rollback(self, database_name: str, target_version: str = None) -> bool:
        """
        回滚数据库迁移
        
        Args:
            database_name: 数据库名称
            target_version: 目标版本，None表示回滚最后一个迁移
            
        Returns:
            bool: 回滚是否成功
        """
        try:
            executed_migrations = await self._get_executed_migrations(database_name)
            
            if not executed_migrations:
                logger.info(f"没有可回滚的迁移: {database_name}")
                return True
            
            # 确定要回滚的迁移
            if target_version:
                migrations_to_rollback = [
                    m for m in reversed(executed_migrations)
                    if m['version'] > target_version
                ]
            else:
                # 回滚最后一个迁移
                migrations_to_rollback = [executed_migrations[-1]]
            
            for migration in migrations_to_rollback:
                # 查找迁移文件
                db_migration_dir = self.migration_dir / database_name
                migration_file = db_migration_dir / f"{migration['version']}.sql"
                
                if not migration_file.exists():
                    logger.error(f"迁移文件不存在: {migration_file}")
                    return False
                
                # 解析迁移文件获取DOWN SQL
                migration_data = self._parse_migration_file(migration_file)
                
                if not migration_data['down'].strip():
                    logger.error(f"迁移文件没有DOWN SQL: {migration['version']}")
                    return False
                
                # 执行回滚
                async with postgres_manager.get_session(database_name) as session:
                    await session.execute(text(migration_data['down']))
                    
                    # 删除迁移记录
                    await session.execute(
                        text(f"DELETE FROM {self.migration_table} WHERE version = :version"),
                        {'version': migration['version']}
                    )
                    
                    await session.commit()
                
                logger.info(f"迁移回滚成功: {database_name}.{migration['version']}")
            
            return True
            
        except Exception as e:
            logger.error(f"迁移回滚失败: {database_name}: {e}")
            return False
    
    async def get_migration_status(self, database_name: str = None) -> Dict[str, Any]:
        """
        获取迁移状态
        
        Args:
            database_name: 数据库名称，None表示所有数据库
            
        Returns:
            Dict[str, Any]: 迁移状态信息
        """
        databases = [database_name] if database_name else self.databases
        status = {}
        
        for db_name in databases:
            try:
                executed_migrations = await self._get_executed_migrations(db_name)
                pending_migrations = await self.get_pending_migrations(db_name)
                
                status[db_name] = {
                    'executed_count': len(executed_migrations),
                    'pending_count': len(pending_migrations),
                    'last_migration': executed_migrations[-1]['version'] if executed_migrations else None,
                    'last_executed_at': executed_migrations[-1]['executed_at'].isoformat() if executed_migrations else None,
                    'pending_migrations': [m['version'] for m in pending_migrations]
                }
            except Exception as e:
                status[db_name] = {
                    'error': str(e)
                }
        
        return status

# 全局迁移管理器实例
migration_manager = MigrationManager(
    migration_dir=os.path.join(os.path.dirname(__file__), "migrations")
)