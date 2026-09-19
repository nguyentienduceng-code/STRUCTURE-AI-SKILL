
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
draw_comparison_chart.py — Ve bieu do radar + bar chart so sanh phuong an

Su dung:
  python draw_comparison_chart.py --out sosanh.png --json data.json

  File JSON mau:
  {
    "title": "SO SANH PHUONG AN KET CAU SAN",
    "categories": ["Chiu luc", "CP vat lieu", "CP nhan cong", "Tien do", "Rui ro", "Bao tri", "My quan", "TCVN"],
    "weights": [20, 15, 10, 15, 10, 10, 10, 10],
    "plans": {
      "PA1 - San BTCT": [4, 3, 4, 4, 4, 4, 3, 5],
      "PA2 - San thep": [5, 4, 3, 3, 3, 5, 5, 5],
      "PA3 - San nhe": [3, 5, 5, 5, 4, 3, 4, 5]
    }
  }

Tinh nang:
  - Ve bieu do radar (spider chart) so sanh truc quan cac phuong an
  - Ve bar chart tong diem gia quyen
  - Mau sac tu dong cho moi phuong an
  - Xuat file .png chat luong cao (300 DPI)
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import argparse
import json
import sys
import os

# Fix Unicode issue on Windows console
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Mau sac cho cac phuong an
PLAN_COLORS = [
    '#E74C3C',  # Do
    '#2980B9',  # Xanh duong
    '#27AE60',  # Xanh la
    '#F39C12',  # Cam
    '#8E44AD',  # Tim
    '#1ABC9C',  # Xanh ngoc
]


