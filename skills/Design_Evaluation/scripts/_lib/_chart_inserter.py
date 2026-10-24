"""
_chart_inserter.py — Auto-insert matplotlib charts vào DOCX/MD.

Cung cấp:
- add_chart_to_docx(doc, chart_path, caption, width_cm)
- add_chart_to_md(md_text, chart_path, caption)
- generate_comparison_chart(json_data, out_path)
- generate_progress_chart(data, out_path)
- generate_eta_heatmap(items, out_path)

Updated: 2026-08-31 — Phase A of Reporting Upgrade v4.0
"""

import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
import os
from typing import List, Dict, Optional, Union

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np


# ════════════════════════════════════════════════════════════════════════════
# DOCX CHART INSERTION
# ════════════════════════════════════════════════════════════════════════════

def add_chart_to_docx(doc, chart_path: str, caption: Optional[str] = None,
                      width_cm: float = 15.0):
    """
    Add chart image vào DOCX document.
    Auto-import _docx_helpers để tránh circular import.
    """
    from _lib._docx_helpers import add_img, add_image_caption

    if not os.path.exists(chart_path):
        return doc.add_paragraph(
            f'[Chart không tìm thấy: {chart_path}]'
        )

    add_img(doc, chart_path, w=width_cm, caption=caption)
    return doc


# ════════════════════════════════════════════════════════════════════════════
# MARKDOWN CHART INSERTION
# ════════════════════════════════════════════════════════════════════════════

def add_chart_to_md(md_text: str, chart_path: str, caption: Optional[str] = None,
                    position: str = 'append') -> str:
    """
    Add chart reference vào Markdown text.
    Returns updated markdown.
    """
    if not os.path.exists(chart_path):
        ref = f'\n> ⚠️ Chart không tìm thấy: {chart_path}\n'
    else:
        rel_path = os.path.basename(chart_path)
        ref = f'\n![{caption or "Chart"}]({rel_path})\n'
        if caption:
            ref += f'*{caption}*\n'

    if position == 'prepend':
        return ref + '\n' + md_text
    return md_text + ref


# ════════════════════════════════════════════════════════════════════════════
# CHART GENERATORS
# ════════════════════════════════════════════════════════════════════════════

def generate_comparison_chart(categories: List[str], plans: Dict[str, List[float]],
                              out_path: str, chart_type: str = 'radar',
                              title: str = ''):
    """
    Generate comparison chart (radar hoặc bar).
    Schema:
        categories: ['Cost', 'Schedule', 'Quality', 'Safety', 'Carbon']
        plans: {
            'Plan A': [85, 90, 80, 95, 70],
            'Plan B': [75, 85, 90, 80, 85],
        }
    """
    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)

    if chart_type == 'radar':
        _draw_radar(ax, categories, plans)
    else:
        _draw_grouped_bar(ax, categories, plans)

    if title:
        ax.set_title(title, fontsize=14, fontweight='bold', color='#1C3557', pad=15)

    plt.tight_layout()
    plt.savefig(out_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    return out_path


def _draw_radar(ax, categories, plans):
    """Draw radar chart."""
    N = len(categories)
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]

    ax = plt.subplot(111, polar=True)
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)

    plt.xticks(angles[:-1], categories, size=10)

    ax.set_rlabel_position(0)
    plt.yticks([20, 40, 60, 80, 100], ['20', '40', '60', '80', '100'],
               color='grey', size=8)
    plt.ylim(0, 100)

    colors = ['#1C3557', '#E74C3C', '#27AE60', '#F39C12', '#9B59B6']

    for i, (name, values) in enumerate(plans.items()):
        vals = values + values[:1]
        color = colors[i % len(colors)]
        ax.plot(angles, vals, linewidth=2, linestyle='solid', label=name, color=color)
        ax.fill(angles, vals, alpha=0.15, color=color)

    plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))


def _draw_grouped_bar(ax, categories, plans):
    """Draw grouped bar chart."""
    n_plans = len(plans)
    x = np.arange(len(categories))
    width = 0.8 / max(n_plans, 1)

    colors = ['#1C3557', '#E74C3C', '#27AE60', '#F39C12', '#9B59B6']

    for i, (name, values) in enumerate(plans.items()):
        offset = (i - (n_plans - 1) / 2) * width
        color = colors[i % len(colors)]
        rects = ax.bar(x + offset, values, width, label=name, color=color, alpha=0.85)
        # Value labels on top
        for rect in rects:
            height = rect.get_height()
            ax.annotate(f'{height:.0f}',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3), textcoords='offset points',
                        ha='center', va='bottom', fontsize=8)

    ax.set_xticks(x)
    ax.set_xticklabels(categories, rotation=15, ha='right')
    ax.set_ylim(0, max([max(v) for v in plans.values()]) * 1.2 + 10)
    ax.legend(loc='best')
    ax.grid(axis='y', alpha=0.3)


