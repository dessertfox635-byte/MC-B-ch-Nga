# Sách hiệu ứng — khi nào dùng gì

Đạo diễn và Biên tập đọc file này trước khi viết `edit-plan.json`.
**Chỉ dùng hiệu ứng có dấu ✅.** Hiệu ứng ⏳ chưa có trong bộ máy: chọn cái thay thế ghi ở cột cuối và ghi vào báo cáo.

## 1. Chọn theo việc người nói đang làm

| Người nói đang… | Dùng | Ghi trong plan |
|---|---|---|
| Mở đầu, 3 giây đầu | Chữ kinetic + từ khoá đỏ; đảo câu mạnh nhất lên đầu | `hook`, `captions.hero` |
| Tự giới thiệu lần đầu | Thanh tên | `overlays: lower-third` |
| Nói một từ/cụm là ý chính của câu | Từ khoá đỏ khổng lồ (1 từ mỗi 2–3 giây, không hơn) | `captions.hero` |
| Nhấn một câu chốt, câu gây sốc | Phóng giật vào mặt đúng từ nhấn | `zooms: snap` |
| Kể một đoạn dài 5–10 giây không đổi cảnh | Đẩy máy chậm cho khung "sống" | `zooms: push` |
| Chuyển ý lớn, cú twist | Chớp âm bản 2–3 khung | `zooms: impact` (tối đa 2 lần/phút) |
| Liệt kê "thứ nhất, thứ hai…" | Danh sách tích dần, neo từng mục vào lúc nói | `overlays: checklist` |
| Nêu con số (khách, năm, %, tiền) | Số đếm tăng dần | `overlays: counter` |
| Nhắc lời khen, câu hỏi của khách | Bình luận rơi xuống | `overlays: comment-drop` |
| Nhắc tới sân khấu, sản phẩm, sự kiện cụ thể và CÓ file hình | B-roll phủ toàn khung hoặc khung nhỏ | `broll: full / pip` |
| Kết thúc, kêu gọi | Nút theo dõi, neo vào câu kêu gọi (không neo 3 giây cuối khi dùng kinetic) | `overlays: cta` |
| Cần lời dẫn nối đoạn | Giọng Bích Nga (chỉ khi `voice check` đạt) | `voiceover` |

Liều lượng cho reel 30–60 giây: 1 thanh tên, 1 nút theo dõi, 2–4 lần phóng máy, tối đa 1 checklist hoặc 1 counter.
Chữ kinetic đã là "món chính"; thêm hiệu ứng khác chỉ khi nó giúp hiểu nhanh hơn.

## 2. Chuyển động máy quay (giả lập khi dựng) ✅

```jsonc
"zooms": [
  {"type": "snap",   "at_word": 24, "until_word": 25},                 // phóng 18% trong 0.08s, giữ tới hết từ
  {"type": "push",   "at_word": 28, "until_word": 36, "amount": 0.12}, // đẩy dần đều
  {"type": "impact", "at_word": 16, "duration": 0.1}                    // chớp âm bản
]
```
`focus: [x, y]` (0–1) là điểm phóng vào, mặc định `[0.5, 0.38]` (mặt người ngồi giữa khung).
Không đặt hai lần phóng chồng thời gian. Không phóng trong lúc đang có B-roll toàn khung.

## 3. Kiểu chữ / phụ đề ✅
| style | Khi dùng |
|---|---|
| `kinetic` (mặc định) | Reel, TikTok, video giới thiệu: chữ bám lời, từ khoá đỏ, chữ chui sau người |
| `pop` | Video dạy học, cần đọc đủ từng chữ: 2 dòng dưới, sáng từng từ |
| `box` | Nền rối, cần chữ dễ đọc tuyệt đối |
| `clean` | Phỏng vấn, podcast dài, khách doanh nghiệp: phụ đề nhỏ, trang nhã |

## 4. Danh mục 39 hiệu ứng trong hai video bạn gửi

