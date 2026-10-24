# -*- coding: utf-8 -*-
"""
Technical_Illustrator - Drawing Standards Library
============================================

Quy chuẩn vẽ kỹ thuật theo TCVN cho Việt Nam.

Nguồn sự thật: TCVN 5574:2018, TCVN 5575:2024, TCVN 9386:2025

Usage:
    from modules.drawing_standards import DrawingStandards, TCVN_COLORS, TCVN_HATCH

    DrawingStandards.apply_rc_style(ax)
    DrawingStandards.add_dimension(ax, ...)
    DrawingStandards.add_title_block(fig, ...)
"""

import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.lines import Line2D
import numpy as np
from typing import Tuple, Optional, Dict, Any
import os

# =============================================================================
# CONSTANTS - TCVN Drawing Standards
# =============================================================================

# Màu sắc theo quy chuẩn Việt Nam
TCVN_COLORS = {
    # Bê tông cốt thép
    "concrete": "#B8B8B8",           # Xám bê tông
    "concrete_light": "#D5D5D5",    # Bê tông sáng
    "concrete_dark": "#8C8C8C",      # Bê tông tối

    # Cốt thép
    "rebar": "#C0392B",            # Đỏ thép
    "rebar_dark": "#922B21",         # Thép đậm
    "stirrup": "#E74C3C",           # Đai thép

    # Thép kết cấu
    "steel": "#2C3E50",             # Xanh đen thép
    "steel_light": "#34495E",         # Thép nhạt
    "bolt": "#7F8C8D",              # Xám bulông
    "weld": "#F39C12",               # Vàng đường hàn

    # Đường kích thước
    "dimension": "#2980B9",           # Xanh dương đường kích thước
    "dimension_alt": "#27AE60",       # Xanh lá (alternate)
    "extension_line": "#7F8C8D",      # Xám đường kéo dài

    # Đường vẽ
    "section_line": "#1A1A1A",       # Đen đậm (đường cắt)
    "outline": "#2C3E50",            # Đường bao
    "hidden": "#95A5A6",             # Đường khuất

    # Đất nền
    "soil": "#C4A35A",              # Nâu đất
    "soil_dark": "#8B7355",          # Đất đậm
    "backfill": "#D4A574",            # Đất đắp

    # Lớp lót
    "bedding": "#BDC3C7",            # Xám lớp lót
    "formwork": "#F5CBA7",           # Cam ván khuôn

    # Annotation
    "annotation": "#8E44AD",          # Tím annotation
    "warning": "#E67E22",            # Cam cảnh báo
    "note": "#16A085",                # Xanh ngọc ghi chú
}

# Hatch patterns theo ANSI/AWS standards
TCVN_HATCH = {
    "concrete": "///",               # Gạch chéo 3 đường - bê tông
    "concrete_solid": "\\\\",         # Gạch chéo ngược - bê tông đặc
    "rebar": "...",                   # Chấm tròn - cốt thép
    "rebar_cross": "xxx",            # X đôi - lưới thép
    "soil": "..",                    # Chấm nhỏ - đất
    "backfill": "...",                # Chấm - đất đắp
    "bedding": "---",                # Đường ngang - lớp lót
    "formwork": "+++",               # Đường cộng - ván khuôn
    "weld": "+++",                  # Đường cộng - que hàn
    "grout": "...",
    "waterproofing": "///",
    "insulation": "\\\\\\",
    "wood": "|||",
}

# Font settings
FONT_SETTINGS = {
    "dimension": {
        "family": "DejaVu Sans",
        "size": 9,
        "weight": "bold",
    },
    "annotation": {
        "family": "DejaVu Sans",
        "size": 8,
        "weight": "normal",
    },
    "title": {
        "family": "DejaVu Sans",
        "size": 14,
        "weight": "bold",
    },
    "technical_note": {
        "family": "monospace",
        "size": 8,
        "weight": "normal",
    },
}

# Line width standards (mm equivalent)
LINE_WIDTH = {
    "outline": 1.2,               # Đường bao chính
    "section": 1.5,               # Đường cắt
    "dimension": 0.5,             # Đường kích thước
    "extension": 0.35,            # Đường kéo dài
    "hidden": 0.5,               # Đường khuất
    "center": 0.5,               # Đường tâm
    "hatch": 0.3,                # Đường hatch
}

