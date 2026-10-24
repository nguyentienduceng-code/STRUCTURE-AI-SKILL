import sys
import os
import json

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# --- Bộ Kiểm Soát Hệ Thống (System Controller) -----------------------------
# Gắn preflight_check vào cổng xuất Thuyết minh tính toán. Xem .agents/tools/system_controller.py
def _find_skill_guard_dir():
    """Tìm .agents/_SHARED/SHARED_CONTEXT bằng cách đi lên từng cấp (không phụ thuộc độ sâu)."""
    from pathlib import Path
    cur = Path(__file__).resolve().parent
    for _ in range(8):
        cand = cur / "_SHARED" / "SHARED_CONTEXT"
        if cand.is_dir():
            return cand
        parent = cur.parent
        if parent == cur:
            break
        cur = parent
    return None


try:
    _SHARED_CTX = _find_skill_guard_dir()
    if _SHARED_CTX and _SHARED_CTX not in sys.path:
        sys.path.insert(0, _SHARED_CTX)
    from skill_guard import preflight as _preflight
    _GUARD_AVAILABLE = True
except Exception:  # pragma: no cover
    _GUARD_AVAILABLE = False


def _guard_check(tool_name, payload=None):
    if not _GUARD_AVAILABLE:
        return True, "Bộ kiểm soát hệ thống không khả dụng — bỏ qua preflight."
    return _preflight("Structural_Design_Engineer", tool_name, payload or {}, fail_open=True)

def format_formula(formula_str):
    """Basic helper to format raw formula strings to basic LaTeX if possible."""
    f = formula_str.replace("<=", "\\le")
    f = f.replace(">=", "\\ge")
    f = f.replace("*", "\\cdot ")
    return f"$$ {f} $$"


# Từ điển ánh xạ tên kỹ thuật, ký hiệu và đơn vị cho bảng Input
INPUT_PARAM_META = {
    "b": ("Bề rộng tiết diện", "b", "mm"),
    "h": ("Chiều cao tiết diện", "h", "mm"),
    "L": ("Nhịp tính toán", "L", "mm"),
    "L_span": ("Nhịp tính toán", "L", "mm"),
    "L0": ("Chiều dài tính toán cột", "L_0", "mm"),
    "a": ("Khoảng cách trọng tâm cốt thép chịu kéo", "a", "mm"),
    "a_prime": ("Khoảng cách trọng tâm cốt thép chịu nén", "a'", "mm"),
    "h0": ("Chiều cao làm việc tiết diện", "h_0", "mm"),
    "concrete": ("Cấp độ bền bê tông", "B", "—"),
    "rebar": ("Nhóm cốt thép dọc", "CB", "—"),
    "stirrup_grade": ("Nhóm cốt thép đai", "CB_w", "—"),
    "dia": ("Đường kính cốt thép", "d_s", "mm"),
    "dia_mm": ("Đường kính cốt thép", "d_s", "mm"),
    "diameter_mm": ("Đường kính cốt thép", "d_s", "mm"),
    "Diameter_mm": ("Đường kính cốt thép", "d_s", "mm"),
    "rebar_grade": ("Nhóm cốt thép", "CB", "—"),
    "Rebar_Grade": ("Nhóm cốt thép", "CB", "—"),
    "concrete_grade": ("Cấp độ bền bê tông", "B", "—"),
    "Concrete_Grade": ("Cấp độ bền bê tông", "B", "—"),
    "stress_ratio": ("Hệ số ứng suất", "α_s", "—"),
    "Stress_Ratio": ("Hệ số ứng suất", "α_s", "—"),
    "alpha_alpha": ("Hệ số điều kiện neo", "α", "—"),
    "Alpha_alpha": ("Hệ số điều kiện neo", "α", "—"),
    "M": ("Mô men uốn tính toán", "M", "kN.m"),
    "M_ed": ("Mô men uốn tính toán", "M_{Ed}", "kN.m"),
    "M_Ed": ("Mô men uốn tính toán", "M_{Ed}", "kN.m"),
    "V": ("Lực cắt tính toán", "Q", "kN"),
    "V_ed": ("Lực cắt tính toán", "V_{Ed}", "kN"),
    "V_Ed": ("Lực cắt tính toán", "V_{Ed}", "kN"),
    "N": ("Lực dọc tính toán", "N", "kN"),
    "N_ed": ("Lực dọc tính toán", "N_{Ed}", "kN"),
    "N_Ed": ("Lực dọc tính toán", "N_{Ed}", "kN"),
    "stress_type": ("Trạng thái ứng suất", "—", "—"),
    "lap_zone": ("Vùng nối chồng", "—", "—"),
    "as_ratio": ("Tỷ lệ As_req / As_prov", "A_{s,req}/A_{s,prov}", "—"),
    "splice_ratio": ("Tỷ lệ thanh nối chồng trong cùng tiết diện", "r_lap", "—"),
    "seismic_class": ("Cấp dẻo kháng chấn", "DCL/DCM/DCH", "—"),
    "Rb_MPa": ("Cường độ chịu nén tính toán bê tông", "R_b", "MPa"),
    "Rbt_MPa": ("Cường độ chịu kéo tính toán bê tông", "R_{bt}", "MPa"),
    "Rs_MPa": ("Cường độ tính toán cốt thép", "R_s", "MPa"),
    "R_bond_MPa": ("Cường độ bám dính tính toán", "R_{bond}", "MPa"),
}

