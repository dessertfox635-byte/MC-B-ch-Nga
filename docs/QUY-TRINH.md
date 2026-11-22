# Quy trình sử dụng Xưởng Phim — cách giao việc cho Claude

Bạn chỉ làm hai việc: **bỏ file vào `inbox/`** và **viết một đoạn yêu cầu**. Phần còn lại Claude tự làm và tự kiểm.

## 1. Ai làm gì

| Bước | Ai | Làm gì | Kết quả |
|---|---|---|---|
| 0 | Bạn | Quay theo hướng dẫn (mục 5), bỏ file vào `inbox/` | file quay |
| 1 | Whisper | Nghe tiếng Việt, mốc thời gian từng từ | `transcript.json` |
| 2 | Claude Biên tập | Cắt vấp/lặp, chọn câu mở đầu, sửa chính tả, chọn từ khoá, chọn hiệu ứng theo sách hiệu ứng | `edit-plan.json` |
| 3 | Bộ máy dựng | Cắt, đổi khổ, phóng máy, nhận mặt, tách người, dựng chữ, B-roll, nhạc, chuẩn âm lượng | `.mp4` |
| 4 | Máy kiểm định | 10 luật (đè chữ, che mặt, vùng an toàn, cắt giữa từ, âm lượng…), tự sửa 2 vòng | `qa.json` |
| 5 | Claude Kiểm định | Nhìn ảnh khung hình, sửa kế hoạch, tối đa 3 vòng | bản cuối |
| 6 | Claude Đạo diễn | Viết báo cáo, nêu điều bạn cần xem lại | `outbox/…/BAO-CAO.md` |

## 2. Ba cách gọi

```bash
./dung-phim.sh inbox/clip.mp4 "yêu cầu"     # một video
./canh-thu-muc.sh                            # canh inbox/: có video mới là tự dựng (yêu cầu ghi trong clip.txt cùng tên)
claude                                       # mở Claude Code trong thư mục, rồi nói: "Dựng inbox/clip.mp4 thành reel 45 giây"
```

## 3. Cách viết yêu cầu để Claude hiểu đúng

Claude tự quyết hiệu ứng theo `sach-hieu-ung.md`. Bạn chỉ cần nói **mục đích**, không cần gọi tên hiệu ứng.
Một yêu cầu tốt có 5 ý:

```
1. Đăng ở đâu, dài bao nhiêu:   Reel/TikTok dọc 45 giây  |  YouTube ngang 3 phút  |  cả hai khổ
2. Người xem là ai:              chủ doanh nghiệp cần thuê MC sự kiện
3. Muốn họ nhớ điều gì:          chị Nga dẫn song ngữ Việt–Anh, 500+ sự kiện
4. Giọng điệu:                   sôi động  |  sang trọng, điềm tĩnh  |  thân mật
5. Điều bắt buộc / cấm:          phải có số điện thoại cuối video; không dùng giọng AI; không cắt đoạn nhắc tên khách
```

Bảng dịch: bạn nói thế này thì Claude làm thế kia.

| Bạn viết | Claude sẽ làm |
|---|---|
| "sôi động", "bắt trend", "TikTok" | chữ kinetic, từ khoá đỏ, phóng giật vào câu chốt, cắt nhanh |
| "sang trọng", "doanh nghiệp", "podcast" | phụ đề `clean`, ít hiệu ứng, đẩy máy chậm, không chớp |
| "dạy học", "hướng dẫn từng bước" | phụ đề `pop` đủ từng chữ, danh sách tích dần |
| "nhấn mạnh con số…" | số đếm tăng dần đúng lúc nói con số |
| "có feedback khách: …" | bình luận rơi xuống, đúng nguyên văn bạn đưa |
| "dùng cảnh sân khấu trong inbox/san-khau.mp4 khi nhắc tới gala" | B-roll đúng đoạn nói về gala |
| "tối đa 30 giây" | cắt bớt câu ít giá trị cho đủ độ dài; không đủ thì báo |
| "thêm lời dẫn giọng chị Nga: '…'" | Agent 3 đọc đúng câu đó, nếu có giấy đồng ý; không có thì bỏ và báo |
| "nhạc vui" | chọn trong `assets/music/`; thư mục trống thì không có nhạc và báo |
| "giống video mẫu này" + gửi file | giao Agent 2 phân tích và làm kiểu mới trước, rồi mới dựng |
| "hoạt hình phong cách Riso / Blueprint / Pixel…" | chuyển sang Lemo-Opuscar (phim vẽ bằng code, không cần file quay) |

