# 防火墙和网络配置指南

## 问题症状

- ✅ 前端页面可以访问（8080端口）
- ❌ API无法连接（8000端口）
- ❌ curl测试超时：`curl: (28) Failed to connect to 47.109.43.11 port 8000`

**原因**：端口8000被防火墙阻止

---

## 解决方案

### 一、阿里云安全组配置（必须）

#### 方法1：通过Web控制台（推荐）

**1. 登录阿里云ECS控制台**
- 访问：https://ecs.console.aliyun.com/
- 使用您的阿里云账号登录

**2. 定位到您的实例**
- 左侧菜单：**实例与镜像** → **实例**
- 搜索或找到：`iZ2vc65np72imhjg5ds8k0Z`
- 公网IP应该显示为：`47.109.43.11`

**3. 进入安全组配置**
- 点击实例ID进入详情页
- 点击 **安全组** 标签
- 找到绑定的安全组（通常名称类似 `sg-xxxxxx`）
- 点击安全组ID进入规则管理页面

**4. 添加入方向规则**

点击 **入方向** → **手动添加** 或 **快速添加**

填写以下信息：
```
┌─────────────────────────────────────────┐
│ 授权策略:   允许                         │
│ 优先级:     1                            │
│ 协议类型:   自定义 TCP                   │
│ 端口范围:   8000/8000                    │
│ 授权对象:   0.0.0.0/0                    │
│ 描述:       RAG Backend API              │
└─────────────────────────────────────────┘
```

**说明**：
- `0.0.0.0/0` 表示允许所有IP访问
- 如需更安全，可以限制为您的IP地址（例如：`140.235.143.5/32`）

**5. 保存规则**
- 点击 **保存**
- 规则立即生效，无需重启实例

#### 方法2：使用阿里云CLI

如果您已安装 `aliyun` CLI工具：

```bash
# 1. 查看实例的安全组ID
aliyun ecs DescribeInstances \
  --InstanceIds '["iZ2vc65np72imhjg5ds8k0Z"]' \
  | grep SecurityGroupIds

# 2. 添加入方向规则（替换 <SecurityGroupId> 为实际值）
aliyun ecs AuthorizeSecurityGroup \
  --RegionId cn-hangzhou \
  --SecurityGroupId <SecurityGroupId> \
  --IpProtocol tcp \
  --PortRange 8000/8000 \
  --SourceCidrIp 0.0.0.0/0 \
  --Description "RAG Backend API"

# 3. 验证规则已添加
aliyun ecs DescribeSecurityGroupAttribute \
  --SecurityGroupId <SecurityGroupId> \
  | grep 8000
```

**注意**：将 `cn-hangzhou` 替换为您实例所在的实际区域

---

### 二、系统防火墙配置（可选）

通常云服务器的系统防火墙是关闭的，但建议检查一下：

#### Ubuntu/Debian (ufw)

```bash
# 检查防火墙状态
sudo ufw status

# 如果防火墙是启用的，允许8000端口
sudo ufw allow 8000/tcp

# 重新加载
sudo ufw reload
```

#### CentOS/RHEL (firewalld)

```bash
# 检查防火墙状态
sudo firewall-cmd --state

# 如果防火墙运行中，添加规则
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --reload

# 验证
sudo firewall-cmd --list-ports
```

#### 查看当前监听的端口

```bash
# 方法1：使用 netstat
netstat -tuln | grep 8000

# 方法2：使用 ss
ss -tuln | grep 8000

# 方法3：使用 lsof
lsof -i :8000
```

应该看到类似输出：
```
tcp        0      0 0.0.0.0:8000            0.0.0.0:*               LISTEN      12345/python
```

---

## 验证配置

### 方法1：使用验证脚本

在服务器上运行：
```bash
cd /root/workplace/lightrag/LightRAG1  # 或您的项目路径
./verify_port.sh
```

### 方法2：手动测试

**从服务器内部测试（应该成功）：**
```bash
curl http://localhost:8000/api/admin/health
```

预期输出：
```json
{
  "status": "healthy",
  "rag_instances_count": 0,
  "timestamp": "2025-11-08T..."
}
```

**从本地Windows机器测试（配置前会失败，配置后应该成功）：**

在Windows PowerShell或CMD中：
```cmd
curl http://47.109.43.11:8000/api/admin/health
```

或使用浏览器直接访问：
```
http://47.109.43.11:8000/docs
```

**预期结果**：
- ✅ 看到JSON响应或Swagger文档页面
- ❌ 如果仍然超时，说明安全组规则未生效或配置错误

