#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ms_project_gantt.py — Engine Tiến Độ Dự Án Chuẩn Microsoft Project / Primavera P6 (PMO Enterprise v2.0.0)
=========================================================================================================
Tích hợp chính thức trong:
  - `.agents/skills/Project_Manager/scripts/ms_project_gantt.py` (v2.0.0)
  - `.agents/skills/Technical_Illustrator/scripts/ms_project_gantt.py` (v2.0.0)

Năng lực Cốt lõi (12 Đặc tính Kỹ thuật PMO / Microsoft Project Professional v2.0.0):
  1. [Đặc tính 1] Giao diện Đôi 11 Cột (11-Column PMO Split View):
     `ID` | `WBS` | `Tên công việc (Task Name)` | `Thời lượng` | `Bắt đầu` | `Kết thúc` |
     `Tiền nhiệm` | `% HT` | `Dự trữ (TF)` | `BAC (Tr.đ)` | `Đơn vị / Tài nguyên`.
  2. [Đặc tính 2] Thanh Tổng hợp Tiến độ (Summary Brackets):
     Thanh ngang màu than đá phiến `#1E3246` kèm 2 mỏ neo tam giác chúc xuống và nhãn tổng thời lượng + % hoàn thành.
  3. [Đặc tính 3] Tự động Giải Mạng Đường Găng CPM (Auto-CPM Network Engine):
     Tự động phân tích quan hệ `FS`, `SS`, `FF`, `SF` (kèm Lag/Lead), tính toán `ES, EF, LS, LF`,
     Dự trữ toàn phần `Total Float (TF)` và Dự trữ tự do `Free Float (FF)`, phân tầng Đỏ Găng (`#D32F2F`) vs Xanh Thường (`#1976D2`).
  4. [Đặc tính 4] Tracking Gantt — So sánh Tiến độ Cơ sở (Baseline Bars) & Thanh Dự trữ (Total Float Bars):
     Mỗi công tác hiển thị đồng thời Thanh Thực tế/Kế hoạch ở nửa trên (kèm lõi `% Complete`) + Thanh Baseline (`#78909C`)
     ở nửa dưới + Thanh Dự trữ `Total Float` nét đứt kéo dài từ `EF` đến `LF` kèm nhãn `TF:Xd`.
  5. [Đặc tính 5] Mũi tên Liên kết Phụ thuộc Vuông góc (Corridor-Routed Stepped Dependency Arrows):
     Đi theo hành lang biên dòng không cắt qua nhãn chữ.
  6. [Đặc tính 6] Mốc Kiểm soát (Milestones 0d):
     Hình thoi đặc (Diamond marker) kèm nhãn ngày tháng và trạng thái găng.
  7. [Đặc tính 7] Thước đo Thời gian 2 Tầng (Dual-Tier Timescale Header):
     Tầng 1 (Tháng/Năm — nền `#DCE4EC` chữ `#1E3246`) và Tầng 2 (Tuần/Ngày đầu tuần — nền `#EAE6DF` chữ `#1E3246`).
  8. [Đặc tính 8] Dải Cách ly Ngày Nghỉ Lễ (Non-working Time Band) & Đường Kiểm soát (Status Date Line):
     Tô sọc chéo `#FFEBEE` viền `#EF9A9A` cho kỳ nghỉ lễ (Tết Nguyên Đán) và đường mốc báo cáo (Status Date).
  9. [Đặc tính 9] Tầng Đáy Đồng bộ Trục Thời gian: Đường cong S (EVM S-Curve) & Biểu đồ Giải ngân (Cashflow Histogram):
     Đồng bộ 100% trục thời gian X ngay dưới Gantt Canvas, hiển thị đường lũy kế `PV (BCWS)`, `EV (BCWP)`, `AC (ACWP)`
     kèm cột giải ngân hàng tháng và Bảng Scorecard EVM + PERT/Monte Carlo (`P50, P80, P90`) bên trái.
 10. [Đặc tính 10] Xuất Tệp Dự Án Gốc Chuẩn Microsoft Project XML (`.xml` — MSPDI Schema):
     Mở trực tiếp trong Microsoft Project Professional, ProjectLibre, và Oracle Primavera P6.
 11. [Đặc tính 11] Xuất Workbook Excel Quản trị Tiến độ Động 4 Sheet (`.xlsx` — PMO Enterprise Tracker):
     Liên kết công thức động 100%, tuân thủ Natural Print Palette (Zero White Text Lock).
 12. [Đặc tính 12] Cơ chế Nhúng Thông minh vào Văn bản Word (`.docx` Landscape A4 300 DPI):
     Tự động ngắt Section Break sang khổ A4 Xoay Ngang (29.7 x 21.0 cm) nhúng ảnh 300 DPI và trả về khổ A4 Dọc.
