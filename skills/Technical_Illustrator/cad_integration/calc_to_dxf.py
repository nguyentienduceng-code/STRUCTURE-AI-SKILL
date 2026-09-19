# -*- coding: utf-8 -*-
"""
calc_to_dxf.py - Tich hop Calculator JSON sang DXF Generator

Tich hop giua:
- Structural_Design_Engineer/scripts/calc_rc_section.py (BTCT)
- Structural_Design_Engineer/scripts/calc_steel_beam.py (Thep)
- dce_dxf_generator.py (DCE Pro DXF)

Su dung:
    from calc_to_dxf import RCCalculatorToDXF, SteelCalculatorToDXF

    # Tu RC Beam Calculator
    calc_result = {
        "section": "bxh = 300x600 mm",
        "concrete": "B25",
        "As_chon_mm2": 1500.0,
        "mu_percent": 0.83,
        ...
    }
    dxf = RCCalculatorToDXF(calc_result)
    dxf.generate("output/DA01_MC-D1_01.dxf")

Author: AI Assistant
Version: 1.0.0
"""

import sys
import os
import json
import math
import re

# Setup UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

try:
    import ezdxf
    HAS_EZDXF = True
except ImportError:
    HAS_EZDXF = False
    print("[WARN] ezdxf not installed. Install with: pip install ezdxf")


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def parse_section_size(section_str: str) -> dict:
    """
    Parse section string nhu "bxh = 300x600 mm" -> {b: 300, h: 600}.

    Args:
        section_str: String kich thuoc, VD: "bxh = 300x600 mm"

    Returns:
        Dict with b, h values
    """
    # Tim pattern "300x600" hoac "300 x 600"
    pattern = r'(\d+)\s*[xX]\s*(\d+)'
    match = re.search(pattern, section_str)
    if match:
        return {
            'b': int(match.group(1)),
            'h': int(match.group(2))
        }
    return {'b': 300, 'h': 600}


def calculate_bar_layout(As_needed: float, bar_dia: float) -> dict:
    """
    Tinh toan bo tri cot thep.

    Args:
        As_needed: Dien tich thep yeu cau (mm2)
        bar_dia: Duong kinh thanh thep (mm)

    Returns:
        Dict with n_bars, As_provided, spacing
    """
    A_bar = math.pi * bar_dia ** 2 / 4
    n_bars = max(2, math.ceil(As_needed / A_bar))
    As_provided = n_bars * A_bar

    return {
        'n_bars': n_bars,
        'bar_dia': bar_dia,
        'As_provided': round(As_provided, 1),
        'As_needed': round(As_needed, 1)
    }


def bar_string(n: int, dia: int) -> str:
    """Tao string nhu "3D22"."""
    return f"{n}D{dia}"


# =============================================================================
# RC BEAM CALCULATOR -> DXF
# =============================================================================

