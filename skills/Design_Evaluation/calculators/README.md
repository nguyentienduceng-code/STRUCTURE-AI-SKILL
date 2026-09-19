# Calculators Suite — Design_Evaluation

> **Version:** 2.2.0  
> **Last Updated:** 2026-08-30  
> **Reference:** [STANDARDS_LOCK.md](../STANDARDS_LOCK.md)

---

## Tổng quan

Thư mục chứa các script tính toán kết cấu. **Mọi tính toán phải gọi script**, không tự nhẩm tay (theo AGENTS.md Rule C14).

---

## Bảng Scripts

| Script | Tiêu chuẩn | Phạm vi | Trạng thái |
|--------|-------------|----------|-------------|
| `rc_flexure_design.py` | **TCVN 5574:2018** | Tiết diện chữ nhật, cốt đơn, chịu uốn | ✅ OK |
| `steel_member_check_v2024.py` | **TCVN 5575:2024** | Thép chịu nén-uốn-cắt, LTB | ✅ OK v2.1.0 |
| `steel_member_check.py` | ~~TCVN 5575:2012~~ | Thép (bản cũ) | ⚠️ **DEPRECATED** — Dùng v2024 |
| `wind_load_calc.py` | **TCVN 2737:2023** | Tải trọng gió tĩnh | ✅ OK |
| `earthquake_load_calc.py` | **TCVN 9386:2025** (P1+P5) | Tải trọng động đất | ✅ OK |
| `deflection_check.py` | TCVN 5574:2018 | Kiểm tra độ võng | ✅ OK |
| `foundation_bearing.py` | TCVN 9362:2012 | Sức chịu tải móng nông | ✅ OK |

---

## Quick Start

### Chạy 1 script đơn lẻ

```bash
# Tính thép theo TCVN 5575:2024
python steel_member_check_v2024.py \
  --M 250 --V 80 --Area 84.8 --Wx 1310 --Iy 562 \
  --tf 13 --tw 8 --h 400 --b 200 --L_beam 6000 --fy 345

# Tính BTCT uốn theo TCVN 5574:2018
python rc_flexure_design.py \
  --M 180 --b 0.3 --h0 0.65 --Rb 14.5 --Rs 365

# Tính gió theo TCVN 2737:2023
python wind_load_calc.py \
  --w0 83 --z 30 --terrain B --c 0.8 --gamma_f 1.2 \
  --gamma_f_source "TCVN 2737:2023 Điều 10.2 Bảng 4 Tr.45"
```

### Chạy nhiều script (Pipeline)

```python
# Gọi từ Python code
from steel_member_check_v2024 import check_steel_member_v2024
from rc_flexure_design import design_rc_flexure

# Tính dầm thép
result_steel = check_steel_member_v2024(
    M=250, V=80, Area=84.8, Wx=1310, Iy=562,
    tf=13, tw=8, h=400, b=200, L_beam=6000, fy=345
)

# Tính dầm BTCT
result_rc = design_rc_flexure(
    M=180, b=0.3, h0=0.65, Rb=14.5, Rs=365
)
```

---

## Output Format (JSON)

Mọi script trả về JSON với cấu trúc chuẩn:

```json
{
  "Input": { ... },
  "Results": {
    "M_c_Rd": 310.5,
    "eta_M": 0.805,
    ...
  },
  "Standard_Method": "TCVN 5575:2024",
  "Scope_Limitation": "...",
  "Calculation_Logs": [
    {
      "Step": 1,
      "Description": "...",
      "Formula": "...",
      "Citation": { ... },
      "Substitution": "...",
      "Result": "..."
    }
  ]
}
```

---

## Validation

### Input Validation (phải có)

```python
def validate_inputs(**kwargs):
    errors = []
    if kwargs.get('M', 0) <= 0:
        errors.append("Momen M phải > 0")
    if kwargs.get('b', 0) <= 0:
        errors.append("Bề rộng b phải > 0")
    if errors:
        raise ValueError("; ".join(errors))
```

### Unit Tests

```bash
# Chạy tất cả tests
pytest tests/ -v

# Chạy 1 test cụ thể
pytest tests/test_steel_member.py::test_basic_calculation -v
```

---

## Known Issues

| Issue | Workaround | Fixed |
|-------|------------|-------|
| `calc_steel_beam.py` dùng EN 1993-1-1 | Dùng `steel_member_check_v2024.py` cho TCVN | ✅ |
| `steel_member_check.py` (2012) cũ | Migrate sang v2024 | ⚠️ DEPRECATED |

---

## Tiếp theo

- **Design Report:** [SKILL_REPORT.md](../SKILL_REPORT.md)
- **Standards:** [STANDARDS_LOCK.md](../STANDARDS_LOCK.md)
- **Error Codes:** [AGENTS.md](../AGENTS.md) mục 15
