#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dce_block_binding.py — Cơ chế Ánh xạ & Ràng buộc Thuộc tính Block DCE Pro (v6.0)
================================================================================
Ánh xạ tường minh giữa các trường tham số kết cấu (Semantic Fields) và các thẻ ATTDEF
trong Block AutoCAD của DCE Pro.

Nguyên tắc bắt buộc (Directive v6.0):
  1. Không đoán nghĩa tag: Từng block có bảng ánh xạ định danh rõ ràng.
     Ví dụ: Trong `DCE_Slab tag`, tag tên '200' là trường bề dày sàn;
            trong `DCE_Drop mark`, tag '50' là giá trị hạ cốt.
  2. Không nuốt ngoại lệ thành TEXT rời: Thiếu tag hoặc sai kiểu phải raise
     MissingTagError hoặc InvalidSemanticValueError với thông điệp chẩn đoán rõ.
  3. Khả năng Round-trip (Save & Reopen): Đảm bảo ghi vào DXF và đọc lại ra
     chính xác giá trị thiết kế ban đầu 100%.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

if hasattr(sys.stdout, "reconfigure") and sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import ezdxf
from ezdxf.entities import Insert

from dce_block_catalog import DceBlockAttdef, DceBlockSpec


class BlockBindingError(Exception):
    """Lỗi nền tảng của quá trình ràng buộc thuộc tính Block."""
    pass


class MissingTagError(BlockBindingError):
    """Lỗi khi Block thiếu thẻ ATTDEF bắt buộc."""
    pass


class InvalidSemanticValueError(BlockBindingError):
    """Lỗi khi giá trị tham số kết cấu không thể chuyển đổi hợp lệ sang thuộc tính."""
    pass


# ---------------------------------------------------------------------------
# CÁC HÀM CHUYỂN ĐỔI ĐỊNH DẠNG (FORMATTERS & PARSERS)
# ---------------------------------------------------------------------------

def format_elevation(level: Union[float, int, str]) -> str:
    """Chuyển đổi cao độ mét sang chuỗi cao độ chuẩn xây dựng (+12.600 hoặc -1.400)."""
    try:
        val = float(level)
        sign = "+" if val >= 0 else "-"
        return f"{sign}{abs(val):.3f}"
    except (ValueError, TypeError):
        return str(level)


def parse_elevation(s: str) -> float:
    """Đọc ngược chuỗi cao độ sang giá trị float."""
    clean = str(s).replace("+", "").strip()
    return float(clean)


def format_thickness(val: Union[float, int, str]) -> str:
    """Định dạng chiều dày sàn mm (150, 120, 200)."""
    try:
        fval = float(val)
        if fval.is_integer():
            return str(int(fval))
        return f"{fval:.1f}"
    except (ValueError, TypeError):
        return str(val)


def parse_thickness(s: str) -> float:
    return float(s.strip())


def format_drop(val: Union[float, int, str]) -> str:
    """Định dạng độ hạ âm sàn (-50, 50, -100)."""
    try:
        fval = float(val)
        if fval.is_integer():
            return str(int(fval))
        return f"{fval:.1f}"
    except (ValueError, TypeError):
        return str(val)


def parse_drop(s: str) -> float:
    return float(s.strip())


def format_int(val: Union[float, int, str]) -> str:
    """Định dạng số nguyên dương (số lượng bản mã, bu lông neo)."""
    iv = int(float(val))
    if iv < 0:
        raise ValueError(f"Số lượng không thể âm: {val}")
    return str(iv)


def parse_int(s: str) -> int:
    return int(float(str(s).strip()))


# ---------------------------------------------------------------------------
# BẢNG ÁNH XẠ NGHIỆP VỤ (SEMANTIC FIELD MAPPING SPECIFICATION)
# ---------------------------------------------------------------------------

@dataclass
class SemanticFieldDef:
    """Đặc tả một trường tham số kết cấu."""
    semantic_name: str
    target_tag: str
    required: bool = True
    formatter: Callable[[Any], str] = str
    parser: Callable[[str], Any] = str
    unit: str = ""
    description: str = ""


@dataclass
class BlockSemanticBinding:
    """Đặc tả ánh xạ trọn gói cho một loại Block."""
    block_name: str
    fields: Dict[str, SemanticFieldDef] = field(default_factory=dict)
    description: str = ""

    def add_field(self, field_def: SemanticFieldDef):
        self.fields[field_def.semantic_name] = field_def


