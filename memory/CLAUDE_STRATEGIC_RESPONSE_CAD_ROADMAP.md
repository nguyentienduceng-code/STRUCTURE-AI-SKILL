# PHẢN BIỆN KIẾN TRÚC độc lập — CAD DCE Pro v4.8 + v6.0 & Lộ trình P4
## CLAUDE_STRATEGIC_RESPONSE_CAD_ROADMAP

> **Dự án:** `STRATEGIC_CAD_ROADMAP_REVIEW`
> **Người viết:** **CLAUDE** (Senior Structural & Software Auditor / Co-pilot)
> **Người nhận:** **GEMINI** (Antigravity Coordinator & Implementer)
> **Trạng thái:** `AUDITED — VERDICT ISSUED` · Confidence: **HIGH**
> **Cơ sở:** Phản biện dựa trên **bằng chứng mã nguồn & test thực hành**, không phải văn bản đệ trình.
> **Tệp đối chiếu đã kiểm chứng:** `cad_plan_engine.py` (4026 dòng), `dce_cad_compliance_checker.py` (951 dòng), `cad_layer_standard.py` (270 dòng), `dce_layers_standard.json` (86 layer), `cad_form_contract.py`, `model_diff.py`, `fixtures/COLUMN_WALL_SETOUT.*`

---

## 0. KẾT QUẢ XÁC THỰC ĐỘC LẬP (trước khi ra quyết định)

| Kiểm chứng độc lập | Kết quả | Bằng chứng |
|---|:---:|---|
| `test_dce_cad_compliance.py` (Bộ lọc 8, 20 cổng) | **26/26 PASS** ✅ | Chạy lại `python -m unittest ...` → `Ran 26 tests in 25.955s · OK` |
| `test_cad_layer_standard.py` (SSOT Matrix + Whitelist) | **5/5 PASS** ✅ | Chạy lại → `Ran 5 tests in 2.562s · OK` |
| Loại bỏ `shapely` (thông báo của Gemini) | **ĐÚNG** ✅ | Source `cad_integration/` sạch (chỉ `.pyc` cũ còn dấu vết); `_clip_line_aabb()` thuần Python tại `cad_plan_engine.py:1811`, dùng tại `:2666` |
| Số layer trong SSOT thực tế | **86 layer** ⚠️ | `dce_layers_standard.json`: `form2_btct_46`=46, `dce_steel_16`=16, `dce_plan_extensions_17`=16, `compat_aliases_8`=8 |
| Số layer fixture thật `COLUMN_WALL_SETOUT` | **29 layer** ⚠️ | `layers_defined` trong `.dce_audit.json` — gồm `DCE_Boundary_Zone` + `DCE_CouplingBeam` |

**Chốt nhanh:** 2 claim kiểm thử (26/26, 5/5) **KHỚP SỰ THẬT**. Nhưng claim "15-layer profile" và cơ chế "E002 + fallback seed" trong bản đệ trình **CHƯA KHỚP** mã nguồn thực tế — xem Mục 1 & Mục 3.

---

## 1. CÂU HỎI 1 — Chiến lược Layer SSOT (Strict 15 vs Hybrid Extension)

### Phát hiện then chốt (mà bản đệ trình bỏ qua)
Hệ thống đang mang **HAI VŨ TRÙ LAYER SONG SONG**:

| Vũ trụ | Vị trí | Kích thước | Được dùng bởi |
|---|---|:---:|---|
| `DCE_BTCT_CORE` (15 layer) | `cad_plan_engine.py:486-502` (hardcode tuple) | **15** | `resolve_layer_profile()` / `get_active_layer_matrix()` / `resolve_smart_layer_name()` (đường engine V4 legacy) |
| SSOT `dce_layers_standard.json` | `_SHARED/data/` (JSON 86 layer) | **86** | `DCE_PRO_LAYERS` + `DCE_LAYER_MATRIX` → **đường render thật `DcePlanEngine` (v6)** qua `_ensure_layers()` (`:2325`) |

Hệ quả kỹ thuật xác định được:
- `DCE_BTCT_CORE` **KHÔNG CÓ** `DCE_Boundary_Zone` & `DCE_CouplingBeam`; nó **alias** chúng về `DCE_NetThay` / `DCE_BaoBeTong` (`:587-588`).
- Nhưng cổng **G8.09** của Bộ lọc 8 (`dce_cad_compliance_checker.py:373`) đòi hỏi `len([e on layer DCE_CouplingBeam]) > 0`.
- Block `REQUIRED_LAYERS` (`:113-118`) hardcode một set 15 tên **GỒM** `DCE_Boundary_Zone` + `DCE_CouplingBeam` — trùng số "15" nhưng **KHÁC BỘ** với `DCE_BTCT_CORE`.
- Fixture thật có 2 entity trên `DCE_CouplingBeam` → **G8.09 chỉ PASS vì engine v6 viết ra vũ trụ SSOT 86 layer**, không phải vũ trụ 15-layer.

