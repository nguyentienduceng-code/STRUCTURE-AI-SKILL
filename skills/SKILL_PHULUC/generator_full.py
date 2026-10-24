"""
TMTT_Generator.py — Generator Thuyết minh Tính toán Kết cấu Đầy đủ

Tạo Thuyết minh Tính toán Kết cấu theo chuẩn của đơn vị tư vấn thiết kế.
Format chuẩn: 12 chương với PHỤ LỤC TÍNH TOÁN chi tiết.

Usage:
    python TMTT_Generator.py --input data.json --output TMTT.md
    python TMTT_Generator.py --input data.json --output TMTT.docx --format docx
"""

import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
import json
import argparse
import sys
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# =============================================================================
# TEMPLATE REGISTRY
# =============================================================================

TEMPLATE_DIR = Path(__file__).parent / "templates"

TEMPLATES = {
    "full": TEMPLATE_DIR / "TMTT_FULL.md",
    "partial_be": TEMPLATE_DIR / "PARTIAL_BE_TONG.md",
    "partial_thep": TEMPLATE_DIR / "PARTIAL_THEP.md",
}

# =============================================================================
# VALUE FORMATTERS
# =============================================================================

def fmt_number(val: float, decimals: int = 2) -> str:
    """Format số với số chữ số thập phân"""
    if val is None:
        return "-"
    return f"{val:.{decimals}f}"


def fmt_eta(val: float) -> str:
    """Format hệ số sử dụng η"""
    if val is None:
        return "-"
    return f"{val:.3f}"


def fmt_status(val: float, threshold: float = 1.0) -> str:
    """Format trạng thái"""
    if val is None:
        return "CHƯA TÍNH"
    if val <= threshold:
        return "ĐẠT"
    return "KHÔNG ĐẠT"


def fmt_bar_string(n: int, dia: int) -> str:
    """Format chuỗi thanh thép: 3, 20 -> '3T20'"""
    return f"{n}Φ{dia}"


def fmt_stirrup_string(dia: int, s1: int, s2: int = 0) -> str:
    """Format chuỗi thanh đai: 8, 100, 200 -> 'Φ8a100/200'"""
    if s2 > 0:
        return f"Φ{dia}a{s1}/{s2}"
    return f"Φ{dia}a{s1}"


# =============================================================================
# MATERIAL PROPERTIES DATABASE
# =============================================================================

CONCRETE_GRADES = {
    "B12.5": {"Rb": 7.5, "Rbt": 0.66, "Eb": 21500, "fc": 7.5, "fct": 0.66, "Ec": 21500, "class": 12.5},
    "B15":   {"Rb": 8.5, "Rbt": 0.75, "Eb": 24000, "fc": 8.5, "fct": 0.75, "Ec": 24000, "class": 15},
    "B20":   {"Rb": 11.5, "Rbt": 0.90, "Eb": 27500, "fc": 11.5, "fct": 0.90, "Ec": 27500, "class": 20},
    "B22.5": {"Rb": 13.0, "Rbt": 1.00, "Eb": 29000, "fc": 13.0, "fct": 1.00, "Ec": 29000, "class": 22.5},
    "B25":   {"Rb": 14.5, "Rbt": 1.05, "Eb": 30000, "fc": 14.5, "fct": 1.05, "Ec": 30000, "class": 25},
    "B30":   {"Rb": 17.0, "Rbt": 1.15, "Eb": 32500, "fc": 17.0, "fct": 1.15, "Ec": 32500, "class": 30},
    "B35":   {"Rb": 19.5, "Rbt": 1.30, "Eb": 34500, "fc": 19.5, "fct": 1.30, "Ec": 34500, "class": 35},
    "B40":   {"Rb": 22.0, "Rbt": 1.40, "Eb": 36000, "fc": 22.0, "fct": 1.40, "Ec": 36000, "class": 40},
    "B45":   {"Rb": 25.0, "Rbt": 1.50, "Eb": 37000, "fc": 25.0, "fct": 1.50, "Ec": 37000, "class": 45},
    "B50":   {"Rb": 27.5, "Rbt": 1.60, "Eb": 38000, "fc": 27.5, "fct": 1.60, "Ec": 38000, "class": 50},
    "B55":   {"Rb": 30.0, "Rbt": 1.70, "Eb": 39000, "fc": 30.0, "fct": 1.70, "Ec": 39000, "class": 55},
    "B60":   {"Rb": 33.0, "Rbt": 1.80, "Eb": 39500, "fc": 33.0, "fct": 1.80, "Ec": 39500, "class": 60},
}

