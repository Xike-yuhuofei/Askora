#!/bin/bash
# 苏格拉底式教学 App 后端 - 启动脚本
# 使用 Python 3.11 虚拟环境运行
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 清除 TRAE 环境干扰变量
unset PYTHONHOME PYTHONPATH

# 激活虚拟环境
source .venv/bin/activate

# 显示环境信息
echo "========================================="
echo "  苏格拉底式教学 App 后端"
echo "========================================="
echo "  Python:  $(python --version)"
echo "  虚拟环境: $VIRTUAL_ENV"
echo "  端口:     8000"
echo "  API文档:  http://localhost:8000/docs"
echo "========================================="
echo ""

# 启动服务器
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
