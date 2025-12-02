# xwRAG 部署文档（NebulaGraph + Milvus）

## 目录

- [系统概述](#系统概述)
- [系统架构](#系统架构)
- [系统要求](#系统要求)
- [快速开始](#快速开始)
- [数据库部署](#数据库部署)
  - [NebulaGraph 部署](#nebulagraph-部署)
  - [Milvus 部署](#milvus-部署)
- [应用服务部署](#应用服务部署)
  - [Docker Compose 部署（推荐）](#docker-compose-部署推荐)
  - [本地源码部署](#本地源码部署)
- [配置说明](#配置说明)
- [验证部署](#验证部署)
- [性能优化](#性能优化)
- [故障排查](#故障排查)
- [监控和维护](#监控和维护)

---

## 系统概述

xwRAG 是一个基于知识图谱和向量数据库的高性能 RAG（检索增强生成）系统。本文档专注于使用 **NebulaGraph** 作为图数据库和 **Milvus** 作为向量数据库的部署方案。

### 核心特性

- **图数据库**：NebulaGraph - 高性能分布式图数据库，批量查询性能优化 40 倍
- **向量数据库**：Milvus - 开源向量数据库，支持大规模向量相似度搜索
- **混合检索**：结合知识图谱和向量搜索的混合检索策略
- **RESTful API**：基于 FastAPI 构建的高性能 API 服务
- **多模态文档处理**：支持 PDF、DOCX、TXT 等多种格式

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                        客户端应用                              │
│              (Web UI / API Client / 第三方集成)                │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/WebSocket
┌────────────────────────▼────────────────────────────────────┐
│                   FastAPI 后端服务 (app/)                      │
│  ┌──────────────┬──────────────┬──────────────┬───────────┐  │
│  │ 文档管理路由  │  查询路由     │  图谱路由     │  管理路由  │  │
│  │ documents.py │  query.py    │  graph.py    │  admin.py │  │
│  └──────────────┴──────────────┴──────────────┴───────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                    xwRAG 核心库 (xwrag/)                       │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  知识图谱处理                                           │    │
│  │  - 实体/关系抽取 (kg/nebula_impl.py)                   │    │
│  │  - 向量化                                              │    │
│  │  - 混合检索                                            │    │
│  └──────────────────────────────────────────────────────┘    │
└───┬────────────────────┬────────────────────┬───────────────┘
    │                    │                    │
┌───▼──────────┐  ┌─────▼──────────┐  ┌─────▼──────────┐
│  NebulaGraph │  │     Milvus     │  │   LLM 服务     │
│  图数据库     │  │   向量数据库    │  │  OpenAI/Ollama │
│  端口: 9669   │  │  端口: 19530   │  │                │
└──────────────┘  └────────────────┘  └────────────────┘
```

---

## 系统要求

### 最低配置

- **CPU**: 4 核
- **内存**: 16 GB RAM
- **磁盘**: 100 GB 可用空间 (SSD 推荐)
- **操作系统**: Linux (Ubuntu 20.04+) / macOS / Windows (WSL2)

### 推荐配置（生产环境）

- **CPU**: 8 核 +
- **内存**: 32 GB RAM +
- **磁盘**: 500 GB+ SSD
- **GPU**: 可选，用于本地 Embedding 模型加速

### 软件依赖

- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Python**: 3.10+ (本地部署)

---

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/your-org/myRAG.git
cd myRAG
```

### 2. 配置环境变量

```bash
# 复制示例配置文件
cp env.example .env

# 编辑 .env 文件
nano .env
```

**关键配置项**：

```bash
# LLM 配置
LLM_BINDING=openai
LLM_MODEL=gpt-4o
LLM_BINDING_HOST=https://api.openai.com/v1
LLM_BINDING_API_KEY=sk-your-api-key-here

# Embedding 配置
EMBEDDING_BINDING=openai
EMBEDDING_MODEL=text-embedding-3-large
EMBEDDING_DIM=3072
EMBEDDING_BINDING_API_KEY=sk-your-api-key-here

# NebulaGraph 配置
xwrag_GRAPH_STORAGE=NebulaGraphStorage
NEBULA_HOST=localhost
NEBULA_PORT=9669
NEBULA_USER=root
NEBULA_PASSWORD=nebula
NEBULA_SPACE=xwrag

# Milvus 配置
xwrag_VECTOR_STORAGE=MilvusVectorDBStorage
MILVUS_URI=http://localhost:19530
MILVUS_DB_NAME=xwrag
```

### 3. 启动所有服务

```bash
# 使用 Docker Compose 启动（最简单）
docker-compose up -d

# 查看服务状态
docker-compose ps
```

### 4. 验证部署

```bash
# 检查 API 健康状态
curl http://localhost:8000/api/admin/health

# 访问 API 文档
open http://localhost:8000/docs
```

---

## 数据库部署

### NebulaGraph 部署

NebulaGraph 是一个分布式图数据库，本项目中经过性能优化，批量查询性能提升 40 倍。

#### 方式一：Docker 单机部署（推荐开发/测试）

```bash
# 创建目录
mkdir -p nebula-docker

# 下载 docker-compose.yml
cd nebula-docker
wget https://raw.githubusercontent.com/vesoft-inc/nebula-docker-compose/master/docker-compose.yaml

# 启动 NebulaGraph
docker-compose up -d

# 检查服务状态
docker-compose ps
```

服务端口：
- **Graph 服务**: 9669 (客户端连接)
- **Meta 服务**: 9559
- **Storage 服务**: 9779

#### 方式二：Docker Compose 集成部署

在项目的 `docker-compose.yml` 中添加：

```yaml
version: '3.8'

services:
  # NebulaGraph Meta 服务
  nebula-metad:
    image: vesoft/nebula-metad:v3.6.0
    container_name: nebula-metad
    environment:
      USER: root
      TZ: UTC
    command:
      - --meta_server_addrs=nebula-metad:9559
      - --local_ip=nebula-metad
      - --ws_ip=nebula-metad
      - --port=9559
      - --data_path=/data/meta
      - --log_dir=/logs
      - --v=0
      - --minloglevel=0
    healthcheck:
      test: ["CMD", "curl", "-f", "http://nebula-metad:19559/status"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 20s
    ports:
      - "9559:9559"
      - "19559:19559"
    volumes:
      - nebula_meta_data:/data/meta
      - nebula_meta_logs:/logs
    networks:
      - rag-network
    restart: unless-stopped

  # NebulaGraph Storage 服务
  nebula-storaged:
    image: vesoft/nebula-storaged:v3.6.0
    container_name: nebula-storaged
    environment:
      USER: root
      TZ: UTC
    command:
      - --meta_server_addrs=nebula-metad:9559
      - --local_ip=nebula-storaged
      - --ws_ip=nebula-storaged
      - --port=9779
      - --data_path=/data/storage
      - --log_dir=/logs
      - --v=0
      - --minloglevel=0
    depends_on:
      nebula-metad:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://nebula-storaged:19779/status"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 20s
    ports:
      - "9779:9779"
      - "19779:19779"
    volumes:
      - nebula_storage_data:/data/storage
      - nebula_storage_logs:/logs
    networks:
      - rag-network
    restart: unless-stopped

  # NebulaGraph Graph 服务
  nebula-graphd:
    image: vesoft/nebula-graphd:v3.6.0
    container_name: nebula-graphd
    environment:
      USER: root
      TZ: UTC
    command:
      - --meta_server_addrs=nebula-metad:9559
      - --port=9669
      - --local_ip=nebula-graphd
      - --ws_ip=nebula-graphd
      - --log_dir=/logs
      - --v=0
      - --minloglevel=0
    depends_on:
      nebula-metad:
        condition: service_healthy
      nebula-storaged:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://nebula-graphd:19669/status"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 20s
    ports:
      - "9669:9669"
      - "19669:19669"
    volumes:
      - nebula_graph_logs:/logs
    networks:
      - rag-network
    restart: unless-stopped

  # NebulaGraph Console (可选，用于管理)
  nebula-console:
    image: vesoft/nebula-console:v3.6.0
    container_name: nebula-console
    entrypoint: ""
    command:
      - sh
      - -c
      - |
        sleep 30;
        nebula-console -addr nebula-graphd -port 9669 -u root -p nebula
    depends_on:
      - nebula-graphd
    networks:
      - rag-network

volumes:
  nebula_meta_data:
  nebula_meta_logs:
  nebula_storage_data:
  nebula_storage_logs:
  nebula_graph_logs:

networks:
  rag-network:
    driver: bridge
```

#### 方式三：本地安装（生产环境）

**Ubuntu/Debian**:

```bash
# 添加 NebulaGraph 仓库
wget https://oss-cdn.nebula-graph.com.cn/package/3.6.0/nebula-graph-3.6.0.ubuntu2004.amd64.deb
sudo dpkg -i nebula-graph-3.6.0.ubuntu2004.amd64.deb

# 启动服务
sudo /usr/local/nebula/scripts/nebula.service start all

# 检查状态
sudo /usr/local/nebula/scripts/nebula.service status all
```

**CentOS/RHEL**:

```bash
# 下载 RPM 包
wget https://oss-cdn.nebula-graph.com.cn/package/3.6.0/nebula-graph-3.6.0.el8.x86_64.rpm
sudo rpm -ivh nebula-graph-3.6.0.el8.x86_64.rpm

# 启动服务
sudo /usr/local/nebula/scripts/nebula.service start all
```

#### 初始化 NebulaGraph Space

连接到 NebulaGraph 并创建 Space：

```bash
# 使用 nebula-console 连接
docker exec -it nebula-console nebula-console -addr nebula-graphd -port 9669 -u root -p nebula
```

在 console 中执行：

```cypher
-- 创建 Space
CREATE SPACE IF NOT EXISTS xwrag (
  partition_num = 10,
  replica_factor = 1,
  vid_type = FIXED_STRING(256)
);

-- 使用 Space
USE xwrag;

-- 创建 Tag (节点类型)
CREATE TAG IF NOT EXISTS entity (
  name string,
  description string,
  source_id string,
  created_at timestamp
);

-- 创建 Edge Type (关系类型)
CREATE EDGE IF NOT EXISTS relationship (
  description string,
  weight double,
  source_id string,
  created_at timestamp
);

-- 创建索引（重要！提升查询性能）
CREATE TAG INDEX IF NOT EXISTS entity_name_index ON entity(name(256));
CREATE TAG INDEX IF NOT EXISTS entity_source_index ON entity(source_id(256));
CREATE EDGE INDEX IF NOT EXISTS rel_weight_index ON relationship(weight);

-- 等待索引构建完成（约 20 秒）
SHOW TAG INDEXES;
SHOW EDGE INDEXES;
```

---

### Milvus 部署

Milvus 是一个开源向量数据库，专为大规模向量相似度搜索设计。

#### 方式一：Docker Standalone 部署（推荐开发/测试）

```bash
# 下载 docker-compose.yml
wget https://github.com/milvus-io/milvus/releases/download/v2.3.3/milvus-standalone-docker-compose.yml -O docker-compose-milvus.yml

# 启动 Milvus
docker-compose -f docker-compose-milvus.yml up -d

# 检查状态
docker-compose -f docker-compose-milvus.yml ps
```

服务端口：
- **Milvus 服务**: 19530
- **管理界面**: 9091 (Attu - 可选安装)

#### 方式二：Docker Compose 集成部署

在项目的 `docker-compose.yml` 中添加：

```yaml
version: '3.8'

services:
  # etcd - Milvus 元数据存储
  etcd:
    image: quay.io/coreos/etcd:v3.5.9
    container_name: milvus-etcd
    environment:
      - ETCD_AUTO_COMPACTION_MODE=revision
      - ETCD_AUTO_COMPACTION_RETENTION=1000
      - ETCD_QUOTA_BACKEND_BYTES=4294967296
      - ETCD_SNAPSHOT_COUNT=50000
    volumes:
      - milvus_etcd_data:/etcd
    command: etcd -advertise-client-urls=http://127.0.0.1:2379 -listen-client-urls http://0.0.0.0:2379 --data-dir /etcd
    networks:
      - rag-network
    restart: unless-stopped

  # MinIO - Milvus 对象存储
  minio:
    image: minio/minio:RELEASE.2023-03-20T20-16-18Z
    container_name: milvus-minio
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    volumes:
      - milvus_minio_data:/minio_data
    command: minio server /minio_data --console-address ":9001"
    ports:
      - "9000:9000"
      - "9001:9001"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 20s
      retries: 3
    networks:
      - rag-network
    restart: unless-stopped

  # Milvus Standalone
  milvus:
    image: milvusdb/milvus:v2.3.3
    container_name: milvus-standalone
    command: ["milvus", "run", "standalone"]
    environment:
      ETCD_ENDPOINTS: etcd:2379
      MINIO_ADDRESS: minio:9000
    volumes:
      - milvus_data:/var/lib/milvus
    ports:
      - "19530:19530"
      - "9091:9091"
    depends_on:
      - etcd
      - minio
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9091/healthz"]
      interval: 30s
      start_period: 90s
      timeout: 20s
      retries: 3
    networks:
      - rag-network
    restart: unless-stopped

  # Attu - Milvus 管理界面 (可选)
  attu:
    image: zilliz/attu:v2.3.3
    container_name: milvus-attu
    environment:
      MILVUS_URL: milvus:19530
    ports:
      - "3001:3000"
    depends_on:
      - milvus
    networks:
      - rag-network
    restart: unless-stopped

volumes:
  milvus_etcd_data:
  milvus_minio_data:
  milvus_data:

networks:
  rag-network:
    driver: bridge
```

#### 方式三：本地安装（生产环境）

使用 Helm 在 Kubernetes 上部署：

```bash
# 添加 Milvus Helm 仓库
helm repo add milvus https://milvus-io.github.io/milvus-helm/
helm repo update

# 安装 Milvus
helm install milvus milvus/milvus --set cluster.enabled=false

# 查看状态
kubectl get pods
```

或使用二进制安装：

```bash
# 下载 Milvus
wget https://github.com/milvus-io/milvus/releases/download/v2.3.3/milvus-standalone-linux-amd64.tar.gz

# 解压
tar -xzf milvus-standalone-linux-amd64.tar.gz
cd milvus-standalone

# 启动
./milvus run standalone
```

#### 验证 Milvus 连接

```python
from pymilvus import connections, utility

# 连接 Milvus
connections.connect("default", host="localhost", port="19530")

# 检查版本
print(utility.get_server_version())

# 列出所有集合
print(utility.list_collections())
```

---

## 应用服务部署

### Docker Compose 部署（推荐）

#### 完整的 docker-compose.yml

创建一个完整的 `docker-compose.yml` 文件，包含所有服务：

```yaml
version: '3.8'

services:
  # =====================
  # NebulaGraph 服务组
  # =====================
  nebula-metad:
    image: vesoft/nebula-metad:v3.6.0
    container_name: nebula-metad
    environment:
      USER: root
      TZ: UTC
    command:
      - --meta_server_addrs=nebula-metad:9559
      - --local_ip=nebula-metad
      - --ws_ip=nebula-metad
      - --port=9559
      - --data_path=/data/meta
      - --log_dir=/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://nebula-metad:19559/status"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 20s
    ports:
      - "9559:9559"
      - "19559:19559"
    volumes:
      - nebula_meta_data:/data/meta
      - nebula_meta_logs:/logs
    networks:
      - rag-network
    restart: unless-stopped

  nebula-storaged:
    image: vesoft/nebula-storaged:v3.6.0
    container_name: nebula-storaged
    environment:
      USER: root
      TZ: UTC
    command:
      - --meta_server_addrs=nebula-metad:9559
      - --local_ip=nebula-storaged
      - --ws_ip=nebula-storaged
      - --port=9779
      - --data_path=/data/storage
      - --log_dir=/logs
    depends_on:
      nebula-metad:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://nebula-storaged:19779/status"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 20s
    ports:
      - "9779:9779"
      - "19779:19779"
    volumes:
      - nebula_storage_data:/data/storage
      - nebula_storage_logs:/logs
    networks:
      - rag-network
    restart: unless-stopped

  nebula-graphd:
    image: vesoft/nebula-graphd:v3.6.0
    container_name: nebula-graphd
    environment:
      USER: root
      TZ: UTC
    command:
      - --meta_server_addrs=nebula-metad:9559
      - --port=9669
      - --local_ip=nebula-graphd
      - --ws_ip=nebula-graphd
      - --log_dir=/logs
    depends_on:
      nebula-metad:
        condition: service_healthy
      nebula-storaged:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://nebula-graphd:19669/status"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 20s
    ports:
      - "9669:9669"
      - "19669:19669"
    volumes:
      - nebula_graph_logs:/logs
    networks:
      - rag-network
    restart: unless-stopped

  # =====================
  # Milvus 服务组
  # =====================
  etcd:
    image: quay.io/coreos/etcd:v3.5.9
    container_name: milvus-etcd
    environment:
      - ETCD_AUTO_COMPACTION_MODE=revision
      - ETCD_AUTO_COMPACTION_RETENTION=1000
      - ETCD_QUOTA_BACKEND_BYTES=4294967296
      - ETCD_SNAPSHOT_COUNT=50000
    volumes:
      - milvus_etcd_data:/etcd
    command: etcd -advertise-client-urls=http://127.0.0.1:2379 -listen-client-urls http://0.0.0.0:2379 --data-dir /etcd
    networks:
      - rag-network
    restart: unless-stopped

  minio:
    image: minio/minio:RELEASE.2023-03-20T20-16-18Z
    container_name: milvus-minio
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    volumes:
      - milvus_minio_data:/minio_data
    command: minio server /minio_data --console-address ":9001"
    ports:
      - "9000:9000"
      - "9001:9001"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 20s
      retries: 3
    networks:
      - rag-network
    restart: unless-stopped

  milvus:
    image: milvusdb/milvus:v2.3.3
    container_name: milvus-standalone
    command: ["milvus", "run", "standalone"]
    environment:
      ETCD_ENDPOINTS: etcd:2379
      MINIO_ADDRESS: minio:9000
    volumes:
      - milvus_data:/var/lib/milvus
    ports:
      - "19530:19530"
      - "9091:9091"
    depends_on:
      - etcd
      - minio
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9091/healthz"]
      interval: 30s
      start_period: 90s
      timeout: 20s
      retries: 3
    networks:
      - rag-network
    restart: unless-stopped

  # =====================
  # RAG API 服务
  # =====================
  rag-api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: xwrag-api
    ports:
      - "8000:8000"
    environment:
      - PYTHONUNBUFFERED=1

      # LLM 配置
      - LLM_BINDING=${LLM_BINDING:-openai}
      - LLM_MODEL=${LLM_MODEL:-gpt-4o}
      - LLM_BINDING_HOST=${LLM_BINDING_HOST:-https://api.openai.com/v1}
      - LLM_BINDING_API_KEY=${LLM_BINDING_API_KEY}

      # Embedding 配置
      - EMBEDDING_BINDING=${EMBEDDING_BINDING:-openai}
      - EMBEDDING_MODEL=${EMBEDDING_MODEL:-text-embedding-3-large}
      - EMBEDDING_DIM=${EMBEDDING_DIM:-3072}
      - EMBEDDING_BINDING_API_KEY=${EMBEDDING_BINDING_API_KEY}

      # NebulaGraph 配置
      - xwrag_GRAPH_STORAGE=NebulaGraphStorage
      - NEBULA_HOST=nebula-graphd
      - NEBULA_PORT=9669
      - NEBULA_USER=root
      - NEBULA_PASSWORD=nebula
      - NEBULA_SPACE=xwrag

      # Milvus 配置
      - xwrag_VECTOR_STORAGE=MilvusVectorDBStorage
      - MILVUS_URI=http://milvus:19530
      - MILVUS_DB_NAME=xwrag

      # 查询配置
      - ENABLE_LLM_CACHE=true
      - TOP_K=40
      - CHUNK_TOP_K=20
      - MAX_ENTITY_TOKENS=6000
      - MAX_RELATION_TOKENS=8000
      - MAX_TOTAL_TOKENS=30000

      # 并发配置
      - MAX_ASYNC=4
      - MAX_PARALLEL_INSERT=2
      - EMBEDDING_FUNC_MAX_ASYNC=8

    depends_on:
      nebula-graphd:
        condition: service_healthy
      milvus:
        condition: service_healthy

    volumes:
      - ./inputs:/app/inputs
      - ./rag_storage:/app/rag_storage

    networks:
      - rag-network

    restart: unless-stopped

    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
        reservations:
          cpus: '2'
          memory: 4G

volumes:
  nebula_meta_data:
  nebula_meta_logs:
  nebula_storage_data:
  nebula_storage_logs:
  nebula_graph_logs:
  milvus_etcd_data:
  milvus_minio_data:
  milvus_data:

networks:
  rag-network:
    driver: bridge
```

#### 启动和管理

```bash
# 构建并启动所有服务
docker-compose up -d --build

# 查看所有服务状态
docker-compose ps

# 查看服务日志
docker-compose logs -f rag-api          # API 服务日志
docker-compose logs -f nebula-graphd    # NebulaGraph 日志
docker-compose logs -f milvus           # Milvus 日志

# 停止服务
docker-compose stop

# 重启服务
docker-compose restart rag-api

# 删除所有服务和数据（谨慎！）
docker-compose down -v
```

---

### 本地源码部署

适合开发环境或需要自定义配置的场景。

#### 1. 安装系统依赖

**Ubuntu/Debian**:

```bash
sudo apt-get update
sudo apt-get install -y build-essential python3-dev git curl wget
```

**macOS**:

```bash
brew install python@3.10 git
```

#### 2. 创建 Python 虚拟环境

```bash
# 使用 conda（推荐）
conda env create -f environment.yml
conda activate lightrag

# 或使用 venv
python3.10 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

#### 3. 安装 Python 依赖

```bash
# 安装核心库
pip install -e .

# 安装 API 相关依赖
pip install -e ".[api]"

# 安装额外依赖
pip install nebula3-python pymilvus
```

#### 4. 启动外部数据库

确保 NebulaGraph 和 Milvus 已经运行（可使用 Docker）：

```bash
# 启动 NebulaGraph
docker-compose up -d nebula-metad nebula-storaged nebula-graphd

# 启动 Milvus
docker-compose up -d etcd minio milvus
```

#### 5. 配置环境变量

编辑 `.env` 文件：

```bash
# NebulaGraph 配置（连接到本地 Docker）
xwrag_GRAPH_STORAGE=NebulaGraphStorage
NEBULA_HOST=localhost
NEBULA_PORT=9669
NEBULA_USER=root
NEBULA_PASSWORD=nebula
NEBULA_SPACE=xwrag

# Milvus 配置（连接到本地 Docker）
xwrag_VECTOR_STORAGE=MilvusVectorDBStorage
MILVUS_URI=http://localhost:19530
MILVUS_DB_NAME=xwrag

# LLM 和 Embedding 配置
LLM_BINDING=openai
LLM_MODEL=gpt-4o
LLM_BINDING_API_KEY=sk-your-api-key

EMBEDDING_BINDING=openai
EMBEDDING_MODEL=text-embedding-3-large
EMBEDDING_DIM=3072
EMBEDDING_BINDING_API_KEY=sk-your-api-key
```

#### 6. 初始化数据库

```bash
# 初始化 NebulaGraph Space
python -c "
from xwrag.kg.nebula_impl import NebulaGraphStorage
import asyncio

async def init():
    storage = NebulaGraphStorage(
        namespace='default',
        global_config={},
        embedding_func=None,
        workspace='xwrag'
    )
    await storage._init_space()
    print('NebulaGraph initialized!')

asyncio.run(init())
"
```

#### 7. 启动 API 服务

**开发模式**（自动重载）:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**生产模式**（使用 Gunicorn）:

```bash
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 300 \
  --access-logfile - \
  --error-logfile -
```

---

## 配置说明

### NebulaGraph 配置详解

```bash
# 存储类型
xwrag_GRAPH_STORAGE=NebulaGraphStorage

# 连接配置
NEBULA_HOST=localhost              # NebulaGraph 主机地址
NEBULA_PORT=9669                   # Graph 服务端口
NEBULA_USER=root                   # 用户名
NEBULA_PASSWORD=nebula             # 密码

# Space 配置
NEBULA_SPACE=xwrag                 # Space 名称（数据库名）

# 可选配置
NEBULA_WORKSPACE=base              # 工作空间名称（多租户隔离）
```

**重要说明**：

- **Space**: NebulaGraph 的数据库概念，类似于 MySQL 的 database
- **Workspace**: 用于多租户隔离，每个 workspace 对应一个独立的 Space
- **性能优化**: 本项目中 NebulaGraph 经过批量查询优化，性能提升 40 倍

### Milvus 配置详解

```bash
# 存储类型
xwrag_VECTOR_STORAGE=MilvusVectorDBStorage

# 连接配置
MILVUS_URI=http://localhost:19530  # Milvus 服务地址
MILVUS_DB_NAME=xwrag               # 数据库名称

# 认证配置（如果启用）
MILVUS_USER=root                   # 用户名（可选）
MILVUS_PASSWORD=your-password      # 密码（可选）
MILVUS_TOKEN=your-token            # Token（云服务）

# 可选配置
MILVUS_WORKSPACE=base              # 工作空间（多租户）
```

**Milvus 索引配置**（在代码中设置）:

```python
# 推荐的索引参数
INDEX_TYPE = "HNSW"                # 索引类型：HNSW, IVF_FLAT, IVF_SQ8
METRIC_TYPE = "COSINE"             # 距离度量：COSINE, L2, IP
INDEX_PARAMS = {
    "M": 16,                       # HNSW M 参数
    "efConstruction": 200          # 构建参数
}
SEARCH_PARAMS = {
    "ef": 100                      # 搜索参数
}
```

### 其他存储配置

```bash
# KV 存储（可选，用于缓存）
xwrag_KV_STORAGE=JsonKVStorage              # 默认 JSON 文件
# xwrag_KV_STORAGE=RedisKVStorage           # 生产环境推荐 Redis

# 文档状态存储
xwrag_DOC_STATUS_STORAGE=JsonDocStatusStorage
# xwrag_DOC_STATUS_STORAGE=RedisDocStatusStorage

# Redis 配置（如果使用）
REDIS_URI=redis://localhost:6379
REDIS_MAX_CONNECTIONS=100
```

### 查询和性能配置

```bash
# 检索参数
TOP_K=40                          # 从图中检索的实体/关系数量
CHUNK_TOP_K=20                    # 向量搜索返回的 chunk 数量
COSINE_THRESHOLD=0.2              # 向量相似度阈值
MAX_ENTITY_TOKENS=6000            # 实体 token 限制
MAX_RELATION_TOKENS=8000          # 关系 token 限制
MAX_TOTAL_TOKENS=30000            # 总 token 限制

# 并发配置
MAX_ASYNC=4                       # LLM 并发请求数
MAX_PARALLEL_INSERT=2             # 并行处理文档数
EMBEDDING_FUNC_MAX_ASYNC=8        # Embedding 并发数
EMBEDDING_BATCH_NUM=10            # Embedding 批次大小

# 缓存配置
ENABLE_LLM_CACHE=true             # 启用 LLM 缓存
ENABLE_LLM_CACHE_FOR_EXTRACT=true # 启用提取缓存
```

---

## 验证部署

### 1. 检查服务状态

```bash
# 检查 Docker 容器
docker-compose ps

# 应该看到所有服务都是 "Up" 状态
```

### 2. 测试 NebulaGraph 连接

```bash
# 使用 nebula-console 连接
docker run --rm -it --network rag-network \
  vesoft/nebula-console:v3.6.0 \
  -addr nebula-graphd -port 9669 -u root -p nebula

# 在 console 中执行
USE xwrag;
SHOW TAGS;
SHOW EDGES;
```

或使用 Python：

```python
from nebula3.gclient.net import ConnectionPool
from nebula3.Config import Config

config = Config()
config.max_connection_pool_size = 10

pool = ConnectionPool()
pool.init([('localhost', 9669)], config)

session = pool.get_session('root', 'nebula')
result = session.execute('SHOW SPACES')
print(result)

pool.close()
```

### 3. 测试 Milvus 连接

```python
from pymilvus import connections, utility

# 连接 Milvus
connections.connect("default", host="localhost", port="19530")

# 检查连接
print("Milvus version:", utility.get_server_version())
print("Collections:", utility.list_collections())

connections.disconnect("default")
```

### 4. 测试 API 服务

```bash
# 健康检查
curl http://localhost:8000/api/admin/health

# 预期输出
{
  "status": "healthy",
  "version": "1.0.0",
  "storage": {
    "graph": "NebulaGraphStorage",
    "vector": "MilvusVectorDBStorage"
  }
}
```

### 5. 测试文档上传

```bash
# 创建测试文档
echo "人工智能是计算机科学的一个分支。" > test.txt

# 上传文档
curl -X POST "http://localhost:8000/api/documents/upload" \
  -F "file=@test.txt" \
  -F "description=测试文档"

# 查看处理状态
curl "http://localhost:8000/api/documents/status"
```

### 6. 测试查询

```bash
# 执行查询
curl -X POST "http://localhost:8000/api/query/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "什么是人工智能？",
    "mode": "hybrid"
  }'
```

### 7. 访问管理界面

- **API 文档**: http://localhost:8000/docs
- **Milvus 管理 (Attu)**: http://localhost:3001 (如果启用)
- **MinIO 控制台**: http://localhost:9001 (用户: minioadmin, 密码: minioadmin)

---

## 性能优化

### NebulaGraph 性能优化

#### 1. 索引优化

确保创建了必要的索引：

```cypher
USE xwrag;

-- 实体名称索引（重要！）
CREATE TAG INDEX IF NOT EXISTS entity_name_index ON entity(name(256));

-- 源文档索引
CREATE TAG INDEX IF NOT EXISTS entity_source_index ON entity(source_id(256));

-- 关系权重索引
CREATE EDGE INDEX IF NOT EXISTS rel_weight_index ON relationship(weight);

-- 查看索引状态
SHOW TAG INDEXES;
SHOW EDGE INDEXES;

-- 重建索引（如果需要）
REBUILD TAG INDEX entity_name_index;
```

#### 2. 配置优化

编辑 NebulaGraph 配置文件 `nebula-graphd.conf`:

```ini
# 增加查询超时时间
--session_idle_timeout_secs=28800

# 增加最大连接数
--num_accept_threads=4
--num_netio_threads=4

# 优化查询执行
--enable_experimental_feature=true
--max_allowed_query_size=4194304
```

#### 3. 批量操作优化

本项目已内置批量查询优化，性能提升 40 倍。关键代码在 `xwrag/kg/nebula_impl.py`:

```python
# 批量边查询（一次查询多个实体的所有边）
async def get_edges_batch(self, entity_ids: List[str]) -> Dict[str, List[Edge]]:
    """批量获取多个实体的边，比循环调用快 40 倍"""
    # 使用 IN 操作符一次性查询
    query = f"""
        USE {self._space_name};
        MATCH (v:entity)-[e:relationship]->(v2:entity)
        WHERE id(v) IN {entity_ids}
        RETURN id(v) AS src, e, id(v2) AS dst;
    """
    # ... 执行查询
```

### Milvus 性能优化

#### 1. 选择合适的索引类型

```python
# 高性能场景（内存充足）
index_params = {
    "index_type": "HNSW",
    "metric_type": "COSINE",
    "params": {
        "M": 16,              # 连接数，越大精度越高但内存占用越大
        "efConstruction": 200 # 构建参数，影响构建速度和精度
    }
}

# 内存优化场景
index_params = {
    "index_type": "IVF_SQ8",
    "metric_type": "COSINE",
    "params": {
        "nlist": 1024        # 聚类中心数量
    }
}

# 平衡场景
index_params = {
    "index_type": "IVF_FLAT",
    "metric_type": "COSINE",
    "params": {
        "nlist": 1024
    }
}
```

#### 2. 搜索参数优化

```python
# 高精度搜索
search_params = {
    "metric_type": "COSINE",
    "params": {
        "ef": 200           # 搜索参数，越大精度越高但速度越慢
    }
}

# 快速搜索
search_params = {
    "metric_type": "COSINE",
    "params": {
        "ef": 50
    }
}
```

#### 3. 内存配置

编辑 `milvus.yaml`:

```yaml
# 缓存配置
cache:
  cache_size: 16GB          # 缓存大小

# 插入缓冲区
rootCoord:
  dmlChannelNum: 16

# 查询节点配置
queryNode:
  cacheEnabled: true
  cacheMemoryLimit: 8GB
```

### 应用服务优化

#### 1. 并发配置优化

根据服务器资源调整 `.env` 配置：

```bash
# 4 核 8GB 内存
MAX_ASYNC=4
MAX_PARALLEL_INSERT=2
EMBEDDING_FUNC_MAX_ASYNC=8

# 8 核 16GB 内存
MAX_ASYNC=8
MAX_PARALLEL_INSERT=4
EMBEDDING_FUNC_MAX_ASYNC=16

# 16 核 32GB 内存
MAX_ASYNC=16
MAX_PARALLEL_INSERT=8
EMBEDDING_FUNC_MAX_ASYNC=32
```

#### 2. Gunicorn 配置

```bash
# 计算 worker 数量：2 * CPU 核心数 + 1
WORKERS=$((2 * $(nproc) + 1))

gunicorn app.main:app \
  --workers $WORKERS \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 300 \
  --max-requests 1000 \
  --max-requests-jitter 100 \
  --access-logfile - \
  --error-logfile -
```

#### 3. 缓存策略

```bash
# 启用所有缓存
ENABLE_LLM_CACHE=true
ENABLE_LLM_CACHE_FOR_EXTRACT=true

# 使用 Redis 作为缓存后端（推荐生产环境）
xwrag_KV_STORAGE=RedisKVStorage
REDIS_URI=redis://localhost:6379
REDIS_MAX_CONNECTIONS=100
```

---

## 故障排查

### NebulaGraph 常见问题

#### 1. 连接失败

**错误信息**:
```
Error: Failed to connect to NebulaGraph at localhost:9669
```

**解决方法**:

```bash
# 检查服务状态
docker-compose ps nebula-graphd

# 检查端口是否开放
telnet localhost 9669

# 查看日志
docker-compose logs nebula-graphd

# 重启服务
docker-compose restart nebula-graphd
```

#### 2. Space 不存在

**错误信息**:
```
Error: Space not exists: xwrag
```

**解决方法**:

```bash
# 连接 NebulaGraph
docker exec -it nebula-console nebula-console \
  -addr nebula-graphd -port 9669 -u root -p nebula

# 创建 Space
CREATE SPACE IF NOT EXISTS xwrag (
  partition_num = 10,
  replica_factor = 1,
  vid_type = FIXED_STRING(256)
);

# 等待 Space 就绪（约 20 秒）
SHOW SPACES;
USE xwrag;
```

#### 3. 查询超时

**解决方法**:

```bash
# 增加环境变量中的超时时间
NEBULA_TIMEOUT=60

# 或在 Docker Compose 中设置
services:
  nebula-graphd:
    command:
      - --session_idle_timeout_secs=28800
```

#### 4. 索引未生效

**解决方法**:

```cypher
-- 检查索引状态
SHOW TAG INDEX STATUS;

-- 如果索引状态不是 FINISHED，重建索引
REBUILD TAG INDEX entity_name_index;

-- 等待索引重建完成
SHOW TAG INDEX STATUS;
```

### Milvus 常见问题

#### 1. 连接失败

**错误信息**:
```
Error: Failed to connect to Milvus at localhost:19530
```

**解决方法**:

```bash
# 检查 Milvus 服务状态
docker-compose ps milvus

# 检查依赖服务
docker-compose ps etcd minio

# 查看 Milvus 日志
docker-compose logs milvus

# 检查健康状态
curl http://localhost:9091/healthz

# 重启服务（确保依赖先启动）
docker-compose restart etcd minio
docker-compose restart milvus
```

#### 2. 集合创建失败

**错误信息**:
```
Error: Collection already exists
```

**解决方法**:

```python
from pymilvus import connections, utility, Collection

connections.connect("default", host="localhost", port="19530")

# 删除已存在的集合
if utility.has_collection("your_collection"):
    collection = Collection("your_collection")
    collection.drop()

# 重新创建集合
# ... 创建代码
```

#### 3. 搜索结果为空

**可能原因**:
- 数据未刷新到磁盘
- 索引未构建

**解决方法**:

```python
from pymilvus import Collection

collection = Collection("your_collection")

# 刷新数据
collection.flush()

# 加载集合到内存
collection.load()

# 检查数据量
print(collection.num_entities)
```

#### 4. 内存不足

**解决方法**:

```yaml
# 在 docker-compose.yml 中限制内存
services:
  milvus:
    deploy:
      resources:
        limits:
          memory: 8G
```

或优化索引类型：

```python
# 使用内存优化的索引
index_params = {
    "index_type": "IVF_SQ8",  # 量化索引，节省内存
    "metric_type": "COSINE",
    "params": {"nlist": 1024}
}
```

### 应用服务常见问题

#### 1. 导入错误

**错误信息**:
```
ModuleNotFoundError: No module named 'nebula3'
```

**解决方法**:

```bash
# 安装缺失的包
pip install nebula3-python pymilvus

# 或重新安装所有依赖
pip install -e ".[api]"
```

#### 2. 环境变量未生效

**解决方法**:

```bash
# 确保 .env 文件在正确位置
ls -la .env

# 手动加载环境变量
export $(cat .env | xargs)

# 或在 Python 中显式加载
from dotenv import load_dotenv
load_dotenv(override=True)
```

#### 3. 并发问题

**错误信息**:
```
Error: Too many concurrent requests
```

**解决方法**:

```bash
# 减少并发配置
MAX_ASYNC=2
MAX_PARALLEL_INSERT=1
EMBEDDING_FUNC_MAX_ASYNC=4

# 增加数据库连接池
NEO4J_MAX_CONNECTION_POOL_SIZE=100
REDIS_MAX_CONNECTIONS=100
```

---

## 监控和维护

### 日志管理

#### 查看服务日志

```bash
# API 服务日志
docker-compose logs -f rag-api

# NebulaGraph 日志
docker-compose logs -f nebula-graphd
docker-compose logs -f nebula-storaged

# Milvus 日志
docker-compose logs -f milvus

# 所有服务日志
docker-compose logs -f

# 最近 100 行日志
docker-compose logs --tail=100 rag-api
```

#### 日志配置

在 `.env` 中配置日志级别：

```bash
LOG_LEVEL=INFO          # DEBUG, INFO, WARNING, ERROR
VERBOSE=True            # 详细日志
LOG_MAX_BYTES=10485760  # 10MB
LOG_BACKUP_COUNT=5      # 保留 5 个备份
```

### 性能监控

#### 1. NebulaGraph 监控

```bash
# 查看 NebulaGraph 状态
curl http://localhost:19669/status

# 查看 Meta 服务状态
curl http://localhost:19559/status

# 查看 Storage 服务状态
curl http://localhost:19779/status
```

在 NebulaGraph Console 中：

```cypher
-- 查看 Space 统计信息
USE xwrag;
SHOW STATS;

-- 查看任务状态
SHOW JOBS;

-- 查看查询慢日志
SHOW QUERIES;
```

#### 2. Milvus 监控

```bash
# 查看 Milvus 健康状态
curl http://localhost:9091/healthz

# 查看 Milvus 指标（Prometheus 格式）
curl http://localhost:9091/metrics
```

使用 Python 客户端：

```python
from pymilvus import connections, utility

connections.connect("default", host="localhost", port="19530")

# 查看所有集合
print(utility.list_collections())

# 查看集合统计
from pymilvus import Collection
collection = Collection("your_collection")
print(f"Entities: {collection.num_entities}")
print(f"Index: {collection.index().params}")
```

#### 3. API 服务监控

```bash
# 健康检查
curl http://localhost:8000/api/admin/health

# 查看系统信息
curl http://localhost:8000/api/admin/info
```

### 数据备份

#### 1. NebulaGraph 备份

```bash
# 使用快照备份（推荐）
docker exec nebula-storaged \
  /usr/local/nebula/bin/db_admin \
  --method=snapshot \
  --op=create \
  --snapshot_name=backup_$(date +%Y%m%d)

# 备份配置和数据目录
docker run --rm -v nebula_storage_data:/source -v $(pwd)/backups:/backup \
  alpine tar czf /backup/nebula-data-$(date +%Y%m%d).tar.gz -C /source .
```

#### 2. Milvus 备份

```bash
# 备份 Milvus 数据目录
docker run --rm -v milvus_data:/source -v $(pwd)/backups:/backup \
  alpine tar czf /backup/milvus-data-$(date +%Y%m%d).tar.gz -C /source .

# 备份 MinIO 数据
docker run --rm -v milvus_minio_data:/source -v $(pwd)/backups:/backup \
  alpine tar czf /backup/minio-data-$(date +%Y%m%d).tar.gz -C /source .

# 备份 etcd 数据
docker run --rm -v milvus_etcd_data:/source -v $(pwd)/backups:/backup \
  alpine tar czf /backup/etcd-data-$(date +%Y%m%d).tar.gz -C /source .
```

#### 3. 自动备份脚本

创建 `backup.sh`:

```bash
#!/bin/bash
set -e

BACKUP_DIR="./backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

echo "Starting backup at $(date)"

# 备份 NebulaGraph
echo "Backing up NebulaGraph..."
docker run --rm \
  -v nebula_storage_data:/source \
  -v $BACKUP_DIR:/backup \
  alpine tar czf /backup/nebula-$DATE.tar.gz -C /source .

# 备份 Milvus
echo "Backing up Milvus..."
docker run --rm \
  -v milvus_data:/source \
  -v $BACKUP_DIR:/backup \
  alpine tar czf /backup/milvus-$DATE.tar.gz -C /source .

# 删除 7 天前的备份
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed at $(date)"
```

设置定时任务：

```bash
# 添加到 crontab
crontab -e

# 每天凌晨 2 点执行备份
0 2 * * * /path/to/backup.sh >> /var/log/rag-backup.log 2>&1
```

### 数据恢复

#### 1. NebulaGraph 恢复

```bash
# 停止服务
docker-compose stop nebula-storaged

# 恢复数据
docker run --rm \
  -v nebula_storage_data:/target \
  -v $(pwd)/backups:/backup \
  alpine tar xzf /backup/nebula-20241201.tar.gz -C /target

# 重启服务
docker-compose start nebula-storaged
docker-compose restart nebula-graphd
```

#### 2. Milvus 恢复

```bash
# 停止服务
docker-compose stop milvus

# 恢复数据
docker run --rm \
  -v milvus_data:/target \
  -v $(pwd)/backups:/backup \
  alpine tar xzf /backup/milvus-20241201.tar.gz -C /target

# 重启服务
docker-compose start milvus
```

### 清理和维护

#### 定期清理

```bash
# 清理 Docker 系统
docker system prune -a

# 清理未使用的卷
docker volume prune

# 清理 NebulaGraph 过期数据（在 Console 中）
USE xwrag;
CLEAR SPACE xwrag;

# 清理 Milvus 过期集合
from pymilvus import connections, utility, Collection
connections.connect("default", host="localhost", port="19530")

for name in utility.list_collections():
    collection = Collection(name)
    collection.drop()
```

#### 性能分析

```bash
# 分析 NebulaGraph 查询
USE xwrag;
PROFILE MATCH (v:entity)-[e:relationship]->(v2)
WHERE id(v) == "entity_id"
RETURN v, e, v2;

# 查看 Milvus 集合信息
from pymilvus import Collection
collection = Collection("your_collection")
print(collection.describe())
```

---

## 安全建议

### 1. 网络安全

```yaml
# docker-compose.yml 中限制端口暴露
services:
  nebula-graphd:
    ports:
      - "127.0.0.1:9669:9669"  # 仅本地访问

  milvus:
    ports:
      - "127.0.0.1:19530:19530"  # 仅本地访问
```

### 2. 认证配置

```bash
# 修改默认密码
docker exec -it nebula-console nebula-console \
  -addr nebula-graphd -port 9669 -u root -p nebula

# 在 console 中
ALTER USER root WITH PASSWORD 'new-strong-password';
```

### 3. 使用环境变量

```bash
# 不要在配置文件中硬编码密码
NEBULA_PASSWORD=${NEBULA_PASSWORD}
LLM_BINDING_API_KEY=${LLM_BINDING_API_KEY}

# 使用 Docker secrets
docker secret create nebula_password nebula_password.txt
```

### 4. 防火墙配置

```bash
# 仅允许必要端口
sudo ufw allow 8000/tcp   # API
sudo ufw deny 9669/tcp    # NebulaGraph（仅内部）
sudo ufw deny 19530/tcp   # Milvus（仅内部）
```

---

## 附录

### 常用命令速查

```bash
# Docker Compose
docker-compose up -d              # 启动所有服务
docker-compose ps                 # 查看状态
docker-compose logs -f SERVICE    # 查看日志
docker-compose restart SERVICE    # 重启服务
docker-compose stop               # 停止服务
docker-compose down -v            # 删除所有（包括数据）

# NebulaGraph
docker exec -it nebula-console nebula-console \
  -addr nebula-graphd -port 9669 -u root -p nebula

# Milvus
curl http://localhost:9091/healthz

# API
curl http://localhost:8000/api/admin/health
curl http://localhost:8000/docs
```

### 端口列表

| 服务 | 端口 | 说明 |
|------|------|------|
| API 服务 | 8000 | FastAPI HTTP |
| NebulaGraph Graph | 9669 | 客户端连接 |
| NebulaGraph Meta | 9559 | Meta 服务 |
| NebulaGraph Storage | 9779 | Storage 服务 |
| Milvus | 19530 | 向量数据库 |
| Milvus Admin | 9091 | 管理接口 |
| MinIO | 9000 | 对象存储 |
| MinIO Console | 9001 | 管理界面 |
| Attu | 3001 | Milvus UI |

### 资源链接

- **NebulaGraph 文档**: https://docs.nebula-graph.io/
- **Milvus 文档**: https://milvus.io/docs/
- **FastAPI 文档**: https://fastapi.tiangolo.com/
- **项目仓库**: https://github.com/your-org/myRAG

---

## 联系支持

如遇到问题，请：

1. 查看本文档的故障排查部分
2. 查看项目 Issues: https://github.com/your-org/myRAG/issues
3. 查看日志文件定位问题
4. 提交新 Issue 并附上详细日志和错误信息

---

**祝您部署顺利！**