Trạng thái: ✅ có sẵn · 🔧 làm được một phần bằng cái có sẵn · ⏳ chưa có.
Mô tả dưới đây dựa trên **tên** hiệu ứng trong ảnh chụp màn hình và nghĩa thông dụng trong nghề dựng;
các dòng ghi "(đoán)" là tên riêng của tác giả, cần xem video gốc mới làm đúng được.

| Hiệu ứng | Là gì | Dùng khi | TT | Hiện dùng thay bằng |
|---|---|---|---|---|
| Checklist Pop / Checklist / Running list | Danh sách hiện và tích dần | Liệt kê | ✅ | `checklist` |
| Headline Storm | Nhiều chữ bay vào từ các hướng | Mở đầu dồn dập | ✅ | `headline-storm` |
| Comment drop | Bong bóng bình luận rơi xuống | Trích lời khách | ✅ | `comment-drop` |
| B-roll Overlay | Hình minh hoạ phủ lên lời nói | Nhắc tới vật/cảnh cụ thể | ✅ | `broll` |
| Snap Zoom | Phóng giật vào mặt | Nhấn từ chốt | ✅ | `zooms: snap` |
| Digital Zoom | Đẩy máy chậm | Đoạn kể dài | ✅ | `zooms: push` |
| Impact frame | Chớp âm bản/tương phản mạnh 2–3 khung | Cú twist | ✅ | `zooms: impact` |
| Growth Curve | Đường biểu đồ tăng trưởng vẽ dần | Nói về tăng trưởng | 🔧 | `counter` (có số, chưa có đường cong) |
| Chat Takeover | Khung chat chiếm màn hình | Kể đoạn hội thoại | 🔧 | nhiều `comment-drop` nối nhau |
| Frame Escape / Frame Break | Người hoặc vật tràn ra ngoài khung viền | Tạo chiều sâu | 🔧 | chữ kinetic nằm sau người (đã có tách người) |
| Orbit ring | Vòng chữ/biểu tượng quay quanh đầu | Giới thiệu nhiều công cụ | 🔧 | chữ vòng cung của kinetic (đứng yên, chưa quay) |
| Green Screen | Thay nền sau lưng người nói | Minh hoạ địa điểm, màn hình | ⏳ | `broll: pip` |
| Rack focus | Chuyển nét giữa người và nền | Dồn chú ý vào chữ/người | ⏳ | — |
| Dolly Zoom | Nền giãn ra trong khi người giữ nguyên cỡ | Khoảnh khắc "ngộ ra" | ⏳ | `zooms: snap` |
| Paper Cutout | Người thành hình cắt giấy viền trắng | Phong cách thủ công | ⏳ | — |
| Zoom Through Cut / Zoom Portal | Phóng xuyên qua một điểm để sang cảnh khác | Chuyển cảnh | ⏳ | cắt thẳng + `impact` |
| Blade slice / Paper tear | Chuyển cảnh kiểu chém ngang / xé giấy | Chuyển chương | ⏳ | cắt thẳng |
| Magazine Cover / Press front | Đóng băng khung hình thành bìa tạp chí / trang nhất báo | Giới thiệu nhân vật, tin lớn | ⏳ | `hook-title` |
| Phone Mockup | Video/ảnh nằm trong khung điện thoại | Khoe app, bài đăng | ⏳ | `broll: pip` |
| Post wall | Bức tường bài đăng mạng xã hội | Chứng minh độ phủ | ⏳ | `comment-drop` |
| Liquid Glass | Tấm kính mờ làm nền chữ | Giao diện sang, hiện đại | ⏳ | `box` |
| Live cursor | Con trỏ chuột tự bấm trên giao diện | Hướng dẫn phần mềm | ⏳ | — |
| Code body | Mã lệnh lấp đầy dáng người | Nội dung lập trình/AI | ⏳ | — |
| Sketch words | Chữ vẽ tay | Giọng thân mật | ⏳ | — |
| Studio Reveal | Lùi máy lộ hậu trường | Mở/kết video | ⏳ | cần cảnh quay riêng |
| Orbit | Máy quay vòng quanh chủ thể | Giới thiệu sản phẩm | ⏳ | cần cảnh quay riêng hoặc 3D |
| Layer explode | Tách lớp 3D bung ra | Giải thích cấu tạo | ⏳ | — |
| Letter dive | Máy lao xuyên qua con chữ | Mở đầu | ⏳ | kiểu vào `tumble` của kinetic |
| Clone row, Day dial, Predict keys, Head stack, Banknote | (đoán) tên riêng của tác giả | — | ⏳ | cần video gốc |

