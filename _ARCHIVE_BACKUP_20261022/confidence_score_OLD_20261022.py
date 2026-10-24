"""
Confidence Score Calculator - Tính điểm tin cậy cho kết quả tính toán

Mục đích:
- Đánh giá độ tin cậy của output từ các skill
- Xác định xem cần SKILL_VERIFY hay không
- Block export nếu confidence < 0.60

5 Factors với trọng số:
- data_completeness: 25%
- input_quality: 20%
- standard_compliance: 20%
- calculation_consistency: 20%
- source_reliability: 15%

Cơ chế Veto Multiplier (v2.0):
- Nếu standard_compliance (standards) == 0.0 (không cite tiêu chuẩn) → return 0.0
- Nếu calculation_consistency (consistency) < 0.5 (logs không nhất quán) → return 0.0
- Lý do: Không có tiêu chuẩn hoặc log không nhất quán thì output KHÔNG ĐÁNG TIN,
  bất kể các factor khác có cao.

Tolerance Matrix (SKILL_VERIFY, Rule 2) — tham chiếu khi cross-check:
- Nội lực (M, V, N):        5%
- Utilization ratio η:       3%
- Diện tích cốt thép As:     12%

Usage:
    python confidence_score.py --input calculation_output.json --verbose
"""

import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

# Ensure UTF-8 output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# ============================================================================
# CONFIGURATION
# ============================================================================

CONFIDENCE_CONFIG = {
    "factors": {
        "data_completeness": {
            "weight": 0.25,
            "description": "Required fields present"
        },
        "input_quality": {
            "weight": 0.20,
            "description": "Values in valid ranges"
        },
        "standard_compliance": {
            "weight": 0.20,
            "description": "Standards properly cited"
        },
        "calculation_consistency": {
            "weight": 0.20,
            "description": "Internal log consistency"
        },
        "source_reliability": {
            "weight": 0.15,
            "description": "Data source reliability"
        }
    },
    "thresholds": {
        "HIGH": 0.85,
        "MEDIUM": 0.60,
        "LOW": 0.00
    },
    "required_fields": [
        "geometry",
        "materials",
        "forces",
        "results",
        "calculation_logs"
    ],
    # =========================================================================
    # VETO MULTIPLIER (v2.0) — Tieu chi chan (veto) confidence score
    # =========================================================================
    # Neu bat ky dieu kien veto nao TRUE -> confidence = 0.0
    # Muc dich: Output KHONG co tieu chuan hoac log khong nhat quan
    #            thi KHONG THE chap nhan, bat ke cac factor khac co cao.
    #
    # Hai loai rule:
    # - "factor_score"   : kiem tra gia tri score cua factor (vd: standard_compliance == 0)
    # - "data_field"     : kiem tra su hien cua mot field trong data
    #                      (vd: data.standard_method phai ton tai va khac rong)
    "veto": {
        "enabled": True,
        "rules": [
            {
                "name": "no_standards_cited",
                "description": "Khong co tieu chuan (standard_method rong hoac khong ton tai)",
                "rule_type": "data_field",
                "field": "standard_method",
                "check": "missing_or_empty",
                "action": "VETO_RETURN_ZERO"
            },
            {
                "name": "standard_score_zero",
                "description": "standard_compliance score == 0 (sau khi tinh)",
                "rule_type": "factor_score",
                "factor": "standard_compliance",
                "operator": "eq",
                "threshold": 0.0,
                "action": "VETO_RETURN_ZERO"
            },
            {
                "name": "low_log_consistency",
                "description": "Log khong nhat quan (calculation_consistency < 0.5)",
                "rule_type": "factor_score",
                "factor": "calculation_consistency",
                "operator": "lt",
                "threshold": 0.5,
                "action": "VETO_RETURN_ZERO"
            }
        ]
    },
    # =========================================================================
    # TOLERANCE MATRIX (tham chieu SKILL_VERIFY Rule 2)
    # =========================================================================
    # Dung cho SKILL_VERIFY de quyet dinh PASS/FAIL khi cross-check 2 calculators
    "tolerance_matrix": {
        "internal_force": {
            "label": "Noi luc (M, V, N)",
            "tolerance_percent": 5,
            "description": "Lam tron, tong hop tai khac nhau"
        },
        "utilization_ratio": {
            "label": "Utilization ratio (eta)",
            "tolerance_percent": 3,
            "description": "Quan trong hon, yeu cau chinh xac cao"
        },
        "reinforcement_area": {
            "label": "Dien tich cot thep (As)",
            "tolerance_percent": 12,
            "description": "Do chon thanh thuc te, vong tron"
        }
    }
}

