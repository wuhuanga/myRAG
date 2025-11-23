# xwrag App 后端配置参数文档

本文档列出了 xwrag App 后端 API 的可配置参数，包括当前已支持的参数和建议添加的参数。

---

## 一、RAG 实例创建配置（POST /api/rag/create）

### 1.1 当前已支持的参数

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `rag_id` | str | **必填** | RAG 实例唯一标识 |
| `description` | str | None | 实例描述 |
| `working_dir` | str | "./rag_storage" | 工作目录 |
| `workspace` | str | **必填** | 工作空间（多租户隔离，必须唯一） |
| `top_k` | int | None | 查询返回的实体/关系数量 |
| `chunk_top_k` | int | None | 查询返回的文本块数量 |
| `max_entity_tokens` | int | None | 实体的最大 token 数 |
| `max_relation_tokens` | int | None | 关系的最大 token 数 |
| `max_total_tokens` | int | None | 总的最大 token 数 |
| `cosine_threshold` | float | 0.3 | 余弦相似度阈值 |
| `related_chunk_number` | int | 5 | 每个实体/关系关联的文本块数量 |
| `chunk_token_size` | int | 1200 | 分块 token 大小 |
| `chunk_overlap_token_size` | int | 100 | 分块重叠 token 大小 |
| `enable_llm_cache` | bool | True | 是否启用 LLM 缓存 |
| `enable_llm_cache_for_entity_extract` | bool | True | 是否为实体提取启用 LLM 缓存 |
| `nebula_max_connection_pool_size` | int | None | NebulaGraph 连接池大小 |

### 1.2 建议添加的参数（当前未支持）

| 参数名 | 类型 | 默认值 | 说明 | 优先级 |
|--------|------|--------|------|--------|
| `entity_extract_max_gleaning` | int | 1 | 实体提取最大尝试次数 | 高 |
| `force_llm_summary_on_merge` | int | 8 | 触发 LLM 摘要的描述片段数量 | 中 |
| `kg_chunk_pick_method` | str | "VECTOR" | 文本块选择方法（WEIGHT/VECTOR） | 高 |
| `llm_model_max_async` | int | 4 | 最大并发 LLM 调用数 | 高 |
| `embedding_func_max_async` | int | 8 | 最大并发 Embedding 调用数 | 高 |
| `embedding_batch_num` | int | 10 | Embedding 批处理大小 | 中 |
| `max_parallel_insert` | int | 2 | 最大并行插入数 | 高 |
| `max_graph_nodes` | int | 1000 | 知识图谱返回最大节点数 | 中 |
| `summary_max_tokens` | int | 1200 | 摘要最大 token 数 | 中 |
| `summary_context_size` | int | 12000 | 摘要上下文最大 token 数 | 低 |
| `summary_length_recommended` | int | 600 | 推荐摘要长度 | 低 |
| `default_llm_timeout` | int | 180 | LLM 超时时间（秒） | 中 |
| `default_embedding_timeout` | int | 30 | Embedding 超时时间（秒） | 中 |
| `min_rerank_score` | float | 0.0 | Rerank 最低分数阈值 | 中 |
| `language` | str | "English" | 文档处理语言 | 高 |
| `entity_types` | list | 见默认值 | 要提取的实体类型 | 高 |

---

## 二、查询配置（POST /api/query）

### 2.1 当前已支持的参数

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `rag_id` | str | **必填** | RAG 实例 ID |
| `question` | str | **必填** | 查询问题 |
| `mode` | str | "hybrid" | 查询模式（naive/local/global/hybrid/mix） |
| `only_need_context` | bool | True | 是否只返回上下文 |
| `top_k` | int | 20 | 检索的实体/关系数量 |
| `chunk_top_k` | int | 10 | 检索的文本块数量 |
| `max_entity_tokens` | int | 6000 | 实体最大 token 数 |
| `max_relation_tokens` | int | 8000 | 关系最大 token 数 |
| `max_total_tokens` | int | 16300 | 总最大 token 数 |

### 2.2 建议添加的参数（当前未支持）

| 参数名 | 类型 | 默认值 | 说明 | 优先级 |
|--------|------|--------|------|--------|
| `response_type` | str | "Multiple Paragraphs" | 响应格式 | 高 |
| `stream` | bool | False | 是否启用流式输出 | 高 |
| `enable_rerank` | bool | True | 是否启用 Rerank | 高 |
| `hl_keywords` | list[str] | [] | 高优先级关键词 | 中 |
| `ll_keywords` | list[str] | [] | 低优先级关键词 | 中 |
| `conversation_history` | list[dict] | [] | 对话历史 | 高 |
| `user_prompt` | str | None | 用户自定义提示词 | 中 |
| `include_references` | bool | False | 是否包含引用列表 | 中 |
| `only_need_prompt` | bool | False | 是否只返回提示词 | 低 |

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
    "top_k": 40,
    "chunk_top_k": 20,
    "chunk_token_size": 1200,
    "chunk_overlap_token_size": 100,
    "cosine_threshold": 0.3,
    "related_chunk_number": 5,
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
    "max_total_tokens": 20000
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
- 启用 `enable_rerank`（建议添加）
- 降低 `cosine_threshold`
- 增大 `related_chunk_number`

### 5.2 提高处理速度
- 增大 `llm_model_max_async`（建议添加）
- 增大 `embedding_func_max_async`（建议添加）
- 增大 `max_parallel_insert`（建议添加）
- 启用 `enable_llm_cache`

### 5.3 减少 token 消耗
- 减小 `max_total_tokens`
- 减小 `chunk_token_size`
- 减小 `max_entity_tokens` 和 `max_relation_tokens`

### 5.4 针对中文优化
- 设置 `language = "Chinese"`（建议添加）
- 自定义 `entity_types`（建议添加）
- 适当增大 `chunk_token_size`（中文信息密度较低）

---

## 六、高优先级建议添加的参数

以下参数对调优最有价值，建议优先实现：

### 6.1 实例创建参数
1. **`language`** - 指定文档处理语言，对中文支持至关重要
2. **`entity_types`** - 自定义实体类型，提高提取准确度
3. **`llm_model_max_async`** - 控制 LLM 并发，影响处理速度
4. **`embedding_func_max_async`** - 控制 Embedding 并发
5. **`max_parallel_insert`** - 控制插入并发
6. **`kg_chunk_pick_method`** - 文本块选择策略
7. **`entity_extract_max_gleaning`** - 实体提取尝试次数

### 6.2 查询参数
1. **`stream`** - 流式输出，提升用户体验
2. **`enable_rerank`** - Rerank 开关，平衡质量和速度
3. **`conversation_history`** - 对话历史，支持多轮对话
4. **`response_type`** - 响应格式控制
