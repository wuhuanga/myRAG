# RAG 知识图谱管理系统 - 前端

一个简洁、易用的 Web 界面，用于管理和操作 RAG（检索增强生成）知识图谱系统。

## 📸 功能概览

- ✅ **实例管理**：创建、查看、删除 RAG 实例
- ✅ **文档操作**：上传文档、插入文本、查看状态
- ✅ **查询功能**：支持多种查询模式（Hybrid/Local/Global/Naive）
- ✅ **图谱操作**：实体和关系的创建、查询
- ✅ **数据导出**：支持 CSV、JSON、Markdown 格式

## 🚀 快速开始

### 1. 启动后端 API

```bash
# 方式 1: 使用 uvicorn（开发环境）
cd /home/user/myRAG
uvicorn app.main:app --reload --port 8000

# 方式 2: 使用 gunicorn（生产环境）
gunicorn app.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000
```

### 2. 启动前端

#### 方法 A：使用 Python 内置服务器（推荐）

```bash
cd /home/user/myRAG/frontend
python3 -m http.server 8080
```

然后在浏览器中访问：`http://localhost:8080`

#### 方法 B：使用 Node.js 的 http-server

```bash
# 安装 http-server（首次）
npm install -g http-server

# 启动服务器
cd /home/user/myRAG/frontend
http-server -p 8080
```

#### 方法 C：直接打开 HTML 文件

```bash
# 在浏览器中直接打开
open index.html  # macOS
xdg-open index.html  # Linux
start index.html  # Windows
```

**注意**：直接打开 HTML 文件可能因为 CORS 策略导致 API 请求失败，建议使用方法 A 或 B。

### 3. 配置 API 地址

1. 打开浏览器访问前端页面
2. 在顶部找到 API 地址输入框
3. 确认地址为：`http://localhost:8000`
4. 点击"测试连接"按钮
5. 看到"已连接"绿色标识即表示成功

## 📖 使用指南

### 一、创建 RAG 实例

1. 点击 **📦 实例管理** 标签
2. 填写以下信息：
   - **实例 ID**（必填）：例如 `my-rag-001`
   - **Workspace**（必填）：例如 `project_alpha`
     - ⚠️ **重要**：必须唯一，避免多实例数据冲突
   - **工作目录**：默认 `./rag_storage`
   - **LLM 模型**：例如 `gpt-4o-mini`
   - **Embedding 模型**：例如 `sentence-transformers/all-MiniLM-L6-v2`
   - **向量存储**：选择存储后端（Faiss/Milvus/NanoVectorDB）
   - **图存储**：选择存储后端（Neo4j/NetworkX）
3. 点击"创建实例"按钮
4. 等待创建完成（首次创建需要加载模型，可能需要几分钟）

**创建成功后**，您会在实例列表中看到新创建的实例。

### 二、上传文档

1. 切换到 **📄 文档操作** 标签
2. 在"选择 RAG 实例"下拉框中选择您创建的实例
3. 选择上传方式：

#### 方式 A：上传文件

- 点击"选择文件"，支持的格式：
  - `.txt` - 纯文本
  - `.pdf` - PDF 文档
  - `.docx` - Word 文档
  - `.md` - Markdown 文档
- （可选）输入自定义文档 ID
- 点击"上传并索引"

#### 方式 B：直接输入文本

- 在"文本内容"框中输入或粘贴文本
- （可选）输入文档 ID 和文件路径
- 点击"插入文本"

**索引过程说明**：
- 文档会被自动分块（chunk）
- 提取实体和关系，构建知识图谱
- 生成向量嵌入，存储到向量数据库
- 整个过程可能需要几秒到几分钟（取决于文档大小）

### 三、查询知识图谱

1. 切换到 **🔍 查询** 标签
2. 选择 RAG 实例
3. 输入查询问题，例如：
   - "什么是人工智能？"
   - "深度学习和机器学习的关系是什么？"
   - "介绍一下神经网络"
4. 选择查询模式：
   - **Hybrid（推荐）**：结合本地和全局信息
   - **Local**：基于局部子图
   - **Global**：基于全局社区
   - **Naive**：简单检索
5. 配置参数：
   - **只需要上下文**：勾选后不调用 LLM，仅返回检索到的上下文
   - **Top K**：返回的实体/关系数量（默认 20）
   - **Chunk Top K**：返回的文本块数量（默认 10）
6. 点击"查询"按钮
7. 查看结果面板中的返回内容

### 四、图谱操作

#### 实体操作

1. 切换到 **🕸️ 图谱操作** 标签
2. 点击"实体操作"子标签
3. **创建实体**：
   - 输入实体名称（必填）
   - 输入实体类型，例如：`人物`、`地点`、`概念`
   - 输入描述
   - 点击"创建实体"
4. **查询实体**：
   - 输入实体名称
   - 点击"查询"
   - 查看实体详细信息

#### 关系操作

1. 点击"关系操作"子标签
2. **创建关系**：
   - 输入源实体名称
   - 输入目标实体名称
   - 输入关系描述
   - 点击"创建关系"
3. **查询关系**：
   - 输入源实体和目标实体
   - 点击"查询"
   - 查看关系详细信息

#### 数据导出

1. 点击"数据导出"子标签
2. 选择导出格式：
   - **CSV**：适合在 Excel 中查看
   - **JSON**：适合程序处理
   - **Markdown**：适合文档阅读