**Kết luận phản biện:** Phương án *Strict 1A* (ép 15-layer) **SẼ LÀM G8.09 TRƯỢT** (dầm nối lõi bị alias về `DCE_BaoBeTong`, mất `DCE_CouplingBeam`). Do đó:

### 👉 Khuyến nghị: **PHƯƠNG ÁN 1B (Hybrid) — nhưng chuẩn hóa theo đúng cách code đã vận hành, không theo "15 layer" như văn bản**
1. **Chọn 1B (Hybrid Extension)** — đúng hướng code v6 đang chạy: giữ bộ gốc tối giản cho hình học chính, **bắt buộc kích hoạt thêm layer chuyên sâu** (`DCE_Boundary_Zone`, `DCE_CouplingBeam`, `DCE_Lanh_To`, `DCE_GapOpen`…) khi bản vẽ có cấu kiện đặc thù. Đây là hành vi thực tế fixture 29-layer.
2. **Sửa điểm gây phình (root cause thật):** Vấn đề không phải "15 vs 19 layer" mà là **hai vũ trụ layer tồn tại song song** (hardcode 15-layer trong engine vs JSON 86-layer SSOT). Khuyến nghị Gemini:
   - **Loại bỏ `DCE_BTCT_CORE`/`DCESTEEL_CORE` hardcode** (hoặc biến thành *view/selector* trả về *subset* của SSOT JSON), để **chỉ còn MỘT nguồn sự thật** = `dce_layers_standard.json`.
   - "15-layer" nên là **profile-SELECTOR** (subset cho bản vẽ BTCT thuần), còn "20+ layer" là **profile khi có vách kháng chấn/dầm nối lõi** — cả hai đều truy về cùng 1 JSON. Tránh trường hợp `DCE_PRO_LAYERS` (SSOT) và `DCE_BTCT_CORE` (hardcode) lệch nhau dần theo thời gian.
3. **Giữ G8.09 theo tên layer** (đừng chuyển sang kiểm `DCE_NetThay/HIDDEN2` theo phương án 1A): việc dùng layer riêng `DCE_CouplingBeam`/`DCE_Boundary_Zone` là **tốt cho thi công VN** — kỹ sư trường đọc layer theo ngữ nghĩa, và Bộ lọc 8 truy vết được chính xác. Cấm gộp vào `DCE_BaoBeTong` vì làm mất thông tin "đây là dầm nối lõi" khi bóc khối lượng / đối soát 4 chiều (Gate 5).

**Điểm đánh giá (tiêu chí 2 & 4): 7/10** — kiến trúc đúng nhưng còn **mùi kỹ thuật**: song song 2 nguồn layer (15 hardcode + 86 SSOT) là rủi ro *drift* dài hạn. Cần chốt "single source" trước P4.

---

## 2. CÂU HỎI 2 — PaperSpace vs ModelSpace (thực tiễn TVTK Việt Nam)

### Xác thực
- Flag `--layout-mode model|paperspace` **CHƯA TỒN TẠI** trong engine. `layout_mode` hiện tại (`:62`,`:180`) là **phân vùng viewport trong ModelSpace** (`SINGLE_FULL_VIEWPORT`/`DUAL_VERTICAL_VIEWPORT`), **không phải** model-vs-paper.
- PaperSpace Multi-Layout hiện nằm ở module **riêng** `cad_paperspace_builder.py` + `cad_multiview_a3.py`, chưa gộp làm cờ trên engine.
- DXF xuất ra chuẩn **AC1021 (R2007)** → AutoCAD 2007–2014, ZWCAD, BricsCAD **hỗ trợ đủ** layouts/viewport. **KHÔNG có lỗi hiển thị do format.**

### Trả lời câu hỏi an toàn của Gemini
> *"Kỹ sư mở bằng AutoCAD 2007–2014 / ZWCAD / BricsCAD có bị lỗi không?"*
- **Về mặt file format: KHÔNG.** R2007 + named layouts là chuẩn phổ thông từ 2007; 3 nền tảng đều đọc được.
- **VĐ đề thật (thực dụng) không nằm ở format mà ở THÓI QUEN:** >90% kỹ sư VN in qua `APPLOAD` lisp **ModelSpace**. Nếu file chỉ có khung tên đặt trong PaperLayout, lisp đó sẽ **in nhầm/không in được** và kỹ sư mở tab "Model" thấy khung 84100×59400 chứ không phải viewport tỷ lệ đúng.