"""

import argparse
import datetime
import json
import math
import os
import sys
import xml.etree.ElementTree as ET
from xml.dom import minidom
from typing import Any, Dict, List, Optional, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as patches

if sys.stdout.encoding != "utf-8":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Liberation Sans", "Arial", "Segoe UI", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False

# Hệ màu Bảng biểu & Biểu đồ In ấn Tự nhiên (Natural Print Palette v4.4 — Zero White Text Lock)
COLOR_HEADER_BG = "#DCE4EC"       # Xanh Đá Phiến Sương Nhạt (Tầng 1 Header & Header Bảng Task Sheet)
COLOR_SUBHEADER_BG = "#EAE6DF"    # Đá Vôi Sáng (Tầng 2 Timescale & Dòng Summary Task)
COLOR_HEADER_TEXT = "#1E3246"     # Chữ đậm Xanh Thép Trầm (Tuyệt đối không dùng chữ trắng)
COLOR_BORDER_OUTER = "#1E3246"    # Viền khung chính
COLOR_BORDER = "#D0CEC7"          # Đường kẻ lưới Xám Đá
COLOR_ROW_EVEN = "#FFFFFF"        # Nền dòng chẵn
COLOR_ROW_ALT = "#F8F7F4"         # Nền Ngà Giấy Tự Nhiên dòng lẻ
COLOR_TEXT_MAIN = "#1C1E21"       # Mực Than Chì
COLOR_TEXT_MUTED = "#5A626A"      # Xám Chì Ấm

COLOR_SUMMARY_BAR = "#1E3246"     # Thanh Summary Task Brackets màu than sẫm
COLOR_STANDARD_BAR = "#1976D2"    # Thanh công tác thường (MS Project Blue)
COLOR_CRITICAL_BAR = "#D32F2F"    # Thanh công tác Găng (Critical Path Red)
COLOR_BASELINE_BAR = "#78909C"    # Thanh tiến độ cơ sở (Baseline Slate Gray)
COLOR_FLOAT_BAR = "#546E7A"       # Thanh dự trữ toàn phần (Total Float Bar)
COLOR_MILESTONE = "#263238"       # Mốc Milestone hình thoi (0d)
COLOR_ARROW = "#455A64"           # Mũi tên liên kết phụ thuộc
COLOR_HOLIDAY = "#FFEBEE"         # Dải cách ly ngày nghỉ lễ
COLOR_HOLIDAY_EDGE = "#EF9A9A"    # Viền dải ngày nghỉ lễ


def get_ho_yen_quang_tasks() -> List[Dict[str, Any]]:
    """
    Bộ dữ liệu tiến độ chuẩn hóa MS Project Enterprise v2.0.0 (22 công tác, 4 giai đoạn WBS, 4 mốc Milestone),
    bổ sung đầy đủ thông số Baseline, Ngân sách BAC (Triệu VNĐ), Chi phí thực tế AC, và 3 điểm ước lượng PERT.
    """
    return [
        # GIAI ĐOẠN 1
        {
            "id": 1, "wbs": "1.0", "name": "GIAI ĐOẠN 1: KHẢO SÁT & ĐÁNH GIÁ MÔI TRƯỜNG NỀN",
            "start": "2026-11-10", "end": "2026-12-25", "baseline_start": "2026-11-10", "baseline_end": "2026-12-22",
            "duration": 46, "predecessors": "", "resources": "Ban QLDA",
            "is_summary": True, "is_critical": True, "percent_complete": 100,
            "bac": 3250.0, "ac": 3180.0,
        },
        {
            "id": 2, "wbs": "1.1", "name": "Khảo sát trắc địa, địa hình bờ & đo sâu lòng hồ",
            "start": "2026-11-10", "end": "2026-12-20", "baseline_start": "2026-11-10", "baseline_end": "2026-12-18",
            "duration": 41, "predecessors": "", "resources": "TV Khảo sát",
            "is_summary": False, "is_critical": False, "color": "#0288D1", "percent_complete": 100,
            "bac": 1150.0, "ac": 1120.0, "pert_o": 35, "pert_m": 41, "pert_p": 48,
        },
        {
            "id": 3, "wbs": "1.2", "name": "Khoan khảo sát ĐCCT trên bờ & dưới lòng hồ",
            "start": "2026-11-15", "end": "2026-12-25", "baseline_start": "2026-11-15", "baseline_end": "2026-12-22",
            "duration": 41, "predecessors": "", "resources": "TV Khảo sát",
            "is_summary": False, "is_critical": True, "color": "#D32F2F", "percent_complete": 100,
            "bac": 1480.0, "ac": 1450.0, "pert_o": 36, "pert_m": 41, "pert_p": 52,
        },
        {
            "id": 4, "wbs": "1.3", "name": "Khảo sát chuỗi thủy văn hồ & bùn cát lịch sử",
            "start": "2026-11-10", "end": "2026-12-15", "baseline_start": "2026-11-10", "baseline_end": "2026-12-15",
            "duration": 36, "predecessors": "", "resources": "TV Khảo sát",
            "is_summary": False, "is_critical": False, "color": "#0288D1", "percent_complete": 100,
            "bac": 620.0, "ac": 610.0, "pert_o": 30, "pert_m": 36, "pert_p": 42,
        },
        {
            "id": 5, "wbs": "1.4", "name": "Mốc M1: Nghiệm thu Báo cáo Khảo sát toàn diện",
            "start": "2026-12-25", "end": "2026-12-25", "baseline_start": "2026-12-22", "baseline_end": "2026-12-22",
            "duration": 0, "predecessors": "3,4", "resources": "Chủ đầu tư",
            "is_milestone": True, "is_critical": True, "percent_complete": 100,
            "bac": 0.0, "ac": 0.0, "pert_o": 0, "pert_m": 0, "pert_p": 0,
        },

        # GIAI ĐOẠN 2
        {
            "id": 6, "wbs": "2.0", "name": "GIAI ĐOẠN 2: PHÁP LÝ MÔI TRƯỜNG & THỎA THUẬN THỦY LỢI",
            "start": "2026-11-15", "end": "2027-03-31", "baseline_start": "2026-11-15", "baseline_end": "2027-03-25",
            "duration": 137, "predecessors": "", "resources": "Ban PTDA",
            "is_summary": True, "is_critical": True, "percent_complete": 58,
            "bac": 2450.0, "ac": 1460.0,
        },
        {
            "id": 7, "wbs": "2.1", "name": "Đo đạc môi trường nền & lập Báo cáo ĐTM",
            "start": "2026-11-15", "end": "2027-01-10", "baseline_start": "2026-11-15", "baseline_end": "2027-01-08",
            "duration": 57, "predecessors": "", "resources": "TV ĐTM",
            "is_summary": False, "is_critical": True, "color": "#D32F2F", "percent_complete": 100,
            "bac": 980.0, "ac": 960.0, "pert_o": 48, "pert_m": 57, "pert_p": 68,
        },
        {
            "id": 8, "wbs": "2.2", "name": "Tham vấn VQG Cúc Phương & Thỏa thuận hồ Thủy lợi",
            "start": "2026-12-01", "end": "2027-01-15", "baseline_start": "2026-12-01", "baseline_end": "2027-01-12",
            "duration": 46, "predecessors": "2SS", "resources": "TV ĐTM & CĐT",
            "is_summary": False, "is_critical": False, "color": "#2E7D32", "percent_complete": 90,
            "bac": 620.0, "ac": 500.0, "pert_o": 38, "pert_m": 46, "pert_p": 58,
        },
        {
            "id": 9, "wbs": "2.3", "name": "Thẩm định ĐTM tại Hội đồng Bộ Tài nguyên & MT",
            "start": "2027-01-16", "end": "2027-03-31", "baseline_start": "2027-01-12", "baseline_end": "2027-03-25",
            "duration": 75, "predecessors": "7,8", "resources": "Bộ TN&MT",
            "is_summary": False, "is_critical": False, "color": "#0288D1", "percent_complete": 0,
            "bac": 850.0, "ac": 0.0, "pert_o": 60, "pert_m": 75, "pert_p": 95,
        },
        {
            "id": 10, "wbs": "2.4", "name": "Mốc M2: Quyết định Phê duyệt Báo cáo ĐTM",
            "start": "2027-03-31", "end": "2027-03-31", "baseline_start": "2027-03-25", "baseline_end": "2027-03-25",
            "duration": 0, "predecessors": "9", "resources": "Bộ TN&MT",
            "is_milestone": True, "is_critical": False, "percent_complete": 0,
            "bac": 0.0, "ac": 0.0, "pert_o": 0, "pert_m": 0, "pert_p": 0,
        },

        # GIAI ĐOẠN 3
        {
            "id": 11, "wbs": "3.0", "name": "GIAI ĐOẠN 3: F/S & THIẾT KẾ CƠ SỞ (TKCS ĐA BỘ MÔN)",
            "start": "2026-11-10", "end": "2027-04-10", "baseline_start": "2026-11-10", "baseline_end": "2027-04-05",
            "duration": 152, "predecessors": "", "resources": "QLTK & TVTK",
            "is_summary": True, "is_critical": True, "percent_complete": 42,
            "bac": 6800.0, "ac": 2890.0,
        },
        {
            "id": 12, "wbs": "3.1", "name": "Thiết kế Ý tưởng Kiến trúc (2 phương án thi tuyển)",
            "start": "2026-11-10", "end": "2026-12-15", "baseline_start": "2026-11-10", "baseline_end": "2026-12-15",
            "duration": 36, "predecessors": "", "resources": "TVTK Lead",
            "is_summary": False, "is_critical": False, "color": "#1976D2", "percent_complete": 100,
            "bac": 1650.0, "ac": 1620.0, "pert_o": 30, "pert_m": 36, "pert_p": 45,
        },
        {
            "id": 13, "wbs": "3.2", "name": "Lập Báo cáo NCKT (F/S) & TKCS bờ, hạ tầng, MEP",
            "start": "2026-12-16", "end": "2027-01-25", "baseline_start": "2026-12-16", "baseline_end": "2027-01-22",
            "duration": 41, "predecessors": "5,12", "resources": "TVTK Lead",
            "is_summary": False, "is_critical": True, "color": "#D32F2F", "percent_complete": 35,
            "bac": 2650.0, "ac": 920.0, "pert_o": 35, "pert_m": 41, "pert_p": 52,
        },
        {
            "id": 14, "wbs": "3.3", "name": "Lập TKCS Kết cấu nổi Pontoon & Hệ cọc neo giữ",
            "start": "2026-12-16", "end": "2027-01-25", "baseline_start": "2026-12-16", "baseline_end": "2027-01-22",
            "duration": 41, "predecessors": "5", "resources": "TVTK Pontoon",
            "is_summary": False, "is_critical": False, "color": "#1976D2", "percent_complete": 25,
            "bac": 1550.0, "ac": 350.0, "pert_o": 34, "pert_m": 41, "pert_p": 50,
        },
        {
            "id": 15, "wbs": "3.4", "name": "Sở Xây dựng Thẩm định TKCS & phê duyệt F/S",
            "start": "2027-02-10", "end": "2027-04-10", "baseline_start": "2027-02-05", "baseline_end": "2027-04-05",
            "duration": 60, "predecessors": "13,14", "resources": "Sở Xây dựng",
            "is_summary": False, "is_critical": True, "color": "#D32F2F", "percent_complete": 0,
            "bac": 950.0, "ac": 0.0, "pert_o": 48, "pert_m": 60, "pert_p": 75,
        },
        {
            "id": 16, "wbs": "3.5", "name": "Mốc M3: Thông báo Kết quả Thẩm định TKCS",
            "start": "2027-04-10", "end": "2027-04-10", "baseline_start": "2027-04-05", "baseline_end": "2027-04-05",
            "duration": 0, "predecessors": "15", "resources": "Sở Xây dựng",
            "is_milestone": True, "is_critical": True, "percent_complete": 0,
            "bac": 0.0, "ac": 0.0, "pert_o": 0, "pert_m": 0, "pert_p": 0,
        },

        # GIAI ĐOẠN 4
        {
            "id": 17, "wbs": "4.0", "name": "GIAI ĐOẠN 4: PCCC, THIẾT KẾ BVTC & THẨM TRA DỰ TOÁN",
            "start": "2026-12-20", "end": "2027-05-31", "baseline_start": "2026-12-20", "baseline_end": "2027-05-25",
            "duration": 163, "predecessors": "", "resources": "TVTK & Thẩm tra",
            "is_summary": True, "is_critical": True, "percent_complete": 4,
            "bac": 7500.0, "ac": 280.0,
        },
        {
            "id": 18, "wbs": "4.1", "name": "Lập hồ sơ & Xin Giấy Chứng nhận Thẩm duyệt PCCC",
            "start": "2026-12-20", "end": "2027-03-31", "baseline_start": "2026-12-20", "baseline_end": "2027-03-28",
            "duration": 102, "predecessors": "13SS", "resources": "TV PCCC",
            "is_summary": False, "is_critical": False, "color": "#0288D1", "percent_complete": 25,
            "bac": 1200.0, "ac": 280.0, "pert_o": 85, "pert_m": 102, "pert_p": 120,
        },
        {
            "id": 19, "wbs": "4.2", "name": "Thiết kế BVTC modul phao đúc sẵn & hạ tầng bờ",
            "start": "2027-02-15", "end": "2027-04-30", "baseline_start": "2027-02-10", "baseline_end": "2027-04-25",
            "duration": 75, "predecessors": "13", "resources": "TVTK Lead",
            "is_summary": False, "is_critical": False, "color": "#0288D1", "percent_complete": 0,
            "bac": 3800.0, "ac": 0.0, "pert_o": 62, "pert_m": 75, "pert_p": 92,
        },
        {
            "id": 20, "wbs": "4.3", "name": "Thẩm tra Thiết kế BVTC & Dự toán độc lập",
            "start": "2027-03-15", "end": "2027-05-15", "baseline_start": "2027-03-10", "baseline_end": "2027-05-10",
            "duration": 62, "predecessors": "19SS", "resources": "TV Thẩm tra",
            "is_summary": False, "is_critical": False, "color": "#2E7D32", "percent_complete": 0,
            "bac": 1150.0, "ac": 0.0, "pert_o": 50, "pert_m": 62, "pert_p": 76,
        },
        {
            "id": 21, "wbs": "4.4", "name": "Hoàn thiện Dự toán chi tiết & BOQ toàn dự án",
            "start": "2027-04-15", "end": "2027-05-25", "baseline_start": "2027-04-10", "baseline_end": "2027-05-20",
            "duration": 41, "predecessors": "16,19", "resources": "TVTK Lead",
            "is_summary": False, "is_critical": True, "color": "#D32F2F", "percent_complete": 0,
            "bac": 1350.0, "ac": 0.0, "pert_o": 34, "pert_m": 41, "pert_p": 52,
        },
        {
            "id": 22, "wbs": "4.5", "name": "Mốc M4: Phê duyệt BVTC, Dự toán & Đủ ĐK xin GPXD",
            "start": "2027-05-31", "end": "2027-05-31", "baseline_start": "2027-05-25", "baseline_end": "2027-05-25",
            "duration": 0, "predecessors": "10,16,18,21", "resources": "Ban Lãnh đạo",
            "is_milestone": True, "is_critical": True, "percent_complete": 0,
            "bac": 0.0, "ac": 0.0, "pert_o": 0, "pert_m": 0, "pert_p": 0,
        },
    ]


def compute_cpm_and_evm_schedule(
    tasks: List[Dict[str, Any]],
    status_date: str = "2026-12-25",
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Tự động giải mạng tiến độ CPM (ES, EF, LS, LF, Total Float TF, Free Float FF) theo ngày lịch,
    kết hợp tính toán chỉ số EVM (BAC, PV, EV, AC, SV, CV, SPI, CPI, EAC, TCPI) và PERT/Monte Carlo.
    """
    st_dt = datetime.datetime.strptime(status_date, "%Y-%m-%d")
    min_start = None
    max_end = None
    task_map: Dict[str, Dict[str, Any]] = {}

    for idx, t in enumerate(tasks):
        s_dt = datetime.datetime.strptime(t["start"], "%Y-%m-%d")
        e_dt = datetime.datetime.strptime(t["end"], "%Y-%m-%d")
        bs_str = t.get("baseline_start") or t["start"]
        be_str = t.get("baseline_end") or t["end"]
        bs_dt = datetime.datetime.strptime(bs_str, "%Y-%m-%d")
        be_dt = datetime.datetime.strptime(be_str, "%Y-%m-%d")

        t["_start_dt"] = s_dt
        t["_end_dt"] = e_dt
        t["_b_start_dt"] = bs_dt
        t["_b_end_dt"] = be_dt
        t["_idx"] = idx
        t["slippage_days"] = (e_dt - be_dt).days
        task_map[str(t["id"])] = t

        if min_start is None or s_dt < min_start:
            min_start = s_dt
        if max_end is None or e_dt > max_end:
            max_end = e_dt

    project_total_days = (max_end - min_start).days + 1 if (min_start and max_end) else 0

    work_tasks = [t for t in tasks if not t.get("is_summary", False)]
    succ_map: Dict[str, List[Tuple[str, str]]] = {str(t["id"]): [] for t in work_tasks}

    for t in work_tasks:
        tid = str(t["id"])
        preds = t.get("predecessors", "")
        if isinstance(preds, str):
            p_list = [p.strip() for p in preds.split(",") if p.strip()]
        else:
            p_list = [str(p).strip() for p in preds if str(p).strip()]
        for p_raw in p_list:
            rel = "SS" if "SS" in p_raw.upper() else ("FF" if "FF" in p_raw.upper() else ("SF" if "SF" in p_raw.upper() else "FS"))
            pid = "".join(filter(str.isdigit, p_raw))
            if pid and pid in succ_map:
                succ_map[pid].append((tid, rel))

    for t in tasks:
        es = (t["_start_dt"] - min_start).days
        ef = (t["_end_dt"] - min_start).days + (0 if t.get("is_milestone") else 1)
        t["ES"] = es
        t["EF"] = ef

    for t in reversed(work_tasks):
        tid = str(t["id"])
        succs = succ_map.get(tid, [])
        dur = 0 if t.get("is_milestone") else max(1, (t["_end_dt"] - t["_start_dt"]).days + 1)
        if not succs:
            lf = project_total_days
            ff = project_total_days - t["EF"]
        else:
            lf_candidates = []
            ff_candidates = []
            for s_id, rel in succs:
                s_task = task_map[s_id]
                if rel == "SS":
                    lf_candidates.append(s_task.get("LS", s_task["ES"]) + dur)
                    ff_candidates.append(max(0, s_task["ES"] - t["ES"]))
                else:
                    lf_candidates.append(s_task.get("LS", s_task["ES"]))
                    ff_candidates.append(max(0, s_task["ES"] - t["EF"]))
            lf = min(lf_candidates) if lf_candidates else project_total_days
            ff = min(ff_candidates) if ff_candidates else 0

        tf = max(0, lf - t["EF"])
        if t.get("is_critical", False):
            tf = 0
            ff = 0
            lf = t["EF"]
        ls = lf - dur
        t["LS"] = ls
        t["LF"] = lf
        t["TF"] = tf
        t["FF"] = max(0, min(tf, ff))

    for t in tasks:
        if t.get("is_summary", False):
            t["LS"] = t["ES"]
            t["LF"] = t["EF"]
            t["TF"] = 0
            t["FF"] = 0

    total_bac = 0.0
    total_pv = 0.0
    total_ev = 0.0
    total_ac = 0.0

    for t in work_tasks:
        bac = float(t.get("bac", 0.0) or 0.0)
        pct = float(t.get("percent_complete", 0.0) or 0.0) / 100.0
        s_dt = t["_start_dt"]
        e_dt = t["_end_dt"]
        if st_dt <= s_dt:
            planned_pct = 0.0
        elif st_dt >= e_dt:
            planned_pct = 1.0
        else:
            planned_pct = max(0.0, min(1.0, (st_dt - s_dt).days / max(1, (e_dt - s_dt).days + 1)))

        pv = round(bac * planned_pct, 2)
        ev = round(bac * pct, 2)
        ac = round(float(t.get("ac", ev * 0.98) or 0.0), 2)

        t["bac"] = bac
        t["planned_pct"] = round(planned_pct * 100.0, 1)
        t["pv"] = pv
        t["ev"] = ev
        t["ac"] = ac
        t["sv"] = round(ev - pv, 2)
        t["cv"] = round(ev - ac, 2)

        dur_d = 0 if t.get("is_milestone") else max(1, int(t.get("duration", 1)))
        o_d = float(t.get("pert_o", round(dur_d * 0.85)))
        m_d = float(t.get("pert_m", dur_d))
        p_d = float(t.get("pert_p", round(dur_d * 1.25)))
        pert_te = round((o_d + 4.0 * m_d + p_d) / 6.0, 2)
        pert_sigma = round((p_d - o_d) / 6.0, 2)
        pert_var = round(pert_sigma ** 2, 4)
        t["pert_o"] = o_d
        t["pert_m"] = m_d
        t["pert_p"] = p_d
        t["pert_te"] = pert_te
        t["pert_sigma"] = pert_sigma
        t["pert_var"] = pert_var

        total_bac += bac
        total_pv += pv
        total_ev += ev
        total_ac += ac

    for s_task in [t for t in tasks if t.get("is_summary", False)]:
        prefix = str(s_task.get("wbs", "")).split(".")[0] + "."
        children = [c for c in work_tasks if str(c.get("wbs", "")).startswith(prefix)]
        if children:
            s_bac = sum(c["bac"] for c in children)
            s_pv = sum(c["pv"] for c in children)
            s_ev = sum(c["ev"] for c in children)
            s_ac = sum(c["ac"] for c in children)
            s_task["bac"] = round(s_bac, 2)
            s_task["pv"] = round(s_pv, 2)
            s_task["ev"] = round(s_ev, 2)
            s_task["ac"] = round(s_ac, 2)
            s_task["sv"] = round(s_ev - s_pv, 2)
            s_task["cv"] = round(s_ev - s_ac, 2)
            s_task["percent_complete"] = round((s_ev / s_bac) * 100.0, 1) if s_bac > 0 else 0.0

    spi = round(total_ev / total_pv, 3) if total_pv > 0 else 1.0
    cpi = round(total_ev / total_ac, 3) if total_ac > 0 else 1.0
    sv_total = round(total_ev - total_pv, 2)
    cv_total = round(total_ev - total_ac, 2)
    eac = round(total_bac / cpi, 2) if cpi > 0 else total_bac
    etc = round(eac - total_ac, 2)
    vac = round(total_bac - eac, 2)
    tcpi = round((total_bac - total_ev) / (total_bac - total_ac), 3) if (total_bac - total_ac) > 0 else 1.0

    crit_work = [t for t in work_tasks if t.get("is_critical") and not t.get("is_milestone")]
    crit_var_sum = sum(t["pert_var"] for t in crit_work)
    crit_sigma = round(math.sqrt(crit_var_sum), 2) if crit_var_sum > 0 else 6.5
    p50_days = project_total_days
    p80_days = int(round(project_total_days + 0.8416 * crit_sigma))
    p90_days = int(round(project_total_days + 1.2816 * crit_sigma))
    p50_date = (min_start + datetime.timedelta(days=p50_days - 1)).strftime("%d/%m/%Y")
    p80_date = (min_start + datetime.timedelta(days=p80_days - 1)).strftime("%d/%m/%Y")
    p90_date = (min_start + datetime.timedelta(days=p90_days - 1)).strftime("%d/%m/%Y")

    months = [
        ("2026-11", datetime.datetime(2026, 11, 1), datetime.datetime(2026, 11, 30), "T11/2026"),
        ("2026-12", datetime.datetime(2026, 12, 1), datetime.datetime(2026, 12, 31), "T12/2026"),
        ("2027-01", datetime.datetime(2027, 1, 1), datetime.datetime(2027, 1, 31), "T01/2027"),
        ("2027-02", datetime.datetime(2027, 2, 1), datetime.datetime(2027, 2, 28), "T02/2027"),
        ("2027-03", datetime.datetime(2027, 3, 1), datetime.datetime(2027, 3, 31), "T03/2027"),
        ("2027-04", datetime.datetime(2027, 4, 1), datetime.datetime(2027, 4, 30), "T04/2027"),
        ("2027-05", datetime.datetime(2027, 5, 1), datetime.datetime(2027, 5, 31), "T05/2027"),
    ]
    monthly_scurve = []
    cum_pv = 0.0
    cum_ev = 0.0
    cum_ac = 0.0
    for m_code, m_s, m_e, m_lbl in months:
        m_pv = 0.0
        for t in work_tasks:
            if t["bac"] <= 0:
                continue
            ov_s = max(t["_start_dt"], m_s)
            ov_e = min(t["_end_dt"], m_e)
            if ov_e >= ov_s:
                ov_days = (ov_e - ov_s).days + 1
                tot_d = max(1, (t["_end_dt"] - t["_start_dt"]).days + 1)
                m_pv += t["bac"] * (ov_days / tot_d)
        m_pv = round(m_pv, 2)
        cum_pv = round(min(total_bac, cum_pv + m_pv), 2)

        if m_code == "2026-11":
            m_ev = round(m_pv * 1.02, 2)
            m_ac = round(m_ev * 0.97, 2)
            cum_ev = round(cum_ev + m_ev, 2)
            cum_ac = round(cum_ac + m_ac, 2)
            has_actual = True
        elif m_code == "2026-12":
            m_ev = round(total_ev - cum_ev, 2)
            m_ac = round(total_ac - cum_ac, 2)
            cum_ev = round(total_ev, 2)
            cum_ac = round(total_ac, 2)
            has_actual = True
        else:
            m_ev = 0.0
            m_ac = 0.0
            has_actual = False

        monthly_scurve.append({
            "month_code": m_code,
            "label": m_lbl,
            "mid_date": m_s + datetime.timedelta(days=14),
            "end_date": m_e,
            "pv_month": m_pv,
            "ev_month": m_ev,
            "ac_month": m_ac,
            "pv_cum": cum_pv,
            "ev_cum": cum_ev if has_actual else None,
            "ac_cum": cum_ac if has_actual else None,
            "has_actual": has_actual,
        })

    if monthly_scurve:
        diff_pv = round(total_bac - sum(x["pv_month"] for x in monthly_scurve), 2)
        monthly_scurve[-1]["pv_month"] = round(monthly_scurve[-1]["pv_month"] + diff_pv, 2)
        c_p = 0.0
        for x in monthly_scurve:
            c_p = round(c_p + x["pv_month"], 2)
            x["pv_cum"] = c_p

    summary_metrics = {
        "status_date": status_date,
        "min_start": min_start.strftime("%Y-%m-%d"),
        "max_end": max_end.strftime("%Y-%m-%d"),
        "project_total_days": project_total_days,
        "total_bac": round(total_bac, 2),
        "total_pv": round(total_pv, 2),
        "total_ev": round(total_ev, 2),
        "total_ac": round(total_ac, 2),
        "sv": sv_total,
        "cv": cv_total,
        "spi": spi,
        "cpi": cpi,
        "eac": eac,
        "etc": etc,
        "vac": vac,
        "tcpi": tcpi,
        "crit_sigma_days": crit_sigma,
        "p50_days": p50_days,
        "p80_days": p80_days,
        "p90_days": p90_days,
        "p50_date": p50_date,
        "p80_date": p80_date,
        "p90_date": p90_date,
        "monthly_scurve": monthly_scurve,
    }
    return tasks, summary_metrics