Hai việc **chưa nối vào dây chuyền tự động**, hiện phải mở `claude` và yêu cầu riêng sau khi dựng xong:
tạo B-roll bằng AI trả phí (Higgsfield, Magnific — luôn cần bạn cho hạn mức credit) và đăng bài qua post-bridge.

### Ba mẫu yêu cầu dùng ngay

**Reel giới thiệu dịch vụ**
> Reel dọc 45 giây cho TikTok và Instagram. Người xem: chủ doanh nghiệp đang tìm MC cho tiệc cuối năm.
> Muốn họ nhớ: chị Nga dẫn song ngữ, đã dẫn hơn 500 sự kiện. Giọng sôi động. Cuối video có nút theo dõi.
> Không dùng giọng AI.

**Podcast / phỏng vấn dài**
> Video ngang 16:9, giữ nguyên độ dài, chỉ cắt chỗ vấp và khoảng lặng. Phụ đề nhỏ trang nhã, không hiệu ứng nhảy.
> Thêm thanh tên khi khách mời xuất hiện: "Nguyễn Văn A – Giám đốc Công ty B".

**Bí quyết / chia sẻ kinh nghiệm**
> Cả hai khổ 9:16 và 16:9, tối đa 60 giây. Đưa câu hay nhất lên đầu. Có danh sách tích dần khi chị liệt kê.
> Phóng máy vào những câu chốt. Nhạc nền nhẹ từ assets/music.

## 4. Nhận kết quả và yêu cầu sửa

`outbox/<ngày-tên>/` gồm file `.mp4` từng khổ, ảnh `kiem-dinh.*.png` (12 khung để lướt nhanh) và `BAO-CAO.md`
(đã cắt gì, từ khoá nào, điểm kiểm định, điều cần bạn xem lại).

Muốn sửa: mở `claude` trong thư mục rồi nói bằng lời thường, kèm tên dự án:
> Dự án 20261122-gioi-thieu: bỏ từ khoá đỏ "giao lưu", giữ lại câu "cảm ơn anh Khôi" đã bị cắt, đổi nút cuối thành "Liên hệ 09xx".

Claude chỉ sửa kế hoạch rồi dựng lại, không làm lại từ đầu. Mọi thứ neo theo lời nói nên cắt thêm bớt không làm lệch chữ.

## 5. Cách quay
Xem mục 6 trong `.claude/skills/xuong-phim/sach-hieu-ung.md`. Tóm tắt: quay ngang 4K, người ở giữa, chừa trống trên đầu
và hai bên; nền cách người 1,5 m; micro cài áo; nói vấp thì dừng 1 giây rồi nói lại cả câu; quay thêm 3–5 cảnh minh hoạ ngắn.

## 6. Giới hạn hiện tại — nói thẳng
- Trong 39 hiệu ứng bạn liệt kê, bộ máy có sẵn 7 nhóm (danh sách tích, bão tiêu đề, bình luận rơi, B-roll, phóng giật,
  đẩy máy, chớp âm bản) cùng kiểu chữ kinetic. Phần còn lại chưa có; bảng đầy đủ kèm cách thay thế ở sách hiệu ứng mục 4.
- Mười phong cách hoạt hình chưa được dựng thử: đã chọn công cụ (Lemo-Opuscar) và bảng đối chiếu, chưa chạy phim nào.
- Mọi thử nghiệm tới giờ dùng giọng máy và ảnh mẫu, **chưa có video thật của chị Nga**. Bản dựng thật đầu tiên cần bạn xem kỹ.
- Chưa có: tự chuyển cảnh giữa nhiều máy quay của podcast, và tự cắt một video dài thành nhiều đoạn ngắn.
- Giọng Bích Nga chưa bật: cần giấy đồng ý đã ký và một bản ghi âm mẫu.
- Chưa cài trên MacBook: cần chạy `setup/install_mac.sh` trên máy đó.
- Nhận diện mặt dùng bộ nhận diện cổ điển của OpenCV: mặt nghiêng nhiều hoặc đeo khẩu trang có thể không nhận ra,
  khi đó chữ không biết để né. Báo cáo sẽ ghi "mặt người: thấy ở N% khung" để bạn biết.