# ============================================================================
# CONFIDENCE CALCULATORS
# ============================================================================

class ConfidenceCalculator:
    """Calculator cho từng factor"""

    def __init__(self):
        self.factors = {}

    @staticmethod
    def _get_ci_field(dict_obj, *keys, default=None):
        """Lấy giá trị từ dict_obj theo danh sách keys không phân biệt hoa thường."""
        if not isinstance(dict_obj, dict):
            return default
        for k in keys:
            if k in dict_obj and dict_obj[k] is not None:
                return dict_obj[k]
        for k in keys:
            k_lower = k.lower()
            for dk, dv in dict_obj.items():
                if dk.lower() == k_lower and dv is not None:
                    return dv
        return default

    def calculate_data_completeness(self, data):
        """
        Tính điểm data_completeness (25%)
        Điểm cao nhất khi tất cả required fields present (không phân biệt hoa/thường)
        """
        required = CONFIDENCE_CONFIG["required_fields"]
        present = []
        missing = []
        for f in required:
            val = self._get_ci_field(data, f)
            if val is not None and val != "" and val != [] and val != {}:
                present.append(f)
            else:
                missing.append(f)

        score = len(present) / len(required) if required else 1.0

        self.factors["data_completeness"] = {
            "score": score,
            "present": present,
            "missing": missing,
            "weight": 0.25
        }

        return score

    def calculate_input_quality(self, data):
        """
        Tính điểm input_quality (20%)
        Kiểm tra giá trị có trong range hợp lệ
        """
        score = 1.0
        issues = []

        # Check geometry
        geometry = self._get_ci_field(data, "geometry", default={})
        if geometry:
            # Positive dimensions
            for key in ["b", "h", "L", "a"]:
                val = self._get_ci_field(geometry, key)
                if val is not None and val <= 0:
                    score -= 0.1
                    issues.append(f"{key} must be positive")

        # Check forces
        forces = self._get_ci_field(data, "forces", default={})
        if forces and isinstance(forces, dict):
            # Check for reasonable values
            for key, value in forces.items():
                if isinstance(value, (int, float)) and abs(value) > 1e6:  # kN - reasonable upper bound
                    score -= 0.1
                    issues.append(f"{key} value seems unreasonably large")

        # Check materials
        materials = self._get_ci_field(data, "materials", default={})
        if materials and isinstance(materials, dict):
            # Check concrete grade
            concrete = self._get_ci_field(materials, "concrete", "concrete_grade", default="")
            if concrete and not self._is_valid_concrete_grade(str(concrete)):
                score -= 0.1
                issues.append("Unknown concrete grade")

        score = max(0.0, min(1.0, score))  # Clamp 0-1

        self.factors["input_quality"] = {
            "score": score,
            "issues": issues,
            "weight": 0.20
        }

        return score

    def calculate_standard_compliance(self, data):
        """
        Tính điểm standard_compliance (20%)
        Kiểm tra tiêu chuẩn được cite đầy đủ (không phân biệt hoa/thường)
        """
        score = 1.0
        issues = []

        # Check standard_method
        standard = self._get_ci_field(data, "standard_method", "Standard_Method", "standard", "Standard", "Tieu_Chuan", default="")
        if not standard:
            score -= 0.15
            issues.append("Missing standard_method")
        elif not self._is_valid_standard(str(standard)):
            score -= 0.1
            issues.append(f"Standard '{standard}' may not be recognized")

        # Check citations in logs
        logs = self._get_ci_field(data, "calculation_logs", "Calculation_Logs", default=[]) or []
        logs_with_citation = 0
        total_logs = len(logs) if isinstance(logs, list) else 0

        if total_logs > 0:
            for log in logs:
                if isinstance(log, dict) and self._get_ci_field(log, "citation", "Citation"):
                    logs_with_citation += 1
            citation_ratio = logs_with_citation / total_logs
            if citation_ratio < 1.0:
                score -= (1.0 - citation_ratio) * 0.1
                issues.append(f"Only {logs_with_citation}/{total_logs} steps have citations")

        score = max(0.0, min(1.0, score))

        self.factors["standard_compliance"] = {
            "score": score,
            "citation_ratio": logs_with_citation / total_logs if total_logs > 0 else 1.0,
            "issues": issues,
            "weight": 0.20
        }

        return score

    def calculate_calculation_consistency(self, data):
        """
        Tính điểm calculation_consistency (20%)
        Kiểm tra calculation_logs nhất quán (không phân biệt hoa/thường)
        """
        score = 1.0
        issues = []
        logs = self._get_ci_field(data, "calculation_logs", "Calculation_Logs", default=[]) or []

        if not logs:
            score = 0.0  # Penalty for no logs: 0.0 per audit fix
            issues.append("No calculation logs present")
            self.factors["calculation_consistency"] = {
                "score": score,
                "consistency_issues": issues,
                "weight": 0.20
            }
            return score

        # Check each step has required fields (formula, substitution, result)
        valid_steps = 0
        for i, log in enumerate(logs):
            if not isinstance(log, dict):
                continue
            has_formula = bool(self._get_ci_field(log, "formula", "Formula"))
            has_sub = bool(self._get_ci_field(log, "substitution", "Substitution", "values", "Values"))
            has_res = self._get_ci_field(log, "result", "Result") is not None
            if has_formula and has_sub and has_res:
                valid_steps += 1

        step_ratio = valid_steps / len(logs) if logs else 0
        score = step_ratio

        if step_ratio < 1.0:
            issues.append(f"Only {valid_steps}/{len(logs)} steps complete")

        # Check step sequence consistency
        for i in range(1, len(logs)):
            prev_result = self._get_ci_field(logs[i-1], "result", "Result")
            current_substitution = str(self._get_ci_field(logs[i], "substitution", "Substitution", "values", "Values", default="") or "")

            if prev_result and str(prev_result) not in current_substitution:
                # May be legitimate if using different notation
                pass

        score = max(0.0, min(1.0, score))

        self.factors["calculation_consistency"] = {
            "score": score,
            "valid_steps": valid_steps,
            "total_steps": len(logs),
            "consistency_issues": issues,
            "weight": 0.20
        }

        return score

    def calculate_source_reliability(self, data):
        """
        Tính điểm source_reliability (15%)
        Đánh giá nguồn dữ liệu
        """
        score = 1.0
        source = data.get("source", "unknown")
        issues = []

        source_scores = {
            "measured": 1.0,      # Từ khảo sát thực tế
            "calculated": 0.85,   # Từ tính toán kỹ thuật
            "estimated": 0.6,     # Ước tính
            "assumed": 0.4,       # Giả định
            "unknown": 0.3        # Không rõ nguồn
        }

        score = source_scores.get(source.lower(), 0.3)

        if source.lower() == "unknown":
            issues.append("Source not specified - assuming lowest reliability")

        # Check if has additional metadata
        if "metadata" in data:
            if data["metadata"].get("verified"):
                score = min(1.0, score + 0.1)

        self.factors["source_reliability"] = {
            "score": score,
            "source": source,
            "issues": issues,
            "weight": 0.15
        }

        return score

    def calculate_overall(self, data):
        """Tính overall confidence score"""

        scores = {
            "data_completeness": self.calculate_data_completeness(data),
            "input_quality": self.calculate_input_quality(data),
            "standard_compliance": self.calculate_standard_compliance(data),
            "calculation_consistency": self.calculate_calculation_consistency(data),
            "source_reliability": self.calculate_source_reliability(data)
        }

        # Weighted sum
        overall = sum(
            scores[key] * CONFIDENCE_CONFIG["factors"][key]["weight"]
            for key in scores
        )

        # =====================================================================
        # VETO MULTIPLIER (v2.0)
        # =====================================================================
        # Neu bat ky rule veto nao kich hoat -> return 0.0
        # Muc dich: Output khong co tieu chuan HOAC log khong nhat quan
        #            thi khong the chap nhan, bat ke cac factor khac.
        #
        # Ho tro 2 loai rule:
        #   1. rule_type="factor_score": kiem tra scores[factor] theo operator
        #   2. rule_type="data_field":   kiem tra field trong data (missing/empty)
        veto_config = CONFIDENCE_CONFIG.get("veto", {})
        if veto_config.get("enabled", False):
            for rule in veto_config.get("rules", []):
                action = rule.get("action")
                rule_type = rule.get("rule_type", "factor_score")
                triggered = False
                evidence = {}

                if rule_type == "factor_score":
                    factor_name = rule.get("factor")
                    operator = rule.get("operator")
                    threshold = rule.get("threshold")
                    if factor_name not in scores:
                        continue
                    score_value = scores[factor_name]
                    if operator == "eq" and score_value == threshold:
                        triggered = True
                    elif operator == "lt" and score_value < threshold:
                        triggered = True
                    elif operator == "lte" and score_value <= threshold:
                        triggered = True
                    elif operator == "gt" and score_value > threshold:
                        triggered = True
                    elif operator == "gte" and score_value >= threshold:
                        triggered = True
                    evidence = {
                        "factor": factor_name,
                        "factor_score": round(score_value, 4),
                        "operator": operator,
                        "threshold": threshold
                    }
                elif rule_type == "data_field":
                    field = rule.get("field")
                    check = rule.get("check", "missing_or_empty")
                    value = self._get_ci_field(data, field)
                    if check == "missing_or_empty":
                        if not value:  # None, "", [], {}
                            triggered = True
                    elif check == "missing":
                        if value is None:
                            triggered = True
                    evidence = {
                        "field": field,
                        "check": check,
                        "field_value": str(value)[:80]
                    }

                if triggered and action == "VETO_RETURN_ZERO":
                    # Ghi nhan ly do veto
                    if "veto_results" not in self.factors:
                        self.factors["veto_results"] = {
                            "triggered": True,
                            "vetoed_rules": [],
                            "weight": 0.0
                        }
                    self.factors["veto_results"]["vetoed_rules"].append({
                        "rule_name": rule.get("name"),
                        "description": rule.get("description"),
                        "rule_type": rule_type,
                        **evidence
                    })
                    return 0.0

        return overall

    def get_veto_details(self):
        """Lay chi tiet ve cac veto da kich hoat (neu co)"""
        return self.factors.get("veto_results", {
            "triggered": False,
            "vetoed_rules": [],
            "weight": 0.0
        })

    def get_level(self, score):
        """Xác định level từ score"""
        if score >= CONFIDENCE_CONFIG["thresholds"]["HIGH"]:
            return "HIGH"
        elif score >= CONFIDENCE_CONFIG["thresholds"]["MEDIUM"]:
            return "MEDIUM"
        else:
            return "LOW"

    def _is_valid_concrete_grade(self, grade):
        """Kiểm tra concrete grade hợp lệ"""
        valid_grades = [
            "B12.5", "B15", "B20", "B22.5", "B25", "B30", "B35", "B40", "B45", "B50", "B55", "B60"
        ]
        return str(grade).upper() in [g.upper() for g in valid_grades]

    def _is_valid_standard(self, standard):
        """Kiểm tra standard được công nhận (mở rộng đầy đủ tiêu chuẩn TCVN/quốc tế)"""
        valid_standards = [
            "TCVN 5574:2018", "TCVN 5574", "TCVN 5575:2024", "TCVN 5575",
            "TCVN 2737:2023", "TCVN 2737", "TCVN 9386:2025", "TCVN 9386-1:2025",
            "TCVN 9386", "TCVN 10304:2025", "TCVN 10304", "TCVN 9362:2012",
            "TCVN 9362", "TCVN 9351:2012", "TCVN 9351",
            "QCVN 03:2022/BXD", "QCVN 03:2022", "QCVN 03", "QCVN 02:2022/BXD",
            "QCVN 06:2022/BXD", "AASHTO", "ACI", "EC", "EUROCODE",
            "EN 1992", "EN 1993", "EN 1997", "EN 1998", "JIS", "ASTM", "BS"
        ]
        for vs in valid_standards:
            if vs.lower() in standard.lower():
                return True
        return False


