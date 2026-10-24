#!/usr/bin/env python3
"""
dce_binary_scanner.py
Quét binary DLL tìm tất cả chuỗi (ASCII + UTF-16LE).
Dùng cả 2 method: raw byte scan + UTF-16LE pair scan.
"""

import sys
import os
import re
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

DCE_PRO_ROOT = Path(r"C:\Dce Pro")
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "docs"

# Target DLLs
TARGET_DLLS = [
    DCE_PRO_ROOT / "DCE Pro.dll",           # 30.7MB - full scan
    DCE_PRO_ROOT / "V.2020" / "DCE Excel.dll",  # 10.8MB
    DCE_PRO_ROOT / "BcDCE Pro.dll",          # 30.9MB
    DCE_PRO_ROOT / "V.2020" / "DceAnalyssiss64.dll",  # 346KB
]

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB max per file

def extract_ascii_strings(data: bytes, min_len: int = 4) -> list:
    """Trích xuất chuỗi ASCII thuần (null-terminated)."""
    strings = []
    pattern = rb'[ -~]{%d,200}' % min_len
    for m in re.finditer(pattern, data):
        s = m.group(0).decode('ascii', errors='ignore')
        strings.append((s, m.start()))
    return strings

def extract_utf16le_strings_raw(data: bytes, min_len: int = 4) -> list:
    """
    Trích xuất chuỗi UTF-16LE bằng cách đọc tất cả byte pairs.
    Mỗi ký tự hợp lệ: byte_lo != 0x00 (thường) HOẶC là Vietnamese chars.
    """
    strings = []
    i = 0
    while i < len(data) - 1:
        # Kiểm tra byte pair có phải UTF-16LE char hợp lệ?
        byte1 = data[i]
        byte2 = data[i + 1]

        # Valid if:
        # - byte2 == 0x00 and byte1 is printable ASCII (ASCII in UTF-16LE)
        # - byte1 != 0x00 (Vietnamese/Latin supplement)

        valid = False
        if byte2 == 0x00 and 0x20 <= byte1 <= 0x7E:
            valid = True  # ASCII printable
        elif byte1 != 0x00 and 0x20 <= byte2 <= 0xFF:
            valid = True  # Extended Latin/Vietnamese
        elif byte1 != 0x00 and byte2 == 0x00 and 0xC0 <= byte1 <= 0xFF:
            valid = True  # High Latin chars

        if valid:
            # Extract string starting from this position
            j = i
            char_buf = []
            while j < len(data) - 1:
                b1, b2 = data[j], data[j+1]

                # Continue if valid char
                if b2 == 0x00 and 0x20 <= b1 <= 0x7E:
                    char_buf.append(b1)
                    j += 2
                elif b1 != 0x00 and 0x20 <= b2 <= 0xFF:
                    char_buf.append(b1)  # Take lo byte
                    j += 2
                elif b1 == 0x00 and b2 == 0x00:
                    j += 2  # Null terminator
                    break
                elif b2 == 0x00 and 0xC0 <= b1 <= 0xFF:
                    char_buf.append(b1)
                    j += 2
                else:
                    break

            if len(char_buf) >= min_len:
                try:
                    # Reconstruct as UTF-16LE
                    utf16_buf = bytearray()
                    for idx, b in enumerate(char_buf):
                        utf16_buf.append(b)
                        utf16_buf.append(0x00)

                    # If it's ASCII, decode as ASCII
                    is_ascii = all(0x20 <= c <= 0x7E for c in char_buf)
                    if is_ascii:
                        s = bytes(char_buf).decode('ascii', errors='ignore')
                    else:
                        s = utf16_buf.decode('utf-16le', errors='ignore')

                    s = s.strip('\x00 \t\n')
                    if len(s) >= min_len:
                        strings.append((s, i))
                except:
                    pass

            i = j
        else:
            i += 1

    return strings

def extract_all_utf16le_pairs(data: bytes, min_pairs: int = 3) -> list:
    """
    Quét tất cả byte pairs trong file, xây dựng chuỗi từ các pair hợp lệ.
    """
    strings = []
    i = 0
    while i < len(data) - 1:
        b1, b2 = data[i], data[i+1]

        # Valid pair: printable ASCII as UTF-16LE (0xXX 0x00)
        if b2 == 0x00 and 0x20 <= b1 <= 0x7E:
            # Found start of UTF-16LE ASCII string
            j = i
            buf = bytearray()
            while j < len(data) - 1:
                lo, hi = data[j], data[j+1]
                if hi == 0x00 and 0x20 <= lo <= 0x7E:
                    buf.append(lo)
                    j += 2
                elif lo == 0x00 and hi == 0x00:
                    # Null terminator
                    j += 2
                    break
                else:
                    break

            if len(buf) >= min_pairs:
                try:
                    s = buf.decode('ascii', errors='ignore').strip()
                    if s and len(s) >= min_pairs:
                        strings.append(s)
                except:
                    pass

            i = j
        else:
            i += 1

    return strings

