# Xưởng Phim – MC Bích Nga

Dây chuyền dựng phim tự động: người dùng chỉ bỏ file quay vào `inbox/`, Claude chỉ đạo các mô hình
(Whisper, VieNeu-TTS, MediaPipe, Chromium+GSAP, ffmpeg) dựng ra phim hoàn chỉnh trong `outbox/`, tự kiểm định, không cần người can thiệp.

## Ba agent
| Agent | Vai trò | Ở đâu |
|---|---|---|
| **Agent 1 – Đạo diễn** | Chạy toàn bộ quy trình, giao việc cho subagent `bien-tap` và `kiem-dinh` | skill `xuong-phim` |
| **Agent 2 – Dựng hình** ("CapCut không màn hình") | Bộ máy timeline → MP4, thư viện chữ animation, học phong cách từ video mẫu | subagent `dung-hinh` |
| **Agent 3 – Giọng Bích Nga** | Clone giọng có giấy đồng ý, đọc lời dẫn có watermark | subagent `giong-bich-nga` |

## Quy ước
- Mọi lệnh: `.venv/bin/python -m xuong <lệnh>` (xem `python -m xuong -h`). Kiểm tra máy: `python -m xuong doctor`.
- Khi dựng một video: chỉ sửa `projects/<P>/edit-plan.json`, không sửa code bộ máy.
- Neo mọi hiệu ứng vào chỉ số từ (`at_word`), không neo vào giây.
- Tiếng Việt có dấu là bắt buộc trong mọi chữ trên hình; phụ đề sai chính tả là lỗi nặng.
- Không dùng giọng Bích Nga khi `python -m xuong voice check bich-nga` thất bại.
- Không gọi dịch vụ trả phí trừ khi người dùng cho phép kèm hạn mức.
- Trả lời người dùng bằng tiếng Việt, ngắn gọn.
