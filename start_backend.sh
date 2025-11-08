#!/bin/bash

# 后端启动脚本

echo "======================================"
echo "启动 RAG 后端 API 服务"
echo "======================================"

# 进入项目目录
cd "$(dirname "$0")" || exit 1

echo ""
echo "📁 项目目录: $(pwd)"
echo ""

# 检查虚拟环境
if [ ! -z "$VIRTUAL_ENV" ]; then
    echo "✅ 虚拟环境: $VIRTUAL_ENV"
else
    echo "⚠️  未检测到虚拟环境"
    echo "   建议先激活虚拟环境: source /path/to/venv/bin/activate"
fi

echo ""

# 检查必要文件
if [ ! -d "app" ]; then
    echo "❌ 错误: app 目录不存在！"
    exit 1
fi

echo "✅ 找到 app 目录"
echo ""

# 获取服务器 IP
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || echo "无法获取")

echo "======================================"
echo "🚀 启动后端服务..."
echo "======================================"
echo ""
echo "API 地址:"
echo "  本地: http://localhost:8000"
echo "  远程: http://$SERVER_IP:8000"
echo "  文档: http://$SERVER_IP:8000/docs"
echo ""
echo "环境变量配置:"
echo "  LLM_MODEL: ${LLM_MODEL:-未设置，将使用默认值}"
echo "  LITELLM_URL: ${LITELLM_URL:-未设置，将使用默认值}"
echo ""
echo "按 Ctrl+C 停止服务"
echo "======================================"
echo ""

# 启动后端
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
