# -*- coding: utf-8 -*-
"""
cad_layer_standard.py — Single Source of Truth (SSOT) cho Bộ Layer Chuẩn DCE Pro + DCE STEEL
=============================================================================================

Đồng bộ trên mọi thiết bị thông qua `.agents/_SHARED/data/dce_layers_standard.json`
(không phụ thuộc ổ đĩa cố định hay cài đặt cục bộ `C:\\Dce Pro`).

Hợp nhất từ 3 nguồn chuẩn:
1. Form 2.dxf / DCE_Master_Seed_Template.dxf (46 layers BTCT gốc DCE Pro)
2. DbimSteelAutocad.dll -> DbimSteelAutocad.DceLayerName + System/VN_LayerThepGc.txt (16 layers DCE STEEL)
3. Các layer mở rộng mặt bằng, khung tờ, thép & kiểm toán (16 layers Plan + 8 compat aliases)
"""

from __future__ import annotations

import json
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

if hasattr(sys.stdout, "reconfigure") and sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

SHARED_CONTEXT_DIR = Path(__file__).resolve().parent
SHARED_DIR = SHARED_CONTEXT_DIR.parent
AGENTS_DIR = SHARED_DIR.parent
DATA_DIR = SHARED_DIR / "data"

STANDARD_JSON_PATH = DATA_DIR / "dce_layers_standard.json"
DEFAULT_TEMPLATE_DXF_PATH = DATA_DIR / "DCE_Pro_And_Steel_Template.dxf"
SEED_TEMPLATE_PATH = (
    AGENTS_DIR / "skills" / "Technical_Illustrator" / "cad_integration" / "templates" / "DCE_Master_Seed_Template.dxf"
)

VALID_DXF_LINEWEIGHTS = {
    5, 9, 13, 15, 18, 20, 25, 30, 35, 40, 50, 53, 60, 70, 80, 90, 100
}

_V4_LTYPE_FALLBACK = {
    "Continuous": "CONTINUOUS",
    "CONTINUOUS": "CONTINUOUS",
    "HIDDEN_DBIM": "HIDDEN2",
    "BEAM HIDEN_DBIM": "HIDDEN2",
    "DASHDOT2_DBIM": "CENTER2",
    "CENTER2_DBIM": "CENTER2",
}


@lru_cache(maxsize=4)
def load_dce_layer_standard(json_path: Optional[str] = None) -> Dict[str, Any]:
    """Đọc toàn bộ chuẩn layer DCE Pro + DCE STEEL từ file JSON SSOT."""
    target = Path(json_path) if json_path else STANDARD_JSON_PATH
    if not target.is_file():
        raise FileNotFoundError(f"Không tìm thấy SSOT layer JSON tại: {target}")
    return json.loads(target.read_text(encoding="utf-8"))


def get_layer_specs(
    profile: str = "dce_native",
    groups: Optional[Sequence[str]] = None,
    include_compat: bool = True,
) -> Dict[str, Dict[str, Any]]:
    """Trả về từ điển cấu hình layer theo profile (`dce_native` hoặc `light_bg_plot`)."""
    data = load_dce_layer_standard()
    overrides = data.get("light_bg_plot_overrides", {}) if profile == "light_bg_plot" else {}
    group_filter = set(groups) if groups else None

    result: Dict[str, Dict[str, Any]] = {}
    for item in data.get("layers", []):
        grp = str(item.get("group", ""))
        if not include_compat and grp == "compat_aliases_8":
            continue
        if group_filter is not None and grp not in group_filter:
            continue

        name = str(item["name"])
        spec = {
            "name": name,
            "color": int(item.get("color", 7)),
            "linetype": str(item.get("linetype", "Continuous")),
            "lineweight": int(item.get("lineweight", 18)),
            "screening": int(item.get("screening", 100)),
            "group": grp,
            "source": str(item.get("source", "")),
            "note": str(item.get("note", "")),
        }
        if name in overrides:
            ov = overrides[name]
            spec["color"] = int(ov.get("color", spec["color"]))
            spec["linetype"] = str(ov.get("linetype", spec["linetype"]))
            spec["lineweight"] = int(ov.get("lineweight", spec["lineweight"]))
        result[name] = spec
    return result


