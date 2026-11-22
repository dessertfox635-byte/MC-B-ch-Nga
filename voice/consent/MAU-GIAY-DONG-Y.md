# GIẤY ĐỒNG Ý SỬ DỤNG GIỌNG NÓI ĐỂ TẠO GIỌNG NÓI NHÂN TẠO (AI)

Tôi, **[Họ và tên đầy đủ]**, CCCD số **[……]**, sau đây gọi là "Người có giọng", đồng ý cho
**[Tên công ty / cá nhân sử dụng]** (sau đây gọi là "Bên sử dụng") thu thập các đoạn ghi âm giọng nói
của tôi và dùng phần mềm trí tuệ nhân tạo để tạo ra giọng nói nhân tạo mô phỏng giọng của tôi, với các điều kiện sau:

1. **Phạm vi được dùng** (đánh dấu):
   - [ ] Lời dẫn, lời thoại bổ sung trong video giới thiệu dịch vụ MC của chính tôi
   - [ ] Video mạng xã hội trên kênh của tôi / của Bên sử dụng
   - [ ] Quảng cáo trả phí
   - [ ] Khác: ……
2. **Không được dùng** giọng nhân tạo để: nói thay tôi những nội dung tôi chưa duyệt; gọi điện, nhắn
   tin giả danh tôi; xác thực danh tính; chính trị, tôn giáo; nội dung sai sự thật, xúc phạm, người lớn.
3. **Duyệt nội dung:** mọi câu chữ đọc bằng giọng nhân tạo phải được tôi hoặc người tôi ủy quyền duyệt trước khi đăng.
4. **Ghi nhãn:** video có dùng giọng nhân tạo phải ghi rõ "có sử dụng giọng nói AI" khi nền tảng yêu cầu.
   File âm thanh tạo ra được gắn watermark kỹ thuật.
5. **Lưu trữ:** giọng mẫu và dữ liệu giọng chỉ lưu trên máy của Bên sử dụng, không đưa lên dịch vụ công cộng.
6. **Thời hạn:** từ ngày ……/……/20…… đến ngày ……/……/20…… .
7. **Thu hồi:** tôi có quyền thu hồi đồng ý bất kỳ lúc nào bằng văn bản. Khi đó Bên sử dụng xoá giọng mẫu,
   dữ liệu giọng và ngừng tạo nội dung mới bằng giọng của tôi trong vòng 7 ngày.

Ký tại ……, ngày …… tháng …… năm 20……

| Người có giọng | Bên sử dụng |
|---|---|
| (ký, ghi rõ họ tên) | (ký, ghi rõ họ tên, chức vụ) |

---

## Sau khi ký — cách bật Agent 3

1. Scan bản đã ký thành PDF, đặt vào `voice/consent/bich-nga-da-ky.pdf`.
2. Tạo file `voice/consent/bich-nga.json`:

```json
{
  "person": "Bích Nga",
  "signed": true,
  "document": "voice/consent/bich-nga-da-ky.pdf",
  "scope": ["lời dẫn video dịch vụ MC", "video mạng xã hội"],
  "expires": "2027-12-31",
  "revoked": false
}
```

3. Kiểm tra: `python -m xuong voice check bich-nga`
4. Lấy giọng mẫu từ 1–3 bản ghi âm rõ của chị Nga (máy tự chọn đoạn 3–8 giây tốt nhất):
   `python -m xuong voice prepare bich-nga ~/Downloads/ghi-am-1.m4a ~/Downloads/video-noi.mp4`
5. Muốn thu hồi: đặt `"revoked": true` và xoá `voice/reference/bich-nga.*`. Hệ thống sẽ từ chối ngay.

Cả thư mục `voice/consent/` (trừ file mẫu này) và `voice/reference/` đều bị chặn khỏi git để dữ liệu giọng không rời khỏi máy.
