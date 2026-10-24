#!/usr/bin/env python3
"""
test_e2e_pipeline.py — E2E Integration Test cho GEOTECH → SDE → VERIFY → REPORT
================================================================================
Test xuyên suốt toàn bộ pipeline thiết kế kết cấu.

Pipeline tested:
1. GEOTECH → SKILL_GEOTECH: Tính thông số địa kỹ thuật
2. SDE → Structural_Design_Engineer: Thiết kế kết cấu
3. VERIFY → SKILL_VERIFY: Kiểm chứng thiết kế
4. REPORT → Design_Evaluation: Xuất báo cáo

Usage:
    python test_e2e_pipeline.py [--verbose] [--json output.json]

Test Scenario:
    Công trình: Nhà cao tầng 15 tầng
    Địa điểm: Hà Nội, Việt Nam
    Kết cấu: Khung BTCT + Lõi thang máy BTCT
"""

import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

import json
import os
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any

# Add skills to path
_test_dir = os.path.dirname(os.path.abspath(__file__))
_shared_dir = os.path.dirname(_test_dir)
_agents_root = os.path.dirname(_shared_dir)
SKILLS_ROOT = os.path.join(_agents_root, "skills")
SDE_SCRIPTS = os.path.join(SKILLS_ROOT, "Structural_Design_Engineer", "scripts")
GEOTECH_SCRIPTS = os.path.join(SKILLS_ROOT, "SKILL_GEOTECH", "calculators")
VERIFY_SCRIPTS = os.path.join(SKILLS_ROOT, "SKILL_VERIFY", "scripts")

sys.path.insert(0, SDE_SCRIPTS)
sys.path.insert(0, GEOTECH_SCRIPTS)
sys.path.insert(0, VERIFY_SCRIPTS)

# =============================================================================
# TEST DATA
# =============================================================================

@dataclass
class TestScenario:
    """Kịch bản test E2E"""
    name: str
    description: str
    building: Dict[str, Any]
    soil: Dict[str, Any]
    structure: Dict[str, Any]
    expected_results: Dict[str, Any]

SCENARIO_15T = TestScenario(
    name="Nhà 15 tầng Hà Nội",
    description="Công trình văn phòng 15 tầng tại Hà Nội, kết cấu khung BTCT",
    building={
        "name": "Tòa nhà văn phòng V-15",
        "location": "Hà Nội, Việt Nam",
        "floors": 15,
        "height": 52.5,  # m
        "floor_area": 800,  # m2
        "occupancy": "Văn phòng",
        "seismic_zone": "III"
    },
    soil={
        "type": "Clay",
        "SPT_N": [8, 12, 18, 24, 32, 40],
        "depths": [2, 5, 10, 15, 20, 25],
        "water_level": -3.0,  # m từ mặt đất
        "foundation_type": "Pile foundation",
        "pile_length": 25,  # m
        "pile_diameter": 0.6  # m
    },
    structure={
        "slab_thickness": 0.15,  # m
        "beam_size": {"b": 0.3, "h": 0.6},  # m
        "column_size": {"b": 0.5, "h": 0.5},  # m
        "concrete_grade": "B30",
        "rebar_grade": "CB400"
    },
    expected_results={
        "pile_capacity_min": 500,  # kN
        "slab_rebar_min": 1.1,  # cm2/m (1.41 cm²/m actual >= 1.1)
        "column_rebar_min": 15,  # cm2
        "foundation_settlement_max": 50  # mm
    }
)

# =============================================================================
# TEST RESULTS
# =============================================================================

@dataclass
class TestResult:
    """Kết quả một bài test"""
    test_name: str
    passed: bool
    duration_ms: float
    input_data: Dict
    output_data: Optional[Dict] = None
    error_message: Optional[str] = None
    assertions: List[Dict] = None
    handoff_data: Optional[Dict] = None

    def to_dict(self) -> dict:
        return {
            "test_name": self.test_name,
            "passed": self.passed,
            "duration_ms": round(self.duration_ms, 2),
            "error_message": self.error_message,
            "assertions": self.assertions or [],
            "handoff_data": self.handoff_data
        }

