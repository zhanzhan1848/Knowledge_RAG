#!/bin/bash

# Knowledge RAG 系统开发环境快速设置脚本
# 作者: Knowledge RAG Team
# 描述: 自动化设置开发环境，包括环境变量配置、依赖安装和服务启动

set -e  # 遇到错误时退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查必要工具
check_requirements() {
    log_info "检查系统要求..."
    
    # 检查 Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi
    
    # 检查 Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose 未安装，请先安装 Docker Compose"
        exit 1
    fi
    
    # 检查 Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 未安装，请先安装 Python 3.10+"
        exit 1
    fi
    
    log_success "系统要求检查通过"
}

# 设置环境变量
setup_env() {
    log_info "设置环境变量..."
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            log_success "已从 .env.example 创建 .env 文件"
        else
            log_error ".env.example 文件不存在"
            exit 1
        fi
    else
        log_warning ".env 文件已存在，跳过创建"
    fi
    
    # 检查必要的环境变量
    if ! grep -q "OPENAI_API_KEY=your_openai_api_key_here" .env; then
        log_warning "请在 .env 文件中设置 OPENAI_API_KEY"
    fi
    
    if ! grep -q "JWT_SECRET_KEY=your_jwt_secret_key_here" .env; then
        log_warning "请在 .env 文件中设置 JWT_SECRET_KEY"
    fi
}

# 创建必要目录
setup_directories() {
    log_info "创建必要目录..."
    
    directories=(
        "data/uploads"
        "data/temp"
        "data/processed"
        "data/chroma"
        "data/faiss"
        "data/graphrag"
        "logs"
        "models/huggingface"
    )
    
    for dir in "${directories[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            log_success "创建目录: $dir"
        fi
    done
}

# 安装 Python 依赖
install_dependencies() {
    log_info "安装 Python 依赖..."
    
    # 检查是否安装了 uv
    if ! command -v uv &> /dev/null; then
        log_info "安装 uv 包管理器..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        source $HOME/.cargo/env
    fi
    
    if [ -f "pyproject.toml" ]; then
        uv sync --dev --prerelease=allow
        log_success "Python 依赖安装完成"
    elif [ -f "requirements.txt" ]; then
        uv sync --prerelease=allow
        log_success "Python 依赖安装完成"
    else
        log_warning "pyproject.toml 或 requirements.txt 文件不存在，跳过依赖安装"
    fi
}

# 启动基础设施服务
start_infrastructure() {
    log_info "启动基础设施服务..."
    
    # 启动数据库和中间件服务
    docker-compose up -d postgres redis elasticsearch neo4j rabbitmq weaviate
    
    log_info "等待服务启动..."
    sleep 30
    
    # 检查服务状态
    services=("postgres" "redis" "elasticsearch" "neo4j" "rabbitmq" "weaviate")
    for service in "${services[@]}"; do
        if docker-compose ps $service | grep -q "Up"; then
            log_success "$service 服务启动成功"
        else
            log_error "$service 服务启动失败"
        fi
    done
}

# 初始化数据库
init_database() {
    log_info "初始化数据库..."
    
    # 等待 PostgreSQL 完全启动
    log_info "等待 PostgreSQL 启动..."
    until docker-compose exec postgres pg_isready -U postgres; do
        sleep 2
    done
    
    # 创建数据库
    databases=("auth_db" "document_db" "vector_db" "knowledge_graph_db")
    for db in "${databases[@]}"; do
        docker-compose exec postgres psql -U postgres -c "CREATE DATABASE $db;" 2>/dev/null || true
        log_success "数据库 $db 已准备就绪"
    done
}

# 启动微服务
start_services() {
    log_info "启动微服务..."
    
    # 构建并启动所有服务
    docker-compose up -d --build
    
    log_info "等待微服务启动..."
    sleep 20
    
    # 检查微服务状态
    services=("api-gateway" "auth-service" "document-service" "vector-service" "llm-service" "qa-service" "knowledge-graph-service" "notification-service" "graph-service")
    for service in "${services[@]}"; do
        if docker-compose ps $service | grep -q "Up"; then
            log_success "$service 启动成功"
        else
            log_warning "$service 可能启动失败，请检查日志"
        fi
    done
}

# 显示服务信息
show_services_info() {
    log_info "服务访问信息:"
    echo ""
    echo "🌐 API Gateway: http://localhost:8000"
    echo "🔐 Auth Service: http://localhost:8001"
    echo "📄 Document Service: http://localhost:8002"
    echo "🔍 Vector Service: http://localhost:8003"
    echo "🤖 LLM Service: http://localhost:8004"
    echo "❓ QA Service: http://localhost:8005"
    echo "🕸️  Knowledge Graph Service: http://localhost:8006"
    echo "📧 Notification Service: http://localhost:8007"
    echo "📊 Graph Service: http://localhost:8008"
    echo ""
    echo "📊 Monitoring:"
    echo "   - Prometheus: http://localhost:9090"
    echo "   - Grafana: http://localhost:3000 (admin/admin)"
    echo ""
    echo "🗄️  Databases:"
    echo "   - PostgreSQL: localhost:5432"
    echo "   - Redis: localhost:6379"
    echo "   - Elasticsearch: http://localhost:9200"
    echo "   - Neo4j: http://localhost:7474 (neo4j/neo4j123)"
    echo "   - Weaviate: http://localhost:8080"
    echo ""
}

# 主函数
main() {
    echo "🚀 Knowledge RAG 系统开发环境设置"
    echo "====================================="
    echo ""
    
    check_requirements
    setup_env
    setup_directories
    install_dependencies
    start_infrastructure
    init_database
    start_services
    
    echo ""
    log_success "开发环境设置完成！"
    echo ""
    
    show_services_info
    
    echo "💡 提示:"
    echo "   - 查看服务日志: docker-compose logs [service_name]"
    echo "   - 停止所有服务: docker-compose down"
    echo "   - 重启服务: docker-compose restart [service_name]"
    echo "   - 查看服务状态: docker-compose ps"
    echo ""
    echo "📖 更多信息请查看: docs/environment-setup.md"
}

# 执行主函数
main "$@"