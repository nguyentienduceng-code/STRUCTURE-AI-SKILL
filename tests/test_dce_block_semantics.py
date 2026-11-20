# -*- coding: utf-8 -*-
"""
Test Suite: test_dce_block_semantics.py
Description:
    Kiem tra toan dien kien truc Du lieu & Block Semantics v6.0 (Phase GEMINI G1):
      1. Block Catalog scanner, trich xuat ATTDEF, basepoint va SHA-256 hash.
      2. Semantic Binding definitions & mapping tags.
      3. Round-trip integrity: Save DXF voi bind_block_attributes va Reopen kiem tra ATTRIB.
      4. Xu ly thieu tag & validation attributes voi InvalidSemanticValueError va MissingTagError.
      5. Immutable CadElementRegistry: Bao toan element_id khi doi ten, link refs, JSON round-trip.
      6. DCE Steel Adapter: Static vector geometry (khong scale X/Y), khai bao nang luc minh bach,
         va xu ly payload XData tham chieu.
"""

import sys
if hasattr(sys.stdout, "reconfigure") and sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

import hashlib
import json
import os
import unittest
import tempfile
from pathlib import Path

# Them duong dan module vao sys.path
INTEGRATION_DIR = Path(__file__).resolve().parent.parent / "skills" / "Technical_Illustrator" / "cad_integration"
if str(INTEGRATION_DIR) not in sys.path:
    sys.path.insert(0, str(INTEGRATION_DIR))

import ezdxf
from dce_block_catalog import DceBlockCatalog, DceBlockSpec, DceBlockAttdef, get_default_catalog
from dce_block_binding import (
    get_default_binding_registry,
    bind_block_attributes,
    extract_semantic_values,
    InvalidSemanticValueError,
    MissingTagError,
)
from cad_element_registry import (
    StructuralElement,
    CadElementRegistry,
    filter_rebar_strips_by_face,
    load_c1_fixture,
    validate_dxf_entity_map_linkage,
    DEFAULT_C1_FIXTURE_PATH,
)
from dce_steel_adapter import (
    STEEL_CHANNEL_PROFILES,
    STEEL_PIPE_PROFILES,
    STEEL_BASEPLATE_PRESETS,
    evaluate_steel_capability,
    evaluate_steel_drawing_request,
    get_i_profile_polygon,
    get_box_profile_polygons,
    get_channel_profile_polygon,
    get_pipe_profile_circles,
    generate_baseplate_geometry,
    validate_uniform_block_scale,
    render_steel_components_to_dxf,
    verify_steel_dxf_roundtrip,
    serialize_steel_xdata_payload,
    deserialize_steel_xdata_payload,
)


