import sys
import argparse
import json

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def determine_grade(building_type, height, stories, span, capacity):
    """
    Simplified project grading logic based on TT 06/2021/TT-BXD for Civil/Industrial buildings.
    """
    grade = "Cấp IV"
    reasons = []

    if building_type == "civil":
        if stories > 50 or height > 200:
            grade = "Cấp Đặc biệt"
            reasons.append(f"Số tầng {stories} > 50 hoặc Chiều cao {height} > 200m")
        elif (25 <= stories <= 50) or (75 < height <= 200) or span >= 100:
            grade = "Cấp I"
            reasons.append(f"Số tầng {stories} (25-50) hoặc Chiều cao {height} (75-200) hoặc Nhịp {span} >= 100")
        elif (8 <= stories <= 24) or (28 < height <= 75) or (50 <= span < 100):
            grade = "Cấp II"
            reasons.append(f"Số tầng {stories} (8-24) hoặc Chiều cao {height} (28-75) hoặc Nhịp {span} (50-100)")
        elif (3 <= stories <= 7) or (6 < height <= 28) or (15 <= span < 50):
            grade = "Cấp III"
            reasons.append(f"Số tầng {stories} (3-7) hoặc Chiều cao {height} (6-28) hoặc Nhịp {span} (15-50)")
        else:
            grade = "Cấp IV"
            reasons.append(f"Số tầng < 3, Chiều cao <= 6, Nhịp < 15")
    
    # Adding logic for water/marine structures (e.g. floating houses)
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

    return {
        "Project_Grade": grade,
        "Determining_Factors": reasons,
        "Design_Steps_Required": 3 if grade in ["Cấp Đặc biệt", "Cấp I"] else (2 if grade in ["Cấp II", "Cấp III"] else 1),
        "Appraisal_Authority": "Bộ Xây dựng" if grade in ["Cấp Đặc biệt", "Cấp I"] else "Sở Xây dựng (Tỉnh/Thành phố)"
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Xác định Cấp công trình theo TT 06/2021/TT-BXD")
    parser.add_argument("--type", choices=["civil", "marine"], default="civil", help="Loại công trình (civil/marine)")
    parser.add_argument("--height", type=float, default=0, help="Chiều cao công trình (m)")
    parser.add_argument("--stories", type=int, default=1, help="Số tầng")
    parser.add_argument("--span", type=float, default=0, help="Nhịp kết cấu lớn nhất (m)")
    parser.add_argument("--capacity", type=int, default=0, help="Sức chứa (người)")

    args = parser.parse_args()

    result = determine_grade(args.type, args.height, args.stories, args.span, args.capacity)
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
