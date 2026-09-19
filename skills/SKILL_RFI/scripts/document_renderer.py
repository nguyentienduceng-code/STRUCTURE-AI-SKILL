"""
document_renderer.py — Render SKILL_RFI documents ra DOCX/PDF

Mục đích: Chuyển JSON output của document_generator.py thành file Word chuyên nghiệp.

Hỗ trợ:
- RFI (Request for Information)
- NCR (Non-Conformance Report)
- SUBMITTAL (Shop Drawing/Material)
- CO (Change Order)
- TQ (Tech Query)
- PBRFI (Pre-Bid RFI)

Usage:
    # Xuất 1 document ra DOCX
    python document_renderer.py \\
        --input _data/document_registry.json \\
        --code RFI-GEN-20260831-739 \\
        --format docx

    # Xuất tất cả documents ra 1 folder
    python document_renderer.py \\
        --input _data/document_registry.json \\
        --all \\
        --output _output/

    # Xuất riêng RFI ra PDF
    python document_renderer.py \\
        --input _data/document_registry.json \\
        --code RFI-GEN-20260831-739 \\
        --format pdf \\
        --output report.pdf

Updated: 2026-08-31 — Phase D of Reporting Upgrade v4.0
"""

import sys
import os
import argparse
import json
from pathlib import Path
from datetime import datetime

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

SCRIPT_DIR = Path(__file__).parent
TEMPLATES_DIR = SCRIPT_DIR.parent / 'templates'
DATA_DIR = SCRIPT_DIR.parent / 'data'


# ════════════════════════════════════════════════════════════════════════════
# DATA LOADING
# ════════════════════════════════════════════════════════════════════════════

def load_registry(path: str) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def find_doc_by_code(registry: dict, code: str) -> tuple:
    """Tìm document theo code. Returns (doc_type, doc_dict) hoặc (None, None)."""
    documents = registry.get('documents', {})
    for doc_type, docs in documents.items():
        for d in docs:
            if d.get('Doc_Code') == code:
                return doc_type, d
    return None, None


def get_all_docs(registry: dict) -> list:
    """Trả về list of (doc_type, doc_dict) cho TẤT CẢ documents."""
    result = []
    documents = registry.get('documents', {})
    for doc_type, docs in documents.items():
        for d in docs:
            result.append((doc_type, d))
    return result


# ════════════════════════════════════════════════════════════════════════════
# DOCX RENDERERS (one per document type)
# ════════════════════════════════════════════════════════════════════════════

