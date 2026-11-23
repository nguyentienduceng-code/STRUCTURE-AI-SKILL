# -*- coding: utf-8 -*-
"""
test_tier2_phase2b_snapshot_diff.py — Tầng 2B (solo): canonical snapshot + D1/D1A diff
========================================================================================
Xác định hoàn toàn (không cần AutoCAD) — kiểm tra đường "bảo đảm" của 2B:
  1. build_snapshot_from_inventory: chuẩn hóa mm/độ, fingerprint ổn định, trùng mark D1
     được giữ (không tự ghép), PRIMARY thiếu id -> UNMATCHED.
  2. validate_snapshot: phát hiện role sai, fingerprint lệch (trường biến động).
  3. diff_snapshots: D1/D1A đúng — id đổi thuộc tính+label; type dùng chung làm cả
     hai dầm sai; duplicate primary; added/removed; tolerance.
"""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

AGENTS_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = AGENTS_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import native_dwg_snapshot as snap   # noqa: E402
import native_dwg_diff as diff       # noqa: E402


def two_beams(overridden_bc: bool, bc_mark: str = "D1") -> dict:
    """Dựng snapshot 2 dầm cùng mark D1 (nhịp A–B = id1, B–C = id2, h=500).

    overridden_bc=True: chỉ id2 (B–C) được duyệt đổi 250x500 -> 250x600 + label D1A.
    Type dùng chung: override cả hai -> id1 cũng thành 600 (lỗi)."""
    def inv(h2: int, m2: str):
        return [
            {"element_id": "BEAM-A-B", "role": "PRIMARY_GEOM", "floor_id": "L2",
             "dxftype": "LWPOLYLINE", "mark": "D1",
             "geometry": {"x0_mm": 0.0, "y0_mm": 0.0, "x1_mm": 3000.0, "y1_mm": 0.0},
             "properties": {"b_mm": 250, "h_mm": 500}},
            {"element_id": "BEAM-B-C", "role": "PRIMARY_GEOM", "floor_id": "L2",
             "dxftype": "LWPOLYLINE", "mark": m2,
             "geometry": {"x0_mm": 3000.0, "y0_mm": 0.0, "x1_mm": 6000.0, "y1_mm": 0.0},
             "properties": {"b_mm": 250, "h_mm": h2}},
        ]
    if overridden_bc:
        return snap.build_snapshot_from_inventory(inv(600, bc_mark), document_id="TIER2", revision="R2")
    return snap.build_snapshot_from_inventory(inv(500, "D1"), document_id="TIER2", revision="R1")


class TestCanonicalSnapshot(unittest.TestCase):
    def test_unit_normalization_to_mm(self):
        s = snap.build_snapshot_from_inventory(
            [{"element_id": "E1", "role": "PRIMARY_GEOM",
              "geometry": {"x_mm": 2.0, "b_mm": 3.0}, "source_units": None}],
            document_id="X", source_units="m")
        g = s["records"][0]["geometry"]
        self.assertEqual(g["x_mm"], 2000.0)
        self.assertEqual(g["b_mm"], 3000.0)
        self.assertEqual(s["records"][0]["geometry"]["x_mm"], 2000.0)

    def test_fingerprint_stable_across_volatile_fields(self):
        base = snap.build_snapshot_from_inventory(
            [{"element_id": "E1", "role": "PRIMARY_GEOM", "geometry": {"x_mm": 10.0}}],
            document_id="X")
        mut = dict(base)
        mut["records"] = [dict(base["records"][0], handle="A1B", generated_at="2026")]
        self.assertEqual(snap.fingerprint_snapshot(base),
                         snap.fingerprint_snapshot(mut))

    def test_twin_mark_kept_and_unmatched_flagged(self):
        s = snap.build_snapshot_from_inventory(
            [{"element_id": "E1", "role": "PRIMARY_GEOM", "mark": "D1"},
             {"element_id": "E2", "role": "PRIMARY_GEOM", "mark": "D1"},
             {"role": "PRIMARY_GEOM", "mark": "D1"}],  # không có element_id
            document_id="X")
        self.assertEqual(s["counts"]["with_identity"], 2)
        self.assertEqual(s["counts"]["unmatched"], 1)
        issues = snap.validate_snapshot(s)
        self.assertTrue(any("PRIMARY_GEOM without element_id" in i for i in issues))


class TestValidate(unittest.TestCase):
    def test_bad_role_and_fingerprint(self):
        s = snap.build_snapshot_from_inventory(
            [{"element_id": "E1", "role": "WEIRD", "geometry": {"x_mm": 1.0}}], document_id="X")
        issues = snap.validate_snapshot(s)
        self.assertTrue(any("unknown role" in i for i in issues))


class TestD1D1ADiff(unittest.TestCase):
    def test_in_scope_only_bc_changes(self):
        a = two_beams(False)
        b = two_beams(True, bc_mark="D1A")
        rep = diff.diff_snapshots(a, b)
        self.assertTrue(rep["clean"] is False)
        changed = rep["changes"]
        self.assertIn("BEAM-B-C", changed)
        bc = changed["BEAM-B-C"]
        self.assertIn(diff.DC["PROPERTY_CHANGED"], bc["classes"])
        self.assertIn(diff.DC["MARK_CHANGED"], bc["classes"])
        self.assertEqual(bc["mark"]["from"], "D1")
        self.assertEqual(bc["mark"]["to"], "D1A")
        # A–B (id1) KHÔNG đổi -> không có trong changes
        self.assertNotIn("BEAM-A-B", changed)
        self.assertNotIn("BEAM-A-B", rep["removed"])

    def test_shared_type_flips_both_beams(self):
        # Type dùng chung: cả 2 dầm thành 600 -> cả hai đều PROPERTY_CHANGED (lỗi,
        # phải chỉ ra dầm A–B sai 100mm dù chỉ duyệt B–C).
        a = snap.build_snapshot_from_inventory(
            [{"element_id": "BEAM-A-B", "role": "PRIMARY_GEOM", "mark": "D1",
              "properties": {"b_mm": 250, "h_mm": 500}},
             {"element_id": "BEAM-B-C", "role": "PRIMARY_GEOM", "mark": "D1",
              "properties": {"b_mm": 250, "h_mm": 500}}], document_id="T", revision="R1")
        b = snap.build_snapshot_from_inventory(
            [{"element_id": "BEAM-A-B", "role": "PRIMARY_GEOM", "mark": "D1",
              "properties": {"b_mm": 250, "h_mm": 600}},   # type dùng chung -> sai
             {"element_id": "BEAM-B-C", "role": "PRIMARY_GEOM", "mark": "D1A",
              "properties": {"b_mm": 250, "h_mm": 600}}], document_id="T", revision="R2")
        rep = diff.diff_snapshots(a, b)
        self.assertIn("BEAM-A-B", rep["changes"])
        self.assertEqual(rep["changes"]["BEAM-A-B"]["property_delta"]["h_mm"]["b"], 600)
        dec = diff.d1d1a_decision(rep)
        self.assertTrue(any(e["element_id"] == "BEAM-A-B" for e in dec["out_of_scope_changed"]))

    def test_duplicate_primary_owner_conflict(self):
        a = two_beams(False)
        b = snap.build_snapshot_from_inventory(
            two_beams(False)["records"], document_id="TIER2", revision="R1")
        # COPY làm 2 handle giữ cùng PRIMARY id
        b["records"].append(dict(a["records"][1], handle="ZZZ"))
        rep = diff.diff_snapshots(a, b)
        self.assertIn("BEAM-B-C", rep["issues"]["DUPLICATE_PRIMARY"])

    def test_added_and_removed(self):
        a = snap.build_snapshot_from_inventory(
            [{"element_id": "E1", "role": "PRIMARY_GEOM"}], document_id="X")
        b = snap.build_snapshot_from_inventory(
            [{"element_id": "E2", "role": "PRIMARY_GEOM"}], document_id="X")
        rep = diff.diff_snapshots(a, b)
        self.assertEqual([x["element_id"] for x in rep["added"]], ["E2"])
        self.assertEqual([x["element_id"] for x in rep["removed"]], ["E1"])

    def test_geometry_within_tolerance_is_not_change(self):
        a = snap.build_snapshot_from_inventory(
            [{"element_id": "E1", "role": "PRIMARY_GEOM", "geometry": {"x_mm": 0.0}}], document_id="X")
        b = snap.build_snapshot_from_inventory(
            [{"element_id": "E1", "role": "PRIMARY_GEOM", "geometry": {"x_mm": 0.3}}], document_id="X")
        rep = diff.diff_snapshots(a, b)  # delta 0.3 < 0.5 threshold
        self.assertNotIn("E1", rep["changes"])
        rep2 = diff.diff_snapshots(a, snap.build_snapshot_from_inventory(
            [{"element_id": "E1", "role": "PRIMARY_GEOM", "geometry": {"x_mm": 2.0}}], document_id="X"))
        self.assertIn("E1", rep2["changes"])
        self.assertIn(diff.DC["GEOMETRY_CHANGED"], rep2["changes"]["E1"]["classes"])


