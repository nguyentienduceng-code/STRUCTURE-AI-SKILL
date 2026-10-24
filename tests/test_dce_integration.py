"""
test_dce_integration.py — Unit & Integration Test Suite for DCE Pro Integration
=================================================================================
Sprint 3 · Phase 3 · Test Suite 10

Kiểm thử toàn diện 4 nhiệm vụ:
1. DceRulesRegistry (1.239 txt configs + DLL reflection + Form 2.dxf assets)
2. CadBridge DCE Engine (Form 2.dxf template, TK1..TK44 rebar schedule, symbols)
3. RebarCuttingOptimizer (11.7m 1D-CSP, old_stock reuse, L_lap=40d, stagger >= 10d)
4. ETABS COM Reader DCE Extended (Joint reactions, story drifts, pier forces, update sections)
"""

import sys
import os
import json
import unittest
from pathlib import Path

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

AGENTS_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AGENTS_ROOT / "tools"))
sys.path.insert(0, str(AGENTS_ROOT / "skills" / "Structural_Design_Engineer" / "scripts"))

from dce_rules_registry import DceRulesRegistry, DEFAULT_OUTPUT_JSON
from cad_bridge import (
    draw_beam_section,
    insert_dce_rebar_schedule,
    insert_dce_truc,
    insert_dce_caotrinh,
    insert_dce_tencaukien,
    insert_dce_khtsh,
    EzdxfDrawer,
    parse_rebar_string,
    unit_weight_kg_m,
)
from rebar_cutting_optimizer import RebarCuttingOptimizer
from etabs_com_reader import read_etabs, _demo_payload


class TestDceRulesRegistry(unittest.TestCase):
    """Kiểm thử Nhiệm vụ 1: DceRulesRegistry & dce_engineering_rules.json."""

    @classmethod
    def setUpClass(cls):
        cls.registry = DceRulesRegistry.get_instance(DEFAULT_OUTPUT_JSON)

    def test_01_registry_loaded(self):
        self.assertIsNotNone(self.registry.data)
        self.assertIn("metadata", self.registry.data)
        self.assertIn("rc_detailing_rules", self.registry.data)
        self.assertIn("viewport_packing_rules", self.registry.data)
        self.assertIn("steel_sections_catalog", self.registry.data)
        self.assertIn("steel_bolt_rules", self.registry.data)
        self.assertIn("steel_layers_and_blocks", self.registry.data)
        self.assertIn("revit_family_mappings", self.registry.data)

    def test_02_rc_detailing_rules(self):
        lap_mult = self.registry.get_rc_rule("standard_lap_multiplier")
        self.assertEqual(lap_mult, 40)
        stock_len = self.registry.get_rc_rule("standard_stock_length_mm")
        self.assertEqual(stock_len, 11700)
        self.assertTrue(self.registry.get_rc_rule("cat_sole_cung_mot_lop"))

    def test_03_steel_bolt_rules(self):
        m20 = self.registry.get_bolt_spec("M20")
        self.assertIsInstance(m20, dict)
        self.assertIn("B", m20)
        self.assertIn("C", m20)
        blng1 = self.registry.get_bolt_edge_pitch(1)
        self.assertGreater(blng1, 0)
        blnw1 = self.registry.get_bolt_plate_width(1)
        self.assertGreater(blnw1, 0)

    def test_04_steel_sections_catalog(self):
        w_i1 = self.registry.get_steel_weight("I", 1)
        self.assertGreater(w_i1, 0)
        w_u1 = self.registry.get_steel_weight("U", 1)
        self.assertGreater(w_u1, 0)

    def test_05_layers_and_blocks_assets(self):
        layers = self.registry.get_dce_layers()
        blocks = self.registry.get_dce_blocks()
        self.assertGreaterEqual(len(layers), 40)
        self.assertGreaterEqual(len(blocks), 44)

    def test_06_bolt_edge_pitch_5_and_m33(self):
        # BLNG5 phải là 200.0 (không bị MD5 hash ghi đè)
        pitch_5 = self.registry.get_bolt_edge_pitch(5)
        self.assertEqual(pitch_5, 200.0)
        # M33 bolt spec B=70, P=200 (số nguyên/số thực)
        m33 = self.registry.get_bolt_spec("M33")
        self.assertEqual(int(m33.get("B", 0)), 70)
        self.assertEqual(int(m33.get("P", 0)), 200)

    def test_07_steel_sections_catalog_dimensions(self):
        # Catalog phải chứa đầy đủ h_mm, b_mm, tw_mm, tf_mm
        sec_i1 = self.registry.get_steel_section("I", 1)
        self.assertIn("h_mm", sec_i1)
        self.assertIn("b_mm", sec_i1)
        self.assertIn("tw_mm", sec_i1)
        self.assertIn("tf_mm", sec_i1)
        self.assertEqual(sec_i1["h_mm"], 150.0)
        self.assertEqual(sec_i1["b_mm"], 75.0)
        self.assertEqual(sec_i1["tw_mm"], 5.0)
        self.assertEqual(sec_i1["tf_mm"], 7.0)


