"""
report_dispatcher.py — Unified Report Dispatcher

Mục đích: 1 lệnh CLI, nhiều output formats, audience-aware.

Usage:
    # Xuất báo cáo đầy đủ cho Designer
    python report_dispatcher.py \\
        --handoff audit_2026.json \\
        --formats md,docx \\
        --audience designer \\
        --output "G:/My Drive/Google AI Studio/01_Projects/REPORT/"

    # Chỉ xuất DOCX, có charts
    python report_dispatcher.py \\
        --handoff audit_2026.json \\
        --format docx \\
        --include-charts \\
        --audience designer

Updated: 2026-08-31 — Phase C of Reporting Upgrade v4.0
"""

import sys
import os
import argparse
import json
import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Force UTF-8 output for Windows console
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Make scripts folder accessible
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from _lib._audience_profiles import get_profile, list_audiences
from _lib._report_utils import (
    format_eta, format_citation, format_vn_date,
    safe_filename, render_priority_badge
)
from _lib._executive_dashboard import (
    render_executive_dashboard_md,
    render_executive_dashboard_html,
    render_executive_dashboard_docx,
)
from _lib._chart_inserter import (
    generate_comparison_chart,
    generate_progress_chart,
    generate_eta_heatmap,
    generate_cost_breakdown_chart,
)


# ════════════════════════════════════════════════════════════════════════════
# DATA LOADING
# ════════════════════════════════════════════════════════════════════════════

def load_handoff(path: str) -> dict:
    """Load JSON handoff file."""
    if not os.path.exists(path):
        print(f"❌ File không tồn tại: {path}")
        sys.exit(1)
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_executive_metrics(handoff: dict) -> dict:
    """
    Trích xuất executive metrics từ handoff JSON.
    Tính toán cho executive dashboard.
    """
    metrics = {
        'cost_delta_pct': 0.0,
        'cost_delta_abs': 0,
        'schedule_impact_days': 0,
        'nla_efficiency_pct': 0.0,
        'critical_issues': 0,
        'open_rfis': 0,
    }

    # Cost delta từ Comparison if exists
    comparison = handoff.get('So_Sanh', {})
    if comparison:
        plans = comparison.get('plans', {})
        if plans:
            base_plan = list(plans.keys())[0]
            base_value = plans[base_plan][0]  # First metric is cost
            for plan_name, values in plans.items():
                if plan_name != base_plan:
                    cost_delta = (values[0] - base_value) / base_value * 100 if base_value else 0
                    metrics['cost_delta_pct'] = cost_delta
                    metrics['cost_delta_abs'] = int(values[0] - base_value)
                    break

    # Count critical issues
    unverified = handoff.get('Unverified_Items', [])
    metrics['critical_issues'] = len([x for x in unverified if isinstance(x, str)])

    # Project info
    return {
        'project_name': handoff.get('Ten_Du_An', 'DỰ ÁN'),
        'date': format_vn_date(datetime.datetime.now()),
        'status': handoff.get('Trang_Thai', 'AT_RISK'),
        'metrics': metrics,
        'top_risks': unverified[:3] if unverified else [],
        'call_to_action': handoff.get('Kien_Nghi', ''),
    }


# ════════════════════════════════════════════════════════════════════════════
# MARKDOWN RENDERER
# ════════════════════════════════════════════════════════════════════════════

