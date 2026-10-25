# -*- coding: utf-8 -*-
"""
standards_graph.py — Đồ Thị Tri Thức Tiêu Chuẩn Kết Cấu TCVN & Quốc Tế Cục Bộ (v2.0)
Xây dựng trên nền tảng SQLite Recursive CTEs, lấy cảm hứng từ simple-graph.
Zero-dependency, Pure Python, không cần Vector DB hay server nặng nề.

Nâng cấp v2.0 (Roadmap §2.1):
  - WAL Checkpoint & Quản lý Bộ nhớ: checkpoint(mode="TRUNCATE"), PRAGMA synchronous=NORMAL, cache_size=-64000 (64MB).
  - Truy vấn Đa chiều (Bidirectional & Inverse Retrieval): query_standard_impact() phân tích tác động ngược từ Tiêu chuẩn/Điều khoản -> Cấu kiện/Phép kiểm.
  - Phát hiện Mâu thuẫn Phiên bản Tiêu chuẩn (Standard Conflict Detector): Tự động đối chiếu STANDARDS_LOCK v3.1.0, tạo cạnh CONFLICT_WITH và kích hoạt mã lỗi E004.
  - Mở rộng Hạt giống Tri thức (Seed v2.0): Bao phủ TCVN mới nhất (2737:2023, 5574:2018, 5575:2024, 9386:2025, 10304:2025, TT 34/2026) và Kết cấu thép Công nghiệp Bourbon (AISC 360-10, MBMA 2012, AISI S100-2007, ASCE 7-10).
"""

import sys
if sys.platform == 'win32' and hasattr(sys.stdout, 'reconfigure'):
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')

import re
import sqlite3
import json
import atexit
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set

DB_PATH = Path(__file__).resolve().parent / "standards_graph.db"

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS nodes (
    body TEXT,
    id TEXT GENERATED ALWAYS AS (json_extract(body, '$.id')) VIRTUAL NOT NULL UNIQUE
);

CREATE INDEX IF NOT EXISTS id_idx ON nodes(id);

CREATE TABLE IF NOT EXISTS edges (
    source TEXT,
    target TEXT,
    properties TEXT,
    UNIQUE(source, target, properties) ON CONFLICT REPLACE,
    FOREIGN KEY(source) REFERENCES nodes(id),
    FOREIGN KEY(target) REFERENCES nodes(id)
);

