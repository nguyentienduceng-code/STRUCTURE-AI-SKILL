import sys
import json
import re

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# ─────────────────────────────────────────────────────────────
# format_etabs_output.py — MODULE 18 (v3.0.0)
# Đọc bảng kết quả ETABS Steel Frame Design Summary
# và định dạng lại thành Bảng Markdown / Word chuẩn cho TMTT
# ─────────────────────────────────────────────────────────────

STATUS_OK  = "ĐẠT"
STATUS_WARN = "⚠ SÁT NGƯỠNG"
STATUS_FAIL = "❌ KHÔNG ĐẠT"
COLOR_OK   = "🟢"
COLOR_WARN = "🟠"
COLOR_FAIL = "🔴"


def classify(ratio: float):
    if ratio <= 0.9:
        return COLOR_OK, STATUS_OK
    elif ratio <= 1.0:
        return COLOR_WARN, STATUS_WARN
    else:
        return COLOR_FAIL, STATUS_FAIL


def parse_etabs_csv(filepath: str) -> list[dict]:
    """
    Đọc file CSV hoặc TXT từ ETABS Frame Design Summary.
    Hỗ trợ 2 định dạng:
      - Tab-delimited TXT từ ETABS Text File
      - CSV từ Export > Design Summary
    Trả về list[dict] các dòng dữ liệu.
    """
    rows = []
    with open(filepath, encoding='utf-8-sig', errors='ignore') as f:
        lines = f.readlines()

    header = None
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue

        # Tự động detect dấu phân cách
        if '\t' in stripped:
            parts = [p.strip() for p in stripped.split('\t')]
        else:
            parts = [p.strip() for p in stripped.split(',')]

        if header is None:
            header = [p.lower().replace(' ', '_') for p in parts]
            continue

        if len(parts) < len(header):
            parts += [''] * (len(header) - len(parts))

        rows.append(dict(zip(header, parts)))

    return rows


def parse_etabs_inline(data: list[dict]) -> list[dict]:
    """Nhận list dict trực tiếp (từ JSON input)."""
    return data


def format_markdown_table(rows: list[dict]) -> str:
    """Sinh bảng Markdown tổng hợp cho Mục 5 TMTT."""
    if not rows:
        return "_Không có dữ liệu_"

    header = "| Label | Tiết diện | Loại | Combo | PMM Ratio | P Ratio | Kết luận |\n"
    sep =    "|:---:|:---:|:---:|:---:|:---:|:---:|:---:|\n"

    lines = [header, sep]
    for r in rows:
        label    = r.get('label', r.get('name', '?'))
        section  = r.get('design_section', r.get('section', '?'))
        dtype    = r.get('design_type', 'Beam')
        combo    = r.get('pmm_combo', r.get('combo', '?'))
        pmm_str  = r.get('pmm_ratio', r.get('ratio', '0'))
        p_str    = r.get('p_ratio', '0')

        try:
            pmm = float(pmm_str)
        except ValueError:
            pmm = 0.0
        try:
            p_ratio = float(p_str)
        except ValueError:
            p_ratio = 0.0

        color, status = classify(pmm)
        lines.append(
            f"| {label} | {section} | {dtype} | {combo} "
            f"| **{pmm:.3f}** {color} | {p_ratio:.3f} | **{status}** |\n"
        )

    return "".join(lines)


def summary_conclusion(rows: list[dict]) -> dict:
    """Tổng hợp kết luận: max ratio, số cấu kiện fail."""
    ratios = []
    for r in rows:
        try:
            ratios.append(float(r.get('pmm_ratio', r.get('ratio', '0'))))
        except ValueError:
            pass

    if not ratios:
        return {"max_ratio": 0, "failed": 0, "total": 0, "conclusion": STATUS_OK}

    max_r   = max(ratios)
    failed  = sum(1 for x in ratios if x > 1.0)
    total   = len(ratios)
    _, conclusion = classify(max_r)

    return {
        "max_ratio": round(max_r, 3),
        "failed": failed,
        "total": total,
        "conclusion": conclusion,
        "note": (
            f"Tỷ số ứng suất lớn nhất: PMM Ratio = {max_r:.3f}. "
            f"{total} cấu kiện kiểm tra, {failed} cấu kiện KHÔNG ĐẠT."
            if failed else
            f"Tỷ số ứng suất lớn nhất: PMM Ratio = {max_r:.3f}. "
            f"Tất cả {total} cấu kiện ĐẠT khả năng chịu lực."
        )
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="MODULE 18: Định dạng Bảng ETABS Design Summary → TMTT Markdown")
    parser.add_argument("--input",  help="File CSV/TXT từ ETABS")
    parser.add_argument("--json",   help="File JSON chứa list kết quả ETABS")
    parser.add_argument("--output", help="Output Markdown file")
    args = parser.parse_args()

    rows = []
    if args.input:
        rows = parse_etabs_csv(args.input)
    elif args.json:
        with open(args.json, encoding='utf-8') as f:
            rows = json.load(f)
    else:
        # Demo với data mẫu từ file TMTT 19/09/2026
        rows = [
            {"label": "B11", "design_section": "H200", "design_type": "Beam",
             "pmm_combo": "ACI LRSD(C)", "pmm_ratio": "0.161", "p_ratio": "0.058"},
            {"label": "B30", "design_section": "H200", "design_type": "Beam",
             "pmm_combo": "ACI LRSD(C)", "pmm_ratio": "0.161", "p_ratio": "0.058"},
            {"label": "B31", "design_section": "H200", "design_type": "Beam",
             "pmm_combo": "(T)",         "pmm_ratio": "0.223", "p_ratio": "0.007"},
            {"label": "B32", "design_section": "H200", "design_type": "Beam",
             "pmm_combo": "ACI LRSD(C)", "pmm_ratio": "0.242", "p_ratio": "0.027"},
            {"label": "B33", "design_section": "H200", "design_type": "Beam",
             "pmm_combo": "(T)",         "pmm_ratio": "0.223", "p_ratio": "0.007"},
            {"label": "B10", "design_section": "H200", "design_type": "Beam",
             "pmm_combo": "(T)",         "pmm_ratio": "0.705", "p_ratio": "0.023"},
            {"label": "B12", "design_section": "H200", "design_type": "Beam",
             "pmm_combo": "ACI LRSD(C)", "pmm_ratio": "0.737", "p_ratio": "0.054"},
            {"label": "B13", "design_section": "H200", "design_type": "Beam",
             "pmm_combo": "(T)",         "pmm_ratio": "0.705", "p_ratio": "0.023"},
        ]

    md_table = format_markdown_table(rows)
    summary  = summary_conclusion(rows)

    output_md = f"""## Bảng Kết quả Kiểm tra Hệ Giằng (ETABS Steel Design Summary — AISC 360-10)

{md_table}

> **Kết luận tổng hợp:** {summary['note']}
> - Tỷ số ứng suất lớn nhất (PMM Ratio): **{summary['max_ratio']}**
> - Kết luận: **{summary['conclusion']}**

*Tổ hợp tải: 1.2DL + 1.6ALD (Áp lực đất chủ động) theo ASCE 7-10. D/C Ratio ≤ 1.0 là đạt yêu cầu.*
"""

    result = {
        "markdown_table": output_md,
        "summary": summary,
        "Calculation_Logs": [{"step": "ETABS Design Summary formatting", "rows_processed": len(rows)}],
        "Standard_Method": "AISC 360-10 / ASCE 7-10",
    }

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output_md)
        print(f"Markdown saved to: {args.output}")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