3. 点击对应的导出按钮
4. 浏览器会自动下载文件

### 五、查看文档状态

1. 在 **📄 文档操作** 标签中
2. 点击"查看状态"按钮
3. 查看当前实例的统计信息：
   - 总文档数
   - 总实体数
   - 总关系数
   - 总文本块数

## 🎨 界面说明

### 顶部导航

- **实例管理**：创建、查看、删除 RAG 实例
- **文档操作**：上传文档、插入文本
- **查询**：知识图谱查询
- **图谱操作**：实体、关系管理和数据导出

### 状态指示

- **绿色"已连接"**：API 连接正常
- **红色"连接失败"**：无法连接到后端 API
- **加载动画**：正在处理请求

### 通知提示

- **绿色通知**：操作成功
- **红色通知**：操作失败
- **橙色通知**：警告信息

## ⚙️ 配置说明

### API 地址配置

默认 API 地址：`http://localhost:8000`

如果后端部署在其他地址，可以在顶部输入框中修改：
- 本地开发：`http://localhost:8000`
- 局域网：`http://192.168.1.100:8000`
- 远程服务器：`http://your-server.com:8000`

### CORS 配置

如果遇到跨域问题，需要在后端 `app/main.py` 中配置：

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],  # 前端地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 🐛 常见问题

### 1. 无法连接到 API

**问题**：点击"测试连接"显示"连接失败"

**解决方法**：
- 确认后端服务已启动：`curl http://localhost:8000/api/admin/health`
- 检查 API 地址是否正确
- 检查防火墙设置
- 查看浏览器控制台的错误信息

### 2. 创建实例失败

**问题**：提示"workspace 不能为空"或"workspace 已被使用"

**解决方法**：
- 确保填写了 workspace 字段
- 每个实例的 workspace 必须唯一
- 参考：[MULTI_INSTANCE_ANALYSIS.md](../MULTI_INSTANCE_ANALYSIS.md)

### 3. 上传文档失败

**问题**：文件上传后报错

**解决方法**：
- 检查文件格式是否支持（.txt, .pdf, .docx, .md）
- 确认文件大小不要太大（建议 < 10MB）
- 查看后端日志了解详细错误

### 4. 查询没有结果

**问题**：查询后返回空结果

**解决方法**：
- 确认已上传并索引了文档
- 使用"查看状态"检查是否有实体和关系
- 尝试更改查询模式（Hybrid/Local/Global）
- 增加 Top K 参数值

### 5. 页面样式异常

**问题**：页面显示混乱，没有样式

**解决方法**：
- 确认 `styles.css` 文件存在
- 使用 HTTP 服务器而不是直接打开 HTML 文件
- 清除浏览器缓存后刷新

## 📁 文件结构

```
frontend/
├── index.html          # 主页面
├── styles.css          # 样式表
├── app.js              # JavaScript 逻辑
└── README.md           # 本文档
```

## 🔧 开发说明

### 技术栈

- **HTML5**：页面结构
- **CSS3**：样式和布局
- **Vanilla JavaScript**：交互逻辑
- **Fetch API**：HTTP 请求

### 代码结构

```javascript
// app.js 主要模块

// 1. 全局状态
let API_BASE_URL = 'http://localhost:8000/api';
let currentInstances = [];

// 2. 工具函数
function showLoading() { ... }
function showNotification() { ... }
function apiRequest() { ... }

// 3. Tab 切换
function showTab() { ... }
function showSubTab() { ... }

// 4. API 调用函数
async function loadInstances() { ... }
async function uploadDocument() { ... }
async function performQuery() { ... }

// 5. 表单处理
document.getElementById('xxx').addEventListener('submit', ...)
```

### 自定义扩展

如果需要添加新功能：

1. **添加新 Tab**：
   - 在 `index.html` 中添加 tab 按钮和内容区域
   - 在 `app.js` 中添加对应的处理函数

2. **添加新 API 调用**：
   - 使用 `apiRequest()` 函数统一处理
   - 添加错误处理和加载提示

3. **修改样式**：
   - 编辑 `styles.css`
   - 使用 CSS 变量便于主题定制

## 🌐 浏览器兼容性

- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

**注意**：不支持 IE 浏览器

## 📝 更新日志

### v1.0.0 (2025-11-07)

- ✨ 首次发布
- ✅ 实例管理功能
- ✅ 文档上传和文本插入
- ✅ 多模式查询
- ✅ 实体和关系管理
- ✅ 数据导出功能

## 🤝 反馈与支持

如遇到问题或有改进建议，请：
1. 查看 [API_DOCUMENTATION.md](../API_DOCUMENTATION.md) 了解 API 详情
2. 参考 [BACKEND_API_QUICKSTART.md](../BACKEND_API_QUICKSTART.md) 了解后端配置
3. 查看浏览器控制台的错误信息
4. 检查后端日志

## 📚 相关文档

- [API 接口文档](../API_DOCUMENTATION.md)
- [后端快速入门](../BACKEND_API_QUICKSTART.md)
- [多实例分析](../MULTI_INSTANCE_ANALYSIS.md)
- [并发指南](../CONCURRENCY_GUIDE.md)
- [锁机制分析](../LOCK_MECHANISM_ANALYSIS.md)

---

**Happy RAGing! 🚀**
