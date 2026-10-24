#!/usr/bin/env python3
"""
stage_gate_checklist.py — Tạo checklist tự động theo giai đoạn dự án

Usage:
    python stage_gate_checklist.py --stage BVTC --building "Nhà chung cư 15 tầng"

Output: Markdown checklist tại stdout (redirect sang file nếu cần)
"""

import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
import argparse
import sys

# ─── Stage definitions ───────────────────────────────────────────────────────

STAGES = {
    "QS": {
        "label": "Quy hoạch - Khảo sát",
        "checks": [
            {"id": "QS-01", "text": "Báo cáo khảo sát địa chất (cọc > 30m → bắt buộc)", "critical": True},
            {"id": "QS-02", "text": "Bản đồ hiện trạng 1:500", "critical": False},
            {"id": "QS-03", "text": "Số liệu mực nước ngầm (tháng đo)", "critical": False},
            {"id": "QS-04", "text": "Kết quả thí nghiệm xuyên tiêu chuẩn SPT", "critical": False},
            {"id": "QS-05", "text": "Hồ sơ đất nền tầng địa chất (lớp, chiều dày, R)", "critical": True},
        ]
    },
    "TH": {
        "label": "Thiết kế sơ bộ / Phương án",
        "checks": [
            {"id": "TH-01", "text": "Phương án kết cấu có ≥2 PA so sánh", "critical": False},
            {"id": "TH-02", "text": "Mô hình ETABS/SAP2000 tải trọng đúng TCVN 2737:2023", "critical": True},
            {"id": "TH-03", "text": "Kiểm tra tổ hợp tải trọng (D+L, D+L+Ex, ...)", "critical": True},
            {"id": "TH-04", "text": "Độ võng giới hạn theo TCVN 5574:2018 Bảng M", "critical": True},
            {"id": "TH-05", "text": "Sơ bộ tiết diện cột/dầm có tỷ số η < 0.9", "critical": False},
            {"id": "TH-06", "text": "Ghi chú khối lượng thép ước tính (kg/m²)", "critical": False},
        ]
    },
    "BVTC": {
        "label": "Thiết kế Bản vẽ Thi công",
        "checks": [
            {"id": "BVTC-01", "text": "Thiết kế móng: báo cáo ĐC được duyệt, cọc theo TCVN 10304:2025", "critical": True},
            {"id": "BVTC-02", "text": "Thiết kế cột: η_max < 0.9, lệch tâm ngẫu nhiên theo TCVN 5574:2018 §7.3.3", "critical": True},
            {"id": "BVTC-03", "text": "Thiết kế dầm: uốn + cắt, kiểm tra võng dài hạn", "critical": True},
            {"id": "BVTC-04", "text": "Bố trí thép: khoảng cách tối thiểu theo TCVN 5574:2018 Bảng 10", "critical": True},
            {"id": "BVTC-05", "text": "Chi tiết neo và nối thép (điều kiện neo thực tế ≥ 40d)", "critical": True},
            {"id": "BVTC-06", "text": "Thiết kế vách/lõi cứng: kiểm tra động đất theo TCVN 9386:2025", "critical": True},
            {"id": "BVTC-07", "text": "Bản vẽ cấu tạo mối nối, cốt thép đai đoạn nối", "critical": False},
            {"id": "BVTC-08", "text": "Chỉ dẫn kỹ thuật thi công: độ sụt bê tông, chiều dày lớp bảo vệ", "critical": True},
            {"id": "BVTC-09", "text": "Kiểm tra PTHH cột/vách theo TCVN 5574:2018 §8.5", "critical": True},
            {"id": "BVTC-10", "text": "Độ võng dầm bậc (drop panel): L/250 hoặc ≤ 20mm", "critical": False},
        ]
    },
    "THAU": {
        "label": "Thẩm tra / Phê duyệt",
        "checks": [
            {"id": "THAU-01", "text": "Thẩm tra toàn bộ hồ sơ (xem Design_Evaluation SKILL)", "critical": True},
            {"id": "THAU-02", "text": "Cross-check SKILLKC vs ETABS (dùng SKILL_VERIFY)", "critical": True},
            {"id": "THAU-03", "text": "Kiểm tra PTHH cấu kiện chịu nén (nếu dùng cột BTCT)", "critical": True},
            {"id": "THAU-04", "text": "Đối chiếu với QCVN 03:2022 — cấp công trình", "critical": False},
            {"id": "THAU-05", "text": "NCR đã giải quyết trước khi phê duyệt", "critical": True},
            {"id": "THAU-06", "text": "Chữ ký Kỹ sư trưởng + Chủ nhiệm đồ án", "critical": True},
        ]
    },
    "GIAHAN": {
        "label": "Giám sát thi công / Hồ sơ hoàn công",
        "checks": [
            {"id": "GIAHAN-01", "text": "Nhật ký thi công: giám sát đổ bê tông cột (mẫu test)", "critical": True},
            {"id": "GIAHAN-02", "text": "Biên bản nghiệm thu cốt thép trước đổ BT (kiểm tra lớp bảo vệ)", "critical": True},
            {"id": "GIAHAN-03", "text": "Kết quả nén mẫu bê tông: đạt ≥ mác thiết kế", "critical": True},
            {"id": "GIAHAN-04", "text": "Hồ sơ hoàn công: đối chiếu vs bản vẽ BVTC, ghi chú thay đổi", "critical": True},
            {"id": "GIAHAN-05", "text": "Biên bản nghiệm thu áp lực thử cọc (nếu có)", "critical": False},
            {"id": "GIAHAN-06", "text": "Đo đạc độ lún sau thi công (tối thiểu 3 năm)", "critical": False},
        ]
    }
}

