# -*- coding: utf-8 -*-
"""
sheet_scale_fitter.py — Dynamic Sheet-Scale Governor & SSOT Layout Engine
=========================================================================

Directive: CLAUDE ENGINEERING DIRECTIVE "Dynamic Sheet-Scale Governor & SSOT
Layout Engine" cho DCE CAD Pro v5.0 (Nhiệm vụ 1 — lớp SheetScaleSolver).

Module THUẦN (stdlib, không phụ thuộc ezdxf/matplotlib) để:
  - `cad_plan_engine.py` nạp qua importlib (cross-skill, pattern có sẵn) khi
    chạy ở chế độ "fill-window" (additive, KHÔNG đổi đường mặc định → giữ
    nguyên 30/30 suites + PNG bit-exact).
  - `mcp_dce_cad_server.py` (tool auto_layout_and_scale_plan) nạp trực tiếp.
  - Chạy thử standalone:  python sheet_scale_fitter.py  (in 3 ca AC1).

Nguyên tắc trung thực: solver trả ĐÚNG kết quả của công thức fill-ratio được
nêu trong directive, KHÔNG nhồi đáp án AC1. Nếu một mục tiêu AC không tái
sinh được từ công thức (vd KC-01 "1:200 @ 78%"), solver vẫn trả 1:100 (quy tắc
"ưu tiên tuyệt đối A1@1:100 nếu fill<=0.85") và để người dùng dùng
`force_scale` để ép giá trị mong muốn — tránh "hard-code đáp án để đạt tiêu
chí".

Công thức (chữ nghĩa trực tiếp theo directive):
    W_canvas_paper = W_paper - 25 - 10 - 220   (= W_paper - 255)  [mm giấy]
    H_canvas_paper = H_paper - 10 - 10         (= H_paper - 20)  [mm giấy]
    W_ext = W_footprint_mm + 84*S   (4 tầng dim mỗi bên: 10+8+12+12 = 42, x2 = 84)
    H_ext = H_footprint_mm + 84*S
    Fill_X = W_ext / (W_canvas_paper * S)
    Fill_Y = H_ext / (H_canvas_paper * S)
    Fill   = max(Fill_X, Fill_Y)
Quy tắc chọn:
    - Nếu S=100 cho Fill <= 0.85 trên khổ A1 => ƯU TIÊN TUYỆT ĐỐI A1 1:100.
    - Còn lại chọn cặp (khung, S) sao cho Fill thuộc [0.65, 0.85]; nếu nhiều
      nghiệm, lấy S cho Fill gần 0.75 nhất.
    - Không có nghiệm trong band trên khổ target => escalate khổ giấy (A2->A1->A0),
      đến khi có; hết khổ vẫn không vào band => lấy S tối thiểu |Fill-0.75|.
"""

from __future__ import annotations

import sys
import types
if __name__ and __name__ not in sys.modules:
    # Guard: @dataclass resolve cls.__module__ qua sys.modules (pattern
    # giống cad_plan_engine.py) — cho phép nạp module qua importlib mà
    # không cần register trước (tránh NoneType ở dataclasses._is_type).
    sys.modules[__name__] = types.ModuleType(__name__)

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# --- Khổ giấy (mm, landscape) — thư viện khả dụng của directive -------------
PAPER_SIZES_MM: Dict[str, Tuple[float, float]] = {
    "A2": (594.0, 420.0),
    "A1": (841.0, 594.0),   # mặc định dự án cao tầng
    "A0": (1189.0, 841.0),  # công trình đại quy mô > 60 m
}
_PAPER_ORDER = ["A2", "A1", "A0"]

# --- Trừ hao phân vùng (mm giấy) --------------------------------------------
MARGIN_LEFT = 25.0      # gáy đóng tập (trái)
MARGIN_OTHER = 10.0     # trên / dưới / phải
SIDEBAR_W = 220.0       # bảng thống kê (phải)
TITLE_BAND_H = 45.0     # dải khung tên (đáy)
# Canvas hữu dụng:
#   W = W_paper - 25 - 10 - 220 = W_paper - 255
#   H = H_paper - 10 - 10       = H_paper - 20
_X_DEDUCT = MARGIN_LEFT + MARGIN_OTHER + SIDEBAR_W          # = 255
_Y_DEDUCT = MARGIN_OTHER + MARGIN_OTHER                      # = 20

# --- Tập tỷ lệ TCVN hợp thức (1:S) ------------------------------------------
TCVN_SCALES: List[float] = [50.0, 75.0, 100.0, 125.0, 150.0, 200.0, 250.0]

