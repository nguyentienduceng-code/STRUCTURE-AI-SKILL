# -*- coding: utf-8 -*-
"""
cad_form_generator.py — Generator for the 4 Editable Open CAD Form Library
===========================================================================

Generates the 4 canonical user-editable DXF Forms + `.manifest.json` contracts
+ AutoCAD editing guide in BOTH:
  - `.agents/_SHARED/data/CAD_Forms/`           (immutable SSOT fallback)
  - `00_Template_&_Standards/CAD_Forms/`        (user-editable on Google Drive)

Each DXF Form clones `DCE_Pro_And_Steel_Template.dxf` (all 78+ authentic
DCE Pro & Steel layers, 18 `Dce_*MV` DimStyles, 98+ DCE Blocks), adds native
`DCE_TITLEBLOCK_A1/A3` ATTDEF blocks, `DCE_Pile_*` + `DCE_COL_*` named blocks,
non-plotting `DCE_ZONE_*` marker rectangles (`plot=0`), and preserves full AC1021
compatibility so engineers can open and customize any Form directly in AutoCAD.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

import ezdxf
from ezdxf.enums import TextEntityAlignment

from cad_form_contract import (
    AGENTS_DIR,
    FORM_CATALOG,
    SSOT_FORMS_DIR,
    USER_FORMS_DIR,
    build_default_manifest,
    refresh_manifest_from_form,
    validate_open_form,
)
from cad_block_adapters import (
    ensure_column_geom_block,
    ensure_pile_block,
    ensure_titleblock_a1_definition,
    ensure_titleblock_a3_definition,
    insert_or_update_titleblock,
)

BASE_TEMPLATE_CANDIDATES = [
    AGENTS_DIR / "_SHARED" / "data" / "DCE_Pro_And_Steel_Template.dxf",
    AGENTS_DIR / "skills" / "Technical_Illustrator" / "cad_integration" / "templates" / "DCE_Master_Seed_Template.dxf",
]


def _pick_base_template() -> Optional[Path]:
    for cand in BASE_TEMPLATE_CANDIDATES:
        if cand.exists():
            return cand
    return None


def _ensure_zone_layer(doc: ezdxf.document.Drawing, layer_name: str, color: int = 40) -> None:
    """Create non-plotting zone guide layer (`plot=0`) visible on screen but hidden in PDF plot."""
    lt = "DASHED" if "DASHED" in doc.linetypes else ("HIDDEN_DBIM" if "HIDDEN_DBIM" in doc.linetypes else "Continuous")
    if layer_name in doc.layers:
        ly = doc.layers.get(layer_name)
    else:
        ly = doc.layers.add(layer_name, color=color, linetype=lt, lineweight=15)
    try:
        ly.dxf.plot = 0
    except Exception:
        pass


def _ensure_core_layers_in_form(doc: ezdxf.document.Drawing) -> None:
    """Guarantee all DCE + Steel + Plan + Zone layers exist with authentic dce_native colors."""
    try:
        shared_ctx = AGENTS_DIR / "_SHARED" / "SHARED_CONTEXT"
        if str(shared_ctx) not in sys.path:
            sys.path.insert(0, str(shared_ctx))
        from cad_layer_standard import get_layer_specs
        specs = get_layer_specs(profile="dce_native", include_compat=False)
        for lname, sp in specs.items():
            if lname in doc.layers:
                ly = doc.layers.get(lname)
                if int(getattr(ly.dxf, "lineweight", -3)) <= 0:
                    ly.dxf.lineweight = int(sp.get("lineweight", 18))
            else:
                lt = str(sp.get("linetype", "Continuous"))
                if lt not in doc.linetypes:
                    lt = "Continuous"
                doc.layers.add(
                    lname,
                    color=int(sp.get("color", 7)),
                    linetype=lt,
                    lineweight=int(sp.get("lineweight", 18)),
                )
    except Exception:
        pass

    if "Dce_Text" not in doc.styles:
        try:
            doc.styles.add("Dce_Text", font="arial.ttf")
        except Exception:
            pass

    for ly in doc.layers:
        if ly.dxf.name.lower() == "defpoints":
            continue
        if int(getattr(ly.dxf, "lineweight", -3)) <= 0:
            try:
                ly.dxf.lineweight = 18
            except Exception:
                pass


def _add_rect(msp, bbox: Tuple[float, float, float, float], layer: str) -> None:
    x0, y0, x1, y1 = bbox
    msp.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], close=True, dxfattribs={"layer": layer, "color": 256})


def _add_zone_box(msp, doc, layer_name: str, bbox: Tuple[float, float, float, float], hint: str, color: int = 40) -> None:
    _ensure_zone_layer(doc, layer_name, color=color)
    _ensure_zone_layer(doc, "DCE_ZONE_GUIDE", color=9)
    _add_rect(msp, bbox, layer=layer_name)
    x0, y0, x1, y1 = bbox
    t = msp.add_text(
        f"[{layer_name}] {hint}",
        height=max(130.0, min(280.0, (x1 - x0) * 0.018)),
        dxfattribs={"layer": "DCE_ZONE_GUIDE", "style": "Dce_Text", "color": 256},
    )
    t.set_placement((x0 + 180.0, y1 - 220.0), align=TextEntityAlignment.TOP_LEFT)


def _warmup_sample_blocks(doc: ezdxf.document.Drawing) -> None:
    """Pre-register Pile and Column sample named blocks inside each Form."""
    for kind in ("TYPE1", "TYPE2", "TYPE3"):
        ensure_pile_block(doc, kind=kind, size_mm=250.0, shape="SQUARE")
    ensure_pile_block(doc, kind="TYPE1", size_mm=300.0, shape="CIRCLE")
    ensure_column_geom_block(doc, kind="RC", b_mm=200.0, h_mm=200.0)
    ensure_column_geom_block(doc, kind="RC", b_mm=200.0, h_mm=300.0)
    ensure_column_geom_block(doc, kind="RC_STOPPED", b_mm=200.0, h_mm=200.0)
    ensure_column_geom_block(doc, kind="STEEL_H", b_mm=200.0, h_mm=200.0)
    ensure_titleblock_a1_definition(doc)
    ensure_titleblock_a3_definition(doc)


def _populate_form_geometry(doc: ezdxf.document.Drawing, form_id: str) -> None:
    msp = doc.modelspace()
    for ent in list(msp):
        msp.delete_entity(ent)

    doc.header["$INSUNITS"] = 4
    doc.header["$MEASUREMENT"] = 1
    doc.header["$LTSCALE"] = 100.0

    _ensure_core_layers_in_form(doc)
    _warmup_sample_blocks(doc)

    if form_id == "FORM_02_MULTIVIEW_A3_BTCT":
        # Canonical A3 Landscape Dual-Viewport Form
        _add_rect(msp, (0.0, 0.0, 42000.0, 29700.0), layer="DCE_Frame")
        _add_rect(msp, (500.0, 212.0, 41821.0, 29488.0), layer="DCE_Frame")
        msp.add_line((500.0, 14850.0), (36858.0, 14850.0), dxfattribs={"layer": "DCE_Frame", "color": 256})
        _add_zone_box(msp, doc, "DCE_ZONE_VIEWPORT_TOP", (700.0, 15250.0, 28300.0, 29200.0), "Vùng Mặt bằng trên (TOP) - Keo gian tuy y", color=40)
        _add_zone_box(msp, doc, "DCE_ZONE_VIEWPORT_BOTTOM", (700.0, 650.0, 28300.0, 14500.0), "Vùng Mặt bằng duoi (BOT) - Keo gian tuy y", color=40)
        _add_zone_box(msp, doc, "DCE_ZONE_TABLE", (700.0, 15250.0, 11200.0, 18600.0), "Vùng Bang thong ke coc/cau kien", color=30)
        _add_zone_box(msp, doc, "DCE_ZONE_NOTE", (28500.0, 650.0, 36400.0, 14500.0), "Vùng Hop Ghi chu", color=50)
        _add_zone_box(msp, doc, "DCE_ZONE_KEYPLAN", (36950.0, 22200.0, 41750.0, 29350.0), "KEY PLAN", color=60)
        insert_or_update_titleblock(
            doc, msp, "DCE_TITLEBLOCK_A3",
            {
                "CHU_DAU_TU": "TÊN CHỦ ĐẦU TƯ",
                "DIA_DIEM": "ĐỊA ĐIỂM XÂY DỰNG",
                "CONG_TY": "CÔNG TY TƯ VẤN THIẾT KẾ",
                "TEN_CONG_TRINH": "TÊN CÔNG TRÌNH",
                "HANG_MUC": "BẢN VẼ KẾT CẤU",
                "TEN_BAN_VE": "MẶT BẰNG KẾT CẤU",
                "BUOC_TK": "TKTC",
                "NAM": "2026",
                "KY_HIEU": "KC.02",
                "TY_LE": "1/100",
            },
            mark_owned=False,
        )
        doc.header["$EXTMIN"] = (0.0, 0.0, 0.0)
        doc.header["$EXTMAX"] = (42000.0, 29700.0, 0.0)

    elif form_id in ("FORM_01_MATBANG_A1_BTCT", "FORM_03_KETCAU_THEP_STEEL"):
        # Canonical A1 Landscape Sheet (RC Plan or Steel Plan)
        _add_rect(msp, (0.0, 0.0, 84100.0, 59400.0), layer="DCE_Frame")
        _add_rect(msp, (2500.0, 1000.0, 83600.0, 58400.0), layer="DCE_Frame")
        msp.add_line((72000.0, 1000.0), (72000.0, 58400.0), dxfattribs={"layer": "DCE_Frame", "color": 256})
        vp_hint = "Vùng Mat bang Ket cau Thep (DCE STEEL)" if "STEEL" in form_id else "Vùng Mat bang Ket cau BTCT (A1)"
        _add_zone_box(msp, doc, "DCE_ZONE_VIEWPORT_MAIN", (2800.0, 1500.0, 71500.0, 57900.0), vp_hint, color=40)
        _add_zone_box(msp, doc, "DCE_ZONE_TABLE", (72500.0, 33000.0, 83600.0, 57900.0), "Vùng Bang thong ke", color=30)
        _add_zone_box(msp, doc, "DCE_ZONE_NOTE", (72500.0, 15600.0, 83600.0, 32200.0), "Vùng Ghi chu ky thuat", color=50)
        insert_or_update_titleblock(
            doc, msp, "DCE_TITLEBLOCK_A1",
            {
                "CHU_DAU_TU": "TÊN CHỦ ĐẦU TƯ",
                "CONG_TY": "CÔNG TY TƯ VẤN THIẾT KẾ",
                "TEN_CONG_TRINH": "TÊN CÔNG TRÌNH",
                "TEN_BAN_VE": "KẾT CẤU THÉP" if "STEEL" in form_id else "MẶT BẰNG KẾT CẤU",
                "TY_LE": "1/100",
                "BUOC_TK": "TKTC",
                "KY_HIEU": "TH-01" if "STEEL" in form_id else "KC-01",
            },
            mark_owned=False,
        )
        doc.header["$EXTMIN"] = (0.0, 0.0, 0.0)
        doc.header["$EXTMAX"] = (84100.0, 59400.0, 0.0)

    elif form_id == "FORM_04_CHITIET_COC_DAM_COT":
        # Canonical A3 Landscape Detail Sheet (Piles / Columns / Beams / Rebar TK)
        _add_rect(msp, (0.0, 0.0, 42000.0, 29700.0), layer="DCE_Frame")
        _add_rect(msp, (500.0, 212.0, 41821.0, 29488.0), layer="DCE_Frame")
        msp.add_line((500.0, 14850.0), (36858.0, 14850.0), dxfattribs={"layer": "DCE_Frame", "color": 256})
        _add_zone_box(msp, doc, "DCE_ZONE_DETAIL_1", (700.0, 15250.0, 24000.0, 29200.0), "Vùng Chi tiet 1 (Coc / Dai mong / Cot)", color=40)
        _add_zone_box(msp, doc, "DCE_ZONE_DETAIL_2", (700.0, 650.0, 24000.0, 14500.0), "Vùng Chi tiet 2 (Mat cat Dam / San / Thang)", color=40)
        _add_zone_box(msp, doc, "DCE_ZONE_TABLE", (24400.0, 15250.0, 36400.0, 29200.0), "Vùng Bang thong ke cot thep (TK1..TK44)", color=30)
        _add_zone_box(msp, doc, "DCE_ZONE_NOTE", (24400.0, 650.0, 36400.0, 14500.0), "Vùng Ghi chu chi tiet & Neo noi thep", color=50)
        insert_or_update_titleblock(
            doc, msp, "DCE_TITLEBLOCK_A3",
            {
                "CHU_DAU_TU": "TÊN CHỦ ĐẦU TƯ",
                "DIA_DIEM": "ĐỊA ĐIỂM XÂY DỰNG",
                "CONG_TY": "CÔNG TY TƯ VẤN THIẾT KẾ",
                "TEN_CONG_TRINH": "TÊN CÔNG TRÌNH",
                "HANG_MUC": "CHI TIẾT KẾT CẤU",
                "TEN_BAN_VE": "CHI TIẾT CỌC - ĐÀI - DẦM - CỘT",
                "BUOC_TK": "TKTC",
                "NAM": "2026",
                "KY_HIEU": "KC.10",
                "TY_LE": "1/20",
            },
            mark_owned=False,
        )
        doc.header["$EXTMIN"] = (0.0, 0.0, 0.0)
        doc.header["$EXTMAX"] = (42000.0, 29700.0, 0.0)


def generate_single_form(
    form_id: str,
    target_dir: Path,
    base_template_path: Optional[Path] = None,
) -> Tuple[Path, Path, Dict[str, Any]]:
    spec = FORM_CATALOG[form_id]
    target_dir.mkdir(parents=True, exist_ok=True)
    src = base_template_path or _pick_base_template()
    doc = ezdxf.readfile(str(src)) if (src and src.exists()) else ezdxf.new("R2007", setup=True)
    _populate_form_geometry(doc, form_id)

    out_dxf = target_dir / spec["filename"]
    doc.saveas(str(out_dxf), encoding="utf-8")

    manifest_path = out_dxf.with_suffix(".manifest.json")
    manifest = build_default_manifest(form_id)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    refresh_manifest_from_form(out_dxf, manifest_path=manifest_path, form_id=form_id)

    val = validate_open_form(out_dxf, manifest_path=manifest_path, form_id=form_id, tier="generated")
    if not val.valid:
        raise RuntimeError(f"Generated Form {form_id} failed self-validation: {val.errors}")
    return out_dxf, manifest_path, val.to_dict()


def write_user_guide(target_dir: Path) -> Path:
    guide = """# HƯỚNG DẪN TÙY BIẾN 4 BỘ FORM CAD TRỰC TIẾP TRONG AUTOCAD

