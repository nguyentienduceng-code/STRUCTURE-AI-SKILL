# PHÂN TÍCH SÂU: CƠ CHẾ ĐIỀU PHỐI & RA SẢN PHẨM KHI PHỐI HỢP VỚI GEMINI (ANTIGRAVITY)

> **Tác giả:** CLAUDE (Claude Code) — ca nghiên cứu theo yêu cầu USER
> **Thời điểm:** 2026-11-19
> **Mục tiêu:** Giải thích vì sao các ca bàn giao của Gemini trên Antigravity "ra thẳng sản phẩm" còn các ca của Claude (kể cả v3.2) chỉ trông như "chỉnh sửa code" — và đề xuất nâng cấp hệ thống để hai phía cùng đạt chuẩn sản phẩm.
> **Căn cứ:** (1) hồ sơ thực thi trong dự án (cad_v6, bus, MCP config), (2) thông tin công khai về nền tảng Antigravity, (3) code v3.2 vừa triển khai.

---

## 1. VẤN ĐỀ QUAN SÁT (TỪ USER)

Ca bàn giao v3.2 của Claude = 49KB script + tests + docs. Ca của Gemini (Antigravity, ví dụ CAD v6 pha G1/G2) = **sản phẩm hữu hình trong cùng một ca**: `dce_block_catalog.json` (98→132 blocks), DXF fixture kiểm chứng, audit log `7/7 geometry checks`, test suite `32/32 PASS`, và **contract giao diện** cho pha kế tiếp. Sự khác biệt không nằm ở chất lượng code mà ở **cơ chế vận hành (operating loop)** của hai nền tảng.

## 2. CƠ CHẾ CỦA MỖI PHÍA — PHÂN TÍCH THEO LỚP

### 2.1. Gemini trên Antigravity (nền tảng phía đối tác)

Antigravity là IDE agentic của Google với **Agent Manager**: panel sinh/giám sát/điều phối nhiều coding agent song song; mỗi agent có context riêng (files, terminal, tests); mô hình **plan → delegate → worker → review** (worker báo về dạng diff + test results); chế độ Supervised (phê duyệt từng bước) / Autonomous (chạy tới cùng, review diff cuối). (Nguồn công khai — xem §7.)

Bốn lớp tạo ra cảm giác "ra thẳng sản phẩm":

| Lớp | Cơ chế Antigravity | Bằng chứng trong dự án |
|---|---|---|
| **Perception loop cùng phiên** | Agent chạy script → nhìn kết quả (terminal, render ảnh, browser) → tự sửa → lặp, tất cả trong cùng context, user xem live | `G2_RESULT.md`: round-trip DXF thật, số liệu đo (5 sections, 2 baseplates, 6/6 blocks), log capability warnings |
| **Sản phẩm = bằng chứng** | Deliverable không phải code mà là **artifact + số kiểm chứng + test log** đính kèm báo cáo pha | `G1_RESULT.md`: catalog JSON 98 blocks + SHA-256 hash; `g2_steel_verification.dxf` + `g2_steel_verification_audit.json` |
| **Tool surface chuẩn (MCP)** | Antigravity gọi chung `mcp-dce-cad` (8 tools: render_cad_plan, render_preview, validate_cad, resolve_cad_collisions, auto_layout_and_scale_plan...) | `mcp_config.json`: danh sách clients = `["Claude Code", "Claude Desktop", "Antigravity IDE", "Cursor"]` — cùng một server |
| **Quy ước sở hữu pha** | Mỗi agent chỉ ghi phạm vi được giao; đổi interface → ghi đề xuất, không tự sửa file bên kia | `CAD_UPGRADE_V6_TASK_PLAN.md`: bảng 3 chủ thể (GEMINI/CLAUDE/CODEX) + "Phạm vi ghi được" + điều kiện bàn giao từng pha |

**Chìa khóa:** Agent Manager cho phép Gemini chạy **song song nhiều sub-agent** trong phiên (parallelism thật, review tập trung ở một view). Bus file giữa hai máy không cần biết chuyện này — nó chỉ đồng bộ trạng thái ở **ranh giới pha**.

### 2.2. Claude trên Claude Code (nền tảng phía mình)

