# -*- coding: utf-8 -*-
"""
run_p2_perception_loop.py — Chạy Chu Trình Perception Loop Thực Nghiệm (P2 Dogfooding)
====================================================================================
Triển khai đúng §1 & §2 của SPEC_P2_MCP_PERCEPTION_LOOP.md:
1. Khởi tạo và gọi công cụ từ mcp_dce_cad_server.py
2. Chu trình Perception Loop: render -> preview -> consume -> validate
3. Đóng băng bằng chứng vĩnh viễn trên đĩa (PNG trụ + Audit JSON + DXF chuẩn)
4. Tính toán mã băm SHA-256 để chuẩn bị bàn giao cho Claude nghiệm thu.
"""

import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

# Đảm bảo UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = Path(__file__).resolve().parents[5]
TOOLS_DIR = ROOT_DIR / ".agents" / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import mcp_dce_cad_server as srv

OUTPUT_DIR = ROOT_DIR / ".agents" / "memory" / "audits" / "skill_dual_agent_bridge" / "gemini"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TARGET_DXF = OUTPUT_DIR / "p2_cad_ground_truth.dxf"
TARGET_PNG = OUTPUT_DIR / "p2_cad_perception_preview.png"
TARGET_JSON = OUTPUT_DIR / "p2_cad_compliance_audit.json"

print("=" * 80)
print("  KHỞI ĐỘNG P2 CAD MCP PERCEPTION LOOP (GEMINI ANTIGRAVITY)")
print("=" * 80)

# 1. BƯỚC 1: Render CAD Plan (sheet KC-02)
print("[1/4] Render CAD Plan mặt bằng kết cấu KC-02...")
render_res = srv.render_cad_plan(sheet_type="KC-02")
assert render_res["status"] == "OK", f"Render thất bại: {render_res}"
temp_dxf_path = Path(render_res["output_dxf"])
print(f"  -> DXF tạm đã tạo: {temp_dxf_path} (kích thước: {temp_dxf_path.stat().st_size} bytes)")

# 2. BƯỚC 2: Render Preview PNG độ nét cao (300 DPI)
print("[2/4] Khởi tạo Perception Preview PNG (300 DPI)...")
preview_res = srv.render_preview(str(temp_dxf_path), dpi=300)
assert preview_res["status"] == "OK", f"Render preview thất bại: {preview_res}"
preview_id = preview_res["preview_id"]
temp_png_path = Path(preview_res["output_png"])
print(f"  -> Preview ID: {preview_id}")
print(f"  -> PNG tạm đã tạo: {temp_png_path} (kích thước: {temp_png_path.stat().st_size} bytes)")

# Đóng băng ảnh PNG về đường dẫn trụ (không bị xóa bởi TTL)
shutil.copy2(temp_png_path, TARGET_PNG)
shutil.copy2(temp_dxf_path, TARGET_DXF)
print(f"  -> Đã đóng băng ảnh PNG trụ tại: {TARGET_PNG}")
print(f"  -> Đã đóng băng DXF trụ tại: {TARGET_DXF}")

# 3. BƯỚC 3: Consume Preview qua Vision Tool & Release Preview
print("[3/4] Soi ảnh qua consume_preview và dọn dẹp token...")
consume_res = srv.consume_preview(preview_id)
print(f"  -> consume_preview thành công: nạp đối tượng ảnh MCP ImageContent ({len(consume_res)} mục)")

# 4. BƯỚC 4: Validate CAD (Profile Physical & 20 Cổng)
print("[4/4] Kiểm toán tự động qua Bộ lọc 8 (validate_cad)...")
audit_res = srv.validate_cad(str(TARGET_DXF), profile="physical")
assert audit_res["status"] == "PASS", f"Validate CAD thất bại: {audit_res}"
with TARGET_JSON.open("w", encoding="utf-8") as fh:
    json.dump(audit_res, fh, ensure_ascii=False, indent=2)
print(f"  -> Đã ghi biên bản kiểm toán tại: {TARGET_JSON}")

# 5. TÍNH TOÁN SHA-256 CHO BẰNG CHỨNG
def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

dxf_hash = sha256(TARGET_DXF)
png_hash = sha256(TARGET_PNG)
json_hash = sha256(TARGET_JSON)

print("\n" + "=" * 80)
print("  TỔNG KẾT BẰNG CHỨNG THỰC NGHIỆM TRÊN ĐĨA (EVIDENCE ON DISK)")
print("=" * 80)
print(f"1. DXF:  {TARGET_DXF.name} | SHA-256: {dxf_hash}")
print(f"2. PNG:  {TARGET_PNG.name} | SHA-256: {png_hash} ({TARGET_PNG.stat().st_size} bytes)")
print(f"3. JSON: {TARGET_JSON.name} | SHA-256: {json_hash}")
print(f"-> Physical Status: {audit_res.get('status')} | Total Entities: {audit_res.get('total_entities')}")
print(f"-> Setting Out Dims: {audit_res.get('graphic_sanity', {}).get('has_setting_out_dims')}")
print(f"-> Solid Hatch: {audit_res.get('graphic_sanity', {}).get('has_concrete_solid_hatch')}")
print(f"-> Standard Frame: {audit_res.get('graphic_sanity', {}).get('has_standard_frame')}")
print("=" * 80)