class TestCadBridgeDceEngine(unittest.TestCase):
    """Kiểm thử Nhiệm vụ 2: Engine vẽ theo Form & Block TK1..TK44 của DCE."""

    def setUp(self):
        import tempfile
        self.scratch_dir = Path(tempfile.gettempdir()) / "antigravity_scratch"
        self.scratch_dir.mkdir(parents=True, exist_ok=True)

    def test_01_unit_weight_tcvn(self):
        # D10 = ~0.617, D20 = ~2.466, D25 = ~3.853
        self.assertAlmostEqual(unit_weight_kg_m(10.0), 0.617, places=2)
        self.assertAlmostEqual(unit_weight_kg_m(20.0), 2.466, places=2)
        self.assertAlmostEqual(unit_weight_kg_m(25.0), 3.853, places=2)

    def test_02_insert_rebar_schedule_tk(self):
        out_dxf = str(self.scratch_dir / "test_suite_schedule.dxf")
        drawer = EzdxfDrawer(out_dxf)
        items = [
            {"sh": 1, "dk": 25, "shape": "TK1", "dims": {"L": 5800}, "sl": 3, "skc": 1},
            {"sh": 2, "dk": 22, "shape": "TK2", "dims": {"L1": 350, "L2": 4500}, "sl": 2, "skc": 1},
            {"sh": 3, "dk": 10, "shape": "TK9", "dims": {"L1": 240, "L2": 540, "M": 80}, "sl": 30, "skc": 1},
        ]
        res = insert_dce_rebar_schedule(drawer.msp, items, insert_pt=(0, 0))
        drawer.save()

        self.assertEqual(res["status"], "SUCCESS")
        self.assertEqual(res["rows_count"], 3)
        self.assertGreater(res["total_length_m"], 40.0)
        self.assertGreater(res["total_weight_kg"], 80.0)
        self.assertTrue(os.path.exists(out_dxf))

    def test_03_insert_dce_symbols(self):
        out_dxf = str(self.scratch_dir / "test_suite_symbols.dxf")
        drawer = EzdxfDrawer(out_dxf)
        r_truc = insert_dce_truc(drawer.msp, (0, 0), "A")
        r_ct = insert_dce_caotrinh(drawer.msp, (20, 0), "+3.600")
        r_ten = insert_dce_tencaukien(drawer.msp, (50, 0), "DẦM D1", 2)
        r_sh = insert_dce_khtsh(drawer.msp, (80, 0), "1")
        drawer.save()
        self.assertTrue(os.path.exists(out_dxf))

    def test_04_draw_beam_section_with_schedule(self):
        out_dxf = str(self.scratch_dir / "test_suite_beam_full.dxf")
        res = draw_beam_section(
            b=300, h=600, cover=30,
            top_str="3D22", bot_str="3D25", stirrup_str="D10@150",
            output_path=out_dxf,
            with_schedule=True
        )
        self.assertIn("schedule", res)
        self.assertEqual(res["schedule"]["status"], "SUCCESS")
        self.assertEqual(res["schedule"]["rows_count"], 3)
        self.assertTrue(os.path.exists(out_dxf))
        self.assertIn("Standard_Method", res)

    def test_05_tk9_rebar_formula(self):
        # Kiểm tra công thức đai kín TK9: L1=150, L2=350, M=64 -> sumL == 1128
        out_dxf = str(self.scratch_dir / "test_tk9_calc.dxf")
        drawer = EzdxfDrawer(out_dxf)
        items = [
            {"sh": 1, "dk": 8, "shape": "TK9", "dims": {"L1": 150, "L2": 350, "M": 64}, "sl": 1, "skc": 1}
        ]
        res = insert_dce_rebar_schedule(drawer.msp, items, insert_pt=(0, 0))
        drawer.save()
        row = res["rows"][0]
        # sumL = 2*(150 + 350) + 2*64 = 1000 + 128 = 1128
        self.assertEqual(row["sumL_mm"], 1128.0)


