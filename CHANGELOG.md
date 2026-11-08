# Các bản cập nhật

## 0.14.19

- Đặt chữ báo lỗi tại clip thay thế và kiểm tra hai đầu của chữ trên timeline. Nếu chữ dài hơn clip hoặc nằm lệch, thử căn lại; nếu chưa xác nhận được, báo để kiểm tra thay vì chèn thêm chữ chồng lên nhau.

## 0.14.18

- Khi thiếu video khớp chủ đề, tìm lại từ khóa đầu và chọn ngẫu nhiên clip đủ dài ở các hàng dưới, ưu tiên clip chưa dùng.
- Thêm chữ báo cảnh dùng video thay thế và ghi trạng thái trong SKST. Nếu tìm thiếu tư liệu, báo để duyệt cảnh thay vì tạo thẻ chữ dự phòng.

## 0.14.17

- Thêm nút Dựng phần tiếp theo khi cảnh cuối đang kẹt và còn phần voice khác. Giữ thiết kế cũ và quay lại xác nhận cảnh cuối trước khi tải MP4.

## 0.14.16

- Tự thử căn cảnh cuối theo điểm kết thúc voice khi xác nhận cảnh đã sửa và khi kiểm tra cả phần. Giữ mốc voice gốc khi đối chiếu.
- Đồng nhất dung sai của cảnh cuối với bước kiểm tra timeline để tránh chặn chuyển phần vì chênh lệch nhỏ.

## 0.14.15

- Dựng hết các phần voice trước khi tải MP4. Sau phần cuối, mở lại các thiết kế còn thiếu tệp xuất rồi ghép video hoàn chỉnh.
- Dự án đang dừng ở tải MP4 giữa chừng có thể chuyển sang phần dựng tiếp theo và giữ những tệp đã tải.

## 0.14.14

- Ghi nhớ lựa chọn AI, model và đường dẫn Antigravity. Khôi phục phiên ChatGPT đã lưu và tự gia hạn khi cần.
- Mã hóa phiên ChatGPT và khóa API bằng Windows. Thêm mục Dán khi bấm chuột phải vào ô khóa API.

## 0.14.13

- Xác nhận đúng nút tải MP4 trong bảng Canva và tiếp tục phiên tải đã theo dõi.
- Lưu MP4 từng phần rồi ghép hình theo thứ tự với voice gốc. Mở lại các phần đã dựng từ bản cũ nếu còn thiếu tệp xuất.

## 0.14.12

- Thêm nút × để đóng cảnh báo tạm dừng trong Canva. Cảnh báo đã đóng chỉ hiện lại khi có nội dung mới hoặc sau một lần chạy lại.

## 0.14.11

- Khi Canva giữ thời lượng khác dự kiến cho thẻ chữ đã chèn, kiểm tra vị trí và mốc timeline rồi tự bù chênh lệch vào các cảnh sau. Giữ điểm kết thúc của phần voice.

## 0.14.10

- Tải thẻ chữ và tiêu đề dưới dạng ảnh PNG, tránh bước xử lý video tiêu đề khiến Canva chờ lâu. Khi tiếp tục, xác nhận ảnh đã chèn và giữ mốc voice.
- Gửi yêu cầu cảnh tiếp theo ngay sau khi hoàn tất, đồng thời cho tác vụ đang chạy thêm thời gian giữ kết nối khi Chrome giảm tần suất xử lý tab.

## 0.14.9

- Với chủ đề ngoài bộ từ khóa, thử bỏ từ mô tả kiểu hình, thao tác và triệu chứng để tìm theo đối tượng chính. Áp dụng cả với cụm tìm do người dùng nhập.
- Xoa đầu, bóp đầu và đau đầu có thể dùng tư liệu vùng đầu. Giữ dấu tiếng Việt khi so khớp để phân biệt đầu với đau.

## 0.14.8

- Dùng bộ chủ đề chung để tìm tư liệu theo đối tượng chính cho cả từ khóa tự động và từ khóa nhập tay. Áp dụng cho thực phẩm, cơ quan, triệu chứng, vận động và các chủ đề đã có trong bộ từ khóa.
- Giữ truy vấn gốc và thử thêm từ khóa ngắn trước khi dùng thẻ chữ.

## 0.14.7

