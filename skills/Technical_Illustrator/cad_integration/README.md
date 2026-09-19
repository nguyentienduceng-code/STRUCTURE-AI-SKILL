# 🖥️ CAD INTEGRATION - HƯỚNG DẪN SỬ DỤNG

## Tổng quan

```
┌─────────────────────────────────────────────────────────────────────┐
│                    AI + CALCULATOR + CAD                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  AI Assistant                                                      │
│       │                                                             │
│       ▼                                                             │
│  Calculator Scripts ──────────┐                                    │
│  (calc_rc_section.py)        │                                    │
│  (calc_steel_beam.py)        │                                    │
│                                 │                                    │
│                                 ▼                                    │
│  calc_to_dxf.py ◄────────────┘                                    │
│       │                                                             │
│       ▼                                                             │
│  DXF Files ─────────────────┐                                    │
│                               │                                    │
│                               ▼                                    │
│  AutoCAD + DCE Pro ◄────────┘                                    │
│       │                                                             │
│       ▼                                                             │
│  Final .dwg (Hồ sơ thi công)                                    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## CẤU TRÚC FILES

```
Technical_Illustrator/
└── cad_integration/
    ├── calc_to_dxf.py           ← Tích hợp Calculator → DXF
    ├── dce_dxf_generator.py     ← Generator DCE Pro
    ├── analyze_dxf.py            ← Phân tích DXF
    ├── README.md                ← Hướng dẫn này
    └── scripts/
        └── export_form2_to_dxf.lsp
```

---

## BẮT ĐẦU

### Cách 1: Tự động (Khuyến nghị)

```python
# -*- coding: utf-8 -*-
"""
tao_ban_ve.py - Tao ban ve tu Calculator
"""

import sys
import os

# Add paths
sys.path.insert(0, '../Structural_Design_Engineer/scripts')
sys.path.insert(0, '.')

from calc_rc_section import calc_rc_beam
from calc_steel_beam import calc_steel_beam
from calc_to_dxf import RCCalculatorToDXF, SteelCalculatorToDXF

# === DAM BTCT ===
# 1. Chay Calculator
rc_result = calc_rc_beam(
    b=300, h=600, a=40,
    concrete="B25", rebar="CB400-V",
    M_ed=250, V_ed=120,
    stirrup_dia=8, stirrup_legs=2, stirrup_spacing=150
)

print(f"Calculator: {rc_result['section']}")
print(f"As_chon: {rc_result['As_chon_mm2']} mm2")
print(f"Status: {rc_result['status']}")

# 2. Tao DXF
rc_dxf = RCCalculatorToDXF(rc_result)
output_dir = "G:/My Drive/Google AI Studio/output"
os.makedirs(output_dir, exist_ok=True)
rc_dxf.generate(os.path.join(output_dir, "DA01_MC-D1_01.dxf"))

# === DAM THÉP ===
steel_result = calc_steel_beam(
    h=400, b=200, tw=8, tf=13,
    M_ed=220, V_ed=150,
    fy=345, L_span=6000
)

steel_dxf = SteelCalculatorToDXF(steel_result)
steel_dxf.generate(os.path.join(output_dir, "DA01_MC-D1_02.dxf"))

print("[OK] Tat ca ban ve da tao!")
```

### Cách 2: Đọc từ JSON file

```python
import json
from calc_to_dxf import RCCalculatorToDXF

# Doc ket qua tu file
with open('calculation_result.json', 'r') as f:
    calc_data = json.load(f)

