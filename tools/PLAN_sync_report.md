# Plan: `tools/sync_report.py` — Tự động đồng bộ báo cáo tổng hợp từ code

> **Trạng thái:** DRAFT — chờ user phê duyệt qua ExitPlanMode
> **Ngày lập:** 2026-10-17
> **Phạm vi:** Tạo tool tự động sinh lại file `docs/BAO_CAO_PHAT_TRIEN_DIEU_PHOI_AI.md` từ code/docs thực tế. Giải quyết vấn đề "báo cáo lạc hậu" mà v2.0 vừa chứng minh.

---

## Context

### Vấn đề

Báo cáo markdown `docs/BAO_CAO_PHAT_TRIEN_DIEU_PHOI_AI.md` được viết tay đã drift so với code thực tế:

- Báo cáo v2.0 (vừa viết) tự khẳng định "intent_classifier 15 test cases" nhưng `run_all_tests.py` mô tả là "17 tests"; source code có 17 `TEST_CASES` entries.
- Báo cáo nói "13/13 Calculators" nhưng `test_runner.py` có 16 case khai báo.
- Báo cáo nói "integration 67/67" nhưng `run_all_tests.py` SUITES label "67 checks" trong khi stdout body in `TESTS_PASSED` (cần chạy để biết số thật).
- Báo cáo liệt kê SKILL_PHULUC v1.0.0 nhưng frontmatter là v1.1.0.
- Báo cáo nói `requires_pre_approval` và `EntityExtractor` là "nhiệm vụ cần làm" nhưng đã có sẵn từ 2026-10-13.

Hệ quả: Mỗi lần agent khác (hoặc con người) đọc báo cáo, sẽ đề xuất làm lại những thứ đang tồn tại, hoặc tin vào con số sai.

### Kết quả mong muốn

Một tool `tools/sync_report.py` chạy được từ CLI, **overwrite** báo cáo hiện tại bằng dữ liệu verified-from-code, có khả năng **tự phát hiện stale-claims** trong báo cáo cũ trước khi ghi đè. Sau khi chạy:

- Không còn drift giữa báo cáo và code.
- Mỗi con số trong báo cáo đều có nguồn trích dẫn (đường dẫn file, regex pattern, hoặc tên biến).
- Có thể chạy trong CI để chặn commit khi báo cáo sai.

### Confirmed requirements (đã user chốt)

1. **Approach:** Sinh lại từ đầu (overwrite), không merge template.
2. **Test data source:** Chạy test suites thật qua subprocess, parse stdout, lấy số liệu real-time.
3. **Cấu trúc file:** 8 modules nhỏ + 1 CLI (đã chốt ở AskUserQuestion).
4. **Verify feature:** Regex pattern matching cho 10-12 claim types (đã chốt).

---

## Cấu trúc file

```
g:/My Drive/Google AI Studio/.agents/
├── tools/                                     # NEW
│   ├── __init__.py                            # empty
│   ├── sync_report.py                         # CLI entry, ~150 LOC
│   ├── _collect_skills.py                     # ~80 LOC
│   ├── _collect_tests.py                      # ~150 LOC
│   ├── _collect_keyword_db.py                 # ~60 LOC
│   ├── _collect_standards.py                  # ~80 LOC
│   ├── _collect_changelog.py                  # ~40 LOC
│   ├── _collect_calculators.py                # ~60 LOC
│   ├── _verify_claims.py                      # ~120 LOC
│   └── _render_markdown.py                    # ~200 LOC
└── tests/
    └── test_sync_report.py                    # NEW, 7 test cases
```

**Quy ước đặt tên:** Module private có tiền tố `_` để phân biệt với public CLI. `__init__.py` trống đánh dấu package.

---

## Module specifications

### 1. `tools/_collect_skills.py`

**Mục tiêu:** Walk `SKILLS_ROOT`, parse YAML frontmatter của mỗi `SKILL.md`, trả về danh sách skill + thống kê.

**Dataclass:**

