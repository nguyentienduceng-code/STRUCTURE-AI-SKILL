import sys
import json
import math

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# =============================================================================
# calc_soil_params_ssc.py — MODULE: Soft Soil Creep Parameters
# =============================================================================
# Version: 2.0.0
# Standard_Method: Plaxis Material Models Manual (SSC)
# =============================================================================

class SoftSoilCreepModel:
    def __init__(self, initial_void_ratio, compression_index, swelling_index, secondary_compression=None):
        self.e0 = initial_void_ratio
        self.Cc = compression_index
        self.Cs = swelling_index
        self.Ca = secondary_compression
        self.warnings = []

    def compute_ssc_parameters(self):
        # Chuyển đổi cơ số logarit tự nhiên (ln 10 ~ 2.303)
        ln_base_factor = 2.303 * (1 + self.e0)
        
        lambda_star = self.Cc / ln_base_factor
        kappa_star = (2 * self.Cs) / ln_base_factor
        
        if self.Ca is not None:
            mu_star = self.Ca / ln_base_factor
        else:
            # Rule of thumb: ratio lambda*/mu* is approximately 20 for Vietnam soft clays
            mu_star = lambda_star / 20.0
            self.warnings.append("Thiếu số liệu C_alpha. Đã áp dụng tỷ số kinh nghiệm lambda*/mu* = 20 để nội suy (W002).")
            
        return {
            "lambda_star": round(lambda_star, 4),
            "kappa_star": round(kappa_star, 4),
            "mu_star": round(mu_star, 5),
            "warnings": self.warnings
        }

def process_ssc(soil_data):
    results = []
    
    for layer in soil_data.get("layers", []):
        if layer.get("model") != "SSC":
            continue
            
        e0 = layer["e0"]
        Cc = layer["Cc"]
        Cs = layer["Cs"]
        Ca = layer.get("Ca")
        
        ssc = SoftSoilCreepModel(e0, Cc, Cs, Ca)
        params = ssc.compute_ssc_parameters()
        
        # Calculate permeability (if provided)
        k_val = layer.get("k_m_day", 1e-4) # very low default for soft clay
        
        results.append({
            "layer_name": layer.get("name", "Soft Clay"),
            "model": "Soft Soil Creep (SSC)",
            "lambda_star": params["lambda_star"],
            "kappa_star": params["kappa_star"],
            "mu_star": params["mu_star"],
            "k_m_per_day": k_val,
            "c_kpa": layer.get("c_kpa", 5.0), # Effective cohesion
            "phi_deg": layer.get("phi_deg", 20.0), # Effective friction angle
            "psi_deg": 0.0,
            "Rinter": layer.get("Rinter", 0.6), # Defaults to sheet pile value in weak clay
            "warnings": params["warnings"]
        })
        
    return {
        "ssc_parameters": results,
        "Calculation_Logs": [
            {"step": "Tính lambda*", "formula": "Cc / (2.3 * (1 + e0))"},
            {"step": "Tính kappa*", "formula": "2 * Cs / (2.3 * (1 + e0))"},
            {"step": "Tính mu*", "formula": "Ca / (2.3 * (1 + e0)) hoặc lambda* / 20"}
        ],
        "Standard_Method": "Plaxis Soft Soil Creep Model"
    }

def main():
    import argparse
    parser = argparse.ArgumentParser(description="MODULE: Phân tích SSC")
    parser.add_argument("--input", required=True)
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)

    result = process_ssc(data)
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
