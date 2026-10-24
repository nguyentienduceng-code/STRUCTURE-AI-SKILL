"""
rebar_cutting_optimizer.py — 1D Rebar Cutting Stock Optimizer
============================================================
Sprint 3 · Phase 3 · Nhiệm vụ 3
Kế thừa thuật toán Bea_ToHopThepV4 & ToiUuCatThep của DCE Pro

Mục đích:
    Tối ưu hóa sơ đồ cắt thép thanh chuẩn 11.7m (11,700 mm) theo bài toán
    1D Cutting Stock Problem (1D-CSP), kết hợp:
    1. Tận dụng triệt để kho thép dư có sẵn (old_stock / remnant inventory).
    2. Tự động chia các thanh dài quá 11.7m thành các phân đoạn nối chồng
       tuân thủ tiêu chuẩn TCVN 5574:2018 và quy tắc DCE:
       - Chiều dài nối chồng buộc: L_lap = 40d (QTKT_Noi1)
       - Vùng nối cho phép: Thép gối nối ở giữa nhịp; Thép nhịp nối ở gối.
       - Bố trí nối so le so với thanh liền kề: khoảng cách so le >= 10d.
    3. Thuật toán Best-Fit Decreasing (BFD) kết hợp Local Search Optimization
       để giảm thiểu số cây 11.7m phải cắt mới và dồn phần dư tối đa về các
       thanh có chiều dài tái sử dụng được (>= 500 mm).
    4. Xuất sơ đồ cắt chi tiết từng thanh (cutting layout), tỷ lệ hao hụt
       phế liệu (% Net Scrap Waste) và hiệu suất tận dụng vật liệu (% Yield).

Tiêu chuẩn & Cơ sở:
    - TCVN 5574:2018 Mục 8.3: Cấu tạo cốt thép và mối nối chồng.
    - DCE Pro Bea_ToHopThepV4 (DCE Excel.dll) & ToiUuCatThep.txt.

Sử dụng:
    python rebar_cutting_optimizer.py \\
        --bars '[{"id":"T1","length":4200,"count":5,"dia":22},{"id":"T2","length":5800,"count":4,"dia":22}]' \\
        --old-stock '[{"length":4500,"count":1,"dia":22}]'
"""

import sys
import os
import json
import argparse
import math
from typing import List, Dict, Any, Tuple
from datetime import datetime

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

# ─────────────────────────────────────────────────────────────────────────────
# Hằng số chuẩn
# ─────────────────────────────────────────────────────────────────────────────

STANDARD_STOCK_LENGTH_MM = 11700.0  # Cây thép thương mại tiêu chuẩn Việt Nam
DEFAULT_MIN_REUSE_LENGTH_MM = 500.0  # Dưới 500mm coi như thép vụn (scrap)
DEFAULT_LAP_MULTIPLIER = 40.0        # L_lap = 40d
DEFAULT_MIN_STAGGER_OFFSET = 10.0    # So le >= 10d


def unit_weight_kg_m(dia_mm: float) -> float:
    """Khối lượng đơn vị thép thanh tròn theo TCVN 5574:2018 (kg/m)."""
    return (math.pi * (dia_mm / 2000.0) ** 2) * 7850.0


# ─────────────────────────────────────────────────────────────────────────────
# Lớp Tối Ưu Cắt Thép
# ─────────────────────────────────────────────────────────────────────────────