STEEL_GRADES_RC = {
    "CB240-T": {"Rs": 210, "Rsc": 210, "Rsw": 170, "Rk": 240, "Es": 200000, "fy": 210, "fyk": 240},
    "CB300-T": {"Rs": 260, "Rsc": 260, "Rsw": 210, "Rk": 300, "Es": 200000, "fy": 260, "fyk": 300},
    "CB300-V": {"Rs": 260, "Rsc": 260, "Rsw": 210, "Rk": 300, "Es": 200000, "fy": 260, "fyk": 300},
    "CB400-V": {"Rs": 350, "Rsc": 350, "Rsw": 280, "Rk": 400, "Es": 200000, "fy": 350, "fyk": 400},
    "CB500-V": {"Rs": 435, "Rsc": 400, "Rsw": 300, "Rk": 500, "Es": 200000, "fy": 435, "fyk": 500},
    # Alias tuong thich nguoc
    "CB240":   {"Rs": 210, "Rsc": 210, "Rsw": 170, "Rk": 240, "Es": 200000, "fy": 210, "fyk": 240},
    "CB300":   {"Rs": 260, "Rsc": 260, "Rsw": 210, "Rk": 300, "Es": 200000, "fy": 260, "fyk": 300},
    "CB400":   {"Rs": 350, "Rsc": 350, "Rsw": 280, "Rk": 400, "Es": 200000, "fy": 350, "fyk": 400},
    "CB500":   {"Rs": 435, "Rsc": 400, "Rsw": 300, "Rk": 500, "Es": 200000, "fy": 435, "fyk": 500},
}

STEEL_GRADES_STEEL = {
    "SS400": {"fy": 235, "fu": 400},
    "SM490": {"fy": 315, "fu": 490},
    "Q235": {"fy": 235, "fu": 370},
    "Q345": {"fy": 345, "fu": 470},
}

REBAR_AREAS = {
    6: 28.3, 8: 50.3, 10: 78.5, 12: 113.1,
    14: 153.9, 16: 201.1, 18: 254.5, 20: 314.2,
    22: 380.1, 25: 490.9, 28: 615.8, 30: 706.9,
    32: 804.2
}

# =============================================================================
# MARKUP ENGINE
# =============================================================================

class MarkupEngine:
    """Engine xử lý template markup đặc biệt"""

    @staticmethod
    def process_foreach(content: str, data: Dict) -> str:
        """Xử lý {{#each key}}...{{/each}} blocks"""
        pattern = r'\{\{#each\s+(\w+)\}\}(.*?)\{\{/each\}\}'

        while True:
            match = re.search(pattern, content, re.DOTALL)
            if not match:
                break

            key = match.group(1)
            block = match.group(2)

            if key in data and isinstance(data[key], list):
                items = data[key]
                rendered = ""
                for i, item in enumerate(items):
                    # Process item with {{key}} placeholders
                    item_content = block
                    for item_key, item_val in item.items():
                        item_content = item_content.replace(f'{{{{{item_key}}}}}', str(item_val))
                    # Add index
                    item_content = item_content.replace('{{stt}}', str(i + 1))
                    item_content = item_content.replace('{{order}}', str(i + 1))
                    rendered += item_content

                content = content[:match.start()] + rendered + content[match.end():]
            else:
                content = content[:match.start()] + content[match.end():]

        return content

    @staticmethod
    def process_if(content: str, data: Dict) -> str:
        """Xử lý {{#if key}}...{{/if}} blocks"""
        pattern = r'\{\{#if\s+(\w+)\}\}(.*?)\{\{/if\}\}'

        while True:
            match = re.search(pattern, content, re.DOTALL)
            if not match:
                break

            key = match.group(1)
            block = match.group(2)

            if key in data and data[key]:
                content = content[:match.start()] + block + content[match.end():]
            else:
                content = content[:match.start()] + content[match.end():]

        return content

    @staticmethod
    def process_placeholders(content: str, data: Dict) -> str:
        """Xử lý {{key}} placeholders"""
        for key, value in data.items():
            if isinstance(value, (int, float)):
                content = content.replace(f'{{{{{key}}}}}', fmt_number(value))
            elif value is not None:
                content = content.replace(f'{{{{{key}}}}}', str(value))

        return content


