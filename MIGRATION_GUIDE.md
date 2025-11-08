# API 迁移指南：从单实例到多实例架构

## 概述

后端 API 已从单实例架构重构为支持多实例管理的模块化架构。

## 快速开始

### 启动新版本服务器

```bash
# 方式1：推荐使用新入口（清晰明确）
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 方式2：向后兼容（仍然使用 backend_api.py，但会加载新架构）
uvicorn backend_api:app --host 0.0.0.0 --port 8000 --reload
```

## 主要变化

### 1. 从单实例到多实例

**旧架构（单实例）：**
- 整个服务只有一个全局 RAG 实例
- 必须先调用 `/api/init` 初始化
- 无法同时管理多个 RAG 实例

**新架构（多实例）：**
- 支持动态创建/管理多个 RAG 实例
- 每个实例有独立的 `rag_id` 和 `workspace`
- 可并发处理不同项目的请求

### 2. API 端点变化

#### 系统管理

| 旧端点 | 新端点 | 说明 |
|--------|--------|------|
| `POST /api/init` | `POST /api/admin/rag_instances/create` | 创建 RAG 实例 |
| `GET /api/health` | `GET /api/admin/health` | 健康检查 |
| - | `GET /api/admin/rag_instances/list` | 列出所有实例 |
| - | `DELETE /api/admin/rag_instances/{rag_id}` | 删除实例 |

#### 文档操作

所有文档操作都需要在请求中指定 `rag_id`：

| 旧端点 | 新端点 | 主要变化 |
|--------|--------|----------|
| `POST /api/documents/upload` | `POST /api/documents/upload` | 需要 FormData 中的 `rag_id` |
| `POST /api/documents/insert` | `POST /api/documents/insert` | 请求体中需要 `rag_id` |
| `GET /api/documents/status` | `GET /api/documents/status/{rag_id}` | URL 路径中需要 `rag_id` |

#### 查询操作

| 旧端点 | 新端点 | 主要变化 |
|--------|--------|----------|
| `POST /api/query` | `POST /api/query/` | 请求体中需要 `rag_id` |
| `POST /api/query_ucd` | `POST /api/query/ucd` | 请求体中需要 `rag_id` |

#### 图操作（实体和关系）

所有图操作端点都移到了 `/api/graph/` 下：

| 旧端点 | 新端点 |
|--------|--------|
| `POST /api/entities/create` | `POST /api/graph/entities/create` |
| `POST /api/entities/info` | `POST /api/graph/entities/info` |
| `POST /api/relations/create` | `POST /api/graph/relations/create` |
| `POST /api/export` | `POST /api/graph/export` |

## 迁移步骤

### 步骤1：创建 RAG 实例

**旧方式（init）：**
```bash
curl -X POST "http://localhost:8000/api/init" \
  -H "Content-Type: application/json" \
  -d '{
    "working_dir": "./rag_storage",
    "llm_model": "gpt-4"
  }'
```

**新方式（create instance）：**
```bash
curl -X POST "http://localhost:8000/api/admin/rag_instances/create" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "my-rag",
    "workspace": "project_001",
    "working_dir": "./rag_storage"
  }'
```

**说明：**
- `rag_id`：实例的唯一标识符（新增，必填）
- `workspace`：工作空间名称（新增，必填，用于数据隔离）
- LLM 配置现在从环境变量读取（见下文）

### 步骤2：上传文档

**旧方式：**
```bash
curl -X POST "http://localhost:8000/api/documents/upload" \
  -F "file=@document.txt"
```

**新方式：**
```bash
curl -X POST "http://localhost:8000/api/documents/upload" \
  -F "rag_id=my-rag" \
  -F "file=@document.txt"
```

**说明：**
- 必须通过 FormData 指定 `rag_id`

### 步骤3：查询

**旧方式：**
```bash
curl -X POST "http://localhost:8000/api/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is RAG?",
    "mode": "hybrid"
  }'
```

**新方式：**
```bash
curl -X POST "http://localhost:8000/api/query/" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "my-rag",
    "question": "What is RAG?",
    "mode": "hybrid"
  }'
```

**说明：**
- 请求体中必须包含 `rag_id`

## 环境变量配置

新版本通过环境变量配置 LLM 和 Embedding 模型（不再通过 API 参数）：

```bash
# 创建 .env 文件
cat > .env <<EOF
# LLM 配置
LLM_MODEL=gpt-4
LITELLM_URL=http://localhost:4000
LITELLM_KEY=sk-1234

# Embedding 配置
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIM=384
EMBEDDING_MAX_TOKEN=5000

# Neo4j 配置
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
EOF
```

## 前端更新

如果你使用前端界面，需要更新：

1. **打开新前端**：使用 `frontend/index.html`（已更新）
2. **API URL**：确保指向正确的端点
3. **实例选择**：现在需要先创建实例，然后选择实例进行操作

## 完整示例：从头开始

```bash
# 1. 启动服务
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 2. 检查健康状态
curl http://localhost:8000/api/admin/health

# 3. 创建 RAG 实例
curl -X POST "http://localhost:8000/api/admin/rag_instances/create" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "project-alpha",
    "workspace": "alpha_workspace",
    "working_dir": "./rag_storage/alpha"
  }'

# 4. 上传文档
curl -X POST "http://localhost:8000/api/documents/upload" \
  -F "rag_id=project-alpha" \
  -F "file=@mydocument.pdf"

# 5. 查询
curl -X POST "http://localhost:8000/api/query/" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "project-alpha",
    "question": "Summarize the document",
    "mode": "hybrid"
  }'

# 6. 列出所有实例
curl http://localhost:8000/api/admin/rag_instances/list
```

## 优势

### 新架构的优点：

1. **多租户支持**：同一服务器可以服务多个独立项目
2. **数据隔离**：每个 workspace 的数据完全隔离
3. **动态管理**：无需重启服务即可创建/删除实例
4. **更好的组织**：路由模块化，代码更清晰
5. **环境变量配置**：更安全，避免敏感信息在 API 请求中传递

## 常见问题

### Q: 旧的 `/api/init` 端点还能用吗？

A: 不能。必须使用新的 `/api/admin/rag_instances/create` 端点。

### Q: 如何迁移现有数据？

A: 如果之前使用了 `./rag_working` 目录，创建实例时指定相同的 `working_dir` 即可：

```json
{
  "rag_id": "legacy",
  "workspace": "default",
  "working_dir": "./rag_working"
}
```

### Q: 可以同时运行多个实例吗？

A: 可以！这正是新架构的优势。每个实例有独立的 `rag_id` 和 `workspace`。

### Q: 前端也需要更新吗？

A: 是的，旧前端无法使用。请使用 `frontend/index.html`（已更新）。

## 获取帮助

- API 文档：http://localhost:8000/docs
- 项目文档：`app/README.md`
- 提交问题：https://github.com/HKUDS/xwrag/issues