def get_dce_pro_layers_dict(
    profile: str = "dce_native",
    include_steel: bool = True,
    include_compat: bool = False,
) -> Dict[str, Dict[str, Any]]:
    """Trả về dict tương thích 100% với `DcePlanEngine.DCE_PRO_LAYERS`."""
    groups = ["form2_btct_46", "dce_plan_extensions_17"]
    if include_steel:
        groups.append("dce_steel_16")
    if include_compat:
        groups.append("compat_aliases_8")
    specs = get_layer_specs(profile=profile, groups=groups, include_compat=include_compat)
    return {
        name: {
            "color": sp["color"],
            "linetype": sp["linetype"],
            "lineweight": sp["lineweight"],
            "screening": sp["screening"],
            "note": sp["note"],
        }
        for name, sp in specs.items()
    }


def get_dce_layer_matrix(include_steel: bool = True) -> List[Tuple[str, int, str, int, int]]:
    """Trả về danh sách tuple `(name, color, ltype, lw, screening)` tương thích `DCE_LAYER_MATRIX` v4.7."""
    # Giữ tương thích với bảng LTYPE tối giản của nhánh v4 (CONTINUOUS / HIDDEN2 / CENTER2)
    base_names = [
        "DCE_Cot", "DCE_Vach", "DCE_Boundary_Zone", "DCE_Hatch", "DCE_Truc",
        "DCE_Dim", "DCE_Setout", "DCE_Name", "DCE_NetThay", "DCE_CouplingBeam",
        "DCE_VoidX", "DCE_Thep_Chu", "DCE_Thep_Dai", "DCE_Schedule", "DCE_Frame",
        "DCE_BaoBeTong", "DCE_MainBeam", "DCE_Beam", "DCE_Leader", "DCE_Note",
        "Dce_text", "DCE_Block", "DCE_Symbol", "DCE_Core", "DCE_GapOpen",
        "DCE_Lanh_To", "DCE_RanhDat", "DCE_ChiGioi", "DCE_Road",
    ]
    steel_names = [
        "DCE_SubBeam", "DCE_Flange", "DCE_Web", "DCE_Plate", "DCE_Bracing",
        "DCE_Purlin", "DCE_Rod", "DCE_Weld", "DCE_Tole", "DCE_Pipe",
        "DCE_Tube", "DCE_L", "DCE_U", "DCE_TopBars", "DCE_ThepSanGC",
    ]
    specs = get_layer_specs(profile="dce_native", include_compat=False)
    ordered = base_names + (steel_names if include_steel else [])
    matrix: List[Tuple[str, int, str, int, int]] = []
    for name in ordered:
        sp = specs.get(name)
        if not sp:
            continue
        lt = _V4_LTYPE_FALLBACK.get(sp["linetype"], "CONTINUOUS")
        matrix.append((name, int(sp["color"]), lt, int(sp["lineweight"]), int(sp["screening"])))
    return matrix


# Danh sách tên Layer định hình chuẩn cho từng Profile (SSOT Profile Selectors)
BTCT_CORE_LAYER_NAMES: Tuple[str, ...] = (
    "DCE_Cot", "DCE_Vach", "DCE_BaoBeTong", "DCE_NetThay", "DCE_Truc",
    "DCE_Dim", "DCE_Setout", "DCE_Name", "DCE_Thep_Chu", "DCE_Thep_Dai",
    "DCE_Hatch", "DCE_VoidX", "DCE_Leader", "DCE_Schedule", "DCE_Frame",
)

STEEL_PEB_LAYER_NAMES: Tuple[str, ...] = (
    "DCE_Steel_Main", "DCE_Steel_Plate", "DCE_Steel_Sec", "DCE_Steel_Bolt",
    "DCE_Steel_Weld", "DCE_Steel_Hidden", "DCE_MainBeam", "DCE_SubBeam",
    "DCE_Bracing", "DCE_Purlin", "DCE_Truc", "DCE_Dim", "DCE_Name",
    "DCE_Leader", "DCE_Schedule", "DCE_Frame",
)
STEEL_CORE_LAYER_NAMES: Tuple[str, ...] = STEEL_PEB_LAYER_NAMES

BPTC_CORE_LAYER_NAMES: Tuple[str, ...] = (
    "DCE_BPTC_Equip", "DCE_BPTC_Tie", "DCE_BPTC_Anchor", "DCE_BPTC_SafeZone",
    "DCE_Cot", "DCE_Vach", "DCE_Truc", "DCE_Dim", "DCE_Name",
    "DCE_Leader", "DCE_Schedule", "DCE_Frame",
)


