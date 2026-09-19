# SKILL_CONNECTION — Thiết kế Chi tiết Liên kết & Mối nối Kết cấu

`SKILL_CONNECTION` tập trung vào việc **thiết kế, tính toán sức chịu tải và chi tiết hóa các nút liên kết** (Nút khung dầm-cột, nối dầm, chân cột thép, neo cốt thép BTCT, đường hàn, bản mã, bu lông).

---

## 1. Tiêu chuẩn Áp dụng

- **Liên kết Thép**: TCVN 5575:2012 / Eurocode 3 Part 1-8 (EN 1993-1-8) / AISC 360-16.
- **Chi tiết Neo & Nối cốt thép BTCT**: TCVN 5574:2018 / Eurocode 2 (EN 1992-1-1).

---

## 2. Các Dạng Liên kết Chính & Quy trình Tính toán

### 2.1. Liên kết Bu lông Cường độ cao (CCT / Shear & Tension Connections)

#### Khả năng chịu cắt của 1 bu lông ($V_{b,Rd}$):
$$V_{b,Rd} = \frac{\alpha_v \cdot f_{ub} \cdot A_s}{\gamma_{M2}}$$
*(TCVN 5575: $\alpha_v = 0.4$ với cấp 8.8, 10.9; $A_s$ là diện tích phần ren)*

#### Khả năng chịu ép mặt của bản mã ($F_{b,Rd}$):
$$F_{b,Rd} = \frac{k_1 \cdot a_b \cdot f_u \cdot d \cdot t}{\gamma_{M2}}$$

#### Khả năng chịu kéo của 1 bu lông ($F_{t,Rd}$):
$$F_{t,Rd} = \frac{0.9 \cdot f_{ub} \cdot A_s}{\gamma_{M2}}$$

#### Kiểm tra tương tác Cắt - Kéo đồng thời:
$$\frac{V_{Ed}}{V_{b,Rd}} + \frac{F_{t,Ed}}{1.4 \cdot F_{t,Rd}} \le 1.0$$

---

### 2.2. Liên kết Đường hàn (Welded Connections)

#### Đường hàn góc chịu cắt / kéo (Fillet Weld):
- Ứng suất tính toán trong đường hàn góc:
  $$\sigma_{w,f} = \frac{N_{Ed}}{a \cdot l_w} \le f_{vw} \cdot \gamma_c$$
  *(Trong đó $a$ là chiều cao đường hàn $a \approx 0.7 k_w$, $l_w$ là chiều dài làm việc đường hàn, $f_{vw}$ là cường độ chịu cắt của đường hàn).*
- Kiểm tra kết hợp lực dọc $N$, lực cắt $V$, mô men $M$:
  $$\tau_w = \sqrt{\sigma_{\perp}^2 + 3(\tau_{\perp}^2 + \tau_{\parallel}^2)} \le \frac{f_u}{\beta_w \cdot \gamma_{M2}}$$

---

### 2.3. Liên kết Chân cột Thép (Baseplate & Anchor Bolts)

#### Tính diện tích bản đế chịu nén ($A_{bp}$):
$$f_{jd} = \beta_j \cdot k_j \cdot f_{cd}$$
$$A_{bp,req} = \frac{N_{Ed}}{f_{jd}}$$

#### Bề dày bản đế chịu uốn ($t_{bp}$):
$$t_{bp} = c \cdot \sqrt{\frac{3 \cdot \sigma_{max}}{f_y / \gamma_{M0}}}$$
*(với $c$ là độ vươn lớn nhất của bản đế ngoài đường tim thép)*

#### Bu lông neo chân cột (Anchor Bolts):
- Đường kính bu lông neo chịu kéo $F_{t,anchor}$:
  $$d_{anchor} \ge \sqrt{\frac{4 \cdot F_{t,anchor}}{\pi \cdot f_{yb} \cdot 0.8}}$$
- Chiều dài neo vào móng bê tông: $L_{anchor} \ge 25 d_{anchor} \div 30 d_{anchor}$.

---

### 2.4. Neo & Nối Cốt thép BTCT (Rebar Anchorage & Lapping)

#### Chiều dài neo cơ bản cốt thép ($L_{0,an}$ TCVN 5574:2018):
$$L_{0,an} = \frac{R_s \cdot A_s}{R_{bond} \cdot u}$$
$$R_{bond} = \eta_1 \cdot \eta_2 \cdot R_{bt}$$

#### Chiều dài neo tính toán ($L_{an}$):
$$L_{an} = \alpha \cdot L_{0,an} \ge L_{an,min} = \max(0.3 L_{0,an}, 15d, 200\text{ mm})$$

#### Chiều dài nối chồng cốt thép ($L_{lap}$):
$$L_{lap} = \alpha_{lap} \cdot L_{an}$$
*(với $\alpha_{lap} = 1.2 \div 2.0$ tùy theo tỷ lệ cốt thép nối tại một mặt cắt).*

---

## 3. Quy trình Xuất Chi tiết Liên kết & Tự động Vẽ 2D

Mọi kết quả tính toán chi tiết liên kết phải tuân thủ luồng:

1. **Bảng tham số kỹ thuật đầu ra (JSON/Params)**:
   - Bu lông: Loại (8.8/10.9), d (mm), số lượng hàng/cột, khoảng cách $e_1, e_2, p_1, p_2$.
   - Bản mã: Bề dày $t$ (mm), kích thước $B \times H$.
   - Đường hàn: Chiều cao đường hàn $a_w$ (mm), chiều dài hàn $l_w$.
2. **Gọi `Technical_Illustrator` (MODE 2D)**:
   - Sử dụng script Python tương ứng (`draw_bolt_connection.py`, `draw_2d_section.py`, `draw_rc_column.py`...) để xuất file ảnh `.png` chất lượng cao.
3. **Đánh giá Khả năng Thi công (Constructability & Clearance)**:
   - Kiểm tra khoảng hở siết bu lông bằng súng vặn (Wrench clearance).
   - Kiểm tra khả năng tháo lắp và thao tác hàn tại công trường.
