# -*- coding: utf-8 -*-
"""
dce_render_preview.py — Bản render Preview DXF → PNG cho Vision Perception Loop
===============================================================================

Mục đích (RFC-20261113-MCP-CAD, Giai đoạn 1):
    Chuyển một file DXF chuẩn DCE Pro (đầu ra của cad_plan_engine.py /
    cad_bridge.py) thành ảnh PNG độ phân giải cao mà KHÔNG cần AutoCAD,
    để mô hình Vision (Claude / Gemini) tự "nhìn" phát hiện va chạm trực
    quan: text đè hatch, nhãn dim bị che, text vượt khung A1.

Kiến trúc (không đụng vào engine lõi):
    - Đây là module adapter độc lập nằm trong .agents/tools/ (theo quy tắc
      "adapter mỏng"), engine cad_plan_engine.py / dce_dxf_generator.py
      giữ nguyên 100%.
    - Backend render: ezdxf.addons.drawing (ezdxf >= 1.4.x).
      * Đường chính (đã test): ezdxf.addons.drawing.matplotlib.qsave
      * Đường crop: MatplotlibBackend + Frontend khi cần view_box (mm).

Yêu cầu hệ thống (đã xác minh trên máy chạy hệ thống này):
    - ezdxf 1.4.x + matplotlib (Agg) — ĐÃ CÓ.
    - KHÔNG cần AutoCAD, ODA File Converter, hay mcp SDK ở giai đoạn 1.

Ghi chú API (EZDXF 1.4.x — khác tài liệu 0.x):
    - Configuration / LinePolicy / HatchPolicy / TextPolicy / ColorPolicy
      import từ `ezdxf.addons.drawing.config` (KHÔNG nằm ở top-level).
    - qsave import từ `ezdxf.addons.drawing.matplotlib`.
    - `ezdxf.bbox` module rỗng ở 1.4.4 -> KHÔNG crop theo bbox tự động,
      crop theo view_box (mm) do caller truyền.

Quy tắc hệ thống: UTF-8 (AGENTS.md §2), đường dẫn tuyệt đối (§1),
xác nhận file tồn tại trước khi báo OK (§10).
"""

import sys
sys.dont_write_bytecode = True

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

import time
import json
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from dce_virtual_drive_guard import (
    configure_runtime, allocate_preview, finish_preview, cleanup_preview, RENDER_LOCK,
)

configure_runtime()

try:
    import ezdxf
    from ezdxf.addons.drawing import Frontend, RenderContext
    from ezdxf.addons.drawing.config import (
        Configuration,
        LinePolicy,
        HatchPolicy,
        TextPolicy,
        ColorPolicy,
    )
    from ezdxf.addons.drawing.matplotlib import qsave, MatplotlibBackend
    _EZDXF_OK = True
    _EZDXF_ERR = ""
except Exception as _e:  # pragma: no cover - môi trường thiếu ezdxf
    _EZDXF_OK = False
    _EZDXF_ERR = f"ezdxf import failed: {_e}"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def render_dxf_to_png(
    dxf_path: str,
    out_png: str = "",
    dpi: int = 150,
    layout_name: str = "Model",
    bg: str = "#FFFFFF",
    fg: str = "#000000",
    view_box: Optional[Tuple[float, float, float, float]] = None,
    config: Optional[Configuration] = None,
) -> Dict[str, Any]:
    """
    Render một layout của file DXF ra ảnh PNG.

    Tham số
    ----
    dxf_path : str
        Đường dẫn tuyệt định (AGENTS.md §1) tới file .dxf.
    out_png : str
        Gợi ý đường dẫn; preview luôn được cô lập local, không ghi tại đây.
        Caller phải đọc output_png thực tế và cleanup bằng preview_id.
    dpi : int (mặc định 150)
        Độ phân giải ảnh. Preview cho vòng lặp Vision dùng 150-200 là đủ
        và nhanh; bản in/Word dùng 300.
    layout_name : str (mặc định "Model")
        Layout trong DXF. DCE Pro vẽ ở Model; sheet A1 có thể nằm trong
        layout "Paper_Space" — caller truyền tên layout cụ thể nếu cần.
    bg / fg : str
        Màu nền / màu nét (hex). Mặc định nền trắng, nét đen — chuẩn in
        đen trắng (Điều 12b AGENTS.md: không được sinh chữ trắng trên nền
        tối).
    view_box : (min_x, min_y, max_x, max_y) theo đơn vị MM (toạ độ world),
        optional. Nếu truyền -> crop vùng này (đường MatplotlibBackend).
        Nếu None -> render toàn layout (đường qsave).
    config : Configuration, optional
        Trọn bộ cấu hình render (hatch_policy, text_policy, ...). Mặc định
        Configuration().

    Trả về (JSON-serializable)
    ----
    dict có các trường:
        status: "OK" | "E001" | "E002" (theo bảng mã lỗi AGENTS.md §17)
        output_png, png_bytes, render_seconds, dpi, layout
        modelspace_entities, layers, blocks  (thông tin kiểm chứng)
        verified_file_exists: bool  (Quy tắc §10 — BẮT BUỘC True trước khi
                                     caller dùng ảnh)
        error: str (chỉ khi status != "OK")
    """
    if not _EZDXF_OK:
        return {
            "status": "E002",
            "error": _EZDXF_ERR,
            "verified_file_exists": False,
        }

    src = Path(dxf_path)
    if not src.is_file():
        return {"status": "E001", "error": f"DXF not found: {src}", "verified_file_exists": False}

    doc = ezdxf.readfile(str(src))
    layouts = [ln.dxf.name for ln in doc.layouts]
    if layout_name not in layouts:
        # Tự chọn layout hợp lệ nếu caller truyền sai
        layout_name = "Model" if "Model" in layouts else layouts[0]
    layout = doc.layouts.get(layout_name)
    msp = doc.modelspace()
    n_ent = sum(1 for _ in msp)
    cfg = config if config is not None else Configuration()

    t0 = time.time()
    preview_id, dst = allocate_preview()
    try:
        with RENDER_LOCK:
            import matplotlib.pyplot as plt
            original_figures = set(plt.get_fignums())
            try:
                if view_box is not None:
                    _render_crop(doc, layout, layout_name, dst, dpi, bg, fg, cfg, view_box)
                else:
                    qsave(layout, str(dst), bg=bg, fg=fg, dpi=dpi, config=cfg)
            finally:
                for number in set(plt.get_fignums()) - original_figures:
                    plt.close(number)
        finish_preview(preview_id)
    except Exception as error:
        cleanup = cleanup_preview(preview_id)
        return {"status": "E003", "error": str(error),
                "verified_file_exists": False, "cleanup": cleanup}

    render_seconds = round(time.time() - t0, 3)
    png_bytes = dst.stat().st_size if dst.exists() else 0

    return {
        "status": "OK",
        "output_png": str(dst),
        "preview_id": preview_id,
        "requested_output_png": out_png,
        "temporary": True,
        "cleanup_tool": "release_preview",
        "vision_tool": "consume_preview",
        "png_bytes": png_bytes,
        "render_seconds": render_seconds,
        "dpi": dpi,
        "layout": layout_name,
        "view_box": view_box,
        "modelspace_entities": n_ent,
        "layers": len(doc.layers),
        "blocks": len(doc.blocks),
        "verified_file_exists": bool(dst.exists() and png_bytes > 0),
    }


