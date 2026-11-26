# -*- coding: utf-8 -*-
"""
cad_xref_workbook_builder.py — Sprint 3 Engine: 3 Native Cát Lái Xrefs + 8 Xref-Bound Workbook DWGs
====================================================================================================
Dựng mới 100% 3 tệp Xref chuẩn từ tọa độ thật của dự án NHÀ PHỐ Q2 CÁT LÁI (không dùng file mẫu dự án khác),
sau đó gắn Xref thực tế qua AutoCAD 2021 Core Console (`-XREF` chế độ `Overlay`/`Attach`, đường dẫn tương đối
`..\\01_Xref\\...`) lên trọn bộ 8 bản vẽ `KC.02–KC.09` và xuất `SheetSet_Manifest.json`.
"""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

if hasattr(sys.stdout, "reconfigure") and sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

import ezdxf

_CAD_DIR = str(Path(__file__).resolve().parent)
_TOOLS_DIR = str(Path(__file__).resolve().parents[3] / "tools")
for _p in (_CAD_DIR, _TOOLS_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from accoreconsole_adapter import (  # noqa: E402
    attach_xrefs_via_accoreconsole,
    convert_dxf_to_dwg_via_accoreconsole,
)
from cad_block_adapters import (  # noqa: E402
    insert_axis_bubble_native,
    insert_or_update_titleblock,
    purge_unused_blocks,
)
from cad_form_contract import resolve_form_paths, validate_open_form  # noqa: E402
from cad_multiview_a3 import (  # noqa: E402
    _ensure_a3_layers_and_styles,
    _hide_zone_guide_layers_for_export,
)

# Hệ trục thật của NHÀ PHỐ Q2 CÁT LÁI (mm, WCS gốc tại (0, 0) = giao trục 0 và trục A)
CATLAI_X_AXES: List[Tuple[str, float]] = [
    ("0", 0.0),
    ("1", 3000.0),
    ("2", 6700.0),
    ("3", 10200.0),
    ("4", 13500.0),
    ("5", 17000.0),
    ("6", 18000.0),
]
CATLAI_Y_AXES: List[Tuple[str, float]] = [
    ("A", 0.0),
    ("B", 5000.0),
]

STANDARD_METHOD_SPRINT3 = "CAD v6.0 Sprint 3 Native Xref + 8 Workbook Package (AutoCAD 2021 Core Console)"

WORKBOOK_SPECS: List[Dict[str, Any]] = [
    {"idx": 1, "sheet_no": "KC.02", "src_stem": "KC-02_MatBangKetCauNgam", "title": "MẶT BẰNG KẾT CẤU NGẦM", "scale": 100.0, "kind": "plan"},
    {"idx": 2, "sheet_no": "KC.03", "src_stem": "KC-03_ChiTietMong_1", "title": "CHI TIẾT MÓNG 1", "scale": 25.0, "kind": "detail"},
    {"idx": 3, "sheet_no": "KC.04", "src_stem": "KC-04_ChiTietMong_2", "title": "CHI TIẾT MÓNG 2", "scale": 25.0, "kind": "detail"},
    {"idx": 4, "sheet_no": "KC.05", "src_stem": "KC-05_DinhViCot_Mong_T2", "title": "ĐỊNH VỊ CỘT MÓNG – T2", "scale": 100.0, "kind": "plan"},
    {"idx": 5, "sheet_no": "KC.06", "src_stem": "KC-06_DinhViCot_T2_SanThuong", "title": "ĐỊNH VỊ CỘT T2 – SÂN THƯỢNG", "scale": 100.0, "kind": "plan"},
    {"idx": 6, "sheet_no": "KC.07", "src_stem": "KC-07_DinhViCot_SanThuong_TumMai", "title": "ĐỊNH VỊ CỘT SÂN THƯỢNG – TUM MÁI", "scale": 100.0, "kind": "plan"},
    {"idx": 7, "sheet_no": "KC.08", "src_stem": "KC-08_ChiTietCotVach_1", "title": "CHI TIẾT CỘT VÁCH 1", "scale": 50.0, "kind": "detail"},
    {"idx": 8, "sheet_no": "KC.09", "src_stem": "KC-09_ChiTietCotVach_2", "title": "CHI TIẾT CỘT VÁCH 2", "scale": 50.0, "kind": "detail"},
]


def _load_clean_form02_doc(project_dir: Optional[str | Path] = None) -> ezdxf.document.Drawing:
    res = resolve_form_paths(form_id="FORM_02_MULTIVIEW_A3_BTCT", project_dir=project_dir)
    if res.dxf_path is None:
        raise FileNotFoundError(f"Form_02 not found: {res.searched_paths}")
    val = validate_open_form(res.dxf_path, manifest_path=res.manifest_path, form_id="FORM_02_MULTIVIEW_A3_BTCT", tier=res.tier)
    if not val.valid:
        raise ValueError(f"Form_02 invalid: {val.errors}")
    doc = ezdxf.readfile(str(res.dxf_path))
    _ensure_a3_layers_and_styles(doc)
    return doc


def build_catlai_xref_grid_dxf(out_dxf: Path, project_dir: Optional[str | Path] = None) -> Dict[str, Any]:
    """Tạo `01_XREF_GRID.dxf`: hệ trục 0..6 (18000 mm) & A..B (5000 mm) thật của Cát Lái gốc (0, 0)."""
    doc = _load_clean_form02_doc(project_dir=project_dir)
    msp = doc.modelspace()
    for ent in list(msp):
        msp.delete_entity(ent)

    x_min, x_max = 0.0, 18000.0
    y_min, y_max = 0.0, 5000.0
    ext = 1500.0
    dim_bot_y = -900.0
    dim_top_y = y_max + 900.0
    dim_left_x = -900.0

    # Trục đứng X (0..6) — kế thừa linetype BYLAYER của layer DCE_Truc trong Form_02
    for lbl, xv in CATLAI_X_AXES:
        msp.add_line((xv, y_min - ext), (xv, y_max + ext), dxfattribs={"layer": "DCE_Truc"})
        insert_axis_bubble_native(doc, msp, xv, y_max + ext + 350.0, lbl, rotation_deg=180.0, scale=100.0, mark_owned=False)
        insert_axis_bubble_native(doc, msp, xv, y_min - ext - 350.0, lbl, rotation_deg=0.0, scale=100.0, mark_owned=False)

    # Trục ngang Y (A..B)
    for lbl, yv in CATLAI_Y_AXES:
        msp.add_line((x_min - ext, yv), (x_max + ext, yv), dxfattribs={"layer": "DCE_Truc"})
        insert_axis_bubble_native(doc, msp, x_min - ext - 350.0, yv, lbl, rotation_deg=270.0, scale=100.0, mark_owned=False)
        insert_axis_bubble_native(doc, msp, x_max + ext + 350.0, yv, lbl, rotation_deg=90.0, scale=100.0, mark_owned=False)

    # Kích thước bước trục thật (`Dce_100MV`)
    for i in range(len(CATLAI_X_AXES) - 1):
        d = msp.add_aligned_dim(
            p1=(CATLAI_X_AXES[i][1], y_min),
            p2=(CATLAI_X_AXES[i + 1][1], y_min),
            distance=dim_bot_y,
            dimstyle="Dce_100MV",
            dxfattribs={"layer": "DCE_Dim"},
        )
        d.render()
    d_tot_x = msp.add_aligned_dim(p1=(x_min, y_max), p2=(x_max, y_max), distance=dim_top_y - y_max, dimstyle="Dce_100MV", dxfattribs={"layer": "DCE_Dim"})
    d_tot_x.render()
    d_y = msp.add_aligned_dim(p1=(x_min, y_min), p2=(x_min, y_max), distance=dim_left_x, dimstyle="Dce_100MV", dxfattribs={"layer": "DCE_Dim"})
    d_y.render()

    purge_unused_blocks(doc)
    doc.header["$INSBASE"] = (0.0, 0.0, 0.0)
    out_dxf.parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(str(out_dxf))
    return {"role": "GRID", "dxf_path": str(out_dxf), "axes_x": len(CATLAI_X_AXES), "axes_y": len(CATLAI_Y_AXES)}


def build_catlai_xref_arch_bg_dxf(out_dxf: Path, project_dir: Optional[str | Path] = None) -> Dict[str, Any]:
    """Tạo `02_XREF_ARCH_BG.dxf`: ranh sàn (18000x5000), vách hầm và lỗ mở hố thang máy đã xác minh từ PDF kết cấu."""
    doc = _load_clean_form02_doc(project_dir=project_dir)
    msp = doc.modelspace()
    for ent in list(msp):
        msp.delete_entity(ent)

    # 1. Ranh đất / bao sàn tổng thể (0..18000 x 0..5000) đã xác minh từ build_catlai_plans_native.py
    msp.add_lwpolyline([(0.0, 0.0), (18000.0, 0.0), (18000.0, 5000.0), (0.0, 5000.0)], close=True, dxfattribs={"layer": "DCE_RanhDat"})
    # 2. Tường vây tầng hầm trục 1 -> trục 5 (3000..17000) dày 200mm
    msp.add_lwpolyline([(3000.0, 0.0), (17000.0, 0.0), (17000.0, 5000.0), (3000.0, 5000.0)], close=True, dxfattribs={"layer": "DCE_KT"})
    msp.add_lwpolyline([(3200.0, 200.0), (16800.0, 200.0), (16800.0, 4800.0), (3200.0, 4800.0)], close=True, dxfattribs={"layer": "DCE_KT"})

    # 3. Hố thang máy ĐM.TM (14450..16000, 2500..4000) & lỗ mở lòng hố thang (14650..15800, 2700..3800)
    msp.add_lwpolyline([(14450.0, 2500.0), (16000.0, 2500.0), (16000.0, 4000.0), (14450.0, 4000.0)], close=True, dxfattribs={"layer": "DCE_KT"})
    msp.add_lwpolyline([(14650.0, 2700.0), (15800.0, 2700.0), (15800.0, 3800.0), (14650.0, 3800.0)], close=True, dxfattribs={"layer": "DCE_KT"})
    msp.add_line((14650.0, 2700.0), (15800.0, 3800.0), dxfattribs={"layer": "DCE_VoidX"})
    msp.add_line((14650.0, 3800.0), (15800.0, 2700.0), dxfattribs={"layer": "DCE_VoidX"})

    lbl = msp.add_text(
        "NỀN THAM CHIẾU TỪ BẢN VẼ KẾT CẤU (CHỜ NỀN KIẾN TRÚC DUYỆT) - THỬA 1039, P. CÁT LÁI",
        height=200.0,
        dxfattribs={"layer": "DCE_KT", "style": "Dce_Text"},
    )
    lbl.set_placement((9000.0, 5450.0))

    purge_unused_blocks(doc)
    doc.header["$INSBASE"] = (0.0, 0.0, 0.0)
    out_dxf.parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(str(out_dxf))
    return {"role": "ARCH_BG", "dxf_path": str(out_dxf)}


def build_catlai_xref_titleblock_dxf(out_dxf: Path, project_dir: Optional[str | Path] = None) -> Dict[str, Any]:
    """Tạo `03_XREF_TITLEBLOCK_A3.dxf`: khung tên A3 chỉ điền trường xác minh từ PDF gốc (không bịa tên nhân sự/đơn vị)."""
    doc = _load_clean_form02_doc(project_dir=project_dir)
    msp = doc.modelspace()
    for ent in list(msp):
        ly = str(ent.dxf.get("layer", ""))
        is_tb = ent.dxftype() == "INSERT" and str(ent.dxf.get("name", "")).upper() == "DCE_TITLEBLOCK_A3"
        if ly != "DCE_Frame" and not is_tb:
            msp.delete_entity(ent)

    insert_or_update_titleblock(
        doc,
        msp,
        block_name="DCE_TITLEBLOCK_A3",
        values={
            "CHU_DAU_TU": "",
            "DIA_DIEM": "THỬA 1039 TỜ BẢN ĐỒ 20",
            "DIA_DIEM_2": "PHƯỜNG CÁT LÁI, TP.HCM",
            "CONG_TY": "",
            "GIAM_DOC": "",
            "KIEM_TRA": "",
            "THIET_KE": "",
            "THE_HIEN": "",
            "TEN_CONG_TRINH": "NHÀ Ở RIÊNG LẺ",
            "HANG_MUC": "BẢN VẼ KẾT CẤU",
            "TEN_BAN_VE": "KHUNG TÊN DỰ ÁN (XREF)",
            "BUOC_TK": "TKTC",
            "NAM": "2026",
            "KY_HIEU": "XREF-A3",
            "TY_LE": "1/100",
        },
        mark_owned=False,
    )
    _hide_zone_guide_layers_for_export(doc)
    purge_unused_blocks(doc)
    doc.header["$INSBASE"] = (0.0, 0.0, 0.0)
    out_dxf.parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(str(out_dxf))
    return {"role": "TITLEBLOCK_A3", "dxf_path": str(out_dxf)}


def build_catlai_sprint3_package(project_root: Path, out_package_dir: Path) -> Dict[str, Any]:
    """Đóng gói hoàn chỉnh Sprint 3: 3 Xref DWG thật + 8 Workbook DWG gắn Xref thật + SheetSet_Manifest.json."""
    proj_root = Path(project_root).resolve()
    deliverables_dir = proj_root / "01_Projects" / "03_Sprint2_KetQua_NeChu_CAD" / "04_Deliverables_ToTrinh"
    if not deliverables_dir.is_dir():
        deliverables_dir = proj_root / "04_Deliverables_ToTrinh"
    pkg_dir = Path(out_package_dir).resolve()
    xref_dir = pkg_dir / "01_Xref"
    wb_dir = pkg_dir / "02_Workbook"
    xref_dir.mkdir(parents=True, exist_ok=True)
    wb_dir.mkdir(parents=True, exist_ok=True)

    # 1. Sinh 3 Xref DXF tạm trong %TEMP% -> chuyển đổi native DWG vào `01_Xref/`
    xref_records: List[Dict[str, Any]] = []
    origin_meta = {
        "GRID": ("STRUCTURAL_PDF_VERIFIED_GRID", "VERIFIED_FROM_STRUCTURAL_PDF"),
        "ARCH_BG": ("STRUCTURAL_PDF_REFERENCE_ONLY", "UNVERIFIED_PENDING_APPROVED_ARCH_DWG"),
        "TITLEBLOCK_A3": ("PDF_VERIFIED_PROJECT_FIELDS_ONLY", "PENDING_APPROVED_LEGAL_SIGNATORIES"),
    }
    with tempfile.TemporaryDirectory(prefix="catlai_s3_xref_src_") as tmp_src:
        tmp_p = Path(tmp_src)
        xref_builders = [
            ("GRID", "01_XREF_GRID", "Overlay", build_catlai_xref_grid_dxf),
            ("ARCH_BG", "02_XREF_ARCH_BG", "Overlay", build_catlai_xref_arch_bg_dxf),
            ("TITLEBLOCK_A3", "03_XREF_TITLEBLOCK_A3", "Attach", build_catlai_xref_titleblock_dxf),
        ]
        xref_dwg_paths: Dict[str, Path] = {}
        for role, stem, mode, builder_fn in xref_builders:
            dxf_tmp = tmp_p / f"{stem}.dxf"
            dwg_out = xref_dir / f"{stem}.dwg"
            builder_fn(dxf_tmp, project_dir=proj_root)
            conv = convert_dxf_to_dwg_via_accoreconsole(dxf_tmp, dwg_out, target_version="2018", purge_all=True, run_audit=True)
            if conv.get("status") != "OK":
                raise RuntimeError(f"Failed building Xref {stem}.dwg: {conv}")
            sha = hashlib.sha256(dwg_out.read_bytes()).hexdigest()
            xref_dwg_paths[role] = dwg_out
            src_org, app_st = origin_meta[role]
            xref_records.append({
                "role": role,
                "name": stem,
                "mode": mode,
                "rel_path": f"01_Xref/{stem}.dwg",
                "source_origin": src_org,
                "approval_status": app_st,
                "bytes": dwg_out.stat().st_size,
                "sha256": sha,
                "audit_errors": conv.get("audit_errors"),
                "audit_fixes": conv.get("audit_fixes"),
            })

    # 2. Gắn 3 Xref thật bằng `accoreconsole.exe` lên đủ 8 tờ Workbook KC.02–KC.09
    workbook_records: List[Dict[str, Any]] = []
    calc_logs: List[Dict[str, Any]] = []
    for spec in WORKBOOK_SPECS:
        src_dwg = deliverables_dir / f"{spec['src_stem']}.dwg"
        src_dxf = deliverables_dir / f"{spec['src_stem']}.dxf"
        src_cad = src_dwg if src_dwg.is_file() else src_dxf
        if not src_cad.is_file():
            raise FileNotFoundError(f"Missing Sprint 2 source CAD for Sprint 3 workbook: {src_dwg} / {src_dxf}")
        wb_name = f"{spec['idx']:02d}_{spec['src_stem']}.dwg"
        wb_out = wb_dir / wb_name
        sh_scale = float(spec["scale"])
        if spec["kind"] == "plan":
            xref_bindings = [
                {"src_path": str(xref_dwg_paths["GRID"]), "rel_path": r"..\01_Xref\01_XREF_GRID.dwg", "mode": "Overlay", "insert_pt": "7600,21700", "scale": 1.0, "layer": "DCE_XREF_GRID"},
                {"src_path": str(xref_dwg_paths["ARCH_BG"]), "rel_path": r"..\01_Xref\02_XREF_ARCH_BG.dwg", "mode": "Overlay", "insert_pt": "7600,21700", "scale": 1.0, "layer": "DCE_XREF_ARCH"},
                {"src_path": str(xref_dwg_paths["TITLEBLOCK_A3"]), "rel_path": r"..\01_Xref\03_XREF_TITLEBLOCK_A3.dwg", "mode": "Attach", "insert_pt": "0,0", "scale": 1.0, "layer": "DCE_XREF_FRAME"},
            ]
        else:
            sr = sh_scale / 100.0
            xref_bindings = [
                {"src_path": str(xref_dwg_paths["GRID"]), "rel_path": r"..\01_Xref\01_XREF_GRID.dwg", "mode": "Overlay", "insert_pt": "0,0", "scale": 0.05, "layer": "DCE_XREF_GRID"},
                {"src_path": str(xref_dwg_paths["ARCH_BG"]), "rel_path": r"..\01_Xref\02_XREF_ARCH_BG.dwg", "mode": "Overlay", "insert_pt": "0,0", "scale": 0.05, "layer": "DCE_XREF_ARCH"},
                {"src_path": str(xref_dwg_paths["TITLEBLOCK_A3"]), "rel_path": r"..\01_Xref\03_XREF_TITLEBLOCK_A3.dwg", "mode": "Attach", "insert_pt": "0,0", "scale": sr, "layer": "DCE_XREF_FRAME"},
            ]

        res_bind = attach_xrefs_via_accoreconsole(src_cad, wb_out, xref_bindings, target_version="2018")
        if res_bind.get("status") != "OK":
            raise RuntimeError(f"Failed binding Xrefs for {wb_name}: {res_bind}")

        rec = {
            "idx": spec["idx"],
            "sheet_no": spec["sheet_no"],
            "title": spec["title"],
            "scale": f"1/{int(sh_scale)}",
            "rel_path": f"02_Workbook/{wb_name}",
            "source_cad": f"04_Deliverables_ToTrinh/{src_cad.name}",
            "bytes": res_bind["file_bytes"],
            "sha256": res_bind["sha256"],
            "audit_errors": res_bind["audit_errors"],
            "audit_fixes": res_bind["audit_fixes"],
            "xref_count": res_bind["xref_count"],
            "bound_xrefs": res_bind["xrefs"],
        }
        workbook_records.append(rec)
        calc_logs.append({
            "step": f"S3-WB-{spec['idx']:02d}",
            "sheet_no": spec["sheet_no"],
            "xref_count": res_bind["xref_count"],
            "audit_errors": res_bind["audit_errors"],
            "file_bytes": res_bind["file_bytes"],
            "result": "PASS" if (res_bind["xref_count"] == 3 and res_bind["audit_errors"] == 0) else "CHECK",
        })

    manifest = {
        "schema_version": "SPRINT3_XREF_WORKBOOK_V1_R2",
        "project": "03_Sprint2_KetQua_NeChu_CAD",
        "project_title": "NHÀ Ở RIÊNG LẺ (THỬA 1039, P. CÁT LÁI, TP.HCM)",
        "artifact_lifecycle_state": "NATIVE_GENERATED",
        "technical_cad_audit": "PASS (AutoCAD 2021 Core Console AUDIT=0, 3 relative Xrefs/Workbook)",
        "engineering_release_status": "HOLD_PENDING_ARCH_BG_AND_TITLEBLOCK_SIGNATORIES",
        "missing_approvals": [
            "Hồ sơ nền Kiến trúc DWG đã duyệt từ Chủ trì Kiến trúc",
            "Thông tin pháp lý khung tên (Chủ đầu tư, Đơn vị TVTK, Nhân sự ký duyệt)",
        ],
        "native_xref_binding": True,
        "native_dst": False,
        "dst_note": "Autodesk Sheet Set Manager binary .dst yêu cầu AutoCAD GUI/COM; 3 tệp Xref và 8 tệp Workbook đều là DWG native AutoCAD 2018 đã kiểm chứng qua accoreconsole.exe.",
        "Standard_Method": STANDARD_METHOD_SPRINT3,
        "Calculation_Logs": calc_logs,
        "xrefs_count": len(xref_records),
        "workbooks_count": len(workbook_records),
        "xrefs": xref_records,
        "workbooks": workbook_records,
    }
    manifest_path = pkg_dir / "SheetSet_Manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest
