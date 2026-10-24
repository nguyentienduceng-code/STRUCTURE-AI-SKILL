#!/usr/bin/env python3
"""
update_prices.py — Cập nhật đơn giá vật tư từ nguồn dữ liệu

Usage:
    python update_prices.py --source "https://example.com/dscl_2025.xlsx" --output prices.json
    python update_prices.py --manual --item "thép D25" --price 18500 --unit "kg"

Quy trình cập nhật:
1. Tải bảng giá mới nhất (DSCL hoặc TT08 hoặc BXD)
2. Parse dữ liệu → mapping vào cấu trúc chuẩn
3. Tính tỷ lệ thay đổi so với bảng giá hiện tại
4. Xuất file prices.json mới
"""

import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
import argparse
import json
import sys
import re
from datetime import datetime, date
from pathlib import Path

# ─── Standard price structure ─────────────────────────────────────────────────

UNIT_PRICE_TEMPLATE = {
    "item_code": "",         # Mã vật tư
    "item_name": "",         # Tên vật tư
    "unit": "",              # Đơn vị (kg, m³, m², cái...)
    "unit_price_VND": 0.0,   # Đơn giá VND
    "source": "",            # Nguồn: "TT08/2021", "DSCL_2025", "manual"...
    "last_updated": "",      # Ngày cập nhật
    "region": "HCM",        # Vùng (HCM, HN, ĐN)
    "notes": "",             # Ghi chú
}

# ─── Standard item codes ─────────────────────────────────────────────────────

ITEM_MAPPING = {
    # Thép thanh
    "thép D6":    {"code": "STEEL-006",  "unit": "kg", "category": "Thép thanh"},
    "thép D8":    {"code": "STEEL-008",  "unit": "kg", "category": "Thép thanh"},
    "thép D10":   {"code": "STEEL-010",  "unit": "kg", "category": "Thép thanh"},
    "thép D12":   {"code": "STEEL-012",  "unit": "kg", "category": "Thép thanh"},
    "thép D16":   {"code": "STEEL-016",  "unit": "kg", "category": "Thép thanh"},
    "thép D18":   {"code": "STEEL-018",  "unit": "kg", "category": "Thép thanh"},
    "thép D20":   {"code": "STEEL-020",  "unit": "kg", "category": "Thép thanh"},
    "thép D22":   {"code": "STEEL-022",  "unit": "kg", "category": "Thép thanh"},
    "thép D25":   {"code": "STEEL-025",  "unit": "kg", "category": "Thép thanh"},
    "thép D28":   {"code": "STEEL-028",  "unit": "kg", "category": "Thép thanh"},
    "thép D32":   {"code": "STEEL-032",  "unit": "kg", "category": "Thép thanh"},
    # Bê tông
    "bt B15":     {"code": "CONC-B15",   "unit": "m³", "category": "Bê tông"},
    "bt B20":     {"code": "CONC-B20",   "unit": "m³", "category": "Bê tông"},
    "bt B25":     {"code": "CONC-B25",   "unit": "m³", "category": "Bê tông"},
    "bt B30":     {"code": "CONC-B30",   "unit": "m³", "category": "Bê tông"},
    "bt B35":     {"code": "CONC-B35",   "unit": "m³", "category": "Bê tông"},
    "bt B40":     {"code": "CONC-B40",   "unit": "m³", "category": "Bê tông"},
    # Cốt pha
    "cốp pha":    {"code": "FORM-STD",   "unit": "m²", "category": "Cốp pha"},
    # Bu lông
    "bulông M16": {"code": "BOLT-M16",   "unit": "cái", "category": "Bu lông"},
    "bulông M20": {"code": "BOLT-M20",   "unit": "cái", "category": "Bu lông"},
    "bulông M24": {"code": "BOLT-M24",   "unit": "cái", "category": "Bu lông"},
    # Xi măng
    "xi măng PCB40": {"code": "CEM-PCB40", "unit": "kg", "category": "Xi măng"},
    # Cát, đá
    "cát vàng":   {"code": "AGG-SAND",   "unit": "m³", "category": "Cốt liệu"},
    "đá 1x2":     {"code": "AGG-CHIP12", "unit": "m³", "category": "Cốt liệu"},
    "đá 2x4":     {"code": "AGG-CHIP24", "unit": "m³", "category": "Cốt liệu"},
}

