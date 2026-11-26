# Đánh giá tài nguyên Skill, Plugin và MCP cho Agent

**Định hướng của Agent.** Sản phẩm chính là hồ sơ thiết kế, thẩm tra và quản trị dự án. Khi phối hợp làm hồ sơ, hệ thống đã phân vai lập và kiểm tra, yêu cầu đối chiếu số liệu gốc và xác nhận đúng tệp cuối. Khi bảo trì công cụ, tiêu chí là phát hiện lỗi và chứng minh bản sửa. Một plugin có thể có ích cho công việc thứ hai nhưng vẫn thiếu căn cứ để đưa vào luồng phát hành hồ sơ. [Hướng dẫn hệ thống](../../USER_GUIDE.md) · [Quy tắc điều phối và kiểm tra](../../AGENTS.md)

**Quyết định ở lần rà soát này.** Giữ các gói ở mức tham khảo. Hai hướng có ca thử rõ là lấy tiêu chí xác minh của Superpowers cho một lỗi script đã biết, và dùng AutoCAD MCP đọc lại một DXF thử nghiệm. Giá trị bổ sung cần được đo trên cùng đầu vào với quy trình hiện có. Đặc tả P4 đặt việc sửa form và đối chiếu RFI/NCR trước chuyển đổi BIM, dùng chuẩn layer DCE tập trung và đặt nghiệp vụ ở phía sau giao diện MCP. Đây là căn cứ chọn ca thử, chưa xác nhận tiến độ triển khai từng hạng mục. [Đặc tả CAD và thứ tự P4](../CLAUDE_P4_SPEC_AND_COMPLEX_TASKS.md)

## Kho skill và công cụ

| Tài nguyên | Phân loại và bằng chứng trong bản tải | Áp dụng cho Agent |
| --- | --- | --- |
| `anthropics-skills` | **Skill và script có sẵn.** Có marketplace manifest, `SKILL.md` và script PDF, DOCX, PPTX, XLSX. `quick_validate.py` chạy đạt trên mẫu và skill PDF với PyYAML. `run_eval.py` gọi Claude CLI. | Tham khảo cách tổ chức hướng dẫn và script đọc hồ sơ. Điều 19 yêu cầu ghi phiên bản. Thử cùng một skill mẫu cho thấy validator chấp nhận mẫu cơ bản nhưng từ chối ngay khi thêm khóa cấp đầu `version`. Cần thống nhất cách biểu diễn phiên bản trước khi dùng validator nội bộ. |
| `awesome-claude-code` | **Danh mục liên kết.** `README.md` và CSV trỏ ra ngoài tới Hooks Guide, Claude Codex Settings và các bộ slash command. Mã Python trong kho phục vụ tạo README, cập nhật danh mục và xử lý đề xuất. | Dùng để tìm ứng viên. Muốn lấy hook, `settings.json` hoặc slash command được giới thiệu phải lấy và rà soát ở kho đích. |
| `obra-superpowers` | **Plugin quy trình có mã.** Có manifest Claude Code và Codex, thư mục `skills/`, test và hook Claude `SessionStart` trong `hooks/hooks.json`. | Tham khảo `verification-before-completion` cho bảo trì. Trên một lỗi đã biết, so khả năng tái hiện lỗi và xác nhận bản sửa với cách đang dùng. Hook `SessionStart` tự nạp hướng dẫn đầu phiên, có thể chồng lên điều phối nội bộ. |
| `garrytan-gstack` | **Bộ skill và công cụ có mã.** Có `review/SKILL.md`, `plan-eng-review/SKILL.md`, CLI/trình duyệt TypeScript và `setup.ps1`. Bản Windows cần Git for Windows, Bun và Node.js, với mức hỗ trợ tối thiểu theo README. | Chỉ đáng trích câu hỏi review diff nếu tìm được lỗi mà quy trình bảo trì hiện tại bỏ sót. Cài cả bộ có chi phí cao so với nhu cầu này. README cũng ghi review ngoài máy được bật mặc định. |
| `autocad-mcp` | **Máy chủ MCP Python có mã.** Có `src/autocad_mcp/server.py`, backend ezdxf và backend File IPC với AutoLISP. Bộ test ezdxf đạt **80/80** sau khi bổ sung `structlog` vào thư mục tạm. | Ca thử phù hợp là đọc lại cùng một form DXF bằng hai công cụ, đối chiếu layer, thuộc tính block và giá trị trước/sau sửa với dữ liệu gốc. 80 test mới chứng minh backend chạy trong bộ test của kho. Nhánh DWG native cần Windows, AutoCAD LT 2024+ và thiết lập AutoLISP. Hồ sơ qualification đi kèm ghi nhận riêng AutoCAD LT 2027. |

**Nhóm tham khảo chọn lọc trong brief.** `awesome-claude-skills-travisvn` là danh mục liên kết. `prompt-engineering-guide` là cẩm nang có notebook và mã trang tài liệu. `awesome-claude-skills-composio` có skill/script thật và plugin `connect-apps` phụ thuộc dịch vụ Composio, phù hợp khi có nhu cầu kết nối ứng dụng cụ thể. `frontend-slides` có skill, mẫu HTML/CSS và script trích PPTX, phù hợp khi cần bản trình bày HTML.

## Các ZIP lưu trữ

