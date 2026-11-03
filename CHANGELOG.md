# Các bản cập nhật

## 0.8.0

- Cài máy mới bằng ZIP Windows đầy đủ. Máy đang dùng 0.7.x cần tải ZIP Windows đầy đủ một lần để thêm DLL C++; giữ Data, không dùng gói Update của bộ cập nhật cũ cho lần chuyển này.

- Máy Windows mới tự tải và thiết lập bộ nhận diện CPU whisper.cpp cùng mô hình đa ngôn ngữ khi Phân tích lần đầu; không cần cài Python/Whisper thủ công. Vẫn dùng được cấu hình Python cũ hoặc JSON/SRT.
- Tệp tải từ bản phát hành chính thức và kho mô hình gốc, đối chiếu SHA-256 cố định, giải nén theo danh sách cho phép. Tải lại khi lỗi không ghi đè tệp đã xác minh.
- Bộ chạy, mô hình, tải về, bộ nhớ tạm đều nằm trong Data cạnh ứng dụng; nhận diện voice trên máy, hiện tiến độ tải, dùng lại ngoại tuyến sau lần thiết lập đầu.
- Đóng gói các DLL C++ cần thiết theo hình thức app-local để máy mới không phải tự cài Visual C++ Runtime. Bộ cập nhật chỉ cho phép thêm đúng tên DLL đã kiểm tra.
- Chuyển mốc từ tiếng Việt từ kết quả native, ghép lại token UTF-8 bị tách để giữ dấu tiếng Việt và thời gian chia cảnh.

## 0.7.1

- Thẻ báo lỗi chuyển sang ảnh PNG nền đen/chữ trắng, chèn qua mục Hình ảnh tải lên; không phụ thuộc mục Video tải lên đang lỗi. Dự án cũ có thẻ lỗi MP4 tự tạo lại PNG khi tiếp tục.
- Tải clip tiêu đề trước khi chờ mục Video xuất hiện, tránh vòng chờ thư viện chưa có video.
- Giữ thời lượng thẻ lỗi theo voice và chỉ xác nhận xong khi thẻ đã chèn đúng timeline.

## 0.7.0

- Bổ sung mã phím Enter/Escape cho sự kiện bàn phím để Canva nhận xác nhận thời lượng thay vì chỉ đổi giá trị ô nhập.
- Khi cảnh cuối đã chèn bị lỗi: kiểm tra số cảnh và mốc bắt đầu, gỡ riêng cảnh đó bằng menu cảnh, xác nhận mốc timeline cũ rồi tự chèn thẻ báo lỗi đúng thời lượng và tiếp tục. Lưu checkpoint trước/sau gỡ để không xóa lặp.
- Nếu không xác nhận được cảnh cuối hoặc thao tác gỡ thất bại, vẫn báo rõ lỗi phục hồi; không tuyên bố đã dựng qua một khoảng voice chưa có hình.

## 0.6.2

- Xác nhận thời lượng ảnh bằng rời ô nhập, chờ Canva thực sự cập nhật; tiếp tục được khi popover thời lượng đang mở. Bù sai số làm tròn vào cuối cảnh để không cộng dồn lệch voice.
- Đọc cuối track hình bằng nút thêm cảnh, không cuộn tới cuối voice dài làm toàn bộ hình rơi khỏi vùng timeline đang hiển thị.

## 0.6.1

- Cho phép chuyển sang thẻ lỗi khi kẹt ở tải clip tiêu đề, trước khi có ý định chèn timeline; giữ 27 cảnh trước và voice trong trường hợp cảnh 28 tải tiêu đề thất bại. Tệp upload dư không được tính thành cảnh đã dựng.

## 0.6.0

- Lỗi ở cảnh chưa chèn mặc định tạo clip nền đen ghi số cảnh, mốc voice và lỗi cụ thể, giữ đúng thời lượng rồi tiếp tục; không đánh dấu xong khi thẻ chưa được xác nhận trên timeline.
- Ghi lỗi theo phần/cảnh/bước tại Data/Errors.json và thêm nút Xem danh sách lỗi dựng trong Kết nối & công cụ.
- Thay thông báo chờ Canva chung chung bằng tên ô/nút đang chờ và thời gian chờ; hiển thị lỗi kết nối ngay trên Canva.
- Tôn trọng Tạm dừng. Nếu cảnh đã chèn dở, voice/mốc timeline chưa xác nhận, hoặc chính thẻ lỗi không chèn được, báo rõ và giữ tiến độ thay vì chèn trùng hoặc bỏ mất khoảng voice.

