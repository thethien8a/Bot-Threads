# Bot-Threads

Bot bình luận tự động trên Threads được xây dựng trên `nodriver`. Bot đăng nhập vào Threads, cuộn feed theo thứ tự, lọc bài đăng bằng Google Gemini, và đăng bình luận với tốc độ giống con người để giảm nguy cơ phát hiện bot.

## Tính năng

- **Điều khiển trình duyệt Nodriver**: khởi chạy một phiên bản Chromium có khả năng chống phát hiện bot tốt hơn undetected_chromedriver.
- **Cấu hình dựa trên môi trường**: tên người dùng, mật khẩu, độ trễ, bình luận, lời nhắc, và khóa API Gemini được lấy từ biến môi trường.
- **Cổng kiểm soát dựa trên AI**: mỗi bài đăng được phân tích qua Gemini 2.5 Flash bằng lời nhắc có thể cấu hình; chỉ những bài đăng tạo ra phản hồi `True` mới được bình luận.
- **Bình luận tuần tự**: bot xử lý một bài đăng tại một thời điểm với logic thử lại và không bao giờ vượt quá `COMMENT_TIMES` bình luận thành công.
- **Tương tác giống con người**: thời gian dừng ngẫu nhiên, tốc độ gõ, tạm dừng, và thời gian nghỉ ngơi để mô phỏng hành vi con người và điều chỉnh hoạt động sau lỗi.
- **Bộ chọn linh hoạt**: nút trả lời và gửi được kích hoạt qua các phần tử tương tác cha mẹ để xử lý các biểu tượng chỉ SVG.

## Cấu trúc dự án

```
bot.py             # Logic cốt lõi của bot và các hàm trợ giúp hành vi giống con người
config.py          # Trình tải cấu hình dựa trên môi trường
env.example        # Mẫu tham chiếu .env
main_nodriver.py   # Điểm nhập ứng dụng (đăng nhập + chạy bot)
requirements.txt   # Các phụ thuộc Python
```

## Điều kiện tiên quyết

- Python 3.11+ (dự án được phát triển/kiểm tra với virtualenv được đóng gói chạy Python 3.12).
- Tài khoản Threads mà bạn được phép tự động hóa.
- Hai khóa API Google Gemini (bot xoay vòng giữa chúng trên mỗi phân tích).
- Chromium/Chrome tương thích với `nodriver`.

## Cài đặt