Muốn thêm một hiệu ứng ⏳: gửi đoạn quay màn hình có hiệu ứng đó (như đã làm với kiểu kinetic) và giao cho
subagent `dung-hinh`. Ưu tiên nên làm trước cho video người ngồi nói: Green Screen, Rack focus, Dolly Zoom,
Zoom Through Cut, Paper Cutout, Phone Mockup, Magazine Cover — vì bộ máy đã có sẵn phần tách người khỏi nền.

## 5. Mười phong cách hoạt hình → dùng Lemo-Opuscar (không dùng bộ máy người-ngồi-nói)

Phim hoạt hình vẽ bằng code là việc khác hẳn cắt dựng người nói. Giao cho plugin
[Lemo-Opuscar](https://github.com/lemomo-ai/lemo-opuscar) (khoảng 100 phong cách, code MIT, phim làm ra được dùng thương mại).
Cài: `bash setup/install_mac.sh --hoat-hinh`. Gọi: `/lemo-opuscar` kèm tên phong cách.

| Bạn gọi | Phong cách tương ứng trong Lemo-Opuscar |
|---|---|
| Flat cartoon | `midcentury-toon`, `flat-space-explainer` |
| Blueprint | `blueprint` |
| Riso print | `risograph` |
| 16-bit pixel | `pixel-rpg` (thêm hiệu ứng lửa/nổ từ PixelFX nếu cần) |
| Ink silhouette | `silhouette-rhythm`, `shadow-puppet`, `ink-wash` |
| Rubber hose | `rubber-hose` |
| ASCII | `ascii-crt` |
| Cardboard cutout | `paper-popup`, `papercut-red` (gần nhất) |
| 90s low poly | `lowpoly-island` |
| Soft clay 3D | chưa có sẵn; gần nhất `brick-toy`, hoặc tự tạo phong cách riêng theo `MY-STYLES.md` của thư viện |

Lưu ý: tôi mới đọc mã và danh sách phong cách của Lemo-Opuscar, chưa dựng thử phim nào bằng nó.

## 6. Cách quay để máy dựng đẹp (gửi cho người quay)

1. **Khung:** quay ngang 4K nếu được (cắt ra cả 9:16 lẫn 16:9). Người ở giữa, mắt nằm ở 1/3 trên.
   Chừa trống phía trên đầu và hai bên: đó là chỗ đặt chữ. Quay dọc thì chừa 1/4 khung phía trên đầu.
2. **Nền:** tách khỏi người ít nhất 1,5 m, không quá rối, khác màu áo. Chữ chui sau lưng người đẹp nhất khi viền người rõ.
3. **Tiếng:** micro cài áo hoặc micro cách miệng 15–20 cm. Phòng yên. Không bật nhạc khi quay (nhạc ghép sau).
4. **Nói:** nói vấp thì dừng 1 giây rồi nói lại cả câu; máy tự cắt lần hỏng. Đừng sửa giữa câu.
   Mỗi ý một câu ngắn. Câu chốt nói chậm và rõ, đó là chỗ đặt từ khoá đỏ và phóng máy.
5. **Mỗi lần quay một file,** để 1 giây im lặng đầu và cuối. Không cần cắt sẵn.
6. **Hình minh hoạ (B-roll):** quay thêm 3–5 cảnh ngắn 5–10 giây (sân khấu, khán giả, hậu trường, cận tay cầm micro),
   bỏ cùng thư mục `inbox/` và ghi trong file yêu cầu cảnh nào dùng cho ý nào.
7. **Giọng mẫu cho Agent 3:** một bản ghi 30–60 giây đọc tự nhiên, phòng yên, không nhạc.