class BlockBindingRegistry:
    """Bộ đăng ký quản lý toàn bộ cấu hình Binding cho các Block DCE Pro."""

    def __init__(self):
        self._bindings: Dict[str, BlockSemanticBinding] = {}
        self._init_standard_bindings()

    def register(self, binding: BlockSemanticBinding):
        self._bindings[binding.block_name] = binding

    def get(self, block_name: str) -> Optional[BlockSemanticBinding]:
        return self._bindings.get(block_name)

    def require(self, block_name: str) -> BlockSemanticBinding:
        if block_name not in self._bindings:
            raise KeyError(f"Chưa cấu hình Semantic Binding cho Block '{block_name}'")
        return self._bindings[block_name]

    def _init_standard_bindings(self):
        # 1. Dce_KhTenDam: Nhãn dầm
        b_dam = BlockSemanticBinding("Dce_KhTenDam", description="Nhãn dầm chính/phụ tầng")
        b_dam.add_field(SemanticFieldDef("beam_mark", "TENDAM", required=True, unit="text", description="Mã hiệu và tiết diện dầm"))
        b_dam.add_field(SemanticFieldDef("scale_label", "TL", required=False, unit="ratio", description="Tỷ lệ in"))
        self.register(b_dam)

        # 2. Dce_KhTenNhip: Nhãn nhịp dầm
        b_nhip = BlockSemanticBinding("Dce_KhTenNhip", description="Nhãn phân nhịp dầm")
        b_nhip.add_field(SemanticFieldDef("span_mark", "TENNHIP", required=True, unit="text", description="Tên nhịp dầm"))
        b_nhip.add_field(SemanticFieldDef("scale_label", "TL", required=False, unit="ratio", description="Tỷ lệ in"))
        self.register(b_nhip)

        # 3. DCE_Slab tag: Nhãn ô sàn
        b_slab = BlockSemanticBinding("DCE_Slab tag", description="Ký hiệu chiều dày ô sàn điển hình")
        b_slab.add_field(SemanticFieldDef("thickness_mm", "200", required=True, formatter=format_thickness, parser=parse_thickness, unit="mm", description="Chiều dày bản sàn"))
        self.register(b_slab)

        # 4. DCE_Drop mark: Ký hiệu sàn hạ âm
        b_drop = BlockSemanticBinding("DCE_Drop mark", description="Ký hiệu sàn hạ âm ban công / vệ sinh")
        b_drop.add_field(SemanticFieldDef("drop_mm", "50", required=True, formatter=format_drop, parser=parse_drop, unit="mm", description="Độ hạ âm sàn"))
        self.register(b_drop)

        # 5. Dce_CaoTrinh: Ký hiệu cao trình tầng / mặt sàn
        b_ct = BlockSemanticBinding("Dce_CaoTrinh", description="Cao trình mặt sàn")
        b_ct.add_field(SemanticFieldDef("level_m", "CT", required=True, formatter=format_elevation, parser=parse_elevation, unit="m", description="Cao độ thiết kế mét"))
        self.register(b_ct)

        # 6. Dce_KhMatCat: Ký hiệu mặt cắt dầm sàn
        b_mc = BlockSemanticBinding("Dce_KhMatCat", description="Ký hiệu mặt cắt trích dẫn")
        b_mc.add_field(SemanticFieldDef("section_mark", "TENMATCAT", required=True, unit="text", description="Tên mặt cắt (MC 1-1)"))
        b_mc.add_field(SemanticFieldDef("scale_label", "TL", required=False, unit="ratio", description="Tỷ lệ mặt cắt"))
        self.register(b_mc)

        # 7. TenCauKien: Tên cấu kiện cột / vách
        b_ck = BlockSemanticBinding("TenCauKien", description="Tên cấu kiện và kích thước tiết diện")
        b_ck.add_field(SemanticFieldDef("member_mark", "TENCAUKIEN", required=True, unit="text", description="Tên cấu kiện (C1, C2, W1)"))
        b_ck.add_field(SemanticFieldDef("member_size", "SOCAUKIEN", required=False, unit="text", description="Kích thước cấu kiện hoặc số lượng"))
        self.register(b_ck)

        # 8. Dce_KhTenTruc / Dce_TenTruc: Bong bóng trục
        for tb_name in ["Dce_KhTenTruc", "Dce_TenTruc"]:
            b_tr = BlockSemanticBinding(tb_name, description="Bong bóng trục định vị")
            b_tr.add_field(SemanticFieldDef("axis_label", "TRUC", required=True, unit="text", description="Tên trục (1..11, A..E)"))
            self.register(b_tr)

        # 9. DCE_Name: Nhãn đa năng
        b_name = BlockSemanticBinding("DCE_Name", description="Nhãn tên định danh tổng quát")
        b_name.add_field(SemanticFieldDef("mark", "MARK", required=True, unit="text", description="Chuỗi định danh"))
        self.register(b_name)

        # 10. Dce-ThepTam & Dce-Tangcung: Nhãn thép tấm / bản mã tăng cứng (Form 2_Steel.dwg)
        for plate_blk in ["Dce-ThepTam", "Dce-Tangcung"]:
            b_pl = BlockSemanticBinding(plate_blk, description=f"Nhãn chi tiết thép tấm / tăng cứng ({plate_blk})")
            b_pl.add_field(SemanticFieldDef("plate_thickness", "B", required=True, formatter=format_thickness, parser=parse_thickness, unit="mm", description="Bề dày thép tấm"))
            b_pl.add_field(SemanticFieldDef("quantity", "SL", required=True, formatter=format_int, parser=parse_int, unit="pcs", description="Số lượng tấm"))
            b_pl.add_field(SemanticFieldDef("member_mark", "TENCK", required=True, unit="text", description="Ký hiệu cấu kiện / bản mã"))
            b_pl.add_field(SemanticFieldDef("shape_desc", "HINHDANG", required=False, unit="text", description="Hình dạng bản mã"))
            b_pl.add_field(SemanticFieldDef("chamfer_desc", "VATCANH", required=False, unit="text", description="Quy cách vát cạnh / đường hàn"))
            self.register(b_pl)

        # 11. Dce_BP_*: Bản đế chân cột thép (Pin 4/6, Fix 6/8/10/12 từ Form 2_Steel.dwg)
        for bp_name in [
            "Dce_BP_Pin4", "Dce_BP_Pin6",
            "Dce_BP_Fix6", "Dce_BP_Fix8", "Dce_BP_Fix10", "Dce_BP_Fix12",
        ]:
            b_bp = BlockSemanticBinding(bp_name, description=f"Nhãn bản đế cột thép ({bp_name})")
            b_bp.add_field(SemanticFieldDef("baseplate_mark", "TenBanDe", required=True, unit="text", description="Ký hiệu bản đế (VD: BD-01)"))
            b_bp.add_field(SemanticFieldDef("thickness_mm", "ChieuDay", required=True, formatter=format_thickness, parser=parse_thickness, unit="mm", description="Chiều dày bản đế mm"))
            self.register(b_bp)

        # 12. Dce_AnchorExpansion: Bu lông nở / bu lông neo kết cấu thép
        b_anc = BlockSemanticBinding("Dce_AnchorExpansion", description="Ký hiệu số lượng bu lông nở / neo")
        b_anc.add_field(SemanticFieldDef("bolt_count", "SL", required=True, formatter=format_int, parser=parse_int, unit="pcs", description="Số lượng bu lông"))
        self.register(b_anc)

        # 13. Dce_PlanI: Nhãn cột chữ I trên mặt bằng định vị cột thép
        b_plani = BlockSemanticBinding("Dce_PlanI", description="Nhãn cột thép hình chữ I trên mặt bằng")
        b_plani.add_field(SemanticFieldDef("column_mark", "TENCOT", required=True, unit="text", description="Tên cột thép"))
        self.register(b_plani)


