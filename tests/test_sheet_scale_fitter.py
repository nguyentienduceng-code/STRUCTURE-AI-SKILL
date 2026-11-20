# -*- coding: utf-8 -*-
"""
test_sheet_scale_fitter.py — Dynamic Sheet-Scale Governor (Directive v5.0)
==========================================================================
AC1/AC2 + regression guard cho tools/sheet_scale_fitter.py:
  - AC1: solver tự đề xuất đúng (khung, S) theo công thức fill-ratio directive
    (KHÔNG nhồi đáp án — assert đúng công thức; điểm AC1 không tái sinh được
    từ công thức được ghi nhận trong test bằng force_scale).
  - AC2: fill-window [0.65, 0.85] => kích thước 4 tầng dim luôn nằm gọn
    canvas hữu dụng (không tràn sidebar / title band).
  - Regression: đường mặc định engine (không scale_spec) giữ nguyên 100%.
"""

import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

AGENTS = Path(__file__).resolve().parent.parent
FITTER = AGENTS / "tools" / "sheet_scale_fitter.py"
ENGINE = AGENTS / "skills" / "Technical_Illustrator" / "cad_integration" / "cad_plan_engine.py"


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, str(path))
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


class TestSheetScaleSolverAC1(unittest.TestCase):
    """AC1 — 3 ca thực chiến: solver đề xuất (khung, S) theo đúng công thức."""

    @classmethod
    def setUpClass(cls):
        cls.f = _load(FITTER, "dce_ssf")

    def test_kc02_picks_a1_100(self):
        d = self.f.SheetScaleSolver().solve(36000.0, 24000.0, "A1")
        self.assertEqual(d.sheet_size, "A1")
        self.assertEqual(d.scale, 100.0)
        self.assertEqual(d.scale_label, "1/100")
        self.assertTrue(0.65 <= d.fill_ratio <= 0.85)

    def test_kc03_picks_a1_100(self):
        d = self.f.SheetScaleSolver().solve(36000.0, 24000.0, "A1")
        self.assertEqual((d.sheet_size, d.scale), ("A1", 100.0))

    def test_kc01_pick_within_band_and_a1(self):
        """KC-01 45x32: công thức fill => A1, nghiệm in-band.

        LƯU Ý trung thực (RFC/AC): mục tiêu AC1 "A1 1:200 @ 78%" KHÔNG tái
        sinh được từ chính công thức directive (1:200 => fill 52.7% ngoài band;
        band + 'ưu tiên 1:100 nếu fill<=0.85' => 1:100 fill 91% nên không áp;
        nghiệm in-band duy nhất là 1:125 @ 75.8%). Test khóa kết quả CÔNG THỨC
        (1:125 in-band), và force_scale=200 là escape-hatch tới mục tiêu AC.
        """
        d = self.f.SheetScaleSolver().solve(45000.0, 32000.0, "A1")
        self.assertEqual(d.sheet_size, "A1")
        self.assertTrue(d.in_fill_band)
        self.assertEqual(d.scale, 125.0)  # nghiệm in-band của công thức, KHÔNG nhồi 200
        forced = self.f.SheetScaleSolver().solve(45000.0, 32000.0, "A1", force_scale=200.0)
        self.assertEqual(forced.scale, 200.0)
        self.assertFalse(forced.in_fill_band)  # trung thực: 1:200 nằm ngoài band

    def test_formula_verbatim(self):
        """Công thức fill khớp nguyên văn directive (canvas = W-255, H-20; ext = fp+84S)."""
        fx, fy, fill = self.f.fill_ratio(36000.0, 24000.0, "A1", 100.0)
        self.assertAlmostEqual(fx, (36000.0 + 84 * 100.0) / ((841.0 - 255.0) * 100.0), places=6)
        self.assertAlmostEqual(fy, (24000.0 + 84 * 100.0) / ((594.0 - 20.0) * 100.0), places=6)
        self.assertAlmostEqual(fill, max(fx, fy), places=9)

    def test_real_model_footprint(self):
        """Model chuẩn .agents (57x28m) => A1 1:150 (in-band, gần 0.75 nhất)."""
        d = self.f.SheetScaleSolver().solve(57000.0, 28000.0, "A1")
        self.assertEqual(d.sheet_size, "A1")
        self.assertTrue(d.in_fill_band)
        self.assertEqual(d.scale, 150.0)

    def test_cli_selftest_runs(self):
        """Chạy CLI standalone (câu lệnh AC1): python sheet_scale_fitter.py.

        Force UTF-8 (AGENTS.md §2) qua env PYTHONUTF8 — console Windows
        mặc định cp1252 sẽ lỗi khi decode stdout tiếng Việt.
        """
        env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
        r = subprocess.run([sys.executable, "-B", str(FITTER)],
                           capture_output=True, timeout=120,
                           cwd=str(AGENTS), env=env)
        out = r.stdout.decode("utf-8", errors="replace")
        err = r.stderr.decode("utf-8", errors="replace")
        self.assertEqual(r.returncode, 0, err[-500:])
        self.assertIn("SheetScaleSolver", out)
        self.assertIn("A1 1/100", out)  # KC-02/KC-03 => A1 1:100 (AC1)


