# -*- coding: utf-8 -*-
"""Kiểm thử Unit Tests cho deflection_check.py (TCVN 2737:2023 Điều 11 & Bảng G.1 + Legacy Comparison)."""
import json
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure") and sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

_CALC_DIR = Path(__file__).resolve().parent.parent
if str(_CALC_DIR) not in sys.path:
    sys.path.insert(0, str(_CALC_DIR))

from deflection_check import (  # noqa: E402
    calculate_deflection,
    get_tcvn_2737_2023_table_g1_limit_ratio,
)


def test_table_g1_breakpoints_and_interpolation_h_le_6m():
    """Kiểm tra các mốc Bảng G.1 (chiều cao phòng <= 6 m) và nội suy tuyến tính."""
    assert get_tcvn_2737_2023_table_g1_limit_ratio(0.5) == 120.0
    assert get_tcvn_2737_2023_table_g1_limit_ratio(1.0) == 120.0
    assert get_tcvn_2737_2023_table_g1_limit_ratio(3.0) == 150.0
    assert get_tcvn_2737_2023_table_g1_limit_ratio(4.5) == 175.0
    assert get_tcvn_2737_2023_table_g1_limit_ratio(6.0) == 200.0
    assert get_tcvn_2737_2023_table_g1_limit_ratio(9.0) == 225.0
    assert get_tcvn_2737_2023_table_g1_limit_ratio(12.0) == 250.0
    assert get_tcvn_2737_2023_table_g1_limit_ratio(18.0) == 275.0
    assert get_tcvn_2737_2023_table_g1_limit_ratio(24.0) == 300.0
    assert get_tcvn_2737_2023_table_g1_limit_ratio(30.0) == 300.0


def test_table_g1_room_height_gt_6m_and_cantilever():
    """Kiểm tra nhánh h > 6 m (Chú thích 3) và cấu kiện công xôn (Chú thích 1: L_eff = 2L)."""
    assert get_tcvn_2737_2023_table_g1_limit_ratio(6.0, room_height_le_6m=False) == 200.0
    assert get_tcvn_2737_2023_table_g1_limit_ratio(12.0, room_height_le_6m=False) == 216.67
    assert get_tcvn_2737_2023_table_g1_limit_ratio(24.0, room_height_le_6m=False) == 250.0
    assert get_tcvn_2737_2023_table_g1_limit_ratio(36.0, room_height_le_6m=False) == 300.0
    assert get_tcvn_2737_2023_table_g1_limit_ratio(40.0, room_height_le_6m=False) == 300.0

    # Công xôn L = 3 m -> L_eff = 6 m -> L/200; L = 6 m -> L_eff = 12 m -> L/250
    assert get_tcvn_2737_2023_table_g1_limit_ratio(3.0, cantilever=True) == 200.0
    assert get_tcvn_2737_2023_table_g1_limit_ratio(6.0, cantilever=True) == 250.0

    raised = False
    try:
        get_tcvn_2737_2023_table_g1_limit_ratio(0.0)
    except ValueError:
        raised = True
    assert raised, "L_m <= 0 phải ném ValueError"


def test_calculate_deflection_default_tcvn_2737_2023():
    """Mặc định dùng TCVN 2737:2023 Bảng G.1 với L=6m -> limit_ratio=200 (Allowable=30mm)."""
    res = calculate_deflection(L=6.0, M=80.0, E=30e6, I_eff=5.4e-3)
    assert res["Standard"] == "TCVN 2737:2023"
    assert res["Standard_Mode"] == "TCVN_2737_2023"
    assert "Bảng G.1" in res["Standard_Method"]
    assert res["limit_ratio"] == 200.0
    assert res["Allowable_mm"] == 30.0
    assert res["Status"] == "PASS"
    assert "Legacy_Warning" not in res
    assert len(res["Calculation_Logs"]) >= 3
    cit = res["Calculation_Logs"][-1]["Citation"]
    assert cit["Ma_TC"] == "TCVN 2737:2023"
    assert "Bảng G.1" in cit["Bang_Hinh"]


def test_calculate_deflection_legacy_comparison_mode():
    """Chế độ đối chiếu TCVN_5574_2018_LEGACY giữ L/250 và bắt buộc kèm Legacy_Warning."""
    res = calculate_deflection(
        L=6.0, M=80.0, E=30e6, I_eff=5.4e-3,
        standard_mode="TCVN_5574_2018_LEGACY",
    )
    assert res["Standard"] == "TCVN 5574:2018"
    assert res["Standard_Mode"] == "TCVN_5574_2018_LEGACY"
    assert res["limit_ratio"] == 250.0
    assert res["Allowable_mm"] == 24.0
    assert "Legacy_Warning" in res and "TCVN 2737:2023" in res["Legacy_Warning"]
    assert len(res["Calculation_Logs"]) >= 3


def test_calculate_deflection_override_and_fail_status():
    """Ghi đè limit_ratio=400 (dầm đỡ tường kính dễ vỡ) và kiểm tra trạng thái FAIL."""
    res = calculate_deflection(L=6.0, M=80.0, E=30e6, I_eff=5.4e-3, limit_ratio=400.0)
    assert res["limit_ratio"] == 400.0
    assert res["Allowable_mm"] == 15.0
    assert res["Limit_Source"] == "user_override"
    # Với L=6, M=80, E=30e6, I=5.4e-3, coeff=2: delta_e=1.85mm -> delta_lt=3.70mm -> PASS
    assert res["Status"] == "PASS"

    fail_res = calculate_deflection(L=6.0, M=400.0, E=30e6, I_eff=5.4e-3, limit_ratio=400.0)
    assert fail_res["Status"] == "FAIL"
    assert fail_res["Rating"] == "RED"
    assert fail_res["utilization_ratio"] > 1.0


def test_deflection_cli_modes():
    """Kiểm tra chạy CLI JSON với cả cờ TCVN 2737:2023 mở rộng và Legacy."""
    script = str(_CALC_DIR / "deflection_check.py")
    cp1 = subprocess.run(
        [sys.executable, script, "--L", "12", "--M", "150", "--E", "30e6", "--I_eff", "0.02", "--room-height-gt-6m"],
        capture_output=True, text=True, encoding="utf-8", check=True,
    )
    data1 = json.loads(cp1.stdout)
    assert data1["limit_ratio"] == 216.67
    assert data1["Standard"] == "TCVN 2737:2023"

    cp2 = subprocess.run(
        [sys.executable, script, "--L", "6", "--M", "80", "--E", "30e6", "--I_eff", "5.4e-3",
         "--standard-mode", "TCVN_5574_2018_LEGACY"],
        capture_output=True, text=True, encoding="utf-8", check=True,
    )
    data2 = json.loads(cp2.stdout)
    assert data2["limit_ratio"] == 250.0
    assert "Legacy_Warning" in data2


if __name__ == "__main__":
    test_table_g1_breakpoints_and_interpolation_h_le_6m()
    test_table_g1_room_height_gt_6m_and_cantilever()
    test_calculate_deflection_default_tcvn_2737_2023()
    test_calculate_deflection_legacy_comparison_mode()
    test_calculate_deflection_override_and_fail_status()
    test_deflection_cli_modes()
    print("[OK] test_deflection_check.py: 6/6 tests passed.")
