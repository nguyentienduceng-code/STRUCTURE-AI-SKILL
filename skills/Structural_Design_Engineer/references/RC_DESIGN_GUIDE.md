# Hướng dẫn Thiết kế Bê tông Cốt thép (RC Design Guide)

## 1. Tính Toán Cốt Thép Dầm BTCT (TCVN 5574:2018)

### 1.1. Cốt thép dọc chịu uốn ($A_s$)
$$\alpha_m = \frac{M_{Ed}}{R_b \cdot b \cdot h_0^2}$$
$$\zeta = 0.5 \cdot (1 + \sqrt{1 - 2\alpha_m})$$
$$A_s = \frac{M_{Ed}}{\zeta \cdot h_0 \cdot R_s}$$
Điều kiện $\alpha_m \le \alpha_{R} \approx 0.39 \div 0.44$ (với thép CB400-V).

### 1.2. Cốt thép đai chịu cắt ($A_{sw}$)
$$q_{sw} = \frac{R_{sw} \cdot A_{sw}}{s}$$
$$Q_{sw} = q_{sw} \cdot c, \quad Q_b = \frac{\phi_{b2} \cdot R_{bt} \cdot b \cdot h_0^2}{c}$$
$$Q_{Rd} = Q_b + Q_{sw} \ge V_{Ed}$$

---

## 2. Chi tiết Neo & Nối Cốt thép

- Chiều dài neo thép uốn $L_{an}$ theo TCVN 5574:2018:
  - Bê tông B25, Thép CB400-V: $L_{an} \approx 35 d$.
  - Bê tông B30, Thép CB400-V: $L_{an} \approx 30 d$.
- Chiều dài nối chồng $L_{lap} = 1.2 \cdot L_{an} \approx 40 d$.