class RCCalculatorToDXF:
    """
    Chuyen doi ket qua tu RC Beam Calculator sang DXF.

    Su dung:
        calc_result = calc_rc_beam(...)  # Tu calc_rc_section.py
        dxf = RCCalculatorToDXF(calc_result)
        dxf.generate("output/beam.dxf")
    """

    def __init__(self, calc_data: dict):
        """
        Khoi tao voi du lieu tu calculator.

        Args:
            calc_data: Dict tu calc_rc_beam()
        """
        self.data = calc_data

        # Parse section
        section = parse_section_size(calc_data.get('section', '300x600'))
        self.b = section['b']
        self.h = section['h']
        self.h0 = calc_data.get('h0_mm', self.h - 40)
        self.a = self.h - self.h0

        # Material
        self.concrete = calc_data.get('concrete', 'B25')
        self.rebar = calc_data.get('rebar', 'CB400-V')

        # Reinforcement
        self.As_chon = calc_data.get('As_chon_mm2', 0)
        self.mu_percent = calc_data.get('mu_percent', 0)

        # Stirrups
        self.stirrup_desc = calc_data.get('stirrup', '2D10@150')

        # Create document
        self.doc = None
        self.msp = None

    def setup_document(self):
        """Thiet lap tai lieu DXF."""
        if not HAS_EZDXF:
            raise RuntimeError("ezdxf not installed")

        self.doc = ezdxf.new('R2018')
        self.msp = self.doc.modelspace()

        # Create layers
        self._setup_layers()

        # Create text styles
        self._setup_text_styles()

        return self

    def _setup_layers(self):
        """Tao layers theo DCE Pro."""
        layers = {
            'DCE_BaoBeTong': (4, 'Continuous'),   # Magenta - Be tong
            'DCE_ThepChu': (1, 'Continuous'),      # Red - Thep chu
            'DCE_ThepDai': (220, 'Continuous'),    # Brown - Thep dai
            'DCE_Truc': (8, 'DASHDOT2_DBIM'),      # Gray - Truc
            'DCE_Dim': (254, 'Continuous'),        # Dimension
            'DCE_Hatch': (8, 'Continuous'),        # Hatch
            'Dce_text': (7, 'Continuous'),         # White - Text
            'DCE_Symbol': (5, 'Continuous'),        # Blue - Symbol
        }

        for name, (color, ltype) in layers.items():
            try:
                self.doc.layers.add(name=name, color=color)
            except:
                pass

    def _setup_text_styles(self):
        """Tao text styles."""
        try:
            self.doc.styles.new("Dce_Text", font="arial.ttf")
        except:
            pass

    def generate(self, output_path: str, scale: str = "1:20") -> str:
        """
        Sinh DXF tu du lieu calculator.

        Args:
            output_path: Duong dan xuat file
            scale: Ty le ban ve

        Returns:
            Duong dan file da tao
        """
        self.setup_document()

        # Scale factor (ve theo mm)
        sf = 1.0

        # Origin
        ox, oy = 100, 100

        # Ve mat cat dam
        self._draw_beam_section(ox, oy, sf)

        # Ve kich thuoc
        self._draw_dimensions(ox, oy, sf)

        # Ve text ghi chu
        self._draw_annotations(ox, oy, sf)

        # Ve title block
        self._draw_title_block(ox, oy, sf, scale)

        # Save
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        self.doc.saveas(output_path)
        print(f"[OK] Da tao DXF: {output_path}")

        return output_path

    def _draw_beam_section(self, ox: float, oy: float, sf: float):
        """Ve mat cat dam."""
        b, h = self.b * sf, self.h * sf

        # Concrete outline
        self.msp.add_lwpolyline([
            (ox, oy),
            (ox + b, oy),
            (ox + b, oy + h),
            (ox, oy + h),
            (ox, oy)
        ], dxfattribs={'layer': 'DCE_BaoBeTong'})

        # Hatch pattern (simple)
        self.msp.add_hatch(
            color=8,
            dxfattribs={'layer': 'DCE_Hatch'}
        )

        # Calculate rebar positions
        # Gia dinh 2 thanh ke + 3 thanh am
        top_bars = 2
        bot_bars = 3
        bar_dia = 22  # Mac dinh

        # Top bars (compression)
        top_spacing = b / (top_bars + 1)
        for i in range(top_bars):
            x = ox + top_spacing * (i + 1)
            y = oy + h - self.a * sf - bar_dia * sf / 2
            self.msp.add_circle(
                (x, y),
                bar_dia * sf / 2,
                dxfattribs={'layer': 'DCE_ThepChu'}
            )

        # Bottom bars (tension)
        bot_spacing = b / (bot_bars + 1)
        for i in range(bot_bars):
            x = ox + bot_spacing * (i + 1)
            y = oy + self.a * sf + bar_dia * sf / 2
            self.msp.add_circle(
                (x, y),
                bar_dia * sf / 2,
                dxfattribs={'layer': 'DCE_ThepChu'}
            )

        # Stirrups (vertical lines)
        stirrup_spacing = 150 * sf  # mm
        n_stirrups = int(h / stirrup_spacing)
        for i in range(n_stirrups):
            y1 = oy + i * stirrup_spacing + 5
            y2 = y1 + 3
            self.msp.add_line(
                (ox + self.a * sf, y1),
                (ox + b - self.a * sf, y2),
                dxfattribs={'layer': 'DCE_ThepDai'}
            )

    def _draw_dimensions(self, ox: float, oy: float, sf: float):
        """Ve cac duong kich thuoc."""
        b, h = self.b * sf, self.h * sf

        # Width dimension
        text_w = f"b={self.b}"
        self.msp.add_linear_dim(
            base=(ox, oy - 40),
            p1=(ox, oy),
            p2=(ox + b, oy),
            text=text_w,
            dxfattribs={'layer': 'DCE_Dim', 'dimstyle': 'Standard'}
        )

        # Height dimension
        text_h = f"h={self.h}"
        self.msp.add_linear_dim(
            base=(ox - 50, oy),
            p1=(ox, oy),
            p2=(ox, oy + h),
            text=text_h,
            angle=90,
            dxfattribs={'layer': 'DCE_Dim', 'dimstyle': 'Standard'}
        )

    def _draw_annotations(self, ox: float, oy: float, sf: float):
        """Ve text ghi chu ky thuat."""
        b, h = self.b * sf, self.h * sf

        # Title
        self.msp.add_text(
            f"DAM BTCT - {self.b}x{self.h}",
            height=8,
            dxfattribs={'layer': 'Dce_text', 'style': 'Dce_Text'}
        ).set_placement((ox + b/2, oy + h + 40))

        # Material info
        self.msp.add_text(
            f"Be tong: {self.concrete} | Thep: {self.rebar}",
            height=4,
            dxfattribs={'layer': 'Dce_text', 'style': 'Dce_Text'}
        ).set_placement((ox + b/2, oy + h + 25))

        # Reinforcement
        As_text = f"As = {self.As_chon:.0f} mm2" if self.As_chon else ""
        mu_text = f"mu = {self.mu_percent:.2f}%" if self.mu_percent else ""
        self.msp.add_text(
            f"{As_text} | {mu_text}",
            height=3,
            dxfattribs={'layer': 'Dce_text', 'style': 'Dce_Text'}
        ).set_placement((ox + b/2, oy + h + 15))

        # Rebar notation
        self.msp.add_text(
            "2D22",
            height=4,
            dxfattribs={'layer': 'DCE_ThepChu', 'style': 'Dce_Text'}
        ).set_placement((ox + b + 30, oy + h - 50))

        self.msp.add_text(
            "3D22",
            height=4,
            dxfattribs={'layer': 'DCE_ThepChu', 'style': 'Dce_Text'}
        ).set_placement((ox + b + 30, oy + 50))

    def _draw_title_block(self, ox: float, oy: float, sf: float, scale: str):
        """Ve title block (don gian)."""
        b, h = self.b * sf, self.h * sf

        # Title block position (bottom right)
        tb_x = ox
        tb_y = oy - 120
        tb_w = 350
        tb_h = 80

        # Border
        self.msp.add_lwpolyline([
            (tb_x, tb_y),
            (tb_x + tb_w, tb_y),
            (tb_x + tb_w, tb_y + tb_h),
            (tb_x, tb_y + tb_h),
            (tb_x, tb_y)
        ], dxfattribs={'layer': 'DCE_Block'})

        # Header line
        self.msp.add_line(
            (tb_x, tb_y + tb_h - 20),
            (tb_x + tb_w, tb_y + tb_h - 20),
            dxfattribs={'layer': 'DCE_Block'}
        )

        # Project name
        self.msp.add_text(
            "DU AN: [TEN DU AN]",
            height=4,
            dxfattribs={'layer': 'Dce_text', 'style': 'Dce_Text'}
        ).set_placement((tb_x + 10, tb_y + tb_h - 15))

        # Drawing title
        self.msp.add_text(
            f"MAT CAT DAM {self.b}x{self.h}",
            height=5,
            dxfattribs={'layer': 'Dce_text', 'style': 'Dce_Text'}
        ).set_placement((tb_x + tb_w/2, tb_y + tb_h/2))

        # Scale & Date
        self.msp.add_text(
            f"Ty le: {scale} | Ngay: 2026",
            height=3,
            dxfattribs={'layer': 'Dce_text', 'style': 'Dce_Text'}
        ).set_placement((tb_x + 10, tb_y + 10))


