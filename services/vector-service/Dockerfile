# Vector Service Dockerfile
# 基于Python 3.11的官方镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖（向量计算需要数学库）
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    libblas-dev \
    liblapack-dev \
    libatlas-base-dev \
    gfortran \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt requirements-dev.txt ./

# 安装Python依赖
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# 复制共享库
COPY shared/ ./shared/
COPY libs/ ./libs/

# 复制向量服务代码
COPY services/vector-service/ ./services/vector-service/

# 创建向量数据库目录
RUN mkdir -p /app/data/vector_db /app/data/chroma /app/data/faiss

# 创建非root用户
RUN addgroup --system appuser && adduser --system --group appuser
RUN chown -R appuser:appuser /app
USER appuser

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8003/health || exit 1

# 暴露端口
EXPOSE 8003

# 启动命令
CMD ["uvicorn", "services.vector-service.main:app", "--host", "0.0.0.0", "--port", "8003", "--workers", "2"]