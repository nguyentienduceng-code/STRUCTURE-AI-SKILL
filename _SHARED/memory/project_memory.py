"""
project_memory.py v2.0 — Project Context Memory Layer
"""
import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict

@dataclass
class DesignDecision:
    decision_id: str
    date: str
    description: str
    approved_by: str
    rationale: str = "Theo quyết định kỹ thuật"
    related_standards: List[str] = field(default_factory=list)
    related_elements: List[str] = field(default_factory=list)
    notes: Optional[str] = None

@dataclass
class ProjectContext:
    project_code: str
    project_name: str
    created_date: str
    last_modified: str
    stage: str
    standards_used: List[str] = field(default_factory=list)
    decisions: List[DesignDecision] = field(default_factory=list)
    issues_log: List[Dict] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

class ProjectMemory:
    def __init__(self, project_code: str, memory_dir: Optional[str] = None):
        self.project_code = project_code
        self.memory_dir = Path(memory_dir) if memory_dir else (Path(__file__).resolve().parent / "projects")
        self.project_dir = self.memory_dir / project_code
        self.context_file = self.project_dir / "context.json"
        self.decisions_file = self.project_dir / "decisions.json"
        self.issues_file = self.project_dir / "issues.json"
        self.project_dir.mkdir(parents=True, exist_ok=True)
    def _load_json(self, filepath: Path) -> Any:
        if not filepath.exists():
            return None
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None
    def _save_json(self, filepath: Path, data: Any):
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    def get_context(self) -> Optional[ProjectContext]:
        data = self._load_json(self.context_file)
        if not data:
            return None
        if "decisions" in data and isinstance(data["decisions"], list):
            data["decisions"] = [DesignDecision(**d) if isinstance(d, dict) else d for d in data["decisions"]]
        return ProjectContext(**data)
    def save_context(self, context: ProjectContext):
        data = asdict(context)
        data['last_modified'] = datetime.now().isoformat()
        self._save_json(self.context_file, data)
    def create_context(self, project_name: str, stage: str = "TKCS"):
        context = ProjectContext(project_code=self.project_code, project_name=project_name, created_date=datetime.now().isoformat(), last_modified=datetime.now().isoformat(), stage=stage)
        self.save_context(context)
        return context
    def add_decision(self, decision: DesignDecision):
        decisions = self._load_json(self.decisions_file) or []
        decisions.append(asdict(decision))
        self._save_json(self.decisions_file, decisions)
    def get_decisions(self) -> List[DesignDecision]:
        data = self._load_json(self.decisions_file)
        if not data:
            return []
        return [DesignDecision(**d) for d in data]
    def add_issue(self, issue: Dict):
        issues = self._load_json(self.issues_file) or []
        issue['logged_at'] = datetime.now().isoformat()
        issues.append(issue)
        self._save_json(self.issues_file, issues)
    def get_issues(self) -> List[Dict]:
        return self._load_json(self.issues_file) or []
    def add_standard(self, standard: str):
        context = self.get_context()
        if not context:
            return
        if standard not in context.standards_used:
            context.standards_used.append(standard)
            self.save_context(context)
    def list_projects(self) -> List[str]:
        if not self.memory_dir.exists():
            return []
        return [d.name for d in self.memory_dir.iterdir() if d.is_dir()]
