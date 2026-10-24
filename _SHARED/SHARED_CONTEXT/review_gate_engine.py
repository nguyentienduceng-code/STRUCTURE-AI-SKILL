"""
Review Gate Engine v2.0 - Cổng Kiểm duyệt Bắt buộc trước khi xuất file
"""
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

REVIEW_GATE_CONFIG = {
    "min_eta_pass": 1.0,
    "max_eta_warning": 0.90,
    "min_confidence_high": 0.85,
    "min_confidence_medium": 0.60,
    "max_variance_pct": 5.0,
    "min_narrative_words": 800,
    "required_sections": ["calculation_logs", "results", "materials", "geometry"]
}

COLORS = {
    "GREEN": "\033[92m", "YELLOW": "\033[93m", "RED": "\033[91m",
    "ORANGE": "\033[38;5;214m", "BLUE": "\033[94m", "BOLD": "\033[1m", "RESET": "\033[0m"
}

def _get_ci(data: dict, *keys, default=None):
    if not isinstance(data, dict):
        return default
    for k in keys:
        if k in data and data[k] is not None:
            return data[k]
    for k in keys:
        kl = k.lower()
        for dk, dv in data.items():
            if dk.lower() == kl and dv is not None:
                return dv
    return default

class PreflightCheck:
    def __init__(self, name, description):
        self.name = name
        self.description = description
        self.passed = False
        self.warnings = []
        self.errors = []
        self.details = {}
    def to_dict(self):
        return {"name": self.name, "description": self.description, "passed": self.passed, "warnings": self.warnings, "errors": self.errors, "details": self.details}

class CalculationLogsCheck(PreflightCheck):
    def __init__(self):
        super().__init__("CALCULATION_LOGS", "Kiểm tra Calculation_Logs có đầy đủ và hợp lệ")
    def run(self, data):
        logs = _get_ci(data, "Calculation_Logs", "calculation_logs", default=[])
        if not logs:
            self.errors.append("Không tìm thấy Calculation_Logs")
            self.passed = False
            return
        valid_entries = 0
        for i, log in enumerate(logs):
            entry_valid = True
            for field in ["formula", "substitution", "result"]:
                if _get_ci(log, field) is None:
                    self.warnings.append(f"Bước {i+1}: Thiếu trường '{field}'")
                    entry_valid = False
            if entry_valid:
                valid_entries += 1
        self.details = {"total_logs": len(logs), "valid_entries": valid_entries, "completion_rate": valid_entries / len(logs) * 100 if logs else 0}
        self.passed = valid_entries > 0

class UtilizationRatioCheck(PreflightCheck):
    def __init__(self):
        super().__init__("UTILIZATION_RATIO", "Kiểm tra Utilization Ratio (η)")
    def run(self, data):
        results = _get_ci(data, "results", "Results", default={}) or data
        eta_checks = []
        if isinstance(results, dict):
            for key, value in results.items():
                if isinstance(value, (int, float)) and ("eta" in key.lower() or key in ["eta_M", "eta_V", "eta_N"]):
                    status = "FAIL" if value > 1.0 else ("WARNING" if value > 0.90 else ("OPTIMAL" if value <= 0.70 else "PASS"))
                    eta_checks.append({"key": key, "value": value, "status": status, "color": ""})
        self.details = {"checks": eta_checks}
        fail_count = sum(1 for c in eta_checks if c["status"] == "FAIL")
        self.passed = (fail_count == 0)
        if not self.passed:
            self.errors.append(f"{fail_count} phần tử vượt khả năng chịu lực (η > 1.0)")

class StandardCitationCheck(PreflightCheck):
    def __init__(self):
        super().__init__("STANDARD_CITATION", "Kiểm tra trích dẫn tiêu chuẩn")
    def run(self, data):
        standard_method = _get_ci(data, "Standard_Method", "standard_method", "Standard", default="")
        citations = _get_ci(data, "Citations", "citations", default=[])
        logs = _get_ci(data, "Calculation_Logs", "calculation_logs", default=[])
        if not standard_method:
            self.warnings.append("Thiếu Standard_Method")
        logs_without_citation = sum(1 for log in logs if not _get_ci(log, "citation", "Citation"))
        if logs_without_citation > 0:
            self.warnings.append(f"{logs_without_citation}/{len(logs)} bước không có citation")
        self.details = {"standard_method": standard_method, "citation_count": len(citations), "logs_without_citation": logs_without_citation}
        self.passed = True

