-- Knowledge RAG System - 测试数据库初始化脚本
-- 创建测试环境所需的数据库结构和初始数据

-- 设置数据库编码和区域设置
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

-- 创建扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- 创建枚举类型
CREATE TYPE user_role AS ENUM ('admin', 'user', 'guest');
CREATE TYPE user_status AS ENUM ('active', 'inactive', 'suspended', 'pending');
CREATE TYPE document_status AS ENUM ('pending', 'processing', 'completed', 'failed', 'deleted');
CREATE TYPE document_type AS ENUM ('pdf', 'txt', 'docx', 'md', 'json', 'html', 'csv');
CREATE TYPE processing_status AS ENUM ('queued', 'in_progress', 'completed', 'failed', 'cancelled');
CREATE TYPE notification_type AS ENUM ('email', 'sms', 'push', 'webhook');
CREATE TYPE notification_status AS ENUM ('pending', 'sent', 'failed', 'cancelled');

-- ===========================================
-- 用户相关表
-- ===========================================

-- 用户表
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    role user_role DEFAULT 'user',
    status user_status DEFAULT 'active',
    avatar_url TEXT,
    last_login_at TIMESTAMP WITH TIME ZONE,
    login_count INTEGER DEFAULT 0,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP WITH TIME ZONE,
    email_verified BOOLEAN DEFAULT FALSE,
    email_verification_token VARCHAR(255),
    password_reset_token VARCHAR(255),
    password_reset_expires TIMESTAMP WITH TIME ZONE,
    preferences JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 用户会话表
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    refresh_token VARCHAR(255) UNIQUE,
    ip_address INET,
    user_agent TEXT,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_accessed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 用户权限表
CREATE TABLE user_permissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    resource VARCHAR(100) NOT NULL,
    action VARCHAR(50) NOT NULL,
    granted BOOLEAN DEFAULT TRUE,
    granted_by UUID REFERENCES users(id),
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(user_id, resource, action)
);

-- ===========================================
-- 文档相关表
-- ===========================================

-- 文档表
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    file_hash VARCHAR(64) NOT NULL,
    mime_type VARCHAR(100),
    document_type document_type NOT NULL,
    status document_status DEFAULT 'pending',
    title TEXT,
    description TEXT,
    content TEXT,
    language VARCHAR(10) DEFAULT 'zh',
    page_count INTEGER,
    word_count INTEGER,
    character_count INTEGER,
    processing_started_at TIMESTAMP WITH TIME ZONE,
    processing_completed_at TIMESTAMP WITH TIME ZONE,
    processing_error TEXT,
    tags TEXT[],
    metadata JSONB DEFAULT '{}',
    search_vector tsvector,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 文档块表（用于向量搜索）
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    token_count INTEGER,
    character_count INTEGER,
    start_position INTEGER,
    end_position INTEGER,
    page_number INTEGER,
    section_title TEXT,
    embedding vector(1536),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(document_id, chunk_index)
);

-- 文档处理任务表
CREATE TABLE document_processing_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    task_type VARCHAR(50) NOT NULL,
    status processing_status DEFAULT 'queued',
    priority INTEGER DEFAULT 0,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    progress_percentage INTEGER DEFAULT 0,
    result JSONB,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ===========================================
-- 问答相关表
-- ===========================================

-- 对话会话表
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255),
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    message_count INTEGER DEFAULT 0,
    last_message_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 消息表
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    content_type VARCHAR(20) DEFAULT 'text',
    token_count INTEGER,
    model_used VARCHAR(100),
    response_time_ms INTEGER,
    confidence_score DECIMAL(3,2),
    sources JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 问答评价表
CREATE TABLE qa_evaluations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    feedback TEXT,
    is_helpful BOOLEAN,
    is_accurate BOOLEAN,
    is_relevant BOOLEAN,
    improvement_suggestions TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ===========================================
-- 知识图谱相关表
-- ===========================================

-- 实体表
CREATE TABLE entities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    entity_type VARCHAR(100) NOT NULL,
    description TEXT,
    aliases TEXT[],
    confidence_score DECIMAL(3,2),
    source_documents UUID[],
    properties JSONB DEFAULT '{}',
    embedding vector(1536),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(name, entity_type)
);

-- 关系表
CREATE TABLE relationships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_entity_id UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    target_entity_id UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    relationship_type VARCHAR(100) NOT NULL,
    description TEXT,
    confidence_score DECIMAL(3,2),
    source_documents UUID[],
    properties JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_entity_id, target_entity_id, relationship_type)
);