def render_markdown(handoff: dict, audience: str = 'designer',
                    include_charts: bool = True,
                    chart_dir: str = '') -> str:
    """Render full report as Markdown."""
    profile = get_profile(audience)
    sections = profile.get('sections', {})

    md_parts = []

    # Executive Dashboard (if included)
    if sections.get('executive_dashboard'):
        dash_data = extract_executive_metrics(handoff)
        md_parts.append(render_executive_dashboard_md(dash_data))
        md_parts.append('\n---\n')

    # Project Info
    if sections.get('project_info'):
        md_parts.append(f'# {handoff.get("Ten_Du_An", "DỰ ÁN")}\n')
        md_parts.append(f'**Hạng mục:** {handoff.get("Hang_Muc", "—")}  ')
        md_parts.append(f'**Giai đoạn:** {handoff.get("Giai_Doan_TK", "—")}  ')
        md_parts.append(f'**Ngày:** {format_vn_date(handoff.get("Ngay"))}\n')

    # Design Basis
    if sections.get('design_basis'):
        md_parts.append('## 1. Cơ sở Thiết kế\n')
        md_parts.append(f'**Loại phân tích:** {handoff.get("Loai_Phan_Tich", "—")}  ')
        md_parts.append(f'**Tiêu chuẩn áp dụng:** {handoff.get("Standard_Method", "TCVN 5574:2018, TCVN 5575:2024")}\n')
        md_parts.append('')

    # Calculation Logs
    if sections.get('calculation_logs'):
        calc_logs = handoff.get('Calculation_Logs', [])
        if calc_logs:
            md_parts.append(f'## { "2" if sections.get("design_basis") else "1"}. Calculation Logs ({len(calc_logs)} bước)\n')
            md_parts.append('| Step | Static Scheme | Formula | Values | Result | η | Rating |')
            md_parts.append('|------|---------------|---------|--------|--------|---|--------|')

            for log in calc_logs:
                if not isinstance(log, dict):
                    continue
                step = log.get('Step', '')
                scheme = log.get('Static_Scheme', '')
                formula = log.get('Formula', '')
                values = str(log.get('Values', ''))[:30]
                result = log.get('Result', '')
                util = log.get('Utilization')
                rating = log.get('Rating', 'GREEN')

                eta_str = format_eta(util) if util is not None else '—'
                rating_str = render_priority_badge(rating)

                # Truncate
                formula_short = formula[:40] + '...' if len(formula) > 40 else formula
                md_parts.append(f'| {step} | {scheme[:15]} | `{formula_short}` | {values} | {result} | {eta_str} | {rating_str} |')

            md_parts.append('')

    # Technical Analysis / Citation
    if sections.get('citations_appendix'):
        citations = handoff.get('Citations', [])
        if citations:
            md_parts.append('## Trích dẫn Tiêu chuẩn\n')
            for c in citations:
                md_parts.append(f'- {format_citation(c)}')
            md_parts.append('')

    # Comparison Table
    if sections.get('comparison_table'):
        comparison = handoff.get('So_Sanh', {})
        if comparison:
            categories = comparison.get('categories', [])
            plans = comparison.get('plans', {})
            if categories and plans:
                md_parts.append('## So sánh Phương án\n')
                md_parts.append('| Tiêu chí | ' + ' | '.join(plans.keys()) + ' |')
                md_parts.append('|----------|' + '|'.join(['---'] * len(plans)) + '|')
                for i, cat in enumerate(categories):
                    row_vals = []
                    for plan_name in plans.keys():
                        vals = plans[plan_name]
                        row_vals.append(str(vals[i]) if i < len(vals) else '—')
                    md_parts.append(f'| {cat} | ' + ' | '.join(row_vals) + ' |')
                md_parts.append('')

                if include_charts and chart_dir:
                    chart_path = os.path.join(chart_dir, 'comparison_chart.png')
                    try:
                        generate_comparison_chart(
                            categories=categories,
                            plans=plans,
                            out_path=chart_path,
                            chart_type='radar',
                            title=f'So sánh {len(plans)} phương án'
                        )
                        md_parts.append(f'![Biểu đồ so sánh]({os.path.basename(chart_path)})\n')
                    except Exception as e:
                        md_parts.append(f'*[Lỗi tạo biểu đồ: {e}]*\n')

    # Approval Matrix
    if sections.get('approval_matrix'):
        md_parts.append('## Approval Matrix\n')
        md_parts.append('| Trách nhiệm | Đề xuất | Kiểm tra | Phê duyệt |')
        md_parts.append('|-------------|---------|----------|-----------|')
        md_parts.append('| Người | AI | Kỹ sư | TP/Ban GĐ |')
        md_parts.append('| Ngày | ' + format_vn_date(datetime.datetime.now()) + ' | — | — |')
        md_parts.append('| Chữ ký | | | |')
        md_parts.append('')

    # Disclaimer
    if sections.get('disclaimer'):
        md_parts.append('---\n')
        md_parts.append('## Disclaimer\n')
        md_parts.append(
            '*Báo cáo này được tạo bởi AI có hỗ trợ kiểm chứng. '
            'Mọi quyết định thiết kế cuối cùng phải được kỹ sư có thẩm quyền phê duyệt.*\n'
        )

    return '\n'.join(md_parts)