# ─── Building type modifiers ─────────────────────────────────────────────────

BUILDING_MODIFIERS = {
    "chung_cu": [
        {"id": "BC-01", "text": "Kiểm tra phòng cháy chữa cháy theo QCVN 06:2022", "critical": True},
        {"id": "BC-02", "text": "Thiết kế thoát hiểm, lõi thang máy ≥ 2 thang", "critical": True},
        {"id": "BC-03", "text": "Động đất: nhà ≥ 7 tầng → TCVN 9386:2025 P1 + P5", "critical": True},
        {"id": "BC-04", "text": "Kiểm tra chuyển vị ngang (drift) theo TCVN 9386:2025 §5.8", "critical": True},
        {"id": "BC-05", "text": "Vách cứng / lõi thang máy: kiểm tra ổn định theo TCVN 5574:2018", "critical": True},
    ],
    "nha_xuong": [
        {"id": "NX-01", "text": "Tải trọng cầu trục (nếu có): theo TCVN 2737:2023 §6", "critical": True},
        {"id": "NX-02", "text": "Kết cấu thép: kiểm tra ổn định tổng thể (LTB) theo TCVN 5575:2024", "critical": True},
        {"id": "NX-03", "text": "Liên kết bu lông: cấp độ bền, khoảng cách tối thiểu", "critical": True},
        {"id": "NX-04", "text": "Nền nhà xưởng: kiểm tra nền theo TCVN 9362:2012", "critical": False},
    ],
    "cau_duong": [
        {"id": "CD-01", "text": "Tải trọng thiết kế: HL93 (AASHTO) hoặc TCN 272-05", "critical": True},
        {"id": "CD-02", "text": "Kiểm tra ổn định: lật, trượt, trượt ngang", "critical": True},
        {"id": "CD-03", "text": "Thiết kế mố trụ: TCVN 11823:2017", "critical": True},
    ],
    "nha_o": [
        {"id": "NO-01", "text": "Nhà 3-5 tầng: kiểm tra động đất theo TCVN 9386:2025", "critical": False},
        {"id": "NO-02", "text": "Móng: địa chất khảo sát đủ cho thiết kế móng nông", "critical": True},
        {"id": "NO-03", "text": "Dầm sàn BTCT: kiểm tra võng theo TCVN 5574:2018", "critical": True},
    ]
}

# ─── Main ────────────────────────────────────────────────────────────────────

def generate_checklist(stage: str, building: str, output_format: str = "md") -> str:
    stage_data = STAGES.get(stage.upper())
    if not stage_data:
        available = ", ".join(STAGES.keys())
        print(f"[E001] Stage '{stage}' không hợp lệ. Chọn: {available}", file=sys.stderr)
        sys.exit(1)

    modifiers = []
    building_lower = building.lower() if building else ""
    for key, items in BUILDING_MODIFIERS.items():
        if key in building_lower:
            modifiers.extend(items)

    lines = []
    lines.append(f"# CHECKLIST — {stage_data['label']}")
    if building:
        lines.append(f"> **Công trình:** {building}")
        lines.append(f"> **Ngày tạo:** 2026-08-19")
    lines.append("")
    lines.append("| # | Mục kiểm tra | ⚠️ Critical | ☐ Đã OK |")
    lines.append("|---|-------------|------------|---------|")

    all_checks = stage_data["checks"] + modifiers
    for i, item in enumerate(all_checks, 1):
        crit = "🔴" if item["critical"] else ""
        lines.append(f"| {i} | {item['text']} | {crit} | ☐ |")

    lines.append("")
    lines.append("## Ghi chú thực hiện")
    lines.append("")
    lines.append("- [ ] Kiểm tra từng mục từ trên xuống")
    lines.append("- [ ] Mục 🔴 Critical: **bắt buộc đạt 100%** mới chuyển giai đoạn")
    lines.append("- [ ] Mục không Critical: cho phép giải thích nếu không áp dụng (N/A)")
    lines.append("- [ ] Ghi lại kết quả kiểm tra (số liệu, ảnh chụp) vào cột 'Đã OK'")
    lines.append("")
    lines.append("---")
    lines.append("*Tạo bởi Design_Evaluation/skill — SKILLKC v1.3.0*")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Tạo stage gate checklist tự động")
    parser.add_argument("--stage", required=True,
                        choices=["QS", "TH", "BVTC", "THAU", "GIAHAN"],
                        help="Giai đoạn dự án")
    parser.add_argument("--building", type=str, default="",
                        help="Loại công trình (vd: 'Nhà chung cư 15 tầng', 'Nhà xưởng')")
    parser.add_argument("--output", type=str, help="Lưu output ra file (mặc định: stdout)")
    args = parser.parse_args()

    output = generate_checklist(args.stage, args.building)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"[I001] Checklist lưu tại: {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