# =============================================================================
# MAIN GENERATOR
# =============================================================================

class TMTTGenerator:
    """Generator class cho Thuyết minh Tính toán Kết cấu"""

    def __init__(self, template_type: str = "full"):
        if template_type not in TEMPLATES:
            raise ValueError(f"Unknown template type: {template_type}")

        self.type = template_type
        self.template_path = TEMPLATES[template_type]
        self.data: Dict[str, Any] = {}
        self.markup = MarkupEngine()

    def load_template(self) -> str:
        """Load template file"""
        with open(self.template_path, 'r', encoding='utf-8') as f:
            return f.read()

    def load_input(self, input_path: str) -> bool:
        """Load input JSON"""
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            return True
        except Exception as e:
            print(f"ERROR: Cannot load input: {e}")
            return False

    def load_from_dict(self, data: Dict):
        """Load from dictionary"""
        self.data = data

    def _preprocess_data(self):
        """Pre-calculate và bổ sung data"""
        now = datetime.now()

        # Basic info
        self.data.setdefault('project_name', self.data.get('project_code', 'Dự án'))
        self.data.setdefault('calc_date', now.strftime('%d/%m/%Y'))

        # Material properties
        if 'concrete_grade' in self.data and self.data['concrete_grade'] in CONCRETE_GRADES:
            props = CONCRETE_GRADES[self.data['concrete_grade']]
            self.data.setdefault('fc', props['fc'])
            self.data.setdefault('fct', props['fct'])
            self.data.setdefault('Ec', props['Ec'])
            self.data.setdefault('concrete_class', props['class'])

        if 'steel_grade_rc' in self.data and self.data['steel_grade_rc'] in STEEL_GRADES_RC:
            props = STEEL_GRADES_RC[self.data['steel_grade_rc']]
            self.data.setdefault('fy', props['fy'])

        # Placeholder cho phần trống
        self.data.setdefault('noi_dung_ve_net', '')
        self.data.setdefault('noi_dung_chong_tham', '')
        self.data.setdefault('noi_dung_tai_trong_gio', '')
        self.data.setdefault('to_hop_tai_trong_tcvn', '')
        self.data.setdefault('to_hop_tai_trong_sls', '')
        self.data.setdefault('to_hop_tai_trong_asce', '')
        self.data.setdefault('vat_lieu_be_tong', '')
        self.data.setdefault('vat_lieu_thep_can', '')
        self.data.setdefault('lop_be_tong_bao_ve', '')

        # Calculator info
        self.data.setdefault('calculator', '')
        self.data.setdefault('reviewer', '')
        self.data.setdefault('approver', '')
        self.data.setdefault('nguoi_tinh', '')
        self.data.setdefault('nguoi_kiem_tra', '')
        self.data.setdefault('nguoi_duyet', '')

    def fill_template(self) -> str:
        """Fill template với data"""
        template = self.load_template()
        self._preprocess_data()

        # Process markup
        content = self.markup.process_foreach(template, self.data)
        content = self.markup.process_if(content, self.data)
        content = self.markup.process_placeholders(content, self.data)

        # Clean up remaining placeholders
        content = re.sub(r'\{\{#\w+\s+\w+\}\}', '', content)
        content = re.sub(r'\{\{\/\w+\}\}', '', content)
        content = re.sub(r'\{\{\w+\}\}', '', content)

        return content

    def save(self, output_path: str) -> bool:
        """Save to file"""
        try:
            content = self.fill_template()
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"SUCCESS: TMTT saved to {output_path}")
            return True
        except Exception as e:
            print(f"ERROR: Cannot save: {e}")
            return False

    def generate(self, data: Dict, output_path: str) -> bool:
        """Convenience method"""
        self.load_from_dict(data)
        return self.save(output_path)


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Generator Thuyết minh Tính toán Kết cấu Đầy đủ"
    )
    parser.add_argument("--input", "-i", required=True,
                       help="Input JSON file")
    parser.add_argument("--output", "-o", required=True,
                       help="Output markdown file")
    parser.add_argument("--type", "-t", default="full",
                       choices=["full", "partial_be", "partial_thep"],
                       help="Template type")

    args = parser.parse_args()

    generator = TMTTGenerator(args.type)
    if not generator.load_input(args.input):
        sys.exit(1)

    if generator.save(args.output):
        print(f"\nTMTT generated: {args.output}")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
