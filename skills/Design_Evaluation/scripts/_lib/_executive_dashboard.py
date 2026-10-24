"""
_executive_dashboard.py — Executive Dashboard block cho reports.

Tạo dashboard tóm tắt ở đầu báo cáo cho Management audience:
- Project status badge
- Key metrics: Δ Cost, Schedule Impact, NLA Efficiency
- Critical issues count
- Call to action

Cung cấp:
- render_executive_dashboard_md(data) → markdown string
- render_executive_dashboard_html(data) → HTML block
- render_executive_dashboard_docx(doc, data) → DOCX section

Updated: 2026-08-31 — Phase A of Reporting Upgrade v4.0
"""

import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
from typing import Optional, Dict, List


# ════════════════════════════════════════════════════════════════════════════
# MARKDOWN RENDERER
# ════════════════════════════════════════════════════════════════════════════

def render_executive_dashboard_md(data: dict) -> str:
    """
    Render Executive Dashboard as Markdown block.

    Input schema:
        {
            'project_name': str,
            'date': str,
            'status': 'ON_TRACK' | 'AT_RISK' | 'DELAYED' | 'CRITICAL',
            'metrics': {
                'cost_delta_pct': float,        # -10.5 = giảm 10.5%
                'cost_delta_abs': float,         # VND
                'schedule_impact_days': float,  # +5 = chậm 5 ngày
                'nla_efficiency_pct': float,     # 92.5%
                'critical_issues': int,
                'open_rfis': int,
            },
            'top_risks': [str, str, str],
            'call_to_action': str,
        }
    """
    project_name = data.get('project_name', 'DỰ ÁN')
    date_str = data.get('date', '—')
    status = data.get('status', 'ON_TRACK')
    metrics = data.get('metrics', {})
    risks = data.get('top_risks', [])
    cta = data.get('call_to_action', '')

    status_emojis = {
        'ON_TRACK': '✅',
        'AT_RISK': '⚠️',
        'DELAYED': '🟠',
        'CRITICAL': '🔴',
    }

    md = []
    md.append('# 📊 EXECUTIVE DASHBOARD')
    md.append(f'**{project_name}** | Ngày: {date_str}')
    md.append('')
    md.append(f'## Trạng thái: {status_emojis.get(status, "❓")} {status}')
    md.append('')

    md.append('## Chỉ số Quan trọng (KPI)')
    md.append('')
    md.append('| Chỉ số | Giá trị | Đánh giá |')
    md.append('|--------|---------|----------|')

    cost_delta = metrics.get('cost_delta_pct', 0)
    cost_eval = '✅ Trong budget' if cost_delta <= 0 else f'⚠️ Vượt {cost_delta:.1f}%'
    md.append(
        f'| Δ Chi phí ({metrics.get("cost_delta_abs", 0):+,.0f} ₫) | '
        f'{cost_delta:+.1f}% | {cost_eval} |'
    )

    schedule = metrics.get('schedule_impact_days', 0)
    schedule_eval = '✅ Đúng tiến độ' if schedule <= 0 else f'⚠️ Chậm {schedule:.0f} ngày'
    md.append(f'| Δ Tiến độ | {schedule:+.0f} ngày | {schedule_eval} |')

    nla = metrics.get('nla_efficiency_pct', 0)
    nla_eval = '✅ Tốt' if nla >= 85 else '⚠️ Cần xem xét'
    md.append(f'| Hiệu quả NLA | {nla:.1f}% | {nla_eval} |')

    crit_issues = metrics.get('critical_issues', 0)
    crit_eval = '✅ Ổn' if crit_issues == 0 else f'🔴 Cần xử lý'
    md.append(f'| Vấn đề Critical | {crit_issues} | {crit_eval} |')

    open_rfis = metrics.get('open_rfis', 0)
    rfis_eval = '✅ Ít' if open_rfis <= 3 else '⚠️ Nhiều'
    md.append(f'| RFI đang mở | {open_rfis} | {rfis_eval} |')

    md.append('')

    if risks:
        md.append('## 🎯 Top 3 Rủi ro')
        md.append('')
        for i, risk in enumerate(risks[:3], 1):
            md.append(f'{i}. {risk}')
        md.append('')

    if cta:
        md.append(f"## 👉 KẾ HOẠCH HÀNH ĐỘNG")
        md.append('')
        md.append(f"> **{cta}**")
        md.append('')

    return '\n'.join(md)


