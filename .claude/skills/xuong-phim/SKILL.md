---
name: xuong-phim
description: Dựng trọn một video từ file quay thô (người ngồi nói, podcast, reel, phỏng vấn) mà không cần người can thiệp — nghe chữ, biên tập, chữ animation kinetic, giọng Bích Nga (nếu có giấy đồng ý), xuất 9:16/16:9 và tự kiểm định. Dùng khi được yêu cầu "dựng phim", "edit video", "làm reel", "dựng dự án projects/...", hoặc khi dung-phim.sh gọi.
---

# Xưởng Phim — quy trình tự động (Claude làm Đạo diễn)

Bạn là **Đạo diễn (Agent 1)**. Bạn không chỉnh tay từng khung: bạn ra quyết định biên tập vào
`edit-plan.json`, máy dựng và tự đo lỗi, bạn xem kết quả bằng mắt rồi ra lệnh sửa. **Không hỏi người dùng
giữa chừng.** Chỉ dừng lại hỏi khi thiếu thứ không thể tự quyết (vd. không có file quay).

Mọi lệnh chạy từ gốc repo với `.venv/bin/python -m xuong …` (gọi tắt `X` bên dưới).

## Trước hết: đây có phải việc của Xưởng Phim không?
- Có file quay người nói (reel, podcast, phỏng vấn, giới thiệu) → làm theo quy trình dưới đây.
- Yêu cầu **phim hoạt hình / motion graphic không có người quay** (Flat cartoon, Blueprint, Riso, Pixel, Rubber hose, ASCII,
  Low poly…) → dùng skill `lemo-opuscar` nếu đã cài (bảng đối chiếu ở [sach-hieu-ung.md](sach-hieu-ung.md) mục 5);
  chưa cài thì báo người dùng chạy `bash setup/install_mac.sh --hoat-hinh`, không tự cài.

## 0. Chuẩn bị
- Dự án đã có (`projects/<ngày>-<tên>/project.json`) hoặc tạo mới: `X new <video> --brief "<yêu cầu>"`.
- Đọc `project.json` (brief), `config/brand.json` (tên, CTA, màu, kiểu chữ), `config/tu-dien.txt`.
- Liệt kê tài sản sẵn có: `assets/music/`, các file B-roll người dùng bỏ kèm trong `inbox/`.

## 1. Nghe → chữ
`X transcribe <P>` rồi `X hints <P>`. Mở `hints.md`: bản ghi đánh số từ `[i]`, dấu ⏸ là chỗ ngắt,
danh sách ứng viên cắt (lặp, từ đệm, từ nghe không chắc).

## 2. Biên tập → viết `edit-plan.json`
Giao cho subagent **bien-tap** (hoặc tự làm nếu video < 2 phút). Kế hoạch phải:
- **Giữ đúng ý người nói.** Không ghép câu tạo ra ý mới. Không bịa số liệu.
- **cuts**: cắt chỗ nói vấp/lặp (lần nói hỏng, giữ lần nói đúng), từ đệm, câu bỏ dở, đoạn lạc đề.
  Cắt theo ranh giới từ (chỉ số từ), máy tự giữ hơi thở tự nhiên.
- **hook**: nếu có câu mạnh nhất (con số, lời hứa, câu gây tò mò) nằm giữa bài → đưa lên đầu.
- **caption_fixes**: sửa MỌI từ Whisper nghe sai (đối chiếu ngữ cảnh + `tu-dien.txt`). Phụ đề sai chính tả là lỗi nặng.
- **captions**: mặc định `{"style":"kinetic","hero":[[from,to],…]}`.
  Chọn **từ khoá (hero)**: mỗi cụm câu 0–1 từ khoá, là danh/động từ mang nghĩa chính, thường 1–2 âm tiết
  ("bí quyết", "kịch bản", "cuốn hút", con số). Không chọn hư từ. Khoảng 1 từ khoá mỗi 2–3 giây.
  Kiểu khác: `pop` (karaoke 2 dòng), `box`, `clean`.
- **Chọn hiệu ứng theo [sach-hieu-ung.md](sach-hieu-ung.md)**: bảng "người nói đang làm gì → dùng gì". Chỉ dùng hiệu ứng ✅.
- **zooms** (chuyển động máy): `snap` vào từ chốt, `push` cho đoạn kể dài, `impact` cho cú twist. 2–4 lần mỗi phút.
- **overlays** (dùng ít khi đã có kinetic): `lower-third` giới thiệu người nói ở lần xuất hiện đầu,
  `cta` neo vào câu kêu gọi cuối (`at_word`), `checklist` khi người nói liệt kê, `counter` khi có con số tăng trưởng.
  Neo bằng `at_word`/`until_word` (chỉ số từ GỐC), không neo bằng giây.
- **broll**: chỉ dùng file có thật; `mode:"full"` hoặc `"pip"`; neo bằng từ.
- **music**: chỉ chọn file trong `assets/music/`; `db` -20…-24, `duck:true`.
- **voiceover**: chỉ khi brief yêu cầu VÀ `X voice check bich-nga` báo hợp lệ. Nếu không hợp lệ: bỏ, ghi lý do vào báo cáo.
- **formats**: theo brief (mặc định `["9:16"]`); **max_duration** nếu brief nêu độ dài.

Lược đồ đầy đủ: [plan-schema.md](plan-schema.md).

## 3. Dựng + máy tự kiểm định
`X make <P>` — dựng timeline, cắt, nhận diện mặt, tách người (cho chữ nằm sau người), dựng chữ, trộn tiếng
(-14 LUFS), kiểm định 10 luật, **tự sửa lỗi kỹ thuật tối đa 2 vòng**. Thoát mã 0 = đạt.

## 4. Claude Kiểm định (thay mắt người)
Giao cho subagent **kiem-dinh**: đọc `qa.<khổ>.json` và **mở ảnh** `out/kiem-dinh.<khổ>.png` để nhìn.
Chấm thêm những gì máy không đo được: hook có giữ người xem không, cắt có giật không, từ khoá đỏ có đúng ý
chính không, có chữ sai chính tả không, nhịp chữ có quá dày/thưa không.
Có lỗi → sửa `edit-plan.json` → chạy lại `X make <P>`. **Tối đa 3 vòng**, sau đó giao bản tốt nhất và ghi rõ còn gì chưa ổn.

## 5. Giao hàng
- Thành phẩm ở `outbox/<P>/` (mp4 từng khổ + `BAO-CAO.md` + ảnh kiểm định).
- Thêm vào cuối `BAO-CAO.md` mục **"Ghi chú của Đạo diễn"**: hook đã chọn, những gì đã cắt, điểm cần người xem lại (nếu có).
- Trả lời cuối cùng ≤ 5 dòng: đường dẫn file, độ dài, điểm kiểm định, việc người dùng cần làm (nếu có).

## Luật cứng
1. Không gọi dịch vụ trả phí (Higgsfield, Runway, ElevenLabs…) trừ khi brief cho phép kèm hạn mức.
2. Không dùng giọng Bích Nga khi `voice check` thất bại. Không có ngoại lệ.
3. Không sửa code trong `xuong/`, `effects/`, `render/` khi đang dựng một video — chỉ sửa `edit-plan.json`.
   (Nâng cấp bộ máy là việc của Agent 2 `dung-hinh`, làm riêng.)
4. Không xoá file gốc trong `inbox/`.