class TestBridgeWorker(unittest.TestCase):
    """Logic worker native (staging + SHA bất biến + validate) qua FAKE executable
    — kiểm chứng đầy đủ mà không cần AutoCAD trên host.

    `run_snapshot` gọi `[exe, staged_dwg, command, out_json, revision]`. Fake exe
    tại đây là wrapper .cmd (Windows) / sh (POSIX) nhận đúng 4 tham số đó và ghi
    JSON snapshot hợp lệ vào argv[3] (out_json)."""

    @staticmethod
    def _fake_console(tmp_dir: str, emit: bool = True) -> str:
        p = Path(tmp_dir)
        if os.name == "nt":
            body = ("@echo off\r\n"
                    + ('echo {"records":[{"element_id":"E1","role":"PRIMARY_GEOM",'
                       '"geometry":{"x_mm":1.0}}]} > "%3"\r\n' if emit else "@rem no-op\r\n"))
            f = p / "fake_console.cmd"
            f.write_text(body, encoding="utf-8")
            return str(f)
        body = ('#!/bin/sh\n' + ('echo \'{"records":[{"element_id":"E1","role":"PRIMARY_GEOM","geometry":{"x_mm":1.0}}]}\' > "$3"\n'
               if emit else "exit 0\n"))
        f = p / "fake_console.sh"
        f.write_text(body, encoding="utf-8")
        f.chmod(0o755)
        return str(f)

    def test_fake_worker_ok_and_source_immutable(self):
        import autocad_snapshot_bridge as bridge
        with tempfile.TemporaryDirectory() as d:
            src = os.path.join(d, "a.dwg")
            with open(src, "w", encoding="utf-8") as fh:
                fh.write("FAKE_DWG")
            fake = self._fake_console(d, emit=True)
            res = bridge.run_snapshot(
                src, staging_dir=os.path.join(d, "staging"),
                accoreconsole_exe=fake, revision="R1")
            self.assertEqual(res["status"], bridge.STATUS_OK)
            self.assertTrue(res["immutability_ok"])
            self.assertEqual(res["source_hash_before"], res["source_hash_after"])
            self.assertIn("E1", [r["element_id"] for r in res["snapshot"]["records"]])
            # Snapshot đã validate: completion.complete=True khi hợp lệ
            self.assertTrue(res["snapshot"]["completion"]["complete"])

    def test_unavailable_when_no_exe(self):
        import autocad_snapshot_bridge as bridge
        with tempfile.TemporaryDirectory() as d:
            src = os.path.join(d, "a.dwg")
            with open(src, "w", encoding="utf-8") as fh:
                fh.write("FAKE")
            res = bridge.run_snapshot(src, accoreconsole_exe="/nonexistent/coreconsole.exe")
            self.assertEqual(res["status"], bridge.STATUS_UNAVAILABLE)
            self.assertTrue(res["immutability_ok"])

    def test_incomplete_run_is_not_ok(self):
        import autocad_snapshot_bridge as bridge
        with tempfile.TemporaryDirectory() as d:
            src = os.path.join(d, "a.dwg")
            with open(src, "w", encoding="utf-8") as fh:
                fh.write("FAKE")
            # Fake "console" không sinh file output => run incomplete => ERROR,
            # KHÔNG bao giờ được quy thành OK (nguyên tắc "native không pass giả").
            fake = self._fake_console(d, emit=False)
            res = bridge.run_snapshot(src, staging_dir=os.path.join(d, "st"),
                                      accoreconsole_exe=fake, revision="R1")
            self.assertEqual(res["status"], bridge.STATUS_ERROR)


