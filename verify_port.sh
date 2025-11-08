#!/bin/bash

# 端口连通性验证脚本

SERVER_IP="47.109.43.11"

echo "======================================"
echo "验证端口连通性"
echo "======================================"
echo ""

echo "📡 测试前端端口 8080..."
if curl -s --connect-timeout 5 http://$SERVER_IP:8080/ > /dev/null 2>&1; then
    echo "✅ 端口 8080 可访问"
else
    echo "❌ 端口 8080 不可访问"
fi

echo ""
echo "📡 测试后端端口 8000..."
if curl -s --connect-timeout 5 http://$SERVER_IP:8000/api/admin/health > /dev/null 2>&1; then
    echo "✅ 端口 8000 可访问"
    echo ""
    echo "API 响应:"
    curl -s http://$SERVER_IP:8000/api/admin/health | python3 -m json.tool 2>/dev/null || curl -s http://$SERVER_IP:8000/api/admin/health
else
    echo "❌ 端口 8000 不可访问"
    echo ""
    echo "💡 请检查："
    echo "   1. 阿里云安全组是否已开放 8000 端口"
    echo "   2. 系统防火墙设置 (ufw/firewalld)"
    echo "   3. 后端服务是否正在运行"
fi

echo ""
echo "======================================"
