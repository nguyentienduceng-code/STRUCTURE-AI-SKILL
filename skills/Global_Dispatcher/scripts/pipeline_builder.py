#!/usr/bin/env python3
"""
Pipeline Builder — Xây dựng và quản lý pipeline thực thi khi cần 2+ Skills.

Usage:
    python pipeline_builder.py --skills "Structural_Design_Engineer,Design_Evaluation"
    python pipeline_builder.py --skills "SKILL_GEOTECH,Structural_Design_Engineer,Cost_Estimator" --verbose
    python pipeline_builder.py --template "design_then_review"
    python pipeline_builder.py --list-templates

Output JSON:
    {
        "pipeline_id": "PL-SDE-DE-20261012-001",
        "stages": [...],
        "handoff_schemas": [...],
        "estimated_steps": 5,
        "review_gates": [...]
    }
"""

import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

import json
import re
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional


# ============================================================================
# CONFIGURATION
# ============================================================================

SCRIPT_DIR = Path(__file__).parent
KEYWORD_DB_PATH = SCRIPT_DIR / "keyword_database.json"

# Skill execution order priority (lower = earlier)
EXECUTION_ORDER = {
    "SKILL_GEOTECH": 10,
    "SKILL_FORENSIC": 15,
    "Structural_Design_Engineer": 20,
    "SKILL_PHULUC": 25,
    "SKILL_TEMPWORKS": 28,
    "Design_Evaluation": 30,
    "Technical_Illustrator": 35,
    "SKILL_VERIFY": 40,
    "Cost_Estimator": 50,
    "SKILL_RFI": 55,
    "Project_Manager": 60,
    "SKILL_BIM_COORDINATION": 65,
    "SKILL_DUAL_AGENT_BRIDGE": 70,
}

# Handoff schemas between skill pairs
HANDOFF_SCHEMAS = {
    ("SKILL_GEOTECH", "Structural_Design_Engineer"): "geotech_to_structural",
    ("Structural_Design_Engineer", "Design_Evaluation"): "structural_design_to_eval",
    ("Structural_Design_Engineer", "SKILL_TEMPWORKS"): "structural_to_tempworks",
    ("Design_Evaluation", "SKILL_PHULUC"): "eval_to_phuluc",
    ("Design_Evaluation", "Cost_Estimator"): "eval_to_cost",
    ("Structural_Design_Engineer", "Cost_Estimator"): "structural_to_cost",
    ("Structural_Design_Engineer", "SKILL_VERIFY"): "calc_to_verify",
    ("Design_Evaluation", "SKILL_VERIFY"): "calc_to_verify",
    ("SKILL_TEMPWORKS", "Cost_Estimator"): "tempworks_to_cost",
    ("SKILL_TEMPWORKS", "Technical_Illustrator"): "tempworks_to_illustrator",
    ("SKILL_TEMPWORKS", "SKILL_VERIFY"): "calc_to_verify",
    ("SKILL_FORENSIC", "Design_Evaluation"): "forensic_to_eval",
    ("SKILL_GEOTECH", "Design_Evaluation"): "geotech_to_design_eval",
    ("SKILL_GEOTECH", "SKILL_FORENSIC"): "geotech_to_forensic",
}

# Review gates — stages after which user approval is required
REVIEW_GATE_SKILLS = {
    "Design_Evaluation",
    "Structural_Design_Engineer",
    "SKILL_FORENSIC",
    "SKILL_TEMPWORKS",
}

# Skills that can run in parallel
PARALLEL_GROUPS = {
    "post_design": ["SKILL_VERIFY", "Technical_Illustrator", "Cost_Estimator"],
    "post_geotech": ["Structural_Design_Engineer", "Design_Evaluation"],
}


# ============================================================================
# PIPELINE BUILDER
# ============================================================================

