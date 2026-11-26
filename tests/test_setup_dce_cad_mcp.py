# -*- coding: utf-8 -*-
"""Machine-local MCP registration — khóa setup_dce_cad_mcp.py.

Mục tiêu: chứng minh quy trình đăng ký dce-cad chỉ ghi vào file config của
tác tử (user-level), giữ server path tuyệt đối của workspace hiện tại và
KHÔNG bao giờ ghi lên Google Drive. Đây là lớp "registration theo máy".
"""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

if hasattr(sys.stdout, "reconfigure") and sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
MODULE_PATH = TOOLS_DIR / "setup_dce_cad_mcp.py"

spec = importlib.util.spec_from_file_location("setup_dce_cad_mcp", MODULE_PATH)
setup_mcp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup_mcp)


class SetupDceCadMcpTests(unittest.TestCase):
    def test_installs_into_user_config_not_drive(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = Path(tmp) / "antigravity" / "mcp_config.json"
            changed = setup_mcp.install(cfg)
            self.assertTrue(changed)
            data = json.loads(cfg.read_text(encoding="utf-8-sig"))
            entry = data["mcpServers"]["dce-cad"]
            self.assertEqual(entry["command"], "py")
            # Runtime chuẩn đa máy: py -3 (tránh khóa cứng py -3.12 gây lỗi trên máy dùng 3.11)
            self.assertIn("-3", entry["args"])
            self.assertNotIn("-3.12", entry["args"])
            # Server path phải tuyệt đối trỏ .agents/tools thật (workspace hiện tại)
            server_arg = entry["args"][-1]
            self.assertTrue(Path(server_arg).is_absolute(), server_arg)
            self.assertEqual(Path(server_arg).name, "mcp_dce_cad_server.py")
            # Config nằm trong thư mục tạm (mô phỏng user-level), KHÔNG nằm trên Drive
            self.assertTrue(cfg.is_relative_to(Path(tmp)))
            self.assertFalse("Google AI Studio" in str(cfg.parent))

    def test_install_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = Path(tmp) / "antigravity" / "mcp_config.json"
            first = setup_mcp.install(cfg)
            second = setup_mcp.install(cfg)
            self.assertTrue(first)
            self.assertFalse(second, "Lần 2 phải không thay đổi (idempotent)")

    def test_merges_preserved_user_env(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = Path(tmp) / "antigravity" / "mcp_config.json"
            # Người dùng đã có ODA path local trong env
            setup_mcp.install(cfg)
            existing = json.loads(cfg.read_text(encoding="utf-8-sig"))
            existing["mcpServers"]["dce-cad"]["env"]["ODA_FILE_CONVERTER"] = r"C:\Local\ODA\ODAFileConverter.exe"
            cfg.write_text(json.dumps(existing, ensure_ascii=False), encoding="utf-8")
            setup_mcp.install(cfg)
            data = json.loads(cfg.read_text(encoding="utf-8-sig"))
            # ODA local do người dùng đặt phải được giữ, không bị template đè
            self.assertEqual(data["mcpServers"]["dce-cad"]["env"]["ODA_FILE_CONVERTER"],
                             r"C:\Local\ODA\ODAFileConverter.exe")
            # Các env standard vẫn được giữ từ template
            self.assertEqual(data["mcpServers"]["dce-cad"]["env"]["PYTHONDONTWRITEBYTECODE"], "1")


if __name__ == "__main__":
    unittest.main(verbosity=2)
