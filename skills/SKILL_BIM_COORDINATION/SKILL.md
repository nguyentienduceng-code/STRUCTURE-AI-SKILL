---
name: SKILL_BIM_COORDINATION
version: 0.5.0
last_updated: 2026-10-17
description: "Kỹ sư BIM Coordination AI: Clash detection giữa kết cấu (Structural) và cơ điện (MEP), phân tích xung đột mô hình IFC, kiểm tra mở lỗ xuyên dầm/sàn (penetration check), đề xuất giải pháp xử lý và xuất báo cáo phối hợp BIM. Kích hoạt khi: clash detection, BIM review, IFC analysis, xung đột kỹ thuật, phối hợp MEP-KC, kiểm tra xuyên dầm."
status: ACTIVE
roadmap: "v0.5.0 — Phase 1 Active: IFC Analysis & Hard Clash Detection Protocol"
---

# SKILL_BIM_COORDINATION — Phối Hợp Mô Hình BIM & Xử Lý Xung Đột Kết Cấu - MEP

> **Phiên bản:** v0.5.0 (Active)
> **Mục đích:** Phát hiện và giải quyết xung đột không gian giữa hệ thống Kết cấu (Structural) và Cơ điện (MEP), kiểm soát lỗ mở kỹ thuật dầm/sàn
> **Cập nhật:** 2026-10-17 — v0.5.0 (Active Module: IFC Analysis & Hard Clash Detection Protocol)

---

## 1. TỔNG QUAN

**SKILL_BIM_COORDINATION** là skill phát hiện và giải quyết xung đột giữa các hệ thống trong mô hình BIM — đặc biệt là clash giữa Structural (Kết cấu) và MEP (Cơ điện).

### 1.1 Mục tiêu

- Clash detection tự động giữa Structural vs MEP
- Phân tích file IFC (Industry Foundation Classes)
- Kiểm tra vùng an toàn khi mở lỗ xuyên dầm (penetration limits)
- Đề xuất giải pháp kỹ thuật cho xung đột (đi vòng, gia cường lỗ mở)
- Tạo báo cáo phối hợp và phân loại trách nhiệm các bên

### 1.2 Scope

| Phạm vi | Trạng thái | Ghi chú |
|----------|------------|---------|
| IFC schema parsing (IFC2x3, IFC4) | ✅ ACTIVE | Trích xuất hình học dầm, cột, sàn, ống gió, đường ống |
| Clash detection Structural vs MEP | ✅ ACTIVE | Phát hiện va chạm cứng (Hard clash) và khoảng cách an toàn (Clearance) |
| Duct/Pipe penetration check | ✅ ACTIVE | Kiểm tra vị trí lỗ khoét dầm BTCT theo TCVN 5574:2018 |
| Phân loại mức độ nghiêm trọng clash | ✅ ACTIVE | Critical (cột/dầm chính) vs Minor (sàn/vách ngăn) |
| Coordination report generation | 🔄 In Progress | Xuất ma trận xử lý clash & biên bản phối hợp đa bộ môn |
| Navisworks / BCF export | ⏳ Planned | Tích hợp định dạng BCF (BIM Collaboration Format) |

---

## 2. INTEGRATION VỚI CÁC SKILL KHÁC

### 2.1 Skill Dependencies

```
SKILL_BIM_COORDINATION (planned)
├── Dependencies:
│   ├── Technical_Illustrator (for clash visualization)
│   ├── Structural_Design_Engineer (for structural model info)
│   └── SKILL_RFI (for coordination documents)
│
└── Will trigger:
    ├── Technical_Illustrator (for clash drawings)
    ├── SKILL_RFI (for RFI creation if clash requires design change)
    └── Design_Evaluation (for structural review of proposed solutions)
```

### 2.2 Data Flow

```markdown
User Upload IFC Files
    │
    ▼
┌───────────────────────────────────────────────────────────────┐
│  SKILL_BIM_COORDINATION                                       │
│  - Parse IFC (Structural + MEP)                              │
│  - Extract element geometry                                   │
│  - Detect clashes                                            │
└───────────────────────────────────────────────────────────────┘
    │
    ├─► Technical_Illustrator (for clash visualization)
    │
    ├─► SKILL_RFI (if clash requires RFI to MEP designer)
    │
    └─► Design_Evaluation (if structural modification needed)
```

---

## 3. CÔNG CỤ CLI ĐÃ KÍCH HOẠT (ACTIVE CLI TOOLS)

### 3.1 Động Cơ Phát Hiện Xung Đột BIM (`clash_detector.py`)
Phát hiện va chạm không gian (Hard clash & Clearance) giữa các cấu kiện Kết cấu (Beam, Column, Slab, Wall) và Cơ điện (Duct, Pipe, CableTray, Equipment).

```bash
# Chạy phát hiện xung đột với mô hình demo tích hợp
python scripts/clash_detector.py

# Quét xung đột với ngưỡng dung sai 50mm và xuất file JSON kết quả
python scripts/clash_detector.py --tolerance 50 --output clashes_output.json
```

