# RAG Backend API 重构说明

## 项目结构

```
myRAG/
├── app/                           # 主应用目录
│   ├── __init__.py                # 包初始化文件
│   ├── main.py                    # 应用入口文件,包含 FastAPI 实例和路由配置
│   ├── dependencies.py            # 依赖管理:RAG 实例管理器、xwragProcessor 类
│   ├── models.py                  # Pydantic 模型定义
│   ├── routers/                   # 路由模块
│   │   ├── __init__.py
│   │   ├── documents.py           # 文档操作路由
│   │   ├── graph.py               # 图操作路由(实体和关系管理)
│   │   └── query.py               # 查询操作路由
│   └── internal/                  # 内部管理模块
│       ├── __init__.py
│       └── admin.py               # 管理功能(RAG 实例管理、健康检查)
├── backend_api.py                 # 旧版本(保留用于参考)
└── uploaded_files/                # 上传文件目录
```

## 启动方式

```bash
# 标准启动
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 或者在项目根目录运行
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 主要功能

### 1. RAG 实例管理

新版本支持管理多个 RAG 实例,每个实例可以有不同的配置。

#### 创建 RAG 实例

```bash
POST /api/admin/rag_instances/create
```

请求体示例:
```json
{
  "rag_id": "my_rag_instance",
  "description": "我的第一个 RAG 实例",
  "working_dir": "./rag_data/instance1",
  "workspace": "default",
  "cosine_threshold": 0.3,
  "chunk_token_size": 1200,
  "chunk_overlap_token_size": 100,
  "enable_llm_cache": true,
  "enable_llm_cache_for_entity_extract": true
}
```

可选参数:
- `kv_storage`: KV 存储类型
- `vector_storage`: 向量存储类型
- `graph_storage`: 图存储类型
- `doc_status_storage`: 文档状态存储类型
- `top_k`: 查询返回的 top k 结果
- `chunk_top_k`: 分块查询返回的 top k 结果
- `max_entity_tokens`: 实体的最大 token 数
- `max_relation_tokens`: 关系的最大 token 数
- `max_total_tokens`: 总的最大 token 数
- `cosine_threshold`: 余弦相似度阈值(默认: 0.3)
- `related_chunk_number`: 相关分块数量(默认: 5)
- `chunk_token_size`: 分块 token 大小(默认: 1200)
- `chunk_overlap_token_size`: 分块重叠 token 大小(默认: 100)
- `enable_llm_cache`: 是否启用 LLM 缓存(默认: true)
- `enable_llm_cache_for_entity_extract`: 是否为实体提取启用 LLM 缓存(默认: true)
- `llm_model`: LLM 模型名称
- `embedding_model`: Embedding 模型名称
- `embedding_dim`: Embedding 维度
- `embedding_max_token`: Embedding 最大 token 数
- `litellm_url`: LiteLLM 服务地址
- `litellm_key`: LiteLLM API 密钥

#### 列出所有 RAG 实例

```bash
GET /api/admin/rag_instances/list
```

#### 获取指定 RAG 实例信息

```bash
GET /api/admin/rag_instances/{rag_id}
```

#### 删除 RAG 实例

```bash
DELETE /api/admin/rag_instances/{rag_id}
```

### 2. 文档操作

所有文档操作都需要指定 `rag_id` 来指定使用哪个 RAG 实例。

#### 上传文档

```bash
POST /api/documents/upload?rag_id=my_rag_instance
```

#### 插入文档内容

```bash
POST /api/documents/insert
```

请求体:
```json
{
  "rag_id": "my_rag_instance",
  "content": "文档内容...",
  "file_path": "document.txt",
  "doc_id": "optional_custom_id"
}
```

#### 批量插入文档

```bash
POST /api/documents/batch_insert
```

请求体:
```json
{
  "rag_id": "my_rag_instance",
  "documents": [
    {
      "content": "文档1内容",
      "file_path": "doc1.txt",
      "doc_id": "doc1"
    },
    {
      "content": "文档2内容",
      "file_path": "doc2.txt"
    }
  ]
}
```

#### 获取文档状态

```bash
GET /api/documents/status/{rag_id}
```

#### 获取指定状态的文档列表

```bash
GET /api/documents/list/{rag_id}/{status}
```

状态可以是: PROCESSED, PENDING, FAILED

### 3. 查询操作

#### 查询知识库

```bash
POST /api/query/
```

请求体:
```json
{
  "rag_id": "my_rag_instance",
  "question": "你的问题",
  "mode": "hybrid",
  "only_need_context": true,
  "top_k": 20,
  "chunk_top_k": 10,
  "max_entity_tokens": 6000,
  "max_relation_tokens": 8000,
  "max_total_tokens": 16300
}
```

QueryParam 参数说明:
- `mode`: 查询模式,可选值: naive, local, global, hybrid (默认: hybrid)
- `only_need_context`: 是否只需要上下文 (默认: true)
- `top_k`: 查询返回的 top k 结果 (默认: 20)
- `chunk_top_k`: 分块查询返回的 top k 结果 (默认: 10)
- `max_entity_tokens`: 实体的最大 token 数 (默认: 6000)
- `max_relation_tokens`: 关系的最大 token 数 (默认: 8000)
- `max_total_tokens`: 总的最大 token 数 (默认: 16300)

#### UCD 建模查询

```bash
POST /api/query/ucd
```

请求体:
```json
{
  "rag_id": "my_rag_instance",
  "question": "你的问题",
  "mode": "hybrid",
  "out_json": "output_uc.json"
}
```

#### 清除缓存

```bash
POST /api/query/clear_cache
```

请求体:
```json
{
  "rag_id": "my_rag_instance",
  "cache_type": "llm_cache"  // 或 "all"
}
```

### 4. 图操作(实体和关系管理)

#### 实体操作

- 创建实体: `POST /api/graph/entities/create`
- 编辑实体: `POST /api/graph/entities/edit`
- 删除实体: `POST /api/graph/entities/delete`
- 获取实体信息: `POST /api/graph/entities/info`
- 合并实体: `POST /api/graph/entities/merge`

所有请求都需要包含 `rag_id` 字段。

示例 - 创建实体:
```json
{
  "rag_id": "my_rag_instance",
  "entity_name": "Python",
  "description": "一种编程语言",
  "entity_type": "TECHNOLOGY",
  "source_id": "manual_creation",
  "file_path": "manual_creation"
}
```

#### 关系操作

- 创建关系: `POST /api/graph/relations/create`
- 编辑关系: `POST /api/graph/relations/edit`
- 删除关系: `POST /api/graph/relations/delete`
- 获取关系信息: `POST /api/graph/relations/info`

示例 - 创建关系:
```json
{
  "rag_id": "my_rag_instance",
  "source_entity": "Python",
  "target_entity": "Django",
  "description": "用于开发",
  "keywords": "web框架",
  "weight": 1.0,
  "source_id": "manual_creation",
  "file_path": "manual_creation"
}
```

#### 导出数据

```bash
POST /api/graph/export
```

请求体:
```json
{
  "rag_id": "my_rag_instance",
  "output_path": "./export_data.csv",
  "file_format": "csv",  // csv, excel, md, txt
  "include_vector_data": false
}
```

### 5. 系统管理

#### 健康检查

```bash
GET /api/admin/health
```

#### 初始化 UCD 建模器

```bash
POST /api/admin/ucd/init
```

请求体:
```json
{
  "base_url": "http://localhost:4000",
  "api_key": "sk-1234",
  "model_name": "gpt-4"
}
```

## WebSocket 支持

WebSocket 端点: `ws://localhost:8000/ws`

