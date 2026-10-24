---
name: Cost_Estimator
version: 1.2.0
last_updated: 2026-09-27
description: "Kỹ sư Định giá AI: Tính toán chi phí vật tư từ BOQ, so sánh chi phí giữa các phương án kết cấu (BTCT/Thép/Tiền chế), tính hàm lượng Carbon (Embodied Carbon), phân tích tác động tiến độ và chi phí lãi vay ẩn. Kích hoạt khi nhắc đến: Value Engineering, so sánh chi phí, tối ưu ngân sách, giảm hàm lượng thép, phân tích CAPEX, embodied carbon, ROI phương án."
---

# Cost Estimator AI — SKILL Entry Point

## Tổng quan

**Cost Estimator** là skill hỗ trợ **Value Engineering** (Tối ưu Giá trị) — phân tích chi phí kỹ thuật để đưa ra quyết định phương án kết cấu tiết kiệm nhất mà vẫn đảm bảo an toàn.

Skill này được thiết kế để phối hợp với `Design_Evaluation` (Rule C8, C11) và `Structural_Design_Engineer`, cung cấp góc nhìn kinh tế-kỹ thuật cho mọi quyết định thiết kế.

---

## Quy tắc Điều phối (Dispatcher Logic)

### Kích hoạt khi:
- User yêu cầu **"so sánh chi phí"**, **"Value Engineering"**, **"tối ưu ngân sách"**, **"giảm hàm lượng thép/bê tông"**
- Phát hiện η ≤ 0.70 (dự trữ > 30%) từ `Design_Evaluation` hoặc `Structural_Design_Engineer`
- Yêu cầu **"tính Carbon"**, **"embodied carbon"**, **"ESG"**, **"green building"**
- So sánh **nhiều phương án** cần ranking theo chi phí

### Không kích hoạt khi:
- Chỉ tính toán kết cấu thuần túy (không đề cập chi phí)
- Review hồ sơ thiết kế (trừ khi yêu cầu đánh giá tính kinh tế)

---

## Năng lực Cốt lõi (5 Modules)

### MODULE 1: BOQ Cost Analysis
**Chức năng:** Tính tổng chi phí từ file BOQ (Bill of Quantities)

**Input:**
- File Excel/CSV BOQ (format chuẩn: Hạng mục | Đơn vị | Khối lượng | Đơn giá | Thành tiền)
- Hoặc JSON từ `boq_extractor.py`

**Output:**
- Tổng chi phí BTCT, Thép, Ván khuôn, Nhân công
- Chi phí trên m² sàn (VNĐ/m²)
- So sánh với Budget ban đầu (Variance %)

**Script:** `scripts/boq_cost_analysis.py`

---

### MODULE 2: Comparative Cost Analysis
**Chức năng:** So sánh chi phí giữa các phương án kết cấu

**Ví dụ:**
- Phương án A: Dầm BTCT 400x700
- Phương án B: Dầm thép H400x200
- Phương án C: Dầm tiền chế BTCT

**Tiêu chí so sánh:**
1. **CAPEX (Chi phí đầu tư):** Vật liệu + Nhân công + Máy móc
2. **Thời gian thi công:** Ảnh hưởng đến chi phí lãi vay ẩn
3. **Hàm lượng vật liệu:** kg thép/m³ bê tông, m³ bê tông/m² sàn
4. **Carbon footprint:** kg CO₂ equivalent

**Script:** `scripts/compare_structural_options.py`

**Output format:**
```json
{
  "Options": [
    {
      "Name": "Phương án A - BTCT",
      "CAPEX_VND": 450000000,
      "Duration_Days": 45,
      "Steel_Ratio": 85,
      "Carbon_kgCO2": 12500,
      "Rank": 2
    },
    {
      "Name": "Phương án B - Thép",
      "CAPEX_VND": 520000000,
      "Duration_Days": 30,
      "Steel_Ratio": 120,
      "Carbon_kgCO2": 18000,
      "Rank": 1
    }
  ],
  "Recommendation": "Phương án B nhanh hơn 15 ngày → tiết kiệm 70M lãi vay → CAPEX điều chỉnh thấp hơn PA-A."
}
```

