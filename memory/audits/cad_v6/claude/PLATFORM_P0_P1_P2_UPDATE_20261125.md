# BÀN GIAO CẬP NHẬT NỀN TẢNG VẬN HÀNH P0+P1+P2 (CLAUDE → GEMINI)

> Ngày: 2026-11-25 | Người thực hiện: CLAUDE | Người nhận: GEMINI
> Phạm vi: hệ thống vận hành đa máy trạm (hooks, bootstrap, MCP, release/backup)
> **KHÔNG** thay đổi: tiêu chuẩn kỹ thuật CAD, schema BUS, công thức, deliverables

---

## 1. Bối cảnh sự cố (P0)

- Hook `.agents/hooks.json` và `.claude/settings.json` hardcode `C:/Users/ADMIN/.../Python312/python.exe`.
- Khi Drive sync sang máy `C:\Users\user` → "The system cannot find the path specified" → **toàn bộ tool ghi/chạy lệnh bị chặn** (fail-closed theo đúng thiết kế `onFailure: block`).
- Recovery: backup `.recovery-backup` + thay bằng `py -3`. Sau đó chuẩn hóa thành lớp P1/P2.

## 2. Nội dung đã triển khai

### P0 — Khôi phục hook
| File | Thay đổi |
|---|---|
| `.agents/hooks.json` | 2 command hook: `py -3 -I -X utf8 -B -S ...` (không còn user `ADMIN`) |
| `.claude/settings.json` | 5 command hook (PreToolUse/PostToolUse/UserPromptSubmit): cùng format trên |
| `*.recovery-backup` | Snapshot config trước recovery (giữ lại, không xóa) |
| `IMPLEMENTATION_PLAN.md` | Kế hoạch triển khai đầy đủ P0→P2 |

### P1 — Bootstrap đa máy + MCP
| File | Vai trò |
|---|---|
| `bootstrap/hook_bootstrap.cmd` | Wrapper fail-closed: cache → `PYTHON_EXECUTABLE` → `py.exe` → `python.exe`; loại stub WindowsApps; không có Python → exit 125. **Invariant: phải giữ CRLF** |
| `bootstrap/setup_machine.ps1` | 1 lần/máy: dò Python + 4 deps (mcp/ezdxf/shapely/matplotlib) + AutoCAD/ODA; ghi `LOCALAPPDATA\GoogleAIStudio\machine.json` (ngoài Drive); `-RegisterMcp` đăng ký dce-cad cho Antigravity; `-DryRun` chỉ in |
| `bootstrap/doctor.ps1` | Chẩn đoán 8 điểm chỉ-đọc; `-FailClosed` chạy ma trận (stub→125, python thật→0). **Chạy được bên ngoài Claude khi hook đang chặn** |
| `bootstrap/repair.ps1` | setup → doctor; không sửa BUS/shared config |
| `bootstrap/machine.example.json` | Mẫu manifest (không secret) |
| `bootstrap/README.md` | Tài liệu bootstrap |
| `.mcp.json` | Đăng ký `dce-cad` cho Claude Code (project-scoped, đường dẫn **tương đối**, không hardcode ổ đĩa) |
| `.agents/tests/test_bootstrap_matrix.py` (suite 34) | 4 case khóa fail-closed wrapper |
| `.agents/tests/test_setup_dce_cad_mcp.py` (suite 35) | 3 case khóa installer MCP (ghi user-level, không ghi Drive, idempotent, giữ env user) |

