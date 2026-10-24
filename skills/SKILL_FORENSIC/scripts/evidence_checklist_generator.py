#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SKILL_FORENSIC Bước 1: Evidence Collection Checklist
Sinh checklist chứng cứ cần thu thập cho 1 sự cố cụ thể.

Input: Loại sự cố (flexural crack / shear failure / collapse / settlement / ...)
Output: Danh sách chứng cứ cần thu thập, kèm hướng dẫn đo đạc cụ thể
"""

import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
import sys
import json
import argparse
from datetime import datetime


EVIDENCE_CATEGORIES = {
    "general": [
        {"item": "Ảnh toàn cảnh hiện trường (4-6 góc)", "priority": "MUST"},
        {"item": "Ảnh cận cảnh vết nứt (có thước đo kèm)", "priority": "MUST"},
        {"item": "Biên bản hiện trường (có chữ ký các bên)", "priority": "MUST"},
        {"item": "Danh sách nhân chứng + lời khai", "priority": "MUST"},
        {"item": "Điều kiện thời tiết/lúc xảy ra sự cố", "priority": "MUST"},
        {"item": "Bản vẽ thiết kế gốc (BVTC hoặc shop drawing)", "priority": "MUST"},
        {"item": "Nhật ký thi công", "priority": "MUST"},
        {"item": "Hồ sơ nghiệm thu (biên bản nghiệm thu các giai đoạn)", "priority": "SHOULD"},
        {"item": "Phiếu kết quả thí nghiệm mẫu bê tông (28 ngày)", "priority": "SHOULD"},
        {"item": "Hợp đồng thi công (điều khoản bảo hành, trách nhiệm)", "priority": "NICE"}
    ],
    "flexural_crack": [
        {"item": "Bề rộng vết nứt đo bằng thước kẹp (đơn vị mm, đo 3 vị trí)", "priority": "MUST"},
        {"item": "Chiều dài vết nứt (mm)", "priority": "MUST"},
        {"item": "Hướng nứt (ngang/dọc/chéo 45°)", "priority": "MUST"},
        {"item": "Vị trí vết nứt (giữa nhịp/gối/cách gối bao nhiêu)", "priority": "MUST"},
        {"item": "Đo độ võng dầm bằng máy thủy bình (mm)", "priority": "MUST"},
        {"item": "Tải trọng thực tế đang đặt lên dầm (cân đo)", "priority": "MUST"},
        {"item": "Ảnh chụp vết nứt ở các mặt (đáy, hông, mặt trên)", "priority": "SHOULD"}
    ],
    "shear_failure": [
        {"item": "Góc nghiêng vết nứt (đo bằng thước đo góc)", "priority": "MUST"},
        {"item": "Vị trí vết nứt (cách gối bao nhiêu, thường 1-3h)", "priority": "MUST"},
        {"item": "Bề rộng vết nứt (mm)", "priority": "MUST"},
        {"item": "Ảnh cận cảnh cốt đai (có bị bung không)", "priority": "MUST"},
        {"item": "Kiểm tra cốt đai bằng máy dò kim loại", "priority": "SHOULD"}
    ],
    "punching_shear": [
        {"item": "Hình dạng vết nứt (xuyên qua bản hay không)", "priority": "MUST"},
        {"item": "Vết nứt có dạng hình nón 45° quanh cột", "priority": "MUST"},
        {"item": "Chiều dày bản đo thực tế", "priority": "MUST"},
        {"item": "Tải tập trung đặt lên sàn (xe, thiết bị, hàng hóa)", "priority": "MUST"}
    ],
    "settlement": [
        {"item": "Sơ đồ vết nứt tường (đo từng vết, khoảng cách, bề rộng)", "priority": "MUST"},
        {"item": "Mức độ lún (đo bằng máy thủy bình các vị trí khác nhau)", "priority": "MUST"},
        {"item": "Lịch sử lún (nếu có quan trắc)", "priority": "MUST"},
        {"item": "Báo cáo khảo sát địa chất", "priority": "MUST"},
        {"item": "Mực nước ngầm hiện tại", "priority": "SHOULD"},
        {"item": "Tình trạng hệ thống thoát nước", "priority": "SHOULD"}
    ],
    "collapse": [
        {"item": "Hiện trường đổ nát (KHÔNG dọn dẹp trước khi khảo sát xong)", "priority": "MUST"},
        {"item": "Vị trí các mảnh vỡ (chụp từ trên xuống)", "priority": "MUST"},
        {"item": "Phân tích thứ tự sập (mảnh nào rơi trước/sau)", "priority": "MUST"},
        {"item": "Tải trọng đặt lên trước lúc sập (cân đo)", "priority": "MUST"},
        {"item": "Quan trắc nhân chứng về thứ tự sập", "priority": "MUST"},
        {"item": "Lấy mẫu bê tông tại vị trí nứt (core test)", "priority": "MUST"},
        {"item": "Lấy mẫu thép (kiểm tra cường độ, hàm lượng C, Mn)", "priority": "MUST"}
    ],
    "corrosion": [
        {"item": "Bề mặt bê tông bong tróc (đo % diện tích)", "priority": "MUST"},
        {"item": "Vết rỉ thép trên bề mặt", "priority": "MUST"},
        {"item": "Đo đường kính cốt thép còn lại (so với thiết kế)", "priority": "MUST"},
        {"item": "Đo lớp bê tông bảo vệ (cover)", "priority": "MUST"},
        {"item": "Đo điện thế cốt thép (half-cell potential)", "priority": "SHOULD"},
        {"item": "Lấy mẫu bê tông để test chloride/carbonation", "priority": "SHOULD"}
    ]
}


def generate_checklist(incident_type, project_name=None):
    """
    Sinh checklist cho 1 loại sự cố.
    """
    general = EVIDENCE_CATEGORIES.get("general", [])
    specific = EVIDENCE_CATEGORIES.get(incident_type, [])

    if not specific:
        return {
            "Status": "UNKNOWN_INCIDENT_TYPE",
            "Available_Types": list(EVIDENCE_CATEGORIES.keys()),
            "Recommendation": "Chọn incident_type từ danh sách trên"
        }

    return {
        "Checklist_ID": f"EVL-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "Generated_At": datetime.now().isoformat(),
        "Project_Name": project_name or "(Chưa cung cấp)",
        "Incident_Type": incident_type,
        "Total_Items": len(general) + len(specific),
        "Must_Collect_Count": sum(1 for i in general + specific if i["priority"] == "MUST"),
        "General_Evidence": general,
        "Specific_Evidence": specific,
        "Priority_Legend": {
            "MUST": "Bắt buộc - không có thì không thể điều tra",
            "SHOULD": "Nên có - thiếu thì giảm độ tin cậy kết luận",
            "NICE": "Nếu có thì tốt - giúp bổ trợ nhưng không bắt buộc"
        },
        "Workflow": [
            "1. Thu thập TẤT Cả MUST trước",
            "2. Chụp ảnh + đo đạc trong vòng 48h (trước khi hiện trường bị xáo trộn)",
            "3. Lưu trữ bằng chứng theo quy trình pháp lý (chain of custody)",
            "4. Có biên bản giao nhận mẫu vật với các bên liên quan"
        ],
        "Legal_Note": (
            "Mọi bằng chứng phải được lưu trữ theo quy trình pháp lý. "
            "Không tự ý thay đổi hiện trường trước khi có ý kiến của cơ quan giám định."
        )
    }


def main():
    parser = argparse.ArgumentParser(description="Evidence Checklist Generator")
    parser.add_argument("--type", required=True,
                        choices=list(EVIDENCE_CATEGORIES.keys()),
                        help="Loại sự cố")
    parser.add_argument("--project", help="Tên dự án")
    parser.add_argument("--output", help="File JSON output")

    args = parser.parse_args()

    result = generate_checklist(args.type, args.project)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
