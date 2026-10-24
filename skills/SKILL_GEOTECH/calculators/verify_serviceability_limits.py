import sys
import json
import math

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# =============================================================================
# verify_serviceability_limits.py — MODULE: Kiểm tra Giới hạn Sử dụng (SLS)
# =============================================================================
# Version: 2.0.0
# Standard_Method: Clough & O'Rourke (1990)
# =============================================================================

def verify_deflection(max_deflection_mm, excavation_depth_m, soil_condition="stiff"):
    """
    Kiểm tra chuyển vị ngang tối đa của tường vây.
    Theo Clough & O'Rourke (1990):
    - Đất cứng/Cát: delta_max ~ 0.2% H
    - Đất mềm: delta_max ~ 0.5% - 1.0% H (Tùy thuộc độ cứng hệ giằng)
    """
    H_mm = excavation_depth_m * 1000.0
    
    # Xác định giới hạn cho phép
    if soil_condition == "stiff":
        limit_ratio = 0.002 # 0.2% H
    elif soil_condition == "medium":
        limit_ratio = 0.005 # 0.5% H
    else: # soft
        limit_ratio = 0.010 # 1.0% H
        
    allowable_deflection_mm = H_mm * limit_ratio
    
    eta = max_deflection_mm / allowable_deflection_mm
    
    # Đánh giá trạng thái
    if eta <= 0.7:
        status = "An toàn, có dư (Có thể tối ưu hệ giằng)"
        action = "Đạt"
        code = "I001"
    elif eta <= 0.9:
        status = "Đạt, thiết kế hợp lý"
        action = "Đạt"
        code = "OK"
    elif eta <= 1.0:
        status = "Đạt nhưng sát ngưỡng"
        action = "Cảnh báo lưu ý"
        code = "W001"
    else:
        status = "KHÔNG ĐẠT"
        action = "Cần tăng độ cứng tường/thêm giằng"
        code = "E003"
        
    return {
        "max_deflection_mm": max_deflection_mm,
        "allowable_deflection_mm": round(allowable_deflection_mm, 1),
        "limit_ratio": f"{limit_ratio * 100}% H",
        "eta": round(eta, 3),
        "status": status,
        "action": action,
        "code": code
    }

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Kiểm tra SLS (Clough & O'Rourke)")
    parser.add_argument("--deflection", type=float, required=True, help="Max deflection in mm")
    parser.add_argument("--depth", type=float, required=True, help="Excavation depth H in m")
    parser.add_argument("--soil", choices=["stiff", "medium", "soft"], default="stiff", help="Soil condition")
    args = parser.parse_args()

    result = verify_deflection(args.deflection, args.depth, args.soil)
    
    output = {
        "Serviceability_Check": result,
        "Standard_Method": "Clough & O'Rourke (1990)",
        "Calculation_Logs": [
            {"step": "Giới hạn chuyển vị", "formula": f"allowable = {result['limit_ratio']} × H"},
            {"step": "Tính hệ số sử dụng", "formula": "eta = max_deflection / allowable"}
        ]
    }
    
    print(json.dumps(output, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
