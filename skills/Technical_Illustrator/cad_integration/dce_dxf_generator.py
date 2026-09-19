# -*- coding: utf-8 -*-
"""
dce_dxf_generator.py - Python DXF Generator theo chuan DCE Pro

 Dua tren phan tich Form 2.dxf:
- 48 layers chuan DCE Pro
- 80+ blocks (TK1-TK44, TKTitle, Block_ALL...)
- 19 dimension styles
- Text styles: Standard, Dce_Text, Dce_Text2

Usage:
    from dce_dxf_generator import DCEDXFGenerator

    gen = DCEDXFGenerator()
    gen.add_beam(b=300, h=700, h0=650)
    gen.add_rebar_top("2D22")
    gen.add_rebar_bottom("3D22")
    gen.add_dimension()
    gen.save("output/DA01_MC-D1_01.dxf")
"""

import sys
import os

# Setup UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

try:
    import ezdxf
    HAS_EZDXF = True
except ImportError:
    HAS_EZDXF = False
    print("[WARN] ezdxf not installed. Install with: pip install ezdxf")

from typing import Tuple, List, Optional
from dataclasses import dataclass


# =============================================================================
# DCE PRO LAYERS - Copy tu Form 2.dxf
# =============================================================================

DCE_LAYERS = {
    # Layer name: (color, linetype, description)
    "DCE_Name": (142, "Continuous", "Ten cau kien"),
    "DCE_KT": (142, "Continuous", "Kich thuoc"),
    "DCE_Dim": (254, "Continuous", "Duong kich thuoc"),
    "DCE_Block": (8, "Continuous", "Blocks"),
    "DCE_MCZiCZac": (144, "Continuous", "Mat cat zi/czac"),
    "Dce_text": (7, "Continuous", "Text"),
    "DCE_BaoBeTong": (4, "Continuous", "Bao be tong"),
    "DCE_ThepChu": (1, "Continuous", "Thep chu"),
    "DCE_ThepDai": (220, "Continuous", "Thep dai"),
    "DCE_Truc": (8, "DASHDOT2_DBIM", "Duong truc"),
    "DCE_NetKhuat": (9, "HIDDEN_DBIM", "Duong khuwat"),
    "DCE_NetDut": (8, "HIDDEN_DBIM", "Duong dut"),
    "DCE_Hatch": (8, "Continuous", "Hatch pattern"),
    "DCE_Gen_Open": (144, "CENTER2_DBIM", "Gen/Open"),
    "DCE_Nhip": (7, "Continuous", "Nhip"),
    "DCE_TKT-TEXT": (2, "Continuous", "Thong ke text"),
    "DCE_Symbol": (8, "Continuous", "Symbol"),
    "DCE_Lanh_To": (3, "Continuous", "Lanh to"),
    "DCE_BottomBars": (1, "HIDDEN_DBIM", "Thep day"),
    "DCE_Beam": (2, "BEAM HIDEN_DBIM", "Dam"),
    "DCE_CDD": (142, "Continuous", "CDD"),
    "DCE_Note": (117, "Continuous", "Ghi chu"),
    "DCE_Coc": (2, "Continuous", "Coc"),
    "DCE_Coc3D": (8, "Continuous", "Coc 3D"),
}

# Color palette (AutoCAD ACI)
DCE_COLORS = {
    "red": 1,
    "yellow": 2,
    "green": 3,
    "cyan": 4,
    "blue": 5,
    "magenta": 6,
    "white": 7,
    "gray": 8,
    "dark_gray": 9,
}


# =============================================================================
# DCE PRO BLOCKS
# =============================================================================

