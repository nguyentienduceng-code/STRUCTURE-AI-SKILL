"""
test_phase2_tools.py — Unit Tests cho Sprint 3 Phase 2 Modules
===============================================================
Sprint 3 · Phase 2 · TD-07 (mở rộng coverage)

Test 4 module mới:
  Suite A — etabs_com_reader.py  (Demo Mode — không cần ETABS)
  Suite B — cad_bridge.py        (Demo Mode — không cần AutoCAD/ezdxf)
  Suite C — rebar_tokenizer.py   (Regex tier — không cần mauhoc.db)
  Suite D — ifc_parser.py        (Demo Mode + Raw parser)

Chạy:
    python tests/test_phase2_tools.py
    python tests/test_phase2_tools.py --verbose
"""

import sys
import os
import json
import importlib.util
import traceback
import argparse
from datetime import datetime

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # .agents/


def _load_module(rel_path: str):
    """Import script bằng đường dẫn tương đối từ ROOT."""
    abs_path = os.path.join(ROOT, rel_path)
    if not os.path.exists(abs_path):
        raise FileNotFoundError(f"Script không tồn tại: {abs_path}")
    spec = importlib.util.spec_from_file_location("_mod_" + rel_path.replace("/","_"), abs_path)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def ok(self, name, detail=""):
        self.passed += 1
        _print_ok(name, detail)

    def fail(self, name, reason):
        self.failed += 1
        self.errors.append({"test": name, "reason": reason})
        _print_fail(name, reason)

    @property
    def total(self):
        return self.passed + self.failed

    @property
    def all_pass(self):
        return self.failed == 0


_VERBOSE = False
_GREEN  = "\033[92m"
_RED    = "\033[91m"
_YELLOW = "\033[93m"
_RESET  = "\033[0m"


def _print_ok(name, detail=""):
    mark = f"{_GREEN}✓{_RESET}"
    suffix = f"  {_YELLOW}({detail}){_RESET}" if detail and _VERBOSE else ""
    print(f"  {mark} {name}{suffix}")


def _print_fail(name, reason):
    print(f"  {_RED}✗{_RESET} {name}")
    print(f"      → {_RED}{reason}{_RESET}")


# ─────────────────────────────────────────────────────────────────────────────
# Suite A — etabs_com_reader
# ─────────────────────────────────────────────────────────────────────────────