def pattern_match(strings: list) -> dict:
    """Pattern matching trên danh sách strings."""
    results = {
        'xdata_fields': set(),
        'excel_sheets': set(),
        'regapp_names': set(),
        'cell_refs': set(),
        'dce_layers': set(),
        'dce_commands': set(),
        'dce_blocks': set(),
        'gan_dl_classes': set(),
        'dimstyles': set(),
        'vba_modules': set(),
        'all_interesting': [],
    }

    xdata_set = {'SH', 'DK', 'SL', 'L', 'TK', 'SKC', 'TSL', 'KL', 'sumL', 'Lall', 'L1', 'L2', 'L3'}
    excel_kw = {'Sheet', 'DATA', 'INPUT', 'OUTPUT', 'Design', 'Beam', 'Column', 'Slab',
                'Wall', 'Foundation', 'Excel', 'Table', 'Summary'}
    gan_dl_set = {'GanDL', 'GanDLL', 'GanDLX'}
    dce_layer_prefixes = {'DCE_', 'Dce_', 'KC_', 'KC-'}
    dimstyle_prefix = 'Dce_'

    # Normalize to plain strings
    plain_strings = []
    for item in strings:
        if isinstance(item, tuple):
            plain_strings.append(item[0])
        else:
            plain_strings.append(str(item))

    for s in plain_strings:
        s = str(s).strip()
        if not s or len(s) < 2:
            continue

        # Skip obvious noise
        if s.startswith('System.') or s.startswith('Microsoft.'):
            continue

        # XData fields
        if s in xdata_set:
            results['xdata_fields'].add(s)

        # Excel sheets
        if any(kw.lower() in s.lower() for kw in excel_kw) and len(s) < 100:
            results['excel_sheets'].add(s)

        # Cell refs
        if re.match(r'^[A-Z]{1,3}\d{1,4}$', s):
            results['cell_refs'].add(s)

        # RegApp names
        if re.match(r'^[A-Z][A-Z0-9_]{2,20}$', s) and len(s) <= 20:
            results['regapp_names'].add(s)

        # DCE Layers
        if any(s.startswith(p) for p in dce_layer_prefixes) and len(s) < 50:
            results['dce_layers'].add(s)

        # DimStyles
        if s.startswith(dimstyle_prefix) and 'MV' in s:
            results['dimstyles'].add(s)

        # GanDL classes
        if s.startswith('GanDL') and len(s) < 100:
            results['gan_dl_classes'].add(s)

        # DCE Commands (heuristic)
        if re.match(r'^(Ve|Gan|Quet|Sua|LK|Shop|ThamSo|TLBan|TSChia)[\w]+$', s):
            if len(s) >= 5 and len(s) < 60:
                results['dce_commands'].add(s)

        # Blocks
        if re.match(r'^TK\d+[A-Za-z]*$', s) or re.match(r'^ChuanBiTK\d+$', s):
            results['dce_blocks'].add(s)

        # Interesting strings
        if len(s) >= 4 and len(s) <= 80:
            results['all_interesting'].append(s)

    return {k: sorted(list(v)) for k, v in results.items()}

