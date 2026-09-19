# Calculators — Engine Tính toán Deterministic

> **Quy tắc C14 (AGENTS.md):** AI nghiêm cấm tự nhẩm các phép toán kỹ thuật phức tạp. Phải gọi script trong folder này và đọc kết quả JSON từ stdout.

---

## Danh sách Scripts

### Nhóm 1: Kết cấu Thép (Steel Structures)

| Script | Tiêu chuẩn | Trạng thái | Mô tả |
|--------|-----------|-----------|-------|
| `steel_member_check.py` | TCVN 5575:2012 | ⚠️ **Legacy** | Kiểm tra bền theo ứng suất pháp (strength check only). Không kiểm tra LTB. |
| `steel_member_check_v2024.py` | TCVN 5575:2024 | ✅ **Recommended** | Kiểm tra đầy đủ: bền uốn + ổn định uốn xoắn (LTB) + cắt. |

**Quy tắc sử dụng:**
- Dự án mới (từ 2024): dùng `steel_member_check_v2024.py`
- Dự án cũ (review hồ sơ 2012-2023): dùng `steel_member_check.py` và ghi rõ cảnh báo trong báo cáo

**Ví dụ gọi v2024:**
```bash
python steel_member_check_v2024.py \
  --M 250 --N 100 --V 80 \
  --Area 76.8 --Wx 1200 --Iy 600 \
  --tf 10 --tw 6 --h 400 --b 200 \
  --L_beam 6000 --fy 345 \
  --lateral_support false
```

**Output chính:**
- `eta_M`: Utilization ratio uốn
- `eta_LTB`: Utilization ratio ổn định uốn xoắn (chỉ khi lateral_support=false)
- `eta_V`: Utilization ratio cắt
- `Calculation_Logs`: Mảng 5 bước tính toán chi tiết

---

### Nhóm 2: Bê tông Cốt thép (RC Structures)

| Script | Tiêu chuẩn | Trạng thái |
|--------|-----------|-----------|
| `rc_flexure_design.py` | TCVN 5574:2018 | ✅ Active |
| `deflection_check.py` | TCVN 5574:2018 (PL M) | ✅ Active |

**Ví dụ:**
```bash
python rc_flexure_design.py --M 250 --b 300 --h 600 --h0 550 --fc 22.5 --fy 400
```

---

### Nhóm 3: Móng & Nền (Foundation)

| Script | Tiêu chuẩn | Trạng thái |
|--------|-----------|-----------|
| `foundation_bearing.py` | TCVN 9362:2012 | ✅ Active |

**Lưu ý:** Script này chỉ kiểm tra sức chịu tải nền. CHƯA kiểm tra lún (settlement). Cần bổ sung module `settlement_calc.py` trong Phase 4.

---

### Nhóm 4: Tải trọng (Loads)

| Script | Tiêu chuẩn | Trạng thái |
|--------|-----------|-----------|
| `wind_load_calc.py` | TCVN 2737:2023 | ✅ Active |

**Lưu ý quan trọng:** Script này BẮT BUỘC truyền `--gamma_f` tường minh. Không còn giá trị mặc định.

```bash
python wind_load_calc.py --W0 0.45 --k 1.0 --c 0.8 --gamma_f 1.2
```

---

## Cấu trúc JSON Output Chuẩn

Mọi script PHẢI trả về JSON với cấu trúc tối thiểu:

```json
{
  "Input": { /* Tham số đầu vào */ },
  "Results": {
    "eta_max": 0.85,
    "Rating": "YELLOW",
    "Status": "PASS"
  },
  "Standard_Method": "TCVN 5575:2024",
  "Scope_Limitation": "Chưa kiểm tra: X, Y, Z",
  "Unverified_Items": ["A", "B", "C"],
  "Warnings": [],
  "Calculation_Logs": [
    {
      "Step": 1,
      "Description": "...",
      "Principle": "...",
      "Formula": "...",
      "Citation": {
        "Ma_TC": "TCVN 5575",
        "Nam": "2024",
        "Dieu_Muc": "Điều 6.2.5",
        "Bang_Hinh": "Bảng 3",
        "Trang": "N/A",
        "Trich_Yeu": "..."
      },
      "Substitution": "...",
      "Result": "...",
      "Utilization": "η = 0.850 (85.0%)",
      "Rating": "YELLOW"
    }
  ],
  "Metadata": {
    "Script_Version": "2.0.0",
    "Standard_Version": "TCVN 5575:2024",
    "Updated_Date": "2026-08-04"
  }
}
```

