"""
dce_steel_writer.py — Ghi data cau kien thep vao Excel DCE Pro

Template: C:/Dce Pro/Excel/DceSteel/*.xlsm

Supported modules:
    - 20. TCVN 5575 Steel Beam Design - Section I.xlsm
    - 25. TCVN 5575 Steel Column Design - Section I.xlsm
    - 160. Chi tiet bu long neo.xlsm

Usage:
    python steel_writer.py --module beam --input data.json --output output.xlsm
    python steel_writer.py --module column --input data.json --output output.xlsm
    python steel_writer.py --module connection --input data.json --output output.xlsm
"""

import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
import json
import sys
import argparse
from pathlib import Path
from openpyxl import load_workbook
from typing import Dict, List, Optional

# =============================================================================
# CONSTANTS & TEMPLATES
# =============================================================================

STEEL_TEMPLATES = {
    "beam": r"C:\Dce Pro\Excel\DceSteel\20. TCVN 5575 Steel Beam Design - Section I.xlsm",
    "column": r"C:\Dce Pro\Excel\DceSteel\25. TCVN 5575 Steel Column Design - Section I.xlsm",
    "connection": r"C:\Dce Pro\Excel\DceSteel\160. Chi tiet bu long neo.xlsm",
}

# Cell mapping cho steel beam
BEAM_CELLS = {
    "project_code": ("Sheet1", "B2"),
    "beam_name": ("Sheet1", "B3"),
    "section_type": ("Sheet1", "B4"),    # I, H, Box...
    "section_size": ("Sheet1", "B5"),    # I300x150...

    # Kích thước tiết diện
    "h": ("Sheet1", "B7"),              # Chiều cao (mm)
    "b": ("Sheet1", "B8"),              # Bề rộng cánh (mm)
    "tw": ("Sheet1", "B9"),             # Bề dày bụng (mm)
    "tf": ("Sheet1", "B10"),            # Bề dày cánh (mm)

    # Vật liệu
    "steel_grade": ("Sheet1", "B12"),   # SS400, SM490...

    # Tải trọng
    "M_ed": ("Sheet1", "B15"),          # kNm
    "V_ed": ("Sheet1", "B16"),         # kN
    "N_ed": ("Sheet1", "B17"),         # kN (neu co)

    # Chiều dài
    "L": ("Sheet1", "B19"),             # Nhịp (mm)
    "Ltb": ("Sheet1", "B20"),          # Chiều dài LTB (mm)

    # Kết quả
    "eta_M": ("Sheet1", "B25"),
    "eta_V": ("Sheet1", "B26"),
    "eta_LTB": ("Sheet1", "B27"),
    "eta_f": ("Sheet1", "B28"),
}

# Cell mapping cho steel column
COLUMN_CELLS = {
    "project_code": ("Sheet1", "B2"),
    "column_name": ("Sheet1", "B3"),
    "section_type": ("Sheet1", "B4"),
    "section_size": ("Sheet1", "B5"),

    "h": ("Sheet1", "B7"),
    "b": ("Sheet1", "B8"),
    "tw": ("Sheet1", "B9"),
    "tf": ("Sheet1", "B10"),

    "steel_grade": ("Sheet1", "B12"),

    "N_ed": ("Sheet1", "B15"),
    "M_ed": ("Sheet1", "B16"),
    "V_ed": ("Sheet1", "B17"),

    "L": ("Sheet1", "B19"),

    "eta_N": ("Sheet1", "B25"),
    "eta_M": ("Sheet1", "B26"),
}


class SteelWriter:
    """Writer class cho Cau kien Thep"""

    def __init__(self, module: str = "beam"):
        self.module = module
        self.template_path = Path(STEEL_TEMPLATES.get(module, STEEL_TEMPLATES["beam"]))
        self.data: Dict = {}
        self.cell_mapping = self._get_cell_mapping()

    def _get_cell_mapping(self) -> Dict:
        """Get cell mapping theo module"""
        if self.module == "beam":
            return BEAM_CELLS
        elif self.module == "column":
            return COLUMN_CELLS
        else:
            return BEAM_CELLS

    def load_template(self) -> bool:
        """Load Excel template"""
        if not self.template_path.exists():
            print(f"ERROR: Template not found: {self.template_path}")
            return False

        try:
            self.wb = load_workbook(self.template_path)
            return True
        except Exception as e:
            print(f"ERROR: Cannot load template: {e}")
            return False

    def format_section(self, section_type: str, h: int, b: int, tw: float, tf: float) -> str:
        """
        Format tiết diện, ví dụ:
        'I', 300, 150, 8, 12 -> 'I300x150x8x12'
        """
        return f"{section_type}{h}x{b}x{tw}x{tf}"

    def set_value(self, field: str, value) -> bool:
        """Set value vao cell theo mapping"""
        if field not in self.cell_mapping:
            print(f"WARNING: Unknown field '{field}'")
            return False

        sheet_name, cell = self.cell_mapping[field]

        try:
            ws = self.wb[sheet_name]
            ws[cell] = value
            return True
        except Exception as e:
            print(f"ERROR: Cannot set {field} -> {cell}: {e}")
            return False

    def load_from_json(self, json_path: str) -> bool:
        """Load data from JSON file"""
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            return True
        except Exception as e:
            print(f"ERROR: Cannot load JSON: {e}")
            return False

    def load_from_dict(self, data: Dict):
        """Load data from dictionary"""
        self.data = data

    def write_all(self) -> bool:
        """Write all data to Excel"""
        # Write simple fields
        for field, data_key in [
            ("project_code", "project_code"),
            ("beam_name", "element_name"),
            ("section_type", "section_type"),
            ("h", "h"),
            ("b", "b"),
            ("tw", "tw"),
            ("tf", "tf"),
            ("steel_grade", "steel_grade"),
            ("M_ed", "M_ed"),
            ("V_ed", "V_ed"),
            ("N_ed", "N_ed"),
            ("L", "L"),
            ("Ltb", "Ltb"),
        ]:
            if data_key in self.data:
                self.set_value(field, self.data[data_key])

        # Auto-generate section size string
        if all(k in self.data for k in ["section_type", "h", "b", "tw", "tf"]):
            section = self.format_section(
                self.data["section_type"],
                self.data["h"],
                self.data["b"],
                self.data["tw"],
                self.data["tf"]
            )
            self.set_value("section_size", section)

        return True

    def save(self, output_path: str) -> bool:
        """Save workbook to output path"""
        try:
            self.wb.save(output_path)
            print(f"SUCCESS: Saved to {output_path}")
            return True
        except Exception as e:
            print(f"ERROR: Cannot save: {e}")
            return False

    def write_and_save(self, data: Dict, output_path: str) -> bool:
        """Convenience method: load data and save"""
        self.load_from_dict(data)
        if not self.load_template():
            return False
        if not self.write_all():
            return False
        return self.save(output_path)


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Ghi data cau kien thep vao Excel DCE Pro")
    parser.add_argument("--module", "-m", required=True,
                       choices=["beam", "column", "connection"],
                       help="Module type")
    parser.add_argument("--input", "-i", required=True, help="Input JSON file")
    parser.add_argument("--output", "-o", help="Output Excel file (default: auto)")

    args = parser.parse_args()

    writer = SteelWriter(module=args.module)
    if not writer.load_from_json(args.input):
        sys.exit(1)

    if args.output:
        output_path = args.output
    else:
        input_path = Path(args.input)
        output_path = str(input_path.parent / f"DCE_Steel_{args.module}_{input_path.stem}_output.xlsm")

    if writer.write_and_save(writer.data, output_path):
        print(f"\nOutput: {output_path}")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
