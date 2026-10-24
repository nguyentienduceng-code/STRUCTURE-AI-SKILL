#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SKILL_VERIFY Loại 5: Report Consistency Check
Kiểm tra số liệu trong báo cáo Word/PDF có khớp với JSON handoff gốc hay không.

Input:
- File JSON handoff từ SKILLKC
- File .docx xuất ra từ SKILL_REPORT

Output:
- Danh sách các số liệu bị lệch (mismatch)
- Severity từng mismatch
- Recommendation

Kỹ thuật parse:
- Đọc .docx bằng python-docx (extract toàn bộ text)
- Tìm các pattern số (η = 0.85, M_Rd = 310.5, As = 1520)
- So khớp với JSON handoff
"""

import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
import json
import argparse
import re
from pathlib import Path
from datetime import datetime

try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False


# Pattern nhận dạng các số liệu kỹ thuật
NUMBER_PATTERNS = {
    "M_Rd":      r"M[_\s]?Rd\s*[=:]\s*([0-9]+[.,]?[0-9]*)",
    "M_Ed":      r"M[_\s]?Ed\s*[=:]\s*([0-9]+[.,]?[0-9]*)",
    "V_Rd":      r"V[_\s]?Rd\s*[=:]\s*([0-9]+[.,]?[0-9]*)",
    "V_Ed":      r"V[_\s]?Ed\s*[=:]\s*([0-9]+[.,]?[0-9]*)",
    "N_Rd":      r"N[_\s]?Rd\s*[=:]\s*([0-9]+[.,]?[0-9]*)",
    "As":        r"\bAs\s*[=:]\s*([0-9]+[.,]?[0-9]*)",
    "eta":       r"[η]\s*[=:]\s*([0-9]+[.,]?[0-9]*)",
    "fck":       r"f[_\s]?ck\s*[=:]\s*([0-9]+[.,]?[0-9]*)",
    "fy":        r"f[_\s]?y\s*[=:]\s*([0-9]+[.,]?[0-9]*)",
    "b_section": r"\bb\s*[=:]\s*([0-9]{2,4})",
    "h_section": r"\bh\s*[=:]\s*([0-9]{2,4})",
    "Rb":        r"\bR[_\s]?b\s*[=:]\s*([0-9]+[.,]?[0-9]*)",
    "Rbt":       r"\bR[_\s]?bt\s*[=:]\s*([0-9]+[.,]?[0-9]*)",
    "Rs":        r"\bR[_\s]?s\s*[=:]\s*([0-9]+[.,]?[0-9]*)",
    "Rsw":       r"\bR[_\s]?sw\s*[=:]\s*([0-9]+[.,]?[0-9]*)",
    "L_an":      r"\bL[_\s]?an\s*[=:]\s*([0-9]+[.,]?[0-9]*)",
    "L_lap":     r"\bL[_\s]?lap\s*[=:]\s*([0-9]+[.,]?[0-9]*)",
    "a_crc":     r"\ba[_\s]?crc\s*[=:]\s*([0-9]+[.,]?[0-9]*)"
}

# Bỏ qua các số:
# - Nhỏ hơn min_value
# - Trùng giữa nhiều pattern (lấy pattern đầu)
IGNORE_PATTERNS = [
    r"^\d{1,2}/\d{1,2}/\d{4}$",  # Ngày tháng
    r"^0\.\d{1,3}$",             # Hệ số gamma nhỏ
    r"^\d{1,3}$",                 # Số đếm nhỏ
]


def extract_numbers_from_text(text: str):
    """
    Trích xuất tất cả số liệu kỹ thuật từ chuỗi văn bản (Markdown, Text, trích từ Docx).
    Xử lý chuẩn hóa dấu phẩy thập phân ',' -> '.' theo chuẩn Việt Nam.
    """
    extracted = {}
    for field, pattern in NUMBER_PATTERNS.items():
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            vals = []
            for m in matches:
                try:
                    val_str = m.replace(",", ".") if isinstance(m, str) else str(m)
                    vals.append(float(val_str))
                except ValueError:
                    continue
            if vals:
                extracted[field] = vals
    return extracted


def extract_numbers_from_docx(docx_path):
    """
    Trích xuất tất cả số liệu kỹ thuật từ file .docx.
    Returns: dict {field_name: [list of values found]}
    """
    if not DOCX_AVAILABLE:
        print("⚠️ python-docx chưa cài. Chạy: pip install python-docx", file=sys.stderr)
        return {}

    doc = Document(docx_path)
    full_text = "\n".join([p.text for p in doc.paragraphs])
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                full_text += "\n" + cell.text

    return extract_numbers_from_text(full_text)


def extract_numbers_from_report_file(file_path):
    """
    Trích xuất số liệu tự động nhận diện định dạng: .docx hoặc .md / .txt
    """
    p = Path(file_path)
    if p.suffix.lower() in [".md", ".txt", ".json"]:
        with open(file_path, "r", encoding="utf-8") as f:
            return extract_numbers_from_text(f.read())
    return extract_numbers_from_docx(file_path)


def extract_numbers_from_handoff(json_path):
    """
    Lấy tất cả số liệu kỹ thuật từ JSON handoff.
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        handoff = json.load(f)

    extracted = {}

    def _walk(obj, prefix=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    extracted[f"{prefix}{k}"] = [float(v)]
                elif isinstance(v, dict):
                    _walk(v, f"{prefix}{k}.")
                elif isinstance(v, list):
                    for i, item in enumerate(v):
                        if isinstance(item, (int, float)) and not isinstance(item, bool):
                            extracted[f"{prefix}{k}[{i}]"] = [float(item)]
                        elif isinstance(item, dict):
                            _walk(item, f"{prefix}{k}[{i}].")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                if isinstance(item, dict):
                    _walk(item, f"[{i}].")

    _walk(handoff)
    return extracted


# Map JSON keys → docx/report patterns
JSON_TO_DOCX_KEY_MAP = {
    "M_Rd":      ["M_Rd", "M.Rd", "MRd", "M_n"],
    "M_Ed":      ["M_Ed", "M.Ed", "MEd", "M_u", "Mu"],
    "V_Rd":      ["V_Rd", "V.Rd", "VRd", "V_n"],
    "V_Ed":      ["V_Ed", "V.Ed", "VEd", "V_u", "Vu"],
    "N_Rd":      ["N_Rd", "N.Rd", "NRd"],
    "N_Ed":      ["N_Ed", "N.Ed", "NEd", "N_u"],
    "As":        ["As", "As_provided", "As_prov", "As_actual"],
    "eta":       ["eta", "eta_M", "η"],
    "fck":       ["fck", "f_ck", "fc"],
    "fy":        ["fy", "f_y"],
    "Rb":        ["Rb", "R_b", "f_cd"],
    "Rbt":       ["Rbt", "R_bt", "f_ctd"],
    "Rs":        ["Rs", "R_s", "fy", "f_yd"],
    "Rsw":       ["Rsw", "R_sw", "fyw", "f_ywd"],
    "L_an":      ["L_an", "Lan", "L_0_an", "L0_an", "Anchorage_Length_mm"],
    "L_lap":     ["L_lap", "Llap", "l_lap", "Lap_Length_mm"],
    "a_crc":     ["a_crc", "acrc", "a_crc_max", "Crack_Width_mm"]
}


def check_consistency(docx_path, json_path, tolerance=0.5):
    """
    So sánh từng giá trị giữa báo cáo (.docx, .md, .txt) và JSON handoff.
    Nếu lệch > tolerance % → báo mismatch.
    """
    docx_data = extract_numbers_from_report_file(docx_path)
    json_data = extract_numbers_from_handoff(json_path)

    mismatches = []
    matches = []

    # Với mỗi pattern trong docx, tìm key tương ứng trong JSON
    for docx_field, docx_values in docx_data.items():
        json_keys = JSON_TO_DOCX_KEY_MAP.get(docx_field, [docx_field])
        json_value = None
        json_key_used = None
        for jk in json_keys:
            if jk in json_data:
                json_value = json_data[jk][0]
                json_key_used = jk
                break
            # Hỗ trợ tìm kiếm các key lồng nhau trong JSON (vd: Section.Rb hoặc Input.Rb)
            matching_keys = [k for k in json_data if k == jk or k.endswith(f".{jk}") or k.endswith(f"_{jk}")]
            if matching_keys:
                json_value = json_data[matching_keys[0]][0]
                json_key_used = matching_keys[0]
                break

        if json_value is None:
            continue

        # So sánh từng giá trị docx
        for docx_val in docx_values:
            if abs(json_value) < 1e-6:
                variance = 0 if abs(docx_val) < 1e-6 else 100
            else:
                variance = abs(docx_val - json_value) / abs(json_value) * 100

            if variance > tolerance:
                severity = "CRITICAL" if variance > 5 else "WARNING" if variance > 1 else "INFO"
                mismatches.append({
                    "field": docx_field,
                    "json_key": json_key_used,
                    "json_value": json_value,
                    "docx_value": docx_val,
                    "variance_pct": round(variance, 2),
                    "severity": severity,
                    "possible_reason": _suggest_reason(variance)
                })
            else:
                matches.append({
                    "field": docx_field,
                    "value": docx_val
                })

    return {
        "Verification_ID": f"VRF-REPORT-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "Timestamp": datetime.now().isoformat(),
        "Docx_File": str(docx_path),
        "Json_File": str(json_path),
        "Tolerance_pct": tolerance,
        "Summary": {
            "Total_Docx_Values": sum(len(v) for v in docx_data.values()),
            "Total_Json_Values": sum(len(v) for v in json_data.values()),
            "Matched_Count": len(matches),
            "Mismatch_Count": len(mismatches),
            "Critical_Count": sum(1 for m in mismatches if m["severity"] == "CRITICAL"),
            "Warning_Count": sum(1 for m in mismatches if m["severity"] == "WARNING")
        },
        "Mismatches": mismatches,
        "Overall_Status": "FAILED" if any(m["severity"] == "CRITICAL" for m in mismatches) else (
            "WARNING" if mismatches else "PASS"
        ),
        "Disclaimer": (
            "Số liệu trong báo cáo Word có thể khác JSON do làm tròn đơn vị (vd: 310.5 → 311). "
            "Cần kỹ sư xác nhận nguyên nhân sai lệch trước khi phát hành."
        )
    }


def _suggest_reason(variance):
    """Đoán nguyên nhân sai lệch dựa trên variance"""
    if variance > 50:
        return "Có thể JSON thiếu field này hoặc docx tham chiếu sai field khác"
    if variance > 5:
        return "Có thể do template Word thay thế số từ 1 JSON khác, hoặc AI ghi nhầm số"
    if variance > 1:
        return "Có thể do làm tròn giữa các bước (310.5 → 311)"
    return "Làm tròn khi in (acceptable)"


def main():
    parser = argparse.ArgumentParser(description="Check Report Consistency")
    parser.add_argument("--docx", required=True, help="File Word (.docx) xuất ra")
    parser.add_argument("--json", required=True, help="File JSON handoff gốc")
    parser.add_argument("--tolerance", type=float, default=0.5, help="Tolerance %%")
    parser.add_argument("--output", help="File JSON output")

    args = parser.parse_args()

    result = check_consistency(args.docx, args.json, args.tolerance)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