-- ===========================================
-- 系统相关表
-- ===========================================

-- 通知表
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    type notification_type NOT NULL,
    status notification_status DEFAULT 'pending',
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    recipient VARCHAR(255) NOT NULL,
    template_id VARCHAR(100),
    template_data JSONB DEFAULT '{}',
    scheduled_at TIMESTAMP WITH TIME ZONE,
    sent_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 系统日志表
CREATE TABLE system_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_name VARCHAR(100) NOT NULL,
    log_level VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    request_id VARCHAR(100),
    trace_id VARCHAR(100),
    ip_address INET,
    user_agent TEXT,
    endpoint VARCHAR(255),
    method VARCHAR(10),
    status_code INTEGER,
    response_time_ms INTEGER,
    error_details JSONB,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- API 使用统计表
CREATE TABLE api_usage_stats (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    service_name VARCHAR(100) NOT NULL,
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    request_count INTEGER DEFAULT 1,
    total_response_time_ms BIGINT DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    date DATE NOT NULL,
    hour INTEGER CHECK (hour >= 0 AND hour <= 23),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, service_name, endpoint, method, date, hour)
);

-- ===========================================
-- 索引创建
-- ===========================================

-- 用户表索引
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_status ON users(status);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_created_at ON users(created_at);

-- 用户会话表索引
CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_token ON user_sessions(session_token);
CREATE INDEX idx_user_sessions_expires_at ON user_sessions(expires_at);
CREATE INDEX idx_user_sessions_is_active ON user_sessions(is_active);

-- 用户权限表索引
CREATE INDEX idx_user_permissions_user_id ON user_permissions(user_id);
CREATE INDEX idx_user_permissions_resource ON user_permissions(resource);

-- 文档表索引
CREATE INDEX idx_documents_user_id ON documents(user_id);
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_documents_type ON documents(document_type);
CREATE INDEX idx_documents_created_at ON documents(created_at);
CREATE INDEX idx_documents_file_hash ON documents(file_hash);
CREATE INDEX idx_documents_search_vector ON documents USING GIN(search_vector);
CREATE INDEX idx_documents_tags ON documents USING GIN(tags);

-- 文档块表索引
CREATE INDEX idx_document_chunks_document_id ON document_chunks(document_id);
CREATE INDEX idx_document_chunks_chunk_index ON document_chunks(chunk_index);
CREATE INDEX idx_document_chunks_content_hash ON document_chunks(content_hash);
-- 向量相似性搜索索引
CREATE INDEX idx_document_chunks_embedding ON document_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- 文档处理任务表索引
CREATE INDEX idx_document_processing_tasks_document_id ON document_processing_tasks(document_id);
CREATE INDEX idx_document_processing_tasks_status ON document_processing_tasks(status);
CREATE INDEX idx_document_processing_tasks_task_type ON document_processing_tasks(task_type);
CREATE INDEX idx_document_processing_tasks_priority ON document_processing_tasks(priority DESC);
CREATE INDEX idx_document_processing_tasks_created_at ON document_processing_tasks(created_at);

-- 对话会话表索引
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_conversations_is_active ON conversations(is_active);
CREATE INDEX idx_conversations_created_at ON conversations(created_at);
CREATE INDEX idx_conversations_last_message_at ON conversations(last_message_at);

-- 消息表索引
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_user_id ON messages(user_id);
CREATE INDEX idx_messages_role ON messages(role);
CREATE INDEX idx_messages_created_at ON messages(created_at);

-- 问答评价表索引
CREATE INDEX idx_qa_evaluations_message_id ON qa_evaluations(message_id);
CREATE INDEX idx_qa_evaluations_user_id ON qa_evaluations(user_id);
CREATE INDEX idx_qa_evaluations_rating ON qa_evaluations(rating);

-- 实体表索引
CREATE INDEX idx_entities_name ON entities(name);
CREATE INDEX idx_entities_type ON entities(entity_type);
CREATE INDEX idx_entities_confidence ON entities(confidence_score);
CREATE INDEX idx_entities_aliases ON entities USING GIN(aliases);
CREATE INDEX idx_entities_embedding ON entities USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- 关系表索引
CREATE INDEX idx_relationships_source_entity ON relationships(source_entity_id);
CREATE INDEX idx_relationships_target_entity ON relationships(target_entity_id);
CREATE INDEX idx_relationships_type ON relationships(relationship_type);
CREATE INDEX idx_relationships_confidence ON relationships(confidence_score);

