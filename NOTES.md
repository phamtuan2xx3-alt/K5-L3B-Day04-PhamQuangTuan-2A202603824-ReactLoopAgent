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

Giả thuyết nguyên nhân từ baseline: system prompt chỉ nhắc chung về giới hạn bằng chứng, chưa yêu cầu cụ thể phải nêu `truncated` và số update được trả. Loop chuyển kết quả tool về model nhưng chưa có kiểm tra riêng cho giới hạn timeline. CP5 bổ sung chỉ dẫn này; lần chạy CP6 cho thấy H1 đã nêu giới hạn, nhưng một lần chạy không chứng minh quan hệ nhân quả hay độ ổn định.

### Demo CP7 từ trace thật

Mở `eval_after.json`, tìm case H1 rồi đọc `result.trace` theo thứ tự:

| Model step | Sự kiện và dữ liệu quan sát |
|---|---|
| 1 | Model yêu cầu hai call `get_incident_details`: GitHub `h02n9572mx9y` và Cloudflare `yaa0witbl2me`. Tool trả lần lượt 3/4 và 3/3 update. |
| 2 | Sau khi nhận tool results, model theo liên kết từ incident GitHub, gọi `get_incident_details` cho `xr3myzj7ms51`. Tool trả 3/9 update và có update `truncated: true`. |
| 3 | Model trả `finish: stop`, không còn calls. Answer dẫn nguồn hai bên, nêu rõ giới hạn dữ liệu và chưa có bằng chứng chung nguyên nhân. Run `completed`, case được chấm 100/100. |

Điểm cần giải thích khi demo: call ở step 2 phụ thuộc dữ liệu lấy ở step 1; Python phải giữ nguyên assistant message và trả mọi tool result với đúng `tool_call_id` trước khi gọi model tiếp. Step tính theo số lần gọi model, không theo số tool calls.

Demo một lỗi còn lại: case H3 trong cùng file. Tool trả `ok: false`, `error: INCIDENT_NOT_FOUND`, với thông báo chỉ tìm trong 50 incident gần nhất. Agent vẫn dùng tiêu đề “Không tồn tại sự cố với mã này”, mạnh hơn bằng chứng. Case đạt 97/100; cần diễn đạt “không tìm thấy trong phạm vi dữ liệu” thay vì kết luận không tồn tại. Lỗi này cho thấy `completed` và điểm cao không đồng nghĩa mọi phát biểu đều đúng.

## 3. Thay đổi đã thực hiện

- Sửa gì, ở đâu: bổ sung `SYSTEM_PROMPT` trong `agent.py`, yêu cầu nói rõ giới hạn khi update có `truncated=true` hoặc `updates_total` lớn hơn số update được trả; không tuyên bố đã đọc toàn bộ timeline.
- Vì sao chọn thay đổi này: H1 trong baseline có bằng chứng cụ thể là update bị cắt và chỉ trả 3/9 update, nhưng câu trả lời không nhắc giới hạn này. Chỉ dẫn cụ thể giúp model nhận biết tín hiệu giới hạn từ dữ liệu thay vì chỉ được nhắc chung chung.
- Hoàn thành kiểm tra nguồn bắt buộc trong `run_agent()`: thu thập URL từ `get_incident_details` có `ok=true`. Nếu final answer không chứa ít nhất một URL đã quan sát, ghi `validation_missing_source`, đưa yêu cầu sửa về model trong cùng `max_steps`. Hết bước mà chưa sửa được thì trả `max_steps`; tool thất bại không tạo yêu cầu dẫn URL.
- Kiểm thử CP5: `py -m unittest discover -s tests -v` đạt **44/44 tests pass**. Bổ sung một test trong `tests/test_validation.py` xác nhận URL chưa quan sát không vượt qua validation. Các test có sẵn kiểm tra việc sửa nguồn trong budget, hết budget và tool không thành công đều pass.
- Giữ nguyên `eval_before.json`, fixtures, dataset và grading. Đã chạy eval đầy đủ sau cải tiến tại CP6; kết quả và so sánh ở mục 4.
- Chạy thử riêng câu hỏi H1 qua 9Router sau cải tiến, `max_steps=8`: trả `completed`, 4 model calls, 5 tool calls. Câu trả lời đã nêu: “Tool chỉ trả về 3 trên tổng số `updates_total: 9`, và bản cập nhật giải quyết sự cố có `truncated: true`”, cùng lưu ý chưa có toàn bộ timeline gốc. Đây là kiểm tra hành vi của một lần chạy, không phải điểm eval sau và không được cộng vào baseline.
- Thay đổi kết nối 9Router (`OPENAI_BASE_URL`, `stream: false`) đã có từ trước baseline, không tính là cải tiến CP5; cấu hình này giữ nguyên cho CP6.

