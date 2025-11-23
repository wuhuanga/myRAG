# xwrag App 后端配置参数文档

本文档列出了 xwrag App 后端 API 的可配置参数。

---

## 一、RAG 实例创建配置（POST /api/rag/create）

### 1.1 基础参数

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `rag_id` | str | **必填** | RAG 实例唯一标识 |
| `description` | str | None | 实例描述 |
| `working_dir` | str | "./rag_storage" | 工作目录 |
| `workspace` | str | **必填** | 工作空间（多租户隔离，必须唯一） |

### 1.2 查询参数

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `top_k` | int | None | 查询返回的实体/关系数量 |
| `chunk_top_k` | int | None | 查询返回的文本块数量 |
| `max_entity_tokens` | int | None | 实体的最大 token 数 |
| `max_relation_tokens` | int | None | 关系的最大 token 数 |
| `max_total_tokens` | int | None | 总的最大 token 数 |
| `cosine_threshold` | float | 0.3 | 余弦相似度阈值 |
| `related_chunk_number` | int | 5 | 每个实体/关系关联的文本块数量 |
| `kg_chunk_pick_method` | str | "VECTOR" | 文本块选择方法（WEIGHT/VECTOR） |
| `max_graph_nodes` | int | 1000 | 知识图谱返回最大节点数 |

### 1.3 文本分块参数

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `chunk_token_size` | int | 1200 | 分块 token 大小 |
| `chunk_overlap_token_size` | int | 100 | 分块重叠 token 大小 |

### 1.4 实体提取参数

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `language` | str | "English" | 文档处理语言 |
| `entity_types` | list[str] | None | 要提取的实体类型（默认使用内置类型） |
| `entity_extract_max_gleaning` | int | 1 | 实体提取最大尝试次数 |

### 1.5 并发与性能参数

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `llm_model_max_async` | int | 4 | 最大并发 LLM 调用数 |
| `embedding_func_max_async` | int | 8 | 最大并发 Embedding 调用数 |
| `max_parallel_insert` | int | 2 | 最大并行插入数 |

### 1.6 缓存参数

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `enable_llm_cache` | bool | True | 是否启用 LLM 缓存 |
| `enable_llm_cache_for_entity_extract` | bool | True | 是否为实体提取启用 LLM 缓存 |

### 1.7 数据库连接参数

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `nebula_max_connection_pool_size` | int | None | NebulaGraph 连接池大小 |

---

## 二、查询配置（POST /api/query）

### 2.1 基础参数

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `rag_id` | str | **必填** | RAG 实例 ID |
| `question` | str | **必填** | 查询问题 |
| `mode` | str | "hybrid" | 查询模式（naive/local/global/hybrid/mix） |

### 2.2 检索参数

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `top_k` | int | 20 | 检索的实体/关系数量 |
| `chunk_top_k` | int | 10 | 检索的文本块数量 |
| `max_entity_tokens` | int | 6000 | 实体最大 token 数 |
| `max_relation_tokens` | int | 8000 | 关系最大 token 数 |
| `max_total_tokens` | int | 16300 | 总最大 token 数 |

### 2.3 输出控制参数

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `only_need_context` | bool | True | 是否只返回上下文 |
| `response_type` | str | "Multiple Paragraphs" | 响应格式 |
| `stream` | bool | False | 是否启用流式输出 |
| `include_references` | bool | False | 是否包含引用列表 |

### 2.4 检索优化参数

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `enable_rerank` | bool | True | 是否启用 Rerank |
| `hl_keywords` | list[str] | None | 高优先级关键词 |
| `ll_keywords` | list[str] | None | 低优先级关键词 |

### 2.5 对话与提示参数

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `conversation_history` | list[dict] | None | 对话历史，格式：`[{"role": "user/assistant", "content": "..."}]` |
| `user_prompt` | str | None | 用户自定义提示词 |

---

## 三、API 使用示例

### 3.1 创建 RAG 实例

```bash
curl -X POST http://localhost:8000/api/rag/create \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "my_rag",
    "workspace": "my_workspace",
    "working_dir": "./rag_storage",
    "language": "Chinese",
    "entity_types": ["人物", "组织", "地点", "事件", "概念"],
    "top_k": 40,
    "chunk_top_k": 20,
    "chunk_token_size": 1200,
    "llm_model_max_async": 8,
    "embedding_func_max_async": 16,
    "max_parallel_insert": 4,
    "enable_llm_cache": true
  }'
```

### 3.2 查询

```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "my_rag",
    "question": "文档的主要内容是什么？",
    "mode": "hybrid",
    "only_need_context": false,
    "top_k": 30,
    "chunk_top_k": 15,
    "max_total_tokens": 20000,
    "enable_rerank": true,
    "response_type": "Multiple Paragraphs",
    "hl_keywords": ["关键词1", "关键词2"]
  }'
```

### 3.3 多轮对话查询

```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "my_rag",
    "question": "能详细说明一下吗？",
    "mode": "hybrid",
    "only_need_context": false,
    "conversation_history": [
      {"role": "user", "content": "文档的主要内容是什么？"},
      {"role": "assistant", "content": "文档主要介绍了..."}
    ]
  }'
```

---

## 四、环境变量配置

以下参数通过环境变量配置（不能通过 API 设置）：

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| `LLM_MODEL` | gpt-4 | LLM 模型名称 |
| `EMBEDDING_MODEL` | sentence-transformers/all-MiniLM-L6-v2 | Embedding 模型路径 |
| `EMBEDDING_DIM` | 384 | Embedding 维度 |
| `EMBEDDING_MAX_TOKEN` | 5000 | Embedding 最大 token 数 |
| `LITELLM_URL` | http://localhost:4000 | LiteLLM 服务地址 |
| `LITELLM_KEY` | sk-1234 | LiteLLM API 密钥 |
| `GRAPH_STORAGE` | NebulaGraphStorage | 图存储类型 |
| `VECTOR_STORAGE` | MilvusVectorDBStorage | 向量存储类型 |

---

## 五、调优建议

### 5.1 提高检索质量
- 增大 `top_k` 和 `chunk_top_k`
- 启用 `enable_rerank`
- 降低 `cosine_threshold`
- 增大 `related_chunk_number`
- 使用 `hl_keywords` 指定重要关键词

### 5.2 提高处理速度
- 增大 `llm_model_max_async`（如 8 或 16）
- 增大 `embedding_func_max_async`（如 16 或 32）
- 增大 `max_parallel_insert`（如 4 或 8）
- 启用 `enable_llm_cache`

### 5.3 减少 token 消耗
- 减小 `max_total_tokens`
- 减小 `chunk_token_size`
- 减小 `max_entity_tokens` 和 `max_relation_tokens`

### 5.4 针对中文优化
- 设置 `language = "Chinese"`
- 自定义 `entity_types` 为中文实体类型，如：
  ```json
  ["人物", "组织", "地点", "事件", "概念", "方法", "数据"]
  ```
- 适当增大 `chunk_token_size`（中文信息密度较低，建议 1500-2000）

### 5.5 多轮对话
- 使用 `conversation_history` 传递历史对话
- 格式：`[{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]`
