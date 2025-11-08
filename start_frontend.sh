#!/bin/bash

# 前端启动脚本

echo "======================================"
echo "启动 RAG 前端服务"
echo "======================================"

# 进入 frontend 目录
cd "$(dirname "$0")/frontend" || exit 1

echo ""
echo "📁 当前目录: $(pwd)"
echo ""

# 检查文件是否存在
if [ ! -f "index.html" ]; then
    echo "❌ 错误: index.html 不存在！"
    echo "   请确认在正确的目录运行此脚本"
    exit 1
fi

echo "✅ 找到 index.html"
echo "✅ 找到 app.js: $([ -f app.js ] && echo '是' || echo '否')"
echo "✅ 找到 styles.css: $([ -f styles.css ] && echo '是' || echo '否')"
echo ""

# 获取服务器 IP
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || echo "无法获取")

echo "======================================"
echo "🚀 启动 HTTP 服务器..."
echo "======================================"
echo ""
echo "访问地址:"
echo "  本地: http://localhost:8080/"
echo "  远程: http://$SERVER_IP:8080/"
echo ""
echo "按 Ctrl+C 停止服务"
echo "======================================"
echo ""

# 启动服务器
python3 -m http.server 8080