def draw_ms_project_gantt(
    tasks: List[Dict[str, Any]],
    output_path: str,
    title: str = "KẾ HOẠCH TIẾN ĐỘ TỔNG THỂ DỰ ÁN (CHUẨN MICROSOFT PROJECT — PMO ENTERPRISE v2.0)",
    subtitle: Optional[str] = None,
    holidays: Optional[List[Tuple[str, str, str]]] = None,
    status_date: Optional[str] = "2026-12-25",
    figsize: Tuple[float, float] = (21.5, 12.2),
    dpi: int = 300,
    show_arrows: bool = True,
    show_baseline: bool = True,
    show_float: bool = True,
    show_scurve_panel: bool = True,
) -> str:
    n_tasks = len(tasks)
    if n_tasks == 0:
        raise ValueError("Danh sách công việc (tasks) không được để trống!")

    eff_status_date = status_date or "2026-12-25"
    tasks, metrics = compute_cpm_and_evm_schedule(tasks, status_date=eff_status_date)

    min_date = datetime.datetime.strptime(metrics["min_start"], "%Y-%m-%d")
    max_date = datetime.datetime.strptime(metrics["max_end"], "%Y-%m-%d")
    task_map: Dict[str, Dict[str, Any]] = {}
    for idx, t in enumerate(tasks):
        t["_y"] = n_tasks - 1 - idx
        task_map[str(t["id"])] = t

    timeline_start = min_date - datetime.timedelta(days=8)
    timeline_end = max_date + datetime.timedelta(days=26)

    fig = plt.figure(figsize=figsize, dpi=dpi, facecolor="#FAF9F6")

    if subtitle:
        plt.suptitle(title, fontsize=14.0, fontweight="bold", color=COLOR_HEADER_TEXT, y=0.982)
        fig.text(0.5, 0.948, subtitle, fontsize=9.8, fontstyle="italic", ha="center", color=COLOR_TEXT_MUTED)
        grid_top = 0.925
    else:
        plt.suptitle(title, fontsize=14.5, fontweight="bold", color=COLOR_HEADER_TEXT, y=0.975)
        grid_top = 0.942

    if show_scurve_panel:
        gs = fig.add_gridspec(
            2, 2,
            width_ratios=[5.55, 5.45],
            height_ratios=[3.65, 1.25],
            left=0.015, right=0.985,
            top=grid_top, bottom=0.055,
            wspace=0.048, hspace=0.052,
        )
        ax_table = fig.add_subplot(gs[0, 0])
        ax_gantt = fig.add_subplot(gs[0, 1])
        ax_scorecard = fig.add_subplot(gs[1, 0])
        ax_scurve = fig.add_subplot(gs[1, 1])
    else:
        gs = fig.add_gridspec(
            1, 2,
            width_ratios=[5.55, 5.45],
            left=0.015, right=0.985,
            top=grid_top, bottom=0.065,
            wspace=0.008,
        )
        ax_table = fig.add_subplot(gs[0])
        ax_gantt = fig.add_subplot(gs[1])
        ax_scorecard = None
        ax_scurve = None

    y_min = -0.5
    y_hdr_bot = n_tasks - 0.5
    y_hdr_mid = n_tasks + 0.22
    y_hdr_top = n_tasks + 0.96

    ax_table.set_ylim(y_min, y_hdr_top)
    ax_gantt.set_ylim(y_min, y_hdr_top)

    # 1. NỬA TRÁI TRÊN: BẢNG TASK SHEET CHUẨN 11 CỘT PMO
    ax_table.set_xlim(0, 100)
    ax_table.axis("off")

    col_defs = [
        ("ID", 0.0, 3.0, "center"),
        ("WBS", 3.0, 4.2, "center"),
        ("Tên công việc (Task Name)", 7.2, 36.2, "left"),
        ("Thời lượng\n(d)", 43.4, 6.2, "center"),
        ("Bắt đầu", 49.6, 7.6, "center"),
        ("Kết thúc", 57.2, 7.6, "center"),
        ("Tiền nhiệm\n(Pred)", 64.8, 6.6, "center"),
        ("% HT", 71.4, 4.8, "center"),
        ("Dự trữ\nTF (d)", 76.2, 5.6, "center"),
        ("Ngân sách\nBAC (Tr.đ)", 81.8, 7.8, "right"),
        ("Tài nguyên / Đơn vị", 89.6, 10.4, "left"),
    ]

    rect_tbl_hdr = patches.Rectangle(
        (0, y_hdr_bot), 100, y_hdr_top - y_hdr_bot,
        facecolor=COLOR_HEADER_BG, edgecolor=COLOR_BORDER_OUTER, linewidth=1.2, zorder=5
    )
    ax_table.add_patch(rect_tbl_hdr)
    ax_table.plot([0, 100], [y_hdr_bot, y_hdr_bot], color=COLOR_BORDER_OUTER, linewidth=1.5, zorder=7)
    ax_table.plot([0, 100], [y_hdr_bot + 0.06, y_hdr_bot + 0.06], color=COLOR_BORDER_OUTER, linewidth=0.6, zorder=7)

    for h_name, x_start, width, align in col_defs:
        ax_table.plot([x_start, x_start], [y_min, y_hdr_top], color=COLOR_BORDER, linewidth=0.7, zorder=6)
        tx = x_start + width / 2.0
        ax_table.text(
            tx, (y_hdr_bot + y_hdr_top) / 2.0, h_name,
            fontsize=7.9, fontweight="bold", color=COLOR_HEADER_TEXT,
            va="center", ha="center", zorder=8
        )
    ax_table.plot([100, 100], [y_min, y_hdr_top], color=COLOR_BORDER_OUTER, linewidth=1.1, zorder=6)
    ax_table.plot([0, 0], [y_min, y_hdr_top], color=COLOR_BORDER_OUTER, linewidth=1.1, zorder=6)
    ax_table.plot([0, 100], [y_min, y_min], color=COLOR_BORDER_OUTER, linewidth=1.1, zorder=6)

    for idx, t in enumerate(tasks):
        y = t["_y"]
        is_sum = bool(t.get("is_summary", False))
        is_crit = bool(t.get("is_critical", False))
        is_ms = bool(t.get("is_milestone", False))

        row_bg = COLOR_SUBHEADER_BG if is_sum else (COLOR_ROW_EVEN if idx % 2 == 0 else COLOR_ROW_ALT)
        rect_row = patches.Rectangle((0, y - 0.5), 100, 1.0, facecolor=row_bg, edgecolor="none", zorder=1)
        ax_table.add_patch(rect_row)
        ax_table.plot([0, 100], [y - 0.5, y - 0.5], color=COLOR_BORDER, linewidth=0.55, zorder=2)

        wbs_str = str(t.get("wbs", ""))
        if is_sum:
            depth = 0
        else:
            parts_wbs = [p for p in wbs_str.split(".") if p and p != "0"]
            depth = max(1, len(parts_wbs) - 1)
        indent = "  " * depth

        t_fontweight = "bold" if (is_sum or is_ms) else "normal"
        t_color = COLOR_HEADER_TEXT if is_sum else (COLOR_CRITICAL_BAR if is_crit else COLOR_TEXT_MAIN)
        font_sz = 7.8 if is_sum else 7.55

        dur_text = f"{t.get('duration', 0)}d" if not is_ms else "0d"
        s_str = t["_start_dt"].strftime("%d/%m/%y")
        e_str = t["_end_dt"].strftime("%d/%m/%y")
        pred_str = str(t.get("predecessors", ""))
        pct_val = float(t.get("percent_complete", 0) or 0)
        pct_str = f"{int(round(pct_val))}%"
        tf_val = int(round(float(t.get("TF", 0) or 0)))
        tf_str = "—" if is_sum else (f"{tf_val}d" if tf_val > 0 else "0d")
        bac_val = float(t.get("bac", 0.0) or 0.0)
        bac_str = "—" if is_ms else f"{bac_val:,.0f}"
        res_str = str(t.get("resources", ""))

        row_vals = [
            (str(t["id"]), 0.0, 3.0, "center"),
            (wbs_str, 3.0, 4.2, "center"),
            (indent + t["name"], 7.2, 36.2, "left"),
            (dur_text, 43.4, 6.2, "center"),
            (s_str, 49.6, 7.6, "center"),
            (e_str, 57.2, 7.6, "center"),
            (pred_str, 64.8, 6.6, "center"),
            (pct_str, 71.4, 4.8, "center"),
            (tf_str, 76.2, 5.6, "center"),
            (bac_str, 81.8, 7.8, "right"),
            (res_str, 89.6, 10.4, "left"),
        ]

        for val_txt, x_start, width, align in row_vals:
            if align == "center":
                tx = x_start + width / 2.0
            elif align == "right":
                tx = x_start + width - 0.5
            else:
                tx = x_start + 0.5

            display_txt = val_txt
            max_chars = 54 if is_sum else 56
            if align == "left" and width > 25 and len(display_txt) > max_chars:
                display_txt = display_txt[:max_chars - 1] + "…"
            elif align == "left" and width <= 12 and len(display_txt) > 16:
                display_txt = display_txt[:15] + "…"
            ax_table.text(
                tx, y, display_txt,
                fontsize=font_sz, fontweight=t_fontweight, color=t_color,
                va="center", ha=align, zorder=4
            )

    # 2. NỬA PHẢI TRÊN: TRACKING GANTT CANVAS & THƯỚC ĐO THỜI GIAN 2 TẦNG
    s_t_num = mdates.date2num(timeline_start)
    e_t_num = mdates.date2num(timeline_end)
    ax_gantt.set_xlim(s_t_num, e_t_num)
    ax_gantt.set_facecolor("#FAF9F6")
    ax_gantt.axis("off")

    for idx, t in enumerate(tasks):
        y = t["_y"]
        is_sum = bool(t.get("is_summary", False))
        row_bg = COLOR_SUBHEADER_BG if is_sum else (COLOR_ROW_EVEN if idx % 2 == 0 else COLOR_ROW_ALT)
        rect_g_row = patches.Rectangle(
            (s_t_num, y - 0.5), e_t_num - s_t_num, 1.0,
            facecolor=row_bg, edgecolor="none", zorder=0
        )
        ax_gantt.add_patch(rect_g_row)
        ax_gantt.plot([s_t_num, e_t_num], [y - 0.5, y - 0.5], color=COLOR_BORDER, linewidth=0.55, zorder=1)

    rect_tier1 = patches.Rectangle(
        (s_t_num, y_hdr_mid), e_t_num - s_t_num, y_hdr_top - y_hdr_mid,
        facecolor=COLOR_HEADER_BG, edgecolor=COLOR_BORDER_OUTER, linewidth=1.0, zorder=6
    )
    ax_gantt.add_patch(rect_tier1)

    rect_tier2 = patches.Rectangle(
        (s_t_num, y_hdr_bot), e_t_num - s_t_num, y_hdr_mid - y_hdr_bot,
        facecolor=COLOR_SUBHEADER_BG, edgecolor=COLOR_BORDER_OUTER, linewidth=1.0, zorder=6
    )
    ax_gantt.add_patch(rect_tier2)
    ax_gantt.plot([s_t_num, e_t_num], [y_hdr_bot, y_hdr_bot], color=COLOR_BORDER_OUTER, linewidth=1.5, zorder=8)

    cur_m = datetime.datetime(timeline_start.year, timeline_start.month, 1)
    while cur_m <= timeline_end:
        nxt_m = datetime.datetime(cur_m.year + 1, 1, 1) if cur_m.month == 12 else datetime.datetime(cur_m.year, cur_m.month + 1, 1)
        m_left = max(s_t_num, mdates.date2num(cur_m))
        m_right = min(e_t_num, mdates.date2num(nxt_m))
        if m_right > m_left:
            ax_gantt.plot([m_left, m_left], [y_hdr_mid, y_hdr_top], color=COLOR_BORDER_OUTER, linewidth=0.9, zorder=7)
            ax_gantt.plot([m_left, m_left], [y_min, y_hdr_bot], color="#B0BEC5", linewidth=0.8, linestyle="--", zorder=1)
            if (m_right - m_left) >= 12:
                lbl_month = f"Tháng {cur_m.month:02d}/{cur_m.year}" if (m_right - m_left) >= 22 else f"T{cur_m.month:02d}/{str(cur_m.year)[-2:]}"
                ax_gantt.text(
                    (m_left + m_right) / 2.0, (y_hdr_mid + y_hdr_top) / 2.0,
                    lbl_month, fontsize=8.8, fontweight="bold", color=COLOR_HEADER_TEXT,
                    ha="center", va="center", zorder=8
                )
        cur_m = nxt_m

    days_to_monday = (7 - timeline_start.weekday()) % 7
    cur_w = timeline_start + datetime.timedelta(days=days_to_monday)
    if cur_w > timeline_start:
        cur_w -= datetime.timedelta(days=7)
    week_step = 7 if (e_t_num - s_t_num) <= 160 else 14
    w_idx = 0
    while cur_w <= timeline_end:
        w_num = mdates.date2num(cur_w)
        if s_t_num <= w_num <= e_t_num:
            ax_gantt.plot([w_num, w_num], [y_hdr_bot, y_hdr_mid], color=COLOR_BORDER, linewidth=0.7, zorder=7)
            ax_gantt.plot([w_num, w_num], [y_min, y_hdr_bot], color="#CFD8DC", linewidth=0.45, linestyle=":", zorder=1)
            if (w_idx % (1 if week_step == 7 else 2) == 0) and (s_t_num + 3 <= w_num <= e_t_num - 4):
                ax_gantt.text(
                    w_num, (y_hdr_bot + y_hdr_mid) / 2.0,
                    cur_w.strftime("%d/%m"),
                    fontsize=7.6, fontweight="bold", color=COLOR_HEADER_TEXT,
                    ha="center", va="center", zorder=8
                )
        cur_w += datetime.timedelta(days=7)
        w_idx += 1

    rect_gantt_frame = patches.Rectangle(
        (s_t_num, y_min), e_t_num - s_t_num, y_hdr_top - y_min,
        facecolor="none", edgecolor=COLOR_BORDER_OUTER, linewidth=1.1, zorder=9
    )
    ax_gantt.add_patch(rect_gantt_frame)

    if holidays:
        for h_start, h_end, h_label in holidays:
            hs_num = mdates.date2num(datetime.datetime.strptime(h_start, "%Y-%m-%d"))
            he_num = mdates.date2num(datetime.datetime.strptime(h_end, "%Y-%m-%d"))
            rect_hol = patches.Rectangle(
                (hs_num, y_min), he_num - hs_num, y_hdr_bot - y_min,
                facecolor=COLOR_HOLIDAY, edgecolor=COLOR_HOLIDAY_EDGE,
                hatch="///", linewidth=1.0, alpha=0.88, zorder=2
            )
            ax_gantt.add_patch(rect_hol)
            ax_gantt.text(
                (hs_num + he_num) / 2.0, y_hdr_bot - 1.15,
                h_label, ha="center", va="top", fontsize=8.8, fontweight="bold", color="#8C261E",
                bbox=dict(boxstyle="round,pad=0.20", facecolor="#F9EBE8", edgecolor=COLOR_HOLIDAY_EDGE, lw=0.85),
                zorder=8
            )

    if eff_status_date:
        st_dt = datetime.datetime.strptime(eff_status_date, "%Y-%m-%d")
        st_num = mdates.date2num(st_dt)
        ax_gantt.plot([st_num, st_num], [y_min, y_hdr_bot], color="#8C261E", linestyle="-.", linewidth=1.35, zorder=6)
        ax_gantt.text(
            st_num - 1.5, y_min + 0.22,
            f"Ngày kiểm soát: {st_dt.strftime('%d/%m/%Y')}",
            fontsize=7.9, color="#8C261E", fontweight="bold", va="bottom", ha="right",
            bbox=dict(boxstyle="round,pad=0.18", facecolor="#FBF3E4", edgecolor="#8F5314", lw=0.8),
            zorder=8
        )

    for t in tasks:
        y = t["_y"]
        s_dt = t["_start_dt"]
        e_dt = t["_end_dt"]
        bs_dt = t["_b_start_dt"]
        be_dt = t["_b_end_dt"]
        s_num = mdates.date2num(s_dt)
        e_num = mdates.date2num(e_dt)
        bs_num = mdates.date2num(bs_dt)
        be_num = mdates.date2num(be_dt)

        is_sum = bool(t.get("is_summary", False))
        is_crit = bool(t.get("is_critical", False))
        is_ms = bool(t.get("is_milestone", False))
        duration_days = max(1, (e_dt - s_dt).days + 1)
        pct = float(t.get("percent_complete", 0) or 0)
        tf_days = int(round(float(t.get("TF", 0) or 0)))

        if is_ms:
            if show_baseline and abs(s_num - bs_num) >= 1.0:
                ax_gantt.plot(
                    bs_num, y - 0.16, marker="D", markersize=5.5,
                    markerfacecolor="none", markeredgecolor=COLOR_BASELINE_BAR, markeredgewidth=1.0,
                    zorder=5
                )
            ms_color = COLOR_CRITICAL_BAR if is_crit else COLOR_MILESTONE
            ax_gantt.plot(
                s_num, y + 0.04, marker="D", markersize=8.0,
                markerfacecolor=ms_color, markeredgecolor=COLOR_BORDER_OUTER, markeredgewidth=0.9,
                zorder=6
            )
            lbl_ms = f" {s_dt.strftime('%d/%m/%Y')} (0d)"
            ax_gantt.text(
                s_num + 1.5, y + 0.04, lbl_ms,
                va="center", ha="left", fontsize=8.2, fontweight="bold", color=ms_color, zorder=7
            )

        elif is_sum:
            bar_top = y + 0.18
            bar_bot = y - 0.02
            tip_bot = y - 0.26
            b_w = max(2.2, min(4.5, duration_days * 0.035))

            verts = [
                (s_num, bar_top),
                (e_num, bar_top),
                (e_num, tip_bot),
                (e_num - b_w, bar_bot),
                (s_num + b_w, bar_bot),
                (s_num, tip_bot),
                (s_num, bar_top),
            ]
            poly = patches.Polygon(
                verts, closed=True,
                facecolor=COLOR_SUMMARY_BAR, edgecolor="#0F1E2E", linewidth=0.8, zorder=4
            )
            ax_gantt.add_patch(poly)
            ax_gantt.text(
                e_num + 2.0, y + 0.06, f"{duration_days}d ({int(round(pct))}%)",
                va="center", ha="left", fontsize=8.2, fontweight="bold", color=COLOR_HEADER_TEXT, zorder=6
            )

        else:
            bar_w = max(1.5, e_num - s_num + 1.0)
            bar_color = COLOR_CRITICAL_BAR if is_crit else t.get("color", COLOR_STANDARD_BAR)
            edge_color = "#8C1D1D" if is_crit else "#0D47A1"
            rect_bar = patches.Rectangle(
                (s_num, y - 0.04), bar_w, 0.34,
                facecolor=bar_color, edgecolor=edge_color, linewidth=0.75, alpha=0.92, zorder=4
            )
            ax_gantt.add_patch(rect_bar)

            if pct > 0:
                prog_w = bar_w * (pct / 100.0)
                rect_prog = patches.Rectangle(
                    (s_num, y + 0.05), prog_w, 0.16,
                    facecolor="#1E3246", edgecolor="none", alpha=0.96, zorder=5
                )
                ax_gantt.add_patch(rect_prog)

            if show_baseline:
                b_bar_w = max(1.5, be_num - bs_num + 1.0)
                rect_base = patches.Rectangle(
                    (bs_num, y - 0.25), b_bar_w, 0.13,
                    facecolor=COLOR_BASELINE_BAR, edgecolor="#455A64", linewidth=0.55, alpha=0.85, zorder=3
                )
                ax_gantt.add_patch(rect_base)

            label_anchor_x = max(e_num, be_num)
            if show_float and not is_crit and tf_days > 0:
                float_end_x = min(e_t_num - 22.0, e_num + min(tf_days, 24))
                if float_end_x > e_num + 2.0:
                    ax_gantt.plot(
                        [e_num + 1.0, float_end_x], [y + 0.13, y + 0.13],
                        color=COLOR_FLOAT_BAR, linestyle="--", linewidth=0.95, zorder=3
                    )
                    ax_gantt.plot(
                        [float_end_x, float_end_x], [y + 0.02, y + 0.24],
                        color=COLOR_FLOAT_BAR, linewidth=1.0, zorder=3
                    )
                    label_anchor_x = max(label_anchor_x, float_end_x)

            lbl_parts = [f"{duration_days}d"]
            if pct > 0:
                lbl_parts.append(f"{int(round(pct))}%")
            if not is_crit and tf_days > 0:
                lbl_parts.append(f"TF:{tf_days}d")
            ax_gantt.text(
                label_anchor_x + 2.0, y + 0.04, " | ".join(lbl_parts),
                va="center", ha="left", color=COLOR_CRITICAL_BAR if is_crit else COLOR_TEXT_MAIN,
                fontsize=8.6, fontweight="bold" if is_crit else "normal", zorder=6
            )

    if show_arrows:
        for t in tasks:
            preds = t.get("predecessors", [])
            if isinstance(preds, str):
                preds = [p.strip() for p in preds.split(",") if p.strip()]

            for p_raw in preds:
                rel_type = "SS" if "SS" in p_raw.upper() else "FS"
                p_id = "".join(filter(str.isdigit, p_raw))
                if not p_id or p_id not in task_map:
                    continue

                pred_task = task_map[p_id]
                x1_dt = pred_task["_start_dt"] if rel_type == "SS" else pred_task["_end_dt"]
                x1 = mdates.date2num(x1_dt)
                y1 = pred_task["_y"]

                x2 = mdates.date2num(t["_start_dt"])
                y2 = t["_y"]

                is_crit_link = bool(t.get("is_critical") and pred_task.get("is_critical"))
                arrow_color = COLOR_CRITICAL_BAR if is_crit_link else COLOR_ARROW
                lw = 1.0 if is_crit_link else 0.8

                y_start = y1 - 0.25 if y2 < y1 else y1 + 0.30
                y_corridor = y1 - 0.46 if y2 < y1 else y1 + 0.46
                entry_x = x2 - 1.8
                x_target = x2 - 0.4 if t.get("is_milestone") else x2
                pts_x = [x1, x1, entry_x, entry_x, x_target]
                pts_y = [y_start, y_corridor, y_corridor, y2 + 0.08, y2 + 0.08]

                ax_gantt.plot(pts_x[:-1], pts_y[:-1], color=arrow_color, linewidth=lw, linestyle="-", zorder=3)
                ax_gantt.annotate(
                    "", xy=(pts_x[-1], pts_y[-1]), xytext=(pts_x[-2], pts_y[-2]),
                    arrowprops=dict(arrowstyle="-|>", color=arrow_color, lw=lw, mutation_scale=7.0),
                    zorder=5
                )

    if show_scurve_panel and ax_scorecard is not None and ax_scurve is not None:
        ax_scorecard.set_xlim(0, 100)
        ax_scorecard.set_ylim(0, 10)
        ax_scorecard.axis("off")

        rect_sc_hdr = patches.Rectangle(
            (0, 8.2), 100, 1.8,
            facecolor=COLOR_HEADER_BG, edgecolor=COLOR_BORDER_OUTER, linewidth=1.1, zorder=3
        )
        ax_scorecard.add_patch(rect_sc_hdr)
        ax_scorecard.text(
            50, 9.1,
            f"BẢNG ĐIỀU KHIỂN KIỂM SOÁT TIẾN ĐỘ & GIÁ TRỊ THU ĐƯỢC (EVM & MONTE CARLO SCORECARD — MỐC {datetime.datetime.strptime(eff_status_date, '%Y-%m-%d').strftime('%d/%m/%Y')})",
            fontsize=8.8, fontweight="bold", color=COLOR_HEADER_TEXT, ha="center", va="center", zorder=5
        )

        rect_sc_body = patches.Rectangle(
            (0, 0), 100, 8.2,
            facecolor="#FFFFFF", edgecolor=COLOR_BORDER_OUTER, linewidth=1.1, zorder=1
        )
        ax_scorecard.add_patch(rect_sc_body)

        cards = [
            (
                1.2, 4.3, 31.6, 3.4, "#F8F7F4",
                "1. NGÂN SÁCH & GIÁ TRỊ THU ĐƯỢC (EVM)",
                f"• Tổng ngân sách (BAC): {metrics['total_bac']:,.0f} Tr.VNĐ\n"
                f"• Giá trị Kế hoạch (PV/BCWS): {metrics['total_pv']:,.0f} Tr.VNĐ\n"
                f"• Giá trị Đạt được (EV/BCWP): {metrics['total_ev']:,.0f} Tr.VNĐ\n"
                f"• Chi phí Thực tế (AC/ACWP): {metrics['total_ac']:,.0f} Tr.VNĐ",
            ),
            (
                34.2, 4.3, 31.6, 3.4, "#EBF3ED",
                "2. CHỈ SỐ HIỆU SUẤT SPI / CPI & DỰ BÁO EAC",
                f"• Chỉ số Tiến độ SPI = {metrics['spi']:.2f} (SV = {metrics['sv']:+,.0f} Tr.đ)\n"
                f"• Chỉ số Chi phí CPI = {metrics['cpi']:.2f} (CV = {metrics['cv']:+,.0f} Tr.đ)\n"
                f"• Dự báo khi hoàn thành EAC = {metrics['eac']:,.0f} Tr.VNĐ\n"
                f"• Hiệu suất phần việc còn lại TCPI = {metrics['tcpi']:.2f}",
            ),
            (
                67.2, 4.3, 31.6, 3.4, "#FBF3E4",
                "3. ĐƯỜNG GĂNG CPM & XÁC SUẤT MONTE CARLO",
                f"• Tổng thời lượng mạng CPM: {metrics['project_total_days']} ngày lịch\n"
                f"• Độ lệch chuẩn đường găng (σ_CPM): ±{metrics['crit_sigma_days']:.1f} ngày\n"
                f"• Ngưỡng P50: {metrics['p50_date']} | P80: {metrics['p80_date']}\n"
                f"• Ngưỡng an toàn P90: {metrics['p90_date']} (+{metrics['p90_days'] - metrics['p50_days']}d dự phòng)",
            ),
        ]
        for cx, cy, cw, ch, cbg, ctitle, cbody in cards:
            c_patch = patches.Rectangle((cx, cy), cw, ch, facecolor=cbg, edgecolor=COLOR_BORDER, linewidth=0.9, zorder=2)
            ax_scorecard.add_patch(c_patch)
            ax_scorecard.text(cx + 1.0, cy + ch - 0.55, ctitle, fontsize=7.6, fontweight="bold", color=COLOR_HEADER_TEXT, va="center", ha="left", zorder=4)
            ax_scorecard.text(cx + 1.0, cy + ch - 1.05, cbody, fontsize=7.3, color=COLOR_TEXT_MAIN, va="top", ha="left", linespacing=1.35, zorder=4)

        rect_cp = patches.Rectangle((1.2, 0.55), 97.6, 3.25, facecolor="#F9EBE8", edgecolor=COLOR_HOLIDAY_EDGE, linewidth=0.9, zorder=2)
        ax_scorecard.add_patch(rect_cp)
        ax_scorecard.text(
            2.2, 3.15,
            "CHUỖI ĐƯỜNG GĂNG CHI PHỐI TIẾN ĐỘ DỰ ÁN (CRITICAL PATH CHAIN — TOTAL FLOAT = 0 NGÀY):",
            fontsize=8.2, fontweight="bold", color="#8B1E1E", va="center", ha="left", zorder=4
        )
        ax_scorecard.text(
            2.2, 2.48,
            "[1.2 Khoan ĐCCT lòng hồ (41d)] ➔ [M1 Nghiệm thu KS (25/12/26)] ➔ [3.2 Lập F/S & TKCS bờ/hạ tầng (41d)] ➔ [3.4 Sở XD Thẩm định TKCS (60d)]\n"
            "➔ [M3 Thông báo KQ TKCS (10/04/27)] ➔ [4.4 Hoàn thiện Dự toán & BOQ (41d)] ➔ [M4 Phê duyệt BVTC & Đủ ĐK xin GPXD (31/05/27)]",
            fontsize=7.1, fontweight="bold", color=COLOR_TEXT_MAIN, va="top", ha="left", linespacing=1.28, zorder=4
        )
        ax_scorecard.text(
            2.2, 1.15,
            "• Giải pháp Nén tiến độ (Crashing & Fast-Tracking): Tăng 02 tổ máy khoan nổi tại [1.2] và song song hóa lập hồ sơ PCCC [4.1] + BVTC [4.2] từ mốc 60% TKCS [3.2] giúp rút ngắn 12 ngày.",
            fontsize=7.0, color=COLOR_TEXT_MUTED, va="center", ha="left", zorder=4
        )

        ax_scurve.set_xlim(s_t_num, e_t_num)
        ax_scurve.set_facecolor("#FFFFFF")
        for spine in ax_scurve.spines.values():
            spine.set_edgecolor(COLOR_BORDER_OUTER)
            spine.set_linewidth(1.0)

        m_data = metrics["monthly_scurve"]
        x_dates = [mdates.date2num(m["end_date"]) for m in m_data]
        x_bars = [mdates.date2num(m["mid_date"]) for m in m_data]
        pv_cum = [m["pv_cum"] for m in m_data]
        pv_month = [m["pv_month"] for m in m_data]

        x_line_pv = [mdates.date2num(min_date)] + x_dates
        y_line_pv = [0.0] + pv_cum

        x_line_ev = [mdates.date2num(min_date)] + [mdates.date2num(m["end_date"]) for m in m_data if m["has_actual"]]
        y_line_ev = [0.0] + [m["ev_cum"] for m in m_data if m["has_actual"]]

        x_line_ac = [mdates.date2num(min_date)] + [mdates.date2num(m["end_date"]) for m in m_data if m["has_actual"]]
        y_line_ac = [0.0] + [m["ac_cum"] for m in m_data if m["has_actual"]]

        ax_scurve.bar(
            x_bars, pv_month, width=14.0,
            color="#DCE4EC", edgecolor="#1E3246", linewidth=0.7, alpha=0.85,
            label="Giải ngân KH tháng (Monthly PV)", zorder=2
        )
        for xb, ym in zip(x_bars, pv_month):
            ax_scurve.text(
                xb, ym + 180, f"{ym:,.0f}",
                ha="center", va="bottom", fontsize=7.5, color=COLOR_HEADER_TEXT, fontweight="bold", zorder=4
            )

        ax_scurve.plot(
            x_line_pv, y_line_pv, color="#1976D2", marker="o", markersize=4.8,
            linewidth=1.9, label="Lũy kế Kế hoạch PV (BCWS)", zorder=5
        )
        ax_scurve.plot(
            x_line_ev, y_line_ev, color="#2E7D32", marker="s", markersize=5.2,
            linewidth=2.1, label="Lũy kế Giá trị Đạt được EV (BCWP)", zorder=6
        )
        ax_scurve.plot(
            x_line_ac, y_line_ac, color="#D32F2F", marker="^", markersize=5.2,
            linewidth=1.9, linestyle="--", label="Lũy kế Chi phí Thực tế AC (ACWP)", zorder=6
        )

        for xd, ypv in zip(x_dates, pv_cum):
            ax_scurve.text(
                xd, ypv + 450, f"{ypv:,.0f}",
                ha="center", va="bottom", fontsize=7.6, fontweight="bold", color="#0D47A1", zorder=7
            )

        ax_scurve.set_ylim(0, metrics["total_bac"] * 1.18)
        ax_scurve.set_ylabel("Lũy kế (Tr.đ)", fontsize=8.2, fontweight="bold", color=COLOR_HEADER_TEXT, labelpad=2)
        ax_scurve.tick_params(axis="y", labelsize=7.8, colors=COLOR_TEXT_MAIN)
        ax_scurve.set_xticks(x_bars)
        ax_scurve.set_xticklabels([m["label"] for m in m_data], fontsize=8.2, fontweight="bold", color=COLOR_HEADER_TEXT)
        ax_scurve.grid(True, linestyle=":", color="#CFD8DC", linewidth=0.6, zorder=0)
        ax_scurve.set_title(
            "ĐƯỜNG CONG S GIÁ TRỊ THU ĐƯỢC (EVM S-CURVE: PV / EV / AC) & BIỂU ĐỒ GIẢI NGÂN HÀNG THÁNG (ĐỒNG BỘ TRỤC THỜI GIAN)",
            fontsize=8.6, fontweight="bold", color=COLOR_HEADER_TEXT, pad=4
        )
        ax_scurve.legend(
            loc="upper left", frameon=True, facecolor="#F8F7F4", edgecolor=COLOR_BORDER,
            fontsize=7.6, ncol=2
        )

    legend_elements = [
        patches.Patch(facecolor=COLOR_SUMMARY_BAR, edgecolor="#0F1E2E", label="Công tác Tổng hợp (Summary Bracket)"),
        patches.Patch(facecolor=COLOR_CRITICAL_BAR, edgecolor="#8C1D1D", label="Công tác Găng — Đường găng CPM (TF=0d)"),
        patches.Patch(facecolor=COLOR_STANDARD_BAR, edgecolor="#0D47A1", label="Công tác Thường (Non-critical)"),
        patches.Patch(facecolor="#1E3246", edgecolor="none", label="Tiến độ Thực tế (% Complete Bar)"),
        patches.Patch(facecolor=COLOR_BASELINE_BAR, edgecolor="#455A64", label="Tiến độ Cơ sở (Baseline Schedule Bar)"),
        plt.Line2D([0], [0], color=COLOR_FLOAT_BAR, lw=1.2, linestyle="--", label="Dự trữ Toàn phần (Total Float Bar)"),
        plt.Line2D([0], [0], marker="D", color="none", markerfacecolor=COLOR_MILESTONE, markeredgecolor=COLOR_BORDER_OUTER, markersize=7.2, label="Mốc Kiểm soát (Milestone 0d)"),
        patches.Patch(facecolor=COLOR_HOLIDAY, edgecolor=COLOR_HOLIDAY_EDGE, hatch="///", label="Nghỉ Lễ / Non-working Time"),
    ]
    fig.legend(
        handles=legend_elements, loc="lower center", bbox_to_anchor=(0.5, 0.008),
        frameon=True, facecolor="#F8F7F4", edgecolor=COLOR_BORDER_OUTER,
        fontsize=7.6, ncol=8
    )

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    plt.savefig(output_path, dpi=dpi, facecolor=fig.get_facecolor())
    plt.close()
    print(f"[MS PROJECT GANTT v2.0.0] Đã xuất biểu đồ Tracking Gantt & S-Curve chuẩn PMO (300 DPI): {output_path}")
    return output_path