-- 通知表索引
CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_type ON notifications(type);
CREATE INDEX idx_notifications_status ON notifications(status);
CREATE INDEX idx_notifications_scheduled_at ON notifications(scheduled_at);
CREATE INDEX idx_notifications_created_at ON notifications(created_at);

-- 系统日志表索引
CREATE INDEX idx_system_logs_service_name ON system_logs(service_name);
CREATE INDEX idx_system_logs_log_level ON system_logs(log_level);
CREATE INDEX idx_system_logs_user_id ON system_logs(user_id);
CREATE INDEX idx_system_logs_request_id ON system_logs(request_id);
CREATE INDEX idx_system_logs_created_at ON system_logs(created_at);

-- API 使用统计表索引
CREATE INDEX idx_api_usage_stats_user_id ON api_usage_stats(user_id);
CREATE INDEX idx_api_usage_stats_service ON api_usage_stats(service_name);
CREATE INDEX idx_api_usage_stats_date ON api_usage_stats(date);
CREATE INDEX idx_api_usage_stats_endpoint ON api_usage_stats(endpoint);

-- ===========================================
-- 触发器函数
-- ===========================================

-- 更新 updated_at 字段的触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 更新搜索向量的触发器函数
CREATE OR REPLACE FUNCTION update_document_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector = to_tsvector('english', COALESCE(NEW.title, '') || ' ' || COALESCE(NEW.description, '') || ' ' || COALESCE(NEW.content, ''));
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 更新对话消息计数的触发器函数
CREATE OR REPLACE FUNCTION update_conversation_message_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE conversations 
        SET message_count = message_count + 1,
            last_message_at = NEW.created_at
        WHERE id = NEW.conversation_id;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE conversations 
        SET message_count = message_count - 1
        WHERE id = OLD.conversation_id;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ language 'plpgsql';

-- ===========================================
-- 创建触发器
-- ===========================================

-- updated_at 字段自动更新触发器
CREATE TRIGGER trigger_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trigger_documents_updated_at BEFORE UPDATE ON documents FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trigger_document_processing_tasks_updated_at BEFORE UPDATE ON document_processing_tasks FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trigger_conversations_updated_at BEFORE UPDATE ON conversations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trigger_entities_updated_at BEFORE UPDATE ON entities FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trigger_relationships_updated_at BEFORE UPDATE ON relationships FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trigger_api_usage_stats_updated_at BEFORE UPDATE ON api_usage_stats FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 文档搜索向量自动更新触发器
CREATE TRIGGER trigger_documents_search_vector BEFORE INSERT OR UPDATE ON documents FOR EACH ROW EXECUTE FUNCTION update_document_search_vector();

-- 对话消息计数自动更新触发器
CREATE TRIGGER trigger_messages_conversation_count AFTER INSERT OR DELETE ON messages FOR EACH ROW EXECUTE FUNCTION update_conversation_message_count();

-- ===========================================
-- 插入测试数据
-- ===========================================

-- 插入测试用户
INSERT INTO users (id, username, email, password_hash, full_name, role, status, email_verified) VALUES
('550e8400-e29b-41d4-a716-446655440001', 'admin', 'admin@test.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PmvlDO', '系统管理员', 'admin', 'active', true),
('550e8400-e29b-41d4-a716-446655440002', 'testuser1', 'user1@test.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PmvlDO', '测试用户1', 'user', 'active', true),
('550e8400-e29b-41d4-a716-446655440003', 'testuser2', 'user2@test.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PmvlDO', '测试用户2', 'user', 'active', true),
('550e8400-e29b-41d4-a716-446655440004', 'guestuser', 'guest@test.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PmvlDO', '访客用户', 'guest', 'active', false);