def get_btct_core_15() -> List[Tuple[str, int, str, int, int]]:
    """Trả về 15 layer cốt lõi cho bản vẽ Kết cấu Bê tông cốt thép (BTCT)."""
    return get_profile_layer_matrix("BTCT")


def get_dcesteel_core_16() -> List[Tuple[str, int, str, int, int]]:
    """Trả về 16 layer cốt lõi cho bản vẽ Kết cấu Thép & PEB."""
    return get_profile_layer_matrix("STEEL_PEB")


def get_bptc_core_12() -> List[Tuple[str, int, str, int, int]]:
    """Trả về 12 layer cốt lõi cho bản vẽ Biện pháp Thi công (BPTC)."""
    return get_profile_layer_matrix("BPTC")


def select_layer_profile(
    profile_name: str = "BTCT",
) -> List[Tuple[str, int, str, int, int]]:
    """Bộ điều phối chọn danh sách layer theo profile: 'BTCT', 'STEEL_PEB', 'BPTC'."""
    p = str(profile_name).upper().strip()
    if p in ("STEEL_PEB", "STEEL", "DCESTEEL_CORE", "DCE_STEEL"):
        return get_dcesteel_core_16()
    elif p in ("BPTC", "DCE_BPTC", "DCE_BPTC_CORE"):
        return get_bptc_core_12()
    else:
        return get_btct_core_15()


def get_profile_layer_matrix(
    profile_name: str = "DCE_BTCT_CORE",
    custom_names: Optional[Sequence[str]] = None,
) -> List[Tuple[str, int, str, int, int]]:
    """Trả về danh sách tuple `(name, color, ltype, lw, screening)` chuẩn hóa theo Profile."""
    p_norm = str(profile_name).upper().strip()
    if custom_names is not None:
        target_names = list(custom_names)
    elif p_norm in ("DCESTEEL_CORE", "STEEL_PEB", "STEEL", "DCE_STEEL"):
        target_names = list(STEEL_PEB_LAYER_NAMES)
    elif p_norm in ("BPTC", "DCE_BPTC", "DCE_BPTC_CORE"):
        target_names = list(BPTC_CORE_LAYER_NAMES)
    else:
        target_names = list(BTCT_CORE_LAYER_NAMES)

    specs = get_layer_specs(profile="dce_native", include_compat=True)
    matrix: List[Tuple[str, int, str, int, int]] = []
    for name in target_names:
        sp = specs.get(name)
        if not sp and name == "DCE_Bolt":
            sp = specs.get("DCE_Steel_Bolt")
        if not sp:
            continue
        lt = _V4_LTYPE_FALLBACK.get(sp["linetype"], "CONTINUOUS")
        matrix.append((name, int(sp["color"]), lt, int(sp["lineweight"]), int(sp["screening"])))
    return matrix


def get_standard_layer_whitelist() -> Set[str]:
    """Trả về tập tên layer viết thường dùng cho Bộ lọc 8 (`DCE_STANDARD_LAYERS`)."""
    data = load_dce_layer_standard()
    names = {str(item["name"]).lower() for item in data.get("layers", [])}
    names.update({
        "0", "defpoints", "dce_text", "dce_bolt",
        "dce_steel_main", "dce_steel_plate", "dce_steel_sec", "dce_steel_bolt",
        "dce_steel_weld", "dce_steel_hidden",
        "dce_bptc_equip", "dce_bptc_tie", "dce_bptc_anchor", "dce_bptc_safezone",
    })
    return names


def ensure_doc_layers(
    doc: Any,
    profile: str = "dce_native",
    layer_names: Optional[Sequence[str]] = None,
    override_existing: bool = False,
    positive_lineweights: bool = True,
    include_compat: bool = False,
) -> int:
    """Nạp đầy đủ các layer chuẩn vào `ezdxf` Drawing; trả về số layer đã thêm/cập nhật."""
    specs = get_layer_specs(profile=profile, include_compat=include_compat)
    if layer_names is not None:
        wanted = set(layer_names)
        specs = {k: v for k, v in specs.items() if k in wanted}

    available_lts = {lt.dxf.name for lt in doc.linetypes}
    changed = 0

    for lname, sp in specs.items():
        if lname.lower().startswith("xref."):
            continue
        lt = sp["linetype"]
        if lt not in available_lts:
            lt = "Continuous" if "Continuous" in available_lts else "CONTINUOUS"
        lw = int(sp["lineweight"]) if positive_lineweights else int(sp.get("lineweight", -3))

        if lname in doc.layers:
            if override_existing:
                ly = doc.layers.get(lname)
                ly.color = int(sp["color"])
                ly.dxf.linetype = lt
                if positive_lineweights and lname.lower() != "defpoints":
                    ly.dxf.lineweight = lw
                changed += 1
        else:
            doc.layers.add(lname, color=int(sp["color"]), linetype=lt, lineweight=lw)
            changed += 1

    if positive_lineweights:
        for ly in doc.layers:
            try:
                if ly.dxf.name.lower() in {"0", "defpoints"}:
                    continue
                if int(getattr(ly.dxf, "lineweight", -3)) <= 0:
                    ly.dxf.lineweight = 18
            except Exception:
                pass
    return changed


