#!/bin/bash

echo "========================================="
echo "NebulaGraph 重启脚本"
echo "========================================="

echo ""
echo "1. 停止所有 NebulaGraph 服务..."
sudo /usr/local/nebula/scripts/nebula.service stop all
sleep 3

echo ""
echo "2. 启动所有 NebulaGraph 服务..."
sudo /usr/local/nebula/scripts/nebula.service start all
sleep 10

echo ""
echo "3. 检查服务状态..."
sudo /usr/local/nebula/scripts/nebula.service status all

echo ""
echo "4. 验证 Storage 节点注册..."
echo "连接到 NebulaGraph 并执行 SHOW HOSTS:"
/usr/local/nebula/bin/nebula-console -addr 127.0.0.1 -port 9669 -u root -p nebula -e "SHOW HOSTS;"

echo ""
echo "========================================="
echo "完成！请检查上面的 SHOW HOSTS 输出"
echo "应该看到 storaged 节点状态为 ONLINE"
echo "========================================="
