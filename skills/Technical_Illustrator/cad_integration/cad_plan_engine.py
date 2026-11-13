# -*- coding: utf-8 -*-
"""
cad_plan_engine.py — Module Chuyên sâu Sinh Bộ Bản vẽ Mặt bằng Kết cấu CAD (DCE Pro)
====================================================================================
Standard Engine v2.0 — Hỗ trợ Đa Bản vẽ Toàn diện (Multi-Sheet DCE Pro Suite):

  Sheet KC-01: TỔNG MẶT BẰNG KẾT CẤU & ĐỊNH VỊ CÔNG TRÌNH (Overall Structural Master Plan)
               - Ranh đất pháp lý (VN-2000 M1..M4), lộ giới đường D1/N2, khoảng lùi công trình.
               - Định vị mốc trắc đạc, tọa độ tim trục, lối xuống ramp dốc hầm i=12%.
               - Bảng tọa độ mốc ranh VN-2000 + Kim chỉ nam hướng Bắc (North Arrow).
               - Tỷ lệ 1/200 trên khổ giấy A1 chuẩn DCE Pro.

  Sheet KC-02: MẶT BẰNG ĐỊNH VỊ CỘT VÁCH TẦNG ĐIỂN HÌNH (Column & Shear Wall Setting-Out Plan)
               - Giải quyết triệt để 7 Gap cốt lõi của handoff bus 15.TEST:
                 Gap 1: Chuỗi kích thước neo định vị trắc đạc (DCE_Setout).
                 Gap 2: Dầm hiển thị nét mờ tham chiếu (DCE_NetThay), KHÔNG ghi nhãn dầm.
                 Gap 3: Bảng Thống kê Tiết diện & Cốt thép Cột Vách B35 (DCE_Schedule).
                 Gap 4: 4 tầng biên ngoài chuẩn quốc tế (Mép sàn -> Dim cột -> Dim trục -> Bong bóng).
                 Gap 5: Block TenCauKien căn chuẩn tâm hình học (World coords, 0 offset error).
                 Gap 6: Khung A1 (84100 x 59400 mm) + Khung tên đồ án DCE Pro (DCE_Frame).
                 Gap 7: Lõi thang máy, cửa mở, lanh tô & gạch chéo X lỗ rỗng sàn (DCE_VoidX).

  Sheet KC-03: MẶT BẰNG KẾT CẤU DẦM SÀN TẦNG ĐIỂN HÌNH (Typical Floor Beam & Slab Plan)
               - Dầm chính double lines theo đúng bề rộng b (DCE_MainBeam, màu xanh lá 3).
               - Dầm phụ chia ô sàn (DCE_Beam, màu vàng 2).
               - Nhãn dầm block Dce_KhTenDam (TENDAM) đặt dọc theo từng nhịp dầm.
               - Ký hiệu mặt cắt dầm sàn Dce_KhMatCat (MC 1-1, MC 2-2).
               - Ô sàn điển hình DCE_Slab tag (h=150) & Sàn hạ âm DCE_Drop mark (-0.050).
               - Ký hiệu cao độ mặt sàn Dce_CaoTrinh (+12.600).
               - Cột vách làm gối tựa hatch solid xám (DCE_Hatch), ẩn nhãn thép cột tránh loạn thị giác.
               - Bảng Thống kê Tiết diện Dầm Sàn B30 & Khung Ghi chú Chỉ dẫn Kỹ thuật.
               - Tỷ lệ 1/100 trên khổ giấy A1 chuẩn DCE Pro.

Tuân thủ nghiêm ngặt:
  - Điều 12b AGENTS.md: ZERO WHITE TEXT LOCK — Mọi TEXT/MTEXT có màu ACI rõ ràng, cấm ByBlock/ByLayer trắng.
  - Điều 12c AGENTS.md: Bê tông thực tế Việt Nam: Cột vách B35, Dầm sàn B30.
  - Điều 12d AGENTS.md: Quy chuẩn Đồ họa Bản vẽ Kỹ thuật CAD DCE Pro (5 điều cấm và chuẩn 7 Gap).
"""

import os
import sys
import math
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

import ezdxf
from ezdxf.enums import TextEntityAlignment

AGENTS_ROOT = Path(__file__).resolve().parent.parent.parent.parent
TEMPLATE_CANDIDATES = [
    Path(__file__).parent / "templates" / "DCE_Master_Seed_Template.dxf",
    AGENTS_ROOT / "skills" / "Technical_Illustrator" / "cad_integration" / "templates" / "DCE_Master_Seed_Template.dxf",
    AGENTS_ROOT / "01_Projects" / "99_Archived" / "DuAn_Test" / "Dam_200x400_DCE.dxf",
]

# Layer màu cố định theo chuẩn DCE Pro (Điều 12b)
DCE_PRO_LAYERS: Dict[str, Dict[str, Any]] = {
    "DCE_Truc":      {"color": 8,   "linetype": "DASHDOT2_DBIM", "note": "Lưới trục định vị"},
    "DCE_BaoBeTong": {"color": 4,   "linetype": "Continuous",    "note": "Biên dạng bê tông dầm, cột, sàn"},
    "DCE_Hatch":     {"color": 8,   "linetype": "Continuous",    "note": "Solid hatch cột và vách BTCT"},
    "DCE_MainBeam":  {"color": 3,   "linetype": "Continuous",    "note": "Nét thấy dầm chính khung"},
    "DCE_Beam":      {"color": 2,   "linetype": "Continuous",    "note": "Nét thấy dầm phụ chia ô sàn"},
    "DCE_Dim":       {"color": 254, "linetype": "Continuous",    "note": "Kích thước thứ nguyên DimStyle Dce_100MV"},
    "DCE_Name":      {"color": 142, "linetype": "Continuous",    "note": "Nhãn tên cấu kiện, dầm, mặt cắt"},
    "Dce_text":      {"color": 7,   "linetype": "Continuous",    "note": "Văn bản thuyết minh, tiêu đề"},
    "DCE_Note":      {"color": 250, "linetype": "Continuous",    "note": "Khung ghi chú quy chuẩn kỹ thuật"},
    "DCE_ThepChu":   {"color": 1,   "linetype": "Continuous",    "note": "Cốt thép chịu lực"},
    "DCE_Setout":    {"color": 253, "linetype": "Continuous",    "note": "Neo định vị trắc đạc (offset dims)"},
    "DCE_Schedule":  {"color": 250, "linetype": "Continuous",    "note": "Bảng thống kê cấu kiện & vật liệu"},
    "DCE_Frame":     {"color": 7,   "linetype": "Continuous",    "note": "Khung bản vẽ A1 + khung tên DCE Pro"},
    "DCE_GapOpen":   {"color": 3,   "linetype": "HIDDEN_DBIM",   "note": "Cửa mở thang máy / lanh tô (nét đứt)"},
    "DCE_Lanh_To":   {"color": 1,   "linetype": "Continuous",    "note": "Dầm lanh tô trên đầu cửa mở"},
    "DCE_VoidX":     {"color": 9,   "linetype": "Continuous",    "note": "Gạch chéo X lỗ rỗng xuyên sàn"},
    "DCE_Core":      {"color": 4,   "linetype": "Continuous",    "note": "Biên lõi cứng / thang / MEP shaft"},
    "DCE_NetThay":   {"color": 7,   "linetype": "HIDDEN_DBIM",   "note": "Dầm tham chiếu nét mờ trên MB định vị"},
    "DCE_NetKhuat":  {"color": 8,   "linetype": "HIDDEN_DBIM",   "note": "Lớp lót tham chiếu kiến trúc"},
    "DCE_Block":     {"color": 7,   "linetype": "Continuous",    "note": "Bong bóng trục, tiêu đề bản vẽ"},
    "DCE_Symbol":    {"color": 140, "linetype": "Continuous",    "note": "Ký hiệu sàn hạ âm, cao trình, tag sàn"},
    "DCE_RanhDat":   {"color": 1,   "linetype": "DASHDOT2_DBIM", "note": "Ranh giới khu đất pháp lý"},
    "DCE_ChiGioi":   {"color": 6,   "linetype": "HIDDEN_DBIM",   "note": "Chỉ giới xây dựng (khoảng lùi)"},
    "DCE_Road":      {"color": 8,   "linetype": "Continuous",    "note": "Đường giao thông, vỉa hè tiếp giáp"},
}

SCALE_MM = 1000.0  # mm/m — input model tính bằng MÉT


def _find_template() -> Optional[Path]:
    for cand in TEMPLATE_CANDIDATES:
        if cand.is_file():
            return cand
    return None