# --- 4 tầng dim biên ngoài (mỗi bên; S là hệ số) ----------------------------
DIM_TIERS: Tuple[float, float, float, float] = (10.0, 8.0, 12.0, 12.0)  # tổng 42
_TIER_TOTAL = 2 * sum(DIM_TIERS)  # = 84 (hai chiều W/H cùng giá trị)

FILL_BAND: Tuple[float, float] = (0.65, 0.85)
_FILL_TARGET = 0.75
ABSOLUTE_PREFER_100_MAX_FILL = 0.85  # quy tắc "ưu tiên tuyệt đối A1 1:100"


def canvas_paper(paper: str) -> Tuple[float, float]:
    """Kích thước canvas hữu dụng trên giấy (mm)."""
    w, h = PAPER_SIZES_MM[paper.upper()]
    return (w - _X_DEDUCT, h - _Y_DEDUCT)


def fill_ratio(fp_mm: float, h_mm: float, paper: str, S: float) -> Tuple[float, float, float]:
    """Trả (fill_x, fill_y, fill=max) theo đúng công thức directive.

    fp_mm / h_mm: kích thước bao mô hình (footprint) theo MODEL mm.
    S: hệ số tỷ lệ (1:S).
    """
    cx, cy = canvas_paper(paper)
    ext = _TIER_TOTAL * S
    fx = (fp_mm + ext) / (cx * S)
    fy = (h_mm + ext) / (cy * S)
    return fx, fy, max(fx, fy)


def _escalation_chain(target: str) -> List[str]:
    """Chuỗi escalate khổ giấy từ target lên A0 (không lùi xuống khổ nhỏ hơn)."""
    start = _PAPER_ORDER.index(target.upper())
    return _PAPER_ORDER[start:]


def dimstyle_params(S: float) -> Dict[str, Dict[str, float]]:
    """Nhiệm vụ 2 — ma trận DimStyle động theo S (model units).

    dimtxt chữ chính (liên trục/tổng thể) và Dce_{S}MV; dimtxt_cot chi tiết
    định vị cột vách; dimasz mũi tên gạch chéo _ArchTick; dimexo hở chân dim;
    dimdle nhô đầu đường gióng. Đơn vị: mm model (= mm giấy * S).
    """
    return {
        "Dce_%dMV" % int(S): {
            "dimtxt": round(2.2 * S, 2),
            "dimasz": round(1.2 * S, 2),
            "dimexo": round(1.5 * S, 2),
            "dimdle": round(1.0 * S, 2),
        },
        "DCE_DIM_COT_%d" % int(S): {
            "dimtxt": round(1.8 * S, 2),  # dimtxt_cot
            "dimasz": round(1.2 * S, 2),
            "dimexo": round(1.5 * S, 2),
            "dimdle": round(1.0 * S, 2),
        },
        "DCE_DIM_MAIN_%d" % int(S): {
            "dimtxt": round(2.2 * S, 2),
            "dimasz": round(1.2 * S, 2),
            "dimexo": round(1.5 * S, 2),
            "dimdle": round(1.0 * S, 2),
        },
    }


def tier_distances(S: float) -> List[float]:
    """Khoảng cách 4 tầng dim biên ngoài (model mm): 10S, 8S, 12S, 12S."""
    return [t * S for t in DIM_TIERS]


@dataclass
class SheetScaleDecision:
    """Kết quả quyết định khổ + tỷ lệ + tham số đồng bộ."""
    sheet_size: str
    scale: float
    scale_label: str
    fill_x: float
    fill_y: float
    fill_ratio: float
    in_fill_band: bool
    footprints: Tuple[float, float]
    paper_mm: Tuple[float, float]
    canvas_paper: Tuple[float, float]
    ext_w_mm: float
    ext_h_mm: float
    dimstyle_params: Dict[str, Dict[str, float]] = field(default_factory=dict)
    tier_dist_mm: List[float] = field(default_factory=list)
    sidebar_w_mm: float = 0.0
    title_band_h_mm: float = 0.0

    def as_dict(self) -> dict:
        d = {k: (list(v) if isinstance(v, tuple) else v)
             for k, v in self.__dict__.items()}
        return d