- Mở rộng gân cơ vùng lưng và đau lưng sang tư liệu vùng lưng, người ôm lưng hoặc cột sống, kể cả khi từ khóa được sửa bằng tay.
- Thử xác nhận lại thời lượng trên chính ảnh đã chèn nếu Canva chưa lưu sau khi rời ô nhập.

## 0.14.6

- Tìm thêm não bộ cho cảnh vi mạch não, não bộ hoặc đau ngực cho cảnh đột quỵ, và máy đo huyết áp cho cảnh máy đo vận tốc sóng mạch.
- Áp dụng cả với cảnh đã sửa từ khóa bằng tay. Dùng từ khóa đang nhập để xác định nhóm tư liệu liên quan.

## 0.14.5

- Đồng nhất ngưỡng kiểm tra điểm kết thúc ảnh với cảnh kế tiếp. Có thể tiếp tục từ ảnh báo lỗi đã chèn nếu điểm cuối lệch không quá 0,12 giây, kể cả khi Canva hiển thị thời lượng mặc định 5 giây.
- Xác nhận ảnh theo mốc của cảnh cuối khi Canva thay đổi số cảnh đang hiển thị trong lúc chỉnh thời lượng.

## 0.14.4

- Khi Canva báo không có video cho từ khóa đang tìm, chuyển ngay sang cụm tiếp theo. Ưu tiên video gần chủ đề trước khi thử ảnh và thẻ chữ.
- Mở rộng vi mạch sang mao mạch, mạch máu và hồng cầu, cầu thận sang giải phẫu thận, vi mạch não sang não bộ hoặc mạch máu.

## 0.14.3

- Khi xác nhận cảnh tự sửa hoặc hoàn tất một phần, cuộn đọc toàn bộ timeline Canva để đếm cả những cảnh ngoài màn hình. Khắc phục tình trạng cảnh 50 đã có nhưng bị báo thiếu cảnh, chặn mở phần voice tiếp theo.
- Áp dụng cách đếm bổ sung khi chèn và phục hồi cảnh. Chỉ chuyển phần sau khi xác nhận đủ cảnh và đúng mốc voice.

## 0.14.2

- Chấp nhận tư liệu Canva gần nghĩa ngay trong kết quả tìm kiếm. Ví dụ nước ép cam có thể dùng quả cam, xơ vữa có thể dùng mạch máu hoặc hồng cầu, elastin có thể dùng mô phỏng sợi đàn hồi.
- Cho phép lặp từ khóa giữa các cảnh. Ưu tiên video rồi ảnh chưa dùng, phân biệt tư liệu theo mã Canva và chỉ dùng lại khi thiếu lựa chọn phù hợp.
- Đọc cả thời lượng hiển thị dạng phút:giây trên thẻ video.

## 0.14.1

- Trước khi chèn thẻ chữ, tìm thêm tư liệu theo đối tượng chính và các tên gọi Canva thường dùng. Ví dụ độ cứng thành mạch có thể dùng mô phỏng động mạch, lòng mạch hoặc xơ vữa.
- Áp dụng cho cảnh chờ trong dự án cũ, kể cả khi AI chưa tạo từ khóa minh họa. Giữ điều kiện đủ thời lượng và tránh lặp.

## 0.14.0

- Thêm Gemini qua đăng nhập Google bằng Antigravity CLI. Dùng model và hạn mức của tài khoản đã đăng nhập trong công cụ Google.
- Chỉ gửi lời đọc khi CLI xác nhận chế độ quyền Strict. Kiểm tra kết quả từ khóa như các nguồn AI khác.

## 0.13.1

- Đưa nút khôi phục bản dựng và lối về Dựng video vào mục Từ khóa AI. Hướng dẫn khi chưa có cảnh và chỉ bật cập nhật từ khóa sau khi đã có danh sách cảnh.
- Ghi rõ Gemini kết nối bằng khóa tạo trong Google AI Studio và thêm nút mở đúng trang lấy khóa.

## 0.13.0

- Thêm Sign in with ChatGPT trong Từ khóa AI để tài khoản đủ điều kiện dùng lượt AI theo gói ChatGPT.
- Tải danh sách model từ tài khoản sau khi cấp quyền. Phiên đăng nhập giữ trong lần mở SKST hiện tại và có thể ngắt trong ứng dụng.