# ─── Default reference prices (TP.HCM, 2024) ────────────────────────────────

DEFAULT_PRICES = {
    "STEEL-006":  {"price": 14500, "source": "DSCL_2024"},
    "STEEL-008":  {"price": 14500, "source": "DSCL_2024"},
    "STEEL-010":  {"price": 14800, "source": "DSCL_2024"},
    "STEEL-012":  {"price": 14800, "source": "DSCL_2024"},
    "STEEL-016":  {"price": 15200, "source": "DSCL_2024"},
    "STEEL-018":  {"price": 15200, "source": "DSCL_2024"},
    "STEEL-020":  {"price": 15300, "source": "DSCL_2024"},
    "STEEL-022":  {"price": 15500, "source": "DSCL_2024"},
    "STEEL-025":  {"price": 15700, "source": "DSCL_2024"},
    "STEEL-028":  {"price": 15800, "source": "DSCL_2024"},
    "STEEL-032":  {"price": 16000, "source": "DSCL_2024"},
    "CONC-B15":   {"price": 1150000, "source": "DSCL_2024"},
    "CONC-B20":   {"price": 1250000, "source": "DSCL_2024"},
    "CONC-B25":   {"price": 1350000, "source": "DSCL_2024"},
    "CONC-B30":   {"price": 1500000, "source": "DSCL_2024"},
    "CONC-B35":   {"price": 1650000, "source": "DSCL_2024"},
    "CONC-B40":   {"price": 1850000, "source": "DSCL_2024"},
    "FORM-STD":   {"price": 250000, "source": "DSCL_2024"},
    "BOLT-M16":   {"price": 25000, "source": "DSCL_2024"},
    "BOLT-M20":   {"price": 38000, "source": "DSCL_2024"},
    "BOLT-M24":   {"price": 55000, "source": "DSCL_2024"},
    "CEM-PCB40":  {"price": 1800, "source": "DSCL_2024"},
    "AGG-SAND":   {"price": 350000, "source": "DSCL_2024"},
    "AGG-CHIP12": {"price": 420000, "source": "DSCL_2024"},
    "AGG-CHIP24": {"price": 380000, "source": "DSCL_2024"},
}


# ─── Core functions ──────────────────────────────────────────────────────────

def build_price_database(base_prices: dict, region: str = "HCM") -> dict:
    """Build full price database from base prices."""
    db = {}
    today = date.today().isoformat()

    for code, data in base_prices.items():
        db[code] = {
            **UNIT_PRICE_TEMPLATE,
            "item_code": code,
            "unit_price_VND": data["price"],
            "source": data["source"],
            "last_updated": today,
            "region": region,
        }

    # Add Vietnamese names
    name_map = {v["code"]: k for k, v in ITEM_MAPPING.items()}
    for code, record in db.items():
        if code in name_map:
            record["item_name"] = name_map[code]
        category = next((v["category"] for v in ITEM_MAPPING.values() if v["code"] == code), "")
        record["category"] = category

    return db


def apply_manual_update(db: dict, item_code: str, new_price: float) -> dict:
    """Apply a manual price update to existing database."""
    if item_code not in db:
        print(f"[W001] Item code '{item_code}' không tìm thấy trong database.", file=sys.stderr)
        return db

    old_price = db[item_code]["unit_price_VND"]
    change_pct = (new_price - old_price) / old_price * 100

    db[item_code]["unit_price_VND"] = new_price
    db[item_code]["last_updated"] = date.today().isoformat()
    db[item_code]["source"] = "manual"
    db[item_code]["notes"] = (
        f"Cập nhật thủ công: {old_price:,.0f} → {new_price:,.0f} VND "
        f"({change_pct:+.2f}%)"
    )
    print(f"[I001] Cập nhật {item_code}: {old_price:,.0f} → {new_price:,.0f} "
          f"({change_pct:+.2f}%)")
    return db


