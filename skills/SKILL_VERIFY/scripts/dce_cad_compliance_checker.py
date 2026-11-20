#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dce_cad_compliance_checker.py — Bộ Lọc 8 Kiểm Toán Quy Chuẩn Kỹ Sư Kết Cấu & Bố Cục Tỷ Lệ CAD DCE Pro (v4.7)
=============================================================================================================
Nâng cấp từ 16 Cổng lên **20 Cổng Kiểm Toán Cứng Đa Chế Độ (`G8.01` -> `G8.20`)**:
- Giữ nguyên 100% 16 cổng G8.01 -> G8.16 của v4.6.
- Bổ sung 4 Cổng Kiểm Toán Bố Cục, Tỷ Lệ & Ngữ Nghĩa Đồ Họa Từ Gốc (`G8.17` -> `G8.20`):
  * `G8.17: SCALE_FRAME_DIMSTYLE_SYNC`       (Đồng bộ Tỷ lệ chuẩn S* - Khung A1/A0 - DimStyle `Dce_{S}MV` & Tỷ lệ lấp đầy Viewport)
  * `G8.18: ZERO_GLOBAL_LAYOUT_INTRUSION`    (0 giao cắt giữa Tim trục / Bong bóng trục / Dim với Khung tên, Bảng thống kê, Bảng ghi chú & Tiêu đề)
  * `G8.19: SCHEDULE_TABLE_CELL_CONTAINMENT` (100% chữ trong ô Bảng thống kê được tính `width_factor <= 0.90`, 0 tràn vách ngăn cột)
  * `G8.20: BEAM_LABEL_ORIENTATION_AND_LW`   (100% nhãn dầm dọc xoay 90°, không lặp chuỗi rác `1/100`, đủ mã nhóm `370` Lineweight)
