#!/usr/bin/env python3
"""
dce_utf16le_scanner.py
Quét chuỗi UTF-16LE (chuẩn .NET #US heap) từ các DLL chính của DCE Pro.
.NET User Strings lưu dưới dạng UTF-16LE null-terminated.
"""

import sys
import os
import re
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Force UTF-8 output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Configuration
DCE_PRO_ROOT = Path(r"C:\Dce Pro")
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "docs"

# Target DLLs (cỡ < 50MB để quét nhanh)
TARGET_DLLS = [
    DCE_PRO_ROOT / "V.2020" / "DCE Excel.dll",   # 10.8MB
    DCE_PRO_ROOT / "DbimSteelAutocad.dll",          # 4.2MB
    DCE_PRO_ROOT / "V.2020" / "DceAnalyssiss64.dll",  # 346KB
]

# Maximum file size to scan (50MB)
MAX_SCAN_SIZE = 50 * 1024 * 1024

def is_valid_utf16le_char(byte_pair: bytes) -> bool:
    """Kiểm tra byte pair có phải là ký tự UTF-16LE hợp lệ."""
    if len(byte_pair) != 2:
        return False
    lo, hi = byte_pair
    # ASCII printable: 0x00-0x7F (byte cao = 0, byte thấp = ASCII)
    if hi == 0x00 and 0x20 <= lo <= 0x7E:
        return True
    # Vietnamese extended: 0x00-0xFF (Latin Supplement)
    if 0x00 <= hi <= 0xFF and 0x00 <= lo <= 0xFF:
        return True
    return False

def extract_utf16le_strings(data: bytes, min_len: int = 4, max_len: int = 300) -> list:
    """
    Trích xuất chuỗi UTF-16LE từ binary data.

    .NET #US heap format:
    - Blob header: varint (byte count, high bit = continuation flag)
    - Payload: UTF-16LE characters
    - Null-terminated (byte pair 0x00 0x00)
    """
    strings = []
    i = 0
    current = bytearray()

    while i < len(data) - 1:
        # Tìm valid UTF-16LE sequence
        if is_valid_utf16le_char(data[i:i+2]):
            current.extend(data[i:i+2])
            i += 2
        else:
            # Kết thúc một chuỗi
            if len(current) >= min_len * 2:
                try:
                    s = current.decode('utf-16le', errors='ignore').strip('\x00 ')
                    # Filter: phải có ít nhất 1 ký tự alphanumeric
                    if len(s) >= min_len and re.search(r'[A-Za-zÀ-ỹ0-9]', s):
                        # Không phải toàn spaces/punctuation
                        alpha_count = sum(1 for c in s if c.isalnum())
                        if alpha_count >= min_len:
                            strings.append(s)
                except:
                    pass
            current.clear()
            i += 1  # Skip byte không hợp lệ

    # Check cuối file
    if len(current) >= min_len * 2:
        try:
            s = current.decode('utf-16le', errors='ignore').strip('\x00 ')
            if len(s) >= min_len and re.search(r'[A-Za-zÀ-ỹ0-9]', s):
                strings.append(s)
        except:
            pass

    return strings