class TestDceBlockSemantics(unittest.TestCase):
    """Test suite cho Block Semantics, Catalog, Registry va Steel Adapter v6.0."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    # --------------------------------------------------------------------------
    # 1. BLOCK CATALOG & HASH TESTS
    # --------------------------------------------------------------------------
    def test_catalog_scan_from_synthetic_dxf(self):
        """Kiem tra catalog scanner trich xuat dung ATTDEF, basepoint va hash SHA-256."""
        doc = ezdxf.new("R2010")
        blk = doc.blocks.new(name="TEST_BEAM_TAG", base_point=(10.0, 20.0, 0.0))
        blk.add_attdef("TENDAM", text="D1", insert=(0, 0, 0))
        blk.add_attdef("TL", text="200x400", insert=(0, -5, 0))
        blk.add_line((0, 0), (100, 0))

        test_dxf_path = self.temp_path / "test_catalog.dxf"
        doc.saveas(test_dxf_path)

        catalog = DceBlockCatalog()
        catalog.scan_dxf(test_dxf_path)

        self.assertIn("TEST_BEAM_TAG", catalog.list_blocks())
        info = catalog.get_block("TEST_BEAM_TAG")
        self.assertIsNotNone(info)
        self.assertEqual(info.name, "TEST_BEAM_TAG")
        self.assertEqual(info.basepoint, (10.0, 20.0, 0.0))
        self.assertIn("TENDAM", info.attdefs)
        self.assertIn("TL", info.attdefs)
        self.assertIsNotNone(info.source_sha256)
        self.assertEqual(len(info.source_sha256), 64)

    # --------------------------------------------------------------------------
    # 2. BINDING DEFINITIONS TESTS
    # --------------------------------------------------------------------------
    def test_semantic_binding_mappings(self):
        """Kiem tra cac tag ky thuat DCE khong bi doan mo ma co anh xa chuan xac."""
        registry = get_default_binding_registry()

        # 1. DCE_Slab tag: tag '200' la chieu day san mm
        slab_binding = registry.get("DCE_Slab tag")
        self.assertIsNotNone(slab_binding)
        self.assertIn("thickness_mm", slab_binding.fields)
        self.assertEqual(slab_binding.fields["thickness_mm"].target_tag, "200")

        # 2. DCE_Drop mark: tag '50' la chieu ha cot mm
        drop_binding = registry.get("DCE_Drop mark")
        self.assertIsNotNone(drop_binding)
        self.assertIn("drop_mm", drop_binding.fields)
        self.assertEqual(drop_binding.fields["drop_mm"].target_tag, "50")

        # 3. Dce_KhTenDam: TENDAM va TL
        beam_binding = registry.get("Dce_KhTenDam")
        self.assertIsNotNone(beam_binding)
        self.assertEqual(beam_binding.fields["beam_mark"].target_tag, "TENDAM")
        self.assertEqual(beam_binding.fields["scale_label"].target_tag, "TL")

        # 4. TenCauKien: TENCAUKIEN va SOCAUKIEN
        col_binding = registry.get("TenCauKien")
        self.assertIsNotNone(col_binding)
        self.assertEqual(col_binding.fields["member_mark"].target_tag, "TENCAUKIEN")
        self.assertEqual(col_binding.fields["member_size"].target_tag, "SOCAUKIEN")

        # 5. Dce_CaoTrinh: CT
        ct_binding = registry.get("Dce_CaoTrinh")
        self.assertIsNotNone(ct_binding)
        self.assertEqual(ct_binding.fields["level_m"].target_tag, "CT")

    # --------------------------------------------------------------------------
    # 3. ROUND-TRIP SAVE & REOPEN INTEGRITY
    # --------------------------------------------------------------------------
    def test_semantic_binding_round_trip(self):
        """
        Kiem tra ghi block voi bind_block_attributes, luu DXF ra dia,
        mo lai doc ATTRIB bang extract_semantic_values phai khop 100%.
        """
        doc = ezdxf.new("R2010")
        msp = doc.modelspace()

        # Dinh nghia block Dce_KhTenDam trong block table
        blk_beam = doc.blocks.new(name="Dce_KhTenDam")
        blk_beam.add_attdef("TENDAM", text="DEFAULT")
        blk_beam.add_attdef("TL", text="1:100")

        spec_beam = DceBlockSpec(
            name="Dce_KhTenDam",
            basepoint=(0.0, 0.0, 0.0),
            attdefs={
                "TENDAM": DceBlockAttdef(tag="TENDAM", prompt="", default_value=""),
                "TL": DceBlockAttdef(tag="TL", prompt="", default_value="1:100")
            }
        )

        # Dinh nghia block DCE_Slab tag
        blk_slab = doc.blocks.new(name="DCE_Slab tag")
        blk_slab.add_attdef("200", text="100")

        spec_slab = DceBlockSpec(
            name="DCE_Slab tag",
            basepoint=(0.0, 0.0, 0.0),
            attdefs={
                "200": DceBlockAttdef(tag="200", prompt="", default_value="100")
            }
        )

        # Chen va bind attributes
        insert_beam = msp.add_blockref("Dce_KhTenDam", (1000, 2000))
        beam_values_in = {"beam_mark": "D1A", "scale_label": "1:100"}
        bind_block_attributes(insert_beam, spec_beam, beam_values_in)

        insert_slab = msp.add_blockref("DCE_Slab tag", (3000, 4000))
        slab_values_in = {"thickness_mm": 120.0}
        bind_block_attributes(insert_slab, spec_slab, slab_values_in)

        # Luu DXF ra file thuc
        dxf_path = self.temp_path / "round_trip_test.dxf"
        doc.saveas(dxf_path)

        # Mo lai DXF doc lap
        doc_reopened = ezdxf.readfile(dxf_path)
        msp_reopened = doc_reopened.modelspace()

        read_beams = []
        read_slabs = []

        for entity in msp_reopened.query("INSERT"):
            if entity.dxf.name == "Dce_KhTenDam":
                val = extract_semantic_values(entity, spec_beam)
                read_beams.append(val)
            elif entity.dxf.name == "DCE_Slab tag":
                val = extract_semantic_values(entity, spec_slab)
                read_slabs.append(val)

        self.assertEqual(len(read_beams), 1)
        self.assertEqual(len(read_slabs), 1)

        # Kiem tra gia tri trich xuat khop 100% voi input
        self.assertEqual(read_beams[0]["beam_mark"], "D1A")
        self.assertEqual(read_beams[0]["scale_label"], "1:100")
        self.assertEqual(read_slabs[0]["thickness_mm"], 120.0)

    # --------------------------------------------------------------------------
    # 4. MISSING ATTRIBUTES & VALIDATION
    # --------------------------------------------------------------------------
    def test_missing_and_invalid_attributes(self):
        """Kiem tra co che validate bat loi thieu tag va gia tri bat thuong."""
        doc = ezdxf.new("R2010")
        msp = doc.modelspace()
        doc.blocks.new(name="Dce_KhTenDam").add_attdef("TENDAM")
        insert_ent = msp.add_blockref("Dce_KhTenDam", (0, 0))

        spec_beam = DceBlockSpec(
            name="Dce_KhTenDam",
            basepoint=(0.0, 0.0, 0.0),
            attdefs={"TENDAM": DceBlockAttdef(tag="TENDAM", prompt="", default_value="")}
        )

        # 1. Thieu truong bat buoc beam_mark trong Dce_KhTenDam -> InvalidSemanticValueError
        with self.assertRaises(InvalidSemanticValueError):
            bind_block_attributes(insert_ent, spec_beam, {"scale_label": "1:100"})

        # 2. Block Spec khong co tag -> MissingTagError
        spec_empty = DceBlockSpec(name="Dce_KhTenDam", basepoint=(0.0, 0.0, 0.0), attdefs={})
        with self.assertRaises(MissingTagError):
            bind_block_attributes(insert_ent, spec_empty, {"beam_mark": "D1A"})

    # --------------------------------------------------------------------------
    # 5. CAD ELEMENT REGISTRY TESTS
    # --------------------------------------------------------------------------
    def test_element_registry_immutability_and_rename(self):
        """Kiem tra registry bao toan element_id bat bien khi doi ten mark."""
        registry = CadElementRegistry("TEST_PROJECT")

        beam = StructuralElement(
            element_id="BEAM_LVL2_D1_001",
            category="BEAM",
            mark="D1",
            span_id="SPAN_1",
            floor_id="TANG_2",
            section_profile={"b_mm": 200, "h_mm": 400}
        )
        registry.register(beam)
        registry.link_tag("BEAM_LVL2_D1_001", "HANDLE_TAG_A1")
        registry.link_geometry("BEAM_LVL2_D1_001", "HANDLE_LINE_L1")
        registry.set_detail_target("BEAM_LVL2_D1_001", "KC.23", "DETAIL_D1A", target_exists=True)

        # Doi ten tu D1 thanh D1A
        success = registry.update_mark("BEAM_LVL2_D1_001", "D1A", reason="Sync with architectural plan")
        self.assertTrue(success)

        retrieved = registry.get("BEAM_LVL2_D1_001")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.element_id, "BEAM_LVL2_D1_001")  # ID bat bien
        self.assertEqual(retrieved.mark, "D1A")                      # Mark da doi
        self.assertIn("HANDLE_TAG_A1", retrieved.tag_refs)
        self.assertEqual(len(retrieved.change_history), 1)
        self.assertEqual(retrieved.change_history[0]["old_mark"], "D1")
        self.assertEqual(retrieved.change_history[0]["new_mark"], "D1A")

        # Kiem tra truy van nguoc qua tag handle
        elem_by_tag = registry.get_by_tag_handle("HANDLE_TAG_A1")
        self.assertEqual(elem_by_tag.element_id, "BEAM_LVL2_D1_001")

        # Kiem tra JSON round-trip
        json_repr = registry.to_json()
        rebuilt = CadElementRegistry.from_json(json_repr)
        self.assertEqual(rebuilt.get("BEAM_LVL2_D1_001").mark, "D1A")
        self.assertEqual(rebuilt.get("BEAM_LVL2_D1_001").detail_ref["sheet_number"], "KC.23")

    # --------------------------------------------------------------------------
    # 6. DCE STEEL ADAPTER TESTS
    # --------------------------------------------------------------------------
    def test_steel_adapter_capability_and_geometry(self):
        """Kiem tra tinh nang cua DCE Steel Adapter: khai bao nang luc va hinh hoc 2D."""
        # 1. Kiem tra danh gia nang luc minh bach
        dyn_eval = evaluate_steel_capability("DYNAMIC_PARAMETRIC_STRETCH", "Dce_BeamI1")
        self.assertFalse(dyn_eval["supported"])
        self.assertEqual(dyn_eval["status"], "UNSUPPORTED_BLOCK_BEHAVIOR")
        self.assertEqual(dyn_eval["fallback"], "STATIC_2D_ACCURATE")

        stat_eval = evaluate_steel_capability("GENERATE_2D_PROFILE", "H200x200x8x12")
        self.assertTrue(stat_eval["supported"])
        self.assertEqual(stat_eval["status"], "SUPPORTED")

        # 2. Kiem tra tao da giac I-Profile khong dung scale X/Y
        i_poly = get_i_profile_polygon("H200x200x8x12", insert_x=0.0, insert_y=0.0)
        self.assertEqual(len(i_poly), 12)
        # H=200 -> hy=100, B=200 -> hx=100
        xs = [pt[0] for pt in i_poly]
        ys = [pt[1] for pt in i_poly]
        self.assertAlmostEqual(max(xs) - min(xs), 200.0)
        self.assertAlmostEqual(max(ys) - min(ys), 200.0)

        # 3. Kiem tra ban ma chan cot Baseplate
        bp = generate_baseplate_geometry(
            b_mm=350.0,
            h_mm=350.0,
            t_mm=16.0,
            bolt_spec_name="M20",
            bolt_offsets=[(-100, -100), (100, -100), (100, 100), (-100, 100)]
        )
        self.assertEqual(len(bp["plate_polygon"]), 4)
        self.assertEqual(len(bp["bolt_holes"]), 4)
        self.assertEqual(bp["bolt_holes"][0]["radius"], 11.0)  # M20 -> hole d=22 -> r=11

        # 4. Kiem tra serialize/deserialize XData Steel tham chieu
        payload = serialize_steel_xdata_payload(tw=8.0, soluong=6, socaukien=2, ghichu="DCE_STEEL_COL")
        self.assertEqual(payload, "8.0#6#2#DCE_STEEL_COL")
        deserialized = deserialize_steel_xdata_payload(payload)
        self.assertTrue(deserialized["is_valid"])
        self.assertEqual(deserialized["tw"], 8.0)
        self.assertEqual(deserialized["soluong"], 6)
        self.assertEqual(deserialized["socaukien"], 2)
        self.assertEqual(deserialized["ghichu"], "DCE_STEEL_COL")

    # --------------------------------------------------------------------------
    # 7. C1 FIXTURE ADAPTER & KC-03 V6 ROUND-TRIP TESTS
    # --------------------------------------------------------------------------
    def test_c1_fixture_adapter_and_kc03_v6_roundtrip(self):
        """
        Kiem tra adapter chuyen doi c1_sample_model.json <-> DcePlanEngine:
        - Du 5 ca bien C1: dam X/Y/xien 45 do, nhieu nhip cung mark D1A, cung tiet dien khac thep,
          san co lo mo + san ha cot 50mm, cot CONTINUOUS vs STOPPED.
        - Xuat KC-03 v6 tu fixture, mo lai DXF doc ATTRIB bang extract_semantic_values khop 100%.
        """
        import cad_plan_engine as cpe

        model, reg = load_c1_fixture()
        self.assertEqual(len(reg.elements), 9)

        # Ca 1: Dam X, Y va dam xien 45 do
        self.assertEqual(len(model["beams_x"]), 2)
        self.assertEqual(len(model["beams_y"]), 1)
        self.assertEqual(len(model["secondary_beams"]), 1)
        self.assertAlmostEqual(model["secondary_beams"][0]["angle_deg"], 45.0)

        # Ca 2: Nhieu nhip cung mark D1A nhung element_id khac nhau
        d1a_elems = reg.query(category="BEAM", mark="D1A")
        self.assertEqual(len(d1a_elems), 2)
        self.assertNotEqual(d1a_elems[0].element_id, d1a_elems[1].element_id)
        self.assertEqual({e.span_id for e in d1a_elems}, {"SPAN_1", "SPAN_2"})

        # Ca 3: Cung tiet dien 200x400 nhung khac nhom thep (3D20 vs 3D22)
        d2_elem = reg.get("BEAM_D2_Y_AXIS_LVL2")
        self.assertEqual(d2_elem.section_profile["b_mm"], 200)
        self.assertEqual(d2_elem.section_profile["h_mm"], 400)
        self.assertNotEqual(d1a_elems[0].design_group_id, d2_elem.design_group_id)

        # Ca 4: San co lo mo MEP va san ha cot 50mm
        self.assertEqual(len(model["voids"]), 1)
        self.assertEqual(model["voids"][0]["name"], "OPENING_MEP_01")
        s2_elem = reg.get("SLAB_S2_WC_DROP_LVL2")
        self.assertEqual(s2_elem.section_profile["drop_mm"], 50)

        # Ca 5: Cot CONTINUOUS va cot STOPPED
        self.assertEqual(len(reg.query(category="COLUMN", status="CONTINUOUS")), 1)
        self.assertEqual(len(reg.query(category="COLUMN", status="STOPPED")), 1)

        # Xuat KC-03 v6 tu c1_sample_model.json va doc lai ATTRIB
        out_dxf = self.temp_path / "c1_fixture_kc03_v6.dxf"
        eng = cpe.export_dce_plan(
            str(out_dxf),
            sheet_type="KC-03",
            model_json_path=str(DEFAULT_C1_FIXTURE_PATH),
            v6=True,
            element_registry=reg,
        )
        self.assertEqual(eng.v6_diagnostics, [])
        self.assertTrue(out_dxf.is_file())

        doc = ezdxf.readfile(str(out_dxf))
        msp = doc.modelspace()
        cat = get_default_catalog()

        beam_tags = [
            extract_semantic_values(ins, cat.get_block("Dce_KhTenDam"))
            for ins in msp.query('INSERT[name=="Dce_KhTenDam"]')
        ]
        slab_tags = [
            extract_semantic_values(ins, cat.get_block("DCE_Slab tag"))
            for ins in msp.query('INSERT[name=="DCE_Slab tag"]')
        ]
        drop_tags = [
            extract_semantic_values(ins, cat.get_block("DCE_Drop mark"))
            for ins in msp.query('INSERT[name=="DCE_Drop mark"]')
        ]
        level_tags = [
            extract_semantic_values(ins, cat.get_block("Dce_CaoTrinh"))
            for ins in msp.query('INSERT[name=="Dce_CaoTrinh"]')
        ]

        beam_marks = [b["beam_mark"] for b in beam_tags]
        self.assertEqual(beam_marks.count("D1A (200x400)"), 2)
        self.assertIn("D2 (200x400)", beam_marks)
        self.assertIn("DX1 (200x350)", beam_marks)
        self.assertEqual(slab_tags[0]["thickness_mm"], 120.0)
        self.assertAlmostEqual(drop_tags[0]["drop_mm"], -0.05)
        self.assertAlmostEqual(level_tags[0]["level_m"], 3.800)

    def test_g2_steel_catalog_and_block_bindings(self):
        """G2.1: Xac minh danh muc block Steel tu Form 2_Steel.dwg va bind/extract dung ATTDEF that."""
        cat = get_default_catalog()
        reg = get_default_binding_registry()

        expected_steel = [
            ("Dce-ThepTam", ["B", "SL", "TENCK", "HINHDANG", "VATCANH"]),
            ("Dce-Tangcung", ["B", "SL", "TENCK", "HINHDANG", "VATCANH"]),
            ("Dce_BP_Pin4", ["TenBanDe", "ChieuDay"]),
            ("Dce_BP_Fix8", ["TenBanDe", "ChieuDay"]),
            ("Dce_AnchorExpansion", ["SL"]),
            ("Dce_PlanI", ["TENCOT"]),
        ]
        for bname, tags in expected_steel:
            spec = cat.require_block(bname)
            self.assertEqual(spec.confidence, "PARTIAL_DWG_WASM_READ_76")
            for tag in tags:
                self.assertIn(tag, spec.attdefs)
            self.assertIsNotNone(reg.get(bname))

        # Round-trip bind -> save -> reopen -> extract cho Dce-ThepTam & Dce_BP_Pin4
        doc = ezdxf.new("R2010")
        msp = doc.modelspace()
        for bname in ("Dce-ThepTam", "Dce_BP_Pin4", "Dce_AnchorExpansion"):
            spec = cat.require_block(bname)
            blk = doc.blocks.new(bname)
            for idx, (tag, adef) in enumerate(spec.attdefs.items()):
                blk.add_attdef(tag=tag, insert=(0.0, float(-idx * 4.0)), text=adef.default_value, height=2.5)

        ins_pl = msp.add_blockref("Dce-ThepTam", (100.0, 100.0))
        bind_block_attributes(
            ins_pl,
            cat.require_block("Dce-ThepTam"),
            {
                "plate_thickness": 14,
                "quantity": 6,
                "member_mark": "BM-G1",
                "shape_desc": "RECT",
                "chamfer_desc": "V45",
            },
            registry=reg,
        )

        ins_bp = msp.add_blockref("Dce_BP_Pin4", (300.0, 100.0))
        bind_block_attributes(
            ins_bp,
            cat.require_block("Dce_BP_Pin4"),
            {"baseplate_mark": "BD-01", "thickness_mm": 22},
            registry=reg,
        )

        ins_anc = msp.add_blockref("Dce_AnchorExpansion", (300.0, 50.0))
        bind_block_attributes(
            ins_anc,
            cat.require_block("Dce_AnchorExpansion"),
            {"bolt_count": 4},
            registry=reg,
        )

        # Kiem tra thieu truong bat buoc phai raise InvalidSemanticValueError
        ins_bad = msp.add_blockref("Dce_BP_Pin4", (500.0, 100.0))
        with self.assertRaises(InvalidSemanticValueError):
            bind_block_attributes(
                ins_bad,
                cat.require_block("Dce_BP_Pin4"),
                {"baseplate_mark": "BD-ERR"},
                registry=reg,
            )

        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "g2_binding_roundtrip.dxf"
            doc.saveas(str(p))
            reopened = ezdxf.readfile(str(p))
            rmsp = reopened.modelspace()

            rp = list(rmsp.query('INSERT[name=="Dce-ThepTam"]'))[0]
            for att in rp.attribs:
                self.assertEqual(att.dxf.true_color, 0x1E3246)
                self.assertNotEqual(att.dxf.color, 7)

            ext_pl = extract_semantic_values(rp, cat.require_block("Dce-ThepTam"), registry=reg)
            self.assertEqual(ext_pl["plate_thickness"], 14.0)
            self.assertEqual(ext_pl["quantity"], 6)
            self.assertEqual(ext_pl["member_mark"], "BM-G1")
            self.assertEqual(ext_pl["shape_desc"], "RECT")
            self.assertEqual(ext_pl["chamfer_desc"], "V45")

            rbp = list(rmsp.query('INSERT[name=="Dce_BP_Pin4"]'))[0]
            ext_bp = extract_semantic_values(rbp, cat.require_block("Dce_BP_Pin4"), registry=reg)
            self.assertEqual(ext_bp["baseplate_mark"], "BD-01")
            self.assertEqual(ext_bp["thickness_mm"], 22.0)

            ranc = list(rmsp.query('INSERT[name=="Dce_AnchorExpansion"]'))[0]
            ext_anc = extract_semantic_values(ranc, cat.require_block("Dce_AnchorExpansion"), registry=reg)
            self.assertEqual(ext_anc["bolt_count"], 4)

    def test_g2_steel_dxf_save_reopen_no_xy_scale_and_capability(self):
        """G2.2: Khoa uniform scale (xscale==yscale), tu choi Dynamic/XData thuong mai, save/reopen 1:1 mm."""
        self.assertTrue(validate_uniform_block_scale(1.0, 1.0)["is_valid"])
        with self.assertRaises(ValueError):
            validate_uniform_block_scale(1.5, 2.0, strict=True)

        # Channel & Pipe 1:1 mm geometry
        ch_pts = get_channel_profile_polygon("U160x64x5", origin=(500.0, 600.0))
        self.assertEqual(len(ch_pts), 8)
        self.assertAlmostEqual(max(p[0] for p in ch_pts) - min(p[0] for p in ch_pts), 64.0)
        self.assertAlmostEqual(max(p[1] for p in ch_pts) - min(p[1] for p in ch_pts), 160.0)

        pp = get_pipe_profile_circles("D219x6.0", origin=(100.0, 200.0))
        self.assertAlmostEqual(pp["outer_radius"], 109.5)
        self.assertAlmostEqual(pp["inner_radius"], 103.5)

        req_dyn = evaluate_steel_drawing_request({"mark": "SB1", "requested_mode": "DYNAMIC", "write_commercial_xdata": True})
        self.assertFalse(req_dyn["supported"])
        self.assertTrue(req_dyn["fallback_used"])
        self.assertEqual(req_dyn["capability_status"], "UNSUPPORTED_BLOCK_BEHAVIOR")
        self.assertFalse(req_dyn["commercial_xdata_written"])
        codes = [w["code"] for w in req_dyn["warnings"]]
        self.assertIn("UNSUPPORTED_BLOCK_BEHAVIOR", codes)
        self.assertIn("UNSUPPORTED_COMMERCIAL_XDATA_DISABLED", codes)

        fix_path = INTEGRATION_DIR / "fixtures" / "g2_steel_and_sheet_fixture.json"
        fixture = json.loads(fix_path.read_text(encoding="utf-8"))

        with tempfile.TemporaryDirectory() as tmpdir:
            dxf_out = Path(tmpdir) / "g2_steel_test.dxf"
            render_res = render_steel_components_to_dxf(dxf_out, fixture)
            self.assertEqual(render_res["sections_count"], 5)
            self.assertEqual(render_res["baseplates_count"], 2)
            self.assertEqual(render_res["plates_count"], 1)
            self.assertFalse(render_res["commercial_xdata_written"])
            warn_codes = [w["code"] for w in render_res["capability_warnings"]]
            self.assertIn("UNSUPPORTED_BLOCK_BEHAVIOR", warn_codes)
            self.assertIn("UNSUPPORTED_COMMERCIAL_XDATA_DISABLED", warn_codes)

            rt = verify_steel_dxf_roundtrip(dxf_out, fixture)
            self.assertTrue(rt["passed"], msg=f"Roundtrip failed: {rt['mismatches']}")
            self.assertTrue(rt["uniform_scale_ok"])
            self.assertEqual(rt["dynamic_block_refs_count"], 0)
            self.assertEqual(rt["commercial_xdata_count"], 0)
            self.assertEqual(len(rt["geometry_checks"]), 7)
            self.assertEqual(len(rt["extracted_blocks"]), 6)

            # Negative roundtrip: insert co X/Y scale khac nhau phai bi phat hien
            tampered = ezdxf.readfile(str(dxf_out))
            tampered.modelspace().add_blockref("Dce_BP_Pin4", (9000.0, 9000.0), dxfattribs={"xscale": 1.5, "yscale": 2.0})
            tampered.saveas(str(dxf_out))
            rt_bad = verify_steel_dxf_roundtrip(dxf_out, fixture)
            self.assertFalse(rt_bad["uniform_scale_ok"])
            self.assertFalse(rt_bad["passed"])

    def test_g2_cross_sheet_semantic_and_registry_validation(self):
        """G2.3: Kiem chuan ngu nghia xuyen to (cot ngung, nhom thiet ke, detail target, 3-chieu, TOP/BOTTOM)."""
        fix_path = INTEGRATION_DIR / "fixtures" / "g2_steel_and_sheet_fixture.json"
        fixture = json.loads(fix_path.read_text(encoding="utf-8"))

        def _build_registry() -> CadElementRegistry:
            reg = CadElementRegistry(project_name=fixture["project_name"])
            for gkey in ("concrete_elements", "steel_sections", "baseplates", "steel_plates"):
                for item in fixture.get(gkey, []):
                    prof = dict(item.get("section_profile") or {})
                    if gkey == "steel_sections":
                        prof = {"profile_type": item["profile_type"], "section_name": item["section_name"]}
                    elif gkey == "baseplates":
                        prof = {
                            "block_name": item["block_name"],
                            "plate_width_mm": item["plate_width_mm"],
                            "plate_height_mm": item["plate_height_mm"],
                            "thickness_mm": item["thickness_mm"],
                        }
                    elif gkey == "steel_plates":
                        prof = {
                            "block_name": item["block_name"],
                            "plate_thickness": item["plate_thickness"],
                            "quantity": item["quantity"],
                        }
                    reg.register(StructuralElement(
                        element_id=item["element_id"],
                        category=item["category"],
                        mark=item["mark"],
                        span_id=item.get("span_id"),
                        floor_id=item["floor_id"],
                        design_group_id=item.get("design_group_id"),
                        section_profile=prof,
                        geometry_refs=list(item.get("geometry_refs", [])),
                        tag_refs=list(item.get("tag_refs", [])),
                        schedule_refs=list(item.get("schedule_refs", [])),
                        detail_ref=dict(item.get("detail_ref", {})),
                        status=item.get("status", "CONTINUOUS"),
                    ))
            return reg

        reg = _build_registry()
        with tempfile.TemporaryDirectory() as tmpdir:
            render_steel_components_to_dxf(Path(tmpdir) / "g2_sem.dxf", fixture, registry=reg)

        res_ok = reg.validate_sheet_set_semantics(
            sheet_manifest=fixture["sheet_set_preview_manifest"],
            rebar_strips=fixture["rebar_strips"],
        )
        self.assertTrue(res_ok["is_valid"], msg=f"Unexpected violations: {res_ok['violations']}")
        for ck, passed in res_ok["checks"].items():
            self.assertTrue(passed, msg=f"Check {ck} should pass")

        # Tach TOP / BOTTOM tuyet doi khong tron lan
        top_only = filter_rebar_strips_by_face(fixture["rebar_strips"], "TOP")
        bot_only = filter_rebar_strips_by_face(fixture["rebar_strips"], "BOTTOM")
        self.assertEqual(len(top_only), 2)
        self.assertEqual(len(bot_only), 2)
        self.assertTrue(all(s["face"] == "TOP" for s in top_only))
        self.assertTrue(all(s["face"] == "BOTTOM" for s in bot_only))
        self.assertEqual({s["strip_id"] for s in top_only} & {s["strip_id"] for s in bot_only}, set())

        # Negative 1: Cot C1 da STOPPED tai F2 nhung van tiep tuc CONTINUOUS tai F3
        reg_bad = _build_registry()
        with tempfile.TemporaryDirectory() as tmpdir:
            render_steel_components_to_dxf(Path(tmpdir) / "g2_sem2.dxf", fixture, registry=reg_bad)
        reg_bad.register(StructuralElement(
            element_id="COL_C1_F3_ERR",
            category="COLUMN",
            mark="C1",
            floor_id="F3_MAI",
            design_group_id="DG-CONC-COL-C1",
            section_profile={"width_mm": 300, "height_mm": 300, "concrete_grade": "B30"},
            geometry_refs=["G_ERR"],
            tag_refs=["T_ERR"],
            schedule_refs=["SCH_C1"],
            detail_ref={"sheet_number": "KC-07", "drawing_id": "CT-COL-C1", "target_exists": True},
            status="CONTINUOUS",
        ))
        # Negative 2: Thieu design_group consistency (BM_D1A_F2_S2 doi tiet dien nhung giu cung group)
        reg_bad.get("BM_D1A_F2_S2").section_profile["height_mm"] = 500
        # Negative 3: Thieu dich detail_ref
        reg_bad.get("BM_D1A_F2_S1").set_detail_target("KC-99", "NO_EXIST", target_exists=False)
        # Negative 4: Thieu schedule_ref (3-way linkage)
        reg_bad.get("BM_D1A_F2_S2").schedule_refs = []

        # Negative 5: Tron lan dai BOTTOM vao viewport TOP
        bad_manifest = json.loads(json.dumps(fixture["sheet_set_preview_manifest"]))
        bad_manifest["sheets"][2]["viewports"][1]["strip_ids"].append("RS_F2_BOT_X1")

        res_bad = reg_bad.validate_sheet_set_semantics(
            sheet_manifest=bad_manifest,
            rebar_strips=fixture["rebar_strips"],
        )
        self.assertFalse(res_bad["is_valid"])
        for ck in (
            "floor_and_column_continuity",
            "design_group_consistency",
            "detail_target_resolution",
            "linkage_completeness",
            "rebar_top_bottom_separation",
        ):
            self.assertFalse(res_bad["checks"][ck], msg=f"Expected {ck} failure to be detected")

    # --------------------------------------------------------------------------
    # 8. A1-06 PHYSICAL DXF ENTITY-MAP & 3-WAY LINKAGE VALIDATOR TESTS
    # --------------------------------------------------------------------------
    def test_11_validate_c2_remediated_entity_map_and_strict_3way_gate(self):
        """A1-06: Doi chieu entity_map -> DXF handles & gate 3-chieu thuc tren c2_remediated."""
        c2_dir = Path(__file__).resolve().parent.parent / "memory" / "audits" / "cad_v6" / "claude" / "c2_remediated"
        fix_path = INTEGRATION_DIR / "fixtures" / "g2_steel_and_sheet_fixture.json"
        fixture = json.loads(fix_path.read_text(encoding="utf-8"))

        sheets = ["KC-02", "KC-03", "KC-04", "KC-06", "KC-07"]
        for sno in sheets:
            dxf_path = c2_dir / f"{sno}_C2_A3.dxf"
            res = validate_dxf_entity_map_linkage(dxf_path, fixture_data=fixture)
            self.assertTrue(res["dxf_sha256_match"], msg=f"{sno}: SHA-256 mismatch")
            self.assertTrue(res["recorded_handles_resolved_ok"], msg=f"{sno}: {res['issues']}")
            self.assertEqual(res["recorded_handle_counts"]["geometry"], 15)
            self.assertEqual(res["recorded_handle_counts"]["tag"], 9)
            self.assertEqual(res["resolved_handle_counts"]["geometry"], 15)
            self.assertEqual(res["resolved_handle_counts"]["tag"], 9)

            # Strict gate must reject metadata-only schedule_refs, untagged baseplates, and unmapped STEEL_PL_01
            self.assertFalse(res["strict_3way_physical_linkage_ok"])
            self.assertGreater(len(res["issues"]["metadata_only_schedule_refs"]), 0)
            missing_tag_ids = {x["element_id"] for x in res["issues"]["missing_physical_tag"]}
            self.assertEqual(missing_tag_ids, {"STEEL_BP_01", "STEEL_BP_02"})
            unmapped_ids = {x["element_id"] for x in res["issues"]["unmapped_expected_elements"]}
            self.assertIn("STEEL_PL_01", unmapped_ids)

            if sno == "KC-04":
                vp_info = res["viewport_inspection"]
                self.assertTrue(vp_info["viewport_nonoverlap_ok"])
                self.assertTrue(vp_info["has_dual_rebar_viewports"])
                self.assertTrue(vp_info["vp_top_freezes_rebar_bottom"])
                self.assertTrue(vp_info["vp_bottom_freezes_rebar_top"])
                self.assertTrue(vp_info["disjoint_visible_rebar_ok"])
                self.assertEqual(vp_info["visible_rebar_handles_in_vp_bottom"], ["73", "74"])
                self.assertEqual(vp_info["visible_rebar_handles_in_vp_top"], ["75", "76"])
                for vp in vp_info["viewports"]:
                    self.assertAlmostEqual(vp["actual_scale_denominator"], 50.0, places=4)

    def test_12_validate_dxf_entity_map_detects_full_physical_3way_and_fake_handles(self):
        """A1-06: Xac minh 3-way linkage PASS khi du handle that & FAIL khi handle gia ('DEAD')."""
        doc = ezdxf.new("R2018")
        doc.layers.add("CONCRETE", dxfattribs={"color": 1})
        doc.layers.add("TAG", dxfattribs={"color": 2})
        doc.layers.add("DCE_Schedule", dxfattribs={"color": 7})

        blk = doc.blocks.new("DCE_TAG_TEST")
        blk.add_attdef("MARK", insert=(0, 0), height=100, text="C1")
        blk.add_attdef("SIZE", insert=(0, -150), height=90, text="300x300")

        msp = doc.modelspace()
        poly = msp.add_lwpolyline([(0, 0), (300, 0), (300, 300), (0, 300)], close=True, dxfattribs={"layer": "CONCRETE"})
        tag_ins = msp.add_blockref("DCE_TAG_TEST", (400, 150), dxfattribs={"layer": "TAG"})
        tag_ins.add_auto_attribs({"MARK": "C1", "SIZE": "300x300"})
        sched_txt = msp.add_text("C1 | 300x300 | B30", height=120, dxfattribs={"layer": "DCE_Schedule"})
        sched_txt.set_placement((1000, 0))

        dxf_path = self.temp_path / "full_3way_ok.dxf"
        doc.saveas(str(dxf_path))
        digest = hashlib.sha256(dxf_path.read_bytes()).hexdigest()

        reg = CadElementRegistry("A1_06_TEST")
        reg.register(StructuralElement(
            element_id="COL_C1_F1",
            category="COLUMN",
            mark="C1",
            floor_id="F1",
            geometry_refs=["SRC_G_C1"],
            tag_refs=["SRC_T_C1"],
            schedule_refs=["SCH_C1"],
        ))

        sidecar_path = dxf_path.with_suffix(".dce_audit.json")
        sidecar_payload = {
            "dxf_sha256": digest,
            "provenance": {"dxf_sha256": digest},
            "sheet_no": "KC-TEST",
            "entity_map": {
                "COL_C1_F1": {
                    "geometry_handles": [poly.dxf.handle],
                    "tag_handle": tag_ins.dxf.handle,
                    "schedule_handle": sched_txt.dxf.handle,
                    "source_refs": ["SRC_G_C1"],
                    "tag_refs": ["SRC_T_C1"],
                    "schedule_refs": ["SCH_C1"],
                }
            },
        }
        sidecar_path.write_text(json.dumps(sidecar_payload, indent=2), encoding="utf-8")

        res_ok = reg.validate_dxf_entity_map(dxf_path, sidecar_path)
        self.assertTrue(res_ok["dxf_sha256_match"])
        self.assertTrue(res_ok["recorded_handles_resolved_ok"])
        self.assertTrue(res_ok["strict_3way_physical_linkage_ok"], msg=f"Unexpected issues: {res_ok['issues']}")
        self.assertEqual(res_ok["resolved_handle_counts"], {"geometry": 1, "tag": 1, "schedule": 1})

        # Mutate schedule_handle to fake handle 'DEAD' -> must fail both handle resolution and strict gate
        sidecar_payload["entity_map"]["COL_C1_F1"]["schedule_handle"] = "DEAD"
        sidecar_path.write_text(json.dumps(sidecar_payload, indent=2), encoding="utf-8")

        res_bad = reg.validate_dxf_entity_map(dxf_path, sidecar_path)
        self.assertFalse(res_bad["recorded_handles_resolved_ok"])
        self.assertFalse(res_bad["strict_3way_physical_linkage_ok"])
        self.assertEqual(res_bad["issues"]["missing_schedule_handles"], [{"element_id": "COL_C1_F1", "handle": "DEAD"}])

    def test_13_validate_c2_remediated_v2_passes_strict_3way_gate_on_all_5_sheets(self):
        """A1-06 + C2-v2: Verify c2_remediated_v2 resolves all 12 fixture elements (incl. STEEL_PL_01/BP) & 3-way linkage PASS."""
        from cad_sheet_set import build_registry_from_fixture

        v2_dir = Path(__file__).resolve().parent.parent / "memory" / "audits" / "cad_v6" / "claude" / "c2_remediated_v2"
        fix_path = INTEGRATION_DIR / "fixtures" / "g2_steel_and_sheet_fixture.json"
        fixture = json.loads(fix_path.read_text(encoding="utf-8"))
        reg = build_registry_from_fixture(fixture)

        for sno in ("KC-02", "KC-03", "KC-04", "KC-06", "KC-07"):
            dxf_path = v2_dir / f"{sno}_C2_A3.dxf"
            res = validate_dxf_entity_map_linkage(dxf_path, registry=reg, fixture_data=fixture)
            self.assertTrue(res["dxf_sha256_match"], msg=f"{sno}: SHA mismatch")
            self.assertTrue(res["provenance_sha256_match"], msg=f"{sno}: provenance SHA mismatch")
            self.assertTrue(res["recorded_handles_resolved_ok"], msg=f"{sno}: {res['issues']}")
            self.assertTrue(res["strict_3way_physical_linkage_ok"], msg=f"{sno}: {res['issues']}")
            self.assertEqual(res["expected_elements_count"], 12)
            self.assertEqual(res["issues"].get("formatting_warnings", []), [])
            self.assertTrue(res["viewport_inspection"]["viewport_nonoverlap_ok"])
            if sno == "KC-04":
                self.assertTrue(res["viewport_inspection"]["disjoint_visible_rebar_ok"])


if __name__ == "__main__":
    unittest.main()