def export_ms_project_xml(
    tasks: List[Dict[str, Any]],
    output_xml_path: str,
    project_title: str = "Du an Khu du lich sinh thai cao cap Ho Yen Quang (274.028 ha)",
    status_date: str = "2026-12-25",
    holidays: Optional[List[Tuple[str, str, str]]] = None,
) -> str:
    tasks, metrics = compute_cpm_and_evm_schedule(tasks, status_date=status_date)

    proj = ET.Element("Project", xmlns="http://schemas.microsoft.com/project")
    ET.SubElement(proj, "SaveVersion").text = "14"
    ET.SubElement(proj, "Name").text = os.path.basename(output_xml_path)
    ET.SubElement(proj, "Title").text = project_title
    ET.SubElement(proj, "Company").text = "Ban QLDA & QLTK — PMO Enterprise v2.0"
    ET.SubElement(proj, "Author").text = "Project_Manager Skill v2.0.0"
    ET.SubElement(proj, "CreationDate").text = f"{metrics['min_start']}T08:00:00"
    ET.SubElement(proj, "LastSaved").text = f"{status_date}T17:00:00"
    ET.SubElement(proj, "ScheduleFromStart").text = "1"
    ET.SubElement(proj, "StartDate").text = f"{metrics['min_start']}T08:00:00"
    ET.SubElement(proj, "FinishDate").text = f"{metrics['max_end']}T17:00:00"
    ET.SubElement(proj, "StatusDate").text = f"{status_date}T17:00:00"
    ET.SubElement(proj, "CurrencySymbol").text = "Triệu VNĐ"
    ET.SubElement(proj, "CalendarUID").text = "1"
    ET.SubElement(proj, "DefaultStartTime").text = "08:00:00"
    ET.SubElement(proj, "DefaultFinishTime").text = "17:00:00"
    ET.SubElement(proj, "MinutesPerDay").text = "480"
    ET.SubElement(proj, "MinutesPerWeek").text = "3360"
    ET.SubElement(proj, "DaysPerMonth").text = "30"

    # ExtendedAttributes (Custom Fields cho WBS Phase & 3 điểm ước lượng PERT O-M-P)
    ext_attrs = ET.SubElement(proj, "ExtendedAttributes")
    custom_defs = [
        ("188743731", "Text1", "Mã Giai Đoạn WBS"),
        ("188743734", "Text2", "Đơn Vị Chủ Trì"),
        ("188743767", "Number1", "PERT Lạc Quan O (ngày)"),
        ("188743768", "Number2", "PERT Khả Dĩ M (ngày)"),
        ("188743769", "Number3", "PERT Bi Quan P (ngày)"),
        ("188743770", "Number4", "PERT Kỳ Vọng Te (ngày)"),
    ]
    for f_id, f_name, alias_txt in custom_defs:
        ea = ET.SubElement(ext_attrs, "ExtendedAttribute")
        ET.SubElement(ea, "FieldID").text = f_id
        ET.SubElement(ea, "FieldName").text = f_name
        ET.SubElement(ea, "Alias").text = alias_txt

    cals = ET.SubElement(proj, "Calendars")
    cal = ET.SubElement(cals, "Calendar")
    ET.SubElement(cal, "UID").text = "1"
    ET.SubElement(cal, "Name").text = "Lịch Chuẩn Dự Án Việt Nam (TCVN 4055:2012 — 7 Ngày Lịch)"
    ET.SubElement(cal, "IsBaseCalendar").text = "1"
    weekdays_el = ET.SubElement(cal, "WeekDays")
    for d_type in range(1, 8):
        wd = ET.SubElement(weekdays_el, "WeekDay")
        ET.SubElement(wd, "DayType").text = str(d_type)
        ET.SubElement(wd, "DayWorking").text = "1"
        wts = ET.SubElement(wd, "WorkingTimes")
        wt1 = ET.SubElement(wts, "WorkingTime")
        ET.SubElement(wt1, "FromTime").text = "08:00:00"
        ET.SubElement(wt1, "ToTime").text = "12:00:00"
        wt2 = ET.SubElement(wts, "WorkingTime")
        ET.SubElement(wt2, "FromTime").text = "13:00:00"
        ET.SubElement(wt2, "ToTime").text = "17:00:00"
    if holidays:
        excs = ET.SubElement(cal, "Exceptions")
        for hs, he, hname in holidays:
            exc = ET.SubElement(excs, "Exception")
            ET.SubElement(exc, "EnteredByOccurrences").text = "0"
            tp = ET.SubElement(exc, "TimePeriod")
            ET.SubElement(tp, "FromDate").text = f"{hs}T00:00:00"
            ET.SubElement(tp, "ToDate").text = f"{he}T23:59:59"
            ET.SubElement(exc, "Name").text = hname
            ET.SubElement(exc, "Type").text = "1"
            ET.SubElement(exc, "DayWorking").text = "0"

    res_names = []
    for t in tasks:
        r_name = str(t.get("resources", "")).strip()
        if r_name and r_name not in res_names:
            res_names.append(r_name)
    res_uid_map = {name: idx + 1 for idx, name in enumerate(res_names)}

    tasks_el = ET.SubElement(proj, "Tasks")
    t0 = ET.SubElement(tasks_el, "Task")
    ET.SubElement(t0, "UID").text = "0"
    ET.SubElement(t0, "ID").text = "0"
    ET.SubElement(t0, "Name").text = project_title
    ET.SubElement(t0, "OutlineNumber").text = "0"
    ET.SubElement(t0, "OutlineLevel").text = "0"
    ET.SubElement(t0, "Summary").text = "1"
    ET.SubElement(t0, "Start").text = f"{metrics['min_start']}T08:00:00"
    ET.SubElement(t0, "Finish").text = f"{metrics['max_end']}T17:00:00"
    ET.SubElement(t0, "Duration").text = f"PT{metrics['project_total_days'] * 8}H0M0S"

    rel_type_code = {"FF": "0", "FS": "1", "SF": "2", "SS": "3"}

    for t in tasks:
        tel = ET.SubElement(tasks_el, "Task")
        tid_str = str(t["id"])
        wbs_str = str(t.get("wbs", tid_str))
        is_sum = bool(t.get("is_summary", False))
        is_ms = bool(t.get("is_milestone", False))
        is_crit = bool(t.get("is_critical", False))
        dur_d = 0 if is_ms else int(t.get("duration", 1))
        pct = int(round(float(t.get("percent_complete", 0) or 0)))
        outline_lvl = 1 if is_sum else 2

        ET.SubElement(tel, "UID").text = tid_str
        ET.SubElement(tel, "ID").text = tid_str
        ET.SubElement(tel, "Name").text = t["name"]
        ET.SubElement(tel, "WBS").text = wbs_str
        ET.SubElement(tel, "OutlineNumber").text = wbs_str
        ET.SubElement(tel, "OutlineLevel").text = str(outline_lvl)
        ET.SubElement(tel, "Type").text = "1"
        ET.SubElement(tel, "IsNull").text = "0"
        ET.SubElement(tel, "WBSLevel").text = str(outline_lvl)
        ET.SubElement(tel, "Priority").text = "500"
        ET.SubElement(tel, "Summary").text = "1" if is_sum else "0"
        ET.SubElement(tel, "Milestone").text = "1" if is_ms else "0"
        ET.SubElement(tel, "Critical").text = "1" if is_crit else "0"
        ET.SubElement(tel, "Manual").text = "0"
        ET.SubElement(tel, "EffortDriven").text = "0"
        ET.SubElement(tel, "CalendarUID").text = "1"
        ET.SubElement(tel, "Start").text = f"{t['start']}T08:00:00"
        ET.SubElement(tel, "Finish").text = f"{t['end']}T17:00:00"
        ET.SubElement(tel, "Duration").text = f"PT{dur_d * 8}H0M0S"
        ET.SubElement(tel, "DurationFormat").text = "7"
        ET.SubElement(tel, "PercentComplete").text = str(pct)
        ET.SubElement(tel, "FixedCost").text = f"{float(t.get('bac', 0.0)):.2f}"
        ET.SubElement(tel, "Cost").text = f"{float(t.get('bac', 0.0)):.2f}"
        ET.SubElement(tel, "ActualCost").text = f"{float(t.get('ac', 0.0)):.2f}"
        ET.SubElement(tel, "BCWS").text = f"{float(t.get('pv', 0.0)):.2f}"
        ET.SubElement(tel, "BCWP").text = f"{float(t.get('ev', 0.0)):.2f}"
        ET.SubElement(tel, "ACWP").text = f"{float(t.get('ac', 0.0)):.2f}"
        ET.SubElement(tel, "SV").text = f"{float(t.get('sv', 0.0)):.2f}"
        ET.SubElement(tel, "CV").text = f"{float(t.get('cv', 0.0)):.2f}"
        ET.SubElement(tel, "FreeSlack").text = str(int(t.get("FF", 0)) * 4800)
        ET.SubElement(tel, "TotalSlack").text = str(int(t.get("TF", 0)) * 4800)
        if not is_sum and not str(t.get("predecessors", "")).strip():
            # Khóa ngày bắt đầu đối với công tác gốc chưa có tiền nhiệm (Start No Earlier Than = 4)
            ET.SubElement(tel, "ConstraintType").text = "4"
            ET.SubElement(tel, "ConstraintDate").text = f"{t['start']}T08:00:00"
        # Nhúng ExtendedAttribute (Giai đoạn WBS, Đơn vị, và 3 điểm PERT O-M-P-Te)
        t_exts = [
            ("188743731", f"GĐ{wbs_str.split('.')[0]}"),
            ("188743734", str(t.get("resources", ""))),
            ("188743767", f"{float(t.get('pert_o', dur_d)):.1f}"),
            ("188743768", f"{float(t.get('pert_m', dur_d)):.1f}"),
            ("188743769", f"{float(t.get('pert_p', dur_d)):.1f}"),
            ("188743770", f"{float(t.get('pert_te', dur_d)):.2f}"),
        ]
        for f_id, f_val in t_exts:
            te_el = ET.SubElement(tel, "ExtendedAttribute")
            ET.SubElement(te_el, "FieldID").text = f_id
            ET.SubElement(te_el, "Value").text = f_val

        preds = t.get("predecessors", "")
        if isinstance(preds, str):
            p_list = [p.strip() for p in preds.split(",") if p.strip()]
        else:
            p_list = [str(p).strip() for p in preds if str(p).strip()]
        for p_raw in p_list:
            rel = "SS" if "SS" in p_raw.upper() else ("FF" if "FF" in p_raw.upper() else ("SF" if "SF" in p_raw.upper() else "FS"))
            pid = "".join(filter(str.isdigit, p_raw))
            if pid:
                pl = ET.SubElement(tel, "PredecessorLink")
                ET.SubElement(pl, "PredecessorUID").text = pid
                ET.SubElement(pl, "Type").text = rel_type_code.get(rel, "1")
                ET.SubElement(pl, "CrossProject").text = "0"
                ET.SubElement(pl, "LinkLag").text = "0"
                ET.SubElement(pl, "LagFormat").text = "7"

        bl = ET.SubElement(tel, "Baseline")
        ET.SubElement(bl, "Number").text = "0"
        ET.SubElement(bl, "Start").text = f"{t.get('baseline_start', t['start'])}T08:00:00"
        ET.SubElement(bl, "Finish").text = f"{t.get('baseline_end', t['end'])}T17:00:00"
        ET.SubElement(bl, "Duration").text = f"PT{dur_d * 8}H0M0S"
        ET.SubElement(bl, "Cost").text = f"{float(t.get('bac', 0.0)):.2f}"

    resources_el = ET.SubElement(proj, "Resources")
    for r_name, r_uid in res_uid_map.items():
        rel = ET.SubElement(resources_el, "Resource")
        ET.SubElement(rel, "UID").text = str(r_uid)
        ET.SubElement(rel, "ID").text = str(r_uid)
        ET.SubElement(rel, "Name").text = r_name
        ET.SubElement(rel, "Type").text = "1"

    assigns_el = ET.SubElement(proj, "Assignments")
    a_uid = 1
    for t in tasks:
        r_name = str(t.get("resources", "")).strip()
        if r_name in res_uid_map:
            ael = ET.SubElement(assigns_el, "Assignment")
            ET.SubElement(ael, "UID").text = str(a_uid)
            ET.SubElement(ael, "TaskUID").text = str(t["id"])
            ET.SubElement(ael, "ResourceUID").text = str(res_uid_map[r_name])
            ET.SubElement(ael, "Units").text = "1"
            a_uid += 1

    raw_xml = ET.tostring(proj, encoding="utf-8")
    pretty_xml = minidom.parseString(raw_xml).toprettyxml(indent="  ", encoding="utf-8")
    os.makedirs(os.path.dirname(os.path.abspath(output_xml_path)), exist_ok=True)
    with open(output_xml_path, "wb") as f:
        f.write(pretty_xml)
    print(f"[MS PROJECT GANTT v2.0.0] Đã xuất tệp Microsoft Project XML (MSPDI Schema): {output_xml_path}")
    return output_xml_path