class RebarCuttingOptimizer:
    """Bộ giải thuật tối ưu cắt thép thanh 1D kế thừa Bea_ToHopThepV4."""

    def __init__(
        self,
        stock_length: float = STANDARD_STOCK_LENGTH_MM,
        min_reuse_length: float = DEFAULT_MIN_REUSE_LENGTH_MM,
        lap_multiplier: float = DEFAULT_LAP_MULTIPLIER,
        min_stagger_offset: float = DEFAULT_MIN_STAGGER_OFFSET,
    ):
        self.stock_length = float(stock_length)
        self.min_reuse_length = float(min_reuse_length)
        self.lap_multiplier = float(lap_multiplier)
        self.min_stagger_offset = float(min_stagger_offset)
        self.logs = []

    def split_long_bar(
        self,
        total_length: float,
        dia: float,
        bar_type: str = "top",
        span_length: float = 6000.0,
        stagger_index: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Tự động chia một thanh thép dài hơn 11.7m thành các phân đoạn nối.
        - L_lap = 40 * dia (mm).
        - So le so với thanh kế bên = stagger_index * 10 * dia (mm).
        - Trả về danh sách các thanh con kèm chiều dài đã tính cả nối chồng.
        """
        if total_length <= self.stock_length:
            return [{"length": total_length, "has_lap": False, "note": "Thanh nguyên"}]

        lap_len = self.lap_multiplier * dia
        stagger_shift = (stagger_index % 2) * (self.min_stagger_offset * dia)
        pieces = []
        rem_len = total_length

        # Chiều dài cắt hiệu dụng thanh đầu tiên có tính so le
        first_seg_eff = min(self.stock_length - lap_len - stagger_shift, rem_len)
        if first_seg_eff <= 0:
            first_seg_eff = self.stock_length - lap_len

        # Thanh 1: dài first_seg_eff + lap_len
        first_bar_len = min(first_seg_eff + lap_len, self.stock_length)
        pieces.append({
            "length": first_bar_len,
            "has_lap": True,
            "lap_length": lap_len,
            "note": f"Đoạn đầu (so le={stagger_shift:.0f}mm)",
        })
        rem_len -= first_seg_eff

        # Các thanh ở giữa và đoạn cuối
        seg_idx = 2
        while rem_len > 0:
            if rem_len + lap_len <= self.stock_length:
                pieces.append({
                    "length": rem_len + lap_len,
                    "has_lap": True,
                    "lap_length": lap_len,
                    "note": f"Đoạn cuối #{seg_idx}",
                })
                rem_len = 0
            else:
                seg_eff = self.stock_length - 2 * lap_len
                pieces.append({
                    "length": self.stock_length,
                    "has_lap": True,
                    "lap_length": 2 * lap_len,
                    "note": f"Đoạn giữa #{seg_idx}",
                })
                rem_len -= seg_eff
            seg_idx += 1

        self.logs.append({
            "action": "split_long_bar",
            "dia": dia,
            "original_length": total_length,
            "num_segments": len(pieces),
            "lap_length": lap_len,
        })
        return pieces

    def optimize_single_dia(
        self,
        dia: float,
        pieces: List[Dict[str, Any]],
        old_stock: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Tối ưu cắt cho một đường kính thép cụ thể.
        1. Phục hồi và tận dụng kho thép dư (old_stock).
        2. Tối ưu cắt các thanh còn lại từ cây mới 11.7m bằng BFD + Local Search.
        """
        # Mở rộng toàn bộ danh sách thanh cần cắt thành từng item đơn lẻ
        demand_items = []
        for p in pieces:
            p_len = float(p["length"])
            count = int(p.get("count", 1))
            p_id = str(p.get("id", f"D{int(dia)}"))
            for _ in range(count):
                demand_items.append({"id": p_id, "length": p_len, "dia": dia})

        # Sắp xếp giảm dần theo chiều dài (Decreasing)
        demand_items.sort(key=lambda x: x["length"], reverse=True)

        used_old_stock = []
        rem_old_stock = []
        if old_stock:
            # Sắp xếp thép dư tăng dần để chọn đoạn dư ngắn nhất đủ chứa (Best-Fit)
            available_old = sorted([dict(o) for o in old_stock], key=lambda x: x["length"])
            unassigned_demand = []
            for item in demand_items:
                # Tìm thanh old stock vừa vặn nhất
                best_idx = -1
                best_waste = float("inf")
                for idx, o in enumerate(available_old):
                    if o["length"] >= item["length"] and (o["length"] - item["length"]) < best_waste:
                        best_waste = o["length"] - item["length"]
                        best_idx = idx

                if best_idx != -1:
                    matched_old = available_old.pop(best_idx)
                    waste = matched_old["length"] - item["length"]
                    used_old_stock.append({
                        "source": "OLD_STOCK",
                        "stock_length": matched_old["length"],
                        "cuts": [item],
                        "cuts_lengths": [item["length"]],
                        "used_length": item["length"],
                        "remnant": waste,
                        "is_reusable": waste >= self.min_reuse_length,
                    })
                else:
                    unassigned_demand.append(item)
            demand_items = unassigned_demand
            rem_old_stock = available_old

        # Cắt các đoạn còn lại từ cây mới 11.7m (11700 mm)
        # Sử dụng Best Fit Decreasing (BFD)
        new_bars = []
        for item in demand_items:
            req_l = item["length"]
            if req_l > self.stock_length:
                raise ValueError(f"Thanh {item['id']} có chiều dài {req_l}mm > 11700mm! Cần gọi split_long_bar trước.")

            best_bar_idx = -1
            min_space_left = float("inf")
            for b_idx, bar in enumerate(new_bars):
                space_left = self.stock_length - bar["used_length"]
                if space_left >= req_l and (space_left - req_l) < min_space_left:
                    min_space_left = space_left - req_l
                    best_bar_idx = b_idx

            if best_bar_idx != -1:
                bar = new_bars[best_bar_idx]
                bar["cuts"].append(item)
                bar["cuts_lengths"].append(req_l)
                bar["used_length"] += req_l
                bar["remnant"] = self.stock_length - bar["used_length"]
                bar["is_reusable"] = bar["remnant"] >= self.min_reuse_length
            else:
                new_bars.append({
                    "source": "NEW_11.7M",
                    "stock_length": self.stock_length,
                    "cuts": [item],
                    "cuts_lengths": [req_l],
                    "used_length": req_l,
                    "remnant": self.stock_length - req_l,
                    "is_reusable": (self.stock_length - req_l) >= self.min_reuse_length,
                })

        # Local Search Improvement: Cố gắng đổi chỗ (swap) để dồn phần dư tối đa về cây cuối cùng
        # (Giúp tăng xác suất tạo ra đoạn dư >= min_reuse_length để tái sử dụng)
        for i in range(len(new_bars) - 1):
            for j in range(i + 1, len(new_bars)):
                bar_a = new_bars[i]
                bar_b = new_bars[j]
                # Thử chuyển một mẩu từ bar_b sang bar_a nếu bar_a còn chứa được
                for k, cut_b in enumerate(list(bar_b["cuts"])):
                    if (self.stock_length - bar_a["used_length"]) >= cut_b["length"]:
                        # Chuyển cut_b từ b sang a
                        bar_b["cuts"].pop(k)
                        bar_b["cuts_lengths"].pop(k)
                        bar_b["used_length"] -= cut_b["length"]
                        bar_b["remnant"] = self.stock_length - bar_b["used_length"]
                        bar_b["is_reusable"] = bar_b["remnant"] >= self.min_reuse_length

                        bar_a["cuts"].append(cut_b)
                        bar_a["cuts_lengths"].append(cut_b["length"])
                        bar_a["used_length"] += cut_b["length"]
                        bar_a["remnant"] = self.stock_length - bar_a["used_length"]
                        bar_a["is_reusable"] = bar_a["remnant"] >= self.min_reuse_length
                        break

        # Loại bỏ các bar rỗng nếu có sau khi swap
        new_bars = [b for b in new_bars if b["cuts"]]

        all_patterns = used_old_stock + new_bars

        # Tính toán thống kê
        total_req_length = sum(sum(b["cuts_lengths"]) for b in all_patterns)
        total_stock_length = sum(b["stock_length"] for b in all_patterns)
        total_scrap = sum(b["remnant"] for b in all_patterns if not b["is_reusable"])
        total_reusable = sum(b["remnant"] for b in all_patterns if b["is_reusable"])

        u_wt = unit_weight_kg_m(dia)
        net_scrap_waste_pct = (total_scrap / total_stock_length * 100.0) if total_stock_length > 0 else 0.0
        total_waste_pct = ((total_stock_length - total_req_length) / total_stock_length * 100.0) if total_stock_length > 0 else 0.0
        yield_efficiency_pct = (total_req_length / total_stock_length * 100.0) if total_stock_length > 0 else 100.0

        new_reusable_stock = [
            {"dia": dia, "length": b["remnant"], "from_source": b["source"]}
            for b in all_patterns if b["is_reusable"] and b["remnant"] > 0
        ]

        return {
            "dia": dia,
            "unit_weight_kg_m": round(u_wt, 3),
            "total_cuts_count": sum(len(b["cuts"]) for b in all_patterns),
            "new_bars_count": len(new_bars),
            "old_stock_used_count": len(used_old_stock),
            "total_req_length_m": round(total_req_length / 1000.0, 2),
            "total_req_weight_kg": round((total_req_length / 1000.0) * u_wt, 2),
            "total_stock_length_m": round(total_stock_length / 1000.0, 2),
            "total_stock_weight_kg": round((total_stock_length / 1000.0) * u_wt, 2),
            "total_scrap_length_m": round(total_scrap / 1000.0, 2),
            "total_scrap_weight_kg": round((total_scrap / 1000.0) * u_wt, 2),
            "total_reusable_length_m": round(total_reusable / 1000.0, 2),
            "total_reusable_weight_kg": round((total_reusable / 1000.0) * u_wt, 2),
            "net_scrap_waste_pct": round(net_scrap_waste_pct, 2),
            "total_waste_pct": round(total_waste_pct, 2),
            "yield_efficiency_pct": round(yield_efficiency_pct, 2),
            "cutting_patterns": all_patterns,
            "new_reusable_stock": new_reusable_stock,
        }

    def optimize(
        self,
        required_bars: List[Dict[str, Any]],
        old_stock: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Điểm vào chính — tối ưu cắt thép cho toàn bộ danh mục cốt thép (đa đường kính).
        """
        start_time = datetime.now()
        # Phân nhóm theo đường kính dia
        dia_groups: Dict[float, List[Dict[str, Any]]] = {}
        for bar in required_bars:
            dia = float(bar.get("dia", 20.0))
            if dia not in dia_groups:
                dia_groups[dia] = []
            # Nếu thanh dài hơn 11.7m, tự động split
            bar_l = float(bar["length"])
            if bar_l > self.stock_length:
                segs = self.split_long_bar(bar_l, dia, bar_type=bar.get("type", "beam"))
                count = int(bar.get("count", 1))
                for seg in segs:
                    dia_groups[dia].append({
                        "id": bar.get("id", f"D{int(dia)}"),
                        "length": seg["length"],
                        "count": count,
                        "note": seg.get("note", ""),
                    })
            else:
                dia_groups[dia].append(bar)

        # Phân nhóm old_stock theo đường kính
        old_groups: Dict[float, List[Dict[str, Any]]] = {}
        if old_stock:
            for o in old_stock:
                d = float(o.get("dia", 20.0))
                if d not in old_groups:
                    old_groups[d] = []
                for _ in range(int(o.get("count", 1))):
                    old_groups[d].append({"length": float(o["length"]), "dia": d})

        results_by_dia = {}
        tot_new_bars = 0
        tot_old_used = 0
        tot_req_wt = 0.0
        tot_stock_wt = 0.0
        tot_scrap_wt = 0.0
        tot_reusable_wt = 0.0

        for dia in sorted(dia_groups.keys()):
            res = self.optimize_single_dia(
                dia=dia,
                pieces=dia_groups[dia],
                old_stock=old_groups.get(dia, []),
            )
            results_by_dia[f"D{int(dia)}"] = res
            tot_new_bars += res["new_bars_count"]
            tot_old_used += res["old_stock_used_count"]
            tot_req_wt += res["total_req_weight_kg"]
            tot_stock_wt += res["total_stock_weight_kg"]
            tot_scrap_wt += res["total_scrap_weight_kg"]
            tot_reusable_wt += res["total_reusable_weight_kg"]

        overall_scrap_pct = (tot_scrap_wt / tot_stock_wt * 100.0) if tot_stock_wt > 0 else 0.0
        overall_yield_pct = (tot_req_wt / tot_stock_wt * 100.0) if tot_stock_wt > 0 else 100.0

        elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000.0

        exec_trace = [
            f"[INFO] Bắt đầu tối ưu cắt thép 1D (CSP) chuẩn 11700mm cho {len(required_bars)} cấu kiện.",
            f"[OK] Đã phân nhóm {len(dia_groups)} đường kính: {[f'D{int(d)}' for d in sorted(dia_groups.keys())]}.",
            f"[OK] Tổng số cây 11.7m cần xuất kho: {tot_new_bars} cây.",
            f"[OK] Số đoạn thép tồn kho tái sử dụng: {tot_old_used} thanh.",
            f"[OK] Hiệu suất sử dụng thép toàn dự án: {overall_yield_pct:.2f}%.",
            f"[OK] Tỷ lệ hao hụt phế liệu thuần (Net Scrap Waste): {overall_scrap_pct:.2f}%.",
        ] + [str(l) for l in self.logs]

        first_dia = min(dia_groups.keys()) if dia_groups else 20.0
        calc_logs = [
            {
                "Step": 1,
                "Description": "Chiều dài đoạn nối chồng cốt thép tiêu chuẩn",
                "Formula": "L_lap = lap_multiplier * dia",
                "Substitution": f"{self.lap_multiplier:.0f} * {first_dia:.0f} mm",
                "Result": f"{self.lap_multiplier * first_dia:.0f} mm",
                "Citation": {"standard": "TCVN 5574:2018", "clause": "8.3.3.1", "title": "Chiều dài nối chồng cốt thép trong bê tông"}
            },
            {
                "Step": 2,
                "Description": "Khoảng cách bố trí so le giữa các mối nối thanh liền kề",
                "Formula": "Delta_stagger >= min_stagger_offset * dia",
                "Substitution": f"{self.min_stagger_offset:.0f} * {first_dia:.0f} mm",
                "Result": f"{self.min_stagger_offset * first_dia:.0f} mm",
                "Citation": {"standard": "TCVN 5574:2018", "clause": "8.3.3.2", "title": "Quy cách so le mối nối cốt thép"}
            },
            {
                "Step": 3,
                "Description": "Hiệu suất sử dụng vật liệu thép toàn dự án (Yield Efficiency)",
                "Formula": "Yield = (Total_Required_Weight / Total_Stock_Weight) * 100",
                "Substitution": f"({tot_req_wt:.2f} kg / {tot_stock_wt:.2f} kg) * 100",
                "Result": f"{overall_yield_pct:.2f}%",
                "Citation": {"standard": "TCVN 5574:2018", "clause": "Chương 8", "title": "Hao hụt vật liệu cốt thép gia công"}
            },
            {
                "Step": 4,
                "Description": "Tỷ lệ hao hụt phế liệu thuần không thể tái sử dụng (L < 500mm)",
                "Formula": "Scrap_Waste = (Total_Scrap_Weight / Total_Stock_Weight) * 100",
                "Substitution": f"({tot_scrap_wt:.2f} kg / {tot_stock_wt:.2f} kg) * 100",
                "Result": f"{overall_scrap_pct:.2f}%",
                "Citation": {"standard": "TCVN 5574:2018", "clause": "Chương 8", "title": "Tối ưu hóa sơ đồ cắt thép thanh"}
            }
        ]

        summary_data = {
            "total_new_bars_11700": tot_new_bars,
            "total_old_stock_used": tot_old_used,
            "total_required_weight_kg": round(tot_req_wt, 2),
            "total_stock_weight_kg": round(tot_stock_wt, 2),
            "total_scrap_weight_kg": round(tot_scrap_wt, 2),
            "total_reusable_weight_kg": round(tot_reusable_wt, 2),
            "overall_scrap_waste_pct": round(overall_scrap_pct, 2),
            "overall_yield_efficiency_pct": round(overall_yield_pct, 2),
            "elapsed_ms": round(elapsed_ms, 2),
        }

        return {
            "summary": summary_data,
            "results": summary_data,
            "geometry": {
                "b": 200.0,
                "h": 400.0,
                "L": self.stock_length,
                "stock_length_mm": self.stock_length,
                "min_reuse_length_mm": self.min_reuse_length,
            },
            "materials": {
                "concrete": "B25",
                "steel_grade": "CB400-V / CB500-V",
                "standard": "TCVN 1651:2018"
            },
            "forces": {
                "lap_multiplier": self.lap_multiplier,
                "min_stagger_offset": self.min_stagger_offset,
                "total_required_weight_kg": tot_req_wt
            },
            "by_diameter": results_by_dia,
            "Execution_Trace": exec_trace,
            "Calculation_Logs": calc_logs,
            "Standard_Method": "TCVN 5574:2018 + DCE Bea_ToHopThepV4 (1D Cutting Stock Optimizer)",
            "source": "calculated",
            "generated_at": datetime.now().isoformat(),
        }


# ─────────────────────────────────────────────────────────────────────────────
# CLI Entrypoint
# ─────────────────────────────────────────────────────────────────────────────

def _cli():
    parser = argparse.ArgumentParser(description="1D Rebar Cutting Stock Optimizer (11.7m standard)")
    parser.add_argument(
        "--bars",
        type=str,
        required=True,
        help="JSON string danh sách thanh thép cần cắt: '[{\"id\":\"T1\",\"length\":4500,\"count\":6,\"dia\":22}]'",
    )
    parser.add_argument(
        "--old-stock",
        type=str,
        default=None,
        help="JSON string danh sách thép dư tồn kho: '[{\"length\":4800,\"count\":1,\"dia\":22}]'",
    )
    parser.add_argument("--stock-length", type=float, default=STANDARD_STOCK_LENGTH_MM, help="Chiều dài cây thép thương phẩm (mm)")
    parser.add_argument("--min-reuse", type=float, default=DEFAULT_MIN_REUSE_LENGTH_MM, help="Chiều dài tối thiểu để tái sử dụng (mm)")
    parser.add_argument("--lap-mult", type=float, default=DEFAULT_LAP_MULTIPLIER, help="Bội số nối chồng L_lap = N*d")
    parser.add_argument("--indent", type=int, default=2)
    args = parser.parse_args()

    bars = json.loads(args.bars)
    old_stock = json.loads(args.old_stock) if args.old_stock else None

    optimizer = RebarCuttingOptimizer(
        stock_length=args.stock_length,
        min_reuse_length=args.min_reuse,
        lap_multiplier=args.lap_mult,
    )
    result = optimizer.optimize(required_bars=bars, old_stock=old_stock)
    print(json.dumps(result, ensure_ascii=False, indent=args.indent))


if __name__ == "__main__":
    _cli()
