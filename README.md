# SKST Canva Studio

Ứng dụng Windows dựng video từ voice và kịch bản, dùng toàn bộ loại video/ảnh/mô phỏng trong kho Canva theo đúng từ khóa qua tiện ích trình duyệt. Giao diện tiếng Việt, cắt cảnh ngắn, ưu tiên tránh trùng trong từng dự án, cho phép dùng lại khi thiếu tư liệu phù hợp và lưu tiến độ. Đây vẫn là **bản thử**, tối đa 50 cảnh/thiết kế; việc điều khiển Canva trọn quy trình chưa được kiểm thử đầy đủ.

**[Tải bản Windows mới nhất](https://github.com/taikhoanzaizai-ux/canva/releases/latest)** · **[Các thay đổi](CHANGELOG.md)**

## Cài và sử dụng

1. Tải `SKST_Canva_Studio_Windows.zip` trong Releases và giải nén toàn bộ.
2. Mở `SKST Canva Studio.exe`.
3. Cài thư mục `TienIch_Canva` dưới dạng tiện ích đã giải nén trong Chrome, Cốc Cốc hoặc Edge. Tải lại tab Canva.
4. Trong ứng dụng, chọn **Kết nối & công cụ → Sao chép mã**. Dán mã vào tiện ích SKST và bật kết nối.
5. Chọn voice/kịch bản, phân tích, duyệt từ khóa rồi dán link một thiết kế Video 16:9 **trống** để dựng.

Từ **0.8.0**, máy mới tự tải bộ nhận diện CPU và mô hình tiếng Việt khi bấm Phân tích lần đầu (cần Internet, khoảng 152 MB). Không cần cài Python/Whisper. Các lần sau dùng lại ngoại tuyến. Có thể giữ cấu hình Python cũ hoặc nhập JSON/SRT. FFmpeg/FFprobe có trong ZIP Windows đầy đủ. Voice không gửi ra ngoài; bộ nhận diện/mô hình/tệp tải về đều nằm trong Data cạnh EXE.

Voice mẫu riêng tư không được đưa lên GitHub. Người đã cài gói cũ vẫn giữ được voice mẫu trên máy; khi cài mới có thể chọn voice của mình.

**Chuyển từ 0.7.x lên 0.8.0:** tải ZIP Windows đầy đủ một lần để thêm thư viện C++ app-local. Đóng ứng dụng, giải nén vào thư mục cũ và giữ Data. Bộ cập nhật cũ chưa cho phép tên DLL mới; các lần sau cập nhật bình thường.

## Cập nhật ngay trong ứng dụng

Từ **0.2.0**, bấm **Kiểm tra cập nhật** ở góc trên phải. Ứng dụng kiểm tra GitHub Releases, tải gói `SKST_Canva_Studio_Update.zip`, đối chiếu SHA-256 do GitHub cung cấp, rồi đóng và mở lại sau khi cài. Bản cũ được sao lưu; bản mới không khởi động được sẽ phục hồi bản trước.

Cấu hình, tiến độ, voice đã cắt, log, cache, file tạm và bản cập nhật nằm trong **`Data` cạnh EXE**, trên đúng ổ bạn giải nén. Thư viện chạy ở `_internal`, không bung vào Temp ổ C. Tệp voice và công cụ có sẵn được giữ khi cập nhật.

Từ **0.2.4**, nút **Cập nhật ứng dụng + tiện ích từ GitHub** tải cả EXE và `TienIch_Canva`. Tiện ích đọc phiên bản manifest cục bộ, tự nạp lại khi đang rảnh, rồi gắn bộ dựng trở lại. Không tải/eval JavaScript từ GitHub trong trình duyệt. Nếu quyền thay đổi, Chrome vẫn cần bạn xác nhận; đang dựng thì hoãn nạp lại.

**Cài lần đầu một lần:** dùng `TienIch_Canva` cạnh EXE làm thư mục cố định. Có thể tải riêng `SKST_Canva_Extension.zip` từ Releases. Trong Kết nối & công cụ, nút **Kiểm tra tiện ích Chrome đang dùng** chỉ rõ đường dẫn đăng ký cũ nếu trình duyệt đang dùng bản khác. Ứng dụng không tự sửa Chrome Preferences hoặc cài ngầm tiện ích. Các bản trước 0.2.4 cần cài bản tiện ích này một lần để có cơ chế tự nạp lại.

**Chuyển từ 0.2.0 trở xuống lên 0.2.1:** tải `SKST_Canva_Studio_Windows.zip` đầy đủ, giải nén trên ổ muốn dùng và giữ nguyên `_internal`. Đây là lần chuyển cấu trúc nên không dùng gói Update cũ. Các lần sau dùng nút cập nhật trong bản portable. Dữ liệu AppData cũ được sao chép sang `Data` nếu chưa có dự án portable; bản gốc được giữ dự phòng.

Tệp MP4 tải từ Canva dùng thư mục tải xuống của trình duyệt. Để lưu MP4 cùng ổ, chọn thư mục tải xuống của trình duyệt trên ổ đó. Ứng dụng không thay đổi thư mục hồ sơ hoặc thiết lập của trình duyệt.

Sau khi chuyển sang bản portable, dùng nút trong ứng dụng cho các bản tiếp theo. Không cập nhật trong lúc đang dựng hoặc nhận diện voice.

## Phát triển và phát hành

Kho chính thức để sửa mã: `https://github.com/taikhoanzaizai-ux/canva`.

- Python 3.11+ với Tk: `python launch.py`.
- Kiểm thử: `python -m unittest discover -s tests -v` và `node tests/test_adapter.cjs`.
- Đóng gói Windows: cài `pyinstaller==6.16.0`, chạy `python scripts/build_release.py`.
- Với sửa đổi mới, tăng `VERSION` trong `canva_studio/core.py`, cập nhật `CHANGELOG.md`, push lên `main`. GitHub Actions kiểm thử, đóng gói, kiểm tra EXE và tạo Release theo phiên bản nếu chưa tồn tại. Chỉ Release đã phát hành mới được nhận làm cập nhật.
- Không commit voice, video, dự án, mã ghép nối hoặc khóa truy cập. Xem [AGENTS.md](AGENTS.md).

Gói cập nhật kiểm tra phiên bản mới, miền tải GitHub, checksum, đường dẫn ZIP, sao lưu/phục hồi và giữ tệp người dùng. Kiểm tra EXE xác nhận ô mã không bị mất sau thu gom bộ nhớ, sao chép đúng và có nút cập nhật. Những kiểm tra này không thay thế kiểm thử trực tiếp chọn cảnh và timeline trong Canva.

Ứng dụng độc lập, không phải sản phẩm của Canva. Không sử dụng API nội bộ, không đọc mật khẩu/cookie, không vượt quyền tài khoản. Chọn hình hiện dựa trên mô tả stock; hãy duyệt hình trước khi dùng bản xuất.