class TestRebarCuttingOptimizer(unittest.TestCase):
    """Kiểm thử Nhiệm vụ 3: Tối ưu cắt thép 11.7m & kho thép dư (Bea_ToHopThepV4)."""

    def setUp(self):
        self.optimizer = RebarCuttingOptimizer(
            stock_length=11700.0,
            min_reuse_length=500.0,
            lap_multiplier=40.0,
            min_stagger_offset=10.0,
        )

    def test_01_split_long_bar(self):
        # Thanh 18m D25 -> vượt 11.7m -> cần nối L_lap = 40*25 = 1000mm
        segs = self.optimizer.split_long_bar(total_length=18000.0, dia=25.0)
        self.assertGreaterEqual(len(segs), 2)
        total_cut_len = sum(s["length"] for s in segs)
        self.assertGreater(total_cut_len, 18000.0)  # Có tính chiều dài nối chồng
        self.assertTrue(all(s["length"] <= 11700.0 for s in segs))

    def test_02_optimize_with_old_stock(self):
        bars = [
            {"id": "T1", "length": 4200, "count": 4, "dia": 22},
            {"id": "T2", "length": 5800, "count": 3, "dia": 22},
        ]
        old_stock = [{"length": 4500, "count": 1, "dia": 22}]
        res = self.optimizer.optimize(bars, old_stock)

        summary = res["summary"]
        self.assertEqual(summary["total_old_stock_used"], 1)
        self.assertGreater(summary["total_new_bars_11700"], 0)
        self.assertGreater(summary["overall_yield_efficiency_pct"], 80.0)
        self.assertLess(summary["overall_scrap_waste_pct"], 5.0)

    def test_03_calculation_logs_and_standard_method(self):
        bars = [{"id": "T1", "length": 3000, "count": 3, "dia": 20}]
        res = self.optimizer.optimize(bars)
        self.assertIn("Calculation_Logs", res)
        self.assertGreater(len(res["Calculation_Logs"]), 0)
        self.assertEqual(res["Standard_Method"], "TCVN 5574:2018 + DCE Bea_ToHopThepV4 (1D Cutting Stock Optimizer)")

    def test_04_confidence_score_no_veto(self):
        sys.path.insert(0, str(AGENTS_ROOT / "_SHARED" / "SHARED_CONTEXT"))
        from confidence_score import ConfidenceCalculator
        bars = [{"id": "T1", "length": 4000, "count": 2, "dia": 20}]
        res = self.optimizer.optimize(bars)
        calc = ConfidenceCalculator()
        score = calc.calculate_overall(res)
        self.assertGreaterEqual(score, 0.85)
        self.assertGreater(score, 0.0)  # Không bị VETO
        self.assertEqual(calc.factors["calculation_consistency"]["score"], 1.0)


class TestEtabsComReaderDceExtended(unittest.TestCase):
    """Kiểm thử Nhiệm vụ 4: Mở rộng etabs_com_reader.py theo DCE_Excel.DceEtabs."""

    def test_01_demo_payload_has_all_dce_fields(self):
        payload = _demo_payload()
        self.assertIn("joint_reactions", payload)
        self.assertIn("story_drifts", payload)
        self.assertIn("pier_forces", payload)
        self.assertGreater(len(payload["joint_reactions"]), 0)
        self.assertGreater(len(payload["story_drifts"]), 0)
        self.assertGreater(len(payload["pier_forces"]), 0)

    def test_02_read_etabs_demo(self):
        res = read_etabs(force_demo=True)
        self.assertIn("joint_reactions", res)
        self.assertIn("story_drifts", res)
        self.assertIn("pier_forces", res)
        self.assertIn("Standard_Method", res)
        self.assertIn("Calculation_Logs", res)
        self.assertIn("DCE_Excel.DceEtabs API", res["Standard_Method"])

        # Kiểm tra chi tiết giá trị phản lực móng
        jr = res["joint_reactions"][0]
        self.assertIn("Fz_kN", jr)
        self.assertGreater(jr["Fz_kN"], 1000.0)

        # Kiểm tra chuyển vị tầng
        sd = res["story_drifts"][0]
        self.assertIn("drift", sd)
        self.assertGreater(sd["drift"], 0.0)

        # Kiểm tra nội lực vách Pier
        pf = res["pier_forces"][0]
        self.assertIn("P_kN", pf)
        self.assertIn("V2_kN", pf)
        self.assertIn("M3_kNm", pf)

    def test_03_update_sections_simulation(self):
        updates = {"B1-S1": "BEAM_B400x800", "C1-S1": "COL_C700x700"}
        res = read_etabs(force_demo=True, update_sections=updates)
        self.assertIn("updated_frames", res)
        self.assertIn("B1-S1", res["updated_frames"])
        self.assertEqual(res["updated_frames"]["B1-S1"]["new_section"], "BEAM_B400x800")
        self.assertTrue(res["updated_frames"]["B1-S1"]["success"])


def suite():
    s = unittest.TestSuite()
    s.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(TestDceRulesRegistry))
    s.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(TestCadBridgeDceEngine))
    s.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(TestRebarCuttingOptimizer))
    s.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(TestEtabsComReaderDceExtended))
    return s


if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite())
    passed = result.testsRun - len(result.failures) - len(result.errors)
    failed = len(result.failures) + len(result.errors)
    total = result.testsRun
    print("\n" + "=" * 50)
    print(f"Passed : {passed}")
    print(f"Failed : {failed}")
    print(f"Total  : {total}")
    print("=" * 50)
    sys.exit(0 if result.wasSuccessful() else 1)
