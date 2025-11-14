# 正确处理扁平结构的 conda-pack Dockerfile

FROM condaforge/miniforge3:latest

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH=/opt/conda/envs/lightrag/bin:$PATH

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    curl \
    wget \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 复制打包好的 conda 环境
COPY ./xwrag.tar.gz /tmp/xwrag.tar.gz

# 解包 conda 环境到正确位置
# xwrag.tar.gz 的结构是: bin/, lib/, ... 直接在根目录
# 所以我们直接解包到 /opt/conda/envs/lightrag/
RUN mkdir -p /opt/conda/envs/lightrag && \
    tar -xzf /tmp/xwrag.tar.gz -C /opt/conda/envs/lightrag && \
    rm /tmp/xwrag.tar.gz && \
    # conda-unpack 修复打包环境的路径引用
    /opt/conda/bin/conda-unpack -p /opt/conda/envs/lightrag || true

# 验证环境安装成功
RUN /opt/conda/envs/lightrag/bin/python --version && \
    /opt/conda/envs/lightrag/bin/pip --version

# 复制项目代码
COPY . .

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/docs || exit 1

# 启动命令 - 直接使用完整路径
CMD ["/opt/conda/envs/lightrag/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]