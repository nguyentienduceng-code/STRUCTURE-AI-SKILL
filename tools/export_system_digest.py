# .agents/tools/export_system_digest.py
import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

import os, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "_SHARED" / "SYSTEM_DIGEST.json"


def export_system_digest(root: Path = ROOT) -> dict:
    digest = {
        "skills": {},
        "calculators": [],
        "schemas": []
    }

    # 1. Quét danh mục SKILL.md
    skills_dir = root / "skills"
    if skills_dir.exists():
        for skill_path in sorted(skills_dir.iterdir()):
            if skill_path.is_dir() and (skill_path / "SKILL.md").exists():
                skill_md = (skill_path / "SKILL.md").read_text(encoding="utf-8", errors="ignore")
                # Cắt lấy 60 dòng đầu (chứa frontmatter, vai trò, inputs, outputs)
                head_lines = "\n".join(skill_md.splitlines()[:60])
                digest["skills"][skill_path.name] = head_lines

    # 2. Liệt kê danh sách calculators và CLI tools
    for p in sorted(root.rglob("*.py")):
        if ".git" in p.parts:
            continue
        rel = str(p.relative_to(root)).replace("\\", "/")
        if "calculators" in rel or "scripts" in rel:
            digest["calculators"].append(rel)

    # 3. Liệt kê danh sách schemas
    for p in sorted(root.rglob("*.json")):
        if ".git" in p.parts:
            continue
        rel = str(p.relative_to(root)).replace("\\", "/")
        if "schemas" in rel or rel.endswith(".schema.json"):
            digest["schemas"].append(rel)

    out_file = root / "_SHARED" / "SYSTEM_DIGEST.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(digest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Đã xuất digest thành công: {out_file}")
    return digest


if __name__ == "__main__":
    export_system_digest()

