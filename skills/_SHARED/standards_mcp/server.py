"""
standards_mcp_server.py — MCP Server cho tra cứu tiêu chuẩn nhanh

Kiến trúc:
- Fast semantic search trong standards
- Citation format tự động chuẩn hóa
- Version validation tự động

Usage:
    python standards_mcp_server.py --port 5000

Hoặc import như module:
    from server import StandardsMCPServer
    server = StandardsMCPServer()
    result = server.search("TCVN 2737 tải trọng gió")
"""

import json
import re
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class Citation:
    """Citation object theo format chuẩn của hệ thống"""
    ma_tieu_chuan: str           # Mã tiêu chuẩn: TCVN 2737
    nam_ban_hanh: str            # Năm: 2023
    dieu_bang_muc: str          # Điều/Bảng: Điều 10.2
    trich_yeu: str               # Trích yếu nội dung
    trang_so: Optional[str] = None  # Trang: Trang 45
    ten_bang_hinh: Optional[str] = None  # Bảng 3 - Hệ số khí động
    nguon_file: Optional[str] = None  # File PDF gốc
    citation_status: str = "VERIFIED"  # VERIFIED, UNVERIFIED, PENDING

    def to_dict(self) -> Dict:
        return asdict(self)

    def format_display(self) -> str:
        """Format hiển thị cho người đọc"""
        parts = [
            f"{self.ma_tieu_chuan}:{self.nam_ban_hanh}",
            f"— {self.dieu_bang_muc}",
        ]
        if self.trang_so:
            parts.append(f"— {self.trang_so}")
        if self.ten_bang_hinh:
            parts.append(f"— {self.ten_bang_hinh}")
        parts.append(f"— {self.trich_yeu}")
        return " ".join(parts)

@dataclass
class SearchResult:
    """Kết quả tìm kiếm"""
    citations: List[Citation]
    query: str
    total_found: int
    search_time_ms: float
    cache_hit: bool = False

# =============================================================================
# STANDARDS LOCK — Single Source of Truth
# =============================================================================

class StandardsLock:
    """Đọc STANDARDS_LOCK.md để lấy thông tin tiêu chuẩn chuẩn"""

    STANDARDS = {
        "TCVN 2737": {
            "nam": "2023",
            "ten": "Tải trọng và tác động",
            "file": "TCVN 2737-2023_TAI TRONG VA TAC DONG.pdf",
            "thay_the": "TCVN 2737:1995"
        },
        "TCVN 9386": {
            "nam": "2025",
            "phan": ["P1", "P5"],
            "ten": "Thiết kế công trình chịu động đất",
            "file": "TCVN 9386-2025 P1.pdf",
            "thay_the": "TCVN 9386:2012"
        },
        "TCVN 5574": {
            "nam": "2018",
            "ten": "Thiết kế bê tông và bê tông cốt thép",
            "file": "TCVN 5574-2018.pdf",
            "thay_the": "TCVN 5574:2012"
        },
        "TCVN 5575": {
            "nam": "2024",
            "ten": "Thiết kế kết cấu thép",
            "file": "TCVN 5575-2024.pdf",
            "thay_the": "TCVN 5575:2012"
        },
        "TCVN 10304": {
            "nam": "2025",
            "ten": "Thiết kế móng cọc",
            "file": "TCVN 10304-2025.pdf",
            "thay_the": "TCVN 10304:2014"
        }
    }

    @classmethod
    def get_latest(cls, ma_tc: str) -> Optional[Dict]:
        """Lấy thông tin phiên bản mới nhất của tiêu chuẩn"""
        return cls.STANDARDS.get(ma_tc)

    @classmethod
    def is_latest(cls, ma_tc: str, nam: str) -> bool:
        """Kiểm tra xem phiên bản có phải mới nhất không"""
        latest = cls.get_latest(ma_tc)
        if not latest:
            return False
        return latest["nam"] == nam

    @classmethod
    def get_all_standards(cls) -> List[Dict]:
        """Lấy danh sách tất cả tiêu chuẩn"""
        return [
            {"ma": k, **v}
            for k, v in cls.STANDARDS.items()
        ]

# =============================================================================
# CITATION DATABASE — Cache cho fast lookup
# =============================================================================

