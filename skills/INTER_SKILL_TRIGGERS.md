---
name: INTER_SKILL_TRIGGERS
version: 1.0.0
last_updated: 2026-09-25
description: "Định nghĩa các trigger tự động kích hoạt skill tiếp theo trong pipeline, điều kiện kích hoạt, và quy trình xử lý lỗi khi trigger thất bại."
---

# INTER_SKILL_TRIGGERS — Tự Động Kích Hoạt Skill Tiếp Theo

> **Phạm vi:** Áp dụng cho **MỌI** automated trigger giữa các skill
> **Nguyên tắc:** Trigger chỉ kích hoạt khi điều kiện được thỏa mãn 100%
> **Cập nhật:** 2026-10-17 — v1.1.0 (Phase B: Code-Enforced via tools/policy_engine.py)
> **Code-enforced:** Toàn bộ 15 triggers trong tài liệu này được thực thi tự động qua `tools/policy_engine.py` (`evaluate_trigger`). Kiểm thử: `tests/test_policy_engine.py`.

---

## 1. TỔNG QUAN TRIGGER SYSTEM

### 1.1 Kiến trúc Trigger

```
┌─────────────────────────────────────────────────────────────┐
│                      TRIGGER ENGINE                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   SKILL A hoàn thành ──► Trigger Check ──► SKILL B kích hoạt │
│                              │                               │
│                              ├── Condition Met? ──► YES ──► Fire
│                              │                               │
│                              └── Condition Met? ──► NO  ──► Skip
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Trigger Types

| Type | Mô tả | Ví dụ |
|------|--------|-------|
| `POST_COMPLETION` | Kích hoạt sau khi skill hoàn thành | SDE → Design_Eval |
| `CONDITIONAL` | Kích hoạt khi điều kiện thỏa mãn | η ≤ 0.70 → Cost_Estimator |
| `MANUAL` | User yêu cầu | User gọi SKILL_VERIFY |
| `ESCALATION` | Kích hoạt khi có lỗi | E004 → SKILL_VERIFY |

---

## 2. POST-COMPLETION TRIGGERS

### 2.1 Design Pipeline Triggers

```yaml
# Trigger ID: POST-SDE-001
trigger_name: "Structural Design → Design Evaluation"
source_skill: "Structural_Design_Engineer"
target_skill: "Design_Evaluation"
condition: "pipeline in ('design-review', 'to_trinh') or require_eval == true"
priority: HIGH

# Pipeline context
pipeline: "Design_Pipeline"
sequence: 1

# Handoff
handoff_type: "structural_design_to_eval"
auto_generate_handoff: true

---
# Trigger ID: POST-DEV-001
trigger_name: "Design Evaluation → SKILL_PHULUC"
source_skill: "Design_Evaluation"
target_skill: "SKILL_PHULUC"
condition: "evaluation_type == 'REVIEW' AND status == 'PASS'"
priority: NORMAL

# Pipeline context
pipeline: "Design_Pipeline"
sequence: 2

# Handoff
handoff_type: "eval_to_phuluc"
auto_generate_handoff: true

---
# Trigger ID: POST-SDE-002
trigger_name: "Structural Design → SKILL_VERIFY"
source_skill: "Structural_Design_Engineer"
target_skill: "SKILL_VERIFY"
condition: "confidence_level < 0.85 OR manual_request == true"
priority: MEDIUM

# Pipeline context
pipeline: "Design_Pipeline"
sequence: 1.5  # Chạy song song với Design_Evaluation

# Handoff
handoff_type: "any_to_verify"
auto_generate_handoff: true
```

### 2.2 Geotech Pipeline Triggers

```yaml
# Trigger ID: POST-GEOTECH-01
trigger_name: "Geotech → Structural Design (Foundation Params)"
source_skill: "SKILL_GEOTECH"
target_skill: "Structural_Design_Engineer"
condition: "foundation_params_ready == true"
priority: HIGH

# Pipeline context
pipeline: "Geotech_Pipeline"
sequence: 10

# Handoff
handoff_type: "geotech_to_structural"
auto_generate_handoff: true

---
# Trigger ID: POST-GEOTECH-02
trigger_name: "Geotech → Design Evaluation (Base Heave Review)"
source_skill: "SKILL_GEOTECH"
target_skill: "Design_Evaluation"
condition: "base_heave_FS < 1.5"
priority: HIGH

