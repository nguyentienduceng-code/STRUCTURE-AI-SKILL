#!/usr/bin/env python3
"""
Envelope Summary Generator — Tạo Envelope Summary JSON từ raw force data

Mục đích:
- Giảm kích thước handoff JSON (từ full raw → envelope values)
- Tiết kiệm token cho Claude context
- Lưu trữ full data riêng cho debugging

Usage:
    python envelope_summary.py --input raw_forces.json --element B1 --output envelope.json
    python envelope_summary.py --input raw_forces.json --summary-only  # In ra console
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

# Ensure UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')


# ============================================================================
# CONFIGURATION
# ============================================================================

DEFAULT_THRESHOLDS = {
    "variance_pct": 5.0,      # Warn if max/min differ by >5%
    "extreme_ratio": 10.0,     # Warn if max/min ratio > 10 (possible error)
}

COLORS = {
    "GREEN": "\033[92m",
    "YELLOW": "\033[93m",
    "RED": "\033[91m",
    "ORANGE": "\033[38;5;214m",
    "BLUE": "\033[94m",
    "BOLD": "\033[1m",
    "RESET": "\033[0m"
}


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class EnvelopeValue:
    """Một giá trị envelope đơn lẻ"""
    key: str
    value: float
    unit: str
    combo_id: Optional[str] = None
    index: Optional[int] = None

    # Thêm metadata để traceback
    is_max: bool = False
    is_min: bool = False
    is_extreme: bool = False  # max, min, or critical


@dataclass
class EnvelopeSummary:
    """Tóm tắt envelope của một loại lực"""
    force_type: str  # "moment", "shear", "axial", "torsion", "deflection"
    max_value: EnvelopeValue
    min_value: EnvelopeValue
    abs_max_value: EnvelopeValue

    # Statistics
    count: int = 0              # Số lượng values
    mean: Optional[float] = None
    std_dev: Optional[float] = None

    # Warnings
    warnings: List[str] = None

    # Full data reference (KHÔNG include trong envelope, chỉ để debug)
    _full_count: int = 0

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


# ============================================================================
# CORE ENVELOPE CALCULATION
# ============================================================================

class EnvelopeCalculator:
    """Tính toán envelope từ raw data"""

    def __init__(self, thresholds: Dict = None):
        self.thresholds = thresholds or DEFAULT_THRESHOLDS
        self.warnings = []

    def extract_force_values(self, data: Any, force_type: str) -> List[EnvelopeValue]:
        """
        Trích xuất tất cả giá trị lực từ data structure.

        Hỗ trợ nhiều format:
        - Simple dict: {"M_combos": [78.5, 85.2, 92.1]}
        - Nested: {"results": {"M_ed": {"combos": [...]}}}
        - Array of objects: [{"M": 78.5, "combo": "C1"}, ...]
        """
        values = []

        # Format 1: Direct array
        if isinstance(data, dict):
            for key in data.keys():
                if force_type.lower() in key.lower():
                    val = data[key]
                    if isinstance(val, list):
                        for i, v in enumerate(val):
                            if isinstance(v, (int, float)):
                                values.append(EnvelopeValue(
                                    key=key,
                                    value=v,
                                    unit="kN.m" if "M" in key else "kN",
                                    index=i,
                                    combo_id=f"{key}_{i}"
                                ))
                    elif isinstance(val, (int, float)):
                        values.append(EnvelopeValue(
                            key=key,
                            value=val,
                            unit="kN.m" if "M" in key else "kN",
                            combo_id=key
                        ))

        # Format 2: Nested with combos
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, dict):
                    for key, val in item.items():
                        if isinstance(val, (int, float)) and force_type.lower() in key.lower():
                            combo = item.get("combo", item.get("case", f"item_{i}"))
                            values.append(EnvelopeValue(
                                key=key,
                                value=val,
                                unit="kN.m" if "M" in key else "kN",
                                index=i,
                                combo_id=combo
                            ))
                elif isinstance(item, (int, float)):
                    values.append(EnvelopeValue(
                        key=force_type,
                        value=item,
                        unit="kN.m" if force_type == "M" else "kN",
                        index=i,
                        combo_id=f"case_{i}"
                    ))

        return values

    def calculate_envelope(self, values: List[EnvelopeValue], force_type: str) -> EnvelopeSummary:
        """Tính envelope summary từ danh sách giá trị"""

        if not values:
            # Return empty envelope
            return EnvelopeSummary(
                force_type=force_type,
                max_value=EnvelopeValue(key="N/A", value=0, unit="N/A"),
                min_value=EnvelopeValue(key="N/A", value=0, unit="N/A"),
                abs_max_value=EnvelopeValue(key="N/A", value=0, unit="N/A"),
                count=0,
                warnings=["No data available"]
            )

        # Find max/min
        max_val = max(values, key=lambda x: x.value)
        min_val = min(values, key=lambda x: x.value)
        abs_max_val = max(values, key=lambda x: abs(x.value))

        # Mark flags
        max_val.is_max = True
        min_val.is_min = True
        if abs_max_val == max_val or abs_max_val == min_val:
            abs_max_val.is_extreme = True

        # Statistics
        numeric_vals = [v.value for v in values]
        mean = sum(numeric_vals) / len(numeric_vals)

        # Std dev
        variance = sum((v - mean) ** 2 for v in numeric_vals) / len(numeric_vals)
        std_dev = variance ** 0.5

        # Warnings
        warnings = []

        # Check variance
        if max_val.value != 0:
            variance_pct = abs(max_val.value - min_val.value) / abs(max_val.value) * 100
            if variance_pct > self.thresholds["variance_pct"]:
                warnings.append(
                    f"High variance ({variance_pct:.1f}%) between max/min "
                    f"— possible modeling error"
                )

        # Check extreme ratio
        if min_val.value != 0:
            ratio = abs(max_val.value / min_val.value)
            if ratio > self.thresholds["extreme_ratio"]:
                warnings.append(
                    f"Extreme ratio (|max/min| = {ratio:.1f}) exceeds threshold "
                    f"— verify load combinations"
                )

        return EnvelopeSummary(
            force_type=force_type,
            max_value=max_val,
            min_value=min_val,
            abs_max_value=abs_max_val,
            count=len(values),
            mean=round(mean, 3),
            std_dev=round(std_dev, 3),
            warnings=warnings,
            _full_count=len(values)
        )

    def process_raw_data(self, data: Dict) -> Dict[str, EnvelopeSummary]:
        """
        Xử lý toàn bộ raw data → trả về dict envelope summaries.

        Tự động detect các loại lực: M, V, N, T, f (deflection)
        """
        results = {}

        # Force type mapping
        force_mappings = {
            "moment": ["M", "moment", "momen"],
            "shear": ["V", "shear", "cat"],
            "axial": ["N", "axial", "phuong"],
            "torsion": ["T", "tor", "xoan"],
            "deflection": ["f", "delta", "vong", "deflection"]
        }

        for force_type, keywords in force_mappings.items():
            # Search for matching keys
            all_values = []

            def search_recursive(obj, path=""):
                if isinstance(obj, dict):
                    for key, val in obj.items():
                        full_key = f"{path}.{key}" if path else key
                        # Check if key matches any keyword
                        if any(kw.lower() in key.lower() for kw in keywords):
                            if isinstance(val, list):
                                for i, v in enumerate(val):
                                    if isinstance(v, (int, float)):
                                        all_values.append(EnvelopeValue(
                                            key=key,
                                            value=v,
                                            unit="mm" if force_type == "deflection" else "kN",
                                            index=i,
                                            combo_id=f"{key}_{i}"
                                        ))
                            elif isinstance(val, (int, float)):
                                all_values.append(EnvelopeValue(
                                    key=key,
                                    value=val,
                                    unit="mm" if force_type == "deflection" else "kN",
                                    combo_id=key
                                ))
                        else:
                            search_recursive(val, full_key)
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        search_recursive(item, f"{path}[{i}]")

            search_recursive(data)

            if all_values:
                results[force_type] = self.calculate_envelope(all_values, force_type)
                self.warnings.extend(results[force_type].warnings)

        return results

    def generate_envelope_json(self, raw_data: Dict, element_id: str = "UNKNOWN") -> Dict:
        """Tạo envelope JSON hoàn chỉnh cho handoff"""

        summaries = self.process_raw_data(raw_data)

        # Build envelope payload
        envelope_payload = {}
        for force_type, summary in summaries.items():
            key = f"{force_type}_envelope"
            envelope_payload[key] = {
                f"{force_type}_max": summary.max_value.value,
                f"{force_type}_max_combo": summary.max_value.combo_id,
                f"{force_type}_min": summary.min_value.value,
                f"{force_type}_min_combo": summary.min_value.combo_id,
                f"{force_type}_abs_max": summary.abs_max_value.value,
                f"{force_type}_abs_max_combo": summary.abs_max_value.combo_id,
                "count": summary.count,
                "mean": summary.mean,
                "std_dev": summary.std_dev,
                "unit": summary.max_value.unit
            }

        # Build full response
        return {
            "envelope_summary": {
                "element_id": element_id,
                "generated_at": datetime.now().isoformat(),
                "total_forces": sum(s.count for s in summaries.values()),
                "total_combinations_processed": max((s.count for s in summaries.values()), default=0),
                "warnings": self.warnings if self.warnings else None,
                "envelopes": envelope_payload,
                "_note": "Full raw data stored separately in _debug/ folder"
            },
            "_metadata": {
                "version": "1.0.0",
                "tool": "envelope_summary.py",
                "thresholds": self.thresholds
            }
        }


# ============================================================================
# CLI
# ============================================================================

def print_envelope_table(summary: EnvelopeSummary):
    """In bảng envelope ra console"""

    force = summary.force_type.upper()
    unit = summary.max_value.unit

    print(f"\n{'─' * 60}")
    print(f"  {COLORS['BOLD']}{force} ENVELOPE{ COLORS['RESET']}")
    print(f"{'─' * 60}")
    print(f"  {'Type':<12} {'Value':<12} {'Combo':<15} {'Unit':<8}")
    print(f"  {'─' * 50}")
    print(f"  {'MAX':<12} {summary.max_value.value:>10.3f} {summary.max_value.combo_id:<15} {unit:<8}")
    print(f"  {'MIN':<12} {summary.min_value.value:>10.3f} {summary.min_value.combo_id:<15} {unit:<8}")
    print(f"  {'ABS_MAX':<12} {summary.abs_max_value.value:>10.3f} {summary.abs_max_value.combo_id:<15} {unit:<8}")

    if summary.mean is not None:
        print(f"  {'─' * 50}")
        print(f"  {'MEAN':<12} {summary.mean:>10.3f} {'':15} {unit:<8}")
        print(f"  {'STD_DEV':<12} {summary.std_dev:>10.3f} {'':15} {unit:<8}")
        print(f"  {'COUNT':<12} {summary.count:>10}")

    # Warnings
    for w in summary.warnings:
        print(f"  {COLORS['ORANGE']}⚠ {w}{COLORS['RESET']}")

    print(f"{'─' * 60}")


def main():
    parser = argparse.ArgumentParser(
        description="Envelope Summary Generator — Tạo envelope JSON từ raw force data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ví dụ:
  python envelope_summary.py --input raw_forces.json --element B1
  python envelope_summary.py --input raw_forces.json --summary-only
  python envelope_summary.py --input data.json --output envelope.json --verbose
        """
    )
    parser.add_argument("--input", "-i", required=True, help="Input JSON file with raw forces")
    parser.add_argument("--output", "-o", help="Output envelope JSON file")
    parser.add_argument("--element", "-e", default="UNKNOWN", help="Element ID (e.g., B1, C2)")
    parser.add_argument("--summary-only", "-s", action="store_true", help="Print summary only, no file output")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Load input
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"{COLORS['RED']}Error: File not found: {args.input}{COLORS['RESET']}")
        sys.exit(1)

    with open(input_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    # Calculate envelopes
    calculator = EnvelopeCalculator()
    envelope_json = calculator.generate_envelope_json(raw_data, args.element)

    # Print summary
    if args.summary_only or args.verbose:
        print(f"\n{COLORS['BLUE']}{COLORS['BOLD']}ENVELOPE SUMMARY: {args.element}{COLORS['RESET']}")
        print(f"Generated: {envelope_json['envelope_summary']['generated_at']}")
        print(f"Total forces: {envelope_json['envelope_summary']['total_forces']}")
        print(f"Total combinations: {envelope_json['envelope_summary']['total_combinations_processed']}")

        # Print each force type table
        for force_type, summary in calculator.process_raw_data(raw_data).items():
            print_envelope_table(summary)

        # Print warnings
        if envelope_json['envelope_summary']['warnings']:
            print(f"\n{COLORS['ORANGE']}⚠ WARNINGS:{COLORS['RESET']}")
            for w in envelope_json['envelope_summary']['warnings']:
                print(f"  • {w}")

    # Output file
    if args.output and not args.summary_only:
        output_path = Path(args.output)

        # Create _debug folder for full data
        debug_dir = output_path.parent / "_debug"
        debug_dir.mkdir(parents=True, exist_ok=True)

        # Save full raw data to debug folder
        debug_file = debug_dir / f"{output_path.stem}_full_data.json"
        with open(debug_file, "w", encoding="utf-8") as f:
            json.dump(raw_data, f, indent=2, ensure_ascii=False)

        # Save envelope summary
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(envelope_json, f, indent=2, ensure_ascii=False)

        print(f"\n{COLORS['GREEN']}✓ Envelope saved: {output_path}{COLORS['RESET']}")
        print(f"  {COLORS['BLUE']}ℹ Full data saved to: {debug_file}{COLORS['RESET']}")
    elif not args.summary_only:
        # Print JSON to stdout
        print(json.dumps(envelope_json, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
