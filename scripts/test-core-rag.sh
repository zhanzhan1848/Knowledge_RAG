#!/bin/bash
# 核心RAG功能测试脚本
# Core RAG Functionality Test Script

set -e

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

# 检查Docker和Docker Compose
check_prerequisites() {
    log_info "检查前置条件..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装或不在PATH中"
        exit 1
    fi
    
    if ! command -v docker compose &> /dev/null; then
        log_error "Docker Compose未安装或不在PATH中"
        exit 1
    fi
    
    log_success "前置条件检查通过"
}

# 准备环境
setup_environment() {
    log_info "准备测试环境..."
    
    # 创建日志目录
    mkdir -p logs
    
    # 准备环境变量文件
    if [ ! -f .env ]; then
        if [ -f .env.template ]; then
            cp .env.template .env
            echo "OPENAI_API_KEY=test_key" >> .env
            echo "HUGGINGFACE_API_KEY=test_key" >> .env
            log_info "已从模板创建.env文件"
        else
            log_warning ".env.template文件不存在，请手动创建.env文件"
        fi
    fi
    
    log_success "环境准备完成"
}

# 清理现有容器
cleanup_containers() {
    log_info "清理现有容器..."
    docker compose -f docker-compose.core.yml down -v 2>/dev/null || true
    log_success "容器清理完成"
}

# 测试阶段1：基础设施服务
test_infrastructure() {
    log_info "=== 阶段1: 测试基础设施服务 ==="
    
    # 启动基础设施
    log_info "启动PostgreSQL和Redis..."
    docker compose -f docker-compose.core.yml up -d postgres redis
    
    # 等待服务就绪
    log_info "等待PostgreSQL就绪..."
    timeout 120 bash -c 'until docker compose -f docker-compose.core.yml exec -T postgres pg_isready -U postgres; do echo "等待中..."; sleep 3; done'
    
    log_info "等待Redis就绪..."
    timeout 60 bash -c 'until docker compose -f docker-compose.core.yml exec -T redis redis-cli ping; do echo "等待中..."; sleep 2; done'
    
    # 测试连接
    log_info "测试PostgreSQL连接..."
    docker compose -f docker-compose.core.yml exec -T postgres psql -U postgres -d knowledge_rag -c "SELECT version();"
    
    log_info "测试Redis连接..."
    docker compose -f docker-compose.core.yml exec -T redis redis-cli set test_key "infrastructure_ok"
    docker compose -f docker-compose.core.yml exec -T redis redis-cli get test_key
    
    log_success "基础设施服务测试通过"
}

# 测试阶段2：核心RAG组件
test_core_rag_components() {
    log_info "=== 阶段2: 测试核心RAG组件 ==="
    
    # 启动核心RAG基础设施
    log_info "启动Neo4j、text2vec-model2vec和Weaviate..."
    docker compose -f docker-compose.core.yml up -d neo4j text2vec-model2vec weaviate
    
    # 等待Neo4j
    log_info "等待Neo4j就绪..."
    timeout 180 bash -c 'until docker compose -f docker-compose.core.yml exec -T neo4j cypher-shell -u neo4j -p neo4j123 "RETURN 1" 2>/dev/null; do echo "等待Neo4j..."; sleep 5; done'
    
    # 等待text2vec-model2vec
    log_info "等待text2vec-model2vec就绪..."
    timeout 120 bash -c 'until curl -f http://localhost:8081/health 2>/dev/null; do echo "等待text2vec-model2vec..."; sleep 3; done'
    
    # 等待Weaviate
    log_info "等待Weaviate就绪..."
    timeout 180 bash -c 'until curl -f http://localhost:8080/v1/.well-known/ready 2>/dev/null; do echo "等待Weaviate..."; sleep 5; done'
    
    # 测试核心组件
    log_info "测试Weaviate连接..."
    curl -X GET "http://localhost:8080/v1/meta" | jq . || log_warning "jq未安装，无法格式化JSON输出"
    
    log_info "测试Neo4j连接..."
    docker compose -f docker-compose.core.yml exec -T neo4j cypher-shell -u neo4j -p neo4j123 "CREATE (n:TestNode {name: 'RAG_Test', timestamp: datetime()}) RETURN n"
    
    log_info "测试text2vec-model2vec连接..."
    curl -X GET "http://localhost:8081/health"
    
    log_success "核心RAG组件测试通过"
}

# 测试阶段3：微服务
test_microservices() {
    log_info "=== 阶段3: 测试核心微服务 ==="
    
    # 启动核心微服务
    log_info "启动核心微服务..."
    docker compose -f docker-compose.core.yml up -d --build api-gateway auth-service vector-service knowledge-graph-service
    
    # 等待服务就绪
    services=("api-gateway:8000" "auth-service:8001" "vector-service:8003" "knowledge-graph-service:8006")
    
    for service in "${services[@]}"; do
        service_name=$(echo $service | cut -d':' -f1)
        port=$(echo $service | cut -d':' -f2)
        
        log_info "等待${service_name}就绪..."
        timeout 120 bash -c "until curl -f http://localhost:${port}/health 2>/dev/null; do echo '等待${service_name}...'; sleep 3; done"
        
        log_info "测试${service_name} API..."
        curl -X GET "http://localhost:${port}/health"
        echo
    done
    
    log_success "核心微服务测试通过"
}