-- 插入测试文档
INSERT INTO documents (id, user_id, filename, original_filename, file_path, file_size, file_hash, mime_type, document_type, status, title, description, content, language) VALUES
('660e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440002', 'test_doc_1.txt', 'test_document_1.txt', '/storage/test_doc_1.txt', 1024, 'abc123def456', 'text/plain', 'txt', 'completed', '测试文档1', '这是一个测试文档', '这是测试文档的内容，用于验证系统功能。', 'zh'),
('660e8400-e29b-41d4-a716-446655440002', '550e8400-e29b-41d4-a716-446655440002', 'test_doc_2.md', 'test_document_2.md', '/storage/test_doc_2.md', 2048, 'def456ghi789', 'text/markdown', 'md', 'completed', '测试文档2', '这是另一个测试文档', '# 测试文档\n\n这是一个Markdown格式的测试文档。', 'zh'),
('660e8400-e29b-41d4-a716-446655440003', '550e8400-e29b-41d4-a716-446655440003', 'test_doc_3.pdf', 'test_document_3.pdf', '/storage/test_doc_3.pdf', 4096, 'ghi789jkl012', 'application/pdf', 'pdf', 'processing', '测试PDF文档', 'PDF格式的测试文档', NULL, 'zh');

-- 插入测试对话
INSERT INTO conversations (id, user_id, title, description, is_active, message_count) VALUES
('770e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440002', '测试对话1', '关于文档处理的对话', true, 2),
('770e8400-e29b-41d4-a716-446655440002', '550e8400-e29b-41d4-a716-446655440003', '测试对话2', '关于知识图谱的对话', true, 1);

-- 插入测试消息
INSERT INTO messages (id, conversation_id, user_id, role, content, content_type, token_count, model_used, response_time_ms, confidence_score) VALUES
('880e8400-e29b-41d4-a716-446655440001', '770e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440002', 'user', '请帮我分析这个文档', 'text', 10, NULL, NULL, NULL),
('880e8400-e29b-41d4-a716-446655440002', '770e8400-e29b-41d4-a716-446655440001', NULL, 'assistant', '我已经分析了您的文档，以下是主要内容摘要...', 'text', 50, 'gpt-3.5-turbo', 1500, 0.95),
('880e8400-e29b-41d4-a716-446655440003', '770e8400-e29b-41d4-a716-446655440002', '550e8400-e29b-41d4-a716-446655440003', 'user', '什么是知识图谱？', 'text', 8, NULL, NULL, NULL);

-- 插入测试实体
INSERT INTO entities (id, name, entity_type, description, confidence_score) VALUES
('990e8400-e29b-41d4-a716-446655440001', '人工智能', 'CONCEPT', '人工智能相关概念', 0.95),
('990e8400-e29b-41d4-a716-446655440002', '机器学习', 'CONCEPT', '机器学习技术', 0.90),
('990e8400-e29b-41d4-a716-446655440003', '深度学习', 'CONCEPT', '深度学习方法', 0.88);

-- 插入测试关系
INSERT INTO relationships (id, source_entity_id, target_entity_id, relationship_type, description, confidence_score) VALUES
('aa0e8400-e29b-41d4-a716-446655440001', '990e8400-e29b-41d4-a716-446655440001', '990e8400-e29b-41d4-a716-446655440002', 'INCLUDES', '人工智能包含机器学习', 0.92),
('aa0e8400-e29b-41d4-a716-446655440002', '990e8400-e29b-41d4-a716-446655440002', '990e8400-e29b-41d4-a716-446655440003', 'INCLUDES', '机器学习包含深度学习', 0.89);

-- 插入测试通知
INSERT INTO notifications (id, user_id, type, status, title, content, recipient) VALUES
('bb0e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440002', 'email', 'sent', '文档处理完成', '您的文档已经处理完成，可以开始使用了。', 'user1@test.com'),
('bb0e8400-e29b-41d4-a716-446655440002', '550e8400-e29b-41d4-a716-446655440003', 'email', 'pending', '欢迎使用系统', '欢迎使用Knowledge RAG系统！', 'user2@test.com');

-- 提交事务
COMMIT;

-- 输出初始化完成信息
\echo '测试数据库初始化完成！'
\echo '创建的表：'
\echo '- 用户相关：users, user_sessions, user_permissions'
\echo '- 文档相关：documents, document_chunks, document_processing_tasks'
\echo '- 问答相关：conversations, messages, qa_evaluations'
\echo '- 知识图谱：entities, relationships'
\echo '- 系统相关：notifications, system_logs, api_usage_stats'
\echo ''
\echo '插入的测试数据：'
\echo '- 4个测试用户（admin, testuser1, testuser2, guestuser）'
\echo '- 3个测试文档'
\echo '- 2个测试对话和3条消息'
\echo '- 3个测试实体和2个关系'
\echo '- 2个测试通知'
\echo ''
\echo '测试用户密码均为：testpass123'