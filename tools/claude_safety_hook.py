"""Claude Code project hooks. Read one event from stdin; never run tool input."""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SHELLS = {"Bash", "PowerShell"}
EDITORS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
REPORTS = {".py", ".docx", ".xlsx", ".md", ".pdf"}
# Keep quoted Windows paths intact, including spaces and backslashes.
TOKENS = re.compile(r'''"([^"]*)"|'([^']*)'|([^\s"';&|<>()]+)''')
PUSH = re.compile(r'''\bgit(?:\.exe)?["']?\s+(?:(?:"[^"]*"|'[^']*'|[^\s;&|"\']+)\s+)*?push\b''', re.I)
DWG_ERROR = "Chặn ghi DWG dự án. Hãy xuất bản mới trong 04_Deliverables_ToTrinh hoặc dùng công cụ snapshot chỉ đọc."


def canonical(value, cwd):
    value = os.path.expanduser(os.path.expandvars(value)).replace("\\\\", "/")
    value = re.sub(r"^/(?:mnt/)?([a-zA-Z])/", r"\\1:/", value)
    return os.path.realpath(os.path.join(cwd, value))


def local_path(value, cwd):
    from pathlib import Path
    return Path(canonical(value, cwd))


def project_parts(path):
    prefix = os.path.normcase(os.path.join(ROOT, "01_Projects")) + os.sep
    name = os.path.normcase(os.path.normpath(path))
    return name[len(prefix):].split(os.sep) if name.startswith(prefix) else ()


def protected(path):
    parts = project_parts(path)
    if not parts or not parts[-1].lower().rstrip(" .").endswith(".dwg"):
        return False
    export = len(parts) >= 3 and parts[1].casefold() == "04_deliverables_totrinh"
    return not export or os.path.lexists(path)


def tokens(command):
    return [next(x for x in match.groups() if x is not None) for match in TOKENS.finditer(command)]


def read_only(command):
    # Redirects, command substitution and compound commands need their own check.
    if re.search(r"[;&|<>\x60$\r\n()]", command):
        return False
    if re.match(r"^\s*git\s+(?:status|diff)\b", command, re.I):
        return not re.search(r"--(?:output|ext-diff|textconv)\b", command, re.I)
    return bool(re.match(r"^\s*(?:cat|type|Get-Content|Get-Item|Get-FileHash|Test-Path|ls|dir)\s", command, re.I))


