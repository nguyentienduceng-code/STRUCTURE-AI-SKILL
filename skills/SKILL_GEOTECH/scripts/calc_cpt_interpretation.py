import sys
import json
import math

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# =============================================================================
# calc_cpt_interpretation.py — MODULE 6: Phân tích CPTu (Piezocone)
# =============================================================================
# Version: 2.3.2
# Standard_Method: Robertson (2016) SBT + Teh & Houlsby (1991) + Nkt động
# Fixes v2.3.2:
#   - Bổ sung SBT 2016 đầy đủ (Robertson & Wride 1997)
#   - Cải thiện calc_dynamic_nkt() theo Robertson 2016
#   - Tích hợp ch (hệ số cố kết thủy lực) từ t50
#   - Thêm Calculation_Logs chi tiết từng bước
# Reference: SKILL_GEOTECH DeepResearch Report
# =============================================================================

# ── SBT 2016 Soil Behavior Type Classification ──────────────────────────────
# Nguồn: Robertson & Wride (1997); Robertson (2009, 2016)
# Bảng phân loại đầy đủ theo Ic (Soil Behavior Type Index)

SBT_2016_CLASSIFICATION = [
    # (Ic_min, Ic_max, soil_type, description, drainage, typical_Nkt)
    (3.60, 9.30, "organic_peat",      "Bùn hữu cơ / Than bùn",        "Undrained",  None),
    (3.60, 9.30, "clay",              "Sét",                            "Undrained",  15),
    (2.95, 3.60, "clayey_silt",       "Sét pha bụi / Silt sét",        "Undrained",  14),
    (2.60, 2.95, "silty_sand_clay",   "Cát pha sét / Sét pha cát",     "Mixed",      12),
    (2.05, 2.60, "sandy_silt",        "Cát pha bụi",                   "Drained",    10),
    (1.31, 2.05, "sand",              "Cát — sạch đến bụi",             "Drained",    8),
    (1.31, 9.30, "gravel_sand",       "Cát sỏi / Đất hạt thô",        "Drained",    6),
]


