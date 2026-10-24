#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_sprint2_conflict_control.py — Bộ kiểm thử tự động cho Sprint 2 (ARGON SPEC v8.0)
Bộ đọc hồ sơ đầu vào (ingest_project_docs) & Kiểm soát xung đột chéo 8 luật (CDC-01 đến CDC-08).
"""

import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
import os
import json
import unittest
from pathlib import Path

# Thêm đường dẫn SKILL_VERIFY vào sys.path
TESTS_DIR = Path(__file__).resolve().parent
AGENTS_ROOT = TESTS_DIR.parent
SKILLS_ROOT = AGENTS_ROOT / "skills"

sys.path.insert(0, str(SKILLS_ROOT / "SKILL_VERIFY" / "scripts"))

import cross_doc_conflict_checker as cdc
import ingest_project_docs as ipd


class TestSprint2ConflictControl(unittest.TestCase):

    def setUp(self):
        """Thiết lập fixture dự án thực tế 'Nhà Nguyên - Trương Công Định'"""
        self.project_graph = {
            "project_name": "Nhà Nguyên - Trương Công Định",
            "project_id": "PRJ-TCD-2026",
            "version": "1.0.0",
            "required_disciplines": ["ARCH", "STRUC", "MEP_ELEC", "MEP_PLUMB"],
            "documents_registry": {
                "ARCH": {
                    "stage": "S3",  # KT ở S3 (TKCS)
                    "present": True,
                    "doc_ref": "KT-01-TCD"
                },
                "STRUC": {
                    "stage": "S4",  # KC ở S4 (TKKT / BVTC) -> CDC-01
                    "present": True,
                    "doc_ref": "KC-01-TCD"
                },
                "MEP_ELEC": {
                    "stage": "S3",
                    "present": True,
                    "doc_ref": "MEP-E-01"
                },
                "MEP_PLUMB": {
                    "present": False  # Thiếu Cấp thoát nước -> CDC-02
                }
            },
            "materials": {
                "general_notes": {
                    "concrete_grade": "M250",  # Ký hiệu cũ M250 -> CDC-03 WARNING
                    "source_doc": "Bản vẽ Ghi chú chung KC"
                },
                "boq": {
                    "concrete_grade": "M300",  # Khác M250/B20 -> CDC-03 CRITICAL
                    "source_doc": "Dự toán BOQ"
                }
            },
            "grids_and_levels": {
                "total_width_x_mm": {
                    "STRUC": 16800,
                    "ARCH": 16800,
                    "MEP": 18000  # Lệch 1200mm -> CDC-05 MAJOR
                },
                "story_levels": [
                    {
                        "story": "Tầng 1",
                        "z_struc_mm": 0,
                        "z_arch_mm": 50,
                        "finish_thickness_mm": 50
                    },
                    {
                        "story": "Tầng 2",
                        "z_struc_mm": 3850,
                        "z_arch_mm": 3900,  # KT 3900 - 0 = 3900 != 3850 -> lệch 50mm -> CDC-04 CRITICAL
                        "finish_thickness_mm": 0
                    }
                ]
            },
            "elements": {
                "columns": [
                    {
                        "id": "C1",
                        "section": "200x200",
                        "stories_present": ["T1", "T2"],
                        "has_foundation": True,
                        "in_arch_plan": True
                    },
                    {
                        "id": "CC1",  # Cột mồ côi chỉ có T2, không móng -> CDC-06 MAJOR
                        "section": "200x200",
                        "stories_present": ["T2"],
                        "has_foundation": False,
                        "in_arch_plan": False
                    },
                    {
                        "id": "CC3",  # Cột mồ côi chỉ có T2, không móng -> CDC-06 MAJOR
                        "section": "200x200",
                        "stories_present": ["T2"],
                        "has_foundation": False,
                        "in_arch_plan": False
                    }
                ],
                "beams": [
                    {
                        "id": "D1X1*",
                        "section": "250x450",
                        "story": "Tầng 2",
                        "story_elevation_mm": 3850,
                        "h_mm": 450,
                        "ceiling_aff_mm": 3100,  # Đáy dầm = 3850 - 450 = 3400 -> MEP = 3400 - 3100 = 300 < 450mm -> CDC-07 MAJOR
                        "mep_clearance_req_mm": 450
                    }
                ]
            },
            "geotech": {
                "gwt_m": -1.5,
                "pile_tip_elev_m": -12.0,
                "pile_tip_layer_spt": 8  # N_SPT = 8 < 15 -> CDC-08 CRITICAL
            }
        }

    def test_2_1_cross_doc_conflict_checker_all_rules(self):
        """Test 2.1: Kiểm tra chạy 8 luật xung đột trên hồ sơ thực tế Nhà Nguyên"""
        result = cdc.run_conflict_checks(self.project_graph)

        self.assertEqual(result["Overall_Status"], "CRITICAL")
        summary = result["Summary"]
        self.assertGreater(summary["Critical_Count"], 0)
        self.assertGreater(summary["Major_Count"], 0)
        self.assertGreater(summary["Warning_Count"], 0)

        rule_ids = [iss["Rule_ID"] for iss in result["Issues"]]

        # Kiểm tra từng luật CDC
        self.assertIn("CDC-01", rule_ids, "Phải bắt lỗi CDC-01: KC ở S4 > KT ở S3")
        self.assertIn("CDC-02", rule_ids, "Phải bắt lỗi CDC-02: Thiếu MEP_PLUMB")
        self.assertIn("CDC-03", rule_ids, "Phải bắt lỗi CDC-03: M250 vs M300 và ký hiệu mác cũ")
        self.assertIn("CDC-04", rule_ids, "Phải bắt lỗi CDC-04: Lệch cao độ sàn Tầng 2 50mm")
        self.assertIn("CDC-05", rule_ids, "Phải bắt lỗi CDC-05: Lưới trục MEP lệch 1200mm")
        self.assertIn("CDC-06", rule_ids, "Phải bắt lỗi CDC-06: Cột mồ côi CC1, CC3")
        self.assertIn("CDC-07", rule_ids, "Phải bắt lỗi CDC-07: Không gian MEP dầm D1X1* thiếu")
        self.assertIn("CDC-08", rule_ids, "Phải bắt lỗi CDC-08: Mũi cọc đặt trong lớp đất N_SPT=8 < 15")

        # Kiểm tra Markdown report generator
        md_rep = cdc.format_markdown_report(result)
        self.assertIn("BÁO CÁO KIỂM SOÁT XUNG ĐỘT HỒ SƠ CHÉO", md_rep)
        self.assertIn("Nhà Nguyên - Trương Công Định", md_rep)
        self.assertIn("CRITICAL", md_rep)

    def test_2_2_ingest_project_docs_adapters(self):
        """Test 2.2: Kiểm tra các adapter đọc dữ liệu của ingest_project_docs.py"""
        # Test BOQ text parser
        boq_data = {
            "text": "Bê tông lót móng M150, Bê tông dầm sàn M250 đá 1x2, Thép thanh vằn CB400-V đường kính D10-D25"
        }
        boq_res = ipd.parse_boq_summary(boq_data)
        self.assertEqual(boq_res["concrete_grade"], "M250")
        self.assertTrue("CB400" in boq_res["rebar_main"])

        # Test FEM mock parser
        fem_mock = {
            "Story_Definitions": [
                {"Story": "Story1", "Elevation": 3850},
                {"Story": "Story2", "Elevation": 7200}
            ],
            "Material_Properties": {
                "Concrete_Grade": "B25"
            }
        }
        fem_res = ipd.parse_fem_tables(fem_mock)
        self.assertEqual(len(fem_res["story_levels"]), 2)
        self.assertEqual(fem_res["story_levels"][0]["z_fem_mm"], 3850)
        self.assertEqual(fem_res["materials"]["fem_model"]["concrete_grade"], "B25")

        # Test Geotech parser
        geo_mock = {
            "gwt_m": -2.0,
            "pile_tip_elev_m": -15.5,
            "pile_tip_layer_spt": 25
        }
        geo_res = ipd.parse_geotech_summary(geo_mock)
        self.assertEqual(geo_res["gwt_m"], -2.0)
        self.assertEqual(geo_res["pile_tip_elev_m"], -15.5)
        self.assertEqual(geo_res["pile_tip_layer_spt"], 25)

        # Test build_truth_graph
        graph = ipd.build_truth_graph(
            project_name="Du An Test",
            documents_registry={"STRUC": {"stage": "S4"}},
            geotech=geo_res
        )
        self.assertEqual(graph["project_name"], "Du An Test")
        self.assertEqual(graph["geotech"]["pile_tip_elev_m"], -15.5)

    def test_2_3_clean_graph_passes_checks(self):
        """Test 2.3: Một đồ thị sự thật chuẩn mực (không lỗi) phải đạt PASS"""
        clean_graph = {
            "project_name": "Tòa Nhà Hoàn Hảo",
            "required_disciplines": ["ARCH", "STRUC"],
            "documents_registry": {
                "ARCH": {"stage": "S4", "present": True},
                "STRUC": {"stage": "S4", "present": True}
            },
            "materials": {
                "notes": {"concrete_grade": "B25"},
                "fem": {"concrete_grade": "B25"}
            },
            "grids_and_levels": {
                "total_width_x_mm": {"STRUC": 12000, "ARCH": 12000},
                "story_levels": [
                    {"story": "T1", "z_struc_mm": 0, "z_arch_mm": 50, "finish_thickness_mm": 50}
                ]
            },
            "elements": {
                "columns": [
                    {"id": "C1", "stories_present": ["T1"], "has_foundation": True, "in_arch_plan": True}
                ],
                "beams": [
                    {"id": "B1", "story_elevation_mm": 3600, "h_mm": 400, "ceiling_aff_mm": 2700, "mep_clearance_req_mm": 450} # 3600 - 400 = 3200, 3200 - 2700 = 500 >= 450
                ]
            },
            "geotech": {
                "pile_tip_elev_m": -18.0,
                "pile_tip_layer_spt": 35
            }
        }

        result = cdc.run_conflict_checks(clean_graph)
        self.assertEqual(result["Overall_Status"], "PASS")
        self.assertEqual(result["Summary"]["Total_Issues"], 0)


if __name__ == "__main__":
    unittest.main()