```bash
python -m venv .venv
. .venv/Scripts/activate      # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

> Kho lưu trữ đã được cung cấp với thư mục `venv/`. Bạn có thể tái sử dụng nó hoặc xóa và tạo lại môi trường ảo mới bằng các bước trên.

## Cấu hình

Tạo file `.env` (sử dụng `env.example` làm mẫu):

```
THREADS_USERNAME=tên_người_dùng_threads_của_bạn
THREADS_PASSWORD=mật_khẩu_threads_của_bạn
COMMENT_TIMES=10
COMMENTS=Xin chào!|Bài đăng hay!|Những hiểu biết tuyệt vời!
COMMENT_DELAY_MIN=2.0
COMMENT_DELAY_MAX=5.0
PROMPT_ENGINEERING=Lời hướng dẫn Gemini của bạn ở đây; trả về True khi an toàn
GG_API_KEY_1=gemini-key-1
GG_API_KEY_2=gemini-key-2
```

Lưu ý quan trọng:

- `COMMENTS` là chuỗi thô. Việc triển khai hiện tại **không** tách nó tự động; cập nhật `config.py` hoặc cung cấp bộ chọn tùy chỉnh nếu bạn cần hành vi danh sách thực sự. Mẫu trên giả định bộ chọn sẽ được mở rộng để tách bằng dấu ống (`|`).
- `COMMENT_DELAY_MIN` và `COMMENT_DELAY_MAX` kiểm soát tạm dừng cơ bản giữa các bình luận thành công. Độ nhiễu bổ sung (0.8–2.0 giây) được tiêm vào.
- `PROMPT_ENGINEERING` nên hướng dẫn Gemini trả lời bằng chuỗi chứa `True` khi bài đăng nên được bình luận, hoặc bất kỳ thứ gì khác để bỏ qua.
- `GG_API_KEY_*` phải có quyền truy cập vào mô hình `gemini-2.5-flash` qua API Generative AI của Google.

## Chạy Bot

```bash
python main_nodriver.py
```

Luồng thực thi:

1. Tải biến môi trường vào `CommentConfig`.
2. Khởi chạy trình duyệt `nodriver` (`headless=False`).
3. Mô phỏng nhập thông tin đăng nhập và đăng nhập vào Threads với tốc độ gõ giống con người.
4. Khởi tạo `ThreadsCommentBot` và chạy vòng lặp bình luận tuần tự.
5. Chờ đầu vào của người dùng trước khi tắt trình duyệt (lời nhắc an toàn).

## Pipeline hành vi

1. **Thu thập bài đăng**: `collect_posts` thu thập các bài đăng hiển thị trên feed.
2. **Phân tích**: `analyze_post` cuộn đến bài đăng, chờ 1.5–3.5 giây, trích xuất văn bản, gọi Gemini với lời nhắc, và mong đợi mô hình trả về chuỗi chứa `True` để phê duyệt bình luận.
3. **Bình luận**: `process_post` mở hộp trả lời, gõ bình luận đã chọn từng ký tự một (độ trễ 50–150 ms), và gửi qua phần tử tương tác cha mẹ của nút.
4. **Tạm dừng & thử lại**: sau mỗi thành công, tạm dừng cho `random_pause()` (độ trễ cơ bản + độ nhiễu). Lỗi kích hoạt lên đến ba lần thử lại với thời gian nghỉ ngơi 6–12 giây.
5. **Cuộn**: sau khi hoàn thành lô hiện tại, bot cuộn 1200–1800 pixel và nghỉ ngơi 2.0–3.5 giây trước khi thu thập bài đăng lại.

## Tùy chỉnh hành vi

- **Logic lời nhắc**: điều chỉnh `PROMPT_ENGINEERING` để thực thi các quy tắc lọc khác nhau. Đảm bảo phản hồi của Gemini rõ ràng chứa `True` hoặc bot sẽ bỏ qua bài đăng.
- **Điều chỉnh giống con người**: điều chỉnh phạm vi độ trễ trong `config.py` hoặc các phương thức trợ giúp (`observe_post`, `type_like_human`, `random_pause`, `cooldown_after_failure`) để cân bằng tốc độ và tính ẩn.
- **Lựa chọn bình luận**: mở rộng `CommentConfig.pick_comment()` để phân tích định dạng mong muốn (ví dụ: tách bằng `|`, đọc từ JSON, hoặc tải từ file) và trả về một chuỗi duy nhất cho mỗi bình luận.
- **Bộ chọn**: cập nhật bộ chọn CSS trong `bot.py` nếu Threads thay đổi DOM của nó.

## Giám sát & Ghi nhật ký

- Nhật ký được phát ra qua mô-đun `logging` tiêu chuẩn ở mức INFO theo mặc định.
- Theo dõi các thông báo như `Không tìm thấy nút reply` hoặc `Submit SVG click fallback...` để chẩn đoán sự cố bộ chọn.
- Phản hồi Gemini không được ghi nhật ký trực tiếp để tránh rò rỉ nội dung nhạy cảm; thêm ghi nhật ký thận trọng nếu bạn cần kiểm tra sâu hơn.

## Khắc phục sự cố

| Vấn đề | Hành động đề xuất |
|--------|-------------------|
| Đăng nhập thất bại | Xác minh thông tin đăng nhập, xác nhận bộ chọn UI, hoặc tăng thời gian ngủ trước khi gõ. |
| Lỗi Gemini | Kiểm tra hạn ngạch khóa API, kết nối mạng, hoặc tính khả dụng của mô hình. |
| Bot bỏ qua bài đăng | Lời nhắc có lẽ trả về chuỗi không có `True`; điều chỉnh từ ngữ lời nhắc. |
| Phát hiện là bot | Tăng độ trễ, thêm tính ngẫu nhiên hành vi hơn, hoặc hạn chế tổng số bình luận mỗi phiên. |
| `COMMENTS` chọn ký tự đơn | Cập nhật `CommentConfig.pick_comment()` để tách chuỗi thành danh sách trước khi gọi `random.choice`. |

## Đạo đức & Tuân thủ

- Tuân thủ Điều khoản dịch vụ của Meta/Threads và quy định địa phương. Tự động hóa hành động người dùng có thể vi phạm chính sách nền tảng và có thể dẫn đến cấm tài khoản.
- Sử dụng tài khoản thử nghiệm hoặc được phê duyệt bất cứ khi nào có thể. Xem xét giới hạn tốc độ bot và thêm điểm kiểm tra xem xét thủ công cho việc sử dụng sản xuất.

## Cải tiến tương lai

- Phân tích `COMMENTS` thành danh sách có cấu trúc (JSON hoặc dựa trên dấu phân cách) để hỗ trợ nhóm bình luận phong phú hơn.
- Lưu trữ các định danh bài đăng đã xử lý để tránh trùng lặp qua các lần chạy.
- Thêm kiểm tra đơn vị/tích hợp một khi bot được ổn định; hiện tại dự án dựa vào xác minh thủ công đầu cuối.
- Tham số hóa lựa chọn mô hình hoặc chuyển sang heuristic cục bộ khi Gemini không khả dụng.

---

**Danh sách kiểm tra xác minh trước các lần chạy sản xuất**

1. Xác nhận biến `.env` được đặt và hợp lệ.
2. Khởi chạy với `COMMENT_TIMES` thấp (ví dụ: 1–2) để xác thực thông tin đăng nhập và bộ chọn.
3. Xem xét nhật ký cho bài đăng bị bỏ qua hoặc lỗi lặp lại.
4. Tăng giới hạn dần dần trong khi giám sát các kích hoạt chống bot.
