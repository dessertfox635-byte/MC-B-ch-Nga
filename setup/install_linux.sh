#!/usr/bin/env bash
# Xưởng Phim – cài trên Ubuntu/Debian (máy chủ hoặc máy có GPU NVIDIA).
set -euo pipefail
cd "$(dirname "$0")/.."
sudo apt-get update -q && sudo apt-get install -y -q ffmpeg git python3 python3-venv libegl1 libgles2 curl
command -v node >/dev/null || { curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash - && sudo apt-get install -y nodejs; }
command -v claude >/dev/null || curl -fsSL https://claude.ai/install.sh | bash
[[ -x .venv/bin/python ]] || python3 -m venv .venv
.venv/bin/pip install -q --upgrade pip && .venv/bin/pip install -q -r requirements.txt
npm install --silent && npx --yes playwright install --with-deps chromium
chmod +x dung-phim.sh canh-thu-muc.sh
.venv/bin/python -m xuong doctor || true
