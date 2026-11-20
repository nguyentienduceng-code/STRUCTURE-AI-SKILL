# RUNBOOK P0-OPS — Vận hành Workspace Hybrid Authoring, Versioning & Lineage Mỏng

> **Cơ sở kiến trúc:** [DECISION_OPS_HYBRID_AUTHORING_20261116.md](../memory/DECISION_OPS_HYBRID_AUTHORING_20261116.md)  
> **Công cụ điều phối:** [project_ops_manager.py](../tools/project_ops_manager.py)  
> **Schema SSOT:** [model_schema.json](../_SHARED/data/model_schema.json), [ncr_schema.json](../_SHARED/data/ncr_schema.json)

---

## 1. Cấu trúc Workspace Chuẩn (`01_Projects/<DuAn>/`)

```text
01_Projects/<DuAn>/
├── model/
│   ├── model.json                  # Model JSON SSOT hiện hành (gắn model_version)
│   └── revisions/
│       ├── model_v001.json         # Bản chụp bất biến mỗi lần tăng version
│       └── model_v002.json
├── forms/                          # Form DXF + .manifest.json ưu tiên tầng dự án
├── blocks/
│   └── block_catalog_lock.json     # Khóa phiên bản block_catalog + hash Form DXF
├── outputs/
│   ├── KC-02.dxf + KC-02.dce_audit.json
│   └── dossier_manifest.json       # Tổng hợp tình trạng phát hành hồ sơ
├── audit/
│   ├── lineage.jsonl               # Append-only: 1 dòng / 1 tờ phát hành
│   └── compliance_report.json      # Báo cáo kiểm định Bộ lọc 8
└── ncr/ (đồng bộ nrc/)
    ├── NCR-001.json                # Phiếu NCR số thứ tự & truy vết thay đổi model
    └── NCR-001.md                  # Biên bản đọc nhanh cho kỹ sư (tự sinh song song)
```

---

## 2. Bộ 4 Lệnh Runbook Chính + Build Dossier

### Lệnh 1: Tạo dự án chuẩn (`init-project`)
```bash
python ".agents/tools/project_ops_manager.py" init-project \
  --project "<DuAn>" \
  --seed-model "<duong_dan_model_seed.json>"
```
- Tạo đủ 6 phân khu (`model/`, `forms/`, `blocks/`, `outputs/`, `audit/`, `ncr/` + mirror `nrc/`).
- Kiểm tra `model.json` qua `model_schema.json` (`model_id`, `model_version=1`, `standards_ref` khóa từ `STANDARDS_LOCK.md v3.3.0`).

### Lệnh 2: Nạp Form tùy biến vào dự án (`add-form`)
```bash
python ".agents/tools/project_ops_manager.py" add-form \
  --project-dir "01_Projects/<DuAn>" \
  --form-id FORM_02_MULTIVIEW_A3_BTCT
```
- Sao chép Form từ `00_Template_&_Standards/CAD_Forms/` (fallback `.agents/_SHARED/data/CAD_Forms/`) vào `forms/`, làm mới manifest và kiểm tra contract (`validate_open_form`).

### Lệnh 3: Đổi thuộc tính Layer theo SSOT (`set-layer`)
```bash
python ".agents/tools/project_ops_manager.py" set-layer \
  --project-dir "01_Projects/<DuAn>" \
  --form-id FORM_02_MULTIVIEW_A3_BTCT \
  --layer DCE_Cot --color 3 --lineweight 35
```
- Chỉ cho phép các Layer thuộc danh sách chuẩn SSOT (`cad_layer_standard.get_standard_layer_whitelist()`). Từ chối layer tùy tiện (`IllegalLayerOverrideError`).

### Lệnh 4: Xử lý NCR & Tái sinh Theo Tờ Ảnh Hưởng (`apply-ncr`)
```bash
python ".agents/tools/project_ops_manager.py" apply-ncr \
  --project-dir "01_Projects/<DuAn>" \
  --element-id C0A --field b_mm --new-value 300 \
  --reason "NCR-001: Tang tiet dien cot C5 tu 200 len 300" \
  --source "FIELD_NCR" --severity MAJOR
```
- Gắn mã tuần tự `NCR-001`, cập nhật trường kỹ thuật trên bản sao model, **kiểm tra qua schema-gate trước khi ghi đè** (`model_version` tăng +1, lưu snapshot `model/revisions/model_v00N.json`), chỉ xuất lại những tờ (`affected_sheets`) có chứa `element_id` và nối dòng mới vào `audit/lineage.jsonl`.

### Phát hành hồ sơ (`build-dossier`)
```bash
python ".agents/tools/project_ops_manager.py" build-dossier \
  --project-dir "01_Projects/<DuAn>" \
  --form-id FORM_02_MULTIVIEW_A3_BTCT \
  --layout-mode model \
  --compliance physical
```
- Hỗ trợ 2 chế độ `--layout-mode`:
  - `model` (mặc định legacy tương thích 100%): xuất từng tờ DXF (`outputs/KC-02.dxf`, ...) theo Form mở (`FORM_01`..`FORM_04`).
  - `paperspace` (P3 D2 — 1 file = 1 dossier): xuất duy nhất `outputs/<ModelId>_MASTER_SET.dxf` chứa ModelSpace chung 1:1 mm (`Dce_KhTenTruc` dùng chung) + nhiều PaperSpace Layout (`KC.02`, `KC.03`, ...) kèm `VIEWPORT` không chồng lấn & `DCE_TITLEBLOCK_*_PAPER` (`ATTDEF` thật).
- Mặc định `--compliance physical` kiểm định hình học/DXF vật lý và gắn nhãn trung thực **`DXF_INTEGRITY_PASS`** (KHÔNG gọi là "PASS Bộ lọc 8" 20 cổng).
- Khi truyền `--compliance plan|full`, chạy `audit_dxf_compliance` và giữ trung thực `NEEDS_REVIEW` nếu còn cổng `UNVERIFIED` (chỉ đạt `FILTER8_*_PASS` khi đủ semantic claims).
- Ghi `dossier_manifest.json` và nối dòng `lineage.jsonl`:
  `model_id × model_version × form_version × sheet_no × form_id × form_sha256 × block_catalog_version × standards_ref × dxf_sha256 × audit_status × element_ids`.
