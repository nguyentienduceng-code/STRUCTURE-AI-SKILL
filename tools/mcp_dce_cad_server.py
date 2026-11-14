# -*- coding: utf-8 -*-
"""
mcp_dce_cad_server.py — DCE CAD-BIM MCP Adapter (Giai đoạn 2, RFC §5/§6)
=======================================================================

Máy chủ MCP (stdio, JSON-RPC) bọc NẸT MỎNG quanh engine CAD DCE Pro có sẵn
của `.agents/` — KHÔNG đụng vào code lõi. Đúng triết lý RFC: "MCP làm giao
diện, engine DCE làm thực chất".

5 CAD tools + 2 preview lifecycle tools (Virtual Drive Guard):

    1. render_cad_plan     -> cad_plan_engine.export_dce_plan(...)  [DcePlanEngine]
    2. render_preview      -> dce_render_preview.render_dxf_to_png(...)
    3. validate_cad        -> dce_cad_compliance_checker.audit_dxf_compliance(...)
    4. edit_entity         -> cad_edit_workbench.CadEditSession(...)
    5. convert_to_dwg      -> ODA File Converter (chưa cài => UNAVAILABLE)

Nguyên tắc từ starter kit (RFC §6.2):
    - dryRun: render_cad_plan chỉ build trong bộ nhớ; edit_entity không commit
      MOVE. Nếu truyền source_dxf, thao tác IMPORT vẫn tạo phiên local và trả
      file_written=True để phản ánh đúng I/O.
    - convert_to_dwg CHƯA có ODA trên máy => degrade an toàn trả
      UNAVAILABLE + hướng dẫn, KHÔNG hard-depend (RFC §5.2.2).

Tương thích SDK: chạy được trên mcp 1.x (FastMCP) VÀ mcp 2.x (MCPServer,
đã đổi tên). Máy hiện tại: mcp 2.3.0.

Yêu cầu (đã có trên máy): ezdxf 1.4.x, matplotlib, mcp.
GHI CHÚ: tool `edit_entity` là revision-locked (optimistic locking) — schema
bắt buộc nhận + trả về `revision`; CẤM bỏ trường này (RFC §5.2.4).
"""

import sys
sys.dont_write_bytecode = True
import os
import json
import asyncio
import shutil
import importlib.util
import base64
from pathlib import Path
from typing import Optional

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from dce_virtual_drive_guard import (
    configure_runtime, session_path, cleanup_preview, consume_preview_bytes,
)

SCRATCH_ROOT = configure_runtime()
from mcp.types import ImageContent

# ---------------------------------------------------------------------------
# 0. Đường dẫn tuyệt đối (AGENTS.md §1) — trỏ về .agents/ thật
# ---------------------------------------------------------------------------
AGENTS = Path(__file__).resolve().parent.parent
CPE    = AGENTS / "skills" / "Technical_Illustrator" / "cad_integration" / "cad_plan_engine.py"
CHECK  = AGENTS / "skills" / "SKILL_VERIFY" / "scripts" / "dce_cad_compliance_checker.py"
WORK   = AGENTS / "tools" / "cad_edit_workbench.py"
PREV   = AGENTS / "tools" / "dce_render_preview.py"
ODA_EXE = os.environ.get(
    "ODA_FILE_CONVERTER",
    r"C:\Program Files\ODA\ODA File Converter\ODAFileConverter.exe",
)
# Thư mục mặc định cho session edit + preview (scratch, không ghi đè bản vẽ gốc)
_EDIT_ROOT_DEFAULT = SCRATCH_ROOT / "sessions"


