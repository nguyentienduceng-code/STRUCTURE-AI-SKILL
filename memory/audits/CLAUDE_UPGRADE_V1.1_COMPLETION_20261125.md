# BÁO CÁO HOÀN THIỆN NÂNG CẤP PLATFORM v1.1 — CLAUDE

- **Ngày:** 2026-11-25
- **Tác tử:** CLAUDE (Software Architect / DevOps)
- **Ca:** SYSTEM_UPGRADE — hoàn thiện nâng cấp P0+P1+P2 theo `BRIEF_CLAUDE_AUDIT_REAL_WORKFLOW_20261125.md`
- **Bus:** KHÔNG ghi (theo lựa chọn bảo tồn ca `03_Sprint2_KetQua_NeChu_CAD` đang `NEED_REVIEW`). Báo cáo đặt tại đây cho Gemini đọc.

> **Báo này tuân thủ chuẩn P1 Report Gate (5 mục đọc máy):**
> 1. `SCOPE_DELIVERED` — sản phẩm đã bàn giao
> 2. `VERIFICATION_COMMAND` — lệnh chạy lại được
> 3. `RESULTS` — kết quả đo được (PASS/FAIL, số liệu)
> 4. `CONSTRAINTS` — đã KHÔNG làm gì, vì sao
> 5. `HANDOFF_CONTRACT` — hợp đồng giao tiếp ca kế tiếp

---

## 1. SCOPE_DELIVERED

Nâng cấp platform đa máy trạm đã hoàn thiện 3 tầng và cắt release `v1.1`:

**P0 — lỗi chặn release (đã vá):**
- `bootstrap/setup_machine.ps1` + `bootstrap/repair.ps1`: thêm BOM UTF-8, loại em-dash (`E2 80 94`) gây vỡ parse PowerShell 5.1 (code page 1252). Parse error: `4+1 → 0`.
- Pin runtime Python `3.12.7` (đủ dependency) vào 4 config: `.mcp.json`, `.agents/tools/mcp_config.json`, `.agents/hooks.json`, `.claude/settings.json` — thay `py -3` (trỏ Python 3.14.5 thiếu `mcp/ezdxf/shapely/matplotlib/pymupdf`).
- `release/manifest_tool.py`: vá parser nhận bare-flag `--write` (trước đó `bus-checksum --write` in checksum nhưng không ghi snapshot). Kèm regression test mới.

**P1 — hoàn thiện:**
- Đăng ký MCP user-level Antigravity: `setup_dce_cad_mcp.py` → `C:\Users\ADMIN\.gemini\antigravity\mcp_config.json` (tạo mới, trỏ server pin 3.12.7).
- `release/machine_registry.json`: thêm bản ghi `TIENDUC / 3.12.7` (giữ lịch sử `LAPTOPTIENDUC / 3.11.9`).
- `.agents/skills/Global_Dispatcher/intent_classifier.py`: vá UTF-8 stdout (trước đó crash `UnicodeEncodeError` code page 1252 khi chạy automation).
- `.agents/tests/test_setup_dce_cad_mcp.py`: cập nhật assertion từ pin `-3` → `-3.12` (khớp quyết định runtime mới).

**P2 — dọn dẹp & cắt release:**
- Dọn `.pytest_cache/`, `release/__pycache__/`, `.agents/memory/audits/__pycache__/`, `*.cpython-314.pyc` (0 pyc 3.14 còn lại).
- `IMPLEMENTATION_PLAN.md` (gốc workspace) → `docs/IMPLEMENTATION_PLAN.md` (không có script tham chiếu).
- Cắt **`release/v1.1`**: `make --release-id v1.1 --tests-passed "60/60"` + `verify` PASS (9 hash + CRLF).

**9 tệp khóa v1.0 được cập nhật (đã khóa lại bằng manifest v1.1):**
`.agents/hooks.json`, `.claude/settings.json`, `.agents/tools/claude_safety_hook.py`, `.agents/tools/antigravity_dual_bus_hook.py`, `.agents/tools/mcp_dce_cad_server.py`, `.agents/tools/mcp_config.json`, `.mcp.json`, `bootstrap/hook_bootstrap.cmd`, `release/manifest_tool.py`.

---

## 2. VERIFICATION_COMMAND

