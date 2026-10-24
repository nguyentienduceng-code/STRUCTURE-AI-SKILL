import os
import sys
import json
import math

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# =============================================================================
# verify_against_ground_truth.py — MODULE: Kiểm chứng Ground Truth
# =============================================================================
# Version: 2.3.1
# Fixes v2.3.1:
#   - Tăng SPT diff tolerance từ 5 → 8
#   - Cải thiện phân loại dính/rời (không còn phụ thuộc "sét" in name)
#   - Thêm fallback khi NO_MATCH — đề xuất Ke/α theo SPT
#   - Thêm calc_logs chi tiết
#   - Warning thresholds: >20% → W001, >30% → E001
# Reference: TMTT BPTC (Saigon Pearl, Navi Tower, Quận 3, Phú Nhuận)
# Mục đích: So sánh thông số E50 tính toán với dữ liệu thực tế đã được phê duyệt.
# =============================================================================

# ── Bảng Ke/α fallback khi không tìm được Ground Truth ──
# Nguồn: CIRIA C760 / Jamiolkowski / Bowles 1997
FALLBACK_E50_BY_SPT = {
    # spt_range    : [Ke_min/alpha_min, Ke_max/alpha_max]
    # Đất dính: dùng Ke với Su ≈ spt × 4.5
    # Đất rời: dùng alpha
    "cohesive_very_soft": {"spt": (0, 2), "Ke_range": (300, 500), "Su_factor": 4.5},
    "cohesive_soft":      {"spt": (2, 5), "Ke_range": (400, 600), "Su_factor": 4.5},
    "cohesive_medium":    {"spt": (5, 15), "Ke_range": (500, 800), "Su_factor": 4.5},
    "cohesive_stiff":     {"spt": (15, 30), "Ke_range": (600, 1000), "Su_factor": 4.5},
    "granular_loose":     {"spt": (4, 10), "alpha_range": (1500, 2000)},
    "granular_medium":    {"spt": (10, 30), "alpha_range": (2000, 2700)},
    "granular_dense":     {"spt": (30, 50), "alpha_range": (2500, 3000)},
    "fill":              {"spt": (5, 15), "alpha_range": (2000, 2500)},
}


def _classify_from_spt(spt, is_cohesive):
    """Phân loại nhóm đất từ SPT."""
    if is_cohesive:
        if spt <= 2:   return "cohesive_very_soft"
        if spt <= 5:   return "cohesive_soft"
        if spt <= 15:  return "cohesive_medium"
        return "cohesive_stiff"
    else:
        if spt < 10:  return "granular_loose"
        if spt < 30:  return "granular_medium"
        return "granular_dense"


def _is_granular_from_name(layer_name):
    """
    Xác định đất rời/dính từ tên lớp — Cải thiện v2.3.1.
    Ưu tiên keyword rời, nếu không có → mặc định là dính (conservative).
    """
    n = layer_name.lower()

    granular_kw = [
        "cát", "sand", "cat", "sỏi", "gravel", "sạn",
        "đắp", "san lấp", "fill"
    ]
    cohesive_kw_only = [
        "sét", "bùn", "clay", "silt", "hữu cơ",
        "organic", "than bùn", "bùn hữu cơ"
    ]
    # Nếu có keyword rời → rời
    if any(k in n for k in granular_kw):
        return True
    # Nếu có keyword dính đặc trưng (không chứa trong "cát pha") → dính
    if any(k in n for k in cohesive_kw_only):
        return False
    # "Cát pha" → rời (có cát)
    if "cát pha" in n or "cat pha" in n:
        return True
    # Mặc định: dính (conservative — tránh sai khi phân loại cát pha)
    return False