- Không có UI "Agent Manager + live diff" tương đương: đầu ra là **terminal log + file**; user chỉ thấy sản phẩm khi ta **chủ động đóng gói** (báo cáo, artifact, link).
- Có `Agent` tool (sub-agent) nhưng dùng cho fan-out nội phiên, không phải vòng plan→delegate→review hiển thị cho user.
- Perception loop tồn tại (chạy test → đọc kết quả → sửa) nhưng **không hiển thị**: kết quả chỉ nằm trong transcript.

**Hệ quả cấu trúc:** cùng một khối lượng làm việc, phía Antigravity tự động "hiện sản phẩm", phía Claude Code bắt buộc phải **đóng gói sản phẩm thủ công** vào file + chat. Ca v3.2 của Claude đã đóng gói (18/18 tests, memo, CHANGELOG) nhưng thiếu lớp **bằng chứng artifact** (không có file preview/receipt kèm) nên bị đánh giá "chỉ là code".

### 2.3. Vai trò thật của Dual-Agent Bus (nhìn lại sau v3.2)

Bus là **kênh trạng thái (who-holds-the-shift)**, KHÔNG phải bộ điều phối task:
- Nó giải quyết đúng: mutex 2 máy ghi đè, atomic write, xung đột Drive, lease treo ca, path chuẩn hóa.
- Nó KHÔNG giải quyết: phân rã task, tiêu chuẩn bằng chứng, review kết quả. Ba việc đó thuộc về **task plan (hợp đồng pha) + RESULT.md (báo cáo bằng chứng) + Codex A1 (nghiệm thu độc lập)** — đúng như cad_v6 đã vận hành (G1→C1→G2→C2→A1, mỗi mắt xích một pha có điều kiện bàn giao rõ).

## 3. BẤT ĐỐI XỨNG CỤ THỂ — VÌ SAO CA V3.2 TRÔNG "THIẾU SẢN PHẨM"

1. **Loại task meta vs product:** v3.2 nâng hạ tầng (cầu nối), không tạo domain artifact (DXF/PNG/báo cáo kết cấu). Artifact của nó chính là code + tests — khó "nhìn" hơn DXF.
2. **Visual Gate v3.2 còn là "paper gate":** trigger theo **keyword** trong task text (cad, bản vẽ, dxf...) và **bypass được bằng `--force` không để lại dấu vết**. Ca v3.2 của Claude đã phải dùng `--force` cho chính meta-handoff của mình (summary chứa từ "CAD") → gate chặn đúng nghĩa nhưng **không kiểm tra bằng chứng thật sự tồn tại trên đĩa**, và bypass không ghi receipt. Đây là lỗ hổng thiết kế, không phải lỗi vận hành.
3. **RECEIPTS bỏ trống:** `.agents/_SHARED/SHARED_CONTEXT/_active/RECEIPTS/` tồn tại nhưng rỗng từ 2026-09-24 — cơ chế "phiếu nghiệm thu" chưa được kích hoạt.
4. **Không dùng MCP loop trong ca:** ca v3.2 chạy thuần CLI; không bước `render_preview → soi ảnh → fix` nào được chạy (đúng vì không có CAD, nhưng cũng không có lớp bằng chứng nào thay thế).
5. **Báo cáo pha không đồng nhất:** cad_v6 có chuẩn `X_RESULT.md` rất tốt (scope → verification command → kết quả số → constraints → handoff contract), nhưng **chưa được quy định cho mọi ca bus** — ca v3.2 chỉ ghi vào memo (do bus tự sinh), không có file báo cáo độc lập.

## 4. ĐỀ XUẤT NÂNG CẤP (KHÓA V3.3, KHÔNG CODE TRÊN CA NÀY)

