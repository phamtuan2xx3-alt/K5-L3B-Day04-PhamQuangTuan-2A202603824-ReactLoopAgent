# Ghi chú phân tích · Day 04

Họ và tên: Phạm Quang Tuấn
MSSV: 2A202603824

## 1. Case được chọn

- ID case: H1 — điều tra nhiều bước, theo liên kết incident GitHub rồi đối chiếu Cloudflare.
- Câu trả lời của agent: đã theo liên kết từ `h02n9572mx9y` tới `xr3myzj7ms51`, so sánh thời gian, component và nguồn với `yaa0witbl2me`; kết luận chưa có bằng chứng chung nguyên nhân. Bản đầy đủ nằm tại case H1, `result.answer` trong `eval_before.json`. Câu trả lời chưa nêu rõ giới hạn dữ liệu bị cắt.
- Điểm ở lần chạy 1: 96/100; factuality 40, completeness 23, evidence 20, boundaries 13.

CP4: `eval_before.json` có đủ 22/22 case được chấm, 0 unscored, điểm tổng **99,32/100**. Tất cả run có `status: completed`; điều này không bảo đảm câu trả lời đúng hoàn toàn.

Các vấn đề cần xem lại từ lần eval đầu:

| Case | Điểm | Phát hiện |
|---|---:|---|
| A1 | 95 | Câu trả lời thêm diễn giải về mạng/PoP so với mô tả nguồn và không nhắc các incident Actions khác trong kết quả tìm kiếm. |
| A2 | 98 | Judge đề nghị nói rõ việc loại trừ incident FedRAMP không loại trừ mọi vấn đề cache khác. Đây là đề xuất của judge, không phải bằng chứng câu trả lời đã khẳng định mọi vấn đề đều được loại trừ. |
| A7 | 96 | Có nhiều suy luận về tuyến mạng ngoài bằng chứng status; cần phân biệt giả thuyết cần kiểm tra với kết luận đã được xác minh. Judge cũng gợi ý kiểm tra mốc thời gian và khả năng có header CF-RAY. |
| H1 | 96 | Tool có update bị cắt và chỉ trả một phần timeline nhưng câu trả lời chưa nêu giới hạn đó. |

Kiểm tra `grade.mechanical`: cả 22 case không có violation. Đây là kiểm tra một số điều kiện, không chứng minh mọi claim đều có nguồn.

## 2. Bằng chứng trong trace

Trong H1, `result.trace` có tool event ở step 2 gọi `get_incident_details` cho GitHub `xr3myzj7ms51`. Trích lược các trường liên quan từ event thật:

```json
{
  "event": "tool",
  "step": 2,
  "name": "get_incident_details",
  "arguments": {"provider": "github", "incident_id": "xr3myzj7ms51"},
  "result": {
    "id": "xr3myzj7ms51",
    "updates_total": 9,
    "updates": [{"status": "resolved", "truncated": true}]
  }
}
```

Event đầy đủ có 3 update trong 9 update tổng cộng; khối trên chỉ trích update đầu. Judge ghi nhận thiếu lưu ý về dữ liệu bị cắt; đối chiếu `result.answer` xác nhận câu trả lời không nêu giới hạn này.

Nguyên nhân có thể xảy ra: system prompt chỉ nhắc chung về giới hạn bằng chứng, chưa yêu cầu cụ thể phải nêu `truncated` và số update được trả. Loop chuyển kết quả tool về model nhưng chưa có kiểm tra riêng cho giới hạn timeline. Đây là giả thuyết cần kiểm tra khi cải tiến ở CP5.

## 3. Thay đổi đã thực hiện

- Sửa gì, ở đâu: chưa thực hiện cải tiến CP5. CP4 giữ nguyên logic agent sau CP3. Chỉ bổ sung hỗ trợ `OPENAI_BASE_URL` và `stream: false` trong `providers.py` để kết nối 9Router; có unit test trong `tests/test_lab.py`.
- Vì sao chọn thay đổi này: Gemini trực tiếp liên tục trả HTTP 429; chuyển endpoint theo yêu cầu sang 9Router. Đây là thay đổi kết nối trước khi lấy baseline, không phải cải tiến để so sánh điểm.
- Hướng dự kiến CP5: nhắc rõ giới hạn update/timeline khi nguồn bị cắt; đồng thời hoàn thành contract validation URL nguồn theo `tests/test_validation.py`.

## 4. So sánh hai lần chạy

| Chỉ số | `eval_before.json` | `eval_after.json` |
|---|---|---|
| Điểm tổng | 99,32/100 | Chưa chạy CP6 |
| Điểm case đã chọn | H1: 96/100 | Chưa chạy CP6 |
| Số model calls | Agent: 54; judge: 22 | Chưa chạy CP6 |
| Token, chi phí nếu có | Agent: 185.027; judge: 105.319; tổng 290.346 token theo `usage.total_tokens`. Không có dữ liệu giá tiền. | Chưa chạy CP6 |

- Lỗi đã giải quyết: chưa đánh giá cải tiến; chưa có lần eval sau.
- Lỗi còn lại hoặc mới xuất hiện: các vấn đề A1, A2, A7, H1 nêu trên; validation nguồn CP5 chưa triển khai.

Cấu hình phải giữ cho CP6: provider/judge provider `openai` (giao thức tương thích qua 9Router, không phải gọi OpenAI trực tiếp); model/judge model `ag/gemini-3.8-flash`; `max_steps=8`; dataset `core`; snapshot có sẵn. Endpoint: `http://127.0.0.1:20128/v1`; chạy tuần tự, khoảng cách request tối thiểu 4,2 giây, khi HTTP 429 chờ 65 giây và thử lại tối đa 3 lần. Bộ điều tiết dùng cho lượt chạy này, chưa tích hợp vào CLI của repo. API key chỉ nằm trong `.env`.

## 5. Giới hạn

- Điểm judge là ước lượng. Agent và judge dùng cùng model nên có thể thiên lệch; điểm cao không chứng minh mọi suy luận đều có căn cứ. Ví dụ A7 vẫn có các diễn giải về tuyến mạng cần kiểm chứng dù được 96 điểm.
- Snapshot bài chính ngày 09/11/2026 không phản ánh tình trạng hiện tại. Tools chỉ tìm trong 50 incident gần nhất; chi tiết có thể lược bớt update hoặc cắt nội dung.
- Một lần chạy baseline và một lần sau cải tiến không chứng minh độ ổn định. Hiện mới có baseline, chưa có kết quả sau cải tiến.
- 9Router có thể đổi routing/model phía sau alias. Cần giữ cấu hình gateway và alias ổn định giữa hai lần; `config` chỉ ghi alias yêu cầu, không xác minh model nội bộ bất biến.
- `usage` là số liệu provider trả về; không tự suy ra chi phí tiền khi chưa có giá và thông tin billing tương ứng.
