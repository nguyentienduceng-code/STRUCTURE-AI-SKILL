#!/usr/bin/env python3
"""
search_fm.py — Tìm kiếm Failure Mode Database theo từ khóa

Usage:
    python search_fm.py --keyword "nứt dầm"
    python search_fm.py --keyword "punching" --severity HIGH
    python search_fm.py --list-all
"""

import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
import argparse
import json
import sys
import os
from pathlib import Path

# ─── Inline Failure Mode Database ────────────────────────────────────────────

FAILURE_MODES = [
    {
        "id": "FM-01", "name": "Flexural Failure (Phá hoại uốn)",
        "element": "Dầm BTCT", "severity": "HIGH",
        "crack_pattern": "Vết nứt dọc, vuông góc trục dầm, tại giữa nhịp, mở rộng từ đáy lên",
        "causes": ["Quá tải uốn", "Thiếu cốt thép", "Bê tông yếu"],
        "back_calc_method": "Từ độ võng → q thực tế → so sánh thiết kế",
        "remedy": ["Dán thép đáy dầm", "Giảm tải", "Tăng tiết diện"],
        "keywords": ["uốn", "dầm", "giữa nhịp", "võng", "flexural", "moment"]
    },
    {
        "id": "FM-02", "name": "Shear Failure (Phá hoại cắt)",
        "element": "Dầm BTCT", "severity": "CRITICAL",
        "crack_pattern": "Vết nứt xiên 45° từ đáy lên, gần gối tựa",
        "causes": ["Thiếu đai", "Tải trọng tập trung gần gối", "Cắt vượt"],
        "back_calc_method": "Từ bề rộng khe nứt xiên → tính ứng suất cắt",
        "remedy": ["Bổ sung đai", "Dán thép đai", "Giảm tải trọng"],
        "keywords": ["cắt", "xiên", "gối", "đai", "shear", "nghiêng"]
    },
    {
        "id": "FM-03", "name": "Compression Failure (Phá hoại nén)",
        "element": "Cột BTCT", "severity": "HIGH",
        "crack_pattern": "Vỡ bê tông, thép cong ra ngoài, vết nứt song song trục cột",
        "causes": ["Vượt tải nén", "Tỷ lệ cốt thép cao", "Bê tông không đạt mác"],
        "back_calc_method": "Lấy mẫu core → xác định f_c thực tế → kiểm tra PTHH",
        "remedy": ["Bọc thép", "Tăng tiết diện cột", "Giảm tải"],
        "keywords": ["nén", "cột", "bóp", "compression", "crushing"]
    },
    {
        "id": "FM-04", "name": "Buckling (Overshooting Column)",
        "element": "Cột thanh mảnh", "severity": "HIGH",
        "crack_pattern": "Cột nghiêng, võng ngang bất thường, vết nứt kết hợp nén + uốn",
        "causes": ["Độ mảnh lớn", "Tải trọng không đúng trục", "Thiếu liên kết ngang"],
        "back_calc_method": "Đo độ nghiêng → tính mô men phụ → kiểm tra PTHH cột",
        "remedy": ["Tăng tiết diện", "Thêm liên kết ngang", "Giảm chiều dài tự do"],
        "keywords": ["mảnh", "nghiêng", "buckling", "slender", "lệch tâm"]
    },
    {
        "id": "FM-05", "name": "Punching Shear (Phá hoại đục thủng)",
        "element": "Sàn BTCT / Đế móng", "severity": "HIGH",
        "crack_pattern": "Vết nứt hình nón 45° quanh cột, xuyên suốt bản sàn",
        "causes": ["Tải trọng tập trung lớn", "Sàn mỏng", "Thiếu thép đục lỗ"],
        "back_calc_method": "Tính V_c theo TCVN 5574:2018 §8.5 → so sánh V thực tế",
        "remedy": ["Tăng chiều dày sàn", "Bổ sung thép đục", "Gia cố đầu cột"],
        "keywords": ["đục thủng", "xuyên", "sàn", "punching", "flat slab"]
    },
    {
        "id": "FM-06", "name": "Excessive Deflection (Võng quá mức)",
        "element": "Dầm / Sàn", "severity": "MEDIUM",
        "crack_pattern": "Võng nhìn thấy bằng mắt, kèm vết nứt uốn mạng nhện",
        "causes": ["Quá tải", "E thấp (bê tông yếu)", "Thiếu độ cứng tiết diện"],
        "back_calc_method": "Đo δ thực tế → tính q = (384×E×I×δ)/(5×L⁴) → so sánh q TK",
        "remedy": ["Tăng tiết diện", "Dán thép", "Giảm nhịp"],
        "keywords": ["võng", "độ võng", "deflection", "sagging", "quá mức"]
    },
    {
        "id": "FM-07", "name": "Corrosion of Reinforcement (Cốt thép gỉ)",
        "element": "Cấu kiện BTCT", "severity": "MEDIUM",
        "crack_pattern": "Vết nứt dọc theo thanh thép, bê tông bong tróc, gỉ chảy",
        "causes": ["Lớp bảo vệ mỏng", "Nứt cho nước thấm", "Môi trường xâm thực"],
        "back_calc_method": "Đo giảm đường kính thép → tính lại A_s hiệu quả",
        "remedy": ["Sửa chữa bê tông", "Bổ sung lớp bảo vệ", "Thay thép bị gỉ nặng"],
        "keywords": ["gỉ", "ăn mòn", "corrosion", "rust", "oxy hóa"]
    },
    {
        "id": "FM-08", "name": "Foundation Settlement (Lún nền)",
        "element": "Móng / Nền", "severity": "HIGH",
        "crack_pattern": "Vết nứt xiên từ góc cửa lên tường, nghiêng công trình",
        "causes": ["Địa chất yếu", "Tải trọng vượt sức chịu tải nền", "Mực nước ngầm thay đổi"],
        "back_calc_method": "Đo chênh cao độ → tính lún differential → kiểm tra TCVN 9362:2012",
        "remedy": ["Gia cường nền (cọc, giếng cát)", "Phân bố lại tải", "Xi măng hóa nền"],
        "keywords": ["lún", "lún không đều", "settlement", "differential", "nền"]
    },
    {
        "id": "FM-09", "name": "Fatigue Failure (Phá hoại mỏi)",
        "element": "Kết cấu thép / Cầu", "severity": "HIGH",
        "crack_pattern": "Vết nứt từ điểm tập trung ứng suất, lan dần, rãnh mỏi",
        "causes": ["Tải trọng lặp nhiều chu kỳ", "Ứng suất tập trung", "Hàn kém"],
        "back_calc_method": "Kiểm tra S-N curve theo TCVN 5575:2024 §10, đếm chu kỳ",
        "remedy": ["Tăng chiều dày bản mã", "Sửa mối hàn", "Giảm tải trọng lặp"],
        "keywords": ["mỏi", "lặp", "fatigue", "cyclic", "nứt lan"]
    },
    {
        "id": "FM-10", "name": "Torsional Failure (Phá hoại xoắn)",
        "element": "Dầm BTCT", "severity": "HIGH",
        "crack_pattern": "Vết nứt xoắn ốc bao quanh dầm, 45° so với trục",
        "causes": ["Mô men xoắn không được tính", "Tải trọng lệch tâm nặng", "Thiếu cốt đai xoắn"],
        "back_calc_method": "Đo vết nứt xoắn → tính T thực tế → so sánh T_Rd",
        "remedy": ["Bổ sung cốt đai xoắn", "Tăng tiết diện", "Phân bố lại tải"],
        "keywords": ["xoắn", "torsional", "xoắn ốc", "twist"]
    },
    {
        "id": "FM-11", "name": "Bearing Failure (Phá hoại móng nông)",
        "element": "Móng đơn / Móng băng", "severity": "CRITICAL",
        "crack_pattern": "Móng trồi lên, bê tông nứt vỡ, công trình nghiêng",
        "causes": ["Sức chịu tải đất nền vượt quá", "Mực nước ngầm tăng", "Đất yếu không được xử lý"],
        "back_calc_method": "Lấy mẫu đất → thí nghiệm → tính R đất thực tế vs thiết kế",
        "remedy": ["Gia cường nền bằng cọc", "Tăng diện tích móng", "Xử lý nền đất"],
        "keywords": ["móng", "nền", "bearing", "trồi", "sức chịu tải"]
    },
    {
        "id": "FM-12", "name": "Lateral Torsional Buckling (LTB)",
        "element": "Dầm thép", "severity": "HIGH",
        "crack_pattern": "Dầm thép vặn xoắn ngang, mất ổn định tổng thể",
        "causes": ["Độ mảnh lớn", "Không đủ giằng bên", "Tải trọng ngang lệch trục"],
        "back_calc_method": "Tính M_cr theo TCVN 5575:2024 → kiểm tra λ_LT",
        "remedy": ["Thêm giằng bên", "Tăng tiết diện", "Giảm nhịp"],
        "keywords": ["LTB", "xoắn ngang", "mất ổn định", "lateral", "buckling"]
    },
    {
        "id": "FM-13", "name": "Connection Failure (Phá hoại liên kết)",
        "element": "Kết cấu thép", "severity": "HIGH",
        "crack_pattern": "Bu lông đứt, mối hàn nứt, bản mã biến dạng",
        "causes": ["Tải trọng vượt thiết kế", "Chất lượng hàn kém", "Bu lông không đủ cấp"],
        "back_calc_method": "Kiểm tra từng bulông/hàn theo TCVN 5575:2024 §7",
        "remedy": ["Thay bu lông cấp cao hơn", "Hàn lại mối hàn", "Tăng bản mã"],
        "keywords": ["liên kết", "bu lông", "hàn", "connection", "bolt", "weld"]
    },
    {
        "id": "FM-14", "name": "Creep & Shrinkage Cracking",
        "element": "Sàn / Tường BTCT", "severity": "LOW",
        "crack_pattern": "Vết nứt mạng nhện trên bề mặt, không theo hướng cụ thể",
        "causes": ["Co ngót dẻo", "Tỷ lệ nước/xi măng cao", "Bảo dưỡng kém"],
        "back_calc_method": "Quan sát + đo bề rộng → xác định loại co ngót",
        "remedy": ["Phun vữa bảo vệ", "Dán lưới sợi", "Cải thiện bảo dưỡng"],
        "keywords": ["co ngót", "creep", "shrinkage", "mạng nhện", "bề mặt"]
    },
    {
        "id": "FM-15", "name": "Fire Damage (Hư hại do cháy)",
        "element": "Toàn bộ kết cấu", "severity": "CRITICAL",
        "crack_pattern": "Bê tông bong tróc, đổi màu (hồng = ~300°C, trắng = ~600°C), thép yếu",
        "causes": ["Cháy công trình", "Nhiệt độ cao kéo dài"],
        "back_calc_method": "Đo cường độ còn lại sau cháy → giảm E, f_y theo TCVN 5574:2018",
        "remedy": ["Đánh giá cường độ còn lại → gia cường hoặc thay thế"],
        "keywords": ["cháy", "lửa", "fire", "nhiệt", "bong tróc"]
    },
]