**Tham số:**
- `--ifc`: Đường dẫn file IFC (nếu có)
- `--tolerance`: Dung sai phát hiện xung đột theo mm (mặc định: `50` mm)
- `--output` / `-o`: Đường dẫn lưu file kết quả định dạng JSON

**Phân loại mức độ va chạm (Severity):**
- `CRITICAL`: Va chạm liên quan đến cấu kiện chịu lực chính (Cột C1, Dầm chính B1 vs Ống gió/Ống áp lực) → Yêu cầu dời tuyến MEP hoặc xử lý RFI
- `HIGH`: Va chạm giữa các hệ thống MEP chính (Ống gió HVAC vs Máng cáp điện Tray)
- `MEDIUM`: Vi phạm khoảng cách an toàn (Clearance < 100mm giữa điện và nước)
- `LOW`: Va chạm thứ yếu (vách nhẹ, chi tiết phụ)

**Exit codes:**
- `0`: Không có va chạm (Clean)
- `1`: Có va chạm thường
- `2`: Có va chạm nghiêm trọng (Critical clash)

---

## 4. CÁC MODULE DỰ KIẾN (PLANNED MODULES)

### MODULE 1: IFC Parser
**Chức năng:** Đọc và phân tích file IFC

```
Supported IFC entities:
├── IfcBuildingElement
│   ├── IfcBeam
│   ├── IfcColumn
│   ├── IfcSlab
│   └── IfcWall
│
├── IfcDistributionElement
│   ├── IfcDuctSegment
│   ├── IfcPipeSegment
│   └── IfcCableSegment
│
└── IfcBuilding
    └── Spatial containers

Output format:
{
  "elements": [
    {
      "global_id": "2x$cHj纱5@t8XWakq6$v74",
      "type": "IfcBeam",
      "name": "B1",
      "geometry": {
        "start": [x1, y1, z1],
        "end": [x2, y2, z2],
        "profile": "H400x200x8x13"
      },
      "location": [x, y, z, rotation]
    }
  ]
}
```

### MODULE 2: Clash Detection Engine
**Chức năng:** Phát hiện xung đột giữa các hệ thống

```
Clash Types:
├── Hard Clash
│   ├── Beam vs Duct intersection
│   ├── Column vs Pipe intersection
│   └── Slab vs MEP equipment
│
├── Clearance Clash
│   ├── Duct too close to beam
│   ├── Pipe not enough clearance from slab
│   └── MEP not enough space for maintenance
│
└── Coordination Clash
    ├── Duct runs through column core
    └── Multiple MEP crossing same space
```

### MODULE 3: Clash Resolution Advisor
**Chức năng:** Đề xuất giải pháp cho clash

```
Resolution Strategies:
├── Level 1: MEP Re-route
│   ├── Move duct/pipe around beam
│   ├── Adjust elevation
│   └── Change routing path
│
├── Level 2: Structural Modification
│   ├── Add penetration sleeve
│   ├── Modify beam web opening
│   └── Coordinate beam shift
│
└── Level 3: Design Change Request
    ├── Request structural review
    ├── Create RFI to MEP designer
    └── Coordination meeting required
```

### MODULE 4: Coordination Report Generator
**Chức năng:** Tạo báo cáo coordination

```
Report Sections:
├── 1. Executive Summary
│   ├── Total clashes found
│   ├── By severity breakdown
│   └── Resolution status
│
├── 2. Clash Register (Detailed)
│   ├── Clash ID, Location
│   ├── Elements involved
│   ├── Clash type & severity
│   ├── Recommended action
│   └── Status (Open/In Progress/Resolved)
│
├── 3. Structural Penetration Schedule
│   ├── Required core holes
│   ├── Sleeve specifications
│   └── Coordination status
│
└── 4. Attachments
    └── Clash location drawings
```

---

## 4. PLANNED SCRIPTS

```
SKILL_BIM_COORDINATION/
├── SKILL.md                           ← BẠN ĐANG Ở ĐÂY (Placeholder)
├── scripts/
│   ├── ifc_parser.py                  ← MODULE 1: IFC parsing
│   ├── clash_detector.py               ← MODULE 2: Clash detection
│   ├── resolution_advisor.py           ← MODULE 3: Resolution suggestions
│   ├── report_generator.py             ← MODULE 4: Coordination report
│   └── navisworks_export.py            ← Export sang Navisworks format
├── data/
│   ├── clash_categories.json          ← Clash type definitions
│   ├── clearance_requirements.json     ← Minimum clearance by system
│   └── resolution_templates.json      ← Standard resolution options
└── templates/
    └── coordination_report.docx       ← Report template
```

---

## 5. PLANNED DATA STRUCTURES

### 5.1 Clash Object

