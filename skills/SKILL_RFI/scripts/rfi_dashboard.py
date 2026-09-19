"""
SKILL_RFI - Document Dashboard
Dashboard tổng quan cho tất cả loại tài liệu (RFI/NCR/Submittal/CO/TQ)

Usage:
    python rfi_dashboard.py
    python rfi_dashboard.py --export dashboard.html
"""

import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path


def load_registry():
    """Load document registry."""
    registry_path = Path(__file__).parent.parent / "data" / "document_registry.json"

    if not registry_path.exists():
        return None

    with open(registry_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def update_tracking(doc):
    """Cập nhật tracking info cho một tài liệu."""
    today = datetime.now()

    try:
        deadline = datetime.strptime(doc.get("Deadline", ""), '%d/%m/%Y')
    except:
        deadline = today + timedelta(days=7)

    try:
        created = datetime.strptime(doc["Tracking"]["Created_Date"], '%d/%m/%Y')
    except:
        created = today

    days_open = (today - created).days
    days_to_deadline = (deadline - today).days

    doc["Tracking"]["Days_Open"] = days_open
    doc["Days_To_Deadline"] = days_to_deadline
    doc["Tracking"]["Overdue"] = days_to_deadline < 0

    # Auto-escalation
    if days_to_deadline < 0:
        overdue_days = abs(days_to_deadline)
        if overdue_days > 14:
            doc["Tracking"]["Escalation_Level"] = 3
        elif overdue_days > 7:
            doc["Tracking"]["Escalation_Level"] = 2
        elif overdue_days > 2:
            doc["Tracking"]["Escalation_Level"] = 1

    return doc


def collect_all_docs(registry):
    """Collect all documents từ registry."""
    all_docs = []
    documents = registry.get("documents", {})

    for doc_type, docs in documents.items():
        for doc in docs:
            doc["_doc_type"] = doc_type
            update_tracking(doc)
            all_docs.append(doc)

    # Sort by priority then deadline
    priority_order = {"CRITICAL": 0, "URGENT": 1, "HIGH": 2, "NORMAL": 3, "ROUTINE": 4}
    all_docs.sort(key=lambda x: (
        priority_order.get(x.get("Priority", "NORMAL"), 5),
        x.get("Days_To_Deadline", 999)
    ))

    return all_docs


def generate_dashboard_html(registry):
    """Generate HTML dashboard cho tất cả loại documents."""

    all_docs = collect_all_docs(registry)
    stats = registry.get("statistics", {})

    # Count by priority
    critical = [d for d in all_docs if d.get("Priority") == "CRITICAL"]
    urgent = [d for d in all_docs if d.get("Priority") == "URGENT"]
    high = [d for d in all_docs if d.get("Priority") == "HIGH"]
    overdue = [d for d in all_docs if d.get("Tracking", {}).get("Overdue", False)]

    # Count by type
    by_type = {}
    for doc in all_docs:
        dtype = doc.get("_doc_type", "UNKNOWN")
        by_type[dtype] = by_type.get(dtype, 0) + 1

    type_stats_html = ""
    for dtype, count in sorted(by_type.items()):
        type_stats_html += f'<span class="type-badge">{dtype}: {count}</span> '

    html = f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>Document Dashboard - {registry.get('project_name', 'Project')}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f5f5f5; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #1a1a2e, #16213e); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }}
        .header h1 {{ font-size: 24px; }}
        .header p {{ opacity: 0.8; margin-top: 5px; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin-bottom: 20px; }}
        .stat-card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; }}
        .stat-card h3 {{ font-size: 32px; color: #333; }}
        .stat-card p {{ color: #666; font-size: 14px; }}
        .stat-critical {{ border-left: 4px solid #c0392b; }}
        .stat-urgent {{ border-left: 4px solid #e74c3c; }}
        .stat-overdue {{ border-left: 4px solid #e74c3c; background: #ffeaea; }}
        .section {{ background: white; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .section h2 {{ border-bottom: 2px solid #eee; padding-bottom: 10px; margin-bottom: 15px; }}
        .doc-item {{ padding: 15px; border: 1px solid #eee; border-radius: 5px; margin-bottom: 10px; }}
        .doc-item:hover {{ background: #f9f9f9; }}
        .doc-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }}
        .doc-code {{ font-weight: bold; color: #333; }}
        .badge {{ padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; margin-left: 5px; }}
        .badge-critical {{ background: #c0392b; color: white; }}
        .badge-urgent {{ background: #e74c3c; color: white; }}
        .badge-high {{ background: #f39c12; color: white; }}
        .badge-normal {{ background: #3498db; color: white; }}
        .type-badge {{ display: inline-block; padding: 4px 10px; background: #ecf0f1; border-radius: 4px; font-size: 14px; margin-right: 5px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #eee; }}
        th {{ background: #f9f9f9; font-weight: 600; }}
        .overdue {{ color: #e74c3c; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📋 Technical Document Dashboard</h1>
        <p>{registry.get('project_name', 'Project')} | Cập nhật: {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
        <p style="margin-top: 10px;">{type_stats_html}</p>
    </div>

    <div class="stats-grid">
        <div class="stat-card stat-critical">
            <h3>{len(critical)}</h3>
            <p>🔴 CRITICAL</p>
        </div>
        <div class="stat-card stat-urgent">
            <h3>{len(urgent)}</h3>
            <p>🟠 URGENT</p>
        </div>
        <div class="stat-card">
            <h3>{len(high)}</h3>
            <p>🟡 HIGH</p>
        </div>
        <div class="stat-card">
            <h3>{len(all_docs)}</h3>
            <p>Tổng số</p>
        </div>
        <div class="stat-card stat-overdue">
            <h3>{len(overdue)}</h3>
            <p>⚠️ Quá hạn</p>
        </div>
    </div>

    <div class="section">
        <h2>🔴 Tài liệu CRITICAL ({len(critical)})</h2>
"""

    if critical:
        for doc in critical:
            days_left = doc.get("Days_To_Deadline", 0)
            days_str = f"{abs(days_left)} ngày trước" if days_left < 0 else f"{days_left} ngày nữa"
            html += f"""
        <div class="doc-item" style="border-left: 4px solid #c0392b;">
            <div class="doc-header">
                <span><span class="type-badge">{doc.get('_doc_type', '')}</span> <span class="doc-code">{doc.get('Doc_Code')}</span></span>
                <span class="badge badge-critical">{doc.get('Priority')}</span>
            </div>
            <div>{doc.get('Issue', {}).get('Summary', '')}</div>
            <div style="margin-top: 8px; font-size: 12px; color: #999;">
                Từ {doc.get('From_Party')} → Đến {doc.get('To_Party')} | Deadline: {doc.get('Deadline')} ({days_str})
            </div>
        </div>"""
    else:
        html += "<p>✅ Không có tài liệu CRITICAL.</p>"

    html += """
    </div>

    <div class="section">
        <h2>📊 Tất cả tài liệu</h2>
        <table>
            <thead>
                <tr>
                    <th>Loại</th>
                    <th>Mã</th>
                    <th>Mức</th>
                    <th>Từ → Đến</th>
                    <th>Vấn đề</th>
                    <th>Deadline</th>
                    <th>Còn lại</th>
                </tr>
            </thead>
            <tbody>
"""

    for doc in all_docs:
        days = doc.get("Days_To_Deadline", 0)
        if days < 0:
            days_str = f'<span class="overdue">{abs(days)} ngày</span>'
        elif days == 0:
            days_str = "Hôm nay!"
        else:
            days_str = f"{days} ngày"

        priority = doc.get("Priority", "NORMAL")
        priority_class = priority.lower()

        html += f"""
                <tr>
                    <td><span class="type-badge">{doc.get('_doc_type', '')}</span></td>
                    <td><strong>{doc.get('Doc_Code')}</strong></td>
                    <td><span class="badge badge-{priority_class}">{priority}</span></td>
                    <td>{doc.get('From_Party', '')[:10]} → {doc.get('To_Party', '')[:10]}</td>
                    <td>{doc.get('Issue', {}).get('Summary', '')[:50]}...</td>
                    <td>{doc.get('Deadline')}</td>
                    <td>{days_str}</td>
                </tr>
"""

    html += """
            </tbody>
        </table>
    </div>
</body>
</html>"""

    return html


def print_dashboard_text(registry):
    """In dashboard ra console (text mode)."""

    all_docs = collect_all_docs(registry)
    stats = registry.get("statistics", {})

    print(f"\n╔{'═' * 90}╗")
    print(f"║ TECHNICAL DOCUMENT DASHBOARD - {registry.get('project_name', 'Project')}".ljust(91) + "║")
    print(f"╠{'═' * 90}╣")

    # Stats by type
    by_type = {}
    for doc in all_docs:
        dtype = doc.get("_doc_type", "UNKNOWN")
        by_type[dtype] = by_type.get(dtype, 0) + 1

    type_str = " | ".join([f"{k}: {v}" for k, v in sorted(by_type.items())])
    print(f"║ {type_str}".ljust(91) + "║")

    critical = len([d for d in all_docs if d.get("Priority") == "CRITICAL"])
    overdue = len([d for d in all_docs if d.get("Tracking", {}).get("Overdue", False)])
    print(f"║ Tổng: {len(all_docs)} | Critical: {critical} | Quá hạn: {overdue}".ljust(91) + "║")
    print(f"╠{'═' * 90}╣")

    # Critical section
    critical_docs = [d for d in all_docs if d.get("Priority") == "CRITICAL"]
    if critical_docs:
        print(f"║ 🔴 CRITICAL ({len(critical_docs)})".ljust(91) + "║")
        for doc in critical_docs[:5]:
            summary = doc.get("Issue", {}).get("Summary", "")[:50]
            print(f"║   • [{doc.get('_doc_type')}] {doc.get('Doc_Code')}: {summary}".ljust(91) + "║")
        print(f"╟{'─' * 90}╢")

    # All docs table
    print(f"║ {'Loại':<10} {'Mã':<22} {'Mức':<10} {'Deadline':<12} {'Còn lại':<10} ║")
    print(f"╟{'─' * 90}╢")

    for doc in all_docs[:20]:
        dtype = doc.get("_doc_type", "")[:8]
        code = doc.get("Doc_Code", "")[:20]
        priority_sym = doc.get("Priority_Symbol", "")
        priority = doc.get("Priority", "")[:8]
        deadline = doc.get("Deadline", "")[:10]
        days = doc.get("Days_To_Deadline", 0)

        if days < 0:
            days_str = f"{abs(days)}d!!"
        elif days == 0:
            days_str = "Hnay!"
        else:
            days_str = f"{days}d"

        print(f"║ {dtype:<10} {code:<22} {priority_sym}{priority:<9} {deadline:<12} {days_str:<10} ║")

    if len(all_docs) > 20:
        print(f"║ ... và {len(all_docs) - 20} tài liệu khác".ljust(91) + "║")

    print(f"╚{'═' * 90}╝")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SKILL_RFI - Document Dashboard")
    parser.add_argument("--export", help="Export ra HTML file")
    parser.add_argument("--text", action="store_true", help="Chế độ text (console)")

    args = parser.parse_args()

    registry = load_registry()
    if not registry:
        print("❌ Registry not found. Chạy document_generator.py trước.")
        sys.exit(1)

    if args.text:
        print_dashboard_text(registry)
    elif args.export:
        html = generate_dashboard_html(registry)
        with open(args.export, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"✅ Dashboard exported: {args.export}")
    else:
        print_dashboard_text(registry)
        print(f"\n💡 Export HTML: python rfi_dashboard.py --export dashboard.html")
