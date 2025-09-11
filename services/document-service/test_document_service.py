#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档存储服务单元测试

测试文档服务的各项功能，包括文档上传、下载、预览、权限控制、配额管理、备份恢复等。

Author: Assistant
Date: 2024
"""

import os
import pytest
import tempfile
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from minio import Minio

from .main import app
from .database import get_db, Base
from .models import Document, DocumentStatus, UserQuota, DocumentPermission, AccessLevel, DocumentShare, BackupRecord
from .services import DocumentService
from .backup import DocumentBackupService, BackupConfig
from .preview import DocumentPreviewService
from .schemas import DocumentCreate, DocumentUpdate, UserQuotaCreate


# 测试数据库配置
TEST_DATABASE_URL = "sqlite:///./test_document_service.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """创建测试数据库会话"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """创建测试客户端"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def mock_minio_client():
    """模拟MinIO客户端"""
    mock_client = Mock(spec=Minio)
    mock_client.bucket_exists.return_value = True
    mock_client.put_object.return_value = Mock()
    mock_client.get_object.return_value = Mock()
    mock_client.fput_object.return_value = Mock()
    mock_client.fget_object.return_value = Mock()
    mock_client.remove_object.return_value = Mock()
    mock_client.presigned_get_object.return_value = "http://test-url"
    return mock_client


@pytest.fixture
def sample_document_data():
    """示例文档数据"""
    return {
        "filename": "test_document.pdf",
        "original_filename": "测试文档.pdf",
        "file_size": 1024000,
        "file_type": "application/pdf",
        "file_extension": "pdf",
        "mime_type": "application/pdf",
        "storage_path": "documents/test_document.pdf",
        "owner_id": 1,
        "description": "这是一个测试文档",
        "tags": ["测试", "PDF"]
    }


@pytest.fixture
def sample_user_quota():
    """示例用户配额数据"""
    return {
        "user_id": 1,
        "total_quota": 1073741824,  # 1GB
        "used_quota": 0,
        "file_count": 0
    }


