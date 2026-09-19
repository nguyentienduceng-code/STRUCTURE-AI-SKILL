#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MODULE 4: Embodied Carbon Calculator
Tính hàm lượng Carbon phát thải theo ISO 14067 / ICE Database v3.0.

Input:
- Danh sách vật liệu kèm khối lượng
- Diện tích sàn (để tính intensity)

Output:
- Tổng kg CO₂e
- Carbon intensity (kg CO₂/m²)
- So sánh với benchmark (LEED Gold, Net Zero)
"""

import sys
import json
import argparse
from datetime import datetime

# Carbon Coefficients Database (cập nhật 2025-2026)
# Nguồn: ICE Database v3.0 + WorldSteel + EPD Việt Nam
CARBON_DB = {
    "concrete": {
        "B15":  {"factor": 280, "unit": "kg CO₂/m³", "source": "ICE v3.0"},
        "B20":  {"factor": 300, "unit": "kg CO₂/m³", "source": "ICE v3.0"},
        "B22.5":{"factor": 310, "unit": "kg CO₂/m³", "source": "ICE v3.0"},
        "B25":  {"factor": 330, "unit": "kg CO₂/m³", "source": "ICE v3.0"},
        "B30":  {"factor": 350, "unit": "kg CO₂/m³", "source": "ICE v3.0"},
        "B35":  {"factor": 380, "unit": "kg CO₂/m³", "source": "ICE v3.0"},
        "B40":  {"factor": 410, "unit": "kg CO₂/m³", "source": "ICE v3.0"},
    },
    "steel": {
        "rebar_CB300V":     {"factor": 2050, "unit": "kg CO₂/tấn", "source": "WorldSteel 2025"},
        "rebar_CB400V":     {"factor": 2100, "unit": "kg CO₂/tấn", "source": "WorldSteel 2025"},
        "rebar_CB500V":     {"factor": 2150, "unit": "kg CO₂/tấn", "source": "WorldSteel 2025"},
        "structural_S235":  {"factor": 2200, "unit": "kg CO₂/tấn", "source": "EPD 2025"},
        "structural_S345":  {"factor": 2300, "unit": "kg CO₂/tấn", "source": "EPD 2025"},
        "structural_S390":  {"factor": 2450, "unit": "kg CO₂/tấn", "source": "EPD 2025"},
    },
    "formwork": {
        "wood":  {"factor": 430, "unit": "kg CO₂/m³", "source": "FSC 2024"},
        "steel": {"factor": 1800, "unit": "kg CO₂/tấn", "source": "Market 2025"},
        "plywood": {"factor": 600, "unit": "kg CO₂/m³", "source": "EPD 2024"},
        "plastic": {"factor": 1850, "unit": "kg CO₂/tấn", "source": "EPD 2024"},
    }
}

# Benchmark
BENCHMARKS = {
    "office_typical":  {"max": 250, "rating": "Standard Office"},
    "LEED_Gold":       {"max": 180, "rating": "LEED Gold certified"},
    "LEED_Platinum":   {"max": 150, "rating": "LEED Platinum"},
    "Net_Zero_2030":   {"max": 120, "rating": "Net Zero Target 2030"},
    "Net_Zero_2050":   {"max": 100, "rating": "Net Zero Target 2050"},
}


def calculate_carbon(materials, floor_area=None):
    """
    Tính tổng Carbon phát thải.

    Args:
        materials: [
            {"category": "concrete", "grade": "B25", "quantity": 120.5, "unit": "m³"},
            {"category": "steel", "grade": "rebar_CB400V", "quantity": 8.5, "unit": "tấn"},
            ...
        ]
        floor_area: Diện tích sàn (m²) cho intensity
    """
    breakdown = []
    total_carbon = 0
    calc_logs = []

    # Bước 1: Tra cứu hệ số
    calc_logs.append({
        "Step": 1,
        "Title": "Tra cứu hệ số Carbon theo ISO 14067",
        "Formula": "Lookup Carbon_Factor(category, grade)",
        "Substitution": f"Tra trong ICE Database v3.0 + WorldSteel + EPD Việt Nam",
        "Result": f"Tìm thấy hệ số cho {len(materials)} loại vật liệu",
        "Citation": {
            "code": "ISO 14067:2018",
            "year": "2018",
            "article": "Greenhouse gas emissions - Products",
            "excerpt": "Carbon footprint of products - Requirements and guidelines"
        }
    })

    # Bước 2-4: Tính carbon từng vật liệu
    for mat in materials:
        cat = mat.get("category", "").lower()
        grade = mat.get("grade", "")
        qty = mat.get("quantity", 0)
        unit = mat.get("unit", "")

        if cat not in CARBON_DB:
            continue
        if grade not in CARBON_DB[cat]:
            continue

        factor = CARBON_DB[cat][grade]["factor"]
        carbon = qty * factor
        total_carbon += carbon

        breakdown.append({
            "category": cat,
            "grade": grade,
            "quantity": qty,
            "unit": unit,
            "carbon_factor": factor,
            "carbon_factor_unit": CARBON_DB[cat][grade]["unit"],
            "carbon_kgCO2": round(carbon, 1),
            "source": CARBON_DB[cat][grade]["source"]
        })

    # Bước 5: Carbon intensity
    intensity = None
    if floor_area and floor_area > 0:
        intensity = total_carbon / floor_area
        calc_logs.append({
            "Step": 5,
            "Title": "Carbon Intensity",
            "Formula": "Intensity = Total_Carbon / Floor_Area",
            "Substitution": f"{total_carbon:,.0f} / {floor_area:,.0f}",
            "Result": f"{intensity:.1f} kg CO₂/m²",
            "Citation": {
                "code": "Method",
                "year": "2025",
                "article": "Industry Standard",
                "excerpt": "kg CO₂ per m² floor area - WLC scope"
            }
        })

    # Benchmark rating
    benchmark_rating = "BELOW_BENCHMARK"
    benchmark_name = "No rating"
    if intensity is not None:
        for key, val in sorted(BENCHMARKS.items(), key=lambda x: x[1]["max"]):
            if intensity <= val["max"]:
                benchmark_rating = key
                benchmark_name = val["rating"]
                break

    return {
        "Calculation_Date": datetime.now().isoformat(),
        "Standard_Method": "ISO 14067:2018 + ICE Database v3.0 + WorldSteel 2025",
        "Calculation_Logs": calc_logs,
        "Breakdown": breakdown,
        "Total_Carbon_kgCO2": round(total_carbon, 1),
        "Floor_Area_m2": floor_area,
        "Carbon_Intensity_kgCO2_per_m2": round(intensity, 1) if intensity else None,
        "Benchmark_Rating": benchmark_rating,
        "Benchmark_Description": benchmark_name,
        "ESG_Recommendations": _generate_esg_recs(intensity, breakdown),
        "Disclaimer": (
            "Hệ số carbon là ước tính trung bình ngành. Để chứng nhận LEED/EDGE cần "
            "EPD cụ thể của nhà cung cấp. Trợ lý AI không thay thế chứng nhận chính thức."
        )
    }


def _generate_esg_recs(intensity, breakdown):
    """Đề xuất ESG dựa trên carbon intensity"""
    recs = []
    if intensity is None:
        return recs
    if intensity > 250:
        recs.append("🔴 Vượt benchmark Office thông thường (>250 kg/m²). Cần giảm 30%+ carbon.")
        recs.append("→ Xem xét dùng bê tông geopolymer, thép tái chế (recycled steel ≥ 30%).")
    elif intensity > 180:
        recs.append("🟡 Đạt office thông thường nhưng chưa đạt LEED Gold.")
        recs.append("→ Có thể đạt LEED Gold bằng cách tăng 15% vật liệu tái chế.")
    elif intensity > 150:
        recs.append("🟢 Đạt LEED Gold. Có thể nâng cấp lên Platinum bằng cách dùng EPD-certified materials.")
    elif intensity > 120:
        recs.append("🌟 Đạt LEED Platinum. Phù hợp cho dự án ESG-conscious.")
    else:
        recs.append("🏆 Net Zero ready. Dự án có thể đăng ký chứng nhận Net Zero.")

    # Tìm top-2 contributor
    sorted_bd = sorted(breakdown, key=lambda x: x["carbon_kgCO2"], reverse=True)[:2]
    if sorted_bd:
        recs.append(
            f"📊 Top contributors: {sorted_bd[0]['category']}/{sorted_bd[0]['grade']} "
            f"({sorted_bd[0]['carbon_kgCO2']:.0f} kg CO₂)"
        )
    return recs


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Embodied Carbon Calculator")
    parser.add_argument("--input", help="JSON file input")
    parser.add_argument("--floor_area", type=float, help="Diện tích sàn (m²)")
    parser.add_argument("--output", help="JSON output file")

    args = parser.parse_args()

    if args.input:
        with open(args.input, 'r', encoding='utf-8') as f:
            materials = json.load(f)
    else:
        # Demo data
        materials = [
            {"category": "concrete", "grade": "B25", "quantity": 120.5, "unit": "m³"},
            {"category": "concrete", "grade": "B30", "quantity": 85.0, "unit": "m³"},
            {"category": "steel", "grade": "rebar_CB400V", "quantity": 10.2, "unit": "tấn"},
            {"category": "steel", "grade": "structural_S345", "quantity": 18.5, "unit": "tấn"},
            {"category": "formwork", "grade": "wood", "quantity": 680 * 0.025, "unit": "m³"},
        ]

    result = calculate_carbon(materials, args.floor_area)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

    print(json.dumps(result, indent=2, ensure_ascii=False))
