# CHIẾN LƯỢC PHÁT TRIỂN & NÂNG CẤP HỆ THỐNG VẼ CAD THAM SỐ (`skill-cad-dce-pro` v4.7 → v5.0)

**Phạm vi:** Mở rộng năng lực triển khai bản vẽ tự động từ Kết cấu BTCT sang **Kết cấu Thép (PEB / Liên kết bản mã–bu lông–đường hàn)** và **Biện pháp Thi công (BPTC)**, đồng bộ khép kín với `design-evaluation-audit` và `skill-phuluc-tmtt`.  
**Nguyên tắc cốt lõi:** Không viết lại lõi v4.7; kế thừa 100% `DceSheetLayoutPlanner`, `ScaleTokenEngine`, `SpatialGridIndex`, `CadCollisionSolver` v2.2 và `cad_vector_renderer.py`, đảm bảo hồi quy **20/20 cổng BTCT (`G8.01–G8.20`) luôn PASS**.

## 1. Mục tiêu Nâng cấp & Kiến trúc Phân tầng

Hệ thống chuyển từ mô hình đơn bộ môn (BTCT, 1 tờ 1 tỷ lệ) sang kiến trúc **Core Dùng chung + Profile Đa bộ môn + Lưới Chi tiết Đa tỷ lệ**:

| Tầng kiến trúc | Thành phần hiện có (v4.7) | Thành phần nâng cấp / bổ sung (v5.0) |
|---|---|---|
| **Tầng 1 — Dữ liệu nguồn (SSOT)** | Dict tham số BTCT, `.dce_audit.json` | Chuẩn hóa `steel_state.json`, `bptc_state.json` (có `sha256_sync_hash` đồng bộ từ `calc_state_pipeline.py`). |
| **Tầng 2 — Bố cục & Layer** | `DceSheetLayoutPlanner` (A1/A0/Dual-Viewport), 15 Layer `DCE_*` | Thêm chế độ `COMPOSITE_DETAIL_GRID` (đa tỷ lệ trên 1 tờ A1) và `cad_layer_standard.py` (`BTCT`, `STEEL_PEB`, `BPTC`). |
| **Tầng 3 — Động cơ Vẽ** | `cad_plan_engine.py`, `cad_beam_elevation_engine.py`, `cad_column_wall_detail_engine.py` | Thêm `cad_steel_primitives.py`, `cad_steel_peb_engine.py`, `cad_bptc_engine.py`. |
| **Tầng 4 — Né chữ & Kiểm toán** | `CadCollisionSolver` v2.2, 20 cổng `G8.01–G8.20` | Giữ nguyên bộ giải va chạm; bổ sung 5 cổng `G8.21–G8.25` chạy theo Profile; xuất `.steel_audit.json` và `.bptc_audit.json`. |
| **Tầng 5 — Đồng bộ Liên SKILL** | Đồng bộ thép BTCT ($A_{s,\text{prov}} \ge A_{s,\text{calc}}$) ở chuẩn v4.6 | Cập nhật `design-evaluation-audit` (v3.7) và `skill-phuluc-tmtt` (v4.2) nhận diện đầy đủ layer mới và `G8.17–G8.25`. |

### Cấu trúc thư mục mục tiêu trong `skill-cad-dce-pro`

- `scripts/cad_layer_standard.py` — Quản lý 3 Layer Profile (`BTCT`, `STEEL_PEB`, `BPTC`) và mã nét in DXF `370`.
- `scripts/cad_plan_engine.py` — Mở rộng `DceSheetLayoutPlanner` hỗ trợ `COMPOSITE_DETAIL_GRID`.
- `scripts/cad_steel_primitives.py` — Thư viện hình học thép tham số (thép hình, bản mã, bu lông, đường hàn, BOM).
- `scripts/cad_steel_peb_engine.py` — Engine xuất bản vẽ Kết cấu Thép & PEB (`ST-01` đến `ST-04`).
- `scripts/cad_bptc_engine.py` — Engine xuất bản vẽ Biện pháp Thi công (`BP-01` đến `BP-03`).
- `scripts/dce_cad_compliance_checker.py` — Nâng cấp lên 25 cổng (`G8.01–G8.25`) hỗ trợ cờ `--profile`.
- `references/SPEC_DCE_PRO_V5.md` — Đặc tả kỹ thuật hợp nhất cho BTCT, Kết cấu Thép và BPTC.

