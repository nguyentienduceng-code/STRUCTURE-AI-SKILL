# CALCULATOR_OUTPUT_STANDARD — Tiêu Chuẩn Output cho Calculator Scripts

> **Mục đích:** Đảm bảo tất cả calculator scripts trả về output theo format thống nhất
> **Phạm vi:** Áp dụng cho MỌI script tính toán trong `.agents/skills/*/scripts/`
> **Cập nhật:** 2026-09-25 — v1.0.0

---

## 1. TỔNG QUAN

### 1.1 Mục tiêu

```
Trước (không chuẩn):
    python calc_rc_beam.py --b 200 --h 400 --M 78.5
    → In ra text: "M_Rd = 310.5 kN.m"

Sau (chuẩn hóa):
    python calc_rc_beam.py --b 200 --h 400 --M 78.5 --json
    → Trả về JSON với đầy đủ meta, logs, results
```

### 1.2 Lợi ích

- **Consistency:** Tất cả calculator cùng format
- **Traceability:** Calculation_Logs đầy đủ
- **Verification:** SKILL_VERIFY dễ kiểm tra
- **Automation:** Review Gate tự động parse

---

## 2. STANDARD OUTPUT SCHEMA

### 2.1 Full Schema

```json
{
  "meta": {
    "script_name": "calc_rc_beam.py",
    "version": "1.2.0",
    "standard_method": "TCVN 5574:2018",
    "timestamp": "2026-09-25T10:30:00+07:00",
    "calculator": "Nguyen Van A",
    "source": "calculated"
  },
  "inputs": {
    "b": 200,
    "h": 400,
    "L": 6000,
    "M_ed": 78.5,
    "V_ed": 125.3
  },
  "calculation_logs": [
    {
      "step": 1,
      "description": "Tính chiều cao làm việc",
      "formula": "d = h - a",
      "substitution": "d = 400 - 35 = 365 mm",
      "result": 365,
      "unit": "mm",
      "citation": "TCVN 5574:2018 §5.2.2"
    }
  ],
  "results": {
    "M_rd": 310.5,
    "V_rd": 245.0,
    "A_s_req": 265.5,
    "A_s_prov": 763,
    "eta_M": 0.348,
    "eta_V": 0.511
  },
  "warnings": [],
  "confidence_score": 0.92
}
```

### 2.2 Required Fields

| Field | Type | Required | Mô tả |
|-------|------|----------|--------|
| `meta.script_name` | string | ✅ | Tên script |
| `meta.version` | string | ✅ | Phiên bản script |
| `meta.standard_method` | string | ✅ | Tiêu chuẩn sử dụng |
| `meta.timestamp` | string | ✅ | Thời điểm tính |
| `calculation_logs` | array | ✅ | Array các bước tính |
| `results` | object | ✅ | Kết quả chính |
| `confidence_score` | number | ✅ | Điểm tin cậy (0-1) |

### 2.3 Calculation Log Entry Schema

```json
{
  "step": 1,
  "description": "Mô tả bước tính",
  "formula": "Công thức tổng quát",
  "substitution": "Thế số cụ thể",
  "result": 365,
  "unit": "mm",
  "citation": "TCVN 5574:2018 §5.2.2"
}
```

---

## 3. TEMPLATE IMPLEMENTATION

### 3.1 Python Template

