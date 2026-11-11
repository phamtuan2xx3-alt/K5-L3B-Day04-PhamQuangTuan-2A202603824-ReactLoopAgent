# Minh chứng CP1 và CP2

Họ tên: Phạm Quang Tuấn  
MSSV: 2A202603824

## CP1 — Setup và khám phá tools

- Python 3.12.10; không cần thư viện ngoài.
- Provider: Gemini; model đang cấu hình: `gemini-3.5-flash-lite`.
- API key nằm trong `.env`, được Git bỏ qua; không đưa key vào minh chứng.
- Kết quả chạy hai tool nằm trong [cp1_tools.json](cp1_tools.json).
- Repo riêng đúng tên; quyền push được kiểm tra bằng `git push`.
- Key gọi được LLM: lần chạy thật trong CP2 đã trả `completed`.

`get_status` trả trạng thái tổng quan, component khớp và tối đa 5 incident
khớp chuỗi trong 50 incident gần nhất. Không tìm thấy không chứng minh incident
không tồn tại. `get_incident_details` trả chi tiết incident và các update có thể
bị lược bỏ; cần đọc `truncated` và `updates_total`.

Hai tool dùng snapshot ngày 09/11/2026, không chứng minh trạng thái hiện tại.
Incident Cloudflare được kiểm tra có phạm vi FedRAMP; không suy rộng sang mọi
khách hàng.

## CP2 — Agent loop

- Mã triển khai: [agent.py](agent.py).
- Giữ nguyên assistant message trước khi trả tool results.
- Parse arguments và xử lý tất cả calls; mỗi kết quả mang đúng `tool_call_id`.
- Chỉ hoàn thành khi `finish == 'stop'` và không còn calls.
- Kết quả có `status`, `answer`, `trace`, `usage`.

Lệnh kiểm thử:

```powershell
py -m unittest discover -s tests -p test_lab.py -v
```

Kết quả: 12/12 tests pass, gồm kiểm tra đúng tool-call ID, nhiều calls và
trajectory hai tool trên snapshot. Log: [cp2_tests.txt](cp2_tests.txt).

Câu hỏi chạy thật:

> GitHub Actions hiện có sự cố không? Hãy kiểm tra incident gần đây.

Kết quả Gemini thật trong [cp2_run.json](cp2_run.json): `completed`, 2 lần model
trả response thành công, 1 call `get_status`. File giữ nguyên answer, trace và usage;
không phải kết quả eval 22 case.

Lần tạo minh chứng dùng bộ điều tiết tạm: tối thiểu 4,2 giây giữa các request,
gặp HTTP 429 thì chờ 65 giây và thử lại, tối đa 3 lần cho mỗi model call.
Các request lỗi không được tính trong danh sách `usage`. Bộ điều tiết này chưa
được tích hợp vào `run.py`; lệnh thông thường chưa tự chờ khi gặp 429.

## Phạm vi hoàn thành

CP1 và CP2 có minh chứng. Chưa hoàn tất bài nộp cuối: còn CP3–CP7,
`eval_before.json`, `eval_after.json` và phần phân tích trong `NOTES.md`.
Toàn bộ tests ở lần kiểm tra trước đạt 35/37; hai test validation nguồn
thuộc phần cải tiến CP5 chưa pass. Không thay đổi fixtures, eval hay rubric.
