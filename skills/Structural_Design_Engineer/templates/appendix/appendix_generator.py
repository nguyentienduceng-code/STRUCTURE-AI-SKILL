"""
appendix_generator.py — Generator Phụ lục Tính toán Kết cấu

Tạo phụ lục tính toán đầy đủ theo chuẩn của đơn vị tư vấn thiết kế.

Usage:
    python appendix_generator.py --type beam_rc --input calc_result.json --output appendix.md
    python appendix_generator.py --type column_rc --input calc_result.json --output appendix.md
    python appendix_generator.py --type steel_beam --input calc_result.json --output appendix.md
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
from typing import Dict, Any, Optional

# =============================================================================
# TEMPLATE REGISTRY
# =============================================================================

TEMPLATE_DIR = Path(__file__).parent

TEMPLATES = {
    "beam_rc": TEMPLATE_DIR / "APPENDIX_BEAM_RC.md",
    "column_rc": TEMPLATE_DIR / "APPENDIX_COLUMN_RC.md",
    "steel_beam": TEMPLATE_DIR / "APPENDIX_STEEL_BEAM.md",
}

# =============================================================================
# VALUE FORMATTERS
# =============================================================================

def fmt_number(val: float, decimals: int = 2) -> str:
    """Format số với số chữ số thập phân"""
    if val is None:
        return "-"
    return f"{val:.{decimals}f}"


def fmt_int(val: int) -> str:
    """Format số nguyên"""
    if val is None:
        return "-"
    return str(int(val))


def fmt_eta(val: float) -> str:
    """Format hệ số sử dụng η"""
    if val is None:
        return "-"
    return f"{val:.3f}"


def fmt_status(val: float, threshold: float = 1.0) -> str:
    """Format trạng thái dựa trên ngưỡng"""
    if val is None:
        return "CHƯA TÍNH"
    if val <= threshold:
        return "ĐẠT"
    return "KHÔNG ĐẠT"


def fmt_bar_string(n: int, dia: int) -> str:
    """Format chuỗi thanh thép: 3, 20 -> '3T20'"""
    return f"{n}T{dia}"


def fmt_stirrup_string(dia: int, s1: int, s2: int = 0) -> str:
    """Format chuỗi thanh đai: 8, 100, 200 -> 'φ8a100/200'"""
    if s2 > 0:
        return f"φ{dia}a{s1}/{s2}"
    return f"φ{dia}a{s1}"


# =============================================================================
# MATERIAL PROPERTIES DATABASE
# =============================================================================

CONCRETE_GRADES = {
    "B15": {"fc": 8.5, "fct": 0.75, "Ec": 23000},
    "B20": {"fc": 11.5, "fct": 0.90, "Ec": 27000},
    "B25": {"fc": 14.5, "fct": 1.05, "Ec": 30000},
    "B30": {"fc": 17.0, "fct": 1.20, "Ec": 32500},
    "B35": {"fc": 19.5, "fct": 1.30, "Ec": 34500},
    "B40": {"fc": 22.0, "fct": 1.40, "Ec": 36000},
    "B45": {"fc": 25.0, "fct": 1.50, "Ec": 37500},
    "B50": {"fc": 27.5, "fct": 1.60, "Ec": 38500},
}

STEEL_GRADES = {
    "CB300": {"fy": 260, "fyk": 300, "Es": 210000},
    "CB400": {"fy": 340, "fyk": 400, "Es": 200000},
    "CB500": {"fy": 415, "fyk": 500, "Es": 200000},
}

STEEL_PIPES = {
    "SS400": {"fy": 235, "fu": 400},
    "SM490": {"fy": 315, "fu": 490},
    "Q235": {"fy": 235, "fu": 370},
    "Q345": {"fy": 345, "fu": 470},
}

# Rebar area table (mm²)
REBAR_AREAS = {
    6: 28.3, 8: 50.3, 10: 78.5, 12: 113.1,
    14: 153.9, 16: 201.1, 18: 254.5, 20: 314.2,
    22: 380.1, 25: 490.9, 28: 615.8, 30: 706.9,
    32: 804.2
}

# =============================================================================
# CALCULATION HELPERS
# =============================================================================

def calc_As_req(M: float, fy: float, z: float, gamma_s: float = 1.15) -> float:
    """Tính diện tích cốt thép yêu cầu"""
    return M * 1e6 / (fy / gamma_s * z)


def calc_z(d: float, a: float) -> float:
    """Tính cánh tay đòn nội lực"""
    return d - a / 2


def calc_alpha(As: float, fy: float, b: float, fc: float) -> float:
    """Tính hệ số α"""
    return As * fy / (b * fc)


def calc_x(alpha: float, d: float, beta1: float = 0.85) -> float:
    """Tính chiều cao vùng nén"""
    return alpha * d / beta1


def calc_check(As_req: float, As_prov: float) -> float:
    """Tính hệ số kiểm tra η"""
    return As_req / As_prov


def calc_rho(As: float, b: float, d: float) -> float:
    """Tính hàm lượng cốt thép (%)"""
    return As / (b * d) * 100


# =============================================================================
# TEMPLATE FILLER
# =============================================================================

class AppendixGenerator:
    """Generator class cho phụ lục tính toán"""

    def __init__(self, appendix_type: str):
        if appendix_type not in TEMPLATES:
            raise ValueError(f"Unknown appendix type: {appendix_type}")

        self.type = appendix_type
        self.template_path = TEMPLATES[appendix_type]
        self.data: Dict[str, Any] = {}

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

    def get_value(self, key: str, default: Any = None) -> Any:
        """Get value from data with dot notation support"""
        keys = key.split('.')
        val = self.data
        for k in keys:
            if isinstance(val, dict):
                val = val.get(k)
            else:
                return default
        return val if val is not None else default

    def fill_template(self) -> str:
        """Fill template with data"""
        template = self.load_template()

        # Pre-calculate values
        self._preprocess_data()

        # Replace placeholders
        result = template

        # Find all {{placeholder}} patterns
        for match in re.finditer(r'\{\{(\w+)\}\}', template):
            key = match.group(1)
            value = self.get_value(key, "")

            # Format based on key suffix
            if isinstance(value, float):
                if 'eta' in key.lower():
                    value = fmt_eta(value)
                elif 'M_' in key or 'V_' in key or 'N_' in key or 'f_' in key:
                    value = fmt_number(value, 2)
                elif 'A_' in key or 'z_' in key or 'x_' in key:
                    value = fmt_number(value, 1)
                else:
                    value = fmt_number(value, 2)
            elif isinstance(value, int):
                if 'n_' in key or 's_' in key or 'b_' in key or 'h_' in key or 'L_' in key:
                    value = fmt_int(value)
                else:
                    value = fmt_int(value)

            result = result.replace('{{' + key + '}}', str(value))

        return result

    def _preprocess_data(self):
        """Pre-calculate derived values"""
        # Calculate concrete properties if grade is provided
        concrete_grade = self.get_value('concrete_grade')
        if concrete_grade and concrete_grade in CONCRETE_GRADES:
            props = CONCRETE_GRADES[concrete_grade]
            self.data.setdefault('fc', props['fc'])
            self.data.setdefault('fct', props['fct'])
            self.data.setdefault('Ec', props['Ec'])

        # Calculate steel properties if grade is provided
        steel_grade = self.get_value('steel_grade')
        if steel_grade and steel_grade in STEEL_GRADES:
            props = STEEL_GRADES[steel_grade]
            self.data.setdefault('fy', props['fy'])
            self.data.setdefault('fyk', props['fyk'])
            self.data.setdefault('Es', props['Es'])

        # Calculate derived values
        b = self.get_value('b', 200)
        h = self.get_value('h', 400)
        d = self.get_value('d', h - 35)

        self.data.setdefault('b', b)
        self.data.setdefault('h', h)
        self.data.setdefault('d', d)
        self.data.setdefault('z_calc', d - 25)

        # Calculate A_s from rebar config
        if 'rebar_top' in self.data:
            rebar = self.data['rebar_top']
            if isinstance(rebar, dict) and 'n' in rebar and 'dia' in rebar:
                n, dia = rebar['n'], rebar['dia']
                area = REBAR_AREAS.get(dia, 0)
                self.data['As_prov'] = n * area
                self.data['rebar_top_str'] = fmt_bar_string(n, dia)

        if 'rebar_bottom' in self.data:
            rebar = self.data['rebar_bottom']
            if isinstance(rebar, dict) and 'n' in rebar and 'dia' in rebar:
                n, dia = rebar['n'], rebar['dia']
                area = REBAR_AREAS.get(dia, 0)
                self.data['As_prov_nhip1'] = n * area
                self.data['rebar_bot_str'] = fmt_bar_string(n, dia)

        # Calculate eta values
        M_req = self.get_value('M_req')
        M_prov = self.get_value('M_prov')
        if M_req and M_prov:
            self.data['eta_M'] = M_req / M_prov

        # Format stirrup string
        if 'stirrup' in self.data:
            stirrup = self.data['stirrup']
            if isinstance(stirrup, dict):
                self.data['stirrup_str'] = fmt_stirrup_string(
                    stirrup.get('dia', 8),
                    stirrup.get('s1', 100),
                    stirrup.get('s2', 200)
                )

        # Add date info
        now = datetime.now()
        self.data.setdefault('calc_date', now.strftime('%d/%m/%Y'))
        self.data.setdefault('project_name', self.data.get('project_code', 'Dự án'))

    def save(self, output_path: str) -> bool:
        """Save filled template to file"""
        try:
            content = self.fill_template()
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"SUCCESS: Appendix saved to {output_path}")
            return True
        except Exception as e:
            print(f"ERROR: Cannot save: {e}")
            return False

    def generate(self, data: Dict, output_path: str) -> bool:
        """Convenience method: load data and save"""
        self.load_from_dict(data)
        return self.save(output_path)


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Generator Phụ lục Tính toán Kết cấu"
    )
    parser.add_argument("--type", "-t", required=True,
                       choices=["beam_rc", "column_rc", "steel_beam"],
                       help="Loại phụ lục")
    parser.add_argument("--input", "-i",
                       help="Input JSON file (optional if using stdin)")
    parser.add_argument("--output", "-o", required=True,
                       help="Output markdown file")
    parser.add_argument("--pretty", "-p", action="store_true",
                       help="Pretty print JSON input (for testing)")

    args = parser.parse_args()

    # Load input
    if args.input:
        with open(args.input, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        # Read from stdin
        data = json.load(sys.stdin)

    # Generate
    generator = AppendixGenerator(args.type)
    if generator.generate(data, args.output):
        print(f"\nAppendix generated: {args.output}")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
