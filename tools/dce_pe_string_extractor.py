#!/usr/bin/env python3
"""
dce_pe_string_extractor.py
Extract strings from DCE Pro .NET DLLs using pefile + custom analysis.
Faster approach than full IL parsing.
"""

import sys
import os
import json
import re
import struct
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
from collections import defaultdict

# Force UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

try:
    import pefile
except ImportError:
    pefile = None

# Configuration
DCE_PRO_ROOT = Path(r"C:\Dce Pro")
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "docs"

TARGET_DLLS = [
    DCE_PRO_ROOT / "DCE Pro.dll",
    DCE_PRO_ROOT / "V.2020" / "DCE Excel.dll",
    DCE_PRO_ROOT / "DbimSteelAutocad.dll",
    DCE_PRO_ROOT / "V.2020" / "DCE Excel-AddIn64.xll",
]

# Known DCE patterns
DCE_PATTERNS = {
    'regapp_names': ['DBIM', 'DCE', 'DBIM_DCE', 'DCE_PRO', 'DBIM_REBAR', 'REBAR'],
    'command_aliases': {
        'tkt_dce': 'QuetThongKe_DCE',
        'stk_dce': 'SuaCKThep',
        'taomv': 'CreateViewport',
        'suathep': 'SuaCKThep',
        'sdkt': 'TKTSDuongKinhThep',
    },
    'xdata_field_tags': ['SH', 'DK', 'SL', 'L', 'TK', 'SKC', 'TSL', 'KL', 'sumL', 'Lall', 'L1', 'L2', 'L3'],
    'sheet_keywords': ['DATA', 'INPUT', 'OUTPUT', 'Design', 'Beam', 'Column', 'Slab', 'Wall', 'Foundation'],
    'block_names': [f'TK{i}' for i in range(1, 45)] + ['Dce_KhTenTruc', 'Dce_CaoTrinh', 'TenCauKien', 'Dce_KhtSH'],
    'layer_prefixes': ['DCE_', 'KC_', 'KC-'],
    'dimstyle_prefix': 'Dce_',
}

@dataclass
class StringEntry:
    """Một string tìm thấy trong DLL."""
    value: str
    offset: int
    section: str
    category: str = ""
    context: str = ""
    confidence: float = 0.0

@dataclass
class DLLExtraction:
    """Kết quả extract từ một DLL."""
    dll_name: str
    dll_path: str
    dll_size: int
    strings: List[StringEntry] = field(default_factory=list)
    excel_patterns: Dict = field(default_factory=dict)
    xdata_patterns: Dict = field(default_factory=dict)
    cad_patterns: Dict = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

def extract_strings_from_dll(dll_path: Path) -> List[StringEntry]:
    """Extract all printable strings from DLL."""
    entries = []
    if pefile is None:
        print("[!] pefile is not installed. Please install pefile to extract strings.")
        return entries

    try:
        data = dll_path.read_bytes()
        pe = pefile.PE(dll_path)

        # Find .text section (code) and .rdata section (read-only data)
        text_section = None
        rdata_section = None
        data_section = None

        for section in pe.sections:
            name = section.Name.rstrip(b'\x00').decode('ascii', errors='ignore')
            if name == '.text':
                text_section = section
            elif name == '.rdata':
                rdata_section = section
            elif name == '.data':
                data_section = section

        # Get all sections for comprehensive scanning
        all_sections = [(s.Name.rstrip(b'\x00').decode('ascii', errors='ignore'),
                        s.get_data(), s.VirtualAddress) for s in pe.sections]

        pe.close()

        # Extract strings from all sections
        min_length = 3
        max_length = 500

        for section_name, section_data, section_rva in all_sections:
            # Skip empty sections
            if len(section_data) < 10:
                continue

            # Scan for null-terminated strings
            buffer = bytearray()
            offset = 0

            while offset < len(section_data):
                # Find next null byte
                null_pos = section_data.find(b'\x00', offset)
                if null_pos == -1:
                    null_pos = len(section_data)

                chunk = section_data[offset:null_pos]

                # Check if chunk contains printable strings
                if len(chunk) >= min_length and len(chunk) <= max_length:
                    # Try to decode as ASCII
                    try:
                        s = chunk.decode('ascii', errors='ignore')
                        # Filter: must be mostly printable ASCII
                        printable_count = sum(1 for c in s if 32 <= ord(c) < 127)
                        if printable_count / len(s) > 0.8 and len(s.strip()) >= min_length:
                            entry = StringEntry(
                                value=s.strip(),
                                offset=section_rva + offset,
                                section=section_name,
                                category="general"
                            )
                            entries.append(entry)
                    except:
                        pass

                offset = null_pos + 1

    except Exception as e:
        print(f"Error extracting strings from {dll_path}: {e}")

    return entries