# 测试阶段4：RAG功能集成
test_rag_integration() {
    log_info "=== 阶段4: 测试RAG功能集成 ==="
    
    # 启动剩余服务
    log_info "启动完整RAG系统..."
    docker compose -f docker-compose.core.yml up -d --build
    
    # 等待所有服务
    additional_services=("llm-service:8004" "qa-service:8005" "graph-service:8008")
    
    for service in "${additional_services[@]}"; do
        service_name=$(echo $service | cut -d':' -f1)
        port=$(echo $service | cut -d':' -f2)
        
        log_info "等待${service_name}就绪..."
        timeout 120 bash -c "until curl -f http://localhost:${port}/health 2>/dev/null; do echo '等待${service_name}...'; sleep 3; done"
    done
    
    # 测试RAG工作流
    log_info "测试文档向量化..."
    curl -X POST "http://localhost:8003/api/v1/vectorize" \
        -H "Content-Type: application/json" \
        -d '{"text": "这是一个测试文档，用于验证RAG系统的向量化功能。GraphRAG结合了图数据库和向量检索的优势。", "metadata": {"source": "test_script", "type": "integration_test"}}'
    echo
    
    log_info "测试知识图谱构建..."
    curl -X POST "http://localhost:8006/api/v1/entities" \
        -H "Content-Type: application/json" \
        -d '{"text": "人工智能（AI）是计算机科学的一个分支，它致力于创建能够执行通常需要人类智能的任务的系统。机器学习是AI的一个子集。", "extract_relations": true}'
    echo
    
    log_info "测试GraphRAG查询..."
    curl -X POST "http://localhost:8008/api/v1/query" \
        -H "Content-Type: application/json" \
        -d '{"query": "什么是GraphRAG？它有什么优势？", "use_graph": true, "max_results": 5}'
    echo
    
    log_info "测试QA服务..."
    curl -X POST "http://localhost:8005/api/v1/ask" \
        -H "Content-Type: application/json" \
        -d '{"question": "请解释GraphRAG技术的核心概念和应用场景", "context_type": "graph", "include_sources": true}'
    echo
    
    log_success "RAG功能集成测试通过"
}

# 收集日志
collect_logs() {
    log_info "收集系统日志..."
    
    # 收集容器日志
    docker compose -f docker-compose.core.yml logs > logs/test-run-$(date +%Y%m%d-%H%M%S).log 2>&1
    
    # 显示容器状态
    log_info "当前容器状态："
    docker compose -f docker-compose.core.yml ps
    
    log_success "日志收集完成，保存在logs/目录中"
}

# 清理资源
cleanup() {
    log_info "清理测试资源..."
    docker compose -f docker-compose.core.yml down -v
    log_success "清理完成"
}

# 主函数
main() {
    echo "==========================================="
    echo "     Knowledge RAG 核心功能测试脚本"
    echo "==========================================="
    echo
    
    # 解析命令行参数
    STAGE="all"
    CLEANUP_AFTER="true"
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --stage)
                STAGE="$2"
                shift 2
                ;;
            --no-cleanup)
                CLEANUP_AFTER="false"
                shift
                ;;
            --help|-h)
                echo "用法: $0 [选项]"
                echo "选项:"
                echo "  --stage STAGE     指定测试阶段 (infrastructure|core|services|integration|all)"
                echo "  --no-cleanup      测试后不清理容器"
                echo "  --help, -h        显示此帮助信息"
                exit 0
                ;;
            *)
                log_error "未知选项: $1"
                exit 1
                ;;
        esac
    done
    
    # 设置错误处理
    trap 'log_error "测试过程中发生错误，正在清理..."; cleanup; exit 1' ERR
    
    # 执行测试
    check_prerequisites
    setup_environment
    cleanup_containers
    
    case $STAGE in
        "infrastructure")
            test_infrastructure
            ;;
        "core")
            test_infrastructure
            test_core_rag_components
            ;;
        "services")
            test_infrastructure
            test_core_rag_components
            test_microservices
            ;;
        "integration")
            test_infrastructure
            test_core_rag_components
            test_microservices
            test_rag_integration
            ;;
        "all")
            test_infrastructure
            test_core_rag_components
            test_microservices
            test_rag_integration
            ;;
        *)
            log_error "无效的测试阶段: $STAGE"
            exit 1
            ;;
    esac
    
    collect_logs
    
    if [ "$CLEANUP_AFTER" = "true" ]; then
        cleanup
    else
        log_info "跳过清理，容器继续运行"
        log_info "手动清理命令: docker compose -f docker-compose.core.yml down -v"
    fi
    
    echo
    log_success "=== 核心RAG功能测试完成 ==="
    echo "测试阶段: $STAGE"
    echo "日志位置: logs/目录"
    
    if [ "$CLEANUP_AFTER" = "false" ]; then
        echo
        log_info "服务访问地址："
        echo "  - API Gateway: http://localhost:8000"
        echo "  - Weaviate: http://localhost:8080"
        echo "  - Neo4j Browser: http://localhost:7474 (neo4j/neo4j123)"
        echo "  - Vector Service: http://localhost:8003"
        echo "  - QA Service: http://localhost:8005"
    fi
}

# 执行主函数
main "$@"