```json
{
  "clash_id": "CLASH-20260925-001",
  "type": "HARD_CLASH",
  "severity": "CRITICAL",
  "location": {
    "x": 5000,
    "y": 3000,
    "z": 2500,
    "floor": "Tầng 3",
    "zone": "Khu A"
  },
  "elements": {
    "structural": {
      "type": "IfcBeam",
      "name": "Dầm B1",
      "global_id": "2x$cHj纱5@t8XWakq6$v74"
    },
    "mep": {
      "type": "IfcDuctSegment",
      "name": "Duct AHU-01",
      "diameter": 600,
      "global_id": "3k$mHk纱6@t9YWblq7$w85"
    }
  },
  "geometry": {
    "intersection_volume": 0.05,
    "penetration_depth": 150
  },
  "resolution": {
    "status": "OPEN",
    "recommended_action": "MEP_REROUTE",
    "assigned_to": "MEP Designer",
    "due_date": "2026-10-01"
  }
}
```

### 5.2 Clearance Requirements

```json
{
  "clearance_requirements": {
    "duct_to_structure": {
      "circular_duct": 100,
      "rectangular_duct": 150,
      "trunking": 75
    },
    "pipe_to_structure": {
      "supply_pipe": 50,
      "drain_pipe": 75,
      "fire_pipe": 100
    },
    "mep_equipment": {
      "ahus": 600,
      "fan_coils": 300,
      "pumps": 400
    },
    "maintenance_access": {
      "duct_access": 450,
      "valve_access": 600,
      "equipment_access": 1000
    }
  }
}
```

---

## 6. INTERFACE VỚI NGƯỜI DÙNG

### 6.1 Planned Commands

```
User: "Check clash cho tầng 3"
→ SKILL_BIM_COORDINATION: "Đang phân tích IFC tầng 3..."
→ Output: Clash register với 15 clashes

User: "Tạo báo cáo coordination"
→ SKILL_BIM_COORDINATION: "Đang tạo Coordination Report..."
→ Output: coordination_report.docx

User: "Giải pháp cho clash B1 vs Duct AHU-01"
→ SKILL_BIM_COORDINATION: "Đề xuất:
   1. Di chuyển duct lên 200mm
   2. Thêm sleeve nếu cần đi qua dầm"

User: "Export sang Navisworks"
→ SKILL_BIM_COORDINATION: "Đang export..."
→ Output: clashes.nwc (Navisworks Clash Detective)
```

### 6.2 Integration Prompts

```
Khi Structural_Design_Engineer hoàn thành:
→ SKILL_BIM_COORDINATION: "Cập nhật structural model để check clash"

Khi Technical_Illustrator tạo drawing:
→ SKILL_BIM_COORDINATION: "Thêm clash location vào drawing"

Khi phát hiện clash cần design change:
→ SKILL_BIM_COORDINATION → SKILL_RFI: "Tạo RFI cho clash resolution"
```

---

## 7. ROADMAP

### Phase 1 (v0.2.0) - IFC Basic Parsing
- [ ] IFC file upload/parsing
- [ ] Element extraction (Structural only)
- [ ] Basic 3D visualization

### Phase 2 (v0.3.0) - MEP Integration
- [ ] MEP element parsing
- [ ] Hard clash detection
- [ ] Clash register export

### Phase 3 (v0.5.0) - Resolution & Reporting
- [ ] Clearance analysis
- [ ] Resolution advisor
- [ ] Coordination report generator

### Phase 4 (v1.0.0) - Full Integration
- [ ] Navisworks export
- [ ] Revit link
- [ ] Real-time coordination dashboard
- [ ] RFI auto-generation

---

## 8. TECHNICAL NOTES

### 8.1 Recommended Libraries

```
Python Libraries:
├── ifcopenshell         # IFC file parsing (GPL license)
├── trimesh              # 3D mesh operations
├── shapely              # 2D geometry operations
├── numpy                # Numerical operations
└── python-docx          # Report generation

External Tools:
├── Navisworks CLI       # Clash detection batch
├── BlenderBIM           # Open-source BIM viewer
└── FreeCAD             # 3D model operations
```

### 8.2 IFC Schema Support

```
Priority 1: IFC2x3
- Most widely supported
- All major BIM software export

Priority 2: IFC4
- Newer schema
- Better geometry representation
- Partial support

Priority 3: IFC4x1
- Latest schema
- Limited tool support
```

### 8.3 Performance Considerations

```
Large Model Handling:
├── Level of Detail (LOD) filtering
├── Floor-by-floor analysis
├── Parallel processing for large models
└── Caching of parsed elements
```

---

## VERSION HISTORY

| Version | Date | Changes |
|---------|------|---------|
| 0.5.0 | 2026-10-17 | Nâng cấp từ Placeholder lên v0.5.0 Active: Kích hoạt protocol phân tích IFC, phát hiện xung đột kết cấu - cơ điện và kiểm tra lỗ mở dầm/sàn |
| 0.1.0 | 2026-09-25 | Initial placeholder |