# ===========================================================================
# MÔ HÌNH KẾT CẤU TỔNG THỂ (MÉT)
# Dự án: Tháp Cao Ốc 40 Tầng + 2 Hầm (H ~ 135m), mặt bằng 57.0m x 28.0m
# ===========================================================================
def build_structural_model() -> Dict[str, Any]:
    # Lưới trục định vị
    grid_x = {
        '1': 0.00,  '2': 6.35,  '3': 12.71, '4': 18.96,
        '5': 23.21, '6': 28.29, '7': 33.80, '8': 37.40,
        '9': 43.86, '10': 50.43, '11': 57.00
    }
    grid_y = {'A': 28.00, 'B': 18.13, 'C': 9.76, 'D': 0.00}

    # Cột BTCT B35
    columns = [
        {'name': 'C1A',  'x': 0.35,  'y': 27.50, 'bx': 0.70, 'by': 1.00, 'size': '700×1000', 'conc': 'B35', 'thep_do': '20 D25', 'thep_dai': 'D10@150'},
        {'name': 'C2A',  'x': 6.35,  'y': 27.00, 'bx': 0.60, 'by': 2.00, 'size': '600×2000', 'conc': 'B35', 'thep_do': '28 D28', 'thep_dai': 'D10@150'},
        {'name': 'C3A',  'x': 12.71, 'y': 26.90, 'bx': 0.60, 'by': 2.20, 'size': '600×2200', 'conc': 'B35', 'thep_do': '32 D28', 'thep_dai': 'D10@150'},
        {'name': 'C4A',  'x': 18.96, 'y': 26.90, 'bx': 0.60, 'by': 2.20, 'size': '600×2200', 'conc': 'B35', 'thep_do': '32 D28', 'thep_dai': 'D10@150'},
        {'name': 'C6A',  'x': 28.29, 'y': 26.80, 'bx': 0.60, 'by': 2.40, 'size': '600×2400', 'conc': 'B35', 'thep_do': '36 D28', 'thep_dai': 'D10@150'},
        {'name': 'C8A',  'x': 37.40, 'y': 26.90, 'bx': 0.60, 'by': 2.20, 'size': '600×2200', 'conc': 'B35', 'thep_do': '32 D28', 'thep_dai': 'D10@150'},
        {'name': 'C9A',  'x': 43.86, 'y': 26.90, 'bx': 0.60, 'by': 2.20, 'size': '600×2200', 'conc': 'B35', 'thep_do': '32 D28', 'thep_dai': 'D10@150'},
        {'name': 'C10A', 'x': 50.43, 'y': 27.00, 'bx': 0.60, 'by': 2.00, 'size': '600×2000', 'conc': 'B35', 'thep_do': '28 D28', 'thep_dai': 'D10@150'},
        {'name': 'C11A', 'x': 56.65, 'y': 27.50, 'bx': 0.70, 'by': 1.00, 'size': '700×1000', 'conc': 'B35', 'thep_do': '20 D25', 'thep_dai': 'D10@150'},

        {'name': 'C1B',  'x': 0.40,  'y': 18.13, 'bx': 0.80, 'by': 1.80, 'size': '800×1800', 'conc': 'B35', 'thep_do': '32 D28', 'thep_dai': 'D10@150'},
        {'name': 'C2B',  'x': 6.35,  'y': 18.13, 'bx': 0.80, 'by': 2.40, 'size': '800×2400', 'conc': 'B35', 'thep_do': '36 D32', 'thep_dai': 'D10@150'},
        {'name': 'C10B', 'x': 50.43, 'y': 18.13, 'bx': 0.80, 'by': 2.40, 'size': '800×2400', 'conc': 'B35', 'thep_do': '36 D32', 'thep_dai': 'D10@150'},
        {'name': 'C11B', 'x': 56.60, 'y': 18.13, 'bx': 0.80, 'by': 1.80, 'size': '800×1800', 'conc': 'B35', 'thep_do': '32 D28', 'thep_dai': 'D10@150'},

        {'name': 'C1C',  'x': 0.40,  'y': 9.76,  'bx': 0.80, 'by': 1.80, 'size': '800×1800', 'conc': 'B35', 'thep_do': '32 D28', 'thep_dai': 'D10@150'},
        {'name': 'C2C',  'x': 6.35,  'y': 9.76,  'bx': 0.80, 'by': 2.40, 'size': '800×2400', 'conc': 'B35', 'thep_do': '36 D32', 'thep_dai': 'D10@150'},
        {'name': 'C10C', 'x': 50.43, 'y': 9.76,  'bx': 0.80, 'by': 2.40, 'size': '800×2400', 'conc': 'B35', 'thep_do': '36 D32', 'thep_dai': 'D10@150'},
        {'name': 'C11C', 'x': 56.60, 'y': 9.76,  'bx': 0.80, 'by': 1.80, 'size': '800×1800', 'conc': 'B35', 'thep_do': '32 D28', 'thep_dai': 'D10@150'},

        {'name': 'C1D',  'x': 0.35,  'y': 0.50,  'bx': 0.70, 'by': 1.00, 'size': '700×1000', 'conc': 'B35', 'thep_do': '20 D25', 'thep_dai': 'D10@150'},
        {'name': 'C2D',  'x': 6.35,  'y': 1.00,  'bx': 0.60, 'by': 2.00, 'size': '600×2000', 'conc': 'B35', 'thep_do': '28 D28', 'thep_dai': 'D10@150'},
        {'name': 'C3D',  'x': 12.71, 'y': 1.10,  'bx': 0.60, 'by': 2.20, 'size': '600×2200', 'conc': 'B35', 'thep_do': '32 D28', 'thep_dai': 'D10@150'},
        {'name': 'C4D',  'x': 18.96, 'y': 1.10,  'bx': 0.60, 'by': 2.20, 'size': '600×2200', 'conc': 'B35', 'thep_do': '32 D28', 'thep_dai': 'D10@150'},
        {'name': 'C6D',  'x': 28.29, 'y': 1.20,  'bx': 0.60, 'by': 2.40, 'size': '600×2400', 'conc': 'B35', 'thep_do': '36 D28', 'thep_dai': 'D10@150'},
        {'name': 'C8D',  'x': 37.40, 'y': 1.10,  'bx': 0.60, 'by': 2.20, 'size': '600×2200', 'conc': 'B35', 'thep_do': '32 D28', 'thep_dai': 'D10@150'},
        {'name': 'C9D',  'x': 43.86, 'y': 1.10,  'bx': 0.60, 'by': 2.20, 'size': '600×2200', 'conc': 'B35', 'thep_do': '32 D28', 'thep_dai': 'D10@150'},
        {'name': 'C10D', 'x': 50.43, 'y': 1.00,  'bx': 0.60, 'by': 2.00, 'size': '600×2000', 'conc': 'B35', 'thep_do': '28 D28', 'thep_dai': 'D10@150'},
        {'name': 'C11D', 'x': 56.65, 'y': 0.50,  'bx': 0.70, 'by': 1.00, 'size': '700×1000', 'conc': 'B35', 'thep_do': '20 D25', 'thep_dai': 'D10@150'},
    ]

    # Vách lõi thang BTCT B35
    shear_walls = [
        {'name': 'W1-1', 'x0': 13.18, 'y0': 11.78, 'x1': 13.18, 'y1': 16.22, 'tw': 0.40},
        {'name': 'W1-2', 'x0': 13.18, 'y0': 16.22, 'x1': 16.00, 'y1': 16.22, 'tw': 0.40},
        {'name': 'W1-3', 'x0': 17.77, 'y0': 16.22, 'x1': 20.51, 'y1': 16.22, 'tw': 0.40},
        {'name': 'W1-4', 'x0': 13.18, 'y0': 11.78, 'x1': 16.00, 'y1': 11.78, 'tw': 0.40},
        {'name': 'W1-5', 'x0': 17.77, 'y0': 11.78, 'x1': 20.51, 'y1': 11.78, 'tw': 0.40},
        {'name': 'W1-6', 'x0': 20.51, 'y0': 11.78, 'x1': 20.51, 'y1': 16.22, 'tw': 0.40},
        {'name': 'W1-7', 'x0': 17.77, 'y0': 11.78, 'x1': 17.77, 'y1': 16.22, 'tw': 0.30},
        {'name': 'W1-8', 'x0': 17.77, 'y0': 14.00, 'x1': 20.51, 'y1': 14.00, 'tw': 0.25},
        {'name': 'W2-1', 'x0': 23.21, 'y0': 11.78, 'x1': 23.21, 'y1': 16.22, 'tw': 0.50},
        {'name': 'W2-2', 'x0': 23.21, 'y0': 16.22, 'x1': 25.80, 'y1': 16.22, 'tw': 0.50},
        {'name': 'W2-3', 'x0': 29.17, 'y0': 16.22, 'x1': 33.80, 'y1': 16.22, 'tw': 0.50},
        {'name': 'W2-4', 'x0': 23.21, 'y0': 11.78, 'x1': 25.80, 'y1': 11.78, 'tw': 0.50},
        {'name': 'W2-5', 'x0': 29.17, 'y0': 11.78, 'x1': 33.80, 'y1': 11.78, 'tw': 0.50},
        {'name': 'W2-6', 'x0': 33.80, 'y0': 11.78, 'x1': 33.80, 'y1': 16.22, 'tw': 0.50},
        {'name': 'W2-7', 'x0': 25.80, 'y0': 11.78, 'x1': 25.80, 'y1': 16.22, 'tw': 0.35},
        {'name': 'W2-8', 'x0': 29.17, 'y0': 11.78, 'x1': 29.17, 'y1': 16.22, 'tw': 0.35},
        {'name': 'W2-9', 'x0': 31.05, 'y0': 11.78, 'x1': 31.05, 'y1': 16.22, 'tw': 0.30},
        {'name': 'W2-10','x0': 23.21, 'y0': 14.00, 'x1': 25.80, 'y1': 14.00, 'tw': 0.25},
        {'name': 'W2-11','x0': 25.80, 'y0': 13.50, 'x1': 29.17, 'y1': 13.50, 'tw': 0.25},
        {'name': 'W2-12','x0': 31.05, 'y0': 14.00, 'x1': 33.80, 'y1': 14.00, 'tw': 0.25},
        {'name': 'W3-1', 'x0': 36.50, 'y0': 11.78, 'x1': 36.50, 'y1': 16.22, 'tw': 0.40},
        {'name': 'W3-2', 'x0': 36.50, 'y0': 16.22, 'x1': 39.24, 'y1': 16.22, 'tw': 0.40},
        {'name': 'W3-3', 'x0': 40.60, 'y0': 16.22, 'x1': 43.86, 'y1': 16.22, 'tw': 0.40},
        {'name': 'W3-4', 'x0': 36.50, 'y0': 11.78, 'x1': 39.24, 'y1': 11.78, 'tw': 0.40},
        {'name': 'W3-5', 'x0': 40.60, 'y0': 11.78, 'x1': 43.86, 'y1': 11.78, 'tw': 0.40},
        {'name': 'W3-6', 'x0': 43.86, 'y0': 11.78, 'x1': 43.86, 'y1': 16.22, 'tw': 0.40},
        {'name': 'W3-7', 'x0': 39.24, 'y0': 11.78, 'x1': 39.24, 'y1': 16.22, 'tw': 0.30},
        {'name': 'W3-8', 'x0': 36.50, 'y0': 14.00, 'x1': 39.24, 'y1': 14.00, 'tw': 0.25},
    ]

    # Dầm chính phương X (Trục A, B, C, D)
    beams_x = [
        # Trục A (Y = 28.00)
        {'name': 'D1A', 'size': '400x800', 'b': 0.40, 'h': 0.80, 'x0': 0.35,  'y0': 27.50, 'x1': 6.35,  'y1': 27.00},
        {'name': 'D1A', 'size': '400x800', 'b': 0.40, 'h': 0.80, 'x0': 6.35,  'y0': 27.00, 'x1': 12.71, 'y1': 26.90},
        {'name': 'D1A', 'size': '400x800', 'b': 0.40, 'h': 0.80, 'x0': 12.71, 'y0': 26.90, 'x1': 18.96, 'y1': 26.90},
        {'name': 'D1A', 'size': '400x800', 'b': 0.40, 'h': 0.80, 'x0': 18.96, 'y0': 26.90, 'x1': 28.29, 'y1': 26.80},
        {'name': 'D1A', 'size': '400x800', 'b': 0.40, 'h': 0.80, 'x0': 28.29, 'y0': 26.80, 'x1': 37.40, 'y1': 26.90},
        {'name': 'D1A', 'size': '400x800', 'b': 0.40, 'h': 0.80, 'x0': 37.40, 'y0': 26.90, 'x1': 43.86, 'y1': 26.90},
        {'name': 'D1A', 'size': '400x800', 'b': 0.40, 'h': 0.80, 'x0': 43.86, 'y0': 26.90, 'x1': 50.43, 'y1': 27.00},
        {'name': 'D1A', 'size': '400x800', 'b': 0.40, 'h': 0.80, 'x0': 50.43, 'y0': 27.00, 'x1': 56.65, 'y1': 27.50},

        # Trục B (Y = 18.13)
        {'name': 'D1B', 'size': '500x900', 'b': 0.50, 'h': 0.90, 'x0': 0.40,  'y0': 18.13, 'x1': 6.35,  'y1': 18.13},
        {'name': 'D1B', 'size': '500x900', 'b': 0.50, 'h': 0.90, 'x0': 6.35,  'y0': 18.13, 'x1': 12.71, 'y1': 16.22},
        {'name': 'DG1', 'size': '400x800', 'b': 0.40, 'h': 0.80, 'x0': 20.51, 'y0': 16.22, 'x1': 23.21, 'y1': 16.22},
        {'name': 'DG2', 'size': '500x800', 'b': 0.50, 'h': 0.80, 'x0': 33.80, 'y0': 16.22, 'x1': 36.50, 'y1': 16.22},
        {'name': 'D1B', 'size': '500x900', 'b': 0.50, 'h': 0.90, 'x0': 43.86, 'y0': 16.22, 'x1': 50.43, 'y1': 18.13},
        {'name': 'D1B', 'size': '500x900', 'b': 0.50, 'h': 0.90, 'x0': 50.43, 'y0': 18.13, 'x1': 56.60, 'y1': 18.13},

        # Trục C (Y = 9.76)
        {'name': 'D1C', 'size': '500x900', 'b': 0.50, 'h': 0.90, 'x0': 0.40,  'y0': 9.76,  'x1': 6.35,  'y1': 9.76},
        {'name': 'D1C', 'size': '500x900', 'b': 0.50, 'h': 0.90, 'x0': 6.35,  'y0': 9.76,  'x1': 12.71, 'y1': 11.78},
        {'name': 'DG1', 'size': '400x800', 'b': 0.40, 'h': 0.80, 'x0': 20.51, 'y0': 11.78, 'x1': 23.21, 'y1': 11.78},
        {'name': 'DG2', 'size': '500x800', 'b': 0.50, 'h': 0.80, 'x0': 33.80, 'y0': 11.78, 'x1': 36.50, 'y1': 11.78},
        {'name': 'D1C', 'size': '500x900', 'b': 0.50, 'h': 0.90, 'x0': 43.86, 'y0': 11.78, 'x1': 50.43, 'y1': 9.76},
        {'name': 'D1C', 'size': '500x900', 'b': 0.50, 'h': 0.90, 'x0': 50.43, 'y0': 9.76,  'x1': 56.60, 'y1': 9.76},

        # Trục D (Y = 0.00)
        {'name': 'D1D', 'size': '400x800', 'b': 0.40, 'h': 0.80, 'x0': 0.35,  'y0': 0.50,  'x1': 6.35,  'y1': 1.00},
        {'name': 'D1D', 'size': '400x800', 'b': 0.40, 'h': 0.80, 'x0': 6.35,  'y0': 1.00,  'x1': 12.71, 'y1': 1.10},
        {'name': 'D1D', 'size': '400x800', 'b': 0.40, 'h': 0.80, 'x0': 12.71, 'y0': 1.10,  'x1': 18.96, 'y1': 1.10},
        {'name': 'D1D', 'size': '400x800', 'b': 0.40, 'h': 0.80, 'x0': 18.96, 'y0': 1.10,  'x1': 28.29, 'y1': 1.20},
        {'name': 'D1D', 'size': '400x800', 'b': 0.40, 'h': 0.80, 'x0': 28.29, 'y0': 1.20,  'x1': 37.40, 'y1': 1.10},
        {'name': 'D1D', 'size': '400x800', 'b': 0.40, 'h': 0.80, 'x0': 37.40, 'y0': 1.10,  'x1': 43.86, 'y1': 1.10},
        {'name': 'D1D', 'size': '400x800', 'b': 0.40, 'h': 0.80, 'x0': 43.86, 'y0': 1.10,  'x1': 50.43, 'y1': 1.00},
        {'name': 'D1D', 'size': '400x800', 'b': 0.40, 'h': 0.80, 'x0': 50.43, 'y0': 1.00,  'x1': 56.65, 'y1': 0.50},
    ]

    # Dầm chính khung phương Y (Trục dọc 1..11)
    beams_y = [
        # Trục 1 (X = 0.35)
        {'name': 'D2', 'size': '300x700', 'b': 0.30, 'h': 0.70, 'x0': 0.35,  'y0': 0.50,  'x1': 0.40,  'y1': 9.76},
        {'name': 'D2', 'size': '300x700', 'b': 0.30, 'h': 0.70, 'x0': 0.40,  'y0': 9.76,  'x1': 0.40,  'y1': 18.13},
        {'name': 'D2', 'size': '300x700', 'b': 0.30, 'h': 0.70, 'x0': 0.40,  'y0': 18.13, 'x1': 0.35,  'y1': 27.50},

        # Trục 2 (X = 6.35)
        {'name': 'D2', 'size': '300x700', 'b': 0.30, 'h': 0.70, 'x0': 6.35,  'y0': 1.00,  'x1': 6.35,  'y1': 9.76},
        {'name': 'D2', 'size': '300x700', 'b': 0.30, 'h': 0.70, 'x0': 6.35,  'y0': 9.76,  'x1': 6.35,  'y1': 18.13},
        {'name': 'D2', 'size': '300x700', 'b': 0.30, 'h': 0.70, 'x0': 6.35,  'y0': 18.13, 'x1': 6.35,  'y1': 27.00},

        # Trục 3, 4, 6, 8, 9
        {'name': 'D2', 'size': '300x700', 'b': 0.30, 'h': 0.70, 'x0': 12.71, 'y0': 1.10,  'x1': 12.71, 'y1': 11.78},
        {'name': 'D2', 'size': '300x700', 'b': 0.30, 'h': 0.70, 'x0': 12.71, 'y0': 16.22, 'x1': 12.71, 'y1': 26.90},

        {'name': 'D2', 'size': '300x700', 'b': 0.30, 'h': 0.70, 'x0': 18.96, 'y0': 1.10,  'x1': 18.96, 'y1': 11.78},
        {'name': 'D2', 'size': '300x700', 'b': 0.30, 'h': 0.70, 'x0': 18.96, 'y0': 16.22, 'x1': 18.96, 'y1': 26.90},

        {'name': 'D2', 'size': '300x700', 'b': 0.30, 'h': 0.70, 'x0': 28.29, 'y0': 1.20,  'x1': 28.29, 'y1': 11.78},
        {'name': 'D2', 'size': '300x700', 'b': 0.30, 'h': 0.70, 'x0': 28.29, 'y0': 16.22, 'x1': 28.29, 'y1': 26.80},

        {'name': 'D2', 'size': '300x700', 'b': 0.30, 'h': 0.70, 'x0': 37.40, 'y0': 1.10,  'x1': 37.40, 'y1': 11.78},
        {'name': 'D2', 'size': '300x700', 'b': 0.30, 'h': 0.70, 'x0': 37.40, 'y0': 16.22, 'x1': 37.40, 'y1': 26.90},

        {'name': 'D2', 'size': '300x700', 'b': 0.30, 'h': 0.70, 'x0': 43.86, 'y0': 1.10,  'x1': 43.86, 'y1': 11.78},
        {'name': 'D2', 'size': '300x700', 'b': 0.30, 'h': 0.70, 'x0': 43.86, 'y0': 16.22, 'x1': 43.86, 'y1': 26.90},

        # Trục 10 (X = 50.43)
        {'name': 'D2', 'size': '300x700', 'b': 0.30, 'h': 0.70, 'x0': 50.43, 'y0': 1.00,  'x1': 50.43, 'y1': 9.76},
        {'name': 'D2', 'size': '300x700', 'b': 0.30, 'h': 0.70, 'x0': 50.43, 'y0': 9.76,  'x1': 50.43, 'y1': 18.13},
        {'name': 'D2', 'size': '300x700', 'b': 0.30, 'h': 0.70, 'x0': 50.43, 'y0': 18.13, 'x1': 50.43, 'y1': 27.00},

        # Trục 11 (X = 56.65)
        {'name': 'D2', 'size': '300x700', 'b': 0.30, 'h': 0.70, 'x0': 56.65, 'y0': 0.50,  'x1': 56.60, 'y1': 9.76},
        {'name': 'D2', 'size': '300x700', 'b': 0.30, 'h': 0.70, 'x0': 56.60, 'y0': 9.76,  'x1': 56.60, 'y1': 18.13},
        {'name': 'D2', 'size': '300x700', 'b': 0.30, 'h': 0.70, 'x0': 56.60, 'y0': 18.13, 'x1': 56.65, 'y1': 27.50},
    ]

    # Dầm phụ chia ô sàn (DP1 250x600)
    secondary_beams = [
        {'name': 'DP1', 'size': '250x600', 'b': 0.25, 'h': 0.60, 'x0': 3.35, 'y0': 1.00,  'x1': 3.35, 'y1': 9.76},
        {'name': 'DP1', 'size': '250x600', 'b': 0.25, 'h': 0.60, 'x0': 3.35, 'y0': 18.13, 'x1': 3.35, 'y1': 27.20},
        {'name': 'DP1', 'size': '250x600', 'b': 0.25, 'h': 0.60, 'x0': 9.53, 'y0': 1.05,  'x1': 9.53, 'y1': 9.76},
        {'name': 'DP1', 'size': '250x600', 'b': 0.25, 'h': 0.60, 'x0': 9.53, 'y0': 18.13, 'x1': 9.53, 'y1': 26.95},
        {'name': 'DP1', 'size': '250x600', 'b': 0.25, 'h': 0.60, 'x0': 47.14, 'y0': 1.05, 'x1': 47.14, 'y1': 9.76},
        {'name': 'DP1', 'size': '250x600', 'b': 0.25, 'h': 0.60, 'x0': 47.14, 'y0': 18.13, 'x1': 47.14, 'y1': 26.95},
        {'name': 'DP1', 'size': '250x600', 'b': 0.25, 'h': 0.60, 'x0': 53.54, 'y0': 1.00, 'x1': 53.54, 'y1': 9.76},
        {'name': 'DP1', 'size': '250x600', 'b': 0.25, 'h': 0.60, 'x0': 53.54, 'y0': 18.13, 'x1': 53.54, 'y1': 27.20},
    ]

    # Các ô sàn & hạ âm
    slab_tags = [
        {'x': 3.35,  'y': 22.50, 'label': 'S1 (h=150)', 'type': 'standard'},
        {'x': 9.53,  'y': 22.50, 'label': 'S1 (h=150)', 'type': 'standard'},
        {'x': 15.80, 'y': 22.50, 'label': 'S1 (h=150)', 'type': 'standard'},
        {'x': 23.60, 'y': 22.50, 'label': 'S2 (h=120)', 'type': 'drop', 'drop': '-0.050'},
        {'x': 32.80, 'y': 22.50, 'label': 'S2 (h=120)', 'type': 'drop', 'drop': '-0.050'},
        {'x': 40.60, 'y': 22.50, 'label': 'S1 (h=150)', 'type': 'standard'},
        {'x': 47.14, 'y': 22.50, 'label': 'S1 (h=150)', 'type': 'standard'},
        {'x': 53.54, 'y': 22.50, 'label': 'S1 (h=150)', 'type': 'standard'},

        {'x': 3.35,  'y': 5.50,  'label': 'S1 (h=150)', 'type': 'standard'},
        {'x': 9.53,  'y': 5.50,  'label': 'S1 (h=150)', 'type': 'standard'},
        {'x': 15.80, 'y': 5.50,  'label': 'S1 (h=150)', 'type': 'standard'},
        {'x': 23.60, 'y': 5.50,  'label': 'S1 (h=150)', 'type': 'standard'},
        {'x': 32.80, 'y': 5.50,  'label': 'S1 (h=150)', 'type': 'standard'},
        {'x': 40.60, 'y': 5.50,  'label': 'S1 (h=150)', 'type': 'standard'},
        {'x': 47.14, 'y': 5.50,  'label': 'S1 (h=150)', 'type': 'standard'},
        {'x': 53.54, 'y': 5.50,  'label': 'S1 (h=150)', 'type': 'standard'},
    ]

    # Lỗ rỗng xuyên sàn (thang bộ + MEP + thang máy)
    voids = [
        {'name': 'THANG BO L1',    'x': 14.50, 'y': 12.50, 'w': 2.20, 'h': 3.20},
        {'name': 'THANG MAY TM2',  'x': 26.50, 'y': 12.30, 'w': 1.80, 'h': 1.40,
         'cua_mo': 1.20, 'cua_mo_y': 15.50, 'lanh_to': True},
        {'name': 'MEP SHAFT',      'x': 31.50, 'y': 12.30, 'w': 1.50, 'h': 1.40},
    ]

    # Dữ liệu quy hoạch Tổng mặt bằng (KC-01)
    site_data = {
        'lot_w': 75.00, 'lot_h': 45.00,
        'bldg_offset_x': 9.00, 'bldg_offset_y': 8.50,
        'setback_front': 6.00, 'setback_rear': 3.00, 'setback_side': 2.50,
        'vn2000_origin_x': 1198200.000, 'vn2000_origin_y': 604300.000,
        'roads': [
            {'name': 'ĐƯỜNG D1 (LỘ GIỚI 20.0m)', 'side': 'south', 'width': 20.0, 'sidewalk': 4.5},
            {'name': 'ĐƯỜNG N2 (LỘ GIỚI 14.0m)', 'side': 'west',  'width': 14.0, 'sidewalk': 3.0},
        ],
        'ramps': [
            {'name': 'RAMP VÀO HẦM (i=12%)', 'x': 5.0,  'y': 4.0, 'w': 3.5, 'l': 12.0, 'dir': 'up'},
            {'name': 'RAMP RA HẦM (i=12%)',  'x': 66.5, 'y': 4.0, 'w': 3.5, 'l': 12.0, 'dir': 'up'},
        ]
    }

    return {
        'L_total': 57.00, 'B_total': 28.00,
        'grid_x': grid_x, 'grid_y': grid_y,
        'columns': columns, 'shear_walls': shear_walls,
        'beams_x': beams_x, 'beams_y': beams_y,
        'secondary_beams': secondary_beams,
        'main_beams': beams_x + beams_y,
        'slab_tags': slab_tags,
        'voids': voids,
        'site_data': site_data,
    }


