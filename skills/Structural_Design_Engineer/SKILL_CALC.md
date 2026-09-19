---
name: SKILL_CALC
version: 2.1.0
last_updated: 2026-08-18
description: "Module tính toán kết cấu: kiểm tra tiết diện BTCT/thép, móng cọc, tải trọng, tổ hợp. Kích hoạt khi: tính toán kết cấu, kiểm tra tiết diện, thuyết minh tính toán."
---

# SKILL_CALC — Quy trình & Công thức Tính toán Thiết kế Kết cấu

`SKILL_CALC` đảm nhận vai trò **tính toán trực tiếp sức chịu tải và biến dạng** của các linh kiện kết cấu (BTCT, Kết cấu thép, Móng) theo các tiêu chuẩn kỹ thuật hiện hành.

---

## 1. Tiêu chuẩn Áp dụng & Phiên bản (Standards Lock)

> ⚠ **Nguồn sự thật duy nhất về phiên bản tiêu chuẩn: `../STANDARDS_LOCK.md`.**
> File này KHÔNG được tự khai báo phiên bản riêng. Bảng dưới chỉ nêu phạm vi lĩnh vực.

| Lĩnh vực | Tiêu chuẩn (phiên bản → xem STANDARDS_LOCK.md) |
|---|---|
| Tải trọng & tổ hợp | TCVN 2737 · TCVN 9386 (động đất) |
| Bê tông cốt thép | TCVN 5574 / Eurocode 2 (EN 1992-1-1) / ACI 318 |
| Kết cấu thép | TCVN 5575 / Eurocode 3 (EN 1993-1-1) / AISC 360 |
| Nền móng | TCVN 10304 (móng cọc) · TCVN 9362 (nền nhà) |

**Lưu ý về script tính toán:** `calc_steel_beam.py` và `calc_steel_connection.py` hiện cài đặt phương pháp **Eurocode 3** (EN 1993-1-1 / EN 1993-1-8), không phải TCVN 5575. Script tự khai báo qua trường `Standard_Method`. Báo cáo phải ghi đúng trường này, không được tự đổi nhãn thành TCVN.

---

## 2. Quy trình Tính toán Chuẩn mực 5 Bước

Mọi bài toán thiết kế kết cấu phải tuân theo quy trình 5 bước:

### Bước 1: Xác định Mô hình Tải trọng & Tổ hợp (Load Combinations)
- **Trạng thái giới hạn thứ nhất (ULS)**: Tổ hợp cơ bản chịu lực:
  $$q_{ULS} = \gamma_G \cdot G + \gamma_Q \cdot Q_1 + \sum \psi_{0i} \cdot \gamma_{Qi} \cdot Q_i$$
  *(Theo TCVN 2737:2023: $\gamma_G = 1.2 \div 1.3$, $\gamma_Q = 1.3 \div 1.5$)*
- **Trạng thái giới hạn thứ hai (SLS)**: Tổ hợp tiêu chuẩn kiểm tra võng & nứt:
  $$q_{SLS} = 1.0 \cdot G + 1.0 \cdot Q$$

### Bước 2: Xác định Nội lực Đầu vào (Internal Forces)
- Mô men uốn $M_{Ed}$ (kNm), Lực cắt $V_{Ed}$ (kN), Lực dọc $N_{Ed}$ (kN), Mô men xoắn $T_{Ed}$ (kNm).

### Bước 3: Tính toán Tiết diện & Khả năng Chịu lực (Capacity Calculations)

#### 3.1. Dầm / Sàn BTCT (Chịu Uốn & Cắt)
- **Chiều cao vùng bê tông chịu nén ($x$)**:
  $$x = \frac{R_s \cdot A_s}{R_b \cdot b}$$
