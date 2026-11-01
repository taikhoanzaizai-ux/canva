# Các bản cập nhật

## 0.2.2

- Sửa nhận diện ô tải voice của Canva: hỗ trợ input ẩn nhận mọi loại tệp và chờ bảng Tải lên tải xong.
- Nhận diện đoạn voice dạng `div role=button` trên timeline; dùng tên tải lên theo mã nội dung để tránh lấy nhầm voice cũ cùng tên.
- Bỏ phần nhãn trang trí ẩn khi tìm nút, để nhận đúng tab Âm thanh của Canva.
- Sửa ô nhập độ dài video: Canva dùng placeholder `--`, không phải aria-label.
- Kiểm tra nút âm lượng trong bảng thu gọn; video stock không có nút âm lượng không làm dừng quá trình dựng.
- Tiện ích kiểm tra kết nối thật và hiển thị lỗi/trạng thái từ ứng dụng.
- Chặn tiện ích cũ tiếp tục thao tác; báo rõ cần cài tiện ích 0.2.2 từ đúng thư mục ứng dụng.
- Đã kiểm tra trực tiếp tải voice vào timeline và cắt một cảnh trên Canva. Chưa xác nhận toàn bộ bản dựng tự động từ đầu đến cuối.

## 0.2.1

- Bản portable: cấu hình, tiến độ, voice đã cắt, log, cache, file tạm và cập nhật lưu trong `Data` cạnh EXE.
- Thư viện `_internal` chạy ngay trong thư mục giải nén, không tự bung vào Temp ổ C.
- Tự sao chép dữ liệu từ AppData cũ khi thư mục portable chưa có dự án; giữ bản gốc để dự phòng.
- Thêm nút mở thư mục dữ liệu. Lần chuyển từ 0.2.0 trở xuống cần tải gói Windows đầy đủ vì cấu trúc ứng dụng đã đổi.

## 0.2.0

- Thêm nút **Kiểm tra cập nhật** trong ứng dụng, tải và cài bản mới từ GitHub Releases.
- Kiểm tra SHA-256, giữ cấu hình/tiến độ, sao lưu bản cũ và phục hồi khi bản mới không khởi động được.
- Đưa mã nguồn, kiểm thử và quy trình phát hành Windows vào GitHub.
- Giữ bản sửa ô mã ghép nối bị trống từ 0.1.1.

## 0.1.1

- Sửa ô mã ghép nối bị mất giá trị hiển thị; kiểm tra cả hiển thị và sao chép.

## 0.1.0

- Bản thử lập cảnh từ voice/kịch bản và điều khiển trình dựng video Canva tiếng Việt.

