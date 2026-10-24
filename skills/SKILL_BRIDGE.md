---
name: SKILL_BRIDGE
version: 3.0.0
last_updated: 2026-10-17
description: "Protocol định nghĩa cấu trúc dữ liệu Handoff giữa các SKILL, validation rules, và error handling. Đây là nguồn sự thật duy nhất cho inter-skill communication."
---

# SKILL_BRIDGE — Giao Thức Handoff Giữa Các Skill

> **Phạm vi:** Áp dụng cho **MỌI** handoff giữa các skill trong `.agents/skills/`
> **Bắt buộc:** Mọi skill output phải tuân theo schema định nghĩa tại đây
> **Cập nhật:** 2026-10-17 — v3.0.0 (Unified Inter-Skill Handoff & Auto-Invocation Protocols)

---

## 1. TỔNG QUAN HANDOFF PROTOCOL

### 1.1 Mục đích

```
SKILL_A ──JSON Handoff──► SKILL_B
        │
        └──► Validation: Schema check
        └──► Transformation: Data mapping nếu cần
        └──► Error: Reject + Request supplemental
```

### 1.2 Các Loại Handoff

| Handoff Type | Source | Target | Mục đích |
|--------------|--------|--------|-----------|
| `structural_design_to_eval` | Structural_Design_Engineer | Design_Evaluation | Review thiết kế |
| `eval_to_phuluc` | Design_Evaluation | SKILL_PHULUC | Tạo phụ lục |
| `calc_to_verify` | (any calc) | SKILL_VERIFY | Kiểm chứng |
| `geotech_to_structural` | SKILL_GEOTECH | Structural_Design_Engineer | Foundation params |
| `eval_to_cost` | Design_Evaluation | Cost_Estimator | Value Engineering |
| `forensic_to_eval` | SKILL_FORENSIC | Design_Evaluation | NCR handling |

---

## 2. HANDOFF SCHEMA DEFINITIONS

### 2.1 Base Handoff Schema (Bắt buộc cho mọi handoff)

```json
{
  "handoff_meta": {
    "handoff_id": "HND-{SourceSKILL}-{TargetSKILL}-{YYYYMMDD}-{NNN}",
    "handoff_type": "structural_design_to_eval",
    "source_skill": "Structural_Design_Engineer",
    "target_skill": "Design_Evaluation",
    "timestamp": "2026-09-25T10:30:00+07:00",
    "confidence_level": "HIGH",
    "priority": "NORMAL",
    "status": "PENDING"
  },
  "project_context": {
    "project_name": "string",
    "project_code": "string",
    "phase": "BVTC|BPTC|THIC|HOAN_CONG",
    "standards_lock_version": "string"
  },
  "payload": {
    // Schema cụ thể theo từng handoff type
  },
  "validation": {
    "schema_valid": true,
    "missing_fields": [],
    "warnings": []
  }
}
```

### 2.2 Structural Design Handoff Schema

```json
{
  "handoff_meta": {
    "handoff_id": "HND-SDE-DEV-20260925-001",
    "handoff_type": "structural_design_to_eval",
    "source_skill": "Structural_Design_Engineer",
    "target_skill": "Design_Evaluation",
    "timestamp": "2026-09-25T10:30:00+07:00",
    "confidence_level": "HIGH",
    "priority": "NORMAL",
    "status": "PENDING"
  },
  "project_context": {
    "project_name": "Công trình ABC",
    "project_code": "ABC-2024",
    "phase": "BVTC",
    "standards_lock_version": "v2.3.0"
  },
  "payload": {
    "design_type": "RC_BEAM|RC_COLUMN|STEEL_BEAM|FOUNDATION|CONNECTION",
    "element_id": "B1|D1|C1|F1|LK-01",
    "geometry": {
      "b": 200,
      "h": 400,
      "L": 6000,
      "a": 35
    },
    "materials": {
      "concrete": "B30",
      "steel": "CB400"
    },
    "forces": {
      "M_ed": 78.5,
      "V_ed": 125.3,
      "N_ed": 0
    },
    "results": {
      "M_rd": 310.5,
      "V_rd": 245.0,
      "A_s_req": 265.5,
      "A_s_prov": 763,
      "eta_M": 0.348,
      "eta_V": 0.511
    },
    "rebar_selected": {
      "top": {"n": 3, "dia": 20},
      "bottom": {"n": 2, "dia": 20},
      "stirrup": {"dia": 8, "s1": 100, "s2": 200}
    },
    "calculation_logs": [
      {
        "step": 1,
        "formula": "d = h - a = 400 - 35",
        "substitution": "d = 365 mm",
        "result": 365,
        "unit": "mm",
        "citation": "TCVN 5574:2018 §5.2.2"
      }
    ],
    "standard_method": "TCVN 5574:2018",
    "drawings": {
      "sketch_required": true,
      "sketch_pending": false
    }
  },
  "validation": {
    "schema_valid": true,
    "missing_fields": [],
    "warnings": [],
    "required_for_eval": [
      "geometry", "materials", "forces", "results", "calculation_logs"
    ]
  }
}
```

### 2.3 Design Evaluation Handoff Schema