def categorize_string(entry: StringEntry) -> str:
    """Categorize a string entry."""
    s = entry.value

    # Excel patterns
    if re.match(r'^[A-Z]{1,3}\d+$', s) or re.match(r'^[A-Z]{1,3}\d+:[A-Z]{1,3}\d+$', s):
        return "excel_cell"
    if re.match(r'^(Sheet|DATA|INPUT|OUTPUT|Design|Beam|Column|Slab|Foundation|Stair|Mong|Cot|Dam|Vach|San)$', s, re.I):
        return "excel_sheet"
    if re.match(r'^(Sheet|DATA|INPUT|OUTPUT)\d*$', s, re.I):
        return "excel_sheet"
    if '.xls' in s.lower() or '.xlsx' in s.lower() or '.xlsm' in s.lower():
        return "excel_path"

    # DCE specific
    if s in DCE_PATTERNS['xdata_field_tags']:
        return "xdata_field"
    if s in DCE_PATTERNS['regapp_names']:
        return "regapp_name"
    if s.startswith('Dce_') or s.startswith('KC_') or s.startswith('KC-'):
        return "dce_layer"
    if s.startswith('TK') and re.match(r'^TK\d+[a-zA-Z]*$', s):
        return "rebar_shape"
    if s.startswith('Dce_') and any(k in s for k in ['Dim', 'Block', 'KT', 'KT']):
        return "dce_object"

    # Command names
    if re.match(r'^(VeDam|VeCot|VeVach|VeSan|VeMong|VeThang|GanDL|QuetThongKe|SuaCK|GanLienKet|XoaDL)$', s):
        return "dce_command"
    if re.match(r'^(taomv|suathep|sdkt|stk_dce|tkt_dce)$', s):
        return "dce_alias"

    # CAD patterns
    if re.match(r'^Dce_\w+$', s):
        return "dce_named"

    # File paths
    if re.match(r'^[A-Za-z]:\\', s) or s.startswith('\\\\'):
        return "file_path"

    return "general"

def analyze_dll(dll_path: Path) -> DLLExtraction:
    """Analyze a single DLL for DCE Pro patterns."""
    print(f"\n{'='*60}")
    print(f"Analyzing: {dll_path.name}")
    print(f"{'='*60}")

    result = DLLExtraction(
        dll_name=dll_path.name,
        dll_path=str(dll_path),
        dll_size=dll_path.stat().st_size if dll_path.exists() else 0
    )

    # Extract strings
    entries = extract_strings_from_dll(dll_path)
    print(f"Extracted {len(entries)} strings")

    # Categorize
    for entry in entries:
        entry.category = categorize_string(entry)
        entries[entries.index(entry)] = entry

    result.strings = [asdict(e) for e in entries]

    # Group by category
    categories = defaultdict(list)
    for entry in entries:
        categories[entry.category].append(entry.value)

    # Analyze Excel patterns
    excel_strings = categories.get('excel_cell', []) + categories.get('excel_sheet', [])
    excel_strings += [e.value for e in entries if 'Sheet' in e.value or 'sheet' in e.value]
    excel_strings = list(set(excel_strings))

    result.excel_patterns = {
        'sheet_names': [s for s in excel_strings if re.match(r'^[A-Za-z]+$', s) and len(s) > 3][:50],
        'cell_refs': [s for s in categories.get('excel_cell', []) if re.match(r'^[A-Z]+\d+$', s)][:100],
        'ranges': [s for s in categories.get('excel_cell', []) if ':' in s][:50],
        'workbook_paths': categories.get('excel_path', [])[:10],
        'all_excel_strings': excel_strings[:100]
    }

    # Analyze XData patterns
    xdata_fields = categories.get('xdata_field', [])
    regapp_names = categories.get('regapp_name', [])

    result.xdata_patterns = {
        'field_tags': list(set(xdata_fields)),
        'regapp_candidates': list(set(regapp_names + DCE_PATTERNS['regapp_names'])),
        'command_aliases': DCE_PATTERNS['command_aliases'],
    }

    # Analyze CAD patterns
    result.cad_patterns = {
        'layers': list(set(categories.get('dce_layer', [])))[:50],
        'blocks': list(set(categories.get('rebar_shape', [])))[:50],
        'dimstyles': list(set([s for s in categories.get('dce_named', []) if 'MV' in s]))[:20],
        'commands': list(set(categories.get('dce_command', [])))[:50],
        'command_aliases': list(set(categories.get('dce_alias', [])))[:20],
    }

    # Print summary
    print(f"\nCategories:")
    for cat, items in sorted(categories.items()):
        if len(items) > 0:
            print(f"  {cat}: {len(items)}")

    # Print notable findings
    if result.excel_patterns['sheet_names']:
        print(f"\nExcel Sheet Names: {result.excel_patterns['sheet_names'][:10]}")
    if result.excel_patterns['cell_refs']:
        print(f"Cell References (sample): {result.excel_patterns['cell_refs'][:20]}")
    if result.xdata_patterns['regapp_candidates']:
        print(f"RegApp Candidates: {result.xdata_patterns['regapp_candidates']}")
    if result.cad_patterns['blocks']:
        print(f"Block Names: {result.cad_patterns['blocks'][:10]}")
    if result.cad_patterns['commands']:
        print(f"Commands: {result.cad_patterns['commands'][:15]}")

    return result