class ConfidenceScoreCheck(PreflightCheck):
    def __init__(self):
        super().__init__("CONFIDENCE_SCORE", "Kiểm tra Confidence Score")
    def run(self, data):
        confidence = _get_ci(data, "confidence_score", "Confidence_Score", default=1.0)
        if confidence >= 0.85:
            self.passed = True
            self.details = {"level": "HIGH", "score": confidence}
        elif confidence >= 0.60:
            self.passed = True
            self.warnings.append(f"Confidence score ở mức MEDIUM ({confidence:.2f})")
            self.details = {"level": "MEDIUM", "score": confidence}
        else:
            self.passed = False
            self.errors.append(f"Confidence score thấp ({confidence:.2f}) - Cần kiểm tra lại")
            self.details = {"level": "LOW", "score": confidence}

class RequiredFieldsCheck(PreflightCheck):
    def __init__(self):
        super().__init__("REQUIRED_FIELDS", "Kiểm tra các trường bắt buộc")
    def run(self, data):
        missing = []
        aliases = {
            "calculation_logs": ("Calculation_Logs", "calculation_logs"),
            "results": ("results", "Results", "summary", "Summary", "status", "Status"),
            "materials": ("materials", "Materials", "inputs", "input_summary"),
            "geometry": ("geometry", "Geometry", "inputs", "input_summary"),
        }
        present = []
        for field in REVIEW_GATE_CONFIG["required_sections"]:
            if _get_ci(data, *aliases.get(field, (field,))) is not None:
                present.append(field)
            else:
                missing.append(field)
        self.details = {"required": REVIEW_GATE_CONFIG["required_sections"], "present": present, "missing": missing}
        if missing:
            self.errors.append(f"Thiếu trường bắt buộc: {', '.join(missing)}")
            self.passed = False
        else:
            self.passed = True

class NarrativeDepthCheck(PreflightCheck):
    def __init__(self):
        super().__init__("NARRATIVE_DEPTH", "Kiểm tra độ sâu diễn giải")
    def run(self, data):
        narrative = _get_ci(data, "narrative", "Narrative", default="")
        word_count = len(narrative.split()) if narrative else 0
        self.details = {"word_count": word_count, "minimum_required": 800}
        if word_count < 800:
            self.warnings.append(f"Narrative chỉ có {word_count} từ (tối thiểu: 800)")
        self.passed = True

class ReviewGate:
    def __init__(self, input_data, verbose=False):
        self.input_data = input_data
        self.verbose = verbose
        self.overall_passed = False
        self.approval_status = "PENDING"
        self.timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S+07:00")
        self.checks = [
            CalculationLogsCheck(), RequiredFieldsCheck(), UtilizationRatioCheck(),
            StandardCitationCheck(), ConfidenceScoreCheck(), NarrativeDepthCheck()
        ]
    def run_all_checks(self):
        for check in self.checks:
            check.run(self.input_data)
        critical_failures = [c for c in self.checks if c.errors and not c.passed]
        self.overall_passed = not bool(critical_failures)
        self.approval_status = "BLOCKED" if critical_failures else "READY"
        return self.overall_passed
    def generate_summary(self):
        return f"ReviewGate Status: {self.approval_status} (Passed={self.overall_passed})"
    def to_json(self):
        return {
            "review_gate": {"timestamp": self.timestamp, "status": self.approval_status, "overall_passed": self.overall_passed, "checks": [c.to_dict() for c in self.checks]},
            "input_summary": {"element_id": _get_ci(self.input_data, "element_id", default="N/A"), "standard_method": _get_ci(self.input_data, "Standard_Method", "standard_method", default="N/A"), "confidence_score": _get_ci(self.input_data, "confidence_score", default=1.0)}
        }
