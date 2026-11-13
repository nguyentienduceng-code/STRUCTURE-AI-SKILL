#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Nonlinear RC fiber-section P-Mx-My, TCVN 5574:2018 8.1.2.7.

Units: geometry mm/mm2, stresses MPa, external N kN, M kNm.
Compression is POSITIVE (opposite to the standard's signed convention).
eps = eps0 + kappa_x*y + kappa_y*x; Mx=sum(F*y), My=sum(F*x).
Moments refer to the gross concrete centroid, reported in Geometry.

Concrete: normative three-segment diagram 6.1.4.2, peak at .002 and .0035
mixed-strain limit; all-compression limit follows equation (86), not a
uniform .0035 strain. Optional parabola/plateau is a declared approximation.
Steel: elastic-perfectly-plastic with distinct tensile/compressive strengths.
Concrete displaced by bars is subtracted at the bar strain (no double count).

A fixed-N capacity ray keeps Mx/My, NOT the neutral-axis direction, fixed.
The angular sweep brackets a solution; a scaled, damped Newton solver then
enforces N, both moments and the governing material strain limit together.

Annex G concerns concrete shear keys. It is NOT the basis of this model.
No member buckling, P-delta, creep, accidental eccentricity, confinement,
shear/torsion, reinforcement anchorage or detailing check is performed here.
Provide design moments INCLUDING required member effects from upstream.
"""
import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

if hasattr(sys.stdout, 'reconfigure') and sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'tools'))
from citation_grounding_auditor import normalize_citation
from input_provenance_guard import audit_inputs
from policy_engine import decide_eta

RB = {'B15': 8.5, 'B20': 11.5, 'B25': 14.5, 'B30': 17., 'B35': 19.5, 'B40': 22.}
EB = {'B15': 24000., 'B20': 27500., 'B25': 30000., 'B30': 32500., 'B35': 34500., 'B40': 36000.}
RS = {'CB240-T': 210., 'CB300-V': 260., 'CB400-V': 350., 'CB500-V': 435.}
RSC = {'CB240-T': 210., 'CB300-V': 260., 'CB400-V': 350., 'CB500-V': 400.}
SCOPE = [
    'Short-term, unconfined, nonprestressed section strength; concrete tension neglected.',
    'No member instability/P-delta, creep, accidental eccentricity, shear, torsion or detailing checks.',
    'Rectangle or union of nonoverlapping axis-aligned rectangular concrete regions.',
    'Midpoint concrete quadrature and point bars; verify mesh convergence for final design.',
    'Fixed-N moment utilization is not a proportional N-Mx-My load multiplier.',
]


def _finite(name, value, positive=False):
    if isinstance(value, bool) or not isinstance(value, (int, float, np.number)) or not math.isfinite(value):
        raise ValueError(f'{name} must be a finite number')
    if positive and value <= 0:
        raise ValueError(f'{name} must be positive')
    return float(value)


def _count(name, value, minimum, maximum):
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f'{name} must be an integer in [{minimum}, {maximum}]')
    return value


def citation(clause, page, summary):
    return normalize_citation({'Ma_Tieu_Chuan': 'TCVN 5574', 'Nam_Ban_Hanh': '2018',
        'Dieu_Bang_Muc': 'Điều '+clause, 'Ten_Bang_Hinh': '', 'Trang_So': page, 'Trich_Yeu': summary})


class FiberSection:
    """Geometry/material integration independent of capacity tracing.

    bars: [{area: mm2, x: mm, y: mm}, ...], or dia instead of area.
    regions: [{x_min,x_max,y_min,y_max}, ...]; default centered b by h rectangle.
    nx/ny are the grid divisions PER region. Shared edges are allowed, overlap is not.
    """
    def __init__(self, b, h, bars, *, concrete='B30', rebar='CB400-V',
                 Rb=None, Eb=None, Rs=None, Rsc=None, Es=200000.,
                 eps_b0=.002, eps_b2=.0035, eps_s_max=.025,
                 concrete_diagram='trilinear', nx=40, ny=40, regions=None):
        self.b, self.h = _finite('b', b, True), _finite('h', h, True)
        _count('nx', nx, 4, 400)
        _count('ny', ny, 4, 400)
        if concrete not in RB or rebar not in RS:
            raise ValueError('Unsupported material grade; do not silently substitute a different grade')
        self.Rb = _finite('Rb', RB[concrete] if Rb is None else Rb, True)
        self.Eb = _finite('Eb', EB[concrete] if Eb is None else Eb, True)
        self.Rs = _finite('Rs', RS[rebar] if Rs is None else Rs, True)
        self.Rsc = _finite('Rsc', RSC[rebar] if Rsc is None else Rsc, True)
        self.Es = _finite('Es', Es, True)
        self.e0, self.eu, self.esu = (_finite(name, value, True) for name, value in
                                     [('eps_b0', eps_b0), ('eps_b2', eps_b2), ('eps_s_max', eps_s_max)])
        if not 0 < .6*self.Rb/self.Eb < self.e0 < self.eu < self.esu:
            raise ValueError('Inconsistent concrete strain/modulus limits')
        if max(self.Rs, self.Rsc)/self.Es >= self.esu:
            raise ValueError('Steel yield strain must be below its ultimate strain')
        if concrete_diagram not in ('trilinear', 'parabolic_plateau'):
            raise ValueError('Unknown concrete diagram')
        self.diagram = concrete_diagram
        if regions is None:
            regions = [dict(x_min=-self.b/2, x_max=self.b/2, y_min=-self.h/2, y_max=self.h/2)]
        if not isinstance(regions, list) or not regions or len(regions)*nx*ny > 500000:
            raise ValueError('Invalid regions or excessive mesh size')
        self.regions = []
        for region in regions:
            r = {key: _finite(key, region[key]) for key in ('x_min', 'x_max', 'y_min', 'y_max')}
            if r['x_min'] >= r['x_max'] or r['y_min'] >= r['y_max']:
                raise ValueError('Concrete region must have positive width and height')
            for previous in self.regions:
                if (min(r['x_max'], previous['x_max']) > max(r['x_min'], previous['x_min']) and
                    min(r['y_max'], previous['y_max']) > max(r['y_min'], previous['y_min'])):
                    raise ValueError('Concrete regions overlap: area would be counted twice')
            self.regions.append(r)
        areas = np.array([(r['x_max']-r['x_min'])*(r['y_max']-r['y_min']) for r in self.regions])
        centers = np.array([[(r['x_max']+r['x_min'])/2, (r['y_max']+r['y_min'])/2] for r in self.regions])
        self.gross_area = float(areas.sum())
        self.centroid = np.sum(centers*areas[:, None], axis=0)/self.gross_area
        points, weights, vertices = [], [], []
        for r, area in zip(self.regions, areas):
            dx, dy = (r['x_max']-r['x_min'])/nx, (r['y_max']-r['y_min'])/ny
            x, y = np.meshgrid(r['x_min']+(np.arange(nx)+.5)*dx, r['y_min']+(np.arange(ny)+.5)*dy)
            points.extend(np.column_stack([x.ravel(), y.ravel()]))
            weights.extend([area/(nx*ny)]*(nx*ny))
            vertices.extend([(x, y) for x in (r['x_min'], r['x_max']) for y in (r['y_min'], r['y_max'])])
        self.points = np.asarray(points)-self.centroid
        self.areas = np.asarray(weights)
        self.vertices = np.unique(np.asarray(vertices)-self.centroid, axis=0)
        self.D = float(np.max(np.ptp(self.vertices, axis=0)))
        if not isinstance(bars, list) or not bars:
            raise ValueError('An explicit longitudinal bar layout is required')
        self.bars = []
        for bar in bars:
            x, y = _finite('bar.x', bar['x']), _finite('bar.y', bar['y'])
            area = (_finite('bar.area', bar['area'], True) if 'area' in bar else
                    math.pi*_finite('bar.dia', bar.get('dia', 0), True)**2/4)
            if 'dia' in bar:
                dia = _finite('bar.dia', bar['dia'], True)
                if abs(area-math.pi*dia**2/4) > 1e-6*area:
                    raise ValueError('Bar diameter and area disagree')
            radius = math.sqrt(area/math.pi)
            def inside(px, py):
                return any(r['x_min'] <= px <= r['x_max'] and r['y_min'] <= py <= r['y_max'] for r in self.regions)
            if not inside(x, y) or not all(inside(x+radius*math.cos(angle), y+radius*math.sin(angle))
                                          for angle in np.linspace(0, 2*math.pi, 32, endpoint=False)):
                raise ValueError('Bar lies outside concrete (center or circumference)')
            if any(math.hypot(x-p['x'], y-p['y']) < radius+math.sqrt(p['area']/math.pi)-1e-8 for p in self.bars):
                raise ValueError('Duplicate or overlapping longitudinal bars')
            self.bars.append(dict(area=area, x=x, y=y))
        self.steel_area = sum(bar['area'] for bar in self.bars)
        if self.steel_area >= self.gross_area:
            raise ValueError('Steel area must be smaller than gross concrete area')
        self.bar_points = np.array([[bar['x'], bar['y']] for bar in self.bars])-self.centroid
        self.bar_areas = np.array([bar['area'] for bar in self.bars])
        self.B = self._basis(self.points)
        self.S = self._basis(self.bar_points)
        self.V = self._basis(self.vertices)
        self.force_scale = self.Rb*(self.gross_area-self.steel_area)+self.Rsc*self.steel_area
        self.scales = np.array([self.force_scale, self.force_scale*self.D, self.force_scale*self.D])

    def _basis(self, points):
        return np.column_stack([np.ones(len(points)), points[:, 1]/self.D, points[:, 0]/self.D])

    def concrete_stress(self, strain):
        e = np.asarray(strain, dtype=float)
        if self.diagram == 'parabolic_plateau':
            t = np.clip(e/self.e0, 0., 1.)
            stress = self.Rb*(2*t-t*t)
            tangent = np.where((e > 0) & (e < self.e0), 2*self.Rb/self.e0*(1-t), 0.)
        else:
            e1 = .6*self.Rb/self.Eb
            slope = .4*self.Rb/(self.e0-e1)
            stress = np.where(e <= 0, 0., np.where(e < e1, self.Eb*e,
                      np.where(e < self.e0, .6*self.Rb+slope*(e-e1), self.Rb)))
            tangent = np.where((e > 0) & (e < e1), self.Eb,
                      np.where((e >= e1) & (e < self.e0), slope, 0.))
        return stress, tangent

    def steel_stress(self, strain):
        e = np.asarray(strain, dtype=float)
        elastic = self.Es*e
        return np.clip(elastic, -self.Rs, self.Rsc), np.where((elastic > -self.Rs) & (elastic < self.Rsc), self.Es, 0.)

    def response(self, q, tangent=False):
        """q=[eps0,kappa_x*D,kappa_y*D]; return [N(N),Mx(Nmm),My(Nmm)].

        Subtract displaced concrete at each actual bar, at its actual strain.
        """
        q = np.asarray(q, dtype=float)
        stress, modulus = self.concrete_stress(self.B@q)
        steel, steel_modulus = self.steel_stress(self.S@q)
        displaced, displaced_modulus = self.concrete_stress(self.S@q)
        forces = self.B.T@(stress*self.areas) + self.S.T@((steel-displaced)*self.bar_areas)
        conversion = np.array([1., self.D, self.D])
        result = forces*conversion
        if not tangent:
            return result
        stiffness = self.B.T@((modulus*self.areas)[:, None]*self.B)
        stiffness += self.S.T@(((steel_modulus-displaced_modulus)*self.bar_areas)[:, None]*self.S)
        return result, conversion[:, None]*stiffness

    def strain_limit(self, q):
        edges, bars = self.V@q, self.S@q
        emax, emin = float(edges.max()), float(edges.min())
        ratio = max(0., emin/emax) if emax > 0 else 0.
        allowed = self.eu-(self.eu-self.e0)*ratio
        concrete = max(0., emax)/allowed
        steel = float(np.max(np.abs(bars)))/self.esu
        return max(concrete, steel)

    def boundary_plane(self, theta, ratio):
        """Extreme concrete strains are proportional to [ratio,1]."""
        normal = np.array([math.sin(theta), math.cos(theta)])
        projection = self.vertices@normal
        low, high = float(projection.min()), float(projection.max())
        gradient = (1-ratio)/(high-low)
        q = np.array([ratio-gradient*low, gradient*self.D*normal[1], gradient*self.D*normal[0]])
        # Equation (86) changes the compression limit for a fully compressed section.
        concrete_max = self.eu-(self.eu-self.e0)*max(0., ratio)
        factor = min(concrete_max, self.esu/max(1e-30, np.max(np.abs(self.S@q))))
        return q*factor

    def plane_at_axial_force(self, theta, axial_N, tolerance=1e-9):
        low, high = -1000., 1.
        q_low = self.boundary_plane(theta, low)
        if self.response(q_low)[0] > axial_N:
            raise ValueError('Axial force below traceable compression/mixed domain')
        for _ in range(65):
            ratio = (low+high)/2
            q = self.boundary_plane(theta, ratio)
            force = self.response(q)
            if abs(force[0]-axial_N)/self.force_scale < tolerance:
                return q, force
            if force[0] > axial_N:
                high = ratio
            else:
                low = ratio
        return q, force

    def newton_boundary(self, seed, fixed_N, direction, tolerance=1e-8, max_iterations=50, axial=False):
        """Four equations, four unknowns: three plane coefficients plus ray scale."""
        x = np.asarray(seed, dtype=float).copy()
        history = []

        def equations(state, jacobian=False):
            force, stiffness = self.response(state[:3], tangent=True)
            target = np.array([state[3]*self.force_scale, 0., 0.]) if axial else np.array([
                fixed_N, state[3]*direction[0]*self.scales[1], state[3]*direction[1]*self.scales[2]])
            residual = np.r_[(force-target)/self.scales, self.strain_limit(state[:3])-1.]
            if not jacobian:
                return residual
            J = np.zeros((4, 4))
            J[:3, :3] = stiffness/self.scales[:, None]
            J[:3, 3] = [-1., 0., 0.] if axial else [0., -direction[0], -direction[1]]
            for col in range(3):
                step = np.zeros(3)
                step[col] = 1e-8
                J[3, col] = (self.strain_limit(state[:3]+step)-self.strain_limit(state[:3]-step))/(2e-8)
            return residual, J

        for iteration in range(max_iterations+1):
            residual, J = equations(x, True)
            error = float(np.max(np.abs(residual)))
            history.append({'iteration': iteration, 'scaled_residual': error})
            if error <= tolerance and x[3] >= 0:
                return x, True, history
            if iteration == max_iterations:
                break
            try:
                delta = np.linalg.solve(J, -residual)
            except np.linalg.LinAlgError:
                delta = np.linalg.lstsq(J, -residual, rcond=1e-12)[0]
            if not np.all(np.isfinite(delta)):
                break
            accepted = False
            alpha = 1.
            for _ in range(22):
                trial = x+alpha*delta
                if trial[3] >= 0 and np.max(np.abs(trial[:3])) < .5:
                    norm = float(np.linalg.norm(equations(trial)))
                    if norm < np.linalg.norm(residual)*(1-1e-4*alpha):
                        x, accepted = trial, True
                        break
                alpha *= .5
            if not accepted:
                break
        return x, False, history

    def capacity(self, N_ed, Mx_ed, My_ed, *, n_angles=36, tolerance=1e-8, max_iterations=50):
        moment = math.hypot(Mx_ed, My_ed)
        if moment < 1e-12:
            force = self.response([self.e0, 0., 0.])
            if np.max(np.abs(force[1:]/self.scales[1:])) < tolerance:
                return np.array([self.e0, 0., 0., force[0]/self.force_scale]), True, [], True
            # Asymmetric steel needs equilibrium too; do not assert P0 at zero moment.
            seed = [.0018, .0002, .0002, .95]
            q, ok, history = self.newton_boundary(seed, 0., [0., 0.], tolerance, max_iterations, axial=True)
            return q, ok, history, True
        direction = np.array([Mx_ed, My_ed])/moment
        axial_N = N_ed*1000.
        if axial_N >= self.force_scale*(1-1e-10):
            return None, False, [], False
        curve = []
        for theta in np.linspace(0., 2*math.pi, n_angles+1):
            q, force = self.plane_at_axial_force(theta, axial_N)
            cross = force[1]*direction[1]-force[2]*direction[0]
            curve.append((theta, q, force, cross))
        solutions, failed = [], []
        for _, plane, force, cross in curve:
            multiplier = float(force[1:]@direction/self.scales[1])
            if abs(cross)/self.scales[1] <= tolerance and multiplier > 0:
                state, ok, history = self.newton_boundary(np.r_[plane, multiplier], axial_N, direction,
                                                          tolerance, max_iterations)
                if ok:
                    solutions.append((state, ok, history, False))
                else:
                    failed.append((state, ok, history, False))
        for left, right in zip(curve, curve[1:]):
            if left[3]*right[3] > 0:
                continue
            weight = abs(left[3])/(abs(left[3])+abs(right[3])+1e-30)
            plane = (1-weight)*left[1]+weight*right[1]
            force = self.response(plane)
            multiplier = float(force[1:]@direction/self.scales[1])
            if multiplier <= 0:
                continue
            state, ok, history = self.newton_boundary(np.r_[plane, multiplier], axial_N, direction,
                                                       tolerance, max_iterations)
            if ok:
                solutions.append((state, ok, history, False))
            else:
                failed.append((state, ok, history, False))
        if not solutions:
            return min(failed, key=lambda solution: solution[2][-1]['scaled_residual']) if failed else (None, False, [], False)
        # The first positive intersection is the conservative capacity on the ray.
        return min(solutions, key=lambda solution: solution[0][3])

    def interaction_surface(self, n_angles=36, n_levels=20):
        # Offset/curvature parameterization also covers fully tensile concrete,
        # unlike a family that fixes a positive compressive extreme strain.
        offsets = np.sinh(np.linspace(-np.arcsinh(50.), np.arcsinh(50.), n_levels))
        points = []
        for theta in np.linspace(0., 2*math.pi, n_angles, endpoint=False):
            normal = np.array([math.sin(theta), math.cos(theta)])
            projection = self.vertices@normal
            low, high = float(projection.min()), float(projection.max())
            gradient = 2/(high-low)
            for offset in offsets:
                q = np.array([offset-gradient*(high+low)/2,
                              gradient*self.D*normal[1], gradient*self.D*normal[0]])
                q = q/self.strain_limit(q)
                force = self.response(q)
                points.append({'N_kN': float(force[0]/1000), 'Mx_kNm': float(force[1]/1e6),
                    'My_kNm': float(force[2]/1e6), 'strain_normal_angle_rad': float(theta),
                    'strain_offset_parameter': float(offset), 'strain_plane': self.plane_dict(q)})
        for label, q in [('uniform_compression', [self.e0, 0., 0.]), ('uniform_tension', [-self.esu, 0., 0.])]:
            force = self.response(q)
            points.append({'N_kN': float(force[0]/1000), 'Mx_kNm': float(force[1]/1e6),
                           'My_kNm': float(force[2]/1e6), 'endpoint': label, 'strain_plane': self.plane_dict(q)})
        return points

    def plane_dict(self, q):
        return {'epsilon_0': float(q[0]), 'kappa_x_per_mm': float(q[1]/self.D), 'kappa_y_per_mm': float(q[2]/self.D)}


def calc_rc_section_pm_3d(b=400., h=400., bars=None, N_ed=1500., Mx_ed=120., My_ed=80.,
                        concrete='B30', rebar='CB400-V', *, Rb=None, Eb=None, Rs=None, Rsc=None,
                        Es=200000., eps_b0=.002, eps_b2=.0035, eps_s_max=.025,
                        concrete_diagram='trilinear', nx=40, ny=40, regions=None,
                        n_angles=36, n_levels=20, generate_surface=True, tolerance=1e-8,
                        max_iterations=50, provenance=None, require_provenance=False):
    """Explicit bar layout required. Input provenance uses paths in result['Inputs'].

    Numerical section_check can PASS without source attestations; approved NEVER
    does. require_provenance=True blocks before any capacity calculation.
    """
    N_ed, Mx_ed, My_ed = (_finite(key, value) for key, value in [('N_ed', N_ed), ('Mx_ed', Mx_ed), ('My_ed', My_ed)])
    if N_ed < 0:
        raise ValueError('This capacity query supports N_ed >= 0 (compression); tension-domain queries are not implemented')
    _count('n_angles', n_angles, 12, 360)
    _count('n_levels', n_levels, 6, 100)
    _count('max_iterations', max_iterations, 1, 200)
    tolerance = _finite('tolerance', tolerance, True)
    if not 1e-12 <= tolerance <= 1e-4:
        raise ValueError('tolerance must be in [1e-12,1e-4]')
    section = FiberSection(b, h, bars, concrete=concrete, rebar=rebar, Rb=Rb, Eb=Eb, Rs=Rs, Rsc=Rsc,
        Es=Es, eps_b0=eps_b0, eps_b2=eps_b2, eps_s_max=eps_s_max,
        concrete_diagram=concrete_diagram, nx=nx, ny=ny, regions=regions)
    physical_inputs = {'b': section.b, 'h': section.h, 'bars': section.bars,
        'N_ed': N_ed, 'Mx_ed': Mx_ed, 'My_ed': My_ed, 'concrete': concrete, 'rebar': rebar,
        'Rb': section.Rb, 'Eb': section.Eb, 'Rs': section.Rs, 'Rsc': section.Rsc, 'Es': section.Es,
        'eps_b0': section.e0, 'eps_b2': section.eu, 'eps_s_max': section.esu,
        'concrete_diagram': concrete_diagram}
    if regions is not None:
        physical_inputs['regions'] = section.regions
    audit = audit_inputs(physical_inputs, provenance)
    logs = []
    def log(step, formula, result, clause='8.1.2.7.4', page=64):
        logs.append({'Step': step, 'Formula': formula, 'Result': result,
                     'Citation': citation(clause, page, step)})
    log('Fiber discretization', 'gross concrete integral + sum As*(sigma_s - sigma_b_at_bar)',
        {'fiber_count': len(section.areas), 'bar_count': len(section.bars),
         'gross_area_mm2': section.gross_area, 'net_concrete_area_mm2': section.gross_area-section.steel_area}, '8.1.2.7.2', 63)
    log('Concrete material law', 'three-segment: Eb*eps; linear to (eps_b0,Rb); Rb plateau',
        {'diagram': concrete_diagram, 'eps_b0': section.e0, 'eps_b2': section.eu}, '6.1.4.2', 38)
    log('Steel material law', 'sigma_s=clip(Es*eps,-Rs,Rsc); abs(eps_s)<=eps_s_max',
        {'Rs_MPa': section.Rs, 'Rsc_MPa': section.Rsc, 'Es_MPa': section.Es, 'eps_s_max': section.esu}, '6.2.4.2', 48)
    warnings = ['REFERENCE_CORRECTION: Annex G is concrete shear keys (PDF page 167); fiber section basis is 8.1.2.7.']
    unverified = []
    if concrete_diagram == 'parabolic_plateau':
        unverified.append('Parabolic/plateau is a declared approximation, not the normative three-segment diagram.')
    if (section.e0, section.eu, section.esu) != (.002, .0035, .025):
        unverified.append('Custom strain limits differ from the implemented short-term TCVN defaults; applicability requires verification.')
    if not audit['allowed']:
        warnings.append('INPUT_PROVENANCE_BLOCKED: numerical results are not approved for design use')
    result = {'status': 'INCONCLUSIVE', 'approved': False, 'section_check': 'INCONCLUSIVE',
        'Standard_Method': 'TCVN 5574:2018 8.1.2.7; short-term nonlinear fiber section',
        'approval_scope': 'Section material-strength check only; not member or project design approval',
        'Scope_Limitation': list(SCOPE), 'Unverified_Items': unverified,
        'Warnings': warnings, 'Inputs': physical_inputs, 'Input_Provenance_Audit': audit,
        'Calculation_Logs': logs, 'eta': None, 'utilization_ratio': None,
        'Geometry': {'centroid_input_xy_mm': section.centroid.tolist(), 'steel_area_mm2': section.steel_area,
                     'gross_area_mm2': section.gross_area, 'concrete_area_mm2': section.gross_area-section.steel_area,
                     'bounding_width_mm': float(np.ptp(section.vertices[:, 0])),
                     'bounding_height_mm': float(np.ptp(section.vertices[:, 1])),
                     'nx': nx, 'ny': ny, 'fiber_count': len(section.areas)},
        'Convention': 'compression positive; eps=eps0+kx*y+ky*x; Mx=sum(F*y), My=sum(F*x); moments about gross centroid',
        'Requested_Reference': {'reference': 'TCVN 5574:2018 Annex G', 'status': 'INCORRECT_SCOPE',
                                'actual_title': 'Tính toán chốt bê tông', 'PDF_page': 167},
        'interaction_surface': [], 'converged': False}
    if require_provenance and not audit['allowed']:
        result['status'] = 'BLOCKED'
        return result
    state, converged, history, axial = section.capacity(N_ed, Mx_ed, My_ed,
        n_angles=n_angles, tolerance=tolerance, max_iterations=max_iterations)
    result.update(converged=converged, Newton_History=history, iterations=len(history)-1 if history else 0)
    log('Boundary equilibrium: damped Newton-Raphson',
        'N=NEd; (Mx,My)=lambda*dM; max(material strain utilizations)=1',
        {'converged': converged, 'history': history}, '8.1.2.7.6', 66)
    if generate_surface:
        result['interaction_surface'] = section.interaction_surface(n_angles, n_levels)
        result['surface_scope'] = 'Sampled strain-limit boundary: compression, mixed strain and tension; untriangulated points, not an exact continuous surface'
    if not converged:
        result['Warnings'].append('NO_CONVERGED_CAPACITY: no design PASS may be inferred')
        if N_ed*1000 > section.force_scale:
            result.update(status='FAILED', section_check='FAIL', failure_reason='N_ed exceeds the uniform compression upper bound')
        return result
    force = section.response(state[:3])
    M_rd = float(math.hypot(force[1], force[2])/1e6)
    eta = N_ed/(force[0]/1000) if axial else math.hypot(Mx_ed, My_ed)/M_rd
    direction = np.array([Mx_ed, My_ed])
    target = np.array([force[0], 0., 0.]) if axial else np.r_[N_ed*1000, direction/math.hypot(*direction)*M_rd*1e6]
    result.update(status='OK', section_check='PASS' if eta <= 1+tolerance else 'FAIL',
        eta=float(eta), utilization_ratio=float(eta),
        capacity={'N_Rd_kN': float(force[0]/1000), 'Mx_Rd_kNm': float(force[1]/1e6),
                  'My_Rd_kNm': float(force[2]/1e6), 'M_Rd_kNm': M_rd,
                  'uniform_compression_upper_bound_kN': section.force_scale/1000},
        strain_plane=section.plane_dict(state[:3]), strain_utilization=section.strain_limit(state[:3]),
        equilibrium_residual={'N_kN': float((force-target)[0]/1000),
                              'Mx_kNm': float((force-target)[1]/1e6), 'My_kNm': float((force-target)[2]/1e6)},
        eta_definition='N_ed/N_Rd at zero M' if axial else 'hypot(Mx_ed,My_ed)/M_Rd at fixed N_ed and fixed moment direction')
    log('Strain limit and utilization', 'eq.(86) for same-sign compression; eta=Mdemand/Mcapacity at fixed N',
        {'strain_utilization': result['strain_utilization'], 'eta': eta}, '8.1.2.7.11', 67)
    decision = decide_eta(float(eta), audit, inputs=physical_inputs, provenance=provenance)
    result.update(approved=decision.is_approved and not unverified,
                  Policy={'action': decision.action.value, 'input_provenance_status': decision.input_provenance_status,
                          'is_approved': decision.is_approved, 'warnings': decision.input_risk_warnings})
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', '-i', required=True, help='Absolute path to JSON keyword inputs')
    parser.add_argument('--output', '-o')
    args = parser.parse_args(argv)
    try:
        data = json.loads(Path(args.input).resolve().read_text(encoding='utf-8-sig'))
        result = calc_rc_section_pm_3d(**data)
        code = (0 if result['approved'] else 3) if result['status'] == 'OK' and result['section_check'] == 'PASS' else 1
    except Exception as error:
        result, code = {'status': 'ERROR', 'approved': False, 'error': f'{type(error).__name__}: {error}'}, 2
    text = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)
    if args.output:
        target = Path(args.output).resolve()
        if target == Path(args.input).resolve():
            parser.error('Output must not overwrite input')
        target.write_text(text, encoding='utf-8')
    print(text)
    return code


if __name__ == '__main__':
    sys.exit(main())
