# MCP DCE CAD — hợp đồng triển khai v2.0 (2026-11-22 — Tầng 2A)

Entry point: `tools/mcp_dce_cad_server.py`; cấu hình mẫu `tools/mcp_config.json` (**13 tools MCP**).
MCP dùng stdio JSON-RPC. Log engine đi stderr; stdout dành cho giao thức.
Không cần AutoCAD đang chạy để dùng các tool DXF/preview.

| # | Tool | Hành vi và điều kiện |
|---|---|---|
| 1 | `render_cad_plan` | KC-01/02/03/CUSTOM_MULTIVIEW; model JSON và template tùy chọn, hỗ trợ `full_evidence=True`. Output UUID local. Dry-run không lưu DXF. Sheet không hợp lệ/đầu vào không tồn tại trả `E001`. |
| 2 | `render_preview` | DXF → PNG local; dùng `output_png` và `preview_id`. |
| 3 | `consume_preview` | Trả `ImageContent`, xóa backing PNG sau khi đọc; token một lần. |
| 4 | `release_preview` | Dọn preview khi caller đã đọc file hoặc hủy lượt. |
| 5 | `validate_cad` | Read-only, schema 2.0; hỗ trợ đủ **5 profile** (`full`, `plan`, `physical`, `steel_peb`, `bptc`) / **25 cổng G8.01..G8.25**. |
| 6 | `edit_entity` | Import vào phiên local, kể cả `dry_run`. Commit cần `handle` và `expected_revision`. Revision cũ bị từ chối; nguồn không ghi đè. |
| 7 | `resolve_cad_collisions` | Dry-run chỉ lập phương án; commit chỉ khi không còn xung đột/lỗi áp dụng. Bảo toàn vùng kỹ sư (`DCE_USER_OVERRIDE`). |
| 8 | `convert_to_dwg` | Không có ODA: `UNAVAILABLE`, giao DXF. Không tự cài hoặc gọi installer. |
| 9 | `auto_layout_and_scale_plan` | Tính toán tỷ lệ động (Sheet-Scale Governor `1:50`..`1:250`) và dàn trang A1/A0 tự động không tràn khung. |
| 10 | `export_cad_sheet_set` | Xuất bộ hồ sơ đa bản vẽ chuẩn `cad_sheet_set.py` (AC1021) kèm chỉ mục bảng vẽ & kiểm tra nhất quán liên tờ. |
| 11 | `open_form` | Mở form bản vẽ chuẩn hóa 3 tầng (Dự án → Chuẩn người dùng → SSOT) để nhập/hiệu chỉnh thông số an toàn. |
| 12 | `diff_form` | So sánh sai lệch form CAD đã chỉnh tay với SSOT (`baseline='ssot'`) tạo `model_patches` có cấu trúc. |
| 13 | `apply_agent_changes` | Merge-lane khóa vùng `DCE_AGENT_OWNED`: kiểm tra `structural_schema_gate`, nâng `model_version` (`v+1`) & chỉ tái sinh tờ ảnh hưởng. |

## Compliance schema 2.0 (5 Profiles / 25 Gates)

`validate_cad(dxf_path, profile="full", beam_dxf_path=None, colwall_dxf_path=None)`.

- `physical`: kiểm tra DXF/entity/layer/graphic sanity, không chạy cổng metadata.
- `plan`: 16 cổng mặt bằng; G8.13–16 `NOT_APPLICABLE`, không cộng vào `PASS`.
- `full`: 20 cổng BTCT (`G8.01..G8.20`); cần mặt bằng và chi tiết dầm/cột/vách. Thiếu bằng chứng → `NEEDS_REVIEW`.
- `steel_peb`: mở rộng kiểm tra kết cấu thép tiền chế (`G8.21` bu lông/đường hàn TCVN 5575:2024, `G8.22` đối soát BOM thép `<= 1%`, `G8.23` bố cục `COMPOSITE_DETAIL_GRID`).
- `bptc`: mở rộng kiểm tra Biện pháp Thi công (`G8.24` vùng nguy hiểm & bán kính cẩu tháp theo QCVN 18:2021/BXD, `G8.25` liên kết XData thép & bảng thống kê).

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
