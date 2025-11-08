# RAG 后端 API 接口文档

## 目录

- [1. 概述](#1-概述)
- [2. 管理接口 (Admin)](#2-管理接口-admin)
  - [2.1 健康检查](#21-健康检查)
  - [2.2 创建 RAG 实例](#22-创建-rag-实例)
  - [2.3 列出所有 RAG 实例](#23-列出所有-rag-实例)
  - [2.4 获取 RAG 实例详情](#24-获取-rag-实例详情)
  - [2.5 删除 RAG 实例](#25-删除-rag-实例)
  - [2.6 初始化 UCD 建模器](#26-初始化-ucd-建模器)
- [3. 文档操作接口 (Documents)](#3-文档操作接口-documents)
  - [3.1 上传文档](#31-上传文档)
  - [3.2 插入文档内容](#32-插入文档内容)
  - [3.3 批量插入文档](#33-批量插入文档)
  - [3.4 获取文档状态](#34-获取文档状态)
  - [3.5 获取指定状态的文档列表](#35-获取指定状态的文档列表)
- [4. 查询接口 (Query)](#4-查询接口-query)
  - [4.1 查询知识库](#41-查询知识库)
  - [4.2 UCD 建模查询](#42-ucd-建模查询)
  - [4.3 清除缓存](#43-清除缓存)
- [5. 图谱操作接口 (Graph)](#5-图谱操作接口-graph)
  - [5.1 创建实体](#51-创建实体)
  - [5.2 编辑实体](#52-编辑实体)
  - [5.3 删除实体](#53-删除实体)
  - [5.4 获取实体信息](#54-获取实体信息)
  - [5.5 合并实体](#55-合并实体)
  - [5.6 创建关系](#56-创建关系)
  - [5.7 编辑关系](#57-编辑关系)
  - [5.8 删除关系](#58-删除关系)
  - [5.9 获取关系信息](#59-获取关系信息)
  - [5.10 导出数据](#510-导出数据)
- [6. WebSocket 接口](#6-websocket-接口)
  - [6.1 WebSocket 连接](#61-websocket-连接)

---

## 1. 概述

### 基本信息
- **服务名称**: RAG Backend API
- **版本**: 3.0.0
- **基础URL**: `http://localhost:8000`
- **API前缀**: `/api`

### 启动服务
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 通用响应格式
所有接口响应均为 JSON 格式。成功响应通常包含 `status` 字段，失败响应包含 `detail` 字段。

---

## 2. 管理接口 (Admin)

### 2.1 健康检查

**接口描述**: 检查服务健康状态和系统信息

**请求方法**: `GET`

**接口路径**: `/api/admin/health`

**请求参数**: 无

**请求示例**:
```bash
curl -X GET "http://localhost:8000/api/admin/health"
```

**响应示例**:
```json
{
  "status": "healthy",
  "rag_instances_count": 2,
  "ucd_initialized": true,
  "timestamp": "2025-01-08T10:30:00.123456"
}
```

---

### 2.2 创建 RAG 实例

**接口描述**: 创建一个新的 RAG 实例

**请求方法**: `POST`

**接口路径**: `/api/admin/rag_instances/create`

**请求参数** (JSON Body):
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| rag_id | string | 是 | RAG 实例唯一标识符 |
| description | string | 否 | 实例描述 |
| working_dir | string | 是 | 工作目录路径 |
| workspace | string | 是 | 工作空间名称 |
| kv_storage | string | 否 | KV 存储类型 |
| vector_storage | string | 否 | 向量存储类型 |
| graph_storage | string | 否 | 图存储类型 |
| doc_status_storage | string | 否 | 文档状态存储类型 |
| top_k | integer | 否 | 查询返回的 top-k 结果数 |
| chunk_top_k | integer | 否 | 块级 top-k 结果数 |
| max_entity_tokens | integer | 否 | 最大实体 token 数 |
| max_relation_tokens | integer | 否 | 最大关系 token 数 |
| max_total_tokens | integer | 否 | 最大总 token 数 |
| cosine_threshold | float | 否 | 余弦相似度阈值(默认 0.3) |
| related_chunk_number | integer | 否 | 相关块数量(默认 5) |
| chunk_token_size | integer | 否 | 块大小(默认 1200) |
| chunk_overlap_token_size | integer | 否 | 块重叠大小(默认 100) |
| enable_llm_cache | boolean | 否 | 是否启用 LLM 缓存(默认 true) |
| enable_llm_cache_for_entity_extract | boolean | 否 | 实体提取是否使用缓存(默认 true) |
| llm_model | string | 否 | LLM 模型名称 |
| embedding_model | string | 否 | 嵌入模型名称 |
| embedding_dim | integer | 否 | 嵌入维度 |
| embedding_max_token | integer | 否 | 嵌入最大 token 数 |
| litellm_url | string | 否 | LiteLLM 服务 URL |
| litellm_key | string | 否 | LiteLLM API Key |

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/admin/rag_instances/create" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "my_rag_instance",
    "description": "我的第一个 RAG 实例",
    "working_dir": "./data/my_rag",
    "workspace": "workspace_1",
    "kv_storage": "JsonKVStorage",
    "vector_storage": "NanoVectorDBStorage",
    "graph_storage": "NetworkXStorage",
    "doc_status_storage": "JsonDocStatusStorage",
    "top_k": 20,
    "chunk_top_k": 10,
    "cosine_threshold": 0.3,
    "enable_llm_cache": true
  }'
```

**响应示例**:
```json
{
  "status": "success",
  "message": "RAG 实例 'my_rag_instance' 创建成功",
  "rag_id": "my_rag_instance",
  "working_dir": "./data/my_rag",
  "workspace": "workspace_1",
  "llm_model": "gpt-4o-mini",
  "embedding_model": "text-embedding-3-small"
}
```

---

### 2.3 列出所有 RAG 实例

**接口描述**: 获取所有已创建的 RAG 实例列表

**请求方法**: `GET`

**接口路径**: `/api/admin/rag_instances/list`

**请求参数**: 无

**请求示例**:
```bash
curl -X GET "http://localhost:8000/api/admin/rag_instances/list"
```

**响应示例**:
```json
[
  {
    "rag_id": "my_rag_instance",
    "description": "我的第一个 RAG 实例",
    "working_dir": "./data/my_rag",
    "workspace": "workspace_1",
    "created_at": "2025-01-08T10:00:00.000000",
    "llm_model": "gpt-4o-mini",
    "embedding_model": "text-embedding-3-small"
  },
  {
    "rag_id": "rag_instance_2",
    "description": "第二个 RAG 实例",
    "working_dir": "./data/rag_2",
    "workspace": "workspace_2",
    "created_at": "2025-01-08T11:00:00.000000",
    "llm_model": "gpt-4o-mini",
    "embedding_model": "text-embedding-3-small"
  }
]
```

---

### 2.4 获取 RAG 实例详情

**接口描述**: 获取指定 RAG 实例的详细信息

**请求方法**: `GET`

**接口路径**: `/api/admin/rag_instances/{rag_id}`

**路径参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| rag_id | string | 是 | RAG 实例ID |

**请求示例**:
```bash
curl -X GET "http://localhost:8000/api/admin/rag_instances/my_rag_instance"
```

**响应示例**:
```json
{
  "status": "success",
  "rag_id": "my_rag_instance",
  "working_dir": "./data/my_rag",
  "workspace": "workspace_1",
  "created_at": "2025-01-08T10:00:00.000000",
  "llm_model": "gpt-4o-mini",
  "embedding_model": "text-embedding-3-small",
  "embedding_dim": 1536,
  "config": {
    "kv_storage": "JsonKVStorage",
    "vector_storage": "NanoVectorDBStorage",
    "graph_storage": "NetworkXStorage",
    "doc_status_storage": "JsonDocStatusStorage",
    "top_k": 20,
    "chunk_top_k": 10,
    "max_entity_tokens": 6000,
    "max_relation_tokens": 8000,
    "max_total_tokens": 16300,
    "cosine_threshold": 0.3,
    "related_chunk_number": 5,
    "chunk_token_size": 1200,
    "chunk_overlap_token_size": 100,
    "enable_llm_cache": true,
    "enable_llm_cache_for_entity_extract": true
  }
}
```

---

### 2.5 删除 RAG 实例

**接口描述**: 删除指定的 RAG 实例

**请求方法**: `DELETE`

**接口路径**: `/api/admin/rag_instances/{rag_id}`

**路径参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| rag_id | string | 是 | RAG 实例ID |

**请求示例**:
```bash
curl -X DELETE "http://localhost:8000/api/admin/rag_instances/my_rag_instance"
```

**响应示例**:
```json
{
  "status": "success",
  "message": "RAG 实例 'my_rag_instance' 已删除",
  "rag_id": "my_rag_instance"
}
```

---

### 2.6 初始化 UCD 建模器

**接口描述**: 初始化用例图(UCD)建模器

**请求方法**: `POST`

**接口路径**: `/api/admin/ucd/init`

**请求参数** (Query):
| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| base_url | string | 否 | http://localhost:4000 | LLM 服务地址 |
| api_key | string | 否 | sk-1234 | API Key |
| model_name | string | 否 | gpt-4 | 模型名称 |

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/admin/ucd/init?base_url=http://localhost:4000&api_key=sk-1234&model_name=gpt-4"
```

**响应示例**:
```json
{
  "status": "success",
  "message": "UCD 建模器初始化成功",
  "config": {
    "base_url": "http://localhost:4000",
    "model_name": "gpt-4"
  }
}
```

---

## 3. 文档操作接口 (Documents)

### 3.1 上传文档

**接口描述**: 上传文档文件并自动处理

**请求方法**: `POST`

**接口路径**: `/api/documents/upload`

**请求参数**:
| 参数名 | 类型 | 位置 | 必填 | 说明 |
|--------|------|------|------|------|
| rag_id | string | query | 是 | RAG 实例ID |
| file | file | form-data | 是 | 上传的文件 |
| custom_id | string | query | 否 | 自定义文档ID |

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/documents/upload?rag_id=my_rag_instance&custom_id=doc_001" \
  -F "file=@./document.txt"
```

**响应示例**:
```json
{
  "status": "success",
  "message": "文档 document.txt 已成功上传并处理",
  "file_path": "uploaded_files/document.txt",
  "custom_id": "doc_001",
  "rag_id": "my_rag_instance"
}
```

---

### 3.2 插入文档内容

**接口描述**: 直接插入文档内容到知识库

**请求方法**: `POST`

**接口路径**: `/api/documents/insert`

**请求参数** (JSON Body):
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| rag_id | string | 是 | RAG 实例ID |
| content | string | 是 | 文档内容 |
| file_path | string | 是 | 文件路径或文件名 |
| doc_id | string | 否 | 文档ID |

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/documents/insert" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "my_rag_instance",
    "content": "这是一篇关于人工智能的文档。人工智能(AI)是计算机科学的一个分支,致力于创建能够执行通常需要人类智能的任务的系统。",
    "file_path": "ai_introduction.txt",
    "doc_id": "doc_ai_001"
  }'
```

**响应示例**:
```json
{
  "status": "success",
  "message": "文档内容已成功插入(文件: ai_introduction.txt)",
  "file_path": "ai_introduction.txt",
  "doc_id": "doc_ai_001",
  "content_length": 98,
  "rag_id": "my_rag_instance"
}
```

---

### 3.3 批量插入文档

**接口描述**: 批量插入多个文档

**请求方法**: `POST`

**接口路径**: `/api/documents/batch_insert`

**请求参数** (JSON Body):
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| rag_id | string | 是 | RAG 实例ID |
| documents | array | 是 | 文档列表 |

文档对象结构:
| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| content | string | 是 | 文档内容 |
| file_path | string | 是 | 文件路径或文件名 |
| doc_id | string | 否 | 文档ID |

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/documents/batch_insert" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "my_rag_instance",
    "documents": [
      {
        "content": "机器学习是人工智能的一个子领域。",
        "file_path": "ml_intro.txt",
        "doc_id": "doc_ml_001"
      },
      {
        "content": "深度学习使用神经网络来处理数据。",
        "file_path": "dl_intro.txt",
        "doc_id": "doc_dl_001"
      },
      {
        "content": "自然语言处理是 AI 的重要应用领域。",
        "file_path": "nlp_intro.txt",
        "doc_id": "doc_nlp_001"
      }
    ]
  }'
```

**响应示例**:
```json
{
  "status": "success",
  "message": "成功批量插入 3 个文档",
  "count": 3,
  "files": [
    "ml_intro.txt",
    "dl_intro.txt",
    "nlp_intro.txt"
  ],
  "rag_id": "my_rag_instance"
}
```

---

### 3.4 获取文档状态

**接口描述**: 获取所有文档的处理状态统计

**请求方法**: `GET`

**接口路径**: `/api/documents/status/{rag_id}`

**路径参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| rag_id | string | 是 | RAG 实例ID |

**请求示例**:
```bash
curl -X GET "http://localhost:8000/api/documents/status/my_rag_instance"
```

**响应示例**:
```json
{
  "total": 10,
  "processed": 8,
  "pending": 1,
  "failed": 1,
  "status_counts": {
    "PROCESSED": 8,
    "PENDING": 1,
    "FAILED": 1
  }
}
```

---

### 3.5 获取指定状态的文档列表

**接口描述**: 根据处理状态获取文档列表

**请求方法**: `GET`

**接口路径**: `/api/documents/list/{rag_id}/{status}`

**路径参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| rag_id | string | 是 | RAG 实例ID |
| status | string | 是 | 文档状态(PROCESSED/PENDING/FAILED) |

**请求示例**:
```bash
curl -X GET "http://localhost:8000/api/documents/list/my_rag_instance/PROCESSED"
```

**响应示例**:
```json
{
  "status": "PROCESSED",
  "count": 8,
  "documents": [
    {
      "doc_id": "doc_ai_001",
      "file_name": "ai_introduction.txt",
      "created_at": "2025-01-08T10:15:00.000000",
      "updated_at": "2025-01-08T10:15:10.000000",
      "error_message": null,
      "status": "PROCESSED"
    },
    {
      "doc_id": "doc_ml_001",
      "file_name": "ml_intro.txt",
      "created_at": "2025-01-08T10:20:00.000000",
      "updated_at": "2025-01-08T10:20:05.000000",
      "error_message": null,
      "status": "PROCESSED"
    }
  ]
}
```

---

## 4. 查询接口 (Query)

### 4.1 查询知识库

**接口描述**: 查询 RAG 知识库获取答案

**请求方法**: `POST`

**接口路径**: `/api/query/`

**请求参数** (JSON Body):
| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| rag_id | string | 是 | - | RAG 实例ID |
| question | string | 是 | - | 查询问题 |
| mode | string | 否 | hybrid | 查询模式(naive/local/global/hybrid) |
| only_need_context | boolean | 否 | true | 是否只需要上下文 |
| top_k | integer | 否 | 20 | Top-K 结果数量 |
| chunk_top_k | integer | 否 | 10 | 块级 Top-K 结果数量 |
| max_entity_tokens | integer | 否 | 6000 | 最大实体 token 数 |
| max_relation_tokens | integer | 否 | 8000 | 最大关系 token 数 |
| max_total_tokens | integer | 否 | 16300 | 最大总 token 数 |

**查询模式说明**:
- `naive`: 仅使用向量检索
- `local`: 基于本地上下文的检索
- `global`: 基于全局知识图谱的检索
- `hybrid`: 混合模式(推荐)

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/query/" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "my_rag_instance",
    "question": "什么是人工智能?",
    "mode": "hybrid",
    "only_need_context": true,
    "top_k": 20
  }'
```

**响应示例**:
```json
{
  "rag_id": "my_rag_instance",
  "question": "什么是人工智能?",
  "answer": "人工智能(AI)是计算机科学的一个分支,致力于创建能够执行通常需要人类智能的任务的系统。它包括机器学习、深度学习、自然语言处理等多个子领域。",
  "mode": "hybrid",
  "timestamp": "2025-01-08T10:30:00.123456"
}
```

---

### 4.2 UCD 建模查询

**接口描述**: 执行查询并进行用例图(UCD)建模

**请求方法**: `POST`

**接口路径**: `/api/query/ucd`

**请求参数** (JSON Body):
| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| rag_id | string | 是 | - | RAG 实例ID |
| question | string | 是 | - | 查询问题 |
| mode | string | 否 | hybrid | 查询模式 |
| out_json | string | 否 | output_uc.json | 输出文件名 |

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/query/ucd" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "my_rag_instance",
    "question": "在线购物系统有哪些用例?",
    "mode": "hybrid",
    "out_json": "shopping_ucd.json"
  }'
```

**响应示例**:
```json
{
  "status": "success",
  "rag_id": "my_rag_instance",
  "question": "在线购物系统有哪些用例?",
  "context": "在线购物系统包括用户注册、商品浏览、添加到购物车、下单、支付、订单管理等功能...",
  "ucd_model": {
    "actors": ["用户", "管理员", "支付系统"],
    "use_cases": [
      {
        "name": "用户注册",
        "description": "新用户创建账号"
      },
      {
        "name": "商品浏览",
        "description": "浏览商品列表和详情"
      },
      {
        "name": "下单购买",
        "description": "选择商品并完成购买"
      }
    ],
    "relationships": [
      {
        "from": "用户",
        "to": "用户注册",
        "type": "association"
      }
    ]
  },
  "output_file": "shopping_ucd.json",
  "mode": "hybrid",
  "timestamp": "2025-01-08T10:35:00.123456"
}
```

---

### 4.3 清除缓存

**接口描述**: 清除 LLM 缓存或所有缓存

**请求方法**: `POST`

**接口路径**: `/api/query/clear_cache`

**请求参数** (JSON Body):
| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| rag_id | string | 是 | - | RAG 实例ID |
| cache_type | string | 否 | all | 缓存类型(llm_cache/all) |

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/query/clear_cache" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "my_rag_instance",
    "cache_type": "llm_cache"
  }'
```

**响应示例**:
```json
{
  "status": "success",
  "message": "RAG 实例 my_rag_instance 的 LLM 缓存已清除",
  "rag_id": "my_rag_instance",
  "cache_type": "llm_cache"
}
```

---

## 5. 图谱操作接口 (Graph)

### 5.1 创建实体

**接口描述**: 在知识图谱中创建新实体

**请求方法**: `POST`

**接口路径**: `/api/graph/entities/create`

**请求参数** (JSON Body):
| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| rag_id | string | 是 | - | RAG 实例ID |
| entity_name | string | 是 | - | 实体名称 |
| description | string | 否 | - | 实体描述 |
| entity_type | string | 否 | UNKNOWN | 实体类型 |
| source_id | string | 否 | manual_creation | 来源ID |
| file_path | string | 否 | manual_creation | 文件路径 |

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/graph/entities/create" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "my_rag_instance",
    "entity_name": "深度学习",
    "description": "一种基于人工神经网络的机器学习方法",
    "entity_type": "CONCEPT",
    "source_id": "manual_001",
    "file_path": "knowledge_base.txt"
  }'
```

**响应示例**:
```json
{
  "status": "success",
  "message": "实体 '深度学习' 创建成功",
  "entity": {
    "name": "深度学习",
    "description": "一种基于人工神经网络的机器学习方法",
    "entity_type": "CONCEPT",
    "source_id": "manual_001",
    "file_path": "knowledge_base.txt"
  },
  "rag_id": "my_rag_instance"
}
```

---

### 5.2 编辑实体

**接口描述**: 编辑知识图谱中的实体

**请求方法**: `POST`

**接口路径**: `/api/graph/entities/edit`

**请求参数** (JSON Body):
| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| rag_id | string | 是 | - | RAG 实例ID |
| entity_name | string | 是 | - | 实体名称 |
| updated_data | object | 是 | - | 更新的数据字典 |
| allow_rename | boolean | 否 | true | 是否允许重命名 |

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/graph/entities/edit" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "my_rag_instance",
    "entity_name": "深度学习",
    "updated_data": {
      "description": "一种使用多层神经网络进行特征学习的机器学习方法",
      "entity_type": "TECHNOLOGY"
    },
    "allow_rename": true
  }'
```

**响应示例**:
```json
{
  "status": "success",
  "message": "实体 '深度学习' 更新成功",
  "entity": {
    "name": "深度学习",
    "description": "一种使用多层神经网络进行特征学习的机器学习方法",
    "entity_type": "TECHNOLOGY"
  },
  "rag_id": "my_rag_instance"
}
```

---

### 5.3 删除实体

**接口描述**: 删除知识图谱中的实体

**请求方法**: `POST`

**接口路径**: `/api/graph/entities/delete`

**请求参数** (JSON Body):
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| rag_id | string | 是 | RAG 实例ID |
| entity_name | string | 是 | 实体名称 |

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/graph/entities/delete" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "my_rag_instance",
    "entity_name": "深度学习"
  }'
```

**响应示例**:
```json
{
  "status": "success",
  "message": "实体已删除",
  "entity_name": "深度学习",
  "rag_id": "my_rag_instance"
}
```

---

### 5.4 获取实体信息

**接口描述**: 获取实体的详细信息

**请求方法**: `POST`

**接口路径**: `/api/graph/entities/info`

**请求参数** (JSON Body):
| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| rag_id | string | 是 | - | RAG 实例ID |
| entity_name | string | 是 | - | 实体名称 |
| include_vector_data | boolean | 否 | false | 是否包含向量数据 |

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/graph/entities/info" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "my_rag_instance",
    "entity_name": "深度学习",
    "include_vector_data": false
  }'
```

**响应示例**:
```json
{
  "status": "success",
  "entity_info": {
    "name": "深度学习",
    "description": "一种使用多层神经网络进行特征学习的机器学习方法",
    "entity_type": "TECHNOLOGY",
    "source_id": "manual_001",
    "file_path": "knowledge_base.txt",
    "related_entities": ["机器学习", "神经网络", "人工智能"],
    "relations_count": 5
  },
  "rag_id": "my_rag_instance"
}
```

---

### 5.5 合并实体

**接口描述**: 将多个实体合并为一个实体

**请求方法**: `POST`

**接口路径**: `/api/graph/entities/merge`

**请求参数** (JSON Body):
| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| rag_id | string | 是 | - | RAG 实例ID |
| source_entities | array | 是 | - | 源实体名称列表 |
| target_entity | string | 是 | - | 目标实体名称 |
| merge_strategy | object | 否 | null | 合并策略 |
| target_entity_data | object | 否 | null | 目标实体数据 |

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/graph/entities/merge" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "my_rag_instance",
    "source_entities": ["DL", "深度神经网络"],
    "target_entity": "深度学习",
    "merge_strategy": {
      "description": "merge"
    },
    "target_entity_data": {
      "entity_type": "TECHNOLOGY"
    }
  }'
```

**响应示例**:
```json
{
  "status": "success",
  "message": "成功合并 2 个实体到 '深度学习'",
  "merged_entity": {
    "name": "深度学习",
    "description": "一种使用多层神经网络进行特征学习的机器学习方法",
    "entity_type": "TECHNOLOGY"
  },
  "rag_id": "my_rag_instance"
}
```

---

### 5.6 创建关系

**接口描述**: 在知识图谱中创建实体间关系

**请求方法**: `POST`

**接口路径**: `/api/graph/relations/create`

**请求参数** (JSON Body):
| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| rag_id | string | 是 | - | RAG 实例ID |
| source_entity | string | 是 | - | 源实体名称 |
| target_entity | string | 是 | - | 目标实体名称 |
| description | string | 否 | - | 关系描述 |
| keywords | string | 否 | - | 关键词 |
| weight | float | 否 | 1.0 | 关系权重 |
| source_id | string | 否 | manual_creation | 来源ID |
| file_path | string | 否 | manual_creation | 文件路径 |

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/graph/relations/create" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "my_rag_instance",
    "source_entity": "深度学习",
    "target_entity": "机器学习",
    "description": "深度学习是机器学习的一个子领域",
    "keywords": "子领域,包含",
    "weight": 0.9,
    "source_id": "manual_002",
    "file_path": "knowledge_base.txt"
  }'
```

**响应示例**:
```json
{
  "status": "success",
  "message": "关系 '深度学习' -> '机器学习' 创建成功",
  "relation": {
    "source_entity": "深度学习",
    "target_entity": "机器学习",
    "description": "深度学习是机器学习的一个子领域",
    "keywords": "子领域,包含",
    "weight": 0.9,
    "source_id": "manual_002",
    "file_path": "knowledge_base.txt"
  },
  "rag_id": "my_rag_instance"
}
```

---

### 5.7 编辑关系

**接口描述**: 编辑知识图谱中的关系

**请求方法**: `POST`

**接口路径**: `/api/graph/relations/edit`

**请求参数** (JSON Body):
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| rag_id | string | 是 | RAG 实例ID |
| source_entity | string | 是 | 源实体名称 |
| target_entity | string | 是 | 目标实体名称 |
| updated_data | object | 是 | 更新的数据字典 |

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/graph/relations/edit" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "my_rag_instance",
    "source_entity": "深度学习",
    "target_entity": "机器学习",
    "updated_data": {
      "description": "深度学习是机器学习的重要分支",
      "weight": 0.95
    }
  }'
```

**响应示例**:
```json
{
  "status": "success",
  "message": "关系 '深度学习' -> '机器学习' 更新成功",
  "relation": {
    "source_entity": "深度学习",
    "target_entity": "机器学习",
    "description": "深度学习是机器学习的重要分支",
    "weight": 0.95
  },
  "rag_id": "my_rag_instance"
}
```

---

### 5.8 删除关系

**接口描述**: 删除知识图谱中的关系

**请求方法**: `POST`

**接口路径**: `/api/graph/relations/delete`

**请求参数** (JSON Body):
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| rag_id | string | 是 | RAG 实例ID |
| source_entity | string | 是 | 源实体名称 |
| target_entity | string | 是 | 目标实体名称 |

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/graph/relations/delete" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "my_rag_instance",
    "source_entity": "深度学习",
    "target_entity": "机器学习"
  }'
```

**响应示例**:
```json
{
  "status": "success",
  "message": "关系已删除",
  "source_entity": "深度学习",
  "target_entity": "机器学习",
  "rag_id": "my_rag_instance"
}
```

---

### 5.9 获取关系信息

**接口描述**: 获取关系的详细信息

**请求方法**: `POST`

**接口路径**: `/api/graph/relations/info`

**请求参数** (JSON Body):
| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| rag_id | string | 是 | - | RAG 实例ID |
| source_entity | string | 是 | - | 源实体名称 |
| target_entity | string | 是 | - | 目标实体名称 |
| include_vector_data | boolean | 否 | false | 是否包含向量数据 |

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/graph/relations/info" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "my_rag_instance",
    "source_entity": "深度学习",
    "target_entity": "机器学习",
    "include_vector_data": false
  }'
```

**响应示例**:
```json
{
  "status": "success",
  "relation_info": {
    "source_entity": "深度学习",
    "target_entity": "机器学习",
    "description": "深度学习是机器学习的重要分支",
    "keywords": "子领域,包含",
    "weight": 0.95,
    "source_id": "manual_002",
    "file_path": "knowledge_base.txt",
    "created_at": "2025-01-08T11:00:00.000000"
  },
  "rag_id": "my_rag_instance"
}
```

---

### 5.10 导出数据

**接口描述**: 导出知识图谱数据到文件

**请求方法**: `POST`

**接口路径**: `/api/graph/export`

**请求参数** (JSON Body):
| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| rag_id | string | 是 | - | RAG 实例ID |
| output_path | string | 是 | - | 输出文件路径 |
| file_format | string | 否 | csv | 文件格式(csv/excel/md/txt) |
| include_vector_data | boolean | 否 | false | 是否包含向量数据 |

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/graph/export" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "my_rag_instance",
    "output_path": "./exports/knowledge_graph.csv",
    "file_format": "csv",
    "include_vector_data": false
  }'
```

**响应示例**:
```json
{
  "status": "success",
  "message": "数据已成功导出到 ./exports/knowledge_graph.csv",
  "output_path": "./exports/knowledge_graph.csv",
  "format": "csv",
  "rag_id": "my_rag_instance"
}
```

---

## 6. WebSocket 接口

### 6.1 WebSocket 连接

**接口描述**: 建立 WebSocket 连接进行实时通信

**协议**: `WebSocket`

**接口路径**: `/ws`

**连接示例** (JavaScript):
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
  console.log('WebSocket 连接已建立');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('收到消息:', data);
};

ws.onerror = (error) => {
  console.error('WebSocket 错误:', error);
};

ws.onclose = () => {
  console.log('WebSocket 连接已关闭');
};
```

**支持的消息类型**:

#### 6.1.1 查询消息

**发送消息格式**:
```json
{
  "type": "query",
  "rag_id": "my_rag_instance",
  "question": "什么是人工智能?",
  "mode": "hybrid"
}
```

**接收消息示例**:
```json
{
  "type": "status",
  "message": "正在查询..."
}
```

```json
{
  "type": "answer",
  "rag_id": "my_rag_instance",
  "question": "什么是人工智能?",
  "context": "人工智能(AI)是计算机科学的一个分支...",
  "mode": "hybrid"
}
```

#### 6.1.2 实体操作消息

**创建实体 - 发送消息**:
```json
{
  "type": "entity_operation",
  "operation": "create",
  "rag_id": "my_rag_instance",
  "entity_name": "神经网络",
  "entity_data": {
    "description": "模拟人脑神经元网络的计算模型",
    "entity_type": "CONCEPT"
  }
}
```

**接收消息**:
```json
{
  "type": "entity_created",
  "rag_id": "my_rag_instance",
  "result": {
    "name": "神经网络",
    "description": "模拟人脑神经元网络的计算模型",
    "entity_type": "CONCEPT"
  }
}
```

**删除实体 - 发送消息**:
```json
{
  "type": "entity_operation",
  "operation": "delete",
  "rag_id": "my_rag_instance",
  "entity_name": "神经网络"
}
```

**接收消息**:
```json
{
  "type": "entity_deleted",
  "rag_id": "my_rag_instance",
  "result": {
    "status": "success",
    "message": "实体已删除"
  }
}
```

#### 6.1.3 UCD 建模消息

**发送消息格式**:
```json
{
  "type": "query_ucd",
  "rag_id": "my_rag_instance",
  "question": "在线购物系统有哪些用例?",
  "mode": "hybrid",
  "out_json": "shopping_ucd.json"
}
```

**接收消息示例**:
```json
{
  "type": "status",
  "message": "正在检索知识..."
}
```

```json
{
  "type": "status",
  "message": "正在进行 UCD 建模..."
}
```

```json
{
  "type": "ucd_result",
  "rag_id": "my_rag_instance",
  "question": "在线购物系统有哪些用例?",
  "context": "在线购物系统包括...",
  "ucd_model": {
    "actors": ["用户", "管理员"],
    "use_cases": [...]
  },
  "output_file": "shopping_ucd.json"
}
```

#### 6.1.4 错误消息

**接收消息示例**:
```json
{
  "type": "error",
  "message": "必须指定 rag_id"
}
```

---

## 附录

### A. 错误码说明

| HTTP 状态码 | 说明 |
|------------|------|
| 200 | 请求成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在(如 RAG 实例不存在) |
| 500 | 服务器内部错误 |

### B. 完整工作流示例

以下是一个完整的使用流程:

```bash
# 1. 创建 RAG 实例
curl -X POST "http://localhost:8000/api/admin/rag_instances/create" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "demo_rag",
    "description": "演示 RAG 实例",
    "working_dir": "./data/demo",
    "workspace": "demo_workspace"
  }'

# 2. 插入文档
curl -X POST "http://localhost:8000/api/documents/insert" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "demo_rag",
    "content": "人工智能是计算机科学的一个重要分支。",
    "file_path": "ai_intro.txt"
  }'

# 3. 查询知识库
curl -X POST "http://localhost:8000/api/query/" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "demo_rag",
    "question": "什么是人工智能?",
    "mode": "hybrid"
  }'

# 4. 创建实体
curl -X POST "http://localhost:8000/api/graph/entities/create" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "demo_rag",
    "entity_name": "人工智能",
    "description": "计算机科学的一个分支",
    "entity_type": "CONCEPT"
  }'

# 5. 导出数据
curl -X POST "http://localhost:8000/api/graph/export" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "demo_rag",
    "output_path": "./exports/demo_graph.csv",
    "file_format": "csv"
  }'
```

### C. Python 客户端示例

```python
import requests
import json

# 基础 URL
BASE_URL = "http://localhost:8000/api"

# 1. 创建 RAG 实例
def create_rag_instance():
    url = f"{BASE_URL}/admin/rag_instances/create"
    data = {
        "rag_id": "python_demo",
        "description": "Python 示例 RAG 实例",
        "working_dir": "./data/python_demo",
        "workspace": "python_workspace"
    }
    response = requests.post(url, json=data)
    print("创建 RAG 实例:", response.json())

# 2. 插入文档
def insert_document():
    url = f"{BASE_URL}/documents/insert"
    data = {
        "rag_id": "python_demo",
        "content": "机器学习是人工智能的核心技术之一。",
        "file_path": "ml_intro.txt"
    }
    response = requests.post(url, json=data)
    print("插入文档:", response.json())

# 3. 查询知识库
def query_knowledge():
    url = f"{BASE_URL}/query/"
    data = {
        "rag_id": "python_demo",
        "question": "什么是机器学习?",
        "mode": "hybrid"
    }
    response = requests.post(url, json=data)
    result = response.json()
    print("查询结果:", result['answer'])

# 4. 创建实体
def create_entity():
    url = f"{BASE_URL}/graph/entities/create"
    data = {
        "rag_id": "python_demo",
        "entity_name": "机器学习",
        "description": "一种人工智能技术",
        "entity_type": "TECHNOLOGY"
    }
    response = requests.post(url, json=data)
    print("创建实体:", response.json())

# 执行示例
if __name__ == "__main__":
    create_rag_instance()
    insert_document()
    query_knowledge()
    create_entity()
```

### D. 常见问题

**Q1: 如何选择查询模式?**
- `naive`: 适合简单的文本检索
- `local`: 适合需要局部上下文的查询
- `global`: 适合需要全局知识的查询
- `hybrid`: 综合多种方式,推荐使用

**Q2: 文档状态有哪些?**
- `PROCESSED`: 已成功处理
- `PENDING`: 等待处理
- `FAILED`: 处理失败

**Q3: 如何处理大批量文档?**
使用批量插入接口 `/api/documents/batch_insert`,可以一次性插入多个文档。

**Q4: WebSocket 什么时候使用?**
需要实时交互或流式响应时使用 WebSocket,如实时查询反馈、进度更新等。

---

## 更新日志

### v3.0.0 (2025-01-08)
- 完整的模块化架构
- 支持多 RAG 实例管理
- 新增图谱操作接口
- 新增 WebSocket 支持
- 新增 UCD 建模功能
- 新增缓存管理功能