## 0.12.5

- Thêm nút khôi phục bản dựng Canva gần nhất trong Kết nối & công cụ, giữ phần đang dựng và cảnh chờ xác nhận.
- Chặn phân tích lại khi đang chờ xác nhận cảnh tự sửa. Lưu tiến độ khi bắt đầu dự án mới và xóa số cảnh chờ cũ khi thay danh sách.

## 0.12.4

- So khớp cụm chủ đề khi tiêu đề Canva đổi thứ tự từ, vẫn yêu cầu đủ từ của đối tượng.
- Tìm video và ảnh theo chủ đề chính trước. Với cảnh trích dẫn hoặc nội dung khó tìm trực tiếp, thử thêm từ khóa minh họa trước khi dùng thẻ chữ. AI có thể đề xuất từ khóa minh họa riêng khi phân tích.
- Phân biệt thẻ chữ dự phòng với cảnh đã chèn tư liệu trong bảng cảnh.

## 0.12.3

- Khi lời đọc nhắc đến nghiên cứu, chấp nhận tư liệu minh họa như nhà khoa học, phòng thí nghiệm, kính hiển vi hoặc bài báo khoa học dù tiêu đề Canva dùng cách gọi khác. Vẫn kiểm tra độ dài và tránh lặp tư liệu.

## 0.12.2

- Thêm GPT-6 Luna (tiết kiệm) và đặt làm model mặc định khi chọn OpenAI cho từ khóa.
- Báo rõ lỗi HTTP 429 của OpenAI khi phản hồi xác định được lỗi giới hạn tốc độ hoặc tín dụng/hạn mức API.

## 0.12.1

- Thêm danh sách chọn model trong Từ khóa AI, gồm GPT-6.1 Sol, GPT-6.1 Terra và nhiều lựa chọn Gemini. Có thể nhập mã model khác.
- Thêm nút Lấy khóa API ngay cạnh ô nhập khóa cho từng nhà cung cấp.

## 0.12.0

- Thêm mục Từ khóa AI với OpenAI (ChatGPT) và Google Gemini. Model đọc lời cảnh và câu kề, đề xuất đối tượng cụ thể và cụm tìm kiếm tiếng Việt, tiếng Anh.
- Dùng khi phân tích voice hoặc cập nhật cảnh chưa dựng ở phần hiện tại. Giữ mốc thời gian, cảnh đã dựng và từ khóa tự sửa. Nếu API không có kết quả hợp lệ, giữ từ khóa hiện có và đánh dấu để duyệt.
- Chế độ trên máy là mặc định. Khi chọn API, chỉ gửi văn bản. Khóa nhập trong ứng dụng chỉ dùng trong phiên mở phần mềm.

## 0.11.4

- Bám đúng đối tượng lời đọc: bổ sung các loại hạt, rau củ, trái cây, não, da và tim; tách dạ dày khỏi đường ruột, đi bộ khỏi thể dục/dưỡng sinh.
- Giữ từ khóa ngắn nhưng không dùng đối tượng khác thay thế (óc chó không thành hạt điều, nước ép không thành trái cây nguyên quả). Ưu tiên thực phẩm được nhắc trực tiếp trước câu mô tả lợi ích cho cơ quan.
- Cảnh cắt giữa câu kế thừa đúng đối tượng trong câu; cập nhật cảnh tự động chưa dựng, giữ nguyên cảnh đã dựng và từ khóa tự sửa.

## 0.11.3

- Rút gọn từ khóa theo chủ đề: mạch máu, đường huyết, người già thể dục… Chấp nhận tư liệu cùng chủ đề; hành động cụ thể chỉ được ưu tiên, không còn bắt buộc.
- Ưu tiên chủ đề trực tiếp trong lời đọc (cam, nước ép…) thay vì kéo dài ngữ cảnh mạch máu sang cảnh khác. Giữ hạn chế lặp trong cùng dự án.
- Tự cập nhật từ khóa tự động của cảnh chưa dựng khi mở lại dự án; giữ cảnh đã dựng và từ khóa người dùng tự sửa.

## 0.11.2

