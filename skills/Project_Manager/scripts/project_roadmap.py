import sys
import argparse

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def generate_roadmap(project_type, grade):
    """
    Tạo mã Mermaid Flowchart cho Lộ trình Dự án Xây dựng theo Luật XD Việt Nam.
    """
    # Base Nodes
    nodes = {
        "A1": "Khảo sát & Lập QH 1/500<br><i>(Luật QHĐT 2009)</i>",
        "A2": "Chấp thuận Chủ trương Đầu tư<br><i>(Luật Đầu tư 2020)</i>",
        "A3": "Phê duyệt Quy hoạch 1/500",
        
        "B1": "Lập Báo cáo ĐTM<br><i>(Luật BVMT 2020)</i>",
        "B2": "Khảo sát Xây dựng<br><i>(NĐ 15/2021)</i>",
        "B3": "Lập F/S & TKCS<br><i>(NĐ 15/2021)</i>",
        
        "C1": "Thẩm định ĐTM<br><i>(Sở/Bộ TNMT)</i>",
        "C2": "Thỏa thuận PCCC<br><i>(NĐ 136/2020)</i>",
        "C3": "Thẩm định F/S & TKCS<br><i>(Sở/Bộ Xây dựng)</i>",
        
        "D1": "Phê duyệt Dự án Đầu tư",
        "D2": "Thiết kế BVTC & Thẩm tra<br><i>(Điều 82, 83 Luật XD)</i>",
        
        "E1": "Cấp Giấy phép Xây dựng<br><i>(Điều 89 Luật XD)</i>",
        "E2": "Lựa chọn Nhà thầu<br><i>(Luật Đấu thầu 2023)</i>",
        "E3": "Thi công Xây dựng<br><i>(NĐ 06/2021)</i>",
        
        "F1": "Nghiệm thu hoàn thành<br><i>(Điều 23 NĐ 06/2021)</i>",
        "F2": "Kiểm tra công tác nghiệm thu<br><i>(Cơ quan NN - Điều 24 NĐ 06/2021)</i>",
        "F3": "Bàn giao & Đưa vào sử dụng",
    }
    
    # Adjust appraisal authority based on grade
    if grade in ["Đặc biệt", "I"]:
        nodes["C3"] = "Thẩm định F/S & TKCS<br><i>(Bộ Xây dựng)</i>"
        nodes["F2"] = "Kiểm tra công tác nghiệm thu<br><i>(Bộ Xây dựng)</i>"
    elif grade in ["II", "III"]:
        nodes["C3"] = "Thẩm định F/S & TKCS<br><i>(Sở Xây dựng)</i>"
        nodes["F2"] = "Kiểm tra công tác nghiệm thu<br><i>(Sở Xây dựng)</i>"

    # Diagram definition
    mermaid_code = "```mermaid\ngraph TD\n"
    
    # Define Subgraphs
    mermaid_code += "    subgraph Phase1 [Giai đoạn 1: Chuẩn bị Dự án]\n"
    mermaid_code += f"        A1[{nodes['A1']}] --> A2[{nodes['A2']}]\n"
    mermaid_code += f"        A2 --> A3[{nodes['A3']}]\n"
    mermaid_code += "    end\n\n"
    
    mermaid_code += "    subgraph Phase2 [Giai đoạn 2: Thực hiện Dự án]\n"
    mermaid_code += f"        A3 --> B2[{nodes['B2']}]\n"
    mermaid_code += f"        B2 --> B3[{nodes['B3']}]\n"
    mermaid_code += f"        B3 -.-> B1[{nodes['B1']}]\n"
    mermaid_code += f"        B1 --> C1[{nodes['C1']}]\n"
    mermaid_code += f"        B3 --> C2[{nodes['C2']}]\n"
    mermaid_code += f"        B3 --> C3[{nodes['C3']}]\n"
    mermaid_code += f"        C1 --> D1[{nodes['D1']}]\n"
    mermaid_code += f"        C2 --> D1\n"
    mermaid_code += f"        C3 --> D1\n"
    mermaid_code += f"        D1 --> D2[{nodes['D2']}]\n"
    mermaid_code += f"        D2 --> E1[{nodes['E1']}]\n"
    mermaid_code += f"        D1 --> E2[{nodes['E2']}]\n"
    mermaid_code += f"        E1 --> E3[{nodes['E3']}]\n"
    mermaid_code += f"        E2 --> E3\n"
    mermaid_code += "    end\n\n"
    
    mermaid_code += "    subgraph Phase3 [Giai đoạn 3: Kết thúc Xây dựng]\n"
    mermaid_code += f"        E3 --> F1[{nodes['F1']}]\n"
    mermaid_code += f"        F1 --> F2[{nodes['F2']}]\n"
    mermaid_code += f"        F2 --> F3[{nodes['F3']}]\n"
    mermaid_code += "    end\n\n"
    
    # Styling
    mermaid_code += "    classDef phase fill:#f9f9f9,stroke:#333,stroke-width:2px;\n"
    mermaid_code += "    classDef critical fill:#ffcccc,stroke:#ff0000,stroke-width:2px;\n"
    mermaid_code += "    class Phase1,Phase2,Phase3 phase;\n"
    mermaid_code += "    class C1,C2,C3 critical;\n"
    
    mermaid_code += "```\n"
    
    return mermaid_code

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sinh biểu đồ Lộ trình Dự án")
    parser.add_argument("--type", choices=["private", "public"], default="private", help="Loại vốn đầu tư (Tư nhân / Đầu tư công)")
    parser.add_argument("--grade", choices=["Đặc biệt", "I", "II", "III", "IV"], default="II", help="Cấp công trình")
    
    args = parser.parse_args()
    
    mermaid_str = generate_roadmap(args.type, args.grade)
    
    print(f"### Sơ đồ Lộ trình Pháp lý Dự án (Cấp {args.grade})")
    print("*(Các ô viền đỏ thể hiện các bước nằm trên đường găng - Critical Path)*")
    print(mermaid_str)
