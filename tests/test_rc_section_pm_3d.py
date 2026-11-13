#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Suite 24: independent mechanics, biaxial equilibrium and adversarial tests.

Legacy comparisons use the same section moments, including the legacy column's
accidental eccentricity. They do NOT pretend its rectangular stress block or
member magnification is identical to nonlinear strain compatibility.
"""
import importlib.util
import json
import math
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

if hasattr(sys.stdout, 'reconfigure') and sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT/'skills/Structural_Design_Engineer/scripts'
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(ROOT/'tools'))
from calc_rc_section_pm_3d import FiberSection, calc_rc_section_pm_3d
from calc_rc_section import calc_rc_beam
from calc_rc_column import calc_rc_column
from citation_grounding_auditor import CitationGroundingAuditor


def layout():
    return [dict(x=x, y=y, dia=25) for x, y in [(-150, -150), (0, -150), (150, -150),
        (-150, 0), (150, 0), (-150, 150), (0, 150), (150, 150)]]


def calculate(**kwargs):
    options = dict(bars=layout(), generate_surface=False)
    options.update(kwargs)
    return calc_rc_section_pm_3d(**options)


class FiberMechanicsTests(unittest.TestCase):
    def test_01_pure_compression_equals_net_concrete_plus_steel(self):
        result = calculate(N_ed=1500, Mx_ed=0, My_ed=0)
        area = 8*math.pi*25**2/4
        expected = (17*(400*400-area)+350*area)/1000
        self.assertTrue(result['converged'])
        self.assertAlmostEqual(result['capacity']['N_Rd_kN'], expected, places=9)
        self.assertAlmostEqual(result['eta'], 1500/expected, places=10)
        self.assertAlmostEqual(result['strain_plane']['epsilon_0'], .002)
        self.assertAlmostEqual(result['strain_utilization'], 1.)
        self.assertFalse(result['approved'])  # No input sources were invented.

    def test_same_sign_compression_uses_equation_86(self):
        section = FiberSection(400, 400, layout())
        for ratio in [0., .25, .8, 1.]:
            q = section.boundary_plane(.3, ratio)
            self.assertAlmostEqual(float((section.V@q).max()), .0035-.0015*ratio, places=12)
            self.assertAlmostEqual(section.strain_limit(q), 1., places=12)

    def test_asymmetric_layout_pure_axial_capacity_enforces_zero_moments(self):
        r = calculate(bars=[dict(x=0, y=120, area=500)], Mx_ed=0, My_ed=0)
        self.assertTrue(r['converged'])
        self.assertGreater(r['iterations'], 0)
        self.assertLess(abs(r['capacity']['Mx_Rd_kNm']), .001)
        self.assertLess(abs(r['capacity']['My_Rd_kNm']), .001)
        self.assertLess(r['capacity']['N_Rd_kN'], r['capacity']['uniform_compression_upper_bound_kN'])

    def test_material_knots_and_distinct_steel_tension_compression(self):
        section = FiberSection(400, 400, layout(), rebar='CB500-V')
        e1 = .6*17/32500
        stress, _ = section.concrete_stress(np.array([-.001, 0, e1, .002, .0035]))
        np.testing.assert_allclose(stress, [0, 0, .6*17, 17, 17])
        stress, _ = section.steel_stress(np.array([-.025, -.0005, .0005, .0035]))
        np.testing.assert_allclose(stress, [-435, -100, 100, 400])

    def test_integrated_tangent_matches_finite_difference(self):
        section = FiberSection(400, 400, layout(), nx=32, ny=35)
        q = np.array([.00071, .00191, .000413])
        _, tangent = section.response(q, tangent=True)
        numerical = np.zeros((3, 3))
        for j in range(3):
            step = np.zeros(3)
            step[j] = 1e-9
            numerical[:, j] = (section.response(q+step)-section.response(q-step))/(2e-9)
        np.testing.assert_allclose(tangent, numerical, rtol=2e-6, atol=.05)

    def test_rectangle_mesh_area_centroid_and_point_bar_replacement(self):
        section = FiberSection(400, 500, [dict(x=10, y=30, area=500)], nx=12, ny=15)
        self.assertEqual(len(section.areas), 180)
        self.assertAlmostEqual(float(section.areas.sum()), 200000)
        np.testing.assert_allclose(section.centroid, [0, 0])
        force = section.response([.002, 0, 0])
        self.assertAlmostEqual(force[0], 17*(200000-500)+350*500)
        self.assertAlmostEqual(force[1], (350-17)*500*30, delta=1e-5)
        self.assertAlmostEqual(force[2], (350-17)*500*10, delta=1e-5)

    def test_l_wall_nonoverlapping_regions_and_centroid(self):
        regions = [dict(x_min=-200, x_max=0, y_min=-300, y_max=300),
                   dict(x_min=0, x_max=400, y_min=-300, y_max=-100)]
        bars = [dict(x=-150, y=250, dia=20), dict(x=-150, y=-250, dia=20), dict(x=350, y=-250, dia=20)]
        section = FiberSection(600, 600, bars, regions=regions, nx=12, ny=12)
        self.assertAlmostEqual(section.gross_area, 200000)
        np.testing.assert_allclose(section.centroid, [20, -80])
        result = calc_rc_section_pm_3d(b=600, h=600, bars=bars, regions=regions,
            N_ed=500, Mx_ed=50, My_ed=30, nx=20, ny=20, generate_surface=False)
        self.assertTrue(result['converged'], result.get('Newton_History'))
        self.assertLess(abs(result['equilibrium_residual']['N_kN']), .001)


class PlanarRegressionTests(unittest.TestCase):
    def test_02_uniaxial_beam_matches_independent_stress_integral_and_legacy_beam(self):
        legacy = calc_rc_beam(b=300, h=600, a=40, concrete='B30', M_ed=250)
        steel_area = legacy['As_chon_mm2']
        bars = [dict(x=-75, y=-260, area=steel_area/2), dict(x=75, y=-260, area=steel_area/2)]
        result = calc_rc_section_pm_3d(b=300, h=600, bars=bars, N_ed=0, Mx_ed=250, My_ed=0,
            nx=16, ny=240, generate_surface=False)
        # Exact integrals of the specified three-segment concrete stress diagram.
        Rb, Eb, e0, eu = 17., 32500., .002, .0035
        e1 = .6*Rb/Eb
        slope = .4*Rb/(e0-e1)
        intercept = .6*Rb-slope*e1
        I0 = Eb*e1**2/2 + slope*(e0**2-e1**2)/2 + intercept*(e0-e1) + Rb*(eu-e0)
        I1 = Eb*e1**3/3 + slope*(e0**3-e1**3)/3 + intercept*(e0**2-e1**2)/2 + Rb*(eu**2-e0**2)/2
        alpha = I0/(Rb*eu)
        beta = 1-I1/(eu*I0)
        depth = 350*steel_area/(Rb*300*alpha)
        expected = 350*steel_area*(560-beta*depth)/1e6
        self.assertTrue(result['converged'])
        self.assertAlmostEqual(result['capacity']['Mx_Rd_kNm']/expected, 1., delta=.001)
        self.assertAlmostEqual(result['capacity']['Mx_Rd_kNm']/250, 1., delta=.025)
        self.assertLess(abs(result['capacity']['My_Rd_kNm']), 1e-5)

    def test_uniaxial_column_uses_legacy_accidental_eccentricity_consistently(self):
        legacy = calc_rc_column(b=400, h=500, a=40, a_prime=40, concrete='B30',
                                N_ed=600, M_ed=180, L0=500)
        bars = [dict(x=x, y=y, area=area/2) for y, area in
                [(-210, legacy['As_chon_mm2']), (210, legacy['As_prime_chon_mm2'])] for x in [-80, 80]]
        effective_M = 180*legacy['eta_uon_doc']+600*legacy['e_a_mm']/1000
        result = calc_rc_section_pm_3d(b=400, h=500, bars=bars, N_ed=600,
            Mx_ed=effective_M, My_ed=0, nx=24, ny=120, generate_surface=False)
        self.assertTrue(result['converged'])
        # Independent fiber compatibility vs legacy rectangular-block design: 2% tolerance.
        self.assertAlmostEqual(result['capacity']['Mx_Rd_kNm']/effective_M, 1., delta=.02)
        self.assertAlmostEqual(result['eta'], 1., delta=.02)


class BiaxialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = calculate()

    def test_03_requested_loads_converge_and_both_moment_equations_balance(self):
        r = self.result
        self.assertTrue(r['converged'])
        self.assertGreater(r['iterations'], 0)
        self.assertLess(r['Newton_History'][-1]['scaled_residual'], 1e-8)
        self.assertAlmostEqual(r['capacity']['N_Rd_kN'], 1500, delta=.001)
        self.assertAlmostEqual(r['capacity']['Mx_Rd_kNm']/r['capacity']['My_Rd_kNm'], 1.5, places=6)
        self.assertAlmostEqual(r['eta'], math.hypot(120, 80)/r['capacity']['M_Rd_kNm'], places=10)
        self.assertAlmostEqual(r['strain_utilization'], 1., places=7)
        for value in r['equilibrium_residual'].values():
            self.assertLess(abs(value), .001)

    def test_independent_gauss_quadrature_and_scipy_root(self):
        from scipy.optimize import root
        z, w = np.polynomial.legendre.leggauss(100)
        x, y = np.meshgrid(z*200, z*200)
        weights = np.outer(w, w).ravel()*200**2
        x, y = x.ravel(), y.ravel()
        bars = layout()
        sx, sy = np.array([p['x'] for p in bars]), np.array([p['y'] for p in bars])
        areas = np.full(8, math.pi*25**2/4)
        direction = np.array([120., 80.])/math.hypot(120, 80)
        def stress(e):
            e1 = .6*17/32500
            return np.where(e <= 0, 0., np.where(e < e1, 32500*e,
                np.where(e < .002, .6*17+.4*17*(e-e1)/(.002-e1), 17.)))
        def residual(q):
            ec = q[0]+q[1]*y/400+q[2]*x/400
            es = q[0]+q[1]*sy/400+q[2]*sx/400
            f = stress(ec)*weights
            fs = (np.clip(200000*es, -350, 350)-stress(es))*areas
            force = np.array([f.sum()+fs.sum(), f@y+fs@sy, f@x+fs@sx])
            return np.r_[(force-[1500000, q[3]*direction[0]*1e6, q[3]*direction[1]*1e6])/[4e6, 1e9, 1e9],
                         (q[0]+.5*abs(q[1])+.5*abs(q[2]))/.0035-1]
        solved = root(residual, [.0003, .004, .0024, 238.], tol=1e-10)
        self.assertTrue(solved.success, solved.message)
        self.assertLess(float(np.max(np.abs(residual(solved.x)))), 1e-8)
        expected_eta = math.hypot(120, 80)/solved.x[3]
        self.assertAlmostEqual(self.result['eta']/expected_eta, 1., delta=.002)

    def test_mesh_refinement_stabilizes_eta(self):
        medium, fine = calculate(nx=60, ny=60), calculate(nx=100, ny=100)
        self.assertTrue(medium['converged'] and fine['converged'])
        self.assertLess(abs(medium['eta']/fine['eta']-1), .001)
        self.assertLess(abs(self.result['eta']/fine['eta']-1), .002)

    def test_reversing_moments_and_swapping_axes_preserve_symmetric_capacity(self):
        for mx, my in [(-120, 80), (120, -80), (-120, -80), (80, 120)]:
            r = calculate(Mx_ed=mx, My_ed=my)
            self.assertTrue(r['converged'])
            self.assertAlmostEqual(r['eta'], self.result['eta'], places=6)

    def test_eta_scales_moments_at_fixed_axial_force(self):
        doubled = calculate(Mx_ed=240, My_ed=160)
        self.assertAlmostEqual(doubled['eta'], 2*self.result['eta'], places=8)
        self.assertEqual(doubled['section_check'], 'FAIL')

    def test_surface_points_satisfy_material_limits_and_cover_all_quadrants(self):
        r = calculate(n_angles=16, n_levels=10, generate_surface=True)
        surface = r['interaction_surface']
        self.assertEqual(len(surface), 162)
        self.assertGreater(max(p['N_kN'] for p in surface), 0)
        self.assertLess(min(p['N_kN'] for p in surface), 0)
        self.assertGreater(max(p['Mx_kNm'] for p in surface), 0)
        self.assertLess(min(p['Mx_kNm'] for p in surface), 0)
        self.assertGreater(max(p['My_kNm'] for p in surface), 0)
        self.assertLess(min(p['My_kNm'] for p in surface), 0)
        section = FiberSection(400, 400, layout())
        for p in surface:
            state = p['strain_plane']
            q = [state['epsilon_0'], state['kappa_x_per_mm']*400, state['kappa_y_per_mm']*400]
            self.assertAlmostEqual(section.strain_limit(q), 1., places=9)
        json.dumps(r, allow_nan=False)


class AdversarialAndSystemTests(unittest.TestCase):
    def test_no_false_pass_when_newton_iteration_limit_is_exhausted(self):
        r = calculate(n_angles=12, max_iterations=1, tolerance=1e-12)
        self.assertFalse(r['converged'])
        self.assertEqual(r['status'], 'INCONCLUSIVE')
        self.assertIsNone(r['eta'])
        self.assertFalse(r['approved'])
        self.assertTrue(r['Newton_History'])

    def test_axial_overload_returns_failure_without_infinite_eta(self):
        r = calculate(N_ed=9000)
        self.assertEqual(r['status'], 'FAILED')
        self.assertEqual(r['section_check'], 'FAIL')
        self.assertIsNone(r['eta'])
        json.dumps(r, allow_nan=False)

    def test_invalid_geometry_materials_loads_and_bars_are_rejected(self):
        cases = [dict(b=-1), dict(N_ed=float('nan')), dict(Mx_ed=float('inf')), dict(N_ed=-10),
                 dict(concrete='B999'), dict(rebar='UNKNOWN'), dict(nx=2), dict(tolerance=0),
                 dict(bars=[]), dict(bars=[dict(x=199, y=0, dia=25)]),
                 dict(bars=[dict(x=0, y=0, dia=25), dict(x=0, y=0, dia=25)]),
                 dict(regions=[dict(x_min=-100, x_max=100, y_min=-100, y_max=100)]*2)]
        for kwargs in cases:
            with self.subTest(kwargs=kwargs), self.assertRaises((ValueError, KeyError)):
                calculate(**kwargs)

    def test_strict_provenance_blocks_before_capacity_calculation(self):
        r = calculate(require_provenance=True)
        self.assertEqual(r['status'], 'BLOCKED')
        self.assertFalse(r['approved'])
        self.assertNotIn('capacity', r)

    def test_explicit_per_parameter_provenance_binds_real_inputs(self):
        r = calculate()
        records = []
        def walk(value, path=''):
            if isinstance(value, dict):
                for key, item in value.items():
                    walk(item, f'{path}.{key}' if path else key)
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    walk(item, f'{path}[{i}]')
            else:
                unit = ('kN' if path == 'N_ed' else 'kNm' if path in ('Mx_ed', 'My_ed') else
                        'MPa' if path in ('Rb', 'Eb', 'Rs', 'Rsc', 'Es') else
                        'mm2' if path.endswith('.area') else
                        'mm' if path in ('b', 'h') or path.endswith(('.x', '.y')) else '1')
                records.append(dict(Parameter=path, Value=value, Unit=unit, Source_Type='ENGINEER_ASSUMED',
                                    Source_Ref='ENG-TEST-24 explicit test fixture', Verified=True))
        walk(r['Inputs'])
        anchored = calculate(provenance=records, require_provenance=True)
        self.assertTrue(anchored['approved'])
        changed = calculate(N_ed=1600, provenance=records, require_provenance=True)
        self.assertEqual(changed['status'], 'BLOCKED')

    def test_citations_ground_in_real_pdf_and_annex_g_misreference_is_explicit(self):
        r = calculate()
        auditor = CitationGroundingAuditor()
        for step in r['Calculation_Logs']:
            verified = auditor.verify_citation(step['Citation'])
            self.assertTrue(verified['Citation_Content_Verified'], verified)
        self.assertEqual(r['Requested_Reference']['status'], 'INCORRECT_SCOPE')
        self.assertIn('8.1.2.7', r['Standard_Method'])
        self.assertNotIn('Annex G', r['Standard_Method'])

    def test_cli_outputs_machine_readable_json_without_overwriting_input(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'input.json'
            path.write_text(json.dumps(dict(bars=layout(), generate_surface=False)), encoding='utf-8')
            before = path.read_bytes()
            process = subprocess.run([sys.executable, str(SCRIPTS/'calc_rc_section_pm_3d.py'), '-i', str(path)],
                                     capture_output=True, text=True, encoding='utf-8', timeout=30)
            self.assertEqual(process.returncode, 3, process.stderr)  # Numeric PASS, inputs unverified.
            self.assertTrue(json.loads(process.stdout)['converged'])
            self.assertEqual(path.read_bytes(), before)

    def test_registered_as_suite_24(self):
        path = ROOT/'tests/run_all_tests.py'
        namespace = {'__file__': str(path), '__name__': 'suite_registry'}
        source = path.read_text(encoding='utf-8').replace("if sys.platform == 'win32':", 'if False:')
        exec(compile(source, str(path), 'exec'), namespace)
        suites = [s for s in namespace['SUITES'] if s[0].startswith('24.')]
        self.assertEqual(len(suites), 1)
        self.assertEqual(Path(suites[0][1][1]).resolve(), Path(__file__).resolve())


if __name__ == '__main__':
    unittest.main(verbosity=2)
