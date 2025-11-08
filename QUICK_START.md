# 快速启动指南

## 🚀 一键启动（推荐）

### 启动后端

```bash
cd /root/workplace/lightrag/LightRAG1
./start_backend.sh
```

### 启动前端（新终端）

```bash
cd /root/workplace/lightrag/LightRAG1
./start_frontend.sh
```

## 🔒 **重要：远程访问前必须配置防火墙**

如果您需要**从其他电脑**访问服务器上的服务，必须先开放端口：

### ⚠️ 阿里云/腾讯云用户（必读）

**症状**：前端可以访问（8080），但API一直loading或超时
**原因**：云服务器默认关闭大部分端口，需要在安全组中开放

**快速解决**：
1. 登录云服务商控制台（阿里云/腾讯云/AWS等）
2. 找到您的ECS/云服务器实例
3. 进入 **安全组配置**
4. 添加**入方向规则**：
   ```
   端口: 8000/8000  (后端API)
   端口: 8080/8080  (前端界面)
   协议: TCP
   来源: 0.0.0.0/0  (或您的IP地址)
   ```

**详细步骤**：参见 `FIREWALL_SETUP.md`

**验证是否成功**：
```bash
# 在本地电脑（非服务器）运行
curl http://YOUR_SERVER_IP:8000/api/admin/health

# 成功会返回：
{"status":"healthy",...}

# 失败会显示：
curl: (28) Failed to connect... timeout
```

---

## 📋 手动启动

### 方法1：启动后端

```bash
# 1. 进入项目目录
cd /root/workplace/lightrag/LightRAG1

# 2. 激活虚拟环境（如果有）
source /path/to/lightrag/bin/activate

# 3. 启动后端
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**验证后端运行**：
```bash
# 在另一个终端测试
curl http://localhost:8000/api/admin/health

# 应该返回：
# {"status":"healthy","rag_instances_count":0,...}
```

### 方法2：启动前端

```bash
# 1. 进入 frontend 目录（重要！）
cd /root/workplace/lightrag/LightRAG1/frontend

# 2. 确认文件存在
ls index.html
# 应该看到：index.html

# 3. 启动 HTTP 服务器
python3 -m http.server 8080
```

**验证前端运行**：
```bash
# 应该看到：
Serving HTTP on 0.0.0.0 port 8080 (http://0.0.0.0:8080/) ...
```

## 🌐 访问方式

### 获取服务器 IP

```bash
# 方法1
curl ifconfig.me

# 方法2
curl icanhazip.com

# 方法3（如果在阿里云）
# 在阿里云控制台查看公网 IP
```

### 浏览器访问

```
前端: http://YOUR_SERVER_IP:8080/
后端文档: http://YOUR_SERVER_IP:8080/docs
```

**重要**：
- ✅ 使用 `http://YOUR_SERVER_IP:8080/`（末尾有斜杠）
- ❌ 不要用 `http://localhost:8080`（除非在服务器上用浏览器）

## ❌ 常见错误及解决

### 错误1：404 File not found

**原因**：在错误的目录启动了 http.server

**解决**：
```bash
# 确保在 frontend 目录内！
cd /root/workplace/lightrag/LightRAG1/frontend
python3 -m http.server 8080
```

### 错误2：前端一直 loading

**原因**：后端未运行或地址不对

**解决**：
1. 检查后端是否运行：`curl http://localhost:8000/api/admin/health`
2. 检查浏览器控制台（F12）查看错误
3. 前端会自动检测 IP，无需手动修改（最新版本）

### 错误3：端口已被占用

**错误信息**：`OSError: [Errno 98] Address already in use`

**解决**：
```bash
# 查找占用端口的进程
lsof -i :8000
# 或
lsof -i :8080

# 杀死进程
kill -9 PID
```

### 错误4：无法远程访问

**可能原因**：防火墙阻止

**解决**：
```bash
# Ubuntu/Debian
sudo ufw allow 8000/tcp
sudo ufw allow 8080/tcp

# 阿里云/腾讯云
# 在控制台的安全组中开放 8000 和 8080 端口
```

## 🔍 调试技巧

### 查看后端日志

后端日志会直接显示在启动终端中，包括：
- 请求记录
- 错误信息
- 警告提示

### 查看前端日志

1. 浏览器按 **F12** 打开开发者工具
2. 查看 **Console** 标签：
   ```javascript
   🔧 自动检测到的 API 地址: http://YOUR_IP:8000
   ✅ API 地址已自动设置为: http://YOUR_IP:8000
   正在连接 API: http://YOUR_IP:8000/api/admin/health
   API 响应: {status: "healthy", ...}
   ```
3. 查看 **Network** 标签：检查 API 请求状态

### 手动测试 API

```bash
# 健康检查
curl http://YOUR_IP:8000/api/admin/health

# 创建实例
curl -X POST "http://YOUR_IP:8000/api/admin/rag_instances/create" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "test",
    "workspace": "test_workspace"
  }'

# 列出实例
curl http://YOUR_IP:8000/api/admin/rag_instances/list
```

## ✅ 验证成功

**前端成功加载的标志**：
1. 页面显示完整界面（不是 loading 或 404）
2. 页面顶部显示 `[已连接]`（绿色）
3. 控制台显示成功连接的日志
4. 可以看到"创建 RAG 实例"表单

**后端正常运行的标志**：
```bash
curl http://localhost:8000/api/admin/health
# 返回：
{"status":"healthy","rag_instances_count":N,...}
```

## 📚 更多帮助

- **防火墙配置**：`FIREWALL_SETUP.md`（远程访问必读）
- 完整 API 文档：`app/README.md`
- 迁移指南：`MIGRATION_GUIDE.md`
- 前端故障排除：`frontend/TROUBLESHOOTING.md`
