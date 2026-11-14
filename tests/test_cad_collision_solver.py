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
        lines = [e for e in reloaded.modelspace() if e.dxftype() == "LINE" and e.dxf.layer == "DCE_Name"]
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


if __name__ == "__main__":
    unittest.main()
