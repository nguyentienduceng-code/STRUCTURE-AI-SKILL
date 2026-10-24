#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bộ kiểm thử tự động (Automated Verification & Regression Test Suite)
Kiểm chứng toàn bộ 16 tệp đã vá (R&D + Cơ học Kết cấu TCVN) của hệ thống .agents.
"""
import sys
import json
import math
import subprocess
from pathlib import Path

PATCH_DIR = Path("/working_dir/c_7dad3a9fa9593898/artifacts/file_generation/ttl=63d/intermediate/patches")
DOWNLOAD_DIR = Path("/working_dir/c_7dad3a9fa9593898/downloads")
sys.path.insert(0, str(PATCH_DIR))

passed = 0
failed = 0

def assert_test(name: str, condition: bool, detail: str = ""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  [PASS] {name}" + (f" — {detail}" if detail else ""))
    else:
        failed += 1
        print(f"  [FAIL] {name}" + (f" — {detail}" if detail else ""))

print("=" * 80)
print("1. KIỂM ĐỊNH NHÓM LỖI R&D & KIẾN TRÚC PIPELINE (BUG-RD-01 -> BUG-RD-05)")
print("=" * 80)

# Test 1: project_grading.py (BUG-RD-01)
import project_grading
res_grade = project_grading.determine_grade(
    building_type="civil", height=85.0, stories=25, gfa=35000.0,
    underground_depth=7.5, underground_stories=2
)
assert_test(
    "BUG-RD-01a: project_grading.py thực thi không lỗi SyntaxError",
    res_grade["Project_Grade"] == "Cấp I" and "C3" in res_grade["Consequence_Class_QCVN03"],
    f"Project_Grade={res_grade['Project_Grade']}, Consequence={res_grade['Consequence_Class_QCVN03']}"
)
assert_test(
    "BUG-RD-01b: project_grading.py tuân thủ Glass-Box (Standard_Method & Calculation_Logs)",
    "Standard_Method" in res_grade and len(res_grade.get("Calculation_Logs", [])) >= 2,
    f"Logs={len(res_grade.get('Calculation_Logs', []))} steps"
)

# Test 2: _collect_standards.py (BUG-RD-02)
import _collect_standards
stds_data = _collect_standards.collect_standards_summary(DOWNLOAD_DIR / "STANDARDS_LOCK.md")
codes_found = stds_data["current_codes"]
assert_test(
    "BUG-RD-02: _collect_standards.py nhận diện đầy đủ 21 dòng trong STANDARDS_LOCK.md v3.1.0 (gồm Thông tư 34/2026/TT-BXD)",
    stds_data["total"] == 21 and any("34/2026/TT-BXD" in c for c in codes_found),
    f"Collected {stds_data['total']} rows ({stds_data['distinct_current']} distinct codes), includes TT 34/2026/TT-BXD"
)

# Test 3: _collect_calculators.py (BUG-RD-04)
import _collect_calculators
assert_test(
    "BUG-RD-04: _collect_calculators.py loại trừ hậu tố _old, _bak, _pre_fix",
    _collect_calculators._is_excluded(Path("project_grading_OLD_20261021.py")) and
    _collect_calculators._is_excluded(Path("dce_excel_bus_v1.0_bak.py")) and
    not _collect_calculators._is_excluded(Path("project_grading.py")),
    "Excluded _OLD_20261021.py & _bak.py"
)

# Test 4: standard_conflict_checker.py (BUG-RD-03)
import standard_conflict_checker
lock_dict = standard_conflict_checker.load_standards_lock(DOWNLOAD_DIR / "STANDARDS_LOCK.md")
assert_test(
    "BUG-RD-03: standard_conflict_checker.py đọc đúng bảng Markdown STANDARDS_LOCK.md",
    len(lock_dict) >= 16 and lock_dict.get("TCVN 5574") == "TCVN 5574:2018" and lock_dict.get("TCVN 5575") == "TCVN 5575:2024",
    f"Loaded {len(lock_dict)} locked standards (TCVN 5574->{lock_dict.get('TCVN 5574')}, TCVN 5575->{lock_dict.get('TCVN 5575')})"
)

print("\n" + "=" * 80)
print("2. KIỂM ĐỊNH CHUYÊN SÂU CƠ HỌC KẾT CẤU & TCVN (BUG-STR-01 -> BUG-STR-08)")
print("=" * 80)

# Test 5: calc_slab.py (BUG-STR-01)
import calc_slab
assert_test(
    "BUG-STR-01a: Bảng tra Rbt, Eb, Rs, alpha_R đúng TCVN 5574:2018 (Bảng 7, 11, 13)",
    calc_slab.CONCRETE_RBT["B25"] == 1.05 and
    calc_slab.CONCRETE_E["B25"] == 30000 and
    calc_slab.REBAR_RS["CB500-V"] == 435 and
    calc_slab.REBAR_RS["CB400-V"] == 350 and
    0.35 <= calc_slab.MaterialProperties("B25", "CB400-V").alpha_m <= 0.45,
    f"B25 Rbt={calc_slab.CONCRETE_RBT['B25']} MPa, Eb={calc_slab.CONCRETE_E['B25']} MPa, CB500-V Rs={calc_slab.REBAR_RS['CB500-V']} MPa, alpha_R={calc_slab.MaterialProperties('B25', 'CB400-V').alpha_m:.3f}"
)
slab_res = calc_slab.calculate_slab({
    "geometry": {"Lx": 6.0, "Ly": 3.0, "h": 0.12, "a": 0.02},
    "loads": {"g_dl": 4.5, "q_ll": 2.0, "gamma_g": 1.1, "gamma_q": 1.3},
    "materials": {"concrete_grade": "B25", "rebar_grade": "CB400-V"},
    "boundary_conditions": "fixed_all"
})
m_res = slab_res["results"]["moments"]
r_res = slab_res["results"]["reinforcement"]
assert_test(
    "BUG-STR-01b & 01c: Sàn 2 phương tính moment theo nhịp ngắn L_short^2 và tính đúng eta_M = As_req / As_prov",
    m_res["M_x_pos"] > 0 and m_res["M_y_pos"] > 0 and
    max(m_res["M_x_pos"], m_res["M_y_pos"]) < 15.0 and
    0.05 < r_res["eta_M"] < 1.0 and
    "Calculation_Logs" in slab_res,
    f"M_x_pos={m_res['M_x_pos']} kNm/m, M_y_pos={m_res['M_y_pos']} kNm/m, eta_M={r_res['eta_M']}"
)

# Test 6: calc_crack_width.py (BUG-STR-02)
import calc_crack_width
crack_dict = calc_crack_width.calculate_crack_width_check({
    "geometry": {"b": 300, "h": 600, "a_bottom": 40, "a_top": 40},
    "reinforcement": {"rebar_bottom": "4d22", "rebar_top": "2d16", "As_bottom": 1520.0, "As_top": 402.0},
    "loads": {"M_service": 120.0, "N_service": 0.0},
    "materials": {"concrete_grade": "B25", "rebar_grade": "CB400-V"},
    "environment": {"type": "normal", "humidity": 60}
})
c_res = crack_dict["results"]["crack_width"]
assert_test(
    "BUG-STR-02a: Công thức bề rộng vết nứt a_crc theo TCVN 5574:2018 Mục 8.2.2.2 không nhân thừa phi_eff",
    0.01 < c_res["a_crc"] <= c_res["a_crc_limit"] and c_res["passed"] is True,
    f"a_crc={c_res['a_crc']} mm <= {c_res['a_crc_limit']} mm (passed={c_res['passed']})"
)
assert_test(
    "BUG-STR-02b: calc_crack_width.py xuất đầy đủ Standard_Method & Calculation_Logs ở root JSON",
    "Standard_Method" in crack_dict and len(crack_dict.get("Calculation_Logs", [])) >= 3,
    f"Standard_Method={crack_dict.get('Standard_Method')}"
)

# Test 7: calc_rc_wall.py (BUG-STR-03)
import calc_rc_wall
wall_res = calc_rc_wall.calc_rc_wall(
    bw=250, hw=3000, L0=3600, N_ed=2500.0, M_ed=800.0, V_ed=350.0,
    concrete="B30", rebar="CB400-V", bending_plane="in_plane"
)
assert_test(
    "BUG-STR-03a: Hệ số uốn dọc vách BTCT eta >= 1.0 (khuếch đại lệch tâm theo TCVN 5574:2018 Mục 8.1.2.4.2)",
    wall_res["eta_slenderness"] >= 1.0 and wall_res["M_ed_calc_kNm"] >= wall_res["M_ed_kNm"],
    f"eta_slenderness={wall_res['eta_slenderness']} >= 1.0, M_ed_calc={wall_res['M_ed_calc_kNm']} kNm"
)
assert_test(
    "BUG-STR-03b: Vách BTCT kiểm tra đồng thời Nén uốn trong mặt phẳng (hw=3000mm) và Cắt Q_ed <= Q_Rd",
    wall_res["h_mm"] == 3000 and wall_res["eta_shear"] < 1.0 and wall_res["overall_eta"] < 1.0,
    f"h_mm={wall_res['h_mm']}, eta_shear={wall_res['eta_shear']}, overall_eta={wall_res['overall_eta']} ({wall_res['Rating']})"
)

# Test 8: calc_steel_beam_tcvn.py (BUG-STR-04)
import calc_steel_beam_tcvn
steel_res = calc_steel_beam_tcvn.calc_steel_beam_tcvn(
    h=400, b=200, tw=8, tf=12, M_ed=112.5, V_ed=75.0, fy=235, L_span=6000, L_b=3000, lateral_support=False
)
expected_Mb_Rd = round(steel_res["chi_LT"] * steel_res["Wpl_cm3"] * 1e3 * (235.0 / 1.10) * 1e-6, 2)
assert_test(
    "BUG-STR-04: Dầm thép TCVN 5575:2024 tính M_b,Rd = chi_LT * W * fy / gamma_M1 (không chia kép gamma_M0)",
    abs(steel_res["M_b_Rd_kNm"] - expected_Mb_Rd) <= 0.15 and steel_res["status"] == "PASSED",
    f"M_b,Rd={steel_res['M_b_Rd_kNm']} kNm (expected ~{expected_Mb_Rd} kNm), Rating={steel_res['Rating']}"
)

# Test 9: calc_punching_shear.py (BUG-STR-05)
import calc_punching_shear
punch_res = calc_punching_shear.calc_punching_shear(
    concrete="B30", rebar="CB400-V", h=250, a=30,
    column_b=400, column_h=400, column_position="interior",
    F_b=350.0, M_bx=30.0, M_by=15.0
)
expected_u = 2.0 * (400.0 + 400.0 + 2.0 * punch_res["d_mm"])
assert_test(
    "BUG-STR-05: Chọc thủng sàn phẳng TCVN 5574:2018 Mục 8.1.6 tính đúng chu vi u_b = 2(b_c+h_c+2h0) và W_bx, W_by",
    abs(punch_res["u_b_mm"] - expected_u) < 1.0 and punch_res["W_bx_cm2"] > 4000.0 and punch_res["eta_punch"] < 1.0,
    f"u_b={punch_res['u_b_mm']} mm, W_bx={punch_res['W_bx_cm2']} cm², eta={punch_res['eta_punch']}"
)

# Test 10: earthquake_load_calc.py (BUG-STR-08)
out_eq = subprocess.check_output(
    [sys.executable, str(PATCH_DIR / "earthquake_load_calc.py"), "--building", "TowerA", "--height", "36", "--floors", "10", "--zone", "II", "--soil", "C", "--weight_kn", "80000"],
    text=True
)
eq_data = json.loads(out_eq)
assert_test(
    "BUG-STR-08: Động đất TCVN 9386:2025 không nhân kép 2.5*2.5=6.25 và không ghi đè Cs_calc bằng Cs_min",
    0.015 < eq_data["C_s"] < 0.08 and eq_data["V_base"] > 1200.0 and "Calculation_Logs" in eq_data,
    f"C_s={eq_data['C_s']}, V_base={eq_data['V_base']} kN"
)

# Test 11: calc_isolated_footing.py & calc_continuous_beam.py (BUG-STR-06)
out_foot = subprocess.check_output(
    [sys.executable, str(PATCH_DIR / "calc_isolated_footing.py"), "-B", "2.0", "-L", "2.4", "-H", "0.6", "--ntc", "600", "--mtc", "60"],
    text=True
)
foot_data = json.loads(out_foot)
assert_test(
    "BUG-STR-06a: Móng đơn tính moment theo biểu đồ áp lực hình thang dưới đáy móng và F_b,ult = Rbt*u_tb*h0",
    foot_data["reinforcement"]["M_x_kNm"] > 140.0 and foot_data["punching_shear"]["status"] == "PASS",
    f"M_x={foot_data['reinforcement']['M_x_kNm']} kNm, F_bu={foot_data['punching_shear']['F_bu_kN']} kN, eta={foot_data['punching_shear']['eta_punch']}"
)

out_beam = subprocess.check_output(
    [sys.executable, str(PATCH_DIR / "calc_continuous_beam.py"), "--spans", "5.0", "6.0", "5.0", "--qd", "12", "--ql", "8", "-b", "250", "-H", "500"],
    text=True
)
beam_data = json.loads(out_beam)
assert_test(
    "BUG-STR-06b: Dầm liên tục kiểm tra ứng suất nén bê tông dải nghiêng Q <= 0.3*phi_b1*Rb*b*h0 nhất quán với công thức log",
    beam_data["shear_checks"]["Q_strip_ult_kN"] > 400.0 and beam_data["status"] == "PASSED",
    f"Q_strip_ult={beam_data['shear_checks']['Q_strip_ult_kN']} kN, eta_V={beam_data['eta_V']}"
)

# Test 12: SKILL_TEMPWORKS 4 calculators (BUG-STR-07)
out_fw_slab = subprocess.check_output(
    [sys.executable, str(PATCH_DIR / "calc_formwork_slab.py"), "--thickness", "150", "--span", "6.0", "--json"],
    text=True
)
fw_slab_data = json.loads(out_fw_slab)
assert_test(
    "BUG-STR-07a: calc_formwork_slab.py đổi đơn vị q * 1000 N/m² khi tính độ võng ván khuôn (delta > 0.1 mm)",
    fw_slab_data["plywood_deflection"] > 0.1 and "Calculation_Logs" in fw_slab_data,
    f"plywood_deflection={fw_slab_data['plywood_deflection']} mm"
)

out_fw_col = subprocess.check_output(
    [sys.executable, str(PATCH_DIR / "calc_formwork_column.py"), "--width", "500", "--depth", "500", "--height", "3.6", "--rate", "2.5", "--temp", "25", "--json"],
    text=True
)
fw_col_data = json.loads(out_fw_col)
assert_test(
    "BUG-STR-07b: calc_formwork_column.py tính áp lực ngang bê tông tươi theo ACI 347-04 & xuất root Calculation_Logs",
    fw_col_data["max_lateral_pressure"] >= 45.0 and "Calculation_Logs" in fw_col_data and "Standard_Method" in fw_col_data,
    f"P_max={fw_col_data['max_lateral_pressure']} kN/m²"
)

out_fw_wall = subprocess.check_output(
    [sys.executable, str(PATCH_DIR / "calc_formwork_wall.py"), "--height", "3.6", "--length", "6.0", "--thickness", "250", "--rate", "2.0", "--temp", "25", "--json"],
    text=True
)
fw_wall_data = json.loads(out_fw_wall)
assert_test(
    "BUG-STR-07c: calc_formwork_wall.py tính áp lực ngang bê tông tươi theo ACI 347-04 & xuất root Calculation_Logs",
    fw_wall_data["max_lateral_pressure"] >= 40.0 and "Calculation_Logs" in fw_wall_data and "Standard_Method" in fw_wall_data,
    f"P_max={fw_wall_data['max_lateral_pressure']} kN/m²"
)

out_shore = subprocess.check_output(
    [sys.executable, str(PATCH_DIR / "calc_shoring_system.py"), "--height", "6.0", "--load", "20.0", "--system", "ringlock", "--json"],
    text=True
)
shore_data = json.loads(out_shore)
assert_test(
    "BUG-STR-07d: calc_shoring_system.py tính độ mảnh chân giáo Ringlock theo bước giằng ngang L_eff=1.5m & xuất root Calculation_Logs",
    shore_data["slenderness_ratio"] < 120.0 and shore_data["all_pass"] is True and "Calculation_Logs" in shore_data,
    f"slenderness={shore_data['slenderness_ratio']} <= 150, status={shore_data['stability_check']}"
)

print("\n" + "=" * 80)
print(f"TỔNG KẾT KIỂM THỬ: {passed} PASSED / {failed} FAILED")
print("=" * 80)
if failed > 0:
    sys.exit(1)
