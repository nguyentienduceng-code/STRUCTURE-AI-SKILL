# DUAL-AGENT HANDOFF MEMO: CHIẾN LƯỢC NÂNG CẤP & MỞ RỘNG TOÀN DIỆN ĐỘNG CƠ TÍNH TOÁN KẾT CẤU (STRUCTURE-HUB v2.5+)

**Dự án:** Cổng Tra cứu & Động cơ Tính toán Kết cấu STRUCTURE-HUB  
**Từ:** Gemini Antigravity (Lead System Architect & Frontend Lead)  
**Tới:** Claude Code (Senior Structural Algorithm Engineer & Master Peer Reviewer)  
**Ngày:** 2026-11-01  
**Trạng thái Bus:** `DUAL_AGENT_BUS.json` v6.0.0 — `CALCULATOR_UPGRADE_PHASE_PLANNING_AND_COLLABORATION`  
**Mục tiêu:** Tổng hợp toàn diện ý kiến đề xuất nâng cấp hệ thống tính toán và tra cứu tải trọng, chuyển giao cho Claude phân tích đánh giá, phản biện chuyên sâu và phân chia phối hợp triển khai.

---

## 1. Bối cảnh & Yêu cầu từ User

User đã trải nghiệm hệ sinh thái STRUCTURE-HUB và nhận định:
> *"Về phần tính toán trên app còn khá đơn giản và thô sơ hãy cho ý tưởng nâng cấp và mở rộng các bài toán tính toán và trường hợp tra cứu tải trọng tích hợp hơn. có thể tham khảo thêm các SKill hiện có để học hỏi. Tổng hợp ý kiến đề xuất của bạn đưa qua Đồng nghiệp Claude thông qua DUAL_AGENT_BUS.json để phân tích đánh giá rồi cả 2 chia ra triển khai nhé."*

Hiện tại, mục **8. Máy tính Tương tác TCVN** của app gồm 6 mô-đun:
1. `CalcWindTCVN2737.jsx`: Gió tĩnh đơn điểm tại cao độ $z$.
2. `CalcLiveLoadReduction.jsx`: Chiết giảm hoạt tải cho 4 nhóm mẫu.
3. `CalcBeamRebar.jsx`: Cốt đơn chịu uốn dầm chữ nhật.
4. `CalcBoltCapacity.jsx`: Cắt và ép mặt cho 1 bu lông đơn lẻ.
5. `CalcPileCapacity.jsx`: Cọc đơn theo SPT (Meyerhof).
6. `CalcAnchorageLap.jsx`: Neo và nối chồng cốt thép.

**Điểm hạn chế cốt lõi cần khắc phục:**
- Thiếu bài toán chịu lực phức tạp (cốt kép, cắt cốt đai, nén uốn lệch tâm xiên cột, chọc thủng, nứt võng).
- Thiếu hệ thống tra cứu và tích lũy tải trọng đồng bộ (tĩnh tải hoàn thiện, tường xây, bảng tra hoạt tải đầy đủ, gió động, tổ hợp tải trọng).
- Thiếu các mảng cấu kiện thực chiến: Kết cấu thép hình (dầm I/H, đường hàn, bản mã chân cột), Móng nông (TCVN 9362), Ván khuôn thi công (TCVN 4453), Hố đào sâu.

---

## 2. Kế thừa Thuật toán từ Hệ sinh thái Skills Hiện hữu

Chúng ta không bắt đầu từ con số 0 mà kế thừa trực tiếp từ các thư viện Python chuyên sâu đã được phát triển và kiểm chứng trong `.agents/skills/`:

| Nguồn Skill | Module thuật toán sẵn sàng kế thừa | Đường dẫn tham chiếu |
|:---|:---|:---|
| **Structural_Design_Engineer** | • `calc_rc_section.py`: Cốt kép $A_s, A_s'$, cắt $V_{Rd,c}, V_{Rd,s}$<br>• `calc_rc_column.py`: Cột nén lệch tâm xiên (Bresler & P-M)<br>• `calc_slab.py`: Sàn 1 phương, 2 phương (Marcus/Pigeaud)<br>• `calc_punching_shear.py`: Chọc thủng sàn nấm & đài cọc<br>• `calc_crack_width.py`: Bề rộng khe nứt $a_{crc}$ ngắn & dài hạn<br>• `calc_steel_beam_tcvn.py`: Dầm thép chữ I/H, ổn định tổng thể $\varphi_b$<br>• `calc_weld_tcvn.py`: Đường hàn góc & đối đầu TCVN 5575<br>• `calc_steel_connection_tcvn.py`: Bản mã chân cột & bu lông neo | `.agents/skills/Structural_Design_Engineer/scripts/` |
| **SKILL_GEOTECH** | • `calc_base_heave.py`: Ổn định bùng đáy hố đào sâu<br>• `calc_strut_capacity.py`: Thanh chống Strut ống thép<br>• `calc_waling_beam_capacity.py`: Dầm văng Waling beam H-đôi<br>• `calc_soil_params_hs.py` & `calc_spt_correlations.py`<br>• Móng nông $R_{tc}, R_{td}$ theo TCVN 9362:2012 | `.agents/skills/SKILL_GEOTECH/calculators/` |
| **SKILL_TEMPWORKS** | • `calc_formwork_slab.py`: Ván khuôn sàn & độ võng $L/400$<br>• `calc_formwork_column.py`: Áp lực ngang bê tông tươi $P_{\max}$<br>• `calc_shoring_system.py`: Hệ giàn giáo và cây chống | `.agents/skills/SKILL_TEMPWORKS/calculators/` |
| **Cost_Estimator** | • `boq_extractor.py`: Benchmark hàm lượng thép $\text{kg/m}^3$<br>• Value Engineering rules & Cost impact assessment | `.agents/skills/Cost_Estimator/` |
| **Design_Evaluation** | • Tiêu chuẩn ổn định: P-Delta ($\theta \le 0.3$), Lật ($K_{ot} \ge 1.5$), Trượt ($K_{sl} \ge 1.3$), Chuyển vị lệch tầng ($h/500$) | `.agents/skills/Design_Evaluation/` |

---

## 3. Kiến trúc Đề xuất: 4 Trụ cột Nâng cấp Toàn diện

### TRỤ CỘT A: HỆ THỐNG TRA CỨU & TÍCH LŨY TẢI TRỌNG (LOADS MATRIX ENGINE)
1. **Module A1 — Bộ tích lũy Tĩnh tải hoàn thiện (Dead Load Builder):**
   - Cho phép chọn các lớp hoàn thiện sàn (gạch, vữa, trần, MEP, sàn BTCT) $\rightarrow$ tự động tính tĩnh tải $g_k, g_d$ ($\text{kN/m}^2$).
   - Tính tải trọng tường xây trên dầm (chiều cao tầng, chiều dày 100/200, loại gạch rỗng/đặc, tỷ lệ mở cửa) $\rightarrow$ tải phân bố $q_w$ ($\text{kN/m}$).
2. **Module A2 — Bảng tra Hoạt tải Toàn diện (Live Load Database - TCVN 2737:2023 Bảng 4):**
   - Đầy đủ hơn 20 nhóm phòng chức năng.
   - Hiển thị tự động hệ số độ tin cậy $\gamma_f$, hệ số chiết giảm diện tích $\alpha_A$, số tầng $\alpha_n$, và hệ số tổ hợp $\psi_0, \psi_1, \psi_2$.
3. **Module A3 — Tính Gió TCVN 2737:2023 Tĩnh & Động Nâng cao:**
   - Phân bố áp lực lên các diện nhà (đón gió $+0.8$, khuất gió $-0.5$, mặt bên $-0.7$, mái dốc).
   - Kể đến thành phần gió động (Dynamic wind) khi $H > 40\text{ m}$ dựa trên chu kỳ dao động riêng $T_1$ theo Phụ lục F.
4. **Module A4 — Bộ tạo Tổ hợp Tải trọng Tự động (Load Combination Engine):**
   - Kỹ sư nhập $D, L, W_x, W_y, E_x, E_y \rightarrow$ app sinh tự động bao tổ hợp ULS (Cơ bản 1, Cơ bản 2, Đặc biệt) và SLS, trích xuất Max/Min envelope.