| # | Nâng cấp | Nội dung | Tác động |
|---|---|---|---|
| 1 | **Product-first brief trong schema bus** | Thêm trường `deliverable` (sản phẩm mong đợi), `evidence_files` (đường dẫn bằng chứng), `acceptance_cmd` (lệnh chạy lại được) vào `next_action_for_partner` | Mỗi ca phải khai báo sản phẩm, không chỉ "việc cần làm" |
| 2 | **RESULT.md bắt buộc theo ca** | Chuẩn hóa mẫu báo cáo pha kiểu `G1/C1_RESULT.md` (scope, lệnh verify, số kết quả, constraints, contract cho pha sau) vào thư mục `memory/audits/<project>/<agent>/` | Sản phẩm hóa mọi ca, kể cả ca meta |
| 3 | **Visual Gate v2 (evidence-based)** | (a) trigger theo `action_type` khai báo (CAD/DOCX...) thay vì đoán keyword; (b) kiểm tra **file bằng chứng tồn tại trên đĩa** (không chỉ nằm trong `artifacts_modified`); (c) `--force` **bắt buộc ghi receipt** vào `RECEIPTS/` (hash + lý do) — audit trail | Gate thành cơ chế nghiệm thu thật, bypass có dấu vết |
| 4 | **Kích hoạt RECEIPTS/** | Mỗi handoff PENDING/COMPLETED sinh 1 receipt JSON: hash SHA-256 các evidence files + trạng thái gate + agent ký | Bằng chứng "ai nghiệm thu cái gì" độc lập khỏi bus |
| 5 | **MCP perception loop cho cả 2 phía** | Claude Code gọi chung `dce-cad` MCP (đã đăng ký trong `mcp_config.json`) để render/soi/sửa trong ca CAD — cùng tool surface Antigravity dùng | Loại bỏ bất đối xứng "nhìn được kết quả" |
| 6 | **Song song đúng ranh giới** | Dùng sub-agent (Agent tool / Agent Manager) cho việc parallel TRONG phiên; bus chỉ trao đổi ở ranh giới pha + lease chống ghi đè | Không biến bus thành polling loop |

**Thứ tự ưu tiên:** (3)+(4) trước (sửa đúng thành phần v3.2 còn yếu, ~1 ngày), (1)+(2) sau (đổi quy trình, cần cả hai phía cam kết), (5) song song (cài `pip mcp` + register cho Claude Code), (6) là nguyên tắc vận hành, không code.

## 5. GIỚI HẠN & LƯU Ý

- Phân tích về Agent Manager dựa trên **thông tin công khai** (public preview); hành vi thực tế trên máy của user có thể khác — nên xác nhận trực tiếp trong Antigravity (các panel: Agents, Plan review, worktree/branch tạo cho sub-agent).
- Không có code phía Antigravity trong repo; "bằng chứng Gemini" là các `*_RESULT.md` do chính họ ghi — nên đọc như tự khai, cần Codex/USER đối chiếu.
- `mcp_dce_cad_server.py` và `dce_render_preview.py` đã tồn tại ở `.agents/tools/` (RFC giai đoạn 1 xong); giai đoạn 2 (FastMCP server) **chưa** thấy file trong repo → mục (5) cần xác nhận trạng thái triển khai trước.

---

## 7. NGUỒN THAM KHẢO

**Công khai về Antigravity:**
- Google Antigravity IDE — Agent Manager, parallel agents, plan→delegate→review loop (kết quả tìm kiếm web 2026-11; nền tảng đang public preview)

**Trong dự án:**
- [CAD_UPGRADE_V6_TASK_PLAN.md](file:///g:/My%20Drive/Google%20AI%20Studio/.agents/memory/CAD_UPGRADE_V6_TASK_PLAN.md) — hợp đồng sở hữu pha 5 mắt G1→C1→G2→C2→A1
- [G1_RESULT.md](file:///g:/My%20Drive/Google%20AI%20Studio/.agents/memory/audits/cad_v6/gemini/G1_RESULT.md) / [G2_RESULT.md](file:///g:/My%20Drive/Google%20AI%20Studio/.agents/memory/audits/cad_v6/gemini/G2_RESULT.md) — chuẩn báo cáo bằng chứng của Gemini
- [C1_RESULT.md](file:///g:/My%20Drive/Google%20AI%20Studio/.agents/memory/audits/cad_v6/claude/C1_RESULT.md) — mẫu tương đương phía Claude (đủ tốt nhưng không được quy định chung)
- [mcp_config.json](file:///g:/My%20Drive/Google%20AI%20Studio/.agents/tools/mcp_config.json) — tool surface MCP dùng chung 4 client
- [RFC_MCP_DCE_CAD_PERCEPTION_LOOP.md](file:///g:/My%20Drive/Google%20AI%20Studio/.agents/docs/RFC_MCP_DCE_CAD_PERCEPTION_LOOP.md) — thiết kế perception loop & kết quả kiểm chứng ezdxf
- `.agents/_SHARED/SHARED_CONTEXT/_active/RECEIPTS/` — trống từ 2026-09-24
- `.agents/tools/sync_bus.py` v3.2 (SSOT) — Visual Gate hiện tại (keyword-based, force bypass)