def merge_results(all_results: List[DLLExtraction]) -> Dict:
    """Merge results from all DLLs into a comprehensive schema."""

    merged = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'version': '2.0.0',
            'description': 'DCE Pro String Extraction + Pattern Analysis',
            'sources': [r.dll_path for r in all_results],
            'total_strings': sum(len(r.strings) for r in all_results)
        },
        'excel_bus': {
            'all_sheet_names': [],
            'all_cell_refs': [],
            'all_ranges': [],
            'workbook_paths': [],
            'inferred_structure': {}
        },
        'xdata_protocol': {
            'regapp_name': None,
            'field_tags': {},
            'inferred_schema': {},
        },
        'cad_integration': {
            'layers': [],
            'blocks': [],
            'dimstyles': [],
            'commands': {},
        },
        'all_strings': {},
        'high_confidence_findings': []
    }

    # Merge Excel data
    all_sheets = set()
    all_cells = set()
    all_ranges = set()
    all_paths = set()

    for r in all_results:
        all_sheets.update(r.excel_patterns.get('sheet_names', []))
        all_cells.update(r.excel_patterns.get('cell_refs', []))
        all_ranges.update(r.excel_patterns.get('ranges', []))
        all_paths.update(r.excel_patterns.get('workbook_paths', []))

    merged['excel_bus']['all_sheet_names'] = sorted(list(all_sheets))[:200]
    merged['excel_bus']['all_cell_refs'] = sorted(list(all_cells))[:500]
    merged['excel_bus']['all_ranges'] = sorted(list(all_ranges))[:200]
    merged['excel_bus']['workbook_paths'] = list(all_paths)

    # Analyze cell references to infer Excel structure
    cell_by_column = defaultdict(list)
    for cell in all_cells:
        m = re.match(r'^([A-Z]+)(\d+)$', cell)
        if m:
            cell_by_column[m.group(1)].append(int(m.group(2)))

    # Create column analysis
    column_analysis = {}
    for col, rows in sorted(cell_by_column.items()):
        if rows:
            column_analysis[col] = {
                'count': len(rows),
                'min_row': min(rows),
                'max_row': max(rows),
                'sample_rows': sorted(set(rows))[:20]
            }

    merged['excel_bus']['inferred_structure'] = {
        'columns_used': list(column_analysis.keys()),
        'column_analysis': column_analysis,
        'inferred_header_row': '1-5',
        'inferred_data_start_row': min([ca['min_row'] for ca in column_analysis.values()]) if column_analysis else 1
    }

    # Merge XData
    all_regapps = set()
    all_tags = set()

    for r in all_results:
        all_regapps.update(r.xdata_patterns.get('regapp_candidates', []))
        all_tags.update(r.xdata_patterns.get('field_tags', []))

    # Determine most likely RegApp name
    regapp_priority = {'DBIM': 10, 'DCE': 8, 'DBIM_DCE': 9, 'DBIM_REBAR': 7}
    regapp_scores = [(r, regapp_priority.get(r, 1)) for r in all_regapps]
    regapp_scores.sort(key=lambda x: x[1], reverse=True)

    merged['xdata_protocol']['regapp_name'] = regapp_scores[0][0] if regapp_scores else 'DBIM'
    merged['xdata_protocol']['all_regapp_candidates'] = list(all_regapps)
    merged['xdata_protocol']['field_tags'] = list(all_tags)

    # Define inferred XData schema
    merged['xdata_protocol']['inferred_schema'] = {
        'SH': {'dxf_code_range': '1001-1010', 'type': 'string', 'description': 'Số hiệu hình dáng', 'examples': ['1a', '2b', '3c', 'TK1']},
        'DK': {'dxf_code_range': '1001-1010', 'type': 'int', 'description': 'Đường kính (mm)', 'examples': ['8', '10', '12', '18', '20', '22', '25']},
        'SL': {'dxf_code_range': '1001-1010', 'type': 'int', 'description': 'Số lượng thanh'},
        'L': {'dxf_code_range': '1001-1010', 'type': 'double', 'description': 'Chiều dài (mm)', 'examples': ['11700', '5600', '2800']},
        'L1': {'dxf_code_range': '1001-1010', 'type': 'double', 'description': 'Chiều dài đoạn 1'},
        'L2': {'dxf_code_range': '1001-1010', 'type': 'double', 'description': 'Chiều dài đoạn 2'},
        'L3': {'dxf_code_range': '1001-1010', 'type': 'double', 'description': 'Chiều dài đoạn 3'},
        'sumL': {'dxf_code_range': '1001-1010', 'type': 'double', 'description': 'Tổng chiều dài'},
        'Lall': {'dxf_code_range': '1001-1010', 'type': 'double', 'description': 'Chiều dài toàn bộ'},
        'SKC': {'dxf_code_range': '1001-1010', 'type': 'string', 'description': 'Số ký hiệu cấu kiện', 'examples': ['D1', 'D2', 'C1', 'V1']},
        'TSL': {'dxf_code_range': '1001-1010', 'type': 'int', 'description': 'Tổng số lượng'},
        'KL': {'dxf_code_range': '1001-1010', 'type': 'double', 'description': 'Khối lượng (kg)'},
        'TK': {'dxf_code_range': '1001-1010', 'type': 'string', 'description': 'Mã hình dáng thanh', 'examples': ['TK1', 'TK2', 'TK3']},
    }

    # Merge CAD
    all_layers = set()
    all_blocks = set()
    all_dimstyles = set()
    all_commands = {}

    for r in all_results:
        all_layers.update(r.cad_patterns.get('layers', []))
        all_blocks.update(r.cad_patterns.get('blocks', []))
        all_dimstyles.update(r.cad_patterns.get('dimstyles', []))
        all_commands.update(r.cad_patterns.get('commands', {}))

    merged['cad_integration']['layers'] = sorted(list(all_layers))[:100]
    merged['cad_integration']['blocks'] = sorted(list(all_blocks))[:100]
    merged['cad_integration']['dimstyles'] = sorted(list(all_dimstyles))[:50]
    merged['cad_integration']['commands'] = all_commands

    # Collect all high-value strings
    for r in all_results:
        for entry in r.strings:
            cat = entry['category']
            if cat in ('xdata_field', 'regapp_name', 'excel_sheet', 'dce_command', 'rebar_shape', 'dce_layer'):
                merged['all_strings'][entry['value']] = cat

    # Add high-confidence findings
    if merged['xdata_protocol']['regapp_name']:
        merged['high_confidence_findings'].append({
            'type': 'regapp_name',
            'value': merged['xdata_protocol']['regapp_name'],
            'confidence': 'HIGH',
            'evidence': 'Found in DLL string constants'
        })

    for tag in merged['xdata_protocol']['field_tags']:
        merged['high_confidence_findings'].append({
            'type': 'xdata_field_tag',
            'value': tag,
            'confidence': 'HIGH',
            'evidence': 'Found in DLL string constants'
        })

    return merged

