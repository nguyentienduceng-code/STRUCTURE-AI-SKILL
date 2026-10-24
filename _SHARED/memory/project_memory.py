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
        # Atomic replace: tránh file hỏng nếu tiến trình bị ngắt giữa chừng.
        tmp_file = filepath.with_suffix(filepath.suffix + ".tmp")
        with open(tmp_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        tmp_file.replace(filepath)
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


# ==============================================================================
# KÝ ỨC TIẾN HÓA LIÊN DỰ ÁN (CROSS-PROJECT LESSONS LEARNED - MEM0 STYLE)
# ==============================================================================

@dataclass
class LessonLearned:
    lesson_id: str
    project_code: str
    category: str  # "BEAM", "COLUMN", "SLAB", "FOUNDATION", "SEISMIC", "CLIENT_PREF", "CONSTRUCTION"
    issue_description: str
    root_cause: str
    preventive_solution: str
    related_standards: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class LessonsLearnedRepository:
    """
    Kho ký ức kinh nghiệm liên dự án.
    Giúp AI học hỏi từ các sự cố, sai sót và thói quen phê duyệt của Chủ đầu tư qua 15 dự án.
    """
    def __init__(self, storage_dir: Optional[Path] = None, seed: bool = True):
        self.storage_dir = Path(storage_dir) if storage_dir else (Path(__file__).resolve().parent / "projects")
        self.storage_file = self.storage_dir / "global_lessons_learned.json"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        if seed:
            self._seed_default_lessons()

    def _load_data(self) -> List[Dict]:
        if not self.storage_file.exists():
            return []
        try:
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []

    def _save_data(self, data: List[Dict]):
        # Ghi tạm rồi thay thế (atomic replace) để không để lại file hỏng nếu bị ngắt giữa chừng.
        tmp_file = self.storage_file.with_suffix(self.storage_file.suffix + ".tmp")
        with open(tmp_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        tmp_file.replace(self.storage_file)

    def add_lesson(self, lesson: LessonLearned):
        data = self._load_data()
        # Tránh trùng lặp ID
        data = [item for item in data if item.get("lesson_id") != lesson.lesson_id]
        data.append(asdict(lesson))
        self._save_data(data)

    def find_lessons(self, category: Optional[str] = None, tags: Optional[List[str]] = None, keyword: Optional[str] = None) -> List[LessonLearned]:
        """Truy vấn bài học kinh nghiệm theo danh mục, thẻ tag hoặc từ khóa."""
        data = self._load_data()
        results = []
        for item in data:
            match = True
            if category and item.get("category", "").upper() != category.upper():
                match = False
            if tags and match:
                item_tags = [t.lower() for t in item.get("tags", [])]
                if not any(t.lower() in item_tags for t in tags):
                    match = False
            if keyword and match:
                kw = keyword.lower()
                text_blob = f"{item.get('issue_description', '')} {item.get('root_cause', '')} {item.get('preventive_solution', '')}".lower()
                if kw not in text_blob:
                    match = False
            if match:
                results.append(LessonLearned(**item))
        return results

    def _seed_default_lessons(self):
        """Khởi tạo bài học thực tế từ các đồ án tiêu biểu."""
        if self.storage_file.exists():
            return
        default_lessons = [
            LessonLearned(
                lesson_id="LL-PRIME-01",
                project_code="Prime_Diamond",
                category="BEAM",
                issue_description="Xuất hiện vết nứt nhiệt và co ngót ở dầm chuyển tầng 4",
                root_cause="Chiều cao dầm h=1.8m khối lớn nhưng thiếu thép cấu tạo chống nứt mặt bên và bảo dưỡng nhiệt",
                preventive_solution="Bố trí thép cấu tạo mặt bên phi 14a150 kèm bảo dưỡng ẩm phủ bao bố liên tục 14 ngày",
                related_standards=["TCVN 5574:2018"],
                tags=["dam_chuyen", "nut_be_tong", "nhiet_khoi_lon"]
            ),
            LessonLearned(
                lesson_id="LL-SS1-01",
                project_code="SS1",
                category="CLIENT_PREF",
                issue_description="Chủ đầu tư từ chối nghiệm thu bản vẽ dầm có hàm lượng thép mu > 2.0%",
                root_cause="Chủ đầu tư yêu cầu khống chế hàm lượng thép dầm để tối ưu chi phí và tránh khó khăn khi đổ bê tông",
                preventive_solution="Tăng tiết diện dầm từ 300x600 lên 350x650 để đưa mu về khoảng tối ưu 1.2% - 1.6%",
                related_standards=["TCVN 5574:2018"],
                tags=["ham_luong_thep", "chu_dau_tu", "toi_uu_boq"]
            ),
            LessonLearned(
                lesson_id="LL-MONTALP-01",
                project_code="MONTALP",
                category="CONSTRUCTION",
                issue_description="Bị Tư vấn giám sát lập biên bản NCR do chiều dày lớp bê tông bảo vệ cọc/móng không đạt 50mm",
                root_cause="Dùng con kê nhựa mỏng 25mm không đúng quy định móng tiếp xúc đất",
                preventive_solution="Quy định bắt buộc dùng con kê bê tông mác cao c_nom >= 50mm cho toàn bộ cấu kiện móng",
                related_standards=["TCVN 5574:2018", "TCVN 9346:2012"],
                tags=["lop_bao_ve", "mong_coc", "ncr"]
            )
        ]
        self._save_data([asdict(l) for l in default_lessons])

