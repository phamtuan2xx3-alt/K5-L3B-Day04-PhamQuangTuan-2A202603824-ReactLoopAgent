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

- Sửa gì, ở đâu: bổ sung `SYSTEM_PROMPT` trong `agent.py`, yêu cầu nói rõ giới hạn khi update có `truncated=true` hoặc `updates_total` lớn hơn số update được trả; không tuyên bố đã đọc toàn bộ timeline.
- Vì sao chọn thay đổi này: H1 trong baseline có bằng chứng cụ thể là update bị cắt và chỉ trả 3/9 update, nhưng câu trả lời không nhắc giới hạn này. Chỉ dẫn cụ thể giúp model nhận biết tín hiệu giới hạn từ dữ liệu thay vì chỉ được nhắc chung chung.
- Hoàn thành kiểm tra nguồn bắt buộc trong `run_agent()`: thu thập URL từ `get_incident_details` có `ok=true`. Nếu final answer không chứa ít nhất một URL đã quan sát, ghi `validation_missing_source`, đưa yêu cầu sửa về model trong cùng `max_steps`. Hết bước mà chưa sửa được thì trả `max_steps`; tool thất bại không tạo yêu cầu dẫn URL.
- Kiểm thử CP5: `py -m unittest discover -s tests -v` đạt **44/44 tests pass**. Bổ sung một test trong `tests/test_validation.py` xác nhận URL chưa quan sát không vượt qua validation. Các test có sẵn kiểm tra việc sửa nguồn trong budget, hết budget và tool không thành công đều pass.
- Giữ nguyên `eval_before.json`, fixtures, dataset và grading. Chưa chạy eval đầy đủ sau cải tiến, chưa khẳng định điểm tăng.
- Chạy thử riêng câu hỏi H1 qua 9Router sau cải tiến, `max_steps=8`: trả `completed`, 4 model calls, 5 tool calls. Câu trả lời đã nêu: “Tool chỉ trả về 3 trên tổng số `updates_total: 9`, và bản cập nhật giải quyết sự cố có `truncated: true`”, cùng lưu ý chưa có toàn bộ timeline gốc. Đây là kiểm tra hành vi của một lần chạy, không phải điểm eval sau và không được cộng vào baseline.
- Thay đổi kết nối 9Router (`OPENAI_BASE_URL`, `stream: false`) đã có từ trước baseline, không tính là cải tiến CP5; cấu hình này giữ nguyên cho CP6.

## 4. So sánh hai lần chạy

| Chỉ số | `eval_before.json` | `eval_after.json` |
|---|---|---|
| Điểm tổng | 99,32/100 | Chưa chạy CP6 |
| Điểm case đã chọn | H1: 96/100 | Chưa chạy CP6 |
| Số model calls | Agent: 54; judge: 22 | Chưa chạy CP6 |
| Token, chi phí nếu có | Agent: 185.027; judge: 105.319; tổng 290.346 token theo `usage.total_tokens`. Không có dữ liệu giá tiền. | Chưa chạy CP6 |

- Lỗi đã giải quyết: các tests thiếu URL nguồn đã pass sau khi thêm validation. Chưa có lần eval đầy đủ sau để đánh giá mức cải thiện H1 hoặc điểm tổng.
- Lỗi còn lại hoặc mới xuất hiện: cần kiểm tra lại A1, A2, A7, H1 ở CP6. Validation URL chỉ yêu cầu một URL đã quan sát, không chứng minh mọi claim hay mọi provider đều có nguồn.

Cấu hình phải giữ cho CP6: provider/judge provider `openai` (giao thức tương thích qua 9Router, không phải gọi OpenAI trực tiếp); model/judge model `ag/gemini-3.8-flash`; `max_steps=8`; dataset `core`; snapshot có sẵn. Endpoint: `http://127.0.0.1:20128/v1`; chạy tuần tự, khoảng cách request tối thiểu 4,2 giây, khi HTTP 429 chờ 65 giây và thử lại tối đa 3 lần. Bộ điều tiết dùng cho lượt chạy này, chưa tích hợp vào CLI của repo. API key chỉ nằm trong `.env`.

## 5. Giới hạn

- Điểm judge là ước lượng. Agent và judge dùng cùng model nên có thể thiên lệch; điểm cao không chứng minh mọi suy luận đều có căn cứ. Ví dụ A7 vẫn có các diễn giải về tuyến mạng cần kiểm chứng dù được 96 điểm.
- Snapshot bài chính ngày 09/11/2026 không phản ánh tình trạng hiện tại. Tools chỉ tìm trong 50 incident gần nhất; chi tiết có thể lược bớt update hoặc cắt nội dung.
- Một lần chạy baseline và một lần sau cải tiến không chứng minh độ ổn định. Hiện mới có baseline, chưa có kết quả sau cải tiến.
- 9Router có thể đổi routing/model phía sau alias. Cần giữ cấu hình gateway và alias ổn định giữa hai lần; `config` chỉ ghi alias yêu cầu, không xác minh model nội bộ bất biến.
- `usage` là số liệu provider trả về; không tự suy ra chi phí tiền khi chưa có giá và thông tin billing tương ứng.
- Chỉ dẫn về dữ liệu bị cắt là cải tiến prompt, không phải bộ kiểm tra ngữ nghĩa bảo đảm model luôn nêu đúng mọi giới hạn. Validation URL hiện kiểm tra chuỗi xuất hiện trong answer, không xác minh URL có thực sự hỗ trợ từng kết luận hay không.