```python
@dataclass(frozen=True)
class Skill:
    name: str
    version: str
    last_updated: str
    description: str
    path: Path
    status: str   # "production" nếu version >= 1.0.0; "placeholder" nếu bắt đầu bằng "0."
```

**Thuật toán parse frontmatter (zero-dependency, không cần PyYAML):**

1. `os.listdir(SKILLS_ROOT)` filter directories có `SKILL.md`.
2. Đọc file, split bằng chuỗi literal `\n---\n` lấy block giữa 2 dấu `---`.
3. Regex `r"^([A-Za-z_][\w-]*):\s*(.+?)\s*$"` với `re.MULTILINE` lấy `key: value`.
4. Với multi-line value (description dài), capture đến khi gặp key mới.
5. Validate: `name` phải khớp parent directory; `version` phải match `^\d+\.\d+\.\d+$`. Nếu sai → raise `SkillFrontmatterError` (catch ở CLI, ghi warning W003).

**Returns:** `collect_skills(skills_root) -> list[Skill]`, `collect_skills_summary(skills_root) -> dict` với `total`, `production`, `placeholder`.

### 2. `tools/_collect_tests.py`

**Mục tiêu:** Import `SUITES` từ `tests/run_all_tests.py` (không redefine), chạy từng suite, parse stdout, trả về `TestRunResult`.

**Quan trọng:** Import thay vì copy để nếu sau này thêm suite mới, sync_report tự động pick up.

**Dataclass:**

```python
@dataclass
class SuiteResult:
    name: str
    cmd: list[str]
    passed: bool
    elapsed_sec: float
    passed_count: int | None
    failed_count: int | None
    total_count: int | None
    raw_stdout_tail: str

@dataclass
class TestRunResult:
    suites: list[SuiteResult]
    all_passed: bool
    total_elapsed_sec: float
    grand_total_passed: int
    grand_total_failed: int
```

**Parser cho 6 suite (regex ASCII-keyword trong Vietnamese output):**

| Suite | Regex |
|---|---|
| `integration_test.py` | `PASSED:\s+(\d+)`, `FAILED:\s+(\d+)`, `TOTAL:\s+(\d+)` |
| `test_runner.py` | `SUMMARY:\s+(\d+)/(\d+)\s+PASSED\s+\\|\s+(\d+)\s+FAILED` |
| `test_approval_gate.py` | `Tests run:\s+(\d+)`, `Failures:\s+(\d+)` |
| `intent_classifier.py --test` | `RESULT:\s+(\d+)/(\d+)\s+passed` + JSON `passed/failed/total` fallback |
| `test_e2e_pipeline.py` | Count `✅ PASS` trong `Stage Results` (4 stages) |
| `DE/calculators/tests/run_tests.py` | `SUMMARY:\s+(\d+)\s+passed,\s+(\d+)\s+failed` |

**Timeout & fallback:** `subprocess.run(..., timeout=300)` mỗi suite. Nếu parse fail → `passed_count = None`, suite đó mark `⛔ UNPARSED` trong báo cáo. Toàn bộ run **không abort** dù 1 suite fail.

**Cache file:** Sau khi chạy, ghi JSON vào `_SHARED/SHARED_CONTEXT/_active/last_test_run.json` để `--skip-tests` dùng lại.

**Import pattern:**

```python
import importlib.util
spec = importlib.util.spec_from_file_location("run_all_tests", TESTS_DIR / "run_all_tests.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
SUITES = mod.SUITES
```

### 3. `tools/_collect_keyword_db.py`

**Đọc** `Global_Dispatcher/scripts/keyword_database.json`, trích:

```python
@dataclass
class KeywordDbStats:
    schema_version: str
    last_updated: str
    declared_total_keywords: int        # từ _meta.total_keywords
    actual_skill_count: int
    actual_primary_keyword_count: int
    actual_secondary_keyword_count: int
    actual_regex_count: int
    actual_anti_keyword_count: int
    tie_breaker_keys: list[str]
    pipeline_templates: list[str]
    declared_vs_actual_delta: dict
```

