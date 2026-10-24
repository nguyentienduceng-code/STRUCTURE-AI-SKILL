# .agents/_SHARED/standards/tables.py
# Bảng hệ số & vật liệu chuẩn — SSOT cho mọi script trong .agents/
#
# Nguồn: .agents/skills/STANDARDS_LOCK.md (v3.1.0) + PDF gốc trong
#        Design_Evaluation/standards/. Mọi script PHẢI import từ đây
#        thay vì hard-code lại (tránh trôi số liệu giữa các skill).
#
# TCVN 5574:2018  — Bê tông và bê tông cốt thép
# TCVN 5575:2024  — Kết cấu thép
# TCVN 2737:2023  — Tải trọng và tác động

from __future__ import annotations

# =============================================================================
# TCVN 5575:2024 — Kết cấu thép (Bảng 3, trang 38)
# =============================================================================
GAMMA_M0 = 1.05   # Hệ số tin cậy vật liệu — bền tiết diện
GAMMA_M1 = 1.10   # Hệ số tin cậy vật liệu — ổn định tổng thể (LTB)
GAMMA_MW = 1.25   # Hệ số tin cậy vật liệu — mối hàn

# Hệ số uốn đồng phẳng theo đường cong (Bảng 6.3)
ALPHA_LT_CURVE = {"a": 0.21, "b": 0.34, "c": 0.49, "d": 0.76}

# Cường độ chịu kéo của bulong theo cấp (MPa) — Bảng 10
BOLT_FUB = {
    "4.6": 400, "4.8": 400,
    "5.6": 500, "5.8": 500,
    "6.8": 600,
    "8.8": 800,
    "10.9": 1000,
}

# Hệ số αv cho cắt bulong
ALPHA_V = {
    "4.6": 0.6, "4.8": 0.6,
    "5.6": 0.6, "5.8": 0.6,
    "6.8": 0.5,
    "8.8": 0.6,
    "10.9": 0.5,
}

# Cường độ mối hàn (MPa) theo cấp thép (Bảng 11.1–11.4)
WELD_RWF = {
    "E35": {"th": 160.0, "ph": 160.0},
    "E42": {"th": 200.0, "ph": 200.0},
    "E50": {"th": 240.0, "ph": 240.0},
    "E60": {"th": 280.0, "ph": 280.0},
}
WELD_RWZ = {
    "E35": {"th": 160.0, "ph": 160.0},
    "E42": {"th": 200.0, "ph": 200.0},
    "E50": {"th": 240.0, "ph": 240.0},
    "E60": {"th": 280.0, "ph": 280.0},
}
BETA_F = 0.7    # Hệ số cộng hưởng độ cong mối hàn
BETA_Z = 1.0

# =============================================================================
# TCVN 5574:2018 — Bê tông & bê tông cốt thép (Bảng 7, trang 35)
# =============================================================================
# Rb — cường độ nén (MPa)
RB_MAP = {
    "B7.5": 6.0, "B10": 8.5, "B12.5": 10.5, "B15": 11.5, "B20": 14.5,
    "B25": 17.0, "B30": 19.5, "B35": 22.0, "B40": 25.0, "B45": 27.5,
    "B50": 30.0, "B55": 33.0, "B60": 37.0, "B70": 41.0, "B80": 44.0,
    "B90": 47.5, "B100": 50.0,
}

# Rbt — cường độ kéo (MPa)
RBT_MAP = {
    "B7.5": 0.48, "B10": 0.56, "B12.5": 0.66, "B15": 0.75, "B20": 0.90,
    "B25": 1.05, "B30": 1.15, "B35": 1.30, "B40": 1.40, "B45": 1.50,
    "B50": 1.60, "B55": 1.70, "B60": 1.80, "B70": 1.90, "B80": 2.10,
    "B90": 2.15, "B100": 2.20,
}

# Rb,ser — cường độ nén tính toán (MPa)
RB_SER_MAP = {
    "B7.5": 8.5, "B10": 11.0, "B12.5": 12.5, "B15": 13.5, "B20": 15.5,
    "B25": 17.0, "B30": 19.0, "B35": 21.0, "B40": 23.0, "B45": 24.5,
    "B50": 26.0, "B55": 27.5, "B60": 29.5, "B70": 32.0, "B80": 34.0,
    "B90": 35.5, "B100": 37.0,
}

# Rbt,ser — cường độ kéo tính toán (MPa)
RBT_SER_MAP = {
    "B7.5": 0.62, "B10": 0.72, "B12.5": 0.81, "B15": 0.93, "B20": 1.10,
    "B25": 1.27, "B30": 1.40, "B35": 1.57, "B40": 1.70, "B45": 1.80,
    "B50": 1.90, "B55": 2.00, "B60": 2.15, "B70": 2.25, "B80": 2.45,
    "B90": 2.50, "B100": 2.60,
}

# Eb — mô đun đàn hồi (MPa)
EB_MAP = {
    "B7.5": 24500, "B10": 27500, "B12.5": 28000, "B15": 30000,
    "B20": 30000, "B25": 32000, "B30": 32500, "B35": 33000,
    "B40": 33000, "B45": 34000, "B50": 34000, "B55": 34500,
    "B60": 34500, "B70": 35000, "B80": 35000, "B90": 35500,
    "B100": 35500,
}

# Rs — cường đng tính toán của cốt thép (MPa)
RS_MAP = {
    "CB240-T": 240, "CB300-T": 260, "CB350": 300, "CB400": 350,
    "CB400-V": 370, "CB500-V": 435, "CB500": 500,
    "SD390": 350, "SD390C": 350, "SD400": 360,
}

# Rs,ser — cường độ tính toán (MPa) ở trạng thái giới hạn thứ hai
RS_SER_MAP = {
    "CB240-T": 240, "CB300-T": 280, "CB350": 320, "CB400": 370,
    "CB400-V": 390, "CB500-V": 460, "CB500": 500,
    "SD390": 370, "SD390C": 370, "SD400": 380,
}

# Es — mô đun đàn hồi cốt thép (MPa)
ES = 200000.0

# Hệ số η1 (ảnh hưởng bề mặt cốt thép) — Mục 10.3.5.4, CT (256)
ETA_1 = {
    "plain": 1.5,          # cốt thép thanh trơn TCVN 1651-1:2008
    "cold_drawn": 2.0,     # cốt thép kéo (cán) nguội có gân
    "hot_rolled": 2.5,     # cốt thép cán nóng có gân + gia công cơ nhiệt
    "default": 2.5,
}

# Hệ số η2 (ảnh hưởng đường kính) — Mục 10.3.5.4, CT (256)
def eta_2(dia_mm: float) -> float:
    """η2 = 1.0 nếu d ≤ 32 mm; 0.9 nếu d = 36, 40 mm và lớn hơn."""
    return 1.0 if dia_mm <= 32 else 0.9


# Hệ số αan (ảnh hưởng trạng thái ứng suất & cấu tạo vùng neo) — Mục 10.3.5.5, CT (257)
ALPHA_AN_TENSION = 1.0     # neo thẳng, cốt thép có gân
ALPHA_AN_COMPRESSION = 0.75
ALPHA_AN_PRESTRESS = 1.0

# Giới hạn dưới chiều dài neo — Mục 10.3.5.5
L_AN_MIN_RATIO = 0.3       # ≥ 0.3 × L0an
L_AN_MIN_D = 15.0          # ≥ 15d
L_AN_MIN_MM = 200.0        # ≥ 200 mm

# Hệ số αlap — Mục 10.3.6.2
ALPHA_LAP_COMPRESSION = 0.9
ALPHA_LAP_TENSION_R05 = 1.2   # tỉ lệ nối ≤ 50%
ALPHA_LAP_TENSION_R10 = 2.0   # tỉ lệ nối = 100%

# Giới hạn dưới chiều dài nối — Mục 10.3.6.2
L_LAP_MIN_RATIO = 0.4      # ≥ 0.4 α × L0an
L_LAP_MIN_D = 20.0         # ≥ 20d
L_LAP_MIN_MM = 250.0       # ≥ 250 mm

# Hàm lượng cốt thép tối thiểu — Mục 10.3.3.1
MU_MIN_FLEXURE = 0.10      # % — cấu kiện chịu uốn, kéo lệch tâm, nén lệch tâm L0/h ≤ 17
MU_MIN_COLUMN = 0.25       # % — nén lệch tâm L0/h ≥ 8 (nội suy 0.10→0.25)
MU_MIN_EDGE = 0.025        # % — cốt thép chịu kéo ở biên cấu kiện nén lệch tâm

# ξR — giới hạn tương đối vùng nén — Mục 8.1.2.2.3
OMEGA_HEAVY = 0.8          # bê tông nặng cấp ≤ B60
EPS_B2 = 0.0035


def xi_r(rs: float, omega: float = OMEGA_HEAVY) -> float:
    """ξR = ω / (1 + εs,el / εb2), với εs,el = Rs / Es."""
    eps_s_el = rs / ES
    return omega / (1.0 + eps_s_el / EPS_B2)


def alpha_r(rs: float, omega: float = OMEGA_HEAVY) -> float:
    """αR = ξR × (1 − 0.5 × ξR). Phụ thuộc cấp cốt thép (≈0.39 CB400-V → 0.44)."""
    xi = xi_r(rs, omega)
    return xi * (1.0 - 0.5 * xi)


# Giới hạn bề rộng vết nứt — Mục 8.2.2
CRACK_WIDTH_LIMITS = {
    "normal": 0.4,          # mm — môi trường thường
    "humid": 0.3,           # mm — môi trường ẩm (cát đá, bể)
    "aggressive": 0.2,      # mm — môi trường xâm thực (biển, hóa chất)
}

# =============================================================================
# TCVN 2737:2023 — Tải trọng và tác động (Bảng 6, trang 38)
# =============================================================================
# Phân loại địa hình: alpha (hệ số lực nâng), k10, z_min
TERRAIN_TYPES = {
    "A": {"alpha": 0.12, "k10": 1.18, "z_min": 2.0},
    "B": {"alpha": 0.16, "k10": 1.00, "z_min": 5.0},
    "C": {"alpha": 0.22, "k10": 0.74, "z_min": 10.0},
}

# Hệ số tầm quan trọng γn theo cấp hậu quả — Phụ lục H, Bảng H.1
GAMMA_N = {"C1": 0.87, "C2": 1.00, "C3": 1.15}


def k_factor(z: float, terrain: str = "B") -> float:
    """k(z) = k10 × (max(z, z_min) / 10)^(2α) — TCVN 2737:2023 Bảng 7."""
    t = TERRAIN_TYPES.get(terrain.upper())
    if t is None:
        raise ValueError(f"Loại địa hình không hợp lệ: {terrain}")
    z_eff = max(z, t["z_min"])
    return t["k10"] * (z_eff / 10.0) ** (2.0 * t["alpha"])


# =============================================================================
# TCVN 5574:2018 — Truy vấn nhanh
# =============================================================================
def concrete_property(grade: str, prop: str = "Rb") -> float:
    """Truy vấn thuộc tính bê tông theo cấp (Rb, Rbt, Rb_ser, Rbt_ser, Eb)."""
    maps = {
        "Rb": RB_MAP, "Rbt": RBT_MAP,
        "Rb_ser": RB_SER_MAP, "Rbt_ser": RBT_SER_MAP,
        "Eb": EB_MAP,
    }
    if prop not in maps:
        raise ValueError(f"Thuộc tính không hợp lệ: {prop}")
    m = maps[prop]
    if grade not in m:
        raise ValueError(
            f"Không tìm thấy {prop} cho mác bê tông '{grade}'. "
            f"Các mác hợp lệ: {', '.join(sorted(m))}"
        )
    return m[grade]


def rebar_property(grade: str, prop: str = "Rs") -> float:
    """Truy vấn thuộc tính cốt thép theo cấp (Rs, Rs_ser)."""
    maps = {"Rs": RS_MAP, "Rs_ser": RS_SER_MAP}
    if prop not in maps:
        raise ValueError(f"Thuộc tính không hợp lệ: {prop}")
    m = maps[prop]
    if grade not in m:
        raise ValueError(
            f"Không tìm thấy {prop} cho cấp cốt thép '{grade}'. "
            f"Các cấp hợp lệ: {', '.join(sorted(m))}"
        )
    return m[grade]