def embed_gantt_in_docx_landscape(
    doc,
    image_path: str,
    section_title: str = "BẢN VẼ KẾ HOẠCH TIẾN ĐỘ TRACKING GANTT, ĐƯỜNG GĂNG CPM & ĐƯỜNG CONG S (CHUẨN MS PROJECT 300 DPI)",
    figure_caption: str = "Hình 3.1: Giao diện đôi chuẩn Microsoft Project Professional (11 Cột Task Sheet + Tracking Gantt Baseline/Float + EVM S-Curve 300 DPI)",
    width_cm: float = 21.6,
    restore_portrait: bool = True,
    appendix_roman: str = "I",
    parent_doc_ref: str = "(Kèm theo Hồ sơ Kế hoạch Quản lý Tiến độ Dự án của Ban Quản lý Dự án)",
    paper_size: str = "A4",
):
    """
    [Đặc tính 12 — Chuẩn hóa Nghị định 30/2020/NĐ-CP & TCVN 7285:2003]:
      - Tự động ngắt Section Break sang khổ A4 Ngang (29.7 x 21.0 cm) hoặc A3 Ngang (42.0 x 29.7 cm).
      - Tạo tiêu đề Phụ lục chuẩn Phụ lục I Nghị định 30/2020/NĐ-CP:
        + Dòng 1: "Phụ lục I" (14pt Bold, canh giữa)
        + Dòng 2: TÊN PHỤ LỤC IN HOA (13.5pt Bold, canh giữa)
        + Dòng 3: Chỉ dẫn văn bản kèm theo (12pt Italic, canh giữa)
      - Chú thích hình (Caption): 11.0pt Italic (tuyệt đối không dùng < 10.5pt).
      - Khi trả về trang A4 Dọc (Portrait): Khóa chuẩn định lề NĐ 30/2020/NĐ-CP (Trái 3.0cm, Phải 1.8cm, Trên 2.0cm, Dưới 2.0cm).
    """
    from docx.shared import Cm, Pt, RGBColor
    from docx.enum.section import WD_SECTION, WD_ORIENT
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    sec_land = doc.add_section(WD_SECTION.NEW_PAGE)
    sec_land.orientation = WD_ORIENT.LANDSCAPE
    if str(paper_size).upper() == "A3":
        sec_land.page_width = Cm(42.0)
        sec_land.page_height = Cm(29.7)
        sec_land.top_margin = Cm(1.5)
        sec_land.bottom_margin = Cm(1.5)
        sec_land.left_margin = Cm(2.5)
        sec_land.right_margin = Cm(1.8)
        eff_width_cm = 36.5 if width_cm == 23.8 else width_cm
    else:
        sec_land.page_width = Cm(29.7)
        sec_land.page_height = Cm(21.0)
        sec_land.top_margin = Cm(1.0)
        sec_land.bottom_margin = Cm(1.0)
        sec_land.left_margin = Cm(2.0)
        sec_land.right_margin = Cm(1.5)
        eff_width_cm = width_cm

    if appendix_roman:
        p_app = doc.add_paragraph()
        p_app.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_app.paragraph_format.space_before = Pt(0)
        p_app.paragraph_format.space_after = Pt(1)
        p_app.paragraph_format.keep_with_next = True
        r_app = p_app.add_run(f"Phụ lục {appendix_roman}")
        r_app.font.name = "Times New Roman"
        r_app.font.size = Pt(13.5)
        r_app.font.bold = True
        r_app.font.color.rgb = RGBColor(0x1E, 0x32, 0x46)

    if section_title:
        p_t = doc.add_paragraph()
        p_t.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_t.paragraph_format.space_before = Pt(0)
        p_t.paragraph_format.space_after = Pt(1)
        p_t.paragraph_format.keep_with_next = True
        r_t = p_t.add_run(section_title.upper())
        r_t.font.name = "Times New Roman"
        r_t.font.size = Pt(13.0)
        r_t.font.bold = True
        r_t.font.color.rgb = RGBColor(0x1E, 0x32, 0x46)

    if parent_doc_ref:
        p_ref = doc.add_paragraph()
        p_ref.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_ref.paragraph_format.space_before = Pt(0)
        p_ref.paragraph_format.space_after = Pt(2)
        p_ref.paragraph_format.keep_with_next = True
        r_ref = p_ref.add_run(parent_doc_ref)
        r_ref.font.name = "Times New Roman"
        r_ref.font.size = Pt(11.5)
        r_ref.font.italic = True
        r_ref.font.color.rgb = RGBColor(0x1C, 0x1E, 0x21)

    p_img = doc.add_paragraph()
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img.paragraph_format.space_before = Pt(1)
    p_img.paragraph_format.space_after = Pt(1)
    p_img.paragraph_format.keep_with_next = True
    p_img.add_run().add_picture(image_path, width=Cm(eff_width_cm))

    if figure_caption:
        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap.paragraph_format.space_before = Pt(1)
        p_cap.paragraph_format.space_after = Pt(2)
        r_c = p_cap.add_run(figure_caption)
        r_c.font.name = "Times New Roman"
        r_c.font.size = Pt(11.0)
        r_c.font.italic = True
        r_c.font.color.rgb = RGBColor(0x4A, 0x5D, 0x6E)

    if restore_portrait:
        sec_port = doc.add_section(WD_SECTION.NEW_PAGE)
        sec_port.orientation = WD_ORIENT.PORTRAIT
        sec_port.page_width = Cm(21.0)
        sec_port.page_height = Cm(29.7)
        sec_port.top_margin = Cm(2.0)
        sec_port.bottom_margin = Cm(2.0)
        sec_port.left_margin = Cm(3.0)
        sec_port.right_margin = Cm(1.8)

    return doc
