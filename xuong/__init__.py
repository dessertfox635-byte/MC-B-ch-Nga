"""Xưởng Phim: dây chuyền dựng phim tự động do Claude chỉ đạo.

Các công đoạn đều là lệnh xác định (deterministic). Claude chỉ đưa ra quyết định biên tập
(file edit-plan.json); phần còn lại máy tự làm và tự kiểm định.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
__version__ = "1.0.0"


def _load_env():
    """Đọc cấu hình đơn giản KEY=VALUE từ .env ở gốc repo (vd. XUONG_WHISPER_MODEL=small)."""
    import os
    f = ROOT / ".env"
    if f.exists():
        for line in f.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


_load_env()
