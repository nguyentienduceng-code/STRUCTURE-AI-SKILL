#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Project adapter: Universal Reader -> concurrent ETABS rows -> RC fiber solver.

API: run_project_pipeline(sources, conventions=..., solver_options=...).
sources: file paths (.dwg/.dxf/.xlsx/.csv/reader-result.json) or Reader dicts.
For multiple storeys, scope CAD via {source: path_or_reader, story: 'L1'}.
CLI: python project_data_pipeline.py --input ABS_MANIFEST.json [--output ABS.json]
     [--summary-csv ABS.csv]
Manifest: {sources: [...], conventions: {...}, solver_options: {...}}.

Workbook contract (column names are case/space insensitive):
  Column Schedule: Column, Story, Joint (optional if matched spatially),
    b(mm), h(mm), Concrete, Rebar, Bars(mm), Angle(deg), [X(mm),Y(mm),Z(mm)].
    Bars is JSON [{x,y,area},...] or [{x,y,dia},...], in local section mm/mm2.
  Model Parameters: Parameter, Value, Unit. Required model/strength parameters:
    Rb,Eb,Rs,Rsc,Es (MPa), eps_b0,eps_b2,eps_s_max (1), concrete_diagram (1).
    Global strength parameters also require Concrete/Rebar grade rows in that
    table, so B30 strengths cannot silently be reused for a B25 member.
    Parameters can instead be columns on each Column Schedule row (per-column
    values take precedence). There are NO invented reinforcement/material defaults.
  Joint Reactions: Joint, OutputCase, [Story,StepType,StepNum], F3(kN),
    M1(kNm),M2(kNm), or names configured in conventions.
  Joint Coordinates (optional): Joint, [Story], X(m),Y(m),[Z(m)].

conventions REQUIRED: reaction_axes='GLOBAL', axial_sign,mx_sign,my_sign = +/-1;
optional axial_column='F3',mx_column='M1',my_column='M2'. The sign mapping
must produce compression-positive N and the solver's Mx=sum(F*y),My=sum(F*x).
Column Angle(deg) rotates global moment components into section-local axes.
Known joint-to-centroid offsets add N*dy and N*dx before that rotation.

CAD: closed rectangular column outlines and unique nearby C1/W1/... labels,
WCS/INSUNITS, matched to Column Schedule names. Sizes/angle are checked against
CAD. Missing joint IDs can bind via unique 3D joint coordinates, never nearest
without a tolerance or across an unknown storey. coordinate_mode='XY_STORY'
explicitly matches flat 2D plans to joint XY within the same documented story;
the default 'XYZ' requires all three WCS coordinates. CAD is not a rebar-layout oracle.