# Pipeline context
pipeline: "Geotech_Pipeline"
sequence: 11

# Notification
alert_level: "URGENT"
message: "Base Heave FS thấp - cần review khẩn cấp"

---
# Trigger ID: POST-GEOTECH-03
trigger_name: "Geotech → SKILL_FORENSIC (Adverse Conditions)"
source_skill: "SKILL_GEOTECH"
target_skill: "SKILL_FORENSIC"
condition: "adverse_conditions_detected == true"
priority: CRITICAL

# Pipeline context
pipeline: "Geotech_Pipeline"
sequence: 12

# Notification
alert_level: "CRITICAL"
message: "Phát hiện điều kiện bất lợi - chuyển Forensic Investigation"
```

### 2.3 Review Pipeline Triggers

```yaml
# Trigger ID: POST-EVAL-01
trigger_name: "Design Evaluation → Cost Estimator (VE Opportunity)"
source_skill: "Design_Evaluation"
target_skill: "Cost_Estimator"
condition: "ANY element has eta <= 0.70"
priority: MEDIUM

# Pipeline context
pipeline: "Review_Pipeline"
sequence: 5

# Handoff
handoff_type: "eval_to_cost"
auto_generate_handoff: true

# Data to pass
data_fields:
  - "element_id"
  - "eta_value"
  - "current_design"
  - "suggested_reduction"

---
# Trigger ID: POST-EVAL-02
trigger_name: "Design Evaluation → SKILL_VERIFY (Standard Conflict)"
source_skill: "Design_Evaluation"
target_skill: "SKILL_VERIFY"
condition: "standard_version_mismatch == true"
priority: HIGH

# Pipeline context
pipeline: "Review_Pipeline"
sequence: 3

# Handoff
handoff_type: "any_to_verify"
verification_type: "STANDARD_VERSION"
auto_generate_handoff: true
```

---

## 3. CONDITIONAL TRIGGERS

### 3.1 Utilization Ratio Triggers

```yaml
# Trigger ID: COND-VE-001
trigger_name: "Value Engineering Trigger"
condition_type: "utilization_ratio"
threshold:
  eta_upper: 0.70
  eta_lower: 0.00
action: "Cost_Estimator"

# Detailed condition
detailed_condition: |
  FOR each element IN design_results:
    IF element.eta_M <= 0.70 OR element.eta_V <= 0.70:
      TRIGGER Cost_Estimator WITH {
        "reason": "VE_OPPORTUNITY",
        "element_id": element.id,
        "eta_M": element.eta_M,
        "eta_V": element.eta_V,
        "saving_potential": "HIGH"
      }

# Alert
user_notification: true
notification_message: "Phát hiện {count} phần tử có η ≤ 70% - Có cơ hội Value Engineering"

---
# Trigger ID: COND-WARNING-001
trigger_name: "Warning Boundary Alert"
condition_type: "utilization_ratio"
threshold:
  eta_upper: 1.00
  eta_lower: 0.90
action: "ALERT_USER"

# Detailed condition
detailed_condition: |
  FOR each element IN design_results:
    IF element.eta_M > 0.90 OR element.eta_V > 0.90:
      FLAG element WITH {
        "warning_level": "APPROACHING_LIMIT",
        "message": "Thiết kế sát ngưỡng cho phép"
      }

# Alert
user_notification: true
notification_level: "WARNING"
notification_message: "⚠️ {count} phần tử có η > 90% - Cần lưu ý"

---
# Trigger ID: COND-FAIL-001
trigger_name: "Design Failure Alert"
condition_type: "utilization_ratio"
threshold:
  eta_upper: 999
  eta_lower: 1.00
action: "BLOCK_EXPORT"

# Detailed condition
detailed_condition: |
  FOR each element IN design_results:
    IF element.eta_M > 1.00 OR element.eta_V > 1.00:
      BLOCK design WITH {
        "failure_element": element.id,
        "eta_M": element.eta_M,
        "eta_V": element.eta_V,
        "action_required": "REDESIGN"
      }

