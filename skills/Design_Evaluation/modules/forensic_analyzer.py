import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
from difflib import SequenceMatcher

class ForensicAnalyzer:
    def generate_comparison_table(self, design, actual, standard):
        """Tạo bảng so sánh 3 cột (Thiết kế - Thực tế - Tiêu chuẩn) với diff highlighting"""

        def similarity_score(a, b):
            # So sánh độ tương đồng chuỗi
            return SequenceMatcher(None, str(a), str(b)).ratio()

        comparison = []
        # Gom tất cả các key (parameter) từ 3 nguồn
        all_keys = set(design.keys()) | set(actual.keys()) | set(standard.keys())
        
        for key in all_keys:
            design_val = design.get(key, "N/A")
            actual_val = actual.get(key, "N/A")
            standard_val = standard.get(key, "N/A")

            # Tính điểm tương đồng giữa Thiết kế và Thực tế
            sim_design_actual = similarity_score(design_val, actual_val) if design_val != "N/A" and actual_val != "N/A" else 0.0
            
            # Đánh giá xem có Compliant (đạt chuẩn) không (Actual vs Standard)
            compliant = False
            if actual_val != "N/A" and standard_val != "N/A":
                try:
                    # Nếu là số, check xem actual có <= standard không (giả định standard là limit)
                    # Note: tùy theo parameter mà logic có thể là >= hoặc <=. Mặc định ở đây lấy <= làm chuẩn.
                    if float(actual_val) <= float(standard_val):
                        compliant = True
                except ValueError:
                    # Nếu là string, check giống hệt nhau
                    if str(actual_val).lower() == str(standard_val).lower():
                        compliant = True
            
            # Severity: Nếu sai khác lớn giữa thiết kế và thực tế, HOẶC không đạt chuẩn -> HIGH
            severity = "LOW"
            if not compliant:
                severity = "HIGH (NON-COMPLIANT)"
            elif sim_design_actual < 0.9:
                severity = "MEDIUM (DIFF_FOUND)"

            comparison.append({
                "parameter": key,
                "design": design_val,
                "actual": actual_val,
                "standard": standard_val,
                "similarity": f"{sim_design_actual:.1%}",
                "compliant": "✅ Đạt" if compliant else "❌ Không đạt",
                "severity": severity
            })

        # Sắp xếp theo severity: HIGH -> MEDIUM -> LOW
        def get_severity_score(item):
            if "HIGH" in item["severity"]: return 0
            if "MEDIUM" in item["severity"]: return 1
            return 2
            
        comparison.sort(key=get_severity_score)
        return comparison