def scan_dll_fast_utf16(dll_path: Path) -> dict:
    """
    Quét nhanh DLL tìm chuỗi UTF-16LE.
    Đọc chunk-by-chunk để tiết kiệm memory.
    """
    print(f"\n{'='*60}")
    print(f"UTF-16LE Scanning: {dll_path.name}")
    print(f"{'='*60}")

    results = {
        'dll_name': dll_path.name,
        'dll_size': dll_path.stat().st_size if dll_path.exists() else 0,
        'total_utf16_strings': 0,
        'all_strings': [],
        'patterns': {
            'xdata_fields': [],
            'excel_sheets': [],
            'regapp_names': [],
            'cell_refs': [],
            'dce_layers': [],
            'dce_commands': [],
            'dce_blocks': [],
            'gan_dl_classes': [],
            'dimstyles': [],
            'numeric_strings': [],
        }
    }

    if not dll_path.exists():
        print(f"  NOT FOUND: {dll_path}")
        return results

    try:
        # Đọc toàn bộ file (hoặc giới hạn)
        file_size = dll_path.stat().st_size
        scan_size = min(file_size, MAX_SCAN_SIZE)
        print(f"  File size: {file_size:,} bytes, scanning: {scan_size:,} bytes")

        with open(dll_path, 'rb') as f:
            data = f.read(scan_size)

        print(f"  Extracting UTF-16LE strings...")
        all_strings = extract_utf16le_strings(data)
        print(f"  Found {len(all_strings)} UTF-16LE strings")

        results['total_utf16_strings'] = len(all_strings)
        results['all_strings'] = all_strings[:5000]  # Store first 5000

        # Pattern matching
        xdata_fields = {'SH', 'DK', 'SL', 'L', 'TK', 'SKC', 'TSL', 'KL', 'sumL', 'Lall', 'L1', 'L2', 'L3'}
        excel_keywords = {'Sheet', 'DATA', 'INPUT', 'OUTPUT', 'Design', 'Beam', 'Column', 'Slab', 'Wall', 'Foundation', 'Excel'}
        regapp_pattern = re.compile(r'^[A-Z][A-Z0-9_]{2,16}$')
        cell_pattern = re.compile(r'^[A-Z]{1,3}\d{1,4}$')
        dce_layer_pattern = re.compile(r'^Dce_[A-Z][A-Za-z0-9_]*$')
        dce_cmd_pattern = re.compile(r'^(Ve|Dam|Cot|Vach|San|Mong|Gan|Quet|Sua|LK|Shop)[\w]+$')
        gan_dl_pattern = re.compile(r'^GanDL[A-Za-z]*$')
        dimstyle_pattern = re.compile(r'^Dce_\d{1,3}MV$')

        for s in all_strings:
            # XData fields
            if s in xdata_fields:
                results['patterns']['xdata_fields'].append(s)

            # Excel sheets
            if any(kw in s for kw in excel_keywords) and len(s) < 50:
                results['patterns']['excel_sheets'].append(s)

            # RegApp names
            if regapp_pattern.match(s) and len(s) <= 20:
                results['patterns']['regapp_names'].append(s)

            # Cell refs
            if cell_pattern.match(s):
                results['patterns']['cell_refs'].append(s)

            # DCE Layers
            if dce_layer_pattern.match(s):
                results['patterns']['dce_layers'].append(s)

            # DCE Commands
            if dce_cmd_pattern.match(s) and len(s) < 50:
                results['patterns']['dce_commands'].append(s)

            # GanDL classes
            if gan_dl_pattern.match(s):
                results['patterns']['gan_dl_classes'].append(s)

            # DimStyles
            if dimstyle_pattern.match(s):
                results['patterns']['dimstyles'].append(s)

            # Numeric strings (lengths, diameters)
            if re.match(r'^\d{3,7}$', s) and 100 <= int(s) <= 20000:
                results['patterns']['numeric_strings'].append(s)

        # Deduplicate
        for key in results['patterns']:
            results['patterns'][key] = sorted(list(set(results['patterns'][key])))

        # Print findings
        print(f"\n  Findings:")
        print(f"    XData fields: {results['patterns']['xdata_fields']}")
        print(f"    RegApp names: {results['patterns']['regapp_names'][:10]}")
        print(f"    GanDL classes: {results['patterns']['gan_dl_classes']}")
        print(f"    DimStyles: {results['patterns']['dimstyles']}")
        print(f"    DCE commands: {len(results['patterns']['dce_commands'])} found")
        print(f"    DCE layers: {len(results['patterns']['dce_layers'])} found")
        print(f"    Excel sheets: {len(results['patterns']['excel_sheets'])} found")
        print(f"    Cell refs: {len(results['patterns']['cell_refs'])} found")

        # Print sample strings
        print(f"\n  Sample UTF-16LE strings (first 30):")
        sample = [s for s in all_strings if 4 <= len(s) <= 80][:30]
        for s in sample:
            print(f"    {repr(s)}")

    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()

    return results