class SheetScaleSolver:
    """Solver định hướng tỷ lệ & chọn khung theo fill-ratio-window."""

    def __init__(self, tcvn_scales=None, fill_band=None):
        self.scales = list(tcvn_scales) if tcvn_scales else list(TCVN_SCALES)
        self.band = tuple(fill_band) if fill_band else FILL_BAND

    def _build(self, fp, h, paper, S, fx, fy, fill) -> SheetScaleDecision:
        cx, cy = canvas_paper(paper)
        return SheetScaleDecision(
            sheet_size=paper,
            scale=S,
            scale_label=f"1/{int(S)}",
            fill_x=round(fx, 4), fill_y=round(fy, 4), fill_ratio=round(fill, 4),
            in_fill_band=self.band[0] <= fill <= self.band[1],
            footprints=(fp, h),
            paper_mm=PAPER_SIZES_MM[paper],
            canvas_paper=(round(cx, 1), round(cy, 1)),
            ext_w_mm=round(fp + _TIER_TOTAL * S, 1),
            ext_h_mm=round(h + _TIER_TOTAL * S, 1),
            dimstyle_params=dimstyle_params(S),
            tier_dist_mm=tier_distances(S),
            sidebar_w_mm=SIDEBAR_W * S,
            title_band_h_mm=TITLE_BAND_H * S,
        )

    def solve(self, fp_mm: float, h_mm: float, target_sheet: str = "A1",
              force_scale: Optional[float] = None,
              auto_escalate: bool = True) -> SheetScaleDecision:
        """Định khổ + tỷ lệ cho footprint (fp_mm, h_mm) theo MODEL mm."""
        fp, h = float(fp_mm), float(h_mm)
        if force_scale is not None:
            S = float(force_scale)
            fx, fy, fill = fill_ratio(fp, h, target_sheet, S)
            return self._build(fp, h, target_sheet, S, fx, fy, fill)

        chain = _escalation_chain(target_sheet) if auto_escalate else [target_sheet.upper()]
        fallback = None
        for i, paper in enumerate(chain):
            # (1) Quy tắc "ưu tiên tuyệt đối A1 1:100" (chỉ với khổ A1)
            if paper == "A1":
                fx100, fy100, f100 = fill_ratio(fp, h, paper, 100.0)
                if f100 <= ABSOLUTE_PREFER_100_MAX_FILL:
                    return self._build(fp, h, paper, 100.0, fx100, fy100, f100)
            # (2) Tìm nghiệm trong band; nhiều nghiệm => gần 0.75 nhất
            inband = []
            for S in self.scales:
                fx, fy, fill = fill_ratio(fp, h, paper, S)
                if self.band[0] <= fill <= self.band[1]:
                    inband.append((S, fx, fy, fill))
            if inband:
                S, fx, fy, fill = min(inband, key=lambda r: abs(r[3] - _FILL_TARGET))
                return self._build(fp, h, paper, S, fx, fy, fill)
            # (3) chưa vào band: ghi nhận best-effort (gần 0.75) để dùng nếu hết khổ
            if fallback is None:
                best = min(
                    ((S, *fill_ratio(fp, h, paper, S)) for S in self.scales),
                    key=lambda r: abs(r[3] - _FILL_TARGET),
                )
                fallback = (paper, best[0], best[1], best[2], best[3])
        # (4) hết khổ vẫn không vào band (A0 không đủ): trả best-effort
        paper, S, fx, fy, fill = fallback
        return self._build(fp, h, paper, S, fx, fy, fill)


# ---------------------------------------------------------------------------
# CLI — chạy thử 3 mô hình thực chiến (AC1)
# ---------------------------------------------------------------------------
def _selftest() -> None:
    solver = SheetScaleSolver()
    cases = [
        ("KC-01 (Tổng mặt bằng 45x32m)", 45000.0, 32000.0, "A1"),
        ("KC-02 (Định vị cột vách 36x24m)", 36000.0, 24000.0, "A1"),
        ("KC-03 (Dầm sàn 36x24m)", 36000.0, 24000.0, "A1"),
    ]
    print("=" * 78)
    print("SheetScaleSolver — 3 ca thực chiến (công thức fill-ratio directive)")
    print("=" * 78)
    for label, fp, hh, sheet in cases:
        d = solver.solve(fp, hh, target_sheet=sheet)
        print(f"\n{label}:")
        print(f"  => {d.sheet_size} {d.scale_label}  fill={d.fill_ratio*100:.1f}% "
              f"({d.fill_x*100:.1f}%/Y {d.fill_y*100:.1f}%)  in-band={d.in_fill_band}")
        print(f"     W_ext={d.ext_w_mm:.0f}mm H_ext={d.ext_h_mm:.0f}mm "
              f"canvas={d.canvas_paper[0]:.0f}x{d.canvas_paper[1]:.0f}mm")
        print(f"     tiers={d.tier_dist_mm}  dimtxt_main={d.dimstyle_params['Dce_%dMV'%int(d.scale)]['dimtxt']}mm")
    # minh họa force_scale (escape hatch khi mục tiêu AC khác công thức)
    forced = solver.solve(45000.0, 32000.0, "A1", force_scale=200.0)
    print(f"\n[force_scale=200] KC-01 -> {forced.sheet_size} {forced.scale_label} "
          f"fill={forced.fill_ratio*100:.1f}% (AC1 nêu 78% — khác fill thực của công thức)")


if __name__ == "__main__":
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
    _selftest()
