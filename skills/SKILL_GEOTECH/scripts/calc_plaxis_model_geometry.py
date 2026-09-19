"""
MODULE 16: calc_plaxis_model_geometry.py
SKILL_GEOTECH v2.5.0 -- Urban Excavation Upgrade
Xác định kích thước mô hình (Model Dimensions) tiêu chuẩn cho Plaxis 2D/3D.
Tiêu chuẩn: Plaxis Reference Manual / CIRIA C760
Usage:
  python calc_plaxis_model_geometry.py --H 3.85 --W 7.1 --L_wall 6.0
"""
import sys, json, math, argparse

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def calc_plaxis_model_dimensions(H_exc, W_exc, L_wall, hard_stratum_depth=None):
    logs = []
    
    # 1. Kích thước theo phương ngang (X-axis)
    # Ranh giới ngang (lateral boundary) phải đủ xa để chuyển vị ngang tại đó xấp xỉ 0.
    # Plaxis khuyến cáo: khoảng cách từ tường chắn đến biên ngang = 3H đến 4H (H: chiều sâu hố đào)
    L_lateral = max(3.0 * H_exc, 20.0) # Tối thiểu 20m hoặc 3H
    
    Total_Width = L_lateral + W_exc + L_lateral
    
    logs.append({
        "step": "Xác định biên ngang (X-axis)",
        "formula": "L_lateral = max(3 * H_exc, 20.0)",
        "value": f"L_lateral = max(3 * {H_exc}, 20.0) = {L_lateral:.1f} m",
        "source": "Plaxis Reference Manual - Excavation Guidelines"
    })
    
    # 2. Kích thước theo phương đứng (Y-axis)
    # Biên dưới (bottom boundary) phải đủ sâu để không ảnh hưởng đến chuyển vị dọc và Base Heave.
    # Khuyến cáo: Sâu hơn mũi tường chắn ít nhất 1.5H đến 2.0H, HOẶC đặt tại lớp đất cứng (hard stratum).
    
    D_bottom_below_tip = max(1.5 * H_exc, 10.0) # Sâu hơn mũi cừ ít nhất 1.5H hoặc 10m
    Total_Depth_from_surface = L_wall + D_bottom_below_tip
    
    if hard_stratum_depth and hard_stratum_depth > L_wall:
        # Nếu có lớp đất cứng ở nông hơn độ sâu tính toán
        Final_Depth = min(Total_Depth_from_surface, hard_stratum_depth)
        logs.append({
            "step": "Xác định biên đứng (Y-axis)",
            "note": "Giới hạn bởi lớp đất cứng",
            "value": f"Y_min = -{Final_Depth:.1f} m (Tại lớp đất cứng)"
        })
    else:
        Final_Depth = Total_Depth_from_surface
        logs.append({
            "step": "Xác định biên đứng (Y-axis)",
            "formula": "Depth = L_wall + max(1.5 * H_exc, 10.0)",
            "value": f"Depth = {L_wall} + max(1.5 * {H_exc}, 10.0) = {Final_Depth:.1f} m",
            "source": "CIRIA C760 / Plaxis Manual"
        })
        
    # Tạo toạ độ bounding box (Giả sử MĐTN tại Y = 0, tâm hố đào tại X = 0)
    X_min = - (W_exc / 2 + L_lateral)
    X_max = (W_exc / 2 + L_lateral)
    Y_max = 0.0
    Y_min = - Final_Depth
        
    return {
        "Standard_Method": "Plaxis Reference Manual / CIRIA C760",
        "Input": {
            "H_excavation_m": H_exc,
            "W_excavation_m": W_exc,
            "L_wall_m": L_wall
        },
        "Recommended_Model_Dimensions": {
            "Total_Width_m": round(Total_Width, 1),
            "Total_Depth_m": round(Final_Depth, 1),
            "Lateral_Distance_From_Wall_m": round(L_lateral, 1),
            "Depth_Below_Wall_Tip_m": round(Final_Depth - L_wall, 1)
        },
        "Plaxis_Bounding_Box": {
            "X_min": round(X_min, 1),
            "X_max": round(X_max, 1),
            "Y_min": round(Y_min, 1),
            "Y_max": round(Y_max, 1)
        },
        "Calculation_Logs": logs
    }

def main():
    p = argparse.ArgumentParser(description="MODULE 16: Plaxis Model Geometry")
    p.add_argument("--H", type=float, required=True, help="Chiều sâu hố đào (m)")
    p.add_argument("--W", type=float, required=True, help="Bề rộng hố đào (m)")
    p.add_argument("--L_wall", type=float, required=True, help="Chiều dài tường chắn/cừ (m)")
    p.add_argument("--hard_stratum", type=float, default=None, help="Độ sâu gặp lớp đất đá cứng (m)")
    
    args = p.parse_args()
    result = calc_plaxis_model_dimensions(args.H, args.W, args.L_wall, args.hard_stratum)
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
