# -*- coding: utf-8 -*-
"""
analyze_dxf.py - Phan tich cau truc DCE Pro Forms

Su dung:
1. Trong AutoCAD, chay: export_dxf.lsp
2. Hoac thủ công: File > Export > DXF
3. Chay script nay: python analyze_dxf.py

Tác dụng:
- Phân tích layers, blocks, entities
- Trích xuất thông tin để tạo template
"""

import sys
import os

try:
    import ezdxf
    HAS_EZDXF = True
except ImportError:
    HAS_EZDXF = False
    print("[WARN] ezdxf not installed. Install with: pip install ezdxf")


def analyze_dxf_file(dxf_path: str) -> dict:
    """Phan tích mot file DXF."""

    if not os.path.exists(dxf_path):
        return {"error": f"File not found: {dxf_path}"}

    if not HAS_EZDXF:
        return {"error": "ezdxf not installed"}

    try:
        doc = ezdxf.readfile(dxf_path)
        msp = doc.modelspace()

        # Lay thong tin layers
        layers = []
        for layer in doc.layers:
            layers.append({
                "name": layer.dxf.name,
                "color": layer.color,
                "linetype": layer.dxf.linetype if hasattr(layer.dxf, 'linetype') else "CONTINUOUS",
                "lineweight": layer.dxf.lineweight if hasattr(layer.dxf, 'lineweight') else 0
            })

        # Lay thong tin blocks
        blocks = []
        for block in doc.blocks:
            if not block.name.startswith('*'):  # Bo qua anonymous blocks
                blocks.append({
                    "name": block.name,
                    "entity_count": len(list(block))
                })

        # Dem entities
        entity_counts = {}
        for entity in msp:
            etype = entity.dxftype()
            entity_counts[etype] = entity_counts.get(etype, 0) + 1

        # Lay thong tin dimstyles
        dimstyles = []
        for ds in doc.dimstyles:
            dimstyles.append(ds.dxf.name)

        # Lay thong tin text styles
        textstyles = []
        for ts in doc.styles:
            textstyles.append({
                "name": ts.dxf.name,
                "font": ts.dxf.font if hasattr(ts.dxf, 'font') else "Unknown"
            })

        # Lay thong tin kich thuoc ban ve
        extmin = msp.extmin
        extmax = msp.extmax
        width = extmax.x - extmin.x
        height = extmax.y - extmin.y

        return {
            "file": dxf_path,
            "layers": layers,
            "blocks": blocks,
            "entity_counts": entity_counts,
            "dimstyles": dimstyles,
            "textstyles": textstyles,
            "bounds": {
                "min": (extmin.x, extmin.y),
                "max": (extmax.x, extmax.y),
                "width": width,
                "height": height
            }
        }

    except Exception as e:
        return {"error": str(e)}


def print_analysis(result: dict):
    """In ket qua phan tich."""
    if "error" in result:
        print(f"[ERROR] {result['error']}")
        return

    print(f"\n{'='*60}")
    print(f"ANALYSIS: {result['file']}")
    print(f"{'='*60}")

    # Bounds
    bounds = result.get('bounds', {})
    print(f"\n--- BOUNDS ---")
    print(f"  Min: ({bounds.get('min', [0,0])[0]:.2f}, {bounds.get('min', [0,0])[1]:.2f})")
    print(f"  Max: ({bounds.get('max', [0,0])[0]:.2f}, {bounds.get('max', [0,0])[1]:.2f})")
    print(f"  Width: {bounds.get('width', 0):.2f}")
    print(f"  Height: {bounds.get('height', 0):.2f}")

    # Layers
    print(f"\n--- LAYERS ({len(result.get('layers', []))}) ---")
    for layer in result.get('layers', []):
        print(f"  [{layer['color']:>3}] {layer['name':<20} | {layer['linetype']}")

    # Blocks
    print(f"\n--- BLOCKS ({len(result.get('blocks', []))}) ---")
    for block in result.get('blocks', []):
        print(f"  {block['name']:<30} ({block['entity_count']} entities)")

    # Entities
    print(f"\n--- ENTITY COUNTS ---")
    for etype, count in sorted(result.get('entity_counts', {}).items()):
        print(f"  {etype:<20}: {count:>5}")

    # Dimstyles
    print(f"\n--- DIMENSION STYLES ---")
    for ds in result.get('dimstyles', []):
        print(f"  {ds}")

    # Text styles
    print(f"\n--- TEXT STYLES ---")
    for ts in result.get('textstyles', []):
        print(f"  {ts['name']:<20} | Font: {ts['font']}")


def analyze_all_forms():
    """Phan tich tat ca cac form da export."""
    forms_dir = r"C:\DCE Pro\Cad"
    dxf_files = [
        "Form 2.dxf",
        "Form 2_Steel.dxf",
        "Form 3.dxf",
        "Form 3_Steel.dxf",
        "Form 4.dxf",
        "Form 4_Steel.dxf",
        "Form 5.dxf",
        "Form 5_Steel.dxf",
    ]

    results = {}
    for dxf_file in dxf_files:
        dxf_path = os.path.join(forms_dir, dxf_file)
        if os.path.exists(dxf_path):
            print(f"\nAnalyzing: {dxf_file}")
            result = analyze_dxf_file(dxf_path)
            results[dxf_file] = result
            if "error" not in result:
                print_analysis(result)
        else:
            print(f"\n[SKIP] {dxf_file} - not found (export first)")

    return results


