#!/usr/bin/env bash
# Canh thư mục inbox/: cứ có video mới (đã chép xong) là tự dựng. Dừng bằng Ctrl+C.
cd "$(dirname "$0")"
mkdir -p inbox/da-xong
echo "Đang canh inbox/ … (bỏ video vào, kèm file .txt cùng tên nếu có yêu cầu riêng)"
while true; do
  for f in inbox/*.{mp4,mov,m4v,MP4,MOV}; do
    [[ -f "$f" ]] || continue
    s1=$(stat -f%z "$f" 2>/dev/null || stat -c%s "$f"); sleep 5
    s2=$(stat -f%z "$f" 2>/dev/null || stat -c%s "$f")
    [[ "$s1" == "$s2" ]] || continue            # file còn đang chép
    echo "=== $(date '+%H:%M') dựng: $f"
    ./dung-phim.sh "$f" || echo "!! lỗi khi dựng $f (xem projects/*/claude.log)"
    mv "$f" inbox/da-xong/; [[ -f "${f%.*}.txt" ]] && mv "${f%.*}.txt" inbox/da-xong/
  done
  sleep 20
done