# ============================================================================
# CONFIDENCE SCORE REPORTER
# ============================================================================

class ConfidenceReporter:
    """Tạo báo cáo confidence score"""

    def __init__(self, calculator, score):
        self.calculator = calculator
        self.score = score
        self.level = calculator.get_level(score)

    def generate_report(self, verbose=False):
        """Tạo báo cáo text"""
        lines = []

        # Header
        lines.append("\n" + "=" * 60)
        lines.append("📊 CONFIDENCE SCORE REPORT")
        lines.append("=" * 60)

        # Veto Multiplier information (Hien thi TRUOC khi overall score)
        veto_details = self.calculator.get_veto_details()
        if veto_details.get("triggered", False):
            lines.append(f"\n{COLORS['RED']}🚫 VETO MULTIPLIER KÍCH HOẠT (v2.0){COLORS['RESET']}")
            lines.append(f"   Confidence score bị ép về 0.0 do:")
            for rule in veto_details.get("vetoed_rules", []):
                rule_type = rule.get("rule_type", "factor_score")
                if rule_type == "data_field":
                    lines.append(
                        f"   - {rule.get('description', '?')}\n"
                        f"     field = {rule.get('field', '?')}, "
                        f"check = {rule.get('check', '?')}, "
                        f"value = {rule.get('field_value', '?')!r}"
                    )
                else:
                    lines.append(
                        f"   - {rule.get('description', '?')}\n"
                        f"     factor = {rule.get('factor', '?')}, "
                        f"score = {rule.get('factor_score', '?')}, "
                        f"operator = {rule.get('operator', '?')}{rule.get('threshold', '')}"
                    )
            lines.append("")

        # Overall score
        color = self._get_color(self.level)
        lines.append(f"\n🎯 Overall Score: {color}{self.score:.3f}{COLORS['RESET']} ({self.level})")

        # Level description
        level_descriptions = {
            "HIGH": "✅ Đầy đủ data, validated - Tiếp tục bình thường",
            "MEDIUM": "⚠️ Thiếu một số data - Nên gửi SKILL_VERIFY",
            "LOW": "🔴 Thiếu critical data - BLOCK export, notify User"
        }
        lines.append(f"   {level_descriptions[self.level]}")

        # Factor breakdown
        lines.append("\n" + "-" * 60)
        lines.append("FACTOR BREAKDOWN:")
        lines.append("-" * 60)

        for factor_name, factor_data in self.calculator.factors.items():
            if factor_name == "veto_results":
                continue  # bo qua trong breakdown (da hien thi o phan Veto)
            score = factor_data["score"]
            weight = factor_data["weight"]
            contrib = score * weight

            color = self._get_score_color(score)
            lines.append(f"\n📌 {factor_name.upper().replace('_', ' ')}")
            lines.append(f"   Score: {color}{score:.3f}{COLORS['RESET']} "
                        f"(Weight: {weight:.0%}, Contribution: {contrib:.3f})")

            if verbose:
                if "issues" in factor_data and factor_data["issues"]:
                    lines.append("   Issues:")
                    for issue in factor_data["issues"]:
                        lines.append(f"     - {issue}")

                if "missing" in factor_data and factor_data["missing"]:
                    lines.append(f"   Missing: {', '.join(factor_data['missing'])}")

                if "present" in factor_data:
                    lines.append(f"   Present: {', '.join(factor_data['present'])}")

        # Recommendations
        lines.append("\n" + "-" * 60)
        lines.append("RECOMMENDATIONS:")
        lines.append("-" * 60)

        if veto_details.get("triggered", False):
            lines.append(f"{COLORS['RED']}🚫 VETO ĐÃ KÍCH HOẠT — BLOCK EXPORT{COLORS['RESET']}")
            lines.append("   1. KHÔNG xuất báo cáo / KHÔNG tích hợp output này")
            lines.append("   2. Fix các yếu tố bị veto (cite tiêu chuẩn / làm rõ logs)")
            lines.append("   3. Re-run sau khi fix")
        elif self.level == "HIGH":
            lines.append("✅ Confidence cao - Không cần kiểm tra thêm")
        elif self.level == "MEDIUM":
            lines.append("⚠️ Confidence trung bình - Khuyến nghị:")
            lines.append("   1. Gửi SKILL_VERIFY để cross-check")
            lines.append("   2. Kiểm tra các missing fields")
            lines.append("   3. Có thể tiếp tục nhưng cần review kỹ")
        else:
            lines.append("🔴 Confidence thấp - BẮT BUỘC:")
            lines.append("   1. BLOCK export file")
            lines.append("   2. Thông báo User về data thiếu")
            lines.append("   3. Yêu cầu bổ sung thông tin trước khi tiếp tục")

        lines.append("\n" + "=" * 60)

        return "\n".join(lines)

    def _get_color(self, level):
        colors = {
            "HIGH": COLORS["GREEN"],
            "MEDIUM": COLORS["YELLOW"],
            "LOW": COLORS["RED"]
        }
        return colors.get(level, COLORS["RESET"])

    def _get_score_color(self, score):
        if score >= 0.85:
            return COLORS["GREEN"]
        elif score >= 0.60:
            return COLORS["YELLOW"]
        else:
            return COLORS["RED"]

    def to_dict(self):
        """Export ra dict"""
        veto_details = self.calculator.get_veto_details()
        return {
            "confidence_score": round(self.score, 3),
            "level": self.level,
            "factors": {
                name: {
                    "score": round(data["score"], 3),
                    "weight": data["weight"],
                    "contribution": round(data["score"] * data["weight"], 3)
                }
                for name, data in self.calculator.factors.items()
                if name != "veto_results"
            },
            "veto": {
                "enabled": True,
                "triggered": veto_details.get("triggered", False),
                "vetoed_rules": veto_details.get("vetoed_rules", [])
            },
            "tolerance_matrix": CONFIDENCE_CONFIG.get("tolerance_matrix", {}),
            "recommendation": self._get_recommendation()
        }

    def _get_recommendation(self):
        if self.level == "HIGH":
            return "Proceed normally"
        elif self.level == "MEDIUM":
            return "Trigger SKILL_VERIFY"
        else:
            return "BLOCK and notify User"


