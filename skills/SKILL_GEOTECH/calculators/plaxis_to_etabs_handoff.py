import sys
import json

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def calc_etabs_loads(anchor_force_kn, spacing_m):
    """
    Quy đổi lực nén thanh chống từ Plaxis sang tải trọng phân bố ETABS.
    Và kiểm tra sơ bộ Momen uốn lớn nhất trên dầm bo.
    """
    if spacing_m <= 0:
        return {"error": "Spacing must be > 0"}

    # Tải phân bố trên dầm bo
    q_kn_per_m = anchor_force_kn / spacing_m

    # Sơ bộ Momen lớn nhất trên dầm bo (giả sử nhịp dầm bo = khoảng cách các thanh chống)
    M_max = (q_kn_per_m * (spacing_m ** 2)) / 8.0

    calc_logs = [
        {
            "step": "Tải trọng phân bố ETABS",
            "formula": "q = F_anchor / L_spacing",
            "F_anchor": f"{anchor_force_kn} kN",
            "L_spacing": f"{spacing_m} m",
            "q": f"{round(q_kn_per_m, 2)} kN/m"
        },
        {
            "step": "Sơ bộ Momen Dầm Bo (Waling Beam)",
            "formula": "M_max ≈ (q × L²)/8 (Mô hình dầm đơn giản thiên về an toàn)",
            "M_max": f"({round(q_kn_per_m, 2)} × {spacing_m}²) / 8 = {round(M_max, 2)} kNm"
        }
    ]

    return {
        "F_anchor_kn": anchor_force_kn,
        "L_spacing_m": spacing_m,
        "q_etabs_kn_per_m": round(q_kn_per_m, 2),
        "M_max_waling_beam_knm": round(M_max, 2),
        "Calculation_Logs": calc_logs,
        "Standard_Method": "Structural Analysis Basics",
        "Scope_Limitation": [
            "L_spacing ở đây là nhịp của dầm bo. Nếu hệ chống có bố trí chống góc (Corner Brace), nhịp thực tế sẽ khác.",
            "Tải trọng q này là tải tiêu chuẩn (Service). Khi gán vào ETABS cần nhân hệ số tổ hợp (VD: 1.6 ALD)."
        ]
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="MODULE 17: Quy đổi Tải trọng Plaxis sang ETABS")
    parser.add_argument("--force", type=float, required=True, help="Lực dọc thanh chống từ Plaxis (kN)")
    parser.add_argument("--spacing", type=float, required=True, help="Bước chống (m)")
    parser.add_argument("--output", help="Output JSON file path")
    args = parser.parse_args()

    result = calc_etabs_loads(args.force, args.spacing)
    
    output_json = json.dumps(result, ensure_ascii=False, indent=2)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json)
        print(f"Output saved to: {args.output}")
    else:
        print(output_json)


if __name__ == "__main__":
    main()