def generate_price_change_report(old_db: dict, new_db: dict) -> list:
    """Generate a report of all price changes."""
    changes = []
    for code in old_db:
        if code not in new_db:
            continue
        old_price = old_db[code]["unit_price_VND"]
        new_price = new_db[code]["unit_price_VND"]
        if old_price != new_price:
            change_pct = (new_price - old_price) / old_price * 100
            changes.append({
                "item_code": code,
                "item_name": new_db[code].get("item_name", code),
                "old_price_VND": old_price,
                "new_price_VND": new_price,
                "change_pct": round(change_pct, 2),
                "direction": "UP" if change_pct > 0 else "DOWN",
                "impact": "HIGH" if abs(change_pct) > 10 else "MEDIUM" if abs(change_pct) > 5 else "LOW"
            })
    changes.sort(key=lambda x: abs(x["change_pct"]), reverse=True)
    return changes


def export_report(changes: list) -> str:
    """Export price change report as markdown."""
    lines = []
    lines.append("# BÁO CÁO THAY ĐỔI ĐƠN GIÁ")
    lines.append(f"> **Ngày:** {date.today().isoformat()}")
    lines.append(f"> **Tổng mục thay đổi:** {len(changes)}")
    lines.append("")
    lines.append("## Tổng quan")
    ups = [c for c in changes if c["direction"] == "UP"]
    downs = [c for c in changes if c["direction"] == "DOWN"]
    lines.append(f"- 🔴 Tăng giá: **{len(ups)}** mục")
    lines.append(f"- 🟢 Giảm giá: **{len(downs)}** mục")
    lines.append("")

    if not changes:
        lines.append("*Không có thay đổi đơn giá.*")
        return "\n".join(lines)

    lines.append("## Chi tiết thay đổi")
    lines.append("")
    lines.append("| Mã | Tên vật tư | Đơn giá cũ | Đơn giá mới | Thay đổi | Mức độ |")
    lines.append("|---|---|---|---|---|---|")
    for c in changes:
        icon = "🔴" if c["impact"] == "HIGH" else "🟡" if c["impact"] == "MEDIUM" else "🟢"
        lines.append(
            f"| {c['item_code']} | {c['item_name']} | "
            f"{c['old_price_VND']:,.0f} | {c['new_price_VND']:,.0f} | "
            f"{c['direction']} {c['change_pct']:+.2f}% | {icon} {c['impact']} |"
        )

    lines.append("")
    lines.append("---")
    lines.append("*Tạo bởi Cost_Estimator/update_prices.py*")
    return "\n".join(lines)


# ─── CLI ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Cập nhật đơn giá vật tư")
    parser.add_argument("--output", type=str, required=True, help="File JSON output")
    parser.add_argument("--manual", action="store_true", help="Cập nhật thủ công")
    parser.add_argument("--item", type=str, help="Mã vật tư (ví dụ: STEEL-025)")
    parser.add_argument("--price", type=float, help="Đơn giá mới (VND)")
    parser.add_argument("--region", type=str, default="HCM", help="Vùng (HCM, HN, ĐN)")
    parser.add_argument("--report", action="store_true", help="Xuất báo cáo thay đổi")
    parser.add_argument("--load-existing", type=str, help="Load existing prices.json first")
    args = parser.parse_args()

    # Load or create base database
    if args.load_existing and Path(args.load_existing).exists():
        with open(args.load_existing, encoding="utf-8") as f:
            db = json.load(f)
        print(f"[I001] Đã tải database hiện có từ: {args.load_existing}", file=sys.stderr)
    else:
        db = build_price_database(DEFAULT_PRICES, args.region)
        print(f"[I001] Khởi tạo database mới với {len(db)} mục", file=sys.stderr)

    old_db = {k: dict(v) for k, v in db.items()}

    # Apply manual update
    if args.manual:
        if not args.item or args.price is None:
            print("[E001] --manual yêu cầu --item và --price", file=sys.stderr)
            sys.exit(1)
        db = apply_manual_update(db, args.item, args.price)

    # Generate report
    if args.report:
        changes = generate_price_change_report(old_db, db)
        report_md = export_report(changes)
        report_path = Path(args.output).with_suffix(".md")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_md)
        print(f"[I001] Báo cáo thay đổi: {report_path}", file=sys.stderr)

    # Save JSON
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
    print(f"[I001] Database lưu tại: {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
