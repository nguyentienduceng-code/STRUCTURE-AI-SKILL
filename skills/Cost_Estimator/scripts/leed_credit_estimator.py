#!/usr/bin/env python3
"""
leed_credit_estimator.py — Ước tính điểm LEED và Carbon footprint

Usage:
    python leed_credit_estimator.py --project "Office Building" --area 5000 \\
        --structure "BTCT" --leed_level "Gold" --scenario "new"

Output: JSON với điểm LEED dự kiến, chi phí VE, và Carbon footprint
"""

import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
import argparse
import json
import sys
from dataclasses import dataclass, asdict

# ─── LEED Credit Structure (LEED v4 BD+C) ────────────────────────────────────

CREDIT_CATEGORIES = {
    "SS":  {"name": "Sustainable Sites",          "max": 10,  "credits": {}},
    "WE":  {"name": "Water Efficiency",           "max": 11,  "credits": {}},
    "EA":  {"name": "Energy & Atmosphere",        "max": 35,  "credits": {}},
    "MR":  {"name": "Materials & Resources",       "max": 14,  "credits": {}},
    "EQ":  {"name": "Environmental Quality",      "max": 15,  "credits": {}},
    "ID":  {"name": "Innovation & Design",        "max": 6,   "credits": {}},
    "RP":  {"name": "Regional Priority",           "max": 4,   "credits": {}},
}

# Credit library (điểm có thể đạt)
CREDIT_LIBRARY = {
    # SS
    "SSc1": {"name": "Construction Activity Pollution Prevention", "pts": 1},
    "SSc2": {"name": "Site Assessment", "pts": 1},
    "SSc4": {"name": "Rainwater Management", "pts": 3},
    "SSc5": {"name": "Heat Island Reduction", "pts": 2},
    "SSc6": {"name": "Light Pollution Reduction", "pts": 1},
    "SSc7": {"name": "Tenant Design & Construction Guidelines", "pts": 1},
    # WE
    "WEc1": {"name": "Outdoor Water Use Reduction", "pts": 4},
    "WEc2": {"name": "Indoor Water Use Reduction", "pts": 6},
    "WEc3": {"name": "Building-Level Water Metering", "pts": 1},
    # EA
    "EAc1": {"name": "Enhanced Commissioning", "pts": 6},
    "EAc2": {"name": "Energy Performance", "pts": 33},
    "EAc3": {"name": "Advanced Energy Metering", "pts": 1},
    "EAc5": {"name": "Enhanced Refrigerant Management", "pts": 1},
    "EAc6": {"name": "Green Power and Carbon Offsets", "pts": 2},
    # MR
    "MRc1": {"name": "Building Life-Cycle Impact Reduction", "pts": 6},
    "MRc2": {"name": "Building Product Disclosure — Environmental Product Declarations", "pts": 2},
    "MRc3": {"name": "Building Product Disclosure — Sourcing of Raw Materials", "pts": 2},
    "MRc4": {"name": "Building Product Disclosure — Material Ingredients", "pts": 2},
    "MRc5": {"name": "Construction & Demolition Waste Management", "pts": 2},
    # EQ
    "EQc1": {"name": "Enhanced Indoor Air Quality Strategies", "pts": 2},
    "EQc2": {"name": "Low-Emitting Materials", "pts": 3},
    "EQc4": {"name": "Interior Lighting", "pts": 2},
    "EQc6": {"name": "Thermal Comfort", "pts": 1},
    "EQc8": {"name": "Acoustic Performance", "pts": 1},
    # ID
    "IDc1": {"name": "Innovation", "pts": 5},
    # RP
    "RPc1": {"name": "Regional Priority", "pts": 4},
}


# ─── Carbon factors ──────────────────────────────────────────────────────────

CARBON_FACTORS = {
    "BTCT": {
        "concrete_kgCO2_m3": 300,  # Bê tông trung bình Việt Nam (fly ash blend)
        "steel_kgCO2_kg": 2.5,      # Thép thanh
        "formwork_kgCO2_m2": 8,     # Cốp pha
    },
    "THEP": {
        "steel_kgCO2_kg": 2.5,
        "bolt_kgCO2_kg": 4.0,
        "weld_kgCO2_kg": 5.0,
    }
}

CARBON_TARGETS = {
    "Platinum": 1200,   # kgCO2e/m²/year (vận hành)
    "Gold":     1500,
    "Silver":   2000,
    "Bronze":   2500,
    "None":     99999,
}


# ─── Main calculation ─────────────────────────────────────────────────────────

