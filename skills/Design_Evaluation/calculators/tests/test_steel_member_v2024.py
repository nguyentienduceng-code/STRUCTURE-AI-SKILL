# -*- coding: utf-8 -*-
"""
Unit Tests cho steel_member_check_v2024.py

Chạy: pytest test_steel_member_v2024.py -v
"""

import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
import sys
import os

# Thêm parent directory vào path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import json
from steel_member_check_v2024 import check_steel_member_v2024


def test_basic_calculation():
    """Test cơ bản: dầm H400x200x8x13"""
    result = check_steel_member_v2024(
        M=250, N=0, V=80,
        Area=84.8, Wx=1310, Iy=562,
        tf=13, tw=8, h=400, b=200,
        L_beam=6000, fy=345,
        lateral_support=True,
        check_ltb=True,
        check_shear=True
    )

    # Kiểm tra output structure
    assert "Results" in result
    assert "Standard_Method" in result
    assert result["Standard_Method"] == "TCVN 5575:2024"

    # Kiểm tra Calculation_Logs
    assert "Calculation_Logs" in result
    assert len(result["Calculation_Logs"]) >= 2  # 2 steps minimum (flexure + summary)

    # Kiểm tra results có đủ fields
    assert "M_c_Rd" in result["Results"]
    assert "eta_M" in result["Results"]
    assert "eta_V" in result["Results"]

    # In ra để verify
    print(f"\n✅ Test passed: η_M = {result['Results']['eta_M']}")
    print(f"   M_c_Rd = {result['Results']['M_c_Rd']} kN.m")


def test_ltb_check():
    """Test LTB: dầm không giằng ngang"""
    result = check_steel_member_v2024(
        M=250, N=0, V=80,
        Area=84.8, Wx=1310, Iy=562,
        tf=13, tw=8, h=400, b=200,
        L_beam=6000, fy=345,
        lateral_support=False,  # Không giằng → kiểm tra LTB
        check_ltb=True,
        check_shear=True
    )

    assert "eta_LTB" in result["Results"]
    assert result["Results"]["eta_LTB"] > 0  # LTB phải được tính

    print(f"\n✅ LTB test: η_LTB = {result['Results']['eta_LTB']}")


def test_overstrength_section():
    """Test tiết diện mạnh: η ~ 0.6-0.7"""
    result = check_steel_member_v2024(
        M=150, N=0, V=50,
        Area=84.8, Wx=1310, Iy=562,
        tf=13, tw=8, h=400, b=200,
        L_beam=6000, fy=345,
        lateral_support=True,
        check_ltb=False,
        check_shear=True
    )

    # η phải < 1.0 (đạt)
    assert result["Results"]["eta_max"] <= 1.0
    assert result["Results"]["Status"] in ["PASS", "FAIL"]

    print(f"\n✅ Overstrength test: η_max = {result['Results']['eta_max']}")


def test_failure_section():
    """Test tiết diện yếu: η > 1.0"""
    result = check_steel_member_v2024(
        M=500, N=0, V=200,
        Area=84.8, Wx=1310, Iy=562,
        tf=13, tw=8, h=400, b=200,
        L_beam=6000, fy=345,
        lateral_support=True,
        check_ltb=True,
        check_shear=True
    )

    # Phải FAIL hoặc η > 1.0
    assert result["Results"]["eta_max"] > 1.0 or result["Results"]["Status"] == "FAIL"

    print(f"\n✅ Failure test: Status = {result['Results']['Status']}, η = {result['Results']['eta_max']}")


def test_gamma_m1_correct():
    """Verify GAMMA_M1 = 1.10 được sử dụng đúng"""
    import steel_member_check_v2024 as sm
    assert sm.GAMMA_M1 == 1.10, "GAMMA_M1 phải = 1.10 theo TCVN 5575:2024"
    print("\n✅ GAMMA_M1 = 1.10 (đúng)")


if __name__ == "__main__":
    print("=" * 60)
    print("  UNIT TESTS: steel_member_check_v2024.py")
    print("=" * 60)

    test_basic_calculation()
    test_ltb_check()
    test_overstrength_section()
    test_failure_section()
    test_gamma_m1_correct()

    print("\n" + "=" * 60)
    print("  ✅ ALL TESTS PASSED")
    print("=" * 60)