**Phát hiện quan trọng đã xác minh:** `_meta.total_keywords = 280` (không phải 220+ như báo cáo cũ nói). Schema version 1.1.0. Date 2026-10-12. Script track cả declared vs actual để stale-claims phát hiện drift này.

### 4. `tools/_collect_standards.py`

**Parse** `SKILLS_ROOT/STANDARDS_LOCK.md`, slice giữa `## 1. Bảng Chốt` và `##` tiếp theo, tách rows bằng `|\n`, extract `(TCVN|QCVN)\s+(\d+):(\d{4})` từ columns 2 và 3.

**Returns:** `list[StandardRow]` với fields: `domain`, `current`, `legacy`, `pdf_ref`.

**Edge case:** Nếu heading `## 1.` đổi tên → fallback scan toàn file bằng regex `(TCVN|QCVN)\s+\d+:\d{4}`. Log `W006`.

### 5. `tools/_collect_changelog.py`

**Parse** `CHANGELOG.md`, regex `r"^## (\d{4}-\d{2}-\d{2}) — (v[\d.]+):\s*(.+)$"` với `re.MULTILINE`, lấy match đầu tiên (entry mới nhất).

**Returns:** `ChangelogLatest` với `version`, `date`, `title`, `bullet_count` (đếm dòng bắt đầu bằng `- **`).

### 6. `tools/_collect_calculators.py`

**Globs** `*.py` trong `KNOWN_CALC_DIRS[skill]`, loại trừ `__init__.py`, `test_*.py`, files trong `_deprecated/`.

**Constant `KNOWN_CALC_DIRS`:** Map 13 skill → list subdirs (`calculators`, `scripts`).

**Returns:** `CalculatorInventory` với `by_skill: dict[str, list[str]]`, `total_count`, `skill_count_with_calculators`.

### 7. `tools/_verify_claims.py` — Tính năng phát hiện stale-claims

**Mục tiêu:** Đọc báo cáo markdown hiện tại, extract numeric/categorical claims qua regex, so sánh với `ReportData` mới, emit danh sách `StaleClaim`.

**Dataclass:**

```python
@dataclass
class StaleClaim:
    pattern_id: str
    line_excerpt: str
    reported_value: str
    actual_value: str
    severity: str   # "ERROR" | "WARNING" | "INFO"
```

**Bảng `CLAIM_PATTERNS` (module-level constant):**

```python
CLAIM_PATTERNS = [
    ("tests/intent",       r"(\d+)\s+test cases?",         lambda d: d.tests.suites[3].total_count),
    ("tests/integration",  r"(\d+)\s+log_test\(",          lambda d: d.tests.suites[0].total_count),
    ("tests/regression",   r"(\d+)\s+calculator",          lambda d: d.tests.suites[1].total_count),
    ("tests/approval",     r"(\d+)\s+approval.*?tests",    lambda d: d.tests.suites[2].total_count),
    ("kwdb/regex",         r"(\d+)\s+regex patterns?",     lambda d: d.keyword_db.actual_regex_count),
    ("kwdb/total_kw",      r"(\d+)\+?\s+từ khóa",          lambda d: d.keyword_db.declared_total_keywords),
    ("kwdb/tie_breaker",   r"(\d+)\s+(nhóm\s+)?tie",       lambda d: len(d.keyword_db.tie_breaker_keys)),
    ("kwdb/pipeline",      r"(\d+)\s+pipeline templ",      lambda d: len(d.keyword_db.pipeline_templates)),
    ("standards/count",    r"(\d+)\s+tiêu chuẩn",         lambda d: len(d.standards)),
    ("skills/total",       r"(\d+)\s+skills?",             lambda d: len(d.skills)),
]
```

**Severity heuristic:**
- Numeric mismatch (test count, version) → `ERROR`.
- Path mismatch (sai vị trí file) → `ERROR`.
- Soft-mismatch (từ mơ hồ "nhiều", "khoảng") → skip.

