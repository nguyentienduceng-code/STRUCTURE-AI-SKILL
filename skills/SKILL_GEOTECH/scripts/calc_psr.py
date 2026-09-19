import sys
import json
import math

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# =============================================================================
# calc_psr.py — MODULE: Hiệu ứng góc 3D (Plane Strain Ratio)
# =============================================================================
# Version: 1.0.0
# Standard_Method: Ou et al. (1996) / Finno et al. (2007)
# =============================================================================

def calculate_psr(L_m, B_m, He_m, distance_from_corner_m=None):
    """
    Tính Plane Strain Ratio (PSR) = Chuyển vị 3D / Chuyển vị 2D
    Dựa trên tỷ lệ kích thước hố đào (L/He, B/He).
    """
    # Ou et al. (1996) simplified correlation for max PSR at center
    # L: Length (cạnh dài), B: Width (cạnh ngắn), He: Chiều sâu đào
    
    L_He = L_m / He_m
    B_He = B_m / He_m
    
    # Hàm kinh nghiệm của Ou (1996) cho PSR tại giữa cạnh dài
    # Nếu L/He > 6, hệ thống đạt trạng thái 2D Plane Strain (PSR ~ 1.0)
    if L_He >= 6.0:
        psr_max = 1.0
    else:
        # Xấp xỉ đơn giản: PSR giảm khi hố đào hẹp và sâu
        # Dựa trên đồ thị Ou (1996)
        psr_max = 1.0 - math.exp(-0.5 * L_He)
        
    # Giảm thêm do bề rộng hẹp
    if B_He < 2.0:
        psr_max *= (0.7 + 0.15 * B_He)
        
    psr_max = min(1.0, max(0.4, psr_max))
    
    # Tại góc hố đào (distance = 0), PSR rất nhỏ (chỉ khoảng 0.2 - 0.4)
    if distance_from_corner_m is not None:
        # Khoảng cách chuẩn hóa
        norm_d = distance_from_corner_m / (L_m / 2.0)
        norm_d = min(1.0, max(0.0, norm_d))
        
        # Đường cong dạng parabol từ góc đến giữa
        psr_local = 0.3 + (psr_max - 0.3) * math.sin(norm_d * math.pi / 2.0)
    else:
        psr_local = psr_max
        
    return {
        "PSR_center": round(psr_max, 3),
        "PSR_local": round(psr_local, 3),
        "L_He": round(L_He, 2),
        "B_He": round(B_He, 2)
    }

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Tính Plane Strain Ratio (PSR) cho hố đào 3D")
    parser.add_argument("--L", type=float, required=True, help="Chiều dài hố đào (m)")
    parser.add_argument("--B", type=float, required=True, help="Chiều rộng hố đào (m)")
    parser.add_argument("--H", type=float, required=True, help="Chiều sâu đào (m)")
    parser.add_argument("--d", type=float, help="Khoảng cách từ góc đến mặt cắt xem xét (m)")
    args = parser.parse_args()

    result = calculate_psr(args.L, args.B, args.H, args.d)
    
    output = {
        "PSR_Analysis": result,
        "Calculation_Logs": [
            {"step": "Tính L/He và B/He", "formula": f"L/He = {result['L_He']}, B/He = {result['B_He']}"},
            {"step": "Đánh giá PSR", "status": "2D Plane Strain" if result['PSR_center'] >= 0.95 else "3D Corner Effect dominates"}
        ],
        "Standard_Method": "Ou et al. (1996) empirical charts"
    }
    
    print(json.dumps(output, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