DCE_BLOCKS = {
    # TK blocks - dimension text boxes
    "TK1": "TK1 dimension block",
    "TK2": "TK2 dimension block",
    "TK3": "TK3 dimension block",
    "TK4": "TK4 dimension block",
    "TK5": "TK5 dimension block",
    "TK6": "TK6 dimension block",
    "TK7": "TK7 dimension block",
    "TK8": "TK8 dimension block",
    "TK9": "TK9 dimension block",
    "TK10": "TK10 dimension block",
    "TKTitle": "Title block",
    "Block_ALL": "All blocks combined",
    "Dce_KhTenTruc": "Khung ten truc",
    "Dce_CaoTrinh": "Cao trinh",
    "Dce_MatCatA": "Mat cat A-A",
}

# =============================================================================
# DCE PRO DIMENSION STYLES
# =============================================================================

DCE_DIMSTYLES = {
    "Dce_100MV": {"scale": 100, "suffix": ""},
    "Dce_50MV": {"scale": 50, "suffix": ""},
    "Dce_25MV": {"scale": 25, "suffix": ""},
    "Dce_20MV": {"scale": 20, "suffix": ""},
    "Dce_30MV": {"scale": 30, "suffix": ""},
    "Dce_40MV": {"scale": 40, "suffix": ""},
    "Dce_75MV": {"scale": 75, "suffix": ""},
    "Dce_120MV": {"scale": 120, "suffix": ""},
    "Dce_125MV": {"scale": 125, "suffix": ""},
    "Dce_150MV": {"scale": 150, "suffix": ""},
    "Dce_200MV": {"scale": 200, "suffix": ""},
    "Dce_206MV": {"scale": 206, "suffix": ""},
    "Dce_207MV": {"scale": 207, "suffix": ""},
    "Dce_208MV": {"scale": 208, "suffix": ""},
    "Dce_205MV": {"scale": 205, "suffix": ""},
    "Dce_209MV": {"scale": 209, "suffix": ""},
    "Dce_LEADERMV": {"scale": 0, "suffix": ""},
}


# =============================================================================
# DATACLASSES
# =============================================================================

@dataclass
class BeamParams:
    """Parameters for beam drawing."""
    b: float = 300        # Width (mm)
    h: float = 700        # Height (mm)
    h0: float = 650       # Effective height (mm)
    a: float = 25          # Cover (mm)


@dataclass
class RebarConfig:
    """Reinforcement configuration."""
    top_bars: str = "2D22"   # Top reinforcement
    bot_bars: str = "3D22"    # Bottom reinforcement
    stirrup_dia: float = 10   # Stirrup diameter
    stirrup_spacing: float = 150  # Stirrup spacing


@dataclass
class ColumnParams:
    """Parameters for column drawing."""
    b: float = 400        # Width (mm)
    h: float = 400        # Depth (mm)
    cover: float = 25


# =============================================================================
# MAIN CLASS
# =============================================================================

