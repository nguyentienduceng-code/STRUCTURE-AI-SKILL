#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dce_block_catalog.py — Catalog Quản lý và Định danh Block Thuộc tính DCE Pro (v6.0)
===================================================================================
Trích xuất, lập danh mục và định danh chính xác toàn bộ Block Thuộc tính (Attribute Blocks)
từ các tệp DXF sản phẩm chuẩn và thư viện DCE Pro / DCE Steel.

Nguyên tắc cốt lõi:
  1. Nguồn sự thật có hash bất biến: Mỗi BlockSpec đều ghi nhận source_file và SHA-256.
  2. Bóc tách chi tiết ATTDEF: Ghi rõ tag, prompt, default, style, height, alignment.
  3. Basepoint & Geometry Bounding Box: Đo lường chính xác tọa độ gốc chèn và hộp bao.
  4. Phân định mức độ tin cậy (Confidence Level):
     - VERIFIED_DXF: Đọc trực tiếp từ DXF sản phẩm hoặc template DXF.
     - PARTIAL_DWG: Dữ liệu bóc tách một phần từ DWG ngoài (cần thận trọng).
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import ezdxf

BLOCK_CATALOG_VERSION = "dce_block_catalog_v6.0"


def get_block_catalog_version() -> str:
    """Return canonical Block Catalog SSOT version identifier."""
    return BLOCK_CATALOG_VERSION


@dataclass
class DceBlockAttdef:
    """Đặc tả một trường thuộc tính ATTDEF trong block."""
    tag: str
    prompt: str = ""
    default_value: str = ""
    style: str = "Standard"
    height: float = 2.5
    layer: str = "0"
    color: int = 256  # ByLayer
    halign: int = 0
    valign: int = 0
    insert: Tuple[float, float] = (0.0, 0.0)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> DceBlockAttdef:
        d = dict(data)
        if "insert" in d and isinstance(d["insert"], list):
            d["insert"] = tuple(d["insert"])
        return cls(**d)


@dataclass
class DceBlockSpec:
    """Đặc tả hoàn chỉnh của một Block trong DCE Pro."""
    name: str
    description: str = ""
    category: str = "STRUCTURAL_ANNOTATION"  # ANNOTATION, MEMBER_TAG, SCHEDULE_ROW, STEEL, FRAME
    basepoint: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    bbox: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)  # xmin, ymin, xmax, ymax
    attdefs: Dict[str, DceBlockAttdef] = field(default_factory=dict)
    entities_count: int = 0
    entity_types: Dict[str, int] = field(default_factory=dict)
    layers_dep: List[str] = field(default_factory=list)
    styles_dep: List[str] = field(default_factory=list)
    source_file: str = ""
    source_sha256: str = ""
    confidence: str = "VERIFIED_DXF"  # VERIFIED_DXF, PARTIAL_DWG, SYNTHETIC
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        res = asdict(self)
        res["attdefs"] = {k: v.to_dict() for k, v in self.attdefs.items()}
        return res

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> DceBlockSpec:
        d = dict(data)
        attdefs = {}
        for k, v in d.get("attdefs", {}).items():
            attdefs[k] = DceBlockAttdef.from_dict(v)
        d["attdefs"] = attdefs
        if "basepoint" in d and isinstance(d["basepoint"], list):
            d["basepoint"] = tuple(d["basepoint"])
        if "bbox" in d and isinstance(d["bbox"], list):
            d["bbox"] = tuple(d["bbox"])
        return cls(**d)


