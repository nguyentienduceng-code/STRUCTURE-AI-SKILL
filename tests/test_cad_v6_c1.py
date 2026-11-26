# -*- coding: utf-8 -*-
"""C1 — renderer/tag placement integration for CAD semantics v6."""
import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CAD = ROOT / "skills" / "Technical_Illustrator" / "cad_integration"
ENGINE = CAD / "cad_plan_engine.py"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, str(path))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


class TestC1TagPlanner(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = load(CAD / "cad_tag_placement.py", "c1_tag_placement").TagPlacementPlanner(
            text_height_mm=200, gap_mm=100, leader_length_mm=1000)

    def test_beam_orientation_and_manual_override(self):
        p = self.p.plan_beam_tag("D1", 0, 0, 10000, 0, element_id="BM_1")
        self.assertEqual(p.rotation_deg, 0)
        self.assertEqual(p.strategy, "direct")
        self.assertEqual((p.element_id, p.view_id), ("BM_1", "model"))
        q = load(CAD / "cad_tag_placement.py", "c1_tag_placement_2").TagPlacementPlanner(
            text_height_mm=200, gap_mm=100, overrides={("BM_1", "KC03"): (50, -25)})
        r = q.plan_beam_tag("D1", 0, 0, 10000, 0, element_id="BM_1", view_id="KC03")
        self.assertAlmostEqual(r.x - p.x, 50, delta=1)
        self.assertAlmostEqual(r.y - p.y, -25, delta=1)

    def test_slab_tag_stays_inside_and_avoids_opening(self):
        p = self.p.plan_slab_tag("S1 h=180", (0, 0, 10000, 8000),
                                 openings=[(4000, 3000, 6000, 5000)], element_id="S1")
        self.assertTrue(0 <= p.x <= 10000 and 0 <= p.y <= 8000)
        self.assertNotEqual(p.strategy, "leader")

    def test_leader_when_all_slots_blocked(self):
        obs = [(-5000, -5000, 15000, 15000)]
        p = self.p.plan_beam_tag("D1", 0, 0, 1000, 0, obstacles=obs, element_id="BM")
        self.assertIn(p.strategy, ("leader", "fallback_center"))
        if p.strategy == "leader":
            self.assertEqual(p.leader_to, (500.0, 0.0))


class TestC1V6Engine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cpe = load(ENGINE, "c1_engine")
        cls.regmod = load(CAD / "cad_element_registry.py", "c1_registry")
        cls.tmp = Path(tempfile.mkdtemp(prefix="c1_v6_"))

    @classmethod
    def tearDownClass(cls):
        import shutil
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def export(self, model):
        reg = self.regmod.CadElementRegistry("C1_FIXTURE")
        out = self.tmp / f"{len(list(self.tmp.glob('*.dxf')))}.dxf"
        eng = self.cpe.DcePlanEngine(model=model, v6=True, element_registry=reg)
        with contextlib.redirect_stdout(io.StringIO()):
            eng.setup().render_sheet_kc03().save_v6(str(out))
        return out, eng, reg

    def test_v6_registry_and_sidecar(self):
        model = self.cpe.build_structural_model()
        out, eng, reg = self.export(model)
        self.assertTrue(out.is_file())
        self.assertEqual(eng.v6, True)
        # Vòng định danh 2B: registry giờ chứa TOÀN BỘ cấu kiện mang XData
        # (dầm + cột + vách), không chỉ dầm như trước. Đếm đúng theo model để
        # giữ bất biến "mọi entity có DCE_ELEMENT_ID đều có registry element khớp".
        expected_ids = (len(model["beams_x"] + model["beams_y"] + model["secondary_beams"])
                       + len(model["columns"]) + len(model["shear_walls"]))
        self.assertEqual(len(reg.elements), expected_ids)
        side = json.loads(out.with_suffix(".dce_audit.json").read_text(encoding="utf-8"))
        self.assertEqual(side["v6_status"], "OK_V6")
        self.assertEqual(side["element_registry"]["total_elements"], len(reg.elements))
        self.assertEqual(reg.validate_integrity()["total_registered"], len(reg.elements))

    def test_v6_registry_content_oracle(self):
        """Oracle NỘI DUNG registry (không chỉ đếm) — bảo đảm 3 điều của việc 2B:
        (a) mọi element_id DETERMINISTIC, KHÔNG UUID;
        (b) KHÔNG có duplicate-key bị silently overwrite (dict elements[eid]=elem);
        (c) sidecar total_elements == len(reg.elements) VÀ bộ key 1-1 (không drift).
        Chốt theo định danh nghiệp vụ, không theo hình học.
        """
        model = self.cpe.build_structural_model()
        out, eng, reg = self.export(model)
        expected_ids = (len(model["beams_x"] + model["beams_y"] + model["secondary_beams"])
                       + len(model["columns"]) + len(model["shear_walls"]))

        # (a) KHÔNG UUID + phải là định danh nghiệp vụ (tiền tố cấu kiện),
        #    không bịa/hàng đợi ngẫu nhiên. Kiên định với naming sau này:
        #    chỉ bắt tiền tố, không pin toàn bộ format.
        import re
        uuid_re = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
                             re.IGNORECASE)
        bad_uuid = [k for k in reg.elements if uuid_re.match(k)]
        self.assertEqual(bad_uuid, [], "element_id UUID bất ngờ: %r" % bad_uuid)
        structural_prefix = ("COL_", "WALL_", "BEAM_", "BM_")
        bad_prefix = [k for k in reg.elements
                      if not k or not k.startswith(structural_prefix)]
        self.assertEqual(bad_prefix, [],
                         "element_id không mang tiền tố cấu kiện: %r" % bad_prefix)

        # (b) KHÔNG duplicate-key bị silently overwrite.
        #     register() ghi collision (2 phân tử KHÁC NHAU cùng eid) vào list;
        #     đồng thời dict Python tự loại key trùng, nên bộ key phải đúng số
        #     cấu kiện vật lý model (112) — mất 1 va chạm => thiếu 1 key => fail.
        self.assertEqual(reg.register_collisions, [],
                         "VA CHẠM element_id (2 phân tử khác nhau cùng key): %r"
                         % reg.register_collisions)
        self.assertEqual(len(set(reg.elements)), len(reg.elements))
        self.assertEqual(len(reg.elements), expected_ids,
                         "registry thiếu cấu kiện (overwrite/lỗi đếm): %d != %d"
                         % (len(reg.elements), expected_ids))
        # mọi value.element_id phải đúng dict-key của nó (liên kết toàn vẹn).
        for key, elem in reg.elements.items():
            self.assertEqual(elem.element_id, key, "key/value lệch: %r vs %r" % (key, elem.element_id))

        # (c) sidecar 1-1 với registry (đếm + bộ key khớp, không drift).
        side = json.loads(out.with_suffix(".dce_audit.json").read_text(encoding="utf-8"))
        side_reg = side["element_registry"]
        self.assertEqual(side_reg["total_elements"], expected_ids)
        self.assertEqual(set(side_reg["elements"].keys()), set(reg.elements.keys()))

    def test_custom_thickness_level_and_scale_round_trip(self):
        model = self.cpe.build_structural_model()
        model["sheet_scale_label"] = "1/75"
        model["slab_level_m"] = 8.4
        model["slab_tags"][0]["thickness_mm"] = 180
        model["slab_tags"][3]["drop_box_mm"] = [1800, 2400]
        reg = self.regmod.CadElementRegistry("C1_CUSTOM")
        out = self.tmp / "custom.dxf"
        with contextlib.redirect_stdout(io.StringIO()):
            self.cpe.DcePlanEngine(model, v6=True, element_registry=reg).setup()
            eng = self.cpe.DcePlanEngine(model, v6=True, element_registry=reg)
            eng.setup().render_sheet_kc03().save_v6(str(out))
        import ezdxf
        doc = ezdxf.readfile(str(out))
        slabs = [e for e in doc.modelspace() if e.dxftype() == "INSERT" and e.dxf.name == "DCE_Slab tag"]
        self.assertIn("180", {a.dxf.text for a in slabs[0].attribs})
        cote = [e for e in doc.modelspace() if e.dxftype() == "INSERT" and e.dxf.name == "Dce_CaoTrinh"]
        self.assertIn("+8.400", {a.dxf.text for a in cote[0].attribs})
        beams = [e for e in doc.modelspace() if e.dxftype() == "INSERT" and e.dxf.name == "Dce_KhTenDam"]
        self.assertIn("1/75", {a.dxf.text for a in beams[0].attribs})

    def test_missing_v6_level_is_degraded_not_silent(self):
        model = self.cpe.build_structural_model()
        model.pop("slab_level_m", None)
        reg = self.regmod.CadElementRegistry("C1_MISSING")
        out = self.tmp / "missing.dxf"
        eng = self.cpe.DcePlanEngine(model, v6=True, element_registry=reg)
        with contextlib.redirect_stdout(io.StringIO()):
            eng.setup().render_sheet_kc03().save_v6(str(out))
        self.assertTrue(any(d["code"] == "MISSING_FIELD" for d in eng.v6_diagnostics))
        side = json.loads(out.with_suffix(".dce_audit.json").read_text(encoding="utf-8"))
        self.assertEqual(side["v6_status"], "DEGRADED")


if __name__ == "__main__":
    unittest.main()