# =============================================================================
# STEEL BEAM CALCULATOR -> DXF
# =============================================================================

class SteelCalculatorToDXF:
    """
    Chuyen doi ket qua tu Steel Beam Calculator sang DXF.

    Su dung:
        calc_result = calc_steel_beam(...)  # Tu calc_steel_beam.py
        dxf = SteelCalculatorToDXF(calc_result)
        dxf.generate("output/steel_beam.dxf")
    """

    def __init__(self, calc_data: dict):
        """Khoi tao voi du lieu tu calculator."""
        self.data = calc_data

        # Parse section
        section_str = calc_data.get('section', 'I400x200x8x13')
        pattern = r'I(\d+)x(\d+)x(\d+)x(\d+)'
        match = re.search(pattern, section_str)
        if match:
            self.h = int(match.group(1))
            self.b = int(match.group(2))
            self.tw = int(match.group(3))
            self.tf = int(match.group(4))
        else:
            self.h, self.b, self.tw, self.tf = 400, 200, 8, 13

        self.fy = calc_data.get('fy', 345)
        self.steel_grade = "SS400"  # Mac dinh

        self.doc = None
        self.msp = None

    def setup_document(self):
        """Thiet lap tai lieu DXF."""
        if not HAS_EZDXF:
            raise RuntimeError("ezdxf not installed")

        self.doc = ezdxf.new('R2018')
        self.msp = self.doc.modelspace()

        # Create layers
        layers = {
            'DCE_Beam': (2, 'Continuous'),      # Yellow - Dam thep
            'DCE_ThepChu': (1, 'Continuous'),   # Red - Thep
            'DCE_Truc': (8, 'DASHDOT2_DBIM'),   # Gray - Truc
            'DCE_Dim': (254, 'Continuous'),     # Dimension
            'Dce_text': (7, 'Continuous'),       # White - Text
        }

        for name, (color, ltype) in layers.items():
            try:
                self.doc.layers.add(name=name, color=color)
            except:
                pass

        # Text styles
        try:
            self.doc.styles.new("Dce_Text", font="arial.ttf")
        except:
            pass

        return self

    def generate(self, output_path: str, scale: str = "1:10") -> str:
        """Sinh DXF tu du lieu calculator."""
        self.setup_document()

        sf = 1.0  # Scale factor
        ox, oy = 100, 100

        # Draw I-beam section
        self._draw_i_beam(ox, oy, sf)

        # Draw dimensions
        self._draw_dimensions(ox, oy, sf)

        # Draw annotations
        self._draw_annotations(ox, oy, sf)

        # Draw title block
        self._draw_title_block(ox, oy, sf, scale)

        # Save
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        self.doc.saveas(output_path)
        print(f"[OK] Da tao DXF: {output_path}")

        return output_path

    def _draw_i_beam(self, ox: float, oy: float, sf: float):
        """Ve mat cat dam thep I."""
        h, b, tw, tf = self.h * sf, self.b * sf, self.tw * sf, self.tf * sf

        # Top flange
        self.msp.add_lwpolyline([
            (ox, oy + h - tf),
            (ox + b, oy + h - tf),
            (ox + b, oy + h),
            (ox, oy + h),
            (ox, oy + h - tf)
        ], dxfattribs={'layer': 'DCE_Beam'})

        # Web
        self.msp.add_lwpolyline([
            (ox + b/2 - tw/2, oy),
            (ox + b/2 + tw/2, oy),
            (ox + b/2 + tw/2, oy + h - tf),
            (ox + b/2 - tw/2, oy + h - tf),
            (ox + b/2 - tw/2, oy)
        ], dxfattribs={'layer': 'DCE_Beam'})

        # Bottom flange
        self.msp.add_lwpolyline([
            (ox, oy),
            (ox + b, oy),
            (ox + b, oy + tf),
            (ox, oy + tf),
            (ox, oy)
        ], dxfattribs={'layer': 'DCE_Beam'})

        # Center line
        self.msp.add_line(
            (ox + b/2, oy - 30),
            (ox + b/2, oy + h + 30),
            dxfattribs={'layer': 'DCE_Truc'}
        )

    def _draw_dimensions(self, ox: float, oy: float, sf: float):
        """Ve cac duong kich thuoc."""
        h, b, tw, tf = self.h * sf, self.b * sf, self.tw * sf, self.tf * sf

        # Height
        self.msp.add_linear_dim(
            base=(ox - 50, oy),
            p1=(ox, oy),
            p2=(ox, oy + h),
            text=f"h={self.h}",
            angle=90,
            dxfattribs={'layer': 'DCE_Dim', 'dimstyle': 'Standard'}
        )

        # Flange width
        self.msp.add_linear_dim(
            base=(ox, oy - 40),
            p1=(ox, oy),
            p2=(ox + b, oy),
            text=f"b={self.b}",
            dxfattribs={'layer': 'DCE_Dim', 'dimstyle': 'Standard'}
        )

        # Web thickness
        self.msp.add_linear_dim(
            base=(ox + b/2, oy + h/2),
            p1=(ox + b/2 - tw/2, oy + h/2),
            p2=(ox + b/2 + tw/2, oy + h/2),
            text=f"tw={self.tw}",
            dxfattribs={'layer': 'DCE_Dim', 'dimstyle': 'Standard'}
        )

        # Flange thickness
        self.msp.add_linear_dim(
            base=(ox + b + 40, oy + h),
            p1=(ox, oy + h),
            p2=(ox, oy + h - tf),
            text=f"tf={self.tf}",
            angle=90,
            dxfattribs={'layer': 'DCE_Dim', 'dimstyle': 'Standard'}
        )

    def _draw_annotations(self, ox: float, oy: float, sf: float):
        """Ve text ghi chu."""
        h, b = self.h * sf, self.b * sf

        # Title
        self.msp.add_text(
            f"DAM THEP I-{self.h}x{self.b}x{self.tw}x{self.tf}",
            height=8,
            dxfattribs={'layer': 'Dce_text', 'style': 'Dce_Text'}
        ).set_placement((ox + b/2, oy + h + 40))

        # Steel grade
        self.msp.add_text(
            f"Vat lieu: fy = {self.fy} MPa",
            height=4,
            dxfattribs={'layer': 'Dce_text', 'style': 'Dce_Text'}
        ).set_placement((ox + b/2, oy + h + 25))

    def _draw_title_block(self, ox: float, oy: float, sf: float, scale: str):
        """Ve title block."""
        h = self.h * sf

        tb_x, tb_y = ox, oy - 120
        tb_w, tb_h = 350, 80

        # Border
        self.msp.add_lwpolyline([
            (tb_x, tb_y),
            (tb_x + tb_w, tb_y),
            (tb_x + tb_w, tb_y + tb_h),
            (tb_x, tb_y + tb_h),
            (tb_x, tb_y)
        ], dxfattribs={'layer': 'DCE_Block'})

        # Header
        self.msp.add_line(
            (tb_x, tb_y + tb_h - 20),
            (tb_x + tb_w, tb_y + tb_h - 20),
            dxfattribs={'layer': 'DCE_Block'}
        )

        self.msp.add_text(
            f"MAT CAT DAM THEP I-{self.h}x{self.b}",
            height=5,
            dxfattribs={'layer': 'Dce_text', 'style': 'Dce_Text'}
        ).set_placement((tb_x + tb_w/2, tb_y + tb_h/2))


