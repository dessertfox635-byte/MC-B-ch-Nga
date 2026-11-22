#!/usr/bin/env bash
# Xưởng Phim – dựng một video, không cần người can thiệp.
#   ./dung-phim.sh inbox/clip.mp4 "Reel 60 giây, chữ kinetic, nhấn 3 bí quyết"
#   ./dung-phim.sh inbox/clip.mp4 --khong-claude     # chỉ dùng máy (không biên tập bằng AI)
set -euo pipefail
cd "$(dirname "$0")"
PY=.venv/bin/python; [[ -x "$PY" ]] || PY=.venv/Scripts/python.exe   # Windows (Git Bash)
[[ -x "$PY" ]] || { echo "Chưa cài. Chạy: bash setup/install_mac.sh"; exit 1; }
VIDEO="${1:?Dùng: ./dung-phim.sh <video> [\"yêu cầu\"] [--khong-claude]}"
shift || true
BRIEF=""; NOAI=0
for a in "$@"; do [[ "$a" == "--khong-claude" ]] && NOAI=1 || BRIEF="$a"; done
TXT="${VIDEO%.*}.txt"
[[ -z "$BRIEF" && -f "$TXT" ]] && BRIEF="$(cat "$TXT")"

if [[ $NOAI == 1 ]] || ! command -v claude >/dev/null; then
  [[ $NOAI == 0 ]] && echo "Không thấy Claude Code → chạy chế độ máy tự động."
  exec "$PY" -m xuong auto "$VIDEO" --brief "$BRIEF"
fi

PROJ="$("$PY" -m xuong new "$VIDEO" --brief "$BRIEF")"
LOG="$PROJ/claude.log"
echo "▶ Dự án: $PROJ  (nhật ký: $LOG)"
claude -p "Dùng skill xuong-phim để dựng trọn dự án $PROJ từ bước 1 đến bước 5, không hỏi lại tôi.
Yêu cầu của khách: ${BRIEF:-không có – dùng mặc định trong config/brand.json}." \
  --permission-mode acceptEdits --output-format text \
  --allowedTools "Bash(.venv/bin/python -m xuong:*)" "Bash(ffmpeg:*)" "Bash(ffprobe:*)" "Bash(ls:*)" "Bash(cat:*)" \
                 "Read" "Edit" "Write" "Glob" "Grep" "Task" "Skill" \
  < /dev/null 2>&1 | tee "$LOG"
echo "✔ Xong. Thành phẩm: outbox/$(basename "$PROJ")/"