# ─── Search engine ────────────────────────────────────────────────────────────

def search_fm(keyword: str, severity: str = None, element: str = None) -> list:
    kw_lower = keyword.lower()
    results = []
    for fm in FAILURE_MODES:
        score = 0
        matched_keywords = []
        for kw in fm.get("keywords", []):
            if kw_lower in kw.lower():
                score += 1
                matched_keywords.append(kw)

        if score > 0:
            fm_result = {**fm, "matched_keywords": matched_keywords, "match_score": score}
            if severity and fm["severity"] != severity.upper():
                continue
            if element and element.lower() not in fm["element"].lower():
                continue
            results.append(fm_result)

    results.sort(key=lambda x: x["match_score"], reverse=True)
    return results


def format_fm(fm: dict) -> str:
    lines = []
    sev_icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(fm["severity"], "")
    lines.append(f"\n{'─'*60}")
    lines.append(f"  {fm['id']}: {fm['name']} {sev_icon} [{fm['severity']}]")
    lines.append(f"{'─'*60}")
    lines.append(f"  Cấu kiện  : {fm['element']}")
    lines.append(f"  Vết nứt   : {fm['crack_pattern']}")
    lines.append(f"  Nguyên nhân: {', '.join(fm['causes'])}")
    lines.append(f"  Back-calc  : {fm['back_calc_method']}")
    lines.append(f"  Xử lý     : {', '.join(fm['remedy'])}")
    lines.append(f"  Từ khóa    : {', '.join(fm['matched_keywords'])} (score={fm['match_score']})")
    return "\n".join(lines)