```python
#!/usr/bin/env python3
"""
[Script Name] - [Brief Description]

Tiêu chuẩn output: Xem CALCULATOR_OUTPUT_STANDARD.md

Usage:
    python script.py --input data.json --json
    python script.py --b 200 --h 400 --json
"""

import sys
import json
import argparse
from datetime import datetime

# Ensure UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# ============================================================================
# CALCULATION FUNCTIONS
# ============================================================================

def calculate(params):
    """Hàm tính toán chính"""
    # ... calculation logic ...
    
    calculation_logs = []
    
    # Step 1: [description]
    step_1_result = params["h"] - params["a"]
    calculation_logs.append({
        "step": 1,
        "description": "Tính chiều cao làm việc",
        "formula": "d = h - a",
        "substitution": f"d = {params['h']} - {params['a']}",
        "result": step_1_result,
        "unit": "mm",
        "citation": "TCVN 5574:2018 §5.2.2"
    })
    
    # Step 2: ...
    
    # Results
    results = {
        "M_rd": 310.5,
        "eta_M": params["M_ed"] / 310.5
    }
    
    return calculation_logs, results


# ============================================================================
# OUTPUT GENERATOR
# ============================================================================

def generate_output(script_name, version, standard_method, inputs, 
                   calculation_logs, results, warnings=None):
    """
    Tạo output theo standard format
    
    Args:
        script_name: Tên script
        version: Phiên bản
        standard_method: Tiêu chuẩn
        inputs: Dict đầu vào
        calculation_logs: Array các bước tính
        results: Dict kết quả
        warnings: Array warnings (optional)
    
    Returns:
        Dict theo standard schema
    """
    # Calculate confidence score
    confidence = calculate_confidence(calculation_logs, results)
    
    output = {
        "meta": {
            "script_name": script_name,
            "version": version,
            "standard_method": standard_method,
            "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S+07:00"),
            "calculator": inputs.get("calculator", "AI Assistant"),
            "source": "calculated"
        },
        "inputs": inputs,
        "calculation_logs": calculation_logs,
        "results": results,
        "warnings": warnings or [],
        "confidence_score": confidence
    }
    
    return output


def calculate_confidence(logs, results):
    """
    Tính confidence score đơn giản
    
    Returns:
        float 0-1
    """
    score = 1.0
    
    # Check logs completeness
    if not logs:
        return 0.3
    
    complete_logs = sum(1 for log in logs 
                       if all(k in log for k in ["formula", "result"]))
    
    log_ratio = complete_logs / len(logs) if logs else 0
    score = min(score, 0.5 + 0.5 * log_ratio)
    
    # Check results completeness
    if not results:
        return 0.2
    
    # Check for warnings
    # (Could add more sophisticated scoring)
    
    return round(score, 3)


def print_json(output, output_file=None):
    """In output dạng JSON"""
    json_str = json.dumps(output, indent=2, ensure_ascii=False)
    
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(json_str)
        print(f"Output saved to: {output_file}")
    else:
        print(json_str)


def print_human_readable(output):
    """In output dạng text cho người đọc"""
    print(f"\n{'='*60}")
    print(f"KẾT QUẢ TÍNH TOÁN")
    print(f"{'='*60}")
    
    print(f"\nScript: {output['meta']['script_name']}")
    print(f"Tiêu chuẩn: {output['meta']['standard_method']}")
    print(f"Thời gian: {output['meta']['timestamp']}")
    
    print(f"\n--- Kết quả ---")
    for key, value in output["results"].items():
        if isinstance(value, float):
            print(f"  {key}: {value:.3f}")
        else:
            print(f"  {key}: {value}")
    
    print(f"\n--- Calculation Logs ---")
    for log in output["calculation_logs"]:
        print(f"\n  Bước {log['step']}: {log['description']}")
        print(f"    Công thức: {log['formula']}")
        print(f"    Thế số: {log['substitution']}")
        print(f"    Kết quả: {log['result']} {log.get('unit', '')}")
        if log.get('citation'):
            print(f"    Trích dẫn: {log['citation']}")
    
    if output.get("warnings"):
        print(f"\n--- Warnings ---")
        for warning in output["warnings"]:
            print(f"  ⚠️ {warning}")
    
    print(f"\nConfidence Score: {output['confidence_score']:.3f}")
    print(f"{'='*60}\n")


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="[Script Description]")
    parser.add_argument("--json", action="store_true", 
                       help="Output JSON format")
    parser.add_argument("--output", "-o", 
                       help="Output file path")
    
    # Add input arguments
    parser.add_argument("--b", type=float, help="Chiều rộng (mm)")
    parser.add_argument("--h", type=float, help="Chiều cao (mm)")
    parser.add_argument("--M", type=float, help="Momen (kNm)")
    # ... more args ...
    
    args = parser.parse_args()
    
    # Build inputs dict
    inputs = {
        "b": args.b,
        "h": args.h,
        "M_ed": args.M
    }
    
    # Run calculation
    logs, results = calculate(inputs)
    
    # Generate output
    output = generate_output(
        script_name="calc_rc_beam.py",
        version="1.0.0",
        standard_method="TCVN 5574:2018",
        inputs=inputs,
        calculation_logs=logs,
        results=results
    )
    
    # Output
    if args.json:
        print_json(output, args.output)
    else:
        print_human_readable(output)


if __name__ == "__main__":
    main()
```

---

## 4. EXISTING CALCULATORS AUDIT

### 4.1 Design_Evaluation/calculators/