class CPTuInterpreter:
    """
    Bộ phân tích CPTu theo Robertson (2016).
    Fix v2.3.2: SBT 2016 đầy đủ, Nkt động theo Bq/Ip, tính ch từ t50.
    """

    def __init__(self, qc_kpa, fs_kpa, u2_kpa, u0_kpa,
                 sigma_v_kpa, sigma_v_eff_kpa, pa=100.0, a_ratio=0.8):
        self.qc = qc_kpa
        self.fs = fs_kpa
        self.u2 = u2_kpa if u2_kpa is not None else 0.0
        self.u0 = u0_kpa
        self.sigma_v = sigma_v_kpa
        self.sigma_v_eff = sigma_v_eff_kpa if sigma_v_eff_kpa > 0 else 1.0
        self.pa = pa
        self.a_ratio = a_ratio
        self.is_cptu = u2_kpa is not None

    def calculate_qt(self):
        """Bước 1: Hiệu chỉnh qt từ qc và u2."""
        if self.is_cptu:
            qt = self.qc + self.u2 * (1 - self.a_ratio)
        else:
            qt = self.qc
        return qt

    def calculate_sbt_index(self):
        """
        Bước 2: Phân loại SBT 2016 — Robertson (2016).
        Tính Ic, Qt, Fr, Bq, xác định loại đất và điều kiện thoát nước.
        Fix v2.3.2: Bổ sung bảng đầy đủ 7 nhóm SBT.
        """
        qt = self.calculate_qt()
        qn = qt - self.sigma_v
        if qn <= 0.01:
            qn = 0.01

        # ── Bq (thường gọi là Bq, Robertson dùng Bq) ──
        Bq = (self.u2 - self.u0) / qn if self.is_cptu and qn > 0 else 0.0

        # ── Lặp để tìm n và Qtn (Robertson 2009) ──
        n = 0.5  # khởi tạo
        Qtn = 1.0

        for _ in range(5):  # 5 vòng lặp để hội tụ
            # Tỷ số ma sát Fr
            Fr = (self.fs / qn) * 100.0 if qn > 0 else 0.1
            if Fr <= 0:
                Fr = 0.1

            Qtn = (qn / self.pa) * ((self.pa / self.sigma_v_eff) ** n)
            if Qtn <= 0.01:
                Qtn = 0.01

            try:
                Ic = math.sqrt(
                    (3.47 - math.log10(Qtn)) ** 2 +
                    (math.log10(Fr) + 1.22) ** 2
                )
            except (ValueError, OverflowError):
                Ic = 3.5

            # Cập nhật n (Robertson 2009)
            n = 0.381 * Ic + 0.05 * (self.sigma_v_eff / self.pa) - 0.15
            n = max(0.5, min(1.0, n))

        # ── Qt = tỷ số sức kháng mũi đã hiệu chỉnh ──
        Qt = qn / self.pa

        # ── Phân loại SBT 2016 — Fix v2.3.2: bảng đầy đủ ──
        for ic_min, ic_max, soil_type, description, drainage, _ in SBT_2016_CLASSIFICATION:
            if ic_min <= Ic < ic_max:
                sbt_result = {
                    "soil_type": soil_type,
                    "description": description,
                    "drainage": drainage,
                }
                break
        else:
            sbt_result = {
                "soil_type": "unknown",
                "description": "Không xác định",
                "drainage": "Mixed",
            }

        return {
            "qt_kpa": round(qt, 1),
            "qn_kpa": round(qn, 1),
            "Bq": round(Bq, 3),
            "Qt": round(Qt, 2),
            "Qtn": round(Qtn, 2),
            "Fr_pct": round(Fr, 2),
            "Ic": round(Ic, 3),
            "n_iterated": round(n, 3),
            **sbt_result
        }

    def calc_nkt(self, Ic, Bq=None, Ip=None):
        """
        Bước 3: Tính Nkt động theo Robertson (2016).
        Fix v2.3.2: Cải thiện từ hardcode 15.

        Công thức:
          - Đất dính (Ic > 2.60): Nkt ≈ 10-15, giảm theo Bq
          - Đất hỗn hợp (2.05 < Ic ≤ 2.60): Nkt ≈ 12-18
          - Đất rời (Ic ≤ 2.05): Nkt ≈ 6-12, giảm theo Fr

        Tham khảo: Robertson (2016), Lunne et al. (1997)
        """
        # Phương pháp 1: Từ Bq (ưu tiên nếu có)
        if Bq is not None and self.is_cptu:
            # Nkt giảm khi Bq tăng (áp lực nước lỗ rỗng cao → đất yếu hơn)
            if Ic > 2.95:
                # Sét
                nkt_bq = max(8.0, min(15.0, 14.0 - 3.0 * max(0, Bq)))
            elif Ic > 2.05:
                # Hỗn hợp
                nkt_bq = max(10.0, min(18.0, 15.0 - 2.0 * max(0, Bq)))
            else:
                # Cát
                nkt_bq = max(6.0, min(12.0, 10.0 - 1.5 * max(0, Bq)))
        else:
            nkt_bq = None

        # Phương pháp 2: Từ Ip (nếu có)
        nkt_ip = None
        if Ip is not None:
            # Tương quan Aas et al. (1986): Nkt = 10 + 0.23*Ip
            nkt_ip = 10.0 + 0.23 * Ip
            nkt_ip = max(8.0, min(20.0, nkt_ip))

        # Chọn Nkt: ưu tiên Bq > Ip > mặc định
        if nkt_bq is not None:
            nkt = nkt_bq
            method = "Bq (Robertson 2016)"
        elif nkt_ip is not None:
            nkt = nkt_ip
            method = "Ip (Aas et al. 1986)"
        else:
            # Fallback: dựa vào Ic
            if Ic > 2.95:
                nkt = 12.0
            elif Ic > 2.05:
                nkt = 15.0
            else:
                nkt = 10.0
            method = f"default (Ic={Ic:.2f})"

        return round(nkt, 1), method

    def compute_ch(self, t50_sec, Ir=100, r_cm=1.78):
        """
        Bước 4: Tính hệ số cố kết thủy lực ch (Teh & Houlsby 1991).
        Fix v2.3.2: Thêm đơn vị rõ ràng.

        Công thức:
            ch = (T50* × r² × √Ir) / t50

        Trong đó:
            T50* = 0.245 (hệ số thời gian cho 50% cố kết)
            r    = bán kính mũi xuyên (cm)
            Ir   = chỉ số cứng = G/su (mặc định 100)
            t50  = thời gian tiêu tán 50% (giây)

        Returns: ch (cm²/s)
        """
        if t50_sec is None or t50_sec <= 0:
            return None
        T50_star = 0.245
        ch = (T50_star * (r_cm ** 2) * math.sqrt(Ir)) / t50_sec
        return round(ch, 4)