```json
{
  "handoff_meta": {
    "handoff_id": "HND-DEV-PHL-20260925-001",
    "handoff_type": "eval_to_phuluc",
    "source_skill": "Design_Evaluation",
    "target_skill": "SKILL_PHULUC",
    "timestamp": "2026-09-25T10:30:00+07:00",
    "confidence_level": "HIGH",
    "priority": "NORMAL",
    "status": "PENDING"
  },
  "project_context": {
    "project_name": "Công trình ABC",
    "project_code": "ABC-2024",
    "phase": "BVTC",
    "owner": "Chủ Đầu Tư ABC",
    "designer": "Công ty XYZ"
  },
  "payload": {
    "evaluation_type": "REVIEW|NCR|TOTAL_QUANTITY|COMPARISON",
    "scope": ["Dầm B1", "Cột C1"],
    "review_results": {
      "element_id": "B1",
      "status": "PASS|WARNING|FAIL",
      "eta_M": 0.348,
      "eta_V": 0.511,
      "issues": [
        {
          "type": "MINOR|MAJOR|CRITICAL",
          "description": "string",
          "recommendation": "string"
        }
      ]
    },
    "total_quantities": {
      "concrete_m3": 150.5,
      "steel_kg": 2500.0,
      "formwork_m2": 320.0
    },
    "comparison_results": {
      // Optional: nếu evaluation_type = COMPARISON
    }
  },
  "validation": {
    "schema_valid": true,
    "missing_fields": [],
    "warnings": []
  }
}
```

### 2.4 Geotech Handoff Schema

```json
{
  "handoff_meta": {
    "handoff_id": "HND-GEO-STR-20260925-001",
    "handoff_type": "geotech_to_structural",
    "source_skill": "SKILL_GEOTECH",
    "target_skill": "Structural_Design_Engineer",
    "timestamp": "2026-09-25T10:30:00+07:00",
    "confidence_level": "HIGH",
    "priority": "NORMAL",
    "status": "PENDING"
  },
  "project_context": {
    "project_name": "Công trình ABC",
    "project_code": "ABC-2024",
    "standards_lock_version": "v2.3.0"
  },
  "payload": {
    "foundation_type": "SINGLE|STRIP|PILES|PILE_CAP",
    "soil_layers": [
      {
        "layer_id": 1,
        "name": "Đất đắp",
        "thickness": 2.0,
        "γ": 18.0,
        "c": 5.0,
        "φ": 25.0,
        "E50": 15000,
        "model": "MC",
        "groundwater_depth": 3.5
      }
    ],
    "foundation_params": {
      "q_allow": 200,
      "settlement_allow": 25,
      "soil_pressure_calc": true
    },
    "excavation_params": {
      // Optional: nếu có hố đào
      "depth": 5.0,
      "width": 20.0,
      "base_heave_FS": 2.1
    },
    "plaxis_input": {
      "model_type": "MC|HS|SSC",
      "materials_prepared": true
    }
  },
  "validation": {
    "schema_valid": true,
    "missing_fields": [],
    "warnings": [
      "Groundwater at -3.5m may affect excavation stability"
    ]
  }
}
```

### 2.5 SKILL_VERIFY Handoff Schema

```json
{
  "handoff_meta": {
    "handoff_id": "HND-ANY-VER-20260925-001",
    "handoff_type": "any_to_verify",
    "source_skill": "Structural_Design_Engineer",
    "target_skill": "SKILL_VERIFY",
    "timestamp": "2026-09-25T10:30:00+07:00",
    "confidence_level": "HIGH",
    "priority": "NORMAL",
    "status": "PENDING"
  },
  "project_context": {
    "project_name": "Công trình ABC",
    "project_code": "ABC-2024"
  },
  "payload": {
    "verification_type": "INTER_MODULE|STANDARD_VERSION|CALCULATION_LOGS|EXTERNAL_SOFTWARE|REPORT_CONSISTENCY",
    "data_to_verify": {
      "element_id": "B1",
      "source_module": "Structural_Design_Engineer",
      "reference_module": "Design_Evaluation",
      "values": {
        "M_rd_source": 310.5,
        "M_rd_reference": 298.2,
        "eta_source": 0.348,
        "eta_reference": 0.352
      }
    },
    "threshold": {
      "variance_pct": 5.0,
      "eta_variance_pct": 3.0
    }
  },
  "validation": {
    "schema_valid": true,
    "missing_fields": [],
    "warnings": []
  }
}
```

---

## 3. VALIDATION RULES

### 3.1 Required Fields Check

```python
REQUIRED_FIELDS = {
    "base": ["handoff_meta", "project_context", "payload"],
    "structural_design": ["geometry", "materials", "forces", "results", "calculation_logs"],
    "geotech": ["soil_layers", "foundation_params"],
    "eval": ["evaluation_type", "scope", "review_results"]
}
```

### 3.2 Validation Logic