def handle(event):
    kind = event["hook_event_name"]
    tool = event["tool_name"]
    data = event["tool_input"]
    command = data.get("command", "") if tool in SHELLS else ""
    if kind == "PreToolUse" and tool in SHELLS and ".dwg" not in command.lower():
        if PUSH.search(command):
            return "ask", "Review Gate: xác nhận đã kiểm tra thay đổi, kết quả test và đích git push."
        return "", ""
    file = data.get("file_path") or data.get("notebook_path")
    cwd = event.get("cwd") or ROOT
    if kind == "PreToolUse" and tool in EDITORS:
        if file and file.casefold().rstrip(" .").endswith(".dwg") and protected(canonical(file, cwd)):
            return "deny", DWG_ERROR
        return "", ""
    from pathlib import Path
    words = tokens(command)
    if kind == "PreToolUse":
        if tool.startswith("mcp__"):
            uncertain = False
            for key, value in data.items():
                if isinstance(value, str) and value.lower().endswith(".dwg") and protected(local_path(value, cwd)):
                    if re.search(r"out|dest|target|save", key, re.I):
                        return "deny", DWG_ERROR
                    if not tool.endswith(("__native_dwg_snapshot", "__native_dwg_diff")):
                        uncertain = True
            if uncertain:
                return "ask", "Xác nhận công cụ CAD chỉ đọc bản DWG dự án."
        if command:
            if ".dwg" in command.lower() and not read_only(command):
                paths = [w.split("=", 1)[-1] for w in words if w.casefold().endswith(".dwg")]
                for word in words:
                    if any(q in word for q in ("'", '"')):
                        paths.extend(w for w in tokens(word) if w.casefold().endswith(".dwg"))
                # The workspace bridge runs Core Console on a staging copy.
                if (len(words) in (4, 5) and not re.search(r"[;&|<>$`\r\n]", command)
                        and re.fullmatch(r"(?:py|python(?:3)?)(?:\.exe)?", words[0], re.I)
                        and local_path(words[1], cwd) == Path(ROOT) / ".agents/tools/autocad_snapshot_bridge.py"
                        and ((words[2] == "snapshot" and len(words) == 4)
                             or (words[2] == "diff" and len(words) == 5))
                        and all(w.lower().endswith(".dwg") for w in words[3:])):
                    return "", ""
                # Read-only AutoCAD Core Console AUDIT on an isolated temp copy.
                if (len(words) == 4 and not re.search(r"[;&|<>$`\r\n]", command)
                        and re.fullmatch(r"(?:py|python(?:3)?)(?:\.exe)?", words[0], re.I)
                        and local_path(words[1], cwd) == Path(ROOT) / ".agents/tools/accoreconsole_adapter.py"
                        and words[2] == "--audit-only"
                        and words[3].lower().endswith(".dwg")):
                    return "", ""
                copy = re.fullmatch(r"\s*(?:cp|copy|copy-item)\s+[^;&|<>$\r\n]+", command, re.I)
                # Copy reads the source. The destination, including a directory, is a write.
                if copy and len(words) == 3:
                    source, dest = (local_path(w, cwd) for w in words[1:])
                    if dest.is_dir():
                        dest = dest / source.name
                    source_parts = project_parts(source)
                    if source_parts and source.suffix.lower() == ".dwg":
                        target_parts = project_parts(dest)
                        if (len(target_parts) < 3 or target_parts[1].casefold() != "04_deliverables_totrinh"
                                or target_parts[0].casefold() != source_parts[0].casefold()):
                            return "deny", DWG_ERROR
                    paths = [str(dest)]
                if any(protected(local_path(p, cwd)) for p in paths):
                    return "deny", DWG_ERROR
                # Shell variables, globs and a changed working directory can hide the target.
                if (not paths or re.search(r"[$*?%]|(?:^|[;&|])\s*(?:cd|pushd|set-location)\s", command, re.I)):
                    return "ask", "Chưa xác định được đích DWG. Xác nhận nguồn chỉ đọc và đường dẫn xuất."
            if PUSH.search(command):
                return "ask", "Review Gate: xác nhận đã kiểm tra thay đổi, kết quả test và đích git push."
        return "", ""
    if kind != "PostToolUse":
        raise ValueError("Sự kiện hook không hợp lệ")
    paths = []
    if file and tool in EDITORS:
        paths.append(file)
    elif command and not read_only(command):
        for word in words:
            candidates = [word, *tokens(word)] if any(q in word for q in ("'", '"')) else [word]
            paths.extend(w.split("=", 1)[-1] for w in candidates if Path(w).suffix.lower() in REPORTS)
        # For a Python invocation the script itself is normally input.
        if len(words) >= 2 and re.fullmatch(r"(?:python(?:3(?:\.\d+)?)?|py)(?:\.exe)?", Path(words[0]).name, re.I):
            paths = [p for p in paths if p != words[1] or Path(p).suffix.lower() != ".py"]
        result = event.get("tool_response") or {}
        if isinstance(result, dict):
            for part in str(result.get("stdout", "")).splitlines():
                path_line = re.sub(r"^.*?(?=[A-Za-z]:[\\\\/])", "", part).strip()
                paths += [path_line, part.strip(), *tokens(part)]
    elif tool.startswith("mcp__"):
        paths.extend(value for key, value in data.items()
                     if isinstance(value, str) and re.search(r"out|dest|target|save", key, re.I))
        response = event.get("tool_response")
        if isinstance(response, dict):
            paths.extend(value for key, value in response.items()
                         if isinstance(value, str) and re.search(r"out|file|path|report", key, re.I))
    checked = set()
    notices = []
    for item in paths:
        if Path(item).suffix.lower() not in REPORTS:
            continue
        path = local_path(item, cwd)
        if path in checked or not path.is_relative_to(ROOT):
            continue
        if not path.is_file():
            if tool in EDITORS:
                notices.append(f"Chưa tìm thấy tệp vừa sửa: {path}")
            continue
        checked.add(path)
        if sys.flags.isolated and os.path.dirname(__file__) not in sys.path:
            sys.path.insert(0, os.path.dirname(__file__))
        from audit_zero_white_text import audit_file
        if path.suffix.lower() == ".pdf" and sys.flags.no_site:
            import site
            site.main()
        problems = audit_file(path)
        if problems:
            notices.append(f"{path}\n" + "\n".join(problems[:10]))
    if notices:
        return "report", "Zero White Text: " + "\n".join(notices)
    return "", ""


def main():
    try:
        action, message = handle(json.load(sys.stdin))
    except Exception as exc:
        action, message = "deny", f"Lỗi kiểm tra hook: {exc}"
    if action in {"deny", "report"}:
        print(message, file=sys.stderr)
        return 2
    if action == "ask":
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                         "permissionDecision": "ask", "permissionDecisionReason": message}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
