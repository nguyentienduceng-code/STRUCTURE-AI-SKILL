#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SKILL_VERIFY Loại 4: External Software Comparison
So sánh kết quả AI với ETABS/SAP2000/SAFE export.

Input:
- File .xlsx hoặc .csv từ ETABS (format: Element | LoadCase | M | V | N)
- File JSON từ AI tính toán (format: elements[].name, M, V, N)

Output:
- Bảng so sánh theo element
- Phát hiện outliers (>5% cho nội lực, >3% cho η)
- Nguyên nhân có thể + recommendation
"""

import sys
import json
import argparse
import csv
from pathlib import Path
from datetime import datetime

try:
    from openpyxl import load_workbook
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False


THRESHOLDS = {
    "M": 5.0,   # Moment: 5%
    "V": 5.0,   # Shear: 5%
    "N": 5.0,   # Axial: 5%
    "eta": 3.0, # Utilization ratio: 3%
    "As": 10.0  # Rebar area: 10%
}


def parse_etabs_xlsx(xlsx_path):
    """
    Parse file Excel xuất từ ETABS/SAP2000.
    Format mong đợi: Story | Beam | Station | M3 | V2 | P | ...
    """
    if not OPENPYXL_AVAILABLE:
        print("⚠️ openpyxl chưa cài. Chạy: pip install openpyxl", file=sys.stderr)
        return []

    wb = load_workbook(xlsx_path, read_only=True, data_only=True)
    etabs_data = []

    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        rows = list(ws.iter_rows(values_only=True))

        if not rows:
            continue

        # Tìm header row
        header = None
        header_idx = -1
        for idx, row in enumerate(rows[:5]):
            if row and any(h and ("beam" in str(h).lower() or "name" in str(h).lower() or "element" in str(h).lower()) for h in row):
                header = [str(h).strip().lower() if h else "" for h in row]
                header_idx = idx
                break

        if header is None:
            continue

        # Tìm cột index
        col_map = {}
        for col_idx, h in enumerate(header):
            if "beam" in h or "name" in h or "element" in h:
                col_map["name"] = col_idx
            elif h == "m3" or "moment" in h or "m_max" in h:
                col_map["M"] = col_idx
            elif h == "v2" or "shear" in h:
                col_map["V"] = col_idx
            elif h in ("p", "axial", "n"):
                col_map["N"] = col_idx

        if "name" not in col_map:
            continue

        for row in rows[header_idx + 1:]:
            if not row or row[col_map["name"]] is None:
                continue
            element_name = str(row[col_map["name"]]).strip()
            if not element_name or element_name.startswith("---"):
                continue
            entry = {"element": element_name}
            for field in ("M", "V", "N"):
                if field in col_map and row[col_map[field]] is not None:
                    try:
                        entry[field] = float(row[col_map[field]])
                    except (ValueError, TypeError):
                        pass
            etabs_data.append(entry)

    wb.close()
    return etabs_data


def parse_etabs_csv(csv_path):
    """
    Parse file CSV từ ETABS export.
    """
    etabs_data = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            entry = {"element": row.get("Beam") or row.get("Name") or row.get("Element")}
            try:
                if row.get("M3") or row.get("M"):
                    entry["M"] = float(row.get("M3") or row.get("M"))
                if row.get("V2") or row.get("V"):
                    entry["V"] = float(row.get("V2") or row.get("V"))
                if row.get("P") or row.get("N"):
                    entry["N"] = float(row.get("P") or row.get("N"))
            except (ValueError, TypeError):
                pass
            if entry["element"]:
                etabs_data.append(entry)
    return etabs_data


def load_ai_results(json_path):
    """
    Load JSON output từ AI tính toán.
    Format mong đợi:
    {
      "results": [
        {"element": "B1", "M_Ed": 250, "M_Rd": 310, "eta": 0.806, "V_Ed": 150, "V_Rd": 200}
      ]
    }
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    results = data.get("results", data) if isinstance(data, dict) else data
    ai_data = []
    for item in results:
        entry = {"element": item.get("element") or item.get("name")}
        for field_in, field_out in [("M_Ed", "M"), ("V_Ed", "V"), ("N_Ed", "N"),
                                     ("M_Rd", None), ("V_Rd", None), ("eta", "eta"),
                                     ("As", "As")]:
            if field_in in item:
                if field_out is None and field_in in ("M_Rd", "V_Rd"):
                    continue
                entry[field_out if field_out else field_in] = item[field_in]
        ai_data.append(entry)
    return ai_data