@contextmanager
def preview_for_vision(dxf_path: str, **kwargs):
    """Python Vision callers: release the preview even if inspection raises."""
    result = render_dxf_to_png(dxf_path, **kwargs)
    try:
        yield result
    finally:
        if result.get('preview_id'):
            cleanup = cleanup_preview(result['preview_id'])
            if cleanup['status'] != 'CLEANED':
                raise OSError(cleanup['error'])


def _render_crop(doc, layout, layout_name, dst: Path, dpi: int,
                 bg: str, fg: str, cfg: Configuration,
                 view_box: Tuple[float, float, float, float]) -> None:
    """Render crop vùng (min_x, min_y, max_x, max_y) mm bằng MatplotlibBackend."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    min_x, min_y, max_x, max_y = view_box
    w = max_x - min_x
    h = max_y - min_y
    if w <= 0 or h <= 0:
        raise ValueError(f"view_box hợp lệ? w/h <= 0: {view_box}")

    # figsize theo tỉ lệ khung + dpi để ảnh ra đúng kích thước pixel
    base_in = 8.0  # cm-ish base
    fig_w_in = max(1.0, (w / 10.0) * 0.05)  # rough mm->in at ~50 mm/in
    fig_h_in = max(1.0, (h / 10.0) * 0.05)
    fig, ax = plt.subplots(figsize=(fig_w_in, fig_h_in), dpi=dpi)

    try:
        backend = MatplotlibBackend(ax, adjust_figure=False)
        Frontend(RenderContext(doc), backend, cfg).draw_layout(layout, finalize=True)
        ax.set_xlim(min_x, max_x)
        ax.set_ylim(min_y, max_y)
        ax.set_aspect("equal")
        ax.axis("off")
        fig.savefig(dst, dpi=dpi, facecolor=bg, bbox_inches="tight", pad_inches=0.1)
    finally:
        plt.close(fig)


# ---------------------------------------------------------------------------
# CLI — chạy độc lập để test / tích hợp pipeline
# ---------------------------------------------------------------------------
def _cli() -> None:
    import argparse

    p = argparse.ArgumentParser(description="DCE render preview DXF -> PNG (Vision loop, Giai đoạn 1)")
    p.add_argument("--dxf", help="Đường dẫn tuyệt định file .dxf")
    p.add_argument("--out", default="", help="Gợi ý tên; đọc output_png local từ kết quả")
    p.add_argument("--release", help="Xóa preview bằng preview_id sau khi Vision đọc xong")
    p.add_argument("--dpi", type=int, default=150, help="Độ phân giải (preview: 150-200, in: 300)")
    p.add_argument("--layout", default="Model", help="Tên layout (Model / Paper_Space / ...)")
    p.add_argument("--bg", default="#FFFFFF", help="Màu nền hex")
    p.add_argument("--fg", default="#000000", help="Màu nét hex")
    p.add_argument("--view-box", default=None,
                   help="Crop 'minx,miny,maxx,maxy' (mm). VD: '0,0,84100,59400'")
    p.add_argument("--indent", type=int, default=2)
    a = p.parse_args()

    if a.release:
        result = cleanup_preview(a.release)
        print(json.dumps(result, ensure_ascii=False))
        sys.exit(0 if result['status'] == 'CLEANED' else 1)
    if not a.dxf:
        p.error('--dxf is required unless --release is used')

    vb = None
    if a.view_box:
        vb = tuple(float(v) for v in a.view_box.split(","))
        if len(vb) != 4:
            print(json.dumps({"status": "E001", "error": "--view-box must be 4 values"}, indent=2))
            sys.exit(1)

    res = render_dxf_to_png(a.dxf, a.out, dpi=a.dpi, layout_name=a.layout,
                            bg=a.bg, fg=a.fg, view_box=vb)
    print(json.dumps(res, ensure_ascii=False, indent=a.indent))
    sys.exit(0 if res["status"] == "OK" else 1)


if __name__ == "__main__":
    _cli()