# =============================================================================
# BATCH PROCESSING
# =============================================================================

class BatchCalculatorToDXF:
    """
    Xu ly nhieu ket qua calculator cung luc.

    Su dung:
        batch = BatchCalculatorToDXF()
        batch.add_rc_beam(rc_result)
        batch.add_steel_beam(steel_result)
        batch.generate_all("output/")
    """

    def __init__(self):
        self.items = []

    def add_rc_beam(self, calc_data: dict, name: str = "RC_Beam"):
        """Them ket qua RC Beam."""
        self.items.append({
            'type': 'rc_beam',
            'data': calc_data,
            'name': name
        })

    def add_steel_beam(self, calc_data: dict, name: str = "Steel_Beam"):
        """Them ket qua Steel Beam."""
        self.items.append({
            'type': 'steel_beam',
            'data': calc_data,
            'name': name
        })

    def generate_all(self, output_dir: str) -> list:
        """Sinh tat ca cac DXF."""
        os.makedirs(output_dir, exist_ok=True)
        results = []

        for item in self.items:
            name = item['name']
            if item['type'] == 'rc_beam':
                dxf = RCCalculatorToDXF(item['data'])
                output_path = os.path.join(output_dir, f"{name}.dxf")
                dxf.generate(output_path)
                results.append(output_path)
            elif item['type'] == 'steel_beam':
                dxf = SteelCalculatorToDXF(item['data'])
                output_path = os.path.join(output_dir, f"{name}.dxf")
                dxf.generate(output_path)
                results.append(output_path)

        return results


