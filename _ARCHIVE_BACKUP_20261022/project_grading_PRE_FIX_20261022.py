import sys
import argparse
import json

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

GRADE_RANK = {"Cấp IV": 1, "Cấp III": 2, "Cấp II": 3, "Cấp I": 4, "Cấp Đặc biệt": 5}
RANK_TO_GRADE = {v: k for k, v in GRADE_RANK.items()}


def determine_grade(
    building_type="civil",
    height=0.0,
    stories=1,
    gfa=0.0,
    span=0.0,
    underground_depth=0.0,
    underground_stories=0,
    capacity=0,
    commercial_area=0.0,
    is_iconic=False,
):
    """
    Xác định Cấp công trình (Quản lý XD) theo Bảng 2 Phụ lục II Thông tư 34/2026/TT-BXD
    (hiệu lực từ 01/07/2026, đối chiếu chuyển tiếp Thông tư 06/2021/TT-BXD)
    và Phân cấp phục vụ thiết kế (Cấp hậu quả C1-C3, Thời hạn sử dụng theo thiết kế)
    theo QCVN 03:2022/BXD & TCVN 2737:2023 (Bảng H.1).
    """
    criteria_grades = {}
    reasons = []

    if building_type == "civil":
        # 1. Tiêu chí a) Chiều cao (m) - Mục 2.1.1 Bảng 2 Phụ lục II
        if height > 200:
            g_h = "Cấp Đặc biệt"
            reasons.append(f"Chiều cao H = {height}m (> 200m) -> Cấp Đặc biệt (Mục 2.1.1.a Bảng 2 PL II)")
        elif 75 < height <= 200:
            g_h = "Cấp I"
            reasons.append(f"Chiều cao H = {height}m (> 75m ÷ 200m) -> Cấp I (Mục 2.1.1.a Bảng 2 PL II)")
        elif 28 < height <= 75:
            g_h = "Cấp II"
            reasons.append(f"Chiều cao H = {height}m (> 28m ÷ 75m) -> Cấp II (Mục 2.1.1.a Bảng 2 PL II)")
        elif 6 < height <= 28:
            g_h = "Cấp III"
            reasons.append(f"Chiều cao H = {height}m (> 6m ÷ 28m) -> Cấp III (Mục 2.1.1.a Bảng 2 PL II)")
        else:
            g_h = "Cấp IV"
            reasons.append(f"Chiều cao H = {height}m (<= 6m) -> Cấp IV (Mục 2.1.1.a Bảng 2 PL II)")
        criteria_grades["height"] = g_h

        # 2. Tiêu chí b) Số tầng cao - Mục 2.1.1 Bảng 2 Phụ lục II
        if stories > 50:
            g_s = "Cấp Đặc biệt"
            reasons.append(f"Số tầng cao = {stories} tầng (> 50 tầng) -> Cấp Đặc biệt (Mục 2.1.1.b Bảng 2 PL II)")
        elif 25 <= stories <= 50:
            g_s = "Cấp I"
            reasons.append(f"Số tầng cao = {stories} tầng (25 ÷ 50 tầng) -> Cấp I (Mục 2.1.1.b Bảng 2 PL II)")
        elif 8 <= stories <= 24:
            g_s = "Cấp II"
            reasons.append(f"Số tầng cao = {stories} tầng (8 ÷ 24 tầng) -> Cấp II (Mục 2.1.1.b Bảng 2 PL II)")
        elif 2 <= stories <= 7:
            g_s = "Cấp III"
            reasons.append(f"Số tầng cao = {stories} tầng (2 ÷ 7 tầng) -> Cấp III (Mục 2.1.1.b Bảng 2 PL II)")
        else:
            g_s = "Cấp IV"
            reasons.append(f"Số tầng cao = {stories} tầng (1 tầng) -> Cấp IV (Mục 2.1.1.b Bảng 2 PL II)")
        criteria_grades["stories"] = g_s

        # 3. Tiêu chí c) Tổng diện tích sàn GFA (m2) - Mục 2.1.1 Bảng 2 Phụ lục II
        if gfa > 30000:
            g_gfa = "Cấp I"
            reasons.append(f"Tổng diện tích sàn GFA = {gfa:,.2f} m² (> 30,000 m²) -> Cấp I (Mục 2.1.1.c Bảng 2 PL II)")
        elif 10000 < gfa <= 30000:
            g_gfa = "Cấp II"
            reasons.append(f"Tổng diện tích sàn GFA = {gfa:,.2f} m² (> 10,000 ÷ 30,000 m²) -> Cấp II (Mục 2.1.1.c Bảng 2 PL II)")
        elif 1000 <= gfa <= 10000:
            g_gfa = "Cấp III"
            reasons.append(f"Tổng diện tích sàn GFA = {gfa:,.2f} m² (1,000 ÷ 10,000 m²) -> Cấp III (Mục 2.1.1.c Bảng 2 PL II)")
        elif gfa > 0:
            g_gfa = "Cấp IV"
            reasons.append(f"Tổng diện tích sàn GFA = {gfa:,.2f} m² (< 1,000 m²) -> Cấp IV (Mục 2.1.1.c Bảng 2 PL II)")
        else:
            g_gfa = "Cấp IV"
        criteria_grades["gfa"] = g_gfa

        # 4. Tiêu chí d) Nhịp kết cấu lớn nhất (m) - Mục 2.1.1 Bảng 2 Phụ lục II
        if span > 200:
            g_sp = "Cấp Đặc biệt"
            reasons.append(f"Nhịp kết cấu lớn nhất = {span}m (> 200m) -> Cấp Đặc biệt (Mục 2.1.1.d Bảng 2 PL II)")
        elif 100 <= span <= 200:
            g_sp = "Cấp I"
            reasons.append(f"Nhịp kết cấu lớn nhất = {span}m (100 ÷ 200m) -> Cấp I (Mục 2.1.1.d Bảng 2 PL II)")
        elif 50 <= span < 100:
            g_sp = "Cấp II"
            reasons.append(f"Nhịp kết cấu lớn nhất = {span}m (50 ÷ <100m) -> Cấp II (Mục 2.1.1.d Bảng 2 PL II)")
        elif 15 <= span < 50:
            g_sp = "Cấp III"
            reasons.append(f"Nhịp kết cấu lớn nhất = {span}m (15 ÷ <50m) -> Cấp III (Mục 2.1.1.d Bảng 2 PL II)")
        else:
            g_sp = "Cấp IV"
        criteria_grades["span"] = g_sp

        # 5. Tiêu chí đ) Độ sâu ngầm (m) (tính đến mặt trên sàn tầng hầm sâu nhất) - Mục 2.1.1 Bảng 2 Phụ lục II
        if underground_depth > 18:
            g_ud = "Cấp I"
            reasons.append(f"Độ sâu ngầm = {underground_depth}m (> 18m) -> Cấp I (Mục 2.1.1.đ Bảng 2 PL II)")
        elif 6 <= underground_depth <= 18:
            g_ud = "Cấp II"
            reasons.append(f"Độ sâu ngầm = {underground_depth}m (6 ÷ 18m) -> Cấp II (Mục 2.1.1.đ Bảng 2 PL II)")
        elif underground_depth > 0:
            g_ud = "Cấp III"
            reasons.append(f"Độ sâu ngầm = {underground_depth}m (< 6m) -> Cấp III (Mục 2.1.1.đ Bảng 2 PL II)")
        else:
            g_ud = "Cấp IV"
        criteria_grades["underground_depth"] = g_ud

        # 6. Tiêu chí e) Số tầng ngầm - Mục 2.1.1 Bảng 2 Phụ lục II
        if underground_stories >= 5:
            g_us = "Cấp I"
            reasons.append(f"Số tầng ngầm = {underground_stories} (≥ 5 tầng) -> Cấp I (Mục 2.1.1.e Bảng 2 PL II)")
        elif 2 <= underground_stories <= 4:
            g_us = "Cấp II"
            reasons.append(f"Số tầng ngầm = {underground_stories} (2 ÷ 4 tầng) -> Cấp II (Mục 2.1.1.e Bảng 2 PL II)")
        elif underground_stories == 1:
            g_us = "Cấp III"
            reasons.append(f"Số tầng ngầm = 1 tầng -> Cấp III (Mục 2.1.1.e Bảng 2 PL II)")
        else:
            g_us = "Cấp IV"
        criteria_grades["underground_stories"] = g_us

        max_rank = max(GRADE_RANK[g] for g in criteria_grades.values())
        grade = RANK_TO_GRADE[max_rank]

    elif building_type == "marine":
        if capacity > 1000:
            grade = "Cấp I"
            reasons.append("Sức chứa > 1000 người")
        elif 500 < capacity <= 1000:
            grade = "Cấp II"
            reasons.append("Sức chứa 500 - 1000 người")
        elif 100 <= capacity <= 500:
            grade = "Cấp III"
            reasons.append("Sức chứa 100 - 500 người")
        else:
            grade = "Cấp IV"
            reasons.append("Sức chứa < 100 người")
    else:
        grade = "Cấp IV"

    # Phân cấp phục vụ thiết kế theo QCVN 03:2022/BXD & TCVN 2737:2023
    if (
        height > 75
        or span >= 100
        or underground_depth >= 18
        or commercial_area > 30000
        or gfa > 30000
        or capacity > 1200
        or grade in ["Cấp Đặc biệt", "Cấp I"]
    ):
        consequence_class = "C3"
        gamma_n = 1.15
        consequence_ basis = "Mục 2.1 & Phụ lục A QCVN 03:2022/BXD; Bảng H.1 Phụ lục H TCVN 2737:2023"
    elif grade in ["Cấp II", "Cấp III"]:
        consequence_class = "C2"
        gamma_n = 1.00
        consequence_basis = "Mục 2.1 & Phụ lục A QCVN 03:2022/BXD; Bảng H.1 Phụ lục H TCVN 2737:2023"
    else:
        consequence_class = "C1"
        gamma_n = 0.87
        consequence_basis = "Mục 2.1 & Phụ lục A QCVN 03:2022/BXD; Bảng H.1 Phụ lục H TCVN 2737:2023"

    if is_iconic:
        design_working_life = "Mức 4: Không nhỏ hơn 100 năm (≥ 100 năm — Công trình độc đáo/biểu tượng theo Bảng 1 Mục 2.2.2 QCVN 03:2022/BXD)"
    else:
        design_working_life = "Mức 3: Không nhỏ hơn 50 năm (≥ 50 năm — Công trình dân dụng/công nghiệp thông thường theo Bảng 1 Mục 2.2.2 QCVN 03:2022/BXD; có thể nâng lên ≥ 100 năm nếu Nhiệm vụ thiết kế của CĐT yêu cầu)"

    return {
        "Project_Grade": grade,
        "Criteria_Breakdown": criteria_grades,
        "Determining_Factors": reasons,
        "Legal_Basis_Management": "Bảng 2 Phụ lục II Thông tư 34/2026/TT-BXD (hiệu lực 01/07/2026) & Thông tư 06/2021/TT-BXD",
        "Consequence_Class_QCVN03": consequence_class,
        "Importance_Factor_gamma_n": gamma_n,
        "Consequence_Class_Basis": consequence_basis,
        "Design_Working_Life_QCVN03": design_working_life,
        "Design_Steps_Required": 3 if grade in ["Cấp Đặc biệt", "Cấp I"] else (2 if grade in ["Cấp II", "Cấp III"] else 1),
        "Appraisal_Authority": "Cơ quan chuyên môn về xây dựng thuộc Bộ Xây dựng" if grade in ["Cấp Đặc biệt", "Cấp I"] else "Sở Xây dựng (Tỉnh/Thành phố)",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Xác định Cấp công trình theo TT 34/2026/TT-BXD (và TT 06/2021/TT-BXD) kèm Cấp hậu quả & Tuổi thọ thiết kế theo QCVN 03:2022/BXD"
    )
    parser.add_argument("--type", choices=["civil", "marine"], default="civil", help="Loại công trình (civil/marine)")
    parser.add_argument("--height", type=float, default=0.0, help="Chiều cao công trình (m)")
    parser.add_argument("--stories", type=int, default=1, help="Số tầng cao (trên mặt đất)")
    parser.add_argument("--gfa", type=float, default=0.0, help="Tổng diện tích sàn GFA kể cả hầm (m²)")
    parser.add_argument("--span", type=float, default=0.0, help="Nhịp kết cấu lớn nhất (m)")
    parser.add_argument("--underground_depth", type=float, default=0.0, help="Độ sâu ngầm tính tới mặt trên sàn hầm sâu nhất (m)")
    parser.add_argument("--underground_stories", type=int, default=0, help="Số tầng ngầm")
    parser.add_argument("--capacity", type=int, default=0, help="Sức chứa (người)")
    parser.add_argument("--commercial_area", type=float, default=0.0, help="Tổng diện tích sàn kinh doanh thương mại (m²)")
    parser.add_argument("--iconic", action="store_true", help="Công trình có kiến trúc độc đáo / biểu tượng quốc gia (Mức 4 >= 100 năm)")

    args = parser.parse_args()

    result = determine_grade(
        building_type=args.type,
        height=args.height,
        stories=args.stories,
        gfa=args.gfa,
        span=args.span,
        underground_depth=args.underground_depth,
        underground_stories=args.underground_stories,
        capacity=args.capacity,
        commercial_area=args.commercial_area,
        is_iconic=args.iconic,
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))