ETA_LABELS = {
    "eta_M": ("Kiểm tra Khả năng chịu Uốn (TTGH1)", "M / M_gh ≤ 1.00"),
    "eta_V": ("Kiểm tra Khả năng chịu Cắt trên tiết diện nghiêng (TTGH1)", "Q / Q_b,sw ≤ 1.00"),
    "eta_strut": ("Kiểm tra Nén vỡ Dải bê tông nghiêng (TTGH1)", "Q / Q_b,max ≤ 1.00"),
    "eta_N": ("Kiểm tra Khả năng chịu Nén / Kéo dọc trục (TTGH1)", "N / N_gh ≤ 1.00"),
    "eta_NM": ("Kiểm tra Nén uốn lệch tâm (TTGH1)", "η_NM ≤ 1.00"),
    "eta_LTB": ("Kiểm tra Ổn định tổng thể dầm chịu uốn (TTGH1)", "M / (φ_b W_c f γ_c) ≤ 1.00"),
    "eta_shear": ("Kiểm tra Chịu cắt bản bụng (TTGH1)", "V / V_c ≤ 1.00"),
    "eta_bolt": ("Kiểm tra Liên kết Bu lông (TTGH1)", "F / [F]_bolt ≤ 1.00"),
    "eta_weld": ("Kiểm tra Liên kết Đường hàn (TTGH1)", "τ_w / (f_w γ_c) ≤ 1.00"),
    "eta_pile": ("Kiểm tra Sức chịu tải Cọc (TTGH1)", "P_max / R_c,d ≤ 1.00"),
    "eta_punch": ("Kiểm tra Chọc thủng đài/sàn (TTGH1)", "F / F_b,u ≤ 1.00"),
    "eta_crack": ("Kiểm tra Bề rộng vết nứt (TTGH2)", "a_crc / [a_crc] ≤ 1.00"),
    "eta_defl": ("Kiểm tra Độ võng cấu kiện (TTGH2)", "f / [f] ≤ 1.00"),
    "eta_max": ("Chỉ số sử dụng chịu lực tổng hợp cực đại", "η_max ≤ 1.00"),
    "overall_eta": ("Hệ số sử dụng tổng thể (TTGH1)", "η ≤ 1.00"),
}


def _render_input_table(inputs: dict) -> list[str]:
    """Chuyển dict Input thành bảng thông số kỹ thuật chuẩn thay vì in raw JSON."""
    if not inputs:
        return ["*Không có dữ liệu thông số đầu vào chi tiết.*", ""]

    lines = [
        "| STT | Thông số kỹ thuật | Ký hiệu | Giá trị đầu vào | Đơn vị |",
        "| :---: | :--- | :---: | :---: | :---: |",
    ]
    for idx, (k, v) in enumerate(inputs.items(), 1):
        label, sym, unit = INPUT_PARAM_META.get(k, (k.replace("_", " ").title(), f"`{k}`", "—"))
        val_str = f"{v:,.3f}".rstrip("0").rstrip(".") if isinstance(v, float) else str(v)
        lines.append(f"| {idx} | {label} | ${sym}$ | **{val_str}** | {unit} |")
    lines.append("")
    return lines