@with_error_handling
def draw_comparison(output_path, data):
    """
    Ve bieu do radar + bar chart so sanh phuong an.

    Args:
        output_path: Duong dan xuat file anh
        data: Dict chua categories, weights, plans
    """
    title = data.get("title", "SO SANH PHUONG AN")
    categories = data["categories"]
    weights = data.get("weights", [100 / len(categories)] * len(categories))
    plans = data["plans"]

    n_cats = len(categories)
    plan_names = list(plans.keys())
    n_plans = len(plan_names)

    # Tinh diem gia quyen cho moi phuong an
    weighted_scores = {}
    for name, scores in plans.items():
        total = sum(s * w for s, w in zip(scores, weights)) / sum(weights)
        weighted_scores[name] = round(total, 2)

    # === TAO HINH VE 2 PANEL ===
    fig = plt.figure(figsize=(16, 9))
    fig.suptitle(title, fontsize=16, fontweight='bold', y=0.98)

    # Panel 1: Radar Chart
    ax1 = fig.add_subplot(121, polar=True)

    # Goc cho moi category
    angles = np.linspace(0, 2 * np.pi, n_cats, endpoint=False).tolist()
    angles += angles[:1]  # Dong vong tron

    # Ve radar cho moi phuong an
    for idx, (name, scores) in enumerate(plans.items()):
        color = PLAN_COLORS[idx % len(PLAN_COLORS)]
        values = scores + scores[:1]
        ax1.plot(angles, values, 'o-', linewidth=2, label=f"{name} ({weighted_scores[name]})",
                color=color, markersize=6)
        ax1.fill(angles, values, alpha=0.1, color=color)

    # Cai dat radar
    ax1.set_xticks(angles[:-1])
    ax1.set_xticklabels(categories, fontsize=9, fontweight='bold')
    ax1.set_ylim(0, 5.5)
    ax1.set_yticks([1, 2, 3, 4, 5])
    ax1.set_yticklabels(['1', '2', '3', '4', '5'], fontsize=8, color='gray')
    ax1.set_title("BIEU DO RADAR", fontsize=12, fontweight='bold', pad=20)
    ax1.legend(loc='upper right', bbox_to_anchor=(1.3, 1.15), fontsize=9)

    # Them vong tron tham chieu
    for r in [1, 2, 3, 4, 5]:
        ax1.plot(angles, [r] * (n_cats + 1), '--', color='#CCCCCC', linewidth=0.5, alpha=0.5)

    # Panel 2: Bar Chart tong diem
    ax2 = fig.add_subplot(122)

    bars_x = np.arange(n_plans)
    bar_width = 0.5
    colors = [PLAN_COLORS[i % len(PLAN_COLORS)] for i in range(n_plans)]

    bars = ax2.bar(bars_x, list(weighted_scores.values()), bar_width,
                   color=colors, edgecolor='#2C3E50', linewidth=1.2, zorder=3)

    # Ghi diem tren cot
    for bar, score in zip(bars, weighted_scores.values()):
        ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.08,
                f"{score:.2f}", ha='center', va='bottom',
                fontsize=12, fontweight='bold', color='#2C3E50')

    # Danh dau phuong an tot nhat
    best_plan = max(weighted_scores, key=weighted_scores.get)
    best_idx = plan_names.index(best_plan)
    bars[best_idx].set_edgecolor('#FFD700')
    bars[best_idx].set_linewidth(3)
    ax2.text(best_idx, weighted_scores[best_plan] + 0.25,
            ">>> KHUYEN NGHI <<<", ha='center', va='bottom',
            fontsize=10, fontweight='bold', color='#F39C12',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#FFF9E6', edgecolor='#F39C12'))

    ax2.set_xticks(bars_x)
    ax2.set_xticklabels(plan_names, fontsize=10, fontweight='bold')
    ax2.set_ylabel("Diem gia quyen (Max = 5.0)", fontsize=10, fontweight='bold')
    ax2.set_ylim(0, max(weighted_scores.values()) + 0.8)
    ax2.set_title("TONG DIEM GIA QUYEN", fontsize=12, fontweight='bold', pad=15)
    ax2.grid(axis='y', alpha=0.3, linestyle='--')
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)

    # Duong nguong tham chieu
    ax2.axhline(y=3.0, color='#E74C3C', linestyle='--', linewidth=1, alpha=0.5)
    ax2.text(n_plans - 0.5, 3.05, "Nguong chap nhan = 3.0", fontsize=8,
            color='#E74C3C', ha='right', style='italic')

    # --- Bang trong so (duoi hinh) ---
    weights_text = "TRONG SO: " + " | ".join(
        f"{cat}: {w}%" for cat, w in zip(categories, weights)
    )
    fig.text(0.5, 0.01, weights_text, ha='center', fontsize=8.5, family='monospace',
             bbox=dict(boxstyle='round', facecolor='#F0F0F0', edgecolor='#CCCCCC'))

    plt.tight_layout(rect=[0, 0.04, 1, 0.94])
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"\u2705 Da xuat bieu do so sanh phuong an: {output_path}")

    # In ket qua ra console
    print(f"\n{'='*50}")
    print(f"KET QUA DANH GIA DA TIEU CHI:")
    print(f"{'='*50}")
    for name, score in sorted(weighted_scores.items(), key=lambda x: -x[1]):
        marker = " >>> KHUYEN NGHI" if name == best_plan else ""
        print(f"  {name}: {score:.2f}/5.00{marker}")
    print(f"{'='*50}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Ve bieu do radar + bar chart so sanh phuong an",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Vi du:
  python draw_comparison_chart.py --out sosanh.png --json data.json

  Cau truc file JSON:
  {
    "title": "SO SANH PHUONG AN",
    "categories": ["Tieu chi 1", "Tieu chi 2", ...],
    "weights": [20, 15, ...],
    "plans": {
      "PA1": [4, 3, ...],
      "PA2": [5, 4, ...]
    }
  }
        """
    )
    parser.add_argument("--out", required=True, help="Duong dan xuat file anh (.png)")
    parser.add_argument("--json", required=True, help="Duong dan file JSON chua du lieu")

    args = parser.parse_args()

    # Doc file JSON
    if not os.path.exists(args.json):
        print(f"\u274c Khong tim thay file JSON: {args.json}")
        sys.exit(1)

    with open(args.json, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Validate
    if "categories" not in data or "plans" not in data:
        print("\u274c File JSON phai co 'categories' va 'plans'")
        sys.exit(1)

    draw_comparison(args.out, data)