def scan_dll(dll_path: Path) -> dict:
    """Quét một DLL với cả ASCII và UTF-16LE."""
    print(f"\n{'='*60}")
    print(f"Scanning: {dll_path.name}")
    print(f"{'='*60}")

    results = {
        'dll_name': dll_path.name,
        'dll_size': 0,
        'scan_size': 0,
        'ascii_strings': 0,
        'utf16_strings': 0,
        'patterns': {},
    }

    if not dll_path.exists():
        print("  NOT FOUND")
        return results

    size = dll_path.stat().st_size
    results['dll_size'] = size
    scan_size = min(size, MAX_FILE_SIZE)
    results['scan_size'] = scan_size
    print(f"  Size: {size:,} bytes, scanning: {scan_size:,} bytes")

    with open(dll_path, 'rb') as f:
        data = f.read(scan_size)

    # Method 1: ASCII strings
    print("  Extracting ASCII strings...")
    ascii_strings = extract_ascii_strings(data)
    results['ascii_strings'] = len(ascii_strings)
    print(f"  Found {len(ascii_strings)} ASCII strings")

    # Method 2: UTF-16LE via byte pairs
    print("  Extracting UTF-16LE strings (byte pairs)...")
    utf16_strings = extract_all_utf16le_pairs(data)
    results['utf16_strings'] = len(utf16_strings)
    print(f"  Found {len(utf16_strings)} UTF-16LE strings")

    # Combine and deduplicate (ASCII strings are tuples, UTF-16 are plain strings)
    all_strings_with_offset = ascii_strings + [(s, 0) for s in utf16_strings]
    all_strings = list(set([s for s in ascii_strings] + utf16_strings))

    # Pattern match
    print("  Pattern matching...")
    results['patterns'] = pattern_match(all_strings_with_offset)

    # Print findings
    print(f"\n  Results:")
    print(f"    XData fields: {results['patterns']['xdata_fields']}")
    print(f"    GanDL classes: {results['patterns']['gan_dl_classes']}")
    print(f"    DimStyles: {results['patterns']['dimstyles']}")
    print(f"    Cell refs: {len(results['patterns']['cell_refs'])} found")
    print(f"    Excel sheets: {results['patterns']['excel_sheets'][:15]}")
    print(f"    DCE commands: {len(results['patterns']['dce_commands'])} found")
    print(f"    DCE layers: {len(results['patterns']['dce_layers'])} found")
    print(f"    DCE blocks: {results['patterns']['dce_blocks'][:15]}")
    print(f"    RegApp names: {results['patterns']['regapp_names'][:15]}")

    # Sample interesting strings
    print(f"\n  Sample interesting strings:")
    sample = results['patterns']['all_interesting'][:30]
    for s in sample:
        print(f"    {repr(s)}")

    return results

def main():
    print("="*70)
    print("DCE Pro - Binary String Scanner (ASCII + UTF-16LE)")
    print("="*70)

    all_results = []

    for dll in TARGET_DLLS:
        if dll.exists():
            result = scan_dll(dll)
            all_results.append(result)
        else:
            print(f"\nSKIP: {dll.name} (not found)")

    # Merge patterns
    merged = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'version': '5.0.0',
            'scanner': 'dce_binary_scanner.py',
            'total_dlls_scanned': len(all_results),
            'total_strings': {
                'ascii': sum(r['ascii_strings'] for r in all_results),
                'utf16': sum(r['utf16_strings'] for r in all_results),
            }
        },
        'per_dll': all_results,
        'merged': {
            'xdata_fields': set(),
            'excel_sheets': set(),
            'regapp_names': set(),
            'cell_refs': set(),
            'dce_layers': set(),
            'dce_commands': set(),
            'dce_blocks': set(),
            'gan_dl_classes': set(),
            'dimstyles': set(),
        }
    }

    for r in all_results:
        p = r['patterns']
        for key in merged['merged']:
            merged['merged'][key].update(p.get(key, []))

    merged['merged'] = {k: sorted(list(v)) for k, v in merged['merged'].items()}

    # Update schema JSON
    json_path = OUTPUT_DIR / "DCE_DEEP_OPERATION_SCHEMA.json"
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            schema = json.load(f)
    except:
        schema = {}

    schema['binary_scan_v5'] = merged
    schema['metadata']['binary_scanned_at'] = merged['metadata']['generated_at']
    schema['metadata']['binary_total_strings'] = (
        merged['metadata']['total_strings']['ascii'] +
        merged['metadata']['total_strings']['utf16']
    )

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(schema, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*70}")
    print("FINAL MERGED RESULTS")
    print("="*70)
    print(f"\nXData fields: {merged['merged']['xdata_fields']}")
    print(f"GanDL classes: {merged['merged']['gan_dl_classes']}")
    print(f"DimStyles: {merged['merged']['dimstyles']}")
    print(f"Cell refs: {merged['merged']['cell_refs'][:20]}")
    print(f"Excel sheets: {merged['merged']['excel_sheets'][:20]}")
    print(f"DCE commands: {merged['merged']['dce_commands'][:30]}")
    print(f"DCE layers: {merged['merged']['dce_layers'][:30]}")
    print(f"DCE blocks: {merged['merged']['dce_blocks'][:20]}")
    print(f"RegApp names: {merged['merged']['regapp_names'][:20]}")

    print(f"\nSaved: {json_path}")
    return merged

if __name__ == "__main__":
    main()
