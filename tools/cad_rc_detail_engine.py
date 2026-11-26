# -*- coding: utf-8 -*-
"""
cad_rc_detail_engine.py (Tools Compatibility Shim -> cad_integration/cad_rc_detail_engine.py)
===========================================================================================
Wrapper giữ tương thích CLI / import cho `.agents/tools/cad_rc_detail_engine.py`,
ủy thác toàn bộ logic dựng bản vẽ chi tiết BTCT chuẩn Form_04 về module chính thức tại
`.agents/skills/Technical_Illustrator/cad_integration/cad_rc_detail_engine.py`.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure") and sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

_CAD_INT = Path(__file__).resolve().parents[1] / "skills" / "Technical_Illustrator" / "cad_integration"
if str(_CAD_INT) not in sys.path:
    sys.path.insert(0, str(_CAD_INT))

from cad_rc_detail_engine import (  # noqa: E402, F401
    CATLAI_DETAIL_SPECS,
    DEFAULT_CATLAI_PROJECT,
    STANDARD_METHOD_DETAIL,
    build_all_catlai_detail_sheets,
    build_custom_detail_sheet,
    build_detail_sheet,
    compute_bbs_rows,
    rebar_unit_weight_kg_per_m,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Native Form_04 RC Detail CAD sheet(s).")
    parser.add_argument("--sheet", default="ALL", help="KC.03, KC.04, KC.08, KC.09, or ALL")
    parser.add_argument("--out-dir", default=r"g:\My Drive\Google AI Studio\01_Projects\03_Sprint2_KetQua_NeChu_CAD\04_Deliverables_ToTrinh")
    args = parser.parse_args()

    sheet_arg = args.sheet.strip().upper().replace("-", ".")
    out_dir = Path(args.out_dir)
    if sheet_arg == "ALL":
        res = build_all_catlai_detail_sheets(out_dir)
    elif sheet_arg in CATLAI_DETAIL_SPECS:
        spec = CATLAI_DETAIL_SPECS[sheet_arg]()
        res = [build_detail_sheet(spec, out_dir / spec["filename"])]
    else:
        raise ValueError(f"Unknown sheet: {args.sheet}")
    print(json.dumps(res, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
