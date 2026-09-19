# Hướng dẫn Thiết kế Kết cấu Thép & Chi tiết Liên kết (Steel Design Guide)

## 1. Kiểm tra Tiết diện Dầm / Cột Thép (TCVN 5575:2012 & Eurocode 3)

### 1.1. Chịu uốn đồng phẳng ($M_x$)
$$M_{sd} \le M_{rd} = \phi_b \cdot W_{x,min} \cdot f_y \cdot \gamma_c$$
Trong đó:
- $\phi_b$: Hệ số giảm khả năng chịu uốn do mất ổn định uốn xoắn (LTB).
- $W_x$: Mô men kháng uốn tiết diện.
- $f_y$: Cường độ chảy của thép (Q355: 345 MPa, SS400: 235 MPa).

### 1.2. Chịu cắt ($V_y$)
$$V_{sd} \le V_{rd} = h_w \cdot t_w \cdot f_v \cdot \gamma_c$$
với $f_v = 0.58 f_y$.

---

## 2. Liên kết Bu lông Cường độ cao (Grade 8.8 / 10.9)

### 2.1. Cắt & Ép mặt
- Lực cắt cho phép 1 mặt cắt bu lông M20 Cấp 8.8 ($f_{ub} = 800\text{ MPa}$):
  $$V_{b,rd} = 0.4 \cdot 800 \cdot 245 = 78.4\text{ kN}$$
- Lực ép mặt cho phép trên bản mã t = 10mm ($f_u = 400\text{ MPa}$):
  $$F_{b,rd} = 2.5 \cdot 1.0 \cdot 400 \cdot 20 \cdot 10 = 200\text{ kN}$$

### 2.2. Lực siết bu lông CCT ma sát (Friction Grip Connections)
$$N_{ft} = \frac{\mu \cdot F_{p,C}}{\gamma_{M3}}$$
Trong đó $\mu = 0.35 \div 0.45$ (bề mặt làm sạch bằng phun cát), $F_{p,C} = 0.7 f_{ub} A_s$.