## 2. Đặc tả Kỹ thuật 4 Trụ cột Nâng cấp

### Trụ cột 1: Lưới Đa tỷ lệ `COMPOSITE_DETAIL_GRID` trong `DceSheetLayoutPlanner`

Bản vẽ Kết cấu Thép và BPTC thường kết hợp 1 sơ đồ tổng thể (`1/50` – `1/100`) cùng 2–4 chi tiết nút liên kết (`1/10` – `1/20`) trên cùng một tờ A1.

- **Phân vùng làm việc:** Giữ nguyên cột Sidebar phải `200·S_sheet mm` và `TITLE_BAND` ở đáy khung A1 (`FORBIDDEN_ZONES` không đổi). Chia `WORK_ZONE` thành:
  - `PRIMARY_ZONE` (chiếm 55–65% diện tích `WORK_ZONE`): đặt mặt bằng hoặc khung tổng thể ở tỷ lệ $S_{\text{main}}$.
  - `DETAIL_CELL[1..N]` (chiếm 35–45% còn lại, xếp lưới 1x3 hoặc 2x2): mỗi ô là một đối tượng `CompositeCellSpec(cell_id, bbox, scale_S, dim_style, title)` mang tỷ lệ $S_i$ độc lập.
- **Cô lập tỷ lệ & DimStyle:** Khi vẽ trong `DETAIL_CELL[i]`, mọi kích thước hình học được nhân hệ số chuyển đổi $k_i = S_{\text{main}} / S_i$ để quy về cùng Model Space, đồng thời gắn `DimStyle = Dce_{S_i}MV` với `dimlfac = 1 / k_i` để số đo thực tế (mm) hiển thị chính xác 100% và chiều cao chữ in ra giấy đồng nhất `2.5 mm`.
- **Tích hợp `SpatialGridIndex`:** Đường biên giữa các ô chi tiết và tiêu đề từng ô được đăng ký vào `FORBIDDEN_ZONES` để `CadCollisionSolver` v2.2 không bao giờ đẩy nhãn hoặc đường dẫn Leader tràn sang ô kế cận.

### Trụ cột 2: Hệ Layer Đa bộ môn (`cad_layer_standard.py`)

Mở rộng hàm `select_layer_profile(profile_name)` trả về cấu hình layer chuẩn theo TCVN 5571:2012 (mã nhóm DXF `370` bắt buộc có trên mọi layer):

| Profile | Nhóm Layer bổ sung | Màu ACI | Kiểu nét | Lineweight (`370`) | Vai trò kỹ thuật |
|---|---|---|---|---|---|
| `STEEL_PEB` | `DCE_Steel_Main` | 7 (White) | `CONTINUOUS` | `50` (`0.50 mm`) | Cột, kèo khung chính, dầm tổ hợp |
| `STEEL_PEB` | `DCE_Steel_Plate` | 3 (Green) | `CONTINUOUS` | `35` (`0.35 mm`) | Bản mã, mặt bích, sườn tăng cứng |
| `STEEL_PEB` | `DCE_Steel_Sec` | 4 (Cyan) | `CONTINUOUS` | `25` (`0.25 mm`) | Xà gồ C/Z, giằng mái, giằng cột |
| `STEEL_PEB` | `DCE_Steel_Bolt` | 2 (Yellow) | `CONTINUOUS` | `25` (`0.25 mm`) | Bu lông cường độ cao, bu lông neo |
| `STEEL_PEB` | `DCE_Steel_Weld` | 1 (Red) | `CONTINUOUS` | `25` (`0.25 mm`) | Ký hiệu đường hàn góc, đường hàn đối đầu |
| `STEEL_PEB` | `DCE_Steel_Hidden` | 8 (Gray) | `HIDDEN2` | `15` (`0.15 mm`) | Nét khuất cánh dầm, lỗ bu lông mặt sau |
| `BPTC` | `DCE_BPTC_Equip` | 6 (Magenta) | `CONTINUOUS` | `35` (`0.35 mm`) | Cần trục tháp, bơm bê tông, xe cẩu |
| `BPTC` | `DCE_BPTC_Tie` | 3 (Green) | `CONTINUOUS` | `50` (`0.50 mm`) | Hệ cùm neo, thanh chống, hệ shoring |
| `BPTC` | `DCE_BPTC_Anchor` | 2 (Yellow) | `CONTINUOUS` | `25` (`0.25 mm`) | Bu lông hóa chất, ty ren xuyên dầm/vách |
| `BPTC` | `DCE_BPTC_SafeZone` | 1 (Red) | `DASHED2` | `18` (`0.18 mm`) | Ranh giới an toàn, bán kính cần trục |

