#!/usr/bin/env bash
# Xưởng Phim – cài đặt trên macOS (Apple Silicon hoặc Intel).
# Chạy:  bash setup/install_mac.sh            (từ trong thư mục repo)
#   hoặc: bash install_mac.sh                  (tự clone repo về ~/Documents/Xuong Phim)
# Tuỳ chọn: --kem-bo-mau   tải thêm Herk Edit Kit + HyperFrames (406 thẻ đồ hoạ tham khảo, ~1 GB)
#           --nhe          dùng Whisper "small" thay vì "large-v3-turbo" (máy yếu / ổ đầy)
#           --hoat-hinh    cài plugin Lemo-Opuscar (phim hoạt hình vẽ bằng code, ~100 phong cách)
set -euo pipefail
REPO_URL="https://github.com/dessertfox635-byte/MC-B-ch-Nga.git"
DEST="${XUONG_DIR:-$HOME/Documents/Xuong Phim}"
EXTRA=0; LIGHT=0; ANIM=0
for a in "$@"; do case "$a" in --kem-bo-mau) EXTRA=1;; --nhe) LIGHT=1;; --hoat-hinh) ANIM=1;; esac; done
say() { printf "\n\033[1;32m▶ %s\033[0m\n" "$*"; }
[[ "$(uname)" == "Darwin" ]] || { echo "Script này dành cho macOS. Linux: bash setup/install_linux.sh"; exit 1; }

say "1/8 Homebrew"
if ! command -v brew >/dev/null; then
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  eval "$(/opt/homebrew/bin/brew shellenv 2>/dev/null || /usr/local/bin/brew shellenv)"
fi

say "2/8 ffmpeg, Node 22+, Python 3.12, git"
brew install ffmpeg node python@3.12 git >/dev/null
PYBIN="$(brew --prefix python@3.12)/bin/python3.12"

say "3/8 Claude Code"
command -v claude >/dev/null || curl -fsSL https://claude.ai/install.sh | bash

say "4/8 Mã nguồn Xưởng Phim → $DEST"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." 2>/dev/null && pwd || true)"
if [[ -n "$HERE" && -f "$HERE/xuong/__main__.py" ]]; then
  DEST="$HERE"
elif [[ -d "$DEST/.git" ]]; then
  git -C "$DEST" pull --ff-only
else
  mkdir -p "$(dirname "$DEST")"; git clone -b "${XUONG_BRANCH:-claude/zealous-lamport-st39h9}" "$REPO_URL" "$DEST"
fi
cd "$DEST"

say "5/8 Môi trường Python (.venv) + thư viện"
[[ -x .venv/bin/python ]] || "$PYBIN" -m venv .venv
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q -r requirements.txt

say "6/8 GSAP + Chromium (Playwright)"
npm install --silent
npx --yes playwright install chromium

say "7/8 Tải trước mô hình (Whisper, VieNeu-TTS, tách người)"
MODEL=large-v3-turbo; [[ $LIGHT == 1 ]] && MODEL=small
grep -q XUONG_WHISPER_MODEL .env 2>/dev/null || echo "XUONG_WHISPER_MODEL=$MODEL" >> .env
.venv/bin/python - <<PY
from faster_whisper import WhisperModel
WhisperModel("$MODEL", device="auto", compute_type="int8"); print("  ✓ Whisper $MODEL")
from vieneu import Vieneu
Vieneu(); print("  ✓ VieNeu-TTS")
import sys; sys.path.insert(0, "."); from xuong.matte import ensure_model; ensure_model(); print("  ✓ Mô hình tách người")
PY

if [[ $EXTRA == 1 ]]; then
  say "Bộ mẫu tham khảo: Herk Edit Kit + HyperFrames"
  mkdir -p vendor
  [[ -d vendor/herk-edit-kit ]] || git clone --depth 1 https://github.com/nateherkai/herk-edit-kit vendor/herk-edit-kit
  (cd vendor/herk-edit-kit && npm ci --silent) || true
  [[ -d vendor/hyperframes ]] || git clone --depth 1 https://github.com/heygen-com/hyperframes vendor/hyperframes
fi

if [[ $ANIM == 1 ]]; then
  say "Phim hoạt hình: plugin Lemo-Opuscar cho Claude Code (lệnh cài theo README của dự án)"
  claude plugin marketplace add lemomo-ai/lemo-opuscar && claude plugin install lemo-opuscar@lemolab \
    || echo "  ! Chưa cài được plugin. Mở claude rồi gõ: /plugin marketplace add lemomo-ai/lemo-opuscar"
fi

say "8/8 Kiểm tra"
chmod +x dung-phim.sh canh-thu-muc.sh
.venv/bin/python -m xuong doctor || true
cat <<MSG

Xong! Cách dùng:
  cd "$DEST"
  ./dung-phim.sh inbox/video-cua-ban.mp4 "Reel 60 giây, chữ kinetic"
  ./canh-thu-muc.sh        # tự dựng mọi video bỏ vào inbox/
Lần đầu chạy Claude Code: gõ  claude  một lần để đăng nhập.
MSG
