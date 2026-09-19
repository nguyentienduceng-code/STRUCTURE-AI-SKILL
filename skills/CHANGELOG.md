# CHANGELOG â€” ToÃ n bá»™ Bá»™ Skills Ká»¹ nÄƒng Káº¿t cáº¥u

> **Pháº¡m vi:** Ghi nháº­n thay Ä‘ï¿½i cá»§a **Má»ŒI skill** trong `.agents/skills/`.
> **Cáº­p nháº­t lá»›n nháº¥t:** 2026-09-01

---

## 2026-09-20 - SKILL_GEOTECH v2.2.0 - **Hoan thien Thuyet minh Giai trinh**

### Tong quan

Hoan thien bo thuyet minh giai trinh ky thuat cho SKILL_GEOTECH.

### Files moi

| File | Mo ta |
|------|--------|
| `references/GEOTECH_GUIDE.md` | Cong thuc goc, bang tuong quan, nguon tham khao |
| `references/PLAXIS_MODEL_GUIDE.md` | Huong dan nhap lieu Plaxis chi tiet |
| `references/THUYET_MINH_TEMPLATE.md` | Template Thuyet minh BPTC chuan (8 muc) |

### Thay doi chinh

- Viet lai `export_geotech_report.py` voi 8 sheets Excel day du:
  - Sheet 1: Ket qua KSDC
  - Sheet 2: Thong so Dat Plaxis
  - Sheet 3: Ung suat Huu hieu
  - Sheet 4: Thong so Ket cau
  - Sheet 5: Kiem chung SLS
  - Sheet 6: Kha nang Chi luc
  - Sheet 7: Huong dan JSON
  - Sheet 8: Nhat ky Tinh toan

### Versions

| File | Truoc | Sau |
|------|--------|-----|
| SKILL_GEOTECH | v2.0.0 | **v2.2.0** |

---

## 2026-09-16 - SKILL_GEOTECH v2.0.0 - **Tich hop CPTu, SSC, SLS, Pile Load Test**

### Tong quan

Mo rong SKILL_GEOTECH voi cac tinh nang nang cao.

### Tinh nang moi