*(Các layer dùng chung gồm `DCE_Truc`, `DCE_Dim`, `DCE_Name`, `DCE_Text`, `DCE_Leader`, `DCE_KhungTen` giữ nguyên chuẩn v4.7.)*

### Trụ cột 3: Thư viện Hình học Tham số & 2 Engine Chuyên biệt

#### A. Thư viện dùng chung `scripts/cad_steel_primitives.py`

Mọi hàm vẽ hình học đều nhận tham số thực (đơn vị `mm`), trả về danh sách thực thể DXF, vùng chiếm chỗ cho `SpatialGridIndex` và bản ghi khối lượng thép (kg) để tự động nạp vào Bảng thống kê (BOM) trong Sidebar:

- `draw_rolled_section(msp, profile_str, origin, rotation, view_mode)`: Vẽ mặt cắt ngang hoặc hình chiếu cạnh cho thép hình tiêu chuẩn (`H`, `I`, `U`, `L`, `C`, `Z`, `Box`, `Pipe`).
- `draw_tapered_member(msp, p_start, p_end, h_start, h_end, tf, tw, bf)`: Vẽ cột/kèo tổ hợp vát tiết diện (PEB) tự động dựng nét cánh, đường hàn bụng và đường tâm trục.
- `draw_gusset_plate(msp, polygon_pts, thickness_mm, stiffeners=None)`: Vẽ bản mã đa giác/vát góc, ghi chú quy cách `PL{t}x{B}x{L}` và sườn tăng cứng.
- `draw_bolt_array(msp, origin, rows, cols, p1, p2, d_bolt, bolt_grade, angle)`: Vẽ lưới bu lông (lục giác hoặc lỗ tròn + đường tâm trục) kèm tự động kiểm tra khoảng cách mép $e_1, e_2$ và bước $p_1, p_2$.
- `draw_weld_symbol_tcvn(msp, target_pt, leg_hf_mm, length_lw_mm, weld_type, both_sides)`: Vẽ mũi tên chỉ thị + ký hiệu tam giác hàn góc/đối đầu chuẩn TCVN.
- `compute_steel_bom(items)`: Tổng hợp bảng thống kê thép hình, bản mã (mật độ $7850\text{ kg/m}^3$), bu lông và tổng khối lượng đưa vào Sidebar (dùng chung `compute_adaptive_column_widths` chống tràn chữ).

#### B. Engine Kết cấu Thép `scripts/cad_steel_peb_engine.py`

Áp dụng tiêu chuẩn **TCVN 5575:2024** và **TCVN 2737:2023**, hỗ trợ 4 nhóm bản vẽ:

- `ST-01` — Mặt đứng khung chính PEB (tổ hợp vát tiết diện, cao độ vai cột/đỉnh kèo, bước cột, ký hiệu vị trí nút `N1..N4`).
- `ST-02` — Mặt bằng bố trí xà gồ mái, thanh chống dọc, hệ giằng mái và giằng cột.
- `ST-03` — Chi tiết nút chân cột & bố trí bu lông neo (mặt bằng bản đế + 2 mặt cắt đứng, tỷ lệ `1/10–1/15`).
- `ST-04` — Chi tiết nút vai cột–kèo mặt bích & nút đỉnh kèo (mảng bu lông cường độ cao, sườn gia cường, ký hiệu đường hàn $h_f$).

#### C. Engine Biện pháp Thi công `scripts/cad_bptc_engine.py`

Áp dụng tiêu chuẩn **QCVN 18:2021/BXD** và **TCVN 5575:2024**, hỗ trợ 3 nhóm bản vẽ:

- `BP-01` — Tổng mặt bằng thi công (vị trí thiết bị, bán kính hoạt động cần trục, ranh giới an toàn `DCE_BPTC_SafeZone`, đường vận chuyển).
- `BP-02` — Chi tiết hệ cùm neo cần trục tháp (mặt bằng tổng thể cùm + khung ôm thân tháp + thanh giằng ống/H + 2–3 ô chi tiết nút liên kết bản mã vào dầm/vách BTCT trên `COMPOSITE_DETAIL_GRID`).
- `BP-03` — Mặt bằng và mặt cắt hệ văng chống shoring hố đào (cừ Larsen/tường vây, hệ dầm H-beam văng chống, góc chống xiên, chi tiết nút bản mã nối dầm).

