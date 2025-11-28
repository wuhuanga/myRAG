# Embedding API 配置指南

本文档介绍如何在 myRAG 后端中使用 API embedding 替代本地模型。

## 支持的 Embedding 类型

| 类型 | 说明 | API Key 环境变量 | 推荐模型 | 维度 |
|------|------|-----------------|---------|------|
| `local` | 本地 HuggingFace 模型 (默认) | - | `sentence-transformers/all-MiniLM-L6-v2` | 384 |
| `openai` | OpenAI Embedding API | `OPENAI_API_KEY` | `text-embedding-3-small` | 1536 |
| `openai` | OpenAI Embedding API (大模型) | `OPENAI_API_KEY` | `text-embedding-3-large` | 3072 |
| `openai` | **智谱 AI (GLM)** | `EMBEDDING_API_KEY` | `embedding-3` | 2-2048 可配置 |
| `jina` | Jina AI Embedding API | `JINA_API_KEY` | `jina-embeddings-v4` | 1024-2048 |

> **注意**: 智谱 AI、硅基流动、DeepSeek 等国内服务商提供的 OpenAI 兼容 API，都使用 `EMBEDDING_TYPE=openai` + `EMBEDDING_BASE_URL`

## 配置方法

### 方法 1: 环境变量 (推荐)

在 `.env` 文件中添加配置：

#### 使用 OpenAI Embedding

```bash
# Embedding 配置
EMBEDDING_TYPE=openai
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIM=1536
EMBEDDING_MAX_TOKEN=8191
EMBEDDING_API_KEY=sk-your-openai-api-key

# 或者使用 OpenAI 官方环境变量
OPENAI_API_KEY=sk-your-openai-api-key
```

#### 使用 Jina AI Embedding

```bash
# Embedding 配置
EMBEDDING_TYPE=jina
EMBEDDING_DIM=1024
EMBEDDING_MAX_TOKEN=8192
EMBEDDING_API_KEY=jina_your-api-key

# 或者使用 Jina 官方环境变量
JINA_API_KEY=jina_your-api-key
```

#### 使用智谱 AI Embedding

```bash
# Embedding 配置
EMBEDDING_TYPE=openai
EMBEDDING_MODEL=embedding-3
EMBEDDING_DIM=1024
EMBEDDING_MAX_TOKEN=512
EMBEDDING_API_KEY=your-zhipu-api-key
EMBEDDING_BASE_URL=https://open.bigmodel.cn/api/paas/v4

# 说明：
# - EMBEDDING_TYPE 设为 openai (智谱兼容 OpenAI 格式)
# - EMBEDDING_BASE_URL 指向智谱 API 地址
# - EMBEDDING_DIM 可设置 2-2048 之间的任意值
```

#### 使用本地模型 (默认)

```bash
# Embedding 配置
EMBEDDING_TYPE=local
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIM=384
EMBEDDING_MAX_TOKEN=5000
```

### 方法 2: 在创建 RAG 实例时指定

通过 API 创建 RAG 实例时设置环境变量：

```bash
# 先设置环境变量
export EMBEDDING_TYPE=openai
export EMBEDDING_MODEL=text-embedding-3-small
export EMBEDDING_DIM=1536
export OPENAI_API_KEY=sk-your-api-key

# 然后创建 RAG 实例
curl -X POST "http://localhost:8000/api/admin/rag_instances/create" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "my_rag",
    "workspace": "default"
  }'
```

## 完整配置示例

### .env 文件示例 (OpenAI)

```bash
# ==================== Embedding 配置 ====================
EMBEDDING_TYPE=openai
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIM=1536
EMBEDDING_MAX_TOKEN=8191
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx

# ==================== LLM 配置 ====================
LITELLM_URL=http://localhost:4000
LITELLM_KEY=sk-1234
LLM_MODEL=gpt-4o-mini

# ==================== 存储配置 ====================
GRAPH_STORAGE=NebulaGraphStorage
VECTOR_STORAGE=MilvusVectorDBStorage

# NebulaGraph 配置
NEBULA_HOSTS=127.0.0.1:9669
NEBULA_USER=root
NEBULA_PASSWORD=nebula
NEBULA_WORKSPACE=default

# Milvus 配置
MILVUS_URI=http://localhost:19530
MILVUS_DB_NAME=default
```

### .env 文件示例 (Jina AI)

```bash
# ==================== Embedding 配置 ====================
EMBEDDING_TYPE=jina
EMBEDDING_DIM=1024
EMBEDDING_MAX_TOKEN=8192
JINA_API_KEY=jina_xxxxxxxxxxxxx

# ==================== LLM 配置 ====================
LITELLM_URL=http://localhost:4000
LITELLM_KEY=sk-1234
LLM_MODEL=gpt-4o-mini

# ==================== 存储配置 ====================
GRAPH_STORAGE=NebulaGraphStorage
VECTOR_STORAGE=MilvusVectorDBStorage

# NebulaGraph 配置
NEBULA_HOSTS=127.0.0.1:9669
NEBULA_USER=root
NEBULA_PASSWORD=nebula
NEBULA_WORKSPACE=default

# Milvus 配置
MILVUS_URI=http://localhost:19530
MILVUS_DB_NAME=default
```

### .env 文件示例 (智谱 AI)