**Hai chế độ sử dụng:**

1. **Trong pipeline:** Khi `sync_report.py` chạy, gọi `diff_against_existing_report()` với file sắp bị overwrite. Kết quả ghi vào §8 của báo cáo mới.
2. **Standalone:** Có thể import `diff_against_existing_report` trong CI script (out of scope plan này).

### 8. `tools/_render_markdown.py` — Pure function

**Dataclass gom tất cả data:**

```python
@dataclass
class ReportData:
    captured_at: str
    skills: list[Skill]
    tests: TestRunResult
    keyword_db: KeywordDbStats
    standards: list[StandardRow]
    changelog: ChangelogLatest
    calculators: CalculatorInventory
    stale_claims: list[StaleClaim]

def render_report(data: ReportData) -> str: ...
```

**Cấu trúc 8 sections + footer (KHÔNG có narrative tự do):**

1. **Header** — version (auto), captured_at, cách tái tạo
2. **§1 TỔNG QUAN** — 4 bullet tóm tắt (skill count, test summary, standard count, calculator count)
3. **§2 SKILL INVENTORY** — table 13 dòng
4. **§3 KẾT QUẢ TEST SUITES** — table 6 dòng + grand totals
5. **§4 KEYWORD DATABASE** — declared vs actual table + tie-breakers + pipelines
6. **§5 TIÊU CHUẨN LOCKED** — table từ STANDARDS_LOCK
7. **§6 CALCULATOR INVENTORY** — per-skill counts
8. **§7 CHANGELOG MỚI NHẤT** — version, date, top 3 bullets
9. **§8 STALE-CLAIMS** — output từ verify_claims (nếu có)
10. **APPROVAL MATRIX** — fixed boilerplate (per AGENTS.md §8)
11. **DISCLAIMER** — fixed line

**Đặc điểm:** Không viết prose tự do. Toàn bộ là tables + bullets. Deterministic — cùng input cho cùng output.

### 9. `tools/sync_report.py` — CLI orchestrator

**CLI flags:**

| Flag | Effect |
|---|---|
| (none) | Chạy collectors, gọi verify, render, ghi file |
| `--dry-run` | Render ra stdout, không ghi file |
| `--output PATH` | Ghi vào PATH thay vì default |
| `--skip-tests` | Đọc cache từ `_active/last_test_run.json` thay vì chạy lại |
| `--strict` | Exit code 3 nếu `verify_claims` tìm thấy ERROR |

**Exit codes:**

| Code | Meaning |
|---|---|
| 0 | OK |
| 1 | Có test suite fail nhưng vẫn ghi report |
| 2 | Thiếu input bắt buộc (no cache + `--skip-tests`, malformed SKILL.md) |
| 3 | Stale-claims ERROR + `--strict` |

**Default paths:**
- Input: `AGENTS_ROOT/skills/`, `AGENTS_ROOT/tests/`, `AGENTS_ROOT/_SHARED/`
- Output: `AGENTS_ROOT/docs/BAO_CAO_PHAT_TRIEN_DIEU_PHOI_AI.md`
- Test cache: `AGENTS_ROOT/_SHARED/SHARED_CONTEXT/_active/last_test_run.json`

**Code skeleton (CLI chính):**

```python
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

def main() -> int:
    args = parse_args()
    data = ReportData(
        captured_at=datetime.now().isoformat(timespec="seconds"),
        skills=collect_skills(SKILLS_ROOT),
        tests=run_all_test_suites(TESTS_DIR) if not args.skip_tests else load_test_cache(),
        keyword_db=collect_keyword_db_stats(SKILLS_ROOT / "Global_Dispatcher" / "scripts" / "keyword_database.json"),
        standards=collect_standards(SKILLS_ROOT / "STANDARDS_LOCK.md"),
        changelog=collect_latest_changelog(AGENTS_ROOT / "skills" / "CHANGELOG.md"),
        calculators=collect_calculators(SKILLS_ROOT),
        stale_claims=[],
    )
    data.stale_claims = diff_against_existing_report(args.output, data)
    rendered = render_report(data)
    if args.dry_run:
        print(rendered)
        return 0
    args.output.write_text(rendered, encoding="utf-8")
    print(f"✅ Đã ghi: {args.output}")
    print(f"   Stale-claims: {len(data.stale_claims)} (ERROR={sum(1 for s in data.stale_claims if s.severity=='ERROR')})")
    if args.strict and any(s.severity == "ERROR" for s in data.stale_claims):
        return 3
    return 0
```