| Calculator | Status | Notes |
|------------|--------|-------|
| `calc_rc_beam.py` | ⏳ Cần update | Thêm --json flag, calculation_logs |
| `calc_rc_column.py` | ⏳ Cần update | Same |
| `eta_check.py` | ⏳ Cần update | Same |
| `load_combination.py` | ⏳ Cần update | Same |

### 4.2 Structural_Design_Engineer/scripts/

| Calculator | Status | Notes |
|------------|--------|-------|
| `calc_rc_beam.py` | ⏳ Cần update | Thêm --json flag |
| `calc_rc_column.py` | ⏳ Cần update | Same |
| `calc_steel_beam.py` | ⏳ Cần update | Same |
| `calc_connection.py` | ⏳ Cần update | Same |
| `calc_bolt.py` | ⏳ Cần update | Same |
| `calc_weld.py` | ⏳ Cần update | Same |
| `calc_foundation.py` | ⏳ Cần update | Same |

### 4.3 SKILL_GEOTECH/scripts/

| Calculator | Status | Notes |
|------------|--------|-------|
| `calc_geostatic_stress.py` | ✅ | Đã có output chuẩn |
| `calc_soil_params_mc.py` | ✅ | Đã có output chuẩn |
| `calc_soil_params_hs.py` | ✅ | Đã có output chuẩn |
| `calc_spt_correlations.py` | ✅ | Đã có output chuẩn |
| `calc_base_heave.py` | ✅ | Đã có output chuẩn |
| `calc_strut_capacity.py` | ✅ | Đã có output chuẩn |

---

## 5. CHECKLIST CHO SCRIPTS MỚI

### 5.1 Required Features

```markdown
□ Thêm `--json` flag cho JSON output
□ Thêm `--output` flag cho file path
□ Implement `generate_output()` function
□ Tất cả calculations phải có `calculation_logs`
□ Mỗi log phải có: step, formula, substitution, result, citation
□ Include `meta` section với script_name, version, standard_method
□ Calculate và include `confidence_score`
```

### 5.2 Example Checklist

```python
# □ Script có template header
#!/usr/bin/env python3
"""
calc_example.py - Example Calculator

Tiêu chuẩn: Xem CALCULATOR_OUTPUT_STANDARD.md
Version: 1.0.0
"""

# □ Imports chuẩn
import sys
import json
from datetime import datetime

# □ UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# □ Argparse với --json
parser.add_argument("--json", action="store_true")

# □ generate_output() function
def generate_output(...): ...

# □ main() với JSON output
def main():
    if args.json:
        print_json(output)
```

---

## 6. VALIDATION SCRIPT

### 6.1 Script để validate output

```python
#!/usr/bin/env python3
"""
validate_calculator_output.py

Validate calculator output against CALCULATOR_OUTPUT_STANDARD

Usage:
    python validate_calculator_output.py output.json
"""

import json
import sys

REQUIRED_META = ["script_name", "version", "standard_method", "timestamp"]
REQUIRED_LOG_FIELDS = ["step", "formula", "result"]

def validate(output):
    errors = []
    warnings = []
    
    # Check meta
    for field in REQUIRED_META:
        if field not in output.get("meta", {}):
            errors.append(f"Missing meta.{field}")
    
    # Check calculation_logs
    logs = output.get("calculation_logs", [])
    if not logs:
        errors.append("Missing calculation_logs")
    
    for i, log in enumerate(logs):
        for field in REQUIRED_LOG_FIELDS:
            if field not in log:
                errors.append(f"Log[{i}] missing {field}")
    
    # Check results
    if "results" not in output:
        errors.append("Missing results")
    
    # Check confidence_score
    if "confidence_score" not in output:
        warnings.append("Missing confidence_score")
    elif not (0 <= output["confidence_score"] <= 1):
        errors.append("confidence_score must be between 0 and 1")
    
    return errors, warnings


if __name__ == "__main__":
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        output = json.load(f)
    
    errors, warnings = validate(output)
    
    if errors:
        print("❌ ERRORS:")
        for e in errors:
            print(f"  - {e}")
    
    if warnings:
        print("⚠️ WARNINGS:")
        for w in warnings:
            print(f"  - {w}")
    
    if not errors and not warnings:
        print("✅ Output is valid")
    
    sys.exit(1 if errors else 0)
```

---

## 7. VERSION HISTORY

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-09-25 | Initial release |
