import sys
import json
import math

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# =============================================================================
# calc_foundation_pile.py — Tinh suc chiu tai coc theo TCVN 10304:2025
# =============================================================================
# Phien ban: TCVN 10304:2025
# Reference: Dieu 7.2 (coc ma sat — PP chi tieu co ly), Dieu 7.3 (coc chong)
# =============================================================================

# --- He so dieu kien lam viec ---
GAMMA_C_DEFAULT = 1.4    # He so an toan cho suc chiu tai coc (mac dinh)
GAMMA_CF = 1.0           # He so dieu kien lam viec cua dat duoi mui coc
GAMMA_CR = 1.0           # He so dieu kien lam viec cua dat quanh than coc

# --- Cuong do ma sat thanh fi theo TCVN 10304:2025 Bang 3 (kPa) ---
# Key: (loai_dat, trang_thai), Value: {do_sau_m: fi_kPa}
# Don gian hoa: Noi suy tuyen tinh theo do sau
FI_TABLE = {
    # Cat hat nho
    ("cat_hat_nho", "chat"): {1: 35, 2: 42, 3: 48, 5: 56, 7: 62, 10: 68, 15: 72, 20: 79, 25: 86, 30: 93},
    ("cat_hat_nho", "chat_vua"): {1: 23, 2: 30, 3: 35, 5: 40, 7: 44, 10: 48, 15: 52, 20: 56, 25: 60, 30: 65},
    # Cat hat trung
    ("cat_hat_trung", "chat"): {1: 42, 2: 52, 3: 58, 5: 64, 7: 70, 10: 76, 15: 82, 20: 88, 25: 94, 30: 100},
    ("cat_hat_trung", "chat_vua"): {1: 33, 2: 40, 3: 44, 5: 50, 7: 54, 10: 58, 15: 63, 20: 67, 25: 72, 30: 76},
    # Set pha cat
    ("set_pha_cat", "0.4"): {1: 12, 2: 16, 3: 18, 5: 22, 7: 24, 10: 26, 15: 28, 20: 30, 25: 32, 30: 34},
    ("set_pha_cat", "0.5"): {1: 8, 2: 12, 3: 14, 5: 16, 7: 18, 10: 19, 15: 20, 20: 22, 25: 24, 30: 26},
    ("set_pha_cat", "0.6"): {1: 4, 2: 7, 3: 8, 5: 9, 7: 10, 10: 10, 15: 11, 20: 12, 25: 13, 30: 14},
    # Set
    ("set", "0.3"): {1: 15, 2: 20, 3: 24, 5: 28, 7: 32, 10: 34, 15: 38, 20: 42, 25: 44, 30: 46},
    ("set", "0.4"): {1: 12, 2: 16, 3: 18, 5: 22, 7: 24, 10: 26, 15: 28, 20: 30, 25: 32, 30: 34},
    ("set", "0.5"): {1: 8, 2: 12, 3: 14, 5: 16, 7: 18, 10: 19, 15: 20, 20: 22, 25: 24, 30: 26},
    ("set", "0.6"): {1: 4, 2: 5, 3: 7, 5: 8, 7: 9, 10: 10, 15: 10, 20: 11, 25: 12, 30: 13},
    ("set", "0.8"): {1: 3, 2: 4, 3: 5, 5: 6, 7: 7, 10: 8, 15: 8, 20: 9, 25: 10, 30: 10},
}

# --- Cuong do chong duoi mui coc qp theo TCVN 10304:2025 Bang 2 (kPa) ---
# Key: (loai_dat_mui, trang_thai_mui), Value: {do_sau_m: qp_kPa}
QP_TABLE = {
    ("cat_hat_nho", "chat"): {3: 1600, 5: 2200, 7: 2800, 10: 3300, 15: 4000, 20: 5000, 25: 5600, 30: 6200},
    ("cat_hat_nho", "chat_vua"): {3: 750, 5: 1000, 7: 1250, 10: 1500, 15: 1700, 20: 2000, 25: 2200, 30: 2500},
    ("cat_hat_trung", "chat"): {3: 2000, 5: 3000, 7: 3500, 10: 4000, 15: 5000, 20: 5500, 25: 6200, 30: 6800},
    ("cat_hat_trung", "chat_vua"): {3: 1000, 5: 1500, 7: 2000, 10: 2500, 15: 3000, 20: 3500, 25: 4000, 30: 4500},
    ("set_pha_cat", "0.3"): {3: 850, 5: 1000, 7: 1100, 10: 1250, 15: 1400, 20: 1500, 25: 1600, 30: 1700},
    ("set_pha_cat", "0.5"): {3: 500, 5: 600, 7: 700, 10: 800, 15: 900, 20: 1000, 25: 1100, 30: 1200},
    ("set", "0.3"): {3: 600, 5: 750, 7: 850, 10: 950, 15: 1050, 20: 1150, 25: 1200, 30: 1300},
    ("set", "0.5"): {3: 300, 5: 400, 7: 450, 10: 500, 15: 550, 20: 600, 25: 650, 30: 700},
}