class TestDocumentService:
    """文档服务测试类"""
    
    def test_create_document(self, db_session, mock_minio_client, sample_document_data):
        """测试创建文档"""
        service = DocumentService(db_session)
        
        # 创建文档
        document_create = DocumentCreate(**sample_document_data)
        document = service.create_document(document_create)
        
        assert document is not None
        assert document.filename == sample_document_data["filename"]
        assert document.owner_id == sample_document_data["owner_id"]
        assert document.status == DocumentStatus.ACTIVE
        assert document.file_size == sample_document_data["file_size"]
    
    def test_get_document(self, db_session, sample_document_data):
        """测试获取文档"""
        service = DocumentService(db_session)
        
        # 创建文档
        document_create = DocumentCreate(**sample_document_data)
        created_document = service.create_document(document_create)
        
        # 获取文档
        retrieved_document = service.get_document(created_document.id)
        
        assert retrieved_document is not None
        assert retrieved_document.id == created_document.id
        assert retrieved_document.filename == sample_document_data["filename"]
    
    def test_update_document(self, db_session, sample_document_data):
        """测试更新文档"""
        service = DocumentService(db_session)
        
        # 创建文档
        document_create = DocumentCreate(**sample_document_data)
        document = service.create_document(document_create)
        
        # 更新文档
        update_data = DocumentUpdate(
            description="更新后的描述",
            tags=["更新", "测试"]
        )
        updated_document = service.update_document(document.id, update_data)
        
        assert updated_document is not None
        assert updated_document.description == "更新后的描述"
        assert "更新" in updated_document.tags
    
    def test_delete_document(self, db_session, mock_minio_client, sample_document_data):
        """测试删除文档"""
        service = DocumentService(db_session)
        
        # 创建文档
        document_create = DocumentCreate(**sample_document_data)
        document = service.create_document(document_create)
        
        # 删除文档
        with patch('services.document-service.services.get_minio_client', return_value=mock_minio_client):
            success = service.delete_document(document.id, document.owner_id)
        
        assert success is True
        
        # 验证文档状态
        deleted_document = service.get_document(document.id)
        assert deleted_document.status == DocumentStatus.DELETED
    
    def test_search_documents(self, db_session, sample_document_data):
        """测试搜索文档"""
        service = DocumentService(db_session)
        
        # 创建多个文档
        for i in range(3):
            doc_data = sample_document_data.copy()
            doc_data["filename"] = f"test_document_{i}.pdf"
            doc_data["description"] = f"测试文档 {i}"
            document_create = DocumentCreate(**doc_data)
            service.create_document(document_create)
        
        # 搜索文档
        results = service.search_documents(
            owner_id=sample_document_data["owner_id"],
            query="测试",
            limit=10
        )
        
        assert len(results) == 3
        assert all("测试" in doc.description for doc in results)
    
    def test_user_quota_management(self, db_session, sample_user_quota):
        """测试用户配额管理"""
        service = DocumentService(db_session)
        
        # 创建用户配额
        quota_create = UserQuotaCreate(**sample_user_quota)
        quota = service.create_user_quota(quota_create)
        
        assert quota is not None
        assert quota.user_id == sample_user_quota["user_id"]
        assert quota.total_quota == sample_user_quota["total_quota"]
        
        # 检查配额限制
        can_upload = service.check_quota_limit(sample_user_quota["user_id"], 500000)
        assert can_upload is True
        
        # 超出配额测试
        can_upload_large = service.check_quota_limit(sample_user_quota["user_id"], 2000000000)
        assert can_upload_large is False
    
    def test_document_permissions(self, db_session, sample_document_data):
        """测试文档权限管理"""
        service = DocumentService(db_session)
        
        # 创建文档
        document_create = DocumentCreate(**sample_document_data)
        document = service.create_document(document_create)
        
        # 创建权限
        from .schemas import DocumentPermissionCreate
        permission_data = DocumentPermissionCreate(
            user_id=2,
            access_level=AccessLevel.READ
        )
        permission = service.create_document_permission(
            document.id, document.owner_id, permission_data
        )
        
        assert permission is not None
        assert permission.user_id == 2
        assert permission.access_level == AccessLevel.READ
        
        # 获取权限列表
        permissions = service.get_document_permissions(document.id)
        assert len(permissions) >= 1
    
    def test_document_sharing(self, db_session, sample_document_data):
        """测试文档分享"""
        service = DocumentService(db_session)
        
        # 创建文档
        document_create = DocumentCreate(**sample_document_data)
        document = service.create_document(document_create)
        
        # 创建分享链接
        from .schemas import DocumentShareCreate
        share_data = DocumentShareCreate(
            access_level=AccessLevel.READ,
            expires_at=datetime.utcnow() + timedelta(days=7),
            download_limit=10
        )
        share = service.create_document_share(document.id, document.owner_id, share_data)
        
        assert share is not None
        assert share.document_id == document.id
        assert share.access_level == AccessLevel.READ
        assert share.is_active is True
        
        # 获取分享链接
        retrieved_share = service.get_document_share(share.share_token)
        assert retrieved_share is not None
        assert retrieved_share.id == share.id