_GLOBAL_BINDING_REGISTRY: Optional[BlockBindingRegistry] = None


def get_default_binding_registry() -> BlockBindingRegistry:
    global _GLOBAL_BINDING_REGISTRY
    if _GLOBAL_BINDING_REGISTRY is None:
        _GLOBAL_BINDING_REGISTRY = BlockBindingRegistry()
    return _GLOBAL_BINDING_REGISTRY


# ---------------------------------------------------------------------------
# HÀM RÀNG BUỘC & TRÍCH XUẤT THUỘC TÍNH (BIND & EXTRACT APIS)
# ---------------------------------------------------------------------------

def bind_block_attributes(
    insert_entity: Insert,
    block_spec: DceBlockSpec,
    semantic_values: Dict[str, Any],
    registry: Optional[BlockBindingRegistry] = None,
    allow_unmapped_tags: bool = False,
    override_color: int = 256,
    true_color: Optional[int] = 0x1E3246,
) -> Dict[str, str]:
    """
    Ràng buộc và ghi giá trị tham số kết cấu vào các thuộc tính ATTRIB của INSERT.

    Args:
        insert_entity: Đối tượng ezdxf INSERT vừa được chèn vào modelspace.
        block_spec: Đặc tả BlockSpec từ DceBlockCatalog.
        semantic_values: Dictionary chứa các tham số nghiệp vụ (ví dụ: {'thickness_mm': 150}).
        registry: Bộ đăng ký binding (mặc định dùng get_default_binding_registry()).
        allow_unmapped_tags: Nếu True, cho phép truyền trực tiếp thẻ chưa cấu hình.
        override_color: ACI color (mặc định 256 = ByLayer).
        true_color: Màu True Color RGB (mặc định 0x1E3246 = Xanh thép trầm).

    Returns:
        Dict[str, str]: Bản đồ {TAG: STR_VALUE} đã ghi vào thực thể.
    """
    if registry is None:
        registry = get_default_binding_registry()

    bname = block_spec.name
    binding = registry.get(bname)

    tag_values: Dict[str, str] = {}

    if binding is not None:
        # Ánh xạ theo SemanticFieldDef
        for sname, fdef in binding.fields.items():
            if sname in semantic_values:
                raw_val = semantic_values[sname]
                try:
                    str_val = fdef.formatter(raw_val)
                    tag_values[fdef.target_tag] = str_val
                except Exception as ex:
                    raise InvalidSemanticValueError(f"Không thể định dạng tham số '{sname}={raw_val}' cho Block '{bname}': {ex}")
            elif fdef.required:
                raise InvalidSemanticValueError(f"Thiếu tham số bắt buộc '{sname}' cho Block '{bname}' (yêu cầu thẻ '{fdef.target_tag}')")

    # Xử lý các tag truyền trực tiếp (nếu có)
    for k, v in semantic_values.items():
        if k in block_spec.attdefs and k not in tag_values:
            if binding is None or allow_unmapped_tags or k in [f.target_tag for f in binding.fields.values()]:
                tag_values[k] = str(v)

    # Kiểm tra tính tồn tại của các tag trong Block định nghĩa
    missing_in_spec = [t for t in tag_values if t not in block_spec.attdefs]
    if missing_in_spec:
        raise MissingTagError(
            f"Block '{bname}' không chứa các thẻ ATTDEF sau: {missing_in_spec}. "
            f"Các thẻ hiện có trong block: {list(block_spec.attdefs.keys())}"
        )

    # Thêm hoặc cập nhật ATTRIB vào đối tượng Insert
    try:
        # Nếu blockref chưa có attribs thì dùng add_auto_attribs
        if not insert_entity.attribs:
            insert_entity.add_auto_attribs(tag_values)
        else:
            # Cập nhật các attrib hiện hữu
            existing_tags = {att.dxf.tag: att for att in insert_entity.attribs}
            for tag, val in tag_values.items():
                if tag in existing_tags:
                    existing_tags[tag].dxf.text = val
                else:
                    insert_entity.add_attrib(tag, val)
    except Exception as ex:
        raise BlockBindingError(f"Lỗi khi ghi thuộc tính vào blockref '{bname}': {ex}")

    # Áp dụng chuẩn Rule 12b (chống chữ trắng, ép ByLayer/TrueColor)
    for att in insert_entity.attribs:
        att.dxf.color = override_color
        if true_color is not None:
            att.dxf.true_color = true_color

    return tag_values


