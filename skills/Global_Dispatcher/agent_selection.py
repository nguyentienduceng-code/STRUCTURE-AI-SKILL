"""Select the allowed agent independently of the task's domain and mode."""
from pathlib import Path
import re
from typing import Optional

import unicodedata

AGENT_CHOICES = ("AUTO", "CLAUDE_ONLY", "GEMINI_ONLY", "DUAL")
SINGLE_AGENT = {"CLAUDE_ONLY": "CLAUDE", "GEMINI_ONLY": "GEMINI"}


_AGENT = r"(?:claude|germini|gemini)"
_PAIR = rf"(?:claude\s*(?:\+|\bva\b)\s*(?:gemini|germini)|(?:gemini|germini)\s*(?:\+|\bva\b)\s*claude)"
_VERB = r"(?:su dung|dung|sai|chay|chon)"
_DIRECTIVE = re.compile(
    rf"(?<!khong )\b(?:rieng ca nay\s+)?(?:"
    rf"(?P<dual>(?:(?:chi\s+)?(?:muon\s+)?(?:{_VERB}|phoi hop|ca)\s+(?:(?:ca|giua)\s+)?{_PAIR})|"
    rf"(?:claude\s*\+\s*(?:gemini|germini)|(?:gemini|germini)\s*\+\s*claude))|"
    rf"(?P<single>chi\s+(?:muon\s+)?(?:{_VERB}\s+)?(?P<name>{_AGENT}))|"
    r"(?P<auto>tu dong chon tac tu|chon tac tu tu dong))\b", re.I,
)


def _directives(prompt):
    # Match on an accent-folded view with the same offsets as the visible text.
    prompt = unicodedata.normalize("NFC", prompt)
    visible = re.sub(r'“[^”]*”|"[^"]*"|\x60[^\x60]*\x60', lambda m: " " * len(m[0]), prompt)
    folded = "".join(unicodedata.normalize("NFD", c)[0] for c in visible.replace("đ", "d").replace("Đ", "D"))
    return prompt, list(_DIRECTIVE.finditer(folded))


def without_agent_directives(prompt):
    text, matches = _directives(prompt)
    for match in reversed(matches):
        text = text[:match.start()] + " " + text[match.end():]
    return text.strip(" ,;")


def selected_agents(prompt: str, explicit: Optional[str], project_dir: Optional[Path]) -> str:
    if explicit is None:
        _, directives = _directives(prompt)
        matches = set()
        for match in directives:
            if match["dual"]:
                matches.add("DUAL")
            elif match["single"]:
                matches.add("CLAUDE_ONLY" if match["name"].lower() == "claude" else "GEMINI_ONLY")
            else:
                matches.add("AUTO")
        if len(matches) > 1:
            raise ValueError("Có nhiều lựa chọn tác tử. Hãy chọn một chế độ cho ca này.")
        explicit = next(iter(matches), None)
    if explicit is None and project_dir is not None:
        preference = project_dir / ".agent-selection"
        if preference.is_file():
            explicit = preference.read_text(encoding="utf-8-sig").strip()
    choice = (explicit or "AUTO").upper()
    if choice not in AGENT_CHOICES:
        raise ValueError(f"Lựa chọn tác tử phải thuộc {AGENT_CHOICES}")
    return choice
