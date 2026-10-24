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
    # Chuẩn hóa line endings: CRLF → LF
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Tách block frontmatter giữa 2 dấu ---
    # File thực tế bắt đầu bằng "---\n" và kết thúc block bằng "\n---\n"
    if not text.startswith("---"):
        return {}
    # Bỏ dòng đầu "---\n"
    after_open = text[4:]
    # Tìm dòng "---" đóng
    parts = after_open.split("\n---\n", 1)
    if len(parts) < 2:
        return []
    block = parts[0]
    result: dict = {}
    current_key: Optional[str] = None
    current_lines: list = []
    for raw_line in block.splitlines():
        # Bỏ qua comment và dòng rỗng đứng một mình
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", raw_line)
        if m:
            # Flush key cũ
            if current_key is not None:
                result[current_key] = "\n".join(current_lines).strip()
            current_key = m.group(1)
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


def collect_skills(skills_root: Path) -> list[Skill]:
    """Walk skills_root, parse mỗi SKILL.md, trả về list[Skill] đã sắp xếp theo tên."""
    if not skills_root.exists():
        return []
    skills: list[Skill] = []
    for entry in sorted(skills_root.iterdir()):
        if not entry.is_dir():
            continue
        skill_md = entry / "SKILL.md"
        if not skill_md.exists():
            continue
        try:
            text = skill_md.read_text(encoding="utf-8", errors="replace")
            fm = _parse_frontmatter(text)
            name = fm.get("name", entry.name)
            # Validate: phải có key version trong frontmatter (không được default)
            if "version" not in fm:
                raise SkillFrontmatterError(
                    f"missing 'version' trong frontmatter của {skill_md}"
                )
            version = fm["version"]
            last_updated = fm.get("last_updated", "unknown")
            description = fm.get("description", "")
            # Validate: name phải khớp thư mục
            if name != entry.name:
                raise SkillFrontmatterError(
                    f"name '{name}' != folder '{entry.name}' in {skill_md}"
                )
            if not re.match(r"^\d+\.\d+\.\d+$", version):
                raise SkillFrontmatterError(
                    f"version '{version}' không đúng định dạng X.Y.Z in {skill_md}"
                )
            skills.append(
                Skill(
                    name=name,
                    version=version,
                    last_updated=last_updated,
                    description=description,
                    path=skill_md,
                    status=_classify_status(version),
                )
            )
        except SkillFrontmatterError as e:
            # Ghi nhận lỗi nhưng không crash; caller sẽ xử lý warning
            raise
        except Exception as e:
            raise SkillFrontmatterError(f"Lỗi đọc {skill_md}: {e}") from e
    return skills


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