def list_all():
    lines = ["\nTẤT CẢ FAILURE MODES:"]
    for fm in FAILURE_MODES:
        sev_icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(fm["severity"], "")
        lines.append(f"  {fm['id']} {sev_icon} [{fm['severity']:8}] — {fm['name']}")
        lines.append(f"    Vết nứt: {fm['crack_pattern'][:60]}...")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Tìm kiếm Failure Mode Database")
    parser.add_argument("--keyword", type=str, help="Từ khóa tìm kiếm (tiếng Việt/Anh)")
    parser.add_argument("--severity", type=str, choices=["CRITICAL","HIGH","MEDIUM","LOW"],
                        help="Lọc theo mức nguy hiểm")
    parser.add_argument("--element", type=str, help="Lọc theo cấu kiện (dầm, cột, sàn, móng...)")
    parser.add_argument("--list-all", action="store_true", help="Liệt kê tất cả")
    parser.add_argument("--json", action="store_true", help="Xuất JSON thay vì text")
    args = parser.parse_args()

    if args.list_all:
        output = list_all()
        if args.json:
            print(json.dumps(FAILURE_MODES, ensure_ascii=False, indent=2))
        else:
            print(output)
        return

    if not args.keyword:
        print("[E001] Cần --keyword hoặc --list-all", file=sys.stderr)
        sys.exit(1)

    results = search_fm(args.keyword, args.severity, args.element)

    if not results:
        print(f"[W001] Không tìm thấy Failure Mode phù hợp với: '{args.keyword}'", file=sys.stderr)
        print("Gợi ý: Thử từ khóa khác như 'uốn', 'cắt', 'punching', 'lún', 'LTB'...")
        sys.exit(1)

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print(f"\n🔍 Tìm thấy {len(results)} kết quả cho: '{args.keyword}'")
        for fm in results:
            print(format_fm(fm))


if __name__ == "__main__":
    main()