```bash
# (1) Verify manifest v1.1 (hash + CRLF) — mong: "VERIFY PASS: release v1.1"
py -3.12 -B release/manifest_tool.py verify --release-id v1.1

# (2) Bus snapshot giờ ghi được (chứng minh vá bare-flag) — mong: "BUS CHECKSUM GHI: ... -> release/bus_checksum.json"
py -3.12 -B release/manifest_tool.py bus-checksum --write

# (3) Full regression 60/60 — mong: "TẤT CẢ TEST SUITES ĐỀU VƯỢT QUA"
py -3.12 -B .agents/tests/run_all_tests.py --full --report-dir .agents/memory/audits/ci_run_v11_final

# (4) Zero-white-text audit — mong: "0 WARNINGS"
py -3.12 -B .agents/tools/audit_zero_white_text.py .agents

# (5) PowerShell 5.1 parse (chứng minh vá encoding) — mong: 0 parse errors mỗi file
powershell -NoProfile -ExecutionPolicy Bypass -File <ps script ParseFile setup_machine.ps1 & repair.ps1>

# (6) MCP handshake bằng runtime pin 3.12 — mong: JSON-RPC initialize trả serverInfo "dce-cad"
printf '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"x","version":"0"}}}' | py -3.12 -B .agents/tools/mcp_dce_cad_server.py
```

---

## 3. RESULTS

| # | Hạng mục | Kết quả đo được |
|---|---|---|
| 1 | `manifest_tool.py verify --release-id v1.1` | **PASS** (hash + CRLF) |
| 2 | `bus-checksum --write` | **PASS** — tạo `release/bus_checksum.json` (SHA-256 `422a1d53…`) |
| 3 | Full suite 60/60 (`ci_run_v11_final`) | **60/60 PASS, exit 0**, "TẤT CẢ TEST SUITES ĐỀU VƯỢT QUA" (440.01s) |
| 4 | Zero-white-text audit `.agents` | **528 files / 29 modules, 0 warnings** |
| 5 | PowerShell 5.1 parse `setup_machine.ps1` | **0 parse errors** (trước 4) |
| 5b | PowerShell 5.1 parse `repair.ps1` | **0 parse errors** (trước 1) |
| 6 | MCP `dce-cad` handshake bằng `py -3.12` | **PASS** — trả `serverInfo.name=dce-cad`, protocol `2024-11-05` |
| 7 | Hook pin `py -3.12` (lệnh đúng trong settings.json) | **exit 0** với payload hợp lệ |
| 8 | Registry | `LAPTOPTIENDUC/3.11.9` (giữ) + `TIENDUC/3.12.7` (mới) |
| 9 | pyc 3.14 còn lại | **0** |
| 10 | BUS SHA (bảo tồn) | **`422a1d5380a52245…` — không đổi** |
| 10b | `_CA_HIEN_TAI.md` ↔ `DUAL_AGENT_HANDOFF_MEMO.md` | **byte-match** (7022 bytes) |

**Lưu ý giải thích (không phải lỗi):** `verify --release-id v1.0` giờ trả **DRIFT** trên 5 tệp đã nâng cấp (hooks/settings/mcp_config/.mcp.json/manifest_tool.py). Đây là hậu quả đúng kỳ vọng của việc cắt v1.1 — v1.1 là release hoạt động mới, v1.0 chỉ còn giá trị đối chiếu lịch sử.

**Bằng chứng SHA-256 (11 tệp đã sửa):**
```
.agents/hooks.json                       fdf04eb66158
.claude/settings.json                   d8e8f4368497
.agents/tools/mcp_config.json           6473375c87ce
.mcp.json                               06c42f88f7fe
bootstrap/setup_machine.ps1             639b38e2fd4b
bootstrap/repair.ps1                   2df988bf5398
release/manifest_tool.py                145270ad70fc
release/machine_registry.json           69fc77127963
.agents/tests/test_setup_dce_cad_mcp.py 7842962d25f6
.agents/tests/test_release_manifest_tool.py 4096da12c30d
.agents/skills/Global_Dispatcher/intent_classifier.py fd82ee75fea1
```

---

## 4. CONSTRAINTS (đã KHÔNG làm gì, vì sao)

