# SKST Canva Studio

Ứng dụng Windows dựng video từ voice và kịch bản, dùng kho stock Canva qua tiện ích trình duyệt. Giao diện tiếng Việt, cắt cảnh ngắn, tránh dùng lại stock và lưu tiến độ. Đây vẫn là **bản thử**, tối đa 50 cảnh/thiết kế; việc điều khiển Canva trọn quy trình chưa được kiểm thử đầy đủ.

**[Tải bản Windows mới nhất](https://github.com/taikhoanzaizai-ux/canva/releases/latest)** · **[Các thay đổi](CHANGELOG.md)**

## Cài và sử dụng

1. Tải `SKST_Canva_Studio_Windows.zip` trong Releases và giải nén toàn bộ.
2. Mở `SKST Canva Studio.exe`.
3. Cài thư mục `TienIch_Canva` dưới dạng tiện ích đã giải nén trong Chrome, Cốc Cốc hoặc Edge. Tải lại tab Canva.
4. Trong ứng dụng, chọn **Kết nối & công cụ → Sao chép mã**. Dán mã vào tiện ích SKST và bật kết nối.
5. Chọn voice/kịch bản, phân tích, duyệt từ khóa rồi dán link một thiết kế Video 16:9 **trống** để dựng.

Nhận diện voice cần môi trường Python có `openai-whisper` và mô hình `.pt` trên máy; có thể nhập Whisper JSON/SRT thay thế. FFmpeg/FFprobe có trong gói Windows đầy đủ. Không gửi voice đến dịch vụ AI bên ngoài.

Voice mẫu riêng tư không được đưa lên GitHub. Người đã cài gói cũ vẫn giữ được voice mẫu trên máy; khi cài mới có thể chọn voice của mình.

## Cập nhật ngay trong ứng dụng

Từ **0.2.0**, bấm **Kiểm tra cập nhật** ở góc trên phải. Ứng dụng kiểm tra GitHub Releases, tải gói `SKST_Canva_Studio_Update.zip`, đối chiếu SHA-256 do GitHub cung cấp, rồi đóng và mở lại sau khi cài. Bản cũ được sao lưu; bản mới không khởi động được sẽ phục hồi bản trước.

Cấu hình và tiến độ nằm ở `%LOCALAPPDATA%\SKST Canva Studio`, tách khỏi thư mục cài. Tệp voice, thư mục công cụ và dữ liệu có sẵn không bị xóa bởi bản cập nhật. Khi tiện ích được sửa, tải lại tiện ích trong trang quản lý tiện ích và tải lại tab Canva.

**Bản 0.1.x chưa có nút cập nhật:** thay EXE bằng bản 0.2.0 một lần. Sau đó dùng nút trong ứng dụng cho các bản tiếp theo. Không cập nhật trong lúc đang dựng hoặc nhận diện voice.

## Phát triển và phát hành

Kho chính thức để sửa mã: `https://github.com/taikhoanzaizai-ux/canva`.

- Python 3.11+ với Tk: `python launch.py`.
- Kiểm thử: `python -m unittest discover -s tests -v` và `node tests/test_adapter.cjs`.
- Đóng gói Windows: cài `pyinstaller==6.16.0`, chạy `python scripts/build_release.py`.
- Với sửa đổi mới, tăng `VERSION` trong `canva_studio/core.py`, cập nhật `CHANGELOG.md`, push lên `main`. GitHub Actions kiểm thử, đóng gói, kiểm tra EXE và tạo Release theo phiên bản nếu chưa tồn tại. Chỉ Release đã phát hành mới được nhận làm cập nhật.
- Không commit voice, video, dự án, mã ghép nối hoặc khóa truy cập. Xem [AGENTS.md](AGENTS.md).

Gói cập nhật kiểm tra phiên bản mới, miền tải GitHub, checksum, đường dẫn ZIP, sao lưu/phục hồi và giữ tệp người dùng. Kiểm tra EXE xác nhận ô mã không bị mất sau thu gom bộ nhớ, sao chép đúng và có nút cập nhật. Những kiểm tra này không thay thế kiểm thử trực tiếp chọn cảnh và timeline trong Canva.

Ứng dụng độc lập, không phải sản phẩm của Canva. Không sử dụng API nội bộ, không đọc mật khẩu/cookie, không vượt quyền tài khoản. Chọn hình hiện dựa trên mô tả stock; hãy duyệt hình trước khi dùng bản xuất.
