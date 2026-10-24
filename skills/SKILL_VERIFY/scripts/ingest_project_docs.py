#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ingest_project_docs.py — Bộ nạp dữ liệu đa nguồn cho Kiểm soát Xung đột Hồ sơ (SKILL_VERIFY)
Đọc và chuẩn hóa dữ liệu từ:
  1. Bảng xuất ETABS / SAFE (parse_fem_tables)
  2. Dự toán BOQ Excel / CSV (parse_boq_summary)
  3. Bản vẽ KC / KT / MEP (parse_drawing_metadata)
  4. Báo cáo Địa chất công trình (parse_geotech_summary)
Hợp nhất thành Single Source of Truth: project_truth_graph.json tuân thủ schema project_truth_graph.schema.json.
"""

import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
import os
import json
import re
import csv
import argparse
from datetime import datetime
from pathlib import Path


def parse_fem_tables(fem_source):
    """
    Adapter 1: Đọc thông số mô hình FEM (ETABS/SAFE).
    Hỗ trợ file JSON, CSV, hoặc dict data.
    Trích xuất: cao độ tầng, cấp độ bền bê tông (f'c, E_b), tiết diện phần tử.
    """
    data = {}
    if isinstance(fem_source, dict):
        data = fem_source
    elif isinstance(fem_source, (str, Path)):
        p = Path(fem_source)
        if not p.exists():
            return {"error": f"File FEM không tồn tại: {fem_source}"}
        if p.suffix.lower() == ".json":
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
        elif p.suffix.lower() == ".csv":
            # Giả định CSV xuất bảng Story hoặc Section
            with open(p, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                data = {"rows": list(reader)}

    # Chuẩn hóa đầu ra
    result = {
        "story_levels": [],
        "materials": {},
        "elements": {"columns": [], "beams": []}
    }

    # Đọc story definitions
    stories = data.get("Story_Definitions", data.get("stories", []))
    for s in stories:
        story_name = s.get("Story") or s.get("Name") or s.get("story", "")
        elev = s.get("Elevation") or s.get("elevation") or s.get("z_mm", 0)
        try:
            elev_val = float(elev)
        except (ValueError, TypeError):
            elev_val = 0.0
        result["story_levels"].append({
            "story": story_name,
            "z_fem_mm": elev_val
        })

    # Đọc vật liệu bê tông
    mats = data.get("Material_Properties", data.get("materials", {}))
    if isinstance(mats, dict):
        conc_grade = mats.get("Concrete_Grade") or mats.get("concrete_grade")
        if conc_grade:
            result["materials"]["fem_model"] = {
                "concrete_grade": str(conc_grade).strip(),
                "source_doc": "ETABS/SAFE Model"
            }
    elif isinstance(mats, list):
        for m in mats:
            if "CONC" in str(m.get("Type", "")).upper() or "B" in str(m.get("Name", "")).upper():
                result["materials"]["fem_model"] = {
                    "concrete_grade": str(m.get("Name", "")).strip(),
                    "source_doc": "ETABS/SAFE Model"
                }
                break

    return result


def parse_boq_summary(boq_source):
    """
    Adapter 2: Đọc bảng dự toán BOQ Excel/CSV/JSON.
    Trích xuất mác bê tông, nhóm cốt thép và danh mục vật tư.
    """
    data = {}
    if isinstance(boq_source, dict):
        data = boq_source
    elif isinstance(boq_source, (str, Path)):
        p = Path(boq_source)
        if not p.exists():
            return {"error": f"File BOQ không tồn tại: {boq_source}"}
        if p.suffix.lower() == ".json":
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
        elif p.suffix.lower() in [".csv", ".txt"]:
            with open(p, "r", encoding="utf-8") as f:
                content = f.read()
                data = {"text": content}

    result = {
        "concrete_grade": None,
        "rebar_main": None,
        "rebar_stirrup": None,
        "items": []
    }

    # Bóc tách qua text hoặc items
    full_text = ""
    if "text" in data:
        full_text = data["text"]
    elif "items" in data:
        for it in data["items"]:
            desc = it.get("description", "") or it.get("Ten_Cong_Tac", "")
            full_text += f"\n{desc}"
    else:
        full_text = json.dumps(data, ensure_ascii=False)

    # Regex nhận dạng mác bê tông trong BOQ: M200, M250, M300, M350, B20, B22.5, B25, B30
    matches = re.findall(r"\b(B12\.5|B15|B20|B22\.5|B25|B30|B35|B40|B45|B50|B55|B60|M150|M200|M250|M300|M350|M400|M450|M500)\b", full_text, re.IGNORECASE)
    if matches:
        structural_matches = [m.upper() for m in matches if m.upper() not in ["M100", "M150", "B7.5", "B10"]]
        if structural_matches:
            result["concrete_grade"] = structural_matches[0]
        else:
            result["concrete_grade"] = matches[0].upper()

    # Regex nhận dạng cốt thép trong BOQ: CB240-T, CB300-V, CB400-V, CB500-V, AII, AIII
    rebar_match = re.search(r"\b(CB240-?T?|CB300-?V?|CB400-?V?|CB500-?V?|A-?II|A-?III)\b", full_text, re.IGNORECASE)
    if rebar_match:
        result["rebar_main"] = rebar_match.group(1).upper()

    return result


def parse_drawing_metadata(drawing_source):
    """
    Adapter 3: Đọc siêu dữ liệu và hình học từ bản vẽ KC, KT, MEP.
    Hỗ trợ file JSON/Dict đã trích xuất từ CAD/BIM/PDF hoặc trực tiếp file bản vẽ.
    """
    data = {}
    if isinstance(drawing_source, dict):
        data = drawing_source
    elif isinstance(drawing_source, (str, Path)):
        p = Path(drawing_source)
        if not p.exists():
            return {"error": f"File bản vẽ không tồn tại: {drawing_source}"}
        if p.suffix.lower() == ".json":
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)

    return data


def parse_geotech_summary(geotech_source):
    """
    Adapter 4: Đọc số liệu khảo sát địa chất công trình.
    Trích xuất: mực nước ngầm GWT, danh sách lớp đất (N_SPT, c, phi), cao độ mũi cọc và N_SPT lớp mũi cọc.
    """
    data = {}
    if isinstance(geotech_source, dict):
        data = geotech_source
    elif isinstance(geotech_source, (str, Path)):
        p = Path(geotech_source)
        if not p.exists():
            return {"error": f"File địa chất không tồn tại: {geotech_source}"}
        if p.suffix.lower() == ".json":
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)

    result = {
        "gwt_m": data.get("gwt_m") or data.get("GWT") or data.get("water_table_m"),
        "pile_tip_elev_m": data.get("pile_tip_elev_m") or data.get("pile_tip_elev"),
        "pile_tip_layer_spt": data.get("pile_tip_layer_spt") or data.get("pile_tip_spt"),
        "soil_layers": data.get("soil_layers", [])
    }
    return result


def build_truth_graph(project_name: str,
                      documents_registry: dict = None,
                      materials: dict = None,
                      grids_and_levels: dict = None,
                      elements: dict = None,
                      geotech: dict = None,
                      required_disciplines: list = None) -> dict:
    """
    Tập hợp và chuẩn hóa tất cả các nguồn dữ liệu thành đồ thị sự thật Project Truth Graph.
    """
    graph = {
        "project_name": project_name,
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "required_disciplines": required_disciplines or ["ARCH", "STRUC", "MEP_ELEC", "MEP_PLUMB"],
        "documents_registry": documents_registry or {},
        "materials": materials or {},
        "grids_and_levels": grids_and_levels or {
            "total_width_x_mm": {},
            "total_length_y_mm": {},
            "story_levels": []
        },
        "elements": elements or {
            "columns": [],
            "beams": [],
            "slabs": []
        },
        "geotech": geotech or {}
    }
    return graph


def main():
    parser = argparse.ArgumentParser(description="Ingest multi-source project documents into Project Truth Graph")
    parser.add_argument("--project", default="Du An Mau", help="Tên dự án")
    parser.add_argument("--fem", help="File dữ liệu mô hình ETABS/SAFE (.json, .csv)")
    parser.add_argument("--boq", help="File dự toán BOQ (.json, .csv, .txt)")
    parser.add_argument("--drawing", help="File dữ liệu trích xuất bản vẽ (.json)")
    parser.add_argument("--geotech", help="File dữ liệu địa chất (.json)")
    parser.add_argument("--output", help="Đường dẫn file JSON đồ thị sự thật xuất ra")

    args = parser.parse_args()

    materials = {}
    grids_and_levels = {"total_width_x_mm": {}, "total_length_y_mm": {}, "story_levels": []}
    elements = {"columns": [], "beams": [], "slabs": []}
    geotech_data = {}
    docs_reg = {}

    if args.fem:
        fem_res = parse_fem_tables(args.fem)
        if "materials" in fem_res:
            materials.update(fem_res["materials"])
        for fs in fem_res.get("story_levels", []):
            s_name = fs.get("story", "")
            z_fem = fs.get("z_fem_mm")
            found = False
            for item in grids_and_levels["story_levels"]:
                if item.get("story") == s_name or item.get("story", "").lower() == s_name.lower():
                    item["z_fem_mm"] = z_fem
                    found = True
                    break
            if not found:
                grids_and_levels["story_levels"].append({
                    "story": s_name,
                    "z_fem_mm": z_fem
                })
        docs_reg["FEM_MODEL"] = {"stage": "S4", "present": True, "file_path": str(args.fem)}

    if args.boq:
        boq_res = parse_boq_summary(args.boq)
        if boq_res.get("concrete_grade"):
            materials["boq"] = {
                "concrete_grade": boq_res["concrete_grade"],
                "rebar_main": boq_res.get("rebar_main"),
                "source_doc": "BOQ"
            }
        docs_reg["BOQ"] = {"stage": "S4", "present": True, "file_path": str(args.boq)}

    if args.drawing:
        drw_res = parse_drawing_metadata(args.drawing)
        if "documents_registry" in drw_res:
            docs_reg.update(drw_res["documents_registry"])
        if "materials" in drw_res:
            materials.update(drw_res["materials"])
        if "grids_and_levels" in drw_res:
            drw_gl = drw_res["grids_and_levels"]
            for k, v in drw_gl.items():
                if k == "story_levels" and isinstance(v, list):
                    for drw_item in v:
                        s_name = drw_item.get("story", "")
                        found = False
                        for item in grids_and_levels["story_levels"]:
                            if item.get("story") == s_name or item.get("story", "").lower() == s_name.lower():
                                z_fem_val = item.get("z_fem_mm")
                                item.update(drw_item)
                                if z_fem_val is not None and "z_fem_mm" not in drw_item:
                                    item["z_fem_mm"] = z_fem_val
                                found = True
                                break
                        if not found:
                            grids_and_levels["story_levels"].append(dict(drw_item))
                elif isinstance(v, dict) and isinstance(grids_and_levels.get(k), dict):
                    grids_and_levels[k].update(v)
                else:
                    grids_and_levels[k] = v
        if "elements" in drw_res:
            elements.update(drw_res["elements"])

    if args.geotech:
        geotech_data = parse_geotech_summary(args.geotech)
        docs_reg["GEOTECH"] = {"stage": "S3", "present": True, "file_path": str(args.geotech)}

    graph = build_truth_graph(
        project_name=args.project,
        documents_registry=docs_reg,
        materials=materials,
        grids_and_levels=grids_and_levels,
        elements=elements,
        geotech=geotech_data
    )

    out_json = json.dumps(graph, indent=2, ensure_ascii=False)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out_json)
        print(f"Đã xuất Project Truth Graph: {args.output}")
    else:
        print(out_json)


if __name__ == "__main__":
    main()