def _interpolate(table, depth):
    """Noi suy tuyen tinh gia tri fi hoac qp theo do sau."""
    depths = sorted(table.keys())
    if depth <= depths[0]:
        return table[depths[0]]
    if depth >= depths[-1]:
        return table[depths[-1]]
    for i in range(len(depths) - 1):
        if depths[i] <= depth <= depths[i + 1]:
            d1, d2 = depths[i], depths[i + 1]
            v1, v2 = table[d1], table[d2]
            return v1 + (v2 - v1) * (depth - d1) / (d2 - d1)
    return table[depths[-1]]


def calc_pile_capacity(pile_type="driven",
                       pile_d=400, pile_length=20,
                       soil_layers=None,
                       tip_soil_type="cat_hat_trung",
                       tip_soil_state="chat_vua",
                       gamma_c=GAMMA_C_DEFAULT,
                       gamma_cf=GAMMA_CF,
                       gamma_cr=GAMMA_CR,
                       N_ed=800):
    """
    Tinh suc chiu tai coc theo PP chi tieu co ly dat — TCVN 10304:2025 Dieu 7.2.

    Args:
        pile_type    : "driven" (dong) hoac "bored" (khoan nhoi)
        pile_d       : Duong kinh / canh coc (mm)
        pile_length  : Chieu dai coc (m) — tu mat dat den mui coc
        soil_layers  : List cac lop dat, moi lop la dict:
                       {
                           "name": "Lop 1 — Set pha cat",
                           "top_m": 0, "bot_m": 5,
                           "soil_type": "set_pha_cat",
                           "state": "0.5"
                       }
        tip_soil_type  : Loai dat tai mui coc
        tip_soil_state : Trang thai dat tai mui coc
        gamma_c      : He so an toan chung
        gamma_cf     : He so dieu kien lam viec dat duoi mui
        gamma_cr     : He so dieu kien lam viec dat quanh than
        N_ed         : Tai trong thiet ke (kN)

    PHAM VI: Coc dong/ep tiet dien vuong/tron, PP chi tieu co ly.
    CHUA kiem tra: PP thi nghiem hien truong, coc khoan nhoi (he so giam),
                   nhom coc, coc chiu keo, coc chiu ngang.
    """
    logs = []
    warnings = []
    unverified = []

    if soil_layers is None:
        soil_layers = [
            {"name": "Lop 1 — Set pha cat", "top_m": 0, "bot_m": 8,
             "soil_type": "set_pha_cat", "state": "0.5"},
            {"name": "Lop 2 — Cat hat trung", "top_m": 8, "bot_m": 20,
             "soil_type": "cat_hat_trung", "state": "chat_vua"},
        ]
        unverified.append("Su dung so lieu dia chat MAU (2 lop). Can nhap so lieu DCCT thuc te.")

    # --- Kich thuoc coc ---
    d_m = pile_d / 1000.0  # m

    # Dien tich mat cat mui coc
    if pile_type == "driven":
        # Coc vuong: Ap = d^2;  Coc tron: Ap = pi*d^2/4
        # Mac dinh: coc vuong (pho bien o VN)
        Ap = (d_m ** 2)  # m2
        u = 4.0 * d_m    # chu vi (m)
        pile_shape = "vuong"
    else:
        Ap = math.pi * (d_m ** 2) / 4.0  # m2
        u = math.pi * d_m  # chu vi (m)
        pile_shape = "tron"

    logs.append({
        "Step": 1,
        "Description": "Xac dinh kich thuoc coc",
        "Principle": "Dien tich mat cat va chu vi coc de tinh suc khang mui va ma sat than.",
        "Formula": f"Coc {pile_shape}: Ap = {'d^2' if pile_shape == 'vuong' else 'pi*d^2/4'},  u = {'4*d' if pile_shape == 'vuong' else 'pi*d'}",
        "Citation": {"Ma_TC": "TCVN 10304:2025", "Dieu_Muc": "Dieu 7.2", "Bang_Hinh": "", "Trang": "32", "Trich_Yeu": "Kích thước hình học và diện tích cọc"},
        "Substitution": f"d = {pile_d} mm = {d_m} m",
        "Result": f"Ap = {Ap:.4f} m2,  u = {u:.3f} m"
    })

    # =========================================================================
    # 2. TINH SUC KHANG QUANH THAN COC (Qf)
    # =========================================================================
    # Chia moi lop dat thanh cac phan tu 2m, tra fi theo do sau trung binh
    Qf_total = 0.0
    fi_details = []

    for layer in soil_layers:
        top = max(layer["top_m"], 0)
        bot = min(layer["bot_m"], pile_length)
        if bot <= top:
            continue

        soil_type = layer["soil_type"]
        state = str(layer["state"])
        key = (soil_type, state)

        if key not in FI_TABLE:
            warnings.append(f"Khong tim thay fi cho ({soil_type}, {state}). Bo qua lop '{layer['name']}'.")
            continue

        fi_map = FI_TABLE[key]

        # Chia phan tu 2m
        z = top
        while z < bot:
            z_next = min(z + 2.0, bot)
            z_mid = (z + z_next) / 2.0
            hi = z_next - z
            fi = _interpolate(fi_map, z_mid)
            Qfi = gamma_cr * fi * u * hi  # kN/m * m = kN (fi la kPa = kN/m2)
            Qf_total += Qfi
            fi_details.append({
                "layer": layer["name"],
                "z_mid_m": round(z_mid, 1),
                "hi_m": round(hi, 1),
                "fi_kPa": round(fi, 1),
                "Qfi_kN": round(Qfi, 1)
            })
            z = z_next

    logs.append({
        "Step": 2,
        "Description": "Tinh suc khang ma sat quanh than coc (Qf)",
        "Principle": "Ma sat than coc = tong (gamma_cr * fi * u * hi) cua tat ca phan tu.",
        "Formula": "Qf = sum(gamma_cr * fi * u * hi)",
        "Citation": {
            "Ma_TC": "TCVN 10304:2025",
            "Dieu_Muc": "Dieu 7.2.1",
            "Bang_Hinh": "Bang 3 — Cuong do ma sat thanh fi",
            "Trang": "35",
            "Trich_Yeu": "Suc chiu tai coc theo chi tieu co ly dat"
        },
        "Substitution": f"u = {u:.3f} m, gamma_cr = {gamma_cr}, so phan tu = {len(fi_details)}",
        "Result": f"Qf = {Qf_total:.1f} kN",
        "Details": fi_details
    })

    # =========================================================================
    # 3. TINH SUC KHANG DUOI MUI COC (Qp)
    # =========================================================================
    tip_key = (tip_soil_type, tip_soil_state)
    if tip_key in QP_TABLE:
        qp = _interpolate(QP_TABLE[tip_key], pile_length)
    else:
        qp = 0
        warnings.append(f"Khong tim thay qp cho ({tip_soil_type}, {tip_soil_state}). Qp = 0.")

    Qp = gamma_cf * qp * Ap  # kN

    # He so giam cho coc khoan nhoi
    if pile_type == "bored":
        coeff_bored = 0.6  # He so giam suc chong mui cho coc khoan nhoi
        Qp = Qp * coeff_bored
        warnings.append(f"Coc khoan nhoi: Qp giam con {coeff_bored*100:.0f}% so voi coc dong.")

    logs.append({
        "Step": 3,
        "Description": "Tinh suc khang duoi mui coc (Qp)",
        "Principle": "Suc chong cua dat duoi mui coc = gamma_cf * qp * Ap.",
        "Formula": "Qp = gamma_cf * qp * Ap",
        "Citation": {
            "Ma_TC": "TCVN 10304:2025",
            "Dieu_Muc": "Dieu 7.2.1",
            "Bang_Hinh": "Bang 2 — Cuong do chong duoi mui coc qp",
            "Trang": "34",
            "Trich_Yeu": "Suc khang duoi mui coc"
        },
        "Substitution": f"qp = {qp:.0f} kPa, Ap = {Ap:.4f} m2, gamma_cf = {gamma_cf}",
        "Result": f"Qp = {Qp:.1f} kN"
    })

    # =========================================================================
    # 4. SUC CHIU TAI CHO PHEP
    # =========================================================================
    Rc = Qf_total + Qp           # kN — suc chiu tai cuc han
    Ra = Rc / gamma_c             # kN — suc chiu tai cho phep

    eta = N_ed / Ra if Ra > 0 else 999

    logs.append({
        "Step": 4,
        "Description": "Tinh suc chiu tai cho phep cua coc",
        "Principle": "Suc chiu tai cuc han chia he so an toan gamma_c.",
        "Formula": "Rc = Qf + Qp;  Ra = Rc / gamma_c",
        "Citation": {
            "Ma_TC": "TCVN 10304:2025",
            "Dieu_Muc": "Dieu 7.1.1",
            "Bang_Hinh": "",
            "Trang": "30",
            "Trich_Yeu": "Suc chiu tai thiet ke cua coc don"
        },
        "Substitution": f"Qf = {Qf_total:.1f} kN, Qp = {Qp:.1f} kN, gamma_c = {gamma_c}",
        "Result": f"Rc = {Rc:.1f} kN,  Ra = {Ra:.1f} kN",
        "Utilization": f"eta = N_Ed/Ra = {N_ed}/{Ra:.1f} = {eta:.3f}"
    })

    # =========================================================================
    # 5. SO COC TOI THIEU
    # =========================================================================
    n_piles_min = math.ceil(N_ed / Ra) if Ra > 0 else 999

    logs.append({
        "Step": 5,
        "Description": "So luong coc toi thieu",
        "Principle": "Tong tai phan bo deu cho cac coc.",
        "Formula": "n = ceil(N_Ed / Ra)",
        "Citation": {"Ma_TC": "TCVN 10304:2025", "Dieu_Muc": "Dieu 7.4", "Bang_Hinh": "", "Trang": "42", "Trich_Yeu": "Xác định số lượng cọc trong móng"},
        "Substitution": f"N_Ed = {N_ed} kN, Ra = {Ra:.1f} kN",
        "Result": f"n_min = {n_piles_min} coc"
    })

    # =========================================================================
    # 6. KET LUAN
    # =========================================================================
    status = "PASSED" if eta <= 1.0 else "FAILED"
    if eta <= 0.70:
        rating = "GREEN"
    elif eta <= 0.90:
        rating = "YELLOW"
    elif eta <= 1.00:
        rating = "ORANGE"
    else:
        rating = "RED"

    return {
        "pile_type": pile_type,
        "pile_shape": pile_shape,
        "pile_d_mm": pile_d,
        "pile_length_m": pile_length,
        "Ap_m2": round(Ap, 4),
        "u_m": round(u, 3),
        "tip_soil": f"{tip_soil_type} ({tip_soil_state})",
        "qp_kPa": round(qp, 0),
        "Qp_kN": round(Qp, 1),
        "Qf_kN": round(Qf_total, 1),
        "Rc_kN": round(Rc, 1),
        "gamma_c": gamma_c,
        "Ra_kN": round(Ra, 1),
        "N_ed_kN": N_ed,
        "n_piles_min": n_piles_min,
        "eta": round(eta, 3),
        "overall_eta": round(eta, 3),
        "Rating": rating,
        "status": status,
        "fi_details": fi_details,
        "Standard": "TCVN 10304:2025",
        "Standard_Method": "TCVN 10304:2025",
        "Scope_Limitation": (
            "Coc dong/ep, PP chi tieu co ly dat (Bang 2, Bang 3). "
            "CHUA kiem tra: PP thi nghiem hien truong, coc khoan nhoi day du, "
            "nhom coc, coc chiu keo, coc chiu ngang, lun nhom coc."
        ),
        "Unverified_Items": unverified,
        "Warnings": warnings,
        "Calculation_Logs": logs
    }


if __name__ == "__main__":
    if len(sys.argv) > 1:
        data = json.loads(sys.argv[1])
        res = calc_pile_capacity(**data)
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        # Sample: Coc 400x400, L=20m, 2 lop dat
        sample = calc_pile_capacity(
            pile_type="driven",
            pile_d=400,
            pile_length=20,
            soil_layers=[
                {"name": "Lop 1 — Set pha cat", "top_m": 0, "bot_m": 8,
                 "soil_type": "set_pha_cat", "state": "0.5"},
                {"name": "Lop 2 — Cat hat trung", "top_m": 8, "bot_m": 20,
                 "soil_type": "cat_hat_trung", "state": "chat_vua"},
            ],
            tip_soil_type="cat_hat_trung",
            tip_soil_state="chat_vua",
            N_ed=800
        )
        print(json.dumps(sample, ensure_ascii=False, indent=2))