class DceBlockCatalog:
    """Kho lưu trữ và quản lý Block DCE Pro chuẩn."""

    def __init__(self):
        self._blocks: Dict[str, DceBlockSpec] = {}
        self._source_files: Dict[str, str] = {}  # file_path -> sha256

    def __len__(self) -> int:
        return len(self._blocks)

    def __contains__(self, name: str) -> bool:
        return name in self._blocks

    def list_blocks(self) -> List[str]:
        return sorted(list(self._blocks.keys()))

    def get_block(self, name: str) -> Optional[DceBlockSpec]:
        return self._blocks.get(name)

    def require_block(self, name: str) -> DceBlockSpec:
        if name not in self._blocks:
            raise KeyError(f"Block '{name}' không tồn tại trong DceBlockCatalog. Danh sách hiện có: {self.list_blocks()[:5]}...")
        return self._blocks[name]

    def register_block(self, spec: DceBlockSpec, allow_override: bool = False):
        if spec.name in self._blocks and not allow_override:
            existing = self._blocks[spec.name]
            # Nếu hash và số lượng attdefs giống nhau thì bỏ qua, nếu khác thì báo xung đột
            if existing.source_sha256 != spec.source_sha256 and existing.attdefs.keys() != spec.attdefs.keys():
                raise ValueError(
                    f"Xung đột định nghĩa Block '{spec.name}': "
                    f"Đã có từ {existing.source_file} (attdefs: {list(existing.attdefs.keys())}), "
                    f"định nghĩa mới từ {spec.source_file} (attdefs: {list(spec.attdefs.keys())})"
                )
        self._blocks[spec.name] = spec

    def scan_dxf(self, dxf_path: Union[str, Path], category_hint: str = "STRUCTURAL_ANNOTATION") -> int:
        """Quét tệp DXF và đăng ký toàn bộ Block định nghĩa vào catalog."""
        p = Path(dxf_path)
        if not p.is_file():
            raise FileNotFoundError(f"Không tìm thấy tệp DXF để quét: {p}")

        raw_bytes = p.read_bytes()
        digest = hashlib.sha256(raw_bytes).hexdigest()
        self._source_files[str(p)] = digest

        doc = ezdxf.readfile(p)
        count = 0

        for block in doc.blocks:
            bname = block.name
            if bname.startswith("*"):
                # Bỏ qua anonymous block như *Model_Space, *Paper_Space
                continue

            # Tính toán ATTDEF
            attdefs: Dict[str, DceBlockAttdef] = {}
            ent_types: Dict[str, int] = {}
            layers_dep: Set[str] = set()
            styles_dep: Set[str] = set()

            xmin, ymin = float("inf"), float("inf")
            xmax, ymax = float("-inf"), float("-inf")

            for ent in block:
                t = ent.dxftype()
                ent_types[t] = ent_types.get(t, 0) + 1
                if hasattr(ent.dxf, "layer") and ent.dxf.layer:
                    layers_dep.add(ent.dxf.layer)
                if hasattr(ent.dxf, "style") and ent.dxf.style:
                    styles_dep.add(ent.dxf.style)

                if t == "ATTDEF":
                    tag = ent.dxf.tag
                    attdefs[tag] = DceBlockAttdef(
                        tag=tag,
                        prompt=getattr(ent.dxf, "prompt", ""),
                        default_value=getattr(ent.dxf, "text", ""),
                        style=getattr(ent.dxf, "style", "Standard"),
                        height=float(getattr(ent.dxf, "height", 2.5)),
                        layer=getattr(ent.dxf, "layer", "0"),
                        color=int(getattr(ent.dxf, "color", 256)),
                        halign=int(getattr(ent.dxf, "halign", 0)),
                        valign=int(getattr(ent.dxf, "valign", 0)),
                        insert=(float(ent.dxf.insert.x), float(ent.dxf.insert.y)),
                    )

                # Ước lượng bbox cơ bản từ tọa độ insert hoặc vertices nếu có
                if hasattr(ent.dxf, "insert"):
                    ix, iy = float(ent.dxf.insert.x), float(ent.dxf.insert.y)
                    xmin, xmax = min(xmin, ix), max(xmax, ix)
                    ymin, ymax = min(ymin, iy), max(ymax, iy)
                elif hasattr(ent.dxf, "start"):
                    sx, sy = float(ent.dxf.start.x), float(ent.dxf.start.y)
                    ex, ey = float(ent.dxf.end.x), float(ent.dxf.end.y)
                    xmin, xmax = min(xmin, sx, ex), max(xmax, sx, ex)
                    ymin, ymax = min(ymin, sy, ey), max(ymax, sy, ey)

            if xmin == float("inf"):
                xmin, ymin, xmax, ymax = 0.0, 0.0, 0.0, 0.0

            base = (float(block.base_point.x), float(block.base_point.y), float(block.base_point.z))

            # Xác định category
            cat = category_hint
            if bname.startswith("TK"):
                cat = "REBAR_SCHEDULE_ROW"
            elif "Truc" in bname or "TRUC" in bname:
                cat = "AXIS_BUBBLE"
            elif "Dam" in bname or "DAM" in bname:
                cat = "BEAM_TAG"
            elif "Slab" in bname or "San" in bname:
                cat = "SLAB_TAG"
            elif "CauKien" in bname or "Cot" in bname or "Vach" in bname:
                cat = "MEMBER_TAG"
            elif "MatCat" in bname or "MC" in bname:
                cat = "SECTION_MARK"
            elif "CaoTrinh" in bname:
                cat = "ELEVATION_TAG"

            spec = DceBlockSpec(
                name=bname,
                description=f"Block {bname} quét từ {p.name}",
                category=cat,
                basepoint=base,
                bbox=(xmin, ymin, xmax, ymax),
                attdefs=attdefs,
                entities_count=len(block),
                entity_types=ent_types,
                layers_dep=sorted(list(layers_dep)),
                styles_dep=sorted(list(styles_dep)),
                source_file=str(p),
                source_sha256=digest,
                confidence="VERIFIED_DXF",
            )
            self.register_block(spec, allow_override=True)
            count += 1

        return count

    def load_steel_dwg_catalog(
        self,
        catalog_json_path: Optional[Union[str, Path]] = None,
        source_key: str = "Form 2_Steel.dwg",
    ) -> int:
        """Nap danh muc Block ket cau thep tu ket qua quet DWG (Form 2_Steel.dwg).

        Giu nguyen muc do tin cay PARTIAL_DWG_WASM_READ_76 do tep DWG chua doc full entity geometry.
        Khong ghi de cac block da co VERIFIED_DXF.
        """
        if catalog_json_path is None:
            catalog_json_path = Path(
                "g:/My Drive/Google AI Studio/.agents/memory/audits/dce_round2_20261114/template_catalog.json"
            )
        else:
            catalog_json_path = Path(catalog_json_path)

        if not catalog_json_path.is_file():
            return 0

        raw_bytes = catalog_json_path.read_bytes()
        digest = hashlib.sha256(raw_bytes).hexdigest()
        data = json.loads(raw_bytes.decode("utf-8"))
        rec = data.get(source_key)
        if not isinstance(rec, dict):
            return 0

        reader_warning = rec.get("reader_warning", 76)
        dyn_keys = rec.get("dynamic_dictionary_keys", [])
        src_ref = f"{catalog_json_path}::{source_key}"
        self._source_files[src_ref] = digest

        steel_exact = {
            "Dce_BeamI1", "Dce_IWeb", "Dce_IFlange", "Dce_IFlangeDHR", "Dce_IFlangeRed",
            "DCE_SectHop", "DCE_SectOng", "DCE_Hop_Ngang", "DCE_Ong_Ngang",
            "Dce-ThepTam", "Dce-Tangcung", "Dce_PlanI",
            "Dce_Bolt", "Dce_MBolt", "Dce.Nut",
            "Dce_Anchor", "Dce_AnchorL", "Dce_AnchorL2", "Dce_AnchorJ", "Dce_AnchorExpansion",
            "DCE_TH200", "DCE_TH300",
        }
        steel_prefixes = ("Dce_BP_", "Dce.nut")

        count = 0
        for b in rec.get("blocks", []):
            bname = b.get("name", "")
            if not bname or bname.startswith("*"):
                continue
            if bname not in steel_exact and not bname.startswith(steel_prefixes):
                continue

            existing = self._blocks.get(bname)
            if existing is not None and existing.confidence == "VERIFIED_DXF":
                continue

            ent_types = dict(b.get("types", {}))
            tags = list(b.get("attribute_tags", []))
            attdefs: Dict[str, DceBlockAttdef] = {}
            for idx, tag in enumerate(tags):
                attdefs[tag] = DceBlockAttdef(
                    tag=tag,
                    prompt=tag,
                    default_value=tag,
                    style="Dce_Text",
                    height=2.5,
                    layer="DCE_Name",
                    color=256,
                    insert=(0.0, float(-idx * 3.5)),
                )

            if bname.startswith("Dce_BP_"):
                cat = "STEEL_BASEPLATE"
            elif bname in ("Dce-ThepTam", "Dce-Tangcung"):
                cat = "STEEL_PLATE_TAG"
            elif "Bolt" in bname or "Nut" in bname or "nut" in bname or "Anchor" in bname:
                cat = "STEEL_FASTENER"
            elif bname.startswith("DCE_TH"):
                cat = "STEEL_SCHEDULE_ROW"
            else:
                cat = "STEEL_SECTION"

            spec = DceBlockSpec(
                name=bname,
                description=f"Steel block {bname} from {source_key} (reader_warning={reader_warning})",
                category=cat,
                basepoint=(0.0, 0.0, 0.0),
                bbox=(0.0, 0.0, 0.0, 0.0),
                attdefs=attdefs,
                entities_count=sum(int(v) for v in ent_types.values()),
                entity_types=ent_types,
                layers_dep=["DCE_Name"] if attdefs else [],
                styles_dep=["Dce_Text"] if attdefs else [],
                source_file=src_ref,
                source_sha256=digest,
                confidence=f"PARTIAL_DWG_WASM_READ_{reader_warning}",
                notes=(
                    f"Loaded from {source_key} metadata (reader_warning={reader_warning}, "
                    f"dynamic_dict_keys={len(dyn_keys)}). Geometry bbox not populated headlessly; "
                    f"static 2D polyline generator required."
                ),
            )
            self.register_block(spec, allow_override=True)
            count += 1

        return count

    def scan_default_suite(self, base_dir: Optional[Union[str, Path]] = None) -> int:
        """Quét bộ DXF chuẩn mực của dự án để nạp toàn bộ block vào catalog."""
        if base_dir is None:
            base_dir = Path("g:/My Drive/Google AI Studio/01_Projects/03_Sprint2_KetQua_NeChu_CAD")
        else:
            base_dir = Path(base_dir)

        total_scanned = 0
        target_files = [
            base_dir / "KC-03_KetCauDamSan_v50_DA_SUA_KHUNG.dxf",
            base_dir / "KC-02_DinhViCotVach_v50_DA_SUA_KHUNG.dxf",
            base_dir / "KC-01_TongMatBang_v50_DA_SUA_KHUNG.dxf",
        ]

        # Kiểm tra thêm Form 2.dxf nếu có
        form2 = Path("C:/Dce Pro/Cad/Form 2.dxf")
        if form2.is_file():
            target_files.append(form2)

        for tf in target_files:
            if tf.is_file():
                try:
                    c = self.scan_dxf(tf)
                    total_scanned += c
                except Exception as ex:
                    print(f"[!] Lỗi khi quét {tf}: {ex}")

        # Nap bo sung danh muc Steel DWG (PARTIAL_DWG_WASM_READ_76)
        total_scanned += self.load_steel_dwg_catalog()

        return total_scanned

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": "6.0",
            "source_files": self._source_files,
            "blocks_count": len(self._blocks),
            "blocks": {k: v.to_dict() for k, v in self._blocks.items()},
        }

    def export_json(self, output_path: Union[str, Path]):
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        payload = self.to_dict()
        p.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    @classmethod
    def from_json(cls, json_path: Union[str, Path]) -> DceBlockCatalog:
        p = Path(json_path)
        data = json.loads(p.read_text(encoding="utf-8"))
        catalog = cls()
        catalog._source_files = data.get("source_files", {})
        for name, bdata in data.get("blocks", {}).items():
            catalog.register_block(DceBlockSpec.from_dict(bdata), allow_override=True)
        return catalog


_GLOBAL_CATALOG: Optional[DceBlockCatalog] = None


def get_default_catalog() -> DceBlockCatalog:
    """Lấy Singleton Catalog mặc định."""
    global _GLOBAL_CATALOG
    if _GLOBAL_CATALOG is None:
        _GLOBAL_CATALOG = DceBlockCatalog()
        _GLOBAL_CATALOG.scan_default_suite()
    return _GLOBAL_CATALOG