def render_rfi_docx(doc_dict: dict, output_path: str):
    """Render RFI ra DOCX."""
    from docx import Document
    from docx.shared import Pt, Cm, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    doc = Document()

    # Page setup
    for section in doc.sections:
        section.top_margin = Cm(2)
        section.bottom_margin = Cm(2)
        section.left_margin = Cm(3)
        section.right_margin = Cm(2)

    # Header banner
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run('REQUEST FOR INFORMATION (RFI)')
    r.font.size = Pt(18)
    r.bold = True
    r.font.color.rgb = RGBColor.from_string('1C3557')

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run('YÊU CẦU LÀM RÕ THÔNG TIN')
    r.font.size = Pt(14)
    r.italic = True
    r.font.color.rgb = RGBColor.from_string('555555')

    # Spacer
    doc.add_paragraph()

    # Doc code
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(f'Mã: {doc_dict.get("Doc_Code", "—")}')
    r.font.size = Pt(13)
    r.bold = True
    r.font.color.rgb = RGBColor.from_string('C0392B' if doc_dict.get('Priority') == 'CRITICAL' else '1C3557')

    # Info table
    info_table = doc.add_table(rows=6, cols=2)
    info_table.style = 'Light Grid Accent 1'
    info_pairs = [
        ('Dự án:', doc_dict.get('Project', '—')),
        ('Từ:', doc_dict.get('From_Party', '—')),
        ('Đến:', doc_dict.get('To_Party', '—')),
        ('Mức ưu tiên:', f'{doc_dict.get("Priority_Symbol", "")} {doc_dict.get("Priority", "—")}'),
        ('Hạn chót:', doc_dict.get('Deadline', '—')),
        ('Ngày tạo:', doc_dict.get('Tracking', {}).get('Created_Date', '—')),
    ]
    for i, (label, value) in enumerate(info_pairs):
        c1 = info_table.rows[i].cells[0]
        c1.text = label
        for p in c1.paragraphs:
            for r in p.runs:
                r.bold = True

        c2 = info_table.rows[i].cells[1]
        c2.text = value

    doc.add_paragraph()

    # Issue section
    h = doc.add_heading('1. Vấn đề cần làm rõ', level=1)
    issue = doc_dict.get('Issue', {})
    summary = issue.get('Summary', '—')
    p = doc.add_paragraph()
    r = p.add_run('Tóm tắt: ')
    r.bold = True
    p.add_run(summary)

    if issue.get('Detail'):
        p = doc.add_paragraph()
        r = p.add_run('Chi tiết: ')
        r.bold = True
        p.add_run(issue['Detail'])

    # Context
    if doc_dict.get('Context'):
        doc.add_heading('2. Bối cảnh', level=1)
        doc.add_paragraph(doc_dict['Context'])

    # Impact
    if doc_dict.get('Impact'):
        doc.add_heading('3. Ảnh hưởng nếu không làm rõ', level=1)
        doc.add_paragraph(doc_dict['Impact'])

    # Required response
    if doc_dict.get('Required_Response'):
        doc.add_heading('4. Yêu cầu phản hồi', level=1)
        doc.add_paragraph(doc_dict['Required_Response'])

    # Drawings
    if doc_dict.get('Drawings'):
        doc.add_heading('5. Bản vẽ/Tài liệu liên quan', level=1)
        for d in doc_dict['Drawings']:
            doc.add_paragraph(f'• {d}', style='List Bullet')

    # History
    history = doc_dict.get('Tracking', {}).get('History', [])
    if history:
        doc.add_heading('6. Lịch sử xử lý', level=1)
        for h in history:
            p = doc.add_paragraph(style='List Bullet')
            date = h.get('date', '')
            action = h.get('action', '')
            by = h.get('by', '')
            r = p.add_run(f'[{date}] {action} - {by}')
            r.font.size = Pt(10)

    # Approval
    doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r = p.add_run(f'Ngày tạo: {doc_dict.get("Tracking", {}).get("Created_Date", datetime.now().strftime("%d/%m/%Y"))}')
    r.font.size = Pt(10)
    r.italic = True

    doc.save(output_path)
    return output_path


