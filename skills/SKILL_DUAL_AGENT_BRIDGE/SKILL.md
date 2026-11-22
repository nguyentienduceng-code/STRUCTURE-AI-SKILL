---
name: SKILL_DUAL_AGENT_BRIDGE
version: 3.4.0
last_updated: 2026-11-20
description: "Giao thức và quy trình chuẩn điều phối làm việc song song hoặc luân phiên giữa Gemini (Antigravity) và Claude (Claude Code / Desktop). Đảm bảo tính nguyên tử của dữ liệu, loại bỏ xung đột file trên Google Drive, khóa phần vùng an toàn, kiểm toán chéo định lượng. v3.2: SSOT chống trùng lặp, Lease/Heartbeat chống ca treo, Project-Scoped Path Resolver, Visual Gate (Điều 12d Enforcer). v3.3: Product-First handoff (deliverable/evidence_files/acceptance_cmd), Visual Gate evidence-based (bằng chứng phải TỒN TẠI trên đĩa, SHA-256), RECEIPTS (mọi --force để lại dấu vết audit), P1 Report Gate (chuẩn RESULT.md 5 mục theo ca, layout cad_v6). v3.4: 2D Dual-Plane & ProductDeliverableGate (Control Plane / Presentation Plane, Jargon Linter, 04_Deliverables_ToTrinh validation)."
triggers:
  - "Khi người dùng yêu cầu bàn giao công việc giữa Gemini và Claude"
  - "Khi cần phối hợp 2 AI cùng làm việc đồng thời trên một dự án"
  - "Khi cần thẩm tra chéo độc lập (Red-Team Audit, Verification) giữa 2 Agent"
  - "Khi đồng bộ trạng thái qua .agents/memory/DUAL_AGENT_BUS.json hoặc DUAL_AGENT_HANDOFF_MEMO.md"
---

# 🛰️ SKILL_DUAL_AGENT_BRIDGE: CẦU NỐI ĐIỀU PHỐI ĐA TÁC TỬ (GEMINI ⚔️ CLAUDE)

> **Cơ sở vận hành:** Hệ thống Bus nguyên tử `.agents/memory/DUAL_AGENT_BUS.json` & Biên bản ca trực `.agents/memory/DUAL_AGENT_HANDOFF_MEMO.md`.  
> **Nguyên tắc cốt lõi:** Tuyệt đối không để 2 AI giẫm chân lên nhau (Zero-Collision), không thất thoát ngữ cảnh (Zero-Context-Leak), và nghiệm thu bằng số liệu cứng (Deterministic Criteria).

> **🏛️ KIẾN TRÚC SSOT v3.2 (Single Source of Truth):** Toàn bộ logic của bus sống duy nhất tại **`.agents/tools/sync_bus.py`**. Bản tại `.agents/skills/SKILL_DUAL_AGENT_BRIDGE/scripts/sync_bus.py` là **thin wrapper** (chỉ đại diện CLI + import, alias module vào `sys.modules["sync_bus"]` để bảo toàn cơ chế monkey-patch của test suite). Mọi bugfix/feature thực thi tại SSOT; wrapper tự kế thừa, không cần đồng bộ mã.

---

## 1. BA KỊCH BẢN PHỐI HỢP ĐỒNG THỜI (OPERATIONAL MODES)

Hệ thống hỗ trợ 3 chế độ cộng tác linh hoạt tùy theo tính chất công việc:

Đọc `agent_selection` và `use_dual_agent_bus` từ phiếu Global_Dispatcher trước khi bàn giao. Với CLAUDE_ONLY hoặc GEMINI_ONLY, tác tử được chọn tự chạy chuỗi skill và kiểm tệp theo phiếu. Dùng bước xác nhận độc lập của con người khi công việc yêu cầu. Với ca phối hợp, truyền `--dispatch-ticket` qua lệnh bàn giao để giữ định danh dự án và tiêu chí nghiệm thu cùng phiên bản.