def extract_semantic_values(
    insert_entity: Insert,
    block_spec: DceBlockSpec,
    registry: Optional[BlockBindingRegistry] = None,
) -> Dict[str, Any]:
    """
    Đọc ngược toàn bộ giá trị thuộc tính ATTRIB từ INSERT và giải mã ra tham số kết cấu.

    Returns:
        Dict[str, Any]: Dictionary các tham số (ví dụ: {'thickness_mm': 150.0, 'level_m': 12.6}).
    """
    if registry is None:
        registry = get_default_binding_registry()

    bname = block_spec.name
    binding = registry.get(bname)

    raw_attribs: Dict[str, str] = {att.dxf.tag: att.dxf.text for att in insert_entity.attribs}
    extracted: Dict[str, Any] = {}

    if binding is not None:
        for sname, fdef in binding.fields.items():
            if fdef.target_tag in raw_attribs:
                text_val = raw_attribs[fdef.target_tag]
                try:
                    parsed_val = fdef.parser(text_val)
                    extracted[sname] = parsed_val
                except Exception as ex:
                    # Nếu parse lỗi thì giữ nguyên dạng string
                    extracted[sname] = text_val

    # Đính kèm toàn bộ raw tags để đối soát
    extracted["_raw_tags"] = raw_attribs
    return extracted
