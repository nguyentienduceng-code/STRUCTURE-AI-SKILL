# QUYẾT ĐỊNH KIẾN TRÚC — HƯỚNG (C) HYBRID AUTHORING & HỆ THỐNG VẬN HÀNH HỒ SƠ

> **Từ:** CLAUDE (kết quả trao đổi trực tiếp với User 2026-11-16)  
> **Đến:** GEMINI — triển khai ca tiếp theo  
> **Bối cảnh:** Gemini đã hoàn Phase 0+1 4-Form + Block Adapters (DCE_TITLEBLOCK_A1/A3, DCE_Pile, DCE_COL, Dce_KhTenTruc; 15 suites xanh). User chốt thêm các quyết định dưới đây cho giai đoạn "triển khai hồ sơ từ đầu + quản lý vận hành".

---

## 1. QUYẾT ĐỊNH CỦA USER (CHỐT)

**D1 — Hướng dữ liệu: (C) HYBRID**
- Model JSON là **SSOT** (single source of truth kỹ thuật).
- CAD Form/Block (4 Form mở, block dùng chung) là **lớp view** — kỹ sư sửa được trực tiếp trong AutoCAD.
- Mọi thay đổi CAD **phải truy vết về model**: authoring từ CAD (sai trục, sửa block) → đọc ngược → **vào model qua schema-gate** (valid schema + diff), chống vẽ tùy tiện.
- Kết luận: không (a) CAD-first thuần, không (b) model-first đóng.

**D2 — Công trình đơn giản/giữa: 1 FILE + BLOCK DÙNG CHUNG (mặc định)**
- Không tách BASE.xref + KC-xx. Trục/outline nằm ModelSpace dùng chung, các khổ là **PaperSpace Layouts**.
- "Sửa 1 lần dùng lại" đạt bằng: (1) block definition chia sẻ trong file + (2) **merge lane** (agent đọc lại block/form đã sửa, chỉ ghi vùng engine-owned).
- **XREF hạ xuống tùy chọn P4** — chỉ nhà cao tầng / đa nhóm mở song song (ngưỡng: tầng > 15 hoặc tờ > 12 hoặc multi-team).
- Lý do: Google Drive đa thiết bị → xref relative path dễ gãy im lặng; 1 file = 1 hash SHA256 (giữ compliance).

**D3 — BỎ ý tưởng MCP live-AutoCAD**
- Không thêm server COM/.NET điều khiển AutoCAD đang chạy (gỉả determinism, 184 tests, file lock trên Drive).
- Thay bằng **3 tools trong MCP `dce-cad` hiện có**:
  - `open_form` — đọc form User đã save, audit zone/ATTDEF/layer theo manifest.
  - `diff_form` — so form User với form SSOT, liệt kê thay đổi (màu, zone, khung tên).
  - `apply_agent_changes` — gộp thay đổi agent vào file User, chỉ vùng engine-owned, không xóa ModelSpace.
- Trải nghiệm "làm việc trực tiếp vô CAD" đạt được qua **merge lane trên file đã lưu**, không cần live cầu nối.

**D4 — Ưu tiên quản lý: WORKSPACE + MODEL VERSIONING trước, LINEAGE MỎNG đi kèm**
- Không xây DB truy vết nặng ngay; 1 dòng record: `model_id × form_id × block_catalog_version × tiêu chuẩn (STANDARDS_LOCK) × hash DXF`.
- Mục tiêu: sửa 1 cột → chỉ tái sinh tờ ảnh hưởng (diff-based regeneration), không regenerate-all.

---

## 2. 3 THỨ "VẼ LẠI" CHƯA CÓ — PHẢI XÂY KHI TRIỂN KHAI TỪ ĐẦU

1. **Đường dữ liệu VÀO (authoring):** hiện đang vào qua PDF/scan. Cần input chính thống: ETABS / form bảng tính có schema / vòng authoring CAD-first (qua schema-gate D1).
2. **Model = tài sản có phiên bản:** mỗi tờ vẽ phải truy vết về `model vN + form vN + block_catalog vN + tiêu chuẩn` → hash DXF.
3. **Vòng NCR/RFI phản hồi ngược:** NCR "C7 sai tiết diện" → đổi field model (giữ version) → tái sinh chỉ vùng ảnh hưởng → xuất dossier mới. Hồ sơ sống, không phải ảnh tĩnh.

