# -*- coding: utf-8 -*-
"""
lessons_lookup.py — Tiện ích truy vấn bài học kinh nghiệm liên dự án.

Module dùng chung cho các Skill (Design_Evaluation, SKILL_VERIFY,
SKILL_RFI, ...) cần nhúng cảnh báo "đã gặp sự cố tương tự" vào báo cáo.

Dựa trên LessonsLearnedRepository trong project_memory.py.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Thêm .agents/_SHARED/memory vào sys.path (để import project_memory)
_THIS_DIR = Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

from project_memory import LessonLearned, LessonsLearnedRepository  # noqa: E402

_DEFAULT_REPO: Optional[LessonsLearnedRepository] = None


def _get_repo() -> Optional[LessonsLearnedRepository]:
    """Lấy repository singleton; trả None nếu lỗi (fail-safe)."""
    global _DEFAULT_REPO
    if _DEFAULT_REPO is not None:
        return _DEFAULT_REPO
    try:
        _DEFAULT_REPO = LessonsLearnedRepository()
    except Exception:
        _DEFAULT_REPO = None
    return _DEFAULT_REPO


def _extract_standard_ids(text: str) -> List[str]:
    """Trích các mã tiêu chuẩn (TCVN ..., ASTM ...) từ chuỗi."""
    if not text:
        return []
    matches = re.findall(r"TCVN\s*\d{4,5}:\d{4}(?::\d{4})?", text)
    return [m.replace(" ", "").upper() for m in matches]


def _lesson_matches(
    lesson: LessonLearned,
    project_code: Optional[str],
    standards: List[str],
    keywords: List[str],
) -> bool:
    """
    Một lesson khớp nếu:
    - Cùng project_code (nếu project_code khác None), HOẶC
    - Bật kỳ liên quan: tiêu chuẩn lesson chứa 1 trong standards, HOẶC
    - Từ khóa lesson khớp 1 trong keywords (issue/root_cause/preventive_solution/tags).
    """
    if project_code:
        if lesson.project_code == project_code:
            return True

    lesson_stds = [s.replace(" ", "").upper() for s in (lesson.related_standards or [])]
    if any(s in lesson_stds for s in standards):
        return True

    if keywords:
        blob = " ".join([
            lesson.issue_description or "",
            lesson.root_cause or "",
            lesson.preventive_solution or "",
            " ".join(lesson.tags or []),
        ]).lower()
        for kw in keywords:
            if kw and kw.lower() in blob:
                return True
    return False


def find_relevant_lessons(
    project_code: Optional[str] = None,
    standards_text: Optional[str] = None,
    keyword_text: Optional[str] = None,
    extra_keywords: Optional[List[str]] = None,
    limit: int = 5,
) -> List[Dict[str, Any]]:
    """
    Tìm các bài học kinh nghiệm liên quan đến ngữ cảnh báo cáo hiện tại.

    Args:
        project_code: Mã dự án. Nếu không None, ưu tiên bài học cùng dự án.
        standards_text: Chuỗi chứa tiêu chuẩn (vd "TCVN 5574:2018, TCVN 5575:2024").
                        Dùng để khớp lesson.related_standards.
        keyword_text:   Chuỗi nội dung hạng mục (vd "khung thép nhà xưởng").
                        Tự động token hoá để tìm khớp trong issue/cause/solution/tags.
        extra_keywords: Danh sách từ khoá bổ sung.
        limit: Số lesson tối đa trả về (default 5).

    Returns:
        List dict: [{lesson_id, project_code, category, issue, root_cause,
                     solution, related_standards, tags}]
    """
    repo = _get_repo()
    if repo is None:
        return []

    standards = _extract_standard_ids(standards_text or "")
    keywords: List[str] = []
    if keyword_text:
        # Token hoá đơn giản: min 3 chữ cái, bỏ stopwords cơ bản
        tokens = re.findall(r"[a-zđà-ỹ]{3,}", keyword_text.lower())
        stop = {"của", "với", "đến", "cho", "nhỏ", "lớn", "kết", "cấu"}
        keywords = [t for t in tokens if t not in stop]
    if extra_keywords:
        keywords.extend(extra_keywords)

    lessons = repo.find_lessons()  # lấy toàn bộ (bộ nhỏ, <100 entries)
    matched = [
        l for l in lessons
        if _lesson_matches(l, project_code, standards, keywords)
    ]

    # Ưu tiên lesson cùng project_code trước, sau đó theo số từ khoá khớp
    def _score(lesson: LessonLearned) -> int:
        s = 0
        if project_code and lesson.project_code == project_code:
            s += 100
        blob = " ".join([
            lesson.issue_description or "",
            lesson.root_cause or "",
            lesson.preventive_solution or "",
            " ".join(lesson.tags or []),
        ]).lower()
        s += sum(1 for kw in keywords if kw and kw.lower() in blob)
        return s

    matched.sort(key=_score, reverse=True)
    matched = matched[:max(0, limit)]

    return [
        {
            "lesson_id": l.lesson_id,
            "project_code": l.project_code,
            "category": l.category,
            "issue": l.issue_description,
            "root_cause": l.root_cause,
            "solution": l.preventive_solution,
            "related_standards": l.related_standards,
            "tags": l.tags,
        }
        for l in matched
    ]


def format_lessons_markdown(lessons: List[Dict[str, Any]], section_title: str = "Kinh nghiệm liên dự án") -> List[str]:
    """
    Render lessons thành chuỗi Markdown (list-of-lines), dùng được cho báo cáo.

    Trả về [] nếu không có lesson.
    """
    if not lessons:
        return []

    lines: List[str] = [f"## {section_title}", ""]
    lines.append(f"*{len(lessons)} bài học có liên quan đến ngữ cảnh hiện tại — kiểm tra trước khi áp dụng.*")
    lines.append("")
    for item in lessons:
        lines.append(f"### {item.get('lesson_id', '?')} — {item.get('category', '')}")
        lines.append(f"- **Dự án nguồn:** {item.get('project_code', '—')}")
        lines.append(f"- **Sự cố:** {item.get('issue', '')}")
        lines.append(f"- **Nguyên nhân:** {item.get('root_cause', '')}")
        lines.append(f"- **Giải pháp dự phòng:** {item.get('solution', '')}")
        if item.get("related_standards"):
            lines.append(f"- **Tiêu chuẩn liên quan:** {', '.join(item['related_standards'])}")
        lines.append("")
    return lines


def format_lessons_docx(lessons: List[Dict[str, Any]]) -> List[List[Any]]:
    """
    Cấu trúc lessons thành list-of-paragraphs cho python-docx (mỗi item là 1 dict
    {"text": str, "bold": bool, "size": int, "style": str}).
    """
    if not lessons:
        return []

    out: List[Dict[str, Any]] = []
    out.append({"text": "Kinh nghiệm liên dự án", "level": 1})
    out.append({"text": f"{len(lessons)} bài học có liên quan — kiểm tra trước khi áp dụng.", "italic": True})
    for item in lessons:
        out.append({"text": f"{item.get('lesson_id', '?')} — {item.get('category', '')}", "level": 2})
        out.append({"text": f"Dự án nguồn: {item.get('project_code', '—')}"})
        out.append({"text": f"Sự cố: {item.get('issue', '')}"})
        out.append({"text": f"Nguyên nhân: {item.get('root_cause', '')}"})
        out.append({"text": f"Giải pháp dự phòng: {item.get('solution', '')}"})
    return out


if __name__ == '__main__':
    # Self-test nhanh
    results = find_relevant_lessons(
        project_code=None,
        standards_text="TCVN 5574:2018, TCVN 5575:2024",
        keyword_text="dầm bê tông cốt thép chịu lực",
        limit=3,
    )
    print(json.dumps(results, ensure_ascii=False, indent=2))
