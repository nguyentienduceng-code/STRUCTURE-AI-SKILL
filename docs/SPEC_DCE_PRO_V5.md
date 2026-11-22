# SPEC_DCE_PRO_V5.md — Đặc Tả Kỹ Thuật Hệ Thống Vẽ CAD Tham Số DCE Pro v5.0

> **Phiên bản:** 5.0.0 (Release)
> **Phạm vi:** Kế thừa trọn vẹn DCE Pro v4.7 (BTCT), mở rộng Kết cấu Thép Tiền chế (PEB) & Biện pháp Thi công (BPTC).
> **Tiêu chuẩn viện dẫn:** TCVN 5575:2024, TCVN 2737:2023, TCVN 5574:2018, QCVN 18:2021/BXD, TCVN 5571:2012.

---

## 1. Kiến Trúc Bố Cục Đa Tỷ Lệ `COMPOSITE_DETAIL_GRID`

Nhằm giải quyết triệt để vấn đề bố trí các chi tiết cấu tạo phóng to trên cùng 1 bản vẽ Model Space với mặt bằng/mặt đứng tổng thể mà không làm sai lệch số đo hay kích thước chữ in:

1. **Phân vùng Bản vẽ (A1 / A0):**
   - **Primary Zone (60% diện tích canvas):** Bố trí mặt bằng hoặc mặt đứng tổng thể ở tỷ lệ chính $S_{\text{main}}$ (ví dụ $1/50, 1/100$).
   - **Detail Grid (40% diện tích canvas):** Phân chia thành lưới 1–4 ô chi tiết cấu tạo (`CT-01`, `CT-02`...) ở các tỷ lệ phóng to $S_i$ (ví dụ $1/10, 1/15, 1/20$).

2. **Quy tắc Độc lập Tỷ lệ & DimStyle:**
   - Đối tượng hình học trong ô chi tiết vẽ theo kích thước thực tế (mm).
   - Đường kích thước trong ô chi tiết sử dụng `DimStyle = Dce_{S_i}MV`.
   - Hệ số tỷ lệ kích thước: `dimlfac = S_i / S_main`, đảm bảo số đo hiển thị là kích thước thật (mm) trong khi chiều cao chữ in trên giấy luôn đồng nhất $2.2\text{ mm}$ (tiêu đề $3.0\text{ mm}$).
   - Toàn bộ ranh giới của các ô chi tiết được nạp vào `forbidden_regions` của `SpatialGridIndex` để triệt tiêu 100% nguy cơ nhãn hoặc leader đâm xuyên qua ô khác.

---

## 2. Hệ Thống 3 Profile Layer Chuẩn Hóa SSOT

| Tên Profile | Số lượng Layer cốt lõi | Các Layer đặc thù chính | Tiêu chuẩn kỹ thuật |
|---|---|---|---|
| **`BTCT`** | 15 Layers | `DCE_Cot`, `DCE_Vach`, `DCE_BaoBeTong`, `DCE_Thep_Chu`, `DCE_Thep_Dai`, `DCE_Hatch`, `DCE_VoidX` | TCVN 5574:2018, TCVN 5571:2012 |
| **`STEEL_PEB`** | 16 Layers | `DCE_Steel_Main` (lw 50), `DCE_Steel_Plate` (lw 25), `DCE_Steel_Sec` (lw 25), `DCE_Steel_Bolt` (lw 18), `DCE_Steel_Weld` (lw 25), `DCE_Steel_Hidden` (lw 15) | TCVN 5575:2024, TCVN 2737:2023 |
| **`BPTC`** | 12 Layers | `DCE_BPTC_Equip` (lw 35), `DCE_BPTC_Tie` (lw 50), `DCE_BPTC_Anchor` (lw 25), `DCE_BPTC_SafeZone` (lw 18) | QCVN 18:2021/BXD, TCVN 5575:2024 |

---

## 3. Danh Mục Các Cổng Kiểm Toán Kỹ Thuật (25 Cổng G8.01–G8.25)