def export_layers_template_dxf(
    output_dxf_path: Optional[Path] = None,
    seed_dxf_path: Optional[Path] = None,
    profile: str = "dce_native",
) -> Path:
    """Xuất file DXF mẫu (ModelSpace trống, AC1021) chứa đủ Form 2 + DCE STEEL + Plan layers."""
    import ezdxf

    seed = Path(seed_dxf_path) if seed_dxf_path else SEED_TEMPLATE_PATH
    out = Path(output_dxf_path) if output_dxf_path else DEFAULT_TEMPLATE_DXF_PATH

    doc = ezdxf.readfile(str(seed)) if seed.is_file() else ezdxf.new("R2007", setup=True)
    msp = doc.modelspace()
    for ent in list(msp):
        msp.delete_entity(ent)

    doc.header["$INSUNITS"] = 4
    doc.header["$MEASUREMENT"] = 1
    doc.header["$LTSCALE"] = 100.0
    ensure_doc_layers(doc, profile=profile, override_existing=False, positive_lineweights=True, include_compat=False)

    out.parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(str(out))
    return out


def export_layer_table_markdown(output_md_path: Optional[Path] = None) -> Path:
    """Xuất bảng tra cứu Markdown chuẩn DCE Pro + DCE STEEL để sử dụng nhanh trên mọi thiết bị."""
    data = load_dce_layer_standard()
    out = Path(output_md_path) if output_md_path else (DATA_DIR / "DCE_LAYER_REFERENCE.md")
    overrides = data.get("light_bg_plot_overrides", {})

    lines = [
        "# BỘ LAYER CHUẨN HỢP NHẤT DCE PRO (FORM 2) + DCE STEEL",
        "",
        f"- **Schema:** `{data.get('schema_version')}`",
        f"- **Nguồn gốc:** `{data['provenance']['base_template']}` + `{data['provenance']['dce_steel_source']}` + `{data['provenance']['system_txt_source']}`",
        f"- **Tổng số layer:** `{data['counts']['total_layers']}` (`Form 2`: {data['counts']['form2_btct_46']}, `DCE STEEL`: {data['counts']['dce_steel_16']}, `Mặt bằng & Khung`: {data['counts']['dce_plan_extensions_17']}, `Compat`: {data['counts']['compat_aliases_8']})",
        f"- **File đồng bộ đa thiết bị:** `dce_layers_standard.json`, `DCE_Pro_And_Steel_Template.dxf`, `cad_layer_standard.py`",
        "",
        "| Nhóm | Tên Layer | ACI (Gốc) | ACI (In Nền Sáng) | Linetype | Lineweight (1/100mm) | Ghi chú |",
        "|---|---|---:|---:|---|---:|---|",
    ]
    for item in data.get("layers", []):
        name = item["name"]
        if name.lower().startswith("xref."):
            continue
        ov = overrides.get(name, {})
        lt_color = ov.get("color", item["color"])
        lines.append(
            f"| `{item['group']}` | `{name}` | {item['color']} | {lt_color} | `{item['linetype']}` | {item['lineweight']} | {item['note']} |"
        )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


if __name__ == "__main__":
    tmpl_out = export_layers_template_dxf()
    md_out = export_layer_table_markdown()
    std = load_dce_layer_standard()
    print(f"[OK] Template DXF: {tmpl_out} ({tmpl_out.stat().st_size} B)")
    print(f"[OK] Reference MD: {md_out} ({md_out.stat().st_size} B)")
    print(f"[OK] Total layers in SSOT: {std['counts']}")
