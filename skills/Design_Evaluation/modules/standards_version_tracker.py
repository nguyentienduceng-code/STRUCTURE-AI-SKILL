import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
import json

class StandardsVersionTracker:
    def __init__(self):
        self.standards_db = {
            "TCVN 2737": ["2023", "2020", "1995"],
            "TCVN 5574": ["2018", "2012"],
            "TCVN 5575": ["2012", "2024"],
            "ACI 318": ["2019", "2014", "2011"],
            "TCVN 10304": ["2014", "2025"]
        }

    def _extract_standards(self, analysis_data):
        """Trích xuất danh sách các tiêu chuẩn đang dùng từ JSON Handoff"""
        # Giả định JSON Handoff có format chứa trường 'Citations' hoặc tương tự
        used_standards = {}
        
        # Đệ quy tìm các Citation Objects
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
        """Phát hiện nếu 1 phân tích dùng 2 version khác nhau của cùng 1 tiêu chuẩn"""
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

        return conflicts