### 方法3：浏览器测试

1. 打开浏览器访问前端：`http://47.109.43.11:8080/`
2. 按 `F12` 打开开发者工具
3. 查看 Console 标签

**成功的标志：**
```
🔧 自动检测到的 API 地址: http://47.109.43.11:8000
✅ API 地址已自动设置为: http://47.109.43.11:8000
正在连接 API: http://47.109.43.11:8000/api/admin/health
API 响应: {status: "healthy", rag_instances_count: 0, ...}
```

4. 页面顶部应该显示 `[已连接]`（绿色）

---

## 故障排查

### 问题1：安全组规则已添加，但仍无法访问

**检查清单**：
1. ✓ 规则的协议类型是 **TCP**（不是UDP）
2. ✓ 端口范围是 **8000/8000**（不是80/8000）
3. ✓ 授权对象是 **0.0.0.0/0** 或您的IP地址
4. ✓ 授权策略是 **允许**（不是拒绝）
5. ✓ 规则优先级足够高（数字越小优先级越高，建议设为1）
6. ✓ 检查是否有其他拒绝规则覆盖了此规则

### 问题2：后端服务未监听在正确的地址

**检查后端启动参数**：
```bash
# 错误（只监听localhost）：
uvicorn app.main:app --host localhost --port 8000

# 错误（只监听127.0.0.1）：
uvicorn app.main:app --host 127.0.0.1 --port 8000

# ✅ 正确（监听所有网络接口）：
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

验证：
```bash
netstat -tuln | grep 8000
# 应该看到 0.0.0.0:8000，而不是 127.0.0.1:8000
```

### 问题3：端口被其他程序占用

```bash
# 查找占用8000端口的进程
lsof -i :8000

# 如果不是您的uvicorn进程，杀死它
kill -9 <PID>

# 然后重新启动后端
./start_backend.sh
```

### 问题4：区域/地域不匹配

确保在正确的阿里云区域配置安全组：
- 检查ECS实例所在区域（例如：华东1-杭州、华北2-北京等）
- 在同一区域下查找安全组

---

## 安全建议

### 生产环境配置

如果这是生产环境，建议限制访问来源：

**限制特定IP访问**：
```
授权对象: YOUR_OFFICE_IP/32
```

**限制IP段访问**：
```
授权对象: 192.168.1.0/24
```

**配置HTTPS**（推荐）：
1. 使用Nginx作为反向代理
2. 配置SSL证书
3. 只在安全组开放443端口（HTTPS）
4. 后端只监听localhost:8000

### 开发环境配置

开发环境可以使用 `0.0.0.0/0`，但建议：
1. 定期检查访问日志
2. 使用强认证机制（API Key/Token）
3. 定期更新依赖包
4. 不要在代码中硬编码密钥

---

## 配置后的完整测试流程

```bash
# 1. 在服务器上确认后端运行
ps aux | grep uvicorn
# 应该看到：python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# 2. 在服务器上测试本地连接
curl http://localhost:8000/api/admin/health
# 应该返回 JSON 数据

# 3. 在服务器上测试外网IP连接
curl http://47.109.43.11:8000/api/admin/health
# 应该返回相同的 JSON 数据

# 4. 在本地Windows机器测试
curl http://47.109.43.11:8000/api/admin/health
# 应该返回相同的 JSON 数据

# 5. 在浏览器测试前端
# 访问 http://47.109.43.11:8080/
# 应该看到 [已连接] 状态
```

---

## 参考资料

- [阿里云ECS安全组配置](https://help.aliyun.com/document_detail/25471.html)
- [阿里云CLI文档](https://help.aliyun.com/document_detail/110344.html)
- [FastAPI部署指南](https://fastapi.tiangolo.com/deployment/)
- [Uvicorn配置文档](https://www.uvicorn.org/settings/)

---

## 获取帮助

如果按照上述步骤操作后仍无法连接，请收集以下信息：

```bash
# 1. 安全组规则截图
# 在阿里云控制台截取安全组入方向规则页面

# 2. 后端启动日志
./start_backend.sh
# 复制全部输出

# 3. 端口监听状态
netstat -tuln | grep 8000
lsof -i :8000

# 4. 本地测试结果
curl -v http://localhost:8000/api/admin/health

# 5. 外网测试结果
curl -v http://47.109.43.11:8000/api/admin/health

# 6. 系统防火墙状态
sudo ufw status
# 或
sudo firewall-cmd --list-all
```

将这些信息提供给技术支持团队。