# Dimension arrow size
ARROW_SIZE = 0.4  # Độ dài mũi tên (data units)

# Title block standard dimensions (relative to figure)
TITLE_BLOCK = {
    "height_ratio": 0.08,         # Chiều cao khung tên / tổng figure
    "left_width_ratio": 0.5,       # Chiều rộng ô trái
    "border_width": 1.5,          # Độ dày viền khung tên
    "border_color": "#2C3E50",     # Màu viền
    "fill_color": "#F5F5F5",       # Màu nền
}

# =============================================================================
# DRAWING STANDARDS CLASS
# =============================================================================

class DrawingStandards:
    """
    Class áp dụng quy chuẩn vẽ kỹ thuật TCVN.

    Usage:
        ds = DrawingStandards(ax)
        ds.apply_rc_style()
        ds.add_dimension(...)
    """

    def __init__(self, ax: plt.Axes = None):
        """Khởi tạo với axes option."""
        self.ax = ax
        if ax is not None:
            ax.set_aspect('equal')

    @staticmethod
    def apply_rc_style(ax: plt.Axes,
                      concrete_color: str = None,
                      rebar_color: str = None,
                      show_grid: bool = False):
        """
        Áp dụng style cho bản vẽ BTCT.

        Args:
            ax: Matplotlib axes
            concrete_color: Override màu bê tông
            rebar_color: Override màu cốt thép
            show_grid: Hiển thị lưới tham chiếu
        """
        ax.set_aspect('equal')

        if not show_grid:
            ax.axis('off')
        else:
            ax.grid(True, alpha=0.3, linestyle='--')

        # Set font
        plt.rcParams['font.family'] = 'DejaVu Sans'

    @staticmethod
    def draw_rect(
        ax: plt.Axes,
        x: float, y: float,
        width: float, height: float,
        element_type: str = "concrete",
        linewidth: float = 1.5,
        hatch: bool = True,
        hatch_color: str = None
    ) -> patches.Rectangle:
        """
        Vẽ hình chữ nhật theo tiêu chuẩn.

        Args:
            ax: Axes
            x, y: Tọa độ góc dưới-trái
            width, height: Kích thước
            element_type: "concrete" | "rebar" | "steel" | "soil" | ...
            linewidth: Độ dày đường viền
            hatch: Có hatch không
            hatch_color: Override màu hatch

        Returns:
            matplotlib.patches.Rectangle
        """
        color = TCVN_COLORS.get(element_type, "#808080")
        if hatch_color:
            color = hatch_color

        patch = patches.Rectangle(
            (x, y), width, height,
            linewidth=linewidth,
            edgecolor=TCVN_COLORS["section_line"],
            facecolor=TCVN_COLORS.get(f"{element_type}_light",
                                     TCVN_COLORS.get(element_type, "#B8B8B8")),
            hatch=TCVN_HATCH.get(element_type) if hatch else None,
            zorder=1
        )
        ax.add_patch(patch)
        return patch

    @staticmethod
    def draw_circle(
        ax: plt.Axes,
        cx: float, cy: float,
        radius: float,
        element_type: str = "rebar",
        linewidth: float = 0.8,
        fill: bool = True,
        zorder: int = 4
    ) -> plt.Circle:
        """
        Vẽ hình tròn (cho cốt thép).

        Args:
            cx, cy: Tọa độ tâm
            radius: Bán kính
            element_type: "rebar" | "bolt" | ...
            linewidth: Độ dày viền
            fill: Có tô màu không
            zorder: Layer order

        Returns:
            plt.Circle
        """
        circle = plt.Circle(
            (cx, cy), radius,
            fill=fill,
            facecolor=TCVN_COLORS.get(element_type, "#2C3E50"),
            edgecolor=TCVN_COLORS["section_line"],
            linewidth=linewidth,
            zorder=zorder
        )
        ax.add_patch(circle)
        return circle

    @staticmethod
    def add_dimension(
        ax: plt.Axes,
        start: Tuple[float, float],
        end: Tuple[float, float],
        text: str,
        offset: float = 15,
        side: str = "above",
        color: str = None,
        fontsize: float = 9
    ):
        """
        Thêm đường kích thước theo style TCVN.

        Args:
            ax: Axes
            start: (x1, y1) điểm bắt đầu
            end: (x2, y2) điểm kết thúc
            text: Text kích thước (VD: "b = 400")
            offset: Khoảng cách text tới đường kích thước
            side: "above" | "below" | "left" | "right"
            color: Override màu
            fontsize: Cỡ chữ
        """
        if color is None:
            color = TCVN_COLORS["dimension"]

        x1, y1 = start
        x2, y2 = end

        # Extension lines
        ext_offset = 5
        if side == "above":
            ax.plot([x1, x1], [y1, y1 + ext_offset], color=TCVN_COLORS["extension_line"], linewidth=LINE_WIDTH["extension"])
            ax.plot([x2, x2], [y2, y2 + ext_offset], color=TCVN_COLORS["extension_line"], linewidth=LINE_WIDTH["extension"])
        elif side == "below":
            ax.plot([x1, x1], [y1, y1 - ext_offset], color=TCVN_COLORS["extension_line"], linewidth=LINE_WIDTH["extension"])
            ax.plot([x2, x2], [y2, y2 - ext_offset], color=TCVN_COLORS["extension_line"], linewidth=LINE_WIDTH["extension"])

        # Dimension line with arrows
        ax.annotate('',
            xy=(x2, y2), xytext=(x1, y1),
            arrowprops=dict(
                arrowstyle='<->',
                color=color,
                lw=LINE_WIDTH["dimension"]
            )
        )

        # Text position
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2

        if side == "above":
            text_pos = (mid_x, mid_y + offset)
            ha, va = 'center', 'bottom'
        elif side == "below":
            text_pos = (mid_x, mid_y - offset)
            ha, va = 'center', 'top'
        elif side == "left":
            text_pos = (mid_x - offset, mid_y)
            ha, va = 'right', 'center'
        else:  # right
            text_pos = (mid_x + offset, mid_y)
            ha, va = 'left', 'center'

        ax.text(text_pos[0], text_pos[1], text,
                ha=ha, va=va,
                fontsize=fontsize,
                color=color,
                fontweight='bold')

    @staticmethod
    def add_dimension_radial(
        ax: plt.Axes,
        center: Tuple[float, float],
        start_angle: float,
        radius: float,
        text: str,
        offset: float = 20,
        color: str = None
    ):
        """
        Thêm dimension theo góc (cho tiết diện tròn).

        Args:
            center: (cx, cy) tâm
            start_angle: Góc bắt đầu (degrees)
            radius: Bán kính
            text: Text kích thước
            offset: Offset từ đường tròn
            color: Override màu
        """
        if color is None:
            color = TCVN_COLORS["dimension"]

        import math
        cx, cy = center
        angle_rad = math.radians(start_angle)

        # Điểm trên đường tròn
        px = cx + radius * math.cos(angle_rad)
        py = cy + radius * math.sin(angle_rad)

        # Vẽ đường kích thước
        ax.annotate('',
            xy=(px, py),
            xytext=(cx + (radius + offset) * math.cos(angle_rad),
                   cy + (radius + offset) * math.sin(angle_rad)),
            arrowprops=dict(arrowstyle='->', color=color, lw=LINE_WIDTH["dimension"])
        )

        # Text
        text_x = cx + (radius + offset * 1.5) * math.cos(angle_rad)
        text_y = cy + (radius + offset * 1.5) * math.sin(angle_rad)
        ax.text(text_x, text_y, text,
                ha='center', va='center',
                fontsize=9, color=color, fontweight='bold')

    @staticmethod
    def add_annotation(
        ax: plt.Axes,
        xy: Tuple[float, float],
        text: str,
        xytext: Tuple[float, float] = None,
        offset: Tuple[float, float] = (20, 0),
        color: str = None,
        box_style: str = "round,pad=0.3"
    ) -> None:
        """
        Thêm annotation (ghi chú kỹ thuật).

        Args:
            ax: Axes
            xy: (x, y) điểm cần annotate
            text: Nội dung ghi chú
            xytext: (x, y) vị trí text (None = tự tính từ offset)
            offset: (dx, dy) offset từ xy
            color: Override màu
            box_style: Style của bbox
        """
        if color is None:
            color = TCVN_COLORS["annotation"]

        if xytext is None:
            xytext = (xy[0] + offset[0], xy[1] + offset[1])

        ax.annotate(text,
            xy=xy, xytext=xytext,
            arrowprops=dict(
                arrowstyle='->',
                color=color,
                lw=0.8
            ),
            fontsize=8,
            color=color,
            fontweight='bold',
            bbox=dict(
                boxstyle=box_style,
                facecolor='#F5EEF8',
                edgecolor=color,
                alpha=0.9
            ),
            zorder=10
        )

    @staticmethod
    def add_title_block(
        fig: plt.Figure,
        project_name: str = "PROJECT NAME",
        drawing_title: str = "DRAWING TITLE",
        scale: str = "1:10",
        date: str = None,
        sheet: str = "1/1",
        author: str = "AI Assistant",
        location: str = "Góc dưới phải"
    ):
        """
        Thêm khung tên chuẩn A3/A4 vào figure.

        Args:
            fig: Matplotlib figure
            project_name: Tên dự án
            drawing_title: Tên bản vẽ
            scale: Tỷ lệ
            date: Ngày vẽ (None = hôm nay)
            sheet: Số thứ tự tờ
            author: Người vẽ
            location: "bottom_right" | "bottom_left" | "top_right" | "top_left"
        """
        if date is None:
            from datetime import datetime
            date = datetime.now().strftime("%d/%m/%Y")

        fig_width, fig_height = fig.get_size_inches()
        dpi = fig.dpi

        # Kích thước title block (inches)
        tb_height = 0.8  # ~20mm
        tb_width = fig_width

        # Vị trí
        if location == "bottom_right":
            tb_x, tb_y = 0, 0
            tb_ha = 'left'
        elif location == "bottom_left":
            tb_x, tb_y = 0, 0
            tb_ha = 'left'
        else:
            tb_x, tb_y = 0, 0
            tb_ha = 'left'

        # Tạo text box cho title block
        title_block_text = (
            f"{'─' * 60}\n"
            f"{'PROJECT:':<15} {project_name:<45} {'DATE:':>8} {date}\n"
            f"{'TITLE:':<15} {drawing_title:<45} {'SCALE:':>8} {scale}\n"
            f"{'DRAWN:':<15} {author:<45} {'SHEET:':>8} {sheet}\n"
            f"{'─' * 60}"
        )

        fig.text(tb_x + 0.02, tb_y + 0.01,
                title_block_text,
                fontsize=7,
                family='monospace',
                verticalalignment='bottom',
                horizontalalignment='left',
                bbox=dict(
                    boxstyle='square',
                    facecolor='#F8F8F8',
                    edgecolor='#CCCCCC',
                    linewidth=1
                )
        )

    @staticmethod
    def add_title_block_visual(
        fig: plt.Figure,
        ax: plt.Axes,
        project_name: str = "PROJECT",
        drawing_no: str = "KCL-01",
        title: str = "Mặt cắt dầm D1",
        scale: str = "1:10",
        unit: str = "mm",
        date: str = None,
        sheet: str = "1/1",
        designed_by: str = "AI",
        checked_by: str = "",
        approved_by: str = ""
    ):
        """
        Thêm khung tên visual (có bảng) vào góc figure.
        Đặt ở dưới cùng của axes.

        Args:
            fig: Figure
            ax: Axes (để tính vị trí)
            Các tham số khác như trên
        """
        if date is None:
            from datetime import datetime
            date = datetime.now().strftime("%d/%m/%Y")

        # Vị trí trong axes coordinates
        x0, y0 = ax.get_xlim()[0], ax.get_ylim()[0]
        x1, y1 = ax.get_xlim()[1], ax.get_ylim()[1]

        tb_height = (y1 - y0) * 0.12
        tb_y = y0 - tb_height * 0.3

        # Background
        tb_bg = patches.Rectangle(
            (x0 - (x1 - x0) * 0.02, tb_y - tb_height),
            (x1 - x0) * 1.04, tb_height * 1.5,
            linewidth=1.5,
            edgecolor=TCVN_COLORS["outline"],
            facecolor='#FAFAFA',
            zorder=100
        )
        ax.add_patch(tb_bg)

        # Lines
        ax.plot([x0, x1 + (x1 - x0) * 0.02], [tb_y, tb_y],
                color=TCVN_COLORS["outline"], linewidth=1.5, zorder=101)

        # Text boxes
        fontsize = min(8, (y1 - y0) * 0.015)

        # Row 1: Project & Drawing No
        ax.text(x0, tb_y - tb_height * 0.2, f"{project_name}",
                fontsize=fontsize, va='top', ha='left',
                fontweight='bold', color=TCVN_COLORS["outline"], zorder=102)
        ax.text(x1 + (x1 - x0) * 0.01, tb_y - tb_height * 0.2,
                f"No: {drawing_no}",
                fontsize=fontsize, va='top', ha='right',
                color=TCVN_COLORS["outline"], zorder=102)

        # Row 2: Title
        ax.text((x0 + x1) / 2, tb_y - tb_height * 0.7, title,
                fontsize=fontsize + 1, va='top', ha='center',
                fontweight='bold', color=TCVN_COLORS["outline"], zorder=102)

        # Row 3: Scale, Date, Sheet
        ax.text(x0, tb_y - tb_height * 1.2,
                f"Scale: {scale}  |  Unit: {unit}  |  Date: {date}",
                fontsize=fontsize - 1, va='top', ha='left',
                color=TCVN_COLORS["dimension"], zorder=102)
        ax.text(x1 + (x1 - x0) * 0.01, tb_y - tb_height * 1.2,
                f"Sheet: {sheet}",
                fontsize=fontsize - 1, va='top', ha='right',
                color=TCVN_COLORS["dimension"], zorder=102)

        # Row 4: Names
        if designed_by or checked_by or approved_by:
            names_text = "  ".join([
                f"D: {designed_by}" if designed_by else "",
                f"C: {checked_by}" if checked_by else "",
                f"A: {approved_by}" if approved_by else ""
            ])
            ax.text(x0, tb_y - tb_height * 1.5,
                    names_text.strip(),
                    fontsize=fontsize - 1, va='top', ha='left',
                    color='#666666', zorder=102)

    @staticmethod
    def draw_section_line(
        ax: plt.Axes,
        start: Tuple[float, float],
        end: Tuple[float, float],
        hatch_region: str = "left",
        line_spacing: float = 8,
        line_angle: float = 45
    ):
        """
        Vẽ đường cắt với đường gạch chéo (section line).

        Args:
            ax: Axes
            start, end: Tọa độ 2 đầu đường cắt
            hatch_region: "left" | "right" | "both"
            line_spacing: Khoảng cách giữa các đường gạch
            line_angle: Góc đường gạch (degrees)
        """
        x1, y1 = start
        x2, y2 = end

        # Vẽ đường chính
        ax.plot([x1, x2], [y1, y2],
                color=TCVN_COLORS["section_line"],
                linewidth=LINE_WIDTH["section"],
                zorder=5)

        # Vẽ mũi tên
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2

        # Arrow at midpoint
        dx, dy = x2 - x1, y2 - y1
        length = np.sqrt(dx**2 + dy**2)
        dx, dy = dx / length, dy / length

        ax.annotate('',
            xy=(mid_x + dx * 5, mid_y + dy * 5),
            xytext=(mid_x - dx * 5, mid_y - dy * 5),
            arrowprops=dict(arrowstyle='->', color=TCVN_COLORS["section_line"],
                          lw=LINE_WIDTH["section"])
        )

    @staticmethod
    def draw_hatch_region(
        ax: plt.Axes,
        polygon_points: list,
        angle: float = 45,
        spacing: float = 8,
        color: str = None
    ):
        """
        Vẽ vùng gạch chéo (hatch pattern).

        Args:
            ax: Axes
            polygon_points: List of (x, y) tuples defining polygon
            angle: Góc hatch (degrees)
            spacing: Khoảng cách đường hatch
            color: Override màu
        """
        if color is None:
            color = TCVN_COLORS["outline"]

        from matplotlib.patches import Polygon
        from matplotlib.collections import LineCollection

        # Create polygon
        poly = Polygon(polygon_points, closed=True, facecolor='none',
                      edgecolor='none')
        ax.add_patch(poly)

        # Calculate hatch lines
        x_coords = [p[0] for p in polygon_points]
        y_coords = [p[1] for p in polygon_points]
        x_min, x_max = min(x_coords), max(x_coords)
        y_min, y_max = min(y_coords), max(y_coords)

        # Generate lines
        angle_rad = np.radians(angle)
        cos_a, sin_a = np.cos(angle_rad), np.sin(angle_rad)

        lines = []
        for i in np.arange(y_min - 50, y_max + 50, spacing):
            for j in np.arange(x_min - 50, x_max + 50, spacing):
                x_start = j
                y_start = i
                x_end = j + 100 * cos_a
                y_end = i + 100 * sin_a
                lines.append([(x_start, y_start), (x_end, y_end)])

        # Clip to polygon
        lc = LineCollection(lines, colors=color, linewidths=0.5)
        lc.set_clip_path(poly)
        ax.add_collection(lc)

    @staticmethod
    def draw_center_line(
        ax: plt.Axes,
        start: Tuple[float, float],
        end: Tuple[float, float],
        dash_pattern: tuple = (10, 5)
    ):
        """
        Vẽ đường tâm (center line).

        Args:
            ax: Axes
            start, end: Tọa độ 2 đầu
            dash_pattern: Pattern gạch ngắn (on, off)
        """
        x1, y1 = start
        x2, y2 = end

        ax.plot([x1, x2], [y1, y2],
                color=TCVN_COLORS["dimension"],
                linewidth=LINE_WIDTH["center"],
                linestyle='-.',
                dashes=dash_pattern,
                zorder=1)

    @staticmethod
    def setup_rc_section_style():
        """Setup matplotlib style cho bản vẽ BTCT."""
        plt.rcParams.update({
            'font.family': 'DejaVu Sans',
            'font.size': 10,
            'axes.titlesize': 14,
            'axes.labelsize': 10,
            'xtick.labelsize': 8,
            'ytick.labelsize': 8,
            'legend.fontsize': 8,
            'figure.titlesize': 14,
        })


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_rc_section_figure(
    width: float = 10,
    height: float = 8,
    title: str = "Mặt cắt cấu kiện BTCT"
) -> Tuple[plt.Figure, plt.Axes]:
    """
    Tạo figure và axes với style chuẩn cho bản vẽ BTCT.

    Args:
        width, height: Kích thước figure (inches)
        title: Tiêu đề figure

    Returns:
        (fig, ax)
    """
    DrawingStandards.setup_rc_section_style()
    fig, ax = plt.subplots(figsize=(width, height))
    DrawingStandards.apply_rc_style(ax)
    ax.set_title(title, pad=20, fontsize=14, fontweight='bold')
    return fig, ax


