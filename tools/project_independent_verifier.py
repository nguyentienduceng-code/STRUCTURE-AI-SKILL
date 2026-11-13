#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P1 verifier: independent Gauss quadrature, provenance rebinding, PDF grounding.

Does not call FiberSection, its material methods or the capacity solver.
Checks a reported limit plane; this is NOT an independent global search proving
that every possible capacity branch was found. Member effects remain upstream.
"""
import math
import sys

import numpy as np
from citation_grounding_auditor import CitationGroundingAuditor
from input_provenance_guard import audit_inputs
from project_run_store import digest

if hasattr(sys.stdout, 'reconfigure') and sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')


def _number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError('Non-finite or nonnumeric mechanics value')
    return float(value)


def independent_section_response(inputs, plane, order=80):
    p = inputs
    b, h = _number(p['b']), _number(p['h'])
    regions = p.get('regions') or [dict(x_min=-b/2, x_max=b/2, y_min=-h/2, y_max=h/2)]
    area = sum((r['x_max']-r['x_min'])*(r['y_max']-r['y_min']) for r in regions)
    cx = sum((r['x_max']-r['x_min'])*(r['y_max']-r['y_min'])*(r['x_min']+r['x_max'])/2 for r in regions)/area
    cy = sum((r['x_max']-r['x_min'])*(r['y_max']-r['y_min'])*(r['y_min']+r['y_max'])/2 for r in regions)/area
    e0, kx, ky = (_number(plane[key]) for key in ('epsilon_0', 'kappa_x_per_mm', 'kappa_y_per_mm'))
    rb, eb, rs, rsc, es = (_number(p[key]) for key in ('Rb', 'Eb', 'Rs', 'Rsc', 'Es'))
    eb0, eb2, esu = (_number(p[key]) for key in ('eps_b0', 'eps_b2', 'eps_s_max'))
    if p['concrete_diagram'] != 'trilinear' or (eb0, eb2, esu) != (.002, .0035, .025):
        raise ValueError('Independent verifier currently supports normative short-term trilinear defaults only')
    def concrete(e):
        first = .6*rb/eb
        return np.interp(e, [0., first, eb0], [0., .6*rb, rb], left=0., right=rb)
    z, w = np.polynomial.legendre.leggauss(order)
    force = np.zeros(3)
    edges = []
    for r in regions:
        dx, dy = (r['x_max']-r['x_min'])/2, (r['y_max']-r['y_min'])/2
        x, y = np.meshgrid((r['x_max']+r['x_min'])/2+dx*z-cx,
                           (r['y_max']+r['y_min'])/2+dy*z-cy)
        weights = np.outer(w, w)*dx*dy
        f = concrete(e0+kx*y+ky*x)*weights
        force += [f.sum(), (f*y).sum(), (f*x).sum()]
        edges.extend(e0+kx*(yy-cy)+ky*(xx-cx) for xx in (r['x_min'], r['x_max']) for yy in (r['y_min'], r['y_max']))
    bars = p['bars']
    strains = []
    for bar in bars:
        x, y, steel_area = bar['x']-cx, bar['y']-cy, bar['area']
        e = e0+kx*y+ky*x
        strains.append(e)
        steel_stress = max(-rs, min(rsc, es*e))
        f = (steel_stress-float(concrete(e)))*steel_area
        force += [f, f*y, f*x]
    maximum, minimum = max(edges), min(edges)
    concrete_limit = eb2-(eb2-eb0)*max(0., minimum/maximum) if maximum > 0 else eb2
    limit_utilization = max(max(0., maximum)/concrete_limit, max(abs(e) for e in strains)/esu)
    upper_bound = (rb*(area-sum(bar['area'] for bar in bars))+rsc*sum(bar['area'] for bar in bars))/1000
    return {'N_kN': float(force[0]/1000), 'Mx_kNm': float(force[1]/1e6), 'My_kNm': float(force[2]/1e6),
            'strain_utilization': limit_utilization, 'compression_upper_bound_kN': upper_bound}


def verify_project_results(project, relative_tolerance=.005, quadrature_order=80):
    """Accept reproducible PASS or FAIL findings, never an uncheckable design PASS."""
    errors, checked, evidence = [], [], {}
    if project.get('status') != 'COMPLETED' or project.get('binding_issues') or project.get('unbound_reaction_rows'):
        errors.append('PROJECT_HAS_INCOMPLETE_BINDING_OR_CASE_COVERAGE')
    if not project.get('source_verification') or any(s.get('scope') != 'ORIGINAL_FILE_RECHECKED' for s in project['source_verification']):
        errors.append('ORIGINAL_SOURCE_FILES_NOT_VERIFIED')
    auditor = CitationGroundingAuditor()
    for index, member in enumerate(project.get('members', []), 1):
        summary = member.get('summary', {})
        if (summary.get('Tên cột'), summary.get('Tầng'), summary.get('STT')) != (member.get('column'), member.get('story'), index):
            errors.append('SCHEDULE_MEMBER_IDENTITY_MISMATCH:'+str(member.get('column')))
        if member.get('errors') or member.get('state') not in ('PASS', 'FAIL'):
            errors.append(f'UNCHECKABLE_MEMBER:{member.get("story")}:{member.get("column")}')
        candidates = []
        if not member.get('case_results'):
            errors.append('MEMBER_WITHOUT_CASES:'+str(member.get('column')))
        for case in member.get('case_results', []):
            label = f'{member.get("story")}:{member.get("column")}:{case.get("case")}:{case.get("step")}'
            item = {'case': label, 'verified': False, 'errors': []}
            checked.append(item)
            try:
                result = case['calculation']
                inputs = result['Inputs']
                if inputs != case['inputs']:
                    raise ValueError('Calculator changed its input mapping')
                if not audit_inputs(inputs, case['Provenance'])['allowed']:
                    raise ValueError('Input provenance does not bind to actual values')
                if result.get('Unverified_Items'):
                    raise ValueError('Unverified model assumptions require explicit resolution')
                for step in result['Calculation_Logs']:
                    citation = step['Citation']
                    key = digest(citation)
                    if key not in evidence:
                        evidence[key] = auditor.verify_citation(citation)
                    if not evidence[key]['Citation_Content_Verified']:
                        raise ValueError('Citation PDF grounding failed')
                # A known axial overload is a verifiable FAIL even without a limit plane.
                if result['status'] == 'FAILED' and result['section_check'] == 'FAIL' and result['eta'] is None:
                    response = independent_section_response(inputs,
                        {'epsilon_0': .002, 'kappa_x_per_mm': 0., 'kappa_y_per_mm': 0.}, quadrature_order)
                    if inputs['N_ed'] <= response['compression_upper_bound_kN']:
                        raise ValueError('Reported axial failure is not supported by the upper bound')
                    item.update(verified=True, disposition='AXIAL_FAILURE_CONFIRMED')
                    candidates.append((True, None, case['source'], case))
                    continue
                if result['status'] != 'OK' or not result['converged']:
                    raise ValueError('Solver did not converge')
                response = independent_section_response(inputs, result['strain_plane'], quadrature_order)
                capacity = result['capacity']
                for actual_key, claimed_key in [('N_kN', 'N_Rd_kN'), ('Mx_kNm', 'Mx_Rd_kNm'), ('My_kNm', 'My_Rd_kNm')]:
                    actual, claimed = response[actual_key], _number(capacity[claimed_key])
                    if abs(actual-claimed) > .05+relative_tolerance*max(abs(actual), abs(claimed)):
                        raise ValueError('Independent integration mismatch:'+actual_key)
                if abs(response['strain_utilization']-1) > 1e-6:
                    raise ValueError('Reported plane is not on the material strain boundary')
                moment = math.hypot(inputs['Mx_ed'], inputs['My_ed'])
                if moment > 1e-10:
                    if abs(capacity['N_Rd_kN']-inputs['N_ed']) > 1e-5*max(1, inputs['N_ed']):
                        raise ValueError('Capacity is not at the requested axial force')
                    cross = capacity['Mx_Rd_kNm']*inputs['My_ed']-capacity['My_Rd_kNm']*inputs['Mx_ed']
                    dot = capacity['Mx_Rd_kNm']*inputs['Mx_ed']+capacity['My_Rd_kNm']*inputs['My_ed']
                    if dot <= 0 or abs(cross) > 1e-6*max(1, moment*capacity['M_Rd_kNm']):
                        raise ValueError('Capacity moment direction changed')
                    eta = moment/math.hypot(response['Mx_kNm'], response['My_kNm'])
                else:
                    if max(abs(response['Mx_kNm']), abs(response['My_kNm'])) > .05:
                        raise ValueError('Pure axial capacity has an unbalanced moment')
                    eta = inputs['N_ed']/response['N_kN']
                if abs(eta-_number(result['eta'])) > relative_tolerance*max(1., eta):
                    raise ValueError('Independent utilization mismatch')
                expected = 'PASS' if result['eta'] <= 1+1e-8 else 'FAIL'
                if result['section_check'] != expected:
                    raise ValueError('Reported section classification contradicts eta')
                item.update(verified=True, independent_response=response, independent_eta=eta,
                            disposition='NUMERICAL_FINDING_REPRODUCED')
                candidates.append((False, result['eta'], case['source'], case))
            except (ValueError, KeyError, TypeError, ZeroDivisionError) as error:
                item['errors'].append(str(error))
                errors.append(label+':'+str(error))
        governing = member.get('governing')
        if candidates:
            failure = next((c for c in candidates if c[0]), None)
            worst = failure or max(candidates, key=lambda c: c[1])
            if not governing or governing != worst[3]:
                errors.append('GOVERNING_CASE_SELECTION_MISMATCH:'+member['column'])
            expected_state = 'FAIL' if any(c[0] or c[1] > 1+1e-8 for c in candidates) else 'PASS'
            summary = member.get('summary', {})
            if member.get('state') != expected_state or summary.get('Trạng thái') != ('ĐẠT' if expected_state == 'PASS' else 'KHÔNG ĐẠT'):
                errors.append('MEMBER_OR_SCHEDULE_CLASSIFICATION_MISMATCH:'+member['column'])
            if summary.get('η') != worst[1]:
                errors.append('SCHEDULE_UTILIZATION_MISMATCH:'+member['column'])
            loads = worst[3]['inputs']
            if any(summary.get(label) != loads.get(key) for label, key in [('N (kN)', 'N_ed'), ('Mx (kNm)', 'Mx_ed'), ('My (kNm)', 'My_ed')]):
                errors.append('SCHEDULE_LOADS_MISMATCH:'+member['column'])
    schedule = [member.get('summary') for member in project.get('members', [])]
    if schedule != project.get('schedule'):
        errors.append('PROJECT_SCHEDULE_DIFFERS_FROM_CHECKED_MEMBERS')
    table = project.get('summary_table', {})
    from project_data_pipeline import SUMMARY_HEADERS
    if table.get('headers') != SUMMARY_HEADERS or table.get('rows') != [[row.get(key) for key in SUMMARY_HEADERS] for row in schedule if isinstance(row, dict)]:
        errors.append('SUMMARY_TABLE_DIFFERS_FROM_CHECKED_SCHEDULE')
    expected_all_passed = bool(schedule) and all(m.get('state') == 'PASS' for m in project.get('members', []))
    if not isinstance(project.get('all_passed'), bool) or project['all_passed'] != expected_all_passed:
        errors.append('PROJECT_ALL_PASSED_FLAG_MISMATCH')
    counts = project.get('counts', {})
    members = project.get('members', [])
    if counts.get('total') != len(members) or any(counts.get(state) != sum(m.get('state') == state for m in members)
                                               for state in ('PASS', 'FAIL', 'BLOCKED', 'INCONCLUSIVE')):
        errors.append('PROJECT_COUNTS_MISMATCH')
    if not checked:
        errors.append('NO_CASES_IN_VERIFICATION')
    return {'status': 'VERIFIED' if not errors else 'BLOCKED', 'verified': not errors,
            'method': 'Independent Gauss quadrature + provenance rebinding + original PDF grounding',
            'quadrature_order': quadrature_order, 'relative_tolerance': relative_tolerance,
            'checked_cases': checked, 'errors': errors, 'citation_evidence': list(evidence.values()),
            'scope': 'Reproduces reported strain-limit states; not a second global capacity search or a member stability check'}
