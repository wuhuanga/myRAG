# RAG Backend API 接口文档

**版本**: 3.0.0
**基础路径**: `http://localhost:8000/api`

---

## 目录

1. [管理接口 (Admin)](#1-管理接口-admin)
2. [文档接口 (Documents)](#2-文档接口-documents)
3. [查询接口 (Query)](#3-查询接口-query)
   - [3.1 查询知识库](#31-查询知识库)
   - [3.2 UCD 建模查询](#32-ucd-建模查询)
   - [3.3 清除缓存](#33-清除缓存)
   - [3.4 关键字列表检索](#34-关键字列表检索) ⭐ **新增**
   - [3.5 清理后的知识图谱检索](#35-清理后的知识图谱检索) ⭐ **新增**
   - [3.6 仅返回文档 Chunks](#36-仅返回文档-chunks) ⭐ **新增**
4. [图操作接口 (Graph)](#4-图操作接口-graph)
   - [4.11 获取 ECharts 图谱 JSON](#411-获取-echarts-图谱-json直接返回) ⭐ **推荐**
5. [WebSocket 接口](#5-websocket-接口)
6. [Rerank 配置](#6-rerank-配置)

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

### 2.6 删除文档

**DELETE** `/api/documents/delete/{rag_id}/{doc_id}`

删除指定文档及其所有关联数据，包括：
- ✅ Milvus 向量库（chunks、entities、relationships 的向量数据）
- ✅ NebulaGraph 图数据库（节点和边）
- ✅ 本地 KV 存储（text_chunks、full_docs、doc_status、full_entities、full_relations）
- ✅ **原始上传文件**（uploaded_files 目录下的文件）

**路径参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `rag_id` | string | 是 | RAG 实例 ID |
| `doc_id` | string | 是 | 文档 ID |

**请求示例**:
```bash
curl -X DELETE "http://localhost:8000/api/documents/delete/rag_1/doc_001"
```

**响应示例 (成功)**:
```json
{
  "status": "success",
  "doc_id": "doc_001",
  "file_path": "document.txt",
  "message": "Document deleted successfully",
  "rag_id": "rag_1",
  "file_deleted": true,
  "file_delete_message": "原始文件已删除: rag_1_document.txt"
}
```

**响应字段说明**:
- `file_deleted`: 布尔值，表示原始文件是否成功删除
- `file_delete_message`: 文件删除详情（成功、不存在或失败原因）

**响应示例 (未找到)**:
```json
{
  "detail": "Document not found: doc_001"
}
```

**响应示例 (失败)**:
```json
{
  "detail": "Deletion failed: error details"
}
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

### 3.4 关键字列表检索

**POST** `/api/query/keywords`

使用提供的关键字列表直接检索，不调用 LLM 提取关键字。关键字同时作为高优先级（搜索关系）和低优先级（搜索实体）关键词。

**请求体**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `rag_id` | string | 是 | - | RAG 实例 ID |
| `keywords` | list[string] | 是 | - | 关键字列表 |
| `mode` | string | 否 | hybrid | 查询模式 |
| `only_need_context` | bool | 否 | true | 只返回上下文 |
| `top_k` | int | 否 | None | 检索的实体/关系数量 |
| `chunk_top_k` | int | 否 | None | 检索的文本块数量 |
| `max_entity_tokens` | int | 否 | None | 实体最大 token 数 |
| `max_relation_tokens` | int | 否 | None | 关系最大 token 数 |
| `max_total_tokens` | int | 否 | None | 总最大 token 数 |
| `enable_rerank` | bool | 否 | None | 是否启用 Rerank |

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/query/keywords" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "rag_1",
    "keywords": ["知识图谱", "实体", "关系"],
    "mode": "hybrid",
    "chunk_top_k": 10,
    "enable_rerank": true
  }'
```

**响应示例**:
```json
{
  "rag_id": "rag_1",
  "keywords": ["知识图谱", "实体", "关系"],
  "context": "检索到的上下文内容...",
  "mode": "hybrid",
  "timestamp": "2024-01-15T10:30:00.000000"
}
```

---

### 3.5 清理后的知识图谱检索

**POST** `/api/query/graph-clean`

使用关键字检索知识图谱，返回清理后的实体和关系（去除 source_id、file_path、created_at 等元数据）。

**请求体**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `rag_id` | string | 是 | - | RAG 实例 ID |
| `keywords` | list[string] | 是 | - | 关键字列表 |
| `top_k` | int | 否 | None | 检索的实体/关系数量 |
| `chunk_top_k` | int | 否 | None | 检索的文本块数量 |
| `max_entity_tokens` | int | 否 | None | 实体最大 token 数 |
| `max_relation_tokens` | int | 否 | None | 关系最大 token 数 |
| `max_total_tokens` | int | 否 | None | 总最大 token 数 |
| `enable_rerank` | bool | 否 | None | 是否启用 Rerank |

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/query/graph-clean" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "rag_1",
    "keywords": ["知识图谱", "向量数据库"],
    "top_k": 20,
    "enable_rerank": true
  }'
```

**响应示例**:
```json
{
  "rag_id": "rag_1",
  "keywords": ["知识图谱", "向量数据库"],
  "entities": [
    {
      "entity_name": "知识图谱",
      "description": "一种结构化的知识表示方式",
      "entity_type": "CONCEPT"
    }
  ],
  "relationships": [
    {
      "src_id": "知识图谱",
      "tgt_id": "向量数据库",
      "description": "知识图谱使用向量数据库存储",
      "keywords": "存储,使用"
    }
  ],
  "timestamp": "2024-01-15T10:30:00.000000"
}
```

**返回字段说明**:
- **实体（entities）**：只包含 `entity_name`、`description`、`entity_type`
- **关系（relationships）**：只包含 `src_id`、`tgt_id`、`description`、`keywords`
- 已去除：`source_id`、`file_path`、`created_at`、`reference_id` 等元数据

---

### 3.6 仅返回文档 Chunks

**POST** `/api/query/chunks-only`

使用关键字检索，只返回文档 chunks（不返回知识图谱），保留顺序和相关性分数。

**请求体**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `rag_id` | string | 是 | - | RAG 实例 ID |
| `keywords` | list[string] | 是 | - | 关键字列表 |
| `chunk_top_k` | int | 否 | None | 检索的文本块数量 |
| `max_total_tokens` | int | 否 | None | 总最大 token 数 |
| `enable_rerank` | bool | 否 | None | 是否启用 Rerank |

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/query/chunks-only" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "rag_1",
    "keywords": ["部署", "配置"],
    "chunk_top_k": 5,
    "enable_rerank": true
  }'
```

**响应示例**:
```json
{
  "rag_id": "rag_1",
  "keywords": ["部署", "配置"],
  "chunks": [
    {
      "content": "系统部署需要配置以下环境变量...",
      "file_path": "deployment_guide.pdf",
      "chunk_id": "chunk-abc123",
      "reference_id": "ref-001"
    }
  ],
  "timestamp": "2024-01-15T10:30:00.000000"
}
```

**返回字段说明**:
- **content**：文本块内容
- **file_path**：来源文件路径
- **chunk_id**：文本块唯一标识
- **reference_id**：引用标识（用于追溯来源和相关性）

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

### 4.11 获取 ECharts 图谱 JSON（直接返回）

**GET** `/api/graph/echarts/{rag_id}`

直接返回 ECharts 格式的知识图谱 JSON 数据，无需指定输出路径。适用于前端直接获取并可视化。

**路径参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `rag_id` | string | 是 | RAG 实例 ID |

**请求示例**:
```bash
curl "http://localhost:8000/api/graph/echarts/rag_1"
```

**JavaScript/Fetch 示例**:
```javascript
// 获取并渲染 ECharts 图谱
fetch('http://localhost:8000/api/graph/echarts/rag_1')
  .then(response => response.json())
  .then(result => {
    const echarts_data = result.data;

    // 使用 ECharts 渲染
    const chart = echarts.init(document.getElementById('graph'));
    chart.setOption({
      series: [{
        type: 'graph',
        layout: 'force',
        data: echarts_data.nodes,
        links: echarts_data.links,
        categories: echarts_data.categories,
        roam: true,
        label: {
          show: true,
          position: 'right'
        },
        force: {
          repulsion: 1000,
          edgeLength: 150
        }
      }]
    });
  });
```

**响应示例**:
```json
{
  "status": "success",
  "rag_id": "rag_1",
  "data": {
    "nodes": [
      {
        "id": "知识图谱",
        "name": "知识图谱",
        "value": 15,
        "category": 0,
        "entity_type": "CONCEPT",
        "description": "一种结构化的知识表示方式"
      },
      {
        "id": "人工智能",
        "name": "人工智能",
        "value": 8,
        "category": 1,
        "entity_type": "TECHNOLOGY"
      }
    ],
    "links": [
      {
        "source": "知识图谱",
        "target": "人工智能",
        "description": "是...的一部分",
        "weight": 1.0,
        "keywords": "应用,技术"
      }
    ],
    "categories": [
      {"name": "CONCEPT"},
      {"name": "TECHNOLOGY"}
    ]
  }
}
```

**数据结构说明**:

**nodes** (节点数组):
- `id`: 节点唯一标识（实体名称）
- `name`: 显示名称
- `value`: 节点大小值（基于度数计算）
- `category`: 分类索引
- `entity_type`: 实体类型
- `description`: 实体描述（可选）

**links** (边数组):
- `source`: 源节点 ID
- `target`: 目标节点 ID
- `description`: 关系描述（可选）
- `weight`: 关系权重（可选）
- `keywords`: 关键词（可选）

**categories** (分类数组):
- `name`: 分类名称

**完整 ECharts 配置示例**:
```javascript
const option = {
  title: {
    text: 'Knowledge Graph',
    top: 'top',
    left: 'center'
  },
  tooltip: {
    formatter: function(params) {
      if (params.dataType === 'node') {
        return `<b>${params.data.name}</b><br/>
                类型: ${params.data.entity_type}<br/>
                连接数: ${params.data.value}<br/>
                ${params.data.description || ''}`;
      } else {
        return `${params.data.source} → ${params.data.target}<br/>
                ${params.data.description || ''}<br/>
                权重: ${params.data.weight || 'N/A'}`;
      }
    }
  },
  legend: [{
    data: echarts_data.categories.map(c => c.name),
    orient: 'vertical',
    left: 'left'
  }],
  series: [{
    type: 'graph',
    layout: 'force',
    data: echarts_data.nodes,
    links: echarts_data.links,
    categories: echarts_data.categories,
    roam: true,
    label: {
      show: true,
      position: 'right',
      formatter: '{b}'
    },
    labelLayout: {
      hideOverlap: true
    },
    scaleLimit: {
      min: 0.4,
      max: 2
    },
    lineStyle: {
      color: 'source',
      curveness: 0.3
    },
    emphasis: {
      focus: 'adjacency',
      lineStyle: {
        width: 10
      }
    },
    force: {
      repulsion: 1000,
      gravity: 0.1,
      edgeLength: [100, 200],
      layoutAnimation: true
    }
  }]
};
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

## 6. Rerank 配置

### 6.1 什么是 Rerank？

Rerank（重排序）是一种检索优化技术，在初步检索后使用专门的模型对结果进行重新排序，提高相关性最高的文档的排名。

**使用场景**：
- 提高检索准确率
- 优化搜索结果排序
- 支持多语言语义匹配

### 6.2 启动本地 Rerank 服务

使用提供的 CPU rerank 服务器：

```bash
# 运行 rerank 服务（默认监听 7777 端口）
python cpu_rerank_server.py
```

**模型**：Qwen3-Reranker-0.6B（CPU 友好）

### 6.3 环境变量配置

在 `.env` 文件中配置 rerank 相关变量：

```bash
# Rerank 服务配置
LOCAL_RERANK_URL=http://localhost:7777/v1/rerank
LOCAL_RERANK_MODEL=local-reranker
LOCAL_RERANK_API_KEY=  # 本地服务可选
```

**重要**：配置后需要重启 API 服务器：
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 6.4 在查询中使用 Rerank

**方法 1：查询时启用**
```bash
curl -X POST "http://localhost:8000/api/query/" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "rag_1",
    "question": "什么是知识图谱？",
    "enable_rerank": true,
    "chunk_top_k": 20
  }'
```

**方法 2：在 RAG 实例创建时配置默认行为**

通过 `addon_params` 或环境变量配置全局 rerank 行为。

### 6.5 Rerank 工作流程

1. **初步检索**：向量检索获取 `chunk_top_k` 个候选文档（如 20 个）
2. **Rerank 重排**：使用 rerank 模型计算相关性分数
3. **结果排序**：按相关性分数重新排序
4. **返回结果**：返回排序后的 top-k 结果

### 6.6 故障排查

**问题 1：WARNING: Rerank is enabled but no rerank model is configured**

**原因**：
- `.env` 文件未被加载
- `rerank_model_func` 未配置

**解决方案**：
1. 确保 `cpu_rerank_server.py` 正在运行
2. 检查 `.env` 文件中的 `LOCAL_RERANK_URL` 配置
3. 重启 API 服务器

**问题 2：Cannot handle batch sizes > 1 if no padding token is defined**

**原因**：旧版本 rerank 服务器缺少 padding token 配置

**解决方案**：使用仓库中提供的修复版 `cpu_rerank_server.py`

**问题 3：Rerank API error 500**

**原因**：
- Rerank 服务未启动
- 端口被占用
- 模型加载失败

**解决方案**：
1. 检查 rerank 服务日志
2. 确认端口 7777 可用
3. 确保有足够的内存加载模型

---

## 环境变量配置

以下环境变量用于配置 LLM、Embedding 和 Rerank：

### LLM 和 Embedding 配置

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `LLM_MODEL` | gpt-4 | LLM 模型名称 |
| `EMBEDDING_MODEL` | sentence-transformers/all-MiniLM-L6-v2 | Embedding 模型 |
| `EMBEDDING_DIM` | 384 | Embedding 维度 |
| `EMBEDDING_MAX_TOKEN` | 5000 | 最大 token 数 |
| `LITELLM_URL` | http://localhost:4000 | LiteLLM 服务地址 |
| `LITELLM_KEY` | sk-1234 | API 密钥 |

### 存储配置

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `GRAPH_STORAGE` | NebulaGraphStorage | 图存储类型 |
| `VECTOR_STORAGE` | MilvusVectorDBStorage | 向量存储类型 |

### Rerank 配置

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `LOCAL_RERANK_URL` | http://localhost:7777/v1/rerank | Rerank 服务地址 |
| `LOCAL_RERANK_MODEL` | local-reranker | Rerank 模型名称 |
| `LOCAL_RERANK_API_KEY` | - | API 密钥（本地服务可选） |

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
