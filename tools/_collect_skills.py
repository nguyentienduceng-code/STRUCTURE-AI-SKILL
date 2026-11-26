# tools/_collect_skills.py
# Bộ thu thập: Walk SKILLS_ROOT, parse YAML frontmatter của mỗi SKILL.md,
# trả về danh sách Skill + thống kê tổng hợp.

from __future__ import annotations

import re
import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class Skill:
    """Một skill trong hệ sinh thái .agents/."""

    name: str
    version: str
    last_updated: str
    description: str
    path: Path
    status: str  # "production" (>= 1.0.0) hoặc "placeholder" (bắt đầu "0.")


class SkillFrontmatterError(Exception):
    """Lỗi khi parse frontmatter SKILL.md (sai format)."""


def _parse_frontmatter(text: str) -> dict:
    """Parse YAML frontmatter đơn giản (zero-dependency).

    Hỗ trợ: key: value (1 dòng), key: "value có dấu" (quoted),
    key: value\n  continuation (multi-line indented).
    Không hỗ trợ: list dạng YAML block, nested objects.

    File có thể dùng CRLF (Windows); chuẩn hóa về LF trước khi parse.
    """
    lines = text.removeprefix("\ufeff").splitlines()
    if not lines or lines[0].rstrip() != "---":
        raise SkillFrontmatterError("Missing opening frontmatter delimiter")
    for end in range(1, len(lines)):
        if lines[end].rstrip() == "---":
            break
    else:
        raise SkillFrontmatterError("Missing closing frontmatter delimiter")
    result: dict = {}
    current_key: Optional[str] = None
    current_lines: list = []
    for raw_line in lines[1:end]:
        # Bỏ qua comment và dòng rỗng đứng một mình
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", raw_line)
        if m:
            # Flush key cũ
            if current_key is not None:
                result[current_key] = "\n".join(current_lines).strip()
            current_key = m.group(1)
            if current_key in result:
                raise SkillFrontmatterError(f"Duplicate frontmatter key: {current_key}")
            value = m.group(2).strip()
            # Bỏ dấu nháy bao quanh nếu có
            if (value.startswith('"') and value.endswith('"')) or (
                value.startswith("'") and value.endswith("'")
            ):
                value = value[1:-1]
            current_lines = [value] if value else []
        else:
            # Dòng continuation (thường là description dài)
            if current_key is not None:
                current_lines.append(raw_line.strip())
    if current_key is not None:
        result[current_key] = "\n".join(current_lines).strip()
    return result


def _classify_status(version: str) -> str:
    """Phân loại skill: production nếu major >= 1, placeholder nếu major == 0."""
    m = re.match(r"^(\d+)\.\d+\.\d+$", version)
    if not m:
        return "unknown"
    major = int(m.group(1))
    return "production" if major >= 1 else "placeholder"


def read_skill(skill_md: Path) -> Skill:
    """Read and validate the metadata for one local skill."""
    try:
        text = skill_md.read_text(encoding="utf-8", errors="replace")
        fm = _parse_frontmatter(text)
        name = fm.get("name", skill_md.parent.name)
        # Validate: phải có key version trong frontmatter (không được default)
        if "version" not in fm:
            raise SkillFrontmatterError(
                f"missing 'version' trong frontmatter của {skill_md}"
            )
        version = fm["version"]
        last_updated = fm.get("last_updated") or fm.get("updated", "unknown")
        description = fm.get("description", "")
        alias = fm.get("alias", "")
        # Validate: name phải khớp thư mục (hoặc khớp qua alias chuẩn hóa)
        if name != skill_md.parent.name:
            if alias == skill_md.parent.name or name.lower().replace("-", "_") == skill_md.parent.name.lower().replace("-", "_"):
                name = skill_md.parent.name
            else:
                raise SkillFrontmatterError(
                    f"name '{name}' != folder '{skill_md.parent.name}' in {skill_md}"
                )
        if not re.match(r"^\d+\.\d+\.\d+$", version):
            raise SkillFrontmatterError(
                f"version '{version}' không đúng định dạng X.Y.Z in {skill_md}"
            )
        return Skill(
            name=name,
            version=version,
            last_updated=last_updated,
            description=description,
            path=skill_md,
            status=_classify_status(version),
        )
    except (OSError, UnicodeError, SkillFrontmatterError) as exc:
        raise SkillFrontmatterError(f"{skill_md}: {exc}") from exc


def collect_skills(skills_root: Path) -> list[Skill]:
    """Read skill entry points in stable directory order."""
    return [read_skill(path) for path in sorted(skills_root.glob("*/SKILL.md"))]



def collect_skills_summary(skills_root: Path) -> dict:
    """Tóm tắt số liệu skill: total, production, placeholder, danh sách version grid."""
    skills = collect_skills(skills_root)
    production = [s for s in skills if s.status == "production"]
    placeholder = [s for s in skills if s.status == "placeholder"]
    return {
        "total": len(skills),
        "production": len(production),
        "placeholder": len(placeholder),
        "skills": [
            {"name": s.name, "version": s.version, "last_updated": s.last_updated, "status": s.status}
            for s in skills
        ],
    }
