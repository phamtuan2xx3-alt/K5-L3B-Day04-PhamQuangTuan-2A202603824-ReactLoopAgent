# Ghi chú phân tích · Day 04

Họ và tên: Phạm Quang Tuấn
MSSV: 2A202603824

## Tiến độ CP1–CP2

### CP1 — Đã hoàn thành

- Python 3.12.10; dự án dùng thư viện chuẩn, không cần cài thêm package.
- Đã cấu hình Gemini với model `gemini-3.5-flash-lite`; API key được giữ trong `.env`, không commit.
- Đã chạy `get_status("github", "Actions")` và `get_incident_details("cloudflare", "wp49bp8bqo6c")`, cả hai trả JSON.
- Đã kiểm tra repo riêng đúng tên và push thành công.
- Minh chứng: [cp1_tools.json](cp1_tools.json).
- Dữ liệu là snapshot ngày 09/11/2026; tìm trong 50 incident gần nhất không chứng minh không có incident ngoài phạm vi đó. Incident Cloudflare được kiểm tra ảnh hưởng khách hàng FedRAMP, không phải mọi khách hàng.

### CP2 — Đã hoàn thành

- Đã triển khai `run_agent()` trong [agent.py](agent.py): gọi model, giữ nguyên assistant message, xử lý mọi tool call, trả kết quả đúng `tool_call_id` và gọi model tiếp.
- Kết quả có `status`, `answer`, `trace`, `usage`; chỉ hoàn thành khi model dừng bằng `stop` và không còn calls.
- Kiểm thử `py -m unittest discover -s tests -p test_lab.py -v`: **12/12 tests pass**. Log: [cp2_tests.txt](cp2_tests.txt).
- Câu hỏi thực tế: “GitHub Actions hiện có sự cố không? Hãy kiểm tra incident gần đây.”
- Gemini trả `completed`, có 2 response model thành công và 1 tool call `get_status`. Minh chứng nguyên bản: [cp2_run.json](cp2_run.json).
- Lần chạy minh chứng giữ khoảng cách tối thiểu 4,2 giây giữa các request, chờ 65 giây khi gặp HTTP 429. Bộ chờ tạm này chưa tích hợp vào `run.py`.

Chi tiết đối chiếu yêu cầu: [CP1_CP2.md](CP1_CP2.md).

Các mục 1–5 bên dưới dành cho phân tích eval ở CP5–CP6, chưa có kết quả để điền. CP1–CP2 chưa thay thế hai lần eval bắt buộc của bài nộp cuối.

## 1. Case được chọn

- ID case:
- Câu trả lời của agent:
- Điểm ở lần chạy 1:

## 2. Bằng chứng trong trace

Dán đoạn trace chứng minh lỗi và nêu nguyên nhân có thể xảy ra.

```text

```

## 3. Thay đổi đã thực hiện

- Sửa gì, ở đâu:
- Vì sao chọn thay đổi này:

## 4. So sánh hai lần chạy

| Chỉ số | `eval_before.json` | `eval_after.json` |
|---|---|---|
| Điểm tổng |  |  |
| Điểm case đã chọn |  |  |
| Số model calls |  |  |
| Token, chi phí nếu có |  |  |

- Lỗi đã giải quyết:
- Lỗi còn lại hoặc mới xuất hiện:

## 5. Giới hạn

Nêu giới hạn của điểm judge, của snapshot và của việc chỉ chạy một lần mỗi phiên bản.