## 4. So sánh hai lần chạy

| Chỉ số | `eval_before.json` | `eval_after.json` |
|---|---|---|
| Điểm tổng | 99,32/100 | 99,82/100 (+0,50 điểm) |
| Điểm case đã chọn | H1: 96/100 | H1: 100/100 (+4 điểm) |
| Số model calls | Agent: 54; judge: 22 | Agent: 61; judge: 22 |
| Token, chi phí nếu có | Agent: 185.027; judge: 105.319; tổng 290.346 token theo `usage.total_tokens`. Không có dữ liệu giá tiền. | Agent: 217.075; judge: 106.734; tổng 323.809 token (+33.463, khoảng +11,53%). Không có dữ liệu giá tiền. |

- Cả hai file có đủ 22/22 case được chấm, 0 unscored, mọi run `completed`; `grade.mechanical.violations` đều rỗng. Khối `config` của hai file giống nhau hoàn toàn.

Các case đổi điểm; 16 case còn lại giữ nguyên 100/100:

| Case | Trước | Sau | Chênh lệch |
|---|---:|---:|---:|
| A1 | 95 | 100 | +5 |
| A2 | 98 | 100 | +2 |
| A7 | 96 | 100 | +4 |
| H1 | 96 | 100 | +4 |
| H3 | 100 | 97 | -3 |
| H6 | 100 | 99 | -1 |

- Lỗi đã giải quyết trong lần chạy quan sát: H1 đã nêu rõ 3/4 update của incident gốc và 3/9 update của incident liên kết, cùng `truncated: true`. Xem case H1, `result.answer` và tool event step 2 cho `xr3myzj7ms51` trong `eval_after.json`. Judge tăng boundaries từ 13 lên 15 và completeness từ 23 lên 25.
- Trace sau có 3 event `validation_missing_source`: E3 step 4, A7 step 3, H3 step 3. Agent đã gọi model tiếp để sửa; final answer ở cả ba case có ít nhất một URL incident đã quan sát. Đây là minh chứng gate thực sự hoạt động trong eval, không chỉ trong unit tests.
- Lỗi còn lại hoặc mới xuất hiện: H3 dùng tiêu đề “Không tồn tại sự cố với mã này” trong khi tool chỉ xác nhận `INCIDENT_NOT_FOUND` trong 50 incident gần nhất. Phần giải thích bên dưới có giới hạn đúng, nhưng tiêu đề vẫn khẳng định quá mức; judge trừ 3 điểm. H6 lọc component bằng “GitHub Actions” và nhận `components: []`, nên trạng thái tổng quan không đủ để xác nhận riêng component; judge trừ 1 điểm vì chưa nêu rõ điểm này và giới hạn tìm kiếm.
- Dù A7 tăng lên 100, câu trả lời vẫn có khẳng định về tuyến Anycast và “ngoại lệ duy nhất” ngoài bằng chứng status. Không coi điểm tăng là chứng minh những suy luận đó đã được xác minh hoặc mọi lỗi A7 đã hết.
- Đánh đổi: agent thêm 7 model calls (khoảng +12,96%), tool calls từ 49 lên 52 và tổng token tăng khoảng 11,53%. Ba lượt sửa nguồn có đóng góp vào số calls; phần còn lại có thể do khác biệt hành vi model. Không quy toàn bộ chênh lệch chi phí cho một thay đổi, cũng không suy ra tiền nếu chưa có giá billing.
- Validation URL chỉ yêu cầu một URL đã quan sát, không chứng minh mọi claim hay mọi provider đều có nguồn.