### 1.1 Kịch bản A: Luân phiên ca trực (Relay / Sequential Handoff)
- **Áp dụng:** Khi một tác tử hoàn thành một giai đoạn (Sprint/Phase) và cần bàn giao toàn bộ cho tác tử kia tiếp quản.
- **Quy trình:**
  1. **Agent hoàn thành:** Chạy lệnh `--auto` hoặc ghi nhận tệp đã sửa, chuyển trạng thái bus sang `PENDING`, chỉ định rõ `target_agent: "CLAUDE"` (hoặc `GEMINI`).
  2. **Agent tiếp nhận:** Kiểm tra bus (`--read`), kích hoạt nhận ca (`--claim`), trạng thái chuyển sang `IN_PROGRESS` và `current_holder: "<AGENT_NAME>"`.
  3. **Thực thi:** Làm theo danh sách `target_files` và hoàn thành từng mục trong `acceptance_criteria`.
  4. **Nghiệm thu:** Chạy `--complete` để đóng ca hoặc `--need-review` để mời đối tác kiểm tra chéo.

### 1.2 Kịch bản B: Làm việc song song có phân vùng (Partitioned Parallel Co-Working)
- **Áp dụng:** Khi cả Gemini và Claude cùng mở và làm việc trong cùng một phiên làm việc (ví dụ: Gemini phụ trách Backend/Calculators, Claude phụ trách Frontend/Docs).
- **Quy tắc bất khả xâm phạm:**
  - **Phân tách tập tệp (Disjoint Sets):** `target_files` của Gemini và `target_files` của Claude **TUYỆT ĐỐI KHÔNG GIAO NHAU**.
  - **Khóa cục bộ (Local File Lock):** Khóa `FileLock` đặt tại `%LOCALAPPDATA%/GoogleAIStudio/locks/` để đảm bảo khi một bên ghi dữ liệu thì bên kia không thể tranh chấp.
  - **Đồng bộ Bus:** Mỗi bên chỉ cập nhật phân đoạn phụ trách của mình vào bus.

### 1.3 Kịch bản C: Thẩm tra đối kháng & Độc lập (Red-Team Adversarial Audit)
- **Áp dụng:** Thẩm định thiết kế kết cấu, kiểm toán thuật toán tài chính (như Crypto-Gold Quant) hoặc review code an toàn trước khi commit.
- **Quy trình:**
  - **Agent 1 (Maker):** Triển khai tính năng, tạo file và ghi nhận log tính toán.
  - **Agent 2 (Breaker / Auditor):** Đóng vai trò phản biện, cố tình thử nghiệm các trường hợp biên (Edge cases), kiểm tra chuẩn TCVN/Eurocode/TypeScript types.
  - **Consensus Matrix:** Chỉ khi Agent 2 xác nhận `APPROVE` và không còn `divergenceFlags`, mã nguồn hoặc tài liệu mới được chốt phê duyệt chính thức.

---

## 2. QUY CHUẨN DỮ LIỆU BUS NGUYÊN TỬ (JSON SCHEMA v3.0)

File `.agents/memory/DUAL_AGENT_BUS.json` bắt buộc tuân thủ cấu trúc sau:

