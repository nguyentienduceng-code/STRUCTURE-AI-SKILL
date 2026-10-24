# BÁO CÁO KIỂM TOÁN ĐỘC LẬP & ĐẶC TẢ BẢN VÁ KỸ THUẬT (v7.0 → v7.1)

## INDEPENDENT LEAD AUDIT REPORT & PATCH SPECIFICATION — DÀNH CHO ANTIGRAVITY IDE

> **Ngày kiểm toán:** 2026-10-18T07:56:00+07:00 **Đơn vị kiểm toán:** Argon — Independent Lead Auditor **Hồ sơ đầu vào:** [ARGON\_AUDIT\_DOSSIER.md](https://drive.google.com/file/d/12CjhG7mfpNsq5r67gxfmm7JlE5nrOfs1/view?usp=drivesdk) (v7.0) **Đích nhận bàn giao:** Antigravity IDE (`.agents/docs/ARGON_AUDIT_RESPONSE_v7.0.md`) **Mục đích:** Cung cấp kết quả rà soát độc lập, danh mục lỗi phát hiện ở cấp độ dòng lệnh (line-level bugs), mã nguồn bản vá (patch diffs) và kịch bản kiểm thử (unit tests) để Antigravity tự động xác minh và nâng cấp hệ thống lên **v7.1**.

## 1\. TỔNG QUAN KẾT QUẢ KIỂM TOÁN (EXECUTIVE AUDIT SUMMARY)

| Hạng mục Kiểm toán | File / Module trọng tâm | Trạng thái hiện tại | Mức độ Rủi ro | Kết luận & Hành động yêu cầu |
| :---- | :---- | :---- | :---- | :---- |
| **1A. Công thức Neo & Nối chồng BTCT** | [calc\_anchorage\_lap.py](https://drive.google.com/file/d/1HBZ9vnjXOxeGgn5fYZZRMzDf2Dzsi0LP/view?usp=drivesdk) | Đúng bản chất toán học cơ sở nhưng **sai số hiệu CT/Mục** và thiếu **7 ngoại lệ cơ học** | **CRITICAL (P0)** | Vá lỗi trích dẫn sang CT (255)–(259); bổ sung hệ số nối chồng cùng tiết diện \$\\alpha \= 2.0\$, quy định kháng chấn, \$R\_{sc}\$ cho CB500-V và kiểm soát biên vật liệu. |
| **1B. Danh mục Tiêu chuẩn Locked** | [STANDARDS\_LOCK.md](https://drive.google.com/file/d/1D6DiH3SQIWoRtDaVQW_BXtAxwqZNcArZ/view?usp=drivesdk), [INDEX\_QUICK.md](https://drive.google.com/file/d/1CF_3eIM3uRYNZTDj0KD8sCxvWtjaM5O5/view?usp=drivesdk) | Khóa 15 tiêu chuẩn nhưng còn 1 quy chuẩn hết hiệu lực (`QCVN 01:2012`) & lệch whitelist | **MEDIUM (P2)** | Cập nhật `QCVN 01:2012` lên [QCVN 01:2021/BXD](https://sxd.laocai.gov.vn/quy-chuan-xay-dung); đồng bộ hậu tố [Sửa đổi 1:2023 QCVN 06:2022/BXD](https://thuvienphapluat.vn/van-ban/Tai-nguyen-Moi-truong/Thong-tu-09-2023-TT-BXD-sua-doi-1-2023-QCVN-06-2022-BXD-an-toan-chay-cho-nha-cong-trinh-583536.aspx) và cập nhật whitelist trong `confidence_score.py`. |
| **2A. Cơ sở dữ liệu Từ khóa (378 Keywords)** | [keyword\_database.json](https://drive.google.com/file/d/1Zipf_hmwIHjmC3LT6hyJUyMjcyyfmGNI/view?usp=drivesdk) | **Lỗi Duplicate Key** `"SKILL_TEMPWORKS"` làm ghi đè mất 24 mục từ khóa & anti-keywords | **HIGH (P1)** | Gộp 2 object `"SKILL_TEMPWORKS"` (dòng 241 & dòng 316\) thành 1 object duy nhất; chuyển danh từ chung (`"thép dầm"`, `"thép cột"`) của SDE xuống secondary. |
| **2B. Bộ phân loại Intent & Tie-breaker** | [intent\_classifier.py](https://drive.google.com/file/d/15aeF4hCK8-3Latms5RAT0Ynr7uL0_kCa/view?usp=drivesdk) | Chuẩn hóa `score / max_score` khiến top-1 luôn đạt `confidence = 1.0`; thiếu nhánh `TB-03` | **HIGH (P1)** | Sửa công thức tính `confidence` theo ngưỡng bão hòa điểm tuyệt đối; bổ sung xử lý `TB-03` khi cả SDE và DE cùng khớp primary keywords. |
| **3A. Phân vùng ngưỡng \$\\eta\$ & Triggers** | [policy\_engine.py](https://drive.google.com/file/d/1ou_l6Fwo2AC1Gq-mUWVcS4wyYWU-0OIE/view?usp=drivesdk) | Xét `TRIGGER_VE` (\$\\eta \\le 0.70\$) trước `PASS_WARNING` (\$\\eta \> 0.90\$) làm nuốt cảnh báo sát ngưỡng | **CRITICAL (P0)** | Đảo thứ tự ưu tiên trong `decide_eta()`: xét `REPAIR` (\$\\eta \> 1.00\$) \$\\rightarrow\$ `PASS_WARNING` (\$0.90 \< \\eta \\le 1.00\$) \$\\rightarrow\$ `TRIGGER_VE` (khi \$\\max(\\eta) \\le 0.70\$). |
| **3B. Cơ chế Veto Multiplier (v2.0)** | [confidence\_score.py](https://drive.google.com/file/d/1dtcfj2-l8cWx6EYD_BY_5_7fNFybxoSS/view?usp=drivesdk) | **Lỗi Case-Sensitivity** (`standard_method` vs `Standard_Method`) gây Veto nhầm 100% output thật | **CRITICAL (P0)** | Hỗ trợ đọc không phân biệt hoa/thường cho `Standard_Method` và `Calculation_Logs`; sửa điểm `not logs` từ `0.5` về `0.0` để không lọt lưới Veto. |

## 2\. ĐIỂM MẠNH KIẾN TRÚC ĐÃ ĐƯỢC XÁC MINH (VERIFIED STRENGTHS)

1. **Thực thi Toán học Xác định (Deterministic Math) & Code hóa Quy tắc (Policy-as-Code)**: Việc tách biệt hoàn toàn tầng suy luận ngôn ngữ của LLM với tầng tính toán số học qua các script Python độc lập và [policy\_engine.py](https://drive.google.com/file/d/1ou_l6Fwo2AC1Gq-mUWVcS4wyYWU-0OIE/view?usp=drivesdk) (36 quy tắc thực thi tự động) triệt tiêu hiệu quả hiện tượng ảo giác số học và trôi quy tắc trong các phiên làm việc dài.  
2. **Kiến trúc Phòng thủ Đa lớp (Multi-Layer Quality Gates)**: Hệ thống thiết lập chuỗi kiểm soát chặt chẽ từ `Pre-Execution Approval Gate` ([test\_approval\_gate.py](https://drive.google.com/file/d/1BwpAaU5yjDB_xMKhtXkZc3WIR-UPlnLs/view?usp=drivesdk)) \$\\rightarrow\$ `Confidence Score Veto v2.0` ([confidence\_score.py](https://drive.google.com/file/d/1dtcfj2-l8cWx6EYD_BY_5_7fNFybxoSS/view?usp=drivesdk)) \$\\rightarrow\$ `SKILL_VERIFY` (với ma trận dung sai phân hóa chuẩn xác theo mức độ nhạy cảm cơ học: \$\\eta \= 3%\$, Nội lực \$= 5%\$, diện tích cốt thép chọn thực tế \$A\_s \= 12%\$) \$\\rightarrow\$ `Review Gate` bắt buộc trước khi xuất hồ sơ ([AGENTS.md](https://drive.google.com/file/d/1UOkKPgkiqUCUh1iNsnq53fGzDrLNZPPx/view?usp=drivesdk)).  
3. **Cơ chế Quản trị Phiên bản Tiêu chuẩn & Known Gaps Minh bạch**: [STANDARDS\_LOCK.md](https://drive.google.com/file/d/1D6DiH3SQIWoRtDaVQW_BXtAxwqZNcArZ/view?usp=drivesdk) phân định rõ ràng phiên bản tiêu chuẩn dùng cho hồ sơ mới và phiên bản cũ dùng để đối chiếu, đồng thời bắt buộc script khai báo trung thực trường `Standard_Method` thay vì tự ý gắn nhãn tiêu chuẩn mới lên công thức cũ.  
4. **Hệ thống Kiểm thử Hồi quy Tự động Tốc độ cao**: Bộ điều khiển [run\_all\_tests.py](https://drive.google.com/file/d/1ZUsqgyPNOkD0dyCRtAah6QT13L2LK93x/view?usp=drivesdk) và `sync_report.py` tạo nền tảng CI/CD nội bộ vững chắc, giúp phát hiện nhanh các sai lệch giữa tài liệu và mã nguồn.

## 3\. CHI TIẾT PHÁT HIỆN KIỂM TOÁN & ĐẶC TẢ BẢN VÁ CHO ANTIGRAVITY

### 3.1. Hạng mục 1A — Vá lỗi `calc_anchorage_lap.py` (TCVN 5574:2018 & TCVN 9386-1:2025)

* **Vị trí file:** `.agents/skills/Structural_Design_Engineer/scripts/calc_anchorage_lap.py` ([calc\_anchorage\_lap.py trên Drive](https://drive.google.com/file/d/1HBZ9vnjXOxeGgn5fYZZRMzDf2Dzsi0LP/view?usp=drivesdk))  
* **Căn cứ tiêu chuẩn đối chiếu trực tiếp:**  
  * [TCVN 5574:2018 (PDF gốc, trang 35, 46–47, 138–142)](https://drive.google.com/file/d/193EqIjOv_X6-oHMxYjQYl46LEvxl4tS9/view?usp=drivesdk)  
  * [TCVN 9386-1:2025 (PDF gốc, Điều 5.6.1–5.6.3, trang 113–115)](https://drive.google.com/file/d/1XBDC4Jw7HDpYDRA6hRVXOhahnha-dB-l/view?usp=drivesdk)

#### Danh sách 7 lỗi cần vá trong `calc_anchorage_lap.py`:

1. **Sai số hiệu công thức và điều khoản trích dẫn (Citation Lock Violation)**:  
   * Trong [TCVN 5574:2018 (PDF, trang 110–113)](https://drive.google.com/file/d/193EqIjOv_X6-oHMxYjQYl46LEvxl4tS9/view?usp=drivesdk), các công thức `(191)`, `(192)`, `(193)`, `(194)` thuộc **Mục 8.2.3.3.4 – 8.2.3.3.6** (tính độ cứng \$D\$ và mô men quán tính quy đổi \$I\_{red}\$ khi kiểm tra võng).  
   * Các công thức neo và nối cốt thép tại **Mục 10.3.5 và 10.3.6 (trang 138–142)** có số hiệu chính xác là:  
     * Chiều dài neo cơ sở \$L\_{0,an} \= \\frac{R\_s A\_s}{R\_{bond} u\_s}\$: **Mục 10.3.5.4 — Công thức (255) — Trang 139** (hiện đang ghi nhầm là `Mục 10.3.5.2 - CT (192)`).  
     * Cường độ bám dính tính toán \$R\_{bond} \= \\eta\_1 \\eta\_2 R\_{bt}\$: **Mục 10.3.5.4 — Công thức (256) — Trang 139** (hiện đang ghi nhầm là `Mục 10.3.5.2 - CT (191)`).  
     * Chiều dài neo tính toán \$L\_{an} \= \\alpha L\_{0,an} \\frac{A\_{s,cal}}{A\_{s,ef}}\$: **Mục 10.3.5.5 — Công thức (257) — Trang 140** (hiện đang ghi nhầm là `Mục 10.3.5.3 - CT (193)`).  
     * Chiều dài nối chồng tính toán \$L\_{lap} \= \\alpha L\_{0,an} \\frac{A\_{s,cal}}{A\_{s,ef}}\$: **Mục 10.3.6.2 — Công thức (259) — Trang 141** (hiện đang ghi nhầm là `Mục 10.3.6.3 - CT (194)`; thực tế Mục 10.3.6.3 ở trang 142 quy định về **nối cốt thép bằng hàn**).  
   * Trường `"Trang"` trong `Citation` đang để chuỗi rỗng `""`, cần điền đúng số trang (`"139"`, `"140"`, `"141"`, `"142"`) để tuân thủ Quy tắc 3 của [AGENTS.md](https://drive.google.com/file/d/1UOkKPgkiqUCUh1iNsnq53fGzDrLNZPPx/view?usp=drivesdk).  
2. **Thiếu hệ số \$\\alpha \= 2.0\$ và nội suy tuyến tính theo tỷ lệ thanh nối chồng trong cùng tiết diện tính toán**:  
   * Theo [TCVN 5574:2018 Mục 10.3.6.2 (trang 141–142)](https://drive.google.com/file/d/193EqIjOv_X6-oHMxYjQYl46LEvxl4tS9/view?usp=drivesdk), giá trị \$\\alpha \= 1.2\$ đối với cốt thép chịu kéo chỉ áp dụng khi tỷ lệ thanh cốt thép có gân được nối trong một tiết diện tính toán (đoạn \$1.3 L\_{lap}\$) **không vượt quá \$50%\$** (và không quá \$25%\$ đối với thép trơn).  
   * Khi nối tới \$100%\$ số thanh chịu kéo tại cùng một tiết diện (rất phổ biến ở thép chờ cột/vách), tiêu chuẩn bắt buộc lấy **\$\\alpha \= 2.0\$**; khi tỷ lệ nối nằm trong khoảng \$(50%, 100%\]\$ với thép gân (hoặc \$(25%, 100%\]\$ với thép trơn), hệ số \$\\alpha\$ phải lấy theo **nội suy tuyến tính**.  
3. **Thiếu quy định neo/nối trong vùng kháng chấn theo [TCVN 9386-1:2025 Điều 5.6 (trang 113–115)](https://drive.google.com/file/d/1XBDC4Jw7HDpYDRA6hRVXOhahnha-dB-l/view?usp=drivesdk)**:  
   * Điều 5.6.2.1(1): Khi tính neo hoặc nối chồng cốt thép cột trong vùng tới hạn kháng chấn, bắt buộc lấy tỷ số \$A\_{s,req}/A\_{s,prov} \= 1.0\$ (không được giảm chiều dài neo/nối theo diện tích thép bố trí dư).  
   * Điều 5.6.2.1(2): Khi cột chịu kéo trong tổ hợp tải trọng động đất, chiều dài neo phải **tăng thêm \$50%\$** (\$\\times 1.50\$).  
   * Điều 5.6.1(3): Trong kết cấu cấp dẻo cao (`DCH`), chiều dài neo của cốt thép dầm/cột vào nút khung phải tính từ điểm cách mặt trong của nút một đoạn \$5 d\_{bL}\$ (cần cộng thêm hoặc xuất cảnh báo cấu tạo rõ ràng).  
4. **Chưa chặn neo thẳng đối với thép trơn chịu kéo & chưa hỗ trợ giảm neo tối đa \$30%\$ khi có mấu neo/uốn móc**:  
   * Theo [TCVN 5574:2018 Mục 10.3.5.2 (trang 138\)](https://drive.google.com/file/d/193EqIjOv_X6-oHMxYjQYl46LEvxl4tS9/view?usp=drivesdk), neo thẳng (`end_type="straight"`) chỉ được phép dùng cho cốt thép có gân; thanh trơn (`CB240-T`, `CB300-T`) chịu kéo bắt buộc phải uốn móc, uốn chữ U hoặc hàn thanh ngang.  
   * Theo Mục 10.3.5.5 (trang 140\) và Mục 10.3.6.2 (trang 142), cho phép giảm chiều dài neo/nối đối với thép có gân có uốn đầu thanh hoặc hàn cốt ngang bổ sung nhưng giảm không quá \$30%\$.  
5. **Chưa chặn giới hạn đường kính nối chồng \$d\_s \> 40\\text{ mm}\$**:  
   * Theo [TCVN 5574:2018 Mục 10.3.6.2 (trang 141\)](https://drive.google.com/file/d/193EqIjOv_X6-oHMxYjQYl46LEvxl4tS9/view?usp=drivesdk), không cho phép nối chồng không hàn khi \$d\_s \> 40\\text{ mm}\$ (phải dùng nối hàn hoặc nối cơ khí coupler).  
6. **Thiếu giới hạn cường độ chịu nén \$R\_{sc} \= 400\\text{ MPa}\$ của `CB500-V` và thiếu mác thép `CB300-T` / dây thép vuốt nguội**:  
   * Theo [TCVN 5574:2018 Bảng 13 (trang 47\) & Mục 6.2.2.2 (trang 45\)](https://drive.google.com/file/d/193EqIjOv_X6-oHMxYjQYl46LEvxl4tS9/view?usp=drivesdk), với thép `CB500-V` (\$R\_s \= 435\\text{ MPa}\$), cường độ chịu nén tính toán dưới tác dụng ngắn hạn của tải trọng bị giới hạn ở \$R\_{sc} \= 400\\text{ MPa}\$. Ngoài ra cần bổ sung `CB300-T` (\$R\_s \= R\_{sc} \= 260\\text{ MPa}, \\eta\_1 \= 1.5\$) và dây thép kéo/vuốt nguội có gân (`Cold_Drawn_Deformed`, \$\\eta\_1 \= 2.0, R\_s \= 435\\text{ MPa}, R\_{sc} \= 380\\text{ MPa}\$).  
7. **Fallback ngầm cấp độ bền bê tông không nằm trong bảng về `B25` & thiếu hệ số điều kiện làm việc \$\\gamma\_{bi}\$**:  
   * Hiện tại `RB_MAP.get(concrete, 14.5)` và `RBT_MAP.get(concrete, 1.05)` chỉ có `B15`–`B40`. Khi `intent_classifier.py` quy đổi mác `M300` sang `"B22.5"` rồi truyền vào `calc_anchorage_lap.py`, hàm âm thầm lấy giá trị của `B25` (`1.05 MPa` thay vì `1.00 MPa`), vi phạm Quy tắc 4 (`No Hallucination`). Cần bổ sung đầy đủ `B12.5`, `B22.5`, `B45`, `B50`, `B55`, `B60` theo [TCVN 5574:2018 Bảng 7 (trang 35\)](https://drive.google.com/file/d/193EqIjOv_X6-oHMxYjQYl46LEvxl4tS9/view?usp=drivesdk), thêm tham số `gamma_b1` (mặc định `1.0` cho tải ngắn hạn, `0.9` cho tải tĩnh dài hạn theo Mục 6.1.2.3 trang 33), và raise `ValueError` (`E001`) nếu truyền mác vật liệu không hợp lệ.

#### Mã nguồn chuẩn hóa đề xuất cho `calc_anchorage_lap.py`:

\# \--- Cuong do vat lieu TCVN 5574:2018 Bang 7 (trang 35\) & Bang 13 (trang 47\) (MPa) \---

RB\_MAP \= {

    "B12.5": 7.5, "B15": 8.5, "B20": 11.5, "B22.5": 13.0, "B25": 14.5,

    "B30": 17.0, "B35": 19.5, "B40": 22.0, "B45": 25.0, "B50": 27.5,

    "B55": 30.0, "B60": 33.0

}

RBT\_MAP \= {

    "B12.5": 0.66, "B15": 0.75, "B20": 0.90, "B22.5": 1.00, "B25": 1.05,

    "B30": 1.15, "B35": 1.30, "B40": 1.40, "B45": 1.50, "B50": 1.60,

    "B55": 1.70, "B60": 1.80

}

RS\_TENSION\_MAP \= {

    "CB240-T": 210, "CB300-T": 260,

    "CB300-V": 260, "CB400-V": 350, "CB500-V": 435,

    "VR-I": 435  \# Day thep vuot nguoi co gan TCVN 6288:1997

}

RSC\_SHORT\_TERM\_MAP \= {

    "CB240-T": 210, "CB300-T": 260,

    "CB300-V": 260, "CB400-V": 350, "CB500-V": 400,  \# Bang 13 Chu thich 1: 400 MPa (ngan han)

    "VR-I": 380

}

def \_get\_eta\_1(rebar: str) \-\> float:

    """He so eta\_1 theo TCVN 5574:2018 Muc 10.3.5.4 \- CT (256) (Trang 139)"""

    if rebar \== "VR-I":

        return 2.0  \# Thep keo/can nguoi co gan

    return 2.5 if \_is\_deformed(rebar) else 1.5

def \_get\_alpha\_lap(stress\_type: str, rebar: str, splice\_ratio: float \= 0.5) \-\> float:

    """

    He so alpha cho noi chong theo TCVN 5574:2018 Muc 10.3.6.2 \- CT (259) (Trang 141-142).

    \- Chiu nen: alpha \= 0.9

    \- Chiu keo:

      \+ Thep co gan: splice\_ratio \<= 0.5 \-\> alpha \= 1.2; splice\_ratio \= 1.0 \-\> alpha \= 2.0 (noi suy tuyen tinh)

      \+ Thep tron (co moc/chu U): splice\_ratio \<= 0.25 \-\> alpha \= 1.2; splice\_ratio \= 1.0 \-\> alpha \= 2.0 (noi suy tuyen tinh)

    """

    if stress\_type \== "compression":

        return 0.9

    r \= max(0.0, min(1.0, float(splice\_ratio)))

    deformed \= \_is\_deformed(rebar)

    threshold \= 0.50 if deformed else 0.25

    if r \<= threshold:

        return 1.2

    return round(1.2 \+ (2.0 \- 1.2) \* (r \- threshold) / (1.0 \- threshold), 4\)

### 3.2. Hạng mục 1B — Đồng bộ Danh mục Tiêu chuẩn (`STANDARDS_LOCK.md` & `INDEX_QUICK.md`)

* **Vị trí file:** `.agents/skills/Design_Evaluation/STANDARDS_LOCK.md` ([STANDARDS\_LOCK.md trên Drive](https://drive.google.com/file/d/1D6DiH3SQIWoRtDaVQW_BXtAxwqZNcArZ/view?usp=drivesdk)) và `.agents/skills/Design_Evaluation/standards/INDEX_QUICK.md` ([INDEX\_QUICK.md trên Drive](https://drive.google.com/file/d/1CF_3eIM3uRYNZTDj0KD8sCxvWtjaM5O5/view?usp=drivesdk)).  
* **Các thay đổi bắt buộc:**  
  1. Thay thế `QCVN 01:2012` (đã hết hiệu lực) bằng [**QCVN 01:2021/BXD**](https://sxd.laocai.gov.vn/quy-chuan-xay-dung) (cột Phiên bản cũ ghi `QCVN 01:2019/BXD, QCVN 01:2012/BXD`).  
  2. Ghi thống nhất tên phiên bản An toàn cháy là [**QCVN 06:2022/BXD \+ Sửa đổi 1:2023**](https://thuvienphapluat.vn/van-ban/Tai-nguyen-Moi-truong/Thong-tu-09-2023-TT-BXD-sua-doi-1-2023-QCVN-06-2022-BXD-an-toan-chay-cho-nha-cong-trinh-583536.aspx) (theo Thông tư 09/2023/TT-BXD) trên cả `STANDARDS_LOCK.md`, `BAO_CAO_PHAT_TRIEN_DIEU_PHOI_AI.md` và `ARGON_AUDIT_DOSSIER.md`.  
  3. Bổ sung `Structural_Design_Engineer/scripts/calc_anchorage_lap.py` và `Structural_Design_Engineer/scripts/calc_weld_tcvn.py` vào Bảng 2 (Kiểm soát trạng thái khớp tiêu chuẩn của các script) trong [STANDARDS\_LOCK.md](https://drive.google.com/file/d/1D6DiH3SQIWoRtDaVQW_BXtAxwqZNcArZ/view?usp=drivesdk).

### 3.3. Hạng mục 2A & 2B — Vá lỗi `keyword_database.json` và `intent_classifier.py`

* **Vị trí file:**  
  * `.agents/skills/Global_Dispatcher/scripts/keyword_database.json` ([keyword\_database.json trên Drive](https://drive.google.com/file/d/1Zipf_hmwIHjmC3LT6hyJUyMjcyyfmGNI/view?usp=drivesdk))  
  * `.agents/skills/Global_Dispatcher/scripts/intent_classifier.py` ([intent\_classifier.py trên Drive](https://drive.google.com/file/d/15aeF4hCK8-3Latms5RAT0Ynr7uL0_kCa/view?usp=drivesdk))

#### Lỗi 1: Trùng khóa JSON `"SKILL_TEMPWORKS"` trong `keyword_database.json`

* Trong [keyword\_database.json](https://drive.google.com/file/d/1Zipf_hmwIHjmC3LT6hyJUyMjcyyfmGNI/view?usp=drivesdk), `"SKILL_TEMPWORKS"` được khai báo ở dòng 241 (`"skill_id": "TEMP"`, đầy đủ 21 primary keywords, 10 secondary keywords, 9 regex patterns và 6 anti-keywords) nhưng lại bị khai báo lặp lần thứ hai ở dòng 316 (`"skill_id": "TW"`, chỉ có 9 primary keywords và `anti_keywords: []`).  
* **Bản vá:** Xóa khối `"SKILL_TEMPWORKS"` thứ hai (dòng 316–340) và hợp nhất các từ khóa riêng của khối thứ hai (`"giàn giáo"`, `"propping"`, `"reshoring"`, `"chống phụ"`, `"falsework"`) vào khối `"SKILL_TEMPWORKS"` thứ nhất, sau đó cập nhật lại `_meta.total_keywords`.

#### Lỗi 2: Nhầm lẫn Intent giữa `Design_Evaluation` (DE) và `Structural_Design_Engineer` (SDE)

* **Nguyên nhân 1:** Các danh từ chung `"thép dầm"`, `"thép cột"`, `"thép sàn"`, `"thép móng"` đang nằm trong `primary_keywords` (`+10` điểm) của `SDE`. Khi người dùng thuộc vai QLTK nhập *"Check thép dầm B1, thép cột C1 xem đạt TCVN không"*, `SDE` được cộng `+20` điểm từ 2 danh từ này và thắng `DE`.  
* **Nguyên nhân 2:** Regex `"(tính|kiểm tra)\\s+(bu lông|đường hàn|bản mã|neo)"` trong `SDE` bắt cả cụm từ `"kiểm tra bu lông / đường hàn / neo"` vốn thường xuất hiện trong công tác thẩm tra/nghiệm thu bản vẽ của `DE`.  
* **Nguyên nhân 3:** Trong [intent\_classifier.py (dòng 159–162)](https://drive.google.com/file/d/15aeF4hCK8-3Latms5RAT0Ynr7uL0_kCa/view?usp=drivesdk):  
    
  max\_score \= max(scores.values()) if scores else 1  
    
  normalized \= {k: v / max\_score for k, v in scores.items()}  
    
  Do chia cho `max_score`, bất kỳ skill nào đứng số 1 (dù chỉ khớp 1 secondary keyword `5.0` điểm) đều nhận `normalized = 1.0 >= HIGH_CONFIDENCE (0.85)`. Hệ thống không bao giờ trả về `MEDIUM` hay `LOW` khi có ít nhất 1 từ khóa khớp.  
    
* **Nguyên nhân 4:** Hàm `_apply_tie_breakers()` ([intent\_classifier.py, dòng 298–309](https://drive.google.com/file/d/15aeF4hCK8-3Latms5RAT0Ynr7uL0_kCa/view?usp=drivesdk)) chưa cài đặt rule `TB-03` (khi cả `sde_has_primary` và `de_has_primary` cùng `True`, cần kích hoạt pipeline `Structural_Design_Engineer → Design_Evaluation`).

#### Mã nguồn bản vá cho `intent_classifier.py`:

\# 1\. Chuẩn hóa điểm kết hợp ngưỡng bão hòa tuyệt đối (Absolute Saturation \= 15.0)

\# Chỉ đạt HIGH (\>= 0.85) khi có ít nhất 1 Primary \+ 1 Secondary (15đ) hoặc 2 Primary (20đ)

SATURATION\_SCORE \= 15.0

max\_score \= max(scores.values()) if scores else 0.0

if max\_score \> 0:

    saturation\_factor \= min(1.0, max\_score / SATURATION\_SCORE)

    normalized \= {k: (v / max\_score) \* saturation\_factor for k, v in scores.items()}

else:

    normalized \= {k: 0.0 for k in scores}

\# 2\. Bổ sung TB-03 trong classify() và \_apply\_tie\_breakers():

if sde\_has\_primary and de\_has\_primary and not pipeline\_result:

    pipeline\_result \= {

        "template": "design\_then\_review",

        "skills": \["Structural\_Design\_Engineer", "Design\_Evaluation"\],

        "description": "Auto-detected pipeline (TB-03): Tính toán thiết kế → Review/Thẩm tra",

        "trigger": "TB-03 (SDE\_keywords\_present AND DE\_keywords\_present)"

    }

### 3.4. Hạng mục 3A — Vá lỗi Thứ tự Ưu tiên Ngưỡng \$\\eta\$ và Trigger `POST-SDE-001` trong `policy_engine.py`

* **Vị trí file:** `.agents/tools/policy_engine.py` ([policy\_engine.py trên Drive](https://drive.google.com/file/d/1ou_l6Fwo2AC1Gq-mUWVcS4wyYWU-0OIE/view?usp=drivesdk))  
* **Phân tích lỗi 1 (`decide_eta` nuốt cảnh báo `W001`):**  
  * Tại dòng 129–182 của [policy\_engine.py](https://drive.google.com/file/d/1ou_l6Fwo2AC1Gq-mUWVcS4wyYWU-0OIE/view?usp=drivesdk), hàm `decide_eta()` kiểm tra `ve_items` (\$\\eta \\le 0.70\$) ở Bước 2 **trước khi** kiểm tra `max_eta > 0.90` ở Bước 3\.  
  * Khi truyền dict của 1 cấu kiện có nhiều nội lực như `{"eta_M": 0.96, "eta_V": 0.50}`, hàm thấy `eta_V = 0.50 <= 0.70` nên lập tức `return PolicyDecision(action=Action.TRIGGER_VE, status_code=StatusCode.VE_RECOMMENDED, color="🟢")` và **bỏ qua hoàn toàn việc `eta_M = 0.96` đang ở vùng nguy hiểm sát giới hạn (`0.90 < η <= 1.00`, mã `W001`)**.  
  * Về mặt cơ học kết cấu, một cấu kiện chịu uốn – cắt đồng thời có \$\\max(\\eta) \= 0.96\$ tuyệt đối **không có dự trữ chịu lực \$\> 30%\$** để giảm tiết diện (Value Engineering).  
* **Phân tích lỗi 2 (`POST-SDE-001` gây chạy tràn pipeline):**  
  * Tại dòng 219 và 443 của [policy\_engine.py](https://drive.google.com/file/d/1ou_l6Fwo2AC1Gq-mUWVcS4wyYWU-0OIE/view?usp=drivesdk), `POST-SDE-001` (`Structural_Design_Engineer → Design_Evaluation`) được gán `fired = True` vô điều kiện (`"always"`), mâu thuẫn với [AGENTS.md §18.2](https://drive.google.com/file/d/1UOkKPgkiqUCUh1iNsnq53fGzDrLNZPPx/view?usp=drivesdk) (sau SDE là `SKILL_VERIFY` rồi `SKILL_CALC_REPORT`, chỉ chuyển sang `Design_Evaluation` khi chạy pipeline thiết kế – thẩm tra hoặc lập tờ trình).

#### Mã nguồn bản vá cho `decide_eta()` trong `policy_engine.py`:

    \# 1\. Kiểm tra điều kiện REPAIR (Ưu tiên số 1 — Vi phạm trạng thái giới hạn η \> 1.00)

    failing\_items \= \[(name, val) for name, val in items if val \> 1.00\]

    if failing\_items:

        detail\_str \= ", ".join(\[f"{name}={val:.3f}" for name, val in failing\_items\[:3\]\])

        if len(failing\_items) \> 3:

            detail\_str \+= f" (+{len(failing\_items) \- 3} phần tử khác)"

        reasons.append(f"Có {len(failing\_items)} vị trí vượt ngưỡng chịu lực (η \> 1.00): {detail\_str}")

        rule\_sources.append("AGENTS.md §6 (η \> 1.00 \-\> KHÔNG ĐẠT)")

        return PolicyDecision(

            action=Action.REPAIR,

            status\_code=StatusCode.REPAIR\_REQUIRED,

            color="🔴",

            max\_eta=max\_eta,

            min\_eta=min\_eta,

            message=f"KHÔNG ĐẠT — η\_max \= {max\_eta:.3f} \> 1.00. Yêu cầu tăng tiết diện hoặc giải pháp gia cường.",

            reasons=reasons,

            triggers=\[\],

            rule\_sources=rule\_sources,

        )

    \# 2\. Kiểm tra cảnh báo sát ngưỡng (Ưu tiên số 2 — 0.90 \< max\_eta \<= 1.00)

    if max\_eta \> 0.90:

        high\_items \= \[(name, val) for name, val in items if val \> 0.90\]

        detail\_str \= ", ".join(\[f"{name}={val:.3f}" for name, val in high\_items\[:3\]\])

        reasons.append(

            f"Có {len(high\_items)} vị trí sát ngưỡng giới hạn (0.90 \< η \<= 1.00): {detail\_str}"

        )

        rule\_sources.append("AGENTS.md §17 (W001: Approaching threshold \> 90%)")

        return PolicyDecision(

            action=Action.PASS,

            status\_code=StatusCode.PASS\_WARNING,

            color="🟠",

            max\_eta=max\_eta,

            min\_eta=min\_eta,

            message=f"ĐẠT — η\_max \= {max\_eta:.3f} (0.90 \< η \<= 1.00). Đạt nhưng sát ngưỡng, cảnh báo lưu ý.",

            reasons=reasons,

            triggers=\[\],

            rule\_sources=rule\_sources,

        )

    \# 3\. Kiểm tra điều kiện TRIGGER\_VE (Khi không có phần tử nào \> 0.90 và tồn tại phần tử \<= 0.70)

    ve\_items \= \[(name, val) for name, val in items if val \<= 0.70\]

    if ve\_items:

        detail\_str \= ", ".join(\[f"{name}={val:.3f}" for name, val in ve\_items\[:3\]\])

        if len(ve\_items) \> 3:

            detail\_str \+= f" (+{len(ve\_items) \- 3} phần tử khác)"

        reasons.append(

            f"Phát hiện {len(ve\_items)} vị trí có η \<= 0.70 (dự trữ chịu lực \> 30%): {detail\_str}"

        )

        triggers.append("POST-DESIGN-02: Cost\_Estimator (Value Engineering)")

        rule\_sources.append("INTER\_SKILL\_TRIGGERS.md §POST-DESIGN-02")

        rule\_sources.append("AGENTS.md §17 (W002: VE possible)")

        return PolicyDecision(

            action=Action.TRIGGER\_VE,

            status\_code=StatusCode.VE\_RECOMMENDED,

            color="🟢",

            max\_eta=max\_eta,

            min\_eta=min\_eta,

            message=f"ĐẠT & AN TOÀN CAO — η\_min \= {min\_eta:.3f} \<= 0.70 (dự trữ \> 30%). Kích hoạt Cost\_Estimator để xem xét Value Engineering.",

            reasons=reasons,

            triggers=triggers,

            rule\_sources=rule\_sources,

        )

*(Lưu ý: Cập nhật đồng thời test case `test_dict_input_triggers_ve_when_element_has_low_eta` trong [test\_policy\_engine.py](https://drive.google.com/file/d/1lS-qNHltqy7IYMvFy9U8C1S7sqzirnHe/view?usp=drivesdk) — với `{"eta_M": 0.85, "eta_V": 0.55}` thì vẫn trả về `TRIGGER_VE` vì `max_eta = 0.85 <= 0.90`, nhưng bổ sung thêm test case `{"eta_M": 0.95, "eta_V": 0.55}` bắt buộc phải trả về `PASS_WARNING` `W001`\!).*

### 3.5. Hạng mục 3B — Vá lỗi Case-Sensitivity & Veto Logic trong `confidence_score.py`

* **Vị trí file:** `.agents/_SHARED/SHARED_CONTEXT/confidence_score.py` ([confidence\_score.py trên Drive](https://drive.google.com/file/d/1dtcfj2-l8cWx6EYD_BY_5_7fNFybxoSS/view?usp=drivesdk))  
* **Phân tích 3 lỗi nghiêm trọng:**  
  1. **Lỗi phân biệt chữ hoa/thường (Case-Sensitivity Mismatch):** Các script thực tế ([calc\_anchorage\_lap.py](https://drive.google.com/file/d/1HBZ9vnjXOxeGgn5fYZZRMzDf2Dzsi0LP/view?usp=drivesdk), [calc\_weld\_tcvn.py](https://drive.google.com/file/d/1GTgD1zpy_nesmTzGnuTNLzKb032A1D_C/view?usp=drivesdk), [calc\_steel\_beam\_tcvn.py](https://drive.google.com/file/d/1RPyMY3tOg1BVL9o_KHI_IYg3VoZsoWXE/view?usp=drivesdk)) đều xuất `"Standard_Method"` và `"Calculation_Logs"` (với các trường con `"Formula"`, `"Substitution"`, `"Result"`, `"Citation"` viết hoa chữ cái đầu theo đúng quy định tại [AGENTS.md §5](https://drive.google.com/file/d/1UOkKPgkiqUCUh1iNsnq53fGzDrLNZPPx/view?usp=drivesdk)). Ngược lại, `confidence_score.py` chỉ tìm `"standard_method"`, `"calculation_logs"`, `"formula"`, `"substitution"`, `"result"`, `"citation"` viết thường. Khi chạy `confidence_score.py` trên JSON thật của calculator, Veto `no_standards_cited` bắn nhầm 100% và trả về `0.0`.  
  2. **Lỗi lọt lưới Veto khi `calculation_logs` rỗng (`[]`):** Tại dòng 213–215, `if not logs: score = 0.5`, trong khi điều kiện Veto `low_log_consistency` là `calculation_consistency < 0.5`. Do `0.5 < 0.5` là `False`, một output hoàn toàn không có `Calculation_Logs` lại không bị Veto\!  
  3. **Thiếu tiêu chuẩn trong `_is_valid_standard()`:** Bổ sung đầy đủ 15 tiêu chuẩn từ [STANDARDS\_LOCK.md](https://drive.google.com/file/d/1D6DiH3SQIWoRtDaVQW_BXtAxwqZNcArZ/view?usp=drivesdk).

#### Mã nguồn bản vá cho `confidence_score.py`:

def \_get\_ci(d: dict, key: str, default=None):

    """Đọc giá trị từ dict không phân biệt chữ hoa/thường (Case-Insensitive Getter)."""

    if not isinstance(d, dict):

        return default

    if key in d:

        return d\[key\]

    key\_lower \= key.lower()

    for k, v in d.items():

        if str(k).lower() \== key\_lower:

            return v

    return default

* Trong `calculate_standard_compliance(self, data)`:  
  * Thay `data.get("standard_method", "")` bằng `_get_ci(data, "standard_method", "") or _get_ci(data, "Standard", "")`.  
  * Thay `data.get("calculation_logs", [])` bằng `_get_ci(data, "calculation_logs", [])`.  
  * Thay `log.get("citation")` bằng `_get_ci(log, "citation")`.  
  * Nếu thiếu cả `standard_method` và `citation_ratio == 0.0`, gán `score = 0.0` để rule `standard_score_zero` hoạt động đúng thiết kế.  
* Trong `calculate_calculation_consistency(self, data)`:  
  * Thay `data.get("calculation_logs", [])` bằng `_get_ci(data, "calculation_logs", [])`.  
  * Khi `if not logs:`, gán **`score = 0.0`** (thay vì `0.5`) để kích hoạt Veto `low_log_consistency` đúng quy tắc [AGENTS.md §5](https://drive.google.com/file/d/1UOkKPgkiqUCUh1iNsnq53fGzDrLNZPPx/view?usp=drivesdk) (*"Nếu script không có Calculation\_Logs → kết quả KHÔNG được đưa vào báo cáo"*).  
  * Thay `all(k in log for k in ["formula", "substitution", "result"])` bằng `all(_get_ci(log, k) is not None for k in ["formula", "substitution", "result"])`.  
* Trong Veto `data_field` check (dòng 311):  
  * Thay `value = data.get(field, "")` bằng `value = _get_ci(data, field, "")`.  
* Trong `_is_valid_standard(self, standard)`:  
    
  valid\_standards \= \[  
    
      "TCVN 5574:2018", "TCVN 5575:2024", "TCVN 5575:2012",  
    
      "TCVN 2737:2023", "TCVN 9386:2025", "TCVN 9386-1:2025", "TCVN 9386-5:2025",  
    
      "TCVN 10304:2025", "TCVN 9362:2012", "TCVN 5573:2025",  
    
      "TCVN 4453:1995", "TCVN 9351:2012",  
    
      "QCVN 01:2021", "QCVN 02:2022", "QCVN 03:2022", "QCVN 04:2021", "QCVN 06:2022",  
    
      "AASHTO", "ACI", "EC", "EN 199", "JIS", "Bowles", "Robertson"  
    
  \]

## 4\. KỊCH BẢN KIỂM THỬ BẮT BUỘC SAU KHI VÁ LỖI (POST-PATCH VERIFICATION SUITE)

Sau khi áp dụng các bản vá trên, Antigravity cần bổ sung và chạy xác nhận 6 bài kiểm thử biên (Boundary Unit Tests) sau đây:

1. **Test `calc_anchorage_lap.py` — Trích dẫn & Nối chồng 100% tiết diện:**  
   * Input: `dia=20, rebar="CB400-V", concrete="B30", stress_type="tension", splice_ratio=1.0`  
   * Kỳ vọng: `alpha_lap == 2.0`, `Citation["Dieu_Muc"] == "Muc 10.3.6.2"`, `Citation["Bang_Hinh"] == "CT (259)"`, `Citation["Trang"] == "141"`.  
2. **Test `calc_anchorage_lap.py` — Chặn neo thẳng thép trơn chịu kéo & đường kính nối chồng \$\> 40\\text{ mm}\$:**  
   * Input 1: `dia=12, rebar="CB240-T", stress_type="tension", end_type="straight"` \$\\rightarrow\$ Kỳ vọng: Cảnh báo hoặc lỗi cấu tạo bắt buộc uốn móc/chữ U theo Mục 10.3.5.2.  
   * Input 2: `dia=45, rebar="CB500-V"` \$\\rightarrow\$ Kỳ vọng: Cảnh báo cấm nối chồng không hàn cho \$d\_s \> 40\\text{ mm}\$ theo Mục 10.3.6.2.  
3. **Test `confidence_score.py` — Tương thích trực tiếp với output của `calc_anchorage_lap.py`:**  
   * Truyền trực tiếp dict trả về từ `calc_anchorage_lap()` (có khóa `"Standard_Method"` và `"Calculation_Logs"` viết hoa) vào `ConfidenceCalculator().calculate_overall(res)`.  
   * Kỳ vọng: `veto.triggered == False` và  `standard_compliance.score == 1.0`.  
4. **Test `confidence_score.py` — Veto khi `Calculation_Logs` rỗng (`[]`):**  
   * Input: `{"Standard_Method": "TCVN 5574:2018", "Calculation_Logs": []}`  
   * Kỳ vọng: `veto.triggered == True` (do `low_log_consistency`), `overall_score == 0.0`.  
5. **Test `policy_engine.py` — Ưu tiên `PASS_WARNING` trước `TRIGGER_VE` trên cấu kiện đa nội lực:**  
   * Input: `decide_eta({"eta_M": 0.96, "eta_V": 0.52})`  
   * Kỳ vọng: `decision.status_code == StatusCode.PASS_WARNING` (`W001`, màu cam 🟠), không được trả về `TRIGGER_VE`.  
6. **Test `keyword_database.json` & `intent_classifier.py` — Không trùng khóa JSON & phân loại đúng DE vs SDE:**  
   * Kiểm tra `json.loads()` với `object_pairs_hook` phát hiện duplicate keys trên `keyword_database.json` \$\\rightarrow\$ Kỳ vọng: `0 duplicate keys`.  
   * Prompt: `"Kiểm tra thép dầm B1 và bu lông neo chân cột theo bản vẽ thiết kế"` \$\\rightarrow\$ Kỳ vọng: `primary_skill == "Design_Evaluation"`.

## 5\. LỆNH THỰC THI DÀNH CHO ANTIGRAVITY (EXECUTION PROMPT)

> **Hướng dẫn cho User:** Bạn có thể mở Antigravity IDE và dán trực tiếp câu lệnh dưới đây:

Chào Antigravity, chuyên gia kiểm toán độc lập Argon đã hoàn tất rà soát Hồ sơ v7.0 và xuất báo cáo kèm đặc tả bản vá tại file \`.agents/docs/ARGON\_AUDIT\_RESPONSE\_v7.0.md\`.

Hãy đọc toàn bộ file \`.agents/docs/ARGON\_AUDIT\_RESPONSE\_v7.0.md\` và thực hiện tuần tự:

1\. Vá lỗi \`.agents/skills/Structural\_Design\_Engineer/scripts/calc\_anchorage\_lap.py\` theo Mục 3.1 (cập nhật Citation đúng CT 255, 256, 257, 259 và số trang của TCVN 5574:2018; bổ sung splice\_ratio nội suy alpha\_lap từ 1.2 đến 2.0; bổ sung tham số kháng chấn TCVN 9386-1:2025 Điều 5.6; bổ sung B12.5, B22.5, B45-B60, CB300-T, Rsc=400MPa cho CB500-V nén ngắn hạn; chặn nối chồng d \> 40mm và cảnh báo neo thẳng thép trơn chịu kéo).

2\. Cập nhật \`.agents/skills/Design\_Evaluation/STANDARDS\_LOCK.md\` và \`INDEX\_QUICK.md\` theo Mục 3.2 (nâng QCVN 01:2012 lên QCVN 01:2021/BXD, đồng bộ hậu tố Sửa đổi 1:2023 cho QCVN 06:2022/BXD).

3\. Sửa lỗi duplicate key \`"SKILL\_TEMPWORKS"\` trong \`.agents/skills/Global\_Dispatcher/scripts/keyword\_database.json\` và nâng cấp thuật toán tính confidence \+ TB-03 trong \`intent\_classifier.py\` theo Mục 3.3.

4\. Sửa thứ tự ưu tiên \`PASS\_WARNING\` trước \`TRIGGER\_VE\` trong hàm \`decide\_eta()\` của \`.agents/tools/policy\_engine.py\` theo Mục 3.4.

5\. Sửa lỗi phân biệt chữ hoa/thường (\`Standard\_Method\`, \`Calculation\_Logs\`), lỗi \`not logs\` trả về \`0.0\` và cập nhật danh sách \`\_is\_valid\_standard()\` trong \`.agents/\_SHARED/SHARED\_CONTEXT/confidence\_score.py\` theo Mục 3.5.

6\. Bổ sung 6 unit tests tại Mục 4, chạy lại \`python .agents/tests/run\_all\_tests.py\` và \`python .agents/tools/sync\_report.py\` để xác nhận 100% PASS trước khi xuất báo cáo v7.1.

## 6\. DANH MỤC TÀI LIỆU & MÃ NGUỒN ĐỐI CHIẾU (REFERENCES)

* **Hồ sơ kiểm toán đầu vào:** [ARGON\_AUDIT\_DOSSIER.md](https://drive.google.com/file/d/12CjhG7mfpNsq5r67gxfmm7JlE5nrOfs1/view?usp=drivesdk)  
* **Quy tắc cốt lõi toàn hệ thống:** [AGENTS.md](https://drive.google.com/file/d/1UOkKPgkiqUCUh1iNsnq53fGzDrLNZPPx/view?usp=drivesdk)  
* **Danh mục khóa phiên bản tiêu chuẩn:** [STANDARDS\_LOCK.md](https://drive.google.com/file/d/1D6DiH3SQIWoRtDaVQW_BXtAxwqZNcArZ/view?usp=drivesdk) và [INDEX\_QUICK.md](https://drive.google.com/file/d/1CF_3eIM3uRYNZTDj0KD8sCxvWtjaM5O5/view?usp=drivesdk)  
* **Tiêu chuẩn thiết kế BTCT:** [10.TCVN 5574-2018\_THIET KE BE TONG VA BE TONG COT THEP.pdf](https://drive.google.com/file/d/193EqIjOv_X6-oHMxYjQYl46LEvxl4tS9/view?usp=drivesdk)  
* **Tiêu chuẩn thiết kế kháng chấn:** [2a. TCVN 9386-2025 P1\_THIET KE CONG TRINH CHIU DONG DAT.pdf](https://drive.google.com/file/d/1XBDC4Jw7HDpYDRA6hRVXOhahnha-dB-l/view?usp=drivesdk) và [2b. TCVN 9386-2025 P5\_THIET KE CONG TRINH CHIU DONG DAT.pdf](https://drive.google.com/file/d/1f6aY_Fs-gCF621ir-tz4LU3UW9euY61r/view?usp=drivesdk)  
* **Quy chuẩn kỹ thuật quốc gia:** [Sửa đổi 1:2023 QCVN 06:2022/BXD (Thông tư 09/2023/TT-BXD)](https://thuvienphapluat.vn/van-ban/Tai-nguyen-Moi-truong/Thong-tu-09-2023-TT-BXD-sua-doi-1-2023-QCVN-06-2022-BXD-an-toan-chay-cho-nha-cong-trinh-583536.aspx) và [QCVN 01:2021/BXD về Quy hoạch xây dựng](https://sxd.laocai.gov.vn/quy-chuan-xay-dung)  
* **Mã nguồn các module được kiểm toán:** [calc\_anchorage\_lap.py](https://drive.google.com/file/d/1HBZ9vnjXOxeGgn5fYZZRMzDf2Dzsi0LP/view?usp=drivesdk), [intent\_classifier.py](https://drive.google.com/file/d/15aeF4hCK8-3Latms5RAT0Ynr7uL0_kCa/view?usp=drivesdk), [keyword\_database.json](https://drive.google.com/file/d/1Zipf_hmwIHjmC3LT6hyJUyMjcyyfmGNI/view?usp=drivesdk), [pipeline\_builder.py](https://drive.google.com/file/d/1wGba0DAxu7zHgAnHdZ_KJ3CJ0yUqSdON/view?usp=drivesdk), [policy\_engine.py](https://drive.google.com/file/d/1ou_l6Fwo2AC1Gq-mUWVcS4wyYWU-0OIE/view?usp=drivesdk), [test\_policy\_engine.py](https://drive.google.com/file/d/1lS-qNHltqy7IYMvFy9U8C1S7sqzirnHe/view?usp=drivesdk), [confidence\_score.py](https://drive.google.com/file/d/1dtcfj2-l8cWx6EYD_BY_5_7fNFybxoSS/view?usp=drivesdk), [run\_all\_tests.py](https://drive.google.com/file/d/1ZUsqgyPNOkD0dyCRtAah6QT13L2LK93x/view?usp=drivesdk)