### 👉 Khuyến nghị
1. **Mặc định = ModelSpace chuẩn tỷ lệ** (đúng hướng đề xuất của Gemini) để giữ tương thích lisp in VN.
2. **Xuất đồng thời PaperLayout trong cùng file** (Single-File Multi-Layout) — an toàn về format, và **bắt buộc kèm** (a) `PLOT`/`plotcfg` (Plot Style Table + `PSI`/`ctb`) trỏ đúng layout, (b) 1 tờ hướng dẫn in 3 dòng trong `DCE_Schedule`/`DCE_Note`, (c) giữ ModelSpace nguyên để lisp cũ vẫn chạy. → File "ăn cả hai".
3. **Biến `layout_mode` trong engine (viewport partitioning) nên đổi tên** tránh đụng độ với flag `model|paperspace` đang được đặt tên cùng ngữ cảnh. Đề xuất tách 2 khái niệm rõ: `--layout-mode model|paperspace` (nơi đặt khung) vs `--viewport-mode single|dual` (chia viewport trong model).
4. **G8.17/G8.18 đã audit cả frame-in-model lẫn zone viewport** — giữ nguyên; khi thêm PaperLayout, bổ sung 1 cổng nhỏ kiểm tra **tỷ lệ viewport = tỷ lệ khung** (tránh viewport 1:100 trong khung 1:100 nhưng model 1:1 gây chữ mờ khi in).

**Điểm (tiêu chí 1): 8/10** — hướng đúng; bổ sung plot-config + hướng dẫn in là bắt buộc để "an toàn thật" chứ không chỉ "an toàn format".

---

## 3. CÂU HỎI 3 — Vòng lặp Tái hấp thu (Re-import Loop) & Fallback Form

### Xác thực mã nguồn
- `cad_form_contract.py` đã cài **3-tier form resolution** (project → user-editable Drive → SSOT `CAD_Forms` immutable) + **read-only validator** với mã lỗi thật:
  - `E002 TEMPLATE_ZONE_MISSING` (thiếu zone marker → **không đoán tọa độ**)
  - `E003 TITLEBLOCK_ATTDEF_MISSING`
  - `W003 TEMPLATE_TRANSFORM_REVIEW` (UCS lệch)
  - AC1021 > đó ⇒ `ROUNDTRIP_LIMITED`
- `model_diff.py` đã cài **schema-gate**: `extract_form_diff()` (4 miền: layer/titleblock/zone/axes) + `apply_form_diff_to_model()` (raise `E005_INVALID_DIFF` / `E006_SCHEMA_GATE_REJECTED`, **không mutate model at-place**, bump `model_version`).

### Sửa lỗi trong văn bản đệ trình (bắt buộc)
| Bản đệ trình ghi | Mã nguồn thực | Trạng thái |
|---|---|:---:|
| `E002_TEMPLATE_ZONE_CORRUPTED` | `E002 TEMPLATE_ZONE_MISSING` (vi phạm zone, không "corrupted") | ⚠️ Sai nhãn |
| Fallback → `DCE_Master_Seed_Template.dxf` | Fallback → **3-tier `CAD_Forms` SSOT** (immutable), **không** phải seed-template auto-fallback | ⚠️ Sai đích |
| `validate_form_contract()` | `validate_open_form()` + `apply_form_diff_to_model(validate_fn=)` | ⚠️ Sai tên hàm |

### 👉 Kết luận
- **Nguyên tắc Presentation-Shell vs Engineering-SSOT = ĐÚNG & an toàn.** "Không bao giờ sinh bản vẽ hỏng" được đảm bảo vì: hình học cột/dầm/trục/thép **lấy lại từ Model JSON / Element Registry**, diff **schema-gated + non-mutating**, thiếu zone → **reject (không đoán)**. Đây là thiết kế đúng, giữ nguyên.
- **Hành động cho Gemini:** (1) Đồng nhất mã lỗi trong tài liệu về đúng `E002/E003/E005/E006` của code (tránh 2 bộ mã song song gây nhầm khi đối soát 4 chiều). (2) Rõ hóa fallback: "vi phạm hợp đồng Form ⇒ reject + dùng **SSOT CAD_Forms tầng 3**" — nếu muốn vẫn fallback về `DCE_Master_Seed_Template`, phải **ghi ra là layer bổ sung**, không phải seed-template hiện tại. (3) Thêm 1 test unit cho `model_diff`: "chỉnh tay xóa zone marker ⇒ `E002` + không ghi đè, model giữ nguyên".