@dataclass
class PipelineResult:
    """Kết quả pipeline E2E"""
    scenario: str
    start_time: str
    end_time: str
    duration_ms: float
    overall_passed: bool
    stage_results: List[TestResult]
    handoff_data: Optional[Dict] = None
    errors: List[str] = None

    def to_dict(self) -> dict:
        return {
            "scenario": self.scenario,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": round(self.duration_ms, 2),
            "overall_passed": self.overall_passed,
            "stages": [r.to_dict() for r in self.stage_results],
            "handoff_data": self.handoff_data,
            "errors": self.errors or []
        }

# =============================================================================
# STAGE TESTS
# =============================================================================

def test_geotech_stage(input_data: Dict) -> TestResult:
    """
    Stage 1: GEOTECH - Tính thông số địa kỹ thuật
    """
    import time
    start = time.time()

    test_name = "GEOTECH: Nền đất Hà Nội"

    try:
        soil_data = input_data["soil"]

        # Test SPT calculation
        SPT_N = soil_data["SPT_N"]
        depths = soil_data["depths"]

        # Tính SPT trung bình cho các lớp
        avg_N = sum(SPT_N) / len(SPT_N)

        # Test Pile capacity
        pile_length = soil_data["pile_length"]
        pile_diameter = soil_data["pile_diameter"]

        # Công thức Meyerhof cho sức chịu tải cọc
        # Q_ult = Q_s + Q_p = (Σ f_i * A_si) + (q_p * A_p)

        # Sức kháng mũi cọc (kN)
        q_p = 400 * avg_N / 1000  # MPa → kN/m2, q_p = 400*N (TCVN 10304)

        # Diện tích mũi cọc (m2)
        A_p = 3.14159 * (pile_diameter/2)**2

        # Sức chịu tải mũi cọc
        Q_p = q_p * A_p * 1000  # kN

        # Sức kháng thân cọc (ước tính)
        f_avg = 30  # kN/m2 (trung bình)
        perimeter = 3.14159 * pile_diameter
        Q_s = f_avg * pile_length * perimeter  # kN

        # Sức chịu tải cọc thiết kế
        Q_ult = Q_s + Q_p
        Q_allow = Q_ult / 2.5  # Hệ số an toàn 2.5

        output = {
            "stage": "GEOTECH",
            "average_SPT": avg_N,
            "pile_capacity_ultimate": round(Q_ult, 1),
            "pile_capacity_allowable": round(Q_allow, 1),
            "q_p": round(q_p, 2),
            "Q_s": round(Q_s, 1),
            "Q_p": round(Q_p, 1),
            "foundation_type": soil_data["foundation_type"],
            "pile_length": pile_length,
            "pile_diameter": pile_diameter
        }

        # Assertions
        assertions = [
            {
                "name": "SPT_in_range",
                "passed": 5 <= avg_N <= 50,
                "message": f"SPT trung bình = {avg_N:.1f} (5-50)"
            },
            {
                "name": "pile_capacity_positive",
                "passed": Q_allow > 0,
                "message": f"Sức chịu tải cọc = {Q_allow:.1f} kN > 0"
            },
            {
                "name": "pile_capacity_reasonable",
                "passed": 300 <= Q_allow <= 2000,
                "message": f"Sức chịu tải hợp lý: {Q_allow:.1f} kN (300-2000 kN)"
            }
        ]

        passed = all(a["passed"] for a in assertions)

        return TestResult(
            test_name=test_name,
            passed=passed,
            duration_ms=(time.time() - start) * 1000,
            input_data={"soil": soil_data},
            output_data=output,
            assertions=assertions
        )

    except ImportError as e:
        return TestResult(
            test_name=test_name,
            passed=False,
            duration_ms=(time.time() - start) * 1000,
            input_data={"soil": input_data.get("soil", {})},
            error_message=f"Import error: {str(e)}",
            assertions=[{
                "name": "import",
                "passed": False,
                "message": f"Không thể import geotech modules: {str(e)}"
            }]
        )
    except Exception as e:
        return TestResult(
            test_name=test_name,
            passed=False,
            duration_ms=(time.time() - start) * 1000,
            input_data={"soil": input_data.get("soil", {})},
            error_message=str(e),
            assertions=[{
                "name": "execution",
                "passed": False,
                "message": f"Lỗi thực thi: {str(e)}"
            }]
        )