- Sửa đổi tên Canva: kích hoạt ô tên qua phần tử tiêu đề trên thanh trên (Canva dùng menuitem), chờ giá trị nhập được nhận rồi chuyển tiêu điểm để lưu; không gửi Enter ngay sau input.
- Xác nhận tên qua ô nhập và phần tiêu đề hiển thị, chấp nhận tiêu đề tab trình duyệt cập nhật chậm. Tên đã đúng thì giữ nguyên, không nhập lại.
- Nếu Canva chưa nhận tên sau các lần thử có giới hạn, báo cạnh ô tên và vẫn dựng tiếp; thử tên lại sau khi kiểm tra xong các cảnh. Không lặp bước đặt tên vô hạn hoặc tạo ảnh lỗi cho tác vụ đổi tên.

## 0.11.1

- Chấp nhận thời lượng tương đối khi người dùng tự sửa: giữ nguyên cảnh đã sửa, đọc lại các mốc thực tế rồi bù chênh lệch vào cảnh chưa dựng tiếp theo. Ví dụ 3–4–5 giây, cảnh đầu đổi thành 2 giây thì kế hoạch tiếp theo thành 2–5–5 giây.
- Nếu cảnh tự sửa dài hơn nhiều, phân bổ phần cần rút ngắn qua các cảnh chưa dựng, giữ cảnh dương thời lượng và tổng độ dài voice. Các cảnh đã dựng trên Canva được giữ nguyên, mốc trong bảng cập nhật theo thực tế.
- Lưu mốc voice ban đầu để nhiều lần tự sửa không làm cộng dồn sai số. Vẫn kiểm tra số cảnh, tính liên tục của timeline và đúng voice; không yêu cầu người dùng khớp từng phần trăm giây.

## 0.11.0

- Thêm cột Trạng thái và đánh dấu đỏ cảnh lỗi ngay trong bảng Cảnh/Thời gian, Lời đọc, Từ khóa Canva. Tự cuộn tới lỗi mới; chọn cảnh để xem lý do và mốc cần sửa. Giữ trạng thái lỗi khi ảnh báo lỗi đã được chèn, phân biệt với cảnh người dùng đã tự sửa.
- Cho chọn cảnh hoặc nhập số cảnh, mở đúng Canva để sửa sau khi tạm dừng. Nút Đã sửa trên Canva — tiếp tục gửi tác vụ chỉ kiểm tra, không chèn/cắt/xóa lại tư liệu người dùng.
- Chỉ xác nhận tự sửa khi có tư liệu đúng cảnh, đúng mốc đầu/cuối, số cảnh hợp lệ và voice gốc còn đủ thời lượng từ giây 0. Đạt yêu cầu thì đánh dấu đã tự sửa, giữ các cảnh hoàn tất và tiếp tục cảnh chưa xong; sai mốc thì báo cụ thể ngay trong phần mềm để sửa lại.
- Lưu yêu cầu kiểm tra và trạng thái tự sửa theo từng phần/dự án, khôi phục sau khi mở lại. Sửa cảnh cũ không xóa mốc thao tác của cảnh khác đang dở.
- Trong chế độ tự sửa, nút Bắt đầu / Tiếp tục thông thường cũng chuyển qua kiểm tra cảnh tự sửa; không quay lại chèn ảnh báo lỗi vào tư liệu người dùng đã thay.

## 0.10.3

- Sửa lưu thời lượng ảnh có nhiều chữ số thập phân: Canva cắt bớt chữ số thay vì làm tròn gần nhất. Phần mềm chủ động làm tròn tới 0,1 giây trước khi gửi, rồi kiểm tra mốc kết thúc với voice gốc; áp dụng chung cho ảnh stock và ảnh báo lỗi, mọi dự án.
- Giữ bù sai số theo mốc tuyệt đối ở cảnh kế tiếp, tránh sai số làm tròn cộng dồn. Ảnh đã đúng mốc được tiếp tục tại chỗ, không chèn lại.
- Đã thử thao tác trực tiếp trên Canva và thêm kiểm thử nhiều thời lượng ngắn/lẻ cùng chuỗi cảnh dài; chưa xác minh toàn bộ bài chạy tự động.

## 0.10.2