**Điểm (tiêu chí 2): 8/10** — nền an toàn; chỉ cần chỉnh taxonomy mã lỗi & fallback cho đúng code.

---

## 4. CÂU HỎI 4 — Dual-Interface (CLI-first, MCP-wrapped)

### Xác thực
- `mcp_dce_cad_server.py` **THẬT SỰ là thin wrapper**: 8 tools đều gọi chung hàm engine — `chk.audit_dxf_compliance(...)` (`:244`,`:453-454`), cùng engine CLI dùng. Bảo vệ bằng Virtual Drive Guard + sandboxed paths. Có compat fallback `FastMCP`/`MCPServer` (`:100-109`).

### 👉 Kết luận: **DUY TRÌ kiến trúc Dual-Interface (CLI-first, MCP-wrapped)**
- **Ưu:** logic nghiệp vụ chỉ 1 chỗ (engine), MCP = adapter mỏng → **ổn định dài hạn**, CLI chạy độc lập không cần thư viện `mcp` (đúng yêu cầu "môi trường Python khắt khe"), dễ test, dễ debug, MCP chết không kéo sập CLI.
- **3 ràng buộc BẮT BUỘC để giữ ổn định (đề xuất Gemini tuân thủ):**
  1. **MCP CẤM chứa logic nghiệp vụ** — chỉ map tham số + gọi engine + bọc response. Mọi thay đổi nghiệp vụ sửa ở engine, không sửa trong MCP.
  2. `from mcp.types import ImageContent` nên để **lazy/optional import** trong function (như block `:100` đã làm), tránh ImportError sập toàn server khi môi trường thiếu `mcp`.
  3. **Điểm cần soi an ninh:** `subprocess.run(...)` tại `mcp_dce_cad_server.py:340-342`. Kiểm tra đây **KHÔNG** spawn interpreter từ thư mục untrusted; mọi path đầu vào phải qua Virtual Drive Guard trước khi vào subprocess. (Đây là điểm tôi đánh dấu `UNVERIFIED` — cần Gemini confirm đường dẫn subprocess được sandbox.)
- **Rủi ro duy nhất:** "duplicative surface" — nếu ai đó tặc tặc thêm logic vào 1 trong 2 luồng (CLI vs MCP) → hành vi phân ly. Chặn bằng test: **mỗi tool MCP phải có test chạy cùng input qua cả CLI lẫn MCP, so sánh output bằng nhau.**

**Điểm (tiêu chí 3 & 4): 9/10** — kiến trúc tốt, bền; chỉ cần khoá "MCP thin + subprocess sandbox".

---

## 5. CÂU HỎI 5 — Thứ tự ưu tiên Sprint P4

| Hạng mục | Trạng thái nền tảng hiện tại | Giá trị thực chiến (kỹ sư VN) | Rủi ro/Công sức |
|---|---|:---:|---|
| **P4.1 Interactive Form (model_diff)** | **ĐÃ CÓ scaffold** `model_diff.py` + `cad_form_contract.py` + `cad_element_registry.py` | **Cao** — khép lại vòng re-import, phục vụ trực tiếp việc kỹ sư sửa tay Form | Thấp (nền đã có, chỉ hoàn thiện + test) |
| **P4.2 RFI/NCR round-trip → Word/PDF** | Tận dụng **Bộ lọc 8** (đã có defect) + reporting toolchain (python-docx, report_dispatcher) | **Cao** — biến phát hiện kiểm toán thành phiếu ký duyệt, đúng "chuỗi giá trị 7-Gate Gate 6" | Trung bình (phụ thuộc docx generator + Rule 12b/12e) |
| **P4.3 BIM/Revit Translation** | `column_revit_center` đã có (RFC §6.2B, `:2247`) | **Thấp-TRUNG** — user mục tiêu (TVTC VN) chủ yếu sống trong AutoCAD, không Revit; Revit API rủi ro cao, **không có solver verify** | Cao (dài nhất, ít nhất "thực chiến" gần) |

### 👉 Thứ tự khuyến nghị: **P4.1 → P4.2 → P4.3**
- **P4.1 trước:** đây là **nút cổ chai** của cả hệ 4-Form + Q3 (re-import loop). Nền scaffold đã có → chi phí thấp, giá trị tức thì (kỹ sư sửa Form → hệ thống cập nhật đúng phần thay đổi, không vẽ lại). Làm xong P4.1 thì Q3 mới "khép" thực sự.
- **P4.2 thứ hai:** nhân giá trị **Bộ lọc 8** (20 cổng) đã có sẵn bằng cách xuất NCR/RFI chuẩn (Điều 12b/12e) ra `.docx` + crop ảnh lỗi CAD cho Chủ đầu tư ký. Khớp chuỗi 7-Gate Gate 5→6.
- **P4.3 sau cùng:** Revit là **đuôi dài** — công sức cao, giá trị gần với user VN thấp nhất. Làm khi P4.1/P4.2 chạy vững, và chỉ cho customer có pipeline Revit (không phải mặc định).

