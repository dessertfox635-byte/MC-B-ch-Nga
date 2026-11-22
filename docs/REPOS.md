# Rà soát công cụ — đã có gì, chọn gì, bỏ gì

Rà ngày 22/11/2026 trên **môi trường cloud "Xuong Phim"** (nơi Claude đang chạy).
MacBook của bạn chưa cho phiên cloud truy cập nên **chưa rà được trên máy Mac**; sau khi chạy `setup/install_mac.sh`,
lệnh `.venv/bin/python -m xuong doctor` sẽ rà đúng trên máy đó.

Tiêu chí chọn: miễn phí · dùng thương mại được · chạy trên Mac không cần GPU · Claude điều khiển bằng lệnh, không cần người bấm.

## 1. Dựng phim

| Công cụ | Đã có? | Giấy phép | Quyết định |
|---|---|---|---|
| **Bộ máy Xưởng Phim** (repo này: Whisper + GSAP/Chromium + ffmpeg + tách người + kiểm định) | ✅ đã cài, đã chạy thử | của bạn | **Lõi chính** cho video người ngồi nói, podcast, reel |
| GSAP 3.13 | ✅ đã cài | miễn phí cả thương mại | Động cơ chuyển động của mọi chữ |
| Playwright + Chromium | ✅ đã cài (dạng thư viện) | Apache 2.0 | Chụp từng khung chữ. Bản "Playwright MCP" (điều khiển trình duyệt) không cần cho dựng phim |
| [Herk Edit Kit](https://github.com/nateherkai/herk-edit-kit) | ⬜ chỉ tải về để đọc mã | MIT | **Tham khảo**, cài kèm bằng `--kem-bo-mau`. Đã lấy luật cắt khoảng lặng và quy trình cắt lỗi. Không làm lõi vì mặc định dùng ElevenLabs trả phí và không có kiểm định che mặt/tiếng Việt |
| [HyperFrames](https://github.com/heygen-com/hyperframes) | ⬜ chỉ tải về để đọc mã | Apache 2.0 | **Tham khảo**, cùng cách làm HTML→video. Dùng khi cần 450 khối đồ hoạ dựng sẵn |
| [OpenFilm](https://github.com/openfilm/openfilm) | ⬜ chỉ tải về để đọc mã | MIT | **Dự phòng**: có trình dựng timeline cho người chỉnh tay. Bạn muốn không ai can thiệp nên không đưa vào dây chuyền |
| "Rea Video" — tôi hiểu là [Revideo](https://github.com/redotvideo/revideo) | ⬜ chưa cài | MIT | **Bỏ**: cùng việc với bộ máy hiện có nhưng viết bằng TypeScript phải biên dịch, không lợi hơn HTML+GSAP. Nếu ý bạn là Remotion: cũng bỏ, vì công ty trên 3 người phải mua giấy phép |
| [OpenMontage](https://github.com/calesthio/OpenMontage) | ⬜ | AGPL-3.0 | **Bỏ**: AGPL buộc công khai mã khi làm dịch vụ cho khách |
| [Lemo-Opuscar](https://github.com/lemomo-ai/lemo-opuscar) | ⬜ đã đọc mã, chưa dựng thử | code MIT · tài liệu CC BY-NC · phim làm ra là của bạn, dùng thương mại được | **Chọn cho phim hoạt hình** (khoảng 100 phong cách). Cài bằng `--hoat-hinh` |
| [PixelFX](https://github.com/patch-gg/pixelfx) | ⬜ | MIT | **Tuỳ chọn**: 244 hiệu ứng pixel cho game; chỉ cần khi làm phong cách 16-bit |
| [Awesome Opus videos](https://github.com/yihui-dev/awesome-opus5-5-videos) | ⬜ | — | Kho prompt mẫu để tham khảo ý tưởng, không phải phần mềm, không cần cài |
| ComfyUI | ⬜ | GPL-3.0 | **Bỏ trên Mac**: cần card NVIDIA. Cần ảnh/video AI thì dùng Higgsfield, Magnific đã kết nối sẵn |
| [Open Generative AI](https://github.com/Anil-matcha/Open-Generative-AI) | ⬜ | MIT | **Bỏ**: chỉ là giao diện gọi dịch vụ MuAPI trả phí, và tự quảng cáo "không có bộ lọc nội dung" |
| [Impeccable](https://github.com/pbakaus/impeccable) | ⬜ | — | **Không thuộc dựng phim**: skill thiết kế giao diện web. Nên cài riêng cho việc làm website |
| Unslop | ⬜ không tìm thấy repo đúng tên | — | Chưa cài. Cần bạn gửi đường dẫn; tôi không cài theo tên đoán |

## 2. Giọng nói và nghe chữ

| Công cụ | Đã có? | Giấy phép | Quyết định |
|---|---|---|---|
| faster-whisper (large-v3-turbo) | ✅ | MIT | **Chọn** để nghe chữ tiếng Việt từng từ |
| [VieNeu-TTS](https://github.com/pnnbao97/VieNeu-TTS) | ✅ đã chạy thử clone giọng | Apache 2.0 | **Chọn** cho Agent 3: chuyên tiếng Việt, chạy CPU, có watermark |
| [VoiceStudio](https://github.com/debpalash/VoiceStudio) | ⬜ | AGPL-3.0 | **Bỏ**: 16 bộ đọc nhưng là app có giao diện, AGPL, và không chuyên tiếng Việt bằng VieNeu |
| [OpenWhispr](https://github.com/OpenWhispr/openwhispr) | ⬜ | MIT | **Không thuộc dây chuyền**: app đọc chính tả thay bàn phím. Hữu ích cho bạn khi soạn kịch bản bằng giọng nói |

## 3. Kết nối (MCP)

| Kết nối | Đã có? | Quyết định |
|---|---|---|
| Perplexity | ⬜ chưa kết nối | Không cần: Claude Code đã có tìm kiếm web sẵn |
| Firecrawl | ⬜ có trong danh mục, chưa cài | **Tuỳ chọn**: cần khi làm video từ nội dung website (lấy chữ, hình từ trang web khách) |
| Playwright | ✅ dạng thư viện | Đủ dùng |
| Composio | ⬜ chưa kết nối | Không cần: bạn đã nối trực tiếp Gmail, Drive, Canva, post-bridge |
| Higgsfield, Magnific | ✅ đã kết nối | Dùng tạo B-roll AI **chỉ khi** bạn cho hạn mức credit trong yêu cầu |
| post-bridge | ✅ đã kết nối | Đăng TikTok/Reels/YouTube sau khi dựng — chỉ đăng khi bạn bảo đăng |
| Google Drive | ✅ đã kết nối | Lấy file quay từ Drive |

## 4. Không liên quan dựng phim
OpenSEO, AppFlowy, OpenProject, Cal.diy, Chatwoot: phần mềm SEO, ghi chú, quản lý dự án, đặt lịch, chăm sóc khách hàng.
Cap: quay màn hình (thay Loom), hữu ích khi cần quay hướng dẫn phần mềm để đưa vào dựng.

## 5. Kiểu chữ từ video mẫu (ScreenRecording 22/11)
Phong cách chữ bám lời đã được phân tích và viết lại từ đầu trong `effects/kinetic.js`, không sao chép tài sản:
chữ hiện theo từng từ, từ khoá đỏ khổng lồ, xếp so le, vòng cung quanh đầu, chữ chui sau người,
kiểu vào pixel / lộn chữ / phóng nhoè / dập. Font OFL có dấu tiếng Việt: Paytone One, Anton, Be Vietnam Pro.
