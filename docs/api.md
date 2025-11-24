# RAG Backend API 接口文档

**版本**: 3.0.0
**基础路径**: `http://localhost:8000/api`

---

## 目录

1. [管理接口 (Admin)](#1-管理接口-admin)
2. [文档接口 (Documents)](#2-文档接口-documents)
3. [查询接口 (Query)](#3-查询接口-query)
4. [图操作接口 (Graph)](#4-图操作接口-graph)
5. [WebSocket 接口](#5-websocket-接口)

---

## 1. 管理接口 (Admin)

### 1.1 健康检查

**GET** `/api/admin/health`

检查服务健康状态。

**响应示例**:
```json
{
  "status": "healthy",
  "rag_instances_count": 2,
  "ucd_initialized": false,
  "timestamp": "2024-01-15T10:30:00.000000"
}
```

---

### 1.2 创建 RAG 实例

**POST** `/api/admin/rag_instances/create`

创建新的 RAG 知识库实例。

**请求体**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `rag_id` | string | 是 | - | 实例唯一标识 |
| `working_dir` | string | 是 | - | 工作目录路径 |
| `workspace` | string | 是 | - | 工作空间名称（必须唯一） |

**检索参数**（None 表示使用 xwrag 默认值/环境变量）:

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `top_k` | int | None | 检索的实体/关系数量 |
| `chunk_top_k` | int | None | 检索的文本块数量 |
| `max_entity_tokens` | int | None | 实体最大 token 数 |
| `max_relation_tokens` | int | None | 关系最大 token 数 |
| `max_total_tokens` | int | None | 总最大 token 数 |
| `cosine_threshold` | float | 0.3 | 余弦相似度阈值 |
| `related_chunk_number` | int | 5 | 关联文本块数量 |
| `kg_chunk_pick_method` | string | None | 文本块选择方法 (VECTOR/WEIGHT) |
| `max_graph_nodes` | int | None | 知识图谱返回最大节点数 |

**文本分块参数**:

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `chunk_token_size` | int | 1200 | 分块 token 大小 |
| `chunk_overlap_token_size` | int | 100 | 分块重叠 token 大小 |

**实体提取参数**:

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `language` | string | None | 文档处理语言 |
| `entity_types` | list[string] | None | 要提取的实体类型 |
| `entity_extract_max_gleaning` | int | None | 实体提取最大尝试次数 |

**并发与性能参数**:

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `llm_model_max_async` | int | None | 最大并发 LLM 调用数 |
| `embedding_func_max_async` | int | None | 最大并发 Embedding 调用数 |
| `max_parallel_insert` | int | None | 最大并行插入数 |
| `nebula_max_connection_pool_size` | int | None | NebulaGraph 连接池大小 |

**缓存参数**:

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `enable_llm_cache` | bool | true | 启用 LLM 缓存 |
| `enable_llm_cache_for_entity_extract` | bool | true | 实体提取时启用 LLM 缓存 |

**LLM 响应处理参数**:

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `strip_think_tags` | bool | false | 去除 LLM 响应中的 `<think>` 块 |

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/admin/rag_instances/create" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "rag_1",
    "working_dir": "./data/rag_1",
    "workspace": "knowledge_base_1",
    "llm_model_max_async": 8,
    "language": "Chinese"
  }'
```

**响应示例**:
```json
{
  "status": "success",
  "message": "RAG 实例 'rag_1' 创建成功",
  "rag_id": "rag_1",
  "working_dir": "./data/rag_1",
  "workspace": "knowledge_base_1",
  "llm_model": "gpt-4",
  "embedding_model": "sentence-transformers/all-MiniLM-L6-v2"
}
```

---

### 1.3 列出所有 RAG 实例

**GET** `/api/admin/rag_instances/list`

**响应示例**:
```json
[
  {
    "rag_id": "rag_1",
    "description": "knowledge_base_1",
    "working_dir": "./data/rag_1",
    "workspace": "knowledge_base_1",
    "created_at": "2024-01-15T10:30:00.000000",
    "llm_model": "gpt-4",
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2"
  }
]
```

---

### 1.4 获取 RAG 实例信息

**GET** `/api/admin/rag_instances/{rag_id}`

**请求示例**:
```bash
curl "http://localhost:8000/api/admin/rag_instances/rag_1"
```

---

### 1.5 删除 RAG 实例

**DELETE** `/api/admin/rag_instances/{rag_id}`

**请求示例**:
```bash
curl -X DELETE "http://localhost:8000/api/admin/rag_instances/rag_1"
```

---

### 1.6 初始化 UCD 建模器

**POST** `/api/admin/ucd/init`

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `base_url` | string | http://localhost:4000 | LLM 服务地址 |
| `api_key` | string | sk-1234 | API 密钥 |
| `model_name` | string | gpt-4 | 模型名称 |

---

## 2. 文档接口 (Documents)

### 2.1 上传文档

**POST** `/api/documents/upload`

上传并处理文档文件（PDF、DOCX、TXT 等）。

**请求参数** (form-data):

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `rag_id` | string | 是 | RAG 实例 ID |
| `file` | file | 是 | 文档文件 |
| `custom_id` | string | 否 | 自定义文档 ID |

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/documents/upload" \
  -F "rag_id=rag_1" \
  -F "file=@document.pdf" \
  -F "custom_id=doc_001"
```

**响应示例**:
```json
{
  "status": "success",
  "message": "文档 document.pdf 已成功上传并处理",
  "file_path": "uploaded_files/rag_1_document.pdf",
  "custom_id": "doc_001",
  "rag_id": "rag_1"
}
```

---

### 2.2 插入文档内容

**POST** `/api/documents/insert`

直接插入文本内容到知识库。

**请求体**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `rag_id` | string | 是 | RAG 实例 ID |
| `content` | string | 是 | 文档文本内容 |
| `file_path` | string | 是 | 文件路径/名称 |
| `doc_id` | string | 否 | 自定义文档 ID |

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/documents/insert" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "rag_1",
    "content": "这是文档内容...",
    "file_path": "example.txt",
    "doc_id": "doc_001"
  }'
```

---

### 2.3 批量插入文档

**POST** `/api/documents/batch_insert`

批量插入多个文档。

**请求体**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `rag_id` | string | 是 | RAG 实例 ID |
| `documents` | array | 是 | 文档数组 |

**documents 数组元素**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `content` | string | 是 | 文档内容 |
| `file_path` | string | 是 | 文件路径/名称 |
| `doc_id` | string | 否 | 自定义文档 ID |

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/documents/batch_insert" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "rag_1",
    "documents": [
      {"content": "文档1内容", "file_path": "doc1.txt"},
      {"content": "文档2内容", "file_path": "doc2.txt", "doc_id": "custom_id"}
    ]
  }'
```

---

### 2.4 获取文档状态统计

**GET** `/api/documents/status/{rag_id}`

**响应示例**:
```json
{
  "total": 100,
  "processed": 95,
  "pending": 3,
  "processing": 1,
  "failed": 1,
  "status_counts": {
    "PROCESSED": 95,
    "PENDING": 3,
    "PROCESSING": 1,
    "FAILED": 1
  }
}
```

---

### 2.5 获取指定状态的文档列表

**GET** `/api/documents/list/{rag_id}/{status}`

**状态值**: `PROCESSED`, `PENDING`, `FAILED`

**请求示例**:
```bash
curl "http://localhost:8000/api/documents/list/rag_1/PROCESSED"
```

---

## 3. 查询接口 (Query)

### 3.1 查询知识库

**POST** `/api/query/`

**请求体**:

**基础参数**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `rag_id` | string | 是 | - | RAG 实例 ID |
| `question` | string | 是 | - | 查询问题 |
| `mode` | string | 否 | hybrid | 查询模式 (naive/local/global/hybrid/mix) |

**检索参数**（None 表示使用 xwrag 默认值）:

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `top_k` | int | None | 检索的实体/关系数量 |
| `chunk_top_k` | int | None | 检索的文本块数量 |
| `max_entity_tokens` | int | None | 实体最大 token 数 |
| `max_relation_tokens` | int | None | 关系最大 token 数 |
| `max_total_tokens` | int | None | 总最大 token 数 |

**输出控制参数**:

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `only_need_context` | bool | true | 是否只返回上下文 |
| `response_type` | string | None | 响应格式 |
| `stream` | bool | None | 是否启用流式输出 |
| `include_references` | bool | None | 是否包含引用列表 |

**检索优化参数**:

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `enable_rerank` | bool | None | 是否启用 Rerank |
| `hl_keywords` | list[string] | None | 高优先级关键词 |
| `ll_keywords` | list[string] | None | 低优先级关键词 |

**对话与提示参数**:

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `conversation_history` | list | None | 对话历史 |
| `user_prompt` | string | None | 用户自定义提示词 |

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/query/" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "rag_1",
    "question": "什么是知识图谱？",
    "mode": "hybrid",
    "top_k": 50,
    "enable_rerank": true
  }'
```

**多轮对话示例**:
```bash
curl -X POST "http://localhost:8000/api/query/" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "rag_1",
    "question": "它有什么应用场景？",
    "conversation_history": [
      {"role": "user", "content": "什么是知识图谱？"},
      {"role": "assistant", "content": "知识图谱是一种..."}
    ]
  }'
```

**响应示例**:
```json
{
  "rag_id": "rag_1",
  "question": "什么是知识图谱？",
  "answer": "知识图谱是一种结构化的知识表示方式...",
  "mode": "hybrid",
  "timestamp": "2024-01-15T10:30:00.000000"
}
```

---

### 3.2 UCD 建模查询

**POST** `/api/query/ucd`

执行查询并进行 UCD（用例图）建模。

**请求体**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `rag_id` | string | 是 | - | RAG 实例 ID |
| `question` | string | 是 | - | 查询问题 |
| `mode` | string | 否 | hybrid | 查询模式 |
| `out_json` | string | 否 | output_uc.json | 输出文件路径 |

---

### 3.3 清除缓存

**POST** `/api/query/clear_cache`

**请求体**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `rag_id` | string | 是 | - | RAG 实例 ID |
| `cache_type` | string | 否 | all | 缓存类型 (llm_cache/all) |

---

## 4. 图操作接口 (Graph)

### 4.1 创建实体

**POST** `/api/graph/entities/create`

**请求体**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `rag_id` | string | 是 | RAG 实例 ID |
| `entity_name` | string | 是 | 实体名称 |
| `entity_type` | string | 是 | 实体类型 |
| `description` | string | 否 | 实体描述 |
| `source_id` | string | 否 | 来源 ID |
| `file_path` | string | 否 | 文件路径 |

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/graph/entities/create" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "rag_1",
    "entity_name": "知识图谱",
    "entity_type": "CONCEPT",
    "description": "一种结构化的知识表示方式"
  }'
```

---

### 4.2 编辑实体

**POST** `/api/graph/entities/edit`

**请求体**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `rag_id` | string | 是 | RAG 实例 ID |
| `entity_name` | string | 是 | 实体名称 |
| `updated_data` | object | 是 | 更新的数据 |
| `allow_rename` | bool | 否 | 是否允许重命名 |

---

### 4.3 删除实体

**POST** `/api/graph/entities/delete`

**请求体**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `rag_id` | string | 是 | RAG 实例 ID |
| `entity_name` | string | 是 | 实体名称 |

---

### 4.4 获取实体信息

**POST** `/api/graph/entities/info`

**请求体**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `rag_id` | string | 是 | - | RAG 实例 ID |
| `entity_name` | string | 是 | - | 实体名称 |
| `include_vector_data` | bool | 否 | false | 是否包含向量数据 |

---

### 4.5 合并实体

**POST** `/api/graph/entities/merge`

将多个实体合并为一个。

**请求体**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `rag_id` | string | 是 | RAG 实例 ID |
| `source_entities` | list[string] | 是 | 源实体列表 |
| `target_entity` | string | 是 | 目标实体名称 |
| `merge_strategy` | string | 否 | 合并策略 |
| `target_entity_data` | object | 否 | 目标实体数据 |

---

### 4.6 创建关系

**POST** `/api/graph/relations/create`

**请求体**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `rag_id` | string | 是 | RAG 实例 ID |
| `source_entity` | string | 是 | 源实体名称 |
| `target_entity` | string | 是 | 目标实体名称 |
| `description` | string | 否 | 关系描述 |
| `keywords` | string | 否 | 关键词 |
| `weight` | float | 否 | 关系权重 |
| `source_id` | string | 否 | 来源 ID |
| `file_path` | string | 否 | 文件路径 |

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/graph/relations/create" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "rag_1",
    "source_entity": "知识图谱",
    "target_entity": "人工智能",
    "description": "是...的一部分",
    "weight": 1.0
  }'
