#!/usr/bin/env python3
"""
dce_fast_scan.py - Fast string extraction using regex on binary data
"""
import sys
import os
import re
import json
from pathlib import Path
from datetime import datetime

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

DCE_PRO_ROOT = Path(r"C:\Dce Pro")
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "docs"

# Regex for printable ASCII strings
STRING_PATTERN = re.compile(rb'[ -~]{4,200}')

# Patterns to find
PATTERNS = {
    'xdata_tags': re.compile(rb'\b(SH|DK|SL|L|TK|SKC|TSL|KL|sumL|Lall|L1|L2|L3)\b'),
    'excel_sheets': re.compile(rb'(Sheet|DATA|INPUT|OUTPUT|Design|Beam|Column|Slab|Foundation)[A-Za-z0-9]*'),
    'dce_commands': re.compile(rb'(VeDam|VeCot|VeVach|VeSan|VeMong|GanDL|QuetThongKe|SuaCK|GanLienKet|ShopDrawing)'),
    'dce_layers': re.compile(rb'Dce_[A-Za-z0-9_]+'),
    'dce_blocks': re.compile(rb'(TK[0-9]+[a-zA-Z]*|Dce_Kh[A-Za-z]+)'),
    'dimstyles': re.compile(rb'Dce_[0-9]+MV'),
    'cell_refs': re.compile(rb'[A-Z]{1,3}[0-9]{1,4}'),
    'ranges': re.compile(rb'[A-Z]{1,3}[0-9]{1,4}:[A-Z]{1,3}[0-9]{1,4}'),
    'regapp': re.compile(rb'\b(DBIM|DCE|DBIM_DCE|DBIM_REBAR)\b'),
}

def extract_from_file(filepath: Path) -> dict:
    """Extract strings from binary file using regex."""
    print(f"Scanning: {filepath.name}...")

    results = {
        'xdata_tags': set(),
        'excel_sheets': set(),
        'dce_commands': set(),
        'dce_layers': set(),
        'dce_blocks': set(),
        'dimstyles': set(),
        'cell_refs': set(),
        'ranges': set(),
        'regapp': set(),
        'all_strings': [],
    }

    try:
        # Read file in chunks for memory efficiency
        chunk_size = 1024 * 1024  # 1MB chunks
        with open(filepath, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break

                # Find all strings in chunk
                for match in STRING_PATTERN.finditer(chunk):
                    s = match.group(0).decode('ascii', errors='ignore')

                    # Skip obvious non-interesting strings
                    if len(s) < 3 or s.startswith(' ') or s.endswith(' '):
                        continue

                    results['all_strings'].append(s)

                    # Match patterns
                    for pattern_name, pattern in PATTERNS.items():
                        if pattern.search(match.group(0)):
                            results[pattern_name].add(s)

        print(f"  Found {len(results['all_strings'])} strings")

    except Exception as e:
        print(f"  Error: {e}")

    return results

def main():
    print("="*60)
    print("DCE Pro - Fast Binary String Scan")
    print("="*60)

    dlls = [
        DCE_PRO_ROOT / "V.2020" / "DCE Excel.dll",
        DCE_PRO_ROOT / "DbimSteelAutocad.dll",
    ]

    # Only use smaller DLLs for fast scan
    all_results = {}

    for dll in dlls:
        if not dll.exists():
            print(f"SKIP: {dll.name} (not found)")
            continue

        size_mb = dll.stat().st_size / (1024*1024)
        if size_mb > 10:
            print(f"SKIP: {dll.name} ({size_mb:.1f}MB - too large)")
            continue

        results = extract_from_file(dll)
        all_results[dll.name] = results

        # Print findings
        print(f"\n  XData tags: {sorted(results['xdata_tags'])}")
        print(f"  Commands: {sorted(results['dce_commands'])}")
        print(f"  Layers: {sorted(results['dce_layers'])[:20]}")
        print(f"  Blocks: {sorted(results['dce_blocks'])[:20]}")
        print(f"  Sheets: {sorted(results['excel_sheets'])}")
        print(f"  DimStyles: {sorted(results['dimstyles'])}")
        print(f"  RegApp: {sorted(results['regapp'])}")

    # Now try DCE Pro.dll with limited scan
    dce_pro = DCE_PRO_ROOT / "DCE Pro.dll"
    if dce_pro.exists():
        print(f"\nScanning {dce_pro.name} (limited)...")
        # Just scan first 5MB for quick results
        results = extract_from_file(dce_pro)
        all_results[dce_pro.name] = results

        print(f"  XData tags: {sorted(results['xdata_tags'])}")
        print(f"  Commands: {sorted(results['dce_commands'])}")
        print(f"  Layers: {sorted(results['dce_layers'])[:20]}")
        print(f"  Blocks: {sorted(results['dce_blocks'])[:20]}")
        print(f"  DimStyles: {sorted(results['dimstyles'])}")
        print(f"  RegApp: {sorted(results['regapp'])}")

    # Merge and save
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    merged = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'version': '3.0.0',
            'description': 'DCE Pro Fast Binary String Analysis',
        },
        'xdata_protocol': {
            'regapp_name': 'DBIM',  # Most likely
            'field_tags': list(set().union(*[r['xdata_tags'] for r in all_results.values()])),
        },
        'excel_bus': {
            'sheet_names': sorted(list(set().union(*[r['excel_sheets'] for r in all_results.values()]))),
            'cell_refs': sorted(list(set().union(*[r['cell_refs'] for r in all_results.values()]))),
            'ranges': sorted(list(set().union(*[r['ranges'] for r in all_results.values()]))),
        },
        'cad_integration': {
            'layers': sorted(list(set().union(*[r['dce_layers'] for r in all_results.values()]))),
            'blocks': sorted(list(set().union(*[r['dce_blocks'] for r in all_results.values()]))),
            'dimstyles': sorted(list(set().union(*[r['dimstyles'] for r in all_results.values()]))),
            'commands': sorted(list(set().union(*[r['dce_commands'] for r in all_results.values()]))),
        },
    }

    json_path = OUTPUT_DIR / "DCE_DEEP_OPERATION_SCHEMA.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)

    print(f"\nSaved: {json_path}")

    # Print summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"RegApp Name: {merged['xdata_protocol']['regapp_name']}")
    print(f"XData Tags: {merged['xdata_protocol']['field_tags']}")
    print(f"Sheets: {merged['excel_bus']['sheet_names']}")
    print(f"Layers: {len(merged['cad_integration']['layers'])} found")
    print(f"Blocks: {len(merged['cad_integration']['blocks'])} found")
    print(f"DimStyles: {merged['cad_integration']['dimstyles']}")
    print(f"Commands: {merged['cad_integration']['commands']}")

    return merged

if __name__ == "__main__":
    main()