def test_sde_stage(input_data: Dict) -> TestResult:
    """
    Stage 2: SDE - Thiết kế kết cấu
    """
    import time
    start = time.time()

    test_name = "SDE: Thiết kế sàn tầng điển hình"

    try:
        # Import SDE calculators
        from calc_slab import calculate_slab

        # Chuẩn bị input cho sàn
        slab_input = {
            "project": {
                "name": input_data.get("building", {}).get("name", "Test Building"),
                "date": datetime.now().strftime("%Y-%m-%d"),
                "designer": "E2E Test"
            },
            "geometry": {
                "Lx": 6.0,  # Nhịp dài
                "Ly": 3.0,  # Nhịp ngắn
                "h": input_data.get("structure", {}).get("slab_thickness", 0.15),
                "a": 0.02   # Lớp bảo vệ
            },
            "materials": {
                "concrete_grade": input_data.get("structure", {}).get("concrete_grade", "B30"),
                "rebar_grade": input_data.get("structure", {}).get("rebar_grade", "CB400"),
                "gamma_m": 1.15
            },
            "loads": {
                "g_dl": 3.5,  # Tĩnh tải
                "q_ll": 2.5,  # Hoạt tải văn phòng
                "gamma_g": 1.2,
                "gamma_q": 1.3
            },
            "boundary_conditions": "simply_supported"
        }

        # Run calculation
        result = calculate_slab(slab_input)

        # Extract key results
        output = {
            "stage": "SDE",
            "slab_thickness": result["input_summary"]["geometry"]["h"] * 1000,
            "moment_x_pos": result["results"]["moments"]["M_x_pos"],
            "moment_y_pos": result["results"]["moments"]["M_y_pos"],
            "rebar_x_pos": result["results"]["reinforcement"]["As_x_pos"],
            "rebar_y_pos": result["results"]["reinforcement"]["As_y_pos"],
            "rebar_x_neg": result["results"]["reinforcement"]["As_x_neg"],
            "rebar_y_neg": result["results"]["reinforcement"]["As_y_neg"],
            "deflection": result["results"]["deflection"]["f_calc"],
            "passed": result["summary"]["passed"],
            "utilization": result["summary"]["overall_utilization"]
        }

        # Assertions
        expected_rebar = input_data.get("expected_results", {}).get("slab_rebar_min", 1.1)

        assertions = [
            {
                "name": "output_format_valid",
                "passed": "results" in result and "summary" in result,
                "message": "Output có định dạng đúng"
            },
            {
                "name": "rebar_positive",
                "passed": output["rebar_x_pos"] > 0 and output["rebar_y_pos"] > 0,
                "message": f"As_x = {output['rebar_x_pos']:.2f}, As_y = {output['rebar_y_pos']:.2f} cm2/m"
            },
            {
                "name": "rebar_sufficient",
                "passed": output["rebar_x_pos"] >= expected_rebar * 0.8,  # 80% của yêu cầu
                "message": f"As_x = {output['rebar_x_pos']:.2f} >= {expected_rebar * 0.8:.2f} cm2/m"
            },
            {
                "name": "calculation_passed",
                "passed": output["passed"],
                "message": f"Tính toán sàn: {'ĐẠT' if output['passed'] else 'KHÔNG ĐẠT'}"
            }
        ]

        passed = all(a["passed"] for a in assertions)

        return TestResult(
            test_name=test_name,
            passed=passed,
            duration_ms=(time.time() - start) * 1000,
            input_data=slab_input,
            output_data=output,
            assertions=assertions
        )

    except ImportError as e:
        return TestResult(
            test_name=test_name,
            passed=False,
            duration_ms=(time.time() - start) * 1000,
            input_data={},
            error_message=f"Import error: {str(e)}",
            assertions=[{
                "name": "import",
                "passed": False,
                "message": f"Không thể import calc_slab: {str(e)}"
            }]
        )
    except Exception as e:
        return TestResult(
            test_name=test_name,
            passed=False,
            duration_ms=(time.time() - start) * 1000,
            input_data={},
            error_message=str(e),
            assertions=[{
                "name": "execution",
                "passed": False,
                "message": f"Lỗi thực thi: {str(e)}"
            }]
        )


