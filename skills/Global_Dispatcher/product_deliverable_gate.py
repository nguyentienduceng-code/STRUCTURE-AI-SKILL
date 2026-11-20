"""ProductDeliverableGate & JargonLinter for 2D Cognitive Dispatcher (v3.4).

Enforces two hard gates in ``PRODUCT_COLLAB`` mode:
1. Real artifact verification inside ``04_Deliverables_ToTrinh/`` (non-empty
   ``.docx``, ``.pdf``, ``.dxf``, or ``.xlsx`` created/updated after task start),
   computing SHA-256 hashes silently for the v3.3 Control Plane.
2. Vietnamese engineering Jargon Linter blocking raw software/DevOps terms
   (``SSOT``, ``unpack``, ``receipt``, ``SHA-256``, ``gate=PASS``, etc.) from
   leaking into user-facing summaries.

Also provides ``build_claude_handover_prompt`` to generate role-locked handoff
instructions for Claude (Lead Auditor TCVN vs. Software Architect).
"""

from __future__ import annotations

from io import BytesIO
from zipfile import ZipFile
from xml.etree import ElementTree

import hashlib
import json
import re
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


DEFAULT_ALLOWED_EXTENSIONS: Tuple[str, ...] = (".docx", ".pdf", ".dxf", ".xlsx")
DEFAULT_FORBIDDEN_AUDIT_DIRS: Tuple[str, ...] = (
    ".agents/memory/audits",
    ".claude/memory",
)
DEFAULT_JARGON_BLACKLIST: Tuple[str, ...] = (
    "SSOT",
    "unpack",
    "receipt",
    "RECEIPTS",
    "SHA-256",
    "evidence_hashes",
    "action_type",
    "gate=PASS",
    "force=False",
    "mock",
    "IPC",
    "POSIX",
    "bus_meta",
    "stdout",
    "stderr",
    "pytest",
    "refactor",
)


def _identity_lines(content: bytes, ext: str):
    """Read visible identification text from the same bytes that are hashed."""
    stream = BytesIO(content)
    if ext == ".docx":
        word = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
        with ZipFile(stream) as archive:
            for name in archive.namelist():
                if re.fullmatch(r"word/(?:document|header\d+|footer\d+)\.xml", name):
                    for para in ElementTree.fromstring(archive.read(name)).iter(word + "p"):
                        yield "".join(node.text or "" for node in para.iter(word + "t"))
    elif ext == ".xlsx":
        import openpyxl
        book = openpyxl.load_workbook(stream, read_only=True, data_only=True)
        try:
            for sheet in book:
                for row in sheet.values:
                    yield " ".join(str(value) for value in row if value is not None)
        finally:
            book.close()
    elif ext == ".pdf":
        import fitz
        with fitz.open(stream=content, filetype="pdf") as pdf:
            for page in pdf:
                yield from page.get_text().splitlines()
    elif ext == ".dxf":
        from ezdxf import recover
        drawing, audit = recover.read(stream)
        if audit.errors:
            raise ValueError("DXF có lỗi cấu trúc.")
        for block in drawing.blocks:
            for entity in block.query("TEXT MTEXT ATTRIB ATTDEF INSERT"):
                if entity.dxftype() == "INSERT":
                    yield from (at.dxf.text for at in entity.attribs)
                else:
                    yield entity.plain_text() if entity.dxftype() == "MTEXT" else entity.dxf.text


def _sha256_file(path: Path, chunk_size: int = 65536) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            chunk = fh.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _format_paths(path: Path) -> Tuple[str, str]:
    raw = str(path)
    return raw.replace("\\", "/"), raw.replace("/", "\\")