Cấu hình đã giữ nguyên giữa CP4 và CP6: provider/judge provider `openai` (giao thức tương thích qua 9Router, không phải gọi OpenAI trực tiếp); model/judge model `ag/gemini-3.8-flash`; `max_steps=8`; dataset `core`; snapshot có sẵn. Endpoint: `http://127.0.0.1:20128/v1`; chạy tuần tự, khoảng cách request tối thiểu 4,2 giây, khi HTTP 429 chờ 65 giây và thử lại tối đa 3 lần. Bộ điều tiết dùng cho các lượt chạy này, chưa tích hợp vào CLI của repo. API key chỉ nằm trong `.env`.

## 5. Giới hạn

- Điểm judge là ước lượng. Agent và judge dùng cùng model nên có thể thiên lệch; điểm cao không chứng minh mọi suy luận đều có căn cứ. Ví dụ A7 vẫn có các diễn giải về tuyến mạng cần kiểm chứng dù được 96 điểm.
- Snapshot bài chính ngày 09/11/2026 không phản ánh tình trạng hiện tại. Tools chỉ tìm trong 50 incident gần nhất; chi tiết có thể lược bớt update hoặc cắt nội dung.
- Một lần chạy baseline và một lần sau cải tiến không chứng minh độ ổn định hoặc tách được ảnh hưởng cải tiến khỏi biến động của model/judge. Hai file hiện thể hiện đúng một lần chạy mỗi phiên bản, không chọn điểm tốt nhất qua nhiều lần.
- 9Router có thể đổi routing/model phía sau alias. Cần giữ cấu hình gateway và alias ổn định giữa hai lần; `config` chỉ ghi alias yêu cầu, không xác minh model nội bộ bất biến.
- `usage` là số liệu provider trả về; không tự suy ra chi phí tiền khi chưa có giá và thông tin billing tương ứng.
- Chỉ dẫn về dữ liệu bị cắt là cải tiến prompt, không phải bộ kiểm tra ngữ nghĩa bảo đảm model luôn nêu đúng mọi giới hạn. Validation URL hiện kiểm tra chuỗi xuất hiện trong answer, không xác minh URL có thực sự hỗ trợ từng kết luận hay không.

### Chốt repo cho CP7

- Đã đối chiếu đủ `agent.py`, `eval_before.json`, `eval_after.json`, `NOTES.md`; giữ nguyên các file gốc của đề, fixtures và grading.
- Unit tests: 44/44 pass. Hai eval có cùng `config`, đủ 22 case mỗi file và điểm tổng khác `null`.
- Repo đúng tên, truy cập không đăng nhập được tại: https://github.com/phamtuan2xx3-alt/K5-L3B-Day04-PhamQuangTuan-2A202603824-ReactLoopAgent
- `.env` không được Git track; chỉ `.env.example` nằm trong repo. Đã kiểm tra các API key cấu hình không xuất hiện trong file nộp; cấu hình chia sẻ 9Router nằm ngoài repo.
- Demo trace nhiều bước H1 và lỗi H3 đã được đối chiếu với kết quả thật như mục 2.
- Trạng thái LMS: chưa xác nhận nộp link. Học viên cần nộp URL repo trên bài Day 04 tại https://aithucchien.vinuni.edu.vn bằng tài khoản cá nhân và kiểm tra trạng thái nộp trước hạn của ca học.
