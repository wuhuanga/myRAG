# RAG 知识图谱系统 - React 前端

这是为 `backend_api.py` 开发的全功能 React 前端应用。

## 功能特性

### 1. 系统初始化
- 配置工作目录
- 设置 LLM 和 Embedding 模型
- 配置 LiteLLM 连接
- 实时健康检查

### 2. 知识查询
- 支持四种查询模式：
  - Hybrid (混合模式)
  - Naive (简单模式)
  - Local (本地模式)
  - Global (全局模式)
- 可选的 UCD 建模功能
- 实时聊天界面
- 历史记录显示

### 3. 文档管理
- 文件上传（支持 PDF, DOC, DOCX, TXT, RTF）
- 直接插入文本内容
- 文档状态统计（已处理/待处理/失败/总计）
- 按状态查看文档列表
- 批量操作支持

### 4. 知识图谱管理

#### 实体管理
- 创建新实体
- 编辑实体信息
- 删除实体
- 查询实体详情
- 合并多个实体

#### 关系管理
- 创建实体间关系
- 编辑关系属性
- 删除关系
- 查询关系信息

#### 数据导出
- 支持多种格式：CSV, Excel, Markdown, Text
- 可选包含向量数据
- 自定义输出路径

## 安装步骤

### 1. 安装依赖

```bash
cd react-frontend
npm install
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
REACT_APP_API_URL=http://localhost:8000
```

### 3. 启动开发服务器

```bash
npm start
```

应用将在 `http://localhost:3000` 启动。

### 4. 构建生产版本

```bash
npm run build
```

构建产物将输出到 `build/` 目录。

## 后端配置

确保后端 API 服务正在运行：

```bash
# 在项目根目录
python backend_api.py
```

或使用 uvicorn：

```bash
uvicorn backend_api:app --host 0.0.0.0 --port 8000 --reload
```

## 项目结构

```
react-frontend/
├── public/
│   └── index.html          # HTML 模板
├── src/
│   ├── components/         # React 组件
│   │   ├── SystemInit.js   # 系统初始化
│   │   ├── QueryPanel.js   # 查询面板
│   │   ├── DocumentManager.js  # 文档管理
│   │   └── GraphManager.js     # 图谱管理
│   ├── services/
│   │   └── api.js          # API 服务
│   ├── App.js              # 主应用组件
│   ├── App.css             # 样式文件
│   ├── index.js            # 应用入口
│   └── index.css           # 全局样式
├── package.json            # 项目配置
├── .env.example            # 环境变量示例
└── README.md               # 本文档
```

## 使用指南

### 首次使用

1. **系统初始化**
   - 打开应用后会自动进入"系统初始化"标签
   - 填写必填字段（工作目录）
   - 可选配置 LLM 模型、Embedding 模型等
   - 点击"初始化系统"按钮
   - 等待初始化完成（可能需要几分钟）

2. **上传文档**
   - 切换到"文档管理"标签
   - 选择"文件上传"模式
   - 点击上传区域选择文件
   - 可选填写自定义文档 ID
   - 点击"上传文档"按钮

3. **查询知识**
   - 切换到"知识查询"标签
   - 选择查询模式（推荐使用 Hybrid）
   - 输入问题
   - 按 Enter 发送（Shift+Enter 换行）
   - 查看 AI 回答

### 高级功能

#### UCD 建模
在"知识查询"标签中勾选"使用 UCD 建模"，查询结果将包含用例图建模信息。

#### 实体管理
1. 切换到"图谱管理"标签
2. 选择"实体管理"
3. 选择操作类型（创建/编辑/删除/查询/合并）
4. 填写相应信息
5. 提交操作

#### 数据导出
1. 切换到"图谱管理"标签
2. 选择"数据导出"
3. 设置输出路径和格式
4. 点击"导出数据"

## API 端点

前端调用的主要 API 端点：

- `POST /api/init` - 初始化系统
- `GET /api/health` - 健康检查
- `POST /api/documents/upload` - 上传文档
- `POST /api/documents/insert` - 插入文档内容
- `GET /api/documents/status` - 获取文档状态
- `POST /api/query` - 查询知识库
- `POST /api/query_ucd` - UCD 建模查询
- `POST /api/entities/*` - 实体管理
- `POST /api/relations/*` - 关系管理
- `POST /api/export` - 导出数据

完整 API 文档请参考后端 `API_DOCUMENTATION.md`。

## 技术栈

- **React 18** - 前端框架
- **Axios** - HTTP 客户端
- **Lucide React** - 图标库
- **CSS3** - 样式（渐变、动画、响应式）

## 浏览器支持

- Chrome（推荐）
- Firefox
- Safari
- Edge

## 故障排除

### 无法连接到后端

1. 确保后端服务正在运行
2. 检查 `.env` 文件中的 API URL 配置
3. 检查浏览器控制台是否有 CORS 错误

### 初始化失败

1. 检查工作目录是否可写
2. 确认 Neo4j 数据库已启动
3. 验证 LiteLLM 服务配置正确
4. 查看后端日志了解详细错误

### 文档上传失败

1. 检查文件格式是否支持
2. 确认文件大小未超过限制
3. 检查后端是否安装了 textract

## 开发说明

### 添加新组件

在 `src/components/` 目录创建新组件：

```javascript
import React from 'react';

function NewComponent() {
  return (
    <div className="panel">
      {/* 组件内容 */}
    </div>
  );
}

export default NewComponent;
```

### 添加新 API

在 `src/services/api.js` 添加新的 API 函数：

```javascript
export const newApiFunction = async (params) => {
  const response = await api.post('/api/new-endpoint', params);
  return response.data;
};
```

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

与主项目相同

## 联系方式

如有问题，请查看主项目文档或提交 Issue。