class PipelineBuilder:
    """Xây dựng pipeline thực thi tự động từ danh sách skills."""

    def __init__(self, db_path: str = None, max_stages: int = 64):
        if isinstance(max_stages, bool) or not isinstance(max_stages, int) or max_stages < 1:
            raise ValueError("max_stages must be a positive integer")
        self.max_stages = max_stages
        self.db_path = db_path or str(KEYWORD_DB_PATH)
        self.db = self._load_database()
        self.templates = self.db.get("pipeline_templates", {})

    def _load_database(self) -> dict:
        """Load keyword database."""
        try:
            with open(self.db_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {"pipeline_templates": {}}

    def build(self, skills: List[str], context: str = "") -> dict:
        """
        Xây dựng pipeline từ danh sách skills.

        Args:
            skills: Danh sách tên skill theo thứ tự mong muốn
            context: Mô tả ngắn về bối cảnh

        Returns:
            Pipeline definition JSON
        """
        # Validate skills
        valid_skills = []
        warnings = []
        for skill in skills:
            if skill in EXECUTION_ORDER:
                valid_skills.append(skill)
            else:
                warnings.append(f"Skill '{skill}' không tìm thấy trong hệ thống")

        if not valid_skills:
            return {
                "error": "Không có skill hợp lệ nào",
                "warnings": warnings
            }

        # Sort by execution order
        sorted_skills = list(valid_skills)  # Explicit requested order is semantic, not a priority sort.

        # Build pipeline ID
        skill_ids = [s[:3].upper() for s in sorted_skills]
        timestamp = datetime.now().strftime("%Y%m%d")
        pipeline_id = f"PL-{'-'.join(skill_ids)}-{timestamp}-001"

        # Build stages
        stages = []
        for i, skill in enumerate(sorted_skills):
            stage = self._build_stage(i + 1, skill, sorted_skills)
            stages.append(stage)

        # Determine handoff schemas
        handoff_schemas = []
        for i in range(len(sorted_skills) - 1):
            pair = (sorted_skills[i], sorted_skills[i + 1])
            schema_type = HANDOFF_SCHEMAS.get(pair, "generic_handoff")
            handoff_schemas.append({
                "from": sorted_skills[i],
                "to": sorted_skills[i + 1],
                "schema_type": schema_type,
                "auto_generate": True
            })

        # Identify review gates
        review_gates = []
        for i, skill in enumerate(sorted_skills):
            if skill in REVIEW_GATE_SKILLS:
                review_gates.append({
                    "after_stage": i + 1,
                    "skill": skill,
                    "action": "USER_APPROVAL",
                    "message": f"Review kết quả {skill} trước khi tiếp tục"
                })

        # Detect parallel opportunities
        parallel_stages = self._detect_parallel(sorted_skills)

        # Estimate total steps
        estimated_steps = sum(s.get("estimated_sub_steps", 1) for s in stages)

        # Pre-Execution Approval Gate configuration (AGENTS.md §3 / P0 Architecture)
        requires_pre_approval = len(sorted_skills) >= 2 or estimated_steps >= 3
        max_repair_iterations = 3

        pipeline = {
            "pipeline_id": pipeline_id,
            "created_at": datetime.now().isoformat(),
            "context": context,
            "total_skills": len(sorted_skills),
            "requires_pre_approval": requires_pre_approval,
            "max_repair_iterations": max_repair_iterations,
            "stages": stages,
            "handoff_schemas": handoff_schemas,
            "review_gates": review_gates,
            "parallel_opportunities": parallel_stages,
            "estimated_steps": estimated_steps,
            "warnings": warnings,
            "execution_instructions": self._build_instructions(sorted_skills, review_gates)
        }

        pipeline["skills"] = sorted_skills
        pipeline.update(self._graph_metadata(stages))
        pipeline["parallel_opportunities"] = []  # A linear plan has no runnable parallel branches.
        return pipeline

    def build_from_template(self, template_name: str) -> dict:
        """Xây dựng pipeline từ template có sẵn."""
        if template_name not in self.templates:
            return {
                "error": f"Template '{template_name}' không tồn tại",
                "available_templates": list(self.templates.keys())
            }

        template = self.templates[template_name]
        return self.build(
            skills=template["skills"],
            context=template.get("description", "")
        )

    @staticmethod
    def _ascii(text):
        import unicodedata
        text = text.lower().replace('đ', 'd')
        return ''.join(c for c in unicodedata.normalize('NFD', text)
                       if unicodedata.category(c) != 'Mn')

    @staticmethod
    def _graph_metadata(stages):
        """Kahn layers are executable dependency layers, not fixed skill priorities."""
        ids = {s['stage'] for s in stages}
        if len(ids) != len(stages):
            raise ValueError('Duplicate stage identifiers')
        remaining = {}
        edges = []
        for stage in stages:
            deps = set(stage['depends_on'])
            if not deps <= ids or stage['stage'] in deps:
                raise ValueError('Unknown dependency or self-cycle')
            condition = stage.get('condition')
            if condition and condition['source_stage'] not in deps:
                raise ValueError('Condition source must be a dependency')
            remaining[stage['stage']] = deps
            edges.extend({'from': dep, 'to': stage['stage']} for dep in sorted(deps))
        layers, order = [], []
        while remaining:
            ready = sorted(k for k, deps in remaining.items() if not deps)
            if not ready:
                raise ValueError('Workflow contains a cycle')
            layers.append(ready)
            order.extend(ready)
            remaining = {k: deps - set(ready) for k, deps in remaining.items() if k not in ready}
        return {'schema_version': '2.0', 'graph_type': 'DAG', 'edges': edges,
                'topological_order': order, 'execution_batches': layers}

    def build_dag(self, definitions, context=''):
        if not definitions:
            raise ValueError('Workflow must contain at least one stage')
        if len(definitions) > self.max_stages:
            raise ValueError('Workflow exceeds max_stages')
        skills = [s['skill'] for s in definitions]
        if any(s not in EXECUTION_ORDER for s in skills):
            raise ValueError('Unknown workflow skill')
        result = self.build(skills, context)
        for number, (stage, definition) in enumerate(zip(result['stages'], definitions), 1):
            stage['depends_on'] = list(dict.fromkeys(definition.get('depends_on', [])))
            stage['condition'] = definition.get('condition')
            stage['join_policy'] = definition.get('join_policy', 'all_success')
            stage['task'] = definition.get('task', '')
            stage['node_id'] = number
            condition = stage['condition']
            if condition:
                if condition.get('op') not in {'in', '>', '>=', '<', '<=', '==', '!='}:
                    raise ValueError('Unsupported condition operator')
                if condition.get('field') not in {'status', 'eta', 'confidence'}:
                    raise ValueError('Unsupported condition field')
                import math
                expected = condition.get('value')
                if condition['field'] == 'status':
                    if condition['op'] != 'in' or not isinstance(expected, list) or not expected or any(not isinstance(x, str) for x in expected):
                        raise ValueError('Status condition needs a non-empty string list')
                elif condition['op'] == 'in' or isinstance(expected, bool) or not isinstance(expected, (int, float)) or not math.isfinite(expected):
                    raise ValueError('Numeric condition needs a finite numeric value')
                if not isinstance(condition.get('negate', False), bool):
                    raise ValueError('Condition negate must be boolean')
            if stage['join_policy'] not in {'all_success', 'all_terminal'}:
                raise ValueError('Unsupported join policy')
        result.update(self._graph_metadata(result['stages']))
        result['parallel_opportunities'] = [
            {'group': 'dag_batch', 'stages': batch,
             'skills': [result['stages'][i-1]['skill'] for i in batch]}
            for batch in result['execution_batches'] if len(batch) > 1]
        # Handoffs follow actual graph edges, including fan-out and joins.
        result['handoff_schemas'] = []
        for edge in result['edges']:
            source, target = (result['stages'][edge[key]-1]['skill'] for key in ('from', 'to'))
            result['handoff_schemas'].append({**edge, 'from_skill': source, 'to_skill': target,
                'schema_type': HANDOFF_SCHEMAS.get((source, target), 'generic_handoff'),
                'auto_generate': True})
        result['execution_instructions'] = (
            'Use ready_stages(states); execute only returned ready nodes. '
            'Persist SUCCESS/FAILURE/SKIPPED outputs. Unknown conditions remain pending. '
            'Respect review_gates; parallel batches require disjoint output files.')
        return result

    @staticmethod
    def _parse_condition(text, source):
        text = text.strip(' ,:')
        numeric = re.fullmatch(r'(eta|confidence)\s*(>=|<=|>|<|==|!=)\s*(\d+(?:\.\d+)?)', text)
        if numeric:
            return {'source_stage': source, 'field': numeric[1], 'op': numeric[2],
                    'value': float(numeric[3]), 'negate': False}
        success = {'dat', 'pass', 'thanh cong', 'kiem chung dat', 'ket qua dat', 'success'}
        failure = {'khong dat', 'fail', 'that bai', 'kiem chung khong dat', 'failure'}
        if text in success | failure:
            return {'source_stage': source, 'field': 'status', 'op': 'in',
                    'value': ['SUCCESS', 'PASS'] if text in success else ['FAILURE', 'FAIL', 'ERROR'],
                    'negate': False}
        raise ValueError(f'Unsupported condition: {text}')

    def plan(self, prompt, classify=None):
        """Bounded Vietnamese/English workflow grammar. Unresolved clauses fail closed."""
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError('Prompt must be a non-empty string')
        if classify is None:
            from intent_classifier import IntentClassifier
            classifier = IntentClassifier(self.db_path)
            classify = lambda text: classifier.classify(text, plan_workflow=False)
        text = self._ascii(prompt).replace("\n", ";")
        token = re.compile(
            r'(\b(?:neu|if)\b.*?\b(?:thi|then)\b|\bnguoc lai\b|\belse\b|'
            r'\bsong song\b|\bdong thoi\b|\bin parallel\b|\broi\b|\bsau do\b|'
            r'\btiep theo\b|\bthen\b|;|\n|\b(?:va|and)\b(?=\s+(?:tinh|ve|kiem|lap|xuat|thiet|phan|so|render|verify|calculate|export|estimate)))')
        parts = token.split(text)
        definitions, frontier, parallel, parallel_base = [], [], [], None
        branch, condition = None, None
        excluded = []
        join_policy = 'all_success'
        for part in parts:
            part = part.strip(' ,:.')
            if not part:
                continue
            if re.fullmatch(r'(?:neu|if)\b.*?\b(?:thi|then)', part):
                if branch is not None or not frontier:
                    raise ValueError('Nested/unsourced condition needs explicit workflow definitions')
                expression = re.sub(r'^(?:neu|if)\s+|\s+(?:thi|then)$', '', part)
                condition = self._parse_condition(expression, frontier[-1])
                branch = {'base': frontier[:], 'condition': condition, 'true': [], 'else': False}
                parallel_base = None
            elif part in {'nguoc lai', 'else'}:
                if branch is None or branch['else']:
                    raise ValueError('Else without a unique if')
                branch['true'] = frontier[:]
                frontier = branch['base'][:]
                condition = {**branch['condition'], 'negate': True}
                branch['else'] = True
                parallel_base = None
            elif part in {'song song', 'dong thoi', 'in parallel'}:
                parallel_base, parallel = frontier[:], []
            elif part in {'roi', 'sau do', 'tiep theo', 'then', ';', '\n'}:
                parallel_base = None
                if branch is not None and branch['else'] and frontier != branch['base']:
                    frontier = branch['true'] + frontier
                    branch, condition = None, None
                    join_policy = 'all_terminal'
            elif part in {'va', 'and'}:
                pass
            else:
                if re.match(r'^(khong\s+(?:can\s+)?|do not\s+|don.t\s+)', part):
                    excluded.append(part)
                    continue
                route = classify(part)
                # Action-scoped routing handles short clauses without leaking nouns from other steps.
                action_rules = [
                    (r'\b(?:lap|xuat|export)\b.*\bphu luc\b', 'SKILL_PHULUC'),
                    (r'\b(?:kiem chung|cross-check|verify|verification)\b', 'SKILL_VERIFY'),
                    (r'\b(?:chi phi|cost|boq)\b', 'Cost_Estimator'),
                    (r'\b(?:tinh|thiet ke|calculate|design)\s+(?:cot thep|dam|cot|san|mong|lien ket|beam|column|foundation)\b', 'Structural_Design_Engineer'),
                    (r'\b(?:lap|xuat)\s+to trinh\b', 'Design_Evaluation'),
                ]
                if not part.startswith('@'):
                    for pattern, chosen in action_rules:
                        if re.search(pattern, part):
                            route = {'primary_skill': chosen, 'confidence_level': 'HIGH'}
                            break
                skill = route.get('primary_skill')
                if not skill or route.get('confidence_level') == 'LOW':
                    raise ValueError(f'Unresolved workflow clause: {part}')
                deps = (parallel_base if parallel_base is not None else frontier)[:]
                if condition and condition['source_stage'] not in deps:
                    deps.append(condition['source_stage'])
                if len(definitions) >= self.max_stages:
                    raise ValueError('Workflow exceeds max_stages')
                definitions.append({'skill': skill, 'task': part, 'depends_on': deps,
                                    'condition': condition, 'join_policy': join_policy})
                join_policy = 'all_success'
                if parallel_base is not None:
                    parallel.append(len(definitions))
                    frontier = parallel[:]
                else:
                    frontier = [len(definitions)]
        result = self.build_dag(definitions, prompt)
        result.update({'template': 'dynamic_dag_v2', 'description': 'Conditional dependency workflow',
                       'excluded_clauses': excluded, 'trigger': 'explicit workflow grammar'})
        return result

    @staticmethod
    def ready_stages(pipeline, states):
        """Pure scheduler: ready/skipped/blocked. No tools or external side effects."""
        graph = PipelineBuilder._graph_metadata(pipeline['stages'])
        state = {int(k): (dict(v) if isinstance(v, dict) else {'status': v}) for k, v in states.items()}
        terminal = {'SUCCESS', 'PASS', 'FAILURE', 'FAIL', 'ERROR', 'SKIPPED'}
        success = {'SUCCESS', 'PASS'}
        ready, skipped, blocked = [], [], []
        for stage_id in graph['topological_order']:
            if stage_id in state:
                continue
            stage = pipeline['stages'][stage_id-1]
            deps = stage['depends_on']
            if not all(state.get(d, {}).get('status') in terminal for d in deps):
                continue
            cond = stage.get('condition')
            verdict = True
            if cond:
                source = state.get(cond['source_stage'], {})
                outputs = source.get('outputs')
                outputs = outputs if isinstance(outputs, dict) else {}
                value = source.get(cond['field'], outputs.get(cond['field']))
                if value is None:
                    continue
                op, expected = cond['op'], cond['value']
                if op == 'in':
                    verdict = value in expected
                else:
                    import math
                    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                        continue
                    verdict = {'>': lambda: value > expected, '>=': lambda: value >= expected,
                               '<': lambda: value < expected, '<=': lambda: value <= expected,
                               '==': lambda: value == expected, '!=': lambda: value != expected}[op]()
                if cond.get('negate'):
                    verdict = not verdict
            if not verdict:
                state[stage_id] = {'status': 'SKIPPED'}
                skipped.append(stage_id)
            elif any(state[d]['status'] == 'SKIPPED' for d in deps) and stage.get('join_policy') != 'all_terminal':
                state[stage_id] = {'status': 'SKIPPED'}
                skipped.append(stage_id)
            else:
                permitted = all(state[d]['status'] in success or
                    (cond and d == cond['source_stage']) or
                    (stage.get('join_policy') == 'all_terminal' and state[d]['status'] == 'SKIPPED') for d in deps)
                if permitted:
                    ready.append(stage_id)
                else:
                    blocked.append(stage_id)
        return {'ready': ready, 'skipped': skipped, 'blocked': blocked}

    def _build_stage(self, stage_num: int, skill: str, all_skills: List[str]) -> dict:
        """Xây dựng 1 stage trong pipeline."""
        skill_data = self.db.get("skills", {}).get(skill, {})

        # Estimate sub-steps based on skill complexity
        sub_steps = {
            "SKILL_GEOTECH": 4,
            "Structural_Design_Engineer": 3,
            "Design_Evaluation": 3,
            "SKILL_FORENSIC": 4,
            "Cost_Estimator": 2,
            "SKILL_VERIFY": 2,
            "Technical_Illustrator": 1,
            "SKILL_PHULUC": 3,
            "SKILL_RFI": 2,
        }

        return {
            "stage": stage_num,
            "skill": skill,
            "skill_id": skill_data.get("skill_id", ""),
            "display_name": skill_data.get("display_name", skill),
            "entry_points": skill_data.get("entry_points", []),
            "is_placeholder": skill_data.get("is_placeholder", False),
            "estimated_sub_steps": sub_steps.get(skill, 1),
            "depends_on": [stage_num - 1] if stage_num > 1 else [],
            "requires_review_gate": skill in REVIEW_GATE_SKILLS,
            "auto_trigger": self._get_auto_triggers(skill, all_skills)
        }

    def _get_auto_triggers(self, skill: str, all_skills: List[str]) -> List[str]:
        """Lấy danh sách trigger tự động cho skill."""
        trigger_map = {
            "Structural_Design_Engineer": ["POST-SDE-001", "POST-SDE-002"],
            "Design_Evaluation": ["POST-EVAL-01", "POST-EVAL-02", "POST-DEV-001"],
            "SKILL_GEOTECH": ["POST-GEOTECH-01", "POST-GEOTECH-02", "POST-GEOTECH-03"],
        }
        return trigger_map.get(skill, [])

    def _detect_parallel(self, skills: List[str]) -> List[dict]:
        """Phát hiện cơ hội chạy song song."""
        parallel = []
        for group_name, group_skills in PARALLEL_GROUPS.items():
            matching = [s for s in skills if s in group_skills]
            if len(matching) >= 2:
                parallel.append({
                    "group": group_name,
                    "skills": matching,
                    "note": "Có thể chạy song song để tăng tốc"
                })
        return parallel

    def _build_instructions(self, skills: List[str], review_gates: List[dict]) -> str:
        """Tạo hướng dẫn thực thi pipeline."""
        lines = ["## Hướng dẫn thực thi Pipeline\n"]

        for i, skill in enumerate(skills, 1):
            lines.append(f"### Stage {i}: {skill}")
            lines.append(f"1. Đọc `SKILL.md` của **{skill}**")
            lines.append(f"2. Thực thi theo entry point")
            lines.append(f"3. Thu thập output JSON")

            # Check review gate
            gate = next((g for g in review_gates if g["after_stage"] == i), None)
            if gate:
                lines.append(f"4. ⚠️ **REVIEW GATE** — Trình bày kết quả và chờ User duyệt")

            if i < len(skills):
                lines.append(f"5. Tạo handoff JSON → chuyển sang Stage {i + 1}")
            lines.append("")

        return "\n".join(lines)


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Pipeline Builder — Xây dựng pipeline thực thi multi-skill",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ví dụ:
  python pipeline_builder.py --skills "Structural_Design_Engineer,Design_Evaluation"
  python pipeline_builder.py --template "design_then_review"
  python pipeline_builder.py --list-templates
        """
    )
    parser.add_argument("--prompt", type=str, help="Plan a conditional DAG from a multi-step request")
    parser.add_argument("--skills", type=str, help="Danh sách skill cách nhau bởi dấu phẩy")
    parser.add_argument("--template", type=str, help="Tên template pipeline")
    parser.add_argument("--context", type=str, default="", help="Mô tả bối cảnh")
    parser.add_argument("--list-templates", action="store_true", help="Liệt kê tất cả templates")
    parser.add_argument("--verbose", action="store_true", help="Hiển thị chi tiết")
    parser.add_argument("--db", type=str, default=None, help="Đường dẫn keyword_database.json")

    args = parser.parse_args()

    builder = PipelineBuilder(db_path=args.db)

    if args.list_templates:
        print(json.dumps({
            "templates": {
                name: {
                    "skills": t["skills"],
                    "description": t["description"]
                }
                for name, t in builder.templates.items()
            }
        }, ensure_ascii=False, indent=2))
        return

    if args.prompt:
        result = builder.plan(args.prompt)
    elif args.template:
        result = builder.build_from_template(args.template)
    elif args.skills:
        skill_list = [s.strip() for s in args.skills.split(",")]
        result = builder.build(skill_list, context=args.context)
    else:
        parser.print_help()
        sys.exit(1)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