### Trụ cột 4: Hợp đồng JSON SSOT & 5 Cổng Kiểm toán Mới (`G8.21–G8.25`)

#### A. Hợp đồng dữ liệu JSON đồng bộ (`calc_state.json` ↔ `.steel_audit.json` / `.bptc_audit.json`)

```json
{
  "schema_version": "5.0",
  "profile": "BPTC",
  "sha256_sync_hash": "<copy_tu_calc_state_pipeline>",
  "sheet_layout": {
    "mode": "COMPOSITE_DETAIL_GRID",
    "paper": "A1",
    "primary_scale": 50,
    "detail_cells": [
      { "cell_id": "CT-01", "title": "CHI TIẾT BẢN MÃ NEO VÁCH", "scale": 10 },
      { "cell_id": "CT-02", "title": "CHI TIẾT KHUNG ÔM THÂN THÁP", "scale": 15 }
    ]
  },
  "members": [
    { "mark": "TG-1", "section": "2U200x73x7", "steel_grade": "SS400", "length_mm": 6450, "qty": 2 }
  ],
  "connections": [
    {
      "node_id": "N1",
      "plate": { "t_mm": 20, "b_mm": 450, "h_mm": 500 },
      "bolts": { "grade": "8.8", "d_mm": 24, "d0_mm": 26, "rows": 2, "cols": 4, "e1_mm": 55, "e2_mm": 50, "p1_mm": 80, "p2_mm": 80 },
      "welds": [{ "type": "fillet", "hf_mm": 8, "lw_mm": 320, "both_sides": true }]
    }
  ]
}
```

#### B. 5 cổng kiểm toán bổ sung trong `scripts/dce_cad_compliance_checker.py`

| Mã cổng | Profile áp dụng | Tiêu chí PASS bắt buộc |
|---|---|---|
| `G8.21_BOLT_SPACING_EDGE_CLEARANCE` | `STEEL_PEB`, `BPTC` | 100% mảng bu lông thỏa điều kiện khoảng cách mép và bước lỗ theo TCVN 5575:2024 ($e_1 \ge 2.0 d_0$ hoặc $1.5 d_0$ cạnh gia công, $e_2 \ge 1.5 d_0$, $p_1, p_2 \ge 2.5 d_0$) và không chạm mép bản mã. |
| `G8.22_WELD_SYMBOL_AND_LEG_SIZE` | `STEEL_PEB`, `BPTC` | 100% nút liên kết hàn có đối tượng trên layer `DCE_Steel_Weld`, ghi đủ $h_f$ (mm) và $l_w$ (mm), không va chạm với đường kích thước hoặc nét thép. |
| `G8.23_STEEL_SECTION_BOM_PARITY` | `STEEL_PEB`, `BPTC` | Khớp 100% số hiệu cấu kiện, quy cách tiết diện và tổng khối lượng thép (sai số $\le 0.5\%$) giữa hình vẽ, Bảng BOM trong Sidebar và `calc_state.json`. |
| `G8.24_MULTI_SCALE_VIEWPORT_PARITY` | `STEEL_PEB`, `BPTC` | Mọi ô chi tiết trong `COMPOSITE_DETAIL_GRID` sử dụng đúng `DimStyle = Dce_{S_i}MV`, không có thực thể hoặc nhãn vượt ra ngoài `bbox` của ô. |
| `G8.25_BPTC_CLEARANCE_AND_ANCHOR_CHECK` | `BPTC` | Khoảng hở an toàn giữa thiết bị/thân tháp và biên kết cấu công trình lớn hơn ngưỡng quy định (QCVN 18:2021/BXD); khớp 100% số lượng, đường kính và chiều sâu chôn neo với thuyết minh BPTC. |

## 3. Lộ trình Triển khai 4 Sprint (Checklist cho Hệ thống Agent)

### Sprint 1 — Lớp nền Đa tỷ lệ & Profile Layer (Ưu tiên 1)