def load_ground_truth_db():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(current_dir, "..", "data", "ground_truth_db.json")
    try:
        with open(db_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Lỗi đọc Ground Truth DB: {e}", file=sys.stderr)
        return None


def find_closest_ground_truth(spt_value, is_cohesive, db):
    """
    Tìm lớp đất có SPT và loại đất (dính/rời) tương đồng nhất trong DB.
    Fix v2.3.1:
      - Tăng diff limit từ 5 → 8
      - So khớp chính xác hơn loại đất (không chỉ keyword)
    """
    best_match = None
    min_spt_diff = float('inf')
    SPT_DIFF_LIMIT = 8.0  # v2.3.1: tăng từ 5.0

    for project in db.get("projects", []):
        for layer in project.get("soil_layers", []):
            layer_name = layer["layer_name"]
            spt_avg = layer["spt_avg"]

            # Xác định loại đất của GT entry
            is_gt_granular = _is_granular_from_name(layer_name)

            # Chỉ so sánh nếu cùng nhóm đất
            if is_cohesive == is_gt_granular:
                diff = abs(spt_value - spt_avg)

                if diff < min_spt_diff and diff <= SPT_DIFF_LIMIT:
                    min_spt_diff = diff
                    best_match = {
                        "project": project["project_name"],
                        "layer": layer_name,
                        "spt_avg": spt_avg,
                        "parameters": layer["parameters"]
                    }

    return best_match


def calculate_fallback(spt_value, is_cohesive):
    """
    Tính E50 ước lượng khi không tìm được Ground Truth phù hợp.
    Fix v2.3.1: Thêm fallback để không mất giá trị tham khảo.
    """
    group = _classify_from_spt(spt_value, is_cohesive)
    fb = FALLBACK_E50_BY_SPT.get(group, {})

    if is_cohesive:
        Ke_range = fb.get("Ke_range", (400, 700))
        Ke = (Ke_range[0] + Ke_range[1]) / 2
        Su_estimate = spt_value * fb.get("Su_factor", 4.5)
        E50_estimate = Ke * Su_estimate
        return {
            "method": "Fallback: Ke × Su (ước lượng Su từ SPT)",
            "Ke_used": Ke,
            "Su_estimate_kpa": round(Su_estimate, 1),
            "E50_ref_kpa_estimate": round(E50_estimate, -3),
            "Ke_range": Ke_range,
            "note": "Su được ước lượng từ SPT — nên dùng Su từ Lab Test để chính xác hơn"
        }
    else:
        alpha_range = fb.get("alpha_range", (2000, 2700))
        alpha = (alpha_range[0] + alpha_range[1]) / 2
        E50_estimate = alpha * spt_value
        return {
            "method": f"Fallback: α × N_SPT = {alpha} × {spt_value}",
            "alpha_used": alpha,
            "E50_ref_kpa_estimate": round(E50_estimate, -3),
            "alpha_range": alpha_range,
            "note": "Sử dụng alpha trung bình — kiểm tra với Lab Test nếu có"
        }


def verify_parameters(calc_params, spt_input, is_cohesive):
    """
    Đối chiếu bộ thông số tính toán với Ground Truth.
    Fix v2.3.1:
      - Thêm calc_logs chi tiết
      - Warning thresholds rõ ràng
      - Fallback khi không match
      - Đề xuất cải thiện cụ thể
    """
    db = load_ground_truth_db()
    if not db:
        return {"status": "ERROR", "message": "Không đọc được Ground Truth DB"}

    gt_match = find_closest_ground_truth(spt_input, is_cohesive, db)

    calc_logs = []

    # ── Tình huống A: Tìm được Ground Truth ──
    if gt_match:
        calc_e50 = calc_params.get("E50_ref_kpa")
        gt_e50 = gt_match["parameters"].get("E50_ref_kpa")

        warnings = []
        errors = []
        suggestions = []

        calc_logs.append({
            "step": "1. Tìm Ground Truth",
            "result": f"Match: {gt_match['project']} — Lớp: {gt_match['layer']}",
            "spt_input": spt_input,
            "spt_gt": gt_match["spt_avg"]
        })

        if calc_e50 and gt_e50:
            diff_pct = abs(calc_e50 - gt_e50) / gt_e50 * 100

            calc_logs.append({
                "step": "2. Tính Deviance",
                "formula": "|E50_calc - E50_GT| / E50_GT × 100%",
                "E50_calc": calc_e50,
                "E50_GT": gt_e50,
                "diff_pct": round(diff_pct, 1)
            })

            if diff_pct > 30:
                errors.append(
                    f"E50 tính toán ({calc_e50:,} kPa) lệch {round(diff_pct, 1)}% so với "
                    f"dự án thực tế ({gt_e50:,} kPa)."
                )
                suggestions.append({
                    "field": "E50_ref_kpa",
                    "current": calc_e50,
                    "suggested": gt_e50,
                    "reason": f"Dự án {gt_match['project']} ({gt_match['layer']}, "
                              f"SPT={gt_match['spt_avg']}) dùng E50 = {gt_e50:,} kPa — "
                              "Chênh lệch > 30% — cần rà soát lại Su hoặc Ip đầu vào."
                })
                status = "ERROR (E001)"
            elif diff_pct > 20:
                warnings.append(
                    f"E50 tính toán ({calc_e50:,} kPa) lệch {round(diff_pct, 1)}% so với "
                    f"dự án thực tế ({gt_e50:,} kPa)."
                )
                suggestions.append({
                    "field": "E50_ref_kpa",
                    "current": calc_e50,
                    "suggested": gt_e50,
                    "reason": f"Dự án {gt_match['project']} ({gt_match['layer']}, "
                              f"SPT={gt_match['spt_avg']}) dùng E50 = {gt_e50:,} kPa — "
                              "Chênh lệch > 20% — kiểm tra lại Ip và Ke."
                })
                status = "WARNING (W001)"
            else:
                status = "VERIFIED_OK"

            # Kiểm tra c, phi
            calc_c = calc_params.get("c_kpa")
            gt_c = gt_match["parameters"].get("c_kpa")
            if calc_c is not None and gt_c is not None and gt_c > 0:
                c_diff_pct = abs(calc_c - gt_c) / gt_c * 100
                if c_diff_pct > 25:
                    warnings.append(
                        f"Lực dính c' ({calc_c} kPa) lệch {round(c_diff_pct, 1)}% so với "
                        f"thực tế ({gt_c} kPa)."
                    )
                    suggestions.append({
                        "field": "c_kpa",
                        "current": calc_c,
                        "suggested": gt_c,
                        "reason": f"Sử dụng c' = {gt_c} kPa từ {gt_match['project']}"
                    })

        calc_logs.append({
            "step": "3. Đánh giá",
            "status": status,
            "warnings": warnings,
            "errors": errors
        })

        return {
            "status": status,
            "ground_truth_reference": {
                "project": gt_match["project"],
                "layer_name": gt_match["layer"],
                "spt": gt_match["spt_avg"],
                "E50_GT_kpa": gt_e50
            },
            "deviance_pct": round(diff_pct, 1) if calc_e50 and gt_e50 else None,
            "warnings": warnings,
            "errors": errors,
            "suggestions": suggestions,
            "Calculation_Logs": calc_logs
        }

    # ── Tình huống B: Không tìm được Ground Truth — dùng Fallback ──
    fallback = calculate_fallback(spt_input, is_cohesive)
    calc_e50 = calc_params.get("E50_ref_kpa")

    calc_logs.append({
        "step": "1. Tìm Ground Truth",
        "result": "NO_MATCH — sử dụng Fallback",
        "reason": f"Không có dữ liệu GT cho SPT={spt_input} trong phạm vi ±8"
    })

    if calc_e50 and fallback:
        fb_e50 = fallback.get("E50_ref_kpa_estimate", 0)
        diff_pct = abs(calc_e50 - fb_e50) / fb_e50 * 100 if fb_e50 > 0 else 0

        calc_logs.append({
            "step": "2. So sánh với Fallback",
            "E50_calc": calc_e50,
            "E50_fallback_estimate": fb_e50,
            "diff_pct": round(diff_pct, 1)
        })

        if diff_pct > 25:
            warnings = [
                f"E50 tính toán ({calc_e50:,} kPa) lệch {round(diff_pct, 1)}% so với "
                f"ước lượng từ database ({fb_e50:,} kPa)."
            ]
            suggestions = [{
                "field": "E50_ref_kpa",
                "current": calc_e50,
                "suggested": fb_e50,
                "reason": f"ước lượng Ke={fallback.get('Ke_used','?')} × Su hoặc "
                          f"α={fallback.get('alpha_used','?')} — kiểm tra lại Ip và Su đầu vào."
            }]
            status = "WARNING (W002 — NO_GT)"
        else:
            warnings = []
            suggestions = []
            status = "VERIFIED_OK (FALLBACK)"

        calc_logs.append({
            "step": "3. Đánh giá",
            "status": status
        })

        return {
            "status": status,
            "ground_truth_reference": None,
            "deviance_pct": round(diff_pct, 1),
            "fallback": fallback,
            "warnings": warnings,
            "suggestions": suggestions,
            "Calculation_Logs": calc_logs,
            "note": "Không tìm được Ground Truth phù hợp — kết quả dựa trên fallback. "
                    "Nên bổ sung Lab Test để xác nhận."
        }

    # ── Tình huống C: Không có cả GT lẫn E50 để so sánh ──
    return {
        "status": "NO_DATA",
        "ground_truth_reference": None,
        "fallback": fallback,
        "warnings": [],
        "suggestions": [],
        "Calculation_Logs": calc_logs,
        "note": "Không đủ dữ liệu để kiểm chứng. Cung cấp E50_ref_kpa đầu vào."
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="MODULE VERIFY: Kiểm chứng Ground Truth v2.3.1"
    )
    parser.add_argument("--spt", type=float, required=True, help="Giá trị SPT đầu vào")
    parser.add_argument("--e50", type=float, required=True, help="E50 tính toán (kPa)")
    parser.add_argument("--cohesive", action="store_true",
                        help="Đất dính (không có flag = đất rời)")
    parser.add_argument("--c", type=float, default=None, help="c' (kPa) — tùy chọn")
    args = parser.parse_args()

    calc_params = {"E50_ref_kpa": args.e50}
    if args.c is not None:
        calc_params["c_kpa"] = args.c

    result = verify_parameters(calc_params, args.spt, args.cohesive)

    # In ra với định dạng đẹp
    print("\n" + "=" * 60)
    print("  VERIFY GROUND TRUTH — SKILL_GEOTECH v2.3.1")
    print("=" * 60)
    print(f"  SPT đầu vào:  {args.spt}")
    print(f"  E50 tính toán: {args.e50:,} kPa")
    print(f"  Loại đất:      {'Đất dính' if args.cohesive else 'Đất rời'}")
    print("-" * 60)

    status_icon = {
        "VERIFIED_OK": "✓",
        "VERIFIED_OK (FALLBACK)": "✓",
        "WARNING (W001)": "⚠",
        "WARNING (W002 — NO_GT)": "⚠",
        "ERROR (E001)": "✗",
        "NO_DATA": "?",
        "ERROR": "✗"
    }.get(result.get("status", ""), "?")

    print(f"  Trạng thái:    {status_icon} {result.get('status', 'N/A')}")

    if result.get("ground_truth_reference"):
        ref = result["ground_truth_reference"]
        print(f"  GT Reference:  {ref.get('project', '?')} — {ref.get('layer_name', '?')}")
        if result.get("deviance_pct") is not None:
            print(f"  Deviance:      {result['deviance_pct']}%")

    if result.get("warnings"):
        print("\n  Cảnh báo:")
        for w in result["warnings"]:
            print(f"    ⚠  {w}")

    if result.get("suggestions"):
        print("\n  Đề xuất:")
        for s in result["suggestions"]:
            print(f"    → {s['field']}: {s.get('current','?')} → {s['suggested']:,} kPa")
            print(f"      Lý do: {s['reason']}")

    if result.get("fallback"):
        fb = result["fallback"]
        print(f"\n  Fallback E50: {fb.get('E50_ref_kpa_estimate','?')} kPa")
        print(f"  Phương pháp:  {fb.get('method','?')}")

    print("=" * 60)
    print()

    # Output JSON đầy đủ cho pipeline
    output_json = json.dumps(result, ensure_ascii=False, indent=2)
    print(output_json)


if __name__ == "__main__":
    main()
