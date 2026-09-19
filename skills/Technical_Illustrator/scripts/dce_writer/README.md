# DCE Writer — Smart Excel Writer for DCE Pro

Kết nối AI Agent với DCE Pro qua việc điền data vào Excel.

## Cấu trúc

```
dce_writer/
├── __init__.py
├── beam_writer.py      ← Dầm BTCT
├── column_writer.py    ← Cột BTCT
├── steel_writer.py     ← Kết cấu thép
└── README.md
```

## Luồng hoạt động

```
AI Agent (Claude Code)
       │
       ├── 1. Tính toán kết cấu
       │
       ├── 2. Gọi dce_writer.py → điền data vào Excel
       │
       ├── 3. DCE Pro Add-In đọc Excel → vẽ CAD
       │
       └── 4. Agent trích xuất PDF/DWG
```

## Sử dụng

### Dầm BTCT

```bash
python -m dce_writer.beam_writer --input data.json --output output.xlsm
```

### Cột BTCT

```bash
python -m dce_writer.column_writer --input data.json --output output.xlsm
```

### Kết cấu thép

```bash
python -m dce_writer.steel_writer --module beam --input data.json
python -m dce_writer.steel_writer --module column --input data.json
python -m dce_writer.steel_writer --module connection --input data.json
```

## Input JSON format

```json
{
  "project_code": "DA001",
  "beam_name": "B1",
  "b": 200,
  "h": 400,
  "L": 6000,
  "concrete": "B30",
  "steel": "CB400",
  "rebar_top": {"n": 3, "dia": 20},
  "rebar_bottom": {"n": 2, "dia": 20},
  "stirrup": {"dia": 8, "s1": 100, "s2": 200},
  "M_ed": 150,
  "V_ed": 80,
  "eta_M": 0.75,
  "eta_V": 0.45
}
```

## Templates

| Module | Template Path |
|--------|--------------|
| Dầm BTCT | `C:\Dce Pro\Excel\File V.2020\09. DCE_Beam_2020.xlsm` |
| Cột BTCT | `C:\Dce Pro\Excel\File V.2020\08. DCE_ColumnWall_2020.xlsm` |
| Thép Dầm | `C:\Dce Pro\Excel\DceSteel\20. TCVN 5575 Steel Beam Design - Section I.xlsm` |
| Thép Cột | `C:\Dce Pro\Excel\DceSteel\25. TCVN 5575 Steel Column Design - Section I.xlsm` |

## Kích hoạt DCE Pro

```bash
python dce_trigger.py --excel output.xlsm --module beam
python dce_trigger.py --excel output.xlsm --module beam --launch-cad
```

## Cập nhật: 2026-08-30
