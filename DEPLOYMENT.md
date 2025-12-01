# xwRAG 部署文档

## 目录

- [系统概述](#系统概述)
- [系统架构](#系统架构)
- [系统要求](#系统要求)
- [快速开始](#快速开始)
- [部署方式](#部署方式)
  - [Docker Compose 部署 (推荐)](#docker-compose-部署-推荐)
  - [本地源码部署](#本地源码部署)
  - [生产环境部署](#生产环境部署)
- [配置说明](#配置说明)
- [存储后端配置](#存储后端配置)
- [性能优化](#性能优化)
- [监控和日志](#监控和日志)
- [故障排查](#故障排查)
- [升级和维护](#升级和维护)

---

## 系统概述

xwRAG 是一个基于知识图谱和向量数据库的高性能 RAG（检索增强生成）系统，支持：

- **多模态文档处理**：PDF、DOCX、TXT 等格式
- **混合检索**：图数据库（知识图谱）+ 向量数据库（语义搜索）
- **灵活的存储后端**：支持 Neo4j、NebulaGraph、Milvus、Qdrant 等
- **多种 LLM 支持**：OpenAI、Ollama、Azure OpenAI 等
- **Embedding 模型**：本地模型或 API (OpenAI, Jina, 智谱等)
- **RESTful API**：FastAPI 构建的高性能 API
- **WebSocket 支持**：实时查询和流式响应

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
│  └──────────────┴──────────────┴──────────────┴───────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                    xwRAG 核心库 (xwrag/)                       │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  知识图谱处理 (operate.py)                              │    │
│  │  - 实体/关系抽取                                        │    │
│  │  - 向量化                                              │    │
│  │  - 混合检索                                            │    │
│  └──────────────────────────────────────────────────────┘    │
└───┬────────────┬─────────────────┬─────────────────┬────────┘
    │            │                 │                 │
┌───▼────┐  ┌───▼──────┐  ┌──────▼──────┐  ┌───────▼────────┐
│  图数据库│  │  向量数据库│  │   LLM 服务   │  │ Embedding 服务 │
│ Neo4j  │  │  Milvus  │  │   OpenAI    │  │  本地模型/API  │
│Nebula  │  │  Qdrant  │  │   Ollama    │  │               │
│Memgraph│  │  Faiss   │  │   Azure     │  │               │
└────────┘  └──────────┘  └─────────────┘  └────────────────┘
```

---

## 系统要求

### 最低配置

- **CPU**: 4 核
- **内存**: 8 GB RAM
- **磁盘**: 50 GB 可用空间
- **操作系统**: Linux (推荐 Ubuntu 20.04+) / macOS / Windows (WSL2)

### 推荐配置（生产环境）

- **CPU**: 8 核 +
- **内存**: 16 GB RAM +
- **磁盘**: 100 GB+ SSD
- **GPU**: 可选，用于本地 Embedding 模型加速

### 软件依赖

- **Python**: 3.10+
- **Docker**: 20.10+ (Docker Compose 部署)
- **Docker Compose**: 2.0+ (Docker Compose 部署)

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

# 编辑 .env 文件，配置必要的参数
nano .env
```

**必须配置的关键参数**：

```bash
# LLM 配置（必须）
LLM_BINDING=openai
LLM_MODEL=gpt-4o
LLM_BINDING_HOST=https://api.openai.com/v1
LLM_BINDING_API_KEY=sk-your-api-key-here

# Embedding 配置（必须）
EMBEDDING_BINDING=openai
EMBEDDING_MODEL=text-embedding-3-large
EMBEDDING_DIM=3072
EMBEDDING_BINDING_API_KEY=sk-your-api-key-here

# 图数据库配置（推荐生产环境）
xwrag_GRAPH_STORAGE=Neo4JStorage
NEO4J_URI=neo4j://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-secure-password

# 向量数据库配置（推荐生产环境）
xwrag_VECTOR_STORAGE=MilvusVectorDBStorage
MILVUS_URI=http://localhost:19530
```

### 3. 启动服务

**使用 Docker Compose（推荐）**:

```bash
./deploy.sh start
```

**或使用本地开发模式**:

```bash
# 安装依赖
pip install -e ".[api]"

# 启动 API 服务
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. 验证部署

访问以下 URL：

- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/api/admin/health
- **Neo4j 控制台** (如果使用): http://localhost:7474

---

## 部署方式

### Docker Compose 部署 (推荐)

Docker Compose 方式最简单，适合开发和中小规模生产部署。

#### 1. 配置 docker-compose.yml

查看并修改 `docker-compose.yml`：

```yaml
version: '3.8'

services:
  rag-api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - LLM_MODEL=gpt-4o
      - LLM_BINDING_API_KEY=${LLM_BINDING_API_KEY}
      # ... 其他环境变量
    depends_on:
      - neo4j
    restart: unless-stopped

  neo4j:
    image: neo4j:5.20.0
    ports:
      - "7474:7474"
      - "7687:7687"
    volumes:
      - neo4j_data:/var/lib/neo4j/data
    restart: unless-stopped
```

#### 2. 使用部署脚本

项目提供了 `deploy.sh` 脚本简化部署流程：

```bash
# 查看帮助
./deploy.sh help

# 构建镜像
./deploy.sh build

# 启动服务
./deploy.sh start

# 查看日志
./deploy.sh logs

# 查看 Neo4j 日志
./deploy.sh logs neo4j

# 查看服务状态
./deploy.sh status

# 重启服务
./deploy.sh restart

# 进入容器调试
./deploy.sh exec bash

# 停止服务
./deploy.sh stop

# 清理所有数据（谨慎！）
./deploy.sh clean
```

#### 3. 环境变量配置

在 `.env` 文件中配置：

```bash
# LLM 配置
LLM_MODEL=gpt-4o
LLM_BINDING_HOST=https://api.openai.com/v1
LLM_BINDING_API_KEY=sk-xxxxxxxx

# Embedding 配置
EMBEDDING_MODEL=text-embedding-3-large
EMBEDDING_DIM=3072
EMBEDDING_BINDING_API_KEY=sk-xxxxxxxx

# Neo4j 密码
NEO4J_PASSWORD=your-secure-password

# 服务端口（可选）
PORT=8000
```

#### 4. 验证部署

```bash
# 检查容器状态
docker-compose ps

# 查看日志
docker-compose logs -f rag-api

# 测试 API
curl http://localhost:8000/api/admin/health
```

---

### 本地源码部署

适合开发环境或需要自定义配置的场景。

#### 1. 安装 Python 依赖

```bash
# 创建虚拟环境（推荐）
python3.10 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装核心库
pip install -e .

# 安装 API 相关依赖
pip install -e ".[api]"
```

#### 2. 启动外部服务

**启动 Neo4j**:

```bash
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your-password \
  -v neo4j_data:/var/lib/neo4j/data \
  neo4j:5.20.0
```

**启动 Milvus** (可选):

```bash
docker run -d \
  --name milvus-standalone \
  -p 19530:19530 \
  -v milvus_data:/var/lib/milvus \
  milvusdb/milvus:latest
```

#### 3. 配置环境变量

```bash
# 复制配置文件
cp env.example .env

# 编辑配置
nano .env
```

#### 4. 启动 API 服务

**开发模式**（自动重载）:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**生产模式**（使用 Gunicorn + Uvicorn Workers）:

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

### 生产环境部署

#### 1. 使用外部数据库服务

生产环境建议使用托管的数据库服务：

**Neo4j Aura（托管 Neo4j）**:

```bash
xwrag_GRAPH_STORAGE=Neo4JStorage
NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password
```

**Milvus Cloud**:

```bash
xwrag_VECTOR_STORAGE=MilvusVectorDBStorage
MILVUS_URI=https://xxxxx.milvus.io:19530
MILVUS_TOKEN=your-token
```

#### 2. 反向代理配置（Nginx）

创建 Nginx 配置 `/etc/nginx/sites-available/rag-api`:

```nginx
upstream rag_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name your-domain.com;

    # 重定向到 HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL 证书配置
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # SSL 安全配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # 请求体大小限制（文件上传）
    client_max_body_size 100M;

    location / {
        proxy_pass http://rag_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket 支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # 超时配置
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}
```

启用配置：

```bash
sudo ln -s /etc/nginx/sites-available/rag-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### 3. Systemd 服务配置

创建服务文件 `/etc/systemd/system/rag-api.service`:

```ini
[Unit]
Description=RAG API Service
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/opt/myRAG
Environment="PATH=/opt/myRAG/venv/bin"
EnvironmentFile=/opt/myRAG/.env
ExecStart=/opt/myRAG/venv/bin/gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 127.0.0.1:8000 \
  --timeout 300 \
  --access-logfile /var/log/rag-api/access.log \
  --error-logfile /var/log/rag-api/error.log
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启用服务：

```bash
# 创建日志目录
sudo mkdir -p /var/log/rag-api
sudo chown www-data:www-data /var/log/rag-api

# 启用并启动服务
sudo systemctl daemon-reload
sudo systemctl enable rag-api
sudo systemctl start rag-api

# 查看状态
sudo systemctl status rag-api

# 查看日志
sudo journalctl -u rag-api -f
```

#### 4. 容器编排（Kubernetes）

对于大规模部署，可以使用 Kubernetes。示例配置：

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rag-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: rag-api
  template:
    metadata:
      labels:
        app: rag-api
    spec:
      containers:
      - name: rag-api
        image: your-registry/rag-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: LLM_BINDING_API_KEY
          valueFrom:
            secretKeyRef:
              name: rag-secrets
              key: llm-api-key
        resources:
          requests:
            memory: "4Gi"
            cpu: "2"
          limits:
            memory: "8Gi"
            cpu: "4"
        livenessProbe:
          httpGet:
            path: /api/admin/health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: rag-api-service
spec:
  selector:
    app: rag-api
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

---

## 配置说明

### 核心配置参数

#### 服务器配置

```bash
# 服务绑定
HOST=0.0.0.0
PORT=9621

# Web UI 配置
WEBUI_TITLE='My Graph KB'
WEBUI_DESCRIPTION="Simple and Fast Graph Based RAG System"

# Worker 配置
WORKERS=4          # Gunicorn workers 数量
TIMEOUT=150        # 请求超时时间（秒）

# CORS 配置
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
```

#### LLM 配置

**OpenAI**:

```bash
LLM_BINDING=openai
LLM_MODEL=gpt-4o
LLM_BINDING_HOST=https://api.openai.com/v1
LLM_BINDING_API_KEY=sk-your-api-key

# 可选参数
OPENAI_LLM_TEMPERATURE=0.9
OPENAI_LLM_MAX_COMPLETION_TOKENS=9000
```

**Ollama**（本地部署）:

```bash
LLM_BINDING=ollama
LLM_MODEL=llama3.1:70b
LLM_BINDING_HOST=http://localhost:11434
OLLAMA_LLM_NUM_CTX=32768
OLLAMA_LLM_NUM_PREDICT=9000
```

**Azure OpenAI**:

```bash
LLM_BINDING=azure_openai
LLM_MODEL=gpt-4o
LLM_BINDING_API_KEY=your-api-key
AZURE_OPENAI_API_VERSION=2024-08-01-preview
AZURE_OPENAI_DEPLOYMENT=gpt-4o
```

#### Embedding 配置

**OpenAI Embedding**:

```bash
EMBEDDING_BINDING=openai
EMBEDDING_MODEL=text-embedding-3-large
EMBEDDING_DIM=3072
EMBEDDING_BINDING_HOST=https://api.openai.com/v1
EMBEDDING_BINDING_API_KEY=sk-your-api-key
```

**本地 Ollama Embedding**:

```bash
EMBEDDING_BINDING=ollama
EMBEDDING_MODEL=bge-m3:latest
EMBEDDING_DIM=1024
EMBEDDING_BINDING_HOST=http://localhost:11434
OLLAMA_EMBEDDING_NUM_CTX=8192
```

**Jina AI Embedding**:

```bash
EMBEDDING_BINDING=jina
EMBEDDING_MODEL=jina-embeddings-v4
EMBEDDING_DIM=2048
EMBEDDING_BINDING_HOST=https://api.jina.ai/v1/embeddings
EMBEDDING_BINDING_API_KEY=your-api-key
```

#### 查询配置

```bash
# LLM 响应缓存
ENABLE_LLM_CACHE=true

# 检索参数
TOP_K=40                    # 从 KG 检索的实体/关系数量
CHUNK_TOP_K=20              # 向量搜索检索的 chunk 数量
COSINE_THRESHOLD=0.2        # 向量相似度阈值

# Token 限制
MAX_ENTITY_TOKENS=6000      # 发送给 LLM 的实体 token 上限
MAX_RELATION_TOKENS=8000    # 发送给 LLM 的关系 token 上限
MAX_TOTAL_TOKENS=30000      # 总 token 上限

# Chunk 选择策略
KG_CHUNK_PICK_METHOD=VECTOR  # VECTOR 或 WEIGHT
RELATED_CHUNK_NUMBER=5       # 每个实体/关系关联的 chunk 数
```

#### 文档处理配置

```bash
# 缓存配置
ENABLE_LLM_CACHE_FOR_EXTRACT=true

# 输出语言
SUMMARY_LANGUAGE=Chinese

# 实体类型
ENTITY_TYPES='["Person", "Organization", "Location", "Event", "Concept"]'

# 文本分块
CHUNK_SIZE=1200
CHUNK_OVERLAP_SIZE=100

# LLM 摘要触发条件
FORCE_LLM_SUMMARY_ON_MERGE=8
SUMMARY_MAX_TOKENS=1200
SUMMARY_LENGTH_RECOMMENDED=600
SUMMARY_CONTEXT_SIZE=12000
```

#### 并发配置

```bash
# LLM 并发请求数
MAX_ASYNC=4

# 并行处理文档数
MAX_PARALLEL_INSERT=2

# Embedding 并发
EMBEDDING_FUNC_MAX_ASYNC=8
EMBEDDING_BATCH_NUM=10
```

---

## 存储后端配置

### 图数据库配置

#### Neo4j

**本地部署**:

```bash
xwrag_GRAPH_STORAGE=Neo4JStorage
NEO4J_URI=neo4j://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password
NEO4J_DATABASE=neo4j
NEO4J_MAX_CONNECTION_POOL_SIZE=100
```

**Neo4j Aura（云服务）**:

```bash
NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password
```

#### NebulaGraph

```bash
xwrag_GRAPH_STORAGE=NebulaGraphStorage
NEBULA_HOST=localhost
NEBULA_PORT=9669
NEBULA_USERNAME=root
NEBULA_PASSWORD=nebula
NEBULA_SPACE=xwrag
```

**注意**: NebulaGraph 在本项目中经过优化，批量查询性能提升 40 倍。

#### Memgraph

```bash
xwrag_GRAPH_STORAGE=MemgraphStorage
MEMGRAPH_URI=bolt://localhost:7687
MEMGRAPH_USERNAME=
MEMGRAPH_PASSWORD=
MEMGRAPH_DATABASE=memgraph
```

### 向量数据库配置

#### Milvus

```bash
xwrag_VECTOR_STORAGE=MilvusVectorDBStorage
MILVUS_URI=http://localhost:19530
MILVUS_DB_NAME=xwrag
MILVUS_USER=root
MILVUS_PASSWORD=your-password
```

#### Qdrant

```bash
xwrag_VECTOR_STORAGE=QdrantVectorDBStorage
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your-api-key
```

#### Faiss（仅本地）

```bash
xwrag_VECTOR_STORAGE=FaissVectorDBStorage
# Faiss 是本地文件存储，无需额外配置
```

### KV 存储配置

#### Redis（推荐生产环境）

```bash
xwrag_KV_STORAGE=RedisKVStorage
xwrag_DOC_STATUS_STORAGE=RedisDocStatusStorage

REDIS_URI=redis://localhost:6379
REDIS_SOCKET_TIMEOUT=30
REDIS_CONNECT_TIMEOUT=10
REDIS_MAX_CONNECTIONS=100
```

#### PostgreSQL

```bash
xwrag_KV_STORAGE=PGKVStorage
xwrag_DOC_STATUS_STORAGE=PGDocStatusStorage
xwrag_GRAPH_STORAGE=PGGraphStorage
xwrag_VECTOR_STORAGE=PGVectorStorage

POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password
POSTGRES_DATABASE=xwrag
POSTGRES_MAX_CONNECTIONS=12

# 向量索引配置
POSTGRES_VECTOR_INDEX_TYPE=HNSW
POSTGRES_HNSW_M=16
POSTGRES_HNSW_EF=200
```

#### MongoDB

```bash
xwrag_KV_STORAGE=MongoKVStorage
xwrag_DOC_STATUS_STORAGE=MongoDocStatusStorage
xwrag_GRAPH_STORAGE=MongoGraphStorage

MONGO_URI=mongodb://root:root@localhost:27017/
MONGO_DATABASE=xwrag
```

---

## 性能优化

### 1. 数据库优化

#### Neo4j 优化

```bash
# 增加内存分配
NEO4J_dbms_memory_heap_initial__size=4G
NEO4J_dbms_memory_heap_max__size=8G
NEO4J_dbms_memory_pagecache_size=2G
```

在 Neo4j 中创建索引：

```cypher
// 为实体节点创建索引
CREATE INDEX entity_name_index FOR (n:Entity) ON (n.name);
CREATE INDEX entity_created_at_index FOR (n:Entity) ON (n.created_at);

// 为关系创建索引
CREATE INDEX relationship_weight_index FOR ()-[r:RELATES_TO]-() ON (r.weight);
```

#### Milvus 优化

```bash
# 选择合适的索引类型
# HNSW: 高性能，但内存占用大
# IVF_FLAT: 平衡性能和内存
# IVF_SQ8: 内存优化

# 在应用层配置索引参数
INDEX_TYPE=HNSW
METRIC_TYPE=COSINE
INDEX_PARAMS='{"M": 16, "efConstruction": 200}'
SEARCH_PARAMS='{"ef": 100}'
```

### 2. 并发配置优化

根据服务器资源调整并发参数：

```bash
# 4 核 8GB 内存配置
MAX_ASYNC=4
MAX_PARALLEL_INSERT=2
EMBEDDING_FUNC_MAX_ASYNC=8

# 8 核 16GB 内存配置
MAX_ASYNC=8
MAX_PARALLEL_INSERT=4
EMBEDDING_FUNC_MAX_ASYNC=16

# 16 核 32GB 内存配置
MAX_ASYNC=16
MAX_PARALLEL_INSERT=8
EMBEDDING_FUNC_MAX_ASYNC=32
```

### 3. 缓存策略

```bash
# 启用所有缓存
ENABLE_LLM_CACHE=true
ENABLE_LLM_CACHE_FOR_EXTRACT=true

# 配置 Redis 作为缓存后端
xwrag_KV_STORAGE=RedisKVStorage
REDIS_MAX_CONNECTIONS=100
```

### 4. Token 优化

根据 LLM 上下文窗口大小调整：

```bash
# GPT-4o (128k context)
MAX_ENTITY_TOKENS=10000
MAX_RELATION_TOKENS=10000
MAX_TOTAL_TOKENS=50000

# GPT-3.5-turbo (16k context)
MAX_ENTITY_TOKENS=3000
MAX_RELATION_TOKENS=3000
MAX_TOTAL_TOKENS=12000
```

### 5. Batch Processing 优化

```bash
# 增加 embedding batch 大小
EMBEDDING_BATCH_NUM=20

# 调整文档处理批次
MAX_PARALLEL_INSERT=4
```

---

## 监控和日志

### 1. 日志配置

```bash
# 日志级别
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR

# 详细日志
VERBOSE=True

# 日志文件大小和轮转
LOG_MAX_BYTES=10485760    # 10MB
LOG_BACKUP_COUNT=5

# 自定义日志目录
LOG_DIR=/var/log/rag-api
```

### 2. 查看日志

**Docker Compose 部署**:

```bash
# 查看 API 日志
docker-compose logs -f rag-api

# 查看 Neo4j 日志
docker-compose logs -f neo4j

# 查看最近 100 行日志
docker-compose logs --tail=100 rag-api
```

**本地部署**:

```bash
# 实时查看日志
tail -f /var/log/rag-api/access.log
tail -f /var/log/rag-api/error.log

# 查看 systemd 日志
sudo journalctl -u rag-api -f
```

### 3. 性能监控

**API 请求耗时统计**:

系统已内置详细的耗时统计，日志中会显示：

```
⏱️  [Timing] LLM keyword extraction: 0.523s
⏱️  [Timing] Context building (search + merge): 2.145s
⏱️      [Embedding] Entity query embedding: 0.234s
⏱️      [VectorDB] Entity similarity search: 0.156s (20 results)
⏱️      [GraphDB] Related edges retrieval: 0.089s
⏱️  [Timing] Final LLM response generation: 1.234s
⏱️  [Timing] === Total query time: 3.902s ===
```

**数据库监控**:

```bash
# Neo4j 性能监控
curl http://localhost:7474/metrics

# Milvus 性能监控
# 访问 Milvus 管理界面或使用 Prometheus
```

### 4. 健康检查

```bash
# API 健康检查
curl http://localhost:8000/api/admin/health

# 返回示例
{
  "status": "healthy",
  "version": "3.0.0",
  "timestamp": "2024-12-01T10:30:00Z"
}
```

---

## 故障排查

### 常见问题

#### 1. 连接数据库失败

**错误信息**:

```
Error: Unable to connect to Neo4j at neo4j://localhost:7687
```

**解决方法**:

```bash
# 检查 Neo4j 是否运行
docker ps | grep neo4j

# 检查网络连接
telnet localhost 7687

# 检查环境变量
echo $NEO4J_URI
echo $NEO4J_PASSWORD

# 重启 Neo4j
docker-compose restart neo4j
```

#### 2. Embedding 超时

**错误信息**:

```
Error: Embedding request timeout after 30s
```

**解决方法**:

```bash
# 增加超时时间
EMBEDDING_TIMEOUT=60

# 减少 batch 大小
EMBEDDING_BATCH_NUM=5

# 增加并发数
EMBEDDING_FUNC_MAX_ASYNC=16
```

#### 3. LLM API 限流

**错误信息**:

```
Error: Rate limit exceeded for API key
```

**解决方法**:

```bash
# 减少并发请求
MAX_ASYNC=2

# 增加重试间隔
# 在代码中已配置 exponential backoff

# 使用备用 API key（通过负载均衡）
```

#### 4. 内存不足

**错误信息**:

```
Error: Out of memory
```

**解决方法**:

```bash
# 减少并发处理
MAX_ASYNC=2
MAX_PARALLEL_INSERT=1

# 减少 token 限制
MAX_TOTAL_TOKENS=20000

# 减少检索数量
TOP_K=20
CHUNK_TOP_K=10

# 增加 Docker 内存限制（docker-compose.yml）
deploy:
  resources:
    limits:
      memory: 16G
```

#### 5. 查询性能慢

**优化建议**:

```bash
# 1. 检查数据库索引
# Neo4j: CREATE INDEX ...

# 2. 优化检索参数
TOP_K=20
CHUNK_TOP_K=10
RELATED_CHUNK_NUMBER=3

# 3. 启用缓存
ENABLE_LLM_CACHE=true

# 4. 使用更快的 embedding 模型
EMBEDDING_MODEL=text-embedding-3-small
```

### 调试模式

启用详细日志：

```bash
# 设置日志级别
LOG_LEVEL=DEBUG
VERBOSE=True

# 重启服务
./deploy.sh restart

# 查看详细日志
./deploy.sh logs
```

---

## 升级和维护

### 版本升级

#### 1. 备份数据

```bash
# 备份 Neo4j 数据
docker exec neo4j neo4j-admin dump --database=neo4j --to=/backups/neo4j-backup.dump

# 备份配置文件
cp .env .env.backup
```

#### 2. 拉取新代码

```bash
git pull origin main
```

#### 3. 更新依赖

```bash
# Docker Compose
./deploy.sh rebuild

# 本地部署
pip install -e ".[api]" --upgrade
```

#### 4. 数据迁移

查看 `CHANGELOG.md` 了解是否需要数据迁移。

### 数据备份

#### Neo4j 备份

```bash
# 完整备份
docker exec neo4j neo4j-admin dump \
  --database=neo4j \
  --to=/backups/neo4j-$(date +%Y%m%d).dump

# 恢复备份
docker exec neo4j neo4j-admin load \
  --from=/backups/neo4j-20241201.dump \
  --database=neo4j --force
```

#### Milvus 备份

```bash
# 导出 collection
# 使用 Milvus 客户端或 API 导出数据
```

### 定期维护

#### 清理缓存

```bash
# 通过 API 清理 LLM 缓存
curl -X POST http://localhost:8000/api/query/clear_cache

# 清理 Redis 缓存（谨慎）
redis-cli FLUSHDB
```

#### 数据库优化

```bash
# Neo4j 索引重建
# 在 Neo4j Browser 中执行
CALL db.indexes()
CALL db.constraints()
```

---

## 安全建议

### 1. API 密钥保护

```bash
# 使用环境变量
export LLM_BINDING_API_KEY=sk-xxxxxxxx

# 不要在代码中硬编码
# 不要提交 .env 到版本控制
```

### 2. 网络安全

```bash
# 限制数据库访问
# Neo4j: 仅允许本地连接
NEO4J_URI=neo4j://127.0.0.1:7687

# 使用防火墙
sudo ufw allow 8000/tcp
sudo ufw deny 7687/tcp  # 仅内部访问
```

### 3. SSL/TLS 配置

```bash
# API SSL 配置
SSL=true
SSL_CERTFILE=/path/to/cert.pem
SSL_KEYFILE=/path/to/key.pem

# Neo4j SSL
NEO4J_URI=neo4j+s://your-server.com:7687
```

### 4. 认证和授权

```bash
# 启用 API 认证
AUTH_ACCOUNTS='admin:secure_password,user1:password123'
TOKEN_SECRET=your-secret-key-here
TOKEN_EXPIRE_HOURS=48

# API Key 认证
xwrag_API_KEY=your-secure-api-key-here
WHITELIST_PATHS=/health,/docs
```

---

## 参考资源

- **项目仓库**: https://github.com/HKUDS/xwrag
- **API 文档**: http://localhost:8000/docs
- **Neo4j 文档**: https://neo4j.com/docs/
- **Milvus 文档**: https://milvus.io/docs/
- **FastAPI 文档**: https://fastapi.tiangolo.com/

---

## 联系支持

如遇到问题，请：

1. 查看本文档的故障排查部分
2. 查看项目 Issues: https://github.com/your-org/myRAG/issues
3. 提交新 Issue 并附上详细日志

---

**祝您部署顺利！**