def scan_dll_ascii_compat(dll_path: Path) -> dict:
    """
    Quét DLL tìm ASCII-compatible strings (1-byte) trong UTF-16LE context.
    Strings ASCII trong .NET: mỗi char = 2 bytes, byte cao = 0x00.
    """
    print(f"\n  [ASCII-compat mode]")

    results = {
        'dll_name': dll_path.name,
        'ascii_compat_strings': [],
        'patterns': {
            'xdata_fields': [],
            'excel_sheets': [],
            'regapp_names': [],
            'cell_refs': [],
            'dce_layers': [],
            'dce_commands': [],
            'gan_dl_classes': [],
            'dimstyles': [],
        }
    }

    if not dll_path.exists():
        return results

    try:
        file_size = dll_path.stat().st_size
        scan_size = min(file_size, MAX_SCAN_SIZE)

        with open(dll_path, 'rb') as f:
            data = f.read(scan_size)

        # Tìm pattern: 0xXX 0x00 (UTF-16LE ASCII)
        # Chuyển đổi các cặp byte có byte cao = 0x00 thành ASCII
        utf16_ascii = bytearray()
        found_strings = []
        i = 0

        while i < len(data) - 1:
            lo, hi = data[i], data[i+1]
            if hi == 0x00 and 0x20 <= lo <= 0x7E:
                # Valid UTF-16LE ASCII char
                utf16_ascii.append(lo)
                i += 2
            else:
                # Kết thúc chuỗi
                if len(utf16_ascii) >= 4:
                    s = utf16_ascii.decode('ascii', errors='ignore').strip()
                    if s and re.search(r'[A-Za-z]', s):
                        found_strings.append(s)
                utf16_ascii.clear()
                i += 1

        results['ascii_compat_strings'] = found_strings[:3000]

        # Pattern matching on ASCII strings extracted from UTF-16LE context
        xdata_fields = {'SH', 'DK', 'SL', 'L', 'TK', 'SKC', 'TSL', 'KL', 'sumL', 'Lall', 'L1', 'L2', 'L3'}
        excel_keywords = {'Sheet', 'DATA', 'INPUT', 'OUTPUT', 'Design', 'Beam', 'Column', 'Slab'}
        regapp_pattern = re.compile(r'^[A-Z][A-Z0-9_]{2,16}$')
        cell_pattern = re.compile(r'^[A-Z]{1,3}\d{1,4}$')
        dce_layer_pattern = re.compile(r'^Dce_[A-Z][A-Za-z0-9_]*$')
        dce_cmd_pattern = re.compile(r'^(Ve|Dam|Cot|Vach|San|Mong|Gan|Quet|Sua|LK|Shop)[\w]+$')
        gan_dl_pattern = re.compile(r'^GanDL[A-Za-z]*$')
        dimstyle_pattern = re.compile(r'^Dce_\d{1,3}MV$')

        for s in found_strings:
            if s in xdata_fields:
                results['patterns']['xdata_fields'].append(s)
            if any(kw in s for kw in excel_keywords) and len(s) < 50:
                results['patterns']['excel_sheets'].append(s)
            if regapp_pattern.match(s) and len(s) <= 20:
                results['patterns']['regapp_names'].append(s)
            if cell_pattern.match(s):
                results['patterns']['cell_refs'].append(s)
            if dce_layer_pattern.match(s):
                results['patterns']['dce_layers'].append(s)
            if dce_cmd_pattern.match(s) and len(s) < 50:
                results['patterns']['dce_commands'].append(s)
            if gan_dl_pattern.match(s):
                results['patterns']['gan_dl_classes'].append(s)
            if dimstyle_pattern.match(s):
                results['patterns']['dimstyles'].append(s)

        for key in results['patterns']:
            results['patterns'][key] = sorted(list(set(results['patterns'][key])))

        print(f"    Found {len(found_strings)} ASCII-compat strings from UTF-16LE")
        print(f"    XData fields: {results['patterns']['xdata_fields']}")
        print(f"    GanDL: {results['patterns']['gan_dl_classes']}")
        print(f"    DimStyles: {results['patterns']['dimstyles']}")
        print(f"    Cell refs: {len(results['patterns']['cell_refs'])}")
        print(f"    Commands: {len(results['patterns']['dce_commands'])}")

    except Exception as e:
        print(f"    ERROR: {e}")

    return results

