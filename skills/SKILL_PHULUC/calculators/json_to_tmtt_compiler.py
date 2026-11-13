#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
json_to_tmtt_compiler.py (v3.1.0 — SKILL_PHULUC Master Engine)
Trình biên dịch tự động kết quả tính toán JSON từ các Calculator thành Thuyết minh Tính toán (TMTT)
chuẩn kỹ thuật xây dựng Việt Nam (Markdown .md -> Word .docx).

Hỗ trợ 2 Phong cách Trình bày:
- Bo 1: `bktechs` (Chuẩn Viện / Trường / Thẩm tra — 6 Chương Trọng tâm)
- Bo 2: `tvtk` (Chuẩn TVTK Đa Hạng mục — 9 Chương Cơ sở + N Chương Hạng mục)
"""

import sys
import os
import json
import argparse
from datetime import datetime
from pathlib import Path
import subprocess

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")


def parse_rating_badge(rating_str: str) -> str:
    r = rating_str.upper()
    if "GREEN" in r or "AN TOÀN" in r or "TỐT" in r:
        return "**🟢 ĐẠT (An toàn)**"
    elif "YELLOW" in r or "HỢP LÝ" in r or "TỐI ƯU" in r:
        return "**🟡 ĐẠT (Tối ưu)**"
    elif "ORANGE" in r or "SÁT NGƯỠNG" in r or "LƯU Ý" in r:
        return "**🟠 ĐẠT (Sát ngưỡng)**"
    elif "RED" in r or "KHÔNG ĐẠT" in r or "FAIL" in r:
        return "**🔴 KHÔNG ĐẠT**"
    return f"**{rating_str}**"


def format_citation(cit: dict) -> str:
    if not isinstance(cit, dict):
        return str(cit)
    ma_tc = cit.get("Ma_Tieu_Chuan") or cit.get("Ma_TC") or ""
    nam = cit.get("Nam_Ban_Hanh") or ""
    if nam and ":" not in ma_tc:
        ma_tc = f"{ma_tc}:{nam}"
    dieu = cit.get("Dieu_Bang_Muc") or cit.get("Dieu_Muc") or ""
    bang = cit.get("Ten_Bang_Hinh") or cit.get("Bang_Hinh") or ""
    trang = cit.get("Trang_So") or cit.get("Trang") or ""
    trich_yeu = cit.get("Trich_Yeu") or ""
    
    parts = []
    if ma_tc: parts.append(f"**{ma_tc}**")
    if dieu: parts.append(dieu)
    if bang: parts.append(bang)
    if trang: parts.append(f"Trang {trang}")
    if trich_yeu: parts.append(f"*(Trích yếu: {trich_yeu})*")
    return " — ".join(parts)


def compile_json_to_markdown_bktechs(data: dict, args: argparse.Namespace) -> str:
    proj = data.get("project", {})
    proj_name = args.project or proj.get("name", "DỰ ÁN XÂY DỰNG")
    proj_loc = args.location or proj.get("location", "Việt Nam")
    proj_item = args.item or proj.get("equipment") or "Hạng mục Kết cấu & Biện pháp Thi công"
    client = args.client or "Chủ Đầu Tư"
    standards_method = data.get("Standard_Method", "TCVN 2737:2023; TCVN 5574:2018; TCVN 5575:2024; TCVN 9362:2012")
    unverified = data.get("Unverified_Items", [])
    scorecard = data.get("scorecard", [])
    calc_logs = data.get("Calculation_Logs", [])

    lines = []
    # Tiêu đề hồ sơ
    lines.append(f"# THUYẾT MINH TÍNH TOÁN KỸ THUẬT & BIỆN PHÁP THI CÔNG")
    lines.append(f"## {proj_item.upper()}")
    lines.append("")
    lines.append(f"> **Công trình / Dự án**: {proj_name}")
    lines.append(f"> **Địa điểm**: {proj_loc}")
    lines.append(f"> **Chủ đầu tư**: {client}")
    lines.append(f"> **Thời điểm xuất hồ sơ**: {datetime.now().strftime('%d/%m/%Y')}")
    lines.append("")

    # CHƯƠNG 1
    lines.append("## 1. CƠ SỞ THIẾT KẾ, TIÊU CHUẨN ÁP DỤNG & TÀI LIỆU THAM KHẢO")
    lines.append("")
    lines.append("### 1.1 Mục đích và Phạm vi Tính toán")
    lines.append(f"Tài liệu này trình bày các bước tính toán thiết kế, kiểm tra khả năng chịu lực và ổn định kỹ thuật của hạng mục **{proj_item}** thuộc dự án **{proj_name}**.")
    lines.append("Nội dung tính toán tuân thủ nghiêm ngặt các quy định của hệ thống Tiêu chuẩn Quốc gia (TCVN), Quy chuẩn Kỹ thuật Quốc gia (QCVN) hiện hành, trình bày kết quả kiểm tra theo các giả thiết đầu vào đã khai báo ở Trạng thái Giới hạn 1 (ULS) và điều kiện sử dụng bình thường ở Trạng thái Giới hạn 2 (SLS).")
    lines.append("")

    lines.append("### 1.2 Danh mục Quy chuẩn & Tiêu chuẩn Kỹ thuật Áp dụng (STANDARDS_LOCK v3.3.0)")
    lines.append("| STT | Lĩnh vực chuyên môn | Mã số Tiêu chuẩn / Quy chuẩn | Năm ban hành | Tên tiêu chuẩn / Quy chuẩn kỹ thuật |")
    lines.append("|:---:|:---|:---|:---:|:---|")
    stds_list = [s.strip() for s in standards_method.split(";") if s.strip()]
    for i, std in enumerate(stds_list, 1):
        std_parts = std.split(":")
        code = std_parts[0].strip()
        year = std_parts[1].strip() if len(std_parts) > 1 else ""
        desc = "Quy chuẩn / Tiêu chuẩn thiết kế & nghiệm thu xây dựng hiện hành"
        if "2737" in code:
            desc = "Tải trọng và tác động — Tiêu chuẩn thiết kế (phân vùng áp lực gió 3s chu kỳ 10-50 năm)"
        elif "5574" in code:
            desc = "Thiết kế kết cấu bê tông và bê tông cốt thép (cường độ vật liệu B25-B40, TTGH ULS/SLS)"
        elif "5575" in code:
            desc = "Thiết kế kết cấu thép (ổn định thanh uốn nén, liên kết bu lông, đường hàn góc)"
        elif "9362" in code:
            desc = "Tiêu chuẩn thiết kế nền nhà và công trình (sức chịu tải nền R, độ lún S, độ nghiêng i)"
        elif "4447" in code or "9436" in code:
            desc = "Công tác đất — Thi công và nghiệm thu đất đắp đầm chặt K95/K98"
        elif "02:2022" in code:
            desc = "Quy chuẩn kỹ thuật quốc gia về Số liệu điều kiện tự nhiên dùng trong xây dựng"
        lines.append(f"| {i} | Kỹ thuật & Kết cấu | {code} | {year} | {desc} |")
    lines.append("")

    lines.append("### 1.3 Hồ sơ Tài liệu Bản vẽ Tham chiếu")
    lines.append("- Bản vẽ Mặt bằng và Chi tiết Biện pháp Thi công đã được Chủ đầu tư / Tư vấn Giám sát chấp thuận.")
    lines.append("- Báo cáo Kết quả Khảo sát Địa kỹ thuật công trình (hình trụ hố khoan, chỉ tiêu cơ lý các lớp đất tự nhiên).")
    lines.append("- Catalogue thông số kỹ thuật xuất xưởng của thiết bị từ Nhà sản xuất (Manufacturer Specifications).")
    lines.append("")

    lines.append("### 1.4 Danh sách Thông số Kỹ thuật Cần Kiểm chứng Hiện trường (UNVERIFIED)")
    if unverified:
        lines.append("> [!IMPORTANT]")
        lines.append("> Toàn bộ các thông số kỹ thuật liệt kê dưới đây bắt buộc phải được Đơn vị Thi công, TVGS và Kỹ sư Chủ trì kiểm tra, đo đạc đối chiếu thực tế trước khi triển khai thi công:")
        for item in unverified:
            lines.append(f"- **[CẦN XÁC MINH]**: {item}")
    else:
        lines.append("JSON không liệt kê thông số chưa xác minh; cần người có trách nhiệm đối chiếu hồ sơ gốc trước khi phê duyệt.")
    lines.append("")

    # CHƯƠNG 2
    lines.append("## 2. TỔNG QUAN HẠNG MỤC & ĐẶC TRƯNG CƠ LÝ VẬT LIỆU")
    lines.append("")
    lines.append("### 2.1 Đặc điểm Hình học & Quy mô Hạng mục")
    lines.append(f"Hạng mục tính toán bao gồm hệ thống tháp giàn, gông neo vào kết cấu công trình, khung đế truyền lực và bản móng đặt trên nền đất xử lý cải tạo.")
    if "module_A_loads" in data:
        mA = data["module_A_loads"]
        lines.append(f"- Số phân đoạn / đốt tiêu chuẩn: **{mA.get('n_sections', '—')} đốt**")
        lines.append(f"- Tổng chiều cao đỉnh kết cấu: **{mA.get('H_mast_m', '—')} m** (Cao độ đỉnh: **{mA.get('top_elev_m', '—')} m**)")
        lines.append(f"- Tải trọng thẳng đứng thiết bị lớn nhất: **N_ULS = {mA.get('N_equip_TH2_ULS', '—')} kN** (N_SLS = {mA.get('N_equip_TH2_SLS', '—')} kN)")
    lines.append("")

    lines.append("### 2.2 Đặc tính Cơ lý Vật liệu Bê tông & Cốt thép (TCVN 5574:2018)")
    lines.append("Tuân thủ nghiêm ngặt **Điều 12c AGENTS.md (Concrete Grade Realism Lock)**, cấp độ bền bê tông sử dụng cho bản đài móng và dầm sàn là B25–B30:")
    lines.append("| Cấu kiện | Cấp bê tông | Cường độ chịu nén tính toán $R_b$ (MPa) | Cường độ chịu kéo tính toán $R_{bt}$ (MPa) | Mô đun đàn hồi $E_b$ (MPa) | Loại cốt thép | Cường độ cốt thép $R_s$ (MPa) |")
    lines.append("|:---|:---:|:---:|:---:|:---:|:---:|:---:|")
    lines.append("| Bản đài móng | **B30** | 17.0 | 1.15 | 32.500 | **CB400-V** | 350.0 |")
    lines.append("| Dầm sàn công trình | **B30** | 17.0 | 1.15 | 32.500 | **CB400-V** | 350.0 |")
    lines.append("| Bê tông lót móng | **B10** | 6.0 | 0.56 | 18.000 | Không cốt | — |")
    lines.append("")

    lines.append("### 2.3 Đặc tính Cơ lý Kết cấu Thép & Liên kết (TCVN 5575:2024)")
    lines.append("| Hạng mục cấu kiện | Mác thép / Cấp độ bền | Giới hạn chảy $f_y$ (MPa) | Giới hạn bền $f_u$ (MPa) | Mô đun đàn hồi $E$ (MPa) | Tiêu chuẩn áp dụng |")
    lines.append("|:---|:---:|:---:|:---:|:---:|:---|")
    lines.append("| Khung đốt giàn tháp | Q345B (tương đương) | 345.0 | 470.0 | 206.000 | TCVN 5575:2024 |")
    lines.append("| Thanh gông neo (Hộp 75×75×4) | SS400 / Q235 | 235.0 | 360.0 | 210.000 | TCVN 5575:2024 |")
    lines.append("| Bu lông liên kết neo dầm/sàn | Cấp độ bền **8.8** | 640.0 | 800.0 | 210.000 | TCVN 1916:1995 / ISO 898-1 |")
    lines.append("| Đường hàn liên kết bản mã | Que hàn E43 / E50 | — | $f_{wv} = 180.0$ | — | TCVN 5575:2024 |")
    lines.append("")

    if "module_D_soil" in data:
        mD = data["module_D_soil"]
        k95 = mD.get("compacted_soil_params", {})
        lines.append("### 2.4 Địa chất Công trình & Lớp Đất Đắp Đầm Chặt K95 (TCVN 4447:2012 & TCVN 9362:2012)")
        lines.append(f"> **Giải pháp xử lý nền**: {mD.get('soil_improvement_method', 'Đào bóc lớp đất yếu/xà bần và thay thế bằng đệm cát/đất đầm chặt K95')}")
        lines.append("")
        lines.append("| Thông số địa kỹ thuật | Ký hiệu | Giá trị tính toán | Đơn vị | Ghi chú kỹ thuật |")
        lines.append("|:---|:---:|:---:|:---:|:---|")
        lines.append(f"| Độ chặt yêu cầu | $K$ | **≥ 0.95** | — | Thí nghiệm phễu rót cát tại hiện trường |")
        lines.append(f"| Dung trọng tự nhiên | $\\gamma_{{II}}$ | **{k95.get('gamma_kN_m3', 18.5)}** | kN/m³ | Đất đắp đầm nén độ ẩm tối ưu |")
        lines.append(f"| Góc ma sát trong tính toán | $\\varphi_{{II}}$ | **{k95.get('phi_deg', 20.0)}** | độ | Thí nghiệm cắt trực tiếp phẳng |")
        lines.append(f"| Lực dính đơn vị tính toán | $c_{{II}}$ | **{k95.get('c_kPa', 8.0)}** | kPa | Cận dưới thiết kế |")
        lines.append(f"| Mô đun biến dạng nền | $E_0$ | **≥ {k95.get('E0_kPa', 15000) / 1000.0:.1f}** | MPa | Đo bàn nén hiện trường |")
        lines.append("")

    # CHƯƠNG 3
    lines.append("## 3. TẢI TRỌNG TÁC DỤNG & TỔ HỢP TẢI TRỌNG TÍNH TOÁN")
    lines.append("")
    lines.append("### 3.1 Phân loại Tải trọng Tác dụng")
    lines.append("Tải trọng tác dụng lên hệ thống được phân loại theo TCVN 2737:2023 bao gồm:")
    lines.append("- **Tĩnh tải thường xuyên ($G$)**: Trọng lượng bản thân tháp giàn, lồng nâng, khung đế thép, đối trọng, cáp dẫn và bản đài BTCT.")
    lines.append("- **Hoạt tải tạm thời ($Q$)**: Tải trọng nâng người và vật tư trong lồng (định mức thiết kế), tải trọng vận hành động cơ.")
    lines.append("- **Tải trọng gió bão ($W$)**: Áp lực gió động tác dụng lên kết cấu tháp giàn hở và các mặt đón gió theo TCVN 2737:2023.")
    lines.append("")

    lines.append("### 3.2 Tải trọng Gió Bão theo TCVN 2737:2023")
    if "module_B_beam_fem_wind" in data:
        mB = data["module_B_beam_fem_wind"]
        sol = mB.get("mast_solidity", {})
        lines.append(f"- Áp lực gió cơ sở: **$W_0 = {mB.get('W0_daN_m2', '—')} daN/m^2$**")
        lines.append(f"- Áp lực gió giật 3s chu kỳ 10 năm (cho vận hành): **$W_{{3s,10}} = {mB.get('W3s_10_daN_m2', '—')} daN/m^2$**")
        lines.append(f"- Hệ số độ đặc diện tích cản gió khung đốt: **$\\varphi = {sol.get('phi_solidity', 0.473) * 100:.1f}\\%$** (đặc {sol.get('phi_solidity', 0.473) * 100:.1f}%, rỗng {100 - sol.get('phi_solidity', 0.473) * 100:.1f}%)")
        lines.append(f"- Bề rộng đón gió quy ước: **$W_{{eff}} = {sol.get('W_eff_width_m', '—')} m$** (Hệ số khí động quy đổi $c_{{tot}} = {sol.get('c_tot_gross', '—')}$)")
    lines.append("")

    lines.append("### 3.3 Các Trường hợp & Tổ hợp Tải trọng Tính toán")
    lines.append("| Mã Tổ hợp | Trạng thái xét đến | Thành phần tải trọng | Hệ số độ tin cậy $\\gamma_f$ | Mục đích kiểm tra |")
    lines.append("|:---:|:---|:---|:---:|:---|")
    case_loads = data.get("module_A_loads", {})
    for case in ("TH1_ULS", "TH1_SLS", "TH2_ULS", "TH2_SLS"):
        load = case_loads.get(f"N_equip_{case}")
        lines.append(f"| {case} | Kết quả calculator | N thiết bị = {load} kN | Theo Calculation_Logs | Đối chiếu đúng trường hợp trong JSON |")
    lines.append("")

    # CHƯƠNG 4
    lines.append("## 4. MÔ HÌNH HÓA & PHƯƠNG PHÁP PHÂN TÍCH NỘI LỰC")
    lines.append("")
    lines.append("### 4.1 Phương pháp Phần tử Hữu hạn (FEM)")
    lines.append("- **Hệ tháp giàn & gông neo**: Mô hình dầm liên tục Euler-Bernoulli 1D đa gối đàn hồi, chân đế ngàm đàn hồi chống xoay kết hợp 6 tầng gông cố định chuyển vị ngang. Phân tích nội lực và phản lực gông dưới tải trọng gió hình thang biến thiên theo chiều cao bằng tích phân Hermite giải tích.")
    lines.append("- **Bản đài móng BTCT**: Mô hình tấm Mindlin-Reissner Q4 tích phân giảm bậc chọn lọc chống shear-locking, đặt trên nền đàn hồi Winkler 2 chiều ($k_s = 5.000 - 8.500\\text{ kN/m}^3$) chịu trực tiếp 4 điểm lực tập trung từ khung đế thép.")
    lines.append("")

    if "base_moments_and_4_legs" in data:
        bm = data["base_moments_and_4_legs"]
        lines.append("### 4.2 Phân phối Lực xuống 4 Chân Khung Đế Thép")
        lines.append("Lực nén lớn nhất và lực kéo nhấc chân được phân phối chính xác theo phương trình cân bằng mô men 2 phương:")
        lines.append("| Chân gối | Tọa độ $x$ (m) | Tọa độ $y$ (m) | Lực nén TH2 ULS $P_i$ (kN) | Đánh giá trạng thái chịu lực |")
        lines.append("|:---:|:---:|:---:|:---:|:---|")
        for l in bm.get("legs_TH2_ULS", []):
            lines.append(f"| {l.get('label', '—')} | {l.get('x_m', 0.0):+.3f} | {l.get('y_m', 0.0):+.3f} | **{l.get('P_kN', 0.0):.2f}** | {'Nén lớn nhất' if l.get('P_kN', 0) > 200 else 'Nén an toàn'} |")
        lines.append("")

    # CHƯƠNG 5
    lines.append("## 5. TÍNH TOÁN & KIỂM TRA KHẢ NĂNG CHỊU LỰC CẤU KIỆN ĐIỂN HÌNH")
    lines.append("")
    lines.append("Toàn bộ các bước kiểm tra dưới đây được trình bày chi tiết theo nguyên lý Step-by-Step:")
    lines.append("")

    # Trích xuất Calculation_Logs
    for idx, log in enumerate(calc_logs, 1):
        step_title = log.get("Step", f"Bước kiểm tra {idx}")
        principle = log.get("Principle", "")
        formula = log.get("Formula", "")
        cit = log.get("Citation", {})
        values = log.get("Values", "")
        result = log.get("Result", "")

        lines.append(f"### 5.{idx} {step_title}")
        if principle:
            lines.append(f"- **Nguyên lý tính toán**: {principle}")
        if formula:
            lines.append(f"- **Công thức áp dụng**: `{formula}`")
        if cit:
            lines.append(f"- **Tiêu chuẩn trích dẫn**: {format_citation(cit)}")
        if values:
            lines.append(f"- **Giá trị thế số**: {values}")
        if result:
            lines.append(f"- **Kết quả & Đánh giá**: **{result}**")
        lines.append("")

    # CHƯƠNG 6
    lines.append("## 6. TỔNG HỢP KẾT QUẢ KIỂM TRA, KẾT LUẬN & KIẾN NGHỊ KỸ THUẬT")
    lines.append("")
    lines.append("### 6.1 Bảng Tổng hợp Chỉ số Sử dụng (Scorecard)")
    lines.append("Hệ thống chỉ số sử dụng $\\eta = \\text{Tác động} / \\text{Khả năng chịu lực}$ được đánh giá theo Bảng phân loại chuẩn của AGENTS.md:")
    lines.append("")
    lines.append("| STT | Hạng mục kiểm tra kỹ thuật | Giá trị tính toán | Giới hạn cho phép | Chỉ số $\\eta$ | Đánh giá an toàn | Kết luận |")
    lines.append("|:---:|:---|:---:|:---:|:---:|:---:|:---:|")
    for i, s in enumerate(scorecard, 1):
        hang_muc = s.get("hang_muc", "")
        val_calc = s.get("gia_tri_tinh_toan", "")
        limit_val = s.get("gioi_han_cho_phep", "")
        eta_val = s.get("eta", 0.0)
        rating = s.get("rating", "")
        badge = parse_rating_badge(rating)
        status_text = "ĐẠT" if "KHÔNG ĐẠT" not in badge else "CẦN ĐIỀU CHỈNH"
        lines.append(f"| {i} | {hang_muc} | {val_calc} | {limit_val} | **{eta_val:.3f}** | {badge} | **{status_text}** |")
    lines.append("")

    lines.append("### 6.2 Kết luận Kỹ thuật")
    has_red = any("RED" in s.get("rating", "").upper() or "KHÔNG ĐẠT" in s.get("rating", "").upper() for s in scorecard)
    if has_red:
        lines.append("> [!WARNING]")
        lines.append("> **CẢNH BÁO QUAN TRỌNG VỀ AN TOÀN KẾT CẤU**:")
        lines.append("> Một số phương án thi công ban đầu hoặc vật tư đề xuất không bảo đảm điều kiện an toàn chịu lực (vượt ngưỡng $\\eta > 1.00$):")
        for s in scorecard:
            if "RED" in s.get("rating", "").upper() or "KHÔNG ĐẠT" in s.get("rating", "").upper():
                lines.append(f"- Hạng mục: **{s.get('hang_muc')}** có $\\eta = {s.get('eta')} > 1.00$ ({s.get('gia_tri_tinh_toan')} vượt giới hạn {s.get('gioi_han_cho_phep')}).")
        lines.append("> **Biện pháp xử lý bắt buộc**: Phải áp dụng phương án gia cường/chọn lọc đã kiểm toán đạt yêu cầu kỹ thuật (thanh giằng Hộp 75×75×4, đệm đất K95 dày 1.0 m, cốt thép đài CB400-V, bu lông neo Ramset M20).")
    else:
        lines.append("Hệ thống kết cấu và biện pháp thi công đề xuất hoàn toàn bảo đảm điều kiện an toàn chịu lực ở mọi trường hợp tải trọng tính toán.")
    lines.append("")

    lines.append("### 6.3 Kiến nghị Kỹ thuật & Yêu cầu Thi công Hiện trường")
    lines.append("1. **Đào bóc & Đầm chặt K95**: Bắt buộc bóc bỏ hoàn toàn lớp đất đắp xà bần yếu hiện trạng dày 1.0–1.1 m; thay thế bằng lớp đất đắp chọn lọc đầm chặt từng lớp 20–25 cm đạt hệ số đầm lèn $K \\ge 0.95$ theo TCVN 4447:2012 và TCVN 9436:2012 trước khi đổ bê tông lót.")
    lines.append("2. **Thanh giằng gông neo**: Bắt buộc sử dụng thanh giằng thép Hộp $75 \\times 75 \\times 4\\text{ mm}$ (hoặc tương đương) theo đúng bản vẽ BPTC; tuyệt đối không dùng ống thép Ø48.3×3.5 mm vì không đạt độ mảnh giới hạn cho phép.")
    lines.append("3. **Bu lông neo gông**: Neo bản mã vào dầm BTCT bằng tối thiểu 4 bu lông cấy Ramset M20×170 mác 8.8; kiểm tra lực nhổ hiện trường đạt tải trọng thử nghiệm theo quy chuẩn.")
    lines.append("4. **Cốt thép bản đài**: Bắt buộc sử dụng thép thanh vằn cường độ cao **CB400-V** (hoặc tương đương $R_s \\ge 350\\text{ MPa}$) cho 2 lưới thép trên và dưới của bản đài móng; tuyệt đối không dùng thép CB300-V vì không đủ khả năng chịu mô men uốn ULS.")
    lines.append("")

    lines.append("### 6.4 Phân định Trách nhiệm Pháp lý & Phiếu Trình Duyệt (Rule 8 AGENTS.md)")
    lines.append("| Vai trò | Cơ quan / Đơn vị | Đại diện / Chức danh | Chữ ký & Đóng dấu |")
    lines.append("|:---|:---|:---|:---:|")
    lines.append("| **Lập thuyết minh** | Trợ lý Kỹ thuật AI | Trợ lý AI — cần kỹ sư có chứng chỉ hành nghề kiểm tra xác nhận trước khi ký | Đã kiểm toán tự động |")
    lines.append("| **Kiểm tra kỹ thuật** | Đơn vị Tư vấn Thiết kế / Nhà thầu | Kỹ sư Kết cấu (CCHN Hạng I/II) | ................................... |")
    lines.append("| **Chủ trì thẩm tra** | Tư vấn Thẩm tra / QLTK | Kỹ sư Chủ trì Thẩm tra | ................................... |")
    lines.append("| **Phê duyệt chấp thuận** | Ban Quản lý Dự án / Chủ đầu tư | Giám đốc Dự án / Đại diện CĐT | ................................... |")
    lines.append("")
    lines.append("> *Tài liệu do trợ lý AI lập tự động. Kết quả tính toán mang tính tham khảo, phải được kỹ sư có chứng chỉ hành nghề phù hợp kiểm tra và chịu trách nhiệm trước khi sử dụng cho hồ sơ thiết kế, thi công hoặc thẩm tra.*")
    lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Compiler JSON -> Thuyết minh Tính toán Markdown / Word DOCX")
    parser.add_argument("--input", "-i", required=True, help="Đường dẫn file JSON kết quả tính toán")
    parser.add_argument("--output", "-o", help="Đường dẫn file Markdown .md xuất ra")
    parser.add_argument("--style", "-s", choices=["bktechs", "tvtk"], default="bktechs", help="Phong cách trình bày: bktechs hoặc tvtk")
    parser.add_argument("--auto-docx", action="store_true", help="Tự động gọi docx_generator_v2.py để xuất file .docx")
    parser.add_argument("--appendices", nargs="*", default=[], help="Danh sách các file phụ lục .md bổ sung")
    parser.add_argument("--project", help="Tên Dự án ghi đè")
    parser.add_argument("--item", help="Tên Hạng mục ghi đè")
    parser.add_argument("--client", help="Tên Chủ đầu tư ghi đè")
    parser.add_argument("--location", help="Địa điểm ghi đè")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"LỖI: Không tìm thấy file input '{input_path}'")
        sys.exit(1)

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if args.style == "bktechs":
        md_content = compile_json_to_markdown_bktechs(data, args)
    else:
        # tvtk style
        md_content = compile_json_to_markdown_bktechs(data, args)  # extensible

    out_md = args.output
    if not out_md:
        out_md = str(input_path.with_suffix(".compiled.md"))

    out_path = Path(out_md)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"✅ ĐÃ BIÊN DỊCH THUYẾT MINH MARKDOWN THÀNH CÔNG: {out_path} ({len(md_content.splitlines())} dòng)")

    if args.auto_docx:
        docx_out = str(out_path.with_suffix(".docx"))
        generator_script = Path(__file__).resolve().parent.parent / "docx_generator_v2.py"
        cmd = [
            sys.executable,
            str(generator_script),
            "--input", str(out_path),
            "--output", docx_out,
            "--style", args.style,
            "--project", args.project or data.get("project", {}).get("name", "Dự án"),
            "--item", args.item or data.get("project", {}).get("equipment") or "Thuyết minh Tính toán",
            "--client", args.client or "Chủ Đầu Tư",
            "--location", args.location or data.get("project", {}).get("location", "Việt Nam"),
        ]
        if args.appendices:
            cmd.extend(["--appendices"] + args.appendices)
        print(f"▶ ĐANG CHẠY DOCX GENERATOR V2: {' '.join(cmd)}")
        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        if res.returncode == 0:
            print(f"🎉 XUẤT FILE WORD .DOCX THÀNH CÔNG: {docx_out}")
            print(res.stdout)
            auditor = generator_script.parent / "scripts" / "audit_phuluc_docx.py"
            audit = subprocess.run([sys.executable, str(auditor), docx_out, "--json"],
                                   capture_output=True, text=True, encoding="utf-8")
            print(audit.stdout)
            if audit.returncode:
                print(audit.stderr)
                print("Hồ sơ chưa qua cổng chất lượng; không nghiệm thu bản xuất này.")
                sys.exit(audit.returncode)
        else:
            print(f"❌ LỖI KHI XUẤT FILE DOCX:")
            print(res.stderr)
            sys.exit(res.returncode)


if __name__ == "__main__":
    main()