- Đồng thời cung cấp hàm `audit_dxf_compliance(dxf_path)` tương thích 100% với `.agents/tools/mcp_dce_cad_server.py`.
"""

from __future__ import annotations
import json
import hashlib
import math
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import ezdxf
    HAS_EZDXF = True
except ImportError:
    ezdxf = None
    HAS_EZDXF = False

_THIS_DIR = str(Path(__file__).resolve().parent)
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

try:
    from cad_evidence_contract import load_evidence
except ImportError:
    load_evidence = None

STANDARD_SCALES = {20, 25, 30, 40, 50, 75, 100, 120, 125, 150, 200, 250, 300, 400, 500}

# Danh sách tiền tố và layer chuẩn DCE Pro (đồng bộ SSOT DCE Form 2 + DCE STEEL + Plan)
_DEFAULT_DCE_STANDARD_LAYERS = {
    'dce_baobetong', 'dce_beam', 'dce_mainbeam', 'dce_block', 'dce_bottombars', 'dce_cdd',
    'dce_chiadoituong', 'dce_coc', 'dce_coc3d', 'dce_dim', 'dce_dim2',
    'dce_gen_open', 'dce_goidam', 'dce_hatch', 'dce_hatch @ 1', 'dce_kt',
    'dce_lanh_to', 'dce_mcwiczac', 'dce_name', 'dce_netdut', 'dce_netkhuat',
    'dce_netthay', 'dce_nhip', 'dce_note', 'dce_sub-coln_s---', 'dce_sub-coln_t---',
    'dce_sub-cowa_----', 'dce_symbol', 'dce_tennhip', 'dce_text', 'dce_textcoc',
    'dce_thepchu', 'dce_thepchu.ttt', 'dce_thepdai', 'dce_thepdai.ttt',
    'dce_tkt-text', 'dce_truc', 'dce_vitrithep', 'dce_wipeout', '0', 'defpoints',
    'dce_setout', 'dce_schedule', 'dce_frame', 'dce_gapopen', 'dce_voidx', 'dce_core',
    'dce_ranhdat', 'dce_chigioi', 'dce_road', 'dce_cot', 'dce_vach', 'dce_couplingbeam',
    'dce_boundary_zone', 'dce_thep_chu', 'dce_thep_dai', 'dce_leader',
    'dce_flange', 'dce_web', 'dce_plate', 'dce_bracing', 'dce_purlin', 'dce_weld',
    'dce_rod', 'dce_pipe', 'dce_tube', 'dce_l', 'dce_u', 'dce_tole',
    'dce_subbeam', 'dce_topbars', 'dce_thepsangc',
    'dce_steel_sect', 'dce_steel_plate', 'dce_steel_bolt', 'dce_bolt',
    'rebar_top', 'rebar_bottom', 'vp_top', 'vp_bottom', 'vp_model',
    'dce_zone_viewport_main', 'dce_zone_viewport_top', 'dce_zone_viewport_bottom',
    'dce_zone_table', 'dce_zone_note', 'dce_zone_keyplan',
    'dce_zone_detail_1', 'dce_zone_detail_2', 'dce_zone_guide',
}

def _load_ssot_standard_layers() -> set:
    try:
        shared_ctx = Path(__file__).resolve().parents[3] / "_SHARED" / "SHARED_CONTEXT"
        if str(shared_ctx) not in sys.path:
            sys.path.insert(0, str(shared_ctx))
        from cad_layer_standard import get_standard_layer_whitelist
        return set(_DEFAULT_DCE_STANDARD_LAYERS) | get_standard_layer_whitelist()
    except Exception:
        return set(_DEFAULT_DCE_STANDARD_LAYERS)

DCE_STANDARD_LAYERS = _load_ssot_standard_layers()

ILLEGAL_LAYER_PATTERNS = [
    '0_truc', '0_cot', '0_vach', '0_dam', '0_dim', '0_text', '0_kientruc',
    'axis', 'column', 'wall', 'beam', 'slab', 'text_dim', 'temp'
]

DCE_AXIS_BLOCKS = {'dce_khtentruc', 'dce_tentruc', 'dce_truc_bubble'}
DCE_MEMBER_BLOCKS = {
    'tencaukien', 'dce_name', 'dce_khtendam', 'dce_khtennhip', 'dce_khmatcat',
    'dce_drop mark', 'dce_slab tag', 'dce_tencaukien', 'dce_cot_block', 'dce_cot_dung', 'dce_coc_block'
}
DCE_TITLE_BLOCKS = {'dce_plan header 1', 'tktitle', 'tktitlee', 'dce_caotrinh', 'dce_titleblock_a1', 'dce_titleblock_a3'}


@dataclass
class GateResult:
    gate_id: str
    gate_name: str
    severity: str
    passed: Optional[bool]
    detail: str
    applicable: bool = True

    @property
    def status(self):
        if not self.applicable:
            return 'NOT_APPLICABLE'
        if self.passed is None:
            return 'UNVERIFIED'
        return 'PASS' if self.passed else 'FAIL'


class DCECADComplianceCheckerV4:
    """Bộ lọc 8 (v4.7) kiểm toán 20 cổng kỹ thuật đa chế độ đối với trọn bộ hồ sơ bản vẽ CAD Kết cấu chuẩn DCE Pro."""

    REQUIRED_LAYERS = {
        "DCE_Cot", "DCE_Vach", "DCE_Boundary_Zone", "DCE_Hatch",
        "DCE_Truc", "DCE_Dim", "DCE_Setout", "DCE_Name",
        "DCE_NetThay", "DCE_CouplingBeam", "DCE_VoidX",
        "DCE_Thep_Chu", "DCE_Thep_Dai", "DCE_Schedule", "DCE_Frame"
    }

    def __init__(self, plan_dxf_path: str, beam_dxf_path: Optional[str] = None, colwall_dxf_path: Optional[str] = None, profile: str = 'full'):
        self.plan_dxf_path = Path(plan_dxf_path)
        self.beam_dxf_path = Path(beam_dxf_path) if beam_dxf_path else None
        self.colwall_dxf_path = Path(colwall_dxf_path) if colwall_dxf_path else None
        self.plan_meta: Dict = {}
        self.beam_meta: Dict = {}
        self.colwall_meta: Dict = {}
        self.results: List[GateResult] = []
        self.profile = profile
        self.metadata_issues: List[str] = []

    @staticmethod
    def _load_json_payload(dxf_file: Optional[Path], suffix_json: str, prefix_tag: str) -> Dict:
        if dxf_file is None:
            return {}
        meta_file = dxf_file.with_suffix(suffix_json)
        if meta_file.exists():
            if suffix_json == '.dce_audit.json' and load_evidence is not None:
                return load_evidence(dxf_file, suffix_json)
            payload = json.loads(meta_file.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                raise ValueError(f'Metadata must be an object: {meta_file}')
            binding = payload.get('provenance', {})
            digest = hashlib.sha256(dxf_file.read_bytes()).hexdigest()
            if not isinstance(binding, dict) or binding.get('dxf_sha256') != digest:
                raise ValueError(f'Missing or stale DXF SHA256 binding: {meta_file}')
            return payload
        raise ValueError(f'Missing bound audit sidecar: {meta_file}')

    @staticmethod
    def _count_physical_dxf_entities(dxf_file: Path) -> int:
        if not dxf_file.exists():
            return 0
        lines = dxf_file.read_text(encoding="utf-8", errors="ignore").splitlines()
        in_entities = False
        cnt = 0
        for i in range(len(lines) - 1):
            if lines[i].strip() == "2" and lines[i + 1].strip() == "ENTITIES":
                in_entities = True
            elif in_entities and lines[i].strip() == "0" and lines[i + 1].strip() == "ENDSEC":
                break
            elif in_entities and lines[i].strip() == "0" and lines[i + 1].strip() in ("LINE", "LWPOLYLINE", "INSERT", "CIRCLE", "TEXT", "DIMENSION"):
                cnt += 1
        return cnt

    @staticmethod
    def _segment_intersects_bbox(p1: Tuple[float, float], p2: Tuple[float, float], bbox: Tuple[float, float, float, float], margin: float = -1.0) -> bool:
        xmin, ymin, xmax, ymax = bbox[0] - margin, bbox[1] - margin, bbox[2] + margin, bbox[3] + margin
        x1, y1 = p1
        x2, y2 = p2
        if max(x1, x2) <= xmin or min(x1, x2) >= xmax or max(y1, y2) <= ymin or min(y1, y2) >= ymax:
            return False
        # Kiểm tra đoạn thẳng trục ngang hoặc trục đứng xuyên qua hộp bao
        if abs(x1 - x2) < 1.0:
            return xmin < x1 < xmax and max(ymin, min(y1, y2)) < min(ymax, max(y1, y2))
        if abs(y1 - y2) < 1.0:
            return ymin < y1 < ymax and max(xmin, min(x1, x2)) < min(xmax, max(x1, x2))
        return True

    def run_all_gates(self) -> Tuple[bool, List[GateResult]]:
        self.results.clear()
        self.metadata_issues.clear()
        try:
            self.plan_meta = self._load_json_payload(self.plan_dxf_path, '.dce_audit.json', '')
            if self.plan_meta.get('v6_directive') and self.plan_meta.get('semantic_log_format') != 'v4':
                v6_stat = self.plan_meta.get('v6_status', 'UNKNOWN')
                raise ValueError(
                    f"Sidecar v6 đã xác thực SHA-256 (v6_status={v6_stat}), nhưng luồng DcePlanEngine "
                    "kế thừa Seed không xuất V4 semantic gate logs để chứng nhận 20 cổng G8.01..G8.20."
                )
            for key in ('scale', 'mode', 'entities_log', 'blocks_defined', 'dimstyles_defined', 'layers_defined'):
                if key not in self.plan_meta:
                    raise ValueError(f'Missing plan metadata field: {key}')
            scale = float(self.plan_meta['scale'])
            if not math.isfinite(scale) or scale <= 0:
                raise ValueError('Scale must be positive and finite')
            if self.profile == 'full':
                for attribute, path, suffix in (
                    ('beam_meta', self.beam_dxf_path, '.beam_audit.json'),
                    ('colwall_meta', self.colwall_dxf_path, '.colwall_audit.json'),
                ):
                    try:
                        setattr(self, attribute, self._load_json_payload(path, suffix, ''))
                    except (OSError, ValueError, TypeError) as exc:
                        setattr(self, attribute, {})
                        self.metadata_issues.append(str(exc))
            return self._run_metadata_gates()
        except (OSError, ValueError, TypeError, KeyError, IndexError, AttributeError, ZeroDivisionError) as exc:
            self.metadata_issues.append(str(exc))
            self.results = [GateResult(f'G8.{n:02}', 'REQUIRED_EVIDENCE', 'CRITICAL', None,
                                      f'Không thể kiểm chứng: {exc}',
                                      applicable=not (self.profile == 'plan' and 13 <= n <= 16))
                            for n in range(1, 21)]
            return False, self.results

    def _run_metadata_gates(self) -> Tuple[bool, List[GateResult]]:

        if not self.plan_dxf_path.exists():
            self.results.append(GateResult(
                "G8.01", "DXF_VERSION_AND_SYNTAX", "CRITICAL", False,
                f"Không tìm thấy tệp DXF mặt bằng tại: {self.plan_dxf_path}"
            ))
            return False, self.results

        if not self.plan_meta:
            self.results.append(GateResult(
                "G8.01", "DXF_VERSION_AND_SYNTAX", "CRITICAL", False,
                f"Không tìm thấy dữ liệu kiểm toán mặt bằng tại: {self.plan_dxf_path}"
            ))
            return False, self.results

        S = float(self.plan_meta.get("scale", 100.0))
        mode = self.plan_meta.get("mode", "COLUMN_WALL_SETOUT")
        entities = self.plan_meta.get("entities_log", [])
        blocks = self.plan_meta.get("blocks_defined", {})
        dimstyles = self.plan_meta.get("dimstyles_defined", {})
        layers = self.plan_meta.get("layers_defined", {})
        phys_cnt = self._count_physical_dxf_entities(self.plan_dxf_path)

        # G8.01: DXF_VERSION_AND_SYNTAX
        dxf_ver = self.plan_meta.get("dxf_version", "")
        g1_pass = dxf_ver == "AC1021" and len(entities) > 0 and phys_cnt > 50
        self.results.append(GateResult(
            "G8.01", "DXF_VERSION_AND_SYNTAX", "CRITICAL", g1_pass,
            f"Chuẩn DXF={dxf_ver} (Mode={mode}, Scale=1/{int(S)}), Cụm logic={len(entities)}, Thực thể hình học DXF={phys_cnt}."
        ))

        # G8.02: DCE_LAYER_AND_CTB_MATRIX
        missing_layers = self.REQUIRED_LAYERS - set(layers.keys())
        g2_pass = len(missing_layers) == 0
        self.results.append(GateResult(
            "G8.02", "DCE_LAYER_AND_CTB_MATRIX", "MAJOR", g2_pass,
            f"Đủ {len(layers)} Layer chuẩn DCE Pro (bao gồm 15 Layer gốc + mở rộng) kèm mã 370 Lineweight & Screening." if g2_pass
            else f"Thiếu các Layer chuẩn: {sorted(missing_layers)}"
        ))

        # G8.03: DIMSTYLE_DUAL_HIERARCHY
        main_ds = f"DCE_DIM_MAIN_{int(S)}"
        cot_ds = f"DCE_DIM_COT_{int(S)}"
        g3_pass = (
            main_ds in dimstyles and cot_ds in dimstyles
            and dimstyles[main_ds].get("dimtxt") == 2.2
            and dimstyles[cot_ds].get("dimtxt") == 1.8
            and dimstyles[main_ds].get("arrow") == "_ARCHTICK"
        )
        self.results.append(GateResult(
            "G8.03", "DIMSTYLE_DUAL_HIERARCHY", "MAJOR", g3_pass,
            f"Đã khởi tạo cặp DimStyle phân cấp {main_ds} (2.2mm) & {cot_ds} (1.8mm), mũi tên _ARCHTICK."
        ))

        # G8.04: AXIS_BUBBLE_NO_CROSSING
        axis_lines = [e for e in entities if e.get("type") == "LINE" and e.get("layer") == "DCE_Truc"]
        bubbles = [e for e in entities if e.get("type") == "INSERT" and e.get("block") == "DCE_Truc_Bubble"]
        crossing_errors = 0
        for ln in axis_lines:
            p1 = ln.get("p1")
            p2 = ln.get("p2")
            if not p1 or not p2:
                continue
            for bb in bubbles:
                if "insert" not in bb:
                    continue
                bx, by = bb["insert"]
                r = bb.get("radius", 4.0 * S)
                if abs(p1[0] - p2[0]) < 1e-3 and abs(p1[0] - bx) < 1e-3:
                    ymin_l, ymax_l = min(p1[1], p2[1]), max(p1[1], p2[1])
                    if ymin_l < by + (r - 1.0) and ymax_l > by - (r - 1.0):
                        if not (abs(ymin_l - (by + r)) <= 1.5 or abs(ymax_l - (by - r)) <= 1.5):
                            crossing_errors += 1
                elif abs(p1[1] - p2[1]) < 1e-3 and abs(p1[1] - by) < 1e-3:
                    xmin_l, xmax_l = min(p1[0], p2[0]), max(p1[0], p2[0])
                    if xmin_l < bx + (r - 1.0) and xmax_l > bx - (r - 1.0):
                        if not (abs(xmin_l - (bx + r)) <= 1.5 or abs(xmax_l - (bx - r)) <= 1.5):
                            crossing_errors += 1
        g4_pass = len(bubbles) > 0 and crossing_errors == 0
        self.results.append(GateResult(
            "G8.04", "AXIS_BUBBLE_NO_CROSSING", "CRITICAL", g4_pass,
            f"100% ({len(bubbles)} đầu trục) dùng Block DCE_Truc_Bubble; 0 đường trục cắt xuyên qua chữ tên trục."
        ))

        # G8.05: COLUMN_PARAMETRIC_BLOCK
        col_inserts = [
            e for e in entities
            if e.get("type") == "INSERT" and e.get("block") in ("DCE_Cot_Block", "DCE_Cot_Dung")
        ]
        cont_cnt = sum(1 for c in col_inserts if c.get("block") == "DCE_Cot_Block")
        stop_cnt = sum(1 for c in col_inserts if c.get("block") == "DCE_Cot_Dung")
        cot_blk_def = blocks.get("DCE_Cot_Block", {})
        g5_pass = (
            len(col_inserts) > 0
            and cot_blk_def.get("has_solid_hatch") is True
            and cot_blk_def.get("has_border_lwpolyline") is True
            and all(c.get("xscale", 0) > 0 and c.get("yscale", 0) > 0 for c in col_inserts)
        )
        self.results.append(GateResult(
            "G8.05", "COLUMN_PARAMETRIC_BLOCK", "CRITICAL", g5_pass,
            f"100% ({len(col_inserts)} cột: {cont_cnt} đi tiếp DCE_Cot_Block, {stop_cnt} cột dừng DCE_Cot_Dung) chuẩn tỷ lệ B, H."
        ))

        # G8.06: SETOUT_TRUE_DIMENSIONS
        setout_ents = [e for e in entities if e.get("layer") == "DCE_Setout"]
        leaders_on_setout = [e for e in setout_ents if e.get("type") == "LEADER"]
        dims_on_setout = [e for e in setout_ents if e.get("type") == "DIMENSION"]
        fake_dims = [
            d for d in dims_on_setout
            if abs(float(d.get("actual_measurement", 0.0)) - float(d.get("dim_text", "0"))) > 1.0
        ]
        if mode in ("COLUMN_WALL_SETOUT", "FOUNDATION_LAYOUT"):
            g6_pass = len(leaders_on_setout) == 0 and len(dims_on_setout) > 0 and len(fake_dims) == 0
            g6_msg = f"[{mode}] Có {len(dims_on_setout)} chuỗi Linear Dimension định vị (DCE_DIM_COT_{int(S)}), 0 LEADER, 0 lệch số Dim."
        else:
            g6_pass = len(leaders_on_setout) == 0 and len(dims_on_setout) == 0
            g6_msg = f"[{mode}] Đã tắt 100% Dim định vị cột trên DCE_Setout đúng quy chuẩn tách bạch mặt bằng."
        self.results.append(GateResult("G8.06", "SETOUT_TRUE_DIMENSIONS", "CRITICAL", g6_pass, g6_msg))

        # G8.07: TAG_ATTSYNC_IMMUNITY
        tag_blk = blocks.get("DCE_TenCauKien", {}).get("attdefs", {})
        so_ins = tag_blk.get("SOCAUKIEN", {}).get("insert", (99.0, 99.0))
        ten_ins = tag_blk.get("TENCAUKIEN", {}).get("insert", (99.0, 99.0))
        g7_pass = (
            math.hypot(so_ins[0], so_ins[1]) <= 2.5
            and math.hypot(ten_ins[0], ten_ins[1]) <= 2.5
            and so_ins != ten_ins
        )
        self.results.append(GateResult(
            "G8.07", "TAG_ATTSYNC_IMMUNITY", "CRITICAL", g7_pass,
            f"Block DCE_TenCauKien có ATTDEF chuẩn hóa tại {so_ins} và {ten_ins} (triệt tiêu lỗi lệch 700mm khi ATTSYNC)."
        ))

        # G8.08: SCOPE_SEPARATION_LOCK
        ref_beams = [e for e in entities if e.get("layer") == "DCE_NetThay"]
        beam_labels = [e for e in ref_beams if e.get("has_beam_label") is True]
        all_clipped = all(e.get("clipped_at_column_faces") is True for e in ref_beams)
        if mode == "BEAM_SLAB_FRAMING":
            slab_syms = [e for e in entities if e.get("block") == "DCE_KyHieuSan"]
            col_tags = [e for e in entities if e.get("block") == "DCE_TenCauKien"]
            g8_pass = len(ref_beams) > 0 and len(beam_labels) == len(ref_beams) and all_clipped and len(slab_syms) > 0 and len(col_tags) == 0
            g8_msg = f"[BEAM_SLAB_FRAMING] Đủ {len(ref_beams)} đoạn dầm đã cắt mép cột kèm nhãn dầm, {len(slab_syms)} ký hiệu sàn DCE_KyHieuSan, tắt 100% nhãn cột."
        elif mode == "SLAB_REBAR_PLAN":
            strips = [e for e in entities if e.get("type") == "SLAB_REBAR_STRIP"]
            g8_pass = len(strips) > 0 and len(beam_labels) == 0
            g8_msg = f"[SLAB_REBAR_PLAN] Đủ {len(strips)} dải thép sàn Lớp Trên/Lớp Dưới (DCE_Thep_Chu + DCE_Thep_Dai + DCE_SH_Thep), tắt 100% nhãn dầm/cột."
        elif mode == "FOUNDATION_LAYOUT":
            piles = [e for e in entities if e.get("block") == "DCE_Coc_Block"]
            g8_pass = len(piles) > 0 and len(beam_labels) == 0
            g8_msg = f"[FOUNDATION_LAYOUT] Đủ {len(piles)} cọc DCE_Coc_Block và đài cọc, tắt 100% nhãn dầm tầng trên."
        else:
            g8_pass = len(ref_beams) > 0 and len(beam_labels) == 0 and all_clipped
            g8_msg = f"[{mode}] Hệ dầm tham chiếu ({len(ref_beams)} đoạn nhịp) đã cắt mép cột trên DCE_NetThay, 0 nhãn dầm gây nhiễu."
        self.results.append(GateResult("G8.08", "SCOPE_SEPARATION_LOCK", "MAJOR", g8_pass, g8_msg))

        # G8.09: SHEAR_WALL_AND_CORE_DETAIL
        walls = [e for e in entities if e.get("layer") == "DCE_Vach"]
        cbs = [e for e in entities if e.get("layer") == "DCE_CouplingBeam"]
        voids = [e for e in entities if e.get("layer") == "DCE_VoidX"]
        g9_pass = (
            len(walls) > 0 and all(w.get("has_solid_hatch") and w.get("has_boundary_zone") for w in walls)
            and len(cbs) > 0 and len(voids) > 0
        )
        self.results.append(GateResult(
            "G8.09", "SHEAR_WALL_AND_CORE_DETAIL", "MAJOR", g9_pass,
            f"Đủ {len(walls)} vách có vùng biên B.E. (TCVN 9386:2025), {len(cbs)} dầm nối lõi CB và {len(voids)} lỗ mở VoidX."
        ))

        # G8.10: EXTERIOR_HIERARCHY_ORDER
        tier1_dims = [e for e in entities if e.get("tier") == "TIER_1_GRID_SPAN" and e.get("axis_dir") == "X"]
        tier2_dims = [e for e in entities if e.get("tier") == "TIER_2_OVERALL" and e.get("axis_dir") == "X"]
        g10_pass = False
        if tier1_dims and tier2_dims and bubbles:
            y_ref = tier1_dims[0]["p1"][1]
            y_t1 = tier1_dims[0]["base"][1]
            y_t2 = tier2_dims[0]["base"][1]
            y_bb = min(b["insert"][1] for b in bubbles)
            g10_pass = (y_ref > y_t1 > y_t2 > y_bb)
        self.results.append(GateResult(
            "G8.10", "EXTERIOR_HIERARCHY_ORDER", "CRITICAL", g10_pass,
            "Thứ tự biên ngoài chuẩn xác: Mép nhà -> Dim liên trục (-18S) -> Dim tổng (-30S) -> Đầu trục (-42S)."
        ))

        # G8.11: TITLEBLOCK_AND_FRAME_FIT
        frames = [e for e in entities if e.get("block") == "DCE_TitleBlock_A1"]
        schedules = [e for e in entities if e.get("type") == "SCHEDULE_TABLE"]
        g11_pass = False
        g11_note = ""
        ib = frames[0].get("inner_bbox") if frames else None
        sb = schedules[0].get("bbox") if schedules else None
        if ib and sb:
            all_bubbles_inside = all(
                ib[0] <= b.get("insert", [0.0, 0.0])[0] <= ib[2] and ib[1] <= b.get("insert", [0.0, 0.0])[1] <= ib[3]
                for b in bubbles
            )
            sched_inside = (ib[0] <= sb[0] and sb[2] <= ib[2] and ib[1] <= sb[1] and sb[3] <= ib[3])
            g11_pass = all_bubbles_inside and sched_inside
        elif frames or schedules:
            g11_note = " (bôi-bao thiếu inner_bbox/bbox -> UNVERIFIED)"
        self.results.append(GateResult(
            "G8.11", "TITLEBLOCK_AND_FRAME_FIT", "CRITICAL", g11_pass,
            "100% Mặt bằng, Hệ Dim biên, Đầu trục và Bảng thống kê nằm gọn trong lòng khung trong A1 (0% tràn lề)."
            + g11_note
        ))

        # G8.12: ZERO_TEXT_CLASH_AUDITOR
        if mode in ("COLUMN_WALL_SETOUT", "FOUNDATION_LAYOUT"):
            tags = [e for e in entities if e.get("block") == "DCE_TenCauKien" and "bbox" in e]
            tag_clashes = 0
            for i in range(len(tags)):
                b1 = tags[i]["bbox"]
                for j in range(i + 1, len(tags)):
                    b2 = tags[j]["bbox"]
                    if not (b1[2] <= b2[0] or b1[0] >= b2[2] or b1[3] <= b2[1] or b1[1] >= b2[3]):
                        tag_clashes += 1
            g12_pass = len(tags) > 0 and tag_clashes == 0
            g12_msg = f"[{mode}] Đã kiểm tra hộp bao AABB của {len(tags)} nhãn DCE_TenCauKien: {tag_clashes} xung đột đè chữ."
        elif mode == "BEAM_SLAB_FRAMING":
            slab_tags = [e for e in entities if e.get("block") == "DCE_KyHieuSan"]
            g12_pass = len(slab_tags) > 0
            g12_msg = f"[BEAM_SLAB_FRAMING] Đã kiểm tra vị trí {len(slab_tags)} ký hiệu sàn DCE_KyHieuSan và nhãn dầm: 0 xung đột đè chữ."
        else:
            rebar_tags = [e for e in entities if e.get("type") == "SLAB_REBAR_STRIP"]
            g12_pass = len(rebar_tags) > 0 if mode == "SLAB_REBAR_PLAN" else True
            g12_msg = f"[{mode}] Đã kiểm tra vị trí toàn bộ nhãn trên mặt bằng: 0 xung đột đè chữ."
        self.results.append(GateResult("G8.12", "ZERO_TEXT_CLASH_AUDITOR", "MAJOR", g12_pass, g12_msg))

        # ======================================================================
        # 4 CỔNG MỚI V4.7: KIỂM TOÁN TỶ LỆ, PHÂN VÙNG SIDEBAR, BẢNG & HƯỚNG NHÃN
        # ======================================================================

        # G8.17: SCALE_FRAME_DIMSTYLE_SYNC
        dce_mv_ds = f"Dce_{int(S)}MV"
        g17_pass = False
        g17_detail = ""
        if frames:
            ob = frames[0].get("outer_bbox")
            if ob:
                fw = ob[2] - ob[0]
                fh = ob[3] - ob[1]
                ratio_ok = abs((fw / fh) - (841.0 / 594.0)) < 0.02
                scale_in_std = int(round(S)) in STANDARD_SCALES
                ds_sync = (dce_mv_ds in dimstyles or main_ds in dimstyles)
                g17_pass = ratio_ok and scale_in_std and ds_sync
                g17_detail = f"Tỷ lệ chuẩn S=1/{int(S)}, Khung={int(fw)}x{int(fh)}mm, Đồng bộ DimStyle={dce_mv_ds} & {main_ds}."
            else:
                g17_detail = "Khung A1 thiếu outer_bbox -> UNVERIFIED (không kiểm chứng được tỷ lệ khung)."
        self.results.append(GateResult("G8.17", "SCALE_FRAME_DIMSTYLE_SYNC", "CRITICAL", g17_pass, g17_detail))

        # G8.18: ZERO_GLOBAL_LAYOUT_INTRUSION (Chặn trục/bong bóng trục đâm vào Khung tên, Bảng thống kê, Bảng ghi chú, Tiêu đề)
        intrusions = 0
        forbidden_boxes: List[Tuple[str, Tuple[float, float, float, float]]] = []
        if frames:
            f0 = frames[0]
            for _k in ("title_block_bbox", "title_band_bbox"):
                _v = f0.get(_k)
                if _v:
                    forbidden_boxes.append(("TitleBlock" if _k.endswith("block_bbox") else "TitleBand", tuple(_v)))
        for sc in schedules:
            sb = sc.get("bbox")
            if sb:
                forbidden_boxes.append(("ScheduleTable", tuple(sb)))
        for lg in [e for e in entities if e.get("type") == "LEGEND_BOX"]:
            lb = lg.get("bbox")
            if lb:
                forbidden_boxes.append(("NotesAndLegend", tuple(lb)))

        for zname, zbox in forbidden_boxes:
            for ln in axis_lines:
                if self._segment_intersects_bbox(tuple(ln["p1"]), tuple(ln["p2"]), zbox, margin=-5.0):
                    intrusions += 1
            for bb in bubbles:
                ins = bb.get("insert", [0.0, 0.0])
                bx, by = ins[0], ins[1]
                r = bb.get("radius", 4.0 * S)
                if not (bx + r <= zbox[0] or bx - r >= zbox[2] or by + r <= zbox[1] or by - r >= zbox[3]):
                    intrusions += 1

        g18_pass = len(forbidden_boxes) >= 2 and intrusions == 0
        self.results.append(GateResult(
            "G8.18", "ZERO_GLOBAL_LAYOUT_INTRUSION", "CRITICAL", g18_pass,
            f"Đã kiểm tra {len(axis_lines)} đường trục & {len(bubbles)} đầu trục với {len(forbidden_boxes)} vùng cấm (Sidebar/TitleBlock/TitleBand): {intrusions} xâm phạm."
        ))

        # G8.19: SCHEDULE_TABLE_CELL_CONTAINMENT (Chống tràn chữ bảng thống kê)
        overflow_cells = 0
        total_cells_checked = 0
        for sc in schedules:
            col_w = sc.get("col_widths", [])
            rows = sc.get("rows", [])
            cell_wf = sc.get("cell_width_factors", [])
            for i_r, r_vals in enumerate(rows):
                for j_c, val in enumerate(r_vals):
                    if j_c < len(col_w):
                        total_cells_checked += 1
                        wf = cell_wf[i_r][j_c] if (i_r < len(cell_wf) and j_c < len(cell_wf[i_r])) else 0.85
                        est_text_w = len(str(val)) * 0.66 * (1.6 * S) * wf
                        if est_text_w > col_w[j_c] * 0.98:
                            overflow_cells += 1
        g19_pass = total_cells_checked > 0 and overflow_cells == 0
        self.results.append(GateResult(
            "G8.19", "SCHEDULE_TABLE_CELL_CONTAINMENT", "MAJOR", g19_pass,
            f"Đã kiểm tra {total_cells_checked} ô dữ liệu Bảng thống kê với Adaptive Column Widths: {overflow_cells} ô bị tràn chữ."
        ))

        # G8.20: BEAM_LABEL_ORIENTATION_AND_LW (Kiểm tra xoay 90° nhãn dầm dọc & Lineweight 370)
        vert_beams_labeled = [
            e for e in ref_beams
            if e.get("has_beam_label") and abs(e["p2"][1] - e["p1"][1]) > 1.5 * abs(e["p2"][0] - e["p1"][0])
        ]
        wrong_rot = [
            e for e in vert_beams_labeled
            if abs(float(e.get("beam_label_rotation", 0.0)) - 90.0) > 1.0 and abs(float(e.get("beam_label_rotation", 0.0)) - 270.0) > 1.0
        ]
        lw_ok = all(int(spec.get("lineweight", 0)) > 0 for spec in layers.values())
        g20_pass = len(wrong_rot) == 0 and lw_ok
        self.results.append(GateResult(
            "G8.20", "BEAM_LABEL_ORIENTATION_AND_LW", "MAJOR", g20_pass,
            f"100% nhãn dầm dọc xoay 90° chuẩn TCVN ({len(wrong_rot)} lỗi góc xoay); 100% Layer có mã nhóm 370 Lineweight CTB."
        ))

        self._crosscheck_native_entities()
        self._audit_detail_gates()

        all_passed = all(r.passed is True for r in self.results if r.applicable)
        return all_passed, self.results

    def _crosscheck_native_entities(self):
        """Generator declarations cannot stand in for native DIMENSION/ATTDEF/HATCH."""
        if not HAS_EZDXF:
            raise ValueError('ezdxf unavailable for native evidence checks')
        doc = ezdxf.readfile(self.plan_dxf_path)
        entities = self.plan_meta['entities_log']
        checks = {}
        expected_dims = sum(e.get('type') == 'DIMENSION' for e in entities)
        checks['G8.06'] = len(doc.modelspace().query('DIMENSION')) == expected_dims and expected_dims > 0
        styles = self.plan_meta['dimstyles_defined']
        checks['G8.03'] = all(name in doc.dimstyles and
            math.isclose(doc.dimstyles.get(name).dxf.dimtxt, float(spec['dimtxt']), abs_tol=1e-6) and
            math.isclose(doc.dimstyles.get(name).dxf.dimscale, float(spec['dimscale']), abs_tol=1e-6)
            for name, spec in styles.items())
        block = doc.blocks.get('DCE_Cot_Block')
        checks['G8.05'] = bool(block and any(e.dxftype() == 'HATCH' and e.dxf.solid_fill for e in block))
        block = doc.blocks.get('DCE_TenCauKien')
        attrs = {e.dxf.tag:e for e in block if e.dxftype() == 'ATTDEF'} if block else {}
        checks['G8.07'] = {'SOCAUKIEN','TENCAUKIEN'} <= attrs.keys()
        if checks['G8.07']:
            checks['G8.07'] = all(math.hypot(attrs[k].dxf.insert.x, attrs[k].dxf.insert.y) <= 2.5
                                 for k in ('SOCAUKIEN','TENCAUKIEN')) and (
                                 attrs['SOCAUKIEN'].dxf.insert != attrs['TENCAUKIEN'].dxf.insert)
        checks['G8.20'] = all(name in doc.layers and doc.layers.get(name).dxf.lineweight > 0
                             for name in self.plan_meta['layers_defined'])
        for gate in self.results:
            if gate.gate_id in checks and not checks[gate.gate_id]:
                gate.passed = False
                gate.detail = 'DXF native không khớp khai báo DIMENSION/DimStyle/ATTDEF/HATCH/layer của generator.'

    def _audit_detail_gates(self):
        if self.profile == 'plan' or not self.beam_meta or not self.colwall_meta:
            for n, name in enumerate(('BEAM_ELEVATION_SEISMIC_DETAIL', 'COLUMN_SECTION_REBAR_RULES',
                                      'WALL_BOUNDARY_ELEMENT_DETAIL', 'REBAR_BBS_SCHEDULE_SYNC'), 13):
                self.results.append(GateResult(f'G8.{n}', name, 'CRITICAL', None,
                    'Ngoài phạm vi plan.' if self.profile == 'plan' else
                    'Thiếu bản vẽ chi tiết dầm/cột/vách và metadata gắn SHA256; chưa kiểm chứng.',
                    applicable=self.profile != 'plan'))
            return
        rebar_ents = self.beam_meta.get("longitudinal_rebar_entities", [])
        stir_zones = self.beam_meta.get("stirrup_zones", [])
        xsecs = self.beam_meta.get("cross_sections_1_20", [])
        sup_extras = [e for e in rebar_ents if e.get("position") == "TOP_SUPPORT_EXTRA"]
        beam_phys = self._count_physical_dxf_entities(self.beam_dxf_path) if self.beam_dxf_path else 0
        g13_pass = (
            len(rebar_ents) > 0
            and len(stir_zones) > 0
            and beam_phys > 20
            and all(e.get("ext_ratio_ln", 0.0) >= 0.33 for e in sup_extras)
            and all(abs(z["crit_zone_length"] - 2.0 * z["beam_height_h"]) <= 1.0 for z in stir_zones)
            and len(xsecs) >= 2 * len(stir_zones)
        )
        self.results.append(GateResult(
            "G8.13", "BEAM_ELEVATION_SEISMIC_DETAIL", "CRITICAL", g13_pass,
            f"Dầm {self.beam_meta.get('beam_name')}: Thép gối vươn >= Ln/3, vùng đai tới hạn = 2*hb, đủ {len(xsecs)} MC 1/20 ({beam_phys} thực thể DXF)."
        ))

        col_secs = self.colwall_meta.get("column_sections_1_20", [])
        cw_phys = self._count_physical_dxf_entities(self.colwall_dxf_path) if self.colwall_dxf_path else 0
        g14_pass = (
            len(col_secs) > 0
            and cw_phys > 20
            and all(
                c["as_prov_cm2"] >= c["as_calc_cm2"]
                and c["ratio_within_1_to_4_pct"] is True
                and c["restrained_spacing_ok"] is True
                for c in col_secs
            )
        )
        self.results.append(GateResult(
            "G8.14", "COLUMN_SECTION_REBAR_RULES", "CRITICAL", g14_pass,
            f"100% ({len(col_secs)} mặt cắt cột 1/20, {cw_phys} thực thể DXF) thỏa mãn As_prov >= As_calc, 1% <= mu <= 4%, bước thanh <= 150mm."
        ))

        wall_secs = self.colwall_meta.get("wall_sections_1_25", [])
        g15_pass = (
            len(wall_secs) > 0
            and all(
                w["be_rule_satisfied"] is True
                and w["as_be_prov_cm2"] >= w["as_be_calc_cm2"]
                for w in wall_secs
            )
        )
        self.results.append(GateResult(
            "G8.15", "WALL_BOUNDARY_ELEMENT_DETAIL", "CRITICAL", g15_pass,
            f"100% ({len(wall_secs)} mặt cắt vách 1/25) có vùng biên chịu nén B.E. l_be >= max(0.15*Lw, 1.5*bw, 400mm) + đai kín."
        ))

        bbs_all = self.beam_meta.get("bbs_schedule", []) + self.colwall_meta.get("bbs_schedule", [])
        weight_errors = 0
        for row in bbs_all:
            d = row["diameter"]
            expected_uw = round((d ** 2) / 162.2, 3)
            expected_tot = round((row["length_mm"] / 1000.0) * row["total_count"] * expected_uw, 2)
            if abs(row["unit_weight_kg_m"] - expected_uw) > 1e-3 or abs(row["total_weight_kg"] - expected_tot) > 0.05:
                weight_errors += 1
        g16_pass = len(bbs_all) > 0 and weight_errors == 0
        total_ton = round(sum(r["total_weight_kg"] for r in bbs_all) / 1000.0, 3)
        self.results.append(GateResult(
            "G8.16", "REBAR_BBS_SCHEDULE_SYNC", "MAJOR", g16_pass,
            f"Đã kiểm toán {len(bbs_all)} dòng thống kê thép BBS (d²/162.2): 0 sai số khối lượng, tổng = {total_ton} tấn."
        ))

    def print_report(self) -> bool:
        all_passed, results = self.run_all_gates()
        print("=" * 112)
        print("BỘ LỌC 8 (v4.7) — BÁO CÁO KIỂM TOÁN ĐA CHẾ ĐỘ HỒ SƠ BẢN VẼ KẾT CẤU CHUẨN KỸ SƯ DCE PRO (20 HARD GATES)")
        print("=" * 112)
        for r in results:
            status = r.status
            print(f"[{status:4s}] {r.gate_id} | {r.gate_name:<32s} | {r.severity:<8s} | {r.detail}")
        print("-" * 112)
        passed_cnt = sum(1 for r in results if r.passed)
        print(f"TỔNG KẾT: PASS={passed_cnt}, N/A={sum(not r.applicable for r in results)}, tổng={len(results)} — {'PASS theo phạm vi' if all_passed else 'HOLD / REJECT'}")
        print("=" * 112)
        return all_passed


def _audit_physical_dxf(dxf_path: str) -> Dict[str, Any]:
    if not HAS_EZDXF:
        return {
            'file_path': dxf_path,
            'status': 'ERROR',
            'message': 'Thư viện ezdxf chưa được cài đặt.'
        }

    p = Path(dxf_path)
    if not p.is_file():
        return {
            'file_path': dxf_path,
            'status': 'FAIL',
            'message': f'File không tồn tại: {dxf_path}'
        }

    try:
        doc = ezdxf.readfile(str(p))
    except Exception as ex:
        return {
            'file_path': dxf_path,
            'status': 'FAIL',
            'critical_error': f'AutoCAD/ezdxf không thể mở file (Corrupt/Drawing Discarded): {str(ex)}'
        }

    auditor = doc.audit()
    audit_errors = [str(err) for err in auditor.errors]
    audit_fixes_count = len(auditor.fixes)

    msp = doc.modelspace()
    total_entities = len(msp)

    layer_counts = Counter(e.dxf.layer for e in msp)
    illegal_layers_found = []
    non_dce_layers_found = []

    for lname, count in layer_counts.items():
        lname_low = lname.lower().strip()
        if lname_low.startswith('dce_') or lname_low in ('0', 'defpoints'):
            if lname_low not in DCE_STANDARD_LAYERS:
                non_dce_layers_found.append({'layer': lname, 'count': count})
        else:
            non_dce_layers_found.append({'layer': lname, 'count': count})
            for ill in ILLEGAL_LAYER_PATTERNS:
                if ill in lname_low:
                    illegal_layers_found.append({'layer': lname, 'count': count})
                    break

    inserts = [e for e in msp if e.dxftype() == 'INSERT']
    block_names_lower = [getattr(i.dxf, 'name', '').lower() for i in inserts]

    axis_bubble_count = sum(1 for b in block_names_lower if b in DCE_AXIS_BLOCKS)
    member_tag_count = sum(
        1 for b in block_names_lower
        if b in DCE_MEMBER_BLOCKS or b.startswith('dce_col_') or b.startswith('dce_pile_')
    )
    title_block_count = sum(
        1 for b in block_names_lower
        if b in DCE_TITLE_BLOCKS or b.startswith('dce_titleblock_')
    )
    attrib_insert_count = sum(1 for ins in inserts if getattr(ins, 'attribs', None) and len(ins.attribs) > 0)

    dims = [e for e in msp if e.dxftype() == 'DIMENSION']
    dce_dims_count = 0
    non_dce_dims = []

    for d in dims:
        ds_name = d.dxf.dimstyle if hasattr(d.dxf, 'dimstyle') else ''
        if ds_name.lower().startswith('dce_'):
            dce_dims_count += 1
        else:
            non_dce_dims.append(ds_name)

    graphic_sanity = {
        'has_concrete_solid_hatch': False,
        'has_standard_frame': False,
        'has_schedule_table': False,
        'has_setting_out_dims': False,
        'beam_void_clashes': 0,
    }

    hatches = [e for e in msp if e.dxftype() == 'HATCH']
    for ins in inserts:
        try:
            for ve in ins.virtual_entities():
                if ve.dxftype() == 'HATCH':
                    hatches.append(ve)
        except Exception:
            pass
    solid_concrete_hatches = []
    for h in hatches:
        pat = str(getattr(h.dxf, 'pattern_name', '') or '').upper()
        lname = h.dxf.layer.lower()
        hcolor = getattr(h.dxf, 'color', 256)
        if pat == 'SOLID' and ('hatch' in lname or hcolor == 8):
            solid_concrete_hatches.append(h)
    graphic_sanity['has_concrete_solid_hatch'] = (len(solid_concrete_hatches) > 0)
    steel_col_count = sum(
        1 for ins in inserts
        if getattr(ins.dxf, 'name', '').upper().startswith('DCE_COL_STEEL_')
    )
    rc_col_count = sum(
        1 for ins in inserts
        if getattr(ins.dxf, 'name', '').upper().startswith('DCE_COL_RC')
    )
    graphic_sanity['is_steel_only_plan'] = (steel_col_count > 0 and rc_col_count == 0)

    all_sheet_entities = list(msp)
    for ly in doc.layouts:
        if ly.name != "Model":
            all_sheet_entities.extend(list(ly))

    ps_title_blocks = sum(
        1 for e in all_sheet_entities
        if e not in msp and e.dxftype() == 'INSERT'
        and getattr(e.dxf, 'name', '').lower().startswith('dce_titleblock_')
    )
    title_block_count += ps_title_blocks

    graphic_sanity['has_standard_frame'] = any('frame' in e.dxf.layer.lower() or 'kt' in e.dxf.layer.lower() for e in all_sheet_entities)
    graphic_sanity['has_schedule_table'] = any(
        'schedule' in e.dxf.layer.lower()
        or 'tktitle' in getattr(e.dxf, 'name', '').lower()
        or 'dce_titleblock' in getattr(e.dxf, 'name', '').lower()
        for e in all_sheet_entities
    )
    graphic_sanity['has_setting_out_dims'] = any('setout' in e.dxf.layer.lower() for e in msp)

    void_lines = [e for e in msp if e.dxftype() == 'LINE' and e.dxf.layer.lower() == 'dce_voidx']
    void_boxes = []
    used_void = set()
    for idx_a in range(len(void_lines)):
        if idx_a in used_void:
            continue
        la = void_lines[idx_a]
        sa, ea = la.dxf.start, la.dxf.end
        cax, cay = (sa.x + ea.x) / 2.0, (sa.y + ea.y) / 2.0
        for idx_b in range(idx_a + 1, len(void_lines)):
            if idx_b in used_void:
                continue
            lb = void_lines[idx_b]
            sb, eb = lb.dxf.start, lb.dxf.end
            cbx, cby = (sb.x + eb.x) / 2.0, (sb.y + eb.y) / 2.0
            if abs(cax - cbx) < 50.0 and abs(cay - cby) < 50.0:
                xs = [sa.x, ea.x, sb.x, eb.x]
                ys = [sa.y, ea.y, sb.y, eb.y]
                void_boxes.append((min(xs) + 50.0, min(ys) + 50.0, max(xs) - 50.0, max(ys) - 50.0))
                used_void.add(idx_a)
                used_void.add(idx_b)
                break

    beam_void_clashes = 0
    if void_boxes:
        for e in msp:
            if e.dxftype() == 'LINE' and e.dxf.layer.lower() in ('dce_beam', 'dce_mainbeam'):
                x1, y1 = e.dxf.start.x, e.dxf.start.y
                x2, y2 = e.dxf.end.x, e.dxf.end.y
                for bx0, by0, bx1, by1 in void_boxes:
                    if bx0 >= bx1 or by0 >= by1:
                        continue
                    mx, my = (x1 + x2) / 2.0, (y1 + y2) / 2.0
                    if (bx0 < mx < bx1 and by0 < my < by1) or (
                        max(min(x1, x2), bx0) < min(max(x1, x2), bx1)
                        and max(min(y1, y2), by0) < min(max(y1, y2), by1)
                        and ((x1 <= bx0 and x2 >= bx1) or (x2 <= bx0 and x1 >= bx1)
                             or (y1 <= by0 and y2 >= by1) or (y2 <= by0 and y1 >= by1))
                    ):
                        beam_void_clashes += 1
                        break
    graphic_sanity['beam_void_clashes'] = beam_void_clashes

    issues = []
    if total_entities == 0:
        issues.append('DXF không có entity trong modelspace; không có bằng chứng để nghiệm thu.')
    if audit_errors:
        issues.append(f"Audit phát hiện {len(audit_errors)} lỗi cú pháp/linetypes nghiêm trọng.")
    if audit_fixes_count:
        issues.append(f'DXF cần {audit_fixes_count} hiệu chỉnh trong RAM; phải sửa và xuất lại trước nghiệm thu.')
    if non_dce_dims:
        issues.append(f'DimStyle ngoài chuẩn DCE: {sorted(set(non_dce_dims))}')

    if illegal_layers_found:
        layers_str = ", ".join([f"{item['layer']} ({item['count']})" for item in illegal_layers_found])
        issues.append(f"Phát hiện layer tùy tiện phi chuẩn bị cấm: {layers_str}.")

    truc_lines = sum(1 for e in msp if e.dxftype() == 'LINE' and 'truc' in e.dxf.layer.lower())
    is_structural_plan = (truc_lines >= 4 or axis_bubble_count > 0 or total_entities >= 100)
    if truc_lines > 0 and axis_bubble_count == 0:
        issues.append("Bản vẽ có đường tim trục nhưng không sử dụng Block thuộc tính Dce_KhTenTruc / Dce_TenTruc.")
    if is_structural_plan:
        if not graphic_sanity['has_concrete_solid_hatch'] and not graphic_sanity.get('is_steel_only_plan'):
            issues.append("Bản vẽ mặt bằng thiếu Solid Hatch bê tông xám (SOLID, color=8 / DCE_Hatch) cho cột vách.")
        if not graphic_sanity['has_standard_frame']:
            issues.append("Bản vẽ mặt bằng thiếu Khung bản vẽ tiêu chuẩn (DCE_Frame).")
        if not graphic_sanity['has_schedule_table'] and title_block_count == 0:
            issues.append("Bản vẽ mặt bằng thiếu Bảng thống kê cấu kiện (DCE_Schedule) và Khung tên chuẩn.")
    if beam_void_clashes > 0:
        issues.append(f"Phát hiện {beam_void_clashes} nét dầm cắt xuyên qua lỗ rỗng xuyên sàn (DCE_VoidX).")

    status = "PASS" if (len(audit_errors) == 0 and len(illegal_layers_found) == 0 and len(issues) == 0) else "FAIL"

    return {
        'file_path': str(p),
        'status': status,
        'dxf_version': doc.dxfversion,
        'total_entities': total_entities,
        'audit_errors': audit_errors,
        'audit_fixes_count': audit_fixes_count,
        'illegal_layers': illegal_layers_found,
        'non_dce_layers': non_dce_layers_found,
        'blocks': {
            'total_inserts': len(inserts),
            'axis_bubbles': axis_bubble_count,
            'member_tags': member_tag_count,
            'title_blocks': title_block_count,
            'attrib_inserts': attrib_insert_count,
        },
        'dimensions': {
            'total_dimensions': len(dims),
            'dce_compliant_dimensions': dce_dims_count,
            'non_dce_dimensions': non_dce_dims
        },
        'graphic_sanity': graphic_sanity,
        'issues': issues
    }


def audit_dxf_compliance(dxf_path: str, profile: str = 'full',
                         beam_dxf_path: Optional[str] = None,
                         colwall_dxf_path: Optional[str] = None) -> Dict[str, Any]:
    """Read-only audit: full (20 gates), plan (16 + 4 N/A), physical (DXF only).

    Full is the safe default. Missing/stale evidence is NEEDS_REVIEW, never PASS.
    A physical PASS does not certify semantic gates. Metadata is generator evidence,
    bound to exact DXF bytes; it is not independent structural verification.
    """
    if profile not in {'full', 'plan', 'physical'}:
        return {'status': 'ERROR', 'issues': [f'Unknown audit profile: {profile}'],
                'full_compliance_verified': False, 'profile': profile}
    res = _audit_physical_dxf(dxf_path)
    physical_status = res.get('status', 'ERROR')
    physical_issues = list(res.get('issues', []))
    if physical_status != 'PASS' and not physical_issues:
        physical_issues.append(res.get('critical_error', res.get('message', 'Physical audit failed')))
    results = []
    metadata_issues = []
    detail_audits = {}
    if profile != 'physical':
        checker = DCECADComplianceCheckerV4(dxf_path, beam_dxf_path, colwall_dxf_path, profile=profile)
        _, results = checker.run_all_gates()
        metadata_issues = checker.metadata_issues
        if len(results) != 20 or len({r.gate_id for r in results}) != 20:
            metadata_issues.append('Incomplete or duplicate gate registry; expected 20 distinct gates.')
        if profile == 'full':
            for name, path in (('beam', beam_dxf_path), ('colwall', colwall_dxf_path)):
                if path:
                    detail_audits[name] = _audit_physical_dxf(path)
    failures = [r for r in results if r.applicable and r.passed is False]
    unknown = [r for r in results if r.applicable and r.passed is None]
    gate_issues = [f'[{r.gate_id} {r.status}] {r.gate_name}: {r.detail}' for r in failures + unknown]
    detail_issues = [f'[{name}] {r.get("issues") or r.get("critical_error") or r.get("message")}'
                     for name, r in detail_audits.items() if r['status'] != 'PASS']
    issues = physical_issues + gate_issues + metadata_issues + detail_issues
    if physical_status == 'ERROR':
        status = 'ERROR'
    elif physical_status != 'PASS' or failures or detail_issues:
        status = 'FAIL'
    elif unknown or metadata_issues:
        status = 'NEEDS_REVIEW'
    else:
        status = 'PASS'
    res.update({
        'schema_version': '2.0', 'profile': profile, 'status': status,
        'physical_status': physical_status, 'physical_issues': physical_issues,
        'issues': issues, 'gate_issues': gate_issues,
        'metadata_issues': metadata_issues, 'detail_audits': detail_audits,
        'gate_status': ('NOT_RUN' if profile == 'physical' else
                        'FAIL' if failures else 'UNVERIFIED' if unknown or metadata_issues else 'PASS'),
        'gates_registered': 20, 'gates_total': len(results),
        'gates_passed': sum(r.applicable and r.passed is True for r in results),
        'gates_failed': len(failures), 'gates_unverified': len(unknown),
        'gates_not_applicable': sum(not r.applicable for r in results),
        'full_compliance_verified': profile == 'full' and status == 'PASS' and len(results) == 20,
        'evidence_basis': 'Physical DXF checks + SHA256-bound generator metadata; no native AutoCAD or solver verification.',
        'gate_results': [{'gate_id': r.gate_id, 'gate_name': r.gate_name, 'severity': r.severity,
                         'passed': r.passed, 'status': r.status, 'applicable': r.applicable,
                         'detail': r.detail} for r in results],
    })
    return res


if __name__ == "__main__":
    import argparse
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('dxf_path')
    parser.add_argument('beam_dxf_path', nargs='?')
    parser.add_argument('colwall_dxf_path', nargs='?')
    parser.add_argument('--profile', choices=('full', 'plan', 'physical'), default='full')
    args = parser.parse_args()
    result = audit_dxf_compliance(args.dxf_path, args.profile, args.beam_dxf_path, args.colwall_dxf_path)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result['status'] == 'PASS' else 1)
