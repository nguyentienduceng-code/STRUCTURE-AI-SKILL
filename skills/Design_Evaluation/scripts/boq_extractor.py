
# Auto-injected Error Handler
import sys
import os
agents_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if agents_dir not in sys.path:
    sys.path.insert(0, agents_dir)
try:
    from modules.error_handler import with_error_handling
except ImportError:
    # Dummy decorator if module not found
    def with_error_handling(func):
        return func

"""
BOQ Extractor — Trích xuất Bảng Khối Lượng từ file Excel/CSV

Sử dụng:
  python boq_extractor.py --file <boq.xlsx|boq.csv> [--sheet <tên_sheet>] [--output <output.json>]

Ví dụ:
  python boq_extractor.py --file BOQ_DuAnA.xlsx --sheet "Sheet1" --output boq_data.json
  python boq_extractor.py --file BOQ_DuAnA.csv

Tính năng:
  - Đọc file .xlsx (dùng openpyxl) hoặc .csv (dùng csv built-in)
  - Tự động phát hiện header row (dòng chứa "STT" hoặc "Mô tả")
  - Xuất JSON chuẩn cho SKILL_REPORT sử dụng
  - Tự động cài openpyxl nếu chưa có
"""

import json
import csv
import os
import sys
import argparse

sys.stdout.reconfigure(encoding='utf-8')

# Auto-install openpyxl nếu chưa có
try:
    import openpyxl
except ImportError:
    print("⏳ Thư viện openpyxl chưa được cài đặt. Đang cài tự động...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "openpyxl", "-q"])
    import openpyxl
    print("✅ Đã cài xong openpyxl.")


def detect_header_row(rows, max_scan=20):
    """Tìm dòng header dựa trên từ khóa phổ biến trong BOQ."""
    keywords = [
        "stt", "no", "mô tả", "mo ta", "description", "hạng mục", "hang muc",
        "đơn vị", "don vi", "unit", "khối lượng", "khoi luong", "quantity",
        "đơn giá", "don gia", "unit price", "thành tiền", "thanh tien", "amount"
    ]
    for i, row in enumerate(rows[:max_scan]):
        row_text = " ".join([str(cell).lower().strip() for cell in row if cell])
        match_count = sum(1 for kw in keywords if kw in row_text)
        if match_count >= 2:
            return i
    return 0  # fallback: dòng đầu tiên


def read_xlsx(file_path, sheet_name=None):
    """Đọc file .xlsx và trả về danh sách dòng dữ liệu."""
    wb = openpyxl.load_workbook(file_path, data_only=True)

    if sheet_name:
        if sheet_name not in wb.sheetnames:
            print(f"❌ Sheet '{sheet_name}' không tồn tại. Các sheet có sẵn: {wb.sheetnames}")
            sys.exit(1)
        ws = wb[sheet_name]
    else:
        ws = wb.active
        print(f"📄 Đang đọc sheet: '{ws.title}' (mặc định)")

    rows = []
    for row in ws.iter_rows(values_only=True):
        rows.append(list(row))
    return rows


def read_csv(file_path):
    """Đọc file .csv và trả về danh sách dòng dữ liệu."""
    rows = []
    # Thử nhiều encoding phổ biến
    for encoding in ["utf-8-sig", "utf-8", "cp1252", "latin-1"]:
        try:
            with open(file_path, "r", encoding=encoding) as f:
                reader = csv.reader(f)
                rows = [row for row in reader]
            break
        except (UnicodeDecodeError, UnicodeError):
            continue
    return rows


def parse_boq(rows):
    """Parse dữ liệu BOQ từ danh sách dòng thành JSON chuẩn."""
    if not rows:
        print("⚠️ File rỗng — không có dữ liệu để trích xuất.")
        return {"status": "empty", "elements": []}

    header_idx = detect_header_row(rows)
    headers = [str(h).strip() if h else f"Col_{i}" for i, h in enumerate(rows[header_idx])]
    print(f"🔍 Header phát hiện tại dòng {header_idx + 1}: {headers}")

    elements = []
    for row_idx, row in enumerate(rows[header_idx + 1:], start=header_idx + 2):
        # Bỏ qua dòng trống hoàn toàn
        if all(cell is None or str(cell).strip() == "" for cell in row):
            continue

        element = {}
        for col_idx, header in enumerate(headers):
            if col_idx < len(row):
                value = row[col_idx]
                # Chuyển đổi kiểu dữ liệu
                if value is None:
                    element[header] = None
                elif isinstance(value, (int, float)):
                    element[header] = value
                else:
                    element[header] = str(value).strip()
            else:
                element[header] = None
        elements.append(element)

    # Loại bỏ các dòng trống (chỉ có None)
    elements = [e for e in elements if any(v is not None and v != "" for v in e.values())]

    return {
        "status": "success",
        "source": os.path.basename(file_path),
        "header_row": header_idx + 1,
        "columns": headers,
        "total_rows": len(elements),
        "elements": elements
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="BOQ Extractor — Trích xuất Bảng Khối Lượng từ Excel/CSV",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ví dụ:
  python boq_extractor.py --file BOQ_DuAnA.xlsx
  python boq_extractor.py --file BOQ_DuAnA.xlsx --sheet "KC" --output boq.json
  python boq_extractor.py --file BOQ_export.csv
        """
    )
    parser.add_argument("--file", type=str, required=True,
                        help="Đường dẫn đến file BOQ (.xlsx hoặc .csv)")
    parser.add_argument("--sheet", type=str, default=None,
                        help="Tên sheet trong file Excel (mặc định: sheet đầu tiên)")
    parser.add_argument("--output", type=str, default=None,
                        help="Đường dẫn file JSON xuất ra (mặc định: in ra màn hình)")
    args = parser.parse_args()

    file_path = args.file

    if not os.path.exists(file_path):
        print(f"❌ Không tìm thấy file: {file_path}")
        sys.exit(1)

    ext = os.path.splitext(file_path)[1].lower()
    print(f"\n{'='*60}")
    print(f"  BOQ EXTRACTOR — Trích xuất Bảng Khối Lượng")
    print(f"{'='*60}")
    print(f"📁 File: {file_path}")

    if ext in [".xlsx", ".xlsm"]:
        rows = read_xlsx(file_path, args.sheet)
    elif ext == ".csv":
        rows = read_csv(file_path)
    else:
        print(f"❌ Định dạng không hỗ trợ: {ext}. Chỉ hỗ trợ .xlsx, .xlsm, .csv")
        sys.exit(1)

    result = parse_boq(rows)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n✅ Đã xuất {result['total_rows']} dòng dữ liệu → {args.output}")
    else:
        print(f"\n📋 Kết quả ({result['total_rows']} dòng):")
        print(json.dumps(result, ensure_ascii=False, indent=2))