### P2 — Release, registry, backup
| File | Vai trò |
|---|---|
| `release/manifest_tool.py` | `make` / `verify` (SHA-256 × 9 file production + check CRLF wrapper), `bus-checksum` (CHỈ ĐỌC BUS), `register-machine` |
| `release/v1.0/manifest.json` | Release đầu tiên đã verify PASS |
| `release/machine_registry.json` | `LAPTOPTIENDUC` (Python 3.11.9, AutoCAD 2021, ODA=chưa, doctor PASS) |
| `release/bus_checksum.json` | Snapshot checksum BUS |
| `docs/OPERATIONS.md` | Quy trình hằng ngày, phát hành, rollback, phân quyền, degrade matrix |
| `docs/RECOVERY.md` | 6 kịch sự cố, mọi lệnh chạy bên ngoài hook |
| `docs/BACKUP_POLICY.md` | 3-2-1 + danh mục backup + kiểm tra toàn vẹn |
| `.agents/tests/test_release_manifest_tool.py` (suite 36) | 4 case khóa manifest tool (roundtrip, drift CRLF, BUS read-only, registry không secret) |

## 3. Bằng chứng kiểm thử

```text
run_all_tests.py --fast  → 27/27 suites PASS (109.56s), gồm suite 34/35/36 mới
test_antigravity_dual_bus_hook.py → 8/8 OK
test_workspace_claude_safety_hook.py → 7/7 OK
doctor.ps1 -FailClosed → 8/8 PASS; ma trận: stub WindowsApps → 125, real python → 0
manifest_tool.py verify --release-id v1.0 → PASS
```

## 4. Chính sách capability (degrade có chủ ý)

| Thiếu | Hành vi |
|---|---|
| Python / chỉ có stub WindowsApps | Hook exit 125, tool bị chặn (fail-closed) |
| ODA (máy này: CHƯA CÀI) | `convert_to_dwg` → `UNAVAILABLE`; render/validate/edit vẫn chạy |
| AutoCAD Core Console | `native_dwg_snapshot/diff` → `NEEDS_REVIEW`; tool DXF vẫn chạy |
| mcp SDK | Server `dce-cad` không khởi động; các client khác không bị ảnh hưởng |

## 5. Nhiệm vụ cho GEMINI

1. **Tổng hợp** bản cập nhật trên thành hướng dẫn vận hành chi tiết cho đội (theo khung `docs/OPERATIONS.md`, `docs/RECOVERY.md`, `docs/BACKUP_POLICY.md` — KHÔNG viết lại mâu thuẫn).
2. **Xác minh độc lập** trên máy mình (3 lệnh, không cần Claude):
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\bootstrap\doctor.ps1 -FailClosed
   py -3 -B release/manifest_tool.py verify --release-id v1.0
   py -3 -B release/manifest_tool.py bus-checksum
   ```
3. **Không tự động** mở HOLD: 2 điều kiện release Sprint 3 R2 (duyệt `02_XREF_ARCH_BG.dwg` + ký danh pháp lý) vẫn do người dùng chốt — ghi rõ trong báo cáo.
4. Khi thay đổi production (nếu cần): quy trình `test → make → verify` (OPERATIONS.md §4), không sửa trực tiếp.

## 6. Invariant phải giữ (vi phạm = verify FAIL hoặc hook hỏng)

- `bootstrap/hook_bootstrap.cmd` **CRLF** (ghi bằng tool Unix → LF → cmd parse lỗi; `verify` có check).
- Không đưa `machine.json` / cache / secret lên Drive hay Git.
- BUS chỉ chuyển trạng thái qua `sync_bus.py` (claim/complete/need-review); hook chỉ inject, không claim.
- Không auto-pickup tự claim ca; conflict Drive trên BUS → dừng, người xử lý.
- Wrapper không được thêm scan registry/PowerShell (giữ median hook < 100ms).

## 7. Điểm chưa hoàn tất (để GEMINI ghi vào hướng dẫn)

- Backup bản 2 (Git/NAS riêng) và bản 3 (ổ ngoài): policy đã có (BACKUP_POLICY.md), hạ tầng ở ngoài workspace do người dùng quyết nơi lưu.
- Đăng ký Codex: chưa làm, chờ xác định schema client.
- ODA trên máy này: chưa cài; `convert_to_dwg` degrade.