Thư mục này chứa **4 Bộ Form Mẫu Mở** đồng bộ trên Google Drive để kỹ sư tự mở bằng AutoCAD chỉnh sửa giao diện, khung tên, màu layer, dimstyle và bố cục khung nhìn. Khi Agent xuất bản vẽ ở chế độ `template_mode="open"`, toàn bộ chỉnh sửa của bạn sẽ được **giữ nguyên 100%**.

## 1. Danh mục 4 Bộ Form

| Tệp Form | Khổ giấy | Công dụng | Block Khung tên |
| :--- | :---: | :--- | :--- |
| `Form_01_MatBang_A1_BTCT.dxf` | A1 | Mặt bằng định vị cột-vách, dầm sàn BTCT | `DCE_TITLEBLOCK_A1` |
| `Form_02_MultiView_A3_BTCT.dxf` | A3 | Bản vẽ triển khai nhiều khung nhìn (`KC.02`, `KC.13–15`...) | `DCE_TITLEBLOCK_A3` |
| `Form_03_KetCau_Thep_Steel.dxf` | A1 | Mặt bằng & liên kết Kết cấu Thép (`DCE STEEL`) | `DCE_TITLEBLOCK_A1` |
| `Form_04_ChiTiet_Coc_Dam_Cot.dxf` | A3 | Chi tiết cọc, đài móng, cột, dầm, thống kê thép `TK*` | `DCE_TITLEBLOCK_A3` |