```

---

### 4.7 编辑关系

**POST** `/api/graph/relations/edit`

**请求体**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `rag_id` | string | 是 | RAG 实例 ID |
| `source_entity` | string | 是 | 源实体名称 |
| `target_entity` | string | 是 | 目标实体名称 |
| `updated_data` | object | 是 | 更新的数据 |

---

### 4.8 删除关系

**POST** `/api/graph/relations/delete`

**请求体**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `rag_id` | string | 是 | RAG 实例 ID |
| `source_entity` | string | 是 | 源实体名称 |
| `target_entity` | string | 是 | 目标实体名称 |

---

### 4.9 获取关系信息

**POST** `/api/graph/relations/info`

**请求体**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `rag_id` | string | 是 | - | RAG 实例 ID |
| `source_entity` | string | 是 | - | 源实体名称 |
| `target_entity` | string | 是 | - | 目标实体名称 |
| `include_vector_data` | bool | 否 | false | 是否包含向量数据 |

---

### 4.10 导出数据

**POST** `/api/graph/export`

导出知识图谱数据。

**请求体**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `rag_id` | string | 是 | - | RAG 实例 ID |
| `output_path` | string | 是 | - | 输出文件路径 |
| `file_format` | string | 否 | csv | 文件格式 |
| `include_vector_data` | bool | 否 | false | 是否包含向量数据 |

**支持的格式**:

| 格式 | 说明 |
|------|------|
| `csv` | CSV 格式 |
| `excel` | Excel 格式（多 sheet） |
| `md` | Markdown 表格格式 |
| `txt` | 纯文本格式 |
| `echarts` | ECharts JSON 格式（用于可视化） |

**ECharts 格式请求示例**:
```bash
curl -X POST "http://localhost:8000/api/graph/export" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "rag_1",
    "output_path": "./exports/graph.json",
    "file_format": "echarts"
  }'