```python
def validate_handoff(handoff_json, handoff_type):
    errors = []
    warnings = []
    
    # 1. Schema validation
    if not validate_schema(handoff_json, handoff_type):
        errors.append({
            "code": "E005",
            "message": "Handoff schema invalid",
            "details": get_schema_violations()
        })
        return {"valid": False, "errors": errors, "warnings": warnings}
    
    # 2. Required fields check
    for field in REQUIRED_FIELDS.get("base", []):
        if field not in handoff_json:
            errors.append({
                "code": "E006",
                "message": f"Missing required field: {field}",
                "field": field
            })
    
    # 3. Type-specific validation
    for field in REQUIRED_FIELDS.get(handoff_type, []):
        if field not in handoff_json.get("payload", {}):
            errors.append({
                "code": "E006",
                "message": f"Missing required payload field: {field}",
                "field": field
            })
    
    # 4. Confidence check
    confidence = handoff_json.get("handoff_meta", {}).get("confidence_level")
    if confidence == "LOW":
        warnings.append({
            "code": "W003",
            "message": "Low confidence output - manual verification recommended"
        })
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }
```

---

## 4. ERROR HANDLING

### 4.1 Error Codes

| Code | Meaning | Action |
|------|---------|--------|
| `E005` | Handoff schema invalid | Reject + Request resend |
| `E006` | Missing required field | List missing fields |
| `E007` | Circular dependency detected | Block + Notify User |
| `W003` | Low confidence output | Mark as PENDING_VERIFICATION |
| `W004` | Handoff timeout | Retry with exponential backoff |

### 4.2 Rejection Protocol

```python
# Khi nhận handoff không hợp lệ:
def reject_handoff(handoff_json, error):
    rejection = {
        "status": "REJECTED",
        "handoff_id": handoff_json["handoff_meta"]["handoff_id"],
        "rejection_reason": error,
        "action_required": "Source skill must correct and resubmit",
        "timestamp": get_current_timestamp()
    }
    
    # Log event
    log_event("HANDOFF_REJECTED", rejection)
    
    # Notify source skill
    notify_source_skill(
        handoff_json["handoff_meta"]["source_skill"],
        rejection
    )
    
    return rejection
```

### 4.3 Retry Logic

```python
RETRY_CONFIG = {
    "max_retries": 3,
    "backoff_multiplier": 2,
    "initial_delay_seconds": 1,
    "timeout_seconds": 30
}

def retry_handoff(handoff_json):
    for attempt in range(RETRY_CONFIG["max_retries"]):
        try:
            result = send_handoff_with_timeout(
                handoff_json,
                timeout=RETRY_CONFIG["timeout_seconds"]
            )
            return result
        except TimeoutError:
            delay = RETRY_CONFIG["initial_delay_seconds"] * (
                RETRY_CONFIG["backoff_multiplier"] ** attempt
            )
            log_event("HANDOFF_RETRY", {
                "attempt": attempt + 1,
                "delay": delay
            })
            sleep(delay)
    
    # Max retries exceeded
    raise HandoffTimeoutError(handoff_json)
```

---

## 5. HANDOFF REGISTRY

### 5.1 Registry Structure

```json
{
  "registry_version": "v1.0.0",
  "last_updated": "2026-09-25T10:30:00+07:00",
  "handoffs": [
    {
      "handoff_id": "HND-SDE-DEV-20260925-001",
      "status": "COMPLETED",
      "source": "Structural_Design_Engineer",
      "target": "Design_Evaluation",
      "created_at": "2026-09-25T10:30:00+07:00",
      "completed_at": "2026-09-25T10:35:00+07:00",
      "validation_passed": true
    }
  ],
  "statistics": {
    "total": 150,
    "completed": 145,
    "pending": 3,
    "rejected": 2,
    "avg_processing_time_seconds": 45
  }
}
```

### 5.2 Registry Location

```
.agents/_SHARED/SHARED_CONTEXT/
├── HANDOFF_REGISTRY.json
├── _active/
│   ├── HND-SDE-DEV-20260925-001.json
│   └── ...
└── _archive/
    ├── 2026-09/
    │   ├── HND-SDE-DEV-20260924-001.json
    │   └── ...
    └── ...
```

---

## 6. INTEGRATION POINTS

### 6.1 Với AGENTS.md Dispatcher

```markdown
## §4.3 Handoff Protocol

Khi một skill cần gửi output sang skill khác:
1. Đọc SKILL_BRIDGE.md để lấy schema chính xác
2. Tạo handoff JSON theo schema
3. Validate trước khi gửi
4. Ghi vào HANDOFF_REGISTRY
5. Gửi notification sang skill đích
```

### 6.2 Với Review Gate

```markdown
## §3.1 Review Gate Integration

Trước khi hiển thị Review Gate:
1. Kiểm tra handoff validation
2. Nếu E005/E006 → Báo lỗi, không cho phép export
3. Nếu W003 → Hiển thị cảnh báo confidence thấp
4. Nếu valid → Tiến hành Review Gate bình thường
```

---

## 7. VERSION HISTORY

| Version | Date | Changes |
|---------|------|---------|
| 3.0.0 | 2026-10-17 | Đồng bộ phiên bản v3.0.0 toàn hệ thống; hoàn thiện inter-skill data contracts và validation rules |
| 1.0.0 | 2026-09-25 | Initial release - Base + 4 handoff schemas |