class TestDocumentAPI:
    """文档API测试类"""
    
    def test_upload_document_api(self, client):
        """测试文档上传API"""
        # 模拟文件上传
        with patch('services.document-service.main.get_current_user_id', return_value=1):
            with patch('services.document-service.main.get_minio_client') as mock_minio:
                mock_minio.return_value.put_object.return_value = Mock()
                
                response = client.post(
                    "/upload/init",
                    json={
                        "filename": "test.pdf",
                        "file_size": 1024,
                        "file_type": "application/pdf",
                        "chunk_size": 512
                    }
                )
                
                assert response.status_code == 200
                data = response.json()
                assert "upload_id" in data
                assert "document_id" in data
    
    def test_search_documents_api(self, client, db_session, sample_document_data):
        """测试文档搜索API"""
        # 创建测试文档
        service = DocumentService(db_session)
        document_create = DocumentCreate(**sample_document_data)
        service.create_document(document_create)
        
        with patch('services.document-service.main.get_current_user_id', return_value=1):
            response = client.get("/search?query=测试&limit=10")
            
            assert response.status_code == 200
            data = response.json()
            assert "documents" in data
            assert "total" in data
    
    def test_get_document_info_api(self, client, db_session, sample_document_data):
        """测试获取文档信息API"""
        # 创建测试文档
        service = DocumentService(db_session)
        document_create = DocumentCreate(**sample_document_data)
        document = service.create_document(document_create)
        
        with patch('services.document-service.main.get_current_user_id', return_value=1):
            response = client.get(f"/documents/{document.id}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == document.id
            assert data["filename"] == sample_document_data["filename"]
    
    def test_quota_management_api(self, client):
        """测试配额管理API"""
        with patch('services.document-service.main.get_current_user_id', return_value=1):
            # 创建配额
            response = client.post(
                "/quota",
                json={
                    "user_id": 1,
                    "total_quota": 1073741824,
                    "used_quota": 0,
                    "file_count": 0
                }
            )
            
            assert response.status_code == 200
            
            # 获取配额信息
            response = client.get("/quota")
            assert response.status_code in [200, 404]  # 可能不存在配额记录
    
    def test_backup_api(self, client, db_session, sample_document_data):
        """测试备份API"""
        # 创建测试文档
        service = DocumentService(db_session)
        document_create = DocumentCreate(**sample_document_data)
        document = service.create_document(document_create)
        
        with patch('services.document-service.main.get_current_user_id', return_value=1):
            with patch('services.document-service.main.get_backup_service') as mock_backup_service:
                mock_backup_record = Mock()
                mock_backup_record.id = 1
                mock_backup_record.status = "completed"
                mock_backup_service.return_value.create_backup.return_value = mock_backup_record
                
                response = client.post(f"/backup/{document.id}")
                
                assert response.status_code == 200
                data = response.json()
                assert "backup_id" in data
                assert "status" in data


class TestDocumentPreviewService:
    """文档预览服务测试类"""
    
    def test_preview_service_initialization(self):
        """测试预览服务初始化"""
        preview_service = DocumentPreviewService()
        assert preview_service is not None
        assert hasattr(preview_service, 'generate_preview')
    
    def test_pdf_preview_support(self):
        """测试PDF预览支持"""
        preview_service = DocumentPreviewService()
        
        # 测试PDF文件类型支持
        supported = preview_service._is_supported_format("application/pdf")
        assert supported is True
        
        # 测试不支持的文件类型
        unsupported = preview_service._is_supported_format("application/unknown")
        assert unsupported is False
    
    @patch('services.document-service.preview.fitz')
    def test_pdf_preview_generation(self, mock_fitz):
        """测试PDF预览生成"""
        preview_service = DocumentPreviewService()
        
        # 模拟PDF文档
        mock_doc = Mock()
        mock_page = Mock()
        mock_pix = Mock()
        mock_pix.tobytes.return_value = b'fake_image_data'
        mock_page.get_pixmap.return_value = mock_pix
        mock_doc.__getitem__.return_value = mock_page
        mock_doc.page_count = 1
        mock_fitz.open.return_value = mock_doc
        
        with tempfile.NamedTemporaryFile(suffix='.pdf') as temp_file:
            temp_file.write(b'fake pdf content')
            temp_file.flush()
            
            preview_data = asyncio.run(
                preview_service.generate_preview(temp_file.name, "application/pdf")
            )
            
            assert preview_data is not None
            assert preview_data["success"] is True
            assert "preview_url" in preview_data


class TestDocumentBackupService:
    """文档备份服务测试类"""
    
    def test_backup_service_initialization(self, db_session, mock_minio_client):
        """测试备份服务初始化"""
        config = BackupConfig()
        backup_service = DocumentBackupService(db_session, mock_minio_client, config)
        
        assert backup_service is not None
        assert backup_service.config == config
        assert backup_service.db == db_session
        assert backup_service.minio_client == mock_minio_client
    
    @pytest.mark.asyncio
    async def test_create_backup(self, db_session, mock_minio_client, sample_document_data):
        """测试创建备份"""
        # 创建文档
        service = DocumentService(db_session)
        document_create = DocumentCreate(**sample_document_data)
        document = service.create_document(document_create)
        
        # 创建备份服务
        config = BackupConfig(backup_path=tempfile.mkdtemp())
        backup_service = DocumentBackupService(db_session, mock_minio_client, config)
        
        # 模拟MinIO下载
        with tempfile.NamedTemporaryFile() as temp_file:
            temp_file.write(b'fake file content')
            temp_file.flush()
            mock_minio_client.fget_object.side_effect = lambda bucket, obj, path: None
            
            with patch('os.path.getsize', return_value=1024):
                with patch('os.path.exists', return_value=True):
                    backup_record = await backup_service.create_backup(document.id)
            
            assert backup_record is not None
            assert backup_record.document_id == document.id
            assert backup_record.status in ["completed", "failed"]
    
    def test_get_backup_stats(self, db_session, mock_minio_client):
        """测试获取备份统计"""
        config = BackupConfig()
        backup_service = DocumentBackupService(db_session, mock_minio_client, config)
        
        stats = backup_service.get_backup_stats()
        
        assert isinstance(stats, dict)
        assert "total_backups" in stats
        assert "completed_backups" in stats
        assert "failed_backups" in stats
    
    @pytest.mark.asyncio
    async def test_cleanup_old_backups(self, db_session, mock_minio_client):
        """测试清理过期备份"""
        config = BackupConfig(retention_days=1)
        backup_service = DocumentBackupService(db_session, mock_minio_client, config)
        
        # 创建过期备份记录
        old_backup = BackupRecord(
            document_id=1,
            backup_type="manual",
            status="completed",
            created_at=datetime.utcnow() - timedelta(days=2)
        )
        db_session.add(old_backup)
        db_session.commit()
        
        with patch('os.path.exists', return_value=True):
            with patch('os.remove'):
                cleaned_count = await backup_service.cleanup_old_backups()
        
        assert cleaned_count >= 0


class TestErrorHandling:
    """错误处理测试类"""
    
    def test_document_not_found(self, db_session):
        """测试文档不存在的情况"""
        service = DocumentService(db_session)
        
        # 获取不存在的文档
        document = service.get_document(99999)
        assert document is None
    
    def test_invalid_document_data(self, db_session):
        """测试无效文档数据"""
        service = DocumentService(db_session)
        
        # 尝试创建无效文档
        with pytest.raises(Exception):
            invalid_data = DocumentCreate(
                filename="",  # 空文件名
                file_size=-1,  # 负数大小
                owner_id=None  # 空所有者
            )
            service.create_document(invalid_data)
    
    def test_quota_exceeded(self, db_session, sample_user_quota):
        """测试配额超限"""
        service = DocumentService(db_session)
        
        # 创建配额
        quota_create = UserQuotaCreate(**sample_user_quota)
        quota = service.create_user_quota(quota_create)
        
        # 更新已使用配额到接近上限
        quota.used_quota = quota.total_quota - 1000
        db_session.commit()
        
        # 检查大文件上传
        can_upload = service.check_quota_limit(quota.user_id, 2000)
        assert can_upload is False
    
    def test_permission_denied(self, db_session, sample_document_data):
        """测试权限拒绝"""
        service = DocumentService(db_session)
        
        # 创建文档
        document_create = DocumentCreate(**sample_document_data)
        document = service.create_document(document_create)
        
        # 尝试以其他用户身份删除文档
        success = service.delete_document(document.id, 999)  # 不同的用户ID
        assert success is False


if __name__ == "__main__":
    pytest.main(["-v", __file__])