def main():
    print("="*70)
    print("DCE Pro - UTF-16LE String Scanner (.NET #US Heap)")
    print("="*70)

    all_results = []

    for dll_path in TARGET_DLLS:
        if not dll_path.exists():
            print(f"\nSKIP: {dll_path} (not found)")
            continue

        # Skip if too large
        size_mb = dll_path.stat().st_size / (1024*1024)
        if size_mb > 50:
            print(f"\nSKIP: {dll_path.name} ({size_mb:.1f}MB - too large)")
            continue

        # UTF-16LE mode
        result = scan_dll_fast_utf16(dll_path)
        all_results.append(result)

        # ASCII-compat mode
        result2 = scan_dll_ascii_compat(dll_path)

        # Merge results
        for key in result2.get('patterns', {}):
            result['patterns'][key] = sorted(list(set(
                result['patterns'].get(key, []) + result2['patterns'].get(key, [])
            )))

    # Merge all results
    merged = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'version': '4.0.0',
            'description': 'DCE Pro UTF-16LE (.NET #US Heap) String Analysis',
            'scanner': 'dce_utf16le_scanner.py',
            'total_strings_found': sum(r['total_utf16_strings'] for r in all_results)
        },
        'per_dll': all_results,
        'merged_patterns': {
            'xdata_fields': [],
            'excel_sheets': [],
            'regapp_names': [],
            'cell_refs': [],
            'dce_layers': [],
            'dce_commands': [],
            'gan_dl_classes': [],
            'dimstyles': [],
        }
    }

    # Merge all patterns
    for key in merged['merged_patterns']:
        for r in all_results:
            merged['merged_patterns'][key] = sorted(list(set(
                merged['merged_patterns'][key] + r['patterns'].get(key, [])
            )))

    # Save JSON
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    json_path = OUTPUT_DIR / "DCE_DEEP_OPERATION_SCHEMA.json"

    # Update existing schema
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            existing = json.load(f)
    except:
        existing = {}

    # Update with new UTF-16LE findings
    existing['utf16le_analysis'] = merged
    existing['metadata']['utf16le_scanned_at'] = merged['metadata']['generated_at']
    existing['metadata']['utf16le_total_strings'] = merged['metadata']['total_strings_found']

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*70}")
    print("MERGED RESULTS")
    print("="*70)
    print(f"\nXData fields: {merged['merged_patterns']['xdata_fields']}")
    print(f"RegApp names: {merged['merged_patterns']['regapp_names'][:20]}")
    print(f"GanDL classes: {merged['merged_patterns']['gan_dl_classes']}")
    print(f"DimStyles: {merged['merged_patterns']['dimstyles']}")
    print(f"DCE commands: {len(merged['merged_patterns']['dce_commands'])} found")
    print(f"DCE layers: {merged['merged_patterns']['dce_layers'][:20]}")
    print(f"Cell refs: {len(merged['merged_patterns']['cell_refs'])} found")
    print(f"Excel sheets: {merged['merged_patterns']['excel_sheets'][:20]}")

    print(f"\nSaved: {json_path}")

    return merged

if __name__ == "__main__":
    main()