def generate_template_code(results: dict) -> str:
    """Sinh ma Python tu ket qua phan tich."""
    code = '''
# ============================================================
# DCE Pro Forms - Layer Templates
# Auto-generated from analyze_dxf.py
# ============================================================

DCE_LAYERS = {
'''

    # Merge all layers from all forms
    all_layers = {}
    for form_name, result in results.items():
        if "error" not in result:
            for layer in result.get('layers', []):
                name = layer['name']
                if name not in all_layers:
                    all_layers[name] = {
                        'color': layer['color'],
                        'linetype': layer['linetype']
                    }

    for name, info in sorted(all_layers.items()):
        code += f'    "{name}": {{\n'
        code += f'        "color": {info["color"]},\n'
        code += f'        "linetype": "{info["linetype"]}",\n'
        code += f'    }},\n'

    code += '''}

# ============================================================
# Form-specific templates
# ============================================================

FORM_2_LAYERS = [  # Dam
    "MAIN-BTCT",
    "MAIN-THEP",
    "MAIN-DIM",
    "MAIN-TEXT",
    "MAIN-HATCH",
    "MAIN-SYMBOL",
    "MAIN-LINE",
]

FORM_3_LAYERS = [  # Cot
    "MAIN-BTCT",
    "MAIN-THEP",
    "MAIN-DIM",
    "MAIN-TEXT",
    "MAIN-HATCH",
]

FORM_4_LAYERS = [  # Vach
    "MAIN-BTCT",
    "MAIN-THEP",
    "MAIN-DIM",
    "MAIN-TEXT",
    "MAIN-HATCH",
]

FORM_5_LAYERS = [  # Mong
    "MAIN-BTCT",
    "MAIN-THEP",
    "MAIN-DIM",
    "MAIN-TEXT",
    "MAIN-HATCH",
    "MAIN-SOIL",
]

# ============================================================
# DXF Generator Class
# ============================================================

class DCEDXFGenerator:
    """Generator tao ban ve theo chuan DCE Pro."""

    def __init__(self, form_type="BEAM"):
        self.form_type = form_type
        self.doc = None
        self.msp = None

        # Mapping form_type to layers
        self.layer_mapping = {
            "BEAM": FORM_2_LAYERS,
            "COLUMN": FORM_3_LAYERS,
            "WALL": FORM_4_LAYERS,
            "FOUNDATION": FORM_5_LAYERS,
        }
        self.layers = self.layer_mapping.get(form_type, FORM_2_LAYERS)

    def setup_document(self):
        """Khoi tao tai lieu DXF."""
        if HAS_EZDXF:
            self.doc = ezdxf.new('R2010')
            self.msp = self.doc.modelspace()
            self._create_layers()
        else:
            print("[ERROR] ezdxf required")
            return False
        return True

    def _create_layers(self):
        """Tao cac layers theo tieu chuan."""
        layer_colors = {
            "MAIN-BTCT": 8,      # White/Gray
            "MAIN-THEP": 1,      # Red
            "MAIN-DIM": 3,       # Green
            "MAIN-TEXT": 7,      # White
            "MAIN-HATCH": 8,     # Gray
            "MAIN-SYMBOL": 5,    # Blue
            "MAIN-LINE": 7,      # White
            "MAIN-SOIL": 40,     # Brown
        }

        for layer_name in self.layers:
            color = layer_colors.get(layer_name, 7)
            self.doc.layers.add(layer_name, color=color)

    def add_rect(self, x, y, width, height, layer="MAIN-BTCT"):
        """Ve hinh chu nhat."""
        if self.msp:
            self.msp.add_lwpolyline(
                [(x, y), (x + width, y), (x + width, y + height), (x, y + height), (x, y)],
                close=True,
                dxfattribs={'layer': layer}
            )

    def save(self, filename):
        """Luu file DXF."""
        if self.doc:
            self.doc.saveas(filename)
            print(f"[OK] Saved: {filename}")

'''

    return code


if __name__ == "__main__":
    print("=" * 60)
    print("DCE Pro Forms - DXF Analyzer")
    print("=" * 60)

    if len(sys.argv) > 1:
        # Analyze specific file
        dxf_path = sys.argv[1]
        result = analyze_dxf_file(dxf_path)
        print_analysis(result)
    else:
        # Analyze all forms
        print("\nAnalyzing all DCE Pro forms...")
        results = analyze_all_forms()

        if results:
            # Generate template code
            print("\n" + "=" * 60)
            print("Generating template code...")

            template_file = os.path.join(
                os.path.dirname(__file__),
                "dce_layers_template.py"
            )

            with open(template_file, 'w', encoding='utf-8') as f:
                f.write(generate_template_code(results))

            print(f"[OK] Template saved: {template_file}")