- Sửa dừng khi đặt thời lượng ảnh/ảnh báo lỗi: chờ React nhận giá trị, chuyển tiêu điểm sang nút thời lượng để lưu rồi đóng bằng chính nút đó; không gửi Enter ngay sau input, không bấm Áp dụng cho mọi trang.
- Xác nhận bằng mốc bắt đầu/kết thúc thực tế trên timeline thay vì chỉ nhãn thanh công cụ. Chấp nhận mức làm tròn 0,1 giây của Canva và bù sai số qua mốc tuyệt đối ở cảnh kế tiếp. Khi ảnh đã đúng thời lượng thì tiếp tục, không chèn lại.
- Đã thử trực tiếp thao tác đổi thời lượng ảnh báo lỗi trên Canva và đối chiếu mốc timeline; voice giữ nguyên. Chưa xác minh toàn bài chạy tự động.

## 0.10.1

- Thêm ô Tên dự án / tên trên Canva, lưu cùng tiến độ và khôi phục khi mở lại. Để trống thì giữ cách đặt tên mặc định của Canva.
- Tự đổi tên thiết kế trước khi dựng: tên gốc ở phần đầu, phần sau thêm .2, .3… vào tên gốc (ví dụ Bài 1, Bài 1.2, Bài 1.3). Không thêm .1 hoặc nối số lặp khi tiếp tục.
- Đổi tên dự án đang tạm dừng không xóa cảnh đã dựng, voice hoặc mốc thao tác đang dở; khóa ô tên khi đang chạy để tránh đổi nhầm giữa chừng.
- Kiểm tra ô nhập, tên lưu trên máy và quy tắc đánh số trong bản Windows đóng gói.

## 0.10.0

- Cảnh lỗi chuyển thành một ảnh PNG báo lỗi đúng mốc/thời lượng, sau đó hoàn tất cảnh và chuyển tiếp; không tìm lại tư liệu gốc. Khôi phục chèn dở bằng đối chiếu số cảnh và mốc timeline, chỉ gỡ đúng cảnh cần thay. Nếu toàn bộ thao tác Canva không phản hồi sau ba lần phục hồi thì báo rõ, không đánh dấu giả đã dựng.
- Tạo ảnh lỗi ngay trong tiện ích bằng canvas, không phụ thuộc FFmpeg/phông chữ ngoài; tự đo và co chữ vừa khung, giữ nguyên dấu phần trăm và chuỗi chẩn đoán dài.
- Tác vụ dự phòng lỗi được thử lại khi có yêu cầu mới; không tạo worker trùng trong lúc chờ. Giới hạn thời gian tìm/tải nguồn ngoài, chuyển đổi và kiểm tra tệp để tránh treo vô hạn.
- Tiêu đề tải thất bại được gửi lại khi chưa thấy tệp; không chèn lại nếu trạng thái chèn chưa được đối chiếu.
- Cho phép mọi kiểu tư liệu nhưng vẫn kiểm tra hành động; bổ sung hành động cụ thể như nhón gót, thức dậy, đi bộ, xoa bóp, hít thở, đo đường huyết. Áp dụng cả ảnh, video, tư liệu dùng lại và nguồn ngoài.
- Kiểm tra đúng tên voice theo nội dung tệp, mốc bắt đầu bằng 0 và biên kết thúc trước khi chuyển phần; xóa tên voice cũ khi đổi phần.
- Quyền downloads là tùy chọn, chỉ xin khi người dùng bấm nút trong tiện ích. Xác nhận đúng phiên tải MP4 Canva hoàn tất và tệp còn trên máy; kiểm tra tệp có hình, âm thanh, đúng thời lượng bằng FFprobe rồi mới báo hoàn thành. Tiếp tục phiên xuất dở không tự bấm xuất trùng.
- Do có quyền tùy chọn mới, cần tải lại tiện ích một lần trong trang Tiện ích của Chrome, sau đó bấm Cho phép kiểm tra tải MP4. Không cài bằng registry/chính sách, không thay quyền ngầm.

## 0.9.2

- Sửa dừng dựng khi lời đọc hoặc thẻ lỗi chứa dấu phần trăm: hiển thị chữ nguyên văn, không diễn giải thành lệnh FFmpeg. Áp dụng cho mọi dự án, tiêu đề và thẻ lỗi.
- Báo nguyên nhân FFmpeg thực tế thay vì chuỗi lệnh bị cắt; giới hạn thời gian tạo thẻ chữ để tránh treo vô hạn.

## 0.9.1