class DCEDXFGenerator:
    """
    DXF Generator theo chuan DCE Pro.

    Su dung:
        gen = DCEDXFGenerator()
        gen.setup_document()
        gen.add_beam(b=300, h=700, h0=650)
        gen.add_rebar_top("2D22")
        gen.add_rebar_bottom("3D22")
        gen.save("output/beam.dxf")
    """

    def __init__(self, doc_type: str = "BEAM"):
        """
        Khoi tao generator.

        Args:
            doc_type: "BEAM" | "COLUMN" | "WALL" | "FOUNDATION"
        """
        self.doc_type = doc_type
        self.doc = None
        self.msp = None
        self.modelspace = None

        # Drawing parameters
        self.beam = BeamParams()
        self.rebar = RebarConfig()
        self.column = ColumnParams()

        # Project info
        self.project_name = "PROJECT"
        self.drawing_no = "KCL-01"
        self.drawing_title = "Mat cat cau kien"
        self.scale = "1:20"
        self.sheet = "1/1"

    def setup_document(self):
        """Thiet lap tai lieu DXF."""
        if not HAS_EZDXF:
            raise RuntimeError("ezdxf not installed")

        # Create new document - R2018 for AutoCAD 2018+
        self.doc = ezdxf.new('R2018')
        self.msp = self.doc.modelspace()

        # Setup layers
        self._setup_layers()

        # Setup linetypes
        self._setup_linetypes()

        # Setup text styles
        self._setup_text_styles()

        # Setup dimension styles
        self._setup_dimstyles()

        # Setup title block
        self._setup_title_block()

        return self

    def _setup_layers(self):
        """Tao cac layers theo chuan DCE Pro."""
        for name, (color, linetype, desc) in DCE_LAYERS.items():
            self.doc.layers.add(
                name=name,
                color=color,
                linetype=linetype if linetype else "Continuous"
            )

        # Add layer 0
        if "0" not in [l.dxf.name for l in self.doc.layers]:
            self.doc.layers.add(name="0", color=7)

    def _setup_linetypes(self):
        """Tao linetypes."""
        # Check if linetypes exist
        existing = [l.dxf.name for l in self.doc.linetypes]
        needed = ["DASHDOT2_DBIM", "HIDDEN_DBIM", "CENTER2_DBIM", "BEAM HIDEN_DBIM"]

        # These are typically loaded from acad.lin
        # For now, use CONTINUOUS as fallback
        pass

    def _setup_text_styles(self):
        """Tao text styles."""
        try:
            self.doc.styles.new("Dce_Text", font="arial.ttf")
        except:
            pass

        try:
            self.doc.styles.new("Dce_Text2", font="arial.ttf")
        except:
            pass

    def _setup_dimstyles(self):
        """Tao dimension styles."""
        for name, params in DCE_DIMSTYLES.items():
            if name not in [d.dxf.name for d in self.doc.dimstyles]:
                try:
                    dimstyle = self.doc.dimstyles.add(name)
                    dimstyle.dxf.dimscale = params["scale"]
                    dimstyle.dxf.dimsz = 2.5
                    dimstyle.dxf.dimexe = 1.25
                    dimstyle.dxf.dimexo = 0.625
                except:
                    pass

    def _setup_title_block(self):
        """Tao title block."""
        # Create TKTitle block
        if "TKTitle" not in [b.name for b in self.doc.blocks]:
            block = self.doc.blocks.new(name="TKTitle")

            # Title block dimensions (A3 size: 420x297)
            w, h = 420, 297
            margin = 5

            # Outer rectangle
            block.add_lwpolyline([
                (0, 0), (w, 0), (w, h), (0, h), (0, 0)
            ], dxfattribs={'layer': 'DCE_Block'})

            # Header line
            header_h = 30
            block.add_line((0, h - header_h), (w, h - header_h),
                         dxfattribs={'layer': 'DCE_Block'})

            # Vertical divider
            div_x = w * 0.6
            block.add_line((div_x, h - header_h), (div_x, h),
                         dxfattribs={'layer': 'DCE_Block'})

            # Title text
            block.add_text("TITLE", height=8, dxfattribs={
                'layer': 'Dce_text',
                'style': 'Dce_Text'
            })

    # =========================================================================
    # DRAWING FUNCTIONS
    # =========================================================================

    def add_beam(self, b: float = None, h: float = None, h0: float = None,
                 a: float = None, x: float = 50, y: float = 50):
        """
        Ve mat cat dam.

        Args:
            b: Chieu rong (mm)
            h: Chieu cao (mm)
            h0: Chieu cao lam viec (mm)
            a: Lop bao ve (mm)
            x, y: Vi tri dat
        """
        if b: self.beam.b = b
        if h: self.beam.h = h
        if h0: self.beam.h0 = h0
        if a: self.beam.a = a

        # Draw concrete section
        self.msp.add_lwpolyline([
            (x, y),
            (x + self.beam.b, y),
            (x + self.beam.b, y + self.beam.h),
            (x, y + self.beam.h),
            (x, y)
        ], dxfattribs={'layer': 'DCE_BaoBeTong'})

        # Add hatch
        self.msp.add_hatch(
            color=8,
            dxfattribs={'layer': 'DCE_Hatch'}
        )

        return self

    def add_rebar_top(self, bars: str = None, x: float = None):
        """
        Ve cot thep gian ke (top bars).

        Args:
            bars: String dinh dang "nDx" (VD: "2D22")
            x: Vi tri x (mac dinh la giua dam)
        """
        if bars:
            self.rebar.top_bars = bars

        # Parse bar string
        import re
        match = re.match(r'(\d+)D(\d+)', self.rebar.top_bars, re.IGNORECASE)
        if match:
            n = int(match.group(1))
            dia = int(match.group(2))
        else:
            n, dia = 2, 22

        # Calculate positions
        spacing = self.beam.b / (n + 1)
        y = self.beam.h - self.beam.a - dia/2

        for i in range(n):
            bar_x = (x or 50) + spacing * (i + 1)
            self.msp.add_circle(
                (bar_x, y),
                dia / 2,
                dxfattribs={'layer': 'DCE_ThepChu'}
            )

        return self

    def add_rebar_bottom(self, bars: str = None, x: float = None):
        """
        Ve cot thep am (bottom bars).

        Args:
            bars: String dinh dang "nDx" (VD: "3D22")
            x: Vi tri x
        """
        if bars:
            self.rebar.bot_bars = bars

        import re
        match = re.match(r'(\d+)D(\d+)', self.rebar.bot_bars, re.IGNORECASE)
        if match:
            n = int(match.group(1))
            dia = int(match.group(2))
        else:
            n, dia = 3, 22

        spacing = self.beam.b / (n + 1)
        y = self.beam.a + dia/2

        for i in range(n):
            bar_x = (x or 50) + spacing * (i + 1)
            self.msp.add_circle(
                (bar_x, y),
                dia / 2,
                dxfattribs={'layer': 'DCE_ThepChu'}
            )

        return self

    def add_stirrups(self, spacing: float = None, dia: float = None,
                    x: float = None, y: float = None):
        """
        Ve cot dai (stirrups).

        Args:
            spacing: Khoang cach cot dai
            dia: Duong kinh cot dai
            x, y: Vi tri
        """
        if spacing:
            self.rebar.stirrup_spacing = spacing
        if dia:
            self.rebar.stirrup_dia = dia

        x = x or 50
        y = y or 50

        # Calculate number of stirrups
        n = int(self.beam.h / self.rebar.stirrup_spacing)

        for i in range(n):
            stir_y = y + i * self.rebar.stirrup_spacing

            # Draw stirrup as rectangle
            sw = self.beam.b - 2 * self.beam.a
            self.msp.add_lwpolyline([
                (x + self.beam.a, stir_y),
                (x + self.beam.b - self.beam.a, stir_y),
                (x + self.beam.b - self.beam.a, stir_y + 3),
                (x + self.beam.a, stir_y + 3),
                (x + self.beam.a, stir_y)
            ], dxfattribs={'layer': 'DCE_ThepDai'})

        return self

    def add_dimension(self, x1: float, y1: float, x2: float, y2: float,
                     text: str = None, angle: float = 0):
        """
        Ve duong kich thuoc.

        Args:
            x1, y1: Diem dau
            x2, y2: Diem cuoi
            text: Gia tri kich thuoc
            angle: Goc nghieng
        """
        self.msp.add_linear_dim(
            base=(0, 0),
            p1=(x1, y1),
            p2=(x2, y2),
            angle=angle,
            text=text,
            dxfattribs={'layer': 'DCE_Dim', 'dimstyle': 'Dce_100MV'}
        )

        return self

    def add_text(self, text: str, x: float, y: float,
                height: float = 2.5, layer: str = "Dce_text"):
        """
        Ve text.

        Args:
            text: Noi dung
            x, y: Vi tri
            height: Chieu cao chu
            layer: Layer
        """
        self.msp.add_text(
            text,
            height=height,
            dxfattribs={
                'layer': layer,
                'style': 'Dce_Text'
            }
        ).set_placement((x, y), align=ezdxf.const.TEXT_ALIGN_MIDDLE_CENTER)

        return self

    def add_dimension_beam_width(self, x: float, y: float, b: float = None):
        """Ve kich thuoc chieu rong dam."""
        b = b or self.beam.b
        self.msp.add_linear_dim(
            base=(x, y - 30),
            p1=(x, y),
            p2=(x + b, y),
            text=f"b={b}",
            dxfattribs={'layer': 'DCE_Dim'}
        )

    def add_dimension_beam_height(self, x: float, y: float, h: float = None):
        """Ve kich thuoc chieu cao dam."""
        h = h or self.beam.h
        self.msp.add_linear_dim(
            base=(x - 30, y),
            p1=(x, y),
            p2=(x, y + h),
            text=f"h={h}",
            angle=90,
            dxfattribs={'layer': 'DCE_Dim'}
        )

    def add_arrow(self, x: float, y: float, angle: float = 0,
                  length: float = 20):
        """Ve mui ten."""
        dx = length * abs(1)
        dy = 0

        if angle == 90:
            dx, dy = 0, length
        elif angle == -90:
            dx, dy = 0, -length

        self.msp.add_line(
            (x, y),
            (x + dx, y + dy),
            dxfattribs={'layer': 'DCE_Symbol'}
        )

    # =========================================================================
    # SAVE & EXPORT
    # =========================================================================

    def save(self, filename: str):
        """Luu file DXF."""
        if not self.doc:
            self.setup_document()

        # Ensure directory exists
        os.makedirs(os.path.dirname(filename) or '.', exist_ok=True)

        # Save
        self.doc.saveas(filename)
        print(f"[OK] Da luu: {filename}")

        return filename

    def save_as_template(self, filename: str):
        """Luu lam template (khong co noi dung)."""
        if not self.doc:
            self.setup_document()

        # Clear modelspace
        # self.msp.delete_all_entities()

        self.doc.saveas(filename)
        print(f"[OK] Template da luu: {filename}")

        return filename


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def parse_bar_string(bar_str: str) -> Tuple[int, int]:
    """
    Parse bar string nhu "2D22" -> (2, 22).

    Args:
        bar_str: String dinh dang "nDx"

    Returns:
        (count, diameter)
    """
    import re
    match = re.match(r'(\d*)D(\d+)', bar_str, re.IGNORECASE)
    if match:
        count = int(match.group(1)) if match.group(1) else 1
        dia = int(match.group(2))
        return count, dia
    return 1, 22


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("DCE Pro DXF Generator - Vi du")
    print("=" * 60)

    # Create generator
    gen = DCEDXFGenerator("BEAM")

    # Setup document
    gen.setup_document()

    # Ve dam
    gen.add_beam(b=300, h=700, h0=650, a=25, x=100, y=100)

    # Ve cot thep
    gen.add_rebar_top("2D22", x=100)
    gen.add_rebar_bottom("3D22", x=100)

    # Ve cot dai
    gen.add_stirrups(spacing=150, dia=10, x=100, y=100)

    # Ve kich thuoc
    gen.add_dimension_beam_width(x=100, y=100, b=300)
    gen.add_dimension_beam_height(x=100, y=100, h=700)

    # Ve text
    gen.add_text("DAM D1", 250, 850, height=5, layer='Dce_text')
    gen.add_text("2D22", 450, 680, height=3, layer='DCE_ThepChu')
    gen.add_text("3D22", 450, 130, height=3, layer='DCE_ThepChu')

    # Ve title block
    gen.add_text("DU AN: ABC", 50, 290, height=3)
    gen.add_text("BAN VE: Mat cat dam D1", 260, 290, height=3)

    # Save
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "DA01_MC-D1_01.dxf")

    gen.save(output_file)

    print()
    print("=" * 60)
    print(f"[OK] Vi du hoan thanh!")
    print(f"    File: {output_file}")
    print("=" * 60)