```json
{
  "project_context": {
    "project_code": "00_MANAGEMENT_QLTK",
    "project_purpose": "Mô tả ngắn gọn mục tiêu của dự án",
    "role_distribution": "Phân vai linh hoạt: Ai làm thiết kế, ai làm thẩm tra",
    "action_type": "DYNAMIC | RELAY | PARALLEL | AUDIT"
  },
  "last_updated_by": "GEMINI | CLAUDE",
  "timestamp": "ISO-8601 with timezone (e.g. 2026-11-07T09:30:00+07:00)",
  "handoff_status": "PENDING | IN_PROGRESS | COMPLETED | NEED_REVIEW",
  "current_holder": "GEMINI | CLAUDE | IDLE",
  "summary": "Tóm tắt súc tích các công việc đã làm trong lượt này",
  "artifacts_modified": [
    ".agents/tools/sync_bus.py",
    ".agents/memory/DUAL_AGENT_BUS.json"
  ],
  "next_action_for_partner": {
    "target_agent": "CLAUDE | GEMINI",
    "task_description": "Chỉ thị hành động cụ thể, không dùng ngôn ngữ mơ hồ",
    "target_files": [
      "src/components/MyComponent.tsx",
      "docs/SPEC.md"
    ],
    "acceptance_criteria": [
      "Tiêu chí định lượng 1 (ví dụ: Test suite PASS 100%)",
      "Tiêu chí định lượng 2 (ví dụ: Không còn lỗi TypeScript)"
    ],
    "command": "Câu lệnh hoặc hướng dẫn ngắn để đối tác bắt đầu ngay"
  },
  "Verification_Status": "CONFIRMED_AND_HANDED_OFF | UNVERIFIED"
}
```

---

## 3. NGUYÊN TẮC KỸ THUẬT CỨNG (HARD RULES)

1. **Chuẩn hóa Đường dẫn Tương đối POSIX (POSIX Relative Paths):**
   - 100% tệp trong `artifacts_modified` và `target_files` bắt buộc dùng định dạng `path/to/file.ext` (dấu `/`, bắt đầu từ thư mục gốc).
   - **CẤM:** Dùng đường dẫn tuyệt đối chứa ổ đĩa (`G:\...`, `D:\...`) hoặc dấu gạch chéo ngược `\` (tránh lỗi JSON escape và tiết kiệm context).

2. **Cơ chế Khóa Nguyên tử Không phụ thuộc Cloud (Local AppData Lock):**
   - Tệp khóa `dual_agent_bus.lock` được đặt ở `%LOCALAPPDATA%`, tuyệt đối không đặt trên ổ Google Drive để tránh deadlock do độ trễ đồng bộ mạng.

3. **Ghi tệp an toàn (Atomic Write with Fsync):**
   - Mọi thao tác ghi bus đều ghi qua tệp tạm ẩn `.{stem}.tmp.{pid}`, gọi `os.fsync()`, rồi mới đổi tên `os.replace()`.

4. **Xử lý Xung đột Google Drive (Drive Conflict Hygiene):**
   - Trước khi nhận ca hoặc khi kết thúc ca, tự động quét các file có đuôi `(1)`, `(2)`. So sánh mtime và hash để bảo tồn bản sửa đổi mới nhất, không xóa nhầm dữ liệu.
5. **Visual & Real-Model Gate Trước Khi Bàn giao (Bài học 2026-11-15 — Chống Ping-Pong Token):**
   - **Cấm bàn giao sang đối tác/Auditor (CODEX/CLAUDE/GEMINI)** khi mới chỉ pass JSON schema trên fixture giả lập. Với task CAD, bên làm phải tự chạy qua engine thật (`DcePlanEngine` + `DCE_Master_Seed_Template.dxf` / MCP `dce-cad`) và tự soi ảnh preview (`render_preview`) trước khi đặt `NEED_REVIEW` hay `COMPLETED`.
   - **Chốt Acceptance Checklist tối đa 5 cổng đo được** ngay từ đầu task; không thêm tiêu chí bất ngờ giữa chừng.
   - **Đóng milestone phải dọn log vào `archive/`** và cập nhật về SSOT (`README.md` / `SKILL.md`), tránh để Agent phiên sau tốn token đọc hàng trăm file audit lịch sử.

---

## 4. HỆ THỐNG LỆNH CLI ĐIỀU PHỐI (`sync_bus.py`)

Công cụ điều phối đặt tại `.agents/tools/sync_bus.py` (SSOT):

```bash
# 1. Đọc trạng thái hiện tại của Bus:
python .agents/tools/sync_bus.py --read

# 2. Agent nhận ca (Khóa bus, ngăn Agent kia ghi đè):
python .agents/tools/sync_bus.py --claim --agent CLAUDE

