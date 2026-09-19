import sys
import json
import math

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# =============================================================================
# calc_pile_load_test.py — MODULE: Phân tích sức chịu tải cọc từ nén tĩnh
# =============================================================================
# Version: 1.0.0
# Standard_Method: Davisson (1972), Chin-Kondner, Butler & Hoy
# =============================================================================

class PileLoadTestInterpreter:
    def __init__(self, loads_kn, settlements_mm, pile_length_m, pile_area_m2, E_pile_kpa, pile_diameter_m):
        self.loads = loads_kn
        self.settlements = settlements_mm
        self.L = pile_length_m
        self.A = pile_area_m2
        self.E = E_pile_kpa
        self.D_mm = pile_diameter_m * 1000.0

    def davisson_method(self):
        """
        Tiêu chí Davisson (1972):
        delta = PL/AE + (0.15 + D/120) inches (convert to mm)
        """
        results = []
        Qu = None
        for P, s in zip(self.loads, self.settlements):
            # Elastic compression PL/AE (m -> mm)
            elastic_mm = (P * self.L / (self.A * self.E)) * 1000.0
            # Offset in mm: (0.15 inch = 3.81 mm, D/120 inch = D(mm)/120)
            # Actually, standard formula is: delta = PL/AE + 4.0 + D/120 (in mm)
            davisson_limit = elastic_mm + 4.0 + (self.D_mm / 120.0)
            
            results.append({
                "P_kN": P,
                "s_mm": s,
                "elastic_mm": round(elastic_mm, 2),
                "davisson_limit_mm": round(davisson_limit, 2)
            })
            
            if s >= davisson_limit and Qu is None:
                Qu = P # Trị số xấp xỉ tại điểm giao
                
        return Qu, results

    def chin_kondner_method(self):
        """
        Tiêu chí Chin-Kondner (Hyperbolic):
        s/P = c1 * s + c2
        Qu = 1 / c1
        """
        # Tránh chia cho 0 ở tải trọng 0
        s_array = []
        s_over_P = []
        for P, s in zip(self.loads, self.settlements):
            if P > 0:
                s_array.append(s)
                s_over_P.append(s / P)
                
        if len(s_array) < 3: return None, "Not enough data"
        
        # Simple Linear Regression: y = c1 * x + c2
        n = len(s_array)
        sum_x = sum(s_array)
        sum_y = sum(s_over_P)
        sum_xx = sum(x*x for x in s_array)
        sum_xy = sum(x*y for x, y in zip(s_array, s_over_P))
        
        denominator = n * sum_xx - sum_x**2
        if denominator == 0: return None, "Math error"
        
        c1 = (n * sum_xy - sum_x * sum_y) / denominator
        if c1 <= 0: return None, "Invalid slope"
        
        Qu = 1.0 / c1
        return Qu, {"c1": round(c1, 5)}

def main():
    import argparse
    parser = argparse.ArgumentParser(description="MODULE: Phân tích thí nghiệm nén tĩnh cọc")
    parser.add_argument("--input", required=True)
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)

    interpreter = PileLoadTestInterpreter(
        data["loads_kn"],
        data["settlements_mm"],
        data["pile_length_m"],
        data["pile_area_m2"],
        data["E_pile_kpa"],
        data["pile_diameter_m"]
    )
    
    qu_davisson, log_davisson = interpreter.davisson_method()
    qu_chin, log_chin = interpreter.chin_kondner_method()
    
    result = {
        "Pile_Capacity": {
            "Davisson_Qu_kN": round(qu_davisson, 1) if qu_davisson else "Chưa phá hoại theo Davisson",
            "Chin_Kondner_Qu_kN": round(qu_chin, 1) if qu_chin else "Lỗi nội suy",
            "Recommended_Design_Load_kN": round(qu_chin / 2.0, 1) if qu_chin else None # FS=2
        },
        "Calculation_Logs": [
            {"step": "Davisson", "formula": "s = PL/AE + 4.0 + D/120"},
            {"step": "Chin-Kondner", "formula": "s/P = c1*s + c2, Qu = 1/c1"}
        ],
        "Standard_Method": "ASTM D1143 + Davisson (1972)"
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
