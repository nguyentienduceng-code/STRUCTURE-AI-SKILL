"""
dce_beam_writer.py — Ghi data dầm BTCT vào Excel DCE Pro

Template: C:/Dce Pro/Excel/File V.2020/09. DCE_Beam_2020.xlsm
Active Sheet: DCE_Pro_Beam

Cấu trúc thực tế (đã verify):
- Row 2: Tên dầm (B2)
- Row 3: b dầm mm (B3)
- Row 4: h dầm mm (B4)
- Row 5: Số cấu kiện (B5)
- Row 6: Cao trình dầm (B6)
- Row 7: h sàn mm (B7)
- Row 10: Gối | Nhịp 1 | Nhịp 2 | ... (B10, C10, D10, E10)
- Row 11: Thép chịu lực TRÊN (B11, C11, D11, E11)
- Row 12: Thép chịu lực DƯỚI (B12, C12, D12, E12)
- Row 26: Thép đai (B26)
- Row 27: Đai trong (B27)

Usage:
    python beam_writer.py --input data.json --output output.xlsm
"""

import json
import sys
import os
import argparse
from pathlib import Path
from openpyxl import load_workbook
from typing import Dict, List, Optional, Union

# =============================================================================
# CONSTANTS
# =============================================================================

DCE_BEAM_TEMPLATE = r"C:\Dce Pro\Excel\File V.2020\09. DCE_Beam_2020.xlsm"
ACTIVE_SHEET = "DCE_Pro_Beam"

# Cell mapping CHÍNH XÁC (đã verify từ thực tế)
CELL_MAPPING = {
    # Thông tin cơ bản
    "beam_name": ("B", 2),      # Tên dầm
    "b": ("B", 3),              # b dầm (mm)
    "h": ("B", 4),              # h dầm (mm)
    "so_cau_kien": ("B", 5),   # Số cấu kiện
    "cao_trinh": ("B", 6),      # Cao trình dầm
    "h_san": ("B", 7),         # h sàn (mm)
    "L_ngan": ("B", 8),        # Dầm ngắn L(m)

    # Thép chịu lực TRÊN (Row 11) - cho từng vị trí
    "As_top_gocitrai": ("B", 11),    # Gối trái
    "As_top_nhip1": ("C", 11),        # Nhịp 1
    "As_top_nhip2": ("D", 11),        # Nhịp 2
    "As_top_nhip3": ("E", 11),        # Nhịp 3
    "As_top_gociphai": ("F", 11),     # Gối phải

    # Thép chịu lực DƯỚI (Row 12) - cho từng vị trí
    "As_bot_gocitrai": ("B", 12),
    "As_bot_nhip1": ("C", 12),
    "As_bot_nhip2": ("D", 12),
    "As_bot_nhip3": ("E", 12),
    "As_bot_gociphai": ("F", 12),

    # Thép tăng cường (Rows 13-17)
    "As_top_layer1": ("B", 13),
    "As_top_layer2": ("B", 14),
    "As_top_layer3": ("B", 15),
    "As_top_layer4": ("B", 16),
    "As_top_layer5": ("B", 17),

    # Thép tăng cường dưới (Rows 18-22)
    "As_bot_layer1": ("B", 18),
    "As_bot_layer2": ("B", 19),
    "As_bot_layer3": ("B", 20),
    "As_bot_layer4": ("B", 21),
    "As_bot_layer5": ("B", 22),

    # Giật mép (Row 23)
    "giat_mep_tren": ("B", 23),

    # Thép đai (Row 26)
    "stirrup": ("B", 26),             # Thép đai
    "stirrup_inner": ("B", 27),      # Đai trong
}

# Cách định dạng giá trị thanh thép
# "3T20" = 3 thanh đường kính 20mm
# "2T20+1T18" = 2 thanh T20 + 1 thanh T18