---

## Testing strategy

**File mới:** `tests/test_sync_report.py` — 7 test cases (unittest, không pytest để khớp convention hiện tại).

| # | Test | Mục đích |
|---|---|---|
| 1 | `test_collect_skills_returns_13` | Walk thật `SKILLS_ROOT`, assert `len == 13` và có đủ 13 tên |
| 2 | `test_collect_keyword_db_stats` | Load thật `keyword_database.json`, assert `actual_regex_count == 57`, `tie_breaker_keys == ["description","rules"]`, `len(pipeline_templates) == 7` |
| 3 | `test_collect_standards_row_count` | Parse thật `STANDARDS_LOCK.md`, assert `len(standards) >= 15` |
| 4 | `test_render_report_deterministic` | Build fixed `ReportData` fixture, gọi `render_report` 2 lần, assert byte-identical |
| 5 | `test_verify_claims_detects_known_drift` | Feed báo cáo hiện tại + real `ReportData`, assert có `StaleClaim` cho `tests/intent` severity ERROR |
| 6 | `test_skip_tests_loads_cache` | Viết cache JSON biết trước, gọi `main` với `--skip-tests --dry-run`, `mock.patch("subprocess.run")` assert không được gọi |
| 7 | `test_malformed_skill_frontmatter_returns_warning` | Tạo temp dir với `SKILL.md` thiếu `version:`, assert không crash, có `W003` warning |

**Không thêm test_sync_report.py vào `run_all_tests.py` SUITES trong plan này** — để tránh scope creep. Ghi nhận là follow-up.

---

## Edge cases & error handling

| Scenario | Hành vi |
|---|---|
| `run_all_tests.py` 1 suite fail | Report vẫn ghi; §3 có row đỏ cho suite fail đó |
| `run_all_tests.py` crash (ImportError) | Mark tất cả `unparsed`, log `W001`, exit 1 |
| `SKILL.md` no frontmatter | Thêm row "missing version" vào data quality, không crash |
| `tests-cache` > 24h | Warn `W004`, vẫn dùng (user opt-in bằng `--skip-tests`) |
| `tests-cache` không tồn tại + `--skip-tests` | Exit 2, không ghi file |
| `keyword_database.json` schema đổi | Catch KeyError, return dataclass rỗng + `W005` |
| `STANDARDS_LOCK.md` heading đổi | Fallback scan toàn file + `W006` |
| Suite timeout 5 phút | Mark `TIMEOUT`, không abort toàn bộ |
| File bị lock (Windows) | Retry 1 lần sau 1s, exit 2 nếu vẫn fail |
| 2 chạy đồng thời | `write_text` atomic với file <1MB, không cần lock |

---

## Các file hiện hữu được tham chiếu

- `g:/My Drive/Google AI Studio/.agents/tests/run_all_tests.py` (import `SUITES`, lines 20-27)
- `g:/My Drive/Google AI Studio/.agents/skills/STANDARDS_LOCK.md` (parse table, lines 14-32)
- `g:/My Drive/Google AI Studio/.agents/skills/Global_Dispatcher/scripts/keyword_database.json` (parse stats)
- `g:/My Drive/Google AI Studio/.agents/skills/CHANGELOG.md` (parse latest)
- `g:/My Drive/Google AI Studio/.agents/AGENTS.md` §8 (boilerplate approval matrix + disclaimer)
- `g:/My Drive/Google AI Studio/.agents/_SHARED/SHARED_CONTEXT/_active/` (cache dir đã tồn tại)

