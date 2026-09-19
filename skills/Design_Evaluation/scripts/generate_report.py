
# Auto-injected Error Handler
import sys
import os
agents_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if agents_dir not in sys.path:
    sys.path.insert(0, agents_dir)
try:
    from modules.error_handler import with_error_handling
except ImportError:
    # Dummy decorator if module not found
    def with_error_handling(func):
        return func

"""
generate_report.py — Luồng 1: Bơm dữ liệu JSON vào Template Word (.docx)

Sử dụng:
  python generate_report.py <file_template.docx> <file_data.json> <file_output.docx>

Ví dụ:
  python generate_report.py "templates/BXD-TTTK KT- TO TRINH MAU.docx" data.json "To_Trinh_Final.docx"

Tính năng:
  - Tự động cài docxtpl nếu chưa có
  - Hỗ trợ UTF-8 (tiếng Việt)
  - [BUG-04] Quét tag bằng docxtpl built-in (không dùng regex)
  - [OPT-03] --dry-run mode: validate trước, không render
  - Hỗ trợ biến list (bảng lặp) trong template
"""

import sys
import json
import os
import subprocess
from datetime import datetime

# Đảm bảo in tiếng Việt ra Terminal không bị lỗi Unicode
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

try:
    from docxtpl import DocxTemplate