def render_ncr_docx(doc_dict: dict, output_path: str):
    """Render NCR ra DOCX với template chuẩn."""
    from docx import Document
    from docx.shared import Pt, Cm, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    doc = Document()
    for section in doc.sections:
        section.top_margin = Cm(2)
        section.bottom_margin = Cm(2)
        section.left_margin = Cm(3)
        section.right_margin = Cm(2)

    # Banner với màu theo severity
    severity = doc_dict.get('NCR_Classification', 'MINOR')
    severity_colors = {
        'CRITICAL': 'C0392B',
        'MAJOR': 'E67E22',
        'MINOR': 'F39C12',
    }

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run('NON-CONFORMANCE REPORT (NCR)')
    r.font.size = Pt(18)
    r.bold = True
    r.font.color.rgb = RGBColor.from_string('1C3557')

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(f'PHIẾU BÁO CÁO KHÔNG PHÙ HỢP — {severity}')
    r.font.size = Pt(14)
    r.bold = True
    r.font.color.rgb = RGBColor.from_string(severity_colors.get(severity, '1C3557'))

    doc.add_paragraph()

    # Doc code
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(f'Mã: {doc_dict.get("Doc_Code", "—")}')
    r.font.size = Pt(13)
    r.bold = True

    # What/Where/When/Why (5W1H)
    doc.add_heading('1. Thông tin Cơ bản', level=1)

    ncr = doc_dict.get('NCR', {})

    table = doc.add_table(rows=4, cols=2)
    table.style = 'Light Grid Accent 1'
    pairs = [
        ('What — Mô tả không phù hợp:', ncr.get('Description', doc_dict.get('Issue', {}).get('Summary', '—'))),
        ('Where — Vị trí:', ncr.get('Location', '—')),
        ('When — Ngày phát hiện:', ncr.get('Detection_Date', doc_dict.get('Tracking', {}).get('Created_Date', '—'))),
        ('Why — Nguyên nhân dự kiến:', ncr.get('Root_Cause', '—')),
    ]
    for i, (label, value) in enumerate(pairs):
        table.rows[i].cells[0].text = label
        for p in table.rows[i].cells[0].paragraphs:
            for r in p.runs:
                r.bold = True
        table.rows[i].cells[1].text = value

    # Impact
    if doc_dict.get('Impact'):
        doc.add_heading('2. Ảnh hưởng Tiềm ẩn', level=1)
        doc.add_paragraph(doc_dict['Impact'])

    # Corrective action
    if ncr.get('Corrective_Action'):
        doc.add_heading('3. Đề xuất Khắc phục', level=1)
        doc.add_paragraph(ncr['Corrective_Action'])

    # Status
    doc.add_heading('4. Phản hồi của Nhà thầu', level=1)
    p = doc.add_paragraph('Trạng thái: ')
    r = p.add_run(doc_dict.get('Status', 'OPEN'))
    r.bold = True

    doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r = p.add_run('Ngày tạo: ' + doc_dict.get('Tracking', {}).get('Created_Date', '—'))
    r.font.size = Pt(10)
    r.italic = True

    doc.save(output_path)
    return output_path


def render_submittal_docx(doc_dict: dict, output_path: str):
    """Render Submittal ra DOCX."""
    from docx import Document
    from docx.shared import Pt, Cm, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    doc = Document()
    for section in doc.sections:
        section.top_margin = Cm(2)
        section.bottom_margin = Cm(2)
        section.left_margin = Cm(3)
        section.right_margin = Cm(2)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run('SUBMITTAL LOG')
    r.font.size = Pt(18)
    r.bold = True
    r.font.color.rgb = RGBColor.from_string('1C3557')

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run('BẢN VẼ THI CÔNG / MẪU VẬT LIỆU')
    r.font.size = Pt(14)
    r.italic = True

    doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(f'Mã: {doc_dict.get("Doc_Code", "—")}')
    r.font.size = Pt(13)
    r.bold = True

    doc.add_heading('1. Thông tin Submittal', level=1)
    table = doc.add_table(rows=6, cols=2)
    table.style = 'Light Grid Accent 1'
    pairs = [
        ('Dự án:', doc_dict.get('Project', '—')),
        ('Nhà thầu:', doc_dict.get('From_Party', '—')),
        ('Gửi đến:', doc_dict.get('To_Party', '—')),
        ('Loại submittal:', doc_dict.get('Submittal_Type', '—')),
        ('Hạn duyệt:', doc_dict.get('Deadline', '—')),
        ('Trạng thái duyệt:', doc_dict.get('Approval_Status', 'Pending')),
    ]
    for i, (label, value) in enumerate(pairs):
        c1 = table.rows[i].cells[0]
        c1.text = label
        for p in c1.paragraphs:
            for r in p.runs:
                r.bold = True
        c2 = table.rows[i].cells[1]
        c2.text = value

    doc.add_heading('2. Mô tả', level=1)
    issue = doc_dict.get('Issue', {})
    if issue.get('Summary'):
        doc.add_paragraph(f'Tóm tắt: {issue["Summary"]}')
    if issue.get('Detail'):
        doc.add_paragraph(f'Chi tiết: {issue["Detail"]}')

    if doc_dict.get('Drawings'):
        doc.add_heading('3. Bản vẽ/Tài liệu đính kèm', level=1)
        for d in doc_dict['Drawings']:
            doc.add_paragraph(f'• {d}', style='List Bullet')

    if doc_dict.get('Reviewer_Comments'):
        doc.add_heading('4. Ý kiến của Reviewer', level=1)
        doc.add_paragraph(doc_dict['Reviewer_Comments'])

    doc.save(output_path)
    return output_path


