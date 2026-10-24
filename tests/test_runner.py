import sys
import json
import os
import importlib.util
import traceback

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# =============================================================================
# test_runner.py — Regression Test cho TOAN BO calculator scripts
# =============================================================================
# Chay: python test_runner.py
# Output: Bao cao PASSED/FAILED cho tung script + tong ket
# =============================================================================

this_dir = os.path.dirname(os.path.abspath(__file__))
SKILLS_ROOT = this_dir if os.path.basename(this_dir) == 'skills' else os.path.join(os.path.dirname(this_dir), 'skills')

# ---- Danh sach cac test case ----
# Moi entry: (module_path, function_name, kwargs, expected_checks)
# expected_checks la dict: {field: lambda value: bool}
TEST_CASES = [
    # =========================================================================
    # 1. Design_Evaluation / calculators
    # =========================================================================
    {
        "name": "RC Flexure Design — B25 300x560 M=250kNm",
        "script": "Design_Evaluation/calculators/rc_flexure_design.py",
        "function": "design_rc_flexure",
        "kwargs": {"M": 250, "b": 300, "h0": 560, "Rb": 14.5, "Rs": 350},
        "checks": {
            "Standard_Method": lambda v: v == "TCVN 5574:2018",
            "Calculation_Logs": lambda v: len(v) >= 1,
        }
    },
    {
        "name": "Deflection Check — L=6m M=80kNm",
        "script": "Design_Evaluation/calculators/deflection_check.py",
        "function": "calculate_deflection",
        "kwargs": {"L": 6000, "M": 80, "E": 30000, "I_eff": 5.4e9},
        "checks": {
            "Standard_Method": lambda v: "TCVN 5574" in v,
        }
    },
    {
        "name": "Steel Member Check v2024 — I400x200",
        "script": "Design_Evaluation/calculators/steel_member_check_v2024.py",
        "function": "check_steel_member_v2024",
        "kwargs": {"M": 200, "N": 0, "V": 100, "Area": 8450, "Wx": 1160e3,
                   "Iy": 17.4e6, "tf": 13, "tw": 8, "h": 400, "b": 200, "L_beam": 6000, "fy": 345},
        "checks": {
            "Standard_Method": lambda v: "TCVN 5575:2024" in v,
            "Results": lambda v: v.get("Status") == "PASS",
        }
    },
    {
        "name": "Foundation Bearing — B=2m D=1.5m R0=150kPa",
        "script": "Design_Evaluation/calculators/foundation_bearing.py",
        "function": "calculate_bearing_capacity",
        "kwargs": {"R0": 150, "b": 2.0, "d": 1.5, "gamma_II": 18.5},
        "checks": {
            "Standard_Method": lambda v: "TCVN 9362" in v,
        }
    },
    {
        "name": "Wind Load — w0=0.83 z=30m cat B",
        "script": "Design_Evaluation/calculators/wind_load_calc.py",
        "function": "calculate_wind_load",
        "kwargs": {"w0": 0.83, "z": 30, "terrain_category": "B", "c": 0.8, "gamma_f": 1.2,
                   "gamma_f_source": "TCVN 2737:2023 Bang 1"},
        "checks": {
            "Standard_Method": lambda v: "TCVN 2737:2023" in v,
        }
    },

    # =========================================================================
    # 2. Structural_Design_Engineer / scripts
    # =========================================================================
    {
        "name": "RC Section — B25 300x600 M=250kNm V=120kN",
        "script": "Structural_Design_Engineer/scripts/calc_rc_section.py",
        "function": "calc_rc_beam",
        "kwargs": {"b": 300, "h": 600, "a": 40, "concrete": "B25", "rebar": "CB400-V",
                   "M_ed": 250, "V_ed": 120, "stirrup_dia": 8, "stirrup_legs": 2, "stirrup_spacing": 150},
        "checks": {
            "status": lambda v: v == "PASSED",
            "Standard_Method": lambda v: v == "TCVN 5574:2018",
            "Calculation_Logs": lambda v: len(v) >= 2,
        }
    },
    {
        "name": "Steel Beam TCVN — I400x200 M=220kNm",
        "script": "Structural_Design_Engineer/scripts/calc_steel_beam_tcvn.py",
        "function": "calc_steel_beam_tcvn",
        "kwargs": {"h": 400, "b": 200, "tw": 8, "tf": 13,
                   "fy": 345, "M_ed": 220, "V_ed": 100, "L_span": 6000},
        "checks": {
            "status": lambda v: v == "PASSED",
            "Standard_Method": lambda v: v == "TCVN 5575:2024",
        }
    },
    {
        "name": "Steel Connection TCVN — M20 cap 8.8 x6",
        "script": "Structural_Design_Engineer/scripts/calc_steel_connection_tcvn.py",
        "function": "calc_steel_connection_tcvn",
        "kwargs": {"bolt_d": 20, "grade": "8.8", "n_bolts": 6, "V_ed": 180,
                   "F_t_ed": 50, "t_plate": 12, "f_u_plate": 400},
        "checks": {
            "status": lambda v: v == "PASSED",
            "Standard_Method": lambda v: v == "TCVN 5575:2024",
            "eta_shear": lambda v: 0 < v < 1.0,
        }
    },
    {
        "name": "RC Column — 400x400 B25 N=1200kN M=120kNm",
        "script": "Structural_Design_Engineer/scripts/calc_rc_column.py",
        "function": "calc_rc_column",
        "kwargs": {"b": 400, "h": 400, "a": 40, "concrete": "B25", "rebar": "CB400-V",
                   "N_ed": 1200, "M_ed": 120, "L0": 4200},
        "checks": {
            "status": lambda v: v == "PASSED",
            "Standard_Method": lambda v: v == "TCVN 5574:2018",
            "eccentricity_type": lambda v: v == "LARGE",
            "overall_eta": lambda v: 0 < v <= 1.0,
        }
    },
    {
        "name": "Weld TCVN — Han goc kf=6 L=200 F=150kN",
        "script": "Structural_Design_Engineer/scripts/calc_weld_tcvn.py",
        "function": "calc_fillet_weld",
        "kwargs": {"weld_length": 200, "weld_leg": 6, "n_welds": 2,
                   "F_ed": 150, "electrode": "E42", "welding_method": "auto", "steel_grade": "CT38"},
        "checks": {
            "status": lambda v: v == "PASSED",
            "Standard_Method": lambda v: v == "TCVN 5575:2024",
            "overall_eta": lambda v: 0 < v < 1.0,
        }
    },
    {
        "name": "Foundation Pile — 400x400 L=20m 2 lop",
        "script": "Structural_Design_Engineer/scripts/calc_foundation_pile.py",
        "function": "calc_pile_capacity",
        "kwargs": {"pile_type": "driven", "pile_d": 400, "pile_length": 20,
                   "tip_soil_type": "cat_hat_trung", "tip_soil_state": "chat_vua", "N_ed": 800},
        "checks": {
            "status": lambda v: v == "PASSED",
            "Standard_Method": lambda v: v == "TCVN 10304:2025",
            "overall_eta": lambda v: 0 < v < 1.0,
            "Ra_kN": lambda v: v > 0,
        }
    },
    {
        "name": "RC Slab 2-way — B25 Lx=6m Ly=3m h=120mm",
        "script": "Structural_Design_Engineer/scripts/calc_slab.py",
        "function": "calculate_slab",
        "kwargs": {
            "input_data": {
                "project": {"name": "Test Slab"},
                "geometry": {"Lx": 6.0, "Ly": 3.0, "h": 0.12, "a": 0.02},
                "materials": {"concrete_grade": "B25", "rebar_grade": "CB300", "gamma_m": 1.15},
                "loads": {"g_dl": 3.5, "q_ll": 2.5, "gamma_g": 1.2, "gamma_q": 1.3},
                "boundary_conditions": "simply_supported"
            }
        },
        "checks": {
            "conclusion": lambda v: v.get("status") == "PASSED",
            "calculator": lambda v: "TCVN 5574:2018" in v.get("standard", ""),
            "summary": lambda v: v.get("passed") is True,
        }
    },

    # =========================================================================
    # 3. SKILL_TEMPWORKS / scripts
    # =========================================================================
    {
        "name": "Slab Formwork — h=200mm span=5m B25",
        "script": "SKILL_TEMPWORKS/calculators/calc_formwork_slab.py",
        "function": "calc_slab_formwork",
        "kwargs": {"thickness": 200, "span": 5.0, "grade": "B25", "plywood": 18},
        "checks": {
            "all_pass": lambda v: v is True,
            "standard_method": lambda v: "ACI 347-04" in v,
            "calculation_logs": lambda v: len(v) >= 5,
        }
    },
]