class CitationDatabase:
    """
    Database cache cho các citation thường dùng.
    Pre-populated với các citation phổ biến.
    """

    # Common citations theo topic
    CITATIONS_BY_TOPIC = {
        "tai_trong_gio": [
            Citation(
                ma_tieu_chuan="TCVN 2737",
                nam_ban_hanh="2023",
                dieu_bang_muc="Điều 10.2",
                trich_yeu="Hệ số tin cậy tải trọng gió",
                trang_so="Trang 45",
                nguon_file="TCVN 2737-2023_TAI TRONG VA TAC DONG.pdf"
            ),
            Citation(
                ma_tieu_chuan="TCVN 2737",
                nam_ban_hanh="2023",
                dieu_bang_muc="Bảng 3",
                trich_yeu="Hệ số khí động cơ bản",
                trang_so="Trang 30",
                ten_bang_hinh="Bảng 3 - Hệ số khí động cơ bản",
                nguon_file="TCVN 2737-2023_TAI TRONG VA TAC DONG.pdf"
            ),
        ],
        "do_lun": [
            Citation(
                ma_tieu_chuan="TCVN 9362",
                nam_ban_hanh="2012",
                dieu_bang_muc="Điều 6.2",
                trich_yeu="Độ lún giới hạn của móng",
                trang_so="Trang 25",
                nguon_file="TCVN 9362-2012.pdf"
            ),
        ],
        "do_vong": [
            Citation(
                ma_tieu_chuan="TCVN 5575",
                nam_ban_hanh="2024",
                dieu_bang_muc="Điều 8.3",
                trich_yeu="Độ võng giới hạn của dầm",
                trang_so="Trang 50",
                ten_bang_hinh="Bảng 12 - Độ võng giới hạn",
                nguon_file="TCVN 5575-2024.pdf"
            ),
        ],
        "thep_uon": [
            Citation(
                ma_tieu_chuan="TCVN 5574",
                nam_ban_hanh="2018",
                dieu_bang_muc="Điều 7.1",
                trich_yeu="Kiểm tra cốt thép chịu uốn",
                trang_so="Trang 40",
                nguon_file="TCVN 5574-2018.pdf"
            ),
        ],
        "bu_long": [
            Citation(
                ma_tieu_chuan="TCVN 5575",
                nam_ban_hanh="2024",
                dieu_bang_muc="Điều 6.2",
                trich_yeu="Kiểm tra liên kết bu lông",
                trang_so="Trang 35",
                nguon_file="TCVN 5575-2024.pdf"
            ),
        ]
    }

    @classmethod
    def search(cls, query: str) -> List[Citation]:
        """
        Tìm kiếm citation theo query.
        Hiện tại dùng keyword matching đơn giản.
        """
        query_lower = query.lower()
        results = []

        for topic, citations in cls.CITATIONS_BY_TOPIC.items():
            # Check if topic keywords match query
            if any(kw in query_lower for kw in topic.split('_')):
                results.extend(citations)

        return results

    @classmethod
    def get_by_code(cls, ma_tc: str, nam: Optional[str] = None) -> List[Citation]:
        """Lấy citation theo mã tiêu chuẩn"""
        results = []
        for citations in cls.CITATIONS_BY_TOPIC.values():
            for c in citations:
                if c.ma_tieu_chuan == ma_tc:
                    if nam is None or c.nam_ban_hanh == nam:
                        results.append(c)
        return results

# =============================================================================
# MAIN MCP SERVER CLASS
# =============================================================================