def interpret_cpt_profile(cpt_data, gamma_avg=18.0, gwl_depth=-2.0, a_ratio=0.8,
                        calc_ch=True):
    """
    Xử lý toàn bộ profile CPTu → thông số địa kỹ thuật.

    Fix v2.3.2:
      - SBT 2016 đầy đủ
      - Nkt động theo Bq/Ip
      - Tính ch từ t50 (Teh & Houlsby)
      - Calculation_Logs chi tiết từng bước
    """
    gamma_w = 9.81
    results = []
    calc_logs = []

    calc_logs.append({
        "step": "1. Thiết lập điều kiện",
        "formula": "qt = qc + u2(1 - a); σ_v = γ×z; u0 = γw×(z - z_GWT)",
        "gamma_avg_assumed": gamma_avg,
        "gwl_depth": gwl_depth,
        "a_ratio": a_ratio
    })

    calc_logs.append({
        "step": "2. Phân loại SBT 2016 (Robertson 2016)",
        "formula": "Ic = √[(3.47 - log10(Qtn))² + (log10(Fr) + 1.22)²]",
        "note": "Lặp 5 vòng để tìm n và Qtn hội tụ"
    })

    calc_logs.append({
        "step": "3. Tính Nkt động",
        "formula_primary": "Nkt = f(Bq) — Robertson 2016",
        "formula_secondary": "Nkt = 10 + 0.23×Ip — Aas et al. 1986",
        "fallback": "Nkt dựa vào Ic khi không có Bq hoặc Ip"
    })

    if calc_ch:
        calc_logs.append({
            "step": "4. Tính ch (hệ số cố kết thủy lực)",
            "formula": "ch = (T50* × r² × √Ir) / t50",
            "note": "T50*=0.245, r=1.78cm, Ir=100 (default)"
        })

    for i, point in enumerate(cpt_data):
        depth = point["depth_m"]
        qc_kpa = point.get("qc_kpa", point.get("qc_kgcm2", 0) * 100.0)
        fs_kpa = point.get("fs_kpa", point.get("fs_kgcm2", 0) * 100.0)
        u2_kpa = point.get("u2_kpa")  # Có thể None nếu CPT thường
        t50_sec = point.get("t50_sec")
        Ip = point.get("Ip")

        sigma_v0 = gamma_avg * depth
        u0 = gamma_w * (depth - abs(gwl_depth)) if depth > abs(gwl_depth) else 0.0
        sigma_v0_eff = sigma_v0 - u0

        interpreter = CPTuInterpreter(
            qc_kpa, fs_kpa, u2_kpa, u0,
            sigma_v0, sigma_v0_eff, a_ratio=a_ratio
        )
        sbt = interpreter.calculate_sbt_index()

        # ── Tính Su ──
        Su = None
        Nkt_used = None
        Nkt_method = None
        if sbt["drainage"] in ("Undrained", "Mixed"):
            Nkt_used, Nkt_method = interpreter.calc_nkt(
                sbt["Ic"], sbt["Bq"], Ip
            )
            if u2_kpa is None and Ip is None:
                Nkt_method += " (default — thiếu u2 và Ip)"
            Su = max(0.0, (sbt["qt_kpa"] - sigma_v0) / Nkt_used)

        # ── Tính ch ──
        ch_cm2s = None
        if calc_ch and t50_sec:
            ch_cm2s = interpreter.compute_ch(t50_sec)

        results.append({
            "depth_m": round(depth, 2),
            "qc_kpa": qc_kpa,
            "fs_kpa": fs_kpa,
            "u2_kpa": u2_kpa,
            "qt_kpa": sbt["qt_kpa"],
            "Bq": sbt["Bq"],
            "Qt": sbt["Qt"],
            "Qtn": sbt["Qtn"],
            "Fr_pct": sbt["Fr_pct"],
            "Ic": sbt["Ic"],
            "soil_classification": {
                "soil_type": sbt["soil_type"],
                "description": sbt["description"],
                "drainage": sbt["drainage"]
            },
            "Su_kpa": round(Su, 1) if Su is not None else None,
            "Nkt_used": Nkt_used,
            "Nkt_method": Nkt_method,
            "ch_cm2s": ch_cm2s
        })

    return {
        "cpt_interpretation": results,
        "Calculation_Logs": calc_logs,
        "Standard_Method": "Robertson (2016) SBT; Teh & Houlsby (1991); Aas et al. (1986)",
        "SBT_2016_Reference": "Robertson & Wride (1997); Robertson (2016)"
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="MODULE 6 v2.3.2: Phân tích CPTu — SBT 2016 đầy đủ"
    )
    parser.add_argument("--input", required=True,
                        help="JSON input file with cpt_points array")
    parser.add_argument("--gamma", type=float, default=18.0,
                        help="Dung trọng trung bình (kN/m³)")
    parser.add_argument("--gwl", type=float, default=-2.0,
                        help="Cao độ mực nước ngầm (m)")
    parser.add_argument("--no-ch", action="store_true",
                        help="Bỏ qua tính ch")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)

    result = interpret_cpt_profile(
        data["cpt_points"],
        args.gamma, args.gwl,
        calc_ch=not args.no_ch
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
