# SKILL_VERIFY — Module Kiểm chứng Chéo

## Mục đích

**SKILL_VERIFY** là module Quality Assurance tự động — đảm bảo tính nhất quán và chính xác giữa các kết quả tính toán từ nhiều nguồn khác nhau (SKILLKC, Structural_Design_Engineer, ETABS, SAP2000).

## Kích hoạt

### Tự động
- Sau khi Design_Evaluation hoặc Structural_Design_Engineer hoàn thành
- Trước khi xuất báo cáo Word/PDF

### Thủ công
User nói: **"kiểm chứng"**, **"verify"**, **"cross-check"**, **"so sánh kết quả"**

## 5 Loại Kiểm chứng

### 1. Inter-Module Verification
**Script:** `inter_module_verify.py`
**Mục đích:** So sánh kết quả từ 2 module (SKILLKC vs Structural_Design_Engineer)

**Ngưỡng:**
- Nội lực (M, V, N): 5%
- Utilization ratio (η): 3%
- Diện tích cốt thép (As): 10%

**Usage:**
```bash
python inter_module_verify.py \
  --result1 skillkc_output.json \
  --result2 sde_output.json \
  --threshold 5.0 \
  --format text
```

**Output:** Báo cáo so sánh, flag nếu sai lệch > ngưỡng

---

### 2. Standard Version Conflict Detection
**Script:** `standard_conflict_checker.py`
**Mục đích:** Phát hiện khi 2 module dùng 2 phiên bản tiêu chuẩn khác nhau cho cùng 1 cấu kiện

**Usage:**
```bash
python standard_conflict_checker.py \
  --results all_results.json \
  --repo_root . \
  --format text
```

**Input format:** JSON array
```json
[
  {"Element": "Dầm B1", "Standard": "TCVN 5575:2024"},
  {"Element": "Dầm B2", "Standard": "TCVN 5575:2012"}
]
```

**Output:** Báo cáo xung đột, so sánh với STANDARDS_LOCK.md

---

### 3. Calculation Logs Consistency Check
**Script:** `calculation_logs_checker.py`
**Mục đích:** Kiểm tra Calculation_Logs có đầy đủ Formula, Substitution, Result không

**Usage:**
```bash
python calculation_logs_checker.py \
  --logs output_with_logs.json \
  --format text
```

**Checklist:**
- [ ] Mọi bước có Formula
- [ ] Mọi bước có Substitution
- [ ] Mọi bước có Result
- [ ] Result bước N khớp với input bước N+1
- [ ] Citation đầy đủ 6 trường (nếu có)

---

### 4. External Software Comparison
**Script:** `compare_with_etabs.py`
**Mục đích:** So sánh kết quả AI với ETABS/SAP2000

**Usage:**
```bash
python compare_with_etabs.py \
  --etabs etabs_export.xlsx \
  --ai ai_results.json \
  --format text
```

---

### 5. Report Consistency Check
**Script:** `report_consistency_check.py`
**Mục đích:** Parse Word output và so sánh với JSON gốc

**Usage:**
```bash
python report_consistency_check.py \
  --word report.docx \
  --json source_data.json \
  --format text
```

---

## Quy tắc

### Rule 1: Zero-Tolerance cho CRITICAL
Nếu có lỗi `Severity: CRITICAL` → KHÔNG xuất báo cáo

### Rule 2: Variance Threshold
- Nội lực: 5%
- η: 3%
- As: 10%

### Rule 3: Log All Verifications
Mọi lần chạy SKILL_VERIFY ghi log vào:
```
.agents/skills/Design_Evaluation/logs/verifications/VRF-YYYYMMDD-###.json
```

### Rule 4: User Can Override
User có thể bỏ qua WARNING (không phải CRITICAL) nếu có lý do

---

## Integration

```
SKILLKC → SKILL_VERIFY → Review Gate Dashboard → SKILL_REPORT
```

Chi tiết đầy đủ: [SKILL.md](./SKILL.md)