@dataclass
class LEEDResult:
    Project: str = ""
    Area_m2: float = 0.0
    StructureType: str = ""
    LEEDLevel: str = ""
    # Credits achieved
    CreditsByCategory: dict = None
    TotalCredits: float = 0.0
    TargetCredits: float = 0.0
    # Carbon
    EmbodiedCarbon_kgCO2e: float = 0.0
    EmbodiedCarbon_kgCO2m2: float = 0.0
    OperationalCarbon_kgCO2m2_year: float = 0.0
    CarbonTarget_kgCO2m2_year: float = 0.0
    CarbonGap_kgCO2m2_year: float = 0.0
    # VE
    CostPremium_pct: float = 0.0
    CostPremium_VND_m2: float = 0.0
    # Metadata
    Status: str = "OK"
    Calculation_Logs: list = None

    def __post_init__(self):
        if self.CreditsByCategory is None:
            self.CreditsByCategory = {}
        if self.Calculation_Logs is None:
            self.Calculation_Logs = []


def estimate_leed_credits(building: str, area: float, structure: str,
                           target_level: str) -> dict:
    logs = []
    credits_by_cat = {}

    # ─── Quyết định điểm dự kiến theo loại công trình ─────────────────────
    if "văn phòng" in building.lower() or "office" in building.lower():
        base_credits = {
            "SS": 7, "WE": 5, "EA": 18, "MR": 7, "EQ": 8, "ID": 4, "RP": 2
        }
    elif "chung cư" in building.lower() or "residential" in building.lower():
        base_credits = {
            "SS": 6, "WE": 4, "EA": 15, "MR": 6, "EQ": 7, "ID": 3, "RP": 2
        }
    elif "nhà xưởng" in building.lower() or "industrial" in building.lower():
        base_credits = {
            "SS": 5, "WE": 3, "EA": 12, "MR": 5, "EQ": 5, "ID": 2, "RP": 1
        }
    else:
        base_credits = {
            "SS": 5, "WE": 3, "EA": 10, "MR": 5, "EQ": 5, "ID": 2, "RP": 1
        }

    # Điều chỉnh theo kết cấu
    if structure.upper() == "BTCT":
        base_credits["MR"] += 2  # BTCT dễ đạt MR credits hơn
    elif structure.upper() == "THEP":
        base_credits["MR"] += 1
        base_credits["EA"] += 3  # Thép nhẹ → tiết kiệm năng lượng vận hành

    total = sum(base_credits.values())
    logs.append({
        "Step": 1, "Formula": "Credits = f(loại công trình, kết cấu)",
        "Substitution": f"Base credits: {base_credits}",
        "Result": f"Tổng dự kiến: {total} điểm"
    })

    credits_by_cat = {k: min(v, CREDIT_CATEGORIES[k]["max"]) for k, v in base_credits.items()}
    total_achieved = sum(credits_by_cat.values())

    # LEED levels (BD+C)
    level_targets = {"Platinum": 80, "Gold": 60, "Silver": 50, "Bronze": 40}
    target = level_targets.get(target_level, 40)

    logs.append({
        "Step": 2,
        "Formula": "LEED level = f(tổng điểm)",
        "Substitution": f"Target={target_level}: cần ≥{target} điểm, dự kiến đạt {total_achieved}",
        "Result": f"{'✅ Có thể đạt' if total_achieved >= target else '⚠️ Cần thêm credit'}: {total_achieved}/{target}"
    })

    return {"credits_by_cat": credits_by_cat, "total": total_achieved,
            "target": target, "logs": logs}


def calc_carbon(area: float, structure: str, operational_energy: float = 150) -> dict:
    """Ước tính carbon vòng đời (embodied + operational)"""
    cf = CARBON_FACTORS.get(structure.upper(), CARBON_FACTORS["BTCT"])

    logs = []
    # Embodied carbon (ước lượng đơn giản)
    if structure.upper() == "BTCT":
        # ~0.25 m³ BT/m², ~80 kg thép/m² (tòa nhà 10-15 tầng)
        concrete_vol = area * 0.25
        steel_weight = area * 80
        embodied = (
            concrete_vol * cf["concrete_kgCO2_m3"] +
            steel_weight * cf["steel_kgCO2_kg"]
        )
        logs.append({
            "Step": 3,
            "Formula": "Embodied CO2 = V_bt × 300 + W_t × 2.5 (BTCT)",
            "Substitution": f"V_bt={concrete_vol:.0f}m³, W_t={steel_weight:.0f}kg",
            "Result": f"Embodied = {embodied/1000:.1f} tCO2e"
        })
    else:
        steel_weight = area * 60
        embodied = steel_weight * cf["steel_kgCO2_kg"]
        logs.append({
            "Step": 3,
            "Formula": "Embodied CO2 = W_t × 2.5 (thép)",
            "Substitution": f"W_t={steel_weight:.0f}kg",
            "Result": f"Embodied = {embodied/1000:.1f} tCO2e"
        })

    # Operational (kWh/m²/năm → kgCO2e)
    # Việt Nam grid: 0.7 kgCO2/kWh
    op_carbon = operational_energy * 0.7  # kgCO2e/m²/year

    embodied_per_m2 = embodied / area if area else 0

    return {
        "embodied_kgCO2e": round(embodied, 1),
        "embodied_kgCO2m2": round(embodied_per_m2, 1),
        "operational_kgCO2m2_year": round(op_carbon, 1),
        "logs": logs
    }


