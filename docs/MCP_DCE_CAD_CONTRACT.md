# MCP DCE CAD — hợp đồng triển khai 2026-11-14

Entry point: `tools/mcp_dce_cad_server.py`; cấu hình mẫu `tools/mcp_config.json`.
MCP dùng stdio JSON-RPC. Log engine đi stderr; stdout dành cho giao thức.
Không cần AutoCAD đang chạy để dùng các tool DXF/preview.

| Tool | Hành vi và điều kiện |
|---|---|
| render_cad_plan | KC-01/02/03; model JSON và template tùy chọn. Output UUID local. `output_dxf_path` là gợi ý; dùng `output_dxf` trả về. `pdf_path` là PDF đầu vào. Dry-run không lưu DXF. Sheet không hợp lệ/đầu vào không tồn tại trả E001. |
| render_preview | DXF → PNG local; dùng output_png và preview_id. |
| consume_preview | Trả ImageContent, xóa backing PNG sau khi đọc; token một lần. |
| release_preview | Dọn preview khi caller đã đọc file hoặc hủy lượt. |
| validate_cad | Read-only, schema 2.0; mặc định full. Chi tiết các profile phía dưới. |
| edit_entity | Import vào phiên local, kể cả dry-run. Commit cần handle và expected_revision. Revision cũ bị từ chối; nguồn không ghi đè. |
| resolve_cad_collisions | Dry-run chỉ lập phương án; commit chỉ khi không còn xung đột/lỗi áp dụng. Output UUID local; tên yêu cầu là gợi ý. |
| convert_to_dwg | Không có ODA: UNAVAILABLE, giao DXF. Không tự cài hoặc gọi installer. Khả năng ODA thật cần kiểm thử trên máy có converter. |

## Compliance schema 2.0

`validate_cad(dxf_path, profile="full", beam_dxf_path=None, colwall_dxf_path=None)`.

- `physical`: kiểm tra DXF/entity/layer/graphic sanity, không chạy 20 cổng metadata.
- `plan`: 16 cổng mặt bằng; G8.13–16 NOT_APPLICABLE, không cộng vào PASS.
- `full`: 20 cổng; cần mặt bằng và chi tiết dầm/cột/vách. Thiếu bằng chứng → NEEDS_REVIEW.

Trạng thái tổng PASS chỉ khi các kiểm tra thuộc phạm vi đều PASS. Cổng FAIL
không bị physical PASS che mất. Cổng UNVERIFIED không được quy về PASS.
Lỗi syntax/entity cần sửa hoặc audit fixes trong RAM làm physical FAIL;
checker không ghi các sửa đổi đó xuống file nguồn.

Đọc `profile`, `status`, `physical_status`, `gate_status`, `gate_results`,
`gates_passed`, `gates_failed`, `gates_unverified`, `gates_not_applicable`.
`full_compliance_verified=true` chỉ cho full PASS đủ 20 cổng. `issues` chứa
cả lỗi vật lý lẫn cổng thất bại/chưa kiểm chứng.

Sidecar `<stem>.dce_audit.json`, `.beam_audit.json`, `.colwall_audit.json`
cần `provenance.dxf_sha256` khớp bytes của DXF tương ứng. Không tự lấy metadata
nhúng cũ làm bằng chứng cho bản vẽ đã sửa. Không cập nhật hash thủ công để
hợp thức hóa dữ liệu cũ. Metadata là bằng chứng của generator, không thay
kiểm tra độc lập hình học/native CAD hoặc xác nhận tính toán kết cấu.

CLI checker và MCP dùng cùng API; CLI exit 0 chỉ khi PASS:

```powershell
python -B "G:/My Drive/Google AI Studio/.agents/skills/SKILL_VERIFY/scripts/dce_cad_compliance_checker.py" "C:/path/plan.dxf" --profile physical
```

Khi nâng cấp caller cũ: nếu trước đây chỉ kiểm tra DXF vật lý, truyền profile
physical tường minh và ghi đúng phạm vi. Không coi response mặc định NEEDS_REVIEW
là lỗi hệ thống rồi tự fallback. DXF legacy không có metadata phải được giữ
trạng thái chưa kiểm chứng cho các cổng ngữ nghĩa.

## Vòng làm việc

Render/đọc DXF → resolve collisions → render_preview → consume_preview → validate_cad.
Khi sửa tay: inspect → dùng revision nhận được để commit → đọc lại → validate.
Output scratch được lưu local; chỉ sao chép sang nơi bàn giao khi có yêu cầu.
No GitHub push khi chưa có chấp thuận của User.

Suites 18, 28, 29, 30 kiểm tra compliance, guard, stdio MCP và collision solver.
Full acceptance vẫn chạy cả 30 suites; không lấy smoke tier thay nghiệm thu.