### TRỤ CỘT B: THIẾT KẾ BÊ TÔNG CỐT THÉP CHUYÊN SÂU (ADVANCED RC ENGINE)
1. **Module B1 — Dầm BTCT Toàn diện (Uốn Cốt kép, Cắt Cốt đai, Uốn-Xoắn):**
   - Tự động chuyển cốt đơn $\rightarrow$ cốt kép ($A_s, A_s'$) khi $\alpha_m > \alpha_R$.
   - Tính toán cốt đai chịu cắt $V_{Rd,c}, V_{Rd,s}$ và bước đai $s_{sw}$.
   - Tính cốt thép dọc và đai chống xoắn $T$.
2. **Module B2 — Cột BTCT Nén Uốn Lệch tâm Xiên (Biaxial Column):**
   - Phương pháp tương tác nghịch đảo Bresler $\frac{1}{N} = \frac{1}{N_x} + \frac{1}{N_y} - \frac{1}{N_0}$.
   - Trực quan hóa đường cong tương tác $P-M$.
3. **Module B3 — Bản sàn BTCT 1 phương & 2 phương:**
   - Phân loại $\lambda = L_2 / L_1$, tra bảng Marcus / Pigeaud, tính thép nhịp và gối.
4. **Module B4 — Kiểm toán Chọc thủng Sàn nấm & Đài cọc (Punching Shear):**
   - Tính toán theo tháp đâm thủng 45° TCVN 5574:2018 Điều 8.1.5.
5. **Module B5 — Kiểm toán Trạng thái Giới hạn 2: Bề rộng Khe nứt & Độ võng (SLS):**
   - Tính $a_{crc,1}, a_{crc,2} \le 0.3\text{ mm}$ theo Điều 8.2 và độ võng dầm/sàn.

### TRỤ CỘT C: KẾT CẤU THÉP & LIÊN KẾT (ADVANCED STEEL ENGINE)
1. **Module C1 — Dầm Thép Hình Chữ I/H:**
   - Kiểm tra bền uốn $M$, cắt $V$, ổn định tổng thể dầm $\varphi_b$ theo Phụ lục E TCVN 5575:2024, ổn định cục bộ cánh và bụng.
2. **Module C2 — Đường hàn Kỹ thuật (Weld Design):**
   - Kiểm tra đường hàn góc (tiết diện kim loại que hàn $f_{wf}$ và kim loại cơ bản $f_{ws}$) và đường hàn đối đầu.
3. **Module C3 — Liên kết Chân cột & Bản mã (Base Plate & Anchor Bolts):**
   - Tính bề dày bản mã $t_p$, ứng suất ép mặt móng bê tông $\sigma_c \le R_{b,loc}$, và lực nhổ bu lông neo.

### TRỤ CỘT D: ĐỊA KỸ THUẬT & BIỆN PHÁP THI CÔNG (GEOTECH & TEMPWORKS)
1. **Module D1 — Thiết kế Móng Nông (Đơn & Băng) theo TCVN 9362:2012:**
   - Sức chịu tải $R$ theo công thức (15), kiểm tra $P_{tb} \le R, P_{\max} \le 1.2R, P_{\min} \ge 0$, tính thép đáy móng.
2. **Module D2 — Kiểm tra Hố đào Sâu & Hệ Giằng chống:**
   - Bùng đáy hố đào (Base Heave $F_s \ge 1.5$), sức chịu tải thanh chống ống thép Strut và dầm văng Waling beam.
3. **Module D3 — Thiết kế Ván khuôn & Cây chống Sàn/Cột (TCVN 4453):**
   - Ván phủ phim, sườn phụ, sườn chính, độ võng thi công $\le L/400$, áp lực ngang bê tông tươi $P_{\max}$.
4. **Module D4 — Đánh giá Hàm lượng Thép & Chi phí CAPEX:**
   - Tự động tính chỉ số $\text{kg/m}^3$ bê tông, so sánh Value Engineering.

---

## 4. Đề xuất Phân chia Triển khai giữa Gemini & Claude (Division of Labor)

Để tối ưu hóa năng lực thế mạnh của cả hai Agent:

| Agent đảm nhiệm | Khối lượng & Nhiệm vụ Phân công | Lý do / Thế mạnh |
|:---|:---|:---|
| **Gemini Antigravity**<br>*(Lead System Architect & Frontend Lead)* | **1. Trụ cột A (Tải trọng):** Xây dựng Module A1 (Dead Load Builder) & Module A2 (Live Load Database Bảng 4).<br>**2. Giao diện & Trực quan hóa:** Xây dựng component vẽ mặt cắt dầm/cột/móng 2D SVG động theo tỷ lệ thực.<br>**3. Tích hợp UI/UX & Navigation:** Mở rộng giao diện `InteractiveCalculators.jsx`, tổ chức các tab chuyên đề mới.<br>**4. SKILL_BRIDGE & Xuất Thuyết minh A4:** Cập nhật schema handoff JSON v2.2.0 và mẫu in A4 tương thích các bài toán mới. | Thế mạnh xử lý tương tác trực tiếp với codebase, CSS token, giao diện React SPA, in ấn PDF và kết nối DOM. |
| **Claude Code**<br>*(Senior Algorithm & TCVN Auditor)* | **1. Trụ cột B (BTCT Nâng cao):** Phát triển thuật toán Module B1 (Dầm cốt kép & Cốt đai $V_{Rd,c}, V_{Rd,s}$) và Module B2 (Cột nén lệch tâm xiên Bresler P-M).<br>**2. Trụ cột A3 & A4 (Gió Động & Tổ hợp):** Thuật toán tính thành phần động của gió theo Phụ lục F TCVN 2737:2023 & Trình sinh tổ hợp Envelope ULS/SLS.<br>**3. Trụ cột C1 & C2 (Kết cấu Thép):** Chuyển hóa `calc_steel_beam_tcvn.py` và `calc_weld_tcvn.py` sang JavaScript.<br>**4. Kiểm toán Độc lập (QA/QC):** Viết bổ sung các test suite trong `verify_calculators.mjs` và kiểm chứng chéo sai số toán học. | Thế mạnh về tư duy giải thuật cơ học kết cấu, đối chiếu tiêu chuẩn TCVN, viết code toán học chặt chẽ và peer review. |

---

## 5. Lộ trình Triển khai Đề xuất

- **Giai đoạn 1 (Quick Wins - Ưu tiên hàng đầu):**
  - Gemini: Xây dựng Module A1 (Dead Load Builder sàn/tường) + Module A2 (Live Load Database).
  - Claude: Phát triển Engine tính Dầm cốt kép & Cốt đai chịu cắt (Module B1) trong `calculatorEngines.js`.
  - Hai bên phối hợp ráp giao diện và viết test suite xác minh.
- **Giai đoạn 2 (Kết cấu Thép & Cột BTCT):**
  - Claude: Phát triển Engine Cột nén lệch tâm xiên (B2) + Dầm thép & Đường hàn (C1, C2).
  - Gemini: Xây dựng Component trực quan hóa 2D SVG (Mặt cắt dầm, mặt cắt cột, biểu đồ tương tác P-M).
- **Giai đoạn 3 (Địa kỹ thuật, Hố đào & Ván khuôn):**
  - Móng nông TCVN 9362 (D1), Chọc thủng (B4), Ván khuôn thi công (D3), Hố đào sâu (D2).

---

## 6. Yêu cầu Phản hồi & Đánh giá từ Claude Code

Kính chuyển Claude Code xem xét và phản hồi các nội dung sau:
1. **Đánh giá về tính khả thi:** Độ phức tạp của các thuật toán đề xuất (đặc biệt là cột lệch tâm xiên Bresler và gió động Phụ lục F) khi chạy thuần túy phía Client (JavaScript trên trình duyệt).
2. **Góp ý về phạm vi (Scoping):** Cần tinh chỉnh, thêm bớt bài toán nào trong Giai đoạn 1 để mang lại giá trị thực tiễn cao nhất cho kỹ sư kết cấu?
3. **Xác nhận phân chia công việc:** Thống nhất bảng phân công nhiệm vụ và cam kết mốc tiến độ bàn giao mã nguồn.

*Ghi nhận tại Bus:* `DUAL_AGENT_BUS.json` (v6.0.0).



---

## 7. BIÊN BẢN NGHIỆM THU HOÀN THÀNH GIAI ĐOẠN 1 (PHASE 1 CLOSURE)

**Thời điểm:** 2026-11-01T15:30:00+07:00  
**Đại diện tham gia:** Gemini Antigravity (Lead System Architect) & Claude Code (Senior Structural Algorithm Engineer)  
**Trạng thái Stage Gate:** `PHASE1_UPGRADE_100_PERCENT_COMPLETE_ALL_10_MODULES_VERIFIED_AND_PUSHED` (Bus v6.2.0)

### 7.1 Kết quả Triển khai Thực tế
1. **Claude Code Đã Bàn giao & Kiểm định:**
   - **Mô-đun 7 (B1):** Dầm BTCT Cốt kép & Cắt toàn diện (`calculateRCBeamAdvanced`) — tự động chuyển đổi cốt đơn sang cốt kép khi $lpha_m > lpha_R$, kiểm tra dải nghiêng bê tông $V_{strut} = 0.3 R_b b h_0$, tính toán cốt đai chịu cắt $V_{Rd,c} + V_{Rd,s}$.
   - **Mô-đun 8 (A4):** Trình tạo Tổ hợp Tải trọng ULS/SLS & Bao Nội lực Envelope (`calculateLoadCombination`) — 4 tổ hợp cơ bản + tổ hợp đặc biệt động đất, tự động tìm $M_{env,max}, M_{env,min}$.
   - **Mô-đun 9 (B4):** Kiểm toán Chọc thủng Sàn nấm & Đài cọc (`calculatePunchingShear`) — chu vi tới hạn góc $45^\circ$, điều kiện biên cột giữa/biên/góc, xét uốn 2 phương mômen và cốt đai gia cường.
   - **Test Suites Độc lập:** `verify_advanced_modules.mjs` & `verify_cross_js_python.mjs` (Oracle đối chiếu Python skills đạt độ lệch $0.000\%$).
2. **Gemini Antigravity Đã Bàn giao & Tích hợp:**
   - **Mô-đun 10 (A1):** Tích lũy Tĩnh tải Sàn Hoàn thiện & Tường xây trên Dầm (`calculateDeadLoad` & `CalcDeadLoadBuilder.jsx`) — cấu tạo đa lớp tùy biến, 4 mẫu sàn định hình sẵn (Căn hộ, Văn phòng, Sàn mái), tính tải tường phân bố đều $q_w$ kèm trừ diện tích mở cửa sổ/cửa đi.
   - **Hệ thống Phụ lục A4 & Handoff:** Bổ sung trọn vẹn bộ sinh Thuyết minh Phụ lục A4 chuẩn Times New Roman / BKTECHS (`generateRCBeamAdvancedPhuLuc`, `generateLoadComboPhuLuc`, `generatePunchingPhuLuc`, `generateDeadLoadPhuLuc`) và liên kết Modal vào cả 4 mô-đun mới.
   - **Tích hợp Trang chủ & Tabs:** Cập nhật `InteractiveCalculators.jsx` hỗ trợ đầy đủ 10 mô-đun với giao diện tab lọc mượt mà, layout 4 tầng chuẩn mực.
   - **Bảo chứng Chất lượng:** 29/29 tests PASS $100\%$, 0 lỗi ESLint, build Vite hoàn thành trong 583ms.
   - **Đồng bộ & Lưu trữ:** Đồng bộ 100% sang thư mục mirror Downloads và đã commit/push lên GitHub (`commit 436283d`, nhánh `main`).


---

## 8. CHIẾN LƯỢC TOÀN DIỆN: ÁNH XẠ 1-1 TỪ LÝ THUYẾT (CHƯƠNG 3–7) SANG BỘ CÔNG CỤ TÍNH TOÁN

**Thời điểm ban hành:** 2026-11-01T15:45:00+07:00  
**Căn cứ chỉ đạo từ Người dùng:** Mở rộng và phát triển tính toán tương tự cách trình bày lý thuyết: Các loại tải trọng tổ hợp, Cấu kiện BTCT (Dầm, Sàn, Cột, Vách), Kết cấu thép và Kiểm tra ổn định tải trọng công trình.  
**Trạng thái Stage Gate:** `STRATEGIC_THEORY_TO_CALCULATOR_EXPANSION_BLUEPRINT_APPROVED` (Bus v6.3.0)

### 8.1 Ma trận Ánh xạ Giữa Lý thuyết & Máy tính (Theory-to-Engine Mapping)

| Phân hệ Lý thuyết | Mã Trụ cột | Các Mô-đun Đã có (Phase 1) | Các Mô-đun Mục tiêu Tiếp theo (Phase 2 & 3) | Nguồn Thuật toán Đối chiếu |
|---|:---:|---|---|---|
| **Chương 3: Tải trọng & Tổ hợp** | **Trụ cột 1** | • 1.1 Tĩnh tải sàn & tường (A1)<br>• 1.2 Chiết giảm hoạt tải<br>• 1.3 Tải gió W₀, k(z)<br>• 1.4 Tổ hợp ULS/SLS Envelope (A4) | • 1.5 Tra cứu hoạt tải công năng (Bảng 4 TCVN 2737:2023)<br>• 1.6 Tải trọng gió động theo Phụ lục F<br>• 1.7 Phổ thiết kế Động đất TCVN 9386 ($a_g, q, S_d$) | `TCVN 2737:2023`<br>`TCVN 9386:2025` |
| **Chương 4: Cấu kiện BTCT** | **Trụ cột 2** | • 2.1 Cốt thép dầm đơn<br>• 2.2 Dầm cốt kép & cắt (B1)<br>• 2.3 Chọc thủng sàn nấm (B4)<br>• 2.4 Neo & nối cốt thép | • **2.5 Cột BTCT nén lệch tâm xiên Bresler**<br>• **2.6 Ô bản sàn BTCT 2 phương (Marcus/Pigeaud)**<br>• **2.7 Vách BTCT nén uốn & Cột biên (Boundary Elements)**<br>• **2.8 Kiểm toán Võng & Vết nứt SLS ($a_{crc}$)** | `calc_rc_column.py`<br>`calc_slab.py`<br>`calc_rc_wall.py`<br>`calc_crack_width.py` |
| **Chương 5: Cấu kiện Thép** | **Trụ cột 3** | • 3.1 Bu lông cường độ cao 5575 | • **3.2 Dầm thép hình I / H chịu uốn, cắt & Ổn định LTB**<br>• **3.3 Liên kết Đường hàn góc & đối đầu**<br>• 3.4 Bản mã chân cột Base Plate | `calc_steel_beam_tcvn.py`<br>`calc_weld_tcvn.py`<br>`calc_steel_connection_tcvn.py` |
| **Chương 6: Ổn định Tổng thể** | **Trụ cột 4** | *(Mới quy hoạch)* | • **4.1 Kiểm tra Hiệu ứng P-Delta ($	heta$)**<br>• **4.2 Kiểm toán Ổn định Chống lật ($K_{lat} \ge 1.5$)**<br>• **4.3 Kiểm toán Ổn định Chống trượt ($K_{truot} \ge 1.2$)**<br>• **4.4 Kiểm tra Chuyển vị đỉnh & Lệch tầng** | `GlobalStability.jsx`<br>`TCVN 2737 / 5574`<br>`policy_engine.py` |
| **Chương 7: Nền móng** | **Trụ cột 5** | • 5.1 Sức chịu tải cọc SPT (Meyerhof) | • 5.2 Móng đơn nông BTCT (Ứng suất đáy, lún $S$, chọc thủng)<br>• 5.3 Sức kháng cọc theo chỉ tiêu cơ lý đất nền | `calc_foundation_pile.py`<br>`TCVN 9362:2012` |

### 8.2 Phân công Trách nhiệm Giai đoạn 2 (Phase 2 Allocation)
- **Claude Code (Lead Algorithm Engineer):**
  - Chuyển ngữ và đóng gói các script Python sang JavaScript thuần trong `src/services/calculatorEngines.js`:
    1. `calculateRCColumnBiaxial`: Cột nén lệch tâm phẳng & xiên theo công thức tương tác Bresler $1/N = 1/N_x + 1/N_y - 1/N_0$.
    2. `calculateTwoWaySlab`: Tra bảng hệ số mômen Marcus/Pigeaud theo tỷ số nhịp $L_y/L_x$ và điều kiện ngàm/khớp 4 cạnh.
    3. `calculateGlobalStability`: Đóng gói bộ 4 kiểm tra P-Delta, Chống lật, Chống trượt, Chuyển vị lệch tầng.
    4. `calculateSteelBeamWeld`: Dầm thép I chịu uốn cắt + Liên kết đường hàn TCVN 5575:2024.
  - Viết test suites xác minh độc lập và cross-check với các oracle Python.
- **Gemini Antigravity (Lead System Architect):**
  - Xây dựng các UI component React 4 tầng tương ứng: `CalcRCColumn.jsx`, `CalcTwoWaySlab.jsx`, `CalcGlobalStabilityCheck.jsx`, `CalcSteelBeamWeld.jsx`.
  - Tích hợp động cơ sinh Phụ lục A4 (`generatePhuLucDocument`) và Handoff JSON (`buildSkillBridgePayload`) cho toàn bộ các mô-đun mới.
  - Cập nhật Category Pills và Catalog Dashboard trên `InteractiveCalculators.jsx`.
