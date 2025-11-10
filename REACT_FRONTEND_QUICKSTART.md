# React 前端快速入门

## 简介

为 `backend_api.py` 创建的全功能 React 前端应用，提供完整的用户界面来管理 RAG 知识图谱系统。

## 核心功能

### ✨ 系统初始化
- 配置工作目录和模型参数
- LiteLLM 服务连接设置
- 实时健康状态监控

### 💬 知识查询
- 4种查询模式：Hybrid, Naive, Local, Global
- 可选 UCD 建模
- 实时聊天界面

### 📄 文档管理
- 文件上传（PDF, DOCX, TXT等）
- 直接文本插入
- 文档状态监控和列表查看

### 🕸️ 图谱管理
- **实体操作**：创建、编辑、删除、查询、合并
- **关系操作**：创建、编辑、删除、查询
- **数据导出**：CSV, Excel, Markdown, Text

## 快速开始

### 1. 启动后端服务

```bash
# 方式1: 直接运行
python backend_api.py

# 方式2: 使用 uvicorn
uvicorn backend_api:app --host 0.0.0.0 --port 8000 --reload
```

### 2. 安装前端依赖

```bash
cd react-frontend
npm install
```

### 3. 配置环境变量

```bash
# 复制环境变量示例
cp .env.example .env

# 编辑 .env 文件
# REACT_APP_API_URL=http://localhost:8000
```

### 4. 启动前端开发服务器

```bash
npm start
```

应用将在 http://localhost:3000 自动打开。

## 使用流程

### 首次使用

1. **初始化系统**
   - 打开应用后，进入"系统初始化"标签
   - 填写工作目录（必填）：如 `./rag_working`
   - 其他字段可选（将使用环境变量或默认值）
   - 点击"初始化系统"并等待完成

2. **上传文档**
   - 切换到"文档管理"标签
   - 选择文件或直接粘贴文本
   - 点击上传/插入

3. **开始查询**
   - 切换到"知识查询"标签
   - 输入问题并发送
   - 查看 AI 回答

### 高级功能

#### 实体管理示例
```
1. 切换到"图谱管理" > "实体管理"
2. 选择"创建"操作
3. 填写实体名称和描述
4. 提交
```

#### 关系管理示例
```
1. 切换到"图谱管理" > "关系管理"
2. 选择"创建"操作
3. 填写源实体、目标实体和关系描述
4. 提交
```

#### 数据导出示例
```
1. 切换到"图谱管理" > "数据导出"
2. 设置输出路径：如 `./exported_data`
3. 选择格式：CSV, Excel, Markdown, Text
4. 点击"导出数据"
```

## 项目结构

```
react-frontend/
├── src/
│   ├── components/          # React 组件
│   │   ├── SystemInit.js    # 系统初始化
│   │   ├── QueryPanel.js    # 查询面板
│   │   ├── DocumentManager.js  # 文档管理
│   │   └── GraphManager.js     # 图谱管理
│   ├── services/
│   │   └── api.js           # API 服务封装
│   ├── App.js               # 主应用
│   └── App.css              # 样式
├── public/
│   └── index.html           # HTML模板
└── package.json             # 项目配置
```

## API 对接

前端完整对接了 backend_api.py 的所有端点：

| 功能 | 端点 | 方法 |
|------|------|------|
| 系统初始化 | `/api/init` | POST |
| 健康检查 | `/api/health` | GET |
| 上传文档 | `/api/documents/upload` | POST |
| 插入文档 | `/api/documents/insert` | POST |
| 查询知识 | `/api/query` | POST |
| UCD建模 | `/api/query_ucd` | POST |
| 创建实体 | `/api/entities/create` | POST |
| 编辑实体 | `/api/entities/edit` | POST |
| 删除实体 | `/api/entities/delete` | POST |
| 创建关系 | `/api/relations/create` | POST |
| 数据导出 | `/api/export` | POST |
| 文档状态 | `/api/documents/status` | GET |

完整 API 文档参考：`API_DOCUMENTATION.md`

## 技术栈

- **React 18** - UI框架
- **Axios** - HTTP客户端
- **Lucide React** - 图标库
- **纯 CSS** - 自定义样式（渐变、动画、响应式）

## 设计特点

### 🎨 现代UI设计
- 紫色渐变主题
- 流畅动画效果
- 响应式布局

### 💡 用户体验
- 实时状态反馈
- 加载状态显示
- 错误提示友好
- 操作确认对话框

### 🚀 性能优化
- 组件化架构
- API 请求封装
- 条件渲染优化

## 常见问题

### Q: 无法连接到后端？
**A:**
1. 确保后端服务在运行（http://localhost:8000）
2. 检查 `.env` 配置
3. 查看浏览器控制台的网络请求

### Q: 初始化失败？
**A:**
1. 检查 Neo4j 是否启动
2. 验证 LiteLLM 配置
3. 确认工作目录可写
4. 查看后端日志

### Q: 文档上传失败？
**A:**
1. 检查文件格式是否支持
2. 确认后端已安装 textract
3. 查看文件大小限制

### Q: 查询没有结果？
**A:**
1. 确保已上传相关文档
2. 文档已处理完成（查看文档状态）
3. 尝试不同的查询模式

## 构建生产版本

```bash
# 构建
cd react-frontend
npm run build

# 部署 build/ 目录到静态文件服务器
# 或使用 serve 测试
npx serve -s build
```

## 开发建议

### 添加新功能
1. 在 `src/components/` 创建新组件
2. 在 `src/services/api.js` 添加 API 函数
3. 在 `App.js` 中集成新组件

### 修改样式
- 全局样式：`src/index.css`
- 组件样式：`src/App.css`
- 颜色主题在 CSS 变量中统一管理

### 调试技巧
- 使用 React DevTools
- 检查浏览器控制台
- 查看网络请求详情

## 后续改进

可能的增强方向：

- [ ] WebSocket 实时通信
- [ ] 知识图谱可视化
- [ ] 批量文档上传
- [ ] 查询历史记录
- [ ] 用户认证授权
- [ ] 多语言支持
- [ ] 深色模式

## 贡献

欢迎提交 Issue 和 Pull Request！

## 参考资料

- [React 官方文档](https://react.dev/)
- [Axios 文档](https://axios-http.com/)
- [Lucide Icons](https://lucide.dev/)
- 后端 API 文档：`API_DOCUMENTATION.md`
- 后端快速入门：`BACKEND_API_QUICKSTART.md`

---

**享受使用 RAG 知识图谱系统！** 🎉
