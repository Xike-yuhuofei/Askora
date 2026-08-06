#!/bin/bash
# Askora Backend Build Script
# 使用 PyInstaller 将 FastAPI 后端打包为独立二进制文件
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/../backend"
OUTPUT_DIR="$SCRIPT_DIR/../frontend/resources/backend"

echo "=== Askora Backend Build ==="
echo "Backend dir: $BACKEND_DIR"
echo "Output dir: $OUTPUT_DIR"

# 检查固定在后端虚拟环境中的 PyInstaller
PYINSTALLER="$BACKEND_DIR/.venv/bin/pyinstaller"
if [ ! -x "$PYINSTALLER" ]; then
    echo "[ERROR] PyInstaller not found in backend .venv"
    echo "Run: cd apps/backend && .venv/bin/pip install -e '.[desktop]'"
    exit 1
fi

# 创建输出目录
mkdir -p "$OUTPUT_DIR"

# 清理旧构建
rm -rf "$BACKEND_DIR/build" "$BACKEND_DIR/dist"

# 打包
cd "$BACKEND_DIR"
"$PYINSTALLER" backend.spec --clean --noconfirm

# 复制产物
if [ -f "$BACKEND_DIR/dist/askora-backend" ]; then
    cp "$BACKEND_DIR/dist/askora-backend" "$OUTPUT_DIR/askora-backend"
    chmod +x "$OUTPUT_DIR/askora-backend"
    echo "[SUCCESS] Backend binary built: $OUTPUT_DIR/askora-backend"
else
    echo "[ERROR] Build failed - no output binary found"
    exit 1
fi