def render_generic_docx(doc_dict: dict, output_path: str, doc_type: str = 'DOCUMENT'):
    """Render generic CO/TQ/PBRFI ra DOCX."""
    from docx import Document
    from docx.shared import Pt, Cm, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    doc = Document()
    for section in doc.sections:
        section.top_margin = Cm(2)
        section.bottom_margin = Cm(2)
        section.left_margin = Cm(3)
        section.right_margin = Cm(2)

    type_names = {
        'CO': 'CHANGE ORDER',
        'TQ': 'TECHNICAL QUERY',
        'PBRFI': 'PRE-BID RFI',
    }
    type_name = type_names.get(doc_type, doc_type)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(f'{type_name}')
    r.font.size = Pt(18)
    r.bold = True
    r.font.color.rgb = RGBColor.from_string('1C3557')

    doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(f'Mã: {doc_dict.get("Doc_Code", "—")}')
    r.font.size = Pt(13)
    r.bold = True

    doc.add_heading(f'1. Thông tin {type_name}', level=1)
    table = doc.add_table(rows=5, cols=2)
    table.style = 'Light Grid Accent 1'
    pairs = [
        ('Dự án:', doc_dict.get('Project', '—')),
        ('Từ:', doc_dict.get('From_Party', '—')),
        ('Đến:', doc_dict.get('To_Party', '—')),
        ('Mức ưu tiên:', f'{doc_dict.get("Priority", "—")}'),
        ('Hạn chót:', doc_dict.get('Deadline', '—')),
    ]
    for i, (label, value) in enumerate(pairs):
        c1 = table.rows[i].cells[0]
        c1.text = label
        for p in c1.paragraphs:
            for r in p.runs:
                r.bold = True
        c2 = table.rows[i].cells[1]
        c2.text = value

    issue = doc_dict.get('Issue', {})
    if issue.get('Summary'):
        doc.add_heading('2. Tóm tắt', level=1)
        doc.add_paragraph(issue['Summary'])
    if issue.get('Detail') or doc_dict.get('Context'):
        doc.add_heading('3. Chi tiết/Bối cảnh', level=1)
        if issue.get('Detail'):
            doc.add_paragraph(issue['Detail'])
        if doc_dict.get('Context'):
            doc.add_paragraph(doc_dict['Context'])
    if doc_dict.get('Impact'):
        doc.add_heading('4. Ảnh hưởng', level=1)
        doc.add_paragraph(doc_dict['Impact'])

    doc.save(output_path)
    return output_path


# ════════════════════════════════════════════════════════════════════════════
# MARKDOWN RENDERERS
# ════════════════════════════════════════════════════════════════════════════

def render_doc_md(doc_dict: dict, doc_type: str) -> str:
    """Render any doc type as Markdown."""
    parts = []
    parts.append(f'# {doc_type} — {doc_dict.get("Doc_Code", "—")}')
    parts.append('')
    parts.append(f'**Dự án:** {doc_dict.get("Project", "—")}  ')
    parts.append(f'**Từ:** {doc_dict.get("From_Party", "—")} → **Đến:** {doc_dict.get("To_Party", "—")}  ')
    parts.append(f'**Mức:** {doc_dict.get("Priority", "—")}  ')
    parts.append(f'**Deadline:** {doc_dict.get("Deadline", "—")}  ')
    parts.append('')

    issue = doc_dict.get('Issue', {})
    if issue.get('Summary'):
        parts.append('## Tóm tắt')
        parts.append(issue['Summary'])
        parts.append('')

    if doc_dict.get('Context'):
        parts.append('## Bối cảnh')
        parts.append(doc_dict['Context'])
        parts.append('')

    if doc_dict.get('Impact'):
        parts.append('## Ảnh hưởng')
        parts.append(doc_dict['Impact'])
        parts.append('')

    # NCR-specific
    if doc_type == 'NCR':
        ncr = doc_dict.get('NCR', {})
        if ncr.get('Description'):
            parts.append('## Mô tả không phù hợp (What)')
            parts.append(ncr['Description'])
            parts.append('')
        if ncr.get('Root_Cause'):
            parts.append('## Nguyên nhân (Why)')
            parts.append(ncr['Root_Cause'])
            parts.append('')
        if ncr.get('Corrective_Action'):
            parts.append('## Đề xuất Khắc phục')
            parts.append(ncr['Corrective_Action'])
            parts.append('')

    history = doc_dict.get('Tracking', {}).get('History', [])
    if history:
        parts.append('## Lịch sử')
        for h in history:
            parts.append(f'- [{h.get("date")}] {h.get("action")} — {h.get("by")}')
        parts.append('')

    parts.append('---')
    parts.append(f'*Ngày tạo: {doc_dict.get("Tracking", {}).get("Created_Date", "—")}*')
    return '\n'.join(parts)


