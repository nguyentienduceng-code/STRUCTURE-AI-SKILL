import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
import json
import argparse

# Database đơn giá vật liệu (Q2/2026 - VNĐ)
MATERIAL_PRICES = {
    "concrete_B15": 1850000,      # VNĐ/m³
    "concrete_B20": 2100000,
    "concrete_B22.5": 2250000,
    "concrete_B25": 2400000,
    "concrete_B30": 2650000,
    "steel_CB300V": 18500,        # VNĐ/kg
    "steel_CB400V": 19500,
    "steel_CB500V": 21000,
    "steel_structural_S235": 22000,
    "steel_structural_S345": 24000,
    "steel_structural_S390": 26500,
    "formwork_wood": 45000,       # VNĐ/m²
    "formwork_steel": 15000,      # VNĐ/m² (thuê)
    "labor_carpenter": 350000,    # VNĐ/ngày
    "labor_steelfixer": 380000,
    "labor_welder": 420000
}

# FIX-LOGIC-01: Labor rates (đơn giá nhân công - có thể cập nhật từ data/labor_rates.json)
# Trước đây hardcoded 370000 VNĐ/ngày - giờ dùng database
DEFAULT_LABOR_RATE = 380000  # VNĐ/ngày - mức trung bình thị trường Q2/2026

# Hệ số Carbon (kg CO₂/unit)
CARBON_COEFFICIENTS = {
    "concrete_B15": 280,     # kg CO₂/m³
    "concrete_B20": 300,
    "concrete_B22.5": 310,
    "concrete_B25": 330,
    "concrete_B30": 350,
    "steel_rebar": 2100,     # kg CO₂/tấn
    "steel_structural": 2300,
    "formwork_wood": 430,    # kg CO₂/m³
    "formwork_steel": 1800   # kg CO₂/tấn
}