# ===========================================================================
# MASTER CAD ENGINE
# ===========================================================================
class DcePlanEngine:
    FRAME_X0, FRAME_Y0 = 2000.0, 2000.0
    FRAME_W, FRAME_H = 84100.0, 59400.0
    PLAN_X0, PLAN_Y0 = 15500.0, 16000.0

    def __init__(self, model: Dict[str, Any], template_path: Optional[Path] = None,
                 arch_lines: Optional[List[Tuple[float, float, float, float]]] = None):
        self.model = model
        self.arch_lines = arch_lines or []
        self.template_path = template_path or _find_template()
        self.doc = None
        self.msp = None
        self.ox, self.oy = self.PLAN_X0, self.PLAN_Y0
        self.L = model['L_total'] * SCALE_MM
        self.B = model['B_total'] * SCALE_MM

    def _wx(self, x_m): return self.ox + x_m * SCALE_MM
    def _wy(self, y_m): return self.oy + y_m * SCALE_MM

    def setup(self):
        if self.template_path and os.path.exists(self.template_path):
            self.doc = ezdxf.readfile(str(self.template_path))
        else:
            self.doc = ezdxf.new('R2007', setup=True)
        self.msp = self.doc.modelspace()
        # Xóa sạch các entity mẫu cũ trong modelspace để tránh lỗi audit & drawing backend
        for e in list(self.msp):
            self.msp.delete_entity(e)
        self.doc.header['$INSUNITS'] = 4
        self.doc.header['$MEASUREMENT'] = 1
        self.doc.header['$LTSCALE'] = 100.0
        self._ensure_layers()
        return self

    def _ensure_layers(self):
        existing = {l.dxf.name for l in self.doc.layers}
        lts = {lt.dxf.name for lt in self.doc.linetypes}
        for name, spec in DCE_PRO_LAYERS.items():
            if name in existing:
                continue
            lt = spec.get('linetype', 'Continuous')
            if lt not in lts:
                lt = 'Continuous'
            try:
                self.doc.layers.add(name, color=spec['color'], linetype=lt)
            except Exception:
                self.doc.layers.add(name, color=spec['color'])

    # ------------------------------------------------------------------
    # CÁC PHẦN DÙNG CHUNG (LƯỚI TRỤC, DIM, KHUNG BẢN VẼ, VOID)
    # ------------------------------------------------------------------
    def render_slab_boundary(self):
        self.msp.add_lwpolyline(
            [(self.ox, self.oy), (self.ox + self.L, self.oy),
             (self.ox + self.L, self.oy + self.B), (self.ox, self.oy + self.B)],
            close=True, dxfattribs={'layer': 'DCE_BaoBeTong'})
        return self

    def render_voids(self):
        msp = self.msp
        for v in self.model.get('voids', []):
            vx = self._wx(v['x']); vy = self._wy(v['y'])
            vw = v['w'] * SCALE_MM; vh = v['h'] * SCALE_MM
            x0, y0 = vx - vw / 2.0, vy - vh / 2.0
            x1, y1 = vx + vw / 2.0, vy + vh / 2.0
            msp.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], close=True,
                               dxfattribs={'layer': 'DCE_Core'})
            msp.add_line((x0, y0), (x1, y1), dxfattribs={'layer': 'DCE_VoidX'})
            msp.add_line((x1, y0), (x0, y1), dxfattribs={'layer': 'DCE_VoidX'})
            if v.get('cua_mo') and v.get('lanh_to'):
                cw = v['cua_mo'] * SCALE_MM
                cy = self._wy(v.get('cua_mo_y', v['y']))
                cx = vx
                c0 = cx - cw / 2.0
                msp.add_line((c0, cy - vh/2), (c0 + cw, cy - vh/2), dxfattribs={'layer': 'DCE_GapOpen'})
                msp.add_line((cx - vw/2, cy + vh/2), (cx + vw/2, cy + vh/2), dxfattribs={'layer': 'DCE_Lanh_To'})
                lab = msp.add_text(v['name'], height=180.0, dxfattribs={'layer': 'DCE_Core', 'style': 'Dce_Text'})
                lab.set_placement((cx, cy), align=TextEntityAlignment.MIDDLE_CENTER)
            else:
                lab = msp.add_text(v['name'], height=180.0, dxfattribs={'layer': 'DCE_Core', 'style': 'Dce_Text'})
                lab.set_placement((vx, vy + vh/2 + 300), align=TextEntityAlignment.BOTTOM_CENTER)
        return self

    def render_axes_and_dims(self, include_setout=True):
        m = self.model
        gx = list(m['grid_x'].items()) if isinstance(m['grid_x'], dict) else [(item['name'], item['pos']) for item in m['grid_x']]
        gy = list(m['grid_y'].items()) if isinstance(m['grid_y'], dict) else [(item['name'], item['pos']) for item in m['grid_y']]
        msp = self.msp

        dim_bay    = -4500.0
        dim_total  = -7500.0
        bub_ext    = 10500.0

        y_bot0 = self._wy(0.0)
        y_top0 = self._wy(self.B / SCALE_MM)
        y_bub_bot = y_bot0 - bub_ext
        y_bub_top = y_top0 + 5500.0
        x_bub_left = self._wx(0.0) - bub_ext
        x_bub_right = self._wx(self.L / SCALE_MM) + 3500.0

        for name, xm in gx:
            x_w = self._wx(xm)
            msp.add_line((x_w, y_bub_bot), (x_w, y_bub_top), dxfattribs={'layer': 'DCE_Truc'})
            self._insert_axis_bubble(x_w, y_bub_bot, name, 0.0)
            self._insert_axis_bubble(x_w, y_bub_top, name, 180.0)

        for name, ym in gy:
            y_w = self._wy(ym)
            msp.add_line((x_bub_left, y_w), (x_bub_right, y_w), dxfattribs={'layer': 'DCE_Truc'})
            self._insert_axis_bubble(x_bub_left, y_w, name, 270.0)
            self._insert_axis_bubble(x_bub_right, y_w, name, 90.0)

        # Dim liên trục X & dim tổng X
        y_d_bay = y_bot0 + dim_bay
        for i in range(len(gx) - 1):
            x1 = self._wx(gx[i][1]); x2 = self._wx(gx[i+1][1])
            self._add_linear_dim((x1, y_d_bay), (x2, y_d_bay), 0.0)
        y_d_tot = y_bot0 + dim_total
        self._add_linear_dim((self._wx(gx[0][1]), y_d_tot), (self._wx(gx[-1][1]), y_d_tot), 0.0)

        # Dim liên trục Y & dim tổng Y
        x_d_bay = self._wx(0.0) + dim_bay
        for i in range(len(gy) - 1):
            y1 = self._wy(gy[i+1][1]); y2 = self._wy(gy[i][1])
            self._add_linear_dim((x_d_bay, y1), (x_d_bay, y2), 90.0)
        x_d_tot = self._wx(0.0) + dim_total
        self._add_linear_dim((x_d_tot, self._wy(gy[-1][1])), (x_d_tot, self._wy(gy[0][1])), 90.0)

        if include_setout:
            self._calc_column_offsets()
        return self

    def _calc_column_offsets(self):
        m = self.model
        msp = self.msp
        gxd = m['grid_x'] if isinstance(m['grid_x'], dict) else {it['name']: it['pos'] for it in m['grid_x']}
        gyd = m['grid_y'] if isinstance(m['grid_y'], dict) else {it['name']: it['pos'] for it in m['grid_y']}

        for col in m['columns']:
            cx = self._wx(col['x']); cy = self._wy(col['y'])
            nearest_gx = min(gxd.keys(), key=lambda k: abs(cx - self._wx(gxd[k])))
            nearest_gy = min(gyd.keys(), key=lambda k: abs(cy - self._wy(gyd[k])))
            gx_dist = cx - self._wx(gxd[nearest_gx])
            gy_dist = cy - self._wy(gyd[nearest_gy])

            if abs(gx_dist) > 10.0:
                grid_x_world = self._wx(gxd[nearest_gx])
                msp.add_line((grid_x_world, cy), (cx, cy), dxfattribs={'layer': 'DCE_Setout'})
                t_val = int(round(abs(gx_dist)))
                msp.add_text(f"{t_val}", height=140.0,
                             dxfattribs={'layer': 'DCE_Setout', 'style': 'Dce_Text'}).set_placement(
                    ((grid_x_world + cx) / 2.0, cy + 120), align=TextEntityAlignment.BOTTOM_CENTER)

            if abs(gy_dist) > 10.0:
                grid_y_world = self._wy(gyd[nearest_gy])
                msp.add_line((cx, grid_y_world), (cx, cy), dxfattribs={'layer': 'DCE_Setout'})
                t_val = int(round(abs(gy_dist)))
                msp.add_text(f"{t_val}", height=140.0,
                             dxfattribs={'layer': 'DCE_Setout', 'style': 'Dce_Text'}).set_placement(
                    (cx + 120, (grid_y_world + cy) / 2.0), align=TextEntityAlignment.MIDDLE_LEFT)

    def _insert_axis_bubble(self, x, y, name, rotation_deg):
        msp = self.msp
        scale = 100.0
        try:
            bref = msp.add_blockref('Dce_KhTenTruc', (x, y), dxfattribs={
                'layer': 'DCE_Block', 'xscale': scale, 'yscale': scale, 'rotation': rotation_deg})
            bref.add_auto_attribs({'TRUC': name})
            r = math.radians(rotation_deg)
            bx, by = 0.0, -3.5 * scale
            c, s = math.cos(r), math.sin(r)
            cx = x + c * bx - s * by
            cy = y + s * bx + c * by
            for att in bref.attribs:
                att.dxf.rotation = 0.0
                att.dxf.insert = (cx, cy, 0.0)
                att.dxf.align_point = (cx, cy, 0.0)
                att.dxf.halign = 1
                att.dxf.valign = 2
        except Exception:
            t = msp.add_text(name, height=300.0, dxfattribs={'layer': 'DCE_Block', 'style': 'Dce_Text'})
            t.set_placement((x, y), align=TextEntityAlignment.MIDDLE_CENTER)

    def _add_linear_dim(self, p1, p2, angle):
        msp = self.msp
        dimstyle = 'Dce_100MV' if 'Dce_100MV' in self.doc.dimstyles else 'Standard'
        dim = msp.add_linear_dim(base=p1, p1=p1, p2=p2, angle=angle, dimstyle=dimstyle,
                                 dxfattribs={'layer': 'DCE_Dim'})
        dim.render()

    def _solid_hatch(self, pts, layer='DCE_Hatch'):
        hatch = self.msp.add_hatch(dxfattribs={'layer': layer})
        hatch.set_solid_fill()
        hatch.paths.add_polyline_path(pts, is_closed=True)
        return hatch

    def render_frame_and_title(self, plan_title="MẶT BẰNG KẾT CẤU TẦNG ĐIỂN HÌNH",
                               scale_label="1/100", sheet_no="KC-02",
                               sub_title_vn="MẶT BẰNG ĐỊNH VỊ CỘT VÁCH TẦNG ĐIỂN HÌNH",
                               sub_title_en="TYPICAL FLOOR STRUCTURAL LAYOUT PLAN"):
        msp = self.msp
        fx0, fy0 = self.FRAME_X0, self.FRAME_Y0
        fw, fh = self.FRAME_W, self.FRAME_H

        # Khung ngoài A1
        msp.add_lwpolyline([
            (fx0, fy0), (fx0 + fw, fy0), (fx0 + fw, fy0 + fh), (fx0, fy0 + fh)
        ], close=True, dxfattribs={'layer': 'DCE_Frame'})

        # Khung viền trong
        in_x0, in_y0 = fx0 + 2500.0, fy0 + 1000.0
        in_x1, in_y1 = fx0 + fw - 1000.0, fy0 + fh - 1000.0
        msp.add_lwpolyline([
            (in_x0, in_y0), (in_x1, in_y0), (in_x1, in_y1), (in_x0, in_y1)
        ], close=True, dxfattribs={'layer': 'DCE_Frame'})

        # Khung tên góc dưới phải
        tb_w, tb_h = 18000.0, 5500.0
        tb_x0 = in_x1 - tb_w; tb_y0 = in_y0
        msp.add_lwpolyline([
            (tb_x0, tb_y0), (tb_x0 + tb_w, tb_y0),
            (tb_x0 + tb_w, tb_y0 + tb_h), (tb_x0, tb_y0 + tb_h)
        ], close=True, dxfattribs={'layer': 'DCE_Frame'})

        msp.add_line((tb_x0, tb_y0 + 3800), (tb_x0 + tb_w, tb_y0 + 3800), dxfattribs={'layer': 'DCE_Frame'})
        msp.add_line((tb_x0, tb_y0 + 2000), (tb_x0 + tb_w, tb_y0 + 2000), dxfattribs={'layer': 'DCE_Frame'})
        msp.add_line((tb_x0 + 7000, tb_y0), (tb_x0 + 7000, tb_y0 + 3800), dxfattribs={'layer': 'DCE_Frame'})
        msp.add_line((tb_x0 + 13000, tb_y0), (tb_x0 + 13000, tb_y0 + 2000), dxfattribs={'layer': 'DCE_Frame'})

        t1 = msp.add_text("TƯ VẤN THIẾT KẾ: DCE PRO STRUCTURAL PARTNERS", height=240.0,
                          dxfattribs={'layer': 'Dce_text', 'style': 'Dce_Text'})
        t1.set_placement((tb_x0 + tb_w / 2.0, tb_y0 + 4600.0), align=TextEntityAlignment.MIDDLE_CENTER)

        t2 = msp.add_text("DỰ ÁN: THÁP CAO ỐC 40 TẦNG + 2 TẦNG HẦM (H ~ 135m)", height=200.0,
                          dxfattribs={'layer': 'Dce_text', 'style': 'Dce_Text'})
        t2.set_placement((tb_x0 + tb_w / 2.0, tb_y0 + 2900.0), align=TextEntityAlignment.MIDDLE_CENTER)

        t3 = msp.add_text(f"BẢN VẼ: {plan_title}", height=220.0,
                          dxfattribs={'layer': 'Dce_text', 'style': 'Dce_Text'})
        t3.set_placement((tb_x0 + 300.0, tb_y0 + 1000.0), align=TextEntityAlignment.LEFT)

        t4 = msp.add_text(f"TỶ LỆ: {scale_label}  |  BẢN VẼ SỐ: {sheet_no}", height=200.0,
                          dxfattribs={'layer': 'Dce_text', 'style': 'Dce_Text'})
        t4.set_placement((tb_x0 + 13300.0, tb_y0 + 1000.0), align=TextEntityAlignment.LEFT)

        # Tiêu đề mặt bằng chuẩn Block DCE_Plan header 1
        px = self.ox + self.L / 2.0; py = 4000.0
        try:
            plan_hdr = msp.add_blockref('DCE_Plan header 1', (px, py), dxfattribs={
                'layer': 'DCE_Block', 'xscale': 100.0, 'yscale': 100.0
            })
            plan_hdr.add_auto_attribs({
                'DRAWING-VN': f"%%u{plan_title}",
                'DRAWING-E': f"%%u{sub_title_en}",
                'SCALE_1:100': f"SCALE: {scale_label}"
            })
        except Exception:
            t = msp.add_text(f"%%u{plan_title}", height=380.0,
                             dxfattribs={'layer': 'DCE_Block', 'style': 'Dce_Text'})
            t.set_placement((px, py), align=TextEntityAlignment.MIDDLE_CENTER)
        return self

    # ------------------------------------------------------------------
    # SHEET KC-02: MẶT BẰNG ĐỊNH VỊ CỘT VÁCH TẦNG ĐIỂN HÌNH
    # ------------------------------------------------------------------
    def render_columns_walls_kc02(self):
        msp = self.msp
        for col in self.model['columns']:
            cx = self._wx(col['x']); cy = self._wy(col['y'])
            bx = col['bx'] * SCALE_MM; by = col['by'] * SCALE_MM
            x0, y0 = cx - bx / 2.0, cy - by / 2.0
            x1, y1 = cx + bx / 2.0, cy + by / 2.0
            pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
            msp.add_lwpolyline(pts, close=True, dxfattribs={'layer': 'DCE_BaoBeTong'})
            self._solid_hatch(pts)
            self._insert_member_tag(cx, cy, by, col['name'], col['size'])

        for w in self.model['shear_walls']:
            x0 = self._wx(w['x0']); y0 = self._wy(w['y0'])
            x1 = self._wx(w['x1']); y1 = self._wy(w['y1'])
            tw = w['tw'] * SCALE_MM
            if abs(x0 - x1) < 50.0:
                pts = [(x0 - tw/2, min(y0, y1)), (x0 + tw/2, min(y0, y1)),
                       (x0 + tw/2, max(y0, y1)), (x0 - tw/2, max(y0, y1))]
            else:
                pts = [(min(x0, x1), y0 - tw/2), (max(x0, x1), y0 - tw/2),
                       (max(x0, x1), y0 + tw/2), (min(x0, x1), y0 + tw/2)]
            msp.add_lwpolyline(pts, close=True, dxfattribs={'layer': 'DCE_BaoBeTong'})
            self._solid_hatch(pts)
        return self

    def _insert_member_tag(self, cx, cy, by_mm, name, size):
        msp = self.msp
        offset = max(by_mm / 2.0 + 400.0, 1200.0)
        ins_y = (cy + offset) if cy >= (self.oy + self.B / 2.0) else (cy - offset)
        try:
            bref = msp.add_blockref('TenCauKien', (cx, ins_y), dxfattribs={
                'layer': 'DCE_Name', 'xscale': 100.0, 'yscale': 100.0, 'rotation': 270.0})
            bref.add_auto_attribs({'TENCAUKIEN': name, 'SOCAUKIEN': size})
            for att in bref.attribs:
                att.dxf.rotation = 0.0
                att.dxf.insert = (cx, ins_y, 0.0)
                att.dxf.align_point = (cx, ins_y, 0.0)
                att.dxf.halign = 1
                att.dxf.valign = 2
        except Exception:
            t = msp.add_text(f"{name} ({size})", height=200.0,
                             dxfattribs={'layer': 'DCE_Name', 'style': 'Dce_Text'})
            t.set_placement((cx, ins_y), align=TextEntityAlignment.MIDDLE_CENTER)
        return self

    def render_beams_reference(self):
        msp = self.msp
        for bm in self.model['main_beams']:
            x0, y0 = self._wx(bm['x0']), self._wy(bm['y0'])
            x1, y1 = self._wx(bm['x1']), self._wy(bm['y1'])
            msp.add_line((x0, y0), (x1, y1), dxfattribs={'layer': 'DCE_NetThay'})
        return self

    def render_arch_underlay(self):
        msp = self.msp
        for l in self.arch_lines:
            msp.add_line((self._wx(l[0]), self._wy(l[1])),
                         (self._wx(l[2]), self._wy(l[3])),
                         dxfattribs={'layer': 'DCE_NetKhuat'})
        return self

    def render_column_schedule(self):
        msp = self.msp
        x0 = 72800.0; y0 = 57500.0
        col_w = [800.0, 1600.0, 2000.0, 1400.0, 2000.0, 1800.0, 1000.0]
        total_w = sum(col_w)
        h_title = 1100.0; h_head = 900.0; h_row = 650.0

        rows = [
            ("1",  "C1A, C11A, C1D, C11D",  "700x1000", "B35", "20 D25",   "D10@150", "4"),
            ("2",  "C2A, C10A, C2D, C10D",  "600x2000", "B35", "28 D28",   "D10@150", "4"),
            ("3",  "C3A, C4A, C8A, C9A",    "600x2200", "B35", "32 D28",   "D10@150", "4"),
            ("4",  "C3D, C4D, C8D, C9D",    "600x2200", "B35", "32 D28",   "D10@150", "4"),
            ("5",  "C6A, C6D",              "600x2400", "B35", "36 D28",   "D10@150", "2"),
            ("6",  "C1B, C11B, C1C, C11C",  "800x1800", "B35", "32 D28",   "D10@150", "4"),
            ("7",  "C2B, C10B, C2C, C10C",  "800x2400", "B35", "36 D32",   "D10@150", "4"),
            ("8",  "W1 (Lõi Thang 1+2TM)",  "tw=400",   "B35", "2L D18@150", "D10@200", "1"),
            ("9",  "W2 (Lõi TM PCCC+3TM)",  "tw=500",   "B35", "2L D20@150", "D10@200", "1"),
            ("10", "W3 (Lõi 2TM+Thang 2)",  "tw=400",   "B35", "2L D18@150", "D10@200", "1"),
        ]

        total_h = h_title + h_head + len(rows) * h_row

        msp.add_lwpolyline([
            (x0, y0), (x0 + total_w, y0),
            (x0 + total_w, y0 - total_h), (x0, y0 - total_h)
        ], close=True, dxfattribs={'layer': 'DCE_Schedule'})

        t_box = msp.add_text("BẢNG THỐNG KÊ TIẾT DIỆN & CỐT THÉP CỘT VÁCH (B35)",
                             height=280.0, dxfattribs={'layer': 'DCE_Schedule', 'style': 'Dce_Text'})
        t_box.set_placement((x0 + total_w / 2.0, y0 - h_title / 2.0), align=TextEntityAlignment.MIDDLE_CENTER)
        msp.add_line((x0, y0 - h_title), (x0 + total_w, y0 - h_title), dxfattribs={'layer': 'DCE_Schedule'})

        headers = ["STT", "MÃ CK", "TIẾT DIỆN", "BÊ TÔNG", "THÉP DỌC", "THÉP ĐAI", "SL"]
        cur_x = x0
        y_head_mid = y0 - h_title - h_head / 2.0
        for i, h_text in enumerate(headers):
            w = col_w[i]
            t = msp.add_text(h_text, height=200.0, dxfattribs={'layer': 'DCE_Schedule', 'style': 'Dce_Text'})
            t.set_placement((cur_x + w / 2.0, y_head_mid), align=TextEntityAlignment.MIDDLE_CENTER)
            cur_x += w

        msp.add_line((x0, y0 - h_title - h_head), (x0 + total_w, y0 - h_title - h_head), dxfattribs={'layer': 'DCE_Schedule'})

        cur_y = y0 - h_title - h_head
        for r in rows:
            next_y = cur_y - h_row
            cur_x = x0
            for i, val in enumerate(r):
                w = col_w[i]
                t = msp.add_text(val, height=170.0, dxfattribs={'layer': 'DCE_Schedule', 'style': 'Dce_Text'})
                t.set_placement((cur_x + w / 2.0, cur_y - h_row / 2.0), align=TextEntityAlignment.MIDDLE_CENTER)
                cur_x += w
            msp.add_line((x0, next_y), (x0 + total_w, next_y), dxfattribs={'layer': 'DCE_Schedule'})
            cur_y = next_y

        cur_x = x0
        for w in col_w[:-1]:
            cur_x += w
            msp.add_line((cur_x, y0 - h_title), (cur_x, y0 - total_h), dxfattribs={'layer': 'DCE_Schedule'})
        return self

    def render_column_notes(self):
        msp = self.msp
        x0 = 72800.0; y0 = 47000.0
        w = 10600.0; h = 7500.0

        msp.add_lwpolyline([
            (x0, y0), (x0 + w, y0), (x0 + w, y0 - h), (x0, y0 - h)
        ], close=True, dxfattribs={'layer': 'DCE_Note'})

        notes = [
            "GHI CHÚ KỸ THUẬT & QUY ĐỊNH THI CÔNG CỘT VÁCH:",
            "1. Tiêu chuẩn áp dụng: TCVN 5574:2018 & TCVN 9386:2025.",
            "2. Quy mô: 40 tầng nổi + 2 hầm (H~135m). Mặt bằng 57m x 28m.",
            "3. Bê tông: Cột và Vách B35 (M450, Rb=19.5 MPa); Dầm sàn B30.",
            "4. Cốt thép chịu lực: CB500-V (Rs=435 MPa). Thép đai: CB240-T.",
            "5. Tải trọng: Tĩnh tải HTT=1.5 kN/m2; Hoạt tải HT=5.0 kN/m2.",
            "6. Khống chế lực nén: nu = N / (Rb*Ac) <= 0.60.",
            "7. Mốc trắc đạc định vị búng mực theo chuỗi kích thước neo (DCE_Setout).",
            "8. Chi tiết nối thép, neo thép xem bản vẽ KC-CHITIET.",
        ]

        t_title = msp.add_text(notes[0], height=240.0, dxfattribs={'layer': 'Dce_text', 'style': 'Dce_Text'})
        t_title.set_placement((x0 + 400.0, y0 - 600.0), align=TextEntityAlignment.LEFT)

        for idx, line in enumerate(notes[1:]):
            t = msp.add_text(line, height=180.0, dxfattribs={'layer': 'DCE_Note', 'style': 'Dce_Text'})
            t.set_placement((x0 + 400.0, y0 - 1300.0 - idx * 650.0), align=TextEntityAlignment.LEFT)
        return self

    def render_sheet_kc02(self, plan_title="MẶT BẰNG ĐỊNH VỊ CỘT VÁCH TẦNG ĐIỂN HÌNH",
                          scale_label="1/100", sheet_no="KC-02"):
        """Sinh trọn gói bản vẽ Mặt bằng Định vị Cột Vách tầng điển hình (KC-02)."""
        self.render_frame_and_title(plan_title=plan_title, scale_label=scale_label, sheet_no=sheet_no,
                                    sub_title_vn="MẶT BẰNG ĐỊNH VỊ CỘT VÁCH TẦNG ĐIỂN HÌNH",
                                    sub_title_en="TYPICAL FLOOR COLUMN & SHEAR WALL LAYOUT PLAN")
        self.render_slab_boundary()
        self.render_arch_underlay()
        self.render_voids()
        self.render_columns_walls_kc02()
        self.render_beams_reference()
        self.render_axes_and_dims(include_setout=True)
        self.render_column_schedule()
        self.render_column_notes()
        return self

    def render_sheet(self, plan_title="MẶT BẰNG ĐỊNH VỊ CỘT VÁCH TẦNG ĐIỂN HÌNH",
                     scale_label="1/100", sheet_no="KC-02"):
        """Backward-compatible entry point cho KC-02."""
        return self.render_sheet_kc02(plan_title=plan_title, scale_label=scale_label, sheet_no=sheet_no)

    # ------------------------------------------------------------------
    # SHEET KC-03: MẶT BẰNG KẾT CẤU DẦM SÀN TẦNG ĐIỂN HÌNH
    # ------------------------------------------------------------------
    def _draw_beam_double_line(self, x0, y0, x1, y1, b_mm, layer):
        msp = self.msp
        dx = x1 - x0
        dy = y1 - y0
        L = math.hypot(dx, dy)
        if L < 10.0:
            return
        nx = -dy / L * (b_mm / 2.0)
        ny = dx / L * (b_mm / 2.0)
        p1_a = (x0 + nx, y0 + ny)
        p2_a = (x1 + nx, y1 + ny)
        p1_b = (x0 - nx, y0 - ny)
        p2_b = (x1 - nx, y1 - ny)
        msp.add_line(p1_a, p2_a, dxfattribs={'layer': layer})
        msp.add_line(p1_b, p2_b, dxfattribs={'layer': layer})

    def _add_beam_tag(self, mx, my, text, rot_deg=0.0):
        msp = self.msp
        try:
            bref = msp.add_blockref('Dce_KhTenDam', (mx, my), dxfattribs={
                'layer': 'DCE_Name', 'xscale': 100.0, 'yscale': 100.0, 'rotation': rot_deg
            })
            bref.add_auto_attribs({'TENDAM': text, 'TL': '1/100'})
            for att in bref.attribs:
                att.dxf.rotation = 0.0
                att.dxf.insert = (mx, my, 0.0)
                att.dxf.align_point = (mx, my, 0.0)
                att.dxf.halign = 1
                att.dxf.valign = 2
        except Exception:
            t = msp.add_text(text, height=200.0, dxfattribs={'layer': 'DCE_Name', 'style': 'Dce_Text'})
            t.set_placement((mx, my), align=TextEntityAlignment.MIDDLE_CENTER)

    def _add_section_cut(self, x, y, name):
        msp = self.msp
        try:
            bref = msp.add_blockref('Dce_KhMatCat', (x, y), dxfattribs={
                'layer': 'DCE_Name', 'xscale': 100.0, 'yscale': 100.0
            })
            bref.add_auto_attribs({'TENMATCAT': name, 'TL': '1/20'})
        except Exception:
            msp.add_text(f"MC {name}", height=220.0, dxfattribs={'layer': 'DCE_Name'}).set_placement((x, y))

    def render_columns_walls_supports(self):
        msp = self.msp
        for col in self.model['columns']:
            cx = self._wx(col['x']); cy = self._wy(col['y'])
            bx = col['bx'] * SCALE_MM; by = col['by'] * SCALE_MM
            pts = [
                (cx - bx/2, cy - by/2), (cx + bx/2, cy - by/2),
                (cx + bx/2, cy + by/2), (cx - bx/2, cy + by/2)
            ]
            msp.add_lwpolyline(pts, close=True, dxfattribs={'layer': 'DCE_BaoBeTong'})
            self._solid_hatch(pts)

        for w in self.model['shear_walls']:
            x0 = self._wx(w['x0']); y0 = self._wy(w['y0'])
            x1 = self._wx(w['x1']); y1 = self._wy(w['y1'])
            tw = w['tw'] * SCALE_MM
            if abs(x0 - x1) < 50.0:
                pts = [(x0 - tw/2, min(y0, y1)), (x0 + tw/2, min(y0, y1)),
                       (x0 + tw/2, max(y0, y1)), (x0 - tw/2, max(y0, y1))]
            else:
                pts = [(min(x0, x1), y0 - tw/2), (max(x0, x1), y0 - tw/2),
                       (max(x0, x1), y0 + tw/2), (min(x0, x1), y0 + tw/2)]
            msp.add_lwpolyline(pts, close=True, dxfattribs={'layer': 'DCE_BaoBeTong'})
            self._solid_hatch(pts)
        return self

    def render_beams_kc03(self):
        # Dầm chính phương X
        for bm in self.model['beams_x']:
            x0 = self._wx(bm['x0']); y0 = self._wy(bm['y0'])
            x1 = self._wx(bm['x1']); y1 = self._wy(bm['y1'])
            b_mm = bm['b'] * SCALE_MM
            self._draw_beam_double_line(x0, y0, x1, y1, b_mm, 'DCE_MainBeam')
            mx = (x0 + x1) / 2.0
            my = (y0 + y1) / 2.0
            tag = f"{bm['name']} ({bm['size']})"
            self._add_beam_tag(mx, my + 600.0, tag)

        # Dầm chính phương Y
        for bm in self.model['beams_y']:
            x0 = self._wx(bm['x0']); y0 = self._wy(bm['y0'])
            x1 = self._wx(bm['x1']); y1 = self._wy(bm['y1'])
            b_mm = bm['b'] * SCALE_MM
            self._draw_beam_double_line(x0, y0, x1, y1, b_mm, 'DCE_MainBeam')
            mx = (x0 + x1) / 2.0
            my = (y0 + y1) / 2.0
            tag = f"{bm['name']} ({bm['size']})"
            self._add_beam_tag(mx + 600.0, my, tag)

        # Dầm phụ
        for bm in self.model['secondary_beams']:
            x0 = self._wx(bm['x0']); y0 = self._wy(bm['y0'])
            x1 = self._wx(bm['x1']); y1 = self._wy(bm['y1'])
            b_mm = bm['b'] * SCALE_MM
            self._draw_beam_double_line(x0, y0, x1, y1, b_mm, 'DCE_Beam')
            mx = (x0 + x1) / 2.0
            my = (y0 + y1) / 2.0
            tag = f"{bm['name']} ({bm['size']})"
            self._add_beam_tag(mx + 500.0, my, tag)

        # Ký hiệu mặt cắt Dce_KhMatCat
        self._add_section_cut(self._wx(9.53), self._wy(27.00), '1-1')
        self._add_section_cut(self._wx(9.53), self._wy(18.13), '2-2')
        return self

    def render_slabs_and_levels(self):
        msp = self.msp
        for s in self.model['slab_tags']:
            sx = self._wx(s['x']); sy = self._wy(s['y'])
            if s.get('type') == 'drop':
                vw = 3000.0; vh = 3500.0
                pts = [
                    (sx - vw/2, sy - vh/2), (sx + vw/2, sy - vh/2),
                    (sx + vw/2, sy + vh/2), (sx - vw/2, sy + vh/2)
                ]
                msp.add_lwpolyline(pts, close=True, dxfattribs={'layer': 'DCE_BaoBeTong'})
                try:
                    bref = msp.add_blockref('DCE_Drop mark', (sx, sy), dxfattribs={
                        'layer': 'DCE_Symbol', 'xscale': 100.0, 'yscale': 100.0
                    })
                    bref.add_auto_attribs({'50': s['drop']})
                except Exception:
                    msp.add_text(f"HẠ ÂM {s['drop']}", height=180.0, dxfattribs={'layer': 'DCE_Name'}).set_placement((sx, sy))
            else:
                try:
                    bref = msp.add_blockref('DCE_Slab tag', (sx, sy), dxfattribs={
                        'layer': 'DCE_Symbol', 'xscale': 100.0, 'yscale': 100.0
                    })
                    bref.add_auto_attribs({'200': '150'})
                except Exception:
                    msp.add_text(s['label'], height=180.0, dxfattribs={'layer': 'DCE_Name'}).set_placement((sx, sy))

        # Cao độ mặt sàn
        cx = self._wx(28.29); cy = self._wy(20.50)
        try:
            bref = msp.add_blockref('Dce_CaoTrinh', (cx, cy), dxfattribs={
                'layer': 'DCE_Symbol', 'xscale': 100.0, 'yscale': 100.0
            })
            bref.add_auto_attribs({'CT': '+12.600'})
        except Exception:
            msp.add_text("COTE +12.600", height=200.0, dxfattribs={'layer': 'DCE_Name'}).set_placement((cx, cy))
        return self

    def render_beam_schedule(self):
        msp = self.msp
        x0 = 72800.0; y0 = 57500.0
        col_w = [800.0, 1600.0, 1800.0, 1400.0, 2000.0, 1600.0, 800.0, 1600.0]
        total_w = sum(col_w)
        h_title = 1000.0; h_head = 700.0; h_row = 650.0

        rows = [
            ["1", "D1A, D1D", "400x800", "B30", "Dầm khung biên", "6.35 - 9.33", "16", "Thép CB500-V"],
            ["2", "D1B, D1C", "500x900", "B30", "Dầm khung chính", "6.35 - 9.33", "12", "Thép CB500-V"],
            ["3", "D2", "300x700", "B30", "Dầm khung ngang", "8.37 - 9.87", "24", "Thép CB500-V"],
            ["4", "DP1", "250x600", "B30", "Dầm phụ chia ô", "8.37 - 9.07", "8", "Thép CB500-V"],
            ["5", "DG1, DG2", "400/500x800", "B30", "Dầm giằng vách", "2.70 - 3.40", "6", "Gia cường đai"],
            ["6", "DL1", "200x400", "B30", "Dầm lanh tô cửa", "1.60", "3", "Đai chống nứt"],
            ["7", "S1", "h=150", "B30", "Sàn điển hình", "3.17x8.37", "Toàn sàn", "Thép 2 lớp D10a150"],
            ["8", "S2", "h=120", "B30", "Sàn WC / Ban công", "Khu WC, logia", "4 ô", "Hạ âm -0.050m"],
        ]

        total_h = h_title + h_head + len(rows) * h_row

        msp.add_lwpolyline([
            (x0, y0), (x0 + total_w, y0),
            (x0 + total_w, y0 - total_h), (x0, y0 - total_h)
        ], close=True, dxfattribs={'layer': 'DCE_Schedule'})

        t_box = msp.add_text("BẢNG THỐNG KÊ TIẾT DIỆN DẦM SÀN TẦNG ĐIỂN HÌNH (B30)",
                             height=280.0, dxfattribs={'layer': 'DCE_Schedule', 'style': 'Dce_Text'})
        t_box.set_placement((x0 + total_w / 2.0, y0 - h_title / 2.0), align=TextEntityAlignment.MIDDLE_CENTER)
        msp.add_line((x0, y0 - h_title), (x0 + total_w, y0 - h_title), dxfattribs={'layer': 'DCE_Schedule'})

        headers = ["STT", "MÃ DẦM", "TIẾT DIỆN", "BÊ TÔNG", "VỊ TRÍ", "NHỊP L (m)", "SL", "GHI CHÚ"]
        cur_x = x0
        y_head_mid = y0 - h_title - h_head / 2.0
        for i, h_text in enumerate(headers):
            w = col_w[i]
            t = msp.add_text(h_text, height=200.0, dxfattribs={'layer': 'DCE_Schedule', 'style': 'Dce_Text'})
            t.set_placement((cur_x + w / 2.0, y_head_mid), align=TextEntityAlignment.MIDDLE_CENTER)
            cur_x += w

        msp.add_line((x0, y0 - h_title - h_head), (x0 + total_w, y0 - h_title - h_head), dxfattribs={'layer': 'DCE_Schedule'})

        cur_y = y0 - h_title - h_head
        for r in rows:
            next_y = cur_y - h_row
            cur_x = x0
            for i, val in enumerate(r):
                w = col_w[i]
                t = msp.add_text(val, height=170.0, dxfattribs={'layer': 'DCE_Schedule', 'style': 'Dce_Text'})
                t.set_placement((cur_x + w / 2.0, cur_y - h_row / 2.0), align=TextEntityAlignment.MIDDLE_CENTER)
                cur_x += w
            msp.add_line((x0, next_y), (x0 + total_w, next_y), dxfattribs={'layer': 'DCE_Schedule'})
            cur_y = next_y

        cur_x = x0
        for w in col_w[:-1]:
            cur_x += w
            msp.add_line((cur_x, y0 - h_title), (cur_x, y0 - total_h), dxfattribs={'layer': 'DCE_Schedule'})
        return self

    def render_beam_notes(self):
        msp = self.msp
        x0 = 72800.0; y0 = 47500.0
        w = 11600.0; h = 7500.0
        msp.add_lwpolyline([
            (x0, y0), (x0 + w, y0), (x0 + w, y0 - h), (x0, y0 - h)
        ], close=True, dxfattribs={'layer': 'DCE_Note'})

        notes = [
            "GHI CHÚ KỸ THUẬT & CHỈ DẪN THI CÔNG DẦM SÀN:",
            "1. Tiêu chuẩn áp dụng: TCVN 5574:2018 & TCVN 2737:2023.",
            "2. Bê tông dầm sàn: B30 (M400, Rb=17.0 MPa, Rbt=1.15 MPa, Eb=32.500 MPa).",
            "3. Cốt thép chịu lực: Thép thanh vằn CB500-V (Rs=435 MPa). Thép đai: CB240-T.",
            "4. Chiều dày sàn điển hình hs = 150mm; sàn vệ sinh hạ âm -50mm, ban công -80mm.",
            "5. Lớp bê tông bảo vệ: Dầm a_bv = 25mm, Sàn a_bv = 20mm.",
            "6. Tải trọng sàn: Tĩnh tải hoàn thiện HTT = 1.5 kN/m2; Hoạt tải sàn HT = 5.0 kN/m2.",
            "7. Độ võng sàn f_max <= L/250; bề rộng khe nứt khống chế a_crc <= 0.3mm.",
            "8. Chi tiết khai triển cốt thép dầm liên tục xem các bản vẽ KC-04 đến KC-12.",
        ]

        t_title = msp.add_text(notes[0], height=240.0, dxfattribs={'layer': 'Dce_text', 'style': 'Dce_Text'})
        t_title.set_placement((x0 + 400.0, y0 - 600.0), align=TextEntityAlignment.LEFT)

        for idx, line in enumerate(notes[1:]):
            t = msp.add_text(line, height=180.0, dxfattribs={'layer': 'DCE_Note', 'style': 'Dce_Text'})
            t.set_placement((x0 + 400.0, y0 - 1300.0 - idx * 650.0), align=TextEntityAlignment.LEFT)
        return self

    def render_sheet_kc03(self, plan_title="MẶT BẰNG KẾT CẤU DẦM SÀN TẦNG ĐIỂN HÌNH",
                          scale_label="1/100", sheet_no="KC-03"):
        """Sinh trọn gói bản vẽ Mặt bằng Kết cấu Dầm Sàn tầng điển hình (KC-03)."""
        self.render_frame_and_title(plan_title=plan_title, scale_label=scale_label, sheet_no=sheet_no,
                                    sub_title_vn="MẶT BẰNG KẾT CẤU DẦM SÀN TẦNG ĐIỂN HÌNH",
                                    sub_title_en="TYPICAL FLOOR BEAM & SLAB STRUCTURAL PLAN")
        self.render_slab_boundary()
        self.render_voids()
        self.render_columns_walls_supports()
        self.render_beams_kc03()
        self.render_slabs_and_levels()
        self.render_axes_and_dims(include_setout=False)
        self.render_beam_schedule()
        self.render_beam_notes()
        return self

    # ------------------------------------------------------------------
    # SHEET KC-01: TỔNG MẶT BẰNG KẾT CẤU & ĐỊNH VỊ CÔNG TRÌNH (1/200)
    # ------------------------------------------------------------------
    def render_north_arrow(self, cx, cy, radius=1200.0):
        msp = self.msp
        # Vòng tròn kim chỉ nam
        msp.add_circle((cx, cy), radius=radius, dxfattribs={'layer': 'DCE_Symbol'})
        # Mũi tên chỉ hướng Bắc
        tip = (cx, cy + radius * 1.3)
        left = (cx - radius * 0.45, cy - radius * 0.45)
        right = (cx + radius * 0.45, cy - radius * 0.45)
        mid = (cx, cy)
        # Nửa đen (solid hatch bên trái)
        pts_left = [mid, left, tip]
        msp.add_lwpolyline(pts_left, close=True, dxfattribs={'layer': 'DCE_Symbol'})
        self._solid_hatch(pts_left, layer='DCE_Symbol')
        # Nửa trắng bên phải
        pts_right = [mid, right, tip]
        msp.add_lwpolyline(pts_right, close=True, dxfattribs={'layer': 'DCE_Symbol'})
        # Chữ B (Bắc / North)
        t = msp.add_text("B", height=350.0, dxfattribs={'layer': 'Dce_text', 'style': 'Dce_Text'})
        t.set_placement((cx, cy + radius * 1.5), align=TextEntityAlignment.BOTTOM_CENTER)

    def render_site_and_footprint_kc01(self):
        msp = self.msp
        sd = self.model['site_data']
        # Tọa độ ranh đất trong hệ bản vẽ
        # Đặt tâm khu đất tại trung tâm vùng đồ họa A1
        site_ox = self.ox - sd['bldg_offset_x'] * SCALE_MM
        site_oy = self.oy - sd['bldg_offset_y'] * SCALE_MM
        lot_w_mm = sd['lot_w'] * SCALE_MM
        lot_h_mm = sd['lot_h'] * SCALE_MM

        # 1. Ranh đất pháp lý
        p_m1 = (site_ox, site_oy)
        p_m2 = (site_ox + lot_w_mm, site_oy)
        p_m3 = (site_ox + lot_w_mm, site_oy + lot_h_mm)
        p_m4 = (site_ox, site_oy + lot_h_mm)
        pts_lot = [p_m1, p_m2, p_m3, p_m4]
        msp.add_lwpolyline(pts_lot, close=True, dxfattribs={'layer': 'DCE_RanhDat'})

        # Nhãn mốc ranh M1..M4
        m_labels = [("M1", p_m1, (-600, -600)), ("M2", p_m2, (600, -600)),
                    ("M3", p_m3, (600, 600)),   ("M4", p_m4, (-600, 600))]
        for lbl, pt, off in m_labels:
            msp.add_circle(pt, radius=350.0, dxfattribs={'layer': 'DCE_RanhDat'})
            t = msp.add_text(lbl, height=240.0, dxfattribs={'layer': 'Dce_text', 'style': 'Dce_Text'})
            t.set_placement((pt[0] + off[0], pt[1] + off[1]), align=TextEntityAlignment.MIDDLE_CENTER)

        # 2. Chỉ giới xây dựng (khoảng lùi)
        sb_f = sd['setback_front'] * SCALE_MM
        sb_r = sd['setback_rear'] * SCALE_MM
        sb_s = sd['setback_side'] * SCALE_MM
        pts_sb = [
            (site_ox + sb_s, site_oy + sb_f),
            (site_ox + lot_w_mm - sb_s, site_oy + sb_f),
            (site_ox + lot_w_mm - sb_s, site_oy + lot_h_mm - sb_r),
            (site_ox + sb_s, site_oy + lot_h_mm - sb_r)
        ]
        msp.add_lwpolyline(pts_sb, close=True, dxfattribs={'layer': 'DCE_ChiGioi'})

        # Text chỉ giới
        t_cg = msp.add_text("CHỈ GIỚI XÂY DỰNG (KHOẢNG LÙI TRƯỚC 6.0m, SAU 3.0m, HÔNG 2.5m)",
                            height=200.0, dxfattribs={'layer': 'DCE_ChiGioi', 'style': 'Dce_Text'})
        t_cg.set_placement((site_ox + lot_w_mm / 2.0, site_oy + sb_f - 400.0), align=TextEntityAlignment.TOP_CENTER)

        # 3. Đường giao thông tiếp giáp
        # Tuyến đường D1 phía Nam
        msp.add_line((site_ox - 8000.0, site_oy - 4500.0), (site_ox + lot_w_mm + 8000.0, site_oy - 4500.0),
                     dxfattribs={'layer': 'DCE_Road'})
        msp.add_line((site_ox - 8000.0, site_oy - 15500.0), (site_ox + lot_w_mm + 8000.0, site_oy - 15500.0),
                     dxfattribs={'layer': 'DCE_Road'})
        t_rd1 = msp.add_text("ĐƯỜNG D1 (LỘ GIỚI 20.0m — LÒNG ĐƯỜNG 11.0m, VỈA HÈ 4.5m)",
                             height=280.0, dxfattribs={'layer': 'DCE_Road', 'style': 'Dce_Text'})
        t_rd1.set_placement((site_ox + lot_w_mm / 2.0, site_oy - 10000.0), align=TextEntityAlignment.MIDDLE_CENTER)

        # Tuyến đường N2 phía Tây
        msp.add_line((site_ox - 3000.0, site_oy - 15500.0), (site_ox - 3000.0, site_oy + lot_h_mm + 6000.0),
                     dxfattribs={'layer': 'DCE_Road'})
        msp.add_line((site_ox - 11000.0, site_oy - 15500.0), (site_ox - 11000.0, site_oy + lot_h_mm + 6000.0),
                     dxfattribs={'layer': 'DCE_Road'})
        t_rd2 = msp.add_text("ĐƯỜNG N2 (LỘ GIỚI 14.0m)",
                             height=260.0, dxfattribs={'layer': 'DCE_Road', 'style': 'Dce_Text'})
        t_rd2.set_placement((site_ox - 7000.0, site_oy + lot_h_mm / 2.0), align=TextEntityAlignment.MIDDLE_CENTER)

        # 4. Footprint Tháp công trình 57m x 28m
        bldg_pts = [
            (self.ox, self.oy), (self.ox + self.L, self.oy),
            (self.ox + self.L, self.oy + self.B), (self.ox, self.oy + self.B)
        ]
        msp.add_lwpolyline(bldg_pts, close=True, dxfattribs={'layer': 'DCE_BaoBeTong'})

        # Dim định vị công trình so với ranh đất
        self._add_linear_dim((site_ox, self.oy), (self.ox, self.oy), 0.0)
        self._add_linear_dim((self.ox + self.L, self.oy), (site_ox + lot_w_mm, self.oy), 0.0)
        self._add_linear_dim((self.ox, site_oy), (self.ox, self.oy), 90.0)
        self._add_linear_dim((self.ox, self.oy + self.B), (self.ox, site_oy + lot_h_mm), 90.0)

        # 5. Ramps hầm
        for r in sd['ramps']:
            rx = site_ox + r['x'] * SCALE_MM; ry = site_oy + r['y'] * SCALE_MM
            rw = r['w'] * SCALE_MM; rl = r['l'] * SCALE_MM
            msp.add_lwpolyline([(rx, ry), (rx + rw, ry), (rx + rw, ry + rl), (rx, ry + rl)],
                               close=True, dxfattribs={'layer': 'DCE_BaoBeTong'})
            msp.add_line((rx + rw / 2.0, ry), (rx + rw / 2.0, ry + rl), dxfattribs={'layer': 'DCE_Truc'})
            t_rm = msp.add_text(r['name'], height=180.0, dxfattribs={'layer': 'Dce_text', 'style': 'Dce_Text'})
            t_rm.set_placement((rx + rw / 2.0, ry + rl / 2.0), align=TextEntityAlignment.MIDDLE_CENTER)

        # 6. Kim chỉ nam
        self.render_north_arrow(site_ox + 4000.0, site_oy + lot_h_mm - 4000.0)
        return self

    def render_master_schedule(self):
        msp = self.msp
        x0 = 72800.0; y0 = 57500.0
        col_w = [800.0, 1600.0, 2600.0, 2600.0, 1400.0, 2000.0]
        total_w = sum(col_w)
        h_title = 1000.0; h_head = 700.0; h_row = 650.0

        rows = [
            ["1", "M1", "1,198,200.000", "604,300.000", "+2.200", "Góc Tây Nam ranh đất"],
            ["2", "M2", "1,198,275.000", "604,300.000", "+2.250", "Góc Đông Nam ranh đất"],
            ["3", "M3", "1,198,275.000", "604,345.000", "+2.300", "Góc Đông Bắc ranh đất"],
            ["4", "M4", "1,198,200.000", "604,345.000", "+2.250", "Góc Tây Bắc ranh đất"],
            ["5", "Gốc 1-D", "1,198,209.000", "604,308.500", "±0.000", "Gốc tim trục tháp"],
            ["6", "Gốc 11-D","1,198,266.000", "604,308.500", "±0.000", "Góc Đông Nam khối tháp"],
            ["7", "Gốc 11-A","1,198,266.000", "604,336.500", "±0.000", "Góc Đông Bắc khối tháp"],
            ["8", "Gốc 1-A", "1,198,209.000", "604,336.500", "±0.000", "Góc Tây Bắc khối tháp"],
        ]

        total_h = h_title + h_head + len(rows) * h_row

        msp.add_lwpolyline([
            (x0, y0), (x0 + total_w, y0),
            (x0 + total_w, y0 - total_h), (x0, y0 - total_h)
        ], close=True, dxfattribs={'layer': 'DCE_Schedule'})

        t_box = msp.add_text("BẢNG TỌA ĐỘ MỐC RANH ĐẤT & TIM TRỤC (HỆ VN-2000)",
                             height=280.0, dxfattribs={'layer': 'DCE_Schedule', 'style': 'Dce_Text'})
        t_box.set_placement((x0 + total_w / 2.0, y0 - h_title / 2.0), align=TextEntityAlignment.MIDDLE_CENTER)
        msp.add_line((x0, y0 - h_title), (x0 + total_w, y0 - h_title), dxfattribs={'layer': 'DCE_Schedule'})

        headers = ["STT", "ĐIỂM MỐC", "TỌA ĐỘ X (N)", "TỌA ĐỘ Y (E)", "CAO ĐỘ Z", "GHI CHÚ"]
        cur_x = x0
        y_head_mid = y0 - h_title - h_head / 2.0
        for i, h_text in enumerate(headers):
            w = col_w[i]
            t = msp.add_text(h_text, height=200.0, dxfattribs={'layer': 'DCE_Schedule', 'style': 'Dce_Text'})
            t.set_placement((cur_x + w / 2.0, y_head_mid), align=TextEntityAlignment.MIDDLE_CENTER)
            cur_x += w

        msp.add_line((x0, y0 - h_title - h_head), (x0 + total_w, y0 - h_title - h_head), dxfattribs={'layer': 'DCE_Schedule'})

        cur_y = y0 - h_title - h_head
        for r in rows:
            next_y = cur_y - h_row
            cur_x = x0
            for i, val in enumerate(r):
                w = col_w[i]
                t = msp.add_text(val, height=170.0, dxfattribs={'layer': 'DCE_Schedule', 'style': 'Dce_Text'})
                t.set_placement((cur_x + w / 2.0, cur_y - h_row / 2.0), align=TextEntityAlignment.MIDDLE_CENTER)
                cur_x += w
            msp.add_line((x0, next_y), (x0 + total_w, next_y), dxfattribs={'layer': 'DCE_Schedule'})
            cur_y = next_y

        cur_x = x0
        for w in col_w[:-1]:
            cur_x += w
            msp.add_line((cur_x, y0 - h_title), (cur_x, y0 - total_h), dxfattribs={'layer': 'DCE_Schedule'})
        return self

    def render_master_notes(self):
        msp = self.msp
        x0 = 72800.0; y0 = 47500.0
        w = 11000.0; h = 7500.0
        msp.add_lwpolyline([
            (x0, y0), (x0 + w, y0), (x0 + w, y0 - h), (x0, y0 - h)
        ], close=True, dxfattribs={'layer': 'DCE_Note'})

        notes = [
            "CHỈ TIÊU QUY HOẠCH & QUY CHUẨN ĐỊNH VỊ TỔNG THỂ:",
            "1. Hệ tọa độ quốc gia: VN-2000, Kinh tuyến trục 105°45', múi chiếu 3°.",
            "2. Hệ cao độ quốc gia: Hòn Dấu (Hải Phòng). Cao độ ±0.000 = +2.500m QG.",
            "3. Diện tích khu đất: 3,375.0 m2 (75.0m x 45.0m).",
            "4. Diện tích xây dựng khối đế: 1,596.0 m2 (Mật độ xây dựng: 47.3% <= 50%).",
            "5. Mật độ xây dựng khối tháp: 38.2% <= 40%.",
            "6. Tổng diện tích sàn (GFA): ~63,840 m2 (FAR ~ 18.9). Tầng cao: 40 tầng + 2 hầm.",
            "7. Khoảng lùi công trình: Lùi trước 6.0m, lùi sau 3.0m, lùi 2 bên hông 2.5m.",
            "8. Mốc định vị trắc đạc bàn giao hiện trường trước khi ép cọc/thi công tường vây.",
        ]

        t_title = msp.add_text(notes[0], height=240.0, dxfattribs={'layer': 'Dce_text', 'style': 'Dce_Text'})
        t_title.set_placement((x0 + 400.0, y0 - 600.0), align=TextEntityAlignment.LEFT)

        for idx, line in enumerate(notes[1:]):
            t = msp.add_text(line, height=180.0, dxfattribs={'layer': 'DCE_Note', 'style': 'Dce_Text'})
            t.set_placement((x0 + 400.0, y0 - 1300.0 - idx * 650.0), align=TextEntityAlignment.LEFT)
        return self

    def render_sheet_kc01(self, plan_title="TỔNG MẶT BẰNG KẾT CẤU & ĐỊNH VỊ CÔNG TRÌNH",
                          scale_label="1/200", sheet_no="KC-01"):
        """Sinh trọn gói bản vẽ Tổng Mặt bằng Kết cấu & Định vị Công trình (KC-01)."""
        self.render_frame_and_title(plan_title=plan_title, scale_label=scale_label, sheet_no=sheet_no,
                                    sub_title_vn="TỔNG MẶT BẰNG KẾT CẤU & ĐỊNH VỊ CÔNG TRÌNH",
                                    sub_title_en="MASTER STRUCTURAL SETTING-OUT PLAN")
        self.render_site_and_footprint_kc01()
        self.render_axes_and_dims(include_setout=False)
        self.render_columns_walls_supports()
        self.render_master_schedule()
        self.render_master_notes()
        return self

    # ------------------------------------------------------------------
    # SAVE & AUDIT
    # ------------------------------------------------------------------
    def save(self, output_dxf_path: str):
        auditor = self.doc.audit()
        print(f"[*] Audit file DXF ({output_dxf_path}):")
        print(f"    - Lỗi (Errors): {len(auditor.errors)}")
        print(f"    - Hiệu chỉnh tự động (Fixes): {len(auditor.fixes)}")
        if auditor.errors:
            for err in auditor.errors[:5]:
                print(f"    [!] {err}")
        os.makedirs(os.path.dirname(os.path.abspath(output_dxf_path)), exist_ok=True)
        self.doc.saveas(output_dxf_path)
        print(f"[OK] Bản vẽ chuẩn DCE Pro đã được lưu thành công tại:")
        print(f"     -> {output_dxf_path}")
        return self