# ════════════════════════════════════════════════════════════════════════════
# HTML RENDERER
# ════════════════════════════════════════════════════════════════════════════

def render_executive_dashboard_html(data: dict) -> str:
    """Render Executive Dashboard as HTML block."""
    project_name = data.get('project_name', 'DỰ ÁN')
    date_str = data.get('date', '—')
    status = data.get('status', 'ON_TRACK')
    metrics = data.get('metrics', {})
    risks = data.get('top_risks', [])
    cta = data.get('call_to_action', '')

    status_colors = {
        'ON_TRACK': '#27AE60',
        'AT_RISK': '#F39C12',
        'DELAYED': '#E74C3C',
        'CRITICAL': '#C0392B',
    }
    status_emojis = {
        'ON_TRACK': '✅',
        'AT_RISK': '⚠️',
        'DELAYED': '🟠',
        'CRITICAL': '🔴',
    }

    cost_delta = metrics.get('cost_delta_pct', 0)
    schedule = metrics.get('schedule_impact_days', 0)
    nla = metrics.get('nla_efficiency_pct', 0)
    crit_issues = metrics.get('critical_issues', 0)

    html = f"""
<div class="executive-dashboard" style="
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    color: white; padding: 30px; border-radius: 12px;
    margin-bottom: 25px; font-family: 'Segoe UI', Arial, sans-serif;
">
  <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid rgba(255,255,255,0.2); padding-bottom: 15px; margin-bottom: 20px;">
    <div>
      <h2 style="margin: 0; font-size: 22px;">📊 Executive Dashboard</h2>
      <p style="margin: 5px 0 0 0; opacity: 0.85;">{project_name} — {date_str}</p>
    </div>
    <div style="background: {status_colors.get(status, '#666')}; padding: 8px 20px; border-radius: 20px; font-weight: bold;">
      {status_emojis.get(status, '')} {status}
    </div>
  </div>

  <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 15px;">
    <div style="background: rgba(255,255,255,0.1); padding: 18px; border-radius: 8px;">
      <div style="font-size: 12px; opacity: 0.8;">Δ CHI PHÍ</div>
      <div style="font-size: 24px; font-weight: bold; margin-top: 6px;">{cost_delta:+.1f}%</div>
      <div style="font-size: 11px; opacity: 0.7;">{metrics.get('cost_delta_abs', 0):+,.0f} ₫</div>
    </div>
    <div style="background: rgba(255,255,255,0.1); padding: 18px; border-radius: 8px;">
      <div style="font-size: 12px; opacity: 0.8;">Δ TIẾN ĐỘ</div>
      <div style="font-size: 24px; font-weight: bold; margin-top: 6px;">{schedule:+.0f} ngày</div>
      <div style="font-size: 11px; opacity: 0.7;">so với kế hoạch</div>
    </div>
    <div style="background: rgba(255,255,255,0.1); padding: 18px; border-radius: 8px;">
      <div style="font-size: 12px; opacity: 0.8;">HIỆU QUẢ NLA</div>
      <div style="font-size: 24px; font-weight: bold; margin-top: 6px;">{nla:.1f}%</div>
    </div>
    <div style="background: rgba(255,255,255,0.1); padding: 18px; border-radius: 8px;">
      <div style="font-size: 12px; opacity: 0.8;">CRITICAL ISSUES</div>
      <div style="font-size: 24px; font-weight: bold; margin-top: 6px;">{crit_issues}</div>
    </div>
  </div>
"""

    if risks:
        html += """
  <div style="margin-top: 20px; padding: 15px; background: rgba(231,76,60,0.15); border-left: 4px solid #E74C3C; border-radius: 6px;">
    <strong>🎯 Top Rủi ro:</strong>
    <ul style="margin: 8px 0 0 20px; padding: 0;">
"""
        for risk in risks[:3]:
            html += f'      <li>{risk}</li>\n'
        html += "    </ul>\n  </div>\n"

    if cta:
        html += f"""
  <div style="margin-top: 20px; padding: 15px; background: rgba(39,174,96,0.2); border-left: 4px solid #27AE60; border-radius: 6px;">
    <strong>👉 KẾ HOẠCH HÀNH ĐỘNG:</strong> {cta}
  </div>
"""

    html += "</div>\n"
    return html