- Nhận cụm căng tức/bụng căng và biến thể nhận diện Bụ căng, tìm trực tiếp đầy hơi/chướng bụng thay vì đưa cả câu dài vào Canva.

- Đóng menu clip bằng chính nút Tùy chọn về trang đang mở thay vì chỉ phát Escape từ tiêu điểm ngoài menu. Khi cần Escape, đưa tiêu điểm vào menu trước.
- Sau khi chọn clip, đóng ngay menu do thao tác chọn mở ra; bỏ qua điều khiển liên kết đơn lẻ không chặn dựng. Không bấm lệnh Hủy liên kết.
- Giữ nguyên các tiêu chí tư liệu và chống trùng mềm của 0.9.0.

## 0.9.0

- Chống trùng mềm theo từng dự án: ưu tiên video/ảnh chưa dùng; nếu không có lựa chọn phù hợp khác, thử lại đúng từ khóa với tư liệu đã dùng, ưu tiên số lần ít và tránh lặp liền cảnh. Dự án mới xóa lịch sử này, các phần trong cùng bài giữ lịch sử chung.

- Bỏ giới hạn tư liệu phải có người thật: dùng video/ảnh/mô phỏng/3D/đồ vật/thực phẩm trong Canva khi khớp chủ thể của lời đọc. Không nới sang tư liệu khác chủ đề; vẫn ưu tiên tránh trùng và ưu tiên video.
- Từ khóa y khoa đi thẳng vào mạch máu/hồng cầu, đường huyết/máy đo, dạ dày/đường ruột/vi sinh, gan, thận, tim; không mặc định đổi mọi nội dung thành bác sĩ/người cao tuổi.
- Gộp mốc cảnh gần trùng do làm tròn, không sinh cảnh 0,001 giây. Dự án dở giữ ID/cảnh đã xong và thời lượng voice, mượn một phần thời gian cảnh kế để sửa cảnh quá ngắn.
- Đếm trực tiếp clip timeline thay vì nút thêm cảnh; suy mốc bắt đầu từ cảnh trước khi clip quá ngắn không có tay cắt. Chọn và đối chiếu cảnh cuối trước khi cắt, bù sai số cuối cảnh cho cả video và ảnh.
- Khôi phục trường hợp cũ đã thu nhầm cảnh trước thành 0,001 giây khi xác nhận được đúng ID/mốc; không yêu cầu phân tích lại toàn bài.

## 0.8.3

- Sửa bấm lại tab Tải lên đang chọn khiến Canva đóng bảng: kiểm tra aria-selected trước khi mở, dùng chung cho voice, clip tiêu đề và ảnh báo lỗi.
- Chỉ ghi insert_intent sau khi đã tìm thấy thẻ ảnh sẵn sàng chèn, tránh báo chèn dở khi chưa hề bấm ảnh.
- Đã đối chiếu trực tiếp hành vi đóng/mở Tải lên và chèn thẻ PNG đầu tiên trên Canva; không suy từ fixture sang xác nhận toàn quy trình.

## 0.8.2

- Thay cờ gắn bộ dựng cũ bằng phiên bản/phiên điều khiển; bản cập nhật không bị cờ cũ chặn, vòng lặp đã thay thế tự ngừng để tránh hai bộ dựng chạy cùng tab.

- Khi Canva chuyển từ trang tạo Video sang /edit bằng điều hướng SPA, tự gắn bộ dựng sau thay đổi URL hoặc tải xong, không phụ thuộc người dùng mở popup. Chỉ nhận đúng link dự án hoặc marker thiết kế mới.
- Khi Chrome khởi động lại, nối lại tab dự án đã có nếu tiện ích đã ghép nối; không tự tạo tab mới và không mở rộng quyền trình duyệt.

## 0.8.1

- Sửa mã lỗi 2 của bộ nhận diện khi thư mục cài/Data có dấu tiếng Việt: chạy trong thư mục công việc bằng đường dẫn Unicode của Windows, chỉ truyền tên nội bộ tương đối không dấu cho bộ native. Không đổi tên hoặc di chuyển voice gốc.
- Phép thử gói Windows nay dùng thư mục có dấu/khoảng trắng và tệp voice tên tiếng Việt, tránh bỏ sót lỗi máy mới.
- Thông báo mã 2 nêu rõ không mở được âm thanh nội bộ, kèm vị trí log.

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