def load_function(script_path, function_name):
    """Dynamically load a function from a Python script."""
    abs_path = os.path.join(SKILLS_ROOT, script_path)
    if not os.path.exists(abs_path):
        raise FileNotFoundError(f"Script not found: {abs_path}")

    spec = importlib.util.spec_from_file_location("module", abs_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    func = getattr(module, function_name)
    return func


def run_tests():
    """Run all test cases and report results."""
    results = []
    passed = 0
    failed = 0
    errors = 0

    print("=" * 70)
    print("  REGRESSION TEST RUNNER — Skills Calculator Suite")
    print("=" * 70)
    print()

    for i, tc in enumerate(TEST_CASES, 1):
        name = tc["name"]
        script = tc["script"]
        func_name = tc["function"]
        kwargs = tc["kwargs"]
        checks = tc["checks"]

        print(f"[{i:02d}/{len(TEST_CASES):02d}] {name}")
        print(f"       Script: {script}")

        try:
            func = load_function(script, func_name)
            result = func(**kwargs)

            # Run checks
            check_results = {}
            all_passed = True
            for field, check_fn in checks.items():
                value = result.get(field)
                try:
                    ok = check_fn(value)
                except Exception:
                    ok = False
                check_results[field] = {"value": value, "passed": ok}
                if not ok:
                    all_passed = False

            if all_passed:
                print(f"       ✅ PASSED (eta={result.get('overall_eta', 'N/A')})")
                passed += 1
                status = "PASSED"
            else:
                failed_checks = [f for f, r in check_results.items() if not r["passed"]]
                print(f"       ❌ FAILED — checks: {failed_checks}")
                for f in failed_checks:
                    print(f"          {f} = {check_results[f]['value']}")
                failed += 1
                status = "FAILED"

            results.append({"name": name, "status": status, "checks": check_results})

        except Exception as e:
            print(f"       💥 ERROR — {type(e).__name__}: {e}")
            traceback.print_exc()
            errors += 1
            results.append({"name": name, "status": "ERROR", "error": str(e)})

        print()

    # Summary
    total = passed + failed + errors
    print("=" * 70)
    print(f"  SUMMARY: {passed}/{total} PASSED | {failed} FAILED | {errors} ERRORS")
    print("=" * 70)

    if failed + errors == 0:
        print("\n  🎉 ALL TESTS PASSED!\n")
    else:
        print(f"\n  ⚠️ {failed + errors} issue(s) need attention.\n")

    return {"passed": passed, "failed": failed, "errors": errors, "total": total}


if __name__ == "__main__":
    run_tests()