## 2. Thứ tự ưu tiên tìm Form

Khi chạy cho một dự án, Agent tự động tìm theo 3 tầng:
1. `<Thư mục dự án>/CAD_Forms/` *(mẫu riêng từng công trình)*
2. `00_Template_&_Standards/CAD_Forms/` *(thư mục chuẩn công ty — chính là thư mục này)*
3. `.agents/_SHARED/data/CAD_Forms/` *(bộ gốc dự phòng bất biến của Agent)*

## 3. Bạn được sửa gì trong AutoCAD?

1. **Sửa Khung tên (`BEDIT` Block `DCE_TITLEBLOCK_A3` hoặc `DCE_TITLEBLOCK_A1`):**
   - Chèn logo công ty, đổi kiểu khung, thêm dòng chữ cố định, đổi Font `Dce_Text`, đổi vị trí/cỡ chữ các ô.
   - **Lưu ý giữ nguyên các Tag thuộc tính (`ATTDEF`) bắt buộc:** `TEN_CONG_TRINH`, `TEN_BAN_VE`, `KY_HIEU`, `TY_LE` (có thể thêm Tag riêng của công ty — Agent sẽ giữ nguyên không xóa).
2. **Sửa Màu Layer, Nét vẽ, DimStyle (`Dce_*MV`), TextStyle:**
   - Mở `LA` (Layer Manager) hoặc `D` (DimStyle) để chỉnh màu nét in, chiều cao chữ, mũi tên dim theo chuẩn riêng của bạn -> Save (`Ctrl+S`).
