
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

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import argparse
import sys

# Fix Unicode issue on Windows console
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

@with_error_handling
def draw_i_beam(output_path, h=300, b=150, tw=6.5, tf=9):
    """
    Vẽ mặt cắt dầm thép chữ I theo kích thước cụ thể.
    """
    fig, ax = plt.subplots(figsize=(6, 8))
    
    # Thiết lập tỷ lệ 1:1
    ax.set_aspect('equal')
    
    # Tính toán tọa độ các thành phần (gốc tọa độ tại tâm dầm)
    # Bản bụng (Web)
    web = patches.Rectangle((-tw/2, -h/2 + tf), tw, h - 2*tf, linewidth=1, edgecolor='blue', facecolor='skyblue', hatch='//')
    # Bản cánh trên (Top Flange)
    top_flange = patches.Rectangle((-b/2, h/2 - tf), b, tf, linewidth=1, edgecolor='blue', facecolor='skyblue', hatch='//')
    # Bản cánh dưới (Bottom Flange)
    bot_flange = patches.Rectangle((-b/2, -h/2), b, tf, linewidth=1, edgecolor='blue', facecolor='skyblue', hatch='//')
    
    ax.add_patch(web)
    ax.add_patch(top_flange)
    ax.add_patch(bot_flange)
    
    # Đánh kích thước (Dimensioning)
    # Chiều cao h
    ax.annotate(f'h = {h}mm', xy=(b/2 + 20, 0), xycoords='data', ha='left', va='center', fontsize=10)
    ax.annotate('', xy=(b/2 + 10, h/2), xytext=(b/2 + 10, -h/2), arrowprops=dict(arrowstyle='<->', color='red'))
    
    # Chiều rộng b
    ax.annotate(f'b = {b}mm', xy=(0, h/2 + 20), xycoords='data', ha='center', va='bottom', fontsize=10)
    ax.annotate('', xy=(-b/2, h/2 + 10), xytext=(b/2, h/2 + 10), arrowprops=dict(arrowstyle='<->', color='red'))
    
    # Chiều dày bản bụng tw
    ax.annotate(f'tw={tw}', xy=(0, 0), xytext=(tw/2 + 30, 0), arrowprops=dict(arrowstyle='->', color='black'), ha='left', va='center')
    
    # Chiều dày bản cánh tf
    ax.annotate(f'tf={tf}', xy=(b/2, h/2 - tf/2), xytext=(b/2 + 30, h/2 - tf/2), arrowprops=dict(arrowstyle='->', color='black'), ha='left', va='center')

    # Cài đặt giới hạn đồ thị
    padding = max(h, b) * 0.3
    ax.set_xlim(-b/2 - padding, b/2 + padding)
    ax.set_ylim(-h/2 - padding, h/2 + padding)
    
    # Ẩn trục tọa độ
    ax.axis('off')
    
    plt.title(f"Mặt Cắt Dầm I-{h}x{b}x{tw}x{tf}", pad=20, fontsize=14, fontweight='bold')
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✅ Đã xuất ảnh mặt cắt thành công tại: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Vẽ mặt cắt dầm I bằng Matplotlib")
    parser.add_argument("--out", type=str, required=True, help="Đường dẫn xuất file ảnh (.png)")
    parser.add_argument("--h", type=float, default=300, help="Chiều cao dầm")
    parser.add_argument("--b", type=float, default=150, help="Chiều rộng cánh")
    parser.add_argument("--tw", type=float, default=6.5, help="Độ dày bụng")
    parser.add_argument("--tf", type=float, default=9, help="Độ dày cánh")
    args = parser.parse_args()
    
    draw_i_beam(args.out, args.h, args.b, args.tw, args.tf)
