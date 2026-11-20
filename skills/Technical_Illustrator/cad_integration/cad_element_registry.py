# -*- coding: utf-8 -*-
"""
Module: cad_element_registry.py
Author: Antigravity (GEMINI) - CAD DCE v6 Architecture
Description:
    He thong dang ky va quan ly danh tinh phan tu ket cau bat bien (Immutable Structural Element Registry).
    Dam bao moi phan tu ket cau (dam, cot, vach, san, mong, thep hinh) co mot element_id duy nhat,
    on dinh xuyen suot vong doi thiet ke, bat ke ten hien thi (mark) hay tiet dien bi thay doi.
    Lien ket da chieu giua:
      - Element ID (bat bien)
      - Mark / Ten hien thi (D1A, C1, S1...)
      - Geometry refs (ID thuc the hinh hoc)
      - Tag refs (Handle / ID block tag tren mat bang)
      - Schedule refs (Dong thong ke trong bang tien do/vat tu)
      - Detail ref (Dich mat cat chi tiet, so hieu to ban ve)
"""

import sys
if hasattr(sys.stdout, "reconfigure") and sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

import hashlib
import json
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union


class StructuralElement:
    """
    Doi tuong dai dien cho mot phan tu ket cau thuc te.
    Element ID la bat bien (immutable primary key).
    """
    def __init__(
        self,
        element_id: Optional[str] = None,
        category: str = "BEAM",
        mark: str = "",
        span_id: Optional[str] = None,
        floor_id: str = "TYPICAL",
        design_group_id: Optional[str] = None,
        section_profile: Optional[Dict[str, Any]] = None,
        geometry_refs: Optional[List[str]] = None,
        tag_refs: Optional[List[str]] = None,
        schedule_refs: Optional[List[str]] = None,
        detail_ref: Optional[Dict[str, Any]] = None,
        status: str = "CONTINUOUS",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.element_id = element_id or f"{category.upper()}_{uuid.uuid4().hex[:10].upper()}"
        self.category = category.upper()  # BEAM, COLUMN, SLAB, WALL, FOUNDATION, STEEL_MEMBER
        self.mark = mark                  # Ten hien thi (vd: D1A, C1) - co the thay doi
        self.span_id = span_id            # Vd: SPAN_1, SPAN_2 (cho dam nhieu nhip cung mark)
        self.floor_id = floor_id          # Vd: TANG_2, TANG_ROOF
        self.design_group_id = design_group_id  # Nhom thiet ke/thep (vd: GRP_200x400_3D20)
        self.section_profile = section_profile or {}  # Thong so tiet dien, vat lieu
        self.geometry_refs = geometry_refs or []      # Entity handles/IDs hinh hoc
        self.tag_refs = tag_refs or []                # Entity handles/IDs cua Block Tag tren mat bang
        self.schedule_refs = schedule_refs or []      # References toi dong bang thong ke
        self.detail_ref = detail_ref or {}            # {'sheet_number': 'KC.23', 'drawing_id': 'D1A_DET', 'target_exists': True}
        self.status = status.upper()                  # CONTINUOUS, STOPPED, TYPICAL, TERMINATED
        self.metadata = metadata or {}                # Thong tin bo sung tuy bien

        # Lich su thay doi (Audit log)
        self.change_history: List[Dict[str, Any]] = []

    def update_mark(self, new_mark: str, reason: str = "Rename") -> None:
        """Doi ten hien thi cua phan tu nhung van giu nguyen element_id bat bien."""
        if new_mark != self.mark:
            self.change_history.append({
                "action": "UPDATE_MARK",
                "old_mark": self.mark,
                "new_mark": new_mark,
                "reason": reason
            })
            self.mark = new_mark

    def update_section(self, new_section: Dict[str, Any], reason: str = "Section change") -> None:
        """Cap nhat thong so tiet dien."""
        self.change_history.append({
            "action": "UPDATE_SECTION",
            "old_section": dict(self.section_profile),
            "new_section": dict(new_section),
            "reason": reason
        })
        self.section_profile.update(new_section)

    def link_geometry(self, geom_id: str) -> None:
        """Gan handle hinh hoc vao phan tu."""
        if geom_id not in self.geometry_refs:
            self.geometry_refs.append(geom_id)

    def link_tag(self, tag_handle: str) -> None:
        """Gan handle block tag vao phan tu."""
        if tag_handle not in self.tag_refs:
            self.tag_refs.append(tag_handle)

    def link_schedule(self, schedule_ref: str) -> None:
        """Gan tham chieu bang thong ke."""
        if schedule_ref not in self.schedule_refs:
            self.schedule_refs.append(schedule_ref)

    def set_detail_target(self, sheet_number: str, drawing_id: str, target_exists: bool = False) -> None:
        """Thiet lap lien ket dich mat cat chi tiet."""
        self.detail_ref = {
            "sheet_number": sheet_number,
            "drawing_id": drawing_id,
            "target_exists": bool(target_exists)
        }

    def to_dict(self) -> Dict[str, Any]:
        """Xuat ra dictionary chuan de luu JSON."""
        return {
            "element_id": self.element_id,
            "category": self.category,
            "mark": self.mark,
            "span_id": self.span_id,
            "floor_id": self.floor_id,
            "design_group_id": self.design_group_id,
            "section_profile": self.section_profile,
            "geometry_refs": list(self.geometry_refs),
            "tag_refs": list(self.tag_refs),
            "schedule_refs": list(self.schedule_refs),
            "detail_ref": dict(self.detail_ref),
            "status": self.status,
            "metadata": dict(self.metadata),
            "change_history": list(self.change_history),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StructuralElement":
        """Khoi tao doi tuong tu dictionary."""
        elem = cls(
            element_id=data.get("element_id"),
            category=data.get("category", "BEAM"),
            mark=data.get("mark", ""),
            span_id=data.get("span_id"),
            floor_id=data.get("floor_id", "TYPICAL"),
            design_group_id=data.get("design_group_id"),
            section_profile=data.get("section_profile"),
            geometry_refs=data.get("geometry_refs"),
            tag_refs=data.get("tag_refs"),
            schedule_refs=data.get("schedule_refs"),
            detail_ref=data.get("detail_ref"),
            status=data.get("status", "CONTINUOUS"),
            metadata=data.get("metadata"),
        )
        elem.change_history = data.get("change_history", [])
        return elem


class CadElementRegistry:
    """
    So dang ky trung tam quan ly toan bo phan tu ket cau trong ho so thiet ke.
    Ho tro truy van theo tang, theo loai, theo nhom thiet ke, va dong bo tag-to-element.
    """
    def __init__(self, project_name: str = "DCE_PROJECT"):
        self.project_name = project_name
        self.elements: Dict[str, StructuralElement] = {}

    def register(self, element: StructuralElement) -> str:
        """Dang ky mot phan tu vao registry. Tra ve element_id."""
        if not element.element_id:
            element.element_id = f"{element.category}_{uuid.uuid4().hex[:10].upper()}"
        self.elements[element.element_id] = element
        return element.element_id

    def get(self, element_id: str) -> Optional[StructuralElement]:
        """Lay phan tu theo element_id bat bien."""
        return self.elements.get(element_id)

    def get_by_tag_handle(self, tag_handle: str) -> Optional[StructuralElement]:
        """Truy van nguoc phan tu nao dang so huu block tag handle nay."""
        for elem in self.elements.values():
            if tag_handle in elem.tag_refs:
                return elem
        return None

    def query(
        self,
        category: Optional[str] = None,
        floor_id: Optional[str] = None,
        mark: Optional[str] = None,
        design_group_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[StructuralElement]:
        """Truy van danh sach phan tu theo nhieu tieu chi loc."""
        results = []
        for elem in self.elements.values():
            if category and elem.category != category.upper():
                continue
            if floor_id and elem.floor_id != floor_id:
                continue
            if mark and elem.mark != mark:
                continue
            if design_group_id and elem.design_group_id != design_group_id:
                continue
            if status and elem.status != status.upper():
                continue
            results.append(elem)
        return results

    def update_mark(self, element_id: str, new_mark: str, reason: str = "Rename") -> bool:
        """
        Doi ten mark cua phan tu.
        Element ID van giu nguyen.
        Tra ve True neu thanh cong, False neu khong tim thay element_id.
        """
        elem = self.get(element_id)
        if not elem:
            return False
        elem.update_mark(new_mark, reason=reason)
        return True

    def update_section(self, element_id: str, new_section: Dict[str, Any], reason: str = "Section change") -> bool:
        """Cap nhat tiet dien cua phan tu."""
        elem = self.get(element_id)
        if not elem:
            return False
        elem.update_section(new_section, reason=reason)
        return True

    def link_tag(self, element_id: str, tag_handle: str) -> bool:
        """Lien ket mot block tag handle vao element."""
        elem = self.get(element_id)
        if not elem:
            return False
        elem.link_tag(tag_handle)
        return True

    def link_geometry(self, element_id: str, geom_id: str) -> bool:
        """Lien ket mot entity hinh hoc vao element."""
        elem = self.get(element_id)
        if not elem:
            return False
        elem.link_geometry(geom_id)
        return True

    def link_schedule(self, element_id: str, schedule_ref: str) -> bool:
        """Lien ket dong bang thong ke vao element."""
        elem = self.get(element_id)
        if not elem:
            return False
        elem.link_schedule(schedule_ref)
        return True

    def set_detail_target(
        self,
        element_id: str,
        sheet_number: str,
        drawing_id: str,
        target_exists: bool = False
    ) -> bool:
        """Thiet lap tham chieu toi mat cat chi tiet."""
        elem = self.get(element_id)
        if not elem:
            return False
        elem.set_detail_target(sheet_number, drawing_id, target_exists)
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Chuyen toan bo registry sang dict de luu JSON."""
        return {
            "project_name": self.project_name,
            "total_elements": len(self.elements),
            "elements": {
                eid: elem.to_dict()
                for eid, elem in self.elements.items()
            }
        }

    def to_json(self, indent: int = 2) -> str:
        """Xuat ra chuoi JSON UTF-8."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CadElementRegistry":
        """Tai tao registry tu dictionary."""
        reg = cls(project_name=data.get("project_name", "DCE_PROJECT"))
        raw_elements = data.get("elements", {})
        for eid, edata in raw_elements.items():
            elem = StructuralElement.from_dict(edata)
            reg.elements[eid] = elem
        return reg

    @classmethod
    def from_json(cls, json_str: str) -> "CadElementRegistry":
        """Tai tao registry tu chuoi JSON."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def validate_integrity(self) -> Dict[str, Any]:
        """
        Kiem tra tinh toan ven du lieu trong Registry:
        - Cac element_id co bi trung lap khong
        - Cac detail_ref co target_exists = False khong (canh bao missing detail)
        - Cac tag_refs co duoc gan khong
        """
        missing_details = []
        untagged_elements = []
        stopped_columns = []

        for eid, elem in self.elements.items():
            if elem.detail_ref and not elem.detail_ref.get("target_exists", False):
                missing_details.append({
                    "element_id": eid,
                    "mark": elem.mark,
                    "detail_ref": elem.detail_ref
                })
            if not elem.tag_refs and elem.category in ("BEAM", "COLUMN"):
                untagged_elements.append({
                    "element_id": eid,
                    "mark": elem.mark,
                    "category": elem.category
                })
            if elem.category == "COLUMN" and elem.status == "STOPPED":
                stopped_columns.append({
                    "element_id": eid,
                    "mark": elem.mark,
                    "floor_id": elem.floor_id
                })

        return {
            "total_registered": len(self.elements),
            "missing_details_count": len(missing_details),
            "missing_details": missing_details,
            "untagged_elements_count": len(untagged_elements),
            "untagged_elements": untagged_elements,
            "stopped_columns_count": len(stopped_columns),
            "stopped_columns": stopped_columns,
            "is_valid": len(missing_details) == 0
        }

    def validate_sheet_set_semantics(
        self,
        sheet_manifest: Optional[Dict[str, Any]] = None,
        rebar_strips: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Kiem chuan ngu nghia xuyen to ban ve (G2 Cross-Sheet Semantic Validator):
          1. floor_and_column_continuity: Cot da STOPPED/TERMINATED o tang duoi khong duoc tiep tuc ACTIVE/CONTINUOUS o tang tren; phat hien xung dot mark/floor.
          2. design_group_consistency: Cac phan tu cung design_group_id phai dong nhat category & thong so tiet dien/vat lieu.
          3. detail_target_resolution: Moi detail_ref phai co target_exists=True va khop to ban ve / detail_targets trong manifest (neu co).
          4. linkage_completeness: Kiem tra lien ket 3 chieu Geometry + Tag + Schedule cho tung cau kien ket cau chinh.
          5. rebar_top_bottom_separation: Tach biet tuyet doi dai thep san TOP vs BOTTOM tren các viewport, khong tron lan.
        """
        manifest = sheet_manifest or {}

        # --- 1. Floor ordering & Column continuity ---
        floor_rank: Dict[str, int] = {}
        raw_order = manifest.get("floor_order") or []
        if isinstance(raw_order, list) and raw_order:
            for idx, fid in enumerate(raw_order):
                floor_rank[str(fid)] = idx
        elif isinstance(manifest.get("floors"), list) and manifest.get("floors"):
            floors_list = manifest["floors"]
            for idx, fitem in enumerate(floors_list):
                if isinstance(fitem, dict) and fitem.get("floor_id"):
                    floor_rank[str(fitem["floor_id"])] = int(fitem.get("order", idx))
                elif isinstance(fitem, str):
                    floor_rank[fitem] = idx

        def _infer_floor_rank(elem: StructuralElement) -> Tuple[int, str]:
            fid = str(elem.floor_id or "")
            if fid in floor_rank:
                return (floor_rank[fid], fid)
            if "floor_index" in elem.metadata:
                return (int(elem.metadata["floor_index"]), fid)
            up = fid.upper()
            if any(k in up for k in ("MONG", "FOUND", "PILE")):
                return (-100, fid)
            if any(k in up for k in ("HAM", "BSM", "BASEMENT")):
                return (-50, fid)
            if any(k in up for k in ("MAI", "ROOF", "TUM")):
                return (999, fid)
            import re as _re
            m = _re.search(r"(\d+)", fid)
            if m:
                return (int(m.group(1)), fid)
            return (0, fid)

        stopped_column_violations: List[Dict[str, Any]] = []
        duplicate_mark_conflicts: List[Dict[str, Any]] = []
        undeclared_floor_violations: List[Dict[str, Any]] = []

        declared_floors = set(floor_rank.keys())
        col_by_mark: Dict[str, List[StructuralElement]] = {}
        seen_slot: Dict[Tuple[str, str, str, str], StructuralElement] = {}
        volatile_keys = {"origin_mm", "element_id", "mark", "note", "notes"}

        def _canonical_profile(elem: StructuralElement) -> Tuple[str, Tuple[Tuple[str, Any], ...]]:
            cleaned = {
                k: v for k, v in sorted((elem.section_profile or {}).items())
                if k not in volatile_keys
            }
            return (elem.category, tuple((k, json.dumps(v, sort_keys=True, ensure_ascii=False)) for k, v in cleaned.items()))

        for elem in self.elements.values():
            if declared_floors and elem.floor_id not in declared_floors and elem.floor_id.upper() not in ("TYPICAL", "ALL"):
                undeclared_floor_violations.append({
                    "element_id": elem.element_id,
                    "mark": elem.mark,
                    "floor_id": elem.floor_id,
                })

            if elem.category in ("COLUMN", "STEEL_COLUMN"):
                col_by_mark.setdefault(elem.mark, []).append(elem)

            slot = (elem.category, elem.floor_id, elem.mark, elem.span_id or "")
            if slot in seen_slot:
                prev = seen_slot[slot]
                if _canonical_profile(prev) != _canonical_profile(elem):
                    duplicate_mark_conflicts.append({
                        "category": elem.category,
                        "floor_id": elem.floor_id,
                        "mark": elem.mark,
                        "element_ids": [prev.element_id, elem.element_id],
                    })
            else:
                seen_slot[slot] = elem

        for mark, cols in col_by_mark.items():
            ranked = sorted(cols, key=_infer_floor_rank)
            stopped_at: Optional[Tuple[Tuple[int, str], StructuralElement]] = None
            for col in ranked:
                r = _infer_floor_rank(col)
                if stopped_at is not None:
                    stop_rank, stop_elem = stopped_at
                    if r[0] > stop_rank[0] and col.status in ("CONTINUOUS", "ACTIVE", "TYPICAL"):
                        stopped_column_violations.append({
                            "mark": mark,
                            "stopped_element_id": stop_elem.element_id,
                            "stopped_at_floor": stop_elem.floor_id,
                            "resumed_element_id": col.element_id,
                            "resumed_at_floor": col.floor_id,
                            "resumed_status": col.status,
                        })
                if col.status in ("STOPPED", "TERMINATED") and stopped_at is None:
                    stopped_at = (r, col)

        # --- 2. Design group consistency ---
        design_groups: Dict[str, List[StructuralElement]] = {}
        for elem in self.elements.values():
            if elem.design_group_id:
                design_groups.setdefault(elem.design_group_id, []).append(elem)

        design_group_violations: List[Dict[str, Any]] = []
        for dg_id, members in design_groups.items():
            sigs = {}
            for m in members:
                sig = _canonical_profile(m)
                sigs.setdefault(sig, []).append({"element_id": m.element_id, "mark": m.mark, "floor_id": m.floor_id})
            if len(sigs) > 1:
                design_group_violations.append({
                    "design_group_id": dg_id,
                    "variants_count": len(sigs),
                    "variants": [
                        {"category": s[0], "profile": dict(s[1]), "elements": elems}
                        for s, elems in sigs.items()
                    ],
                })

        # --- 3. Detail target resolution ---
        declared_sheets: set = set()
        declared_details: set = set()
        for sh in manifest.get("sheets", []):
            if isinstance(sh, dict):
                sno = sh.get("sheet_no") or sh.get("sheet_number")
                if sno:
                    declared_sheets.add(str(sno))
                for vp in sh.get("viewports", []):
                    if isinstance(vp, dict):
                        for did in vp.get("detail_marks", []) or []:
                            declared_details.add(str(did))
                            if sno:
                                declared_details.add(f"{sno}/{did}")
                        if vp.get("drawing_id"):
                            declared_details.add(str(vp["drawing_id"]))
                            if sno:
                                declared_details.add(f"{sno}/{vp['drawing_id']}")

        for dt in manifest.get("detail_targets", []):
            if isinstance(dt, dict):
                sn = dt.get("sheet_number") or dt.get("sheet_no") or ""
                did = dt.get("drawing_id") or ""
                if sn:
                    declared_sheets.add(str(sn))
                if did:
                    declared_details.add(str(did))
                if sn and did:
                    declared_details.add(f"{sn}/{did}")
            elif isinstance(dt, str):
                declared_details.add(dt)

        missing_detail_targets: List[Dict[str, Any]] = []
        for eid, elem in self.elements.items():
            dref = elem.detail_ref or {}
            if not dref:
                continue
            if not dref.get("target_exists", False):
                missing_detail_targets.append({
                    "element_id": eid,
                    "mark": elem.mark,
                    "detail_ref": dref,
                    "reason": "target_exists is False",
                })
                continue
            sn = str(dref.get("sheet_number", "") or "")
            did = str(dref.get("drawing_id", "") or "")
            if declared_sheets and sn and sn not in declared_sheets:
                missing_detail_targets.append({
                    "element_id": eid,
                    "mark": elem.mark,
                    "detail_ref": dref,
                    "reason": f"Sheet '{sn}' not declared in sheet_manifest",
                })
            elif declared_details and did:
                combo = f"{sn}/{did}" if sn else did
                if did not in declared_details and combo not in declared_details:
                    missing_detail_targets.append({
                        "element_id": eid,
                        "mark": elem.mark,
                        "detail_ref": dref,
                        "reason": f"Detail target '{combo}' not found in manifest",
                    })

        # --- 4. 3-way linkage completeness (Geometry + Tag + Schedule) ---
        physical_categories = {
            "BEAM", "COLUMN", "WALL", "SLAB", "FOUNDATION",
            "STEEL_MEMBER", "STEEL_COLUMN", "STEEL_BEAM", "STEEL_BASEPLATE", "STEEL_PLATE",
        }
        incomplete_linkage: List[Dict[str, Any]] = []
        for eid, elem in self.elements.items():
            if elem.category not in physical_categories:
                continue
            missing_legs = []
            if not elem.geometry_refs:
                missing_legs.append("geometry_refs")
            if not elem.tag_refs:
                missing_legs.append("tag_refs")
            if not elem.schedule_refs:
                missing_legs.append("schedule_refs")
            if missing_legs:
                incomplete_linkage.append({
                    "element_id": eid,
                    "mark": elem.mark,
                    "category": elem.category,
                    "floor_id": elem.floor_id,
                    "missing_legs": missing_legs,
                })

        # --- 5. TOP / BOTTOM rebar strip separation ---
        strips = list(rebar_strips) if rebar_strips is not None else list(manifest.get("rebar_strips", []))
        invalid_rebar_faces: List[Dict[str, Any]] = []
        viewport_face_mixing_violations: List[Dict[str, Any]] = []
        strip_face_index: Dict[str, str] = {}

        for st in strips:
            sid = str(st.get("strip_id", ""))
            face_val = str(st.get("face", "")).strip().upper()
            if face_val not in ("TOP", "BOTTOM"):
                invalid_rebar_faces.append({"strip_id": sid, "face": st.get("face"), "floor_id": st.get("floor_id")})
            elif sid:
                prev_face = strip_face_index.get(sid)
                if prev_face is not None and prev_face != face_val:
                    viewport_face_mixing_violations.append({
                        "strip_id": sid,
                        "reason": f"Duplicate strip_id mixes {prev_face} and {face_val}",
                    })
                strip_face_index[sid] = face_val

        for sh in manifest.get("sheets", []):
            if not isinstance(sh, dict):
                continue
            sno = sh.get("sheet_no") or sh.get("sheet_number") or "UNKNOWN"
            for vp in sh.get("viewports", []):
                if not isinstance(vp, dict):
                    continue
                cf = str(vp.get("content_face") or "").strip().upper()
                if cf not in ("TOP", "BOTTOM"):
                    continue
                for sid in vp.get("strip_ids", []) or []:
                    actual = strip_face_index.get(str(sid))
                    if actual and actual != cf:
                        viewport_face_mixing_violations.append({
                            "sheet_no": sno,
                            "viewport_id": vp.get("viewport_id", ""),
                            "content_face": cf,
                            "strip_id": sid,
                            "actual_strip_face": actual,
                            "reason": f"Viewport content_face={cf} contains {actual} rebar strip '{sid}'",
                        })
                for vst in vp.get("rebar_strips", []) or []:
                    if isinstance(vst, dict):
                        vface = str(vst.get("face", "")).strip().upper()
                        if vface and vface != cf:
                            viewport_face_mixing_violations.append({
                                "sheet_no": sno,
                                "viewport_id": vp.get("viewport_id", ""),
                                "content_face": cf,
                                "strip_id": vst.get("strip_id", ""),
                                "actual_strip_face": vface,
                                "reason": f"Viewport content_face={cf} contains {vface} inline strip",
                            })

        top_strips = filter_rebar_strips_by_face(strips, "TOP") if strips else []
        bot_strips = filter_rebar_strips_by_face(strips, "BOTTOM") if strips else []
        top_ids = {s.get("strip_id") for s in top_strips if s.get("strip_id")}
        bot_ids = {s.get("strip_id") for s in bot_strips if s.get("strip_id")}
        overlap_ids = sorted(top_ids & bot_ids)
        if overlap_ids:
            viewport_face_mixing_violations.append({
                "overlapping_strip_ids": overlap_ids,
                "reason": "Strip IDs appear in both TOP and BOTTOM sets",
            })

        checks = {
            "floor_and_column_continuity": (
                len(stopped_column_violations) == 0
                and len(duplicate_mark_conflicts) == 0
                and len(undeclared_floor_violations) == 0
            ),
            "design_group_consistency": len(design_group_violations) == 0,
            "detail_target_resolution": len(missing_detail_targets) == 0,
            "linkage_completeness": len(incomplete_linkage) == 0,
            "rebar_top_bottom_separation": (
                len(invalid_rebar_faces) == 0
                and len(viewport_face_mixing_violations) == 0
            ),
        }
        is_valid = all(checks.values())

        return {
            "Standard_Method": "DCE Sheet Set Semantics G2 (STRUCTURAL_SHEET_SET_GUIDE v6)",
            "is_valid": is_valid,
            "checks": checks,
            "total_elements": len(self.elements),
            "rebar_top_count": len(top_strips),
            "rebar_bottom_count": len(bot_strips),
            "violations": {
                "stopped_column_violations": stopped_column_violations,
                "duplicate_mark_conflicts": duplicate_mark_conflicts,
                "undeclared_floor_violations": undeclared_floor_violations,
                "design_group_violations": design_group_violations,
                "missing_detail_targets": missing_detail_targets,
                "incomplete_linkage": incomplete_linkage,
                "invalid_rebar_faces": invalid_rebar_faces,
                "viewport_face_mixing_violations": viewport_face_mixing_violations,
            },
            "Calculation_Logs": [
                {"step": k, "passed": v} for k, v in checks.items()
            ],
        }

    def validate_dxf_entity_map(
        self,
        dxf_path: Union[str, Path],
        sidecar_path: Optional[Union[str, Path]] = None,
        fixture_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Reopen a DXF and verify every sidecar entity_map handle and 3-way structural ref."""
        return validate_dxf_entity_map_linkage(
            dxf_path=dxf_path,
            sidecar_path=sidecar_path,
            registry=self,
            fixture_data=fixture_data,
        )


def _normalize_handle_list(single_val: Any, list_val: Any) -> List[str]:
    """Normalize optional single handle and list of handles into deduplicated strings."""
    handles: List[str] = []
    if isinstance(single_val, str) and single_val.strip():
        handles.append(single_val.strip())
    if isinstance(list_val, (list, tuple)):
        for item in list_val:
            if isinstance(item, str) and item.strip() and item.strip() not in handles:
                handles.append(item.strip())
    return handles


def _index_layout_entities(layout: Any) -> Dict[str, Dict[str, Any]]:
    """Index DXF entities in a layout by handle with type, layer, and block attribs."""
    if layout is None:
        return {}
    indexed: Dict[str, Dict[str, Any]] = {}
    for entity in layout:
        handle = str(getattr(entity.dxf, "handle", "") or "")
        if not handle:
            continue
        etype = entity.dxftype()
        record: Dict[str, Any] = {
            "handle": handle,
            "dxftype": etype,
            "layer": str(getattr(entity.dxf, "layer", "") or ""),
        }
        if etype == "INSERT":
            record["block_name"] = str(getattr(entity.dxf, "name", "") or "")
            record["attribs"] = {
                str(att.dxf.tag): str(att.dxf.text)
                for att in entity.attribs
            }
        elif etype in ("TEXT", "MTEXT"):
            record["text"] = str(getattr(entity.dxf, "text", "") or "") if etype == "TEXT" else str(entity.text)
        indexed[handle] = record
    return indexed


def _inspect_paperspace_viewports(
    doc: Any,
    msp_by_handle: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """Inspect paperspace viewports, overlaps, effective scales, and TOP/BOTTOM frozen layers."""
    ps_layout = doc.layouts.get("Layout1") if "Layout1" in doc.layouts else None
    if ps_layout is None:
        for layout in doc.layouts:
            if layout.name != "Model":
                ps_layout = layout
                break

    viewports: List[Dict[str, Any]] = []
    if ps_layout is not None:
        for vp in ps_layout.query("VIEWPORT"):
            if getattr(vp.dxf, "id", 0) <= 1:
                continue
            center = vp.dxf.center
            width = float(vp.dxf.width)
            height = float(vp.dxf.height)
            view_height = float(vp.dxf.view_height)
            bbox = [
                round(center.x - width / 2.0, 4),
                round(center.y - height / 2.0, 4),
                round(center.x + width / 2.0, 4),
                round(center.y + height / 2.0, 4),
            ]
            viewports.append({
                "handle": str(vp.dxf.handle),
                "layer": str(getattr(vp.dxf, "layer", "") or ""),
                "paper_bbox": bbox,
                "width_mm": round(width, 4),
                "height_mm": round(height, 4),
                "view_height": round(view_height, 4),
                "actual_scale_denominator": round(view_height / height, 6) if height > 0 else None,
                "frozen_layers": sorted(str(x) for x in vp.frozen_layers),
            })

    overlaps: List[Dict[str, Any]] = []
    for i, vp_a in enumerate(viewports):
        aa = vp_a["paper_bbox"]
        for vp_b in viewports[i + 1:]:
            bb = vp_b["paper_bbox"]
            area = max(0.0, min(aa[2], bb[2]) - max(aa[0], bb[0])) * max(0.0, min(aa[3], bb[3]) - max(aa[1], bb[1]))
            if area > 1e-6:
                overlaps.append({
                    "vp_a": vp_a["handle"],
                    "vp_b": vp_b["handle"],
                    "overlap_mm2": round(area, 4),
                })

    rebar_top_handles = sorted(h for h, rec in msp_by_handle.items() if rec["layer"] == "REBAR_TOP")
    rebar_bottom_handles = sorted(h for h, rec in msp_by_handle.items() if rec["layer"] == "REBAR_BOTTOM")

    vp_top = [v for v in viewports if v["layer"] == "VP_TOP"]
    vp_bot = [v for v in viewports if v["layer"] == "VP_BOTTOM"]
    has_dual_rebar = bool(vp_top and vp_bot)
    top_visible_handles: List[str] = []
    bot_visible_handles: List[str] = []
    if has_dual_rebar:
        top_frozen = set(vp_top[0]["frozen_layers"])
        bot_frozen = set(vp_bot[0]["frozen_layers"])
        if "REBAR_TOP" not in top_frozen:
            top_visible_handles.extend(rebar_top_handles)
        if "REBAR_BOTTOM" not in top_frozen:
            top_visible_handles.extend(rebar_bottom_handles)
        if "REBAR_TOP" not in bot_frozen:
            bot_visible_handles.extend(rebar_top_handles)
        if "REBAR_BOTTOM" not in bot_frozen:
            bot_visible_handles.extend(rebar_bottom_handles)

    vp_top_freezes_bottom = all("REBAR_BOTTOM" in v["frozen_layers"] for v in vp_top) if vp_top else False
    vp_bot_freezes_top = all("REBAR_TOP" in v["frozen_layers"] for v in vp_bot) if vp_bot else False
    disjoint_visible_rebar_ok = (
        has_dual_rebar
        and vp_top_freezes_bottom
        and vp_bot_freezes_top
        and bool(top_visible_handles)
        and bool(bot_visible_handles)
        and set(top_visible_handles).isdisjoint(set(bot_visible_handles))
    )

    return {
        "viewports": viewports,
        "viewport_overlap_mm2": overlaps,
        "viewport_nonoverlap_ok": len(overlaps) == 0,
        "has_dual_rebar_viewports": has_dual_rebar,
        "vp_top_freezes_rebar_bottom": vp_top_freezes_bottom,
        "vp_bottom_freezes_rebar_top": vp_bot_freezes_top,
        "visible_rebar_handles_in_vp_top": top_visible_handles,
        "visible_rebar_handles_in_vp_bottom": bot_visible_handles,
        "disjoint_visible_rebar_ok": disjoint_visible_rebar_ok,
    }


def _collect_expected_elements(
    registry: Optional[CadElementRegistry],
    fixture_data: Optional[Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    """Collect expected physical structural elements from registry and fixture payload."""
    expected: Dict[str, Dict[str, Any]] = {}
    if registry is not None:
        for eid, elem in registry.elements.items():
            expected[eid] = {
                "element_id": eid,
                "category": elem.category,
                "geometry_refs": list(elem.geometry_refs),
                "tag_refs": list(elem.tag_refs),
                "schedule_refs": list(elem.schedule_refs),
            }

    if fixture_data:
        for group_key, default_cat in (
            ("concrete_elements", "CONCRETE"),
            ("steel_sections", "STEEL_MEMBER"),
            ("baseplates", "STEEL_BASEPLATE"),
            ("steel_plates", "STEEL_PLATE"),
        ):
            for row in fixture_data.get(group_key, []):
                eid = row.get("element_id")
                if not eid:
                    continue
                if eid not in expected:
                    expected[eid] = {
                        "element_id": eid,
                        "category": str(row.get("category", default_cat)).upper(),
                        "geometry_refs": list(row.get("geometry_refs", [])),
                        "tag_refs": list(row.get("tag_refs", [])),
                        "schedule_refs": list(row.get("schedule_refs", [])),
                    }
                else:
                    for key in ("geometry_refs", "tag_refs", "schedule_refs"):
                        if not expected[eid][key] and row.get(key):
                            expected[eid][key] = list(row[key])
    return expected


def validate_dxf_entity_map_linkage(
    dxf_path: Union[str, Path],
    sidecar_path: Optional[Union[str, Path]] = None,
    registry: Optional[CadElementRegistry] = None,
    fixture_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    A1-06 Validator: Reopen DXF, verify sidecar SHA-256, resolve every entity_map handle
    to physical DXF entities, inspect KC-04 viewport face filters, and check strict 3-way
    physical linkage (no metadata-only PASS).
    """
    import ezdxf

    dxf_p = Path(dxf_path)
    sc_p = Path(sidecar_path) if sidecar_path is not None else dxf_p.with_suffix(".dce_audit.json")
    if not dxf_p.is_file():
        raise FileNotFoundError(f"DXF not found: {dxf_p}")
    if not sc_p.is_file():
        raise FileNotFoundError(f"Sidecar not found: {sc_p}")

    actual_sha256 = hashlib.sha256(dxf_p.read_bytes()).hexdigest()
    sidecar = json.loads(sc_p.read_text(encoding="utf-8"))
    top_sha = sidecar.get("dxf_sha256")
    prov = sidecar.get("provenance")
    prov_sha = prov.get("dxf_sha256") if isinstance(prov, dict) else None
    provenance_sha256_present = isinstance(prov, dict) and bool(prov_sha)

    top_sha_ok = (top_sha == actual_sha256) if top_sha else False
    prov_sha_ok = (prov_sha == actual_sha256) if provenance_sha256_present else False
    if top_sha and prov_sha:
        dxf_sha256_match = top_sha_ok and prov_sha_ok
    else:
        dxf_sha256_match = top_sha_ok or prov_sha_ok

    doc = ezdxf.readfile(str(dxf_p))
    msp_by_handle = _index_layout_entities(doc.modelspace())
    ps_layout = doc.layouts.get("Layout1") if "Layout1" in doc.layouts else None
    ps_by_handle = _index_layout_entities(ps_layout)
    all_by_handle = {**ps_by_handle, **msp_by_handle}

    vp_report = _inspect_paperspace_viewports(doc, msp_by_handle)
    entity_map = sidecar.get("entity_map", {}) or {}
    rebar_faces = {
        str(r.get("strip_id")): str(r.get("face", "")).upper()
        for r in (fixture_data or {}).get("rebar_strips", [])
        if r.get("strip_id")
    }

    missing_geometry_handles: List[Dict[str, Any]] = []
    missing_tag_handles: List[Dict[str, Any]] = []
    invalid_tag_entities: List[Dict[str, Any]] = []
    missing_schedule_handles: List[Dict[str, Any]] = []
    rebar_layer_mismatches: List[Dict[str, Any]] = []
    formatting_warnings: List[Dict[str, Any]] = []
    resolved_counts = {"geometry": 0, "tag": 0, "schedule": 0}
    recorded_counts = {"geometry": 0, "tag": 0, "schedule": 0}

    for eid, entry in entity_map.items():
        geom_handles = _normalize_handle_list(None, entry.get("geometry_handles"))
        tag_handles = _normalize_handle_list(entry.get("tag_handle"), entry.get("tag_handles"))
        sched_handles = _normalize_handle_list(entry.get("schedule_handle"), entry.get("schedule_handles"))
        recorded_counts["geometry"] += len(geom_handles)
        recorded_counts["tag"] += len(tag_handles)
        recorded_counts["schedule"] += len(sched_handles)

        face_decl = str(entry.get("face") or rebar_faces.get(eid) or "").strip().upper()
        is_rebar = bool(face_decl) or eid.startswith("RS_")

        for gh in geom_handles:
            rec = msp_by_handle.get(gh)
            if rec is None:
                missing_geometry_handles.append({"element_id": eid, "handle": gh})
            else:
                resolved_counts["geometry"] += 1
                if is_rebar and face_decl in ("TOP", "BOTTOM") and rec["layer"] != f"REBAR_{face_decl}":
                    rebar_layer_mismatches.append({
                        "strip_id": eid,
                        "handle": gh,
                        "expected_layer": f"REBAR_{face_decl}",
                        "actual_layer": rec["layer"],
                    })

        for th in tag_handles:
            rec = msp_by_handle.get(th)
            if rec is None:
                missing_tag_handles.append({"element_id": eid, "handle": th})
            elif rec["dxftype"] != "INSERT" or not rec.get("attribs"):
                invalid_tag_entities.append({
                    "element_id": eid,
                    "handle": th,
                    "dxftype": rec["dxftype"],
                    "attribs_count": len(rec.get("attribs", {})),
                })
            else:
                resolved_counts["tag"] += 1
                for tag_key, tag_val in rec["attribs"].items():
                    if tag_val.startswith("{") and tag_val.endswith("}"):
                        formatting_warnings.append({
                            "element_id": eid,
                            "handle": th,
                            "attrib": tag_key,
                            "value": tag_val,
                            "reason": "Raw dict literal serialized into ATTRIB",
                        })

        for sh in sched_handles:
            if sh not in all_by_handle:
                missing_schedule_handles.append({"element_id": eid, "handle": sh})
            else:
                resolved_counts["schedule"] += 1

    recorded_handles_resolved_ok = (
        len(entity_map) > 0
        and len(missing_geometry_handles) == 0
        and len(missing_tag_handles) == 0
        and len(invalid_tag_entities) == 0
        and len(missing_schedule_handles) == 0
        and len(rebar_layer_mismatches) == 0
    )

    expected_elements = _collect_expected_elements(registry, fixture_data)
    unmapped_expected_elements: List[Dict[str, Any]] = []
    missing_physical_geometry: List[Dict[str, Any]] = []
    missing_physical_tag: List[Dict[str, Any]] = []
    metadata_only_schedule_refs: List[Dict[str, Any]] = []
    source_ref_mismatches: List[Dict[str, Any]] = []
    tag_ref_mismatches: List[Dict[str, Any]] = []

    if expected_elements:
        target_ids = list(expected_elements.keys())
    else:
        target_ids = [
            eid for eid, entry in entity_map.items()
            if not (entry.get("face") or eid.startswith("RS_"))
        ]

    for eid in target_ids:
        exp = expected_elements.get(eid, {"geometry_refs": [], "tag_refs": [], "schedule_refs": []})
        if eid not in entity_map:
            unmapped_expected_elements.append({
                "element_id": eid,
                "category": exp.get("category", "UNKNOWN"),
            })
            continue

        entry = entity_map[eid]
        geom_handles = _normalize_handle_list(None, entry.get("geometry_handles"))
        tag_handles = _normalize_handle_list(entry.get("tag_handle"), entry.get("tag_handles"))
        sched_handles = _normalize_handle_list(entry.get("schedule_handle"), entry.get("schedule_handles"))

        resolved_geom = [h for h in geom_handles if h in msp_by_handle]
        resolved_tags = [
            h for h in tag_handles
            if h in msp_by_handle and msp_by_handle[h]["dxftype"] == "INSERT" and msp_by_handle[h].get("attribs")
        ]
        resolved_sched = [h for h in sched_handles if h in all_by_handle]

        if not resolved_geom:
            missing_physical_geometry.append({"element_id": eid})
        if not resolved_tags:
            missing_physical_tag.append({"element_id": eid})

        exp_sched_refs = list(exp.get("schedule_refs") or entry.get("schedule_refs") or [])
        if exp_sched_refs and not resolved_sched:
            metadata_only_schedule_refs.append({
                "element_id": eid,
                "schedule_refs": exp_sched_refs,
                "reason": "Metadata schedule_refs string array has no resolved schedule entity handle in DXF",
            })

        exp_grefs = list(exp.get("geometry_refs") or [])
        ent_srefs = list(entry.get("source_refs") or [])
        if exp_grefs and exp_grefs != ent_srefs:
            source_ref_mismatches.append({
                "element_id": eid,
                "expected_geometry_refs": exp_grefs,
                "entity_map_source_refs": ent_srefs,
            })

        exp_trefs = list(exp.get("tag_refs") or [])
        ent_trefs = list(entry.get("tag_refs") or [])
        if exp_trefs and exp_trefs != ent_trefs:
            tag_ref_mismatches.append({
                "element_id": eid,
                "expected_tag_refs": exp_trefs,
                "entity_map_tag_refs": ent_trefs,
            })

    strict_3way_physical_linkage_ok = (
        dxf_sha256_match
        and recorded_handles_resolved_ok
        and len(unmapped_expected_elements) == 0
        and len(missing_physical_geometry) == 0
        and len(missing_physical_tag) == 0
        and len(metadata_only_schedule_refs) == 0
        and len(source_ref_mismatches) == 0
        and len(tag_ref_mismatches) == 0
    )

    calc_logs = [
        {"step": "sidecar_sha256_match", "passed": dxf_sha256_match},
        {"step": "recorded_handles_resolved", "passed": recorded_handles_resolved_ok},
        {"step": "viewport_nonoverlap", "passed": vp_report["viewport_nonoverlap_ok"]},
        {
            "step": "dual_rebar_viewport_freeze",
            "passed": vp_report["disjoint_visible_rebar_ok"] if vp_report["has_dual_rebar_viewports"] else True,
        },
        {"step": "strict_3way_physical_linkage", "passed": strict_3way_physical_linkage_ok},
    ]

    return {
        "Standard_Method": "DCE A1-06 DXF Entity Map & 3-Way Linkage Validator v6",
        "dxf_path": str(dxf_p),
        "sidecar_path": str(sc_p),
        "sheet_no": sidecar.get("sheet_no"),
        "actual_sha256": actual_sha256,
        "dxf_sha256_match": dxf_sha256_match,
        "top_sha256_match": top_sha_ok,
        "provenance_sha256_present": provenance_sha256_present,
        "provenance_sha256_match": prov_sha_ok,
        "entity_map_entries": len(entity_map),
        "expected_elements_count": len(expected_elements),
        "recorded_handle_counts": recorded_counts,
        "resolved_handle_counts": resolved_counts,
        "recorded_handles_resolved_ok": recorded_handles_resolved_ok,
        "strict_3way_physical_linkage_ok": strict_3way_physical_linkage_ok,
        "viewport_inspection": vp_report,
        "issues": {
            "missing_geometry_handles": missing_geometry_handles,
            "missing_tag_handles": missing_tag_handles,
            "invalid_tag_entities": invalid_tag_entities,
            "missing_schedule_handles": missing_schedule_handles,
            "rebar_layer_mismatches": rebar_layer_mismatches,
            "unmapped_expected_elements": unmapped_expected_elements,
            "missing_physical_geometry": missing_physical_geometry,
            "missing_physical_tag": missing_physical_tag,
            "metadata_only_schedule_refs": metadata_only_schedule_refs,
            "source_ref_mismatches": source_ref_mismatches,
            "tag_ref_mismatches": tag_ref_mismatches,
            "formatting_warnings": formatting_warnings,
        },
        "Calculation_Logs": calc_logs,
    }


def filter_rebar_strips_by_face(
    rebar_strips: List[Dict[str, Any]],
    face: str,
    floor_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Loc danh sach dai thep san theo mat lam viec ('TOP' | 'BOTTOM' | 'BOTH'), tuyet doi khong tron lan.
    """
    target_face = str(face or "").strip().upper()
    if target_face not in ("TOP", "BOTTOM", "BOTH"):
        raise ValueError(f"Gia tri face khong hop le: '{face}'. Chi chap nhan 'TOP', 'BOTTOM', hoac 'BOTH'.")

    filtered: List[Dict[str, Any]] = []
    for strip in rebar_strips or []:
        if floor_id is not None and strip.get("floor_id") != floor_id:
            continue
        sface = str(strip.get("face", "")).strip().upper()
        if target_face == "BOTH":
            if sface in ("TOP", "BOTTOM", "BOTH"):
                filtered.append(dict(strip))
        else:
            if sface == target_face:
                filtered.append(dict(strip))

    filtered.sort(key=lambda item: (str(item.get("floor_id", "")), str(item.get("strip_id", ""))))
    return filtered


# ==============================================================================
# C1 / V6 FIXTURE <-> DCEPLANENGINE MODEL ADAPTER (GEMINI G1 BRIDGE)
# ==============================================================================

DEFAULT_C1_FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "c1_sample_model.json"


def _poly_bounds_mm(polygon: List[Dict[str, float]]) -> Tuple[float, float, float, float]:
    """Tinh (xmin, ymin, xmax, ymax) mm tu danh sach dinh {'x': ..., 'y': ...}."""
    xs = [float(p["x"]) for p in polygon]
    ys = [float(p["y"]) for p in polygon]
    return min(xs), min(ys), max(xs), max(ys)


def c1_fixture_to_engine_model(
    fixture_or_path: Union[Dict[str, Any], str, Path, None] = None,
    floor_id: str = "TANG_2",
    registry: Optional[CadElementRegistry] = None,
) -> Tuple[Dict[str, Any], CadElementRegistry]:
    """
    Chuyen doi fixture v6 (c1_sample_model.json - don vi mm, schema semantic)
    sang dict model chuan cua DcePlanEngine (don vi m cho toa do) va dong thoi
    nap day du cac StructuralElement vao CadElementRegistry.

    Tra ve:
        (engine_model_dict, registry)
    """
    if fixture_or_path is None:
        fixture_or_path = DEFAULT_C1_FIXTURE_PATH

    if isinstance(fixture_or_path, (str, Path)):
        raw = json.loads(Path(fixture_or_path).read_text(encoding="utf-8"))
    else:
        raw = dict(fixture_or_path)

    if registry is None:
        registry = CadElementRegistry(project_name=raw.get("project_name", "DCE_V6_C1_FIXTURE"))

    # 1. Grid system (mm -> m)
    grid_sys = raw.get("grid_system", {})
    x_axes = grid_sys.get("x_axes", [])
    y_axes = grid_sys.get("y_axes", [])
    if x_axes and y_axes:
        grid_x = {str(ax["name"]): round(float(ax["coord"]) / 1000.0, 4) for ax in x_axes}
        grid_y = {str(ax["name"]): round(float(ax["coord"]) / 1000.0, 4) for ax in y_axes}
        L_total = max(grid_x.values()) - min(grid_x.values())
        B_total = max(grid_y.values()) - min(grid_y.values())
    else:
        grid_x = dict(raw.get("grid_x", {"1": 0.0, "2": 4.0, "3": 8.0, "4": 12.0}))
        grid_y = dict(raw.get("grid_y", {"A": 0.0, "B": 5.0, "C": 10.0}))
        L_total = float(raw.get("L_total", max(grid_x.values())))
        B_total = float(raw.get("B_total", max(grid_y.values())))

    # 2. Columns (v6 semantic columns hoac columns_v6)
    v6_cols = raw.get("columns_v6") or [
        c for c in raw.get("columns", [])
        if isinstance(c, dict) and ("section_profile" in c or "location" in c)
    ]
    engine_columns: List[Dict[str, Any]] = []
    for idx, c in enumerate(v6_cols):
        eid = c.get("element_id") or f"COL_{idx+1:03d}"
        mark = c.get("mark") or c.get("name", f"C{idx+1}")
        c_floor = c.get("floor_id", floor_id)
        status = c.get("status", "CONTINUOUS")
        sec = dict(c.get("section_profile") or {})
        b_mm = float(sec.get("b_mm", float(c.get("bx", 0.2)) * 1000.0))
        h_mm = float(sec.get("h_mm", float(c.get("by", 0.2)) * 1000.0))
        loc = c.get("location") or {"x": float(c.get("x", 0.0)) * 1000.0, "y": float(c.get("y", 0.0)) * 1000.0}
        x_m = round(float(loc["x"]) / 1000.0, 4)
        y_m = round(float(loc["y"]) / 1000.0, 4)
        size_str = f"{int(round(b_mm))}x{int(round(h_mm))}"

        elem = StructuralElement(
            element_id=eid,
            category="COLUMN",
            mark=mark,
            floor_id=c_floor,
            section_profile=sec,
            geometry_refs=list(c.get("geometry_refs", [])),
            tag_refs=list(c.get("tag_refs", [])),
            schedule_refs=list(c.get("schedule_refs", [])),
            detail_ref=dict(c.get("detail_ref", {})),
            status=status,
            metadata={"location_mm": loc, "status_note": c.get("status_note", "")},
        )
        registry.register(elem)

        engine_columns.append({
            "element_id": eid,
            "name": mark,
            "x": x_m,
            "y": y_m,
            "bx": round(b_mm / 1000.0, 4),
            "by": round(h_mm / 1000.0, 4),
            "size": size_str,
            "conc": sec.get("concrete_grade", "B30"),
            "thep_do": sec.get("rebar_long", "4D16"),
            "thep_dai": sec.get("stirrup", "d6a150"),
            "status": status,
            "floor_id": c_floor,
            "detail_ref": dict(c.get("detail_ref", {})),
        })

    # 3. Beams (X, Y, Skew, Multi-span same mark, Same section different rebar group)
    v6_beams = raw.get("beams_v6") or raw.get("beams", [])
    beams_x: List[Dict[str, Any]] = []
    beams_y: List[Dict[str, Any]] = []
    secondary_beams: List[Dict[str, Any]] = []

    for idx, bm in enumerate(v6_beams):
        eid = bm.get("element_id") or f"BEAM_{idx+1:03d}"
        mark = bm.get("mark") or bm.get("name", f"D{idx+1}")
        span_id = bm.get("span_id")
        b_floor = bm.get("floor_id", floor_id)
        dgroup = bm.get("design_group_id")
        sec = dict(bm.get("section_profile") or {})
        b_mm = float(sec.get("b_mm", float(bm.get("b", 0.2)) * 1000.0))
        h_mm = float(sec.get("h_mm", float(bm.get("h", 0.4)) * 1000.0))
        sp = bm.get("start_point") or {"x": float(bm.get("x0", 0.0)) * 1000.0, "y": float(bm.get("y0", 0.0)) * 1000.0}
        ep = bm.get("end_point") or {"x": float(bm.get("x1", 0.0)) * 1000.0, "y": float(bm.get("y1", 0.0)) * 1000.0}
        x0_m = round(float(sp["x"]) / 1000.0, 4)
        y0_m = round(float(sp["y"]) / 1000.0, 4)
        x1_m = round(float(ep["x"]) / 1000.0, 4)
        y1_m = round(float(ep["y"]) / 1000.0, 4)
        size_str = f"{int(round(b_mm))}x{int(round(h_mm))}"
        orient = str(bm.get("orientation", "")).upper()

        elem = StructuralElement(
            element_id=eid,
            category="BEAM",
            mark=mark,
            span_id=span_id,
            floor_id=b_floor,
            design_group_id=dgroup,
            section_profile=sec,
            geometry_refs=list(bm.get("geometry_refs", [])),
            tag_refs=list(bm.get("tag_refs", [])),
            schedule_refs=list(bm.get("schedule_refs", [])),
            detail_ref=dict(bm.get("detail_ref", {})),
            status=bm.get("status", "CONTINUOUS"),
            metadata={
                "orientation": orient,
                "angle_deg": bm.get("angle_deg", 0.0),
                "start_point_mm": sp,
                "end_point_mm": ep,
            },
        )
        registry.register(elem)

        bm_rec = {
            "element_id": eid,
            "name": mark,
            "span_id": span_id,
            "floor_id": b_floor,
            "design_group_id": dgroup,
            "size": size_str,
            "b": round(b_mm / 1000.0, 4),
            "h": round(h_mm / 1000.0, 4),
            "x0": x0_m,
            "y0": y0_m,
            "x1": x1_m,
            "y1": y1_m,
            "orientation": orient,
            "angle_deg": float(bm.get("angle_deg", 0.0)),
            "rebar_top": sec.get("rebar_top", ""),
            "rebar_bot": sec.get("rebar_bot", ""),
            "stirrup": sec.get("stirrup", ""),
            "detail_ref": dict(bm.get("detail_ref", {})),
        }
        if "SKEW" in orient or (abs(x1_m - x0_m) > 1e-4 and abs(y1_m - y0_m) > 1e-4):
            secondary_beams.append(bm_rec)
        elif "Y" in orient or abs(x1_m - x0_m) < abs(y1_m - y0_m):
            beams_y.append(bm_rec)
        else:
            beams_x.append(bm_rec)

    # 4. Slabs & Openings (voids)
    v6_slabs = raw.get("slabs_v6") or raw.get("slabs", [])
    slab_tags: List[Dict[str, Any]] = []
    voids: List[Dict[str, Any]] = []
    primary_level_m: Optional[float] = None

    for idx, sl in enumerate(v6_slabs):
        eid = sl.get("element_id") or f"SLAB_{idx+1:03d}"
        mark = sl.get("mark", f"S{idx+1}")
        s_floor = sl.get("floor_id", floor_id)
        thick_mm = float(sl.get("thickness_mm", 120))
        drop_mm = float(sl.get("drop_mm", 0.0))
        level_m = float(sl.get("level_m", 3.800))
        if drop_mm == 0 and primary_level_m is None:
            primary_level_m = level_m

        bpoly = sl.get("boundary_polygon", [])
        if bpoly:
            xmin_mm, ymin_mm, xmax_mm, ymax_mm = _poly_bounds_mm(bpoly)
        else:
            xmin_mm, ymin_mm, xmax_mm, ymax_mm = 0.0, 0.0, 4000.0, 5000.0

        sug = sl.get("tag_suggested_pos") or {
            "x": (xmin_mm + xmax_mm) / 2.0,
            "y": (ymin_mm + ymax_mm) / 2.0,
        }
        sx_m = round(float(sug["x"]) / 1000.0, 4)
        sy_m = round(float(sug["y"]) / 1000.0, 4)

        panel_bounds_m = [
            round(xmin_mm / 1000.0, 4),
            round(ymin_mm / 1000.0, 4),
            round(xmax_mm / 1000.0, 4),
            round(ymax_mm / 1000.0, 4),
        ]
        panel_bounds_mm = [xmin_mm, ymin_mm, xmax_mm, ymax_mm]

        openings_rects_mm: List[List[float]] = []
        for op in sl.get("openings", []):
            op_poly = op.get("polygon", [])
            if op_poly:
                ox0, oy0, ox1, oy1 = _poly_bounds_mm(op_poly)
                openings_rects_mm.append([ox0, oy0, ox1, oy1])
                voids.append({
                    "name": op.get("opening_id", "OPENING"),
                    "type": op.get("type", "MEP_SHAFT"),
                    "x": round((ox0 + ox1) / 2000.0, 4),
                    "y": round((oy0 + oy1) / 2000.0, 4),
                    "w": round((ox1 - ox0) / 1000.0, 4),
                    "h": round((oy1 - oy0) / 1000.0, 4),
                })

        elem = StructuralElement(
            element_id=eid,
            category="SLAB",
            mark=mark,
            floor_id=s_floor,
            section_profile={
                "thickness_mm": int(round(thick_mm)),
                "drop_mm": int(round(drop_mm)),
                "level_m": level_m,
            },
            tag_refs=list(sl.get("tag_refs", [])),
            status="CONTINUOUS",
            metadata={
                "panel_bounds_mm": panel_bounds_mm,
                "openings_mm": openings_rects_mm,
            },
        )
        registry.register(elem)

        if drop_mm > 0:
            drop_str = f"-{drop_mm / 1000.0:.3f}"
            slab_tags.append({
                "element_id": eid,
                "mark": mark,
                "x": sx_m,
                "y": sy_m,
                "label": f"{mark} (h={int(round(thick_mm))})",
                "type": "drop",
                "drop": drop_str,
                "drop_mm": int(round(drop_mm)),
                "thickness_mm": int(round(thick_mm)),
                "level_m": level_m,
                "drop_box_mm": [round(xmax_mm - xmin_mm, 1), round(ymax_mm - ymin_mm, 1)],
                "panel_mm": panel_bounds_m,
                "panel_bounds_mm": panel_bounds_mm,
                "openings_mm": openings_rects_mm,
            })
        else:
            slab_tags.append({
                "element_id": eid,
                "mark": mark,
                "x": sx_m,
                "y": sy_m,
                "label": f"{mark} (h={int(round(thick_mm))})",
                "type": "standard",
                "thickness_mm": int(round(thick_mm)),
                "level_m": level_m,
                "panel_mm": panel_bounds_m,
                "panel_bounds_mm": panel_bounds_mm,
                "openings_mm": openings_rects_mm,
            })

    # 5. Steel members
    for idx, sm in enumerate(raw.get("steel_members", [])):
        eid = sm.get("element_id") or f"STEEL_{idx+1:03d}"
        elem = StructuralElement(
            element_id=eid,
            category="STEEL_MEMBER",
            mark=sm.get("mark", f"SC{idx+1}"),
            floor_id=sm.get("floor_id", "ROOF"),
            section_profile={
                "profile_name": sm.get("profile_name", "H200x200x8x12"),
                "baseplate_spec": sm.get("baseplate_spec", {}),
            },
            status="CONTINUOUS",
            metadata={"capability_declaration": sm.get("capability_declaration", {})},
        )
        registry.register(elem)

    if primary_level_m is None:
        primary_level_m = float(raw.get("slab_level_m", 3.800))

    engine_model: Dict[str, Any] = {
        "_comment": raw.get("_comment", "TEST FIXTURE DATA FOR CLAUDE C1 INTEGRATION - NOT FOR ACTUAL CONSTRUCTION USE"),
        "project_name": raw.get("project_name", "DCE_V6_C1_INTEGRATION_TEST_MODEL"),
        "version": raw.get("version", "6.0.0"),
        "L_total": round(L_total, 4),
        "B_total": round(B_total, 4),
        "grid_x": grid_x,
        "grid_y": grid_y,
        "columns": engine_columns,
        "shear_walls": list(raw.get("shear_walls", [])),
        "beams_x": beams_x,
        "beams_y": beams_y,
        "secondary_beams": secondary_beams,
        "main_beams": beams_x + beams_y,
        "slab_tags": slab_tags,
        "voids": voids,
        "site_data": raw.get("site_data", {
            "lot_w": round(L_total + 6.0, 2),
            "lot_h": round(B_total + 6.0, 2),
            "bldg_offset_x": 3.0,
            "bldg_offset_y": 3.0,
            "setback_front": 3.0,
            "setback_rear": 1.5,
            "setback_side": 1.5,
            "vn2000_origin_x": 1198200.000,
            "vn2000_origin_y": 604300.000,
            "roads": [],
            "ramps": [],
        }),
        "slab_level_m": primary_level_m,
        "slab_level_pos_m": round(L_total / 2.0, 3),
        "slab_level_pos_m_y": round(B_total / 2.0, 3),
        "sheet_scale_label": str(raw.get("sheet_scale_label", "1/100")),
        "section_cuts": list(raw.get("section_cuts", [
            {
                "name": "1-1",
                "x": 2.0,
                "y": 0.0,
                "scale_label": "1/20",
                "detail_ref": {"sheet_number": "KC.23", "drawing_id": "DETAIL_BEAM_D1A", "target_exists": True},
            }
        ])),
        # Preserve original v6 semantic payload for direct inspection
        "grid_system": grid_sys,
        "floors": list(raw.get("floors", [])),
        "columns_v6": v6_cols,
        "beams_v6": v6_beams,
        "slabs_v6": v6_slabs,
        "steel_members": list(raw.get("steel_members", [])),
    }
    return engine_model, registry


def load_c1_fixture(
    fixture_path: Optional[Union[str, Path]] = None,
    floor_id: str = "TANG_2",
) -> Tuple[Dict[str, Any], CadElementRegistry]:
    """Convenience loader tra ve (engine_model_dict, populated_registry) tu c1_sample_model.json."""
    return c1_fixture_to_engine_model(fixture_path or DEFAULT_C1_FIXTURE_PATH, floor_id=floor_id)