# Colors for console output
COLORS = {
    "GREEN": "\033[92m",
    "YELLOW": "\033[93m",
    "RED": "\033[91m",
    "ORANGE": "\033[38;5;214m",
    "RESET": "\033[0m",
    "BOLD": "\033[1m"
}


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Confidence Score Calculator")
    parser.add_argument("--input", "-i", required=True, help="Input JSON file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--json", "-j", action="store_true", help="Output JSON only")
    parser.add_argument("--output", "-o", help="Output JSON file")

    args = parser.parse_args()

    # Load input
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"{COLORS['RED']}Error: File not found: {args.input}{COLORS['RESET']}")
        sys.exit(1)

    with open(input_path, "r", encoding="utf-8") as f:
        input_data = json.load(f)

    # Calculate confidence
    calculator = ConfidenceCalculator()
    score = calculator.calculate_overall(input_data)
    reporter = ConfidenceReporter(calculator, score)

    # Output
    if args.json:
        result = reporter.to_dict()
        print(json.dumps(result, indent=2, ensure_ascii=False))

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
    else:
        print(reporter.generate_report(verbose=args.verbose))

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(reporter.to_dict(), f, indent=2, ensure_ascii=False)

    # Exit code based on level
    if reporter.level == "LOW":
        sys.exit(2)  # Block
    elif reporter.level == "MEDIUM":
        sys.exit(1)  # Warning
    else:
        sys.exit(0)  # OK


if __name__ == "__main__":
    main()