def compare_structural_options(options, floor_area, interest_rate=0.10):
    """
    So sánh chi phí giữa các phương án kết cấu.

    Args:
        options: List of dict, mỗi dict chứa thông tin 1 phương án
            {
                "name": "Phương án A",
                "type": "RC" | "Steel" | "Precast",
                "concrete_vol": 120.5,  # m³
                "steel_weight": 8500,   # kg
                "formwork_area": 450,   # m²
                "duration_days": 45,
                "concrete_grade": "B25",
                "steel_grade": "CB400V"
            }
        floor_area: Diện tích sàn (m²)
        interest_rate: Lãi suất vay năm (%)
    """

    results = []
    base_duration = min(opt.get('duration_days', 999) for opt in options)

    for idx, opt in enumerate(options):
        name = opt.get('name', f'Phương án {idx+1}')
        opt_type = opt.get('type', 'RC')

        # Tính chi phí vật liệu
        concrete_vol = opt.get('concrete_vol', 0)
        steel_weight = opt.get('steel_weight', 0)
        formwork_area = opt.get('formwork_area', 0)
        duration = opt.get('duration_days', 30)

        concrete_grade = opt.get('concrete_grade', 'B25')
        steel_grade = opt.get('steel_grade', 'CB400V')
        formwork_type = opt.get('formwork_type', 'wood')

        # Tính CAPEX
        concrete_cost = concrete_vol * MATERIAL_PRICES.get(f'concrete_{concrete_grade}', 2400000)
        steel_cost = steel_weight * MATERIAL_PRICES.get(f'steel_{steel_grade}', 19500)
        formwork_cost = formwork_area * MATERIAL_PRICES.get(f'formwork_{formwork_type}', 45000)

        # Nhân công (ước tính)
        # FIX-LOGIC-01: Dùng DEFAULT_LABOR_RATE thay vì hardcode 370000
        labor_days = duration * 10  # 10 công nhân trung bình
        labor_cost = labor_days * DEFAULT_LABOR_RATE

        capex = concrete_cost + steel_cost + formwork_cost + labor_cost

        # Tính hàm lượng vật liệu
        steel_ratio = steel_weight / concrete_vol if concrete_vol > 0 else steel_weight / floor_area
        concrete_per_m2 = concrete_vol / floor_area if floor_area > 0 else 0

        # Tính Carbon
        carbon_concrete = concrete_vol * CARBON_COEFFICIENTS.get(f'concrete_{concrete_grade}', 330)
        carbon_steel = (steel_weight / 1000.0) * CARBON_COEFFICIENTS.get('steel_rebar', 2100)
        carbon_formwork = (formwork_area * 0.025) * CARBON_COEFFICIENTS.get('formwork_wood', 430)  # Giả định 25mm dày
        total_carbon = carbon_concrete + carbon_steel + carbon_formwork
        carbon_intensity = total_carbon / floor_area if floor_area > 0 else 0

        # Tính chi phí lãi vay ẩn
        delta_days = duration - base_duration
        hidden_interest = 0
        if delta_days > 0 and 'total_investment' in opt:
            total_investment = opt['total_investment']
            hidden_interest = total_investment * (interest_rate / 365) * delta_days

        # CAPEX điều chỉnh (bao gồm lãi vay ẩn)
        adjusted_capex = capex + hidden_interest

        results.append({
            "Name": name,
            "Type": opt_type,
            "CAPEX_VND": round(capex),
            "Hidden_Interest_VND": round(hidden_interest),
            "Adjusted_CAPEX_VND": round(adjusted_capex),
            "CAPEX_per_m2": round(capex / floor_area if floor_area > 0 else 0),
            "Duration_Days": duration,
            "Concrete_Vol_m3": concrete_vol,
            "Steel_Weight_kg": steel_weight,
            "Steel_Ratio_kg_per_m3": round(steel_ratio, 1) if concrete_vol > 0 else "N/A",
            "Concrete_per_m2": round(concrete_per_m2, 3),
            "Total_Carbon_kgCO2": round(total_carbon),
            "Carbon_Intensity_kgCO2_per_m2": round(carbon_intensity, 1),
            "Breakdown": {
                "Concrete": round(concrete_cost),
                "Steel": round(steel_cost),
                "Formwork": round(formwork_cost),
                "Labor": round(labor_cost)
            }
        })

    # Xếp hạng theo Adjusted CAPEX
    sorted_results = sorted(results, key=lambda x: x['Adjusted_CAPEX_VND'])
    for rank, item in enumerate(sorted_results, start=1):
        item['Rank'] = rank
        item['Rank_Reason'] = "Lowest Adjusted CAPEX" if rank == 1 else ""

    # Tìm phương án tốt nhất
    best_option = sorted_results[0]

    # Decision Matrix (điểm đa tiêu chí)
    criteria_weights = {
        "CAPEX": 0.35,
        "Duration": 0.25,
        "Carbon": 0.20,
        "Complexity": 0.20
    }

    # Chuẩn hóa điểm (0-10)
    max_capex = max(r['Adjusted_CAPEX_VND'] for r in results)
    max_duration = max(r['Duration_Days'] for r in results)
    max_carbon = max(r['Total_Carbon_kgCO2'] for r in results)

    for item in sorted_results:
        # Điểm CAPEX (càng thấp càng tốt → đảo ngược)
        score_capex = 10 * (1 - item['Adjusted_CAPEX_VND'] / max_capex) if max_capex > 0 else 5
        # Điểm Duration (càng ngắn càng tốt → đảo ngược)
        score_duration = 10 * (1 - item['Duration_Days'] / max_duration) if max_duration > 0 else 5
        # Điểm Carbon (càng thấp càng tốt → đảo ngược)
        score_carbon = 10 * (1 - item['Total_Carbon_kgCO2'] / max_carbon) if max_carbon > 0 else 5
        # Điểm Complexity (giả định Steel = 8, RC = 6, Precast = 9)
        complexity_map = {"Steel": 8, "RC": 6, "Precast": 9}
        score_complexity = complexity_map.get(item['Type'], 7)

        total_score = (
            score_capex * criteria_weights['CAPEX'] +
            score_duration * criteria_weights['Duration'] +
            score_carbon * criteria_weights['Carbon'] +
            score_complexity * criteria_weights['Complexity']
        )

        item['Decision_Matrix_Score'] = round(total_score, 2)
        item['Scores_Detail'] = {
            "CAPEX": round(score_capex, 1),
            "Duration": round(score_duration, 1),
            "Carbon": round(score_carbon, 1),
            "Complexity": round(score_complexity, 1)
        }

    # Xếp lại theo Decision Matrix Score
    final_ranking = sorted(sorted_results, key=lambda x: x['Decision_Matrix_Score'], reverse=True)
    for rank, item in enumerate(final_ranking, start=1):
        item['Final_Rank'] = rank

    # Khuyến nghị
    recommended = final_ranking[0]
    savings_vs_expensive = max_capex - recommended['Adjusted_CAPEX_VND']
    savings_percent = (savings_vs_expensive / max_capex * 100) if max_capex > 0 else 0

    recommendation = f"Khuyến nghị: {recommended['Name']} (Rank #{recommended['Final_Rank']} - Điểm: {recommended['Decision_Matrix_Score']}/10). "
    if savings_vs_expensive > 0:
        recommendation += f"Tiết kiệm {savings_vs_expensive:,.0f} VNĐ ({savings_percent:.1f}%) so với phương án đắt nhất."

    # Carbon benchmark
    carbon_status = "GREEN" if recommended['Carbon_Intensity_kgCO2_per_m2'] < 180 else "YELLOW" if recommended['Carbon_Intensity_kgCO2_per_m2'] < 250 else "RED"
    carbon_note = f"Carbon Intensity: {recommended['Carbon_Intensity_kgCO2_per_m2']} kg CO₂/m² ({carbon_status} - Benchmark LEED Gold: <180)"

    return {
        "Comparison_Summary": {
            "Total_Options": len(options),
            "Floor_Area_m2": floor_area,
            "Interest_Rate": interest_rate,
            "Base_Duration_Days": base_duration
        },
        "Options": final_ranking,
        "Recommended_Option": recommended['Name'],
        "Recommendation": recommendation,
        "Carbon_Note": carbon_note,
        "Decision_Criteria_Weights": criteria_weights,
        "Trade_offs": {
            "Fastest": min(results, key=lambda x: x['Duration_Days'])['Name'],
            "Lowest_CAPEX": min(results, key=lambda x: x['CAPEX_VND'])['Name'],
            "Lowest_Carbon": min(results, key=lambda x: x['Total_Carbon_kgCO2'])['Name']
        }
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compare Structural Options Cost")
    parser.add_argument("--options", required=True, help="JSON file chứa danh sách phương án")
    parser.add_argument("--floor_area", type=float, required=True, help="Diện tích sàn (m²)")
    parser.add_argument("--interest_rate", type=float, default=0.10, help="Lãi suất vay năm (%)")
    parser.add_argument("--output", help="File JSON output (optional)")

    args = parser.parse_args()

    with open(args.options, 'r', encoding='utf-8') as f:
        options_data = json.load(f)

    result = compare_structural_options(options_data, args.floor_area, args.interest_rate)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

    print(json.dumps(result, indent=2, ensure_ascii=False))
