# Hướng dẫn Thiết kế Nền Móng & Cọc BTCT (Foundation Design Guide)

## 1. Tính toán Móng Cọc Ép / Cọc Nhồi (TCVN 10304:2014)

### 1.1. Sức chịu tải của Cọc theo Đất nền ($R_{dn}$)
$$R_{dn} = \gamma_c \cdot \left(q_b \cdot A_b + u \cdot \sum f_i \cdot l_i\right)$$
- $q_b$: Mũi cọc tựa vào lớp đất tốt.
- $f_i$: Ma sát thành cọc tại từng lớp đất.

### 1.2. Sức chịu tải của Cọc theo Vật liệu ($R_{vl}$)
$$R_{vl} = \gamma_{cb} \cdot \left(\phi \cdot R_b \cdot A_b + R_s \cdot A_{st}\right)$$

### 1.3. Sức chịu tải cho phép của cọc đơn:
$$P_{cp} = \frac{R_{dn}}{K_{tc}} \quad (K_{tc} = 1.4 \div 1.75)$$

---

## 2. Kiểm tra Đài Móng Cọc

### 2.1. Kiểm tra Chọc thủng Đài móng (Punching Shear)
$$P_{punch} \le P_{rd} = 0.75 \cdot R_{bt} \cdot b_{m} \cdot h_0$$

### 2.2. Tính uốn Đài móng & Bố trí Cốt thép
$$M_{dx} = \sum P_i \cdot y_i, \quad M_{dy} = \sum P_i \cdot x_i$$
$$A_{sx} = \frac{M_{dx}}{0.9 \cdot h_0 \cdot R_s}, \quad A_{sy} = \frac{M_{dy}}{0.9 \cdot h_0 \cdot R_s}$$