- [ ] Chuẩn hóa `scripts/cad_layer_standard.py` với 3 hàm `get_btct_core_15()`, `get_dcesteel_core_16()`, `get_bptc_core_12()` và hàm điều phối `select_layer_profile(profile)`.
- [ ] Bổ sung chế độ `COMPOSITE_DETAIL_GRID` và lớp `CompositeCellSpec` vào `DceSheetLayoutPlanner` trong `scripts/cad_plan_engine.py`.
- [ ] Cập nhật `SpatialGridIndex` nhận ranh giới ô chi tiết vào `FORBIDDEN_ZONES`.
- [ ] Chạy toàn bộ bộ test BTCT hiện hữu xác nhận **20/20 cổng (`G8.01–G8.20`) PASS** không hồi quy.

### Sprint 2 — Thư viện Thép Tham số & Engine BPTC (Ưu tiên 2 — Giá trị thực chiến ngay)

- [ ] Xây dựng `scripts/cad_steel_primitives.py` kèm unit test cho từng hàm vẽ (`H/I/U/L`, bản mã, mảng bu lông, ký hiệu hàn TCVN, BOM).
- [ ] Xây dựng `scripts/cad_bptc_engine.py` triển khai bản vẽ `BP-02` (hệ cùm neo cần trục tháp — kiểm chứng trực tiếp bằng bài toán mẫu QTP125) và `BP-01`, `BP-03`.
- [ ] Kết xuất thử PDF A1 & PNG 300 DPI qua `cad_vector_renderer.py` và rà soát trực quan nét in CTB.

### Sprint 3 — Engine Kết cấu Thép PEB & 5 Cổng Kiểm toán (`G8.21–G8.25`)

- [ ] Xây dựng `scripts/cad_steel_peb_engine.py` cho 4 bản vẽ `ST-01` đến `ST-04`.
- [ ] Cài đặt 5 cổng `G8.21–G8.25` vào `scripts/dce_cad_compliance_checker.py` (kèm cờ `--profile btct|steel_peb|bptc`).
- [ ] Bổ sung Golden Test Suites cho `STEEL_PEB` và `BPTC` vào `run_all_tests.py` (tái sử dụng cơ chế Golden Cache để tối ưu thời gian chạy).

### Sprint 4 — Đồng bộ Liên SKILL & Phát hành v5.0

- [ ] Cập nhật `scripts/drawing_calc_crosscheck.py` (trong `skill-phuluc-tmtt` và `design-evaluation-audit`) đọc thêm `.steel_audit.json` và `.bptc_audit.json`, đối soát tự động tiết diện, bu lông, cạnh hàn $h_f$ và `sha256_sync_hash`.
- [ ] Cập nhật `scripts/cad_deep_reader.py` (`design-evaluation-audit`) phân loại thêm các layer `DCE_Steel_*`, `DCE_BPTC_*` và đọc kết quả từ `G8.17–G8.25` vào cầu nối xuất báo cáo RFI/NCR.
- [ ] Cập nhật `SKILL.md` và `references/SPEC_DCE_PRO_V5.md` trong `skill-cad-dce-pro`, chốt phiên bản **v5.0**.

## 4. Tiêu chí Nghiệm thu (Definition of Done)

1. **Không phá vỡ BTCT:** 100% test suites hiện có trong `run_all_tests.py` PASS; toàn bộ bản vẽ BTCT (`KC-01` đến `KC-03`) đạt 20/20 cổng `G8.01–G8.20`.
2. **Đạt chuẩn kiểm toán mở rộng:** Mọi bản vẽ mẫu `ST-01..04` đạt 24/24 cổng áp dụng (`G8.01–G8.24`); mọi bản vẽ mẫu `BP-01..03` đạt 25/25 cổng (`G8.01–G8.25`).
3. **Chất lượng trình bày trực quan:** File PDF A1 và PNG 300 DPI kiểm tra không có chữ chồng lấn, không tràn ô bảng BOM, đường nét phân cấp đúng độ dày `0.13–0.50 mm` và số đo trên các ô chi tiết đa tỷ lệ khớp tuyệt đối với kích thước thực.
4. **Đồng bộ khép kín 3 SKILL:** Thay đổi 1 tham số trong `calc_state.json` (ví dụ đổi đường kính bu lông từ M24 sang M27) phải tự động cập nhật đồng thời bản vẽ DXF/PDF, bảng BOM Sidebar và vượt qua kiểm tra đối soát của `design-evaluation-audit` cùng `skill-phuluc-tmtt`.