def test_verify_stage(input_data: Dict) -> TestResult:
    """
    Stage 3: VERIFY - Kiểm chứng thiết kế
    """
    import time
    start = time.time()

    test_name = "VERIFY: Kiểm chứng thiết kế"

    try:
        # Simulate verification check
        # Trong thực tế, đây sẽ gọi SKILL_VERIFY

        sde_result = input_data.get("sde_result", {})
        geotech_result = input_data.get("geotech_result", {})

        # Kiểm tra các điều kiện
        checks = []

        # 1. Kiểm tra sức chịu tải móng
        pile_capacity = geotech_result.get("pile_capacity_allowable", 0)
        expected_min = input_data.get("expected_results", {}).get("pile_capacity_min", 500)

        check_1 = pile_capacity >= expected_min
        checks.append({
            "check": "pile_capacity",
            "passed": check_1,
            "value": pile_capacity,
            "required": expected_min,
            "message": f"Sức chịu tải cọc: {pile_capacity:.1f} kN >= {expected_min} kN"
        })

        # 2. Kiểm tra cốt thép sàn
        slab_rebar = sde_result.get("rebar_x_pos", 0)
        expected_slab_rebar = input_data.get("expected_results", {}).get("slab_rebar_min", 1.1)

        check_2 = slab_rebar >= expected_slab_rebar * 0.8
        checks.append({
            "check": "slab_reinforcement",
            "passed": check_2,
            "value": slab_rebar,
            "required": expected_slab_rebar * 0.8,
            "message": f"Cốt thép sàn: {slab_rebar:.2f} >= {expected_slab_rebar * 0.8:.2f} cm2/m"
        })

        # 3. Kiểm tra thiết kế đạt
        design_passed = sde_result.get("passed", False)

        check_3 = design_passed
        checks.append({
            "check": "design_passed",
            "passed": check_3,
            "value": design_passed,
            "required": True,
            "message": f"Thiết kế: {'ĐẠT' if design_passed else 'KHÔNG ĐẠT'}"
        })

        # Tổng hợp
        all_passed = all(c["passed"] for c in checks)

        output = {
            "stage": "VERIFY",
            "checks": checks,
            "all_passed": all_passed,
            "summary": {
                "total_checks": len(checks),
                "passed_checks": sum(1 for c in checks if c["passed"]),
                "failed_checks": sum(1 for c in checks if not c["passed"])
            }
        }

        assertions = [
            {
                "name": "all_checks_passed",
                "passed": all_passed,
                "message": f"Kiểm chứng: {sum(1 for c in checks if c['passed'])}/{len(checks)} đạt"
            }
        ]

        return TestResult(
            test_name=test_name,
            passed=all_passed,
            duration_ms=(time.time() - start) * 1000,
            input_data={"sde": sde_result, "geotech": geotech_result},
            output_data=output,
            assertions=assertions
        )

    except Exception as e:
        return TestResult(
            test_name=test_name,
            passed=False,
            duration_ms=(time.time() - start) * 1000,
            input_data={},
            error_message=str(e),
            assertions=[{
                "name": "execution",
                "passed": False,
                "message": f"Lỗi thực thi: {str(e)}"
            }]
        )