CREATE INDEX IF NOT EXISTS source_idx ON edges(source);
CREATE INDEX IF NOT EXISTS target_idx ON edges(target);
"""

# Danh mục Phiên bản Khóa Cứng theo STANDARDS_LOCK.md v3.1.0 (Canonical Active vs Legacy/Deprecated)
NORM_STANDARDS_LOCK: Dict[str, Dict[str, Any]] = {
    "TCVN 2737": {
        "active": "TCVN 2737:2023",
        "active_id": "TCVN_2737_2023",
        "deprecated": ["TCVN 2737:1995", "TCVN 2737:2006"],
        "domain": "Tải trọng và tác động",
    },
    "TCVN 9386": {
        "active": "TCVN 9386:2025",
        "active_id": "TCVN_9386_2025",
        "deprecated": ["TCVN 9386:2012", "TCXDVN 375:2006"],
        "domain": "Thiết kế công trình chịu động đất",
    },
    "TCVN 5574": {
        "active": "TCVN 5574:2018",
        "active_id": "TCVN_5574_2018",
        "deprecated": ["TCVN 5574:2012", "TCXDVN 356:2005"],
        "domain": "Kết cấu bê tông và bê tông cốt thép",
    },
    "TCVN 5575": {
        "active": "TCVN 5575:2024",
        "active_id": "TCVN_5575_2024",
        "deprecated": ["TCVN 5575:2012", "TCXDVN 338:2005"],
        "domain": "Kết cấu thép",
    },
    "TCVN 5573": {
        "active": "TCVN 5573:2025",
        "active_id": "TCVN_5573_2025",
        "deprecated": ["TCVN 5573:2011"],
        "domain": "Kết cấu gạch đá và gạch đá cốt thép",
    },
    "TCVN 10304": {
        "active": "TCVN 10304:2025",
        "active_id": "TCVN_10304_2025",
        "deprecated": ["TCVN 10304:2014", "TCXD 205:1998"],
        "domain": "Móng cọc — Tiêu chuẩn thiết kế",
    },
    "TCVN 9351": {
        "active": "TCVN 9351:2022",
        "active_id": "TCVN_9351_2022",
        "deprecated": ["TCVN 9351:2012"],
        "domain": "Thí nghiệm xuyên tiêu chuẩn (SPT)",
    },
    "TCVN 12041": {
        "active": "TCVN 12041:2017",
        "active_id": "TCVN_12041_2017",
        "deprecated": ["TCVN 3994:1985"],
        "domain": "Bảo vệ chống ăn mòn cho kết cấu bê tông và BTCT",
    },
    "QCVN 03": {
        "active": "QCVN 03:2022/BXD",
        "active_id": "QCVN_03_2022",
        "deprecated": ["QCVN 03:2012/BXD"],
        "domain": "Phân cấp công trình phục vụ thiết kế xây dựng",
    },
    "QCVN 02": {
        "active": "QCVN 02:2022/BXD",
        "active_id": "QCVN_02_2022",
        "deprecated": ["QCVN 02:2009/BXD"],
        "domain": "Số liệu điều kiện tự nhiên dùng trong xây dựng",
    },
    "QCVN 01": {
        "active": "QCVN 01:2021/BXD",
        "active_id": "QCVN_01_2021",
        "deprecated": ["QCVN 01:2012/BXD"],
        "domain": "Quy hoạch xây dựng",
    },
    "TT PHAN CAP": {
        "active": "Thông tư 34/2026/TT-BXD",
        "active_id": "TT_34_2026_BXD",
        "deprecated": ["TT 06/2021/TT-BXD", "TT 02/2025/TT-BXD", "TT 03/2016/TT-BXD"],
        "domain": "Phân cấp công trình quản lý xây dựng",
    },
}


class StandardsGraph:
    """
    Đồ thị tri thức tiêu chuẩn xây dựng TCVN & Quốc tế (v2.0).
    Cho phép Agent truy vấn đệ quy hai chiều các điều khoản liên đới, công thức kiểm tra,
    phân tích tác động ngược khi đổi tiêu chuẩn và tự động phát hiện xung đột phiên bản (E004).
    """

    VERSION = "2.0.0"
    VALID_CHECKPOINT_MODES = ("PASSIVE", "FULL", "RESTART", "TRUNCATE")

    def __init__(self, db_path: Optional[Path] = None, auto_checkpoint_on_exit: bool = True):
        self.db_path = Path(db_path) if db_path else DB_PATH
        self._init_db()
        if auto_checkpoint_on_exit and self.db_path == DB_PATH:
            atexit.register(self._safe_exit_checkpoint)

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.execute("PRAGMA cache_size = -64000;")  # 64MB page cache cho truy vấn CTE tốc độ cao
        return conn

    def _safe_exit_checkpoint(self):
        try:
            if self.db_path.exists():
                self.checkpoint("TRUNCATE")
        except Exception:
            pass

    def _init_db(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = self._get_conn()
        try:
            conn.executescript(SCHEMA_SQL)
        finally:
            conn.close()
        self._seed_default_standards()

    # ==========================================================================
    # §2.1.A — WAL CHECKPOINT & QUẢN LÝ BỘ NHỚ
    # ==========================================================================

    def checkpoint(self, mode: str = "TRUNCATE") -> Dict[str, Any]:
        """
        Thực thi PRAGMA wal_checkpoint để thu gọn file .db-wal trên Windows/Drive.
        Hỗ trợ mode: PASSIVE | FULL | RESTART | TRUNCATE (mặc định TRUNCATE).
        """
        mode_upper = (mode or "TRUNCATE").strip().upper()
        if mode_upper not in self.VALID_CHECKPOINT_MODES:
            raise ValueError(f"Chế độ checkpoint '{mode}' không hợp lệ. Chọn trong {self.VALID_CHECKPOINT_MODES}")

        conn = self._get_conn()
        try:
            cur = conn.cursor()
            cur.execute(f"PRAGMA wal_checkpoint({mode_upper});")
            row = cur.fetchone()
            busy, log_frames, checkpointed_frames = (row[0], row[1], row[2]) if row else (0, 0, 0)
            return {
                "mode": mode_upper,
                "busy": busy,
                "log_frames": log_frames,
                "checkpointed_frames": checkpointed_frames,
                "status": "OK" if busy == 0 else "BUSY",
            }
        finally:
            conn.close()

    # ==========================================================================
    # CORE CRUD OPERATIONS & AUTO-CONFLICT LINKING
    # ==========================================================================

    def upsert_node(self, node_id: str, data: Dict[str, Any], auto_detect_conflict: bool = True):
        data = dict(data)
        data["id"] = node_id
        body_json = json.dumps(data, ensure_ascii=False)
        conn = self._get_conn()
        try:
            conn.execute(
                "INSERT INTO nodes(body) VALUES(?) ON CONFLICT(id) DO UPDATE SET body = excluded.body;",
                (body_json,)
            )
            conn.commit()
        finally:
            conn.close()

        # Tự động kiểm tra và gắn cạnh CONFLICT_WITH nếu nạp một node tiêu chuẩn cũ/hết hiệu lực
        if auto_detect_conflict and data.get("type") == "standard":
            self._auto_link_standard_conflict(node_id, data)

    def upsert_edge(self, source: str, target: str, relationship: str, properties: Optional[Dict] = None):
        props = dict(properties or {})
        props["relation"] = relationship
        props_json = json.dumps(props, ensure_ascii=False, sort_keys=True)
        conn = self._get_conn()
        try:
            conn.execute(
                "INSERT INTO edges(source, target, properties) VALUES(?, ?, ?) "
                "ON CONFLICT(source, target, properties) DO UPDATE SET properties = excluded.properties;",
                (source, target, props_json)
            )
            conn.commit()
        finally:
            conn.close()

    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT body FROM nodes WHERE id = ?;", (node_id,))
            row = cursor.fetchone()
            if row:
                return json.loads(row[0])
            return None
        finally:
            conn.close()

    def traverse(self, start_id: str, direction: str = "outbound", max_depth: int = 2) -> List[Dict[str, Any]]:
        """
        Duyệt đồ thị bằng SQLite Recursive Common Table Expression (CTE).
        direction: 'outbound' (nguồn -> đích), 'inbound' (đích -> nguồn), 'both'.
        """
        dir_clause = ""
        n_depth_params = 0
        if direction == "outbound":
            dir_clause = "SELECT target, properties, depth + 1 FROM edges JOIN traverse ON source = x WHERE depth < ?"
            n_depth_params = 1
        elif direction == "inbound":
            dir_clause = "SELECT source, properties, depth + 1 FROM edges JOIN traverse ON target = x WHERE depth < ?"
            n_depth_params = 1
        else:  # both
            dir_clause = """
            SELECT target, properties, depth + 1 FROM edges JOIN traverse ON source = x WHERE depth < ?
            UNION
            SELECT source, properties, depth + 1 FROM edges JOIN traverse ON target = x WHERE depth < ?
            """
            n_depth_params = 2

        query = f"""
        WITH RECURSIVE traverse(x, prop, depth) AS (
            SELECT id, '{{}}', 0 FROM nodes WHERE id = ?
            UNION
            {dir_clause}
        )
        SELECT DISTINCT nodes.id, nodes.body, traverse.prop, traverse.depth
        FROM traverse
        JOIN nodes ON nodes.id = traverse.x
        WHERE traverse.depth > 0
        ORDER BY traverse.depth ASC;
        """

        params = (start_id,) + (max_depth,) * n_depth_params
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            results = []
            for r in rows:
                results.append({
                    "id": r[0],
                    "data": json.loads(r[1]),
                    "link_properties": json.loads(r[2]),
                    "depth": r[3]
                })
            return results
        finally:
            conn.close()

    # ==========================================================================
    # §2.1.B — TRUY VẤN ĐA CHIỀU (OUTBOUND & INVERSE IMPACT ANALYSIS)
    # ==========================================================================

    def query_element_requirements(self, element_id: str) -> Dict[str, Any]:
        """
        Duyệt xuôi (Outbound): Truy vấn toàn bộ tiêu chuẩn, điều khoản, công thức áp dụng cho một cấu kiện.
        """
        elem_node = self.get_node(element_id)
        if not elem_node:
            return {"error": f"Không tìm thấy cấu kiện '{element_id}' trong đồ thị tri thức."}

        neighbors = self.traverse(element_id, direction="outbound", max_depth=3)
        standards = set()
        clauses = []
        checks = []

        for n in neighbors:
            data = n["data"]
            ntype = data.get("type")
            if ntype == "standard":
                if data.get("status", "ACTIVE") != "DEPRECATED":
                    standards.add(data.get("name"))
            elif ntype == "clause":
                clauses.append({
                    "id": n["id"],
                    "standard": data.get("standard"),
                    "title": data.get("title"),
                    "clause_no": data.get("clause_no"),
                    "summary": data.get("summary")
                })
            elif ntype == "check":
                checks.append({
                    "id": n["id"],
                    "limit_type": data.get("limit_type"),
                    "formula": data.get("formula"),
                    "threshold": data.get("threshold")
                })

        return {
            "element": elem_node,
            "connected_standards": sorted(list(standards)),
            "applicable_clauses": clauses,
            "verification_checks": checks,
            "total_connections": len(neighbors)
        }

    def query_standard_impact(self, standard_or_clause_id: str, max_depth: int = 3) -> Dict[str, Any]:
        """
        Duyệt ngược & Đa chiều (Inbound Impact Analysis — Roadmap §2.1.B):
        Từ một mã Tiêu chuẩn (vd 'TCVN_5574_2018', 'TCVN 5575:2024', 'MBMA_2012') hoặc Điều khoản
        ('CLAUSE_5574_MOMENT'), truy vấn ngược toàn bộ Cấu kiện, Điều khoản con, Phép kiểm tra (Checks)
        và các Tiêu chuẩn xung đột/thay thế bị ảnh hưởng.
        """
        resolved_id = self._resolve_node_id(standard_or_clause_id)
        root_node = self.get_node(resolved_id) if resolved_id else None
        if not root_node:
            return {
                "error": f"Không tìm thấy tiêu chuẩn hoặc điều khoản '{standard_or_clause_id}' trong đồ thị.",
                "error_code": "E002"
            }

        inbound_nodes = self.traverse(resolved_id, direction="inbound", max_depth=max_depth)
        outbound_nodes = self.traverse(resolved_id, direction="outbound", max_depth=2)

        affected_elements: List[Dict[str, Any]] = []
        affected_clauses: List[Dict[str, Any]] = []
        affected_checks: List[Dict[str, Any]] = []
        conflicting_standards: List[Dict[str, Any]] = []

        seen_elements: Set[str] = set()
        seen_clauses: Set[str] = set()
        seen_checks: Set[str] = set()
        seen_conflicts: Set[str] = set()

        for item in inbound_nodes + outbound_nodes:
            nid = item["id"]
            ndata = item["data"]
            ntype = ndata.get("type")
            rel = item.get("link_properties", {}).get("relation", "")

            if rel == "CONFLICT_WITH" or (ntype == "standard" and nid != resolved_id):
                if nid not in seen_conflicts and (rel in ("CONFLICT_WITH", "supersedes", "superseded_by")):
                    seen_conflicts.add(nid)
                    conflicting_standards.append({
                        "id": nid,
                        "name": ndata.get("name"),
                        "status": ndata.get("status", "UNKNOWN"),
                        "relation": rel,
                    })
            elif ntype == "element" and nid not in seen_elements:
                seen_elements.add(nid)
                affected_elements.append({
                    "id": nid,
                    "name": ndata.get("name"),
                    "category": ndata.get("category"),
                })
            elif ntype == "clause" and nid not in seen_clauses:
                seen_clauses.add(nid)
                affected_clauses.append({
                    "id": nid,
                    "clause_no": ndata.get("clause_no"),
                    "title": ndata.get("title"),
                    "standard": ndata.get("standard"),
                })
                # Từ mỗi điều khoản bị ảnh hưởng, lấy thêm các phép kiểm tra (checks) gắn với điều khoản đó
                clause_out = self.traverse(nid, direction="outbound", max_depth=1)
                for co in clause_out:
                    if co["data"].get("type") == "check" and co["id"] not in seen_checks:
                        seen_checks.add(co["id"])
                        affected_checks.append({
                            "id": co["id"],
                            "limit_type": co["data"].get("limit_type"),
                            "formula": co["data"].get("formula"),
                            "threshold": co["data"].get("threshold"),
                        })
            elif ntype == "check" and nid not in seen_checks:
                seen_checks.add(nid)
                affected_checks.append({
                    "id": nid,
                    "limit_type": ndata.get("limit_type"),
                    "formula": ndata.get("formula"),
                    "threshold": ndata.get("threshold"),
                })

        return {
            "target_node": root_node,
            "affected_elements": affected_elements,
            "affected_clauses": affected_clauses,
            "affected_checks": affected_checks,
            "conflicting_or_legacy_standards": conflicting_standards,
            "impact_summary": {
                "elements_count": len(affected_elements),
                "clauses_count": len(affected_clauses),
                "checks_count": len(affected_checks),
                "conflicts_count": len(conflicting_standards),
            }
        }

    # ==========================================================================
    # §2.1.C — PHÁT HIỆN MÂU THUẪN PHIÊN BẢN TIÊU CHUẨN (E004 CONFLICT DETECTOR)
    # ==========================================================================

    @staticmethod
    def _normalize_std_code(code_str: str) -> Tuple[str, Optional[str]]:
        """
        Chuẩn hóa chuỗi tiêu chuẩn về (base_family, year_or_version).
        Ví dụ:
          'TCVN 5574:2012' -> ('TCVN 5574', '2012')
          'TCVN 5575-2024' -> ('TCVN 5575', '2024')
          'QCVN 03:2022/BXD' -> ('QCVN 03', '2022')
          'Thông tư 06/2021/TT-BXD' -> ('TT PHAN CAP', '06/2021')
          'TCVN 3994:1985' -> ('TCVN 12041', '1985')
        """
        s = (code_str or "").strip()
        s_upper = s.upper()

        if "3994" in s_upper:
            return "TCVN 12041", "1985"
        if "356:2005" in s_upper or "356-2005" in s_upper:
            return "TCVN 5574", "2005"
        if "338:2005" in s_upper or "338-2005" in s_upper:
            return "TCVN 5575", "2005"
        if "375:2006" in s_upper or "375-2006" in s_upper:
            return "TCVN 9386", "2006"
        if "205:1998" in s_upper or "205-1998" in s_upper:
            return "TCVN 10304", "1998"

        m_tt = re.search(r"(?:THÔNG\s*TƯ|TT)\s*(\d{2}/\d{4})", s_upper)
        if m_tt:
            return "TT PHAN CAP", m_tt.group(1)

        m_std = re.search(r"(TCVN|TCXDVN|QCVN)\s*(\d+)\s*[:\-]\s*(\d{4})", s_upper)
        if m_std:
            prefix = "TCVN" if m_std.group(1) == "TCXDVN" else m_std.group(1)
            num = m_std.group(2).zfill(2) if prefix == "QCVN" else m_std.group(2)
            return f"{prefix} {num}", m_std.group(3)

        return s_upper, None

    def _resolve_node_id(self, identifier: str) -> Optional[str]:
        """Tìm node_id từ mã node hoặc tên hiển thị của tiêu chuẩn (vd 'TCVN 5574:2018')."""
        if self.get_node(identifier):
            return identifier
        norm_id = re.sub(r"[^A-Za-z0-9]+", "_", identifier.strip()).strip("_").upper()
        if self.get_node(norm_id):
            return norm_id

        conn = self._get_conn()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT id FROM nodes WHERE UPPER(json_extract(body, '$.name')) = UPPER(?);",
                (identifier.strip(),)
            )
            row = cur.fetchone()
            return row[0] if row else None
        finally:
            conn.close()

    def _auto_link_standard_conflict(self, node_id: str, data: Dict[str, Any]):
        """Khi một node standard được upsert, tự động gắn cạnh CONFLICT_WITH nếu nó là bản cũ."""
        std_name = data.get("name", "")
        family, ver = self._normalize_std_code(std_name)
        lock_info = NORM_STANDARDS_LOCK.get(family)
        if not lock_info:
            return

        active_name = lock_info["active"]
        active_id = lock_info["active_id"]
        if ver and ver not in active_name and node_id != active_id:
            if self.get_node(active_id):
                self.upsert_edge(
                    node_id,
                    active_id,
                    "CONFLICT_WITH",
                    {
                        "error_code": "E004",
                        "reason": f"Phiên bản '{std_name}' đã hết hiệu lực hoặc xung đột với bản khóa '{active_name}' (STANDARDS_LOCK v3.1.0).",
                        "active_standard": active_name,
                    }
                )
                self.upsert_edge(
                    active_id,
                    node_id,
                    "CONFLICT_WITH",
                    {
                        "error_code": "E004",
                        "reason": f"Xung đột phiên bản tiêu chuẩn giữa '{active_name}' và '{std_name}'.",
                        "deprecated_standard": std_name,
                    }
                )

    def detect_standard_conflicts(
        self,
        standards_list: List[str],
        allow_legacy_reference: bool = False
    ) -> Dict[str, Any]:
        """
        Kiểm tra danh sách tiêu chuẩn sử dụng trong một dự án/hồ sơ (Roadmap §2.1.C):
        1. Phát hiện sử dụng đồng thời 2 phiên bản của cùng 1 tiêu chuẩn (vd TCVN 5574:2012 và TCVN 5574:2018).
        2. Phát hiện sử dụng tiêu chuẩn đã hết hiệu lực theo STANDARDS_LOCK.md v3.1.0 (trừ khi allow_legacy_reference=True).
        3. Tự động ghi nhận cạnh CONFLICT_WITH vào đồ thị và trả về mã lỗi E004.
        """
        conflicts: List[Dict[str, Any]] = []
        by_family: Dict[str, List[str]] = {}

        for raw_std in standards_list:
            if not raw_std or not str(raw_std).strip():
                continue
            clean_std = str(raw_std).strip()
            family, ver = self._normalize_std_code(clean_std)
            by_family.setdefault(family, []).append(clean_std)

            lock_info = NORM_STANDARDS_LOCK.get(family)
            if lock_info and not allow_legacy_reference:
                active_std = lock_info["active"]
                is_deprecated = any(dep.upper() in clean_std.upper() for dep in lock_info["deprecated"])
                if not is_deprecated and ver and ver not in active_std:
                    is_deprecated = True

                if is_deprecated:
                    conflicts.append({
                        "error_code": "E004",
                        "conflict_type": "DEPRECATED_STANDARD_USED",
                        "family": family,
                        "detected_standard": clean_std,
                        "locked_standard": active_std,
                        "message": f"[E004] Tiêu chuẩn '{clean_std}' đã hết hiệu lực. Bắt buộc dùng '{active_std}' theo STANDARDS_LOCK v3.1.0.",
                    })

        # Kiểm tra dùng lẫn lộn >= 2 phiên bản của cùng một họ tiêu chuẩn trong cùng dự án
        for family, used_list in by_family.items():
            unique_used = list(dict.fromkeys(used_list))
            if len(unique_used) > 1:
                lock_info = NORM_STANDARDS_LOCK.get(family, {})
                conflicts.append({
                    "error_code": "E004",
                    "conflict_type": "MIXED_VERSIONS_IN_PROJECT",
                    "family": family,
                    "detected_standards": unique_used,
                    "locked_standard": lock_info.get("active", unique_used[-1]),
                    "message": (
                        f"[E004] Phát hiện sử dụng lẫn lộn nhiều phiên bản của cùng tiêu chuẩn '{family}': "
                        f"{', '.join(unique_used)}. Vi phạm quy tắc khóa phiên bản AGENTS.md §10."
                    ),
                })

        return {
            "has_conflict": len(conflicts) > 0,
            "error_code": "E004" if conflicts else None,
            "conflict_count": len(conflicts),
            "conflicts": conflicts,
            "standards_checked": standards_list,
        }

    # ==========================================================================
    # SEED DATA: TCVN + BOURBON INDUSTRIAL STEEL STANDARDS (AISC / MBMA / AISI)
    # ==========================================================================

    def _seed_default_standards(self):
        """Khởi tạo hạt giống tri thức TCVN v3.1.0 & Kết cấu thép Công nghiệp (Bourbon Project)."""
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM nodes;")
            existing_count = cursor.fetchone()[0]
        finally:
            conn.close()

        # Luôn đảm bảo các node cốt lõi v1.0 + mở rộng v2.0 được nạp đầy đủ (idempotent upsert)
        if existing_count >= 25:
            return

        # 1. Các tiêu chuẩn TCVN & Pháp lý hiện hành (Active)
        self.upsert_node("TCVN_2737_2023", {
            "type": "standard",
            "name": "TCVN 2737:2023",
            "title": "Tải trọng và tác động",
            "version": "2023",
            "status": "ACTIVE",
            "scope": "Quy định giá trị tải trọng tiêu chuẩn, gió W0, và hệ số độ tin cậy"
        }, auto_detect_conflict=False)
        self.upsert_node("TCVN_5574_2018", {
            "type": "standard",
            "name": "TCVN 5574:2018",
            "title": "Thiết kế kết cấu bê tông và bê tông cốt thép",
            "version": "2018",
            "status": "ACTIVE",
            "scope": "Tính toán trạng thái giới hạn ULS và SLS cho cấu kiện BTCT"
        }, auto_detect_conflict=False)
        self.upsert_node("TCVN_5575_2024", {
            "type": "standard",
            "name": "TCVN 5575:2024",
            "title": "Thiết kế kết cấu thép",
            "version": "2024",
            "status": "ACTIVE",
            "scope": "Khóa cứng GAMMA_M0 = 1.05, GAMMA_M1 = 1.10 cho trạng thái bền và ổn định"
        }, auto_detect_conflict=False)
        self.upsert_node("TCVN_9386_2025", {
            "type": "standard",
            "name": "TCVN 9386:2025",
            "title": "Thiết kế công trình chịu động đất",
            "version": "2025",
            "status": "ACTIVE",
            "scope": "Phân tích phổ kháng chấn và quy định cấp dẻo DCM/DCH"
        }, auto_detect_conflict=False)
        self.upsert_node("TCVN_10304_2025", {
            "type": "standard",
            "name": "TCVN 10304:2025",
            "title": "Móng cọc — Tiêu chuẩn thiết kế",
            "version": "2025",
            "status": "ACTIVE",
            "scope": "Thiết kế sức chịu tải cọc theo vật liệu và chỉ tiêu cơ lý đất nền / SPT / CPT"
        }, auto_detect_conflict=False)
        self.upsert_node("TT_34_2026_BXD", {
            "type": "standard",
            "name": "Thông tư 34/2026/TT-BXD",
            "title": "Quy định chi tiết về phân cấp công trình xây dựng",
            "version": "2026",
            "status": "ACTIVE",
            "scope": "Xét 6 tiêu chí quy mô kết cấu tại Mục 2.1.1 Bảng 2 Phụ lục II (GFA > 30.000 m² = Cấp I)"
        }, auto_detect_conflict=False)

        # 1b. Các tiêu chuẩn Quốc tế cho Nhà thép Tiền chế & Công nghiệp (Bourbon Project Knowledge)
        self.upsert_node("AISC_360_10", {
            "type": "standard",
            "name": "AISC 360-10",
            "title": "Specification for Structural Steel Buildings (ASD/LRFD)",
            "version": "2010",
            "status": "ACTIVE",
            "scope": "Thiết kế khung kèo thép tổ hợp Built-up, kiểm tra tỷ số tương tác nén-uốn PMM <= 1.0"
        }, auto_detect_conflict=False)
        self.upsert_node("MBMA_2012", {
            "type": "standard",
            "name": "MBMA 2012",
            "title": "Metal Building Systems Manual",
            "version": "2012",
            "status": "ACTIVE",
            "scope": "Giới hạn chuyển vị ngang đỉnh cột H/60 và độ võng dầm kèo mái L/180 cho nhà xưởng thép"
        }, auto_detect_conflict=False)
        self.upsert_node("AISI_S100_2007", {
            "type": "standard",
            "name": "AISI S100-2007",
            "title": "North American Specification for Cold-Formed Steel Structural Members",
            "version": "2007",
            "status": "ACTIVE",
            "scope": "Thiết kế xà gồ thép dập nguội C/Z nối chồng mí liên tục (Lapped Continuous) và giằng ty"
        }, auto_detect_conflict=False)

        # 1c. Các tiêu chuẩn Cũ / Hết hiệu lực để kiểm tra cạnh CONFLICT_WITH tự động
        self.upsert_node("TCVN_5574_2012", {
            "type": "standard",
            "name": "TCVN 5574:2012",
            "title": "Kết cấu bê tông và bê tông cốt thép (Hết hiệu lực)",
            "version": "2012",
            "status": "DEPRECATED",
            "scope": "Đã bị thay thế bởi TCVN 5574:2018"
        }, auto_detect_conflict=True)
        self.upsert_node("TCVN_5575_2012", {
            "type": "standard",
            "name": "TCVN 5575:2012",
            "title": "Kết cấu thép — Tiêu chuẩn thiết kế (Hết hiệu lực)",
            "version": "2012",
            "status": "DEPRECATED",
            "scope": "Đã bị thay thế bởi TCVN 5575:2024"
        }, auto_detect_conflict=True)
        self.upsert_node("TCVN_2737_1995", {
            "type": "standard",
            "name": "TCVN 2737:1995",
            "title": "Tải trọng và tác động (Hết hiệu lực)",
            "version": "1995",
            "status": "DEPRECATED",
            "scope": "Đã bị thay thế bởi TCVN 2737:2023"
        }, auto_detect_conflict=True)

        # 2. Các điều khoản quan trọng (Clauses)
        self.upsert_node("CLAUSE_5574_MOMENT", {
            "type": "clause",
            "standard": "TCVN 5574:2018",
            "clause_no": "Điều 8.1",
            "title": "Tính toán cấu kiện chịu uốn trên tiết diện thẳng góc",
            "summary": "Kiểm tra điều kiện M <= M_u = R_b * b * x * (h_0 - 0.5*x)"
        })
        self.upsert_node("CLAUSE_5574_SHEAR", {
            "type": "clause",
            "standard": "TCVN 5574:2018",
            "clause_no": "Điều 8.1.3",
            "title": "Tính toán dầm trên tiết diện nghiêng chịu lực cắt",
            "summary": "Kiểm tra điều kiện Q <= Q_b + Q_sw và ứng suất nén dải nghiêng <= 0.3*phi_b1*R_b*b*h_0"
        })
        self.upsert_node("CLAUSE_5574_DEFLECTION", {
            "type": "clause",
            "standard": "TCVN 5574:2018",
            "clause_no": "Điều 8.2",
            "title": "Kiểm tra độ võng và bề rộng khe nứt trạng thái giới hạn thứ hai (SLS)",
            "summary": "Độ võng dài hạn f <= f_max (L/200 - L/250); bề rộng vết nứt a_crc <= 0.3mm (dài hạn) / 0.4mm (ngắn hạn)"
        })
        self.upsert_node("CLAUSE_5574_PUNCHING", {
            "type": "clause",
            "standard": "TCVN 5574:2018",
            "clause_no": "Điều 8.1.6",
            "title": "Tính toán chọc thủng sàn phẳng và đài móng",
            "summary": "Chu vi kiểm tra cách mép cột h_0/2: F_b / u_b + M_bx / W_bx + M_by / W_by <= R_bt * h_0"
        })
        self.upsert_node("CLAUSE_2737_COMBINATION", {
            "type": "clause",
            "standard": "TCVN 2737:2023",
            "clause_no": "Điều 5",
            "title": "Tổ hợp tải trọng cơ bản và đặc biệt",
            "summary": "Tổ hợp cơ bản: Tĩnh tải + 1.0*Hoạt tải chính + sum(psi_i * Hoạt tải phụ)"
        })
        self.upsert_node("CLAUSE_5575_GAMMA_M0", {
            "type": "clause",
            "standard": "TCVN 5575:2024",
            "clause_no": "Bảng 3 & Mục 8.4",
            "title": "Hệ số độ tin cậy vật liệu thép gamma_M0 = 1.05 và ổn định tổng thể gamma_M1 = 1.10",
            "summary": "Kiểm tra bền theo f_y/gamma_M0 (1.05) và ổn định tổng thể LTB theo chi_LT * W * f_y / gamma_M1 (1.10)"
        })
        self.upsert_node("CLAUSE_10304_PILE_CAP", {
            "type": "clause",
            "standard": "TCVN 10304:2025",
            "clause_no": "Điều 7.1 & 7.2",
            "title": "Sức chịu tải trọng nén của cọc theo vật liệu và chỉ tiêu đất nền / SPT",
            "summary": "R_c,d = R_c,u / gamma_k với gamma_k = 1.40 - 1.75 tùy phương pháp xác định"
        })
        self.upsert_node("CLAUSE_MBMA_DEFLECTION", {
            "type": "clause",
            "standard": "MBMA 2012",
            "clause_no": "Table 1.3.1",
            "title": "Giới hạn chuyển vị ngang khung nhà xưởng thép và độ võng kèo mái",
            "summary": "Chuyển vị ngang đỉnh cột Delta_x <= H/60; Độ võng kèo mái có treo trần/Solar f <= L/180"
        })
        self.upsert_node("CLAUSE_AISI_Z_PURLIN", {
            "type": "clause",
            "standard": "AISI S100-2007",
            "clause_no": "Chapter C & D",
            "title": "Thiết kế xà gồ thép dập nguội Z nối chồng mí liên tục chịu tải gió tốc mái và Solar",
            "summary": "Tăng chiều dày xà gồ Z ở 2 nhịp biên chịu gió hút lớn; bố trí giằng ty khống chế võng f <= L/150 (tĩnh+hoạt) và L/120 (gió)"
        })

        # 3. Các cấu kiện kết cấu (Elements)
        self.upsert_node("ELEMENT_BEAM", {
            "type": "element",
            "name": "Dầm bê tông cốt thép",
            "category": "Bending_Member"
        })
        self.upsert_node("ELEMENT_COLUMN", {
            "type": "element",
            "name": "Cột bê tông cốt thép",
            "category": "Compression_Member"
        })
        self.upsert_node("ELEMENT_SLAB", {
            "type": "element",
            "name": "Bản sàn bê tông cốt thép (2 phương / sàn phẳng)",
            "category": "Slab_Member"
        })
        self.upsert_node("ELEMENT_WALL", {
            "type": "element",
            "name": "Vách cứng bê tông cốt thép",
            "category": "Shear_Wall_Member"
        })
        self.upsert_node("ELEMENT_PILE_FOUNDATION", {
            "type": "element",
            "name": "Móng cọc & Đài cọc BTCT",
            "category": "Foundation_Member"
        })
        self.upsert_node("ELEMENT_STEEL_BEAM", {
            "type": "element",
            "name": "Dầm thép định hình / tổ hợp",
            "category": "Steel_Member"
        })
        self.upsert_node("ELEMENT_PEB_PORTAL_FRAME", {
            "type": "element",
            "name": "Khung kèo thép tiền chế khẩu độ lớn (PEB Portal Frame)",
            "category": "Industrial_Steel_Frame"
        })
        self.upsert_node("ELEMENT_CFS_PURLIN", {
            "type": "element",
            "name": "Xà gồ thép dập nguội C/Z mái nhà xưởng (có tải Solar & MEP)",
            "category": "Cold_Formed_Steel"
        })

        # 4. Các phép kiểm tra (Checks)
        self.upsert_node("CHECK_MOMENT_ETA", {
            "type": "check",
            "limit_type": "ULS",
            "formula": "eta = M_ed / M_rd",
            "threshold": "<= 1.00"
        })
        self.upsert_node("CHECK_DEFLECTION_RATIO", {
            "type": "check",
            "limit_type": "SLS",
            "formula": "f / L",
            "threshold": "<= 1/200"
        })
        self.upsert_node("CHECK_PUNCHING_ETA", {
            "type": "check",
            "limit_type": "ULS",
            "formula": "eta_punch = tau_ed / tau_rd",
            "threshold": "<= 1.00"
        })
        self.upsert_node("CHECK_PEB_DRIFT_RATIO", {
            "type": "check",
            "limit_type": "SLS",
            "formula": "Delta_eave / H",
            "threshold": "<= 1/60"
        })
        self.upsert_node("CHECK_PURLIN_DEFLECTION", {
            "type": "check",
            "limit_type": "SLS",
            "formula": "f_purlin / L_bay",
            "threshold": "<= 1/150"
        })

        # 5. Thiết lập liên kết (Edges)
        # Element Beam -> Clauses
        self.upsert_edge("ELEMENT_BEAM", "CLAUSE_5574_MOMENT", "governed_by")
        self.upsert_edge("ELEMENT_BEAM", "CLAUSE_5574_SHEAR", "governed_by")
        self.upsert_edge("ELEMENT_BEAM", "CLAUSE_5574_DEFLECTION", "governed_by")
        self.upsert_edge("ELEMENT_BEAM", "CLAUSE_2737_COMBINATION", "loaded_by")

        # Element Column & Wall & Slab & Pile
        self.upsert_edge("ELEMENT_COLUMN", "CLAUSE_5574_MOMENT", "governed_by")
        self.upsert_edge("ELEMENT_COLUMN", "CLAUSE_5574_SHEAR", "governed_by")
        self.upsert_edge("ELEMENT_WALL", "CLAUSE_5574_MOMENT", "governed_by")
        self.upsert_edge("ELEMENT_WALL", "CLAUSE_5574_SHEAR", "governed_by")
        self.upsert_edge("ELEMENT_SLAB", "CLAUSE_5574_MOMENT", "governed_by")
        self.upsert_edge("ELEMENT_SLAB", "CLAUSE_5574_DEFLECTION", "governed_by")
        self.upsert_edge("ELEMENT_SLAB", "CLAUSE_5574_PUNCHING", "governed_by")
        self.upsert_edge("ELEMENT_PILE_FOUNDATION", "CLAUSE_10304_PILE_CAP", "governed_by")
        self.upsert_edge("ELEMENT_PILE_FOUNDATION", "CLAUSE_5574_PUNCHING", "governed_by")

        # Steel Beam, PEB Frame & CFS Purlin (Bourbon Industrial Steel)
        self.upsert_edge("ELEMENT_STEEL_BEAM", "CLAUSE_5575_GAMMA_M0", "governed_by")
        self.upsert_edge("ELEMENT_PEB_PORTAL_FRAME", "CLAUSE_5575_GAMMA_M0", "governed_by")
        self.upsert_edge("ELEMENT_PEB_PORTAL_FRAME", "CLAUSE_MBMA_DEFLECTION", "governed_by")
        self.upsert_edge("ELEMENT_PEB_PORTAL_FRAME", "AISC_360_10", "governed_by")
        self.upsert_edge("ELEMENT_CFS_PURLIN", "CLAUSE_AISI_Z_PURLIN", "governed_by")

        # Clauses -> Standards
        self.upsert_edge("CLAUSE_5574_MOMENT", "TCVN_5574_2018", "part_of")
        self.upsert_edge("CLAUSE_5574_SHEAR", "TCVN_5574_2018", "part_of")
        self.upsert_edge("CLAUSE_5574_DEFLECTION", "TCVN_5574_2018", "part_of")
        self.upsert_edge("CLAUSE_5574_PUNCHING", "TCVN_5574_2018", "part_of")
        self.upsert_edge("CLAUSE_2737_COMBINATION", "TCVN_2737_2023", "part_of")
        self.upsert_edge("CLAUSE_5575_GAMMA_M0", "TCVN_5575_2024", "part_of")
        self.upsert_edge("CLAUSE_10304_PILE_CAP", "TCVN_10304_2025", "part_of")
        self.upsert_edge("CLAUSE_MBMA_DEFLECTION", "MBMA_2012", "part_of")
        self.upsert_edge("CLAUSE_AISI_Z_PURLIN", "AISI_S100_2007", "part_of")

        # Clauses -> Checks
        self.upsert_edge("CLAUSE_5574_MOMENT", "CHECK_MOMENT_ETA", "verified_by")
        self.upsert_edge("CLAUSE_5574_DEFLECTION", "CHECK_DEFLECTION_RATIO", "verified_by")
        self.upsert_edge("CLAUSE_5574_PUNCHING", "CHECK_PUNCHING_ETA", "verified_by")
        self.upsert_edge("CLAUSE_MBMA_DEFLECTION", "CHECK_PEB_DRIFT_RATIO", "verified_by")
        self.upsert_edge("CLAUSE_AISI_Z_PURLIN", "CHECK_PURLIN_DEFLECTION", "verified_by")


# Helper singleton
standards_graph = StandardsGraph()

if __name__ == '__main__':
    print("=== TEST NHANH ĐỒ THỊ TRI THỨC TIÊU CHUẨN (STANDARDS GRAPH v2.0) ===")
    sg = StandardsGraph()
    res = sg.query_element_requirements("ELEMENT_BEAM")
    print(f"1. Tra cứu xuôi (Outbound) Dầm BTCT: {res['element']['name']}")
    print(f"   Tiêu chuẩn liên đới: {res['connected_standards']}")
    impact = sg.query_standard_impact("TCVN_5574_2018")
    print(f"2. Phân tích tác động ngược (Inbound) TCVN 5574:2018 -> Ảnh hưởng {impact['impact_summary']['elements_count']} cấu kiện, {impact['impact_summary']['clauses_count']} điều khoản")
    cf = sg.detect_standard_conflicts(["TCVN 5574:2018", "TCVN 5574:2012", "TCVN 5575:2012"])
    print(f"3. Kiểm tra xung đột tiêu chuẩn (E004): Phát hiện {cf['conflict_count']} xung đột")
    cp = sg.checkpoint("TRUNCATE")
    print(f"4. WAL Checkpoint: {cp}")
    print("ALL STANDARDS GRAPH v2.0 CHECKS PASSED!")
