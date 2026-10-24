# -*- coding: utf-8 -*-
"""
Unit Tests cho rc_flexure_design.py

Chạy: pytest test_rc_flexure.py -v
"""

import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
import sys
import os

# Thêm parent directory vào path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from rc_flexure_design import design_rc_flexure


def test_basic_design():
    """Test thiết kế cơ bản: dầm 300x650, M=180 kN.m"""
    result = design_rc_flexure(
        M=180,  # kN.m
        b=0.3,  # m
        h0=0.65,  # m (chiều cao làm việc)
        Rb=14.5,  # MPa (B22.5)
        Rs=365    # MPa (CB400-V)
    )

    # Kiểm tra output
    assert "Standard" in result
    assert result["Standard"] == "TCVN 5574:2018"
    assert "alpha_m" in result
    assert "As_chon_mm2" in result

    # alpha_m phải <= alpha_R (0.39)
    assert result["alpha_m"] <= 0.39, f"alpha_m = {result['alpha_m']} > 0.39"

    # Status phải PASS
    assert "PASS" in result["Status"]

    print(f"\n✅ Test passed: As_chon = {result['As_chon_mm2']} mm²")
    print(f"   η = {result['utilization_ratio']}")


def test_overreinforced_section():
    """Test tiết diện quá cốt: alpha_m > alpha_R"""
    result = design_rc_flexure(
        M=500,  # kN.m (lớn)
        b=0.3,
        h0=0.5,  # nhỏ
        Rb=14.5,
        Rs=365
    )

    # Phải FAIL
    assert "FAIL" in result["Status"]
    assert result["As_chon_mm2"] == 0

    print(f"\n✅ Over-reinforced test: Status = {result['Status']}")


def test_min_reinforcement():
    """Test cốt thép tối thiểu"""
    result = design_rc_flexure(
        M=50,  # kN.m (nhỏ)
        b=0.3,
        h0=0.6,
        Rb=14.5,
        Rs=365
    )

    # As_chon phải >= As_min
    assert result["As_chon_mm2"] >= result["As_min_mm2"]

    print(f"\n✅ Min reinforcement test: As_min = {result['As_min_mm2']} mm²")


def test_alpha_r_values():
    """Test các giá trị alpha_R"""
    # CB400-V: alpha_R = 0.39
    result_400 = design_rc_flexure(
        M=180, b=0.3, h0=0.65, Rb=14.5, Rs=365, alpha_R=0.39
    )

    # CB300-V: alpha_R = 0.44
    result_300 = design_rc_flexure(
        M=180, b=0.3, h0=0.65, Rb=14.5, Rs=365, alpha_R=0.44
    )

    # alpha_R cao hơn → cho phép As thấp hơn
    assert result_400["As_chon_mm2"] >= result_300["As_chon_mm2"]

    print(f"\n✅ Alpha_R test: CB400-V As = {result_400['As_chon_mm2']} mm²")
    print(f"   CB300-V As = {result_300['As_chon_mm2']} mm²")


def test_calculation_logs():
    """Test Calculation_Logs có đủ thông tin"""
    result = design_rc_flexure(
        M=180, b=0.3, h0=0.65, Rb=14.5, Rs=365
    )

    assert "Calculation_Logs" in result
    assert len(result["Calculation_Logs"]) >= 3

    # Kiểm tra step 1 có Citation
    step1 = result["Calculation_Logs"][0]
    assert "Citation" in step1
    assert step1["Citation"]["Ma_TC"] == "TCVN 5574:2018"

    print(f"\n✅ Calculation_Logs test: {len(result['Calculation_Logs'])} steps")


if __name__ == "__main__":
    print("=" * 60)
    print("  UNIT TESTS: rc_flexure_design.py")
    print("=" * 60)

    test_basic_design()
    test_overreinforced_section()
    test_min_reinforcement()
    test_alpha_r_values()
    test_calculation_logs()

    print("\n" + "=" * 60)
    print("  ✅ ALL TESTS PASSED")
    print("=" * 60)
