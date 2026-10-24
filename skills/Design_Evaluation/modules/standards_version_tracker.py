import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
import json


class StandardsVersionTracker:
    def __init__(self):
        self.standards_db = {
            "TCVN 2737": ["2023", "2020", "1995"],
            "TCVN 5574": ["2018", "2012"],
            "TCVN 5575": ["2024", "2012"],
            "TCVN 5573": ["2025", "2011"],
            "TCVN 9386": ["2025", "2012"],
            "TCVN 10304": ["2025", "2014"],
            "TCVN 9362": ["2012"],
            "TCVN 9363": ["2012"],
            "TCVN 4419": ["1987"],
            "TCVN 9351": ["2022", "2012"],
            "TCVN 12041": ["2017"],
            "TCVN 9346": ["2012"],
            "QCVN 03": ["2022/BXD", "2012/BXD"],
            "TT Phân cấp BXD": ["34/2026/TT-BXD", "02/2025/TT-BXD", "06/2021/TT-BXD"],
            "ACI 318": ["2019", "2014", "2011"],
        }
        self.deprecated_standards = {
            "TCVN 3994:1985": "Đã hết hiệu lực — Bắt buộc thay thế bằng TCVN 12041:2017 và TCVN 9346:2012",
            "TCVN 3993:1985": "Đã hết hiệu lực — Bắt buộc thay thế bằng TCVN 12041:2017",
            "TCXDVN 194:2006": "Đã hết hiệu lực — Bắt buộc thay thế bằng TCVN 9363:2012",
        }

    def _extract_standards(self, analysis_data):
        """Trích xuất danh sách các tiêu chuẩn đang dùng từ JSON Handoff"""
        used_standards = {}

        def find_citations(obj):
            if isinstance(obj, dict):
                if "Ma_Tieu_Chuan" in obj and "Nam_Ban_Hanh" in obj:
                    code = obj["Ma_Tieu_Chuan"].strip()
                    version = obj["Nam_Ban_Hanh"].strip()
                    if code not in used_standards:
                        used_standards[code] = []
                    used_standards[code].append(version)
                else:
                    for key, val in obj.items():
                        find_citations(val)
            elif isinstance(obj, list):
                for item in obj:
                    find_citations(item)

        find_citations(analysis_data)
        return used_standards

    def check_conflict(self, analysis_data):
        """Phát hiện nếu 1 phân tích dùng 2 version khác nhau của cùng 1 tiêu chuẩn hoặc tiêu chuẩn hết hiệu lực"""
        used_standards = self._extract_standards(analysis_data)
        conflicts = []

        for std_code, versions in used_standards.items():
            unique_versions = list(set(versions))
            if len(unique_versions) > 1:
                conflicts.append({
                    "standard": std_code,
                    "versions": unique_versions,
                    "warning": f"⚠ LỖI XUNG ĐỘT: Đang sử dụng {std_code} với nhiều phiên bản cùng lúc: {unique_versions}"
                })
            for v in unique_versions:
                full_code = f"{std_code}:{v}"
                if full_code in self.deprecated_standards:
                    conflicts.append({
                        "standard": full_code,
                        "versions": [v],
                        "warning": f"⚠ TIÊU CHUẨN HẾT HIỆU LỰC ({full_code}): {self.deprecated_standards[full_code]}"
                    })

        return conflicts