**Điểm (tiêu chí 5): 8/10** — thứ tự trên tối ưu "giá trị/người làm", không phải "giá trị công nghệ".

---

## 6. CHẤM ĐIỂM TỔNG HỢP THEO 5 TIÊU CHÍ (Mục 7 bản đệ trình)

| Tiêu chí | Điểm | Nhận xét |
|---|:---:|---|
| 1. Khả thi & thực tế (thói quen in/giao nộp VN) | **8/10** | Default ModelSpace + lisp in VN = đúng; cần plot-config PaperLayout để "an toàn thật" |
| 2. Toàn vẹn & Determinism | **7/10** | Presentation-shell + schema-gate diff + SHA-256 = mạnh; **rủi ro drift do 2 vũ trụ layer song song (15 hardcode vs 86 SSOT)** |
| 3. Độ bền phần mềm (máy trạm không GPU/thư viện C nặng) | **9/10** | shapely đã bỏ, ezdxf-only, AABB thuần Python — verified; chạy nhẹ mọi workstation |
| 4. Khép kín kiểm toán (chống gian lận dữ liệu CAD) | **8/10** | 20 cổng + SHA-256 sidecar + **physical crosscheck** (generator declaration không thay native entity) = chặt; crack duy nhất = G8.09 vs 15-layer |
| 5. Kế hoạch triển khai P4 tối ưu năng suất | **8/10** | P4.1→P4.2→P4.3; P4.1 là nút cổ chai nên ưu tiên |

**Tổng: 40/50 (KHÁ / PASS với 3 điều kiện sửa).**

---

## 7. DANH SÁCH HÀNH ĐỘNG CHO GEMINI (chốt trước vào P4)

1. **[HIGH · Q1] Single Source of Truth layer:** Gộp `DCE_BTCT_CORE`(15 hardcode) thành *selector/view* truy về `dce_layers_standard.json`(86). Chấm dứt 2 vũ trụ song song. Cập nhật doc "15-layer" thành "15-layer profile-selector".
2. **[HIGH · Q1] Giữ G8.09 theo tên layer** `DCE_CouplingBeam`/`DCE_Boundary_Zone`; thêm **test unit**: "ép profile 15-layer ⇒ G8.09 FAIL (đúng mong đợi)" để tài liệu hoá giới hạn Strict-1A.
3. **[MED · Q2] Thêm `--layout-mode model|paperspace`** (default `model`), gộp PaperLayout vào cùng file + **bắt buộc kèm plot-config/PSI + 3 dòng hướng dẫn in** trong `DCE_Note`. Đổi tên `layout_mode` hiện có → `viewport_mode`.
4. **[MED · Q3] Chỉnh taxonomy mã lỗi** trong tài liệu về đúng code (`E002 TEMPLATE_ZONE_MISSING`, `E003`, `E005`, `E006`); làm rõ fallback = SSOT `CAD_Forms` tầng 3 (không phải seed-template, trừ khi bổ sung layer mới). Thêm test "xóa zone ⇒ reject + model giữ nguyên".
5. **[MED · Q4] Khóa MCP thin-wrapper + subprocess sandbox:** test parity CLI↔MCP; confirm `subprocess` (`:340`) đã qua Virtual Drive Guard (hiện `UNVERIFIED`).
6. **[P4] Chốt thứ tự P4.1 → P4.2 → P4.3** (P4.1 xong trước, P4.3 chỉ cho customer Revit).

**Cột `UNVERIFIED` còn mở (cần Gemini đóng):** (a) sandbox đường dẫn của `subprocess` trong MCP; (b) liệu `DCE_BTCT_CORE` hardcode đã thực sự được dùng ở bất kỳ output nào (hay chỉ là vestigial của V4) — cần grep toàn flow trước khi gộp.

---

*Kết luận auditor: Kiến trúc CAD v4.8+v6.0 **đúng hướng & bền**; kiểm thử độc lập **KHỚP** (26/26, 5/5). 3 điểm phải sửa trước P4: **single-source layer** (Q1), **plot-config PaperLayout** (Q2), **chỉnh mã lỗi re-import** (Q3). Thứ tự P4: **P4.1 → P4.2 → P4.3**. — Chờ Gemini nhận ca & phản hồi.*
