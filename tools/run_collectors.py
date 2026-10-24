# .agents/tools/run_collectors.py
# Runner tập trung thu thập toàn bộ metrics từ các script _collect_*.py
# Xuất kết quả ra memory/COLLECTED_METRICS.json và snapshot compact

from __future__ import annotations

import json
import sys
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

# Đảm bảo UTF-8 theo Quy tắc AGENTS.md
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Tìm workspace root và agents root
TOOLS_DIR = Path(__file__).resolve().parent
AGENTS_ROOT = TOOLS_DIR.parent
WORKSPACE_ROOT = AGENTS_ROOT.parent

# Import các collector
from _collect_calculators import collect_calculators
from _collect_changelog import collect_latest_changelog
from _collect_keyword_db import collect_keyword_db_stats
from _collect_skills import collect_skills_summary
from _collect_standards import collect_standards


def run_all_collectors() -> dict:
    skills_root = AGENTS_ROOT / "skills"
    lock_path = skills_root / "STANDARDS_LOCK.md"
    changelog_path = skills_root / "CHANGELOG.md"
    keyword_db_path = skills_root / "Global_Dispatcher" / "scripts" / "keyword_database.json"

    print("[COLLECTOR] 1. Thu thập thông tin skills...")
    skills_data = collect_skills_summary(skills_root)

    print("[COLLECTOR] 2. Thu thập tiêu chuẩn từ STANDARDS_LOCK.md...")
    standards_raw = collect_standards(lock_path)
    standards_data = [asdict(s) for s in standards_raw]

    print("[COLLECTOR] 3. Thu thập entry mới nhất từ CHANGELOG.md...")
    changelog_latest = asdict(collect_latest_changelog(changelog_path))

    print("[COLLECTOR] 4. Thu thập số liệu Keyword Database...")
    keyword_stats = asdict(collect_keyword_db_stats(keyword_db_path))

    print("[COLLECTOR] 5. Thu thập danh mục Calculator Scripts...")
    calc_inv = collect_calculators(skills_root)
    calculators_data = {
        "total_count": calc_inv.total_count,
        "skill_count_with_calculators": calc_inv.skill_count_with_calculators,
        "by_skill": calc_inv.by_skill
    }

    metrics = {
        "timestamp": datetime.now().astimezone().isoformat(),
        "skills_summary": skills_data,
        "standards": {
            "total_standards_locked": len(standards_data),
            "items": standards_data
        },
        "changelog_latest": changelog_latest,
        "keyword_database": keyword_stats,
        "calculators": calculators_data
    }

    # 1. Ghi memory/COLLECTED_METRICS.json
    metrics_file = WORKSPACE_ROOT / "memory" / "COLLECTED_METRICS.json"
    metrics_file.parent.mkdir(parents=True, exist_ok=True)
    metrics_file.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[COLLECTOR] ✅ Đã lưu dữ liệu đầy đủ tại: {metrics_file}")

    # 2. Tạo snapshot siêu nhẹ (< 3KB) cho Claude tại scratch/repo_digest.json và SYSTEM_SNAPSHOT.json
    digest = {
        "version": changelog_latest.get("version", "v6.4"),
        "timestamp": metrics["timestamp"],
        "skills_count": skills_data["total"],
        "production_skills": skills_data["production"],
        "placeholder_skills": skills_data["placeholder"],
        "calculators_total": calc_inv.total_count,
        "standards_locked": len(standards_data),
        "primary_keywords": keyword_stats.get("actual_primary_keyword_count", 0),
        "regex_patterns": keyword_stats.get("actual_regex_count", 0),
        "skill_names": [s["name"] for s in skills_data["skills"]]
    }

    snapshot_file1 = AGENTS_ROOT / "_SHARED" / "SHARED_CONTEXT" / "_active" / "SYSTEM_SNAPSHOT.json"
    snapshot_file1.parent.mkdir(parents=True, exist_ok=True)
    snapshot_file1.write_text(json.dumps(digest, ensure_ascii=False, indent=2), encoding="utf-8")

    digest_file2 = WORKSPACE_ROOT / "scratch" / "repo_digest.json"
    digest_file2.parent.mkdir(parents=True, exist_ok=True)
    digest_file2.write_text(json.dumps(digest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[COLLECTOR] ✅ Đã tạo System Snapshot tại: {snapshot_file1} & {digest_file2}")

    return metrics


if __name__ == "__main__":
    run_all_collectors()