# =============================================================================
# MAIN - TEST
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("CALC TO DXF - Integration Test")
    print("=" * 60)

    # Import calculators
    sys.path.insert(0, '../Structural_Design_Engineer/scripts')

    try:
        from calc_rc_section import calc_rc_beam
        print("[OK] Da load calc_rc_section")
    except ImportError as e:
        print(f"[WARN] Khong load duoc calc_rc_section: {e}")
        calc_rc_beam = None

    try:
        from calc_steel_beam import calc_steel_beam
        print("[OK] Da load calc_steel_beam")
    except ImportError as e:
        print(f"[WARN] Khong load duoc calc_steel_beam: {e}")
        calc_steel_beam = None

    # Test RC Beam
    if calc_rc_beam:
        print("\n--- Testing RC Beam Calculator -> DXF ---")
        rc_result = calc_rc_beam(
            b=300, h=600, a=40,
            concrete="B25", rebar="CB400-V",
            M_ed=250, V_ed=120,
            stirrup_dia=8, stirrup_legs=2, stirrup_spacing=150
        )

        print(f"Calculator result: {rc_result.get('section')}")
        print(f"As_chon: {rc_result.get('As_chon_mm2')} mm2")

        # Generate DXF
        output_dir = "G:/My Drive/Google AI Studio/output"
        os.makedirs(output_dir, exist_ok=True)

        dxf = RCCalculatorToDXF(rc_result)
        dxf_path = dxf.generate(os.path.join(output_dir, "RC_Beam_Test.dxf"))
        print(f"DXF generated: {dxf_path}")

    # Test Steel Beam
    if calc_steel_beam:
        print("\n--- Testing Steel Beam Calculator -> DXF ---")
        steel_result = calc_steel_beam(
            h=400, b=200, tw=8, tf=13,
            M_ed=220, V_ed=150,
            fy=345, L_span=6000
        )

        print(f"Calculator result: {steel_result.get('section')}")
        print(f"M_c_Rd: {steel_result.get('M_c_rd_kNm')} kNm")

        dxf = SteelCalculatorToDXF(steel_result)
        dxf_path = dxf.generate(os.path.join(output_dir, "Steel_Beam_Test.dxf"))
        print(f"DXF generated: {dxf_path}")

    print("\n" + "=" * 60)
    print("[OK] Test hoan thanh!")
    print("=" * 60)