1. **KHÔNG ghi `DUAL_AGENT_BUS.json`** — theo ràng buộc brief gốc và lựa chọn người dùng "bảo tồn ca Sprint3 R2". Bus giữ nguyên ca `03_Sprint2_KetQua_NeChu_CAD` ở `NEED_REVIEW`, holder `IDLE`.
2. **KHÔNG xóa bản ghi cũ registry** — giữ `LAPTOPTIENDUC/3.11.9` để bảo tồn lịch sử máy.
3. **KHÔNG move hay xóa file CAD dự án / secret / cache trong shared source** — P2 chỉ dọn cache artifact + move 1 file kế hoạch.
4. **KHÔNG chạy `doctor.ps1` trên máy trạm khác** — chỉ kiểm chứng được trên máy hiện tại (TIENDUC).
5. **v1.1 chưa qua thẩm tra độc lập** — báo này là bản tự kiểm (self-check) của CLAUDE; cần đối tác (Gemini/Codex) xác nhận đúng phiên bản trước khi coi là `CONFIRMED_AND_HANDED_OFF`.
6. **Không sửa allowlist lịch sử trong `.claude/settings.json`** ngoài phạm vi pin runtime.

---

## 5. HANDOFF_CONTRACT

- **Sản phẩm bàn giao:** platform v1.1 (runtime pin Python 3.12.7, PS 5.1 parse sạch, manifest tool vá, registry + MCP registration hoàn chỉnh, 60/60 suite xanh).
- **Giao diện cho ca kế tiếp (Gemini/Codex):**
  - Cốt lõi: `release/v1.1/manifest.json` (nguồn sự thật hash 9 tệp) + `release/machine_registry.json`.
  - Vận hành: `bootstrap/doctor.ps1` (PASS trên TIENDUC), `bootstrap/repair.ps1`.
  - Lệnh xác thực nhanh: mục 2 (VERIFICATION_COMMAND) ở trên.
- **Hợp đồng nghiệm thu độc lập (Gemini chạy, cùng v1.1):**
  1. `py -3.12 -B release/manifest_tool.py verify --release-id v1.1` → `VERIFY PASS`.
  2. `py -3.12 -B .agents/tests/run_all_tests.py --full` → 60/60 PASS (report thư mục mới).
  3. `py -3.12 -B .agents/tools/audit_zero_white_text.py .agents` → 0 warnings.
  4. Đối chiếu SHA-256 11 tệp (mục 3) khớp hash v1.1 cho 9 tệp khóa; 2 tệp test là bổ trợ.
  5. Xác nhận BUS SHA vẫn `422a1d53…` (ca Sprint3 R2 còn treo → tiếp tục ca đó sau khi đóng v1.1).

**Trạng thái đề xuất cho ca v1.1:** `NEED_REVIEW` (đợi đối tác xác nhận cùng v1.1), KHÔNG phải `COMPLETED` vì chưa qua thẩm tra độc lập.

---

## 6. LỆNH BÀN GIAO QUA BUS (chạy KHI ca Sprint3 R2 đã đóng)

Bus là slot đơn — lệnh này DẼ ca Sprint3 R2 hiện có. Chỉ chạy sau khi ca đó kết thúc, hoặc khi người dùng chấp nhận overwrite. Theo lựa chọn hiện tại ("bảo tồn ca Sprint3 R2"), lệnh này được ghi sẵn nhưng **CHƯA THỰC THI**:

```bash
# Bàn giao ca nâng cấp v1.1 cho Gemini (khi slot bus trống — ca R2 đã đóng):
py -3.12 -B .agents/tools/sync_bus.py --auto --sender CLAUDE --target GEMINI \
  --project MASTER_SYSTEM --action-type INFRA \
  --task "Tham tra doc lap release v1.1 (pin runtime 3.12.7, PS 5.1 parse, manifest tool, registry, MCP registration)" \
  --deliverable "Bao cao CLAUDE_UPGRADE_V1.1_COMPLETION_20261125.md + manifest v1.1 VERIFY PASS + 60/60 suite" \
  --evidence-files ".agents/memory/audits/CLAUDE_UPGRADE_V1.1_COMPLETION_20261125.md,release/v1.1/manifest.json,release/bus_checksum.json" \
  --check-evidence-on-disk \
  --acceptance-cmd "py -3.12 -B release/manifest_tool.py verify --release-id v1.1" \
  --criteria "verify v1.1 PASS;60/60 suite PASS;0 white-text warnings;BUS SHA 422a1d53 khong doi" \
  --files ".agents/hooks.json,.claude/settings.json,.mcp.json,release/manifest_tool.py,bootstrap/setup_machine.ps1,bootstrap/repair.ps1" \
  --confirm
```