```

**ECharts 格式输出示例**:
```json
{
  "nodes": [
    {
      "id": "知识图谱",
      "name": "知识图谱",
      "value": 15,
      "category": 0,
      "entity_type": "CONCEPT",
      "description": "一种结构化的知识表示方式"
    }
  ],
  "links": [
    {
      "source": "知识图谱",
      "target": "人工智能",
      "description": "是...的一部分",
      "weight": 1.0
    }
  ],
  "categories": [
    {"name": "CONCEPT"},
    {"name": "TECHNOLOGY"}
  ]
}
```

---

## 5. WebSocket 接口

**WebSocket** `ws://localhost:8000/ws`

支持实时双向通信。

### 5.1 查询消息

**发送**:
```json
{
  "type": "query",
  "rag_id": "rag_1",
  "question": "什么是知识图谱？",
  "mode": "hybrid"
}
```

**接收**:
```json
{
  "type": "answer",
  "rag_id": "rag_1",
  "question": "什么是知识图谱？",
  "context": "...",
  "mode": "hybrid"
}
```

### 5.2 实体操作

**创建实体**:
```json
{
  "type": "entity_operation",
  "rag_id": "rag_1",
  "operation": "create",
  "entity_name": "测试实体",
  "entity_data": {
    "entity_type": "CONCEPT",
    "description": "测试描述"
  }
}
```