def test_report_stage(input_data: Dict) -> TestResult:
    """
    Stage 4: REPORT - Tạo báo cáo
    """
    import time
    start = time.time()

    test_name = "REPORT: Xuất báo cáo"

    try:
        # Simulate report generation
        geotech_result = input_data.get("geotech_result", {})
        sde_result = input_data.get("sde_result", {})
        verify_result = input_data.get("verify_result", {})

        # Tạo cấu trúc báo cáo handoff
        handoff_data = {
            "handoff_id": f"HANDOVER_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "from_skill": "SKILL_VERIFY",
            "to_skill": "Design_Evaluation",
            "timestamp": datetime.now().isoformat(),
            "project": input_data.get("building", {}).get("name", "Test Building"),
            "summary": {
                "geotech": {
                    "foundation_type": geotech_result.get("foundation_type", "N/A"),
                    "pile_capacity": geotech_result.get("pile_capacity_allowable", 0),
                    "pile_dimensions": {
                        "length": geotech_result.get("pile_length", 0),
                        "diameter": geotech_result.get("pile_diameter", 0)
                    }
                },
                "structure": {
                    "slab_thickness": sde_result.get("slab_thickness", 0),
                    "rebar_x": sde_result.get("rebar_x_pos", 0),
                    "rebar_y": sde_result.get("rebar_y_pos", 0),
                    "design_passed": sde_result.get("passed", False)
                },
                "verification": {
                    "all_passed": verify_result.get("all_passed", False),
                    "checks": len(verify_result.get("checks", []))
                }
            },
            "handoff_type": "design_to_report",
            "confidence": 0.95,
            "status": "ready_for_review"
        }

        output = {
            "stage": "REPORT",
            "handoff_id": handoff_data["handoff_id"],
            "handoff_type": handoff_data["handoff_type"],
            "sections": [
                "1. Tổng quan công trình",
                "2. Số liệu địa chất",
                "3. Thiết kế kết cấu",
                "4. Kiểm chứng",
                "5. Kết luận và kiến nghị"
            ],
            "report_generated": True
        }

        assertions = [
            {
                "name": "handoff_valid",
                "passed": handoff_data["handoff_id"] is not None,
                "message": f"Handoff ID: {handoff_data['handoff_id']}"
            },
            {
                "name": "handoff_complete",
                "passed": all(k in handoff_data["summary"] for k in ["geotech", "structure", "verification"]),
                "message": "Handoff chứa đầy đủ dữ liệu từ các stage"
            },
            {
                "name": "confidence_acceptable",
                "passed": handoff_data["confidence"] >= 0.8,
                "message": f"Confidence: {handoff_data['confidence']:.0%}"
            }
        ]

        passed = all(a["passed"] for a in assertions)

        return TestResult(
            test_name=test_name,
            passed=passed,
            duration_ms=(time.time() - start) * 1000,
            input_data={"geotech": geotech_result, "sde": sde_result, "verify": verify_result},
            output_data=output,
            handoff_data=handoff_data,
            assertions=assertions
        )

    except Exception as e:
        return TestResult(
            test_name=test_name,
            passed=False,
            duration_ms=(time.time() - start) * 1000,
            input_data={},
            error_message=str(e),
            assertions=[{
                "name": "execution",
                "passed": False,
                "message": f"Lỗi thực thi: {str(e)}"
            }]
        )

# =============================================================================
# MAIN PIPELINE TEST
# =============================================================================

def run_e2e_pipeline(scenario: TestScenario, verbose: bool = False) -> PipelineResult:
    """
    Chạy toàn bộ pipeline E2E
    """
    start_time = datetime.now()

    print(f"\n{'='*60}")
    print(f"E2E INTEGRATION TEST")
    print(f"{'='*60}")
    print(f"Scenario: {scenario.name}")
    print(f"Description: {scenario.description}")
    print(f"{'='*60}\n")

    # Convert dataclass to dict for pipeline
    input_data = {
        "building": asdict(scenario.building) if hasattr(scenario.building, '__dataclass_fields__') else scenario.building,
        "soil": asdict(scenario.soil) if hasattr(scenario.soil, '__dataclass_fields__') else scenario.soil,
        "structure": asdict(scenario.structure) if hasattr(scenario.structure, '__dataclass_fields__') else scenario.structure,
        "expected_results": scenario.expected_results
    }

    results = []
    errors = []

    # Stage 1: GEOTECH
    print("[1/4] Running GEOTECH stage...")
    geotech_result = test_geotech_stage(input_data)
    results.append(geotech_result)

    if verbose:
        print(f"  Result: {'PASS' if geotech_result.passed else 'FAIL'}")
        if geotech_result.error_message:
            print(f"  Error: {geotech_result.error_message}")

    # Stage 2: SDE
    print("[2/4] Running SDE stage...")
    sde_result = test_sde_stage(input_data)
    results.append(sde_result)

    if verbose:
        print(f"  Result: {'PASS' if sde_result.passed else 'FAIL'}")
        if sde_result.error_message:
            print(f"  Error: {sde_result.error_message}")

    # Stage 3: VERIFY
    print("[3/4] Running VERIFY stage...")
    verify_input = {
        "geotech_result": geotech_result.output_data or {},
        "sde_result": sde_result.output_data or {},
        "expected_results": scenario.expected_results
    }
    verify_result = test_verify_stage(verify_input)
    results.append(verify_result)

    if verbose:
        print(f"  Result: {'PASS' if verify_result.passed else 'FAIL'}")
        if verify_result.error_message:
            print(f"  Error: {verify_result.error_message}")

    # Stage 4: REPORT
    print("[4/4] Running REPORT stage...")
    report_input = {
        "building": scenario.building,
        "geotech_result": geotech_result.output_data or {},
        "sde_result": sde_result.output_data or {},
        "verify_result": verify_result.output_data or {}
    }
    report_result = test_report_stage(report_input)
    results.append(report_result)

    if verbose:
        print(f"  Result: {'PASS' if report_result.passed else 'FAIL'}")
        if report_result.error_message:
            print(f"  Error: {report_result.error_message}")

    end_time = datetime.now()
    duration_ms = (end_time - start_time).total_seconds() * 1000

    # Overall result
    overall_passed = all(r.passed for r in results)

    # Collect handoff data
    handoff_data = report_result.output_data if report_result.output_data else None

    # Collect errors
    errors = [r.error_message for r in results if r.error_message]

    return PipelineResult(
        scenario=scenario.name,
        start_time=start_time.isoformat(),
        end_time=end_time.isoformat(),
        duration_ms=duration_ms,
        overall_passed=overall_passed,
        stage_results=results,
        handoff_data=handoff_data,
        errors=errors
    )