---

### MODULE 3: Material Optimization (Value Engineering)
**Chức năng:** Đề xuất giảm vật liệu khi phát hiện η ≤ 0.70

**Trigger tự động:**
- Khi `Design_Evaluation` hoặc `Structural_Design_Engineer` trả về η ≤ 0.70

**Quy trình:**
1. Đọc kết quả tính toán gốc (M_Rd, V_Rd, η)
2. Tính lại với tiết diện giảm 1 cấp
3. Kiểm tra η_new ≤ 0.90 (vẫn an toàn)
4. Tính tiết kiệm chi phí (VNĐ và %)

**Ví dụ:**
```
Hiện tại: Dầm B1 (400x700), As = 2010 mm², η = 0.68
Đề xuất: Dầm B1 (400x650), As = 1810 mm², η_new = 0.82
Tiết kiệm: 15 kg thép/dầm × 120 dầm × 25,000 VNĐ/kg = 45,000,000 VNĐ
```

**Script:** `scripts/material_optimization.py`

---

### MODULE 4: Embodied Carbon Calculator
**Chức năng:** Tính lượng Carbon phát thải (Embodied Carbon) của phương án kết cấu

**Database hệ số Carbon (kg CO₂/unit):**
| Vật liệu | Hệ số | Đơn vị | Nguồn |
|----------|-------|--------|-------|
| Bê tông B22.5 | 310 | kg CO₂/m³ | TCVN + ICE Database |
| Bê tông B30 | 350 | kg CO₂/m³ | ICE v3.0 |
| Thép CB400-V | 2,100 | kg CO₂/tấn | WorldSteel 2023 |
| Thép kết cấu S345 | 2,300 | kg CO₂/tấn | EPD Database |
| Gỗ ván khuôn | 430 | kg CO₂/m³ | FSC Data |

**Công thức:**
```
Total_Carbon = Σ (Khối_lượng_i × Hệ_số_Carbon_i)
Carbon_Intensity = Total_Carbon / Diện_tích_sàn (kg CO₂/m²)
```

**Benchmark:**
- Văn phòng thông thường: 200-250 kg CO₂/m²
- Green Building (LEED Gold): < 180 kg CO₂/m²
- Net Zero Target: < 100 kg CO₂/m² (2050)

**Script:** `scripts/carbon_calculator.py`

---

### MODULE 5: Schedule Impact & Hidden Interest Cost
**Chức năng:** Tính chi phí lãi vay ẩn do chậm tiến độ

**Input:**
- Tổng vốn đầu tư (VNĐ)
- Lãi suất vay (% năm)
- Thời gian thi công phương án A vs phương án B (ngày)

**Công thức:**
```
Lãi_vay_ẩn = Tổng_vốn × (Lãi_suất/365) × Δ_Thời_gian
```

**Ví dụ:**
```
Dự án: 500 tỷ VNĐ, lãi suất 10%/năm

PA-A (BTCT): 180 ngày
PA-B (Thép tiền chế): 120 ngày
Δ = 60 ngày

Lãi_vay_ẩn = 500,000,000,000 × (0.10/365) × 60 = 8,219,178,082 VNĐ

→ Dù PA-B đắt hơn 5 tỷ về CAPEX, nhưng tiết kiệm 8.2 tỷ lãi vay
→ Chọn PA-B (NPV cao hơn)
```

**Script:** `scripts/schedule_cost_impact.py`

---

## Cấu trúc Thư mục

```
Cost_Estimator/
├── SKILL.md                          ← BẠN ĐANG Ở ĐÂY
├── scripts/
│   ├── boq_cost_analysis.py          ← MODULE 1
│   ├── compare_structural_options.py ← MODULE 2
│   ├── material_optimization.py      ← MODULE 3
│   ├── carbon_calculator.py          ← MODULE 4
│   └── schedule_cost_impact.py       ← MODULE 5
├── data/
│   ├── material_unit_prices.json     ← Database đơn giá vật liệu (cập nhật Q2/2026)
│   ├── carbon_coefficients.json      ← Database hệ số Carbon
│   └── labor_rates.json              ← Đơn giá nhân công theo vùng
└── templates/
    └── cost_comparison_report.docx   ← Template báo cáo so sánh chi phí
```