# 2b. v3.2: Agent gia hạn lease ca trực (chống ca treo khi crash/quota hết):
python .agents/tools/sync_bus.py --heartbeat --agent CLAUDE

# 3. Hoàn tất ca làm việc và mở khóa:
python .agents/tools/sync_bus.py --complete --agent CLAUDE --summary "Đã hoàn tất tính toán dầm D1"

# 4. Yêu cầu Agent đối tác kiểm tra / thẩm tra chéo:
python .agents/tools/sync_bus.py --need-review --agent CLAUDE

# 5. Tự động bàn giao ca có tiêu chí nghiệm thu:
python .agents/tools/sync_bus.py --auto --sender GEMINI --target CLAUDE \
    --project 00_MANAGEMENT_QLTK --purpose "Đồng bộ giao thức Bus v3.2" \
    --task "Kiểm tra chéo và chạy kiểm thử tự động" \
    --criteria "100% test Suite PASS;Không còn file xung đột Drive" --confirm

# 5b. v3.2: Thu hẹp phạm vi scan artifacts theo đúng dự án đang làm:
python .agents/tools/sync_bus.py --auto --sender CLAUDE --target GEMINI \
    --project 16_BPTC_Q12 --project-dir 01_Projects/16.BPTC\ Q12 \
    --task "Bàn giao kết quả mặt bằng kết cấu DCE" --criteria "Preview .png đính kèm" --confirm

# 6. Quét và dọn dẹp file xung đột Google Drive an toàn:
python .agents/tools/sync_bus.py --scan-conflicts
python .agents/tools/sync_bus.py --clean-conflicts --confirm

# 5c. v3.3: Bàn giao PRODUCT-FIRST (khai báo sản phẩm + bằng chứng + lệnh nghiệm thu):
python .agents/tools/sync_bus.py --auto --sender CLAUDE --target GEMINI \
    --action-type CAD \
    --deliverable "1 ban ve DXF KC-02 + audit log PASS" \
    --evidence-files "out/preview.png" --check-evidence-on-disk \
    --acceptance-cmd "python .agents/tools/dce_render_preview.py out/kc02.dxf out/preview.png" \
    --task "Xuat ban ve KC-02" --files ".agents/tools/dce_render_preview.py"

# 5d. v3.3 P1: Bàn giao kèm báo cáo pha (Report Gate — chuẩn RESULT.md 5 mục theo cad_v6):
python .agents/tools/sync_bus.py --auto --sender CLAUDE --target GEMINI \
    --project CAD_V6 --action-type CAD --phase C1 \
    --task "Kiem tra mat bang ket cau DCE" \
    --deliverable "1 DXF KC-03 + preview PNG" \
    --evidence-files "out/preview.png" --check-evidence-on-disk \
    --acceptance-cmd "python -m unittest discover -s tests" \
    --emit-report --files ".agents/tools/sync_bus.py"
