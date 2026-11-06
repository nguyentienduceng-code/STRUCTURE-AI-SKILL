#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
evm_cpm_calculator.py — Bộ tính toán Tất định Quản lý Dự án (EVM & Đường găng CPM)
===================================================================================
Tuân thủ AGENTS.md §5 (Deterministic Math):
  1. Phân tích Giá trị Thu được (Earned Value Management - EVM):
     PV (BCWS), EV (BCWP), AC (ACWP), SV, CV, SPI, CPI, EAC, ETC, VAC, TCPI.
  2. Phân tích Đường găng Tiến độ (Critical Path Method - CPM):
     Forward Pass (ES, EF), Backward Pass (LS, LF), Total Float (TF), Free Float (FF),
     và xác định chuỗi công tác Găng (Critical Path).
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, List

if sys.stdout.encoding != "utf-8":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def calculate_evm(bac: float, pv: float, ev: float, ac: float) -> Dict[str, Any]:
    """Tính toán bộ chỉ số EVM chuẩn PMBOK."""
    if bac <= 0 or pv < 0 or ev < 0 or ac < 0:
        raise ValueError("Tham số ngân sách BAC phải > 0 và PV, EV, AC phải >= 0.")

    sv = round(ev - pv, 4)
    cv = round(ev - ac, 4)
    spi = round(ev / pv, 4) if pv > 0 else 1.0
    cpi = round(ev / ac, 4) if ac > 0 else 1.0

    eac_cpi = round(bac / cpi, 4) if cpi > 0 else float("inf")
    eac_composite = round(ac + (bac - ev) / (cpi * spi), 4) if (cpi * spi) > 0 else float("inf")
    etc = round(eac_cpi - ac, 4)
    vac = round(bac - eac_cpi, 4)
    rem_budget = bac - ac
    tcpi_bac = round((bac - ev) / rem_budget, 4) if rem_budget > 0 else float("inf")

    eta_cost = round(1.0 / cpi, 4) if cpi > 0 else 9.99
    eta_schedule = round(1.0 / spi, 4) if spi > 0 else 9.99

    status_cost = "ON_BUDGET" if cpi >= 1.0 else ("WARNING" if cpi >= 0.90 else "OVER_BUDGET_CRITICAL")
    status_sched = "ON_SCHEDULE" if spi >= 1.0 else ("WARNING" if spi >= 0.90 else "DELAYED_CRITICAL")

    logs = [
        {"step": 1, "desc": "Chênh lệch tiến độ (Schedule Variance)", "formula": "SV = EV - PV", "value": sv},
        {"step": 2, "desc": "Chênh lệch chi phí (Cost Variance)", "formula": "CV = EV - AC", "value": cv},
        {"step": 3, "desc": "Chỉ số hiệu suất tiến độ (SPI)", "formula": "SPI = EV / PV", "value": spi},
        {"step": 4, "desc": "Chỉ số hiệu suất chi phí (CPI)", "formula": "CPI = EV / AC", "value": cpi},
        {"step": 5, "desc": "Dự báo tổng chi phí khi hoàn thành (EAC)", "formula": "EAC = BAC / CPI", "value": eac_cpi},
        {"step": 6, "desc": "Chỉ số hiệu suất cần đạt cho phần việc còn lại (TCPI)", "formula": "TCPI = (BAC - EV) / (BAC - AC)", "value": tcpi_bac},
    ]

    return {
        "Standard_Method": "PMBOK 7th Edition / TCVN 4055:2012 (Tổ chức thi công)",
        "BAC": bac,
        "PV": pv,
        "EV": ev,
        "AC": ac,
        "SV": sv,
        "CV": cv,
        "SPI": spi,
        "CPI": cpi,
        "EAC_typical": eac_cpi,
        "EAC_composite": eac_composite,
        "ETC": etc,
        "VAC": vac,
        "TCPI_BAC": tcpi_bac,
        "eta_cost": eta_cost,
        "eta_schedule": eta_schedule,
        "Cost_Status": status_cost,
        "Schedule_Status": status_sched,
        "Calculation_Logs": logs,
    }