Verified means deterministic extraction/unit conversion/binding to supplied
Reader rows, not source authorship, engineering truth, or independent OCR review.
Cached Reader results are rechecked against an accessible original file; offline
results explicitly retain only an upstream-Reader attestation with no file hash.
Every physical solver input has DOCUMENT_EXTRACTED provenance with row/entity
evidence. Numerical solver controls are separately recorded as execution settings.
All concurrent load cases/steps are checked; governing = maximum fixed-N eta.
Envelope Max/Min rows are rejected because their components need not be concurrent.
Only the fiber section's material strength is checked, not member/project safety.
"""
import argparse
import copy
import csv
import hashlib
import json
import math
import re
import sys
import unicodedata
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure') and sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(TOOLS.parent/'skills/Structural_Design_Engineer/scripts'))
from doc_reader import read_document
from input_provenance_guard import audit_inputs
from calc_rc_section_pm_3d import calc_rc_section_pm_3d

PARAMETERS = ('Rb', 'Eb', 'Rs', 'Rsc', 'Es', 'eps_b0', 'eps_b2', 'eps_s_max', 'concrete_diagram')
CONTROLS = {'nx', 'ny', 'n_angles', 'n_levels', 'tolerance', 'max_iterations', 'generate_surface'}
SUMMARY_HEADERS = ['STT', 'Tên cột', 'Tầng', 'Tiết diện', 'Thép', 'N (kN)', 'Mx (kNm)', 'My (kNm)', 'η', 'Trạng thái']
LENGTH = {'mm': 1., 'cm': 10., 'm': 1000.}
FORCE = {'n': .001, 'kn': 1.}
MOMENT = {'nmm': 1e-6, 'nm': .001, 'knmm': .001, 'knm': 1.}
STRESS = {'mpa': 1., 'n/mm2': 1., 'kpa': .001, 'pa': 1e-6}


class PipelineDataError(ValueError):
    pass


def _key(value):
    return re.sub(r'[\s_\-]+', '', unicodedata.normalize('NFKC', str(value)).casefold())


def _column_key(value):
    return _key(re.sub(r'\([^)]*\)|\[[^]]*\]', '', str(value)))


def _id_key(value):
    """Identity normalization MUST preserve punctuation: 10-1 is not 101."""
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFKC', str(value)).strip().casefold())


def _identifier(value):
    if value is None or isinstance(value, bool):
        return ''
    if isinstance(value, (int, float)):
        if not math.isfinite(value):
            return ''
        return str(int(value)) if float(value).is_integer() else str(value)
    return unicodedata.normalize('NFKC', str(value)).strip()


def _number(value, name):
    if isinstance(value, bool) or value is None:
        raise PipelineDataError(f'MISSING_OR_INVALID_VALUE:{name}')
    try:
        result = float(value)
    except (ValueError, TypeError):
        raise PipelineDataError(f'INVALID_NUMBER:{name}:{value}') from None
    if not math.isfinite(result):
        raise PipelineDataError(f'NONFINITE_VALUE:{name}')
    return result


def _unit(value):
    return str(value or '').strip().lower().replace('²', '2').replace('³', '3').replace('·', '').replace('.', '').replace(' ', '')


def _convert(value, unit, factors, name):
    normalized = _unit(unit)
    if normalized not in factors:
        raise PipelineDataError(f'MISSING_OR_UNSUPPORTED_UNIT:{name}:{unit}')
    return _number(value, name)*factors[normalized]


def _read_json(path):
    def invalid(value):
        raise PipelineDataError('NONFINITE_JSON:'+value)
    return json.loads(Path(path).read_text(encoding='utf-8-sig'), parse_constant=invalid)


def _load_sources(sources):
    if isinstance(sources, (str, Path, dict)):
        sources = [sources]
    if not isinstance(sources, list) or not sources:
        raise PipelineDataError('NO_SOURCES')
    documents = []
    for source in sources:
        story = ''
        if isinstance(source, dict) and 'source' in source and 'metadata' not in source:
            if set(source)-{'source', 'story'}:
                raise PipelineDataError('UNKNOWN_SOURCE_CONTEXT_FIELDS')
            story = _identifier(source.get('story'))
            if not story:
                raise PipelineDataError('SOURCE_STORY_CONTEXT_REQUIRED')
            source = source['source']
        cached = isinstance(source, dict)
        if isinstance(source, dict):
            result = copy.deepcopy(source)
        else:
            path = Path(source).resolve()
            cached = path.suffix.lower() == '.json'
            result = _read_json(path) if path.suffix.lower() == '.json' else read_document(path)
        if not isinstance(result, dict) or 'metadata' not in result or 'tables' not in result:
            raise PipelineDataError('INVALID_READER_RESULT')
        if result.get('status') not in ('OK', 'PARTIAL'):
            raise PipelineDataError('READER_NOT_USABLE:'+str(result.get('status')))
        metadata = result['metadata']
        name = result.get('source_file') or Path(metadata.get('source_path', '')).name
        if not name:
            raise PipelineDataError('READER_SOURCE_IDENTITY_MISSING')
        result['_pipeline_source'] = name
        declared_story = _identifier(metadata.get('story'))
        if story and declared_story and _id_key(story) != _id_key(declared_story):
            raise PipelineDataError('CONFLICTING_SOURCE_STORY_CONTEXT')
        result['_pipeline_story'] = story or declared_story
        path = Path(metadata['source_path']) if metadata.get('source_path') else None
        if cached and path and path.is_file():
            fresh = read_document(path)
            def snapshot(document):
                meta = document.get('metadata', {})
                return json.dumps({'file_type': document.get('file_type'), 'tables': document.get('tables'),
                    'columns': document.get('engineering_entities', {}).get('columns'),
                    'text_entities': meta.get('text_entities'), 'drawing_units_code': meta.get('drawing_units_code'),
                    'coordinate_system': meta.get('coordinate_system')}, sort_keys=True, ensure_ascii=False, allow_nan=False)
            if fresh.get('status') not in ('OK', 'PARTIAL') or snapshot(fresh) != snapshot(result):
                raise PipelineDataError('STALE_OR_MODIFIED_READER_RESULT:'+name)
            if path.name.casefold() != name.casefold():
                raise PipelineDataError('READER_SOURCE_FILENAME_CONFLICT:'+name)
        result['_pipeline_source_verification'] = 'ORIGINAL_FILE_RECHECKED' if path and path.is_file() else 'SUPPLIED_READER_ROWS_ONLY'
        result['_pipeline_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest() if path and path.is_file() else None
        documents.append(result)
    return documents


def _rows(documents):
    """Keep physical Excel row numbers and original column units; never renumber data rows."""
    for document in documents:
        for table_index, table in enumerate(document['tables']):
            headers = table.get('headers', [])
            names = [_column_key(value) for value in headers]
            if (_key(table.get('sheet', '')) not in ('columnschedule', 'columns', 'sectionschedule',
                    'modelparameters', 'materialparameters', 'jointcoordinates', 'pointcoordinates', 'jointreactions')
                    and table.get('table_type') != 'joint_reactions'
                    and not ('column' in names and ('bars' in names or 'barlayout' in names))):
                continue
            if len(names) != len(set(names)):
                raise PipelineDataError('DUPLICATE_TABLE_HEADERS:'+document['_pipeline_source'])
            units = table.get('units') or [None]*len(headers)
            for index, values in enumerate(table.get('rows', [])):
                if not any(value is not None and str(value).strip() for value in values):
                    continue
                numbers = table.get('row_numbers', [])
                row_number = numbers[index] if index < len(numbers) else None
                location = (f'{document["_pipeline_source"]}, Sheet: {table.get("sheet", table.get("caption", "table"))}, '
                            f'Row: {row_number if row_number is not None else "UNRESOLVED"}')
                row = {}
                for col, (name, header) in enumerate(zip(names, headers)):
                    match = re.search(r'\(([^)]+)\)|\[([^]]+)\]', str(header))
                    unit = next((group for group in match.groups() if group), None) if match else (units[col] if col < len(units) else None)
                    row[name] = {'value': values[col] if col < len(values) else None, 'unit': unit,
                                 'ref': location+f', Column: {header}', 'sha256': document['_pipeline_sha256'],
                                 'row_verified': type(row_number) is int and row_number > 0,
                                 'document_status': document['status'], 'warnings': document['metadata'].get('warnings', [])}
                yield {'cells': row, 'sheet': table.get('sheet', ''), 'location': location,
                       'table_type': table.get('table_type', ''), 'source': document['_pipeline_source'],
                       'table_index': table_index, 'row_number': row_number}


def _cell(row, *names, required=True):
    for name in names:
        result = row['cells'].get(_column_key(name))
        if result is not None and result['value'] is not None and str(result['value']).strip():
            return result
    if required:
        raise PipelineDataError('MISSING_FIELD:'+'/'.join(names)+':'+row['location'])
    return None


def _text(row, *names, required=True):
    value = _cell(row, *names, required=required)
    return _identifier(value['value']) if value else ''


def _provenance(parameter, value, unit, cell, transform='identity'):
    if not cell.get('row_verified'):
        raise PipelineDataError('UNRESOLVED_SOURCE_ROW:'+cell['ref'])
    return {'Parameter': parameter, 'Value': value, 'Unit': unit, 'Source_Type': 'DOCUMENT_EXTRACTED',
            'Source_Ref': cell['ref'], 'Verified': True, 'Source_Value': cell['value'],
            'Source_Unit': cell.get('unit'), 'Source_SHA256': cell.get('sha256'), 'Transform': transform,
            'Verification_Scope': 'Value extracted, converted and bound to this supplied Reader row/entity; not engineering truth'}


def _model_parameters(rows):
    result = {}
    for row in rows:
        if _key(row['sheet']) not in ('modelparameters', 'materialparameters'):
            continue
        name = _text(row, 'Parameter')
        key = _key(name)
        if key in result:
            raise PipelineDataError('DUPLICATE_MODEL_PARAMETER:'+name)
        value = copy.deepcopy(_cell(row, 'Value'))
        value['unit'] = _text(row, 'Unit')
        result[key] = value
    return result


def _material_inputs(row, defaults):
    values, records = {}, []
    for name in PARAMETERS:
        local = _cell(row, name, required=False)
        cell = local or defaults.get(_key(name))
        if not cell:
            raise PipelineDataError('MISSING_DOCUMENTED_MODEL_PARAMETER:'+name)
        if local is None and name in ('Rb', 'Eb', 'Rs', 'Rsc'):
            grade_name = 'Concrete' if name in ('Rb', 'Eb') else 'Rebar'
            grade = defaults.get(_key(grade_name))
            if not grade or _key(grade['value']) != _key(_text(row, grade_name)):
                raise PipelineDataError('MODEL_PARAMETER_GRADE_CONTEXT_MISSING_OR_CONFLICTING:'+name)
        if name in ('Rb', 'Eb', 'Rs', 'Rsc', 'Es'):
            value = _convert(cell['value'], cell['unit'], STRESS, name)
            unit = 'MPa'
        else:
            if _unit(cell['unit']) not in ('1', 'dimensionless', '-'):
                raise PipelineDataError('INVALID_DIMENSIONLESS_UNIT:'+name)
            value = str(cell['value']).strip() if name == 'concrete_diagram' else _number(cell['value'], name)
            unit = '1'
        values[name] = value
        records.append(_provenance(name, value, unit, cell, 'document value converted to solver units'))
    return values, records


def _rectangle(entity, factor):
    points = entity.get('points_wcs', [])
    if entity.get('has_arc') is not False:
        raise PipelineDataError('CAD_ARC_OR_UNVERIFIED_STRAIGHT_EDGE_GEOMETRY')
    if not entity.get('closed') or len(points) not in (4, 5):
        raise PipelineDataError('CAD_COLUMN_NOT_CLOSED_RECTANGLE')
    points = [[_number(value, 'WCS')*factor for value in point] for point in points]
    if len(points) == 5:
        if math.dist(points[0], points[-1]) > 1e-5:
            raise PipelineDataError('CAD_POLYLINE_EXTRA_VERTEX')
        points.pop()
    if any(len(p) != 3 for p in points) or max(p[2] for p in points)-min(p[2] for p in points) > 1e-4:
        raise PipelineDataError('CAD_COLUMN_NOT_PLANAR_XY')
    edges = [[points[(i+1) % 4][j]-points[i][j] for j in (0, 1)] for i in range(4)]
    lengths = [math.hypot(*edge) for edge in edges]
    if min(lengths) < 1e-6:
        raise PipelineDataError('CAD_DEGENERATE_COLUMN')
    for i in range(4):
        if abs(sum(edges[i][j]*edges[(i+1) % 4][j] for j in (0, 1))) > 1e-6*lengths[i]*lengths[(i+1) % 4]:
            raise PipelineDataError('CAD_COLUMN_NOT_RECTANGULAR')
        if math.hypot(*(edges[i][j]+edges[(i+2) % 4][j] for j in (0, 1))) > 1e-5*max(lengths):
            raise PipelineDataError('CAD_COLUMN_OPPOSITE_EDGES_DISAGREE')
    return {'points': points, 'center': [sum(p[j] for p in points)/4 for j in range(3)]}


def _cad_columns(documents, label_tolerance_mm, stories=None):
    result, issues, invalid_names = {}, [], set()
    for doc in documents:
        if str(doc.get('file_type', '')).upper() not in ('DXF', 'DWG'):
            continue
        story = doc['_pipeline_story']
        if stories and story and _id_key(story) not in {_id_key(s) for s in stories}:
            continue
        metadata = doc['metadata']
        for warning in metadata.get('warnings', []):
            if str(warning).startswith('CAD_'):
                issues.append({'source': doc['_pipeline_source'], 'error': 'INCOMPLETE_CAD_READER:'+str(warning)})
        if metadata.get('coordinate_system') != 'WCS':
            raise PipelineDataError('CAD_REQUIRES_WCS')
        unit_code = metadata.get('drawing_units_code')
        factors = {4: 1., 5: 10., 6: 1000.}
        if unit_code not in factors:
            raise PipelineDataError('CAD_UNIT_NOT_SUPPORTED_OR_UNDECLARED')
        factor = factors[unit_code]
        labels = []
        for text in metadata.get('text_entities', []):
            match = re.match(r'\s*((?:COLUMN|COL|WALL|C|W|V)\s*[-_]?\d+[A-Z0-9_-]*)\b', text.get('text', ''), re.I)
            if match and 'position_wcs' in text:
                labels.append((_id_key(match[1]), [float(v)*factor for v in text['position_wcs']], text, match[1].strip()))
        for index, entity in enumerate(doc.get('engineering_entities', {}).get('columns', [])):
            if entity.get('entity_type') not in ('LWPOLYLINE', 'POLYLINE'):
                continue
            try:
                geometry = _rectangle(entity, factor)
                center = geometry['center']
                nearby = [label for label in labels if math.dist(label[1], center) <= label_tolerance_mm]
                if len(nearby) != 1:
                    raise PipelineDataError('CAD_LABEL_MISSING_OR_AMBIGUOUS')
                name = (_id_key(story), nearby[0][0])
                if name in result or name in invalid_names:
                    result.pop(name, None)
                    invalid_names.add(name)
                    raise PipelineDataError('DUPLICATE_CAD_COLUMN_LABEL:'+str(name))
                geometry.update(story=story, name=nearby[0][3])
                geometry['cell'] = {'ref': f'{doc["_pipeline_source"]}, Story context: {story or "UNSCOPED"}, Layer: {entity.get("layer")}, Entity: {index}, WCS',
                    'value': entity['points_wcs'], 'unit': {4: 'mm', 5: 'cm', 6: 'm'}[unit_code],
                    'row_verified': True, 'sha256': doc['_pipeline_sha256']}
                result[name] = geometry
            except (ValueError, KeyError, TypeError) as error:
                issues.append({'source': doc['_pipeline_source'], 'entity': index, 'error': str(error)})
    return result, issues


def _coordinates(rows):
    result = []
    for row in rows:
        if _key(row['sheet']) not in ('jointcoordinates', 'pointcoordinates'):
            continue
        coords = []
        for name in ('X', 'Y', 'Z'):
            cell = _cell(row, name)
            coords.append(_convert(cell['value'], cell['unit'], LENGTH, name))
        result.append({'joint': _text(row, 'Joint'), 'story': _text(row, 'Story', 'Floor', required=False),
                       'position': coords, 'ref': row['location']})
    return result


def _column(row, defaults, cad, coordinates, tolerance, coordinate_mode):
    name, story = _text(row, 'Column', 'ColumnName', 'Tên cột'), _text(row, 'Story', 'Floor', 'Tầng')
    angle_cell = _cell(row, 'Angle', 'Rotation')
    if _unit(angle_cell['unit']) not in ('deg', 'degree', 'degrees', '°'):
        raise PipelineDataError('SECTION_ANGLE_UNIT_REQUIRED')
    angle = math.radians(_number(angle_cell['value'], 'Angle'))
    matches = [g for (floor, label), g in cad.items() if label == _id_key(name) and floor in ('', _id_key(story))]
    if len(matches) > 1:
        raise PipelineDataError('CAD_STORY_BINDING_AMBIGUOUS')
    geometry = matches[0] if matches else None
    def distance(p, q):
        return math.dist(p[:2], q[:2]) if coordinate_mode == 'XY_STORY' else math.dist(p, q)
    center, evidence = None, []
    if geometry:
        center = geometry['center']
        # Transform the actual CAD outline into the declared section axes.
        local_x = [(p[0]-center[0])*math.cos(angle)+(p[1]-center[1])*math.sin(angle) for p in geometry['points']]
        local_y = [-(p[0]-center[0])*math.sin(angle)+(p[1]-center[1])*math.cos(angle) for p in geometry['points']]
        b, h = max(local_x)-min(local_x), max(local_y)-min(local_y)
        if not all(abs(abs(x)-b/2) < tolerance and abs(abs(y)-h/2) < tolerance for x, y in zip(local_x, local_y)):
            raise PipelineDataError('SECTION_ANGLE_DOES_NOT_ALIGN_WITH_CAD')
        b_source = h_source = geometry['cell']
        for dimension, actual in [('b', b), ('h', h)]:
            field = _cell(row, dimension, required=False)
            if field and abs(_convert(field['value'], field['unit'], LENGTH, dimension)-actual) > tolerance:
                raise PipelineDataError('CAD_SCHEDULE_DIMENSION_CONFLICT:'+dimension)
    else:
        b_source, h_source = _cell(row, 'b', 'Width'), _cell(row, 'h', 'Depth')
        b = _convert(b_source['value'], b_source['unit'], LENGTH, 'b')
        h = _convert(h_source['value'], h_source['unit'], LENGTH, 'h')
        point_cells = [_cell(row, axis, required=False) for axis in ('X', 'Y', 'Z')]
        if any(point_cells):
            if not all(point_cells):
                raise PipelineDataError('INCOMPLETE_COLUMN_COORDINATES')
            center = [_convert(c['value'], c['unit'], LENGTH, axis) for axis, c in zip(('X', 'Y', 'Z'), point_cells)]
    evidence.extend([_provenance('b', b, 'mm', b_source, 'CAD/local-axis extent or declared width -> mm'),
                     _provenance('h', h, 'mm', h_source, 'CAD/local-axis extent or declared depth -> mm')])
    for key in ('concrete', 'rebar'):
        cell = _cell(row, key)
        evidence.append(_provenance(key, _identifier(cell['value']), '1', cell))
    bar_cell = _cell(row, 'Bars', 'BarLayout')
    if _unit(bar_cell['unit']) != 'mm':
        raise PipelineDataError('BAR_LAYOUT_REQUIRES_MM_COORDINATES_AND_MM2_AREA')
    bars = json.loads(bar_cell['value']) if isinstance(bar_cell['value'], str) else copy.deepcopy(bar_cell['value'])
    if not isinstance(bars, list) or not bars:
        raise PipelineDataError('EXPLICIT_BAR_LAYOUT_REQUIRED')
    normalized_bars = []
    for index, bar in enumerate(bars):
        if not isinstance(bar, dict) or set(bar)-{'x', 'y', 'area', 'dia'}:
            raise PipelineDataError('INVALID_BAR_LAYOUT_RECORD')
        x, y = _number(bar.get('x'), 'bar.x'), _number(bar.get('y'), 'bar.y')
        diameter = _number(bar['dia'], 'bar.dia') if 'dia' in bar else None
        if diameter is not None and diameter <= 0:
            raise PipelineDataError('NONPOSITIVE_BAR_DIAMETER')
        area = _number(bar['area'], 'bar.area') if 'area' in bar else math.pi*diameter**2/4 if diameter is not None else None
        if area is None or area <= 0:
            raise PipelineDataError('MISSING_OR_NONPOSITIVE_BAR_AREA')
        if diameter is not None and abs(area-math.pi*diameter**2/4) > 1e-6*area:
            raise PipelineDataError('BAR_AREA_DIAMETER_CONFLICT')
        normalized_bars.append(dict(area=area, x=x, y=y))
        for key, value in [('area', area), ('x', x), ('y', y)]:
            evidence.append(_provenance(f'bars[{index}].{key}', value, 'mm2' if key == 'area' else 'mm', bar_cell,
                                       f'JSON bar {index}: '+('area or pi*dia^2/4' if key == 'area' else key)))
    values, material_evidence = _material_inputs(row, defaults)
    values.update(b=b, h=h, bars=normalized_bars, concrete=_text(row, 'Concrete'), rebar=_text(row, 'Rebar'))
    evidence.extend(material_evidence)
    joint = _text(row, 'Joint', 'JointID', required=False)
    binding_method = 'EXPLICIT_DOCUMENT_ID'
    if not joint:
        if center is None:
            raise PipelineDataError('JOINT_ID_OR_3D_POSITION_REQUIRED')
        candidates = [p for p in coordinates if (p['story'] or coordinate_mode != 'XY_STORY')
                      and (not p['story'] or _id_key(p['story']) == _id_key(story))
                      and distance(center, p['position']) <= tolerance]
        if len(candidates) != 1:
            raise PipelineDataError('JOINT_COORDINATE_BINDING_MISSING_OR_AMBIGUOUS')
        joint, binding_method = candidates[0]['joint'], 'UNIQUE_3D_WCS_COORDINATES'
    same_id = [p for p in coordinates if _id_key(p['joint']) == _id_key(joint) and (not p['story'] or _id_key(p['story']) == _id_key(story))]
    if center is not None and coordinate_mode == 'XY_STORY' and any(not p['story'] for p in same_id):
        raise PipelineDataError('COORDINATE_STORY_REQUIRED_FOR_2D_PLAN_BINDING')
    if len(same_id) > 1:
        raise PipelineDataError('DUPLICATE_JOINT_COORDINATES')
    offset = [0., 0., 0.]
    if center is not None and same_id:
        offset = [same_id[0]['position'][i]-center[i] for i in range(3)]
        if distance(same_id[0]['position'], center) > tolerance:
            raise PipelineDataError('JOINT_AND_COLUMN_POSITION_CONFLICT')
    return {'name': name, 'story': story, 'joint': joint, 'angle': angle, 'angle_source': angle_cell, 'values': values,
            'provenance': evidence, 'binding': {'method': binding_method, 'joint': joint,
                'source': row['location'], 'angle_ref': angle_cell['ref'], 'joint_offset_mm': offset,
                'coordinate_ref': same_id[0]['ref'] if same_id else None,
                'coordinate_mode': coordinate_mode,
                'cad_story': geometry['story'] if geometry else None,
                'cad_ref': geometry['cell']['ref'] if geometry else None}}


def _load_cases(rows, conventions):
    if not isinstance(conventions, dict) or conventions.get('reaction_axes') != 'GLOBAL':
        raise PipelineDataError('EXPLICIT_GLOBAL_REACTION_AXIS_CONVENTION_REQUIRED')
    for key in ('axial_sign', 'mx_sign', 'my_sign'):
        if type(conventions.get(key)) not in (int, float) or conventions[key] not in (-1, 1):
            raise PipelineDataError('EXPLICIT_SIGN_CONVENTION_REQUIRED:'+key)
    names = [conventions.get('axial_column', 'F3'), conventions.get('mx_column', 'M1'), conventions.get('my_column', 'M2')]
    if len({_column_key(name) for name in names}) != 3:
        raise PipelineDataError('LOAD_COMPONENT_COLUMNS_MUST_BE_DISTINCT')
    cases = []
    for row in rows:
        if row['table_type'] != 'joint_reactions' and _key(row['sheet']) != 'jointreactions':
            continue
        item = {'joint': _text(row, 'Joint'), 'story': _text(row, 'Story', 'Floor', required=False),
                'case': _text(row, 'OutputCase', 'Case', 'Combo'), 'row': row, 'error': None}
        try:
            step_type = _text(row, 'StepType', required=False)
            case_type = _text(row, 'CaseType', required=False)
            item['step'] = _text(row, 'StepNum', 'Step', required=False)
            item['step_type'] = step_type
            if any(re.search(r'(?i)max|min|envelope', value) for value in (step_type, case_type)):
                raise PipelineDataError('NONCONCURRENT_ENVELOPE_ROW_REJECTED')
            if re.search(r'(?i)envelope', item['case']):
                raise PipelineDataError('NONCONCURRENT_ENVELOPE_CASE_REJECTED')
            if _key(step_type) in ('step', 'time', 'mode') and not item['step']:
                raise PipelineDataError('CONCURRENT_STEP_NUMBER_REQUIRED')
            cells = [_cell(row, name) for name in names]
            item['cells'] = cells
            item['N'] = _convert(cells[0]['value'], cells[0]['unit'], FORCE, names[0])*conventions['axial_sign']
            item['Mx'] = _convert(cells[1]['value'], cells[1]['unit'], MOMENT, names[1])*conventions['mx_sign']
            item['My'] = _convert(cells[2]['value'], cells[2]['unit'], MOMENT, names[2])*conventions['my_sign']
            for cell in cells:
                if not cell['row_verified']:
                    raise PipelineDataError('UNRESOLVED_REACTION_SOURCE_ROW')
            if item['N'] < 0:
                raise PipelineDataError('TENSION_CASE_NOT_SUPPORTED_BY_COMPRESSION_SOLVER')
        except (ValueError, TypeError, KeyError) as error:
            item['error'] = str(error)
        cases.append(item)
    if not cases:
        raise PipelineDataError('NO_JOINT_REACTIONS_FOUND')
    return cases


def _bound_case(column, case, conventions):
    N, mx, my = case['N'], case['Mx'], case['My']
    dx, dy, _ = column['binding']['joint_offset_mm']
    mx, my = mx+N*dy/1000, my+N*dx/1000
    angle = column['angle']
    values = dict(N_ed=N, Mx_ed=mx*math.cos(angle)+my*math.sin(angle),
                  My_ed=-mx*math.sin(angle)+my*math.cos(angle))
    records = []
    combined = copy.deepcopy(case['cells'][1])
    combined['ref'] += ' + '+case['cells'][2]['ref']+' + '+case['cells'][0]['ref']+'; Section axes: '+column['binding']['angle_ref']
    combined['value'] = {'raw_axial': case['cells'][0]['value'], 'raw_mx': case['cells'][1]['value'],
                         'raw_my': case['cells'][2]['value'], 'section_angle_deg': column['angle_source']['value'],
                         'derived_offset_mm': [dx, dy]}
    combined['unit'] = {'axial': case['cells'][0]['unit'], 'mx': case['cells'][1]['unit'],
                        'my': case['cells'][2]['unit'], 'section_angle': column['angle_source']['unit'], 'offset': 'mm'}
    if dx or dy:
        combined['ref'] += '; Joint coordinates: '+str(column['binding']['coordinate_ref'])
        combined['ref'] += '; Section center: '+(column['binding']['cad_ref'] or column['binding']['source'])
    transform = ('explicit signs '+str({key: conventions[key] for key in ('axial_sign', 'mx_sign', 'my_sign')})+
                 f'; N*offset moments dx={dx}mm,dy={dy}mm; GLOBAL->LOCAL angle={math.degrees(angle)}deg')
    for name, value in values.items():
        records.append(_provenance(name, value, 'kN' if name == 'N_ed' else 'kNm',
                                   case['cells'][0] if name == 'N_ed' else combined, transform))
    return values, records


def prepare_project_pipeline(sources, *, conventions=None, solver_options=None, stories=None,
                         coordinate_tolerance_mm=1., label_tolerance_mm=500., coordinate_mode='XYZ'):
    """Return a deterministic schedule plus every evaluated concurrent case.

    A missing/invalid case prevents a column PASS even if another row converges.
    Known failures take precedence; uncheckable columns are never assigned zero eta.
    """
    options = dict(generate_surface=False)
    options.update(solver_options or {})
    if set(options)-CONTROLS:
        raise PipelineDataError('SOLVER_OPTIONS_CANNOT_OVERRIDE_PHYSICAL_INPUTS_OR_PROVENANCE')
    tolerance = _number(coordinate_tolerance_mm, 'coordinate_tolerance_mm')
    label_tolerance = _number(label_tolerance_mm, 'label_tolerance_mm')
    if tolerance <= 0 or label_tolerance <= 0:
        raise PipelineDataError('BINDING_TOLERANCES_MUST_BE_POSITIVE')
    if coordinate_mode not in ('XYZ', 'XY_STORY'):
        raise PipelineDataError('COORDINATE_MODE_MUST_BE_XYZ_OR_XY_STORY')
    if stories is not None and (not isinstance(stories, list) or not stories):
        raise PipelineDataError('STORIES_FILTER_MUST_BE_A_NONEMPTY_LIST')
    documents = _load_sources(sources)
    rows = list(_rows(documents))
    defaults = _model_parameters(rows)
    cad, issues = _cad_columns(documents, label_tolerance, stories)
    coordinates = _coordinates(rows)
    cases = _load_cases(rows, conventions)
    excluded_rows = []
    if stories:
        excluded_rows = [case['row']['location'] for case in cases if case['story'] and _id_key(case['story']) not in {_id_key(s) for s in stories}]
        cases = [case for case in cases if not case['story'] or _id_key(case['story']) in {_id_key(s) for s in stories}]
    column_rows = [row for row in rows if _key(row['sheet']) in ('columnschedule', 'columns', 'sectionschedule')
                   or (_column_key('Column') in row['cells'] and ('bars' in row['cells'] or 'barlayout' in row['cells']))]
    if stories is not None:
        if not isinstance(stories, list) or not stories:
            raise PipelineDataError('STORIES_FILTER_MUST_BE_A_NONEMPTY_LIST')
        column_rows = [row for row in column_rows if _id_key(_text(row, 'Story', 'Floor', 'Tầng')) in {_id_key(s) for s in stories}]
    if not column_rows:
        raise PipelineDataError('NO_COLUMN_SCHEDULE_OR_EXPLICIT_REBAR_LAYOUT')
    members = []
    seen = {}
    for row in column_rows:
        name = _text(row, 'Column', 'ColumnName', 'Tên cột')
        story = _text(row, 'Story', 'Floor', 'Tầng')
        member = {'column': name, 'story': story, 'case_results': [], 'errors': [], 'governing': None,
                  'state': 'BLOCKED', 'approved': False}
        members.append(member)
        identity = (_id_key(story), _id_key(name))
        if identity in seen:
            member['errors'].append('DUPLICATE_COLUMN_IDENTITY')
            seen[identity]['errors'].append('DUPLICATE_COLUMN_IDENTITY')
            continue
        seen[identity] = member
        try:
            member['_column'] = _column(row, defaults, cad, coordinates, tolerance, coordinate_mode)
            if any(str(doc.get('file_type', '')).upper() in ('DWG', 'DXF') for doc in documents) and not member['_column']['binding']['cad_ref']:
                raise PipelineDataError('COLUMN_NOT_UNIQUELY_RESOLVED_IN_SUPPLIED_CAD')
        except (ValueError, TypeError, KeyError) as error:
            member['errors'].append(str(error))
    for (floor, name), geometry in sorted(cad.items()):
        if any(_id_key(member['column']) == name and (not floor or _id_key(member['story']) == floor) for member in members):
            continue
        members.append({'column': geometry['name'], 'story': geometry['story'] or 'UNRESOLVED', 'case_results': [], 'errors': ['CAD_COLUMN_WITHOUT_SCHEDULE_OR_REBAR_LAYOUT'],
                        'governing': None, 'state': 'BLOCKED', 'approved': False})
        issues.append({'column': geometry['name'], 'error': 'CAD_COLUMN_WITHOUT_SCHEDULE_OR_REBAR_LAYOUT'})
    for member in members:
        column = member.get('_column')
        if not column:
            continue
        for other in members:
            peer = other.get('_column')
            if peer and other is not member and column['binding']['cad_ref'] and column['binding']['cad_story'] == '' and \
                    column['binding']['cad_ref'] == peer['binding']['cad_ref'] and _id_key(peer['story']) != _id_key(column['story']):
                member['errors'].append('UNSCOPED_CAD_REUSED_ACROSS_STORIES')
            if peer and other is not member and _id_key(peer['joint']) == _id_key(column['joint']):
                if _id_key(peer['story']) == _id_key(column['story']) or any(not case['story'] and _id_key(case['joint']) == _id_key(column['joint']) for case in cases):
                    member['errors'].append('JOINT_ASSIGNED_TO_MULTIPLE_COLUMNS_OR_UNKNOWN_STORIES')
                    break
    return {'schema_version': 'project.prepared.v1', 'documents': documents, 'members': members,
            'cases': cases, 'issues': issues, 'excluded_rows': excluded_rows, 'options': options,
            'conventions': copy.deepcopy(conventions), 'coordinate_mode': coordinate_mode}


def calculate_prepared_project(prepared, *, calculation_executor=None):
    """Evaluate an immutable prepared snapshot; executor is trusted Python integration only."""
    if not isinstance(prepared, dict) or prepared.get('schema_version') != 'project.prepared.v1':
        raise PipelineDataError('INVALID_PREPARED_PROJECT')
    if calculation_executor is not None and not callable(calculation_executor):
        raise PipelineDataError('CALCULATION_EXECUTOR_MUST_BE_A_TRUSTED_CALLABLE')
    snapshot = copy.deepcopy(prepared)
    documents, members, cases = (snapshot[key] for key in ('documents', 'members', 'cases'))
    issues, excluded_rows, options = (snapshot[key] for key in ('issues', 'excluded_rows', 'options'))
    conventions, coordinate_mode = snapshot['conventions'], snapshot['coordinate_mode']
    executor = calculation_executor or calc_rc_section_pm_3d
    consumed_cases = set()
    for member in members:
        column = member.get('_column')
        if not column or member['errors']:
            continue
        member['Binding'] = column['binding']
        relevant = [(i, case) for i, case in enumerate(cases) if _id_key(case['joint']) == _id_key(column['joint'])
                    and (not case['story'] or _id_key(case['story']) == _id_key(column['story']))]
        if not relevant:
            member['errors'].append('NO_LOAD_CASES_FOR_BOUND_JOINT')
            continue
        identities = set()
        for index, case in relevant:
            consumed_cases.add(index)
            identity = (case['case'], case.get('step_type'), case.get('step'))
            if identity in identities:
                member['errors'].append('DUPLICATE_CONCURRENT_CASE_OR_STEP:'+case['row']['location'])
            identities.add(identity)
        if member['errors']:
            continue
        for _, case in relevant:
            entry = {'case': case['case'], 'step': case.get('step'), 'source': case['row']['location'], 'error': case['error']}
            member['case_results'].append(entry)
            if case['error']:
                member['errors'].append(case['error']+':'+case['row']['location'])
                continue
            try:
                loads, records = _bound_case(column, case, conventions)
                inputs = dict(column['values'], **loads)
                provenance = column['provenance']+records
                preflight = audit_inputs(inputs, provenance)
                if not preflight['allowed']:
                    raise PipelineDataError('PIPELINE_PROVENANCE_PREFLIGHT_BLOCKED')
                calculation = executor(**inputs, **options, provenance=provenance, require_provenance=True)
                entry.update(inputs=inputs, Provenance=provenance, calculation=calculation)
                if calculation['status'] not in ('OK', 'FAILED') or (calculation['status'] == 'OK' and not calculation['Input_Provenance_Audit']['allowed']):
                    member['errors'].append('CASE_NOT_CONCLUSIVE:'+case['row']['location'])
            except (ValueError, TypeError, KeyError, ArithmeticError) as error:
                entry['error'] = str(error)
                member['errors'].append(str(error)+':'+case['row']['location'])
        evaluated = [item for item in member['case_results'] if 'calculation' in item]
        failures = [item for item in evaluated if item['calculation']['section_check'] == 'FAIL']
        finite = [item for item in evaluated if item['calculation'].get('eta') is not None]
        undefined_failure = [item for item in failures if item['calculation'].get('eta') is None]
        governing = undefined_failure[0] if undefined_failure else max(finite, key=lambda item: item['calculation']['eta']) if finite else None
        member['governing'] = governing
        member['governing_is_final'] = not member['errors']
        if failures:
            member['state'] = 'FAIL'
        elif not member['errors'] and len(evaluated) == len(relevant) and all(item['calculation']['approved'] for item in evaluated):
            member.update(state='PASS', approved=True)
        else:
            member['state'] = 'INCONCLUSIVE'
    schedule = []
    for index, member in enumerate(members, 1):
        column = member.pop('_column', None)
        inputs = column['values'] if column else {}
        governing = member['governing']
        loads = governing.get('inputs', {}) if governing else {}
        status = 'ĐẠT' if member['state'] == 'PASS' else 'KHÔNG ĐẠT' if member['state'] == 'FAIL' else 'CHƯA ĐỦ DỮ LIỆU'
        summary = {'STT': index, 'Tên cột': member['column'], 'Tầng': member['story'],
            'Tiết diện': f'{inputs["b"]:g}×{inputs["h"]:g} mm' if inputs else None,
            'Thép': f'{len(inputs["bars"])} thanh; As={sum(b["area"] for b in inputs["bars"]):.2f} mm²; {inputs["rebar"]}' if inputs else None,
            'N (kN)': loads.get('N_ed'), 'Mx (kNm)': loads.get('Mx_ed'), 'My (kNm)': loads.get('My_ed'),
            'η': governing['calculation'].get('eta') if governing else None, 'Trạng thái': status}
        member['summary'] = summary
        schedule.append(summary)
    orphan_cases = [case['row']['location'] for index, case in enumerate(cases) if index not in consumed_cases]
    counts = {state: sum(member['state'] == state for member in members) for state in ('PASS', 'FAIL', 'BLOCKED', 'INCONCLUSIVE')}
    complete = counts['PASS']+counts['FAIL']
    blocked = bool(issues or orphan_cases or any(member['errors'] for member in members))
    return {'status': 'COMPLETED' if complete == len(members) and not blocked else 'PARTIAL' if complete else 'BLOCKED',
        'all_passed': counts['PASS'] == len(members) and not blocked,
        'counts': {'total': len(members), **counts}, 'schedule': schedule,
        'summary_table': {'headers': SUMMARY_HEADERS, 'rows': [[row[key] for key in SUMMARY_HEADERS] for row in schedule]},
        'members': members, 'binding_issues': issues, 'unbound_reaction_rows': orphan_cases,
        'excluded_by_story_filter': excluded_rows,
        'reader_warnings': {doc['_pipeline_source']: doc['metadata'].get('warnings', []) for doc in documents},
        'source_verification': [{'source': doc['_pipeline_source'], 'scope': doc['_pipeline_source_verification'],
                                  'sha256': doc['_pipeline_sha256']} for doc in documents],
        'Execution_Settings': options, 'Conventions': conventions, 'coordinate_mode': coordinate_mode,
        'Scope_Limitation': ['Section material strength only; member stability/P-delta and project safety are not checked.',
                            'Required design moments/member effects and concurrent combinations must be supplied upstream.',
                            'Verified provenance means extraction and binding, not independent source-content or OCR validation.'],
        'Calculation_Logs': [{'Step': 'Evaluate all concurrent rows and select governing utilization',
                              'Rule': 'No independently enveloped N/Mx/My; no PASS if a bound case is uncheckable',
                              'Result': counts}]}



def run_project_pipeline(sources, *, conventions=None, solver_options=None, stories=None,
                         coordinate_tolerance_mm=1., label_tolerance_mm=500., coordinate_mode='XYZ'):
    """Backward-compatible one-shot execution; durable orchestration uses the two stages."""
    prepared = prepare_project_pipeline(sources, conventions=conventions, solver_options=solver_options,
        stories=stories, coordinate_tolerance_mm=coordinate_tolerance_mm,
        label_tolerance_mm=label_tolerance_mm, coordinate_mode=coordinate_mode)
    return calculate_prepared_project(prepared)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', '-i', required=True, help='Absolute path to manifest JSON')
    parser.add_argument('--output', '-o')
    parser.add_argument('--summary-csv')
    args = parser.parse_args(argv)
    try:
        manifest = _read_json(Path(args.input).resolve())
        result = run_project_pipeline(**manifest)
        code = 0 if result['all_passed'] else 1
    except (ValueError, TypeError, KeyError, OSError) as error:
        result, code = {'status': 'ERROR', 'all_passed': False, 'error': f'{type(error).__name__}: {error}'}, 2
    outputs = [Path(value).resolve() for value in (args.output, args.summary_csv) if value]
    protected = {Path(args.input).resolve()}
    if 'manifest' in locals() and isinstance(manifest, dict):
        sources = manifest.get('sources', [])
        if isinstance(sources, (str, Path)):
            sources = [sources]
        for source in sources:
            if isinstance(source, (str, Path)):
                protected.add(Path(source).resolve())
    if any(path in protected or path.exists() for path in outputs) or len(outputs) != len(set(outputs)):
        parser.error('Outputs must be new paths and must not overwrite input sources or each other')
    encoded = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)
    if args.output:
        Path(args.output).resolve().write_text(encoded, encoding='utf-8')
    if args.summary_csv and 'summary_table' in result:
        with Path(args.summary_csv).resolve().open('w', encoding='utf-8-sig', newline='') as output:
            writer = csv.writer(output)
            writer.writerow(SUMMARY_HEADERS)
            writer.writerows(result['summary_table']['rows'])
    print(encoded)
    return code


if __name__ == '__main__':
    sys.exit(main())
