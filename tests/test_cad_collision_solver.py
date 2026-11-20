# g:\My Drive\Google AI Studio\.agents\tests\test_cad_collision_solver.py
"""Unit and Integration Tests for CAD Scene Index & Collision Solver.

Suite 30 in the .agents verification framework.
Tests:
1. Clean drawing without collision.
2. Detection of text label colliding with structural column boundary.
3. Successful displacement of colliding label to an obstacle-free zone.
4. Automatic Leader Line creation when displacement > 300mm.
5. Dry-run mode preserves original DXF file integrity.
6. Two mutually colliding labels avoid each other without deadlock.
"""

import sys
import unittest
import tempfile
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

AGENTS_ROOT = Path(__file__).resolve().parent.parent
if str(AGENTS_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENTS_ROOT))
TOOLS_DIR = AGENTS_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import ezdxf

from tools.cad_scene_index import CadSceneIndex, BoundingBox
from tools.cad_collision_solver import CadCollisionSolver


class TestCadCollisionSolver(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dxf = Path(self.temp_dir.name) / "test_model.dxf"

    def tearDown(self):
        self.temp_dir.cleanup()

    def _create_minimal_dxf(self) -> ezdxf.document.Drawing:
        doc = ezdxf.new("R2010")
        doc.header["$INSUNITS"] = 4
        doc.layers.add("DCE_Cot", color=4)
        doc.layers.add("DCE_Name", color=142)
        doc.layers.add("DCE_Truc", color=8)
        return doc

    def test_01_no_collision_clean_drawing(self):
        doc = self._create_minimal_dxf()
        msp = doc.modelspace()
        # Add column at (0, 0)
        msp.add_lwpolyline([(0, 0), (400, 0), (400, 400), (0, 400), (0, 0)], dxfattribs={"layer": "DCE_Cot"})
        # Add text far away at (2000, 2000)
        msp.add_text("C1", dxfattribs={"layer": "DCE_Name", "height": 250, "insert": (2000, 2000, 0)})
        doc.saveas(self.test_dxf)

        solver = CadCollisionSolver.from_dxf(self.test_dxf)
        collisions = solver.detect_collisions()
        self.assertEqual(len(collisions), 0, "Clean drawing should have 0 collisions")

        res = solver.solve_all(dry_run=True)
        self.assertEqual(res["displacements_planned"], 0)

    def test_02_detect_text_overlapping_column(self):
        doc = self._create_minimal_dxf()
        msp = doc.modelspace()
        # Column at (1000, 1000) - size 400x400
        msp.add_lwpolyline([(1000, 1000), (1400, 1000), (1400, 1400), (1000, 1400), (1000, 1000)], dxfattribs={"layer": "DCE_Cot"})
        # Text label placed exactly inside the column (1100, 1100)
        msp.add_text("C1 400x400", dxfattribs={"layer": "DCE_Name", "height": 250, "insert": (1100, 1100, 0)})
        doc.saveas(self.test_dxf)

        solver = CadCollisionSolver.from_dxf(self.test_dxf)
        collisions = solver.detect_collisions()
        self.assertGreater(len(collisions), 0, "Must detect collision between text and column")
        self.assertEqual(collisions[0].entity_text, "C1 400x400")

    def test_03_resolve_and_displace_colliding_label(self):
        doc = self._create_minimal_dxf()
        msp = doc.modelspace()
        # Column at (1000, 1000)
        msp.add_lwpolyline([(1000, 1000), (1400, 1000), (1400, 1400), (1000, 1400), (1000, 1000)], dxfattribs={"layer": "DCE_Cot"})
        # Text inside column
        text_ent = msp.add_text("C1", dxfattribs={"layer": "DCE_Name", "height": 250, "insert": (1100, 1100, 0)})
        orig_handle = text_ent.dxf.handle
        doc.saveas(self.test_dxf)

        # Run solver with real application
        out_dxf = Path(self.temp_dir.name) / "resolved.dxf"
        solver = CadCollisionSolver.from_dxf(self.test_dxf)
        res = solver.solve_all(dry_run=False, output_path=out_dxf)

        self.assertEqual(res["status"], "OK")
        self.assertEqual(res["displacements_applied"], 1)

        # Reload and verify new text position
        reloaded = ezdxf.readfile(out_dxf)
        moved_text = reloaded.entitydb.get(orig_handle)
        new_insert = moved_text.dxf.insert
        self.assertNotEqual((new_insert[0], new_insert[1]), (1100, 1100), "Text must be displaced from original location")

        # Verify no collisions in reloaded drawing
        new_solver = CadCollisionSolver.from_dxf(out_dxf)
        self.assertEqual(len(new_solver.detect_collisions()), 0, "No collisions should remain after displacement")

    def test_04_automatic_leader_line_generation(self):
        doc = self._create_minimal_dxf()
        msp = doc.modelspace()
        # Large structural zone around (0, 0) forcing displacement > 300mm
        msp.add_lwpolyline([(-200, -200), (600, -200), (600, 600), (-200, 600), (-200, -200)], dxfattribs={"layer": "DCE_Cot"})
        msp.add_text("BIG_LABEL", dxfattribs={"layer": "DCE_Name", "height": 250, "insert": (100, 100, 0)})
        doc.saveas(self.test_dxf)

        out_dxf = Path(self.temp_dir.name) / "with_leader.dxf"
        solver = CadCollisionSolver.from_dxf(self.test_dxf)
        res = solver.solve_all(dry_run=False, output_path=out_dxf)

        self.assertGreater(res["leaders_created"], 0, "Leader line must be created for displacement > 300mm")
        self.assertTrue(res["plans"][0]["needs_leader"])

        # Check line entity created in modelspace
        reloaded = ezdxf.readfile(out_dxf)
        lines = [e for e in reloaded.modelspace() if e.dxftype() == "LINE" and e.dxf.layer == "DCE_Leader"]
        self.assertGreaterEqual(len(lines), 1, "Must find newly created leader line")

    def test_05_dry_run_mode_does_not_modify_file(self):
        doc = self._create_minimal_dxf()
        msp = doc.modelspace()
        msp.add_lwpolyline([(0, 0), (400, 0), (400, 400), (0, 400), (0, 0)], dxfattribs={"layer": "DCE_Cot"})
        msp.add_text("C1", dxfattribs={"layer": "DCE_Name", "height": 250, "insert": (100, 100, 0)})
        doc.saveas(self.test_dxf)

        stat_before = self.test_dxf.stat()
        solver = CadCollisionSolver.from_dxf(self.test_dxf)
        res = solver.solve_all(dry_run=True)

        self.assertEqual(res["status"], "DRY_RUN_OK")
        self.assertEqual(res["displacements_applied"], 0)
        self.assertEqual(self.test_dxf.stat().st_size, stat_before.st_size, "File size must remain untouched in dry_run")

    def test_06_two_close_labels_mutual_avoidance(self):
        doc = self._create_minimal_dxf()
        msp = doc.modelspace()
        # Two text labels overlapping each other
        msp.add_text("LABEL_A", dxfattribs={"layer": "DCE_Name", "height": 250, "insert": (500, 500, 0)})
        msp.add_text("LABEL_B", dxfattribs={"layer": "DCE_Name", "height": 250, "insert": (520, 510, 0)})
        doc.saveas(self.test_dxf)

        out_dxf = Path(self.temp_dir.name) / "avoided.dxf"
        solver = CadCollisionSolver.from_dxf(self.test_dxf)
        res = solver.solve_all(dry_run=False, output_path=out_dxf)

        self.assertGreaterEqual(res["displacements_applied"], 1)

        # Check collision count decreased
        reloaded_solver = CadCollisionSolver.from_dxf(out_dxf)
        remaining = reloaded_solver.detect_collisions()
        self.assertEqual(len(remaining), 0, "Labels must not overlap after solving")

    def test_07_nested_scaled_rotated_block(self):
        doc = self._create_minimal_dxf()
        inner = doc.blocks.new("inner")
        inner.add_lwpolyline([(0,0),(1000,0),(1000,200),(0,200)], close=True)
        outer = doc.blocks.new("outer")
        outer.add_blockref("inner", (0,0))
        ref = doc.modelspace().add_blockref("outer", (100,200), dxfattribs={"rotation":90,"xscale":2,"yscale":3})
        box = CadSceneIndex(doc).grid.entities[ref.dxf.handle].bbox
        self.assertLessEqual(box.min_x, -500)
        self.assertGreaterEqual(box.max_y, 2200)

    def test_08_unicode_rotated_aligned_text_preserved(self):
        import unicodedata
        doc = self._create_minimal_dxf()
        from ezdxf.enums import TextEntityAlignment
        text = unicodedata.normalize("NFD", "D\u1ea6M CH\u00c9O T\u1ea6NG \u0110I\u1ec2N H\u00ccNH")
        ent = doc.modelspace().add_text(text, dxfattribs={"layer":"DCE_Name","height":250,"rotation":137})
        ent.set_placement((100,100), align=TextEntityAlignment.MIDDLE_CENTER)
        box = CadSceneIndex(doc).grid.entities[ent.dxf.handle].bbox
        self.assertGreater(box.width, 250)
        self.assertGreater(box.height, 250)
        ent.translate(500,700,0)
        self.assertEqual(ent.dxf.text,text)
        self.assertEqual(ent.dxf.rotation,137)
        self.assertEqual(ent.dxf.align_point.x,600)

    def test_09_mtext_rotation_and_paragraphs(self):
        doc = self._create_minimal_dxf()
        ent = doc.modelspace().add_mtext("{\\C1;C\u1ed8T}\\PT\u1ea6NG 40",dxfattribs={"layer":"DCE_Name","char_height":250,"rotation":90,"width":1000})
        box = CadSceneIndex(doc).grid.entities[ent.dxf.handle].bbox
        self.assertGreater(box.height,500)
        self.assertGreater(box.width,250)

    def test_10_dry_run_repeat_restores_index(self):
        doc = self._create_minimal_dxf()
        for x in (900,920,940):
            doc.modelspace().add_text("C\u1ed8T",dxfattribs={"layer":"DCE_Name","height":250,"insert":(x,100,0)})
        solver = CadCollisionSolver(CadSceneIndex(doc,cell_size=100))
        first = solver.solve_all(dry_run=True)
        second = solver.solve_all(dry_run=True)
        self.assertEqual(first,second)

    def test_11_blocked_region_reports_unresolved(self):
        doc = self._create_minimal_dxf()
        doc.modelspace().add_lwpolyline([(-10000,-10000),(10000,-10000),(10000,10000),(-10000,10000)],close=True,dxfattribs={"layer":"DCE_Cot"})
        doc.modelspace().add_text("C1",dxfattribs={"layer":"DCE_Name","height":250})
        result=CadCollisionSolver(CadSceneIndex(doc)).solve_all(dry_run=True)
        self.assertEqual(result["status"],"NEEDS_REVIEW")
        self.assertEqual(result["displacements_planned"],0)

    def test_12_locked_layer_and_user_override(self):
        doc=self._create_minimal_dxf()
        ent=doc.modelspace().add_text("LOCKED",dxfattribs={"layer":"DCE_Name","height":250})
        doc.layers.get("DCE_Name").lock()
        self.assertFalse(CadSceneIndex(doc).grid.entities[ent.dxf.handle].is_movable)
        doc.layers.get("DCE_Name").unlock()
        doc.appids.new("DCE_USER_OVERRIDE")
        ent.set_xdata("DCE_USER_OVERRIDE",[(1000,"locked")])
        self.assertFalse(CadSceneIndex(doc).grid.entities[ent.dxf.handle].is_movable)

    def test_13_grid_relocation_crosses_cells(self):
        from tools.cad_scene_index import CadSpatialGrid,SceneEntity
        grid=CadSpatialGrid(100)
        ent=SceneEntity("A","TEXT","DCE_Name",bbox=BoundingBox(0,0,20,20))
        grid.insert(ent);grid.remove(ent)
        ent.bbox=BoundingBox(2000,2000,2020,2020);grid.insert(ent)
        self.assertEqual(grid.query_bbox(BoundingBox(0,0,20,20)),[])
        self.assertEqual(grid.query_bbox(ent.bbox),[ent])

    def test_14_block_attributes_translate_with_insert(self):
        doc=self._create_minimal_dxf()
        block=doc.blocks.new("TenCauKien")
        block.add_attdef("NAME",(0,0),height=250)
        ent=doc.modelspace().add_blockref("TenCauKien",(100,100),dxfattribs={"layer":"DCE_Name"})
        ent.add_auto_attribs({"NAME":"C\u1ed8T 40"})
        doc.modelspace().add_lwpolyline([(0,0),(500,0),(500,500),(0,500)],close=True,dxfattribs={"layer":"DCE_Cot"})
        before=ent.attribs[0].dxf.insert
        result=CadCollisionSolver(CadSceneIndex(doc)).solve_all(output_path=Path(self.temp_dir.name)/"attrs.dxf")
        delta=result["plans"][0]["delta"]
        self.assertAlmostEqual(ent.attribs[0].dxf.insert.x-before.x,delta[0])
        self.assertAlmostEqual(ent.attribs[0].dxf.insert.y-before.y,delta[1])

    def test_15_cloud_output_rejected_before_mutation(self):
        doc=self._create_minimal_dxf()
        ent=doc.modelspace().add_text("A",dxfattribs={"layer":"DCE_Name","height":250})
        from dce_virtual_drive_guard import UnsafeScratchPath
        with self.assertRaises(UnsafeScratchPath):
            CadCollisionSolver(CadSceneIndex(doc)).solve_all(output_path="G:/My Drive/should_not_exist.dxf")
        self.assertEqual(tuple(ent.dxf.insert),(0,0,0))

    def test_17_title_region_fixed_beam_tag_movable(self):
        doc = self._create_minimal_dxf()
        doc.layers.new("DCE_Frame")
        doc.modelspace().add_lwpolyline([(10000,0),(28000,0),(28000,5500),(10000,5500)], close=True, dxfattribs={"layer":"DCE_Frame"})
        title = doc.modelspace().add_text("TITLE", dxfattribs={"layer":"DCE_Name","insert":(11000,1000),"height":250})
        block = doc.blocks.new("Dce_KhTenDam")
        block.add_text("BEAM", dxfattribs={"height":250})
        tag = doc.modelspace().add_blockref("Dce_KhTenDam", (100,100), dxfattribs={"layer":"DCE_Name","rotation":37})
        scene = CadSceneIndex(doc)
        self.assertFalse(scene.grid.entities[title.dxf.handle].is_movable)
        self.assertTrue(scene.grid.entities[tag.dxf.handle].is_movable)

    def test_18_leader_segment_uses_segment_not_aabb(self):
        hit = CadCollisionSolver._segment_hits_box
        self.assertTrue(hit((0,0),(100,100),BoundingBox(45,45,55,55)))
        self.assertFalse(hit((0,0),(100,100),BoundingBox(0,80,20,100)))
        self.assertTrue(hit((10,0),(10,100),BoundingBox(5,40,15,60)))

    def test_19_slab_boundary_semantics_does_not_erase_solid_obstacles(self):
        doc = self._create_minimal_dxf()
        doc.layers.new('DCE_BaoBeTong');doc.appids.new('DCE_SCENE')
        slab = doc.modelspace().add_lwpolyline([(0,0),(57000,0),(57000,28000),(0,28000)],close=True,dxfattribs={'layer':'DCE_BaoBeTong'})
        slab.set_xdata('DCE_SCENE',[(1000,'boundary_only')])
        label = doc.modelspace().add_text('FLOOR',dxfattribs={'layer':'DCE_Name','height':250,'insert':(5000,5000)})
        self.assertEqual(CadCollisionSolver(CadSceneIndex(doc)).detect_collisions(),[])
        doc.modelspace().add_lwpolyline([(4900,4900),(5500,4900),(5500,5500),(4900,5500)],close=True,dxfattribs={'layer':'DCE_Cot'})
        self.assertTrue(CadCollisionSolver(CadSceneIndex(doc)).detect_collisions())
        self.assertEqual(label.dxf.insert.x,5000)

    def test_20_dimension_empty_interior_is_not_a_solid(self):
        doc = self._create_minimal_dxf()
        dim = doc.modelspace().add_linear_dim(base=(0,5000),p1=(0,0),p2=(10000,0),override={'dimtxt':100,'dimasz':100})
        dim.render()
        doc.modelspace().add_text('FREE',dxfattribs={'layer':'DCE_Name','height':100,'insert':(4500,2500)})
        self.assertEqual(CadCollisionSolver(CadSceneIndex(doc)).detect_collisions(),[])

    def test_21_diagonal_line_narrow_phase(self):
        doc = self._create_minimal_dxf()
        doc.modelspace().add_line((0,0),(10000,10000),dxfattribs={'layer':'DCE_Cot'})
        doc.modelspace().add_text('FREE',dxfattribs={'layer':'DCE_Name','height':100,'insert':(0,8000)})
        self.assertEqual(CadCollisionSolver(CadSceneIndex(doc)).detect_collisions(),[])

    def test_22_metre_and_millimetre_physical_equivalence(self):
        results=[]
        for unit,scale in ((4,1),(6,0.001)):
            doc=self._create_minimal_dxf();doc.header['$INSUNITS']=unit
            doc.modelspace().add_lwpolyline([(0,0),(400*scale,0),(400*scale,400*scale),(0,400*scale)],close=True,dxfattribs={'layer':'DCE_Cot'})
            doc.modelspace().add_text('C1',dxfattribs={'layer':'DCE_Name','height':250*scale,'insert':(100*scale,100*scale)})
            result=CadCollisionSolver(CadSceneIndex(doc)).solve_all(dry_run=True)
            self.assertEqual(result['status'],'DRY_RUN_OK')
            results.append(result['plans'][0]['distance_mm'])
        self.assertAlmostEqual(*results,places=1)

    def test_23_unitless_rejected(self):
        doc=self._create_minimal_dxf();doc.header['$INSUNITS']=0
        with self.assertRaisesRegex(ValueError,'INSUNITS'):
            CadSceneIndex(doc)

    def test_24_locked_label_conflict_requires_review(self):
        doc=self._create_minimal_dxf()
        doc.modelspace().add_text('KEEP',dxfattribs={'layer':'DCE_Name','height':250})
        doc.layers.get('DCE_Name').lock()
        doc.modelspace().add_lwpolyline([(-100,-100),(400,-100),(400,400),(-100,400)],close=True,dxfattribs={'layer':'DCE_Cot'})
        result=CadCollisionSolver(CadSceneIndex(doc)).solve_all(dry_run=True)
        self.assertEqual(result['status'],'NEEDS_REVIEW')
        self.assertEqual(result['displacements_planned'],0)
        self.assertGreater(result['remaining_collision_count'],0)

    def test_25_persisted_leader_and_repeat_are_clean(self):
        doc=self._create_minimal_dxf()
        doc.modelspace().add_lwpolyline([(-200,-200),(600,-200),(600,600),(-200,600)],close=True,dxfattribs={'layer':'DCE_Cot'})
        doc.modelspace().add_text('COLUMN',dxfattribs={'layer':'DCE_Name','height':250,'insert':(100,100)})
        path=Path(self.temp_dir.name)/'leader.dxf'
        result=CadCollisionSolver(CadSceneIndex(doc)).solve_all(output_path=path)
        self.assertEqual(result['status'],'OK')
        self.assertTrue(result['leader_paths'])
        fresh=CadCollisionSolver.from_dxf(path)
        self.assertEqual(fresh.detect_leader_conflicts(),[])
        repeat=fresh.solve_all(dry_run=True)
        self.assertEqual(repeat['displacements_planned'],0)
        self.assertEqual(repeat['status'],'DRY_RUN_OK')

    def test_26_corrupt_leader_crossing_is_detected(self):
        doc=self._create_minimal_dxf();doc.appids.new('DCE_COLLISION')
        owner=doc.modelspace().add_text('OWNER',dxfattribs={'layer':'DCE_Name','height':100,'insert':(5000,5000)})
        line=doc.modelspace().add_line((-1000,0),(1000,0),dxfattribs={'layer':'DCE_Name'})
        line.set_xdata('DCE_COLLISION',[(1000,'leader'),(1005,owner.dxf.handle),(1005,'0'),(1070,0)])
        doc.modelspace().add_lwpolyline([(-100,-100),(100,-100),(100,100),(-100,100)],close=True,dxfattribs={'layer':'DCE_Cot'})
        solver=CadCollisionSolver(CadSceneIndex(doc))
        self.assertTrue(solver.detect_leader_conflicts())
        self.assertEqual(solver.solve_all(dry_run=True)['status'],'NEEDS_REVIEW')

    def test_27_dry_run_restores_rotated_geometry_exactly(self):
        doc=self._create_minimal_dxf()
        for x in (1.125,10.375):
            doc.modelspace().add_text('ROTATED',dxfattribs={'layer':'DCE_Name','height':250,'rotation':37.7,'insert':(x,12.625)})
        solver=CadCollisionSolver(CadSceneIndex(doc))
        before={e.handle:e.geometry.wkb for e in solver.scene.movable_entities}
        first=solver.solve_all(dry_run=True)
        self.assertEqual(before,{e.handle:e.geometry.wkb for e in solver.scene.movable_entities})
        self.assertEqual(first,solver.solve_all(dry_run=True))

    def test_28_both_tower_sheets_reopen_clean(self):
        import importlib.util
        from ezdxf.lldxf.tagwriter import TagCollector
        path=AGENTS_ROOT/'skills/Technical_Illustrator/cad_integration/cad_plan_engine.py'
        spec=importlib.util.spec_from_file_location('collision_test_plan',path)
        engine=importlib.util.module_from_spec(spec);sys.modules[spec.name]=engine;spec.loader.exec_module(engine)
        for method in ('render_sheet_kc02','render_sheet_kc03'):
            with self.subTest(method=method):
                plan=engine.DcePlanEngine(engine.build_structural_model());plan.setup();getattr(plan,method)()
                source=Path(self.temp_dir.name)/(method+'_source.dxf')
                plan.save(str(source))
                solver=CadCollisionSolver.from_dxf(source)
                handles={e.handle for e in solver.scene.movable_entities}
                fixed={e.dxf.handle:TagCollector.dxftags(e) for e in solver.doc.modelspace() if e.dxf.handle not in handles}
                output=Path(self.temp_dir.name)/(method+'.dxf')
                result=solver.solve_all(output_path=output)
                self.assertEqual(result['status'],'OK')
                fresh=CadCollisionSolver.from_dxf(output)
                self.assertEqual(fresh.detect_collisions(),[])
                self.assertEqual(fresh.detect_leader_conflicts(),[])
                for h,value in fixed.items():
                    self.assertEqual(TagCollector.dxftags(fresh.doc.entitydb[h]),value,msg=h)

    def test_29_unroutable_leader_does_not_partially_apply(self):
        from unittest.mock import patch
        doc=self._create_minimal_dxf()
        label=doc.modelspace().add_text('COLUMN',dxfattribs={'layer':'DCE_Name','height':250,'insert':(100,100)})
        doc.modelspace().add_lwpolyline([(-200,-200),(600,-200),(600,600),(-200,600)],close=True,dxfattribs={'layer':'DCE_Cot'})
        solver=CadCollisionSolver(CadSceneIndex(doc));before=tuple(label.dxf.insert)
        with patch.object(solver,'_route',return_value=None):
            result=solver.solve_all(output_path=Path(self.temp_dir.name)/'no_partial.dxf')
        self.assertEqual(result['status'],'NEEDS_REVIEW')
        self.assertEqual(tuple(label.dxf.insert),before)
        self.assertFalse(result['output_dxf'])
        self.assertEqual(result['displacements_applied'],0)

    def test_30_generated_member_attributes_are_visible_and_separate(self):
        import importlib.util
        path=AGENTS_ROOT/'skills/Technical_Illustrator/cad_integration/cad_plan_engine.py'
        spec=importlib.util.spec_from_file_location('collision_label_plan',path)
        module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
        engine=module.DcePlanEngine(module.build_structural_model());engine.setup()
        engine._insert_member_tag(10000,10000,1000,'C1','800x1000')
        engine._add_beam_tag(20000,20000,'D1 (400x800)',37)
        scene=CadSceneIndex(engine.doc)
        labels=[e for e in engine.doc.modelspace().query('INSERT') if e.dxf.name in {'TenCauKien','Dce_KhTenDam'}]
        self.assertEqual(len(labels),2)
        for label in labels:
            self.assertEqual(len(label.attribs),2)
            for att in label.attribs:
                self.assertTrue(att.dxf.text)
                self.assertEqual(att.dxf.true_color,0x1E3246)
                self.assertEqual(att.dxf.rotation,0)
            a,b=label.attribs
            self.assertFalse(scene._geometry(a).intersects(scene._geometry(b)))

    def test_16_source_overwrite_rejected(self):
        doc=self._create_minimal_dxf();doc.saveas(self.test_dxf)
        with self.assertRaises(ValueError):
            CadCollisionSolver.from_dxf(self.test_dxf).solve_all(output_path=self.test_dxf)

    def _leader_fixture(self):
        doc = self._create_minimal_dxf()
        doc.modelspace().add_lwpolyline([(-200,-200),(600,-200),(600,600),(-200,600)], close=True, dxfattribs={'layer':'DCE_Cot'})
        doc.modelspace().add_text('BIG_LABEL', dxfattribs={'layer':'DCE_Name','height':250,'insert':(100,100)})
        return doc

    def test_31_no_source_micro_leader_is_suppressed(self):
        doc = self._create_minimal_dxf()
        for x,y,text in ((500,500,'LABEL_A'),(520,510,'LABEL_B')):
            doc.modelspace().add_text(text, dxfattribs={'layer':'DCE_Name','height':250,'insert':(x,y)})
        result = CadCollisionSolver(CadSceneIndex(doc)).solve_all(output_path=self.test_dxf)
        self.assertEqual(result['status'], 'OK')
        self.assertGreater(result['displacements_applied'], 0)
        self.assertEqual(result['leaders_created'], 0)
        self.assertEqual(result['remaining_collision_count'], 0)

    def test_32_layer_creation_failure_cannot_fallback_or_commit(self):
        from unittest.mock import patch
        doc = self._leader_fixture()
        before = [(e.dxf.handle, str(e.dxf.all_existing_dxf_attribs())) for e in doc.modelspace()]
        original = doc.layers.add
        appids_before = list(doc.appids.entries)
        def fail(name, *args, **kwargs):
            if name == 'DCE_Leader':
                raise OSError('injected failure')
            return original(name, *args, **kwargs)
        with patch.object(doc.layers, 'add', side_effect=fail):
            result = CadCollisionSolver(CadSceneIndex(doc)).solve_all(output_path=self.test_dxf)
        self.assertEqual(result['status'], 'NEEDS_REVIEW')
        self.assertEqual(result['displacements_applied'], 0)
        self.assertEqual(result['leaders_created'], 0)
        self.assertIsNone(result['output_dxf'])
        self.assertEqual(appids_before, list(doc.appids.entries))
        self.assertTrue(result['apply_errors'])
        self.assertEqual(before, [(e.dxf.handle, str(e.dxf.all_existing_dxf_attribs())) for e in doc.modelspace()])

    def test_33_dry_run_preserves_layer_and_appid_tables(self):
        doc = self._leader_fixture()
        before = (list(doc.layers.entries), list(doc.appids.entries))
        result = CadCollisionSolver(CadSceneIndex(doc)).solve_all(dry_run=True)
        self.assertEqual(result['status'], 'DRY_RUN_OK')
        self.assertEqual(before, (list(doc.layers.entries), list(doc.appids.entries)))

    def test_34_dedicated_leader_layer_is_normalized(self):
        doc = self._leader_fixture()
        layer = doc.layers.new('DCE_Leader', dxfattribs={'color':1})
        layer.off(); layer.freeze(); layer.lock()
        result = CadCollisionSolver(CadSceneIndex(doc)).solve_all(output_path=self.test_dxf)
        self.assertEqual(result['status'], 'OK')
        self.assertEqual(layer.dxf.color, 250)
        self.assertFalse(layer.is_off() or layer.is_frozen() or layer.is_locked())
        self.assertTrue(all(e.dxf.layer == 'DCE_Leader' and e.dxf.color == 250
                            for e in doc.modelspace().query('LINE') if e.has_xdata('DCE_COLLISION')))

    def test_35_leader_length_boundary_after_shortening(self):
        solver = CadCollisionSolver(CadSceneIndex(self._create_minimal_dxf()))
        for final, expected in ((99.9,'SKIPPED_PROXIMITY'),(100.0,'OK'),(100.1,'OK')):
            result = solver._add_leader((0,0,10,10), (final+25,0,final+35,10), source_point=(0,0), dry_run=True)
            self.assertEqual(result['status'], expected)
            self.assertAlmostEqual(result['final_length'], final)


if __name__ == "__main__":
    unittest.main()