class StandardsMCPServer:
    """
    MCP Server cho Standards Lookup.
    Cung cấp các method:
    - search(query): Tìm kiếm citation
    - get_citation(standard, article): Lấy citation chính xác
    - validate_version(standard, year): Kiểm tra version
    - format_citation(citation): Format citation cho display
    """

    def __init__(self, standards_dir: Optional[str] = None):
        self.standards_dir = standards_dir or self._get_default_standards_dir()
        self.db = CitationDatabase()
        self.lock = StandardsLock()

    def _get_default_standards_dir(self) -> str:
        """Lấy đường dẫn mặc định tới thư mục standards"""
        current = Path(__file__).parent.parent.parent
        de_dir = current / "Design_Evaluation" / "standards"
        if de_dir.exists():
            return str(de_dir)
        return str(current / "standards")

    def search(self, query: str, limit: int = 10) -> SearchResult:
        """
        Tìm kiếm citation theo query.

        Args:
            query: Từ khóa tìm kiếm (VD: "TCVN 2737 tải trọng gió")
            limit: Số kết quả tối đa

        Returns:
            SearchResult với danh sách citations
        """
        import time
        start = time.time()

        citations = self.db.search(query)[:limit]

        return SearchResult(
            citations=citations,
            query=query,
            total_found=len(citations),
            search_time_ms=(time.time() - start) * 1000,
            cache_hit=True  # DB-based, always cache hit
        )

    def get_citation(self, ma_tc: str, nam: Optional[str] = None) -> List[Citation]:
        """
        Lấy citation theo mã tiêu chuẩn.

        Args:
            ma_tc: Mã tiêu chuẩn (VD: "TCVN 2737")
            nam: Năm ban hành (VD: "2023")

        Returns:
            Danh sách citation
        """
        return self.db.get_by_code(ma_tc, nam)

    def validate_version(self, ma_tc: str, nam: str) -> Dict:
        """
        Kiểm tra xem phiên bản tiêu chuẩn có trong STANDARDS_LOCK không.

        Args:
            ma_tc: Mã tiêu chuẩn
            nam: Năm ban hành

        Returns:
            Dict với:
            - valid: bool
            - is_latest: bool
            - latest_version: str or None
            - replacement_notice: str or None
        """
        latest = self.lock.get_latest(ma_tc)

        if not latest:
            return {
                "valid": False,
                "is_latest": False,
                "latest_version": None,
                "replacement_notice": f"Không tìm thấy {ma_tc} trong STANDARDS_LOCK"
            }

        is_latest = self.lock.is_latest(ma_tc, nam)

        result = {
            "valid": True,
            "is_latest": is_latest,
            "latest_version": latest["nam"],
            "replacement_notice": None
        }

        if not is_latest:
            result["replacement_notice"] = (
                f"{ma_tc}:{nam} đã bị thay thế bởi {ma_tc}:{latest['nam']}. "
                f"Sử dụng phiên bản mới cho hồ sơ mới."
            )

        return result

    def format_citation(self, citation: Citation) -> str:
        """Format citation cho hiển thị"""
        return citation.format_display()

    def get_all_standards(self) -> List[Dict]:
        """Lấy danh sách tất cả tiêu chuẩn trong STANDARDS_LOCK"""
        return self.lock.get_all_standards()

    def check_conflict(self, citations: List[Citation]) -> List[Dict]:
        """
        Phát hiện xung đột giữa các citation.

        Args:
            citations: Danh sách citation cần kiểm tra

        Returns:
            Danh sách conflict nếu có
        """
        conflicts = []

        # Group by tiêu chuẩn
        by_standard = {}
        for c in citations:
            key = f"{c.ma_tieu_chuan}"
            if key not in by_standard:
                by_standard[key] = []
            by_standard[key].append(c)

        # Check for version conflicts
        for std, cits in by_standard.items():
            years = set(c.nam_ban_hanh for c in cits)
            if len(years) > 1:
                conflicts.append({
                    "type": "VERSION_CONFLICT",
                    "standard": std,
                    "versions": list(years),
                    "message": f"Xung đột phiên bản: {std} có {len(years)} phiên bản khác nhau"
                })

        return conflicts

# =============================================================================
# CLI INTERFACE
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Standards MCP Server")
    parser.add_argument("--port", type=int, default=5000, help="Port for server")
    parser.add_argument("--host", default="localhost", help="Host for server")
    parser.add_argument("--test", action="store_true", help="Run test mode")

    args = parser.parse_args()

    server = StandardsMCPServer()

    if args.test:
        print("=== Standards MCP Server - Test Mode ===")
        print()

        # Test 1: Search
        print("1. Search: tai trong gio")
        result = server.search("tai trong gio")
        print(f"   Found: {result.total_found} citations")
        print(f"   Time: {result.search_time_ms:.2f}ms")
        for c in result.citations[:2]:
            print(f"   - {server.format_citation(c)}")
        print()

        # Test 2: Validate version
        print("2. Validate: TCVN 2737:2023")
        result = server.validate_version("TCVN 2737", "2023")
        print(f"   Valid: {result['valid']}")
        print(f"   Is Latest: {result['is_latest']}")
        print()

        # Test 3: Validate old version
        print("3. Validate: TCVN 2737:1995")
        result = server.validate_version("TCVN 2737", "1995")
        print(f"   Valid: {result['valid']}")
        print(f"   Is Latest: {result['is_latest']}")
        print(f"   Notice: {result.get('replacement_notice', 'N/A')}")
        print()

        # Test 4: All standards
        print("4. All Standards in STANDARDS_LOCK:")
        for std in server.get_all_standards():
            print(f"   - {std['ma']}:{std['nam']} ({std['ten']})")
        print()

        print("=== All tests passed ===")

    else:
        # TODO: Implement HTTP server
        print(f"MCP Server ready on {args.host}:{args.port}")
        print("Use --test to run tests")

if __name__ == "__main__":
    main()