def suite_a_etabs_reader(r: TestResult):
    print(f"\n{'─'*60}")
    print("  Suite A — etabs_com_reader (Demo Mode)")
    print(f"{'─'*60}")

    try:
        mod = _load_module("tools/etabs_com_reader.py")
    except Exception as e:
        r.fail("Load etabs_com_reader", str(e))
        return

    # A-01: Demo mode trả về dict hợp lệ
    try:
        result = mod.read_etabs(force_demo=True)
        assert isinstance(result, dict), "Không phải dict"
        r.ok("A-01 read_etabs(demo) → dict")
    except Exception as e:
        r.fail("A-01 read_etabs(demo) → dict", str(e))
        return

    # A-02: Trường bắt buộc
    for field in ("etabs_version", "model_file", "storeys", "frame_sections",
                  "rebar_results", "Calculation_Logs", "Standard_Method", "source"):
        try:
            assert field in result, f"Thiếu trường '{field}'"
            r.ok(f"A-02 field '{field}' present")
        except AssertionError as e:
            r.fail(f"A-02 field '{field}' present", str(e))

    # A-03: storeys không rỗng
    try:
        assert len(result.get("storeys", [])) >= 3, "Cần ≥ 3 tầng"
        r.ok("A-03 stories count ≥ 3", f"{len(result['storeys'])} tầng")
    except AssertionError as e:
        r.fail("A-03 stories count ≥ 3", str(e))

    # A-04: rebar_results có As values
    try:
        rr = result.get("rebar_results", [])
        assert len(rr) >= 1
        for rec in rr:
            assert "As_top_req" in rec and "As_bot_req" in rec
        r.ok("A-04 rebar_results có As fields", f"{len(rr)} records")
    except AssertionError as e:
        r.fail("A-04 rebar_results có As fields", str(e))

    # A-05: Standard_Method chứa TCVN
    try:
        sm = result.get("Standard_Method", "")
        assert "TCVN" in sm, f"Thiếu TCVN trong Standard_Method: {sm}"
        r.ok("A-05 Standard_Method chứa TCVN")
    except AssertionError as e:
        r.fail("A-05 Standard_Method chứa TCVN", str(e))

    # A-06: source là DEMO_MODE
    try:
        assert "DEMO" in result.get("source", "")
        r.ok("A-06 source=DEMO_MODE trong demo flag")
    except AssertionError as e:
        r.fail("A-06 source=DEMO_MODE", str(e))

    # A-07: Demo payload _demo_payload() trực tiếp
    try:
        dp = mod._demo_payload()
        assert "grids" in dp and len(dp["grids"]) >= 4
        r.ok("A-07 _demo_payload() có grids", f"{len(dp['grids'])} grids")
    except Exception as e:
        r.fail("A-07 _demo_payload grids", str(e))

    # A-08: Calculation_Logs có entry dạng dict
    try:
        logs = result.get("Calculation_Logs", [])
        dict_logs = [l for l in logs if isinstance(l, dict)]
        assert len(dict_logs) >= 1
        r.ok("A-08 Calculation_Logs có dict entry")
    except AssertionError as e:
        r.fail("A-08 Calculation_Logs dict entry", str(e))

    # A-09: generated_at có định dạng ISO
    try:
        ga = result.get("generated_at", "")
        assert "T" in ga and "Z" in ga
        r.ok("A-09 generated_at ISO format")
    except AssertionError as e:
        r.fail("A-09 generated_at ISO format", str(e))

    # A-10: Đơn vị As phải là mm² (> 0)
    try:
        rr = result.get("rebar_results", [])
        for rec in rr:
            assert rec.get("As_top_req", 0) > 0 or rec.get("As_bot_req", 0) > 0
        r.ok("A-10 As values > 0 mm²")
    except AssertionError as e:
        r.fail("A-10 As values > 0", str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Suite B — cad_bridge
# ─────────────────────────────────────────────────────────────────────────────

def suite_b_cad_bridge(r: TestResult):
    print(f"\n{'─'*60}")
    print("  Suite B — cad_bridge (Demo Mode + rebar parser)")
    print(f"{'─'*60}")

    try:
        mod = _load_module("tools/cad_bridge.py")
    except Exception as e:
        r.fail("Load cad_bridge", str(e))
        return

    # B-01: Rebar string parser
    tests_parser = [
        ("2D25",         [{"n": 2, "dia": 25.0}]),
        ("3D22+1D25",    [{"n": 3, "dia": 22.0}, {"n": 1, "dia": 25.0}]),
        ("D10@150",      [{"dia": 10.0, "spacing": 150}]),
        ("4Φ20",         [{"n": 4, "dia": 20.0}]),
    ]
    for raw, expected in tests_parser:
        try:
            bars = mod.parse_rebar_string(raw)
            assert len(bars) == len(expected), f"Số bars khác: {bars}"
            for i, exp in enumerate(expected):
                assert bars[i]["dia"] == exp["dia"]
                if "n" in exp and exp["n"] is not None:
                    assert bars[i]["n"] == exp["n"]
            r.ok(f"B-01 parse_rebar('{raw}')", f"{len(bars)} bars")
        except AssertionError as e:
            r.fail(f"B-01 parse_rebar('{raw}')", str(e))

    # B-02: rebar_area_mm2
    import math
    try:
        bars = [{"n": 3, "dia": 22.0, "spacing": None}]
        area = mod.rebar_area_mm2(bars)
        expected = 3 * math.pi * 11 ** 2
        assert abs(area - expected) < 1.0, f"Sai: {area:.2f} vs {expected:.2f}"
        r.ok("B-02 rebar_area_mm2(3D22)", f"{area:.2f} mm²")
    except AssertionError as e:
        r.fail("B-02 rebar_area_mm2", str(e))

    # B-03: draw_beam_section (demo mode)
    try:
        result = mod.draw_beam_section(
            b=400, h=700, cover=30,
            top_str="2D25", bot_str="3D22", stirrup_str="D10@150",
            force_demo=True,
        )
        assert isinstance(result, dict)
        r.ok("B-03 draw_beam_section(demo) → dict")
    except Exception as e:
        r.fail("B-03 draw_beam_section(demo)", str(e))

    # B-04: fields bắt buộc
    for field in ("As_top_mm2", "As_bot_mm2", "Calculation_Logs", "Standard_Method"):
        try:
            assert field in result
            r.ok(f"B-04 field '{field}' present")
        except AssertionError as e:
            r.fail(f"B-04 field '{field}'", str(e))

    # B-05: As_top > As_bot (2D25 > 3D22 sai—thực tế bot nhiều hơn)
    try:
        as_top = result.get("As_top_mm2", 0)
        as_bot = result.get("As_bot_mm2", 0)
        assert as_top > 0 and as_bot > 0
        r.ok("B-05 As_top & As_bot > 0",
             f"top={as_top:.0f} bot={as_bot:.0f} mm²")
    except AssertionError as e:
        r.fail("B-05 As > 0", str(e))

    # B-06: TCVN trong Standard_Method
    try:
        sm = result.get("Standard_Method", "")
        assert "TCVN" in sm
        r.ok("B-06 Standard_Method chứa TCVN")
    except AssertionError as e:
        r.fail("B-06 Standard_Method TCVN", str(e))

    # B-07: Kiểm tra _rect_pts
    try:
        pts = mod._rect_pts(0, 0, 400, 700)
        assert len(pts) == 5       # 4 góc + đóng
        assert pts[0] == (0, 0)
        assert pts[1] == (400, 0)
        r.ok("B-07 _rect_pts geometry")
    except Exception as e:
        r.fail("B-07 _rect_pts", str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Suite C — rebar_tokenizer
# ─────────────────────────────────────────────────────────────────────────────

def suite_c_rebar_tokenizer(r: TestResult):
    print(f"\n{'─'*60}")
    print("  Suite C — rebar_tokenizer (Regex tier)")
    print(f"{'─'*60}")

    try:
        mod = _load_module(
            "skills/Structural_Design_Engineer/scripts/rebar_tokenizer.py")
    except Exception as e:
        r.fail("Load rebar_tokenizer", str(e))
        return

    # C-01: Khởi tạo không có DB
    try:
        tok = mod.RebarTokenizer(db_path="nonexistent_db.db")
        r.ok("C-01 RebarTokenizer init (no DB)")
    except Exception as e:
        r.fail("C-01 RebarTokenizer init", str(e))
        return

    # C-02 đến C-10: tokenize các chuỗi thép
    test_vectors = [
        # (input_str, context, expected_tier, min_entities, min_As)
        ("2D25", "TOP", "REGEX", 1, 900.0),
        ("3D22", "BOT", "REGEX", 1, 1000.0),
        ("D10@150", "STIRRUP", "REGEX", 1, 0.0),          # stirrup không tính As
        ("2D25+1D22", "TOP", "REGEX", 2, 1280.0),
        ("4Φ20", "", "REGEX", 1, 1200.0),
        ("2D16 / D8@200", "SLAB", "REGEX", 2, 400.0),
        ("#5", "", "REGEX", 1, 0.0),                       # US bar
        ("3D25 / D12@100", "BOT", "REGEX", 2, 1470.0),
        ("2d25+2d22", "TOP", "REGEX", 2, 1340.0),          # lowercase
    ]

    import math
    for i, (text, ctx, exp_tier, min_ents, min_as) in enumerate(test_vectors, 2):
        test_name = f"C-0{i} tokenize('{text}')"
        try:
            result = tok.tokenize(text, context=ctx)

            # Trường bắt buộc
            assert "entities" in result
            assert "As_summary" in result
            assert "Calculation_Logs" in result

            # Số entities
            ents = result["entities"]
            assert len(ents) >= min_ents, f"entities={len(ents)} < {min_ents}"

            # As tổng
            As = result["As_summary"]["As_total_mm2"]
            if min_as > 0:
                assert As >= min_as * 0.9, f"As={As:.1f} < {min_as}"

            tier = result.get("tier_used", "")
            r.ok(test_name, f"tier={tier} ents={len(ents)} As={As:.0f}mm²")
        except Exception as e:
            r.fail(test_name, str(e))

    # C-11: batch_tokenize
    try:
        inputs = ["2D25", "3D22", "D10@150"]
        results = tok.batch_tokenize(inputs)
        assert len(results) == 3
        r.ok("C-11 batch_tokenize(3 items)")
    except Exception as e:
        r.fail("C-11 batch_tokenize", str(e))

    # C-12: db_stats khi không có DB
    try:
        stats = tok.db_stats()
        assert stats.get("ready") == False
        r.ok("C-12 db_stats(no DB) → ready=False")
    except Exception as e:
        r.fail("C-12 db_stats", str(e))

    # C-13: Fuzzy fallback cho chuỗi lỗi chính tả
    try:
        result = tok.tokenize("2DD25")  # lỗi đánh máy
        assert "entities" in result
        r.ok("C-13 fuzzy fallback (typo '2DD25')")
    except Exception as e:
        r.fail("C-13 fuzzy fallback", str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Suite D — ifc_parser
# ─────────────────────────────────────────────────────────────────────────────

def suite_d_ifc_parser(r: TestResult):
    print(f"\n{'─'*60}")
    print("  Suite D — ifc_parser (Demo Mode + CDC validation)")
    print(f"{'─'*60}")

    try:
        mod = _load_module("tools/ifc_parser.py")
    except Exception as e:
        r.fail("Load ifc_parser", str(e))
        return

    # D-01: Demo mode
    try:
        result = mod.parse_ifc(force_demo=True)
        assert isinstance(result, dict)
        r.ok("D-01 parse_ifc(demo) → dict")
    except Exception as e:
        r.fail("D-01 parse_ifc(demo)", str(e))
        return

    # D-02: Trường bắt buộc
    for field in ("ifc_schema", "project_name", "storeys", "elements",
                  "grids", "reinforcement", "Calculation_Logs", "Standard_Method"):
        try:
            assert field in result
            r.ok(f"D-02 field '{field}' present")
        except AssertionError as e:
            r.fail(f"D-02 field '{field}'", str(e))

    # D-03: Storeys
    try:
        storeys = result.get("storeys", [])
        assert len(storeys) >= 3
        for s in storeys:
            assert "name" in s and "elevation_mm" in s
        r.ok("D-03 storeys ≥ 3 với name+elevation", f"{len(storeys)} tầng")
    except AssertionError as e:
        r.fail("D-03 storeys", str(e))

    # D-04: Elements có IfcBeam / IfcColumn
    try:
        elements = result.get("elements", [])
        types = {e["type"] for e in elements}
        assert "IfcBeam" in types or "IfcColumn" in types
        r.ok("D-04 elements chứa Beam/Column", f"{len(elements)} elements")
    except AssertionError as e:
        r.fail("D-04 elements Beam/Column", str(e))

    # D-05: Grids
    try:
        grids = result.get("grids", [])
        assert len(grids) >= 3
        r.ok("D-05 grids ≥ 3", f"{len(grids)} grids")
    except AssertionError as e:
        r.fail("D-05 grids", str(e))

    # D-06: CDC validation chạy được
    try:
        issues = result.get("cdc_issues", [])
        assert isinstance(issues, list)
        r.ok("D-06 cdc_issues là list", f"{len(issues)} issues")
    except AssertionError as e:
        r.fail("D-06 cdc_issues", str(e))

    # D-07: parse_ifc với file không tồn tại → fallback demo
    try:
        r2 = mod.parse_ifc(filepath="nonexistent.ifc")
        assert "storeys" in r2
        r.ok("D-07 fallback khi file không tồn tại")
    except Exception as e:
        r.fail("D-07 fallback nonexistent file", str(e))

    # D-08: _demo_payload trực tiếp
    try:
        dp = mod._demo_payload()
        assert len(dp.get("elements", [])) >= 3
        r.ok("D-08 _demo_payload() ≥ 3 elements")
    except Exception as e:
        r.fail("D-08 _demo_payload", str(e))

    # D-09: validate_cdc function
    try:
        dummy_data = {
            "storeys":  [{"guid": "S1", "name": "L1", "elevation_mm": 0}],
            "elements": [
                {"guid": "E1", "type": "IfcBeam", "name": "B1",
                 "storey": "", "section": "", "material": ""},
            ],
            "grids": [],
        }
        issues2 = mod.validate_cdc(dummy_data, [])
        assert any(i["rule"] in ("CDC-01", "CDC-02") for i in issues2)
        r.ok("D-09 validate_cdc phát hiện issues")
    except Exception as e:
        r.fail("D-09 validate_cdc", str(e))

    # D-10: Standard_Method chứa ISO/IFC
    try:
        sm = result.get("Standard_Method", "")
        assert "IFC" in sm or "ISO" in sm
        r.ok("D-10 Standard_Method chứa IFC/ISO")
    except AssertionError as e:
        r.fail("D-10 Standard_Method", str(e))

    # D-11: _UNIT SCALES (đơn vị)
    try:
        dp = mod._demo_payload()
        for s in dp.get("storeys", []):
            assert s["elevation_mm"] >= 0
        r.ok("D-11 elevation_mm >= 0")
    except AssertionError as e:
        r.fail("D-11 elevation_mm", str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Main runner
# ─────────────────────────────────────────────────────────────────────────────

def main():
    global _VERBOSE
    parser = argparse.ArgumentParser(
        description="Sprint 3 Phase 2 — Unit Tests (Phase2 Tools)")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()
    _VERBOSE = args.verbose

    print("=" * 60)
    print("  SPRINT 3 PHASE 2 — UNIT TEST SUITE")
    print(f"  {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print("=" * 60)

    r = TestResult()

    suite_a_etabs_reader(r)
    suite_b_cad_bridge(r)
    suite_c_rebar_tokenizer(r)
    suite_d_ifc_parser(r)

    # ── Tổng kết ─────────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    status = f"{_GREEN}ALL PASS{_RESET}" if r.all_pass else f"{_RED}FAILED{_RESET}"
    print(f"  KẾT QUẢ: {status}")
    print(f"  Passed : {_GREEN}{r.passed}{_RESET}")
    print(f"  Failed : {_RED}{r.failed}{_RESET}")
    print(f"  Total  : {r.total}")
    if r.errors:
        print(f"\n  {_RED}Failed tests:{_RESET}")
        for err in r.errors:
            print(f"    • {err['test']}: {err['reason']}")
    print("=" * 60)

    sys.exit(0 if r.all_pass else 1)


if __name__ == "__main__":
    main()