# Alert
user_notification: true
notification_level: "CRITICAL"
notification_message: "🔴 {count} phần tử vượt khả năng chịu lực - YÊU CẦU ĐIỀU CHỈNH THIẾT KẾ"
```

### 3.2 Confidence Triggers

```yaml
# Trigger ID: COND-CONF-001
trigger_name: "Low Confidence → SKILL_VERIFY"
condition_type: "confidence_score"
threshold:
  confidence_upper: 0.60
  confidence_lower: 0.00
action: "SKILL_VERIFY"

# Detailed condition
detailed_condition: |
  IF handoff.confidence_level == "LOW":
    TRIGGER SKILL_VERIFY WITH {
      "reason": "LOW_CONFIDENCE",
      "confidence_score": handoff.confidence_score,
      "verification_scope": "FULL"
    }

# Pipeline behavior
pipeline_action: "PAUSE"
pause_until_verified: true

---
# Trigger ID: COND-CONF-002
trigger_name: "Medium Confidence → SKILL_VERIFY (Light)"
condition_type: "confidence_score"
threshold:
  confidence_upper: 0.85
  confidence_lower: 0.60
action: "SKILL_VERIFY"

# Detailed condition
detailed_condition: |
  IF handoff.confidence_level == "MEDIUM":
    TRIGGER SKILL_VERIFY WITH {
      "reason": "MEDIUM_CONFIDENCE",
      "verification_scope": "SPOT_CHECK"
    }

# Pipeline behavior
pipeline_action: "CONTINUE_WITH_WARNING"
```

### 3.3 Error Triggers

```yaml
# Trigger ID: ERR-STANDARD-001
trigger_name: "Standard Version Conflict → SKILL_VERIFY"
condition_type: "error_code"
error_codes:
  - "E004"  # Standard conflict detected
action: "SKILL_VERIFY"

# Detailed condition
detailed_condition: |
  IF error.code == "E004":
    TRIGGER SKILL_VERIFY WITH {
      "reason": "STANDARD_CONFLICT",
      "conflict_type": error.details.conflict_type,
      "modules": error.details.modules,
      "action": "RESOLVE_CONFLICT"
    }

# Pipeline behavior
pipeline_action: "BLOCK_UNTIL_RESOLVED"

---
# Trigger ID: ERR-DATA-001
trigger_name: "Missing Data → SKILL_RFI"
condition_type: "error_code"
error_codes:
  - "E002"  # Missing required data
action: "SKILL_RFI"

# Detailed condition
detailed_condition: |
  IF error.code == "E002":
    TRIGGER SKILL_RFI WITH {
      "document_type": "RFI",
      "reason": "DATA_MISSING",
      "missing_fields": error.details.missing_fields,
      "urgency": "HIGH"
    }

# Pipeline behavior
pipeline_action: "AWAIT_DATA"
```

---

## 4. MANUAL TRIGGERS (User-Initiated)

### 4.1 User-Requested Triggers

```yaml
# Trigger ID: MANUAL-VERIFY-001
trigger_name: "User Requested Verification"
user_keywords:
  - "kiểm chứng"
  - "verify"
  - "cross-check"
  - "so sánh kết quả"
target_skill: "SKILL_VERIFY"

# Pipeline context
pipeline: "Manual"
requires_context: true

---
# Trigger ID: MANUAL-VE-001
trigger_name: "User Requested Value Engineering"
user_keywords:
  - "tối ưu chi phí"
  - "giảm vật liệu"
  - "value engineering"
  - "so sánh phương án"
target_skill: "Cost_Estimator"

# Pipeline context
pipeline: "Manual"
requires_context: false
```

---

## 5. PIPELINE DEFINITIONS

### 5.1 Design Pipeline

```yaml
pipeline_name: "Design_Pipeline"
description: "Pipeline cho thiết kế kết cấu độc lập"

