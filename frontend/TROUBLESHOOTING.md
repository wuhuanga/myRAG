# 前端故障排除指南

## 问题：前端一直显示"正在加载..."

### 快速诊断清单

#### ✅ 第一步：确认后端运行

```bash
# 在服务器上执行
curl http://localhost:8000/api/admin/health

# 应该看到：
# {"status":"healthy","rag_instances_count":0,...}

# 如果失败，启动后端：
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### ✅ 第二步：检查 API 地址配置

**问题症状**：远程服务器上运行后端，但前端无法连接

**原因**：前端默认使用 `http://localhost:8000`，但 localhost 指向浏览器所在机器，而不是服务器！

**解决方法**：

1. 打开前端页面
2. 在页面顶部找到 API 地址输入框：`[未连接] [http://localhost:8000] [测试连接]`
3. 修改为服务器的实际地址：
   - 公网 IP：`http://YOUR_SERVER_IP:8000`
   - 内网 IP：`http://192.168.x.x:8000`
   - 域名：`http://your-domain.com:8000`
4. 点击"测试连接"按钮

#### ✅ 第三步：检查浏览器控制台

按 **F12** 打开开发者工具，查看：

**Console 标签**：
```javascript
// 应该看到：
正在连接 API: http://YOUR_IP:8000/api/admin/health
API 响应: {status: "healthy", ...}

// 如果看到错误：
Failed to fetch
// → 后端未运行或地址错误

CORS error
// → 跨域配置问题（见下文）

404 Not Found
// → 端点路径错误或后端版本不匹配
```

**Network 标签**：
- 查看 `/api/admin/health` 请求
- 状态码：
  - `200 OK` → 成功
  - `404 Not Found` → 路由不匹配
  - `(failed) net::ERR_CONNECTION_REFUSED` → 后端未运行
  - `(failed) net::ERR_CONNECTION_TIMED_OUT` → 防火墙阻止

### 常见问题及解决方案

#### 问题1：Failed to fetch / ERR_CONNECTION_REFUSED

**原因**：
- 后端服务未启动
- API 地址错误
- 端口被占用

**解决**：
```bash
# 检查后端是否运行
ps aux | grep uvicorn

# 检查端口是否被占用
lsof -i :8000
# 或
netstat -tuln | grep 8000

# 重启后端
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 问题2：CORS 错误

**错误信息**：
```
Access to fetch at 'http://xxx' from origin 'http://yyy' has been blocked by CORS policy
```

**原因**：浏览器阻止跨域请求

**解决**：
后端已经配置了 CORS（允许所有来源）。如果仍有问题，检查：

1. 后端是否真的在运行最新代码
2. 是否使用了代理或负载均衡器

#### 问题3：404 Not Found on /api/admin/health

**原因**：使用了旧版本的后端

**诊断**：
```bash
# 测试旧端点
curl http://localhost:8000/api/health

# 如果返回数据，说明运行的是旧版本
```

**解决**：
```bash
# 停止旧服务（Ctrl+C）

# 拉取最新代码
git pull origin your-branch

# 运行新版本
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 或向后兼容入口（会自动加载新架构）
python -m uvicorn backend_api:app --host 0.0.0.0 --port 8000 --reload
```

#### 问题4：防火墙阻止

**症状**：本地访问正常，远程访问失败

**检查防火墙**：
```bash
# Ubuntu/Debian
sudo ufw status
sudo ufw allow 8000/tcp

# CentOS/RHEL
sudo firewall-cmd --list-ports
sudo firewall-cmd --add-port=8000/tcp --permanent
sudo firewall-cmd --reload

# 阿里云/腾讯云
# 需要在控制台的安全组规则中开放 8000 端口
```

#### 问题5：一直loading，没有错误提示

**更新后的前端**会显示详细错误。如果仍看不到错误：

**临时调试**（在浏览器控制台执行）：
```javascript
// 强制重新检查
checkApiStatus();

// 查看当前 API URL
console.log('API URL:', getApiUrl());

// 手动测试连接
fetch('http://YOUR_IP:8000/api/admin/health')
  .then(r => r.json())
  .then(d => console.log('Success:', d))
  .catch(e => console.error('Error:', e));
```

### 完整测试流程

#### 1. 本地测试（同一台机器）

```bash
# 终端1：启动后端
cd /path/to/myRAG
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 终端2：启动前端
cd /path/to/myRAG/frontend
python3 -m http.server 8080

# 浏览器访问
http://localhost:8080

# 前端 API 地址保持默认
http://localhost:8000
```

#### 2. 远程访问（客户端 → 服务器）

```bash
# 服务器上：启动后端
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 服务器上：启动前端（可选，也可以在本地）
python3 -m http.server 8080

# 本地浏览器访问
http://SERVER_IP:8080

# 修改前端 API 地址为
http://SERVER_IP:8000
```

### 验证成功的标志

✅ **成功连接后应该看到：**

1. 页面顶部状态从 `[未连接]` 变为 `[已连接]`
2. 绿色通知：`✅ API 连接成功`
3. 页面不再loading，显示完整界面
4. 控制台输出：
   ```
   正在连接 API: http://YOUR_IP:8000/api/admin/health
   API 响应: {status: "healthy", rag_instances_count: 0, ...}
   ```

### 仍然无法解决？

收集以下信息：

1. **后端日志**：
   ```bash
   # 查看后端启动输出
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **浏览器控制台输出**（截图或复制文本）

3. **Network 标签中的请求详情**

4. **环境信息**：
   ```bash
   # Python 版本
   python --version

   # 已安装的包
   pip list | grep -E "(fastapi|uvicorn|pydantic)"

   # 系统信息
   uname -a
   ```

5. **API 直接测试**：
   ```bash
   # 在服务器上
   curl -v http://localhost:8000/api/admin/health

   # 从客户端
   curl -v http://SERVER_IP:8000/api/admin/health
   ```

将这些信息提供给技术支持。
