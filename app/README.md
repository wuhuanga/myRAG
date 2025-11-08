# RAG Backend API

模块化的 RAG 后端 API 服务，支持多实例管理。

## 快速开始

### 1. 安装依赖

```bash
# 安装后端 API 依赖
pip install -r app/requirements.txt

# 或者安装完整的 xwrag 包（包含 API 支持）
pip install -e ".[api]"
```

### 2. 配置环境变量

创建 `.env` 文件：

```bash
# LLM 配置
LLM_MODEL=gpt-4
LITELLM_URL=http://localhost:4000
LITELLM_KEY=sk-1234

# Embedding 配置
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIM=384
EMBEDDING_MAX_TOKEN=5000

# Neo4j 配置（如果使用 Neo4j）
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
```

### 3. 启动服务

```bash
# 开发模式（带自动重载）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 4. 访问 API

- API 文档: http://localhost:8000/docs
- 前端界面: 打开 `frontend/index.html`

## 项目结构

```
app/
├── __init__.py           # 包初始化
├── main.py               # FastAPI 应用入口
├── models.py             # Pydantic 数据模型
├── dependencies.py       # RAG 实例管理（单线程）
├── dependencies_concurrent.py  # RAG 实例管理（并发安全）
├── internal/
│   └── admin.py          # 管理接口（实例、健康检查）
└── routers/
    ├── documents.py      # 文档操作接口
    ├── query.py          # 查询接口
    └── graph.py          # 图操作接口
```

## API 端点

### 管理接口 (`/api/admin`)

- `GET /api/admin/health` - 健康检查
- `POST /api/admin/rag_instances/create` - 创建 RAG 实例
- `GET /api/admin/rag_instances/list` - 列出所有实例
- `GET /api/admin/rag_instances/{rag_id}` - 获取实例详情
- `DELETE /api/admin/rag_instances/{rag_id}` - 删除实例

### 文档接口 (`/api/documents`)

- `POST /api/documents/upload` - 上传文档
- `POST /api/documents/insert` - 插入文本
- `POST /api/documents/batch_insert` - 批量插入
- `GET /api/documents/status/{rag_id}` - 获取文档状态

### 查询接口 (`/api/query`)

- `POST /api/query/` - 查询知识库
- `POST /api/query/ucd` - UCD 建模查询
- `POST /api/query/clear_cache` - 清除缓存

### 图操作接口 (`/api/graph`)

- `POST /api/graph/entities/create` - 创建实体
- `POST /api/graph/entities/info` - 获取实体信息
- `POST /api/graph/entities/edit` - 编辑实体
- `POST /api/graph/entities/delete` - 删除实体
- `POST /api/graph/relations/create` - 创建关系
- `POST /api/graph/relations/info` - 获取关系信息
- `POST /api/graph/export` - 导出数据

## 模型说明

### RAGInstanceCreate

创建 RAG 实例的请求模型：

```python
{
    "rag_id": "my-rag",                    # 实例 ID（必填）
    "workspace": "project_001",             # 工作空间（必填）
    "working_dir": "./rag_storage",         # 工作目录
    "description": "My RAG instance",       # 描述（可选）
    # 查询配置（可选）
    "top_k": 20,
    "chunk_top_k": 10,
    # ... 其他可选参数
}
```

**注意**: LLM 和 Embedding 配置从环境变量读取，存储固定使用 Neo4j + Faiss。

### RAGInstanceInfo

RAG 实例信息响应模型：

```python
{
    "rag_id": "my-rag",
    "workspace": "project_001",
    "working_dir": "./rag_storage",
    "created_at": "2024-01-01T00:00:00",
    "llm_model": "gpt-4",
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2"
}
```

## 使用示例

### 创建 RAG 实例

```bash
curl -X POST "http://localhost:8000/api/admin/rag_instances/create" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "my-rag",
    "workspace": "project_001",
    "working_dir": "./rag_storage"
  }'
```

### 上传文档

```bash
curl -X POST "http://localhost:8000/api/documents/upload" \
  -F "rag_id=my-rag" \
  -F "file=@document.txt"
```

### 查询

```bash
curl -X POST "http://localhost:8000/api/query/" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "my-rag",
    "question": "What is RAG?",
    "mode": "hybrid"
  }'
```

## 故障排查

### 导入错误

如果遇到 `ModuleNotFoundError: No module named 'fastapi'`：

```bash
pip install -r app/requirements.txt
```

### 数据库连接错误

确保 Neo4j 正在运行并配置正确：

```bash
# 检查 Neo4j 状态
docker ps | grep neo4j

# 启动 Neo4j
docker run -d \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your_password \
  neo4j:latest
```

## 开发

### 运行测试

```bash
python test_models.py
```

### 代码格式化

```bash
ruff check app/
ruff format app/
```