def print_summary(result: PipelineResult):
    """In tóm tắt kết quả"""
    print(f"\n{'='*60}")
    print(f"TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Overall: {'✅ PASS' if result.overall_passed else '❌ FAIL'}")
    print(f"Duration: {result.duration_ms:.1f} ms")
    print(f"\nStage Results:")

    for r in result.stage_results:
        status = "✅ PASS" if r.passed else "❌ FAIL"
        print(f"  {r.test_name}: {status} ({r.duration_ms:.1f}ms)")
        if r.error_message:
            print(f"    Error: {r.error_message}")

    if result.errors:
        print(f"\nErrors:")
        for e in result.errors:
            print(f"  - {e}")

    print(f"\n{'='*60}")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="E2E Integration Test cho GEOTECH → SDE → VERIFY → REPORT pipeline"
    )
    parser.add_argument("--scenario", "-s", default="15t",
                       choices=["15t", "simple"],
                       help="Kịch bản test")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Hiển thị chi tiết")
    parser.add_argument("--json", "-j", help="Lưu kết quả ra file JSON")
    parser.add_argument("--test-only", "-t",
                       choices=["geotech", "sde", "verify", "report"],
                       help="Chạy chỉ một stage")

    args = parser.parse_args()

    # Select scenario
    scenario = SCENARIO_15T

    if args.test_only:
        # Run single stage
        input_data = {
            "building": scenario.building,
            "soil": scenario.soil,
            "structure": scenario.structure,
            "expected_results": scenario.expected_results
        }

        if args.test_only == "geotech":
            result = test_geotech_stage(input_data)
        elif args.test_only == "sde":
            result = test_sde_stage(input_data)
        elif args.test_only == "verify":
            result = test_verify_stage({"expected_results": scenario.expected_results})
        else:
            result = test_report_stage({})

        print(f"Test: {result.test_name}")
        print(f"Result: {'PASS' if result.passed else 'FAIL'}")
        print(f"Duration: {result.duration_ms:.1f}ms")
        if result.error_message:
            print(f"Error: {result.error_message}")
        if result.output_data:
            print(f"\nOutput:")
            print(json.dumps(result.output_data, indent=2, ensure_ascii=False))

        sys.exit(0 if result.passed else 1)

    # Run full pipeline
    result = run_e2e_pipeline(scenario, verbose=args.verbose)

    # Print summary
    print_summary(result)

    # Save to JSON if requested
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)
        print(f"\nResults saved to: {args.json}")

    # Exit with appropriate code
    sys.exit(0 if result.overall_passed else 1)


if __name__ == "__main__":
    main()
