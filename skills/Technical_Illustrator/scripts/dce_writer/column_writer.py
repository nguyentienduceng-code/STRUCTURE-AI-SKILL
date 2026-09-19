"""
dce_column_writer.py — Ghi data cot BTCT vao Excel DCE Pro

Template: C:/Dce Pro/Excel/File V.2020/08. DCE_ColumnWall_2020.xlsm

Usage:
    python column_writer.py --input data.json --output output.xlsm
"""

import json
import sys
import argparse
from pathlib import Path
from openpyxl import load_workbook
from typing import Dict, List, Optional

# =============================================================================
# CONSTANTS
# =============================================================================

DCE_COLUMN_TEMPLATE = r"C:\Dce Pro\Excel\File V.2020\08. DCE_ColumnWall_2020.xlsm"

# Cell mapping cho cot
CELL_MAPPING = {
    "project_code": ("Sheet1", "B2"),
    "column_name": ("Sheet1", "B3"),
    "column_width": ("Sheet1", "B4"),     # b (mm)
    "column_depth": ("Sheet1", "B5"),      # h (mm)
    "height": ("Sheet1", "B6"),           # H (mm)
    "floor_height": ("Sheet1", "B7"),      # Chieu cao tang
    "concrete_grade": ("Sheet1", "B8"),   # B30, B35...
    "steel_grade": ("Sheet1", "B9"),     # CB300, CB400...

    # Thép chịu nén
    "corner_rebar": ("Sheet1", "B11"),   # Thép góc
    "side_rebar": ("Sheet1", "B12"),     # Thép bên

    # Thép đai
    "tie_dia": ("Sheet1", "B14"),        # VD: a8
    "tie_spacing": ("Sheet1", "B15"),    # VD: a200

    # Tải trọng
    "N_ed": ("Sheet1", "B18"),           # kN
    "M_ed": ("Sheet1", "B19"),           # kNm
    "V_ed": ("Sheet1", "B20"),           # kN

    # Kết quả kiểm tra
    "eta_N": ("Sheet1", "B25"),
    "eta_M": ("Sheet1", "B26"),
}


class ColumnWriter:
    """Writer class cho Cot BTCT"""

    def __init__(self, template_path: str = DCE_COLUMN_TEMPLATE):
        self.template_path = Path(template_path)
        self.data: Dict = {}

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

    def format_bar_string(self, n: int, dia: int) -> str:
        """Format thanh thanh thanh: 3, 20 -> '3D20'"""
        return f"{n}D{dia}"

    def format_column_rebar(self, corner: Dict, side: Dict) -> str:
        """
        Format thanh cot, vi du:
        corner = {n: 4, dia: 25}
        side = {n: 2, dia: 20}
        -> '4D25 + 2D20'
        """
        parts = []
        if corner.get("n", 0) > 0:
            parts.append(f"{corner['n']}D{corner['dia']}")
        if side.get("n", 0) > 0:
            parts.append(f"{side['n']}D{side['dia']}")
        return " + ".join(parts) if parts else ""

    def set_value(self, field: str, value) -> bool:
        """Set value vao cell theo mapping"""
        if field not in CELL_MAPPING:
            print(f"WARNING: Unknown field '{field}'")
            return False

        sheet_name, cell = CELL_MAPPING[field]

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
        simple_fields = [
            ("project_code", "project_code"),
            ("column_name", "column_name"),
            ("column_width", "b"),
            ("column_depth", "h"),
            ("height", "H"),
            ("floor_height", "floor_H"),
            ("concrete_grade", "concrete"),
            ("steel_grade", "steel"),
            ("N_ed", "N_ed"),
            ("M_ed", "M_ed"),
            ("V_ed", "V_ed"),
        ]

        for field, data_key in simple_fields:
            if data_key in self.data:
                self.set_value(field, self.data[data_key])

        # Write structured rebar
        if "rebar_corner" in self.data:
            corner = self.data["rebar_corner"]
            if "n" in corner and "dia" in corner:
                self.set_value("corner_rebar", self.format_bar_string(corner["n"], corner["dia"]))

        if "rebar_side" in self.data:
            side = self.data["rebar_side"]
            if "n" in side and "dia" in side:
                self.set_value("side_rebar", self.format_bar_string(side["n"], side["dia"]))

        # Write tie
        if "tie" in self.data:
            tie = self.data["tie"]
            if "dia" in tie:
                self.set_value("tie_dia", f"a{tie['dia']}")
            if "spacing" in tie:
                self.set_value("tie_spacing", f"a{tie['spacing']}")

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
    parser = argparse.ArgumentParser(description="Ghi data cot BTCT vao Excel DCE Pro")
    parser.add_argument("--input", "-i", required=True, help="Input JSON file")
    parser.add_argument("--output", "-o", help="Output Excel file (default: auto)")

    args = parser.parse_args()

    writer = ColumnWriter()
    if not writer.load_from_json(args.input):
        sys.exit(1)

    if args.output:
        output_path = args.output
    else:
        input_path = Path(args.input)
        output_path = str(input_path.parent / f"DCE_{input_path.stem}_output.xlsm")

    if writer.write_and_save(writer.data, output_path):
        print(f"\nOutput: {output_path}")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
