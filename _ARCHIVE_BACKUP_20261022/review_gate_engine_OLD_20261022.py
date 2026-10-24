"""
Review Gate Engine - Cổng Kiểm duyệt Bắt buộc trước khi xuất file

Mục đích:
- Chạy pre-flight checks trước khi export
- Hiển thị tóm tắt cho User
- Yêu cầu xác nhận trước khi ghi file

Usage:
    python review_gate_engine.py --input calculation_output.json --verbose
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

REVIEW_GATE_CONFIG = {
    "min_eta_pass": 1.0,
    "max_eta_warning": 0.90,
    "min_confidence_high": 0.85,
    "min_confidence_medium": 0.60,
    "max_variance_pct": 5.0,
    "min_narrative_words": 800,
    "required_sections": [
        "calculation_logs",
        "results",
        "materials",
        "geometry"
    ]
}

COLORS = {
    "GREEN": "\033[92m",
    "YELLOW": "\033[93m",
    "RED": "\033[91m",
    "ORANGE": "\033[38;5;214m",
    "BLUE": "\033[94m",
    "BOLD": "\033[1m",
    "RESET": "\033[0m"
}

# ============================================================================
# PRE-FLIGHT CHECKS
# ============================================================================

class PreflightCheck:
    """Base class for pre-flight checks"""

    def __init__(self, name, description):
        self.name = name
        self.description = description
        self.passed = False
        self.warnings = []
        self.errors = []
        self.details = {}

    def run(self, data):
        raise NotImplementedError

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "passed": self.passed,
            "warnings": self.warnings,
            "errors": self.errors,
            "details": self.details
        }


class CalculationLogsCheck(PreflightCheck):
    """Kiểm tra Calculation_Logs presence và quality"""

    def __init__(self):
        super().__init__(
            "CALCULATION_LOGS",
            "Kiểm tra Calculation_Logs có đầy đủ và hợp lệ"
        )

    def run(self, data):
        logs = data.get("calculation_logs", [])

        if not logs:
            self.errors.append("Không tìm thấy Calculation_Logs")
            self.passed = False
            return

        # Check each log entry
        valid_entries = 0
        for i, log in enumerate(logs):
            entry_valid = True

            # Required fields
            for field in ["formula", "substitution", "result"]:
                if field not in log:
                    self.warnings.append(f"Bước {i+1}: Thiếu trường '{field}'")
                    entry_valid = False

            if entry_valid:
                valid_entries += 1

        self.details = {
            "total_logs": len(logs),
            "valid_entries": valid_entries,
            "completion_rate": valid_entries / len(logs) * 100 if logs else 0
        }

        if valid_entries == len(logs):
            self.passed = True
        elif valid_entries > 0:
            self.warnings.append(f"Chỉ {valid_entries}/{len(logs)} entries hợp lệ")
            self.passed = True  # Warning only
        else:
            self.passed = False


class UtilizationRatioCheck(PreflightCheck):
    """Kiểm tra Utilization Ratio (η)"""

    def __init__(self):
        super().__init__(
            "UTILIZATION_RATIO",
            "Kiểm tra Utilization Ratio (η)"
        )

    def run(self, data):
        results = data.get("results", {})

        eta_checks = []
        for key, value in results.items():
            if "eta" in key.lower() or key in ["eta_M", "eta_V", "eta_N"]:
                status = "PASS"
                color = COLORS["GREEN"]

                if value > REVIEW_GATE_CONFIG["min_eta_pass"]:
                    status = "FAIL"
                    color = COLORS["RED"]
                elif value > REVIEW_GATE_CONFIG["max_eta_warning"]:
                    status = "WARNING"
                    color = COLORS["ORANGE"]
                elif value <= 0.70:
                    status = "OPTIMAL"
                    color = COLORS["GREEN"]

                eta_checks.append({
                    "key": key,
                    "value": value,
                    "status": status,
                    "color": color
                })

        self.details = {"checks": eta_checks}

        # Check if any FAIL
        fail_count = sum(1 for c in eta_checks if c["status"] == "FAIL")
        if fail_count > 0:
            self.passed = False
            self.errors.append(f"{fail_count} phần tử vượt khả năng chịu lực (η > 1.0)")
        else:
            self.passed = True


class StandardCitationCheck(PreflightCheck):
    """Kiểm tra Standard citation đầy đủ"""

    def __init__(self):
        super().__init__(
            "STANDARD_CITATION",
            "Kiểm tra trích dẫn tiêu chuẩn"
        )

    def run(self, data):
        standard_method = data.get("standard_method", "")
        citations = data.get("citations", [])
        logs = data.get("calculation_logs", [])

        issues = []

        # Check standard_method
        if not standard_method:
            issues.append("Thiếu Standard_Method")

        # Check citations in logs
        logs_without_citation = 0
        for log in logs:
            if "citation" not in log or not log["citation"]:
                logs_without_citation += 1

        if logs_without_citation > 0:
            issues.append(f"{logs_without_citation}/{len(logs)} bước không có citation")

        self.details = {
            "standard_method": standard_method,
            "citation_count": len(citations),
            "logs_without_citation": logs_without_citation
        }

        if issues:
            self.warnings.extend(issues)
            self.passed = True  # Warning, not blocking
        else:
            self.passed = True


class ConfidenceScoreCheck(PreflightCheck):
    """Kiểm tra Confidence Score"""

    def __init__(self):
        super().__init__(
            "CONFIDENCE_SCORE",
            "Kiểm tra Confidence Score"
        )

    def run(self, data):
        confidence = data.get("confidence_score", 1.0)

        if confidence >= REVIEW_GATE_CONFIG["min_confidence_high"]:
            self.passed = True
            self.details = {"level": "HIGH", "score": confidence}
        elif confidence >= REVIEW_GATE_CONFIG["min_confidence_medium"]:
            self.passed = True
            self.warnings.append(f"Confidence score ở mức MEDIUM ({confidence:.2f})")
            self.details = {"level": "MEDIUM", "score": confidence}
        else:
            self.passed = False
            self.errors.append(f"Confidence score thấp ({confidence:.2f}) - Cần kiểm tra lại")
            self.details = {"level": "LOW", "score": confidence}


class RequiredFieldsCheck(PreflightCheck):
    """Kiểm tra Required fields presence"""

    def __init__(self):
        super().__init__(
            "REQUIRED_FIELDS",
            "Kiểm tra các trường bắt buộc"
        )

    def run(self, data):
        missing = []

        for field in REVIEW_GATE_CONFIG["required_sections"]:
            if field not in data:
                missing.append(field)

        self.details = {
            "required": REVIEW_GATE_CONFIG["required_sections"],
            "present": [f for f in REVIEW_GATE_CONFIG["required_sections"] if f in data],
            "missing": missing
        }

        if missing:
            self.errors.append(f"Thiếu trường bắt buộc: {', '.join(missing)}")
            self.passed = False
        else:
            self.passed = True


class NarrativeDepthCheck(PreflightCheck):
    """Kiểm tra độ sâu narrative (cho báo cáo)"""

    def __init__(self):
        super().__init__(
            "NARRATIVE_DEPTH",
            "Kiểm tra độ sâu diễn giải"
        )

    def run(self, data):
        narrative = data.get("narrative", "")
        word_count = len(narrative.split()) if narrative else 0

        min_words = REVIEW_GATE_CONFIG["min_narrative_words"]

        self.details = {
            "word_count": word_count,
            "minimum_required": min_words
        }

        if word_count < min_words:
            self.warnings.append(
                f"Narrative chỉ có {word_count} từ (tối thiểu: {min_words})"
            )
            self.passed = True  # Warning only
        else:
            self.passed = True


# ============================================================================
# REVIEW GATE ENGINE
# ============================================================================

class ReviewGate:
    """Review Gate - Cổng kiểm duyệt chính"""

    def __init__(self, input_data, verbose=False):
        self.input_data = input_data
        self.verbose = verbose
        self.checks = []
        self.overall_passed = False
        self.approval_status = "PENDING"
        self.timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S+07:00")

        # Initialize checks
        self.checks = [
            CalculationLogsCheck(),
            RequiredFieldsCheck(),
            UtilizationRatioCheck(),
            StandardCitationCheck(),
            ConfidenceScoreCheck(),
            NarrativeDepthCheck()
        ]

    def run_all_checks(self):
        """Chạy tất cả pre-flight checks"""
        for check in self.checks:
            check.run(self.input_data)

        # Overall result
        critical_failures = [c for c in self.checks if c.errors and not c.passed]

        if critical_failures:
            self.overall_passed = False
            self.approval_status = "BLOCKED"
        else:
            self.overall_passed = True
            self.approval_status = "READY"

        return self.overall_passed

    def generate_summary(self):
        """Tạo tóm tắt cho User"""
        output = []
        output.append("\n" + "=" * 70)
        output.append(f"{COLORS['BOLD']}📋 REVIEW GATE SUMMARY{COLORS['RESET']}")
        output.append("=" * 70)

        # Timestamp
        output.append(f"\n⏰ Thời điểm: {self.timestamp}")

        # Overall status
        if self.approval_status == "BLOCKED":
            status_color = COLORS["RED"]
            status_text = "🔴 BLOCKED - Không thể xuất file"
        else:
            status_color = COLORS["GREEN"]
            status_text = "🟢 READY - Có thể xuất file"

        output.append(f"\n📊 Trạng thái tổng: {status_color}{status_text}{COLORS['RESET']}")

        # Check results
        output.append("\n" + "-" * 70)
        output.append("KẾT QUẢ KIỂM TRA:")
        output.append("-" * 70)

        for check in self.checks:
            if check.passed:
                icon = f"{COLORS['GREEN']}✅{COLORS['RESET']}"
            else:
                icon = f"{COLORS['RED']}❌{COLORS['RESET']}"

            output.append(f"\n{icon} {COLORS['BOLD']}{check.name}{COLORS['RESET']}")
            output.append(f"   {check.description}")

            if self.verbose:
                # Details
                for key, value in check.details.items():
                    output.append(f"   - {key}: {value}")

            # Warnings
            for warning in check.warnings:
                output.append(f"   {COLORS['ORANGE']}⚠️ {warning}{COLORS['RESET']}")

            # Errors
            for error in check.errors:
                output.append(f"   {COLORS['RED']}✖️ {error}{COLORS['RESET']}")

        # η Summary table
        eta_check = next((c for c in self.checks if c.name == "UTILIZATION_RATIO"), None)
        if eta_check and eta_check.details.get("checks"):
            output.append("\n" + "-" * 70)
            output.append("BẢNG CHỈ SỐ SỬ DỤNG (η):")
            output.append("-" * 70)

            for eta in eta_check.details["checks"]:
                output.append(
                    f"   {eta['color']}{eta['key']:10} = {eta['value']:6.3f} "
                    f"[{eta['status']}]{COLORS['RESET']}"
                )

        # Final message
        output.append("\n" + "=" * 70)
        if self.approval_status == "BLOCKED":
            output.append(f"{COLORS['RED']}⛔ KHÔNG THỂ XUẤT FILE{COLORS['RESET']}")
            output.append("Vui lòng khắc phục các lỗi trên trước khi tiếp tục.")
        else:
            output.append(f"{COLORS['GREEN']}✅ SẴN SÀNG XUẤT FILE{COLORS['RESET']}")
            output.append("\n📝 XÁC NHẬN XUẤT FILE:")
            output.append("   Gõ 'Đồng ý', 'OK', 'Xuất file', 'Approved' để tiếp tục.")
            output.append("   Hoặc yêu cầu điều chỉnh nếu cần.")
        output.append("=" * 70)

        return "\n".join(output)

    def to_json(self):
        """Export kết quả ra JSON"""
        return {
            "review_gate": {
                "timestamp": self.timestamp,
                "status": self.approval_status,
                "overall_passed": self.overall_passed,
                "checks": [c.to_dict() for c in self.checks]
            },
            "input_summary": {
                "element_id": self.input_data.get("element_id", "N/A"),
                "standard_method": self.input_data.get("standard_method", "N/A"),
                "confidence_score": self.input_data.get("confidence_score", 1.0)
            }
        }

    def approve(self):
        """Mark as approved"""
        self.approval_status = "APPROVED"
        return self.approval_status

    def reject(self, reason=""):
        """Mark as rejected"""
        self.approval_status = "REJECTED"
        self.rejection_reason = reason
        return self.approval_status


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Review Gate Engine")
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

    # Run review gate
    gate = ReviewGate(input_data, verbose=args.verbose)
    gate.run_all_checks()

    # Output
    if args.json:
        result = gate.to_json()
        print(json.dumps(result, indent=2, ensure_ascii=False))

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
    else:
        print(gate.generate_summary())

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(gate.to_json(), f, indent=2, ensure_ascii=False)

    # Exit code
    sys.exit(0 if gate.overall_passed else 1)


if __name__ == "__main__":
    main()