| Nhóm Cổng | Mã Cổng | Tên Cổng Kiểm Toán | Áp dụng | Tiêu chí Đạt chuẩn (PASS) |
|---|---|---|---|---|
| **Cốt lõi (BTCT & Chung)** | `G8.01` | `DXF_VERSION_AND_SYNTAX` | Mọi bản vẽ | AC1021, 0 lỗi cú pháp ezdxf audit |
| | `G8.02` | `DCE_LAYER_AND_CTB_MATRIX` | Mọi bản vẽ | 100% Layer thuộc Profile, đủ Lineweight 370 |
| | `G8.03` | `DIMSTYLE_DUAL_HIERARCHY` | `BTCT` | DimStyle phân cấp, mũi tên _ARCHTICK |
| | `G8.04` | `AXIS_BUBBLE_NO_CROSSING` | `BTCT` | Bong bóng trục không đè ranh giới |
| | `G8.05–G8.16` | Các cổng kiểm tra kết cấu BTCT | `BTCT` | Cột vách, dầm sàn, cốt thép, BBS |
| | `G8.17` | `SCALE_FRAME_DIMSTYLE_SYNC` | Mọi bản vẽ | Khung A1/A0/A3 và DimStyle đồng bộ tỷ lệ |
| | `G8.18` | `ZERO_GLOBAL_LAYOUT_INTRUSION` | Mọi bản vẽ | 0 xâm phạm TitleBlock / Sidebar |
| | `G8.19` | `SCHEDULE_TABLE_CELL_CONTAINMENT` | `BTCT`, `STEEL_PEB`, `BP-02` | Bảng BOM co giãn tự động không tràn chữ |
| | `G8.20` | `BEAM_LABEL_ORIENTATION_AND_LW` | Mọi bản vẽ | Nhãn dầm xoay 90° / 100% Layer có mã `370` Lineweight dương |
| **Mở rộng v5.0 (Thép & BPTC)** | `G8.21` | `BOLT_SPACING_EDGE_CLEARANCE` | `STEEL_PEB`, `BP-02` | Bước bu lông $p \ge 2.5 d_0$, mép $e \ge 1.5 d_0$ (TCVN 5575:2024) |
| | `G8.22` | `WELD_SYMBOL_AND_LEG_SIZE` | `STEEL_PEB`, `BP-02` | 100% mối hàn ghi đủ $h_f$ và $l_w$ trên `DCE_Steel_Weld` |
| | `G8.23` | `STEEL_SECTION_BOM_PARITY` | `STEEL_PEB`, `BP-02` | Khớp 100% khối lượng thép BOM và các cấu kiện (sai số $\le 0.5\%$) |
| | `G8.24` | `MULTI_SCALE_VIEWPORT_PARITY` | `STEEL_PEB`, `BP-02` | Bố cục `COMPOSITE_DETAIL_GRID` đúng số ô chi tiết, mỗi ô chứa đúng nhãn tỷ lệ/tiêu đề tương ứng |
| | `G8.25` | `BPTC_CLEARANCE_AND_ANCHOR_CHECK` | `BPTC` | `BP-01`: tâm thiết bị & vòng `SafeZone` nằm trong ranh giới công trường/khung bản vẽ; `BP-02`: đủ thiết bị, thanh giằng, neo & bu lông hợp lệ theo QCVN 18:2021/BXD |

> **Phạm vi kiểm chứng của Bộ lọc 25 cổng (`G8.01–G8.25`):** Các cổng trên kiểm chứng cấu trúc thực thể/hình học DXF, chuẩn lớp/tỷ lệ DCE và tính nhất quán với sidecar gắn SHA-256. Những hạng mục đòi hỏi chứng minh nội lực hoặc liên kết độc lập (như chiều sâu neo vào vách BTCT hoặc độ bền tiết diện từ mô hình ETABS/SAP2000) phải do hồ sơ tính toán kỹ thuật xác nhận riêng, không thay thế bằng kiểm tra hình học DXF.

---

## 4. Hợp Đồng Dữ Liệu Đồng Bộ SSOT

Mọi bản vẽ xuất ra từ `CadSteelPebEngine` hoặc `CadBptcEngine` đều sinh tệp sidecar song hành `.steel_audit.json` hoặc `.bptc_audit.json` chứa mã băm SHA-256 trên byte DXF thật (`sha256_sync_hash` và `provenance.dxf_sha256`), danh mục `members`, `connections`, và `bom_summary`. Khi một tham số kỹ thuật trong `calc_state.json` thay đổi, hệ thống liên SKILL (`design-evaluation-audit`, `skill-phuluc-tmtt`, `SKILL_VERIFY`) đối chiếu sai lệch giữa dữ liệu hình học DXF và hồ sơ tính toán nguồn.