def _load(path: Path, modname: str):
    """Nạp module theo đường dẫn tuyệt đối (cross-skill, không phải package)."""
    spec = importlib.util.spec_from_file_location(modname, str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Không nạp được module: {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# 1. Tạo server (tương thích mcp 1.x / 2.x)
# ---------------------------------------------------------------------------
def _make_server():
    try:  # mcp 2.x
        from mcp.server.mcpserver import MCPServer
        return MCPServer("dce-cad", title="DCE CAD-BIM MCP Adapter",
                          description="MCP adapter mỏng bọc engine CAD DCE Pro (.agents/)")
    except (ImportError, ModuleNotFoundError):
        pass
    try:  # mcp 1.x
        from mcp.server.fastmcp import FastMCP
        return FastMCP("dce-cad")
    except Exception as e:  # pragma: no cover
        raise SystemExit(
            "[E002] Chưa cài mcp SDK. Chạy:  python -m pip install 'mcp'  "
            f"(lỗi: {e})"
        )


SERVER = _make_server()
_tool = SERVER.tool  # decorator

# ---------------------------------------------------------------------------
# 2. Tools
# ---------------------------------------------------------------------------
@_tool()
def render_cad_plan(
    sheet_type: str = "KC-02",
    output_dxf_path: str = "",
    template_path: Optional[str] = None,
    pdf_path: Optional[str] = None,
    model_json_path: Optional[str] = None,
    dry_run: bool = False,
) -> dict:
    """Sinh bản vẽ mặt bằng CAD chuẩn DCE Pro (khung A1, 4 tầng dim, hatch,
    bảng thống kê — Điều 12d).

    sheet_type: "KC-01" (tổng mặt bằng) / "KC-02" (định vị cột vách) /
    "KC-03" (dầm sàn). model_json_path: handoff JSON; để trống => model mặc định.
    dry_run=True: build trong bộ nhớ, KHÔNG ghi file (chống bừa, xem trước).
    """
    cpe = _load(CPE, "dce_cpe")
    out = Path(output_dxf_path or str(AGENTS / "output" / f"dce_{sheet_type}.dxf"))

    if dry_run:
        # Build engine trong bộ nhớ, render nhưng KHÔNG save (nguyên tắc dryRun)
        model = cpe.build_structural_model()
        if model_json_path and os.path.isfile(model_json_path):
            model = json.loads(Path(model_json_path).read_text(encoding="utf-8"))
        t = Path(template_path) if template_path else None
        eng = cpe.DcePlanEngine(model=model, template_path=t)
        eng.setup()
        st = sheet_type.upper()
        if st in ("KC-01", "KC01", "MASTER", "TONG_THE"):
            eng.render_sheet_kc01()
        elif st in ("KC-03", "KC03", "DAM_SAN", "BEAMS"):
            eng.render_sheet_kc03()
        else:
            eng.render_sheet_kc02()
        msp = eng.doc.modelspace()
        return {
            "status": "DRY_RUN_OK",
            "sheet_type": sheet_type,
            "would_save_to": str(out),
            "modelspace_entities": sum(1 for _ in msp),
            "layers": len(eng.doc.layers),
            "file_written": False,
        }

    eng = cpe.export_dce_plan(str(out), template_path=template_path,
                              pdf_path=pdf_path, sheet_type=sheet_type,
                              model_json_path=model_json_path)
    return {
        "status": "OK",
        "sheet_type": sheet_type,
        "output_dxf": str(out),
        "verified_file_exists": out.is_file(),
        "file_bytes": out.stat().st_size if out.is_file() else 0,
    }


@_tool()
def render_preview(
    dxf_path: str,
    out_png: str = "",
    dpi: int = 150,
    layout: str = "Model",
    view_box: Optional[list] = None,
) -> dict:
    """Render DXF -> PNG độ phân giải cao (Vision Perception Loop, RFC §5.2.1).

    dpi: preview 150-200 (nhanh), in/Word 300. view_box: [minx,miny,maxx,maxy]
    (mm) để crop vùng; None => render toàn layout (qsave, nhanh nhất).
    """
    prev = _load(PREV, "dce_render_preview")
    vb = tuple(float(v) for v in view_box) if view_box else None
    return prev.render_dxf_to_png(dxf_path, out_png, dpi=dpi,
                                  layout_name=layout, view_box=vb)


@_tool()
def consume_preview(preview_id: str) -> list[ImageContent]:
    """Nhận ảnh để Vision kiểm tra; tự xóa PNG local sau khi nạp đủ vào response.

    Gọi sau render_preview bằng preview_id trả về. Ảnh nằm trong response,
    không còn phụ thuộc file local. Token chỉ dùng một lần.
    """
    data = consume_preview_bytes(preview_id)
    return [ImageContent(type="image", data=base64.b64encode(data).decode('ascii'),
                         mimeType="image/png")]


@_tool()
def release_preview(preview_id: str) -> dict:
    """Dọn PNG sau khi client đọc output_png trực tiếp hoặc hủy lượt Vision."""
    return cleanup_preview(preview_id)


@_tool()
def validate_cad(dxf_path: str) -> dict:
    """Chạy Bộ lọc 8 (kiểm toán Điều 12d) trên 1 file DXF.
    Trả status: PASS/FAIL + graphic_sanity (hatch, khung, bảng thống kê,
    setout, va chạm dầm-lỗ)."""
    chk = _load(CHECK, "dce_checker")
    return chk.audit_dxf_compliance(dxf_path)


@_tool()
def edit_entity(
    session_dir: str = "",
    source_dxf: str = "",
    handle: Optional[str] = None,
    dx: float = 0.0,
    dy: float = 0.0,
    expected_revision: Optional[str] = None,
    dry_run: bool = True,
) -> dict:
    """Sửa TEXT/MTEXT/DIMENSION trên BẢN SAO (không ghi đè bản vẽ gốc).

    Revision-locked: luôn truyền `expected_revision` (lấy từ inspect) và nhận
    về `revision` mới. dry_run=True (mặc định): chỉ inspect + preview diff,
    KHÔNG commit (nguyên tắc dryRun của kit C). Chỉ TEXT/MTEXT/DIMENSION
    phẳng; INSERT/ATTRIB/paper-space không hỗ trợ.
    source_dxf tạo bản sao phiên local kể cả khi dry_run=True; trả session_dir
    thực tế để tiếp tục phiên. Phiên không bị cơ chế TTL preview xóa.
    """
    work = _load(WORK, "dce_workbench")
    root = session_path(session_dir)
    if source_dxf:
        sess = work.CadEditSession.create(source_dxf, root)
    else:
        if not root.joinpath("HEAD.json").is_file():
            return {"status": "E002",
                    "error": "Session chưa tồn tại; truyền source_dxf trước.",
                    "suggestion": "Gọi lại với source_dxf để IMPORT."}
        sess = work.CadEditSession(str(root))

    view = sess.inspect()  # đọc HEAD, an toàn cả khi dry_run

    if dry_run:
        return {"status": "DRY_RUN_OK", "file_written": bool(source_dxf),
                "session_dir": str(root), "revision": view["revision"],
                "would_apply": {"handle": handle, "dx": dx, "dy": dy},
                "expected_revision": expected_revision,
                "current": view}

    # commit thật
    if not handle:
        return {"status": "E001", "error": "--handle required để commit MOVE."}
    new_rev = sess.move(handle, dx, dy, expected_revision=expected_revision or view["revision"])
    view = sess.inspect()
    return {"status": "OK", "file_written": True,
            "session_dir": str(root),
            "revision": new_rev, "drawing": view["drawing"]}


@_tool()
def convert_to_dwg(dxf_path: str, out_dwg: str = "") -> dict:
    """DXF -> DWG qua ODA File Converter (nếu đã cài).
    Chưa cài => degrade an toàn trả UNAVAILABLE + hướng dẫn (RFC §5.2.2),
    KHÔNG hard-depend."""
    if not os.path.isfile(ODA_EXE):
        return {"status": "UNAVAILABLE",
                "reason": f"ODA File Converter không tìm thấy tại {ODA_EXE}",
                "suggestion": ("Cài ODA File Converter (miễn phí, Open Design "
                               "Alliance) rồi set env ODA_FILE_CONVERTER nếu "
                               "đặt khác vị trí."),
                "fallback": "Giao file .dxf trực tiếp (mở được mọi AutoCAD)."}
    dst = Path(out_dwg or str(Path(dxf_path).with_suffix(".dwg")))
    dst.parent.mkdir(parents=True, exist_ok=True)
    # ODA batch mode: ODAFileConverter <inpath> <outpath> <version> [infmt] [outfmt]
    # version 0 => ACAD 2018; fmt dxf->dwg
    import subprocess
    try:
        subprocess.run(
            [ODA_EXE, str(dxf_path), str(dst.parent), "0", "dxf", "dwg"],
            check=False, timeout=120, capture_output=True,
        )
    except Exception as e:
        return {"status": "FAIL", "error": str(e)}
    return {"status": "OK" if dst.exists() else "FAIL",
            "output_dwg": str(dst), "verified_file_exists": dst.exists()}


# ---------------------------------------------------------------------------
# 3. Entrypoint
# ---------------------------------------------------------------------------
def main():
    if hasattr(SERVER, "run_stdio_async"):
        # mcp 2.x: MCPServer — coroutine, chạy bằng asyncio
        asyncio.run(SERVER.run_stdio_async())
    elif hasattr(SERVER, "run"):
        # mcp 1.x: FastMCP — method đồng bộ (self-served event loop)
        try:
            SERVER.run(transport="stdio")
        except TypeError:
            SERVER.run()
    else:
        raise SystemExit("[E003] mcp version không tương thích: "
                         "thiếu cả run_stdio_async lẫn run.")


if __name__ == "__main__":
    main()
