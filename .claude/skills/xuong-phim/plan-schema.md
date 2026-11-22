# Lược đồ `edit-plan.json`

Mọi chỉ số từ (`*_word`, `from_word`, `to_word`, `hero`) là chỉ số `[i]` trong `hints.md` / `transcript.json`
— tức trên bản ghi GỐC, trước khi cắt. Máy tự dời mọi thứ theo các đoạn đã cắt.

```jsonc
{
  "title": "3 bí quyết dẫn sự kiện",
  "formats": ["9:16", "16:9"],          // 9:16 | 16:9 | 1:1 | 4:5
  "max_duration": 60,                    // giây, tuỳ chọn – kiểm định báo lỗi nếu vượt
  "hook": {"from_word": 9, "to_word": 25},          // đoạn đưa lên đầu (tuỳ chọn)
  "cuts": [{"from_word": 26, "to_word": 27, "reason": "nói lặp"}],
  "caption_fixes": {"41": "lưu", "46": "ánh"},      // sửa chính tả từng từ
  "captions": {
    "style": "kinetic",                  // kinetic | pop | box | clean
    "hero": [[13, 14], [16, 17]],        // kinetic: các từ khoá đỏ (khoảng chỉ số từ)
    "enabled": true
  },
  "overlays": [
    {"type": "lower-third", "at_word": 0, "until_word": 8, "text": "MC Bích Nga", "subtext": "Dẫn chương trình sự kiện"},
    {"type": "checklist", "at_word": 28, "until_word": 61, "title": "Bí quyết",
     "items": [{"text": "Kịch bản kỹ", "at_word": 31}, {"text": "Giao lưu", "at_word": 39}]},
    {"type": "keyword-pop", "at_word": 47, "duration": 1.4, "text": "ánh mắt"},
    {"type": "counter", "at_word": 15, "from": 0, "to": 500, "suffix": "+", "label": "sự kiện"},
    {"type": "comment-drop", "at_word": 5, "author": "Khách hàng", "text": "MC dẫn quá cuốn!"},
    {"type": "cta", "start": -3.0, "end": -0.2, "text": "Theo dõi Bích Nga"}   // số âm = tính từ cuối
  ],
  "zooms": [                              // chuyển động máy giả lập (xem sach-hieu-ung.md mục 2)
    {"type": "snap", "at_word": 24, "until_word": 25},
    {"type": "push", "at_word": 28, "until_word": 36, "amount": 0.12},
    {"type": "impact", "at_word": 16, "duration": 0.1}
  ],
  "broll": [{"file": "inbox/san-khau.mp4", "at_word": 37, "until_word": 44, "mode": "full", "in": 2.0}],
  "music": {"file": "assets/music/nen-vui.mp3", "db": -22, "duck": true},
  "voiceover": [{"text": "Ba bí quyết vàng cho MC.", "voice": "bich-nga", "start": 0.0, "gain_db": 0}],
  "reframe": {"mode": "crop", "x": 0.5},  // crop (cắt khung, x = vị trí ngang 0–1) | fit-blur (khung nền mờ)
  "theme": {"hero": "#E3120B", "accent": "#FFD23F", "accent2": "#FF4D6D"},
  "silence": {"gap": 0.55}                // ngắt dài hơn mức này bị rút về hơi thở tự nhiên
}
```

## Hiệu ứng (`overlays[].type`)
| type | vùng | trường |
|---|---|---|
| hook-title | top | text, highlight[] |
| keyword-pop | center | text |
| lower-third | center | text, subtext |
| checklist | top | title, items[{text, at_word}] |
| comment-drop | top | author, text |
| counter | center | from, to, prefix, suffix, label |
| typewriter | center | text |
| headline-storm | center | text |
| sticker-burst | center | text |
| cta | center | text |

Có thể ép vùng bằng `"zone": "top"|"center"`. Hai hiệu ứng cùng vùng không được trùng thời gian (máy tự lùi hoặc bỏ).

## Mã lỗi kiểm định
E1 chữ đè chữ · E2 ra ngoài vùng an toàn TikTok/Reels · E3 chữ bị co quá nhỏ · E4 cắt giữa từ ·
E5 phụ đề sai thứ tự · E6 âm lượng/đỉnh âm · E7 khung đen/hình đứng · E8 quá dài · E9 thiếu hình/tiếng ·
E10 chữ che mặt người nói.