def compare_results(etabs_data, ai_data, thresholds=None):
    """
    So sánh giữa AI và ETABS, phát hiện outlier.
    """
    if thresholds is None:
        thresholds = THRESHOLDS

    # Match elements
    ai_dict = {item["element"]: item for item in ai_data if item.get("element")}
    comparisons = []
    unmatched = []

    for etabs_item in etabs_data:
        elem = etabs_item["element"]
        ai_item = ai_dict.get(elem)
        if not ai_item:
            unmatched.append({"element": elem, "reason": "Not found in AI results"})
            continue

        variance = {}
        warnings = []
        for field in ("M", "V", "N", "eta", "As"):
            etabs_val = etabs_item.get(field)
            ai_val = ai_item.get(field)
            if etabs_val is not None and ai_val is not None and etabs_val != 0:
                var_pct = abs(etabs_val - ai_val) / abs(etabs_val) * 100
                variance[field] = round(var_pct, 2)
                threshold = thresholds.get(field, 5.0)
                if var_pct > threshold * 2:  # 2× threshold = CRITICAL
                    severity = "CRITICAL"
                elif var_pct > threshold:
                    severity = "WARNING"
                else:
                    severity = "OK"
                if severity != "OK":
                    warnings.append({
                        "field": field,
                        "etabs": etabs_val,
                        "ai": ai_val,
                        "variance_pct": round(var_pct, 2),
                        "threshold_pct": threshold,
                        "severity": severity
                    })

        comparisons.append({
            "element": elem,
            "etabs_values": {k: etabs_item[k] for k in ("M", "V", "N") if k in etabs_item},
            "ai_values": {k: ai_item[k] for k in ("M", "V", "N") if k in ai_item},
            "variance": variance,
            "warnings": warnings,
            "status": "FAILED" if any(w["severity"] == "CRITICAL" for w in warnings) else ("WARNING" if warnings else "PASS")
        })

    matched_count = len(comparisons)
    total_warnings = sum(1 for c in comparisons if c["status"] == "WARNING")
    total_critical = sum(1 for c in comparisons if c["status"] == "FAILED")
    total_pass = sum(1 for c in comparisons if c["status"] == "PASS")

    return {
        "Verification_ID": f"VRF-ETABS-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "Timestamp": datetime.now().isoformat(),
        "Comparison_Summary": {
            "Total_Etabs_Elements": len(etabs_data),
            "Matched_Count": matched_count,
            "Pass_Count": total_pass,
            "Warning_Count": total_warnings,
            "Critical_Count": total_critical,
            "Unmatched_Count": len(unmatched)
        },
        "Comparisons": comparisons,
        "Unmatched": unmatched,
        "Overall_Status": "FAILED" if total_critical > 0 else ("WARNING" if total_warnings > 0 else "PASS"),
        "Possible_Reasons": [
            "AI dùng tổ hợp tải khác ETABS (phong bì vs 1.2D+1.6L)",
            "AI chưa tính P-Delta (ETABS có)",
            "AI làm tròn sớm hơn ETABS",
            "AI dùng W_pl khác với ETABS (do catalogue section)",
            "ETABS có độ cứng khớp khác AI giả định (rigid vs pinned)"
        ],
        "Thresholds": thresholds,
        "Disclaimer": (
            "Sai lệch giữa AI và ETABS có thể do nhiều nguyên nhân. "
            "Cần kỹ sư có chuyên môn phân tích nguyên nhân trước khi quyết định dùng kết quả nào."
        )
    }


def main():
    parser = argparse.ArgumentParser(description="Compare AI results with ETABS/SAP2000")
    parser.add_argument("--etabs", required=True, help="ETABS export file (.xlsx hoặc .csv)")
    parser.add_argument("--ai", required=True, help="AI results JSON file")
    parser.add_argument("--threshold_M", type=float, default=5.0)
    parser.add_argument("--threshold_V", type=float, default=5.0)
    parser.add_argument("--threshold_eta", type=float, default=3.0)
    parser.add_argument("--output", help="File JSON output")

    args = parser.parse_args()

    # Parse ETABS
    etabs_path = Path(args.etabs)
    if etabs_path.suffix.lower() in (".xlsx", ".xlsm"):
        etabs_data = parse_etabs_xlsx(etabs_path)
    else:
        etabs_data = parse_etabs_csv(etabs_path)

    ai_data = load_ai_results(args.ai)

    thresholds = {
        "M": args.threshold_M,
        "V": args.threshold_V,
        "N": args.threshold_M,
        "eta": args.threshold_eta,
        "As": 10.0
    }

    result = compare_results(etabs_data, ai_data, thresholds)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