stages:
  - stage: 1
    skill: "Structural_Design_Engineer"
    triggers_after:
      - "POST-SDE-001"  # → Design_Evaluation
      - "POST-SDE-002"  # → SKILL_VERIFY (if confidence < 0.85)

  - stage: 1.5
    skill: "SKILL_VERIFY"
    depends_on: [1]
    condition: "confidence < 0.85"
    triggers_after: []

  - stage: 2
    skill: "Design_Evaluation"
    depends_on: [1]
    triggers_after:
      - "POST-EVAL-01"  # → Cost_Estimator (if η ≤ 0.70)
      - "POST-EVAL-02"  # → SKILL_VERIFY (if standard conflict)

  - stage: 3
    skill: "Cost_Estimator"
    depends_on: [2]
    condition: "VE opportunity exists"
    triggers_after: []

  - stage: 4
    skill: "SKILL_PHULUC"
    depends_on: [2]
    condition: "evaluation_type == 'REVIEW'"
    triggers_after: []

  - stage: 5
    skill: "Technical_Illustrator"
    depends_on: [1]
    condition: "requires_drawing == true"
    triggers_after: []

# Gate
review_gate_after: 2
export_allowed_after: "USER_APPROVAL"
```

### 5.2 Geotech Pipeline

```yaml
pipeline_name: "Geotech_Pipeline"
description: "Pipeline cho phân tích địa kỹ thuật"

stages:
  - stage: 1
    skill: "SKILL_GEOTECH"
    triggers_after:
      - "POST-GEOTECH-01"  # → Structural_Design_Engineer
      - "POST-GEOTECH-02"  # → Design_Evaluation (if base heave < 1.5)
      - "POST-GEOTECH-03"  # → SKILL_FORENSIC (if adverse conditions)

  - stage: 10
    skill: "Structural_Design_Engineer"
    depends_on: [1]
    condition: "foundation_params_ready"
    triggers_after: []

  - stage: 11
    skill: "Design_Evaluation"
    depends_on: [1]
    condition: "base_heave_FS < 1.5"
    triggers_after: []

  - stage: 12
    skill: "SKILL_FORENSIC"
    depends_on: [1]
    condition: "adverse_conditions_detected"
    triggers_after: []
```

### 5.3 Review Pipeline

```yaml
pipeline_name: "Review_Pipeline"
description: "Pipeline cho review/QA/QC"

stages:
  - stage: 1
    skill: "Design_Evaluation"
    triggers_after:
      - "POST-EVAL-01"  # → Cost_Estimator
      - "POST-EVAL-02"  # → SKILL_VERIFY
      - "POST-DEV-001"  # → SKILL_PHULUC

  - stage: 3
    skill: "SKILL_VERIFY"
    depends_on: [1]
    condition: "standard_conflict"
    triggers_after: []

  - stage: 5
    skill: "Cost_Estimator"
    depends_on: [1]
    condition: "VE_opportunity"
    triggers_after: []
```

---

## 6. TRIGGER PROCESSING LOGIC

### 6.1 Trigger Engine

```python
class TriggerEngine:
    def __init__(self):
        self.triggers = self.load_triggers()
        self.pipeline_state = {}
    
    def evaluate_trigger(self, trigger_id, context):
        """Đánh giá trigger có nên fire không"""
        trigger = self.get_trigger(trigger_id)
        
        if trigger.condition_type == "always":
            return True
        
        elif trigger.condition_type == "utilization_ratio":
            return self.check_eta_condition(trigger, context)
        
        elif trigger.condition_type == "confidence_score":
            return self.check_confidence_condition(trigger, context)
        
        elif trigger.condition_type == "error_code":
            return self.check_error_condition(trigger, context)
        
        return False
    
    def check_eta_condition(self, trigger, context):
        """Kiểm tra điều kiện η"""
        threshold = trigger.threshold
        
        for element in context.get("design_results", []):
            eta = element.get("eta_M") or element.get("eta_V")
            if eta and threshold.eta_lower <= eta <= threshold.eta_upper:
                return True
        return False
    
    def check_confidence_condition(self, trigger, context):
        """Kiểm tra điều kiện confidence"""
        confidence = context.get("confidence_score", 1.0)
        threshold = trigger.threshold
        return threshold.confidence_lower <= confidence < threshold.confidence_upper
    
    def check_error_condition(self, trigger, context):
        """Kiểm tra điều kiện error code"""
        error = context.get("error", {})
        return error.get("code") in trigger.error_codes