# ════════════════════════════════════════════════════════════════════════════
# DOCX RENDERER
# ════════════════════════════════════════════════════════════════════════════

def render_docx(handoff: dict, audience: str = 'designer',
                output_path: str = '', include_charts: bool = True,
                chart_dir: str = ''):
    """Render full report as DOCX."""
    from docx import Document
    from _lib._docx_helpers import (
        new_document, add_cover_page, add_toc, add_header_footer,
        add_h, add_p, add_bullet, add_callout, build_table,
        add_img, COLOR_PRIMARY,
    )

    profile = get_profile(audience)
    sections = profile.get('sections', {})

    doc = new_document()

    # Cover page
    if sections.get('cover_page'):
        add_cover_page(
            doc,
            project_name=handoff.get('Ten_Du_An', 'DỰ ÁN'),
            report_title=handoff.get('Hang_Muc', 'BÁO CÁO KỸ THUẬT'),
            subtitle='Báo cáo Phân tích Kỹ thuật',
            author='AI Structural Engineer',
            date_str=format_vn_date(datetime.datetime.now()),
            version='v1.0',
        )

    # Header/Footer
    add_header_footer(
        doc,
        project_name=handoff.get('Ten_Du_An', ''),
        report_title=handoff.get('Hang_Muc', ''),
    )

    # TOC
    if sections.get('toc'):
        add_toc(doc)

    # Executive Dashboard
    if sections.get('executive_dashboard'):
        dash_data = extract_executive_metrics(handoff)
        render_executive_dashboard_docx(doc, dash_data)
        doc.add_page_break()

    # Project Info
    add_h(doc, '1. Thông tin Dự án', lv=1)
    info_rows = [
        ['Tên dự án', handoff.get('Ten_Du_An', '—')],
        ['Hạng mục', handoff.get('Hang_Muc', '—')],
        ['Giai đoạn', handoff.get('Giai_Doan_TK', '—')],
        ['Ngày', format_vn_date(handoff.get('Ngay'))],
        ['Loại phân tích', handoff.get('Loai_Phan_Tich', '—')],
        ['Audience', profile.get('name', audience)],
        ['Tiêu chuẩn', handoff.get('Standard_Method', 'TCVN 5574:2018, TCVN 5575:2024')],
    ]
    build_table(doc, ['Trường', 'Giá trị'], info_rows, col_widths_cm=[5.0, 11.0])

    # Calculation Logs
    if sections.get('calculation_logs'):
        calc_logs = handoff.get('Calculation_Logs', [])
        if calc_logs:
            add_h(doc, '2. Calculation Logs', lv=1)
            headers = ['Step', 'Scheme', 'Result', 'η', 'Rating']
            rows = []
            for log in calc_logs:
                if not isinstance(log, dict):
                    continue
                step = str(log.get('Step', ''))
                scheme = str(log.get('Static_Scheme', ''))[:15]
                result = str(log.get('Result', ''))[:25]
                util = log.get('Utilization')
                eta_str = f'{util:.2f}' if util is not None else '—'
                rating_str = log.get('Rating', 'GREEN')
                rows.append([step, scheme, result, eta_str, rating_str])
            build_table(doc, headers, rows, col_widths_cm=[2.0, 3.5, 6.5, 2.0, 2.5])

    # Citations Appendix
    if sections.get('citations_appendix'):
        citations = handoff.get('Citations', [])
        if citations:
            add_h(doc, '3. Citations', lv=1)
            for c in citations:
                add_p(doc, format_citation(c), size=10, sa=2)

    # Charts
    if include_charts and chart_dir:
        os.makedirs(chart_dir, exist_ok=True)

        # Comparison chart
        comparison = handoff.get('So_Sanh', {})
        if comparison and sections.get('comparison_table'):
            categories = comparison.get('categories', [])
            plans = comparison.get('plans', {})
            if categories and plans:
                chart_path = os.path.join(chart_dir, 'comparison_chart.png')
                try:
                    generate_comparison_chart(
                        categories=categories, plans=plans,
                        out_path=chart_path, chart_type='radar',
                        title='So sánh Phương án',
                    )
                    add_h(doc, '4. Biểu đồ So sánh', lv=1)
                    add_img(doc, chart_path, w=15.0,
                            caption='Biểu đồ radar so sánh các phương án')
                except Exception as e:
                    add_p(doc, f'[Lỗi tạo biểu đồ: {e}]', italic=True)

        # eta heatmap
        if sections.get('calculation_logs'):
            eta_items = []
            for log in handoff.get('Calculation_Logs', []):
                if isinstance(log, dict) and 'Utilization' in log:
                    eta_items.append({
                        'name': str(log.get('Step', ''))[:5],
                        'eta': log.get('Utilization', 0),
                    })
            if eta_items and len(eta_items) >= 2:
                chart_path = os.path.join(chart_dir, 'eta_heatmap.png')
                try:
                    # Reformat for heatmap (need multiple eta fields)
                    sample = eta_items[:10]
                    rows = [{'name': i['name'], 'eta': i['eta']} for i in sample]
                    generate_eta_heatmap(rows, chart_path, 'η Utilization')
                    add_img(doc, chart_path, w=14.0,
                            caption='Heatmap hệ số η (utilization ratio)')
                except Exception as e:
                    pass  # Optional - skip on failure

    # Approval Matrix
    if sections.get('approval_matrix'):
        doc.add_page_break()
        add_h(doc, '5. Approval Matrix', lv=1)
        today = format_vn_date(datetime.datetime.now())
        rows = [
            ['Đề xuất', 'AI / Kỹ sư thiết kế', today, '________'],
            ['Kiểm tra', 'Kỹ sư Tính toán', '—', '________'],
            ['Phê duyệt', 'TP / Ban GĐ', '—', '________'],
        ]
        build_table(doc, ['Vai trò', 'Người', 'Ngày', 'Chữ ký'], rows,
                    col_widths_cm=[3.0, 5.0, 3.0, 5.0])

    # Disclaimer
    if sections.get('disclaimer'):
        doc.add_page_break()
        add_callout(
            doc,
            '*Báo cáo này được tạo bởi AI có hỗ trợ kiểm chứng. '
            'Mọi quyết định thiết kế cuối cùng phải được kỹ sư có thẩm quyền phê duyệt.*',
            kind='info',
        )

    # Save
    doc.save(output_path)
    return output_path