3. **Kéo giãn / Dời vị trí vùng vẽ (`DCE_ZONE_*`):**
   - Các khung chữ nhật trên layer `DCE_ZONE_VIEWPORT_TOP`, `DCE_ZONE_VIEWPORT_BOTTOM`, `DCE_ZONE_TABLE`, `DCE_ZONE_NOTE`, `DCE_ZONE_KEYPLAN` là layer không in (`No Plot`). Bạn dùng lệnh `Stretch` kéo to/nhỏ hoặc dời vị trí khung nhìn; Agent sẽ tự căn chỉnh bản vẽ lọt vào đúng khung mới.
4. **Lưu file:**
   - Lưu dưới định dạng **AutoCAD 2007 DXF (`AC1021`)** hoặc cao hơn để đảm bảo tương thích. Tránh xóa mất các khung `DCE_ZONE_*` hoặc đổi UCS khỏi `World`.

## 4. Kho Block DCE chuẩn tích hợp sẵn trong mọi Form

- Trục định vị: `Dce_KhTenTruc` (`TRUC`), `Dce_TenTruc`
- Cột & Tên cấu kiện: `DCE_COL_*` (hình học chuẩn từng tiết diện không méo hatch) + `TenCauKien` (`TENCAUKIEN`, `SOCAUKIEN`), `DCE_CL_REC1_`, `DCE_CL_Circle_`
- Cọc: `DCE_Pile_SQ_TYPE1/2/3_250_X`, `DCE_Pile_CIR_TYPE1_D300` (`PILE_ID`, `D`, `L`, `Q`)
- Cao trình / Sàn / Dầm / Thống kê thép: `Dce_CaoTrinh` (`CT`), `DCE_Slab tag` (`200`), `DCE_Drop mark` (`50`), `DCE_Plan header 1`, `DCE_Beam2`, `Dce_KhTenDam`, `TK1`..`TK44`
"""
    gp = target_dir / "README_HUONG_DAN_SUA_FORM_AUTOCAD.md"
    gp.write_text(guide, encoding="utf-8")
    return gp


def generate_all_forms(
    directories: Optional[List[Path]] = None,
    overwrite_user_existing: bool = True,
) -> Dict[str, Any]:
    dirs = directories or [SSOT_FORMS_DIR, USER_FORMS_DIR]
    report: Dict[str, Any] = {}
    for target_dir in dirs:
        target_dir.mkdir(parents=True, exist_ok=True)
        write_user_guide(target_dir)
        dir_res: Dict[str, Any] = {}
        for form_id in FORM_CATALOG:
            spec = FORM_CATALOG[form_id]
            dxf_target = target_dir / spec["filename"]
            if dxf_target.exists() and not overwrite_user_existing and target_dir == USER_FORMS_DIR:
                dir_res[form_id] = {"skipped_existing": str(dxf_target)}
                continue
            dxf_p, man_p, val = generate_single_form(form_id, target_dir)
            dir_res[form_id] = {
                "dxf": str(dxf_p),
                "manifest": str(man_p),
                "valid": val["valid"],
                "zones": list(val["zones_wcs"].keys()),
                "titleblock_tags_count": len(val["titleblock_tags"]),
            }
        report[str(target_dir)] = dir_res
    return report


if __name__ == "__main__":
    res = generate_all_forms()
    print(json.dumps(res, ensure_ascii=False, indent=2))
