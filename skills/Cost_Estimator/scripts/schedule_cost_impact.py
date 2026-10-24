#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MODULE 5: Schedule Impact & Hidden Interest Cost
Tính chi phí lãi vay ẩn do chênh lệch tiến độ giữa các phương án.

Công thức: Hidden_Interest = Total_Investment × (Rate/365) × Δ_Duration_Days

Input:
- Tổng vốn đầu tư
- Lãi suất vay năm
- Danh sách phương án (mỗi PA có duration_days)

Output:
- Bảng so sánh CAPEX điều chỉnh
- Khuyến nghị PA có Adjusted_CAPEX thấp nhất
"""

import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
import sys
import json
import argparse
from datetime import datetime


def calculate_schedule_impact(options, total_investment, annual_rate=0.10, time_unit="days"):
    """
    Tính hidden interest cho mỗi phương án.

    Args:
        options: [
            {"name": "PA-A", "type": "RC", "capex": 968500000, "duration_days": 45},
            ...
        ]
        total_investment: Tổng vốn đầu tư (VNĐ)
        annual_rate: Lãi suất năm (decimal, e.g. 0.10 = 10%/năm)
        time_unit: 'days' hoặc 'months'
    """
    if not options:
        return {"error": "options rỗng"}

    if time_unit == "months":
        divisor = 12
    else:
        divisor = 365

    # Tìm base duration (PA ngắn nhất)
    base_duration = min(opt.get("duration_days", 999) for opt in options)

    calc_logs = []
    calc_logs.append({
        "Step": 1,
        "Title": "Xác định phương án nhanh nhất (baseline)",
        "Formula": "Base_Duration = min(duration_days) across options",
        "Substitution": f"min({[opt.get('duration_days', 0) for opt in options]})",
        "Result": f"Base_Duration = {base_duration} {time_unit}",
        "Citation": {
            "code": "Method",
            "year": "2026",
            "article": "NPV time-value adjustment",
            "excerpt": "Phương án nhanh nhất được chọn làm baseline (Δ=0)"
        }
    })

    calc_logs.append({
        "Step": 2,
        "Title": "Công thức Hidden Interest",
        "Formula": "Hidden_Interest = Total_Investment × (Rate/365) × Δ_Duration",
        "Substitution": (
            f"{total_investment:,.0f} × ({annual_rate}/{divisor}) × Δ_Duration"
        ),
        "Result": (
            f"Hidden_Interest / day = "
            f"{total_investment * annual_rate / divisor:,.0f} VNĐ/ngày"
        ),
        "Citation": {
            "code": "TCVN 2628:1995",
            "year": "1995",
            "article": "Time-value of money",
            "excerpt": "Chiết khấu dòng tiền theo lãi suất thị trường"
        }
    })

    results = []
    for opt in options:
        capex = opt.get("capex", 0)
        duration = opt.get("duration_days", 0)
        delta = duration - base_duration

        # Hidden interest: chỉ tính phần delta vượt baseline
        hidden_interest = 0
        if delta > 0:
            hidden_interest = total_investment * (annual_rate / divisor) * delta

        adjusted_capex = capex + hidden_interest

        results.append({
            "name": opt.get("name", "PA"),
            "type": opt.get("type", "Unknown"),
            "capex": capex,
            "duration_days": duration,
            "delta_days": delta,
            "hidden_interest_VND": round(hidden_interest),
            "adjusted_capex": round(adjusted_capex),
            "adjusted_capex_per_day_saved": round((adjusted_capex - capex) / delta, 0) if delta > 0 else 0
        })

    # Sort by adjusted_capex
    sorted_results = sorted(results, key=lambda x: x["adjusted_capex"])
    for rank, item in enumerate(sorted_results, start=1):
        item["rank"] = rank

    # Recommendation
    winner = sorted_results[0]
    runner_up = sorted_results[1] if len(sorted_results) > 1 else None
    savings_vs_runner_up = (
        runner_up["adjusted_capex"] - winner["adjusted_capex"]
        if runner_up else 0
    )

    recommendation = f"Khuyến nghị: {winner['name']}"
    if savings_vs_runner_up > 0:
        recommendation += (
            f" (tiết kiệm {savings_vs_runner_up:,.0f} VNĐ so với {runner_up['name']} "
            f"sau khi tính hidden interest)"
        )

    calc_logs.append({
        "Step": 3,
        "Title": "Xếp hạng theo Adjusted_CAPEX",
        "Formula": "Sort(options, key=adjusted_capex)",
        "Substitution": (
            f"Sorted: {[r['name'] for r in sorted_results]}"
        ),
        "Result": (
            f"#{winner['rank']} = {winner['name']}, "
            f"Adjusted_CAPEX = {winner['adjusted_capex']:,.0f} VNĐ"
        ),
        "Citation": {
            "code": "Method",
            "year": "2026",
            "article": "NPV-adjusted cost comparison",
            "excerpt": "Phương án tối ưu khi xét time-value of money"
        }
    })

    return {
        "Calculation_Date": datetime.now().isoformat(),
        "Standard_Method": "NPV Adjustment / TCVN 2628:1995",
        "Inputs": {
            "Total_Investment_VND": total_investment,
            "Annual_Rate": annual_rate,
            "Time_Unit": time_unit,
            "Divisor": divisor,
            "Interest_Per_Day": round(total_investment * annual_rate / divisor, 0)
        },
        "Calculation_Logs": calc_logs,
        "Base_Duration_Days": base_duration,
        "Options": sorted_results,
        "Winner": winner["name"],
        "Recommendation": recommendation,
        "NPV_Note": (
            "Trong dự án thực, tiền lãi vay còn phụ thuộc vào schedule giải ngân "
            "(cash-flow curve), không phải đều đặn. Công cụ này giả định giải ngân đều."
        ),
        "Disclaimer": (
            "Tính toán tham khảo. Lãi suất và tổng vốn cần xác nhận với phòng Tài chính. "
            "Trợ lý AI không thay thế chuyên gia tài chính dự án."
        )
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Schedule Impact & Hidden Interest")
    parser.add_argument("--investment", type=float, required=True, help="Tổng vốn đầu tư (VNĐ)")
    parser.add_argument("--rate", type=float, default=0.10, help="Lãi suất năm (decimal)")
    parser.add_argument("--options", help="JSON file input")
    parser.add_argument("--output", help="JSON output file")

    args = parser.parse_args()

    if args.options:
        with open(args.options, 'r', encoding='utf-8') as f:
            options = json.load(f)
    else:
        options = [
            {"name": "PA-A BTCT", "type": "RC", "capex": 968500000, "duration_days": 45},
            {"name": "PA-B Steel", "type": "Steel", "capex": 818300000, "duration_days": 30},
            {"name": "PA-C Precast", "type": "Precast", "capex": 869100000, "duration_days": 35}
        ]

    result = calculate_schedule_impact(
        options=options,
        total_investment=args.investment,
        annual_rate=args.rate
    )

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

    print(json.dumps(result, indent=2, ensure_ascii=False))
