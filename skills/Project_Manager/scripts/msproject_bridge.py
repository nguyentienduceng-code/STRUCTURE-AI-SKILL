# -*- coding: utf-8 -*-
"""
msproject_bridge.py — Cầu nối Điều phối Hợp nhất Tiến độ Microsoft Project (v2.0.0)
====================================================================================
Tích hợp toàn diện 4 chức năng trong 1 công cụ duy nhất:
  1. [EXPORT]: Xuất danh sách công việc sang file Microsoft Project XML (MSPDI Schema).
  2. [RENDER]: Vẽ biểu đồ tiến độ chuẩn MS Project 300 DPI Split-View (ms_project_gantt.py).
  3. [EMBED]: Nhúng biểu đồ vào trang A4 xoay ngang (Landscape) trong văn bản Word (.docx).
  4. [IMPORT]: Đọc ngược file XML từ Microsoft Project vào hệ thống AI để phân tích trễ hạn.
"""

import os
import sys
import argparse
import json

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Import các engine nội bộ
try:
    from msproject_xml_engine import export_to_msproject_xml, import_from_msproject_xml, convert_xml_to_mpp
    from ms_project_gantt import draw_ms_project_gantt, embed_gantt_in_docx_landscape, get_ho_yen_quang_tasks
except ImportError:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(script_dir)
    from msproject_xml_engine import export_to_msproject_xml, import_from_msproject_xml, convert_xml_to_mpp
    from ms_project_gantt import draw_ms_project_gantt, embed_gantt_in_docx_landscape, get_ho_yen_quang_tasks


def run_pipeline(
    tasks,
    project_name="DỰ ÁN XÂY DỰNG",
    company_name="TẬP ĐOÀN C.T GROUP",
    start_date="2026-11-10",
    finish_date="2027-05-31",
    xml_out=None,
    mpp_out=None,
    png_out=None,
    docx_out=None,
    holidays=None
):
    print("====================================================================")
    print(f"   BẮT ĐẦU PIPELINE TIẾN ĐỘ MICROSOFT PROJECT: {project_name}")
    print("====================================================================")

    # 1. Xuất file Microsoft Project XML
    if xml_out:
        print(f"\n[Bước 1/4] Đang xuất file Microsoft Project XML -> {xml_out}")
        export_to_msproject_xml(
            tasks=tasks,
            output_xml_path=xml_out,
            project_name=project_name,
            company_name=company_name,
            start_date=start_date,
            finish_date=finish_date,
            holidays=holidays
        )

    # 2. Tự động chuyển đổi sang .MPP gốc
    if xml_out and mpp_out:
        print(f"\n[Bước 2/4] Đang chuyển đổi sang file dự án gốc Microsoft Project .mpp -> {mpp_out}")
        convert_xml_to_mpp(xml_out, mpp_out)

    # 3. Vẽ biểu đồ Gantt MS Project 300 DPI
    if png_out:
        print(f"\n[Bước 3/4] Đang kết xuất biểu đồ Gantt Split-View 300 DPI -> {png_out}")
        holiday_tuples = [(h["start"], h["end"], h.get("label", "Nghỉ Lễ")) for h in (holidays or [])]
        draw_ms_project_gantt(
            tasks=tasks,
            output_path=png_out,
            title=f"KẾ HOẠCH TIẾN ĐỘ TỔNG THỂ — {project_name.upper()}",
            subtitle="Chuẩn hóa theo Microsoft Project & Quản trị Đường găng CPM (300 DPI)",
            holidays=holiday_tuples,
            dpi=300
        )

    # 4. Nhúng vào Word nếu có yêu cầu
    if docx_out and png_out and os.path.exists(png_out):
        print(f"\n[Bước 4/4] Đang nhúng biểu đồ vào trang A4 Landscape -> {docx_out}")
        import docx
        doc = docx.Document(docx_out) if os.path.exists(docx_out) else docx.Document()
        embed_gantt_in_docx_landscape(
            doc=doc,
            image_path=png_out,
            section_title=f"KẾ HOẠCH TIẾN ĐỘ TỔNG THỂ ({project_name.upper()})",
            figure_caption="Biểu đồ tiến độ chuẩn Microsoft Project (Split-View 8 cột WBS & Đường găng CPM)",
            width_cm=25.4,
            restore_portrait=True
        )
        doc.save(docx_out)
        print(f"Đã lưu văn bản Word thành công: {docx_out}")

    print("\n====================================================================")
    print("   PIPELINE TIẾN ĐỘ MICROSOFT PROJECT HOÀN TẤT THÀNH CÔNG 100%!")
    print("====================================================================")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Microsoft Project Bridge CLI")
    parser.add_argument("--demo", choices=["yen_quang"], help="Chạy demo mẫu dự án")
    parser.add_argument("--xml-out", help="Đường dẫn file XML đầu ra")
    parser.add_argument("--mpp-out", help="Đường dẫn file MPP đầu ra")
    parser.add_argument("--png-out", help="Đường dẫn file ảnh Gantt PNG 300 DPI đầu ra")
    parser.add_argument("--docx-out", help="Đường dẫn file Word nhúng trang Landscape")
    args = parser.parse_args()

    if args.demo == "yen_quang":
        tasks_data = get_ho_yen_quang_tasks()
        holidays_data = [
            {"start": "2027-01-26", "end": "2027-02-05", "label": "Nghỉ Tết Nguyên Đán Đinh Mùi 2027"}
        ]
        xml_path = args.xml_out or r"g:\My Drive\Google AI Studio\01_Projects\HO YEN QUANG\04_Deliverables_ToTrinh\YenQuang_TienDo_MSProject.xml"
        mpp_path = args.mpp_out or r"g:\My Drive\Google AI Studio\01_Projects\HO YEN QUANG\04_Deliverables_ToTrinh\YenQuang_TienDo_MSProject.mpp"
        png_path = args.png_out or r"g:\My Drive\Google AI Studio\01_Projects\HO YEN QUANG\04_Deliverables_ToTrinh\chart_tiendo_msproject_standard.png"
        
        run_pipeline(
            tasks=tasks_data,
            project_name="DỰ ÁN KHU DU LỊCH VÀ NGHỈ DƯỠNG SINH THÁI CAO CẤP HỒ YÊN QUANG",
            company_name="TẬP ĐOÀN C.T GROUP",
            start_date="2026-11-10",
            finish_date="2027-05-31",
            xml_out=xml_path,
            mpp_out=mpp_path,
            png_out=png_path,
            docx_out=args.docx_out,
            holidays=holidays_data
        )
    else:
        parser.print_help()

