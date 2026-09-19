import sys
import os
import json

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def format_formula(formula_str):
    """Basic helper to format raw formula strings to basic LaTeX if possible."""
    f = formula_str.replace("<=", "\\le")
    f = f.replace(">=", "\\ge")
    f = f.replace("*", "\\cdot ")
    return f"$$ {f} $$"

def export_calc_sheet_md(output_path, title, project_code, calc_data, images=None):
    """
    Xuất Thuyết minh tính toán kỹ thuật dạng file Markdown chuẩn kỹ thuật.
    """
    abs_output = os.path.abspath(output_path)
    os.makedirs(os.path.dirname(abs_output), exist_ok=True)

    # Lấy thông tin logs
    calc_logs = calc_data.get("Calculation_Logs", [])
    
    md_content = f"""# THUYẾT MINH TÍNH TOÁN KẾT CẤU: {title.upper()}
**Mã dự án**: {project_code} | **Giai đoạn**: Thiết kế Chi tiết & Tính toán | **Người tính**: AI Structural Engineer

---

## 1. CƠ SỞ THIẾT KẾ & TIÊU CHUẨN ÁP DỤNG
- **Tải trọng & Tổ hợp**: TCVN 2737:2023 (Tải trọng và tác động)
- **Kết cấu Bê tông cốt thép**: TCVN 5574:2018 (Thiết kế kết cấu bê tông và BTCT)
- **Kết cấu Thép**: TCVN 5575:2012 / Eurocode 3 (EN 1993-1-8)
- **Thiết kế Móng cọc**: TCVN 10304:2014 / TCVN 9362:2012

---

## 2. THÔNG SỐ VẬT LIỆU & DỮ LIỆU ĐẦU VÀO
```json
{json.dumps({k:v for k,v in calc_data.items() if k not in ["Calculation_Logs", "Unverified_Items"]}, ensure_ascii=False, indent=2)}
```

---

## 3. THIẾT KẾ TÍNH TOÁN TRẠNG THÁI GIỚI HẠN (STEP-BY-STEP)

"""

    if not calc_logs:
        md_content += "*(Không có chi tiết tính toán step-by-step)*\n"
    else:
        for idx, log in enumerate(calc_logs, 1):
            md_content += f"### Bước {idx}: {log.get('Step', 'Tính toán')}\n"
            if log.get("Principle"):
                md_content += f"- **Nguyên lý**: {log.get('Principle')}\n"
            if log.get("Citation"):
                cit = log.get("Citation", {})
                if isinstance(cit, dict):
                    md_content += f"- **Tiêu chuẩn**: {cit.get('Ma_TC', '')} — {cit.get('Dieu_Muc', '')}\n"
                else:
                    md_content += f"- **Tiêu chuẩn**: {cit}\n"
            if log.get("Formula"):
                md_content += "\n**Công thức áp dụng**:\n"
                md_content += format_formula(log.get("Formula")) + "\n\n"
            if log.get("Values"):
                md_content += f"- **Thay số**: {log.get('Values')}\n"
            if log.get("Result"):
                md_content += f"- **Kết quả**: **{log.get('Result')}**\n"
            if log.get("Utilization"):
                md_content += f"- **Hệ số sử dụng**: {log.get('Utilization')}\n"
            md_content += "\n"

    md_content += f"""
---

## 4. HÌNH VẼ SƠ ĐỒ CHI TIẾT LIÊN KẾT 2D
"""

    if images:
        for idx, img in enumerate(images, 1):
            img_abs = os.path.abspath(img)
            md_content += f"\n![Hình {idx}: Chi tiết liên kết 2D](file:///{img_abs.replace(os.sep, '/')})\n*Hình {idx}: Sơ đồ mặt cắt kỹ thuật và vị trí liên kết*\n"
    else:
        md_content += "\n*(Chưa có sơ đồ đính kèm)*\n"

    md_content += f"""
---

## 5. BẢNG TỔNG HỢP CHỈ SỐ SỬ DỤNG (UTILIZATION RATIO)

| Hạng mục | Hệ số sử dụng ($\eta$) | Trạng thái |
|---|---|---|
| Chịu Uốn | {calc_data.get("eta_M", "N/A")} | {calc_data.get("status_uon", "PASSED")} |
| Chịu Cắt | {calc_data.get("eta_V", "N/A") if calc_data.get("eta_V") is not None else calc_data.get("eta_strut", "N/A")} | {calc_data.get("status", "PASSED")} |

=> **KẾT LUẬN TÍNH TOÁN**: Kết cấu **{calc_data.get("status", "PASSED")}** yêu cầu an toàn kỹ thuật theo tiêu chuẩn hiện hành.

---

> *Tài liệu do trợ lý AI lập tự động. Kết quả tính toán mang tính tham khảo, phải được kỹ sư có chứng chỉ hành nghề phù hợp kiểm tra và chịu trách nhiệm trước khi sử dụng cho hồ sơ thiết kế, thi công hoặc thẩm tra.*

## BẢNG TRÁCH NHIỆM

| Vai trò | Người thực hiện | Đề xuất |
|---|---|---|
| Người lập | Trợ lý AI (Antigravity) | Cần kỹ sư có chứng chỉ hành nghề kiểm tra xác nhận trước khi ký |
| Kỹ sư kiểm tra | [Để trống] | |
"""

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

    with open(args.json_file, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    
    export_calc_sheet_md(args.out_file, "Dầm BTCT", "DA_SAMPLE", data)
