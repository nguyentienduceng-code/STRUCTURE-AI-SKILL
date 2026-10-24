# SHARED_CONTEXT — Agentic Workflow Data Exchange

> **Mục đích:** Lưu trữ các JSON handoff giữa các skills trong agentic workflow.
> **Sử dụng bởi:** Tất cả skills — qua SKILL_BRIDGE.md protocol.

---

## Cấu trúc Thư mục

```
_SHARED/
└── SHARED_CONTEXT/
    ├── _active/              ← Handoff đang xử lý
    │   └── RECEIPTS/        ← Receipt confirmations
    ├── _archive/            ← Handoff đã xử lý xong
    └── _rejected/           ← Handoff bị từ chối (thiếu field)
```

---

## File Naming Convention

```
{handoff_type}_{project_id}_{timestamp}.json
```

**Ví dụ:**
- `geotech_to_structural_PROJ001_20260925_143000.json`
- `structural_to_verify_PROJ001_20260925_144500.json`
- `geotech_to_structural_PROJ001_20260925_143000_receipt.json`

---

## Handoff Types

| Type | From | To | Schema |
|------|------|----|--------|
| `geotech_to_structural` | SKILL_GEOTECH | Structural_Design_Engineer | Foundation params |
| `structural_to_verify` | Structural_Design_Engineer | SKILL_VERIFY | QA check request |
| `structural_to_cost` | Structural_Design_Engineer | Cost_Estimator | Design output for VE |
| `design_eval_to_cost` | Design_Evaluation | Cost_Estimator | VE analysis request |
| `geotech_to_design_eval` | SKILL_GEOTECH | Design_Evaluation | Foundation review |

---

## Lifecycle

1. **ACTIVE:** Skill tạo handoff → ghi vào `_active/`
2. **PROCESSING:** Consumer đọc và validate
3. **RECEIPT:** Consumer ghi receipt vào `_active/RECEIPTS/`
4. **ARCHIVED:** Hoàn thành → di chuyển vào `_archive/`
5. **REJECTED:** Nếu invalid → ghi vào `_rejected/`

---

## Ví dụ Workflow

```
1. SKILL_GEOTECH hoàn thành soil params
       ↓
2. Tạo: geotech_to_structural_PROJ001_20260925_143000.json
       ↓
3. Ghi vào _active/
       ↓
4. Structural_Design_Engineer đọc
       ↓
5. Validate schema
       ↓
6. Nếu OK → ghi receipt: *_receipt.json
       ↓
7. Di chuyển vào _archive/
```

---

## Auto-Cleanup

- Files trong `_active/` quá 24h → cảnh báo
- Files trong `_rejected/` → giữ lại để debug
- Files trong `_archive/` → có thể xóa sau 90 ngày

---

## Chi tiết Schema

Xem `SKILL_BRIDGE.md` §3 cho định nghĩa JSON schema đầy đủ.