| Gói | Bản tải chứa gì | Áp dụng cho Agent |
| --- | --- | --- |
| `horizun-revit-mcp.zip` | **Mã server và add-in Revit.** Có `src/Horizun.Server/Program.cs`, dự án .NET, `.addin`, test và danh mục công cụ. | Giữ cho nhu cầu BIM ở P4.3. Khi có mô hình mẫu Windows/Revit 2023–2027, đối chiếu mã cấu kiện, đơn vị và số lượng truy vấn với bảng thống kê trong Revit. |
| `rvt-mcp.zip` | **Mã một phần.** Có add-in R22/R25, mã dùng chung, test và README tiếng Việt. Solution tham chiếu `src/server/RvtMcp.Server.csproj`, nhưng ZIP thiếu toàn bộ `src/server/` và binary gateway. | Tham khảo cấu hình giới hạn quyền và danh mục 237 công cụ theo README. Nếu cần thử gateway, phải có bộ phát hành tương ứng hoặc bản nguồn đầy đủ. |
| `agent-circuit-breaker.zip` | **Công cụ Python có mã.** Có CLI, MCP proxy và `hooks_native.py` sinh cấu hình `PreToolUse`/`PostToolUse` cho Claude. CLI đã phân loại hai đầu vào giả lập thành `BLOCK` và `UNKNOWN`. | CLI trả `UNKNOWN` cả với `git status`. Muốn đánh giá hook cần thử trong phiên Claude Code với một lệnh đọc hợp lệ và một thao tác ghi ngoài phạm vi, rồi kiểm tra tác động thực tế ở cả hai ca. |
| `rule-engine.zip` | **Thư viện Python.** Đã chạy biểu thức và kiểm tra cả trường hợp đạt lẫn vượt ngưỡng trên dữ liệu giả. | Có thể thử trên một quy tắc NCR có nguồn, đơn vị và ngưỡng đã được xác nhận. Đo kết quả tại đúng ngưỡng và khi thiếu đầu vào. |
| `pyconcrete.zip` | **Thư viện `rcdetailing` tiền alpha.** Có mã và test vẽ chi tiết dầm/cốt thép DXF. Đã khởi tạo thử đối tượng thanh thép. | Tham khảo sinh hình chi tiết dầm. Cần kiểm tra quy ước bản vẽ và đối chiếu độc lập trước khi đưa vào hồ sơ. |
| `simple-graph.zip` | **SQL và mẫu truy vấn SQLite.** Đã tạo bảng, hai nút và một cạnh trong bộ nhớ. | Dùng khi cần truy vết quan hệ nút, cấu kiện hoặc dữ liệu nguồn. |
| `verdict-rules.zip` | **Một JSON mẫu eval.** Tệp dự án được tham chiếu vắng trong ZIP. | Tham khảo cách mô tả tiêu chí chấm theo từng điều kiện. |

Cả 7 ZIP đều đạt kiểm tra CRC và khớp SHA-256 với manifest tại chỗ. Các kiểm tra chạy chỉ bao phủ validator, DXF headless, CLI và mẫu thư viện nêu trên. AutoCAD/Revit native, cài đặt plugin và hook trong phiên Claude Code mới được kiểm tra qua mã và cấu hình.


## Phần đã triển khai ngày 23/11/2026

Đã áp dụng cách tái hiện lỗi trước khi sửa của Superpowers và ý tưởng đọc lại DXF trên dữ liệu thực vào công cụ nội bộ `diff_form`. MCP và bộ sửa form nay dùng chung cách chọn bản sửa theo số phiên bản. Kết quả ghi SHA-256 của hai DXF và ghi nhận layer bị mất. Hai lỗi đã được tái hiện trên form mẫu trước khi sửa. Sau khi sửa, 13 test MCP, 14 test xử lý form và 9 test RFI/NCR đều đạt. Phép thử dùng backend DXF trên dự án tạm. [Hợp đồng công cụ](../../docs/MCP_DCE_CAD_CONTRACT.md)


## Nâng cấp tầng 1 tại workspace

Bộ kiểm tra tích hợp và công cụ lập báo cáo dùng chung bộ đọc metadata nội bộ cho 14 skill, giữ quy ước phiên bản X.Y.Z và alias. Đã tái hiện rồi sửa trường hợp ví dụ phiên bản trong thân bài làm skill thiếu metadata vẫn báo đạt. Kiểm thử hồi quy bao phủ cả khóa trùng, thiếu dòng đóng, BOM và CRLF. Suite 1 đạt 64 phép kiểm tra, suite 15 đạt 15 test.

Lệnh Claude Code `/kiem-tra-agent` áp dụng cách review diff của gstack và xác minh kết quả của Superpowers cho công việc bảo trì. Lệnh yêu cầu đọc diff, xác định bên gọi, chạy suite liên quan và ghi bằng chứng cho từng nhận định. Claude CLI đã liệt kê được lệnh khi khởi tạo từ gốc workspace. [Lệnh review](../../../.claude/commands/kiem-tra-agent.md)


## Ứng dụng khi Agent nhận việc

Global Dispatcher 3.1 áp dụng ý tưởng nạp hướng dẫn theo nhu cầu từ Anthropic Skills. Với phiếu do `dispatch_task.py prepare` tạo, bộ điều phối dùng skill đã chọn và nội dung của bước để tìm tài liệu chuyên sâu trong danh mục cục bộ. Đường dẫn xuất hiện trong `guide_files` và trong lời bàn giao của phiếu sẵn sàng thực hiện. Đã khai báo 8 tài liệu thuộc 3 skill thiết kế kết cấu, thẩm tra thiết kế và lập phụ lục.

Trong phép thử qua CLI, yêu cầu tính bu lông rồi kiểm chứng dẫn tới `SKILL_CONNECTION.md` ở bước thiết kế và `SKILL_VERIFY` ở bước sau. Năm suite liên quan đã đạt, gồm 22 test điều phối 2D. Phép thử xác minh việc chọn tài liệu và bàn giao, chưa đo chất lượng tính toán của mô hình. [Hướng dẫn điều phối](../../skills/Global_Dispatcher/SKILL.md)
