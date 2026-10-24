"""
project_memory.py — Project Context Memory Layer

Lưu trữ context của dự án giữa các session để:
- Nhớ các quyết định thiết kế đã duyệt
- Nhớ standards đã sử dụng
- Nhớ các vấn đề/thay đổi đã xử lý

Usage:
    from project_memory import ProjectMemory
    memory = ProjectMemory("DUAN_A")
    memory.save_context({"standards_used": ["TCVN 2737:2023"]})
"""

import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict

# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class DesignDecision:
    """Quyết định thiết kế đã duyệt"""
    decision_id: str
    date: str
    description: str
    approved_by: str
    rationale: str
    related_standards: List[str] = field(default_factory=list)
    related_elements: List[str] = field(default_factory=list)
    notes: Optional[str] = None

@dataclass
class ProjectContext:
    """Context của dự án"""
    project_code: str
    project_name: str
    created_date: str
    last_modified: str
    stage: str  # TKCS, TKKT, BVTC, Hoan cong
    standards_used: List[str] = field(default_factory=list)
    decisions: List[DesignDecision] = field(default_factory=list)
    issues_log: List[Dict] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

# =============================================================================
# PROJECT MEMORY CLASS
# =============================================================================

class ProjectMemory:
    """
    Memory layer cho project context.
    Lưu trữ trong thư mục: .agents/skills/shared/memory/projects/{project_code}/
    """

    def __init__(self, project_code: str, memory_dir: Optional[str] = None):
        self.project_code = project_code

        if memory_dir:
            self.memory_dir = Path(memory_dir)
        else:
            # Default: shared/memory/projects/
            current = Path(__file__).parent.parent.parent
            self.memory_dir = current / "shared" / "memory" / "projects"

        self.project_dir = self.memory_dir / project_code
        self.context_file = self.project_dir / "context.json"
        self.decisions_file = self.project_dir / "decisions.json"
        self.issues_file = self.project_dir / "issues.json"

        # Ensure directory exists
        self.project_dir.mkdir(parents=True, exist_ok=True)

    def _load_json(self, filepath: Path) -> Any:
        """Load JSON file, return None if not exists"""
        if not filepath.exists():
            return None
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None

    def _save_json(self, filepath: Path, data: Any):
        """Save data to JSON file"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)

    def get_context(self) -> Optional[ProjectContext]:
        """Lấy context của dự án"""
        data = self._load_json(self.context_file)
        if not data:
            return None
        return ProjectContext(**data)

    def save_context(self, context: ProjectContext):
        """Lưu context của dự án"""
        data = asdict(context)
        data['last_modified'] = datetime.now().isoformat()
        self._save_json(self.context_file, data)

    def create_context(self, project_name: str, stage: str = "TKCS"):
        """Tạo context mới cho dự án"""
        context = ProjectContext(
            project_code=self.project_code,
            project_name=project_name,
            created_date=datetime.now().isoformat(),
            last_modified=datetime.now().isoformat(),
            stage=stage
        )
        self.save_context(context)
        return context

    def add_decision(self, decision: DesignDecision):
        """Thêm quyết định thiết kế"""
        decisions = self._load_json(self.decisions_file) or []
        decisions.append(asdict(decision))
        self._save_json(self.decisions_file, decisions)

    def get_decisions(self) -> List[DesignDecision]:
        """Lấy danh sách quyết định"""
        data = self._load_json(self.decisions_file)
        if not data:
            return []
        return [DesignDecision(**d) for d in data]

    def add_issue(self, issue: Dict):
        """Thêm issue vào log"""
        issues = self._load_json(self.issues_file) or []
        issue['logged_at'] = datetime.now().isoformat()
        issues.append(issue)
        self._save_json(self.issues_file, issues)

    def get_issues(self) -> List[Dict]:
        """Lấy danh sách issues"""
        return self._load_json(self.issues_file) or []

    def add_standard(self, standard: str):
        """Thêm tiêu chuẩn đã sử dụng"""
        context = self.get_context()
        if not context:
            return
        if standard not in context.standards_used:
            context.standards_used.append(standard)
            self.save_context(context)

    def list_projects(self) -> List[str]:
        """Liệt kê tất cả dự án đã lưu"""
        if not self.memory_dir.exists():
            return []
        return [d.name for d in self.memory_dir.iterdir() if d.is_dir()]

# =============================================================================
# CLI INTERFACE
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Project Memory CLI")
    parser.add_argument("--project", required=True, help="Project code")
    parser.add_argument("--action", choices=["create", "list", "show", "add-decision"],
                        required=True, help="Action to perform")
    parser.add_argument("--name", help="Project name (for create)")
    parser.add_argument("--stage", default="TKCS", help="Stage (for create)")
    parser.add_argument("--description", help="Decision description (for add-decision)")

    args = parser.parse_args()

    memory = ProjectMemory(args.project)

    if args.action == "create":
        if not args.name:
            print("Error: --name required for create")
            return
        ctx = memory.create_context(args.name, args.stage)
        print(f"Created context for {ctx.project_name} ({ctx.project_code})")
        print(f"Stage: {ctx.stage}")

    elif args.action == "list":
        projects = memory.list_projects()
        print(f"Projects: {len(projects)}")
        for p in projects:
            print(f"  - {p}")

    elif args.action == "show":
        ctx = memory.get_context()
        if not ctx:
            print(f"No context found for {args.project}")
            return
        print(f"Project: {ctx.project_name}")
        print(f"Code: {ctx.project_code}")
        print(f"Stage: {ctx.stage}")
        print(f"Standards: {', '.join(ctx.standards_used)}")
        print(f"Decisions: {len(ctx.decisions)}")
        print(f"Issues: {len(ctx.issues_log)}")

    elif args.action == "add-decision":
        if not args.description:
            print("Error: --description required for add-decision")
            return
        decision = DesignDecision(
            decision_id=f"DEC-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            date=datetime.now().isoformat(),
            description=args.description,
            approved_by="Kỹ sư trưởng"
        )
        memory.add_decision(decision)
        print(f"Added decision: {decision.decision_id}")

if __name__ == "__main__":
    main()