def calculate_cpm(tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Tính toán sơ đồ mạng CPM (Forward Pass & Backward Pass).
    Mỗi task: {"id": "A", "duration": 10, "predecessors": []}
    """
    nodes: Dict[str, Dict[str, Any]] = {}
    for t in tasks:
        tid = str(t["id"])
        nodes[tid] = {
            "id": tid,
            "name": t.get("name", tid),
            "duration": float(t["duration"]),
            "predecessors": [str(p) for p in t.get("predecessors", [])],
            "successors": [],
            "ES": 0.0,
            "EF": 0.0,
            "LS": 0.0,
            "LF": 0.0,
            "TF": 0.0,
            "FF": 0.0,
            "is_critical": False,
        }

    for tid, nd in nodes.items():
        for p in nd["predecessors"]:
            if p not in nodes:
                raise ValueError(f"Công tác tiền nhiệm '{p}' của '{tid}' không tồn tại.")
            nodes[p]["successors"].append(tid)

    in_deg = {tid: len(nd["predecessors"]) for tid, nd in nodes.items()}
    queue = [tid for tid, deg in in_deg.items() if deg == 0]
    order: List[str] = []
    while queue:
        curr = queue.pop(0)
        order.append(curr)
        for nxt in nodes[curr]["successors"]:
            in_deg[nxt] -= 1
            if in_deg[nxt] == 0:
                queue.append(nxt)

    if len(order) != len(nodes):
        raise ValueError("Phát hiện vòng lặp phụ thuộc (Circular Dependency) trong mạng tiến độ CPM!")

    for tid in order:
        nd = nodes[tid]
        nd["ES"] = max((nodes[p]["EF"] for p in nd["predecessors"]), default=0.0)
        nd["EF"] = round(nd["ES"] + nd["duration"], 4)

    project_duration = max((nd["EF"] for nd in nodes.values()), default=0.0)

    for tid in reversed(order):
        nd = nodes[tid]
        if not nd["successors"]:
            nd["LF"] = project_duration
        else:
            nd["LF"] = min(nodes[s]["LS"] for s in nd["successors"])
        nd["LS"] = round(nd["LF"] - nd["duration"], 4)
        nd["TF"] = round(nd["LF"] - nd["EF"], 4)
        if nd["successors"]:
            nd["FF"] = round(min(nodes[s]["ES"] for s in nd["successors"]) - nd["EF"], 4)
        else:
            nd["FF"] = nd["TF"]
        nd["is_critical"] = abs(nd["TF"]) < 1e-6

    critical_path = [tid for tid in order if nodes[tid]["is_critical"]]
    return {
        "Standard_Method": "CPM Network Analysis / TCVN 4055:2012",
        "project_duration_days": project_duration,
        "critical_path": critical_path,
        "tasks": [nodes[tid] for tid in order],
        "Calculation_Logs": [
            {"step": 1, "desc": "Forward Pass (ES, EF)", "formula": "ES_j = max(EF_i); EF_j = ES_j + D_j", "value": project_duration},
            {"step": 2, "desc": "Backward Pass (LS, LF) & Total Float", "formula": "LF_i = min(LS_j); TF_i = LF_i - EF_i", "value": len(critical_path)},
        ],
    }


def main():
    parser = argparse.ArgumentParser(description="EVM & CPM Deterministic Calculator (Project_Manager v1.0.0)")
    parser.add_argument("--bac", type=float, default=100.0, help="Budget at Completion (Tỷ VNĐ)")
    parser.add_argument("--pv", type=float, default=50.0, help="Planned Value (Tỷ VNĐ)")
    parser.add_argument("--ev", type=float, default=45.0, help="Earned Value (Tỷ VNĐ)")
    parser.add_argument("--ac", type=float, default=48.0, help="Actual Cost (Tỷ VNĐ)")
    parser.add_argument("--self-test", action="store_true", help="Chạy kiểm thử tự động EVM + CPM")
    args = parser.parse_args()

    evm_res = calculate_evm(args.bac, args.pv, args.ev, args.ac)
    sample_tasks = [
        {"id": "A", "name": "Pháp lý & GPXD", "duration": 15, "predecessors": []},
        {"id": "B", "name": "Thi công Cọc & Móng", "duration": 25, "predecessors": ["A"]},
        {"id": "C", "name": "Gia công Kết cấu thép tại xưởng", "duration": 20, "predecessors": ["A"]},
        {"id": "D", "name": "Lắp dựng Khung thép & Xà gồ", "duration": 18, "predecessors": ["B", "C"]},
        {"id": "E", "name": "Hoàn thiện & Nghiệm thu PCCC", "duration": 12, "predecessors": ["D"]},
    ]
    cpm_res = calculate_cpm(sample_tasks)
    out = {
        "module": "Project_Manager.evm_cpm_calculator",
        "version": "1.0.0",
        "Standard_Method": evm_res["Standard_Method"],
        "evm": evm_res,
        "cpm": cpm_res,
        "Calculation_Logs": evm_res["Calculation_Logs"] + cpm_res["Calculation_Logs"],
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
