# Các bản cập nhật

## 0.3.2

- Sửa vòng lặp yêu cầu tự mở tab: nút Kết nối Canva tự mở đúng thiết kế đã lưu hoặc tạo Video khổ ngang đang được phần mềm chờ, rồi gắn bộ dựng khi trang tải xong.
- Khi chỉ ghép nối và chưa chọn voice, không yêu cầu mở tab; báo sẵn sàng để bấm Bắt đầu trong phần mềm.
- Dùng lại tab đang mở khi bấm Kết nối nhiều lần; chỉ nhận tab mang dấu khởi tạo đúng dự án, không chọn nhầm tab Canva cũ.
- Không tự bỏ trạng thái Tạm dừng khi người dùng chỉ bấm Kết nối.

## 0.3.1

- Bắt đầu tự động: nếu chưa phân tích thì phân tích voice, mở Chrome đúng hồ sơ có SKST, tạo Video khổ ngang, tự nhận link và dựng; không cần tạo thiết kế/dán link thủ công.
- Nhận đúng tab mới bằng dấu khởi tạo công khai, khác mã ghép nối; chỉ nhận thiết kế trống, không tác động tab Canva cũ.
- Giữ mã ghép nối trong Data/pairing.json để tiện ích tự nối lại những lần sau. Không truyền mã trong URL Canva, không sửa cấu hình trình duyệt.
- Tiếp tục mở đúng thiết kế đã lưu, giữ tiến độ; chặn bấm lặp khi Chrome đang mở và báo rõ nếu tiện ích/đăng nhập chưa sẵn sàng sau 120 giây.

## 0.3.0

- Mặc định chỉ video người thật: chặn hoạt hình, 3D, khung neon, ký hiệu và mô phỏng; yêu cầu cả dấu hiệu người thật lẫn từ khóa liên quan. Chủ đề nội tạng dùng bác sĩ/người bệnh thay cho đồ họa.
- Khoảng nghỉ kế thừa cảnh sinh hoạt theo ngữ cảnh; không tìm stock bằng chữ Khoảng nghỉ.
- Phân tích hết voice gốc khi để trống Đến giây. Chia 50 cảnh/phần rồi cắt WAV chính xác theo biên cảnh, kiểm tra FFprobe; phần cuối có thể ít hơn 50 khi hết voice.
- Tự mở tab Video khổ ngang, chuyển voice và cảnh tiếp theo sau khi đối chiếu số cảnh và thời lượng trên Canva; giữ lịch sử thiết kế, mốc voice và danh sách clip đã dùng qua mọi phần.
- Cuộn tới cuối vùng timeline thật để tránh đọc nhầm cảnh cuối đang hiển thị khi Canva ẩn các cảnh ngoài khung nhìn; kiểm tra số cảnh sau thao tác chèn.
- Không ghi đè thiết kế cũ hoặc thay các cảnh đã dựng. Bản cũ có đồ họa cần chọn voice gốc và dựng lại trên thiết kế trống.

## 0.2.8

- Áp dụng sửa từ khóa cho mọi chủ đề/kịch bản: tránh khớp một phần từ như gian→gan, thân→thận và tác→tắc.
- Nhận diện và nâng cấp toàn bộ từ khóa cũ do phần mềm tạo cho cảnh chưa làm, không giới hạn cảnh động tác; giữ từ khóa chỉnh tay và cảnh đã dựng/dở.
- Kiểm thử nhiều chủ đề, kịch bản khác và tính ổn định khi mở lại nhiều lần.

## 0.2.7

- Sửa nhận nhầm “động tác” thành “tắc”, dùng ranh giới từ và cụm tắc mạch rõ nghĩa; thêm cảnh tập tại nhà.
- Khi mở lại, sửa từ khóa huyết khối bị gán sai ở cảnh chưa dựng; giữ cảnh đã xong, cảnh dở và từ khóa người dùng chỉnh.
- Tìm thêm kết quả stock và chờ tải trước khi dừng do hết clip chưa dùng; không tự thử lại thao tác chèn.

## 0.2.6

- Thêm nút Cập nhật tiện ích ngay trên popup SKST: nạp bản đi kèm ứng dụng đã cập nhật từ GitHub, giữ mã kết nối và không gỡ/cài lại.
- Đọc phiên bản gói từ ứng dụng thay vì phụ thuộc bản manifest có thể bị trình duyệt lưu đệm; chặn cập nhật khi đang dựng, đổi quyền hoặc hạ phiên bản.
- Bản popup cũ cần bấm Tải lại ở trang quản lý tiện ích một lần để hiện nút mới. Tiện ích phải trỏ tới TienIch_Canva cạnh ứng dụng.

## 0.2.5

- Sửa lỗi dừng sau hai cảnh: nút Thêm chuyển cảnh nằm cố định giữa các cảnh không còn bị nhận nhầm là bảng nổi phải đóng.
- Giữ nguyên tiến độ, tiếp tục từ cảnh chưa làm; thêm kiểm thử cho nút cố định, popup nhiều mục và hộp thoại.

## 0.2.4

- Tích hợp rõ cập nhật ứng dụng và tiện ích trong một quy trình GitHub; phát hành thêm gói `SKST_Canva_Extension.zip` riêng.
- Tiện ích tự nhận tệp mới đã được ứng dụng tải và kiểm tra, rồi tự nạp lại khi đang rảnh; không tự nạp lại giữa tác vụ hoặc khi có quyền mới cần xác nhận.
- Thêm nút kiểm tra thư mục tiện ích mà Chrome/Cốc Cốc/Edge đang nạp, để phát hiện bản cũ ở thư mục khác.
- Cần cài bản 0.2.4 vào thư mục cố định một lần để bắt đầu dùng cơ chế tự nạp lại. Không cài ngầm hoặc sửa chính sách bảo mật trình duyệt.

## 0.2.3

- Kết nối Canva tự gắn lại bộ dựng vào đúng tab đang mở sau khi cài/cập nhật tiện ích.
- Xác nhận tín hiệu từ tab trước khi cho Bắt đầu; báo rõ sai tab, tiện ích cũ hoặc chưa kết nối.
- Dừng có thông báo sau 25 giây mất tín hiệu thay vì chờ im lặng; giữ nguyên tiến độ.
- Ghi chẩn đoán kết nối không chứa mã ghép nối vào Data/connection.json.
- Tiện ích thêm quyền scripting chỉ trên Canva để gắn lại bộ dựng; không cần mở lại toàn bộ trình duyệt.

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

