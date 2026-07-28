#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -x ".venv/bin/python" ]; then
  echo "首次运行，正在创建独立 Python 环境……"
  python3 -m venv .venv
  .venv/bin/python -m pip install --upgrade pip
  .venv/bin/python -m pip install -e .
fi

.venv/bin/python -m lrcgetter.cli
echo
read -r -p "按回车键关闭窗口……"