class BeamWriter:
    """Writer class cho Dầm BTCT"""

    def __init__(self, template_path: str = DCE_BEAM_TEMPLATE):
        self.template_path = Path(template_path)
        self.data: Dict = {}
        self.sheet_name = ACTIVE_SHEET

    def load_template(self) -> bool:
        """Load Excel template"""
        if not self.template_path.exists():
            print(f"ERROR: Template not found: {self.template_path}")
            return False

        try:
            self.wb = load_workbook(self.template_path, keep_vba=True)
            return True
        except Exception as e:
            print(f"ERROR: Cannot load template: {e}")
            return False

    def format_bar_string(self, n: int, dia: int) -> str:
        """Format thanh thanh thanh: 3, 20 -> '3T20'"""
        return f"{n}T{dia}"

    def format_bar_string_v2(self, n: int, dia: int, extra_n: int = 0, extra_dia: int = 0) -> str:
        """
        Format thanh thanh thanh với thanh extra:
        3, 20, 1, 18 -> '3T20+1T18'
        """
        main = f"{n}T{dia}"
        if extra_n > 0:
            main += f"+{extra_n}T{extra_dia}"
        return main

    def parse_bar_string(self, bar_str: str) -> Dict:
        """
        Parse string thanh thanh thanh, vi du:
        "3T20" -> {"n": 3, "dia": 20}
        "3T20+1T18" -> {"n": 3, "dia": 20, "extra_n": 1, "extra_dia": 18}
        """
        import re

        result = {"n": 0, "dia": 0}

        # Match pattern like "3T20" or "3phi20"
        match = re.match(r'(\d+)[TtPhi](\d+)', bar_str.strip())
        if match:
            result["n"] = int(match.group(1))
            result["dia"] = int(match.group(2))

        # Check for extra bar like "3T20+1T18"
        match_extra = re.search(r'\+(\d+)[TtPhi](\d+)', bar_str)
        if match_extra:
            result["extra_n"] = int(match_extra.group(1))
            result["extra_dia"] = int(match_extra.group(2))

        return result

    def format_stirrup_string(self, dia: int, s1: int, s2: int = 0) -> str:
        """
        Format thanh đai:
        8, 100, 200 -> '8-100/200'
        """
        if s2 > 0:
            return f"{dia}-{s1}/{s2}"
        return f"{dia}-{s1}"

    def parse_stirrup_string(self, stirrup_str: str) -> Dict:
        """
        Parse string thanh đai, vi du:
        "8-100/200" -> {"dia": 8, "s1": 100, "s2": 200}
        "8-100" -> {"dia": 8, "s1": 100, "s2": 0}
        """
        import re

        result = {"dia": 8, "s1": 100, "s2": 0}

        # Match pattern like "8-100/200" or "a8a100/200"
        match = re.match(r'?(\d+)-(\d+)/?(\d*)', stirrup_str.strip())
        if match:
            result["dia"] = int(match.group(1))
            result["s1"] = int(match.group(2))
            if match.group(3):
                result["s2"] = int(match.group(3))

        return result

    def set_value(self, field: str, value) -> bool:
        """Set value vao cell theo mapping"""
        if field not in CELL_MAPPING:
            print(f"WARNING: Unknown field '{field}'")
            return False

        col, row = CELL_MAPPING[field]

        try:
            ws = self.wb[self.sheet_name]
            cell_ref = f"{col}{row}"
            ws[cell_ref] = value
            return True
        except Exception as e:
            print(f"ERROR: Cannot set {field} -> {col}{row}: {e}")
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
        success = True

        # Write simple fields
        simple_fields = [
            ("beam_name", "beam_name"),
            ("b", "b"),
            ("h", "h"),
            ("so_cau_kien", "so_cau_kien"),
            ("cao_trinh", "cao_trinh"),
            ("h_san", "h_san"),
            ("L_ngan", "L_ngan"),
        ]

        for field, data_key in simple_fields:
            if data_key in self.data:
                if not self.set_value(field, self.data[data_key]):
                    success = False

        # Write structured rebar - top
        if "rebar_top" in self.data:
            rebar = self.data["rebar_top"]
            if isinstance(rebar, dict):
                # Single position
                if "n" in rebar and "dia" in rebar:
                    self.set_value("As_top_gocitrai",
                                  self.format_bar_string(rebar["n"], rebar["dia"]))
            elif isinstance(rebar, list):
                # Multiple positions
                positions = ["As_top_gocitrai", "As_top_nhip1", "As_top_nhip2",
                           "As_top_nhip3", "As_top_gociphai"]
                for i, bar in enumerate(rebar):
                    if i < len(positions) and isinstance(bar, dict):
                        if "n" in bar and "dia" in bar:
                            self.set_value(positions[i],
                                          self.format_bar_string(bar["n"], bar["dia"]))

        # Write structured rebar - bottom
        if "rebar_bottom" in self.data:
            rebar = self.data["rebar_bottom"]
            if isinstance(rebar, dict):
                if "n" in rebar and "dia" in rebar:
                    self.set_value("As_bot_gocitrai",
                                  self.format_bar_string(rebar["n"], rebar["dia"]))
            elif isinstance(rebar, list):
                positions = ["As_bot_gocitrai", "As_bot_nhip1", "As_bot_nhip2",
                           "As_bot_nhip3", "As_bot_gociphai"]
                for i, bar in enumerate(rebar):
                    if i < len(positions) and isinstance(bar, dict):
                        if "n" in bar and "dia" in bar:
                            self.set_value(positions[i],
                                          self.format_bar_string(bar["n"], bar["dia"]))

        # Write stirrup
        if "stirrup" in self.data:
            stirrup = self.data["stirrup"]
            if isinstance(stirrup, dict):
                dia = stirrup.get("dia", 8)
                s1 = stirrup.get("s1", 100)
                s2 = stirrup.get("s2", 0)
                self.set_value("stirrup", self.format_stirrup_string(dia, s1, s2))
            elif isinstance(stirrup, str):
                self.set_value("stirrup", stirrup)

        return success

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
    parser = argparse.ArgumentParser(description="Ghi data dam BTCT vao Excel DCE Pro")
    parser.add_argument("--input", "-i", required=True, help="Input JSON file")
    parser.add_argument("--output", "-o", help="Output Excel file (default: auto)")

    args = parser.parse_args()

    # Load data
    writer = BeamWriter()
    if not writer.load_from_json(args.input):
        sys.exit(1)

    # Generate output path
    if args.output:
        output_path = args.output
    else:
        input_path = Path(args.input)
        output_path = str(input_path.parent / f"DCE_{input_path.stem}_output.xlsm")

    # Write and save
    if writer.write_and_save(writer.data, output_path):
        print(f"\nOutput: {output_path}")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