# ════════════════════════════════════════════════════════════════════════════
# HTML RENDERER (optional, for web preview)
# ════════════════════════════════════════════════════════════════════════════

def render_html(handoff: dict, audience: str = 'designer', output_path: str = ''):
    """Render full report as HTML."""
    profile = get_profile(audience)
    sections = profile.get('sections', {})

    html_parts = []
    html_parts.append('<!DOCTYPE html>')
    html_parts.append('<html lang="vi">')
    html_parts.append('<head><meta charset="UTF-8">')
    html_parts.append(f'<title>{handoff.get("Ten_Du_An", "Report")}</title>')
    html_parts.append('<style>body{font-family:"Segoe UI",Arial,sans-serif;max-width:900px;margin:40px auto;padding:0 20px;color:#222;line-height:1.6}h1{color:#1C3557;border-bottom:2px solid #1C3557;padding-bottom:8px}h2{color:#2980B9;margin-top:30px}table{border-collapse:collapse;width:100%;margin:16px 0}th,td{padding:8px 12px;border:1px solid #ddd;text-align:left}th{background:#1C3557;color:#fff}</style>')
    html_parts.append('</head><body>')

    # Executive Dashboard
    if sections.get('executive_dashboard'):
        dash_data = extract_executive_metrics(handoff)
        html_parts.append(render_executive_dashboard_html(dash_data))

    html_parts.append(f'<h1>{handoff.get("Ten_Du_An", "DỰ ÁN")}</h1>')
    html_parts.append(f'<p><strong>Hạng mục:</strong> {handoff.get("Hang_Muc", "—")}<br>')
    html_parts.append(f'<strong>Giai đoạn:</strong> {handoff.get("Giai_Doan_TK", "—")}<br>')
    html_parts.append(f'<strong>Ngày:</strong> {format_vn_date(handoff.get("Ngay"))}</p>')

    html_parts.append('</body></html>')

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(html_parts))
    return output_path


# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description='Report Dispatcher — Unified báo cáo từ SKILLKC JSON Handoff',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single format
  python report_dispatcher.py --handoff data.json --format docx --audience designer

  # Multiple formats
  python report_dispatcher.py --handoff data.json --formats md,docx,html --audience owner

  # With charts
  python report_dispatcher.py --handoff data.json --format docx --include-charts

  # List audiences
  python report_dispatcher.py --list-audiences
        """,
    )
    parser.add_argument('--handoff', help='Path to SKILLKC JSON handoff file')
    parser.add_argument('--formats', default='md',
                        help='Comma-separated formats: md,docx,html (default: md)')
    parser.add_argument('--audience', default='designer',
                        help=f'Audience profile: {", ".join(list_audiences())} (default: designer)')
    parser.add_argument('--output', default='',
                        help='Output directory (default: same dir as handoff)')
    parser.add_argument('--output-filename', default='',
                        help='Output filename (without ext)')
    parser.add_argument('--include-charts', action='store_true',
                        help='Auto-generate charts và insert vào report')
    parser.add_argument('--list-audiences', action='store_true',
                        help='List available audience profiles')
    parser.add_argument('--json-input', action='store_true',
                        help='Use sample handoff for testing')
    args = parser.parse_args()

    # List audiences
    if args.list_audiences:
        print(f"\n📋 Available audiences:")
        for aud in list_audiences():
            p = get_profile(aud)
            print(f"  • {aud:12s} — {p.get('name', '')}")
            print(f"    {p.get('description', '')}")
        return

    # Validate
    if not args.handoff:
        print("❌ Cần --handoff (path to JSON file)")
        parser.print_help()
        sys.exit(1)

    # Load data
    handoff = load_handoff(args.handoff)
    print(f"✅ Loaded handoff: {args.handoff}")
    print(f"   Project: {handoff.get('Ten_Du_An', 'N/A')}")
    print(f"   Audience: {args.audience}")

    # Output paths
    if args.output:
        out_dir = args.output
    else:
        out_dir = os.path.dirname(args.handoff)
    os.makedirs(out_dir, exist_ok=True)

    if args.output_filename:
        base_name = args.output_filename
    else:
        project = safe_filename(handoff.get('Ten_Du_An', 'report'))
        hangmuc = safe_filename(handoff.get('Hang_Muc', 'analysis'))
        base_name = f'{project}_{hangmuc}_{args.audience}'

    formats = [f.strip() for f in args.formats.split(',')]
    chart_dir = os.path.join(out_dir, '_charts')
    if args.include_charts:
        os.makedirs(chart_dir, exist_ok=True)

    print(f"\n📄 Generating {len(formats)} format(s)...")

    for fmt in formats:
        try:
            if fmt == 'md':
                out_path = os.path.join(out_dir, f'{base_name}.md')
                content = render_markdown(
                    handoff, args.audience,
                    include_charts=args.include_charts,
                    chart_dir=chart_dir,
                )
                with open(out_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"   ✅ MD   → {out_path}")

            elif fmt == 'docx':
                out_path = os.path.join(out_dir, f'{base_name}.docx')
                render_docx(
                    handoff, args.audience, out_path,
                    include_charts=args.include_charts,
                    chart_dir=chart_dir,
                )
                print(f"   ✅ DOCX → {out_path}")

            elif fmt == 'html':
                out_path = os.path.join(out_dir, f'{base_name}.html')
                render_html(handoff, args.audience, out_path)
                print(f"   ✅ HTML → {out_path}")

            else:
                print(f"   ⚠️ Format không hỗ trợ: {fmt}")

        except Exception as e:
            print(f"   ❌ Lỗi format {fmt}: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n✨ Done. Outputs in: {out_dir}")


if __name__ == '__main__':
    main()