@dataclass
class JargonLintResult:
    passed: bool
    violations: List[str] = field(default_factory=list)
    missing_sections: List[str] = field(default_factory=list)
    message_vi: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class VerifiedArtifact:
    filename: str
    extension: str
    path_posix: str
    path_win: str
    size_bytes: int
    mtime_epoch: float
    mtime_iso: str
    sha256: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class GateVerificationResult:
    status: str  # PASS | BLOCKED_INVALID_DIR | BLOCKED_MISSING_DELIVERABLE | BLOCKED_JARGON_VIOLATION
    passed: bool
    deliverable_dir_posix: str
    deliverable_dir_win: str
    verified_artifacts: List[VerifiedArtifact] = field(default_factory=list)
    evidence_hashes: Dict[str, str] = field(default_factory=dict)
    stray_md_files: List[str] = field(default_factory=list)
    jargon_lint: Optional[Dict[str, Any]] = None
    message_vi: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "passed": self.passed,
            "deliverable_dir_posix": self.deliverable_dir_posix,
            "deliverable_dir_win": self.deliverable_dir_win,
            "verified_artifacts": [a.to_dict() for a in self.verified_artifacts],
            "evidence_hashes": self.evidence_hashes,
            "stray_md_files": self.stray_md_files,
            "jargon_lint": self.jargon_lint,
            "message_vi": self.message_vi,
        }


class JargonLinter:
    """Blocks raw DevOps/programming jargon in PRODUCT_COLLAB user reports."""

    def __init__(
        self,
        blacklist: Optional[Sequence[str]] = None,
        db_path: Optional[str | Path] = None,
    ) -> None:
        terms: List[str] = []
        if blacklist is not None:
            terms = list(blacklist)
        elif db_path and Path(db_path).exists():
            data = json.loads(Path(db_path).read_text(encoding="utf-8"))
            terms = list(data.get("jargon_blacklist_product_vi", DEFAULT_JARGON_BLACKLIST))
        else:
            sibling = Path(__file__).with_name("keyword_database.json")
            if sibling.exists():
                data = json.loads(sibling.read_text(encoding="utf-8"))
                terms = list(data.get("jargon_blacklist_product_vi", DEFAULT_JARGON_BLACKLIST))
            else:
                terms = list(DEFAULT_JARGON_BLACKLIST)

        # Deduplicate while preserving order
        seen: set[str] = set()
        self.blacklist: List[str] = []
        for term in terms:
            key = term.lower()
            if key not in seen:
                seen.add(key)
                self.blacklist.append(term)

    def lint(self, report_text: str) -> JargonLintResult:
        if not report_text or not report_text.strip():
            return JargonLintResult(
                passed=False,
                violations=[],
                missing_sections=["(1) Đã sửa gì", "(2) File ở đâu", "(3) Số liệu đạt hay không"],
                message_vi=(
                    "Thiếu báo cáo tóm tắt tiếng Việt 3 ý: "
                    "(1) Đã sửa gì? (2) File ở đâu? (3) Số liệu đạt hay không?"
                ),
            )

        violations: List[str] = []
        for term in self.blacklist:
            # Use boundary match for alphanumeric words; substring match for symbols like '=' or '-'
            if re.fullmatch(r"[A-Za-z0-9_]+", term):
                pattern = rf"(?<![A-Za-z0-9_]){re.escape(term)}(?![A-Za-z0-9_])"
            else:
                pattern = re.escape(term)
            if re.search(pattern, report_text, flags=re.IGNORECASE):
                violations.append(term)

        lowered = report_text.lower()
        missing_sections: List[str] = []
        if not any(k in lowered for k in ("đã sửa", "chỉnh sửa", "cập nhật", "thẩm tra", "rá soát", "rà soát")):
            missing_sections.append("(1) Đã sửa gì")
        if not any(k in lowered for k in (".docx", ".pdf", ".dxf", ".xlsx")):
            missing_sections.append("(2) File ở đâu")
        if not any(k in lowered for k in ("đạt", "chưa đủ căn cứ", "chưa đủ cơ sở")):
            missing_sections.append("(3) Số liệu đạt hay không")

        if violations:
            bad = ", ".join(violations)
            return JargonLintResult(
                passed=False,
                violations=violations,
                missing_sections=missing_sections,
                message_vi=(
                    f"Báo cáo người dùng chứa biệt ngữ lập trình bị cấm trong chế độ dự án: {bad}. "
                    "Vui lòng viết lại bằng tiếng Việt kỹ thuật ngắn gọn theo 3 ý: "
                    "(1) Đã sửa gì? (2) File ở đâu? (3) Số liệu đạt hay không?"
                ),
            )

        return JargonLintResult(
            passed=not missing_sections,
            violations=[],
            missing_sections=missing_sections,
            message_vi="Thiếu " + ", ".join(missing_sections) if missing_sections else "Báo cáo tiếng Việt kỹ thuật hợp lệ.",
        )


