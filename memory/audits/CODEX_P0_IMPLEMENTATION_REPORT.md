# Báo cáo triển khai P0 — hook Claude Code và AGENTS.md

Ngày 23/11/2026 · TASK-P0-HOOKS-SLIM-AGENTS-20261123

Đã cài hook ở cấp workspace và đồng bộ ba bản AGENTS.md dưới 15 KB. Suite 1, Suite 15 và bộ test riêng của hook đều đạt. Mục tiêu dưới 50 ms đạt ở trung vị của hai ca PreToolUse được đo. Một số lượt khởi chạy Python vượt ngưỡng.

## Hook bảo vệ dự án

Claude Code 2.1.330 đã trả về đường dẫn hook trong cấu hình hiệu lực qua `get_settings`. Các phép thử gọi lệnh đã đăng ký bằng sự kiện JSON cục bộ, dùng tệp mẫu. [Cấu hình](../../../.claude/settings.json) · [Mã hook](../../tools/claude_safety_hook.py)

| Sự kiện | Hành vi đã kiểm tra |
|---|---|
| Trước khi ghi DWG | Chặn Write/Edit, ghi qua shell và chuyển hướng vào DWG gốc dưới `01_Projects`. Cho xuất DWG mới vào `04_Deliverables_ToTrinh` của dự án. Tên đích đã tồn tại bị chặn. Lệnh snapshot của cầu nối Core Console nội bộ được phép dùng bản staging. |
| Trước khi push | Hook trả `permissionDecision: ask` để Claude Code yêu cầu người dùng duyệt. Lệnh kiểm tra thông thường như `git status`, `git diff`, `pytest` và chạy script Python thông thường tiếp tục theo quyền hiện hành. |
| Sau khi sửa hoặc xuất | Kiểm tra từng đường dẫn trong workspace qua `audit_zero_white_text.py`. Đã thử tệp Python, Word có chữ trắng trực tiếp và qua style, ô Excel có chữ trắng, PDF có chữ trắng và các mẫu Word/Excel chữ tối. Vi phạm được phản hồi cho Claude sau thao tác. |

**Quyết định về giao thức.** Hook dùng mã thoát 2 và thông báo tiếng Việt để chặn trước thao tác. Mã 1 nêu trong brief không đảm bảo chặn theo giao thức Claude Code. PostToolUse báo lỗi sau khi ghi, tệp vẫn tồn tại để sửa. [Tài liệu hook chính thức](https://code.claude.com/docs/en/hooks#exit-code-2)

**Phạm vi bảo vệ.** Hook quan sát tham số và kết quả công cụ Claude trong workspace. Shell có đích DWG chưa phân giải được có thể yêu cầu xác nhận. Một chương trình con tự tính đường dẫn và âm thầm ghi tệp có thể nằm ngoài phạm vi phát hiện. Kiểm tra màu trên báo cáo bao phủ các cách biểu diễn đã thử, chưa xác minh mọi theme Office hoặc chữ nằm trong ảnh quét. Chưa thực hiện push hoặc mở AutoCAD trên bản vẽ dự án thật.

## Tinh gọn hướng dẫn

Ba bản tại gốc workspace, `.agents/` và `.agents/skills/` đều giảm từ **48.033 xuống 12.986 byte**. Đã so sánh từng byte và kiểm tra chỉ mục trỏ đủ các tài liệu tách ra. SHA-256 chung là `0b9079710ea11116a78fc81e4d40d0cc45c445e073e0dbf0c36d5adb405e597a`.

Phần lõi giữ ma trận điều phối, bảng 14 skill, Review Gate, quy tắc tính toán, tiêu chuẩn, trách nhiệm và xác nhận đầu ra. Điều 12b–12e gốc được đối chiếu lại với bản trước khi tách. Điều 12e hiện hành là quy tắc Word/Excel nên được lưu riêng ở `RULE_12E_TYPOGRAPHY.md`. Tệp Revit mang tên brief yêu cầu dẫn tới đặc tả P4.3 và bộ chuyển dữ liệu BIM. [Hướng dẫn lõi](../../../AGENTS.md) · [Thư mục quy tắc chi tiết](../../skills/references/)

## Bằng chứng nghiệm thu

| Kiểm tra | Kết quả |
|---|---|
| Suite 1, tích hợp | 64/64 đạt, 0 cảnh báo |
| Suite 15, báo cáo đồng bộ | 15/15 đạt theo số test thực chạy |
| Suite 53, hook P0 | 7/7 đạt |
| PreToolUse cho `git status`, 30 tiến trình mới | Trung vị 39,1 ms. P95 55,6 ms. Tối đa 56,0 ms. |
| PreToolUse từ chối Edit DWG, 30 tiến trình mới | Trung vị 41,8 ms. P95 63,8 ms. Tối đa 76,5 ms. |

Lệnh nghiệm thu từ gốc workspace là `python -X utf8 -B .agents/tests/run_all_tests.py --suite 1 --suite 15 --suite 53`. Số đo thời gian gồm khởi chạy Python đến lúc thoát, chưa cộng thời gian Claude khởi chạy shell. Thời gian đọc và phân tích một báo cáo sau khi xuất phụ thuộc kích thước tệp. [Test hook](../../tests/test_workspace_claude_safety_hook.py) · [Công cụ kiểm tra màu](../../tools/audit_zero_white_text.py)
