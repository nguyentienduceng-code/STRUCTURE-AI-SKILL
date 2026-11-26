"""Install the workspace DCE CAD MCP server in Antigravity's user config."""

import sys
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

import argparse
import json
import os
import tempfile
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parent
DEFAULT_CONFIG = Path.home() / ".gemini" / "antigravity" / "mcp_config.json"


def install(config_path: Path) -> bool:
    template = json.loads((TOOLS_DIR / "mcp_config.json").read_text(encoding="utf-8"))
    registration = template["mcpServers"]["dce-cad"]
    server_path = (TOOLS_DIR / registration["args"][-1]).resolve(strict=True)
    registration["args"][-1] = str(server_path)

    try:
        config = json.loads(config_path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        config = {}
    if not isinstance(config, dict):
        raise ValueError("MCP config must contain a JSON object.")
    servers = config.setdefault("mcpServers", {})
    if not isinstance(servers, dict):
        raise ValueError("mcpServers must contain a JSON object.")
    current = servers.get("dce-cad", {})
    if not isinstance(current, dict) or not isinstance(current.get("env", {}), dict):
        raise ValueError("The existing dce-cad entry and its env must be JSON objects.")
    updated = {**current, **registration}
    updated["env"] = {**current.get("env", {}), **registration["env"]}
    if updated == current:
        return False
    servers["dce-cad"] = updated

    config_path.parent.mkdir(parents=True, exist_ok=True)
    pending = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=config_path.parent, prefix=".dce-cad-", suffix=".tmp", delete=False
        ) as stream:
            pending = Path(stream.name)
            stream.write((json.dumps(config, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(pending, config_path)
    finally:
        if pending is not None:
            pending.unlink(missing_ok=True)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG, help=f"Default: {DEFAULT_CONFIG}")
    args = parser.parse_args()
    config_path = args.config.expanduser().resolve()
    try:
        changed = install(config_path)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"DCE CAD MCP setup failed: {exc}\n")
    print(f"{'Registered' if changed else 'Already registered'} dce-cad in {config_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