class ProductDeliverableGate:
    """Hard gate verifying real project artifacts and Vietnamese technical summary."""

    def __init__(
        self,
        allowed_extensions: Sequence[str] = DEFAULT_ALLOWED_EXTENSIONS,
        forbidden_audit_dirs: Sequence[str] = DEFAULT_FORBIDDEN_AUDIT_DIRS,
        jargon_linter: Optional[JargonLinter] = None,
    ) -> None:
        self.allowed_extensions = tuple(ext.lower() for ext in allowed_extensions)
        self.forbidden_audit_dirs = tuple(forbidden_audit_dirs)
        self.jargon_linter = jargon_linter or JargonLinter()

    def _scan_stray_md(self, workspace_root: Optional[Path], task_started_at: float) -> List[str]:
        if not workspace_root:
            return []
        strays: List[str] = []
        for rel in self.forbidden_audit_dirs:
            folder = workspace_root / rel
            if not folder.exists() or not folder.is_dir():
                continue
            for entry in folder.rglob("*.md"):
                try:
                    if entry.stat().st_mtime >= task_started_at - 1.0:
                        strays.append(str(entry).replace("\\", "/"))
                except OSError:
                    continue
        return sorted(strays)

    def verify(
        self,
        deliverable_dir: str | Path,
        task_started_at: float,
        user_report_vi: str,
        workspace_root: Optional[str | Path] = None,
        expected_extensions: Optional[Iterable[str]] = None,
        expected_files: Sequence[str] = (),
        required_extensions: Sequence[str] = (),
        project_identity: Optional[str] = None,
    ) -> GateVerificationResult:
        deliv_path = Path(deliverable_dir)
        deliv_posix, deliv_win = _format_paths(deliv_path)
        ws_path = Path(workspace_root) if workspace_root else None
        exts = tuple(e.lower() for e in expected_extensions) if expected_extensions else self.allowed_extensions

        if not deliv_path.exists() or not deliv_path.is_dir():
            strays = self._scan_stray_md(ws_path, task_started_at)
            return GateVerificationResult(
                status="BLOCKED_INVALID_DIR",
                passed=False,
                deliverable_dir_posix=deliv_posix,
                deliverable_dir_win=deliv_win,
                stray_md_files=strays,
                message_vi=(
                    f"Thư mục bàn giao không tồn tại: {deliv_win}. "
                    "Chưa thể đóng ca khi chưa có hồ sơ thực tế trong thư mục dự án."
                ),
            )

        required = {name.casefold() for name in expected_files}
        verified: List[VerifiedArtifact] = []
        evidence_hashes: Dict[str, str] = {}
        for entry in sorted(deliv_path.iterdir(), key=lambda p: p.name.lower()):
            if not entry.is_file():
                continue
            if entry.name.startswith("~$") or entry.name.startswith("."):
                continue
            ext = entry.suffix.lower()
            if (required and entry.name.casefold() not in required) or ext not in exts:
                continue
            stat = entry.stat()
            if stat.st_size <= 0:
                continue
            if stat.st_mtime < (task_started_at - 1.0):
                continue
            if project_identity:
                try:
                    content = entry.read_bytes()
                    marker = " ".join(project_identity.casefold().split())
                    identity_match = re.compile(r"(?<!\w)" + re.escape(marker) + r"(?!\w)")
                    if not marker or not any(identity_match.search(" ".join(line.casefold().split()))
                                             for line in _identity_lines(content, ext)):
                        raise ValueError("Không xác nhận được định danh " + project_identity)
                    digest = hashlib.sha256(content).hexdigest()
                except Exception as exc:
                    return GateVerificationResult(
                        "BLOCKED_PROJECT_IDENTITY", False, deliv_posix, deliv_win,
                        message_vi=f"{entry.name}: {exc}",
                    )
            else:
                digest = _sha256_file(entry)
            after = entry.stat()
            if (stat.st_size, stat.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                return GateVerificationResult(
                    "BLOCKED_FILE_CHANGED", False, deliv_posix, deliv_win,
                    message_vi=f"{entry.name} thay đổi trong khi kiểm tra. Cần chạy lại.",
                )
            p_posix, p_win = _format_paths(entry)
            mtime_iso = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()
            verified.append(
                VerifiedArtifact(
                    filename=entry.name,
                    extension=ext,
                    path_posix=p_posix,
                    path_win=p_win,
                    size_bytes=stat.st_size,
                    mtime_epoch=stat.st_mtime,
                    mtime_iso=mtime_iso,
                    sha256=digest,
                )
            )
            evidence_hashes[p_posix] = digest

        missing = required.difference(a.filename.casefold() for a in verified)
        missing.update(set(required_extensions).difference(a.extension for a in verified))
        if missing:
            return GateVerificationResult(
                "BLOCKED_MISSING_DELIVERABLE", False, deliv_posix, deliv_win,
                message_vi="Thiếu tệp của ca: " + ", ".join(sorted(missing)),
            )
        if not verified:
            strays = self._scan_stray_md(ws_path, task_started_at)
            stray_note = (
                f" Phát hiện {len(strays)} file nháp .md bị ghi lạc vào thư mục hệ thống ({', '.join(strays[:2])})."
                if strays
                else ""
            )
            ext_list = ", ".join(exts)
            return GateVerificationResult(
                status="BLOCKED_MISSING_DELIVERABLE",
                passed=False,
                deliverable_dir_posix=deliv_posix,
                deliverable_dir_win=deliv_win,
                stray_md_files=strays,
                message_vi=(
                    f"Chưa tìm thấy hồ sơ mới ({ext_list}) trong {deliv_win}.{stray_note} "
                    "Yêu cầu chạy script xuất file hoàn chỉnh vào đúng thư mục dự án trước khi đóng ca."
                ),
            )

        lint_res = self.jargon_linter.lint(user_report_vi)
        if lint_res.passed and not any(a.filename.casefold() in user_report_vi.casefold() for a in verified):
            lint_res.passed = False
            lint_res.missing_sections.append("(2) Tên tệp thực tế")
            lint_res.message_vi = "Báo cáo cần dẫn tới tệp đã được kiểm tra trong thư mục dự án."
        if not lint_res.passed:
            return GateVerificationResult(
                status="BLOCKED_JARGON_VIOLATION",
                passed=False,
                deliverable_dir_posix=deliv_posix,
                deliverable_dir_win=deliv_win,
                verified_artifacts=verified,
                evidence_hashes=evidence_hashes,
                jargon_lint=lint_res.to_dict(),
                message_vi=lint_res.message_vi,
            )

        file_names = ", ".join(a.filename for a in verified)
        return GateVerificationResult(
            status="PASS",
            passed=True,
            deliverable_dir_posix=deliv_posix,
            deliverable_dir_win=deliv_win,
            verified_artifacts=verified,
            evidence_hashes=evidence_hashes,
            jargon_lint=lint_res.to_dict(),
            message_vi=f"Đạt cổng nghiệm thu hồ sơ ({len(verified)} tệp: {file_names}) tại {deliv_win}.",
        )


def build_claude_handover_prompt(
    classification: Dict[str, Any],
    task_title: str,
    source_scripts: Optional[Sequence[str]] = None,
    notes: str = "",
) -> str:
    """Generate role-locked handover instructions for Claude based on engagement_mode."""
    mode = classification.get("engagement_mode", "SOLO_EXECUTION")
    domain = classification.get("domain_skill", "GENERAL")

    choice = classification.get("agent_selection", "AUTO")
    actor = {"GEMINI_ONLY": "Gemini", "CLAUDE_ONLY": "Claude"}.get(choice)
    role = f"{actor} lập hồ sơ và tự kiểm tra" if actor else "Chủ trì thẩm tra kỹ thuật"
    if mode == "PRODUCT_COLLAB":
        deliv_win = classification.get("deliverable_dir_win") or "<CHƯA XÁC ĐỊNH THƯ MỤC DỰ ÁN>"
        allow_patch = bool(classification.get("allow_script_patch", False))
        scripts_block = (
            "\n".join(f"- {s}" for s in source_scripts)
            if source_scripts
            else "- (Tự đối chiếu script build trong thư mục dự án)"
        )
        patch_rule = (
            "Được phép sửa trực tiếp script build cục bộ của dự án để khắc phục lỗi trình bày/số liệu và chạy lại lệnh xuất hồ sơ."
            if allow_patch
            else "Dùng script hiện có. Nếu cần sửa script, trình người dùng duyệt thay đổi quyền."
        )
        extra = f"\nGhi chú bổ sung từ Chủ trì: {notes.strip()}" if notes.strip() else ""
        return (
            f"PHIẾU GIAO THẨM TRA HỒ SƠ DỰ ÁN\n"
            f"Hạng mục: {task_title}\n"
            f"Chuyên môn: {domain}\n"
            f"Vai trò thực hiện: {role}. Áp dụng skill chuyên môn và trình kết quả theo Điều 3 trước khi xuất.\n"
            f"Thư mục xuất hồ sơ BẮT BUỘC: {deliv_win}\n"
            f"Định dạng đầu ra bắt buộc: .docx, .pdf, .dxf hoặc .xlsx (KHÔNG chỉ xuất file .md vào .agents/memory/).\n"
            f"Script/hồ sơ liên quan:\n{scripts_block}\n"
            f"Yêu cầu thực hiện:\n"
            f"1. Đối chiếu chéo số liệu tính toán, tiêu chuẩn TCVN hiện hành và văn phong hành chính chuẩn Nghị định 30.\n"
            f"2. {patch_rule}\n"
            f"3. Báo cáo kết quả hoàn toàn bằng tiếng Việt kỹ thuật (cấm dùng thuật ngữ lập trình/DevOps) theo đúng 3 ý:\n"
            f"   - Đã sửa gì?\n"
            f"   - File hoàn chỉnh nằm ở đâu?\n"
            f"   - Số liệu và tiêu chuẩn đạt hay chưa đạt?{extra}"
        )

    if mode == "SYSTEM_UPGRADE":
        protocol = "Run locally and record self-checks." if actor else "Follow the v3.3 dual-agent protocol."
        scripts_block = ", ".join(source_scripts) if source_scripts else "(core .agents/ modules)"
        extra = f"\nNotes: {notes.strip()}" if notes.strip() else ""
        return (
            f"[SYSTEM_UPGRADE HANDOVER - v3.4]\n"
            f"Task: {task_title}\n"
            f"Domain: {domain} | Executor: {actor or 'assigned agent'} | Role: Software Architect / DevOps\n"
            f"Target files: {scripts_block}\n"
            f"Requirements:\n"
            f"1. {protocol}\n"
            f"2. Keep changes scoped to .agents/tools/, .agents/skills/, or .agents/memory/audits/.\n"
            f"3. Run regression tests via run_all_tests.py before marking COMPLETED.{extra}"
        )

    return f"Thực hiện theo skill đã chọn: {task_title}. Tác tử: {actor or choice}."
