#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MODULE 3: Material Optimization (Value Engineering)
Đề xuất giảm vật liệu khi η ≤ 0.70.

Trigger: Được gọi bởi Design_Evaluation/Structural_Design_Engineer khi phát hiện η thấp.

Input:
- Kết quả tính gốc: M_Rd, V_Rd, η, tiết diện hiện tại
- Loại cấu kiện (dầm/cột/sàn)

Output:
- Đề xuất giảm tiết diện/cốt thép
- η mới sau tối ưu
- Tiết kiệm chi phí ước tính
"""

import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
import sys
import json
import argparse

# Đơn giá tham chiếu (cùng dataset với boq_cost_analysis.py)
# Bảng giảm tiết diện tiêu chuẩn: -50mm mỗi step cho bề cao, -50mm cho bề rộng
BEAM_DOWNGRADE_OPTIONS = [
    {"label": "Giảm 50mm cao",  "dh": -50, "db": 0,   "min_eta": 0.85},
    {"label": "Giảm 100mm cao", "dh": -100, "db": 0,  "min_eta": 0.85},
    {"label": "Giảm 100mm+50mm rộng", "dh": -100, "db": -50, "min_eta": 0.85},
    {"label": "Giảm 150mm+50mm rộng", "dh": -150, "db": -50, "min_eta": 0.85},
    {"label": "Giảm cốt thép 10%", "rebar_reduction": 0.10, "min_eta": 0.85},
    {"label": "Giảm cốt thép 20%", "rebar_reduction": 0.20, "min_eta": 0.80},
]

COLUMN_DOWNGRADE_OPTIONS = [
    {"label": "Giảm 50mm mỗi chiều", "dh": -50, "db": -50, "min_eta": 0.85},
    {"label": "Giảm 100mm mỗi chiều", "dh": -100, "db": -100, "min_eta": 0.85},
]


def estimate_eta_after_downgrade(original_eta, original_h, original_b, dh, db):
    """
    Ước tính η mới sau khi giảm tiết diện.
    η tỷ lệ nghịch với b·h²·d (modulus resistance).
    """
    new_h = original_h + dh
    new_b = original_b + db
    if new_h <= 0 or new_b <= 0:
        return None
    # M_Rd ∝ b·d² → d giảm theo tỷ lệ h
    ratio = (original_b * original_h**2) / (new_b * new_h**2)
    new_eta = original_eta / ratio if ratio > 0 else original_eta
    return round(new_eta, 3)


def optimize_beam(member_data, material_prices=None):
    """
    Tối ưu tiết diện dầm.

    Args:
        member_data: {
            "name": "B1",
            "type": "beam",
            "section_b": 300,        # mm
            "section_h": 700,         # mm
            "eta": 0.65,             # Utilization hiện tại
            "m_rd": 350,             # kN.m
            "v_rd": 250,             # kN
            "rebar_kg_per_m": 8.5,   # kg/m
            "concrete_grade": "B25",
            "steel_grade": "CB400V",
            "quantity": 120          # số lượng dầm
        }
    """
    if not material_prices:
        material_prices = {
            "concrete_B25": 2400000,  # VNĐ/m³
            "steel_CB400V": 19500,    # VNĐ/kg
            "formwork": 45000         # VNĐ/m²
        }

    name = member_data.get("name", "Beam")
    orig_b = member_data.get("section_b", 300)
    orig_h = member_data.get("section_h", 600)
    orig_eta = member_data.get("eta", 0.70)
    quantity = member_data.get("quantity", 1)

    # Nếu η > 0.85 → không cần VE
    if orig_eta > 0.85:
        return {
            "Status": "NO_OPTIMIZATION_NEEDED",
            "Reason": f"η = {orig_eta:.1%} > 85%, không có dư để tối ưu",
            "Recommendation": "Giữ nguyên tiết diện"
        }

    suggestions = []
    for opt in BEAM_DOWNGRADE_OPTIONS:
        new_h = orig_h + opt.get("dh", 0)
        new_b = orig_b + opt.get("db", 0)
        new_eta = estimate_eta_after_downgrade(orig_eta, orig_h, orig_b, opt.get("dh", 0), opt.get("db", 0))

        if new_eta is None or new_eta > opt.get("min_eta", 0.85):
            continue

        # Tính tiết kiệm
        # Tiết kiệm bê tông (m³): L (giả định 6m) × ΔA
        beam_L = member_data.get("length_mm", 6000) / 1000  # default 6m
        orig_concrete = orig_b * orig_h * beam_L / 1e6  # m³
        new_concrete = new_b * new_h * beam_L / 1e6
        concrete_save = orig_concrete - new_concrete
        concrete_save_vnd = concrete_save * material_prices["concrete_B25"] * 1000  # convert

        # Tiết kiệm cốt thép (nếu có)
        rebar_save = 0
        rebar_save_vnd = 0
        if "rebar_reduction" in opt:
            rebar_per_m = member_data.get("rebar_kg_per_m", 8.5)
            rebar_save = rebar_per_m * opt["rebar_reduction"] * beam_L
            rebar_save_vnd = rebar_save * material_prices["steel_CB400V"] * 1000

        # Tiết kiệm ván khuôn
        formwork_save = ((orig_b * 2 + orig_h * 2) - (new_b * 2 + new_h * 2)) / 1000 * beam_L
        formwork_save_vnd = max(0, formwork_save * material_prices["formwork"] * 1000)

        total_save = concrete_save_vnd + rebar_save_vnd + formwork_save_vnd

        # nhân số lượng dầm
        total_save_qty = total_save * quantity

        suggestions.append({
            "Label": opt["label"],
            "New_Section": f"{new_b}×{new_h}",
            "New_Eta": new_eta,
            "Savings_VND_per_unit": round(total_save, 0),
            "Savings_VND_total": round(total_save_qty, 0),
            "Concrete_Saved_m3": round(concrete_save * quantity, 2),
            "Rebar_Saved_kg": round(rebar_save * quantity, 1),
            "Status": "OK" if new_eta <= opt["min_eta"] else "BORDERLINE",
            "Trade_off": {
                "eta_increase": f"{orig_eta:.1%} → {new_eta:.1%}",
                "warning": "Giảm dự trữ an toàn" if new_eta > 0.80 else "Vẫn còn dự trữ hợp lý"
            }
        })

    if not suggestions:
        return {
            "Status": "NO_SAFE_DOWNGRADE",
            "Reason": "Mọi phương án giảm tiết diện đều vượt min_eta",
            "Recommendation": "Giữ nguyên, hoặc kiểm tra điều kiện biên để giảm tải"
        }

    # Chọn suggestion tiết kiệm nhất với η ≤ 90%
    best = max(suggestions, key=lambda x: x["Savings_VND_total"] if x["Status"] == "OK" else 0)

    return {
        "Status": "OPTIMIZATION_FOUND",
        "Member": name,
        "Original_Section": f"{orig_b}×{orig_h}",
        "Original_Eta": orig_eta,
        "Standard_Method": "TCVN 5574:2018 - Uốn & Veo",
        "Suggestions": suggestions,
        "Recommended": best,
        "Saving_Percent_VS_Original": round(
            (best["Savings_VND_total"] / (material_prices["concrete_B25"] * orig_b * orig_h * 6000 / 1e6 * 1000 + 10000000)) * 100, 1
        ),
        "Disclaimer": (
            "Đề xuất VE mang tính tham khảo. Cần kiểm tra lại với đầy đủ tổ hợp tải "
            "và điều kiện biên trước khi áp dụng. Kỹ sư có chứng chỉ hành nghề phải duyệt."
        )
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Material Optimization (VE)")
    parser.add_argument("--input", help="JSON file input (member_data)")
    parser.add_argument("--output", help="JSON file output")

    args = parser.parse_args()

    if args.input:
        with open(args.input, 'r', encoding='utf-8') as f:
            member_data = json.load(f)
    else:
        member_data = {
            "name": "Demo Beam",
            "type": "beam",
            "section_b": 300,
            "section_h": 700,
            "eta": 0.65,
            "rebar_kg_per_m": 8.5,
            "concrete_grade": "B25",
            "steel_grade": "CB400V",
            "quantity": 120
        }

    result = optimize_beam(member_data)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

    print(json.dumps(result, indent=2, ensure_ascii=False))