---

## 3. KẾ HOẠCH TRIỂN KHAI CHO GEMINI (THEO THỨ TỰ)

### P0-OPS — Nền vận hành (làm trước tiên)
- Chuẩn hóa **project workspace** `01_Projects/<DuAn>/`: `model/`, `forms/`, `blocks/`, `outputs/`, `audit/`, `nrc/`.
- **Model schema + versioning**: file `model_schema.json` (schema của model JSON) + trường `model_version` trong model.
- **Lineage mỏng**: 1 file `lineage.jsonl` (append-only) — mỗi dòng: model_id × form_id × block_catalog_version × standards_ref × dxf_sha256 × timestamp.
- **Runbook** 4 lệnh: tạo dự án, thêm form, đổi layer (qua SSOT), xử lý NCR.
- Exit: dự án mẫu chạy author → generate → validate (Bộ lọc 8) → phát hành dossier; lineage có 1 dòng/trên tờ.

### P1 — Schema-Gate Authoring (thực thi D1)
- `model_diff.py`: đọc form/block đã sửa trong AutoCAD → extract thay đổi (trục, layer, title block) → validate vào model schema → ghi model mới (version +1) **chỉ khi valid**; sai → báo `E005/E006` + diff, không tự sửa model.
- Merge lane 3 tools của D3 (`open_form`/`diff_form`/`apply_agent_changes`) trong MCP `dce-cad`.
- Exit: kỹ sư sửa trục trong Form 02 → save → agent đọc ngược → model_version +1 → chỉ tái sinh các tờ dùng trục đó.

### P2 — NCR Back-Loop
- Schema phiếu NCR (JSON): `element_id + field + giá trị mới + nguồn`.
- Áp dụng vào model (version +1), tái sinh diff-based, xuất dossier + RFI/NCR số thứ tự.
- Exit: 1 NCR mẫu chạy end-to-end không đụng tay vào code.

### P3 — PaperSpace Multi-Layout (theo D2)
- Chuyển KC-xx sang Layouts (1 layout = 1 khổ A1/A3, viewport vào ModelSpace).
- TEXT/ATTRIB set theo **model-scale height** (chống méo khi 1 block dùng nhiều tỉ lệ); basepoint = WCS tâm (tránh lỗi 700mm cũ).
- Exit: 1 file, nhiều layout; block trục dùng chung; SHA256 1 hash/file.

### P4 — Tùy chọn mở rộng (KHÔNG làm trước khi User yêu cầu)
- XREF reference file (ngưỡng nhà cao tầng, multi-team) + cổng audit `MISSING_XREF` + hash block trục.
- ODA DWG adapter (xref native).

---

## 4. GUARDRAIL BẮT BUỘC
- **Giữ 184/184 tests xanh** (15 suites) ở mọi phase; test mới chỉ thêm.
- Legacy path `cad_plan_engine` / `cad_multiview_a3` **không refactor** trong P0–P2; mọi chế độ mới chạy qua flag (D2: single-file mặc định, xref chỉ P4).
- Không gọi `full_compliance_verified=true` khi thiếu native block/ATTRIB + zone evidence.
- Mỗi phase bàn giao qua Bus + 1 ca công trình thật + soi ảnh `render_preview` (Rule 12d.6).

## 5. ĐIỂM CẦN GEMINI CHỐT TRƯỚC KHI CODE P0-OPS
- Schema model: dùng `jsonschema` hay dataclass+pydantic (khuyến nghị `jsonschema`, nhẹ, không thêm dependency nặng)?
- Location workspace: `01_Projects/<DuAn>/` (khuyến nghị, khớp quy ước hiện có) vs trong `.agents`?
- NCR số thứ tự: dùng `nrc/` riêng trong workspace (khuyến nghị) hay nối luôn SKILL_RFI?
