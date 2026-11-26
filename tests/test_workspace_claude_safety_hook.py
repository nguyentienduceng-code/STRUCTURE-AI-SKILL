"""Project-level Claude tool events; all writable fixtures live in a temporary folder."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))
import claude_safety_hook as hook


class HookTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name).resolve()
        self.project = self.root / "01_Projects" / "Case"
        self.out = self.project / "04_Deliverables_ToTrinh"
        self.out.mkdir(parents=True)
        self.original = self.project / "Original.DWG"
        self.original.write_bytes(b"unchanged")
        root_patch = patch.object(hook, "ROOT", self.root)
        root_patch.start()
        self.addCleanup(root_patch.stop)

    def event(self, tool, post=False, **data):
        return {"cwd": str(self.project), "tool_name": tool, "tool_input": data,
                "hook_event_name": "PostToolUse" if post else "PreToolUse"}

    def test_original_and_new_exports(self):
        for tool in ("Write", "Edit", "MultiEdit"):
            for path in (self.original, self.out / ".." / self.original.name):
                self.assertEqual(hook.handle(self.event(tool, file_path=str(path)))[0], "deny")
        new = self.out / "new.dwg"
        self.assertFalse(hook.handle(self.event("Write", file_path=str(new)))[0])
        new.touch()
        self.assertEqual(hook.handle(self.event("Write", file_path=str(new)))[0], "deny")

    def test_commands(self):
        bridge = self.root / ".agents/tools/autocad_snapshot_bridge.py"
        accore = self.root / ".agents/tools/accoreconsole_adapter.py"
        for command in ("git status", "git diff", "pytest -q", "python tests/smoke.py",
                        "Get-FileHash Original.DWG", "git diff -- Original.DWG",
                        f'python "{bridge}" snapshot Original.DWG',
                        f'python "{accore}" --audit-only 04_Deliverables_ToTrinh/new_or_existing.dwg',
                        'copy Original.DWG "04_Deliverables_ToTrinh/new.dwg"'):
            with self.subTest(command=command):
                self.assertFalse(hook.handle(self.event("Bash", command=command))[0])
        for command in ("echo data > Original.DWG", "git status && echo x > Original.DWG",
                        f'python "{accore}" Original.DWG',
                        f'python "{accore}" --audit-only Original.DWG; echo hi',
                        "Set-Content Original.DWG sample", 'python -c "open(\'Original.DWG\', \'wb\')"'):
            with self.subTest(command=command):
                self.assertEqual(hook.handle(self.event("PowerShell", command=command))[0], "deny")

    def test_push_review(self):
        for command in ("git push origin main", 'git -C "repo with spaces" push', "git status && git push"):
            self.assertEqual(hook.handle(self.event("Bash", command=command))[0], "ask")

    def test_post_source_and_docx(self):
        code = self.project / "format.py"
        code.write_text('text_color = "FFFFFF"')
        self.assertEqual(hook.handle(self.event("Edit", post=True, file_path=str(code)))[0], "report")
        code.write_text('text_color = "222222"')
        self.assertFalse(hook.handle(self.event("Edit", post=True, file_path=str(code)))[0])
        doc = self.project / "Báo cáo.docx"
        for color, decision in (("FFFFFF", "report"), ("1C1E21", "")):
            with ZipFile(doc, "w") as z:
                z.writestr("word/document.xml", f'<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:p><w:r><w:rPr><w:color w:val="{color}"/></w:rPr><w:t>abc</w:t></w:r></w:p></w:document>')
            self.assertEqual(hook.handle(self.event("Bash", post=True, command=f'python report.py "{doc}"'))[0], decision)

    def test_copy_source_stays_in_project_deliverables(self):
        outside = self.root / "external.dwg"
        self.assertEqual(hook.handle(self.event("PowerShell", command=f'Copy-Item Original.DWG "{outside}"'))[0], "deny")

    def test_actual_office_reports(self):
        from docx import Document
        from docx.shared import RGBColor
        from openpyxl import Workbook
        from openpyxl.styles import Font
        for white in (True, False):
            rgb = "FFFFFF" if white else "222222"
            doc = Document()
            doc.styles["Normal"].font.color.rgb = RGBColor.from_string(rgb)
            doc.add_table(rows=1, cols=1).cell(0, 0).text = "Kết quả"
            word = self.project / "inline.docx"
            doc.save(word)
            book = Workbook()
            cell = book.active["A1"]
            cell.value = "Kết quả"
            cell.font = Font(color=rgb)
            sheet = self.project / "inline.xlsx"
            book.save(sheet)
            for path in (word, sheet):
                with self.subTest(path=path, rgb=rgb):
                    self.assertEqual(hook.handle(self.event("Write", post=True, file_path=str(path)))[0],
                                     "report" if white else "")

    def test_installed_protocol(self):
        root = TOOLS.parents[1]
        settings = json.loads((root / ".claude/settings.json").read_text(encoding="utf-8"))
        for event, expected in [
            (self.event("Bash", command="git status"), 0),
            (self.event("Write", file_path=str(root / "01_Projects/Fixture/Input.dwg")), 2),
            (self.event("Bash", command="git push"), 0),
        ]:
            config = settings["hooks"][event["hook_event_name"]]
            command = next(h["command"] for group in config for h in group["hooks"] if "claude_safety_hook.py" in h.get("command", ""))
            result = subprocess.run(hook.tokens(command), input=json.dumps(event), text=True, capture_output=True, encoding="utf-8")
            self.assertEqual(result.returncode, expected, result.stderr)
            if event["tool_input"].get("command") == "git push":
                self.assertEqual(json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"], "ask")


if __name__ == "__main__":
    unittest.main()
