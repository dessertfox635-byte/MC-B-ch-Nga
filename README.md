# Xưởng Phim – MC Bích Nga

Dây chuyền **dựng phim tự động bằng Claude**: bỏ file quay vào `inbox/`, nhận phim hoàn chỉnh trong `outbox/`.
Không cần người chỉnh tay. Claude làm đạo diễn, chỉ đạo các mô hình miễn phí chạy ngay trên máy:

```
file quay ─▶ Whisper (nghe chữ tiếng Việt, từng từ)
          ─▶ Claude Biên tập  (cắt vấp/lặp, chọn hook, sửa chính tả, chọn từ khoá)
          ─▶ Bộ máy dựng      (cắt + đổi khổ · phóng máy · nhận diện mặt · tách người · chữ kinetic GSAP · B-roll · nhạc · −14 LUFS)
          ─▶ Máy kiểm định    (10 luật: đè chữ, che mặt, vùng an toàn TikTok, cắt giữa từ, âm lượng…) + tự sửa 2 vòng
          ─▶ Claude Kiểm định (nhìn ảnh khung hình, sửa kế hoạch, tối đa 3 vòng)
          ─▶ outbox/…/*.mp4 + BAO-CAO.md
```

## Ba agent
- **Agent 1 – Đạo diễn** (`.claude/skills/xuong-phim`): chạy cả quy trình, giao việc cho `bien-tap` và `kiem-dinh`.
- **Agent 2 – Dựng hình, "CapCut không màn hình"** (`.claude/agents/dung-hinh.md`): timeline JSON → MP4,
  thư viện chữ animation, học kiểu chữ từ video mẫu (đã học kiểu kinetic của video bạn gửi).
- **Agent 3 – Giọng Bích Nga** (`.claude/agents/giong-bich-nga.md`): VieNeu-TTS clone giọng từ 3–8 giây ghi âm,
  **chỉ chạy khi có giấy đồng ý đã ký** (`voice/consent/MAU-GIAY-DONG-Y.md`), mọi file có watermark.

## Cài trên MacBook (một lần)
```bash
curl -fsSL -o /tmp/install.sh https://raw.githubusercontent.com/dessertfox635-byte/MC-B-ch-Nga/claude/zealous-lamport-st39h9/setup/install_mac.sh
bash /tmp/install.sh            # cài vào ~/Documents/Xuong Phim
```
Hoặc đã có repo: `bash setup/install_mac.sh`. Cần ~10–15 GB ổ trống. Kiểm tra lại bất cứ lúc nào: `.venv/bin/python -m xuong doctor`.
Mở thư mục bằng `claude` một lần để đăng nhập và bấm "tin cậy thư mục" (Trust).

## Dùng hằng ngày
```bash
./dung-phim.sh inbox/gioi-thieu.mp4 "Reel 60 giây, chữ kinetic, nhấn 3 gói dịch vụ MC"
./canh-thu-muc.sh                 # canh inbox/: bỏ video vào là tự dựng (yêu cầu riêng để trong file .txt cùng tên)
./dung-phim.sh inbox/x.mp4 --khong-claude    # chỉ dùng máy, không biên tập bằng AI
```

Cách viết yêu cầu để Claude hiểu đúng, và cách quay: **`docs/QUY-TRINH.md`**.
Claude chọn hiệu ứng theo `.claude/skills/xuong-phim/sach-hieu-ung.md`. Rà soát công cụ: `docs/REPOS.md`.

## Tuỳ chỉnh
- `config/brand.json` – tên, chức danh, câu kêu gọi, màu, kiểu chữ mặc định (`kinetic`).
- `config/tu-dien.txt` – tên riêng/thuật ngữ để Whisper viết đúng chính tả.
- `assets/music/` – nhạc nền có bản quyền; Claude chỉ chọn nhạc trong thư mục này.
- `.env` – `XUONG_WHISPER_MODEL=large-v3-turbo` (chuẩn) hoặc `small` (nhanh, máy yếu).

## Bật giọng Bích Nga (Agent 3)
1. In `voice/consent/MAU-GIAY-DONG-Y.md`, chị Nga ký, scan → `voice/consent/bich-nga-da-ky.pdf`, tạo `bich-nga.json` theo hướng dẫn trong file mẫu.
2. `.venv/bin/python -m xuong voice prepare bich-nga ~/Downloads/ghi-am.m4a`
3. Từ đây Claude được phép thêm lời dẫn bằng giọng chị Nga khi yêu cầu có nói tới.

Dữ liệu giọng và giấy đồng ý không bao giờ được đưa lên git (đã chặn trong `.gitignore`).

## Lệnh cho người kỹ thuật
`python -m xuong -h` · `new` · `transcribe` · `hints` · `plan-auto` · `make [--fix N] [--format 9:16]` · `auto` · `effects` · `voice check|prepare|say` · `doctor`.
Kế hoạch biên tập: `.claude/skills/xuong-phim/plan-schema.md`. Các repo đã xét: `docs/REPOS.md`.
