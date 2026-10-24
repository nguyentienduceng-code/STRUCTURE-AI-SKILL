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

    def __init__(self, db_path: str = None):
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
        sorted_skills = sorted(valid_skills, key=lambda s: EXECUTION_ORDER.get(s, 99))

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

    if args.template:
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