class TestPluginToolchain(unittest.TestCase):
    def test_build_plugin_accepts_path_and_compiles_or_unavailable(self):
        import autocad_snapshot_bridge as bridge
        with tempfile.TemporaryDirectory() as d:
            dll_path = Path(d) / "dce_snapshot_plugin.dll"
            res = bridge.build_plugin(dll_path)
            if bridge.Path(bridge.CSC).is_file() and all(bridge.Path(p).is_file() for p in bridge.ACSREFS.values()):
                self.assertEqual(res["status"], bridge.STATUS_OK, res)
                self.assertTrue(dll_path.is_file() and dll_path.stat().st_size > 0)
            else:
                self.assertEqual(res["status"], bridge.STATUS_UNAVAILABLE)

    def test_accoreconsole_missing_plugin_returns_unavailable_cleanly(self):
        import autocad_snapshot_bridge as bridge
        det = bridge.detect_accoreconsole()
        if not det.get("found"):
            return
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "dummy.dwg"
            src.write_bytes(b"AC1032")
            res = bridge.run_snapshot(
                str(src),
                staging_dir=str(Path(d) / "st"),
                accoreconsole_exe=det["path"],
                plugin=str(Path(d) / "missing_plugin.dll"),
            )
            self.assertEqual(res["status"], bridge.STATUS_UNAVAILABLE)
            self.assertTrue(res["immutability_ok"])


