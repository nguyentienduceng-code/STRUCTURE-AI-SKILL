#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SKILL_FORENSIC Bước 7: Remedial Solution Generator
Đề xuất giải pháp xử lý 3 cấp độ:
- Khẩn cấp (Emergency, 24h)
- Tạm thời (Temporary, 1-2 tuần)
- Vĩnh viễn (Permanent, 1-3 tháng)

Input: Failure mode + severity + member type
Output: Plan xử lý chi tiết với cost & timeline estimate
"""

import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
import sys
import json
import argparse
from datetime import datetime


REMEDIAL_LIBRARY = {
    "flexural_crack": {
        "emergency": [
            "Chống đỡ tạm dưới dầm bằng giáo PAL hoặc cây chống thép (spacing ≤1.5m)",
            "Giảm tải trọng sử dụng xuống 50% hoặc cấm sử dụng",
            "Lắp đặt thiết bị quan trắc vết nứt (demac gauge) để theo dõi 24/7"
        ],
        "temporary": [
            "Dựng dầm phụ (propost beam) bằng thép H200-H300 bên dưới dầm bị nứt",
            "Bơm keo epoxy vào vết nứt rộng >0.3mm (đóng vai kim phong ẩn)",
            "Giới hạn tải trọng sử dụng theo tính toán"
        ],
        "permanent": [
            "Dán bản thép (steel plate) dày 6-10mm vào mặt đáy dầm + bulong neo",
            "Dán FRP (Carbon Fiber Sheet) 2-3 lớp ở mặt đáy và mặt bên",
            "Tăng tiết diện dầm bằng bê tông phun + cốt thép bổ sung (jacket method)",
            "Xem xét thay thế cấu kiện nếu η > 1.5 hoặc chiều dài nứt > 70% chiều cao dầm"
        ]
    },
    "shear_crack": {
        "emergency": [
            "Chống đỡ tạm 2 phía đầu dầm (cách gối 0.5L)",
            "Cấm tải trọng động (xe, máy)",
            "Quan trắc chiều rộng vết nứt mỗi 4h"
        ],
        "temporary": [
            "Dựng thanh chống chéo (steel angle L100×100×10)",
            "Bơm keo epoxy áp lực cao",
            "Giới hạn tải trọng tĩnh tại khu vực lân cận"
        ],
        "permanent": [
            "Dán FRP chữ U quấn quanh dầm (tăng khả năng chịu cắt)",
            "Khoan cấy cốt đai bổ sung dọc theo thân dầm",
            "Bọc cốt thép + bê tông phun toàn bộ mặt bên dầm (jacket)",
            "Cân nhắc phá dỡ và thi công lại dầm mới nếu cốt đai thiếu > 30%"
        ]
    },
    "punching": {
        "emergency": [
            "Di dời tải tập trung ra xa cột (xe, thiết bị nặng)",
            "Chống đỡ tạm sàn bằng giáo ngay dưới khu vực",
            "Cấm lưu thông qua khu vực có nguy cơ"
        ],
        "temporary": [
            "Dựng cột chống tạm (telescopic prop) dưới sàn",
            "Lắp các tấm phân bố lại tải (load distribution plate)",
            "Quan trắc biến dạng sàn"
        ],
        "permanent": [
            "Dán FRP từ trên xuống (shear reinforcement) tại vùng cột",
            "Khoan cấy thanh stud vào sàn + bê tông phun tăng chiều dày",
            "Tăng cường cốt thép chống đục thủng (shear reinforcement bars)",
            "Thay thế toàn bộ tấm sàn khu vực nếu chiều dày < 70% thiết kế"
        ]
    },
    "settlement": {
        "emergency": [
            "Di dời người và tài sản ra khỏi khu vực lún",
            "Cấm xe tải nặng đi qua khu vực",
            "Lắp đặt quan trắc lún (settlement marker) ở 5-10 vị trí"
        ],
        "temporary": [
            "Đặt giáo chống dưới dầm tại các vị trí chịu lún nhiều",
            "Bơm xi măng áp lực cao vào nền dưới móng (compensation grouting)",
            "Cân nhắc giảm tải trọng tầng trên"
        ],
        "permanent": [
            "Ép cọc bổ sung (micropile) và nối với móng hiện hữu",
            "Bơm foam polyurethane hoặc xi măng vào lỗ rỗng dưới móng",
            "Tăng chiều sâu móng hoặc gia cố đất nền bằng jet grouting",
            "Xem xét kết cấu mới (cải tạo) nếu nguyên nhân là biến đổi địa chất"
        ]
    },
    "corrosion": {
        "emergency": [
            "Đánh giá tức thì khả năng chịu lực còn lại",
            "Cấm tải nặng tại khu vực ăn mòn",
            "Quan trắc bong tróc bê tông"
        ],
        "temporary": [
            "Đục bỏ lớp bê tông bong tróc, làm sạch cốt thép gỉ",
            "Sơn chống ăn mòn (epoxy coating) cho cốt thép lộ thiên",
            "Trát vữa polymer tạm thời"
        ],
        "permanent": [
            "Bọc lớp bê tông mới + cốt thép bổ sung (jacket toàn diện)",
            "Dùng bê tông cốt sợi (SFRC) thay thế phần bê tông bị ăn mòn",
            "Thay thế cốt thép mới (nếu đường kính giảm >15%)",
            "Áp dụng phương pháp cathodic protection cho công trình liên tục"
        ]
    }
}


COST_ESTIMATES = {
    # Ước tính chi phí trung bình cho mỗi phương pháp (VNĐ - dự án nhỏ 100m²)
    "chống đỡ tạm giáo PAL": {"cost_million": 25, "duration_days": 2},
    "demac gauge quan trắc": {"cost_million": 5, "duration_days": 1},
    "bơm keo epoxy": {"cost_million": 15, "duration_days": 3},
    "dán thép tấm dày 8mm": {"cost_million": 85, "duration_days": 14},
    "dán FRP carbon 2 lớp": {"cost_million": 120, "duration_days": 10},
    "BT phun jacket dầm": {"cost_million": 180, "duration_days": 28},
    "khoan cấy cốt thép": {"cost_million": 60, "duration_days": 7},
    "phá dỡ + thi công lại cấu kiện": {"cost_million": 350, "duration_days": 45},
    "ép cọc micropile bổ sung": {"cost_million": 250, "duration_days": 21},
    "bơm xi măng áp lực": {"cost_million": 90, "duration_days": 14}
}


def generate_remedial_plan(failure_mode, severity="medium", member_type="beam"):
    """
    Sinh kế hoạch xử lý 3 cấp.
    """
    if failure_mode not in REMEDIAL_LIBRARY:
        return {
            "Status": "UNKNOWN_FAILURE_MODE",
            "Available_Modes": list(REMEDIAL_LIBRARY.keys()),
            "Recommendation": f"Chọn mode từ danh sách. Hoặc dùng 'custom' và liệt kê giải pháp"
        }

    lib = REMEDIAL_LIBRARY[failure_mode]
    severity_multiplier = {
        "low": 0.6,
        "medium": 1.0,
        "high": 1.5,
        "critical": 2.0
    }
    mul = severity_multiplier.get(severity, 1.0)

    # Generate timeline estimate
    timeline = {
        "emergency": {"duration": "0-24 giờ", "phase": 1},
        "temporary": {"duration": "1-2 tuần", "phase": 2},
        "permanent": {"duration": "1-3 tháng", "phase": 3}
    }

    # Estimate total cost (rough)
    cost_estimates = []
    if severity in ("high", "critical"):
        # Estimate từ giải pháp permanent
        cost_estimates.append({
            "phase": "permanent",
            "estimated_cost_million_VND": 200 * mul,
            "estimated_duration_days": int(45 * mul)
        })
    else:
        cost_estimates.append({
            "phase": "permanent",
            "estimated_cost_million_VND": 120 * mul,
            "estimated_duration_days": int(20 * mul)
        })

    return {
        "Plan_ID": f"RSP-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "Generated_At": datetime.now().isoformat(),
        "Failure_Mode": failure_mode,
        "Severity": severity,
        "Member_Type": member_type,
        "Severity_Multiplier": mul,
        "Phase_1_Emergency": {
            "target": "Ngăn sập, bảo vệ sinh mạng",
            "deadline": "Trong 24h",
            "actions": lib.get("emergency", []),
            "responsible": "Nhà thầu thi công + Chỉ huy trưởng + Tư vấn giám sát"
        },
        "Phase_2_Temporary": {
            "target": "Duy trì sử dụng hạn chế",
            "deadline": "1-2 tuần",
            "actions": lib.get("temporary", []),
            "responsible": "Đơn vị sửa chữa + Tư vấn thiết kế"
        },
        "Phase_3_Permanent": {
            "target": "Phục hồi toàn bộ khả năng chịu lực",
            "deadline": "1-3 tháng",
            "actions": lib.get("permanent", []),
            "responsible": "Nhà thầu chuyên gia + Tư vấn thiết kế + Thẩm tra"
        },
        "Cost_Estimates": cost_estimates,
        "Pre_Actions": [
            "⚠️ Ngừng sử dụng công trình nếu severity >= high",
            "⚠️ Quan trắc 24/7 trước khi xử lý",
            "Lập biên bản sự cố có xác nhận các bên",
            "Thông báo Chủ đầu tư + Cơ quan quản lý xây dựng (nếu cần)"
        ],
        "Post_Actions": [
            "Thí nghiệm kiểm chứng sau khi xử lý (load test)",
            "Cập nhật hồ sơ hoàn công",
            "Rút kinh nghiệm và lưu vào case study"
        ],
        "Legal_Disclaimer": (
            "Phương án mang tính kỹ thuật tham khảo. Việc thiết kế sửa chữa cuối cùng "
            "phải do đơn vị có chứng chỉ hành nghề thiết kế sửa chữa, được thẩm tra. "
            "Trợ lý AI không chịu trách nhiệm pháp lý."
        )
    }


def main():
    parser = argparse.ArgumentParser(description="Remedial Solution Generator")
    parser.add_argument("--mode", required=True, help="Failure mode")
    parser.add_argument("--severity", default="medium",
                        choices=["low", "medium", "high", "critical"])
    parser.add_argument("--member", default="beam", help="Loại cấu kiện")
    parser.add_argument("--output", help="File JSON output")

    args = parser.parse_args()

    result = generate_remedial_plan(args.mode, args.severity, args.member)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