---

## Verification (end-to-end)

Sau khi implement xong, kiểm tra theo các bước:

1. **Smoke test dry-run:**
   ```powershell
   cd "g:/My Drive/Google AI Studio/.agents"
   python tools/sync_report.py --dry-run | head -100
   ```
   Expect: Markdown bắt đầu với header đúng, có 8 sections, table skill inventory liệt kê 13 skill đúng version.

2. **Smoke test full run:**
   ```powershell
   python tools/sync_report.py
   ```
   Expect: File `docs/BAO_CAO_PHAT_TRIEN_DIEU_PHOI_AI.md` được ghi đè, exit 0, summary in `Stale-claims: N (ERROR=M)`.

3. **Verify stale-claims detection:**
   ```powershell
   python tools/sync_report.py --strict
   ```
   Nếu báo cáo cũ có claims sai (ví dụ "15 test cases" trong khi thực tế 17), exit code phải là 3.

4. **Verify cache:**
   ```powershell
   python tools/sync_report.py         # chạy thật, ghi cache
   python tools/sync_report.py --skip-tests --dry-run  # dùng cache, không gọi subprocess
   ```

5. **Run test suite cho tool:**
   ```powershell
   python -m unittest tests.test_sync_report -v
   ```
   Expect: 7/7 passed.

6. **Manual review report mới:**
   Mở `docs/BAO_CAO_PHAT_TRIEN_DIEU_PHOI_AI.md` và verify:
   - Con số test counts khớp với output thật của `run_all_tests.py`
   - Phiên bản skill khớp với `SKILL.md` frontmatter
   - §8 STALE-CLAIMS có chỉ ra các lỗi cũ (15 → 17, 13 → 16, v.v.)

---

## Out of scope (ghi nhận follow-up, KHÔNG làm trong plan này)

- Thêm `tests/test_sync_report.py` vào `run_all_tests.py` SUITES (thành 7 suite).
- Tạo `tools/README.md` (chỉ tạo nếu user yêu cầu).
- Pre-commit hook `.git/hooks/pre-commit` chạy `--strict`.
- CI workflow `.github/workflows/sync-report.yml`.
- Thêm `**/SHARED_CONTEXT/_active/last_test_run.json` vào `.gitignore`.
- Viết narrative/kiến nghị chuyên sâu (sections §3-§7 của báo cáo v2.0 — đó là phần con người viết, không tự động sinh được).

---

## Sequenced implementation steps

1. **Bước 1 (~1h):** Tạo `tools/__init__.py` rỗng + 8 submodules với dataclass + `pass`. Verify import OK.
2. **Bước 2 (~2h):** Implement `_collect_skills.py` + `_collect_standards.py` (pure functions, dễ nhất). Thêm test 1, 3.
3. **Bước 3 (~2h):** Implement `_collect_keyword_db.py` + `_collect_changelog.py` + `_collect_calculators.py`. Thêm test 2.
4. **Bước 4 (~3h):** Implement `_collect_tests.py` (phức tạp nhất — 6 parsers + cache).
5. **Bước 5 (~2h):** Implement `_verify_claims.py` với `CLAIM_PATTERNS` table. Thêm test 5.
6. **Bước 6 (~3h):** Implement `_render_markdown.py` (template cố định).
7. **Bước 7 (~1h):** Implement `sync_report.py` CLI. Thêm test 6, 7.
8. **Bước 8 (~30 min):** End-to-end smoke test: `--dry-run` → review → full run → verify §8 stale-claims.
9. **Bước 9 (~30 min):** Final review, fix edge cases phát sinh, cập nhật nếu cần.

Tổng: ~14.5 giờ làm việc (2 ngày).

---

*Báo cáo này tự giải thích nó: sau khi `tools/sync_report.py` chạy lần đầu, §8 STALE-CLAIMS sẽ liệt kê chính những sai sót của báo cáo v2.0 mà bạn vừa tạo.*
