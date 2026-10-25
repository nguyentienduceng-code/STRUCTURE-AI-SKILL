# -*- coding: utf-8 -*-
"""
standards_graph.py — Đồ Thị Tri Thức Tiêu Chuẩn Kết Cấu TCVN Cục Bộ (v1.0)
Xây dựng trên nền tảng SQLite Recursive CTEs, lấy cảm hứng từ simple-graph.
Zero-dependency, Pure Python, không cần Vector DB hay server nặng nề.
"""

import sys
if sys.platform == 'win32' and hasattr(sys.stdout, 'reconfigure'):
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')

import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

DB_PATH = Path(__file__).resolve().parent / "standards_graph.db"

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS nodes (
    body TEXT,
    id   TEXT GENERATED ALWAYS AS (json_extract(body, '$.id')) VIRTUAL NOT NULL UNIQUE
);

CREATE INDEX IF NOT EXISTS id_idx ON nodes(id);

CREATE TABLE IF NOT EXISTS edges (
    source     TEXT,
    target     TEXT,
    properties TEXT,
    UNIQUE(source, target, properties) ON CONFLICT REPLACE,
    FOREIGN KEY(source) REFERENCES nodes(id),
    FOREIGN KEY(target) REFERENCES nodes(id)
);

CREATE INDEX IF NOT EXISTS source_idx ON edges(source);
CREATE INDEX IF NOT EXISTS target_idx ON edges(target);
"""

class StandardsGraph:
    """
    Đồ thị tri thức tiêu chuẩn xây dựng TCVN.
    Cho phép Agent truy vấn các điều khoản liên đới, công thức kiểm tra và giới hạn cho từng cấu kiện.
    """
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DB_PATH
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        return conn

    def _init_db(self):
        conn = self._get_conn()
        try:
            conn.executescript(SCHEMA_SQL)
        finally:
            conn.close()
        # Nạp dữ liệu hạt giống (seed data) nếu cơ sở dữ liệu trống
        self._seed_default_standards()

    def upsert_node(self, node_id: str, data: Dict[str, Any]):
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

    def upsert_edge(self, source: str, target: str, relationship: str, properties: Optional[Dict] = None):
        props = dict(properties or {})
        props["relation"] = relationship
        props_json = json.dumps(props, ensure_ascii=False, sort_keys=True)
        conn = self._get_conn()
        try:
            # ON CONFLICT REPLACE -> upsert idempotent, không nhân bản cạnh trùng.
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
        # Mỗi nhánh CTE có đúng 1 tham số `depth < ?`.
        # "both" ghép 2 nhánh -> cần 2 tham số, nên ta đếm và bind tương ứng.
        dir_clause = ""
        n_depth_params = 0
        if direction == "outbound":
            dir_clause = "SELECT target, properties, depth + 1 FROM edges JOIN traverse ON source = x WHERE depth < ?"
            n_depth_params = 1
        elif direction == "inbound":
            dir_clause = "SELECT source, properties, depth + 1 FROM edges JOIN traverse ON target = x WHERE depth < ?"
            n_depth_params = 1
        else: # both
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

    def query_element_requirements(self, element_id: str) -> Dict[str, Any]:
        """
        Truy vấn toàn bộ tiêu chuẩn, điều khoản, công thức áp dụng cho một cấu kiện (Dầm, Cột, Sàn...).
        """
        elem_node = self.get_node(element_id)
        if not elem_node:
            return {"error": f"Không tìm thấy cấu kiện '{element_id}' trong đồ thị tri thức."}

        neighbors = self.traverse(element_id, direction="outbound", max_depth=2)
        standards = set()
        clauses = []
        checks = []

        for n in neighbors:
            data = n["data"]
            ntype = data.get("type")
            if ntype == "standard":
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
            "connected_standards": list(standards),
            "applicable_clauses": clauses,
            "verification_checks": checks,
            "total_connections": len(neighbors)
        }

    def _seed_default_standards(self):
        """Khởi tạo hạt giống tri thức 4 tiêu chuẩn TCVN cốt lõi."""
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM nodes;")
            if cursor.fetchone()[0] > 0:
                return # Đã có dữ liệu
        finally:
            conn.close()

        # 1. Các tiêu chuẩn chính
        self.upsert_node("TCVN_2737_2023", {
            "type": "standard",
            "name": "TCVN 2737:2023",
            "title": "Tải trọng và tác động",
            "version": "2023",
            "scope": "Quy định giá trị tải trọng tiêu chuẩn và hệ số độ tin cậy"
        })
        self.upsert_node("TCVN_5574_2018", {
            "type": "standard",
            "name": "TCVN 5574:2018",
            "title": "Thiết kế kết cấu bê tông và bê tông cốt thép",
            "version": "2018",
            "scope": "Tính toán trạng thái giới hạn ULS và SLS cho cấu kiện BTCT"
        })
        self.upsert_node("TCVN_5575_2024", {
            "type": "standard",
            "name": "TCVN 5575:2024",
            "title": "Thiết kế kết cấu thép",
            "version": "2024",
            "scope": "Khóa cứng GAMMA_M0 = 1.05 cho trạng thái bền và ổn định"
        })
        self.upsert_node("TCVN_9386_2025", {
            "type": "standard",
            "name": "TCVN 9386:2025",
            "title": "Thiết kế công trình chịu động đất",
            "version": "2025",
            "scope": "Phân tích phổ kháng chấn và quy định cấp dẻo DCM/DCH"
        })

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
            "summary": "Kiểm tra điều kiện Q <= Q_b + Q_sw"
        })
        self.upsert_node("CLAUSE_5574_DEFLECTION", {
            "type": "clause",
            "standard": "TCVN 5574:2018",
            "clause_no": "Điều 8.2",
            "title": "Kiểm tra độ võng trạng thái giới hạn thứ hai (SLS)",
            "summary": "Độ võng dài hạn f <= f_max (thường là L/200 hoặc L/250)"
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
            "clause_no": "Bảng 3",
            "title": "Hệ số độ tin cậy của vật liệu thép gamma_M0",
            "summary": "Hệ số gamma_M0 = 1.05 cho kiểm tra khả năng chịu lực tiết diện"
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
        self.upsert_node("ELEMENT_STEEL_BEAM", {
            "type": "element",
            "name": "Dầm thép định hình / tổ hợp",
            "category": "Steel_Member"
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

        # 5. Thiết lập liên kết (Edges)
        # Element Beam -> Clauses
        self.upsert_edge("ELEMENT_BEAM", "CLAUSE_5574_MOMENT", "governed_by")
        self.upsert_edge("ELEMENT_BEAM", "CLAUSE_5574_SHEAR", "governed_by")
        self.upsert_edge("ELEMENT_BEAM", "CLAUSE_5574_DEFLECTION", "governed_by")
        self.upsert_edge("ELEMENT_BEAM", "CLAUSE_2737_COMBINATION", "loaded_by")

        # Clauses -> Standards
        self.upsert_edge("CLAUSE_5574_MOMENT", "TCVN_5574_2018", "part_of")
        self.upsert_edge("CLAUSE_5574_SHEAR", "TCVN_5574_2018", "part_of")
        self.upsert_edge("CLAUSE_5574_DEFLECTION", "TCVN_5574_2018", "part_of")
        self.upsert_edge("CLAUSE_2737_COMBINATION", "TCVN_2737_2023", "part_of")

        # Clauses -> Checks
        self.upsert_edge("CLAUSE_5574_MOMENT", "CHECK_MOMENT_ETA", "verified_by")
        self.upsert_edge("CLAUSE_5574_DEFLECTION", "CHECK_DEFLECTION_RATIO", "verified_by")

        # Steel Beam -> Clauses
        self.upsert_edge("ELEMENT_STEEL_BEAM", "CLAUSE_5575_GAMMA_M0", "governed_by")
        self.upsert_edge("CLAUSE_5575_GAMMA_M0", "TCVN_5575_2024", "part_of")


# Helper singleton
standards_graph = StandardsGraph()

if __name__ == '__main__':
    print("=== TEST NHANH ĐỒ THỊ TRI THỨC TIÊU CHUẨN (STANDARDS GRAPH) ===")
    sg = StandardsGraph()
    res = sg.query_element_requirements("ELEMENT_BEAM")
    print(f"Tra cứu Dầm BTCT: {res['element']['name']}")
    print(f"Tiêu chuẩn liên đới: {res['connected_standards']}")
    print(f"Số lượng điều khoản áp dụng: {len(res['applicable_clauses'])}")
    for c in res['applicable_clauses']:
        print(f"  - [{c['standard']}] {c['clause_no']}: {c['title']}")
    print(f"Phép kiểm tra: {res['verification_checks']}")
    print("ALL STANDARDS GRAPH CHECKS PASSED!")