```

### 6.2 Pipeline Orchestrator

```python
class PipelineOrchestrator:
    def __init__(self):
        self.pipelines = self.load_pipelines()
        self.current_stage = 0
    
    def execute_pipeline(self, pipeline_name, context):
        """Thực thi pipeline"""
        pipeline = self.pipelines[pipeline_name]
        
        for stage in pipeline.stages:
            # Check dependencies
            if not self.check_dependencies(stage, context):
                continue
            
            # Execute stage
            result = self.execute_skill(stage.skill, context)
            
            # Evaluate post-completion triggers
            for trigger_id in stage.triggers_after:
                if self.trigger_engine.evaluate_trigger(trigger_id, context):
                    self.fire_trigger(trigger_id, context)
            
            # Check pipeline actions
            if pipeline.pipeline_action == "PAUSE":
                if not self.verify_trigger_result(trigger_id):
                    return {"status": "PAUSED", "reason": trigger_id}
            
            elif pipeline.pipeline_action == "BLOCK_UNTIL_RESOLVED":
                if not self.is_issue_resolved(context):
                    return {"status": "BLOCKED", "reason": "UNRESOLVED_ISSUE"}
        
        return {"status": "COMPLETED"}
    
    def fire_trigger(self, trigger_id, context):
        """Kích hoạt trigger - gọi skill tiếp theo"""
        trigger = self.get_trigger(trigger_id)
        
        # Log trigger event
        self.log_event("TRIGGER_FIRED", {
            "trigger_id": trigger_id,
            "target_skill": trigger.target_skill,
            "timestamp": get_current_timestamp()
        })
        
        # Generate handoff if needed
        if trigger.auto_generate_handoff:
            handoff = self.generate_handoff(trigger, context)
            self.validate_and_send_handoff(handoff)
        
        # Send notification if needed
        if trigger.user_notification:
            self.send_notification(trigger, context)
```

---

## 7. ERROR HANDLING

### 7.1 Trigger Failure Handling

```yaml
failure_handling:
  timeout:
    max_wait_seconds: 300
    action: "RETRY_3_TIMES"
    fallback: "NOTIFY_USER"
  
  skill_not_found:
    action: "LOG_ERROR"
    fallback: "SKIP_TRIGGER"
  
  handoff_validation_failed:
    action: "REJECT_AND_REQUEST_RESEND"
    notify_source: true
```

### 7.2 Retry Logic

```python
RETRY_CONFIG = {
    "max_retries": 3,
    "backoff_seconds": [1, 5, 15],
    "retry_on": ["TIMEOUT", "CONNECTION_ERROR"]
}

def execute_trigger_with_retry(trigger):
    for attempt in range(RETRY_CONFIG["max_retries"]):
        try:
            return execute_trigger(trigger)
        except RetryableError as e:
            if attempt < RETRY_CONFIG["max_retries"] - 1:
                wait_time = RETRY_CONFIG["backoff_seconds"][attempt]
                sleep(wait_time)
                continue
            else:
                log_error("TRIGGER_FAILED_AFTER_RETRIES", trigger)
                notify_user(f"Trigger {trigger.id} failed after {attempt+1} attempts")
                return {"status": "FAILED"}
```

---

## 8. LOGGING & AUDIT

### 8.1 Trigger Event Log

```json
{
  "event_log": [
    {
      "event_id": "EVT-20260925-001",
      "event_type": "TRIGGER_FIRED",
      "trigger_id": "POST-SDE-001",
      "source_skill": "Structural_Design_Engineer",
      "target_skill": "Design_Evaluation",
      "timestamp": "2026-09-25T10:30:00+07:00",
      "context_summary": {
        "elements_processed": 5,
        "confidence_level": "HIGH"
      },
      "result": "Handoff sent successfully"
    },
    {
      "event_id": "EVT-20260925-002",
      "event_type": "TRIGGER_CONDITION_MET",
      "trigger_id": "COND-VE-001",
      "condition_details": {
        "eta_threshold": 0.70,
        "matching_elements": ["B1", "C2"]
      },
      "timestamp": "2026-09-25T10:35:00+07:00"
    }
  ]
}
```

### 8.2 Log Location

```
.agents/_SHARED/SHARED_CONTEXT/
├── logs/
│   ├── triggers/
│   │   ├── YYYY-MM/
│   │   │   ├── trigger_events.json
│   │   │   └── trigger_failures.json
│   │   └── ...
│   └── pipelines/
│       └── ...
└── HANDOFF_REGISTRY.json
```

---

## 9. VERSION HISTORY

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-09-25 | Initial release - Full trigger definitions |