class TestAC2CanvasContainment(unittest.TestCase):
    """AC2 — fill-window bảo đảm 4 tầng dim nằm trong canvas hữu dụng."""

    @classmethod
    def setUpClass(cls):
        cls.f = _load(FITTER, "dce_ssf")

    def test_extents_within_canvas_when_in_band(self):
        for fp, hh in [(36000.0, 24000.0), (45000.0, 32000.0), (57000.0, 28000.0)]:
            d = self.f.SheetScaleSolver().solve(fp, hh, "A1")
            self.assertTrue(d.in_fill_band)
            cx, cy = d.canvas_paper
            S = d.scale
            # (fp + 84S)/(cx*S)  <=  0.85  <=>  kích thước 4 tầng dim (mỗi bên
            # 42S) luôn nằm gọn canvas hữu dụng => không xâm phạm Sidebar
            # (220mm) / Title band (45mm) (AC2).
            self.assertLessEqual(d.ext_w_mm / (cx * S), 0.85 + 1e-9,
                                 f"W_ext vượt canvas @ {d.scale_label}")
            self.assertLessEqual(d.ext_h_mm / (cy * S), 0.85 + 1e-9)

    def test_sidebar_and_title_band_paper_deductions(self):
        """Canvas hữu dụng = (W-255, H-20) đúng chỉ tiêu (220 sidebar + 25+10 lề; 45 title band)."""
        self.assertEqual(self.f.canvas_paper("A1"), (841.0 - 255.0, 594.0 - 20.0))
        self.assertEqual(self.f.canvas_paper("A0"), (1189.0 - 255.0, 841.0 - 20.0))
        self.assertEqual(self.f.canvas_paper("A2"), (594.0 - 255.0, 420.0 - 20.0))


class TestEngineRegressionAndGovernor(unittest.TestCase):
    """Engine: đường mặc định giữ nguyên 100%; governor áp DimStyle động theo S."""

    @classmethod
    def setUpClass(cls):
        cls.cpe = _load(ENGINE, "dce_cpe_probe")
        cls.f = _load(FITTER, "dce_ssf_probe")
        cls.tmp = Path(tempfile.mkdtemp(prefix="ssf_engine_"))

    @classmethod
    def tearDownClass(cls):
        import shutil
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def _quiet(self, fn):
        import contextlib, io
        with contextlib.redirect_stdout(io.StringIO()):
            return fn()

    def test_default_path_unaffected(self):
        p = self.tmp / "default.dxf"
        self._quiet(lambda: self.cpe.export_dce_plan(str(p), sheet_type="KC-02"))
        self.assertTrue(p.is_file())
        import ezdxf
        doc = ezdxf.readfile(str(p))
        # Khung tên mặc định KC-02 giữ nguyên "TỶ LỆ: 1/100" (chưa governor)
        texts = [e.dxf.text for e in doc.modelspace() if e.dxftype() == "TEXT"]
        self.assertTrue(any("TỶ LỆ: 1/100" in t for t in texts),
                        "đường mặc định bị governor thay đổi — VI PHẠM regression")
        self.assertFalse(any("TỶ LỆ: 1/150" in t for t in texts))

    def test_governor_overrides_label_and_dimstyle(self):
        p = self.tmp / "governor.dxf"
        d = self.f.SheetScaleSolver().solve(57000.0, 28000.0, "A1")
        eng = self._quiet(lambda: self.cpe.export_dce_plan(
            str(p), sheet_type="KC-02", scale_spec=d.as_dict()))
        self.assertTrue(p.is_file())
        import ezdxf
        doc = ezdxf.readfile(str(p))
        texts = [e.dxf.text for e in doc.modelspace() if e.dxftype() == "TEXT"]
        self.assertTrue(any(f"TỶ LỆ: {d.scale_label}" in t for t in texts),
                        "governor không ghi nhãn tỷ lệ vào khung tên")
        # DimStyle động theo S (Nhiệm vụ 2): Dce_{S}MV tồn tại với dimscale
        ds = doc.dimstyles.get(f"Dce_{int(d.scale)}MV")
        self.assertIsNotNone(ds, f"thiếu dimstyle Dce_{int(d.scale)}MV")
        self.assertEqual(ds.dxf.dimtxt, round(2.2 * d.scale, 2))
        self.assertEqual(ds.dxf.dimasz, round(1.2 * d.scale, 2))
        self.assertEqual(ds.dxf.dimdle, round(1.0 * d.scale, 2))
        self.assertEqual(eng.print_scale, d.scale)

    def test_governor_dxf_passes_audit(self):
        """DXF governor: 0 audit error, hatch/đủ entity (không phá graphic_sanity)."""
        p = self.tmp / "gov_audit.dxf"
        d = self.f.SheetScaleSolver().solve(57000.0, 28000.0, "A1")
        self._quiet(lambda: self.cpe.export_dce_plan(
            str(p), sheet_type="KC-02", scale_spec=d.as_dict()))
        import ezdxf
        doc = ezdxf.readfile(str(p))
        self.assertEqual(len(doc.audit().errors), 0)
        n_ent = sum(1 for _ in doc.modelspace())
        self.assertGreater(n_ent, 300)


if __name__ == "__main__":
    unittest.main()