---

## Rating System (Color Code)

| Rating | η Range | Màu | Ý nghĩa |
|--------|---------|-----|---------|
| GREEN | ≤ 0.70 | 🟢 | An toàn, dự trữ > 30% → Value Engineering |
| YELLOW | 0.70 - 0.90 | 🟡 | Đạt, mức sử dụng hợp lý |
| ORANGE | 0.90 - 1.00 | 🟠 | Sát ngưỡng → Cảnh báo |
| RED | > 1.00 | 🔴 | KHÔNG ĐẠT → Thiết kế lại |

---

## Quy trình Bổ sung Script Mới

### Bước 1: Đặt tên file
Format: `[vật_liệu]_[loại_kiểm_tra]_[version].py`

Ví dụ:
- `rc_shear_check_v2018.py`
- `steel_connection_bolts_v2024.py`
- `pile_settlement_v2025.py`

### Bước 2: Template code bắt buộc

```python
import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
import json
import argparse

def main_function(...):
    """
    Docstring bắt buộc ghi rõ:
    - Công thức áp dụng
    - Tiêu chuẩn
    - Phạm vi (scope)
    - Hạn chế (limitation)
    """
    logs = []
    
    # Bước 1: ...
    logs.append({
        "Step": 1,
        "Description": "...",
        "Principle": "...",
        "Formula": "...",
        "Citation": {...},
        "Substitution": "...",
        "Result": "..."
    })
    
    # ... các bước tiếp theo
    
    return {
        "Input": {...},
        "Results": {...},
        "Standard_Method": "TCVN XXXX:YYYY",
        "Scope_Limitation": "...",
        "Unverified_Items": [...],
        "Calculation_Logs": logs,
        "Metadata": {
            "Script_Version": "1.0.0",
            "Updated_Date": "YYYY-MM-DD"
        }
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="...")
    # ... định nghĩa args
    args = parser.parse_args()
    result = main_function(...)
    print(json.dumps(result, indent=2, ensure_ascii=False))
```

### Bước 3: Test & Validate

```bash
# Test với data mẫu
python new_script.py --arg1 value1 --arg2 value2

# Validate JSON output
python new_script.py ... | python -m json.tool
```

### Bước 4: Cập nhật file này (README_CALCULATORS.md)

Thêm dòng vào bảng phù hợp ở trên.

---

## Troubleshooting

### Lỗi: "Script trả về trống"
- Kiểm tra encoding: `sys.stdout.reconfigure(encoding='utf-8')`
- Kiểm tra `print(json.dumps(...))` ở cuối main block

### Lỗi: "Citation Object thiếu field"
- Citation PHẢI có đủ 6 field: `Ma_TC`, `Nam`, `Dieu_Muc`, `Bang_Hinh`, `Trang`, `Trich_Yeu`
- Nếu không có Trang/Bảng → điền `"N/A"`, không để trống

### Lỗi: "Calculation_Logs không hiển thị trong báo cáo"
- Kiểm tra `Calculation_Logs` là mảng (array), không phải object
- Mỗi step phải có đủ: `Step`, `Description`, `Formula`, `Result`

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.0.0 | 2026-08-04 | Thêm `steel_member_check_v2024.py` (TCVN 5575:2024). Deprecate bản 2012. |
| 1.5.0 | 2026-07-28 | Bổ sung `Calculation_Logs` cho tất cả script cũ. |
| 1.0.0 | 2024-01-01 | Release ban đầu với 5 scripts. |