def generate_progress_chart(items: List[Dict], out_path: str, title: str = ''):
    """
    Generate progress bar chart.
    items: [{'name': 'Dầm tầng 1', 'progress': 100, 'color': 'green'}, ...]
    """
    fig, ax = plt.subplots(figsize=(10, max(4, len(items) * 0.5)), dpi=300)

    names = [item.get('name', '') for item in items]
    progresses = [item.get('progress', 0) for item in items]
    colors_map = {
        'green': '#27AE60', 'yellow': '#F39C12', 'red': '#E74C3C',
        'complete': '#27AE60', 'in-progress': '#F39C12', 'pending': '#95A5A6',
        'critical': '#E74C3C'
    }
    bar_colors = [colors_map.get(
        item.get('color', item.get('status', 'pending')).lower(),
        '#95A5A6'
    ) for item in items]

    y_pos = np.arange(len(names))
    bars = ax.barh(y_pos, progresses, color=bar_colors, alpha=0.85)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(names)
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xlabel('Tiến độ (%)')
    ax.grid(axis='x', alpha=0.3)

    # Value labels
    for bar, prog in zip(bars, progresses):
        ax.text(bar.get_width() + 2, bar.get_y() + bar.get_height() / 2,
                f'{prog:.0f}%', va='center', fontsize=9)

    if title:
        ax.set_title(title, fontsize=14, fontweight='bold', color='#1C3557', pad=15)

    plt.tight_layout()
    plt.savefig(out_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    return out_path


def generate_eta_heatmap(items: List[Dict], out_path: str, title: str = 'η Heatmap'):
    """
    Generate η heatmap (utilization ratio).
    items: [{'name': 'D1', 'eta_M': 0.85, 'eta_V': 0.65, 'eta_LTB': 0.92}, ...]
    """
    if not items:
        return None

    keys = [k for k in items[0].keys() if k.startswith('eta_') or k == 'name']
    eta_keys = [k for k in keys if k.startswith('eta_')]
    if not eta_keys:
        return None

    names = [item.get('name', f'#{i}') for i, item in enumerate(items)]
    data = np.array([[item.get(k, 0) for k in eta_keys] for item in items])

    fig, ax = plt.subplots(figsize=(10, max(4, len(items) * 0.4)), dpi=300)

    im = ax.imshow(data, cmap='RdYlGn_r', aspect='auto', vmin=0, vmax=1.2)

    ax.set_xticks(np.arange(len(eta_keys)))
    ax.set_xticklabels([k.replace('eta_', 'η_') for k in eta_keys])
    ax.set_yticks(np.arange(len(names)))
    ax.set_yticklabels(names)

    # Annotations
    for i in range(len(names)):
        for j in range(len(eta_keys)):
            value = data[i, j]
            color = 'white' if value > 0.8 or value < 0.3 else 'black'
            ax.text(j, i, f'{value:.2f}', ha='center', va='center',
                    color=color, fontsize=9)

    ax.set_title(title, fontsize=14, fontweight='bold', color='#1C3557', pad=15)
    plt.colorbar(im, ax=ax, label='η (utilization)')

    plt.tight_layout()
    plt.savefig(out_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    return out_path


def generate_cost_breakdown_chart(items: List[Dict], out_path: str,
                                  title: str = 'Phân bổ Chi phí'):
    """
    Generate cost breakdown chart (pie + bar).
    items: [{'category': 'Thép', 'amount': 1200000000}, ...]
    """
    if not items:
        return None

    categories = [item.get('category', '') for item in items]
    amounts = [item.get('amount', 0) for item in items]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6), dpi=300,
                                    gridspec_kw={'width_ratios': [1, 1.2]})

    # Pie chart
    colors = plt.cm.Set3(np.linspace(0, 1, len(categories)))
    wedges, texts, autotexts = ax1.pie(
        amounts, labels=categories, autopct='%1.1f%%',
        colors=colors, startangle=90, pctdistance=0.85
    )
    for autotext in autotexts:
        autotext.set_color('black')
        autotext.set_fontsize(9)
    ax1.set_title('Tỷ lệ Chi phí', fontsize=12, fontweight='bold')

    # Bar chart
    sorted_indices = np.argsort(amounts)[::-1]
    sorted_categories = [categories[i] for i in sorted_indices]
    sorted_amounts = [amounts[i] for i in sorted_indices]

    y_pos = np.arange(len(sorted_categories))
    bars = ax2.barh(y_pos, sorted_amounts, color=[colors[i] for i in sorted_indices])
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(sorted_categories)
    ax2.invert_yaxis()
    ax2.set_xlabel('Số tiền (₫)')
    ax2.xaxis.set_major_formatter(
        plt.FuncFormatter(lambda x, p: f'{x/1e6:.0f}M')
    )
    ax2.grid(axis='x', alpha=0.3)

    for bar, amt in zip(bars, sorted_amounts):
        ax2.text(bar.get_width(), bar.get_y() + bar.get_height() / 2,
                 f'  {amt/1e6:.0f}M ₫', va='center', fontsize=9)

    ax2.set_title('Chi tiết Chi phí', fontsize=12, fontweight='bold')

    fig.suptitle(title, fontsize=14, fontweight='bold', color='#1C3557')

    plt.tight_layout()
    plt.savefig(out_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    return out_path