- **Điều kiện hạn chế**: $\xi = \frac{x}{h_0} \le \xi_R = \frac{\alpha_R}{1 + \frac{\sigma_{sr}}{R_{sc}} \left(1 - \frac{\alpha_R}{1.1}\right)}$
- **Mô men chống uốn ($M_{Rd}$)**:
  $$M_{Rd} = R_b \cdot b \cdot x \cdot \left(h_0 - 0.5x\right)$$
- **Kiểm tra uốn**: $\eta_M = \frac{M_{Ed}}{M_{Rd}} \le 1.0$
- **Kiểm tra cắt (Dầm BTCT)**:
  $$Q_{b} = 0.5 \cdot R_{bt} \cdot b \cdot h_0, \quad Q_{sw} = q_{sw} \cdot c_0$$
  $$Q_{Rd} = Q_b + Q_{sw} \ge V_{Ed} \quad (\eta_V = \frac{V_{Ed}}{Q_{Rd}} \le 1.0)$$

#### 3.2. Cột BTCT (Chịu Nén Uốn Lệch Tâm)
- Đột lệch tâm tính toán: $e_0 = \frac{M_{Ed}}{N_{Ed}} + e_a$. Đặt $e = e_0 + \frac{h}{2} - a$.
- Xác định trường hợp lệch tâm lớn ($\xi \le \xi_R$) hay lệch tâm bé ($\xi > \xi_R$).
- Diện tích cốt thép dọc $A_s, A_s'$ tính toán đảm bảo hàm lượng $\mu = \frac{A_s + A_s'}{b \cdot h} \in [0.8\%, 4.0\%]$.

#### 3.3. Dầm Thép (chịu Uốn, Cắt & Mất ổn định tổng thể LTB)
- **Độ bền uốn tiết diện**: $M_{c,Rd} = W_{pl} \cdot f_y / \gamma_{M0}$
- **Ổn định tổng thể (Lateral Torsional Buckling)**:
  $$M_{b,Rd} = \chi_{LT} \cdot W_{pl} \cdot f_y / \gamma_{M1}$$
- **Lực cắt bền**: $V_{c,Rd} = A_v \cdot \left(f_y / \sqrt{3}\right) / \gamma_{M0}$
- **Kiểm tra tổng hợp**: $\eta = \max(\frac{M_{Ed}}{M_{b,Rd}}, \frac{V_{Ed}}{V_{c,Rd}}) \le 1.0$

#### 3.4. Sức chịu tải Móng cọc (BTCT)
- Sức chịu tải cọc đơn theo vật liệu $R_{vl}$ và theo đất nền $R_{dn}$ (TCVN 10304:2014):
  $$P_{rc} = \min(R_{vl}, R_{dn})$$
- Tải trọng truyền lên cọc góc/cọc biên trong đài móng:
  $$P_{max} = \frac{N^{tc}}{n} + \frac{M_y^{tc} \cdot x_{max}}{\sum x_i^2} + \frac{M_x^{tc} \cdot y_{max}}{\sum y_i^2} \le 1.2 \cdot P_{rc}$$

### Bước 4: Kiểm tra Trạng thái Giới hạn thứ Hai (SLS)
- **Độ võng ($f$)**: $f_{max} \le [f] = L / 250 \div L / 400$.
- **Bề rộng khe nứt BTCT ($a_{crc}$)**: $a_{crc} \le [a_{crc}] = 0.3 \text{ mm}$ (dài hạn), $0.4 \text{ mm}$ (ngắn hạn).

### Bước 5: Đánh giá & Kết luận
- Tổng hợp bảng chỉ số $\eta$:
  $$\text{Chỉ số sử dụng } \eta = \max\left(\eta_M, \eta_V, \eta_{SLS}, \eta_{foundation}\right)$$
- Nếu $\eta \le 1.0 \rightarrow$ **ĐẠT (PASSED)**.
- Nếu $\eta > 1.0 \rightarrow$ **KHÔNG ĐẠT (FAILED)** $\rightarrow$ Đề xuất tăng tiết diện hoặc tăng cấp độ bền vật liệu.