except ImportError:
    print("⏳ Thư viện docxtpl chưa được cài đặt. Đang tiến hành cài đặt tự động...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "docxtpl"])
    from docxtpl import DocxTemplate

try:
    from jinja2 import UndefinedError
except ImportError:
    UndefinedError = None


def scan_template_tags(template_path):
    """[BUG-04] Quét tag bằng docxtpl built-in method (đáng tin cậy hơn regex).
    
    Phương pháp cũ dùng regex trên para.text sẽ thất bại khi Word chia nhỏ
    text thành nhiều run (do formatting thay đổi giữa {{ và }}). Phương pháp
    mới dùng Jinja2 engine của docxtpl để parse chính xác.
    """
    doc = DocxTemplate(template_path)
    
    # Phương pháp chính: dùng docxtpl built-in (chính xác nhất)
    try:
        tags = doc.get_undeclared_template_variables()
        return tags
    except Exception:
        pass
    
    # Fallback: quét regex trên XML source (đáng tin hơn quét para.text)
    import re
    tags = set()
    # docxtpl thay {{tag}} bằng {%raw%}...{%endraw%} trong XML nội bộ
    # nhưng para.text vẫn giữ nguyên, nên fallback dùng regex
    for para in doc.docx.paragraphs:
        found = re.findall(r'\{\{\s*(\w+)\s*\}\}', para.text)
        tags.update(found)
    for table in doc.docx.tables:
        for row in table.rows:
            for cell in row.cells:
                found = re.findall(r'\{\{\s*(\w+)\s*\}\}', cell.text)
                tags.update(found)
    return tags


def validate_mapping(template_tags, json_keys):
    """Kiểm tra sự khớp giữa tags trong template và keys trong JSON."""
    missing_in_json = template_tags - json_keys
    extra_in_json = json_keys - template_tags
    matched = template_tags & json_keys

    print(f"\n📊 KẾT QUẢ KIỂM TRA TAG MAPPING:")
    print(f"   ✅ Khớp (Matched):    {len(matched)} tags")
    
    if missing_in_json:
        # Lọc bỏ các tag thuộc cú pháp Jinja2 (for, endfor, if, endif, ...)
        real_missing = {t for t in missing_in_json 
                       if not any(t.strip().startswith(kw) for kw in ['%', '#', 'for ', 'endfor', 'if ', 'endif', 'else'])}
        if real_missing:
            print(f"   ⚠️  Thiếu trong JSON: {len(real_missing)} tags")
            for t in sorted(real_missing):
                print(f"       - {{{{{t}}}}}")
    
    if extra_in_json:
        print(f"   ℹ️  Dư trong JSON:    {len(extra_in_json)} keys (sẽ bị bỏ qua)")
        for t in sorted(extra_in_json):
            print(f"       - {t}")
    
    return len(missing_in_json) == 0


@with_error_handling
def generate_report(template_path, json_data_path, output_path):
    """Hàm chính: bơm dữ liệu JSON vào template Word."""
    
    print("=" * 60)
    print("  GENERATE REPORT — Luồng 1: Template-based")
    print("=" * 60)
    
    # Kiểm tra file tồn tại
    if not os.path.exists(template_path):
        print(f"\n❌ [LỖI] Không tìm thấy file mẫu (template) tại:\n   {template_path}")
        sys.exit(1)
        
    if not os.path.exists(json_data_path):
        print(f"\n❌ [LỖI] Không tìm thấy file dữ liệu JSON tại:\n   {json_data_path}")
        sys.exit(1)

    # Bước 1: Đọc template
    print(f"\n📄 Template: {os.path.basename(template_path)}")
    doc = DocxTemplate(template_path)

    # Bước 2: Quét tags trong template
    print("🔍 Đang quét {{Tag}} trong template...")
    template_tags = scan_template_tags(template_path)
    if template_tags:
        print(f"   Tìm thấy {len(template_tags)} tags: {', '.join(sorted(template_tags)[:10])}{'...' if len(template_tags) > 10 else ''}")
    else:
        print("   ⚠️  Không tìm thấy tag nào! Kiểm tra lại file template.")

    # Bước 3: Đọc dữ liệu JSON
    print(f"\n📋 Data JSON: {os.path.basename(json_data_path)}")
    try:
        with open(json_data_path, 'r', encoding='utf-8') as f:
            context = json.load(f)
    except json.JSONDecodeError as e:
        print(f"\n❌ [LỖI] File JSON không hợp lệ: {e}")
        sys.exit(1)
    
    json_keys = set(context.keys())
    print(f"   Tìm thấy {len(json_keys)} keys")

    # Bước 4: Validate mapping
    if template_tags:
        validate_mapping(template_tags, json_keys)

    # Bước 5: Render
    print(f"\n⚙️  Đang bơm dữ liệu (Render) vào Word...")
    try:
        doc.render(context)
    except Exception as e:
        print(f"\n❌ [LỖI] Render thất bại: {e}")
        print("   Kiểm tra lại cú pháp Jinja2 trong template và dữ liệu JSON.")
        sys.exit(1)
    
    # Bước 6: Thêm Phụ lục Log Tính Toán (nếu có)
    if "Calculation_Logs" in context and isinstance(context["Calculation_Logs"], list) and len(context["Calculation_Logs"]) > 0:
        print("\n➕ Đang tự động chèn Phụ lục: Log tính toán...")
        from docx.shared import Pt, RGBColor
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.oxml.ns import qn
        from docx.oxml import OxmlElement
        
        docx_obj = doc.docx
        docx_obj.add_page_break()
        heading = docx_obj.add_heading('PHỤ LỤC: CHI TIẾT TÍNH TOÁN', level=1)
        heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        logs = context["Calculation_Logs"]
        table = docx_obj.add_table(rows=1, cols=4)
        table.style = 'Table Grid'
        
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = 'Bước / Step'
        hdr_cells[1].text = 'Công thức / Formula'
        hdr_cells[2].text = 'Thay số / Values'
        hdr_cells[3].text = 'Kết quả / Result'
        
        for idx, cell in enumerate(hdr_cells):
            # Bold header
            for run in cell.paragraphs[0].runs:
                run.font.bold = True
                
        for log in logs:
            row_cells = table.add_row().cells
            row_cells[0].text = str(log.get("Step", ""))
            row_cells[1].text = str(log.get("Formula", ""))
            row_cells[2].text = str(log.get("Values", ""))
            row_cells[3].text = str(log.get("Result", ""))
            
    # Bước 7: Lưu file
    doc.save(output_path)
    file_size = os.path.getsize(output_path)
    
    print(f"\n{'=' * 60}")
    print(f"  ✅ THÀNH CÔNG!")
    print(f"  📁 File output: {output_path}")
    print(f"  📐 Kích thước:  {file_size / 1024:.1f} KB")
    print(f"  🕐 Thời gian:   {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--scan":
        print("Hướng dẫn: python generate_report.py --scan <file_template.docx>")
        sys.exit(0)
    
    if len(sys.argv) == 3 and sys.argv[1] == "--scan":
        t_path = sys.argv[2]
        if not os.path.exists(t_path):
            print(f"❌ Không tìm thấy: {t_path}")
            sys.exit(1)
        tags = scan_template_tags(t_path)
        print(f"\n📄 Template: {os.path.basename(t_path)}")
        print(f"🔍 Tìm thấy {len(tags)} tags:")
        for t in sorted(tags):
            print(f"   {{{{{t}}}}}")
        sys.exit(0)

    # [OPT-03] --dry-run mode: validate tag mapping mà KHÔNG render
    if len(sys.argv) == 4 and sys.argv[1] == "--dry-run":
        t_path = sys.argv[2]
        j_path = sys.argv[3]
        if not os.path.exists(t_path):
            print(f"❌ Không tìm thấy template: {t_path}")
            sys.exit(1)
        if not os.path.exists(j_path):
            print(f"❌ Không tìm thấy JSON: {j_path}")
            sys.exit(1)
        
        print("=" * 60)
        print("  DRY RUN — Validate Only (không xuất file)")
        print("=" * 60)
        
        tags = scan_template_tags(t_path)
        print(f"\n📄 Template: {os.path.basename(t_path)} ({len(tags)} tags)")
        
        with open(j_path, 'r', encoding='utf-8') as f:
            context = json.load(f)
        json_keys = set(context.keys())
        print(f"📋 JSON: {os.path.basename(j_path)} ({len(json_keys)} keys)")
        
        is_valid = validate_mapping(tags, json_keys)
        print(f"\n{'✅ SẴN SÀNG render!' if is_valid else '⚠️ Có tag chưa mapping — kiểm tra lại.'}")
        sys.exit(0 if is_valid else 1)

    if len(sys.argv) != 4:
        print("=" * 60)
        print("  GENERATE REPORT — Bơm dữ liệu JSON vào Template Word")
        print("=" * 60)
        print()
        print("Cách dùng:")
        print("  python generate_report.py <template.docx> <data.json> <output.docx>")
        print()
        print("Chế độ đặc biệt:")
        print("  --scan <template>          Quét tags trong template")
        print("  --dry-run <template> <json> Validate mapping (không xuất file)")
        print()
        sys.exit(1)
        
    t_path = sys.argv[1]
    j_path = sys.argv[2]
    o_path = sys.argv[3]
    
    generate_report(t_path, j_path, o_path)
