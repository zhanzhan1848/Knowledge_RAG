-- Knowledge RAG System - Database Initialization Script
-- 用于在PostgreSQL容器启动时创建多个数据库

-- 创建认证服务数据库
CREATE DATABASE auth_db;
GRANT ALL PRIVILEGES ON DATABASE auth_db TO postgres;

-- 创建文档服务数据库
CREATE DATABASE document_db;
GRANT ALL PRIVILEGES ON DATABASE document_db TO postgres;

-- 创建向量服务数据库
CREATE DATABASE vector_db;
GRANT ALL PRIVILEGES ON DATABASE vector_db TO postgres;

-- 创建知识图谱服务数据库
CREATE DATABASE knowledge_graph_db;
GRANT ALL PRIVILEGES ON DATABASE knowledge_graph_db TO postgres;

-- 为每个数据库启用必要的扩展
\c auth_db;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

\c document_db;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

\c vector_db;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

\c knowledge_graph_db;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

\c knowledge_rag;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- 输出初始化完成信息
\echo 'Database initialization completed successfully!'