**删除实体**:
```json
{
  "type": "entity_operation",
  "rag_id": "rag_1",
  "operation": "delete",
  "entity_name": "测试实体"
}
```

### 5.3 UCD 建模查询

```json
{
  "type": "query_ucd",
  "rag_id": "rag_1",
  "question": "系统需求是什么？",
  "mode": "hybrid",
  "out_json": "output_uc.json"
}
```

---

## 环境变量配置

以下环境变量用于配置 LLM 和 Embedding：

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `LLM_MODEL` | gpt-4 | LLM 模型名称 |
| `EMBEDDING_MODEL` | sentence-transformers/all-MiniLM-L6-v2 | Embedding 模型 |
| `EMBEDDING_DIM` | 384 | Embedding 维度 |
| `EMBEDDING_MAX_TOKEN` | 5000 | 最大 token 数 |
| `LITELLM_URL` | http://localhost:4000 | LiteLLM 服务地址 |
| `LITELLM_KEY` | sk-1234 | API 密钥 |
| `GRAPH_STORAGE` | NebulaGraphStorage | 图存储类型 |
| `VECTOR_STORAGE` | MilvusVectorDBStorage | 向量存储类型 |

---

## 错误响应

所有接口在发生错误时返回统一格式：

```json
{
  "detail": "错误描述信息"
}
```

常见 HTTP 状态码：

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在（如 RAG 实例不存在） |
| 500 | 服务器内部错误 |
