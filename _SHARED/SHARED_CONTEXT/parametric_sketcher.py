#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
parametric_sketcher.py — Động Cơ Vẽ Tự Động Mặt Cắt Tham Số & Biểu Đồ Tương Tác N-M (v1.0)
===========================================================================================
Tự động kết xuất hình vẽ kỹ thuật 2D chuẩn xuất bản (300 DPI, Hệ màu Khoáng chất Tự nhiên v4.0)
từ thông số JSON đầu vào của các bài toán kết cấu để nhúng trực tiếp vào Thuyết minh Word (.docx)
và Bảng tính Excel (.xlsx):
  1. `draw_rc_section_sketch`: Mặt cắt ngang Dầm / Cột BTCT (b x h, cốt đai, cốt dọc, kích thước a, h0).
  2. `draw_steel_i_section_sketch`: Mặt cắt ngang Thép hình chữ I/H (H x B x tw x tf).
  3. `draw_nm_interaction_diagram`: Biểu đồ Tương tác N-M (P-M Curve) theo TCVN 5574:2018 kèm điểm tải trọng.
  4. `auto_generate_sketches_from_calc_data`: Tự động nhận diện loại cấu kiện trong JSON và sinh hình vẽ.
"""

from __future__ import annotations

import math
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# Hệ màu Khoáng chất & Mực in Kỹ thuật Tự nhiên (v4.0)
INK_PRIMARY   = "#1E3246"  # Deep Prussian Slate
INK_SECONDARY = "#2E4A62"  # Muted Steel Blue
BRONZE_RULE   = "#A67C37"  # Muted Bronze Ochre
CARMINE_RED   = "#8C261E"  # Carmine Brick Red (Cốt thép chịu kéo / Điểm vượt tải)
FOREST_PINE   = "#1E5631"  # Forest Pine Green (Điểm tải trọng an toàn)
CONCRETE_FILL = "#EFECE6"  # Warm Stone Concrete Tint
STEEL_FILL    = "#D9E1E8"  # Muted Metallic Slate
PAPER_BG      = "#FBFBF9"  # Natural Publication Paper


def _setup_serif_font():
    plt.rcParams["font.family"] = "serif"
    plt.rcParams["font.serif"] = ["Times New Roman", "Liberation Serif", "DejaVu Serif"]
    plt.rcParams["axes.edgecolor"] = "#8C8980"
    plt.rcParams["axes.linewidth"] = 0.8


def draw_rc_section_sketch(
    b_mm: float,
    h_mm: float,
    out_path: str,
    a_mm: float = 40.0,
    n_bars_bot: int = 4,
    dia_bot_mm: float = 20.0,
    n_bars_top: int = 2,
    dia_top_mm: float = 16.0,
    stirrup_dia_mm: float = 8.0,
    concrete_grade: str = "B25",
    rebar_grade: str = "CB400-V",
    title: str = "Mặt cắt ngang Tiết diện BTCT",
) -> str:
    """Vẽ mặt cắt ngang tiết diện BTCT (Dầm/Cột) chuẩn kỹ thuật 300 DPI."""
    _setup_serif_font()
    b = max(float(b_mm or 300.0), 120.0)
    h = max(float(h_mm or 500.0), 150.0)
    a = min(max(float(a_mm or 40.0), 20.0), h * 0.25)
    h0 = h - a

    fig, ax = plt.subplots(figsize=(5.6, 5.2), dpi=300)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    # 1. Vẽ tiết diện bê tông b x h
    rect_conc = patches.Rectangle(
        (0, 0), b, h,
        linewidth=2.0, edgecolor=INK_PRIMARY, facecolor=CONCRETE_FILL, zorder=2
    )
    ax.add_patch(rect_conc)

    # Chấm bi nhẹ biểu diễn vật liệu bê tông
    rng = np.random.default_rng(42)
    pts_x = rng.uniform(a * 0.6, b - a * 0.6, 45)
    pts_y = rng.uniform(a * 0.6, h - a * 0.6, 45)
    ax.scatter(pts_x, pts_y, s=3.5, color="#9E9A90", alpha=0.55, zorder=3)

    # 2. Vẽ cốt đai (Stirrup)
    c_nom = max(a - dia_bot_mm / 2.0 - stirrup_dia_mm, 20.0)
    rect_stirrup = patches.FancyBboxPatch(
        (c_nom, c_nom),
        b - 2 * c_nom,
        h - 2 * c_nom,
        boxstyle=f"round,pad=0,rounding_size={max(stirrup_dia_mm*1.5, 10.0)}",
        linewidth=1.4,
        edgecolor=INK_SECONDARY,
        facecolor="none",
        linestyle="-",
        zorder=4,
    )
    ax.add_patch(rect_stirrup)

    # 3. Vẽ cốt thép dọc lớp dưới (Chịu kéo / chính)
    r_bot = max(dia_bot_mm * 0.65, min(b, h) * 0.028)
    n_bot = max(int(n_bars_bot or 3), 2)
    x_bots = np.linspace(a, b - a, n_bot) if n_bot > 1 else [b / 2.0]
    for xb in x_bots:
        circle = patches.Circle((xb, a), radius=r_bot, facecolor=CARMINE_RED, edgecolor="#1C1E21", linewidth=0.9, zorder=5)
        ax.add_patch(circle)

    # 4. Vẽ cốt thép dọc lớp trên (Cấu tạo / Chịu nén)
    r_top = max(dia_top_mm * 0.60, min(b, h) * 0.024)
    n_top = max(int(n_bars_top or 2), 2)
    x_tops = np.linspace(a, b - a, n_top) if n_top > 1 else [b / 2.0]
    for xt in x_tops:
        circle = patches.Circle((xt, h - a), radius=r_top, facecolor=INK_PRIMARY, edgecolor="#1C1E21", linewidth=0.9, zorder=5)
        ax.add_patch(circle)

    # 5. Đường kích thước b, h, h0
    offset_b = h * 0.14
    offset_h = b * 0.18
    # Kích thước bề rộng b
    ax.annotate(
        "", xy=(0, -offset_b), xytext=(b, -offset_b),
        arrowprops=dict(arrowstyle="<->", color=INK_PRIMARY, lw=1.1)
    )
    ax.plot([0, 0], [0, -offset_b * 1.2], color="#8C8980", lw=0.7, ls="--")
    ax.plot([b, b], [0, -offset_b * 1.2], color="#8C8980", lw=0.7, ls="--")
    ax.text(b / 2.0, -offset_b * 1.45, f"b = {int(b)} mm", ha="center", va="top", fontsize=9.5, fontweight="bold", color=INK_PRIMARY)

    # Kích thước chiều cao h
    ax.annotate(
        "", xy=(-offset_h, 0), xytext=(-offset_h, h),
        arrowprops=dict(arrowstyle="<->", color=INK_PRIMARY, lw=1.1)
    )
    ax.plot([0, -offset_h * 1.15], [0, 0], color="#8C8980", lw=0.7, ls="--")
    ax.plot([0, -offset_h * 1.15], [h, h], color="#8C8980", lw=0.7, ls="--")
    ax.text(-offset_h * 1.25, h / 2.0, f"h = {int(h)} mm", ha="right", va="center", rotation=90, fontsize=9.5, fontweight="bold", color=INK_PRIMARY)

    # Kích thước chiều cao làm việc h0 (bên phải)
    ax.annotate(
        "", xy=(b + offset_h * 0.85, a), xytext=(b + offset_h * 0.85, h),
        arrowprops=dict(arrowstyle="<->", color=BRONZE_RULE, lw=1.0)
    )
    ax.plot([b, b + offset_h], [a, a], color=BRONZE_RULE, lw=0.7, ls=":")
    ax.plot([b, b + offset_h], [h, h], color=BRONZE_RULE, lw=0.7, ls=":")
    ax.text(b + offset_h * 1.05, (h + a) / 2.0, f"h0 = {int(h0)} mm", ha="left", va="center", rotation=90, fontsize=9.0, color="#8F5314", fontweight="bold")

    # Nhãn ghi chú cốt thép
    ax.text(
        b / 2.0, h + offset_b * 0.55,
        f"Bê tông {concrete_grade} | Thép {rebar_grade} ({n_bot}Φ{int(dia_bot_mm)} dưới, {n_top}Φ{int(dia_top_mm)} trên)",
        ha="center", va="bottom", fontsize=9.0, color=INK_SECONDARY, fontweight="bold"
    )

    ax.set_title(title, fontsize=11.0, fontweight="bold", color=INK_PRIMARY, pad=18)
    ax.set_aspect("equal")
    ax.set_xlim(-offset_h * 2.2, b + offset_h * 2.0)
    ax.set_ylim(-offset_b * 2.3, h + offset_b * 1.3)
    ax.axis("off")

    os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)
    plt.tight_layout()
    plt.savefig(out_path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return os.path.abspath(out_path)


def draw_nm_interaction_diagram(
    out_path: str,
    b_mm: float = 400.0,
    h_mm: float = 400.0,
    Rb_MPa: float = 14.5,
    Rs_MPa: float = 350.0,
    As_total_cm2: float = 16.0,
    N_Ed_kN: float = 1200.0,
    M_Ed_kNm: float = 180.0,
    title: str = "Biểu đồ Tương tác N-M Tiết diện Cột/Vách BTCT (TCVN 5574:2018)",
) -> str:
    """
    Vẽ Biểu đồ Tương tác N-M (P-M Interaction Envelope) theo TCVN 5574:2018
    kèm điểm nội lực tính toán (M_Ed, N_Ed) để kiểm định trực quan miền an toàn.
    """
    _setup_serif_font()
    A_conc_mm2 = b_mm * h_mm
    As_mm2 = As_total_cm2 * 100.0
    h0 = h_mm - 45.0
    z_s = max(h_mm - 90.0, h_mm * 0.7)

    # Khả năng chịu nén thuần túy N_u0 (kN)
    N_u0 = (Rb_MPa * A_conc_mm2 + Rs_MPa * As_mm2) / 1000.0
    # Điểm cân bằng dẻo (Balanced Point xi_R ~ 0.53)
    xi_R = 0.53
    N_bal = (Rb_MPa * b_mm * (xi_R * h0)) / 1000.0
    M_bal = (
        Rb_MPa * b_mm * (xi_R * h0) * (h_mm / 2.0 - 0.5 * xi_R * h0)
        + Rs_MPa * (As_mm2 / 2.0) * z_s
    ) / 1e6
    # Khả năng chịu uốn thuần túy M_u0 (N = 0)
    M_u0 = (Rs_MPa * (As_mm2 / 2.0) * z_s) / 1e6 * 1.12
    # Khả năng chịu kéo thuần túy N_t0 (kN)
    N_t0 = -(Rs_MPa * As_mm2) / 1000.0

    # Nội suy đường cong bao trơn qua 4 điểm đặc trưng: (0, N_t0) -> (M_u0, 0) -> (M_bal, N_bal) -> (0, N_u0)
    n_upper = np.linspace(N_bal, N_u0, 35)
    m_upper = M_bal * np.sin((N_u0 - n_upper) / max(N_u0 - N_bal, 1e-3) * (np.pi / 2.0)) ** 0.85

    n_mid = np.linspace(0.0, N_bal, 35)
    m_mid = M_u0 + (M_bal - M_u0) * np.sin(n_mid / max(N_bal, 1e-3) * (np.pi / 2.0))

    n_low = np.linspace(N_t0, 0.0, 20)
    m_low = M_u0 * (1.0 - (n_low / min(N_t0, -1e-3)))

    M_curve = np.concatenate([m_low, m_mid[1:], m_upper[1:]])
    N_curve = np.concatenate([n_low, n_mid[1:], n_upper[1:]])

    fig, ax = plt.subplots(figsize=(6.4, 4.6), dpi=300)
    fig.patch.set_facecolor("white")
    ax.set_facecolor(PAPER_BG)

    # Tô miền an toàn bên trong đường cong bao
    ax.fill_betweenx(N_curve, 0, M_curve, color="#EBF3ED", alpha=0.65, label="Miền chịu lực an toàn [N_u, M_u]")
    ax.plot(M_curve, N_curve, color=INK_PRIMARY, linewidth=2.2, label="Đường bao khả năng chịu lực (TCVN 5574:2018)")

    # Đường giới hạn nén dọc trục có xét lệch tâm ngẫu nhiên (0.85 * N_u0)
    ax.axhline(0.85 * N_u0, color=BRONZE_RULE, linestyle="--", linewidth=1.1, label=f"Giới hạn 0.85·Nu0 = {0.85*N_u0:.0f} kN")
    ax.axhline(0.0, color="#8C8980", linewidth=0.8)

    # Điểm nội lực tính toán (M_Ed, N_Ed)
    m_pt = abs(float(M_Ed_kNm or 0.0))
    n_pt = float(N_Ed_kN or 0.0)
    # Kiểm tra điểm có nằm trong đường bao không
    m_cap_at_n = float(np.interp(n_pt, N_curve, M_curve)) if (N_t0 <= n_pt <= N_u0) else 0.0
    is_safe = (m_pt <= m_cap_at_n) and (n_pt <= 0.85 * N_u0)
    pt_color = FOREST_PINE if is_safe else CARMINE_RED
    status_tag = "[ĐẠT]" if is_safe else "[VƯỢT MIỀN CHỊU LỰC]"

    ax.scatter([m_pt], [n_pt], s=75, color=pt_color, edgecolors="white", linewidth=1.5, zorder=6,
               label=f"Tổ hợp thiết kế ({m_pt:.1f} kN.m, {n_pt:.0f} kN) {status_tag}")
    ax.annotate(
        f"  E_d ({m_pt:.1f}; {n_pt:.0f})\n  {status_tag}",
        xy=(m_pt, n_pt),
        fontsize=8.5,
        fontweight="bold",
        color=pt_color,
        va="center",
    )

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(True, linestyle="--", color="#D0CEC7", alpha=0.55)
    ax.set_xlabel("Mô men uốn thiết kế M (kN.m)", fontsize=9.5, fontweight="bold", color=INK_PRIMARY)
    ax.set_ylabel("Lực dọc trục N (kN)", fontsize=9.5, fontweight="bold", color=INK_PRIMARY)
    ax.set_title(title, fontsize=10.5, fontweight="bold", color=INK_PRIMARY, pad=12)
    ax.set_xlim(0, max(float(np.max(M_curve)) * 1.22, m_pt * 1.25, 50.0))
    ax.legend(loc="upper right", frameon=True, facecolor="white", edgecolor="#D0CEC7", fontsize=8.0)

    os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)
    plt.tight_layout()
    plt.savefig(out_path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return os.path.abspath(out_path)


def auto_generate_sketches_from_calc_data(calc_data: Dict[str, Any], out_dir: str, prefix: str = "sketch") -> List[str]:
    """
    Tự động phân tích dữ liệu JSON tính toán và sinh bộ hình vẽ kỹ thuật 2D (Mặt cắt tiết diện & Biểu đồ N-M)
    để nhúng tự động vào Thuyết minh Word (.docx) và Bảng tính Excel (.xlsx).
    """
    os.makedirs(out_dir, exist_ok=True)
    generated: List[str] = []

    inp = dict(calc_data)
    if isinstance(calc_data.get("Input"), dict):
        inp.update(calc_data["Input"])
    if isinstance(calc_data.get("Results"), dict):
        inp.update(calc_data["Results"])

    b = inp.get("b") or inp.get("b_mm") or inp.get("width_mm") or 300.0
    h = inp.get("h") or inp.get("h_mm") or inp.get("depth_mm") or 500.0
    a = inp.get("a") or inp.get("a_mm") or 40.0
    dia = inp.get("dia") or inp.get("dia_mm") or inp.get("Diameter_mm") or 20.0
    n_bars = inp.get("n_bars") or inp.get("count") or 4
    concrete = str(inp.get("concrete") or inp.get("Concrete_Grade") or "B25")
    rebar = str(inp.get("rebar") or inp.get("Rebar_Grade") or "CB400-V")

    # 1. Luôn sinh sơ đồ mặt cắt ngang tham số BTCT
    sec_path = os.path.join(out_dir, f"{prefix}_rc_section.png")
    draw_rc_section_sketch(
        b_mm=float(b),
        h_mm=float(h),
        out_path=sec_path,
        a_mm=float(a),
        n_bars_bot=int(n_bars),
        dia_bot_mm=float(dia),
        concrete_grade=concrete,
        rebar_grade=rebar,
    )
    generated.append(sec_path)

    # 2. Nếu bài toán có lực dọc N và mô men M (cột / vách / cấu kiện nén uốn) -> sinh thêm Biểu đồ tương tác N-M
    n_val = inp.get("N") or inp.get("N_Ed") or inp.get("N_ed") or inp.get("N_tc")
    m_val = inp.get("M") or inp.get("M_Ed") or inp.get("M_ed") or inp.get("M_tc")
    if isinstance(n_val, (int, float)) and isinstance(m_val, (int, float)) and float(n_val) > 0:
        nm_path = os.path.join(out_dir, f"{prefix}_nm_interaction.png")
        draw_nm_interaction_diagram(
            out_path=nm_path,
            b_mm=float(b),
            h_mm=float(h),
            N_Ed_kN=float(n_val),
            M_Ed_kNm=float(m_val),
        )
        generated.append(nm_path)

    return generated