```

> **📄 Chuẩn báo cáo pha (P1 Report Gate):** ca GATED (`--action-type CAD/DOCX/REPORT_VISUAL`)
> **bắt buộc** kèm `report_file` (báo cáo RESULT.md) TỒN TẠI trên đĩa khi khép ca / request review.
> Layout chuẩn theo cad_v6 (cả 2 phía đã dùng): `.agents/memory/audits/<project>/<agent>/<PHASE>_RESULT.md`
> (vd `cad_v6/claude/C1_RESULT.md`). `--emit-report` sinh skeleton **5 mục cố định**
> (đọc máy được bởi Codex/đối tác):
> 1. `SCOPE_DELIVERED` — sản phẩm/scope đã bàn giao; 2. `VERIFICATION_COMMAND` — lệnh chạy lại được;
> 3. `RESULTS` — kết quả đo được (số liệu, PASS/FAIL); 4. `CONSTRAINTS` — đã KHÔNG làm gì, vì sao;
> 5. `HANDOFF_CONTRACT` — hợp đồng giao diện cho ca kế tiếp.
> Cờ `--emit-report` **không ghi đè** file đã tồn tại; ca legacy (CODE/META/…) không bị ảnh hưởng.

**Cờ `--force` (bắt buộc ghi rõ khi dùng):** Bỏ qua cảnh báo IN_PROGRESS (lease active) VÀ Visual Gate (Điều 12d) để ghi đè bus. v3.3: **mọi `--force` đều sinh RECEIPT** (phiếu audit: lý do + hash bằng chứng SHA-256 + chữ ký) — bypass không còn "vô danh". Kèm `--receipt-reason "<lý do>"`.

### 4.1. Nâng cấp Kiến trúc v3.2 (4 Trọng tâm)

| # | Nâng cấp | Hành vi | Cờ / Trường |
|---|----------|---------|-------------|
| 1 | **SSOT Khử trùng lặp** | Logic tập trung tại `tools/sync_bus.py`; bản `scripts/` là thin wrapper alias module | `import sync_bus` → SSOT |
| 2 | **Lease / Heartbeat** | Ca IN_PROGRESS kèm `lease_expire_at` (mặc định 60 phút, env `DUAL_AGENT_LEASE_MIN`). Hết hạn mà không heartbeat → đối tác auto-claim không cần `--force` | `--heartbeat`, `--force` |
| 3 | **Project-Scoped Resolver** | Chuẩn hóa mọi artifact về gốc workspace; `--project-dir` thu hẹp scan tránh gom nhầm dự án khác | `--project-dir` |
| 4 | **Visual Gate (Điều 12d)** | Task CAD/Bản vẽ bắt buộc ≥1 bằng chứng (`preview.png` / `_verification.json`) trong artifacts trước khi PENDING/NEED_REVIEW/COMPLETED | `--complete-files`, `--force` |

### 4.2. Nâng cấp Kiến trúc v3.3 (Product-First Handoff — 4 Điểm)

| # | Nâng cấp | Hành vi | Cờ / Trường |
|---|----------|---------|-------------|
| 1 | **Product-First Schema** | Ca bàn giao khai báo tường minh: `deliverable` (sản phẩm mong đợi), `evidence_files` (bằng chứng), `acceptance_cmd` (lệnh chạy lại được để tự chứng minh). Không khai báo → bus hoạt động như v3.2 (backward-compatible) | `--deliverable`, `--evidence-files`, `--acceptance-cmd` |
| 2 | **Visual Gate v2 (Evidence-Based)** | Kích hoạt theo `--action-type`: CAD/DOCX/REPORT_VISUAL → bắt buộc bằng chứng; CODE/META/INFRA/TEST/DOCS → miễn; không khai báo → fallback dò keyword (hành vi v3.2). Cờ `--check-evidence-on-disk` yêu cầu file bằng chứng **THẬT SỰ TỒN TẠI trên đĩa** (băm SHA-256) — không chấp nhận danh khai suông | `--action-type`, `--check-evidence-on-disk` |
| 3 | **RECEIPTS (Phiếu nghiệm thu)** | Ca `NEED_REVIEW`/`COMPLETED` và MỌI `--force` sinh 1 receipt JSON vào `.agents/_SHARED/SHARED_CONTEXT/_active/RECEIPTS/`: hash bằng chứng, trạng thái gate, lý do force, chữ ký agent. Codex A1 nghiệm thu độc lập dựa trên bằng chứng, không phải tin lời bus | tự động; `--receipt-reason` |
| 4 | **P1 Report Gate (chuẩn RESULT.md theo ca)** | Ca GATED (CAD/DOCX/REPORT_VISUAL) **bắt buộc kèm báo cáo pha** `report_file` (RESULT.md) tồn tại trên đĩa khi khép ca / review. `--emit-report` sinh skeleton 5 mục đọc máy được, layout chuẩn cad_v6 `<project>/<agent>/<PHASE>_RESULT.md`; không ghi đè file có sẵn | `--emit-report`, `--report-file`, `--phase` |

> **Nguyên tắc tương thích ngược (v3.3):** Toàn bộ API/CLI v1.0–v3.2 vẫn hoạt động không đổi. Các trường Product-First chỉ xuất hiện trong payload khi được khai báo; ca legacy (không `action_type`, không `evidence_files`) qua gate đúng hành vi v3.2 (keyword + danh khai artifacts).

> **Nguyên tắc tương thích ngược (v3.2, vẫn hiệu lực):** Bus cũ không có mốc thời gian (legacy) vẫn được bảo vệ — bắt buộc `--force` để tiếp quản; v3.3: bypass đó sinh RECEIPT audit.

---

---

## 4.3. Nâng cấp Kiến trúc v3.4 (2D Dual-Plane & ProductDeliverableGate — 2026-11-20)

Áp dụng song song với **Điều 0 (`AGENTS.md`)** khi bàn giao qua `sync_bus.py` và `handover_task.py`:

1. **Tách 2 lớp Control Plane / Presentation Plane:**
   - **Control Plane (`bus_meta`):** Giữ nguyên khóa nguyên tử, `receipts`, `evidence_hashes` (SHA-256) chạy ngầm để chống hỏng file Google Drive.
   - **Presentation Plane (`human_handoff`):** Ở chế độ `PRODUCT_COLLAB`, mọi báo cáo trả người dùng phải viết 100% tiếng Việt kỹ thuật theo đúng **3 ý**: *(1) Đã sửa gì? (2) File ở đâu? (3) Số liệu đạt hay không?* Cấm biệt ngữ lập trình (`SSOT`, `unpack`, `receipt`, `SHA-256`, `gate=PASS`, `force=False`, `mock`, `IPC`, `POSIX`).
2. **Cổng Nghiệm thu Hồ sơ (`ProductDeliverableGate`):**
   - `sync_bus.py` tự động gọi `_verify_product_ticket()` trước khi đóng ca `PRODUCT_COLLAB`.
   - Từ chối đóng ca (`BLOCKED_MISSING_DELIVERABLE`) nếu chỉ ghi file `.md` vào `.agents/memory/audits/` hoặc `.claude/memory/` mà không có file `.docx`/`.pdf`/`.dxf`/`.xlsx` mới trong `04_Deliverables_ToTrinh/`.
   - Từ chối đóng ca (`BLOCKED_JARGON_VIOLATION`) nếu báo cáo người dùng lẫn biệt ngữ dev.
3. **Chọn tác tử & Phiếu công việc (`--agent-selection` & `--dispatch-ticket`):**
   - `handover_task.py` và `sync_bus.py` hỗ trợ `--agent-selection AUTO|CLAUDE_ONLY|GEMINI_ONLY|DUAL` và `--dispatch-ticket <tệp phiếu JSON>`.
   - Ở chế độ `SOLO_EXECUTION`, `SyncBus2DAdapter` trả về `None` và **không ghi `DUAL_AGENT_BUS.json`** để triệt tiêu độ trễ.

## 5. MẪU LỆNH CHUYỂN TIẾP NHANH (PROMPT TEMPLATES)

### Khi Gemini bàn giao sang Claude:
> *"Claude ơi, tôi đã hoàn tất công việc ở phần của mình. Trạng thái bus đã cập nhật tại `.agents/memory/DUAL_AGENT_BUS.json`. Bạn hãy chạy `python .agents/tools/sync_bus.py --claim --agent CLAUDE` để nhận ca và đối soát các tiêu chí nghiệm thu trong `.agents/memory/DUAL_AGENT_HANDOFF_MEMO.md` nhé."*

### Khi Claude bàn giao sang Gemini:
> *"Gemini ơi, tôi đã thực hiện xong các hạng mục được giao và xác nhận tiêu chí nghiệm thu. Tôi đã chuyển trạng thái sang `COMPLETED`. Bạn hãy kiểm tra lại bus qua `python .agents/tools/sync_bus.py --read` để tiếp tục tiến trình nhé."*