所有 WebSocket 消息都需要包含 `rag_id` 字段来指定使用哪个 RAG 实例。

### 查询示例

```json
{
  "type": "query",
  "rag_id": "my_rag_instance",
  "question": "你的问题",
  "mode": "hybrid"
}
```

### 实体操作示例

```json
{
  "type": "entity_operation",
  "rag_id": "my_rag_instance",
  "operation": "create",
  "entity_name": "Python",
  "entity_data": {
    "description": "一种编程语言"
  }
}
```

### UCD 建模示例

```json
{
  "type": "query_ucd",
  "rag_id": "my_rag_instance",
  "question": "你的问题",
  "mode": "hybrid",
  "out_json": "output_uc.json"
}
```

## 主要改进

1. **多实例支持**: 可以同时管理多个 RAG 实例,每个实例有独立的配置
2. **模块化设计**: 代码按功能分为不同的模块,易于维护和扩展
3. **灵活的配置**: 创建 RAG 实例时可以指定大量可选参数
4. **灵活的查询参数**: 查询时可以动态指定 QueryParam 的各种参数
5. **缓存管理**: 支持清除 LLM 缓存
6. **清晰的 API 结构**: 路由按功能分组,易于理解和使用

## 迁移指南

如果你之前使用的是 `backend_api.py`,需要做以下调整:

1. **初始化**: 之前直接调用 `/api/init`,现在需要先调用 `/api/admin/rag_instances/create` 创建 RAG 实例
2. **所有操作**: 所有 API 调用都需要包含 `rag_id` 参数来指定使用哪个 RAG 实例
3. **查询**: 查询时可以指定更多的 QueryParam 参数来控制查询行为
4. **路由变化**:
   - 文档操作: `/api/documents/*`
   - 查询操作: `/api/query/*`
   - 图操作: `/api/graph/*`
   - 管理操作: `/api/admin/*`

## 依赖要求

```bash
pip install fastapi uvicorn python-multipart aiofiles
pip install xwrag transformers llama-index-llms-litellm
pip install textract python-dotenv nest-asyncio
```