def export_figure(
    fig: plt.Figure,
    output_path: str,
    dpi: int = 300,
    transparent: bool = False,
    bbox_inches: str = 'tight',
    facecolor: str = 'white'
) -> str:
    """
    Xuất figure ra file với settings tối ưu.

    Args:
        fig: Matplotlib figure
        output_path: Đường dẫn file output
        dpi: Độ phân giải
        transparent: Transparent background
        bbox_inches: Bounding box
        facecolor: Màu nền

    Returns:
        output_path đã được xác nhận tồn tại
    """
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Save
    fig.savefig(output_path,
                dpi=dpi,
                transparent=transparent,
                bbox_inches=bbox_inches,
                facecolor=facecolor,
                edgecolor='none')

    # Verify
    if os.path.exists(output_path):
        file_size = os.path.getsize(output_path) / 1024
        print(f"[OK] Da xuat: {output_path} ({file_size:.1f} KB)")
        return output_path
    else:
        raise FileNotFoundError(f"Khong the xuat file: {output_path}")


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    # Ví dụ: Vẽ mặt cắt dầm BTCT đơn giản
    fig, ax = create_rc_section_figure(
        width=8, height=6,
        title="Ví dụ: Drawing Standards Library"
    )

    # Vẽ tiết diện bê tông
    DrawingStandards.draw_rect(
        ax, -150, -200, 300, 400,
        element_type="concrete",
        linewidth=2,
        hatch=True
    )

    # Vẽ cốt thép
    for i, y in enumerate([-150, 0, 150]):
        DrawingStandards.draw_circle(
            ax, 0, y, 12,
            element_type="rebar"
        )

    # Thêm dimension
    DrawingStandards.add_dimension(
        ax, (-150, -200), (150, -200),
        "b = 300", offset=25
    )
    DrawingStandards.add_dimension(
        ax, (-150, -200), (-150, 200),
        "h = 400", offset=25, side="left"
    )

    # Thêm annotation
    DrawingStandards.add_annotation(
        ax, (0, 150),
        "4Ø25",
        xytext=(120, 120)
    )

    # Export
    output = os.path.join(os.path.dirname(__file__), "example_output.png")
    export_figure(fig, output)

    print("\n[*] Drawing Standards Library - Example completed!")
    print(f"   Output: {output}")
