# -*- coding: utf-8 -*-
"""
mcp_dce_cad_server.py — DCE CAD-BIM MCP Adapter (Giai đoạn 2, RFC §5/§6)
=======================================================================

Máy chủ MCP (stdio, JSON-RPC) bọc NẸT MỎNG quanh engine CAD DCE Pro có sẵn
của `.agents/` — KHÔNG đụng vào code lõi. Đúng triết lý RFC: "MCP làm giao
diện, engine DCE làm thực chất".

13 tools (danh sách chính xác theo `mcp_config.json` `_note.tools`):

    Render/validate (7):
    1. render_cad_plan         -> cad_plan_engine.export_dce_plan(...)  [DcePlanEngine]
    2. render_preview          -> dce_render_preview.render_dxf_to_png(...)
    3. consume_preview         -> trả ảnh cho Vision + tự dọn PNG (Virtual Drive Guard)
    4. release_preview         -> tự dọn PNG sau khi đọc trực tiếp (Virtual Drive Guard)
    5. validate_cad            -> dce_cad_compliance_checker.audit_dxf_compliance(...)
    6. edit_entity             -> cad_edit_workbench.CadEditSession(...)
    7. resolve_cad_collisions  -> cad_collision_solver (khử va chạm thực thể)
    Convert/layout (2):
    8. convert_to_dwg          -> ODA File Converter (chưa cài => UNAVAILABLE)
    9. auto_layout_and_scale_plan / 10. export_cad_sheet_set -> sheet scale fitter
    P4.1 merge lane (3):
    11. open_form / 12. diff_form / 13. apply_agent_changes

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
import contextlib
import uuid
from pathlib import Path
from typing import Optional, Literal

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from dce_virtual_drive_guard import (
    configure_runtime, session_path, cleanup_preview, consume_preview_bytes, managed_dir,
)

SCRATCH_ROOT = configure_runtime()
from mcp.types import ImageContent

# ---------------------------------------------------------------------------
# 0. Đường dẫn tuyệt đối (AGENTS.md §1) — trỏ về .agents/ thật
# ---------------------------------------------------------------------------
AGENTS = Path(__file__).resolve().parent.parent
CPE    = AGENTS / "skills" / "Technical_Illustrator" / "cad_integration" / "cad_plan_engine.py"
CSS    = AGENTS / "skills" / "Technical_Illustrator" / "cad_integration" / "cad_sheet_set.py"
REG    = AGENTS / "skills" / "Technical_Illustrator" / "cad_integration" / "cad_element_registry.py"
CFC    = AGENTS / "skills" / "Technical_Illustrator" / "cad_integration" / "cad_form_contract.py"
MDF    = AGENTS / "skills" / "Technical_Illustrator" / "cad_integration" / "model_diff.py"
PATCH  = AGENTS / "skills" / "Technical_Illustrator" / "cad_integration" / "cad_form_patcher.py"
POM    = AGENTS / "tools" / "project_ops_manager.py"
CHECK  = AGENTS / "skills" / "SKILL_VERIFY" / "scripts" / "dce_cad_compliance_checker.py"
WORK   = AGENTS / "tools" / "cad_edit_workbench.py"
SOLVER = AGENTS / "tools" / "cad_collision_solver.py"
PREV   = AGENTS / "tools" / "dce_render_preview.py"
ODA_EXE = os.environ.get(
    "ODA_FILE_CONVERTER",
    r"C:\Program Files\ODA\ODA File Converter\ODAFileConverter.exe",
)
# Tầng 2B (solo) — cầu nối native DWG + snapshot diff (kiến trúc 2B đã duyệt).
SNAP_BRIDGE = AGENTS / "tools" / "autocad_snapshot_bridge.py"
# Thư mục mặc định cho session edit + preview (scratch, không ghi đè bản vẽ gốc)
_EDIT_ROOT_DEFAULT = SCRATCH_ROOT / "sessions"


def _load(path: Path, modname: str):
    """Nạp module theo đường dẫn tuyệt đối (cross-skill, không phải package)."""
    if modname in sys.modules:
        return sys.modules[modname]
    spec = importlib.util.spec_from_file_location(modname, str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Không nạp được module: {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[modname] = mod
    try:
        spec.loader.exec_module(mod)
    except Exception:
        sys.modules.pop(modname, None)
        raise
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
    v6: bool = True,
    dry_run: bool = False,
    full_evidence: bool = False,
) -> dict:
    """Sinh bản vẽ mặt bằng CAD chuẩn DCE Pro (khung A1, 4 tầng dim, hatch,
    bảng thống kê — Điều 12d). Chỉ xuất CAD (.dxf), không xuất PDF.

    sheet_type: "KC-01" (tổng mặt bằng) / "KC-02" (định vị cột vách) /
    "KC-03" (dầm sàn). model_json_path: handoff JSON; để trống => model mặc định.
    v6=True (mặc định): bật tag-placement hình học, registry phần tử bất biến
    và ghi sidecar .dce_audit.json. dry_run=True: build trong bộ nhớ, KHÔNG ghi file.
    full_evidence=True: nhúng đầy đủ semantic_log_format v4 vào sidecar .dce_audit.json.
    """
    aliases = {'KC-01': 'KC-01', 'KC01': 'KC-01', 'MASTER': 'KC-01', 'TONG_THE': 'KC-01',
               'KC-02': 'KC-02', 'KC02': 'KC-02', 'COT_VACH': 'KC-02',
               'KC-03': 'KC-03', 'KC03': 'KC-03', 'DAM_SAN': 'KC-03', 'BEAMS': 'KC-03',
               'CUSTOM_MULTIVIEW': 'CUSTOM_MULTIVIEW', 'A3_MULTIVIEW': 'CUSTOM_MULTIVIEW', 'MULTIVIEW_A3': 'CUSTOM_MULTIVIEW'}
    canonical = aliases.get(sheet_type.upper())
    if canonical is None:
        return {'status': 'E001', 'error': f'Unsupported sheet_type: {sheet_type}', 'file_written': False}
    for label, path in (('model_json_path', model_json_path), ('template_path', template_path), ('pdf_path', pdf_path)):
        if path and not Path(path).is_file():
            return {'status': 'E001', 'error': f'{label} does not exist: {path}', 'file_written': False}
    cpe = _load(CPE, "dce_cpe")
    reg_mod = _load(REG, "dce_reg") if v6 else None
    registry = reg_mod.CadElementRegistry(project_name=f"MCP_{canonical}") if reg_mod else None
    # Output names are hints. Never overwrite a source/template or write scratch to Drive.
    out = managed_dir('temp') / (uuid.uuid4().hex + '.dxf')

    if dry_run:
        # Build engine trong bộ nhớ, render nhưng KHÔNG save (nguyên tắc dryRun)
        with contextlib.redirect_stdout(sys.stderr):
            eng = cpe.export_dce_plan(
                str(out), template_path=template_path, pdf_path=pdf_path,
                sheet_type=canonical, model_json_path=model_json_path,
                v6=v6, element_registry=registry, dry_run=True,
                full_evidence=full_evidence,
            )
        msp = eng.doc.modelspace()
        return {
            "status": "DRY_RUN_OK",
            "sheet_type": sheet_type,
            "v6": v6,
            "full_evidence": full_evidence,
            "would_save_to": str(out),
            "requested_output_dxf": output_dxf_path,
            "modelspace_entities": sum(1 for _ in msp),
            "layers": len(eng.doc.layers),
            "file_written": False,
        }

    # Engine diagnostics must not corrupt the MCP JSON-RPC stdout stream.
    with contextlib.redirect_stdout(sys.stderr):
        eng = cpe.export_dce_plan(
            str(out), template_path=template_path, pdf_path=pdf_path,
            sheet_type=canonical, model_json_path=model_json_path,
            v6=v6, element_registry=registry, full_evidence=full_evidence,
        )
        if v6 and not out.with_suffix(".dce_audit.json").exists() and hasattr(eng, "_v6_write_sidecar"):
            eng._v6_write_sidecar(str(out))
    return {
        "status": "OK",
        "sheet_type": sheet_type,
        "v6": v6,
        "full_evidence": full_evidence,
        "output_dxf": str(out),
        "input_pdf": pdf_path,
        "requested_output_dxf": output_dxf_path,
        "file_written": out.is_file(),
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
def validate_cad(dxf_path: str, profile: Literal['full', 'plan', 'physical', 'steel_peb', 'bptc'] = 'full',
                 beam_dxf_path: Optional[str] = None, colwall_dxf_path: Optional[str] = None) -> dict:
    """Bộ lọc 8: hỗ trợ 5 profile (full, plan, physical, steel_peb, bptc) / 25 cổng G8.01..G8.25.
    full mặc định yêu cầu 20 cổng BTCT và bằng chứng chi tiết; steel_peb/bptc mở rộng
    lên G8.21..G8.25. plan: 16 cổng mặt bằng, 4 cổng chi tiết N/A. physical: chỉ kiểm tra DXF.
    Thiếu/stale metadata SHA256 => NEEDS_REVIEW. Đọc status, profile,
    gate_results và full_compliance_verified; physical PASS không phải tuân thủ đầy đủ.
    Không sửa DXF; trả PASS/FAIL/NEEDS_REVIEW/ERROR.
    """
    chk = _load(CHECK, "dce_checker")
    return chk.audit_dxf_compliance(dxf_path, profile, beam_dxf_path, colwall_dxf_path)


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
    if not dry_run and (not handle or not expected_revision):
        return {'status': 'E001', 'error': 'Commit requires handle and expected_revision.', 'file_written': False}
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
    new_rev = sess.move(handle, dx, dy, expected_revision=expected_revision)
    view = sess.inspect()
    return {"status": "OK", "file_written": True,
            "session_dir": str(root),
            "revision": new_rev, "drawing": view["drawing"]}


@_tool()
def resolve_cad_collisions(
    dxf_path: str,
    output_dxf: str = "",
    dry_run: bool = False,
) -> dict:
    """Tự động phát hiện và giải quyết xung đột đè chữ trong bản vẽ CAD (Sprint 2).

    Sử dụng thuật toán tìm kiếm hướng tâm (8 hướng) và hàm mục tiêu khoảng cách/vật cản.
    Tự động sinh Leader Line (đường chỉ dẫn) nếu nhãn bị dời > 300mm.
    dry_run=True: chỉ trả về danh sách va chạm và kế hoạch dời, KHÔNG sửa file.
    dry_run=False: áp dụng dời nhãn và lưu file kết quả.
    """
    solver_mod = _load(SOLVER, "cad_solver")
    if not os.path.isfile(dxf_path):
        return {"status": "E001", "error": f"Không tìm thấy file DXF tại: {dxf_path}"}
    solver = solver_mod.CadCollisionSolver.from_dxf(dxf_path)
    from dce_virtual_drive_guard import managed_dir
    import uuid
    target = managed_dir("temp") / (uuid.uuid4().hex + ".dxf") if not dry_run else None
    res = solver.solve_all(dry_run=dry_run, output_path=target)
    res["requested_output_dxf"] = output_dxf
    res["file_written"] = bool(res.get("output_dxf"))
    return res


@_tool()
def convert_to_dwg(dxf_path: str, out_dwg: str = "") -> dict:
    """DXF -> DWG qua ODA File Converter (nếu đã cài).
    Chưa cài => degrade an toàn trả UNAVAILABLE + hướng dẫn (RFC §5.2.2),
    KHÔNG hard-depend.
    Đã được sandbox hoá hoàn toàn qua VirtualDriveGuard và scratch local:
    - Đầu vào DXF được cô lập trên ổ NTFS cục bộ (C:/D:)
    - ODA subprocess chỉ thao tác trong thư mục scratch cô lập
    - Kết quả DWG được kiểm tra và chuyển an toàn về đích đến mong muốn
    """
    if not os.path.isfile(ODA_EXE):
        return {"status": "UNAVAILABLE",
                "reason": f"ODA File Converter không tìm thấy tại {ODA_EXE}",
                "suggestion": ("Cài ODA File Converter (miễn phí, Open Design "
                               "Alliance) rồi set env ODA_FILE_CONVERTER nếu "
                               "đặt khác vị trí."),
                "fallback": "Giao file .dxf trực tiếp (mở được mọi AutoCAD)."}

    safe_dxf = Path(dxf_path).resolve()
    if not safe_dxf.is_file():
        return {"status": "E001", "error": f"Không tìm thấy file DXF tại: {dxf_path}"}
    if safe_dxf.suffix.lower() != ".dxf":
        return {"status": "E001", "error": f"File không có định dạng .dxf: {dxf_path}"}

    # Sandbox qua Virtual Drive Guard scratch C:/D:
    job_id = uuid.uuid4().hex
    conv_in = managed_dir("temp") / f"oda_in_{job_id}"
    conv_out = managed_dir("temp") / f"oda_out_{job_id}"
    conv_in.mkdir(parents=True, exist_ok=True)
    conv_out.mkdir(parents=True, exist_ok=True)

    try:
        isolated_dxf = conv_in / safe_dxf.name
        shutil.copy2(safe_dxf, isolated_dxf)

        # ODA batch mode: ODAFileConverter <inpath> <outpath> <version> [infmt] [outfmt]
        # version 0 => ACAD 2018; fmt dxf->dwg
        import subprocess
        proc = subprocess.run(
            [ODA_EXE, str(conv_in), str(conv_out), "0", "dxf", "dwg"],
            check=False, timeout=120, capture_output=True,
        )

        expected_dwg = conv_out / safe_dxf.with_suffix(".dwg").name
        if not expected_dwg.is_file():
            # Thử tìm file .dwg bất kỳ trong conv_out
            dwgs = list(conv_out.glob("*.dwg"))
            expected_dwg = dwgs[0] if dwgs else None

        if not expected_dwg or not expected_dwg.is_file():
            stderr_msg = proc.stderr.decode("utf-8", errors="replace") if proc.stderr else ""
            return {"status": "FAIL", "error": f"ODA không sinh được file DWG. {stderr_msg}".strip()}

        if out_dwg:
            dst = Path(out_dwg).resolve()
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(expected_dwg, dst)
            final_dwg = dst
        else:
            saved_dwg = managed_dir("temp") / f"{safe_dxf.stem}_{job_id[:8]}.dwg"
            shutil.copy2(expected_dwg, saved_dwg)
            final_dwg = saved_dwg

        return {
            "status": "OK",
            "output_dwg": str(final_dwg),
            "requested_output_dwg": out_dwg or str(Path(dxf_path).with_suffix(".dwg")),
            "verified_file_exists": final_dwg.exists(),
            "file_bytes": final_dwg.stat().st_size if final_dwg.exists() else 0,
        }
    except Exception as e:
        return {"status": "FAIL", "error": str(e)}
    finally:
        shutil.rmtree(conv_in, ignore_errors=True)
        shutil.rmtree(conv_out, ignore_errors=True)


# ---------------------------------------------------------------------------
# 2B (solo) — Native DWG snapshot + D1/D1A diff (AutoCAD 2021 Core Console)
# ---------------------------------------------------------------------------
# Bọc MỎNG `autocad_snapshot_bridge` (out-of-process, read-only, staging + SHA
# bất biến). Thiếu Core Console/plugin => UNAVAILABLE trung thực (KHÔNG báo
# "native pass"). DXF lane (ezdxf) vẫn chạy độc lập song song.

@_tool()
def native_dwg_snapshot(dwg_path: str, out_json: str = "", revision: str = "") -> dict:
    """Chụp snapshot chính tắc mm từ 1 DWG native (AutoCAD 2021 Core Console,
    read-only). Trả SHA-256 bất biến + fingerprint + counts.

    Chạy ngoài tiến trình: copy staging + accoreconsole + plugin .NET DCE_SNAPSHOT.
    Thiếu accoreconsole/plugin => UNAVAILABLE + hướng dẫn (không bịa "native pass").
    out_json (tùy chọn): ghi snapshot đầy đủ ra đường dẫn này.
    """
    bridge = _load(SNAP_BRIDGE, "dce_snap_bridge")
    tc = bridge.detect_toolchain()
    if not tc.get("native_ready"):
        return {"status": "UNAVAILABLE", "toolchain": tc,
                "reason": ("accoreconsole.exe / plugin DCE snapshot chưa sẵn trên host. "
                           "Đường DXF (ezdxf) vẫn chạy độc lập; không quy thành native pass."),
                "suggestion": "Cài AutoCAD 2021 + build plugin (autocad_snapshot_bridge build).",
                "file_written": False}
    src = Path(dwg_path)
    if not src.is_file():
        return {"status": "E001", "error": f"Không tìm thấy file DWG tại: {dwg_path}"}
    res = bridge.run_snapshot(str(src), revision=revision)
    if out_json and res.get("snapshot"):
        bridge.snap.dump_snapshot(res["snapshot"], out_json)
    snap = res.get("snapshot") or {}
    return {
        "status": res["status"],
        "error": res.get("error"),
        "immutability_ok": res.get("immutability_ok"),
        "source_sha256": res.get("source_hash_before"),
        "record_counts": snap.get("counts"),
        "fingerprint": snap.get("fingerprint"),
        "complete": snap.get("completion", {}).get("complete") if snap else None,
        "snapshot_written": out_json if (out_json and res.get("snapshot")) else None,
    }


@_tool()
def native_dwg_diff(dwg_a: str, dwg_b: str, rev_a: str = "A", rev_b: str = "B") -> dict:
    """So 2 DWG native (A cơ sở, B ứng viên) theo element_id (D1/D1A).

    Trả report diff (added/removed/changed + decision classes) + verdict
    out-of-scope. Thiếu toolchain native => UNAVAILABLE trung thực.
    """
    bridge = _load(SNAP_BRIDGE, "dce_snap_bridge")
    tc = bridge.detect_toolchain()
    if not tc.get("native_ready"):
        return {"status": "UNAVAILABLE", "toolchain": tc,
                "reason": "accoreconsole.exe / plugin DCE snapshot chưa sẵn trên host.",
                "suggestion": "Cài AutoCAD 2021 + build plugin (autocad_snapshot_bridge build)."}
    dres = bridge.diff_revisions(str(dwg_a), str(dwg_b), rev_a=rev_a, rev_b=rev_b)
    if dres.get("status") != "OK":
        return {"status": dres.get("status"), "error": dres.get("error"),
                "a_sha256": dres.get("a_hash"), "b_sha256": dres.get("b_hash")}
    report = dres["diff"]
    import native_dwg_diff as diff_mod
    decision = diff_mod.d1d1a_decision(report)
    return {
        "status": "OK",
        "overall": report.get("overall"),
        "summary": report.get("summary"),
        "changes": report.get("changes"),
        "issues": report.get("issues"),
        "decision": decision,
        "a_sha256": dres.get("a_hash"), "b_sha256": dres.get("b_hash"),
    }


# ---------------------------------------------------------------------------
# 3. Tool mới — Dynamic Sheet-Scale Governor (Directive v5.0, Nhiệm vụ 3)
# ---------------------------------------------------------------------------
SSF    = AGENTS / "tools" / "sheet_scale_fitter.py"
VRDR   = AGENTS / "skills" / "Technical_Illustrator" / "cad_integration" / "cad_vector_renderer.py"


@_tool()
def auto_layout_and_scale_plan(
    json_model_path: str = "",
    target_sheet: str = "A1",
    force_scale: Optional[int] = None,
    sheet_type: str = "KC-02",
    output_dxf_path: str = "",
    render_dpi: int = 300,
    render_preview_png: bool = False,
    v6: bool = True,
    dry_run: bool = False,
) -> dict:
    """Pipeline "Dynamic Sheet-Scale Governor & SSOT Layout" (CAD-first, không tự xuất PDF):

    1) Đọc mô hình JSON SSOT (json_model_path; để trống => model chuẩn).
    2) Chạy SheetScaleSolver (tools/sheet_scale_fitter.py) tự tính khổ giấy
       (A2/A1/A0) + tỷ lệ S theo fill-ratio-window [0.65, 0.85].
    3) Sinh DXF AC1021 chuẩn DCE Pro theo tỷ lệ S (bật v6=True mặc định).
    4) Chỉ kết xuất PNG khi render_preview_png=True (mặc định False để ưu tiên CAD).
    5) Thẩm tra Bộ lọc 8 (20 cổng G8.01-G8.20, profile 'full') + physical.
    Output luôn cô lập local (Virtual Drive Guard), không ghi Drive.
    """
    import uuid as _uuid

    if json_model_path and not Path(json_model_path).is_file():
        return {"status": "E001", "error": f"model JSON not found: {json_model_path}"}
    if force_scale is not None and force_scale not in [50, 75, 100, 125, 150, 200, 250]:
        return {"status": "E001", "error": f"force_scale {force_scale} không thuộc tập TCVN [50..250]"}
    if target_sheet.upper() not in ("A2", "A1", "A0"):
        return {"status": "E001", "error": f"target_sheet phải là A2/A1/A0, nhận: {target_sheet}"}

    ssf = _load(SSF, "dce_ssf")
    cpe = _load(CPE, "dce_cpe")

    # (1) Đọc SSOT model
    if json_model_path:
        model = json.loads(Path(json_model_path).read_text(encoding="utf-8"))
    else:
        model = cpe.build_structural_model()

    fp = model.get("footprint_bbox_mm")
    if fp and len(fp) == 4:
        fp_w = float(fp[2]) - float(fp[0])
        fp_h = float(fp[3]) - float(fp[1])
    else:
        fp_w = float(model["L_total"]) * 1000.0
        fp_h = float(model["B_total"]) * 1000.0
    if fp_w <= 0 or fp_h <= 0:
        return {"status": "E001", "error": "Footprint không hợp lệ (<=0)"}

    # (2) SheetScaleSolver
    decision = ssf.SheetScaleSolver().solve(fp_w, fp_h, target_sheet=target_sheet.upper(),
                                            force_scale=float(force_scale) if force_scale else None)
    scale_spec = decision.as_dict()

    out = managed_dir("temp") / (_uuid.uuid4().hex + ".dxf")
    if dry_run:
        return {
            "status": "DRY_RUN_OK",
            "file_written": False,
            "pdf_generated": False,
            "footprint_mm": {"w": fp_w, "h": fp_h},
            "decision": scale_spec,
            "would_generate": [str(out), "Bộ lọc 8 (20 cổng)"],
        }

    # (3) Sinh DXF chuẩn DCE Pro theo tỷ lệ S
    reg_mod = _load(REG, "dce_reg") if v6 else None
    registry = reg_mod.CadElementRegistry(project_name=f"MCP_AUTO_{sheet_type.upper()}") if reg_mod else None
    with contextlib.redirect_stdout(sys.stderr):
        eng = cpe.export_dce_plan(
            str(out), sheet_type=sheet_type, model_json_path=json_model_path or None,
            dry_run=False, scale_spec=scale_spec, v6=v6, element_registry=registry,
        )
        if v6 and not out.with_suffix(".dce_audit.json").exists() and hasattr(eng, "_v6_write_sidecar"):
            eng._v6_write_sidecar(str(out))
    dxf_ok = out.is_file()

    # (4) PNG chỉ render khi yêu cầu rõ render_preview_png=True (CAD-first, không tự xuất PDF)
    if render_preview_png:
        prev = _load(PREV, "dce_render_preview")
        png_res = prev.render_dxf_to_png(str(out), "", dpi=int(render_dpi))
        png_info = {
            "status": png_res.get("status"),
            "output_png": png_res.get("output_png"),
            "preview_id": png_res.get("preview_id"),
            "dpi": png_res.get("dpi"),
            "vision_tool": "consume_preview",
        }
    else:
        png_info = {"status": "SKIPPED", "reason": "CAD-first default; truyền render_preview_png=True hoặc gọi render_preview nếu cần kiểm tra ảnh."}

    # (5) Bộ lọc 8 — 20 cổng G8.01-G8.20 (profile full) + physical
    chk = _load(CHECK, "dce_checker")
    full = chk.audit_dxf_compliance(str(out), "full")
    physical = chk.audit_dxf_compliance(str(out), "physical")

    return {
        "status": "OK" if dxf_ok else "FAIL",
        "file_written": dxf_ok,
        "output_dxf": str(out),
        "v6": v6,
        "pdf_generated": False,
        "footprint_mm": {"w": fp_w, "h": fp_h},
        "decision": {
            "sheet_size": decision.sheet_size,
            "scale_label": decision.scale_label,
            "fill_ratio": decision.fill_ratio,
            "in_fill_band": decision.in_fill_band,
            "dimstyle": [k for k in decision.dimstyle_params if "MV" in k][0]
                        if decision.dimstyle_params else None,
            "tier_dist_mm": decision.tier_dist_mm,
            "forced": force_scale is not None,
        },
        "png": png_info,
        "gates": {"full": full.get("status"), "gates_unverified": full.get("gates_unverified"),
                   "physical": physical.get("status"),
                   "full_compliance_verified": full.get("full_compliance_verified")},
    }


@_tool()
def export_cad_sheet_set(
    model_json_path: Optional[str] = None,
    sheet_types: Optional[list[str]] = None,
    target_sheet: str = "A1",
    force_scale: Optional[int] = None,
    auto_scale: bool = False,
    render_preview: bool = False,
    export_pdf: bool = False,
    dry_run: bool = False,
) -> dict:
    """Xuất bộ bản vẽ CAD đồng bộ qua engine thật (`DcePlanEngine` v6 + Master Template + Registry).

    Mục tiêu mặc định: CHỈ xuất file CAD (.dxf), sidecar (.dce_audit.json) và
    `project_element_registry.json`. KHÔNG tự xuất PDF (`export_pdf=False`) hay PNG
    (`render_preview=False`) trừ khi người dùng ghi chú yêu cầu.
    """
    if model_json_path and not Path(model_json_path).is_file():
        return {"status": "E001", "error": f"model_json_path không tồn tại: {model_json_path}", "file_written": False}
    if force_scale is not None and force_scale not in [50, 75, 100, 125, 150, 200, 250]:
        return {"status": "E001", "error": f"force_scale {force_scale} không thuộc TCVN [50..250]", "file_written": False}
    if target_sheet.upper() not in ("A2", "A1", "A0"):
        return {"status": "E001", "error": f"target_sheet phải là A2/A1/A0, nhận: {target_sheet}", "file_written": False}

    aliases = {"KC-01": "KC-01", "KC01": "KC-01", "KC-02": "KC-02", "KC02": "KC-02", "KC-03": "KC-03", "KC03": "KC-03"}
    raw_sheets = sheet_types or ["KC-02", "KC-03"]
    sheets: list[str] = []
    for raw in raw_sheets:
        c = aliases.get(str(raw).upper())
        if c is None:
            return {"status": "E001", "error": f"Unsupported sheet_type in sheet_types: {raw}", "file_written": False}
        sheets.append(c)

    scale_spec = None
    if auto_scale or force_scale is not None or target_sheet.upper() != "A1":
        cpe = _load(CPE, "dce_cpe")
        ssf = _load(SSF, "dce_ssf")
        model = json.loads(Path(model_json_path).read_text(encoding="utf-8")) if model_json_path else cpe.build_structural_model()
        fp = model.get("footprint_bbox_mm")
        if fp and len(fp) == 4:
            fp_w, fp_h = float(fp[2]) - float(fp[0]), float(fp[3]) - float(fp[1])
        else:
            fp_w, fp_h = float(model["L_total"]) * 1000.0, float(model["B_total"]) * 1000.0
        decision = ssf.SheetScaleSolver().solve(
            fp_w, fp_h, target_sheet=target_sheet.upper(),
            force_scale=float(force_scale) if force_scale is not None else None,
        )
        scale_spec = decision.as_dict()

    out_dir = managed_dir("temp") / f"sheet_set_{uuid.uuid4().hex[:10]}"
    if dry_run:
        return {
            "status": "DRY_RUN_OK",
            "file_written": False,
            "pdf_generated": False,
            "output_dir": str(out_dir),
            "sheets": sheets,
            "scale_spec": scale_spec,
        }

    css = _load(CSS, "dce_css")
    with contextlib.redirect_stdout(sys.stderr):
        res = css.export_project_a3_sheets(
            out_dir,
            model_json_path=model_json_path,
            scale_spec=scale_spec,
            render_previews=render_preview,
            export_pdf=export_pdf,
            sheet_types=tuple(sheets),
        )

    return {
        "status": "OK" if res.get("status") == "PASS" else "FAIL",
        "file_written": bool(res.get("sheets")),
        "output_dir": str(out_dir),
        "sheets": res.get("sheets", []),
        "registry_path": res.get("registry_path", ""),
        "registry_total_elements": res.get("registry_total_elements", 0),
        "manifest_path": res.get("manifest_path", ""),
        "preview_pngs": res.get("preview_pngs", []),
        "pdf_generated": bool(res.get("pdf_path")),
        "pdf_path": res.get("pdf_path", ""),
        "Standard_Method": res.get("Standard_Method", ""),
    }


@_tool()
def open_form(
    project_dir: Optional[str] = None,
    form_id: str = "FORM_02_MULTIVIEW_A3_BTCT",
) -> dict:
    """Đọc Form DXF User đã lưu trong dự án/Drive và audit theo manifest (read-only, không copy/ghi đè)."""
    cfc = _load(CFC, "dce_cfc")
    res = cfc.resolve_form_paths(form_id=form_id, project_dir=project_dir)
    if res.dxf_path is None:
        return {
            "status": "E001",
            "error": f"Không tìm thấy Form '{form_id}' trong các tầng: {res.searched_paths}",
            "tier": "missing",
        }
    val = cfc.validate_open_form(res.dxf_path, manifest_path=res.manifest_path, form_id=form_id, tier=res.tier)
    out = val.to_dict()
    out["status"] = "OK" if val.valid else "INVALID"
    return out


@_tool()
def diff_form(
    project_dir: str,
    form_id: str = "FORM_02_MULTIVIEW_A3_BTCT",
    baseline: Literal["ssot", "prev_rev"] = "ssot",
) -> dict:
    """So sánh Form DXF của User với SSOT hoặc revision trước; nhóm thay đổi & ánh xạ vào model JSON."""
    cfc = _load(CFC, "dce_cfc")
    mdf = _load(MDF, "dce_mdf")

    res = cfc.resolve_form_paths(form_id=form_id, project_dir=project_dir)
    if res.dxf_path is None:
        return {"status": "E001", "error": f"Form '{form_id}' không tồn tại: {res.searched_paths}"}

    spec = cfc.FORM_CATALOG.get(form_id)
    if spec is None:
        return {"status": "E001", "error": f"Unknown form_id: {form_id}"}

    base_path: Optional[Path] = None
    if baseline == "prev_rev":
        rev_dir = Path(project_dir) / "forms" / "revisions"
        stem = Path(spec["filename"]).stem
        revs = sorted(rev_dir.glob(f"{stem}_v*.dxf")) if rev_dir.is_dir() else []
        if len(revs) >= 2:
            base_path = revs[-2]
        elif len(revs) == 1:
            base_path = revs[0]
    if base_path is None or not base_path.is_file():
        base_path = cfc.SSOT_FORMS_DIR / spec["filename"]

    model_dict = None
    model_file = Path(project_dir) / "model" / "model.json"
    if model_file.is_file():
        model_dict = json.loads(model_file.read_text(encoding="utf-8"))

    try:
        diff_res = mdf.extract_form_diff(res.dxf_path, base_path, model=model_dict, form_id=form_id)
        diff_res["baseline_mode"] = baseline
        diff_res["tier"] = res.tier
        return diff_res
    except mdf.DiffValidationError as exc:
        return {"status": "ERROR", "code": exc.code, "error": exc.message, "details": exc.diff_details}


@_tool()
def apply_agent_changes(
    project_dir: str,
    form_id: str = "FORM_02_MULTIVIEW_A3_BTCT",
    changes: Optional[dict] = None,
    commit: bool = True,
    compliance: Literal["physical", "plan", "full"] = "physical",
) -> dict:
    """Merge-lane region-scoped (DCE_AGENT_OWNED): schema-gate vào model (v+1) & tái sinh chỉ tờ ảnh hưởng."""
    mdf = _load(MDF, "dce_mdf")
    pom = _load(POM, "dce_pom")
    pcf = _load(PATCH, "dce_pcf")

    def _combined_validate(candidate):
        """P4.1 structural gate + JSON-schema gate.

        Reuses the patcher's pure `structural_schema_gate` (single source of truth
        for the B≤B35/B40, section≥100mm, rebar 0.1–3.0% limits) but raises the
        SERVER's own `mdf.DiffValidationError` — the patcher loads its own
        `model_diff` copy, so its exception class is NOT the one the `except`
        below matches.
        """
        pom.validate_model_dict(candidate)
        violations = pcf.structural_schema_gate(candidate)
        if violations:
            raise mdf.DiffValidationError(
                "E006_SCHEMA_GATE_REJECTED",
                "P4.1 structural schema-gate rejected candidate.",
                violations,
            )
        return candidate

    proj = Path(project_dir)
    model_path = proj / "model" / "model.json"
    if not model_path.is_file():
        return {"status": "E001", "error": f"Model SSOT không tồn tại: {model_path}", "committed": False}

    current_model = pom.validate_model_dict(json.loads(model_path.read_text(encoding="utf-8")))
    if changes is None:
        changes = diff_form(project_dir=project_dir, form_id=form_id, baseline="ssot")
        if changes.get("status") not in ("OK", None):
            return {
                "status": "REJECTED",
                "code": changes.get("code", "E005_INVALID_DIFF"),
                "error": changes.get("error", "Diff failed"),
                "committed": False,
            }

    try:
        candidate, affected_sheets = mdf.apply_form_diff_to_model(
            current_model, changes, validate_fn=_combined_validate
        )
    except mdf.DiffValidationError as exc:
        return {
            "status": "REJECTED",
            "code": exc.code,
            "error": exc.message,
            "details": exc.diff_details,
            "committed": False,
            "model_version": int(current_model["model_version"]),
        }

    if not commit:
        return {
            "status": "DRY_RUN_OK",
            "committed": False,
            "region_scope_appid": "DCE_AGENT_OWNED",
            "from_model_version": int(current_model["model_version"]),
            "candidate_model_version": int(candidate["model_version"]),
            "affected_sheets": affected_sheets,
            "patches_count": len(changes.get("model_patches", [])),
        }

    pom._atomic_write_json(model_path, candidate)
    rev_path = proj / "model" / "revisions" / f"model_v{int(candidate['model_version']):03d}.json"
    pom._atomic_write_json(rev_path, candidate)

    # The model SSOT is committed above; regeneration is the step that can still
    # fail (dossier generation). Keep the commit honest: if regen fails, report
    # COMMITTED but STALE DRAWINGS instead of a raw 500, so SSOT/drawing drift
    # is detectable and the caller knows a re-run is required (AGENTS §10).
    regen_error = None
    dossier = None
    try:
        with contextlib.redirect_stdout(sys.stderr):
            dossier = pom.build_project_dossier(
                proj,
                form_id=form_id,
                sheet_numbers=affected_sheets,
                compliance=compliance,
            )
    except Exception as exc:  # ValueError (no matching sheets), audit/Drive errors
        regen_error = f"{type(exc).__name__}: {exc}"

    base = {
        "region_scope_appid": "DCE_AGENT_OWNED",
        "from_model_version": int(current_model["model_version"]),
        "to_model_version": int(candidate["model_version"]),
        "affected_sheets": affected_sheets,
        "revision_path": str(rev_path),
        "committed": True,
    }
    if regen_error:
        base.update({
            "status": "COMMITTED_REGEN_FAILED",
            "dossier_status": None,
            "regen_error": regen_error,
            "stale_drawings": True,
            "hint": "Model SSOT đã commit (v+1) nhưng bản vẽ chưa được tái sinh. Chạy lại apply_agent_changes (commit=False rồi True) hoặc regenerate dossier để đồng bộ.",
        })
        return base
    base.update({
        "status": "OK",
        "dossier_status": (dossier or {}).get("status"),
    })
    return base


# ---------------------------------------------------------------------------
# 4. Entrypoint
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