```bash
# ==================== Embedding 配置 ====================
EMBEDDING_TYPE=openai
EMBEDDING_MODEL=embedding-3
EMBEDDING_DIM=1024
EMBEDDING_MAX_TOKEN=512
EMBEDDING_API_KEY=your-zhipu-api-key
EMBEDDING_BASE_URL=https://open.bigmodel.cn/api/paas/v4

# ==================== LLM 配置 ====================
LITELLM_URL=http://localhost:4000
LITELLM_KEY=sk-1234
LLM_MODEL=gpt-4o-mini

# ==================== 存储配置 ====================
GRAPH_STORAGE=NebulaGraphStorage
VECTOR_STORAGE=MilvusVectorDBStorage

# NebulaGraph 配置
NEBULA_HOSTS=127.0.0.1:9669
NEBULA_USER=root
NEBULA_PASSWORD=nebula
NEBULA_WORKSPACE=default

# Milvus 配置
MILVUS_URI=http://localhost:19530
MILVUS_DB_NAME=default
```

## API Key 获取方式

### OpenAI API Key

1. 访问 [OpenAI Platform](https://platform.openai.com/)
2. 登录后进入 API Keys 页面
3. 点击 "Create new secret key"
4. 复制生成的 key (格式: `sk-proj-...`)

### Jina AI API Key

1. 访问 [Jina AI](https://jina.ai/)
2. 注册并登录
3. 进入 API Keys 管理页面
4. 创建新的 API key (格式: `jina_...`)

### 智谱 AI API Key

1. 访问 [智谱 AI 开放平台](https://open.bigmodel.cn/)
2. 注册并登录
3. 进入 API Keys 管理页面
4. 创建新的 API key
5. 充值（新用户有免费额度）

## 重要说明

### 1. 维度配置

⚠️ **EMBEDDING_DIM 必须与模型匹配！**

| 模型 | 正确维度 |
|------|---------|
| `text-embedding-3-small` | 1536 |
| `text-embedding-3-large` | 3072 |
| `text-embedding-ada-002` | 1536 |
| `jina-embeddings-v4` | 1024 / 2048 (可配置) |

### 2. 性能对比

| 类型 | 速度 | 成本 | 质量 | 适用场景 |
|------|------|------|------|---------|
| 本地模型 | ⚡️ 快 | 💰 免费 | ⭐⭐⭐ | 小规模、离线场景 |
| OpenAI API | 🐌 较慢 | 💰💰 收费 | ⭐⭐⭐⭐⭐ | 高质量要求 |
| Jina AI | ⚡️⚡️ 很快 | 💰 免费/收费 | ⭐⭐⭐⭐ | 大规模、多语言 |

### 3. 成本估算

**OpenAI Embedding**:
- `text-embedding-3-small`: $0.02 / 1M tokens
- `text-embedding-3-large`: $0.13 / 1M tokens

**Jina AI Embedding**:
- 免费额度: 1M tokens/月
- 付费: $0.02 / 1M tokens

## 验证配置

启动服务后，检查日志输出：

```bash
# 正确的日志应该显示
INFO - Embedding 类型: openai
INFO - 使用 OpenAI Embedding API: text-embedding-3-small
INFO - Embedding 维度: 1536

# 或者
INFO - Embedding 类型: jina
INFO - 使用 Jina AI Embedding API (dimensions: 1024)
INFO - Embedding 维度: 1024
```

## 故障排查

### 问题 1: API Key 无效

```bash
# 错误信息
Error: Invalid API key

# 解决方案
1. 检查 .env 文件中的 API key 是否正确
2. 确认环境变量已加载: echo $OPENAI_API_KEY
3. 重启服务
```

### 问题 2: 维度不匹配

```bash
# 错误信息
ValueError: Expected embedding dimension 384, got 1536

# 解决方案
确保 EMBEDDING_DIM 与模型匹配:
- text-embedding-3-small → 1536
- text-embedding-3-large → 3072
- jina-embeddings-v4 → 1024 或 2048
```

### 问题 3: 速率限制

```bash
# 错误信息
RateLimitError: Rate limit exceeded

# 解决方案
1. 等待一段时间后重试
2. 升级 API 套餐
3. 使用 Jina AI (更高的免费额度)
```

## 切换 Embedding 类型注意事项

⚠️ **重要**: 切换 embedding 类型会导致**所有现有向量失效**！

如果要切换 embedding 类型，需要：

1. 删除现有的 RAG 实例
2. 清空 Milvus 数据库
3. 修改 `.env` 配置
4. 重新创建 RAG 实例
5. 重新上传所有文档

```bash
# 清空 Milvus 数据 (谨慎操作！)
# 方法 1: 通过 API 删除实例
curl -X DELETE "http://localhost:8000/api/admin/rag_instances/my_rag"

# 方法 2: 直接清空 Milvus 数据库
# 连接到 Milvus 并删除 collection
```

## 推荐配置

### 开发环境

```bash
EMBEDDING_TYPE=local
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIM=384
```

### 生产环境 (中文为主)

```bash
EMBEDDING_TYPE=jina
EMBEDDING_DIM=1024
JINA_API_KEY=your-api-key
```

### 生产环境 (高质量要求)

```bash
EMBEDDING_TYPE=openai
EMBEDDING_MODEL=text-embedding-3-large
EMBEDDING_DIM=3072
OPENAI_API_KEY=your-api-key
```