# ════════════════════════════════════════════════════════════════════════════
# DOCX RENDERER
# ════════════════════════════════════════════════════════════════════════════

def render_executive_dashboard_docx(doc, data: dict):
    """
    Render Executive Dashboard as DOCX section.
    Sử dụng _docx_helpers để đảm bảo style consistency.
    """
    from _lib._docx_helpers import (
        add_h, add_p, add_callout, build_table,
        COLOR_PRIMARY, COLOR_ACCENT, COLOR_WARN_BORDER, COLOR_CRITICAL,
        COLOR_SUCCESS
    )

    project_name = data.get('project_name', 'DỰ ÁN')
    date_str = data.get('date', '—')
    status = data.get('status', 'ON_TRACK')
    metrics = data.get('metrics', {})
    risks = data.get('top_risks', [])
    cta = data.get('call_to_action', '')

    status_kind = {
        'ON_TRACK': 'success',
        'AT_RISK': 'warn',
        'DELAYED': 'warn',
        'CRITICAL': 'critical',
    }.get(status, 'info')

    # Banner
    add_h(doc, '📊 EXECUTIVE DASHBOARD', lv=1, color=COLOR_PRIMARY)
    add_p(doc, f'{project_name} — {date_str}', bold=True, color=COLOR_ACCENT, sa=8)

    # Status
    add_callout(doc, f'Trạng thái: {status}', kind=status_kind)

    # Metrics table
    add_h(doc, 'Chỉ số Quan trọng (KPI)', lv=2)

    cost_delta = metrics.get('cost_delta_pct', 0)
    schedule = metrics.get('schedule_impact_days', 0)
    nla = metrics.get('nla_efficiency_pct', 0)
    crit_issues = metrics.get('critical_issues', 0)
    open_rfis = metrics.get('open_rfis', 0)

    rows = [
        ['Δ Chi phí', f'{cost_delta:+.1f}% ({metrics.get("cost_delta_abs", 0):+,.0f} ₫)',
         '✅ Trong budget' if cost_delta <= 0 else f'⚠️ Vượt {cost_delta:.1f}%'],
        ['Δ Tiến độ', f'{schedule:+.0f} ngày',
         '✅ Đúng tiến độ' if schedule <= 0 else f'⚠️ Chậm {schedule:.0f} ngày'],
        ['Hiệu quả NLA', f'{nla:.1f}%', '✅ Tốt' if nla >= 85 else '⚠️ Cần xem xét'],
        ['Vấn đề Critical', f'{crit_issues}',
         '✅ Ổn' if crit_issues == 0 else '🔴 Cần xử lý'],
        ['RFI đang mở', f'{open_rfis}',
         '✅ Ít' if open_rfis <= 3 else '⚠️ Nhiều'],
    ]
    build_table(doc, ['Chỉ số', 'Giá trị', 'Đánh giá'], rows,
                col_widths_cm=[5.0, 6.0, 6.0])

    # Top risks
    if risks:
        add_h(doc, '🎯 Top 3 Rủi ro', lv=2)
        for i, risk in enumerate(risks[:3], 1):
            add_p(doc, f'{i}. {risk}', size=10.5, sa=2)

    # Call to action
    if cta:
        add_callout(doc, f'👉 KẾ HOẠCH HÀNH ĐỘNG: {cta}', kind='info')

    return doc