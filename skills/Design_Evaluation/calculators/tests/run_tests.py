# -*- coding: utf-8 -*-
"""
Test Runner cho tất cả calculators

Chạy: python run_tests.py
Hoặc: pytest tests/ -v
"""

import sys
import os

# Force UTF-8 on Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def run_all_tests():
    """Chạy tất cả unit tests"""
    print("=" * 70)
    print("  CALCULATORS SUITE - UNIT TESTS")
    print("=" * 70)
    print()

    tests_dir = os.path.dirname(os.path.abspath(__file__))
    calc_dir = os.path.dirname(tests_dir)
    if tests_dir not in sys.path:
        sys.path.insert(0, tests_dir)
    if calc_dir not in sys.path:
        sys.path.insert(0, calc_dir)

    passed = 0
    failed = 0

    for filename in os.listdir(tests_dir):
        if filename.startswith("test_") and filename.endswith(".py"):
            test_name = filename[:-3]
            print(f"\n📂 Running: {test_name}")

            try:
                # Import test module
                import importlib
                if test_name in sys.modules:
                    mod = importlib.reload(sys.modules[test_name])
                else:
                    mod = importlib.import_module(test_name)

                # Run tests directly (không dùng pytest)
                if hasattr(mod, '__main__'):
                    print(f"   → {test_name}: OK (no errors)")
                    passed += 1
                else:
                    # Check if module has test functions
                    test_funcs = [name for name in dir(mod) if name.startswith('test_')]
                    if test_funcs:
                        for func_name in test_funcs:
                            func = getattr(mod, func_name)
                            if callable(func):
                                print(f"   → {func_name}...", end=" ")
                                try:
                                    func()
                                    print("PASSED ✅")
                                    passed += 1
                                except Exception as e:
                                    print(f"FAILED ❌: {e}")
                                    failed += 1
                    else:
                        print(f"   ⚠️  No test functions found")

            except Exception as e:
                print(f"   ❌ Error loading {test_name}: {e}")
                failed += 1

    print()
    print("=" * 70)
    print(f"  SUMMARY: {passed} passed, {failed} failed")
    print("=" * 70)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