## 0.5.1

- Sửa vòng chờ khi tab Canva chạy tiện ích cũ nhưng ứng dụng đang mở thiết kế: chuyển sang trạng thái nghỉ an toàn cho tiện ích tự nạp bản đã cập nhật, rồi nối lại đúng tab/marker và tiến độ. Tạm dừng thủ công vẫn được tôn trọng.

## 0.5.0

- Khi thiếu video phù hợp, tìm ảnh stock Canva với cùng điều kiện chủ thể/hành động và chống trùng; cắt ảnh theo thời lượng cảnh, giữ tiến độ đã dựng.
- Thử trang công khai Pexels/Pixabay không cần khóa API; chỉ nhận trang tư liệu gốc và máy chủ media chính thức, bỏ quảng cáo ngoài nguồn, lưu nguồn/giấy phép tại Data/Sources.json.
- Nguồn trả 401/403/429 được bỏ qua, không vượt chặn. Nếu không có tư liệu phù hợp, tạo thẻ nền đen ghi đúng lời đọc thay vì dừng bài hoặc chọn hình sai.
- Chuẩn bị tư liệu ở nền, duy trì kết nối và kiểm tra tạm dừng để không gây treo trong lúc tải/chuyển đổi.

## 0.4.1

- Sửa dừng ngay sau tải voice vì câu chào “Quý vị thân mến” bị đánh dấu thiếu ngữ cảnh. Lời dẫn dùng cảnh người giới thiệu; các đoạn cắt theo dấu phẩy được xét cùng câu đầy đủ.
- Khi thư mục voice có đúng một DOCX, tự đối chiếu kịch bản để sửa chữ nhận diện sai ở cảnh chưa dựng; giữ nguyên mốc thời gian, cảnh xong và voice đã tải. Nếu có nhiều kịch bản, không tự đoán.
- Xóa cờ chặn cũ khi đã tìm được chủ đề cụ thể; cập nhật lại từ khóa do phần mềm sinh, giữ từ khóa người dùng tự chỉnh.
- Hiện lý do tạm dừng ngay trên Canva để phân biệt lỗi/chờ với treo; thông báo tự ẩn khi tiếp tục.
- Giữ voice và tiến độ đã lưu, không cần phân tích hay tải voice lại cho bản sửa này.

## 0.4.0

- Nhận tiêu đề mục đánh số từ kịch bản, đối chiếu mốc voice; tạo clip nền đen, chữ trắng hiện dần khoảng 3 giây. Cảnh tiêu đề thay đúng khoảng hình đã có, không kéo dài/lệch voice, vẫn tính trong giới hạn 50 cảnh.
- Tạo và tải clip tiêu đề lên Canva bằng luồng Tải lên riêng; không chọn stock cho tiêu đề. Chữ được ghép trong clip MP4, không phải hộp chữ chỉnh sửa trên Canva.
- Từ khóa ưu tiên chủ thể/hành động/triệu chứng trong câu và ngữ cảnh mục/câu liền kề; thêm điều kiện khớp chủ thể để loại cảnh người cao tuổi chung chung. Câu chưa đủ ngữ cảnh được đánh dấu cần kiểm tra.
- Sửa dừng khi Canva rút gọn/thay đổi tiêu đề kết quả tìm kiếm: kiểm tra ô nhập, trạng thái tải và lưới kết quả; chỉ tự thử lại thao tác tìm kiếm, không chèn lại cảnh chưa xác nhận.
- Khi mở dự án cũ, chỉ cải thiện từ khóa cảnh chưa làm; không chèn lại/sửa cảnh đã dựng. Muốn thêm đầy đủ cảnh chuyển mục, nạp kịch bản và phân tích lại trên thiết kế mới.

## 0.3.3

- Bỏ qua dấu nghỉ rỗng có thời lượng bằng 0 do Whisper tạo, không hủy cả bài; không đổi mốc lời đọc xung quanh. Vẫn chặn đoạn có lời nhưng thời lượng bằng 0, mốc âm/không hữu hạn và chồng lấn thực sự.
- Báo rõ số đoạn và mốc thời gian nếu dữ liệu thực sự sai.
- Dùng lại kết quả nhận diện cục bộ khi tệp WAV đã giải mã khớp từng byte và JSON hợp lệ, tránh nhận diện lại toàn bài sau lỗi chia cảnh. Không sửa bản nhận diện gốc.

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