# Tao DXF
dxf = RCCalculatorToDXF(calc_data)
dxf.generate('output/banve.dxf')
```

### Cách 3: Chạy script có sẵn

```bash
cd "G:\My Drive\Google AI Studio\.agents\skills\Technical_Illustrator\cad_integration"
python calc_to_dxf.py
```

---

## WORKFLOW HOÀN CHỈNH

```
┌────────────────────────────────────────────────────────────────────┐
│  BƯỚC 1: AI Assistant phân tích                              │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  User: "Thiet ke dam BTCT D1, M=250kNm, V=120kN"              │
│                                                                     │
│  AI:                                                           │
│    1. Tinh toan: calc_rc_beam(b=300, h=600, M=250...)        │
│    2. Ket qua: bxH = 300x600mm, As_chon = 1500mm2           │
│    3. Status: PASSED                                           │
│                                                                     │
└────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────────┐
│  BƯỚC 2: Tao DXF                                              │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Python:                                                         │
│    from calc_to_dxf import RCCalculatorToDXF                    │
│    dxf = RCCalculatorToDXF(calc_result)                        │
│    dxf.generate("output/DA01_MC-D1_01.dxf")                    │
│                                                                     │
│  Output:                                                         │
│    G:\My Drive\Google AI Studio\output\DA01_MC-D1_01.dxf    │
│                                                                     │
└────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────────┐
│  BƯỚC 3: Mo trong AutoCAD                                      │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. Mo AutoCAD 2021                                            │
│  2. File > Open > DA01_MC-D1_01.dxf                            │
│  3. Ban ve hien thi:                                             │
│     - Mat cat dam 300x600                                        │
│     - Thep 2D22 + 3D22                                         │
│     - Kich thuoc, text theo chuan DCE Pro                      │
│                                                                     │
└────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────────┐
│  BƯỚC 4: DCE Pro bo sung (optional)                           │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Trong AutoCAD:                                                  │
│    - Dung DCE Pro: ShopDrawingBeam                             │
│    - Hoac: Bo sung thu cong cac chi tiet                        │
│    - Export: .dwg                                                │
│                                                                     │
└────────────────────────────────────────────────────────────────────┘
```

---

## DCE PRO LAYERS (tu Form 2.dxf)

| Layer | Color | Mô tả |
|-------|-------|--------|
| `DCE_BaoBeTong` | 4 | Bê tông |
| `DCE_ThepChu` | 1 | Thép chủ |
| `DCE_ThepDai` | 220 | Thép đai |
| `DCE_Dim` | 254 | Kích thước |
| `Dce_text` | 7 | Text |
| `DCE_Truc` | 8 | Đường trục |
| `DCE_Block` | 8 | Block |

---

## FILES ĐÃ TAO

```
G:\My Drive\Google AI Studio\
└── output\
    ├── DA01_MC-D1_01.dxf       ← Mat cat dam mau
    ├── RC_Beam_Integrated.dxf  ← Tu RC Calculator
    └── Steel_Beam_Integrated.dxf ← Tu Steel Calculator
```

---

## CÁC LỆNH DCE PRO HỮU ÍCH

```autolisp
; Trong AutoCAD:
vd          ; Ve dam
ShopDrawingBeam  ; Shop drawing dam
vc          ; Ve cot
ImportKichThuocCot  ; Import kich thuoc cot
tkt_dce     ; Thong ke thep
```

---

## VÍ DỤ ĐẦY ĐỦ

```python
# tao_ban_ve_du_an.py
import sys
import os
from datetime import datetime

# Setup paths
sys.path.insert(0, '../Structural_Design_Engineer/scripts')
sys.path.insert(0, '.')

from calc_rc_section import calc_rc_beam
from calc_steel_beam import calc_steel_beam
from calc_to_dxf import (
    RCCalculatorToDXF,
    SteelCalculatorToDXF,
    BatchCalculatorToDXF
)

# === CAU HINH ===
PROJECT_CODE = "DA01"
output_dir = "G:/My Drive/Google AI Studio/output"
os.makedirs(output_dir, exist_ok=True)

# === DAM D1 - BTCT ===
print("Dang xu ly dam D1...")
rc_d1 = calc_rc_beam(
    b=300, h=600, a=40,
    concrete="B25", rebar="CB400-V",
    M_ed=250, V_ed=120,
    stirrup_dia=8, stirrup_legs=2, stirrup_spacing=150
)
rc_d1_dxf = RCCalculatorToDXF(rc_d1)
rc_d1_dxf.generate(f"{output_dir}/{PROJECT_CODE}_MC-D1_01.dxf")

# === DAM D2 - THEP ===
print("Dang xu ly dam D2 (thep)...")
steel_d2 = calc_steel_beam(
    h=400, b=200, tw=8, tf=13,
    M_ed=220, V_ed=150,
    fy=345, L_span=6000
)
steel_d2_dxf = SteelCalculatorToDXF(steel_d2)
steel_d2_dxf.generate(f"{output_dir}/{PROJECT_CODE}_MC-D2_01.dxf")

# === COT C1 - BTCT ===
print("Dang xu ly cot C1...")
# (Them calculator cho cot neu can)

print()
print("="*60)
print("[OK] Tat ca ban ve da tao!")
print(f"Thu muc: {output_dir}")
print("="*60)
```

---

## HỖ TRỢ

Nếu cần thêm:
- Script cho cột, vách, móng
- Title block template
- Layer standards
- Batch processing

**Gửi yêu cầu cho tôi!**

---

*Generated: 2026-08-18*