# ===========================================================================
# TIỆN ÍCH XUẤT BẢN VẼ
# ===========================================================================
def export_dce_plan(output_dxf_path: str, template_path: Optional[str] = None,
                    pdf_path: Optional[str] = None, sheet_type: str = "KC-02",
                    model_json_path: Optional[str] = None):
    arch_lines = []
    if pdf_path and os.path.isfile(pdf_path):
        try:
            import fitz
            doc = fitz.open(pdf_path)
            page = doc[0]
            drawings = page.get_drawings()
            scale = 0.055
            X0, Y0 = 60.36, 154.16
            for d in drawings:
                for it in d['items']:
                    if it[0] == 'l':
                        p1, p2 = it[1], it[2]
                        x1 = (p1.x - X0) * scale
                        x2 = (p2.x - X0) * scale
                        y1 = 28.00 - (p1.y - Y0) * scale
                        y2 = 28.00 - (p2.y - Y0) * scale
                        if (-0.5 <= x1 <= 57.5 and -0.5 <= x2 <= 57.5 and
                                -0.5 <= y1 <= 28.5 and -0.5 <= y2 <= 28.5):
                            if math.hypot(x2 - x1, y2 - y1) >= 0.3:
                                arch_lines.append((x1, y1, x2, y2))
        except Exception as ex:
            print(f"[!] Bỏ qua đọc vector pdf: {ex}")

    t_path = Path(template_path) if template_path else None
    if model_json_path and os.path.isfile(model_json_path):
        import json as _json
        with open(model_json_path, 'r', encoding='utf-8') as _f:
            model = _json.load(_f)
    else:
        model = build_structural_model()

    st = sheet_type.upper()
    if st in ['KC-01', 'KC01', 'MASTER', 'TONG_THE']:
        engine = DcePlanEngine(model=model, template_path=t_path, arch_lines=arch_lines)
        engine.setup()
        engine.render_sheet_kc01()
        engine.save(output_dxf_path)
        return engine

    elif st in ['KC-03', 'KC03', 'DAM_SAN', 'BEAMS']:
        engine = DcePlanEngine(model=model, template_path=t_path, arch_lines=arch_lines)
        engine.setup()
        engine.render_sheet_kc03()
        engine.save(output_dxf_path)
        return engine

    elif st in ['ALL', 'FULL']:
        out_dir = os.path.dirname(os.path.abspath(output_dxf_path))
        p_kc01 = os.path.join(out_dir, "mat_bang_tong_the_ket_cau.dxf")
        p_kc02 = os.path.join(out_dir, "mat_bang_cot_vach_tang_dien_hinh.dxf")
        p_kc03 = os.path.join(out_dir, "mat_bang_dam_san_tang_dien_hinh.dxf")

        print("=== [1/3] ĐANG XUẤT SHEET KC-01: TỔNG MẶT BẰNG KẾT CẤU ===")
        e1 = DcePlanEngine(model=model, template_path=t_path, arch_lines=arch_lines)
        e1.setup()
        e1.render_sheet_kc01()
        e1.save(p_kc01)

        print("=== [2/3] ĐANG XUẤT SHEET KC-02: MẶT BẰNG ĐỊNH VỊ CỘT VÁCH ===")
        e2 = DcePlanEngine(model=model, template_path=t_path, arch_lines=arch_lines)
        e2.setup()
        e2.render_sheet_kc02()
        e2.save(p_kc02)

        print("=== [3/3] ĐANG XUẤT SHEET KC-03: MẶT BẰNG KẾT CẤU DẦM SÀN ===")
        e3 = DcePlanEngine(model=model, template_path=t_path, arch_lines=arch_lines)
        e3.setup()
        e3.render_sheet_kc03()
        e3.save(p_kc03)
        return e3

    else:
        # Mặc định: KC-02
        engine = DcePlanEngine(model=model, template_path=t_path, arch_lines=arch_lines)
        engine.setup()
        engine.render_sheet_kc02()
        engine.save(output_dxf_path)
        return engine


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="DCE Pro Multi-Sheet Plan Engine")
    parser.add_argument('--output', '-o', default=r'g:\My Drive\Google AI Studio\01_Projects\15.TEST\04_Deliverables_ToTrinh\mat_bang_cot_vach_tang_dien_hinh.dxf', help="Path to output DXF")
    parser.add_argument('--template', '-t', default=r'g:\My Drive\Google AI Studio\.agents\skills\Technical_Illustrator\cad_integration\templates\DCE_Master_Seed_Template.dxf', help="Path to DCE seed template")
    parser.add_argument('--pdf', '-p', default=r'g:\My Drive\Google AI Studio\01_Projects\15.TEST\01_Input_CAD_PDF\a.pdf', help="Path to architectural PDF")
    parser.add_argument('--sheet', '-s', default='KC-02', choices=['KC-01', 'KC-02', 'KC-03', 'all'], help="Sheet type to generate")
    parser.add_argument('--input-json', '-i', default=None, help="Optional structural model JSON file overriding built-in demo model")
    args = parser.parse_args()
    export_dce_plan(args.output, args.template, args.pdf, sheet_type=args.sheet, model_json_path=args.input_json)