def calc_ve_cost_premium(area: float, target_level: str, structure: str) -> dict:
    """Ước tính chi phí premium cho LEED"""
    premiums = {
        "Platinum": {"BTCT": 12, "THEP": 10},   # % premium so với base
        "Gold":     {"BTCT": 7,  "THEP": 6},
        "Silver":   {"BTCT": 4,  "THEP": 3},
        "Bronze":   {"BTCT": 2,  "THEP": 1},
        "None":     {"BTCT": 0,  "THEP": 0},
    }
    pcts = premiums.get(target_level, {"BTCT": 0, "THEP": 0})
    pct = pcts.get(structure.upper(), 0)
    # Base cost ~8M VND/m² cho kết cấu (BTCT) hoặc 7M (thép)
    base_cost = 8_000_000 if structure.upper() == "BTCT" else 7_000_000
    cost_premium_m2 = base_cost * pct / 100
    logs = [{
        "Step": 4,
        "Formula": "Cost_premium = Base_cost × LEED_premium_%",
        "Substitution": f"Base={base_cost/1e6:.0f}M/m², premium={pct}%",
        "Result": f"Chi phí thêm: {cost_premium_m2/1000:.0f}k/m² = {cost_premium_m2*area/1e6:.1f}M VNĐ"
    }]
    return {
        "premium_pct": pct,
        "premium_VND_m2": round(cost_premium_m2),
        "premium_total_VND": round(cost_premium_m2 * area),
        "logs": logs
    }


def main():
    parser = argparse.ArgumentParser(description="LEED Credit Estimator + Carbon Calculator")
    parser.add_argument("--project", type=str, required=True)
    parser.add_argument("--area", type=float, required=True, help="Diện tích sàn (m²)")
    parser.add_argument("--structure", type=str, required=True, choices=["BTCT","THEP","LAI"],
                        help="Loại kết cấu")
    parser.add_argument("--leed_level", type=str, default="None",
                        choices=["Platinum","Gold","Silver","Bronze","None"],
                        help="Mức LEED mục tiêu")
    parser.add_argument("--scenario", type=str, default="new",
                        choices=["new","existing","renovation"],
                        help="Loại dự án")
    parser.add_argument("--operational_energy", type=float, default=150,
                        help="Năng lượng vận hành kWh/m²/năm")
    parser.add_argument("--output", type=str, help="Lưu JSON ra file")
    args = parser.parse_args()

    res = LEEDResult(
        Project=args.project,
        Area_m2=args.area,
        StructureType=args.structure,
        LEEDLevel=args.leed_level,
    )

    all_logs = []

    # LEED credits
    leed = estimate_leed_credits(args.project, args.area, args.structure, args.leed_level)
    res.CreditsByCategory = leed["credits_by_cat"]
    res.TotalCredits = leed["total"]
    res.TargetCredits = leed["target"]
    all_logs.extend(leed["logs"])

    # Carbon
    carbon = calc_carbon(args.area, args.structure, args.operational_energy)
    res.EmbodiedCarbon_kgCO2e = carbon["embodied_kgCO2e"]
    res.EmbodiedCarbon_kgCO2m2 = carbon["embodied_kgCO2m2"]
    res.OperationalCarbon_kgCO2m2_year = carbon["operational_kgCO2m2_year"]
    res.CarbonTarget_kgCO2m2_year = CARBON_TARGETS.get(args.leed_level, 99999)
    res.CarbonGap_kgCO2m2_year = round(res.OperationalCarbon_kgCO2m2_year - res.CarbonTarget_kgCO2m2_year, 1)
    all_logs.extend(carbon["logs"])

    # VE cost
    ve = calc_ve_cost_premium(args.area, args.leed_level, args.structure)
    res.CostPremium_pct = ve["premium_pct"]
    res.CostPremium_VND_m2 = ve["premium_VND_m2"]
    all_logs.extend(ve["logs"])

    res.Calculation_Logs = all_logs

    output = {"Standard_Method": "LEED v4 BD+C + IPCC Carbon Factors", **asdict(res)}

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        print(f"[I001] Kết quả lưu tại: {args.output}", file=sys.stderr)
    else:
        print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