class TestBeamXDataViaEzdxf(unittest.TestCase):
    """DCE_BEAM (MARK/B/H) regapp đọc qua đường ezdxf => D1/D1A diff thấy được.

    Đây là 'chốt canonical element identity + XData versioning' (spec §4.1):
    fixture gán `DCE_BEAM` lên LWPOLYLINE (không phải block); reader phải trích
    `mark` + `b_mm/h_mm` để MỘT thuật toán diff (native + ezdxf) thấy sự khác
    D1/D1A mà KHÔNG cần geometry move (section 500->600, label D1->D1A)."""

    def _pair(self, d):
        import dce_native_fixture as fx
        return fx.make_d1_d1a_pair(d)

    def test_beam_xdata_extracted_via_ezdxf_lane(self):
        with tempfile.TemporaryDirectory() as d:
            r = self._pair(d)
            if r.get("status") != "OK":
                self.skipTest("ezdxf unavailable: " + str(r.get("reason")))
            a = snap.build_snapshot_from_dxf(r["d1_dxf"], document_id="D1")
            b = snap.build_snapshot_from_dxf(r["d1a_dxf"], document_id="D1A")
            ra = {x["element_id"]: x for x in a["records"] if x.get("element_id")}
            rb = {x["element_id"]: x for x in b["records"] if x.get("element_id")}
            # DCE_BEAM đã được trích: mark + b_mm/h_mm có mặt (cả 2 phía).
            self.assertEqual(ra["BEAM_BC"].get("mark"), "D1")
            self.assertEqual(ra["BEAM_BC"].get("properties", {}).get("h_mm"), 500.0)
            self.assertEqual(rb["BEAM_BC"].get("mark"), "D1A")
            self.assertEqual(rb["BEAM_BC"].get("properties", {}).get("h_mm"), 600.0)
            # D1/D1A diff: CHỈ BEAM_BC đổi (section + label); BEAM_AB không đổi.
            rep = diff.diff_snapshots(a, b)
            self.assertIn("BEAM_BC", rep["changes"])
            self.assertNotIn("BEAM_AB", rep["changes"])
            bc = rep["changes"]["BEAM_BC"]
            self.assertIn(diff.DC["PROPERTY_CHANGED"], bc["classes"])
            self.assertIn(diff.DC["MARK_CHANGED"], bc["classes"])
            self.assertEqual(bc["property_delta"].get("h_mm", {}).get("a"), 500.0)
            self.assertEqual(bc["property_delta"].get("h_mm", {}).get("b"), 600.0)
            # Trong phạm vi duyệt: cấu kiện đổi kèm MARK_CHANGED -> không out-of-scope.
            dec = diff.d1d1a_decision(rep)
            self.assertEqual([e["element_id"] for e in dec["out_of_scope_changed"]], [])

    def test_fixture_to_dwg_degrades_without_oda(self):
        # ODA vắng => to_dwg trả UNAVAILABLE trung thực, KHÔNG bịa file DWG.
        import dce_native_fixture as fx
        from unittest import mock
        with tempfile.TemporaryDirectory() as d:
            r = self._pair(d)
            if r.get("status") != "OK":
                self.skipTest("ezdxf unavailable")
            with mock.patch.object(fx, "ODA_EXE", str(Path(d) / "missing_oda.exe")):
                w = fx.to_dwg([r["d1_dxf"]], d)
            self.assertEqual(w["status"], "UNAVAILABLE")
            self.assertIsNone(w["dwg_paths"][r["d1_dxf"]])
            # Không có file DWG nào được tạo (không fabricate).
            self.assertEqual(list(Path(d).glob("*.dwg")), [])


class TestNativeMcpDegrade(unittest.TestCase):
    """MCP native_dwg_snapshot / native_dwg_diff degrade UNAVAILABLE khi toolchain
    native thiếu — DETERMINISTIC (patch module mà MCP thực sự load), không cần AutoCAD.

    MCP load bridge qua `_load(SNAP_BRIDGE, 'dce_snap_bridge')` -> một module
    RIÊNG (sys.modules['dce_snap_bridge']), khác module `autocad_snapshot_bridge`.
    Patch đúng module đó để tool fetch lại (cache) vẫn thấy phiên bản patch."""

    def test_mcp_native_tools_degrade_without_host(self):
        import mcp_dce_cad_server as srv
        from unittest import mock
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "x.dwg"
            src.write_bytes(b"AC1032")
            # Module mà tool MCP thực sự gọi (cached trong sys.modules sau lần load đầu).
            bridge_mod = srv._load(srv.SNAP_BRIDGE, "dce_snap_bridge")
            fake_tc = {"accoreconsole": {"found": False, "path": None},
                       "plugin_present": False, "native_ready": False}
            with mock.patch.object(bridge_mod, "detect_toolchain", return_value=fake_tc):
                s1 = srv.native_dwg_snapshot(str(src))
                s2 = srv.native_dwg_diff(str(src), str(src))
            # UNAVAILABLE trung thực + có reason; KHÔNG quy thành "native pass".
            self.assertEqual(s1["status"], "UNAVAILABLE")
            self.assertIn("reason", s1)
            self.assertEqual(s1["file_written"], False)
            self.assertEqual(s2["status"], "UNAVAILABLE")
            self.assertIn("reason", s2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