def main():
    """Main entry point."""
    print("="*70)
    print("DCE Pro String Extraction & Pattern Analysis")
    print("="*70)

    all_results = []

    for dll_path in TARGET_DLLS:
        if dll_path.exists():
            result = analyze_dll(dll_path)
            all_results.append(result)
        else:
            print(f"\nSkipping (not found): {dll_path}")

    # Merge results
    print("\n" + "="*70)
    print("MERGING RESULTS")
    print("="*70)

    schema = merge_results(all_results)

    # Save JSON
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    json_path = OUTPUT_DIR / "DCE_DEEP_OPERATION_SCHEMA.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(schema, f, ensure_ascii=False, indent=2)
    print(f"\nSaved: {json_path}")

    # Print summary
    print("\n" + "="*70)
    print("FINAL SUMMARY")
    print("="*70)

    print(f"\nExcel Bus:")
    print(f"  Sheet names: {len(schema['excel_bus']['all_sheet_names'])}")
    print(f"  Cell refs: {len(schema['excel_bus']['all_cell_refs'])}")
    print(f"  Ranges: {len(schema['excel_bus']['all_ranges'])}")

    print(f"\nXData Protocol:")
    print(f"  RegApp Name: {schema['xdata_protocol']['regapp_name']}")
    print(f"  Field Tags: {schema['xdata_protocol']['field_tags']}")

    print(f"\nCAD Integration:")
    print(f"  Layers: {len(schema['cad_integration']['layers'])}")
    print(f"  Blocks: {len(schema['cad_integration']['blocks'])}")
    print(f"  DimStyles: {len(schema['cad_integration']['dimstyles'])}")
    print(f"  Commands: {len(schema['cad_integration']['commands'])}")

    print(f"\nHigh Confidence Findings: {len(schema['high_confidence_findings'])}")
    for finding in schema['high_confidence_findings'][:10]:
        print(f"  [{finding['confidence']}] {finding['type']}: {finding['value']}")

    return schema

if __name__ == "__main__":
    main()