# ════════════════════════════════════════════════════════════════════════════
# MAIN DISPATCHER
# ════════════════════════════════════════════════════════════════════════════

def render_one(doc_type: str, doc_dict: dict, fmt: str, output_path: str) -> str:
    """Render a single document."""
    if fmt == 'md':
        content = render_doc_md(doc_dict, doc_type)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
    elif fmt == 'docx':
        if doc_type == 'RFI' or doc_type == 'PBRFI':
            return render_rfi_docx(doc_dict, output_path)
        elif doc_type == 'NCR':
            return render_ncr_docx(doc_dict, output_path)
        elif doc_type == 'SUBMITTAL':
            return render_submittal_docx(doc_dict, output_path)
        else:
            return render_generic_docx(doc_dict, output_path, doc_type)
    else:
        raise ValueError(f'Format không hỗ trợ: {fmt}')

    return output_path


def main():
    parser = argparse.ArgumentParser(
        description='SKILL_RFI Document Renderer — JSON → DOCX/MD',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('--input', required=True,
                        help='Path to document_registry.json')
    parser.add_argument('--code', help='Doc code cụ thể (e.g., RFI-GEN-20260831-001)')
    parser.add_argument('--all', action='store_true',
                        help='Render tất cả documents')
    parser.add_argument('--format', default='docx',
                        choices=['docx', 'md'],
                        help='Output format (default: docx)')
    parser.add_argument('--output', default='',
                        help='Output directory (default: alongside input)')
    parser.add_argument('--type', help='Filter theo doc type (RFI/NCR/SUBMITTAL/CO/TQ/PBRFI)')
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f'❌ File không tồn tại: {args.input}')
        sys.exit(1)

    registry = load_registry(args.input)
    project = registry.get('project_name', 'unknown')

    out_dir = args.output or os.path.dirname(args.input)
    os.makedirs(out_dir, exist_ok=True)

    if args.all:
        all_docs = get_all_docs(registry)
        if args.type:
            all_docs = [(t, d) for t, d in all_docs if t.upper() == args.type.upper()]
        print(f'📄 Rendering {len(all_docs)} documents...')
        for doc_type, doc_dict in all_docs:
            code = doc_dict.get('Doc_Code', 'unknown')
            ext = 'docx' if args.format == 'docx' else 'md'
            out_path = os.path.join(out_dir, f'{code}.{ext}')
            try:
                render_one(doc_type, doc_dict, args.format, out_path)
                print(f'   ✅ {code} → {out_path}')
            except Exception as e:
                print(f'   ❌ {code}: {e}')
    elif args.code:
        doc_type, doc_dict = find_doc_by_code(registry, args.code)
        if not doc_dict:
            print(f'❌ Không tìm thấy code: {args.code}')
            sys.exit(1)
        ext = 'docx' if args.format == 'docx' else 'md'
        out_path = os.path.join(out_dir, f'{args.code}.{ext}')
        render_one(doc_type, doc_dict, args.format, out_path)
        print(f'✅ Rendered: {out_path}')
    else:
        print('❌ Cần --code hoặc --all')
        parser.print_help()
        sys.exit(1)

    print(f'\n✨ Done.')


if __name__ == '__main__':
    main()
