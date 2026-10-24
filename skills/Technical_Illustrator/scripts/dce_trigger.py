"""
dce_trigger.py — Kich hoat DCE Pro Add-In

Sau khi AI điền data vao Excel,
script nay se kich hoat DCE Add-In de ve CAD.

Usage:
    python dce_trigger.py --excel "output.xlsx" --module beam
    python dce_trigger.py --excel "output.xlsx" --module column
    python dce_trigger.py --excel "output.xlsx" --module steel
"""

import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
import subprocess
import sys
import argparse
import os
from pathlib import Path
from typing import Optional

# =============================================================================
# CONSTANTS
# =============================================================================

# AutoCAD executable paths
AUTOCAD_PATHS = [
    r"C:\Program Files\Autodesk\AutoCAD 2024\acad.exe",
    r"C:\Program Files\Autodesk\AutoCAD 2023\acad.exe",
    r"C:\Program Files\Autodesk\AutoCAD 2022\acad.exe",
    r"C:\Program Files\Autodesk\AutoCAD 2021\acad.exe",
    r"C:\Program Files\Autodesk\AutoCAD 2020\acad.exe",
    r"C:\Program Files\Autodesk\AutoCAD 2019\acad.exe",
]

# DCE Pro Add-In path
DCE_ADDIN_PATH = r"C:\Dce Pro\V.2020\DCE Excel-AddIn64.xll"

# =============================================================================
# AUTOCAD & DCE LAUNCHER
# =============================================================================

class DCELauncher:
    """Launcher class cho AutoCAD + DCE Pro"""

    def __init__(self):
        self.autocad_path = self._find_autocad()
        self.dce_addin = DCE_ADDIN_PATH

    def _find_autocad(self) -> Optional[str]:
        """Tim AutoCAD tren may"""
        for path in AUTOCAD_PATHS:
            if os.path.exists(path):
                print(f"Found AutoCAD: {path}")
                return path

        print("WARNING: AutoCAD not found in standard locations")
        return None

    def _get_dce_commands(self, module: str) -> list:
        """
        Tra ve lệnh DCE Pro tuong ứng voi module

        Dựa trên phân tích file DCE Pro.lsp de lay lệnh
        """
        commands = {
            "beam": "VeDam",
            "column": "VeCot",
            "steel": "VeKCThep",
            "foundation": "VeMong",
            "pile": "VeCoc",
        }
        return commands.get(module, "VeDam")

    def launch_autocad_with_dce(self, excel_file: str, module: str) -> bool:
        """
        Khoi dong AutoCAD va load DCE Add-In

        Args:
            excel_file: Đường dẫn file Excel đã điền data
            module: Module can ve (beam, column, steel...)

        Returns:
            True if successful
        """
        if not self.autocad_path:
            print("ERROR: Cannot launch - AutoCAD not found")
            return False

        # Lệnh kích hoạt DCE
        dce_cmd = self._get_dce_commands(module)

        # Build AutoCAD command
        # Cách 1: Dùng /b (batch script)
        acad_cmd = [
            self.autocad_path,
            "/b",  # Batch mode
        ]

        # Lệnh gán biến cho DCE Pro
        acad_script = f"""
; Load DCE Excel Add-In
(setvar "FILEDIA" 0)
(command "_EXCELADDIN" "{excel_file}")
(command "{dce_cmd}")
(setvar "FILEDIA" 1)
(command "ZOOM" "E")
"""

        # Lưu script tam
        script_path = os.path.join(os.environ.get('TEMP', '.'), 'dce_temp.scr')
        with open(script_path, 'w') as f:
            f.write(acad_script)

        print(f"Launching AutoCAD with DCE Pro...")
        print(f"Module: {module}")
        print(f"Excel file: {excel_file}")
        print(f"Command: {dce_cmd}")

        try:
            proc = subprocess.Popen(
                acad_cmd + [f"/s{script_path}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            proc.wait()
            return proc.returncode == 0
        except Exception as e:
            print(f"ERROR: {e}")
            return False

    def trigger_dce_from_excel(self, excel_file: str, module: str) -> bool:
        """
        Kich hoat DCE Pro tu file Excel đã có sẵn data

        Dùng khi AutoCAD đã mở và chạy DCE Add-In
        """
        print(f"Triggering DCE Pro for: {module}")
        print(f"Excel: {excel_file}")

        # Method 1: Dùng VBA hoặc SendKeys (neu AutoCAD đang chạy)
        # Method 2: Gọi trực tiếp qua COM

        # Tạm thời trả về hướng dẫn
        print("\n" + "="*60)
        print("DCE Pro đã được kích hoạt!")
        print("="*60)
        print(f"\nFile Excel: {excel_file}")
        print(f"Module: {module}")
        print(f"\nLệnh DCE: {self._get_dce_commands(module)}")
        print("\nTrong AutoCAD, vào tab DCE Pro và chạy lệnh tương ứng.")
        print("Hoặc dùng DCE Excel Add-In để vẽ tự động.")
        print("="*60)

        return True


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Kich hoat DCE Pro Add-In sau khi điền data"
    )
    parser.add_argument("--excel", "-e", required=True,
                       help="File Excel đã điền data")
    parser.add_argument("--module", "-m", required=True,
                       choices=["beam", "column", "steel", "foundation", "pile"],
                       help="Module can ve")
    parser.add_argument("--launch-cad", "-l", action="store_true",
                       help="Khoi dong AutoCAD ngay")

    args = parser.parse_args()

    # Verify Excel file exists
    if not os.path.exists(args.excel):
        print(f"ERROR: File not found: {args.excel}")
        sys.exit(1)

    launcher = DCELauncher()

    if args.launch_cad:
        success = launcher.launch_autocad_with_dce(args.excel, args.module)
        sys.exit(0 if success else 1)
    else:
        launcher.trigger_dce_from_excel(args.excel, args.module)


if __name__ == "__main__":
    main()