| Tinh nang | Mo ta |
|-----------|--------|
| **CPTu Support** | Ap luc lo rong, Nkt dong dua tren Bq/Ip, OCR tu CPTu |
| **Soft Soil Creep (SSC)** | Thong so lambda*, kappa*, mu* tu Oedometer |
| **Eurocode 7 & CIRIA C760** | Tich hop de chon Rinter, SBT 2016 |
| **Stiffness Degradation** | Suy giam do cung cho tuong vay (cracked section) |
| **SLS Check** | Kiem chung chuyen vi ngang (Clough & O'Rourke) |
| **Pile Load Test** | Dien dich thi nghiem nen tinh coc (Davisson, Chin-Kondner) |

### Scripts moi

| Script | Chuc nang |
|--------|-----------|
| `calc_soil_params_ssc.py` | Soft Soil Creep parameters |
| `calc_pile_load_test.py` | Davisson, Chin-Kondner |
| `calc_psr.py` | Plane Strain Ratio |
| `verify_serviceability_limits.py` | SLS check |

### Versions

| File | Truoc | Sau |
|------|--------|-----|
| SKILL_GEOTECH | v1.0.0 | **v2.0.0** |

---
## 2026-09-01 â€” PHULUC Upgrade (v4.2) â€” **Phá»¥ lá»¥c TÃ­nh toÃ¡n ChuyÃªn nghiá»‡p**

### Tá»•ng quan

Táº¡o há»‡ thá»‘ng **Phá»¥ lá»¥c TÃ­nh toÃ¡n** Ä‘áº§y Ä‘á»§ theo chuáº©n Ä‘Æ¡n vá»‹ tÆ° váº¥n thiáº¿t káº¿ Ä‘á»™c láº­p.

### Option A â€” NÃ¢ng cáº¥p SKILL_CALC_REPORT

| File | MÃ´ táº£ |
|------|--------|
| `templates/appendix/APPENDIX_BEAM_RC.md` | Template dáº§m BTCT |
| `templates/appendix/APPENDIX_COLUMN_RC.md` | Template cá»™t BTCT |
| `templates/appendix/APPENDIX_STEEL_BEAM.md` | Template dáº§m thÃ©p |
| `templates/appendix/appendix_generator.py` | Generator script |

### Option B â€” SKILL_PHULUC Má»›i

| File | MÃ´ táº£ |
|------|--------|
| `SKILL_PHULUC/SKILL.md` | Skill entry point |
| `SKILL_PHULUC/references/MATERIAL_TABLES.md` | Báº£ng tra váº­t liá»‡u |
| `SKILL_PHULUC/templates/` | Templates (shared vá»›i Option A) |

### Cáº¥u trÃºc Phá»¥ lá»¥c (Step-by-Step)

```
1. THÃ”NG TIN CHUNG
2. Váº¬T LIá»†U (Ä‘áº§y Ä‘á»§ báº£ng tra)
3. Táº¢I TRá»ŒNG (tÄ©nh táº£i, hoáº¡t táº£i, tá»• há»£p)
4. SÆ  Äá»’ Káº¾T Cáº¤U (hÃ¬nh váº½)
5. Ná»˜I Lá»°C (báº£ng chi tiáº¿t)
6. TÃNH TOÃN CHI TIáº¾T
   â”œâ”€â”€ BÆ°á»›c 1: ...
   â”œâ”€â”€ BÆ°á»›c 2: ...
   â””â”€â”€ Kiá»ƒm tra: Î· = ...
7. Báº¢NG Tá»”NG Há»¢P
8. Káº¾T LUáº¬N
9. PHá»¤ Lá»¤C (báº£ng tra, há»‡ sá»‘)
10. CHá»® KÃ XÃC NHáº¬N
```

### Versions má»›i

| File | Version |
|------|---------|
| SKILL_PHULUC | v1.0.0 |
| Structural_Design_Engineer | v1.4.0 |

---

## 2026-08-31 â€” Reporting Upgrade (v4.1) â€” **NÃ¢ng cáº¥p TrÃ¬nh bÃ y BÃ¡o cÃ¡o**

### Tá»•ng quan

NÃ¢ng cáº¥p toÃ n diá»‡n kháº£ nÄƒng **trÃ¬nh bÃ y vÃ  thá»ƒ hiá»‡n bÃ¡o cÃ¡o chuyÃªn nghiá»‡p** cho cáº£ 3 skill (Design_Evaluation, SKILL_RFI, Technical_Illustrator). Thá»‘ng nháº¥t qua **Unified Dispatcher** vá»›i 5 audience profiles.

### Phase A â€” Foundation Library (`_lib/`)

| File | Chá»©c nÄƒng |
|------|-----------|
| `_lib/__init__.py` | Version stamp v1.0.0 |
| `_lib/_docx_helpers.py` | DOCX helpers: cover page (NÄ 30/2020), TOC field, header/footer + PAGE/NUMPAGES, styled tables (zebra, borders), callouts (info/warn/critical/success), headings |
| `_lib/_report_utils.py` | Formatters: `format_eta()` (Î· + emoji), `format_citation()` (4-tuple), `format_currency()`, `safe_filename()` (Vietnamese), `safe_print()` |
| `_lib/_chart_inserter.py` | Charts (matplotlib Agg): radar, grouped bar, progress, eta heatmap, cost breakdown; auto-insert DOCX/MD |
| `_lib/_executive_dashboard.py` | Dashboard cho Owner: KPI table, status banner, top 3 risks, CTA â€” MD/HTML/DOCX |
| `_lib/_audience_profiles.py` | 5 profiles: **designer** / **engineer** / **contractor** / **owner** / **authority** â€” section selection, tone, detail level |

### Phase C â€” Unified Dispatcher (Report v4.0)

| File | Chá»©c nÄƒng |
|------|-----------|
| `Design_Evaluation/scripts/report_dispatcher.py` | â­ Unified CLI: 1 handoff JSON â†’ nhiá»u format MD/DOCX/HTML, vá»›i audience-aware sections, charts tá»± Ä‘á»™ng |

**Usage:**
```bash
python report_dispatcher.py --handoff audit.json --audience designer --formats md,docx
python report_dispatcher.py --handoff audit.json --audience owner --formats docx --include-charts
python report_dispatcher.py --list-audiences
```

### Phase D â€” SKILL_RFI Document Renderer

| File | Chá»©c nÄƒng |
|------|-----------|
| `SKILL_RFI/scripts/document_renderer.py` | Render RFI/NCR/SUBMITTAL/CO/TQ/PBRFI ra DOCX (vá»›i severity colors, 5W1H NCR) hoáº·c MD |

### Phase E â€” Excel Generator

| File | Chá»©c nÄƒng |
|------|-----------|
| `Design_Evaluation/scripts/xlsx_report.py` | Excel: BOQ (Bill of Quantities), Calc Sheet (Î· + Rating mÃ u), Comparison Matrix (cÃ³ chart), Submittal Log (cho SKILL_RFI) |

### Phase F â€” Documentation

| File | Chá»©c nÄƒng |
|------|-----------|
| `Design_Evaluation/references/REPORT_FORMATS.md` | â­ Catalogue 4 luá»“ng reporting + decision flow |

### Backward Compatibility

âœ… **Giá»¯ nguyÃªn 100%** 4 generator cÅ© (`generate_report.py`, `generate_to_trinh.js`, `md_to_docx_report.js`, `md_to_pdf_report.js`) â€” khÃ´ng breaking change.

### Audience Profile Matrix

| Audience | Sections Ä‘áº§y Ä‘á»§ | Tone | Executive Dashboard |
|----------|----------------|------|---------------------|
| `designer` | âœ… Cover + TOC + Dashboard + Logs + Citations + Charts | Formal technical | CÃ³ |
| `engineer` | Cover + TOC + Logs + Charts | Technical precise | KhÃ´ng |
| `contractor` | Cover + TOC + Project Info + Charts + Approval | Practical | CÃ³ (compact) |
| `owner` | Cover + Dashboard + Comparison + Charts | Business friendly | CÃ³ (Ä‘áº§y Ä‘á»§) |
| `authority` | Cover + TOC + All sections + Full audit | Official formal | CÃ³ |

### Output Quality Standards (má»›i Ã¡p dá»¥ng)

- [x] Cover page (logo, project, version, date) cho `.docx`
- [x] Header/Footer + Page X/Y
- [x] Executive Dashboard (Owner/Contractor)
- [x] Calculation logs vá»›i Î· + Rating mÃ u (Designer/Engineer)
- [x] Citations format 4-tuple (Designer/Authority)
- [x] Charts auto-generated 300 DPI
- [x] Approval Matrix 3-column
- [x] Disclaimer á»Ÿ cuá»‘i

### Audit

- 13 files má»›i táº¡o/sá»­a
- 0 breaking changes
- Tested: report_dispatcher (designer 44 Ä‘oáº¡n vs owner 35 Ä‘oáº¡n), xlsx 3 types, document_renderer 5 doc types

---

## 2026-08-31 â€” Final Audit & Validator Fix (v4.0)

### Tá»•ng quan

Audit cuá»‘i cÃ¹ng vÃ  sá»­a 3 váº¥n Ä‘á» quan trá»ng phÃ¡t hiá»‡n Ä‘Æ°á»£c.

### Váº¥n Ä‘á» Ä‘Ã£ sá»­a

| Issue | MÃ´ táº£ | Fix |
|-------|-------|-----|
| **VALIDATOR-BROKEN** | `validate_registry.py` khÃ´ng bao giá» cháº¡y Ä‘Æ°á»£c â€” dÃ¹ng field `file_path` khÃ´ng tá»“n táº¡i trong registry.json | Rewrite Ä‘á»ƒ dÃ¹ng `name` field + auto-detect path cho cáº¥u trÃºc _CORE_SKILLS má»›i |
| **DASHBOARD-FORMAT-MISMATCH** | `rfi_dashboard.py` chá»‰ Ä‘á»c field `rfis` cÅ©, khÃ´ng hiá»ƒu thá»‹ cÃ¡c loáº¡i document khÃ¡c | Rewrite Ä‘á»ƒ iterate qua `documents.{type}` dict |
| **REGISTRY-MISSING-DCE** | 5 DCE scripts trong `dce_writer/` khÃ´ng cÃ³ trong registry.json | ThÃªm DCE scripts vÃ o registry vá»›i `status: ACTIVE` |

### TÃ­nh nÄƒng má»›i

| TÃ­nh nÄƒng | MÃ´ táº£ |
|-----------|--------|
| `validate_registry.py` v2.0 | Auto-detect path, há»— trá»£ `_deprecated/` scripts, UTF-8 output |
| Validator skip `internal: true` | KhÃ´ng cáº£nh bÃ¡o orphan cho __init__.py |

### Files Ä‘Ã£ sá»­a

| File | Thay Ä‘á»•i |
|------|----------|
| `_CORE_SKILLS/Design_Evaluation/scripts/validate_registry.py` | v1.0 â†’ v2.0 â€” rewrite hoÃ n toÃ n |
| `_SUPPORT_SKILLS/SKILL_RFI/scripts/rfi_dashboard.py` | Rewrite Ä‘á»ƒ Ä‘á»c multi-document registry |
| `_CORE_SKILLS/Technical_Illustrator/scripts/registry.json` | v2.1.0 â€” thÃªm 5 DCE scripts |

### Audit káº¿t quáº£

âœ… **PASSED** â€” 0 issues, 0 warnings
- 89 Python scripts
- 7 SKILL.md files (Ä‘á»“ng bá»™ version)
- 77 .md references
- 5 _deprecated/ scripts (Ä‘Ã£ archive Ä‘Ãºng chá»—)
- 6 loáº¡i documents trong registry (RFI/NCR/Submittal/CO/TQ/PBRFI)

---

## 2026-08-30 â€” SKILL_RFI Extended (v3.9)

### Tá»•ng quan

Má»Ÿ rá»™ng SKILL_RFI tá»« RFI-only sang há»‡ thá»‘ng quáº£n lÃ½ giao dá»‹ch ká»¹ thuáº­t toÃ n diá»‡n.

### CÃ¡c loáº¡i tÃ i liá»‡u Ä‘Æ°á»£c há»— trá»£

| Loáº¡i | MÃ£ | MÃ´ táº£ | Gá»­i cho |
|------|------|--------|---------|
| **RFI** | Request for Information | YÃªu cáº§u lÃ m rÃµ thÃ´ng tin | Designer/CSHT |
| **NCR** | Non-Conformance Report | BÃ¡o cÃ¡o khÃ´ng phÃ¹ há»£p | Contractor |
| **Submittal** | Shop Drawing/Material | Báº£n váº½ thi cÃ´ng | Designer/CSHT |
| **Change Order** | CO | YÃªu cáº§u thay Ä‘á»•i KL | Owner |
| **Tech Query** | TQ | CÃ¢u há»i ká»¹ thuáº­t chuyÃªn sÃ¢u | Designer |
| **Pre-Bid RFI** | PB-RFI | LÃ m rÃµ trÆ°á»›c Ä‘áº¥u tháº§u | Owner/Designer |

### Ma tráº­n cÃ¡c bÃªn

| BÃªn | Vai trÃ² | Nháº­n tá»« | Gá»­i Ä‘áº¿n |
|------|---------|----------|----------|
| Owner | Chá»§ Ä‘áº§u tÆ° | CO, Final Submittal | Approval |
| Designer | ÄÆ¡n vá»‹ TK | RFI, Shop Drawing | RFI Response |
| CSHT | TÆ° váº¥n GS | RFI, NCR | Approval |
| Contractor | NhÃ  tháº§u | RFI, NCR | Shop Drawing, CO |

### Files má»›i

| File | MÃ´ táº£ |
|------|--------|
| `SKILL_RFI/data/party_contacts.json` | Template danh báº¡ cÃ¡c bÃªn |
| `SKILL_RFI/scripts/document_generator.py` | Táº¡o táº¥t cáº£ loáº¡i tÃ i liá»‡u |
| `SKILL_RFI/scripts/document_tracker.py` | Theo dÃµi táº¥t cáº£ loáº¡i tÃ i liá»‡u |
| `SKILL_RFI/references/Party_Matrix.md` | Ma tráº­n trÃ¡ch nhiá»‡m cÃ¡c bÃªn |

### Priority Levels má»›i

| Má»©c | KÃ½ hiá»‡u | Trigger | Deadline |
|------|----------|---------|----------|
| ðŸ”´ CRITICAL | An toÃ n/Káº¿t cáº¥u | "sáº­p", "ná»©t", "nguy hiá»ƒm" | 24h |
| ðŸŸ  URGENT | áº¢nh hÆ°á»Ÿng tiáº¿n Ä‘á»™ | "cháº­m", "phÃ¡t sinh" | 3 ngÃ y |
| ðŸŸ¡ HIGH | Ká»¹ thuáº­t quan trá»ng | "thiáº¿u thÃ´ng tin" | 7 ngÃ y |
| ðŸŸ¢ NORMAL | Ká»¹ thuáº­t thÃ´ng thÆ°á»ng | "xÃ¡c nháº­n", "lÃ m rÃµ" | 14 ngÃ y |
| ðŸ”µ ROUTINE | HÃ nh chÃ­nh | "cáº­p nháº­t", "bá»• sung" | 21 ngÃ y |

---

## 2026-08-30 â€” SKILL_RFI New Skill (v3.8)

### Tá»•ng quan

PhÃ¡t triá»ƒn SKILL_RFI hoÃ n chá»‰nh â€” module quáº£n lÃ½ Request for Information (RFI) vá»›i vÃ²ng Ä‘á»i Ä‘áº§y Ä‘á»§.

### SKILL_RFI Features

| Feature | MÃ´ táº£ |
|---------|--------|
| **RFI Generator** | Táº¡o RFI vá»›i auto-priority detection |
| **RFI Tracker** | Theo dÃµi tráº¡ng thÃ¡i & deadline |
| **RFI Dashboard** | Dashboard HTML tá»•ng quan |
| **Priority Levels** | URGENT/HIGH/NORMAL/LOW vá»›i deadline tá»± Ä‘á»™ng |
| **Auto-escalation** | Leo thang khi quÃ¡ háº¡n |

### Files má»›i

| File | MÃ´ táº£ |
|------|--------|
| `SKILL_RFI/SKILL.md` | Entry point Ä‘áº§y Ä‘á»§ |
| `SKILL_RFI/scripts/rfi_generator.py` | Táº¡o RFI vá»›i priority detection |
| `SKILL_RFI/scripts/rfi_tracker.py` | Theo dÃµi tráº¡ng thÃ¡i |
| `SKILL_RFI/scripts/rfi_dashboard.py` | Dashboard HTML |
| `SKILL_RFI/references/RFI_Types_Guide.md` | HÆ°á»›ng dáº«n phÃ¢n loáº¡i RFI |

### RFI Priority Classification

| Má»©c | Trigger | Deadline |
|------|---------|----------|
| ðŸ”´ URGENT | "sáº­p", "nguy hiá»ƒm", "an toÃ n" | 24h |
| ðŸŸ  HIGH | "cháº­m tiáº¿n Ä‘á»™", "phÃ¡t sinh" | 3 ngÃ y |
| ðŸŸ¡ NORMAL | "thiáº¿u thÃ´ng tin", "cáº§n xÃ¡c nháº­n" | 7 ngÃ y |
| ðŸŸ¢ LOW | "lÃ m rÃµ", "bá»• sung" | 14 ngÃ y |

### Integration

```
Design_Evaluation phÃ¡t hiá»‡n Data Missing
    â†“
SKILL_RFI táº¡o RFI tá»± Ä‘á»™ng
    â†“
Theo dÃµi & leo thang
    â†“
Pháº£n há»“i â†’ TÃ­ch há»£p vÃ o phÃ¢n tÃ­ch
```

---

## 2026-08-30 â€” Audit Fixes & Standards Synchronization (v3.7)

### Tá»•ng quan

Sá»­a cÃ¡c lá»—i Ä‘Æ°á»£c phÃ¡t hiá»‡n qua audit toÃ n bá»™ há»‡ thá»‘ng skills.

### Váº¥n Ä‘á» Ä‘Ã£ sá»­a

| Issue | MÃ´ táº£ | Fix |
|-------|-------|-----|
| REGISTRY_INDEX-SCRIPT-NAMES | Script names khÃ´ng khá»›p vá»›i files thá»±c táº¿ | Viáº¿t láº¡i REGISTRY_INDEX.md vá»›i Ä‘Ãºng names |
| SKILL_INDEX-VERSION-MISMATCH | SKILL_INDEX ghi version cÅ© cho 2 skills | Cáº­p nháº­t: SDE v1.3.0, TI v1.3.0, DE v2.1.1 |
| REGISTRY_JSON-DEPRECATED | Deprecated scripts khÃ´ng cÃ³ `status: "DEPRECATED"` | ThÃªm trÆ°á»ng status cho 5 scripts cÅ© |

### Files Ä‘Ã£ sá»­a

| File | Thay Ä‘á»•i |
|------|----------|
| `_SYSTEM/SKILL_INDEX.md` | v1.3 â†’ v1.4, cáº­p nháº­t 3 version |
| `Technical_Illustrator/scripts/REGISTRY_INDEX.md` | Viáº¿t láº¡i hoÃ n toÃ n vá»›i Ä‘Ãºng script names |
| `Technical_Illustrator/scripts/registry.json` | v2.0.0 â†’ v2.1.0, thÃªm `"status": "DEPRECATED"` |

### Scripts trong registry.json

**ACTIVE (10 scripts):**
- `draw_2d_section.py` âœ…
- `draw_bolt_connection.py` âœ…
- `draw_rc_column.py` âœ…
- `draw_foundation.py` âœ…
- `draw_slab_rebar.py` âœ…
- `draw_comparison_chart.py` âœ…
- `draw_rc_beam_full.py` âœ…
- `draw_rc_wall.py` âœ…
- `draw_pile_cap.py` âœ…
- `draw_weld_detail.py` âœ…

**DEPRECATED (5 scripts):**
- `draw_ap_luc_dat_bo_ke.py` âš ï¸
- `draw_ke_buy_dung.py` âš ï¸
- `draw_ke_pi_gieng.py` âš ï¸
- `draw_pi_gieng_composite.py` âš ï¸
- `draw_tham_da.py` âš ï¸

---

## 2026-08-30 â€” DCE Pro Integration (v3.6)

### Tá»•ng quan

TÃ­ch há»£p AI Agent vá»›i DCE Pro qua chiáº¿n lÆ°á»£c má»›i:
- AI chá»‰ Ä‘iá»n data vÃ o Excel
- DCE Pro Add-In tá»± váº½ CAD
- KhÃ´ng cáº§n COM Interop phá»©c táº¡p

### Files má»›i

| File | MÃ´ táº£ | Size |
|------|--------|------|
| `dce_writer/__init__.py` | Module init | 525B |
| `dce_writer/beam_writer.py` | Ghi data dáº§m BTCT â†’ Excel | 8KB |
| `dce_writer/column_writer.py` | Ghi data cá»™t BTCT â†’ Excel | 6.7KB |
| `dce_writer/steel_writer.py` | Ghi data káº¿t cáº¥u thÃ©p â†’ Excel | 7.8KB |
| `dce_writer/README.md` | HÆ°á»›ng dáº«n sá»­ dá»¥ng | 2KB |
| `dce_trigger.py` | KÃ­ch hoáº¡t DCE Pro | 5.9KB |

### Luá»“ng hoáº¡t Ä‘á»™ng

```
AI Agent (Claude Code)
       â”‚
       â”œâ”€â”€ 1. TÃ­nh toÃ¡n káº¿t cáº¥u
       â”‚
       â”œâ”€â”€ 2. Gá»i dce_writer.py â†’ Ä‘iá»n data vÃ o Excel
       â”‚
       â”œâ”€â”€ 3. DCE Pro Add-In Ä‘á»c Excel â†’ váº½ CAD
       â”‚
       â””â”€â”€ 4. Agent trÃ­ch xuáº¥t PDF/DWG
```

### Templates Ä‘Æ°á»£c há»— trá»£

| Module | Template DCE | Status |
|--------|-------------|--------|
| Dáº§m BTCT | `09. DCE_Beam_2020.xlsm` | âœ… |
| Cá»™t BTCT | `08. DCE_ColumnWall_2020.xlsm` | âœ… |
| ThÃ©p Dáº§m | `20. TCVN 5575 Steel Beam Design - Section I.xlsm` | âœ… |
| ThÃ©p Cá»™t | `25. TCVN 5575 Steel Column Design - Section I.xlsm` | âœ… |
| Bu lÃ´ng neo | `160. Chi tiet bu long neo.xlsm` | âœ… |

### Version updates

| File | TrÆ°á»›c | Sau |
|------|--------|-----|
| Technical_Illustrator | v1.2.0 | **v1.3.0** |

---

## 2026-08-30 â€” Reorganization (v3.5)

### Tá»•ng quan

TÃ¡i cáº¥u trÃºc toÃ n bá»™ há»‡ thá»‘ng Ä‘á»ƒ dá»… sá»­ dá»¥ng vÃ  báº£o trÃ¬.

### Cáº¥u trÃºc má»›i

```
.agents/skills/
â”‚
â”œâ”€â”€ _SYSTEM/                    â† ðŸ“– Äá»ŒC TRÆ¯á»šC
â”‚   â”œâ”€â”€ AGENTS.md             â† Quy táº¯c chung
â”‚   â”œâ”€â”€ SKILL_INDEX.md         â† Chá»‰ má»¥c & tra cá»©u
â”‚   â””â”€â”€ STANDARDS_LOCK.md     â† TiÃªu chuáº©n chuáº©n
â”‚
â”œâ”€â”€ _CORE_SKILLS/             â† ðŸ”§ SKILLS CHÃNH
â”‚   â”œâ”€â”€ Design_Evaluation/
â”‚   â”œâ”€â”€ Structural_Design_Engineer/
â”‚   â””â”€â”€ Technical_Illustrator/
â”‚
â”œâ”€â”€ _SUPPORT_SKILLS/           â† ðŸ”§ SKILLS Há»– TRá»¢
â”‚   â”œâ”€â”€ Cost_Estimator/
â”‚   â”œâ”€â”€ SKILL_FORENSIC/
â”‚   â””â”€â”€ SKILL_VERIFY/
â”‚
â”œâ”€â”€ _SHARED/shared/           â† ðŸ”§ Shared utilities
â”‚
â”œâ”€â”€ _archive/                â† ðŸ“¦ File cÅ©
â”‚
â”œâ”€â”€ README.md               â† ðŸ”¹ Entry point Má»šI
â””â”€â”€ CHANGELOG.md
```

### Thay Ä‘á»•i

| Thay Ä‘á»•i | Chi tiáº¿t |
|-----------|----------|
| Táº¡o README.md | Entry point má»›i â€” user biáº¿t báº¯t Ä‘áº§u tá»« Ä‘Ã¢u |
| NhÃ³m _SYSTEM | AGENTS.md, SKILL_INDEX.md, STANDARDS_LOCK.md |
| NhÃ³m _CORE_SKILLS | 3 skills chÃ­nh |
| NhÃ³m _SUPPORT_SKILLS | 3 skills há»— trá»£ |
| NhÃ³m _SHARED | Utilities chung |

### Version updates

| File | TrÆ°á»›c | Sau |
|------|--------|-----|
| README.md | âŒ KhÃ´ng cÃ³ | âœ… Má»›i |
| AGENTS.md | v5.2 | **v5.3** |
| SKILL_INDEX.md | v1.2 | **v1.3** |

---

## 2026-08-30 â€” Plan A Cleanup (v3.4)

### Tá»•ng quan

Dá»n dáº¹p file rÃ¡c vÃ  cáº¥u trÃºc thá»«a.

### ÄÃ£ xÃ³a

| File | LÃ½ do |
|------|--------|
| `AUDIT_REPORT_2026-08-18.md` | ÄÃ£ ghi nháº­n trong CHANGELOG |
| `UPGRADE_SUMMARY.md` | TrÃ¹ng láº·p vá»›i CHANGELOG |
| `check_upgrade_status.py` | One-time script |
| `__pycache__/` | Cache khÃ´ng cáº§n thiáº¿t |

### ÄÃ£ di chuyá»ƒn

| File | Äáº¿n |
|------|------|
| `INTEGRATION_TEST.py` | `_archive/` |

### Giá»¯ nguyÃªn

| File | LÃ½ do |
|------|--------|
| `SKILL_INDEX.md` | Giá»¯ riÃªng vÃ¬ AGENTS.md lÃ  rules, SKILL_INDEX.md lÃ  reference â€” gá»™p láº¡i sáº½ quÃ¡ lá»›n (29KB) |

---

## 2026-08-30 â€” Phase 2 Architecture Improvements (v3.3)

### Tá»•ng quan

HoÃ n thÃ nh Phase 2: Cáº£i tiáº¿n kiáº¿n trÃºc há»‡ thá»‘ng.

### Shared Utilities â€” Táº¡o má»›i

| Module | File | MÃ´ táº£ | Status |
|--------|------|--------|--------|
| **Standards MCP** | `shared/standards_mcp/server.py` | Fast citation lookup, version validation | âœ… HoÃ n thÃ nh |
| **Memory Layer** | `shared/memory/project_memory.py` | Project context persistence | âœ… HoÃ n thÃ nh |
| **Parallel Workflow** | `shared/workflows/parallel_review_workflow.py` | Parallel review engine | âœ… HoÃ n thÃ nh |

### Shared Folder Structure

```
shared/
â”œâ”€â”€ standards_mcp/          â† MCP Server cho standards
â”‚   â”œâ”€â”€ server.py          â† Main server
â”‚   â””â”€â”€ cache/             â† Cache directory
â”œâ”€â”€ memory/               â† Memory layer
â”‚   â”œâ”€â”€ projects/        â† Project contexts
â”‚   â””â”€â”€ project_memory.py â† CLI tool
â””â”€â”€ workflows/            â† Workflow templates
    â”œâ”€â”€ templates/        â† Reusable templates
    â””â”€â”€ parallel_review_workflow.py
```

### Documentation Updates

- **SKILL_INDEX.md v1.2**: ThÃªm má»¥c 7 â€” Shared Utilities
- **shared/README.md**: HÆ°á»›ng dáº«n sá»­ dá»¥ng cÃ¡c tools má»›i

---

## 2026-08-30 â€” Phase 1 Quick Wins (v3.2)

### Tá»•ng quan

HoÃ n thÃ nh Phase 1 Quick Wins: nhá»¯ng thay Ä‘á»•i Ã­t rá»§i ro, hiá»‡u quáº£ cao.

### Scripts Má»›i â€” Validation Tools

| Script | Vá»‹ trÃ­ | MÃ´ táº£ | Status |
|--------|--------|--------|--------|
| `validate_registry.py` | `Design_Evaluation/scripts/` | Kiá»ƒm tra consistency giá»¯a registry.json vÃ  actual files | âœ… HoÃ n thÃ nh |
| `validate_handoff.py` | `Design_Evaluation/scripts/` | Validate JSON handoff tá»« SKILLKC â†’ SKILL_REPORT | âœ… HoÃ n thÃ nh |

### Eurocode Scripts â€” ÄÃ£ xá»­ lÃ½

| Script | HÃ nh Ä‘á»™ng | Tráº¡ng thÃ¡i |
|--------|------------|-------------|
| `calc_steel_beam.py` | Di chuyá»ƒn â†’ `_deprecated/` | âœ… HoÃ n thÃ nh |
| `calc_steel_connection.py` | Di chuyá»ƒn â†’ `_deprecated/` | âœ… HoÃ n thÃ nh |

### Version Updates

| Skill | TrÆ°á»›c | Sau |
|-------|--------|-----|
| Design_Evaluation | 2.1.0 | **2.1.1** |
| Structural_Design_Engineer | 1.2.0 | **1.3.0** |
| AGENTS.md | v5.0 | **v5.1** |
| SKILL_INDEX.md | v1.0 | **v1.1** |

### Documentation Updates

- **SKILL_INDEX.md v1.1**: Cáº­p nháº­t deprecated scripts table, Standards Lock summary
- **Structural_Design_Engineer/SKILL.md v1.3.0**: ThÃªm `_deprecated/` folder, cáº­p nháº­t script table
- **Design_Evaluation/SKILL.md v2.1.1**: ThÃªm reference Ä‘áº¿n validation scripts
- **AGENTS.md v5.1**: Cáº­p nháº­t changelog

---

## 2026-08-25 â€” Complete Fixes & TCVN 5575:2024 Scripts (v3.1)

### Tá»•ng quan

HoÃ n thÃ nh táº¥t cáº£ cÃ¡c fix cÃ²n láº¡i tá»« audit 2026-08-18.

### Scripts Má»›i â€” TCVN 5575:2024

| Script | MÃ´ táº£ | Status |
|--------|--------|--------|
| `calc_steel_beam_tcvn.py` | Kiá»ƒm tra dáº§m thÃ©p: uá»‘n + cáº¯t + LTB + vÃµng | âœ… HoÃ n thÃ nh |
| `calc_steeL_connection_tcvn.py` | Kiá»ƒm tra liÃªn káº¿t bu lÃ´ng: cáº¯t + Ã©p máº·t + kÃ©o | âœ… HoÃ n thÃ nh |

**Verification:**
- `calc_steel_beam_tcvn.py`: I400x200x8x13, M_ed=220kNm â†’ eta_M=54.7%, eta_V=27.7%, eta_LTB=57.3%, eta_f=51.8% â†’ PASS âœ…
- `calc_steel_connection_tcvn.py`: M20 cáº¥p 8.8, 6 bu lÃ´ng â†’ eta_shear=31.9%, eta_bearing=43.4%, eta_tension=5.9% â†’ PASS âœ…

### Cáº­p nháº­t STANDARDS_LOCK.md

- ThÃªm 2 script má»›i vÃ o báº£ng script
- Cáº­p nháº­t Known Gap section: âœ… FIXED cho cáº£ 2 issues
- HÆ°á»›ng dáº«n chá»n script: dÃ¹ng script TCVN cho há»“ sÆ¡ má»›i, Eurocode cho Ä‘á»‘i chiáº¿u quá»‘c táº¿

### Cáº­p nháº­t SKILL_INDEX.md

- ThÃªm 2 script má»›i vÃ o báº£ng Structural_Design_Engineer
- ThÃªm 2 script má»›i vÃ o Quick Reference

### Integration Test

- 46/46 tests PASS âœ…

---

## 2026-08-25 â€” Critical Cleanup & Governance Fixes (v3.0)

### Tá»•ng quan

Fix 5 váº¥n Ä‘á» governance vÃ  structure Ä‘Æ°á»£c phÃ¡t hiá»‡n qua audit.

### Version Synchronization

| Skill | TrÆ°á»›c | Sau |
|-------|-------|-----|
| Design_Evaluation | 1.3.0 | **2.1.0** |
| Technical_Illustrator | 1.1.0 | **1.2.0** |
| Cost_Estimator | 1.1.0 | **1.2.0** |
| SKILL_FORENSIC | 1.1.0 | **1.2.0** |
| SKILL_VERIFY | 1.1.0 | **1.2.0** |

### Deprecated Scripts â€” Di chuyá»ƒn sang `_deprecated/`

5 script fixed-geometry khÃ´ng sá»­ dá»¥ng Ä‘Æ°á»£c cho dá»± Ã¡n khÃ¡c:

| Script | LÃ½ do | HÃ nh Ä‘á»™ng |
|--------|-------|-----------|
| `draw_ap_luc_dat_bo_ke.py` | Fixed geometry | Di chuyá»ƒn â†’ `_deprecated/` |
| `draw_ke_buy_dung.py` | Fixed geometry | Di chuyá»ƒn â†’ `_deprecated/` |
| `draw_ke_pi_gieng.py` | Fixed geometry | Di chuyá»ƒn â†’ `_deprecated/` |
| `draw_pi_gieng_composite.py` | Fixed geometry | Di chuyá»ƒn â†’ `_deprecated/` |
| `draw_tham_da.py` | Fixed geometry | Di chuyá»ƒn â†’ `_deprecated/` |

### SKILL_INDEX.md â€” Táº¡o má»›i

Táº¡o file `SKILL_INDEX.md` lÃ m nguá»“n sá»± tháº­t DUY NHáº¤T vá»:
- Kiáº¿n trÃºc tá»•ng thá»ƒ (dependency graph)
- Danh má»¥c Ä‘áº§y Ä‘á»§ 6 skill + sub-modules
- Báº£ng tra nhanh: tÃ¬nh huá»‘ng â†’ skill â†’ script
- Tá»•ng há»£p STANDARDS_LOCK
- Pipeline Ä‘iá»ƒn hÃ¬nh
- Error codes

### Cáº­p nháº­t SKILL.md

Táº¥t cáº£ SKILL.md Ä‘Æ°á»£c cáº­p nháº­t:
- ThÃªm reference tá»›i `SKILL_INDEX.md`
- Cáº­p nháº­t path deprecated scripts tá»« má»¥c chÃ­nh sang `_deprecated/`

### Audit Findings Addressed

| Issue ID | MÃ´ táº£ | Fix |
|----------|-------|-----|
| AUDIT-01 | Version mismatch giá»¯a SKILL.md vÃ  SKILLKC.md | Äá»“ng bá»™ vá» 2.1.0 |
| AUDIT-02 | 5 deprecated scripts váº«n náº±m trong thÆ° má»¥c chÃ­nh | Di chuyá»ƒn sang `_deprecated/` |
| AUDIT-03 | Thiáº¿u centralized index | Táº¡o `SKILL_INDEX.md` |
| AUDIT-04 | KhÃ´ng cÃ³ integration test | Ghi nháº­n, cáº§n táº¡o sau |
| AUDIT-05 | Database calibration cáº§n cáº­p nháº­t | Ghi nháº­n trong SKILL_INDEX |

---

## 2026-08-19 â€” New Scripts & Reference Files (v2.1)

---

## 2026-08-18 â€” Critical Bug Fixes & Standards Cleanup (v2.1.1)

### Critical Fixes (Priority 1 - MUST FIX)

| Bug ID | File | Issue | Fix |
|--------|------|-------|-----|
| BUG-01 | `calc_steel_beam.py` | `GAMMA_M1 = 1.05` (sai) | Changed to `GAMMA_M1 = 1.10` |
| BUG-02 | `calc_steel_beam.py` | `ALPHA_LT = 0.34` (sai) | Changed to `ALPHA_LT = 0.21` (Ä‘Æ°á»ng cong a) |
| BUG-03 | `steel_member_check_v2024.py` | `M_c_Rd * 10` (vÃ´ nghÄ©a) | Removed `* 10`, Ä‘Ãºng Ä‘Æ¡n vá»‹ |
| BUG-04 | `calc_steel_beam.py` | KhÃ´ng tuyÃªn bá»‘ Eurocode | ThÃªm warning lá»›n Ä‘áº§u file |

### Logic Fixes

| Fix ID | File | Issue | Fix |
|--------|------|-------|-----|
| LOGIC-01 | `compare_structural_options.py` | Hardcoded `370000` labor rate | DÃ¹ng `DEFAULT_LABOR_RATE` constant |
| LOGIC-02 | `auto_rfi_generator.py` | `hash()` khÃ´ng deterministic | DÃ¹ng `hashlib.md5()` |

### Documentation Updates

| Doc ID | File | Change |
|--------|------|--------|
| DOC-01 | `SKILLKC.md` | ThÃªm YAML frontmatter |
| DOC-01 | `SKILL_REPORT.md` | ThÃªm YAML frontmatter |
| DOC-01 | `SKILL_CALC.md` | ThÃªm YAML frontmatter |

### Standards Cleanup

- Thá»‘ng nháº¥t `TCVN 9386` â†’ `TCVN 9386:2025` (P1+P5)
- Thá»‘ng nháº¥t `TCVN 10304` â†’ `TCVN 10304:2025`
- ÄÃ¡nh dáº¥u `calc_steel_beam.py` dÃ¹ng EN 1993-1-1 (khÃ´ng pháº£i TCVN)
- Cáº­p nháº­t `STANDARDS_LOCK.md` vá»›i thÃ´ng tin má»›i

### Deprecated Files

| File | Tráº¡ng thÃ¡i | Thay tháº¿ bá»Ÿi |
|------|------------|---------------|
| `steel_member_check.py` (2012) | âš ï¸ DEPRECATED | `steel_member_check_v2024.py` |

---

## 2026-08-19 â€” New Scripts & Reference Files (v2.1)

### Tá»•ng quan

Bá»• sung 9 script/reference file má»›i Ä‘á»ƒ hoÃ n thiá»‡n há»‡ thá»‘ng.

### Design_Evaluation
- **Má»šI:** `calculators/earthquake_load_calc.py` â€” TÃ­nh táº£i trá»ng Ä‘á»™ng Ä‘áº¥t TCVN 9386:2025 (P1+P5), phá»• pháº£n á»©ng, phÃ¢n bá»‘ lá»±c theo chiá»u cao
- **Má»šI:** `scripts/stage_gate_checklist.py` â€” Táº¡o checklist tá»± Ä‘á»™ng theo giai Ä‘oáº¡n (QS/TH/BVTC/THAU/GIAHAN), cÃ³ modifier theo loáº¡i cÃ´ng trÃ¬nh

### Technical_Illustrator
- **Má»šI:** `scripts/REGISTRY_INDEX.md` â€” Báº£ng tra cá»©u nhanh: tÃ¬nh huá»‘ng â†’ script, quy Æ°á»›c Ä‘áº·t tÃªn file output

### Structural_Design_Engineer
- **Má»šI:** `references/INDEX.md` â€” Chá»‰ má»¥c tham chiáº¿u: 3 nhÃ³m (BTCT/thÃ©p/mÃ³ng) + quick reference

### SKILL_VERIFY
- **Má»šI:** `scripts/verify_all.py` â€” Unified CLI cháº¡y Ä‘á»“ng thá»i cáº£ 5 loáº¡i kiá»ƒm chá»©ng, exit code theo CRITICAL/PASS

### SKILL_FORENSIC
- **Má»šI:** `references/RED_FLAG_TRIGGERS.md` â€” 4 cáº¥p nguy hiá»ƒm (CRITICALâ†’LOW), 18 triggers cá»¥ thá»ƒ, checklist kÃ­ch hoáº¡t, máº«u bÃ¡o cÃ¡o kháº©n
- **Má»šI:** `scripts/search_fm.py` â€” TÃ¬m kiáº¿m Failure Mode Database theo tá»« khÃ³a, 15 failure modes cÃ³ sáºµn

### Cost_Estimator
- **Má»šI:** `scripts/update_prices.py` â€” Cáº­p nháº­t Ä‘Æ¡n giÃ¡ thá»§ cÃ´ng/tá»± Ä‘á»™ng, so sÃ¡nh vs giÃ¡ cÅ©, xuáº¥t bÃ¡o cÃ¡o markdown
- **Má»šI:** `scripts/leed_credit_estimator.py` â€” Æ¯á»›c tÃ­nh Ä‘iá»ƒm LEED v4 BD+C, Carbon footprint vÃ²ng Ä‘á»i (embodied + operational), chi phÃ­ VE premium

---

## 2026-08-18 â€” Major Cleanup & Synchronization (v2.0)

### Tá»•ng quan

Äá»“ng bá»™ toÃ n bá»™ 6 skills: thÃªm frontmatter version, xÃ³a ná»™i dung trÃ¹ng láº·p, má»Ÿ rá»™ng AGENTS.md, cáº­p nháº­t STANDARDS_LOCK.md, táº¡o CHANGELOG táº­p trung.

### Design_Evaluation
- ThÃªm `version: 1.3.0` + `last_updated: 2026-08-18` vÃ o frontmatter
- Cáº­p nháº­t reference tá»« `SKILLKC.md` (19 nhÃ³m, 19 rules)

### Technical_Illustrator
- **FIX:** XÃ³a block trÃ¹ng láº·p ~200 dÃ²ng (2 báº£n mÃ´ táº£ vai trÃ² QLTK)
- ThÃªm `version: 1.1.0` + `last_updated: 2026-08-18` vÃ o frontmatter
- Bá»• sung tráº¡ng thÃ¡i **âš ï¸ DEPRECATED** cho 5 fixed-geometry scripts
- ThÃªm quy Æ°á»›c Ä‘áº·t tÃªn file output: `{ProjectCode}_{Element}_{View}_{Rev}.png`
- ThÃªm reference tá»›i `scripts/REGISTRY_INDEX.md` (táº¡o khi cáº§n)

### Structural_Design_Engineer
- ThÃªm `version: 1.2.0` + `last_updated: 2026-08-18` vÃ o frontmatter
- Bá»• sung hÆ°á»›ng dáº«n `calc_steel_beam.py` dÃ¹ng Eurocode 3 (khÃ´ng pháº£i TCVN 5575)

### Cost_Estimator
- ThÃªm `version: 1.1.0` + `last_updated: 2026-08-18` vÃ o frontmatter

### SKILL_FORENSIC
- ThÃªm `version: 1.1.0` + `last_updated: 2026-08-18` vÃ o frontmatter

### SKILL_VERIFY
- ThÃªm `version: 1.1.0` + `last_updated: 2026-08-18` vÃ o frontmatter

### AGENTS.md (má»›i)
- Má»Ÿ rá»™ng tá»« 3 skills lÃªn **6 skills** Ä‘áº§y Ä‘á»§
- Bá»• sung má»¥c 15: **Error Code System** (E001â€“E004, W001, I001)
- Bá»• sung má»¥c 16: **Pipeline Ä‘iá»ƒn hÃ¬nh** cho 4 luá»“ng cÃ´ng viá»‡c chÃ­nh
- Bá»• sung má»¥c 17: **Version Control** cho skills
- Cáº­p nháº­t Version History: v1.0 â†’ v4.0

### STANDARDS_LOCK.md
- Cáº­p nháº­t version: v1.0 â†’ v2.0
- Bá»• sung `steel_member_check_v2024.py` (TCVN 5575:2024 âœ…) vÃ o báº£ng script
- ThÃªm **HÆ°á»›ng dáº«n chá»n script** giá»¯a v2024 vÃ  v2012

### Changelog (má»›i)
- Táº¡o file `CHANGELOG.md` táº­p trung táº¡i `.agents/skills/`
- Ghi nháº­n táº¥t cáº£ thay Ä‘á»•i tá»« v1.0 Ä‘áº¿n v2.0

---

## 2026-07-28 â€” AGENTS.md v3.0 & STANDARDS_LOCK v1.0

- ThÃªm vÄƒn phong ká»¹ thuáº­t chuáº©n hÃ³a (Ä‘iá»u 12)
- ThÃªm version control cho file output
- Táº¡o STANDARDS_LOCK.md lÃ m nguá»“n sá»± tháº­t duy nháº¥t vá» tiÃªu chuáº©n
- Bá»• sung Citation Object 6 trÆ°á»ng

---

## 2026-07-15 â€” Deterministic Math v2.0

- Báº¯t buá»™c gá»i script tÃ­nh toÃ¡n, cáº¥m nháº©m tay
- YÃªu cáº§u má»i script tráº£ vá» `Calculation_Logs` + `Standard_Method`
- Má»Ÿ rá»™ng Standards Version Lock

---

## 2026-06-01 â€” Initial Release

- 3 skills ban Ä‘áº§u: Design_Evaluation, Structural_Design_Engineer, Technical_Illustrator
- AGENTS.md v1.0 vá»›i 11 Ä‘iá»u