---

## Quy tắc Đặc biệt

### Rule 1: Always Show Trade-offs (Luôn hiển thị đánh đổi)
Mọi đề xuất tiết kiệm phải nêu rõ:
- Tiết kiệm bao nhiêu (VNĐ và %)
- **Đánh đổi gì:** Thời gian, rủi ro, độ phức tạp thi công, carbon

**Ví dụ:**
```
✅ Tiết kiệm: 45M VNĐ (7.2%)
⚠️ Đánh đổi:
  - η tăng từ 68% → 82% (vẫn an toàn nhưng giảm dự trữ)
  - Không có dư lượng cho thay đổi thiết kế sau này
  - Tăng 2 ngày thời gian cốt thép (phức tạp hơn)
```

### Rule 2: Budget Variance Alert (Cảnh báo Vượt ngân sách)
Nếu tổng chi phí vượt Budget > 5% → **BẮT BUỘC** cảnh báo:
```
🚨 BUDGET ALERT: Chi phí ước tính 520M vượt ngân sách duyệt 480M (+8.3%)
→ Yêu cầu:
   1. Phê duyệt bổ sung 40M, HOẶC
   2. Áp dụng VE để giảm xuống ≤ 500M (cho phép +5%)
```

### Rule 3: Carbon Reporting Mandatory (Báo cáo Carbon bắt buộc)
Từ 2026, mọi báo cáo so sánh phương án PHẢI có mục **"Hàm lượng Carbon"** (theo Rule 20 - ESG & Future-proofing).

### Rule 4: Multi-Criteria Decision Matrix
Khi so sánh ≥ 3 phương án, xuất **Decision Matrix** (bảng điểm đa tiêu chí):

| Tiêu chí | Trọng số | PA-A | PA-B | PA-C |
|----------|----------|------|------|------|
| Chi phí CAPEX | 35% | 8/10 | 6/10 | 7/10 |
| Thời gian thi công | 25% | 5/10 | 9/10 | 7/10 |
| Carbon footprint | 20% | 7/10 | 4/10 | 8/10 |
| Rủi ro thi công | 20% | 8/10 | 6/10 | 9/10 |
| **Tổng điểm** | | **7.05** | **6.30** | **7.55** |

→ **Khuyến nghị: Phương án C** (điểm cao nhất, cân bằng tốt nhất)

---

## Phối hợp với Các Skill khác

### Với Design_Evaluation:
```
SKILLKC phân tích → phát hiện η = 0.65 →
Cost_Estimator tự động kích hoạt MODULE 3 (Material Optimization) →
Đề xuất VE → Review Gate hiển thị tiết kiệm chi phí
```

### Với Structural_Design_Engineer:
```
SKILL_CALC tính nhiều phương án →
Cost_Estimator so sánh chi phí (MODULE 2) →
SKILL_CALC_REPORT chèn bảng so sánh vào Thuyết minh tính toán
```

---

## Ví dụ Workflow End-to-End

**User:** *"So sánh chi phí giữa dầm BTCT 400x700 và dầm thép H400x200, dự án 5000m² sàn."*

**AI:**
1. Kích hoạt `Cost_Estimator` MODULE 2
2. Gọi `compare_structural_options.py`:
   ```bash
   python compare_structural_options.py \
     --option1 '{"type":"RC", "b":400, "h":700, "L":6000}' \
     --option2 '{"type":"Steel", "section":"H400x200", "L":6000}' \
     --floor_area 5000 \
     --interest_rate 0.10
   ```
3. Đọc JSON output
4. Gọi `carbon_calculator.py` cho cả 2 phương án
5. Tổng hợp Decision Matrix
6. Xuất báo cáo so sánh (gọi `SKILL_REPORT` MODE 2)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-08-04 | Initial release - 5 modules cơ bản |