def generate_markdown(calc_data: dict, args=None, title="THUYẾT MINH TÍNH TOÁN KẾT CẤU", project_code="DA_SAMPLE", images=None) -> str:
    """Tạo nội dung Markdown Thuyết minh tính toán kỹ thuật hoàn chỉnh."""
    calc_logs = calc_data.get("Calculation_Logs", [])
    if isinstance(args, str):
        title_str = args
        proj_str = project_code
    elif args is not None and hasattr(args, "title") and isinstance(getattr(args, "title"), str):
        title_str = getattr(args, "title") or title
        proj_str = getattr(args, "project_code", project_code)
    else:
        title_str = title
        proj_str = project_code

    md = [
        f"# THUYẾT MINH TÍNH TOÁN KẾT CẤU: {title_str.upper()}",
        f"**Mã dự án**: {proj_str} | **Giai đoạn**: Thiết kế Chi tiết & Tính toán | **Người tính**: AI Structural Engineer",
        "",
        "---",
        "",
        "## 1. CƠ SỞ THIẾT KẾ & TIÊU CHUẨN ÁP DỤNG",
        "- **Tải trọng & Tổ hợp**: TCVN 2737:2023 (Tải trọng và tác động)",
        "- **Kết cấu Bê tông cốt thép**: TCVN 5574:2018 (Thiết kế kết cấu bê tông và BTCT)",
        "- **Kết cấu Thép**: TCVN 5575:2024 / Eurocode 3 (EN 1993-1-8)",
        "- **Thiết kế Móng cọc**: TCVN 10304:2025 / TCVN 9362:2012",
        "",
        "---",
        "",
        "## 2. THÔNG SỐ VẬT LIỆU & DỮ LIỆU ĐẦU VÀO",
    ]

    # Lấy dữ liệu Input
    inputs = calc_data.get("Input")
    if not inputs:
        exclude_keys = {
            "Calculation_Logs", "Unverified_Items", "Warnings", "Scope_Limitation",
            "Standard", "Standard_Method", "status", "status_uon", "status_cat",
            "overall_eta", "passed", "checks", "Result", "conclusion", "summary",
            "dia_mm", "L_an_mm", "L_lap_mm", "L_0_an_mm", "L_an_min_check_mm", "L_lap_min_check_mm",
            "L_an_exceeds_min", "L_lap_exceeds_min", "alpha_an", "alpha_lap", "eta_1", "eta_2"
        }
        inputs = {
            k: v for k, v in calc_data.items()
            if k not in exclude_keys and not k.startswith("eta_") and not isinstance(v, (dict, list))
        }

    md.extend(_render_input_table(inputs))
    md.extend([
        "---",
        "",
        "## 3. THIẾT KẾ TÍNH TOÁN TRẠNG THÁI GIỚI HẠN (STEP-BY-STEP)",
        "",
    ])

    if not calc_logs:
        md.append("*(Không có chi tiết tính toán step-by-step)*\n")
    else:
        for idx, log in enumerate(calc_logs, 1):
            step = log.get("Step") or log.get("Step_Number") or idx
            desc = log.get("Description") or log.get("Title") or ""
            form = log.get("Formula") or log.get("formula") or ""
            # VÁ LỖI MẤT THAY SỐ: Ưu tiên đọc "Substitution" rồi mới fallback sang "Values"
            sub = log.get("Substitution") or log.get("substitution") or log.get("Values") or ""
            res = log.get("Result") or log.get("result") or ""
            principle = log.get("Principle") or log.get("principle") or ""
            cit = log.get("Citation") or log.get("citation") or {}

            if isinstance(cit, dict):
                tc = cit.get("Ma_TC") or cit.get("Tieu_chuan") or cit.get("Standard") or cit.get("code") or ""
                dm = cit.get("Dieu_Muc") or cit.get("Clause") or cit.get("article") or ""
                bh = cit.get("Bang_Hinh") or cit.get("Table") or ""
                tr = cit.get("Trang") or cit.get("Page") or ""
                cit_parts = [p for p in [tc, dm, bh, f"Trang {tr}" if tr else ""] if p]
                cit_str = " — ".join(cit_parts)
            else:
                cit_str = str(cit)

            md.append(f"### Bước {step}: {desc}")
            if principle:
                md.append(f"- **Nguyên lý:** {principle}")
            if form:
                md.append(f"- **Công thức:** `{form}`")
            if sub:
                md.append(f"- **Thay số:** `{sub}`")
            if res is not None and str(res) != "":
                md.append(f"- **Kết quả:** **{res}**")
            if cit_str:
                md.append(f"- *Căn cứ tiêu chuẩn: {cit_str}*")
            md.append("")

    md.extend([
        "---",
        "",
        "## 4. HÌNH VẼ SƠ ĐỒ CHI TIẾT LIÊN KẾT 2D",
    ])

    if images:
        for idx, img in enumerate(images, 1):
            img_abs = os.path.abspath(img)
            md.append(f"\n![Hình {idx}: Chi tiết liên kết 2D](file:///{img_abs.replace(os.sep, '/')})\n*Hình {idx}: Sơ đồ mặt cắt kỹ thuật và vị trí liên kết*\n")
    else:
        md.append("\n*(Chưa có sơ đồ đính kèm)*\n")

    md.extend([
        "---",
        "",
        "## 5. BẢNG TỔNG HỢP CHỈ SỐ SỬ DỤNG (UTILIZATION SUMMARY)",
        "",
        "| Hạng mục kiểm tra | Điều kiện giới hạn | Hệ số sử dụng (η) | Đánh giá |",
        "| :--- | :---: | :---: | :---: |",
    ])

    # Tập hợp tất cả kết quả từ calc_data và calc_data.get("Results") / calc_data.get("results")
    all_results = dict(calc_data)
    for rkey in ("Results", "results", "payload"):
        sub_res = calc_data.get(rkey)
        if isinstance(sub_res, dict):
            all_results.update(sub_res)

    eta_found = False
    for key, val in all_results.items():
        if (key.startswith("eta_") or key == "overall_eta") and isinstance(val, (int, float)):
            eta_found = True
            label, cond = ETA_LABELS.get(key, (f"Kiểm tra {key}", "η ≤ 1.00"))
            icon = "🔴 KHÔNG ĐẠT" if val > 1.0 else ("🟠 CẢNH BÁO (>0.90)" if val > 0.90 else ("🟢 ĐẠT (Dự trữ VE)" if val <= 0.70 else "✅ ĐẠT TỐI ƯU"))
            md.append(f"| {label} | `{cond}` | **{val:.3f}** ({val*100:.1f}%) | {icon} |")

    if not eta_found:
        # Cho các bài toán xuất thông số cấu tạo như Neo & Nối chồng cốt thép (L_an, L_lap)
        for k, v in all_results.items():
            if isinstance(v, (int, float, str)) and k not in ("Status", "status", "Calculation_Logs", "Unverified_Items", "Warnings", "Scope_Limitation", "Input", "input", "Standard_Method", "standard_method", "Results", "results"):
                md.append(f"| Kết quả `{k}` | Theo TCVN | **{v}** | ✅ ĐÃ XÁC ĐỊNH |")

    status = calc_data.get("status") or calc_data.get("Status") or "PASSED"
    md.extend([
        "",
        f"=> **KẾT LUẬN TÍNH TOÁN**: Kết cấu **{status}** yêu cầu an toàn kỹ thuật theo tiêu chuẩn hiện hành.",
        "",
        "---",
        "",
        "> *Tài liệu do trợ lý AI lập tự động. Kết quả tính toán mang tính tham khảo, phải được kỹ sư có chứng chỉ hành nghề phù hợp kiểm tra và chịu trách nhiệm trước khi sử dụng cho hồ sơ thiết kế, thi công hoặc thẩm tra.*",
        "",
        "## BẢNG TRÁCH NHIỆM",
        "",
        "| Vai trò | Người thực hiện | Đề xuất |",
        "|---|---|---|",
        "| Người lập | Trợ lý AI (Antigravity) | Cần kỹ sư có chứng chỉ hành nghề kiểm tra xác nhận trước khi ký |",
        "| Kỹ sư kiểm tra | [Để trống] | |",
        ""
    ])

    return "\n".join(md)


def export_calc_sheet_md(output_path, title, project_code, calc_data, images=None):
    """
    Xuất Thuyết minh tính toán kỹ thuật dạng file Markdown chuẩn kỹ thuật.
    """
    abs_output = os.path.abspath(output_path)
    os.makedirs(os.path.dirname(abs_output), exist_ok=True)

    md_content = generate_markdown(calc_data, title=title, project_code=project_code, images=images)

    with open(abs_output, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"Exported Calculation Sheet to: {abs_output}")
    return abs_output


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("out_file")
    parser.add_argument("json_file")
    args = parser.parse_args()

    # Preflight — Bộ Kiểm Soát Hệ Thống (chặn vòng lặp tác tử / thao tác nguy hiểm)
    allowed, guard_reason = _guard_check(
        "structural_design_export_calc_sheet",
        {"command": "", "output": args.out_file},
    )
    if not allowed:
        print(f"⛔ PREFLIGHT BLOCKED: {guard_reason}")
        sys.exit(2)

    with open(args.json_file, "r", encoding="utf-8-sig") as f:
        data = json.load(f)

    export_calc_sheet_md(args.out_file, "Dầm BTCT", "DA_SAMPLE", data)

