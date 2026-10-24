# ĐẶC TẢ KỸ THUẬT & BẢN VÁ NÂNG CẤP HỆ SINH THÁI .AGENTS (SPRINT 1 & SPRINT 2 — v8.0)

## TECHNICAL SPECIFICATION & IMPLEMENTATION BLUEPRINT — DÀNH CHO ANTIGRAVITY IDE

> **Ngày ban hành:** 2026-10-18T09:05:00+07:00 **Đơn vị lập đặc tả:** Argon — Independent Lead Auditor & Chief Systems Architect **Phạm vi chốt triển khai:**  
> 

> - **Sprint 1:** Chuẩn hóa Toàn diện Bộ Xuất Thuyết minh Tính toán & Phụ lục Step-by-Step (`export_calc_sheet.py`, `generator_full.py`, `docx_generator.py`, `TMTT_FULL.md`, `report_dispatcher.py`, `report_consistency_check.py`).  
> - **Sprint 2:** Xây dựng Bộ Đọc Dữ liệu Đầu vào Đa nguồn & Kiểm soát Xung đột Hồ sơ Chéo (`project_truth_graph.json`, `ingest_project_docs.py`, `cross_doc_conflict_checker.py`). **Tài liệu nền tảng kế thừa:** [ARGON\_AUDIT\_RESPONSE\_v7.0.md](https://docs.google.com/document/d/1NuD8ACn23bxTHChSn3fNuEv9IxmsnTrYgIp7nz82EfA/edit?usp=drivesdk&ouid=104836374233888202276), [AGENTS.md](https://drive.google.com/file/d/1UOkKPgkiqUCUh1iNsnq53fGzDrLNZPPx/view?usp=drivesdk), [STANDARDS\_LOCK.md](https://drive.google.com/file/d/1D6DiH3SQIWoRtDaVQW_BXtAxwqZNcArZ/view?usp=drivesdk).

## 1\. TỔNG QUAN KIẾN TRÚC SPRINT 1 & SPRINT 2

| Giai đoạn | Mục tiêu cốt lõi | File hiện hữu cần nâng cấp / vá lỗi | File / Module mới cần khởi tạo | Đầu ra kiểm chứng (Deliverables) |
| :---- | :---- | :---- | :---- | :---- |
| **Sprint 1: Chuẩn hóa Thuyết minh Tính toán Kèm theo** | Mỗi phép tính kết cấu xuất ra đều kèm Thuyết minh & Phụ lục tính toán step-by-step chuẩn TCVN, có bảng thông số đầu vào, dòng thay số trung gian và bảng tổng hợp \$\\eta\$ đầy đủ | [export\_calc\_sheet.py](https://drive.google.com/file/d/1m3B0Gmsi9fVECO_paHvXdTUAy_Ktyh8j/view?usp=drivesdk), [generator\_full.py](https://drive.google.com/file/d/19XBAPi5nRGvxZhO2zONWjZCQmh_mOV-q/view?usp=drivesdk), [docx\_generator.py](https://drive.google.com/file/d/1TRSzJTikQAD3sQc07RtRhQXHqJKauH7s/view?usp=drivesdk), [TMTT\_FULL.md](https://drive.google.com/file/d/1WuazBRdS7-Whf1M6Kvp4HAFCk_ewWvFY/view?usp=drivesdk), [report\_dispatcher.py](https://drive.google.com/file/d/1UmnAKoZvz23zeJSmQOukpIhut9j5lHb9/view?usp=drivesdk), [report\_consistency\_check.py](https://drive.google.com/file/d/1jbT2bSMYfzfYCcf8R73YPt_1ryQheJVS/view?usp=drivesdk) | `.agents/tests/test_sprint1_reporting.py` | Thuyết minh `.md` / `.docx` hiển thị bảng thông số TCVN, công thức \+ thay số \+ trích dẫn đầy đủ, khớp 100% với JSON gốc |
| **Sprint 2: Đọc Hồ sơ Đầu vào & Kiểm soát Xung đột Chéo** | Đọc dữ liệu từ Bản vẽ (KC/KT/MEP), Báo cáo Địa chất, Bảng xuất Mô hình và Dự toán BOQ vào 1 đồ thị dữ liệu chuẩn để bắt xung đột hồ sơ trước khi tính toán | [boq\_extractor.py](https://drive.google.com/file/d/1rfXLJfuAL-GiB_7SlJzM_RoU1rcRkf0r/view?usp=drivesdk), [compare\_with\_etabs.py](https://drive.google.com/file/d/1LPp2mrk0FF7viYqT5nn5r_pnYOkq0ERD/view?usp=drivesdk), [verify\_all.py](https://drive.google.com/file/d/1W0-P9nxkjSHnI4lfQ4bzwMsYtwtayimp/view?usp=drivesdk), [SKILL\_BRIDGE.md](https://drive.google.com/file/d/1J5S3Vz8G9ASRR4wPteJv-rjH01rVR5df/view?usp=drivesdk) | `.agents/_SHARED/schemas/project_truth_graph.schema.json`, `.agents/skills/SKILL_VERIFY/scripts/ingest_project_docs.py`, `.agents/skills/SKILL_VERIFY/scripts/cross_doc_conflict_checker.py`, `.agents/tests/test_sprint2_conflict_control.py` | Tệp `project_truth_graph.json` và **Báo cáo Kiểm soát Hồ sơ & Xung đột (Document Control & Clash Report)** tự động phát hiện 8 nhóm xung đột |

## 2\. ĐẶC TẢ CHI TIẾT SPRINT 1 — NÂNG CẤP KHẢ NĂNG THỂ HIỆN THUYẾT MINH KÈM THEO

### 2.1. Tổng hợp 6 Lỗi Nghiêm trọng Phát hiện trong Các Module Thuyết minh Hiện tại

Qua kiểm toán mã nguồn trực tiếp trên hệ thống, dưới đây là 6 lỗi làm sai lệch số liệu vật liệu hoặc làm hỏng bố cục thuyết minh cần phải vá ngay trong Sprint 1:

1. **Sai cường độ vật liệu theo TCVN 5574:2018 trong [generator\_full.py](https://drive.google.com/file/d/19XBAPi5nRGvxZhO2zONWjZCQmh_mOV-q/view?usp=drivesdk) (Dòng 71–85) — Mức độ: CRITICAL (P0):**  
   * Mã nguồn hiện tại khai báo:  
     * `"B30": {"fc": 17.0, "fct": 1.20, "Ec": 32500}` \$\\rightarrow\$ Theo [TCVN 5574:2018 Bảng 7 (trang 35\)](https://drive.google.com/file/d/193EqIjOv_X6-oHMxYjQYl46LEvxl4tS9/view?usp=drivesdk), cường độ chịu kéo tính toán của bê tông `B30` là **\$R\_{bt} \= 1.15\\text{ MPa}\$** (con số `1.20 MPa` là của tiêu chuẩn cũ `TCVN 5574:2012`).  
     * `"CB400": {"fy": 340, "fyk": 400, "Es": 200000}` và `"CB500": {"fy": 415, "fyk": 500, "Es": 200000}` \$\\rightarrow\$ Theo [TCVN 5574:2018 Bảng 13 (trang 47\)](https://drive.google.com/file/d/193EqIjOv_X6-oHMxYjQYl46LEvxl4tS9/view?usp=drivesdk), cường độ chịu kéo tính toán của `CB400-V` là **\$R\_s \= 350\\text{ MPa}\$** (không phải `340 MPa` — lỗi này đã xuất hiện trực tiếp trong báo cáo thực tế [ThamTra\_ClashDetection\_TMTT.md](https://drive.google.com/file/d/1x2O7wc5zAK37xQq1KNhmaBQV4ufBWxH3/view?usp=drivesdk) mục 2.2), và của `CB500-V` là **\$R\_s \= 435\\text{ MPa}\$** (\$R\_{sc} \= 400\\text{ MPa}\$ khi nén ngắn hạn, không phải `415 MPa`). Đồng thời mô đun đàn hồi của `CB300-V` là \$E\_s \= 200,000\\text{ MPa}\$ theo Mục 6.2.4.1 (trang 49).  
2. **In thẳng khối code JSON thô vào Mục 2 của Thuyết minh trong [export\_calc\_sheet.py](https://drive.google.com/file/d/1m3B0Gmsi9fVECO_paHvXdTUAy_Ktyh8j/view?usp=drivesdk) (Dòng 89–92) — Mức độ: HIGH (P1):**  
   * Hiện tại Mục 2 (*"Thông số vật liệu & Dữ liệu đầu vào"*) gọi `json.dumps(data.get("Input", {}), indent=2)` đặt trong block ```` ```json ````, khiến tờ phụ lục tính toán xuất ra cho Chủ đầu tư / Cơ quan thẩm định hiển thị đoạn mã JSON thay vì bảng thông số kỹ thuật chuẩn (Tên thông số | Ký hiệu | Giá trị | Đơn vị | Nguồn/Tiêu chuẩn).  
3. **Mất hoàn toàn dòng "Thay số" (`Substitution`) trong [export\_calc\_sheet.py](https://drive.google.com/file/d/1m3B0Gmsi9fVECO_paHvXdTUAy_Ktyh8j/view?usp=drivesdk) (Dòng 104\) — Mức độ: CRITICAL (P0):**  
   * Dòng 104 viết `val = log.get("Values", "")`, trong khi quy chuẩn tại [AGENTS.md (§5)](https://drive.google.com/file/d/1UOkKPgkiqUCUh1iNsnq53fGzDrLNZPPx/view?usp=drivesdk) và các script tính toán ([calc\_anchorage\_lap.py](https://drive.google.com/file/d/1HBZ9vnjXOxeGgn5fYZZRMzDf2Dzsi0LP/view?usp=drivesdk), [calc\_weld\_tcvn.py](https://drive.google.com/file/d/1GTgD1zpy_nesmTzGnuTNLzKb032A1D_C/view?usp=drivesdk), [calculation\_logs\_checker.py](https://drive.google.com/file/d/1uzSJSXYEn5rzm3t3lq-Vz2gFjn-8QW8R/view?usp=drivesdk)) đều xuất khóa `"Substitution"`. Hệ quả là mọi tờ thuyết minh xuất từ `export_calc_sheet.py` bị mất sạch bước thế số trung gian.  
4. **Bó cứng bảng tổng hợp \$\\eta\$ chỉ có 2 dòng (Uốn & Cắt) trong [export\_calc\_sheet.py](https://drive.google.com/file/d/1m3B0Gmsi9fVECO_paHvXdTUAy_Ktyh8j/view?usp=drivesdk) (Dòng 123–129) — Mức độ: HIGH (P1):**  
   * Khi xuất thuyết minh cho Cột chịu nén lệch tâm (`eta_N`, `eta_NM`), Sàn/Dầm kiểm tra nứt và võng (`eta_crack`, `eta_defl`), Móng cọc (`eta_pile`), Neo/nối cốt thép (`L_an`, `L_lap`), hoặc Liên kết bu lông/đường hàn (`eta_bolt`, `eta_weld`), bảng tổng hợp Mục 5 bị trống hoặc hiển thị `0.000`.  
5. **Vi phạm `STANDARDS_LOCK.md` trong mẫu [TMTT\_FULL.md](https://drive.google.com/file/d/1WuazBRdS7-Whf1M6Kvp4HAFCk_ewWvFY/view?usp=drivesdk) (Dòng 28\) và xung đột Font trong [docx\_generator.py](https://drive.google.com/file/d/1TRSzJTikQAD3sQc07RtRhQXHqJKauH7s/view?usp=drivesdk) (Dòng 35\) — Mức độ: MEDIUM (P2):**  
   * `TMTT_FULL.md` vẫn trích dẫn `QCVN 03:2012/BXD` và `Thông tư số 06/2021/TT-BXD`, thiếu `TCVN 9386:2025`, `TCVN 10304:2025` và `QCVN 06:2022/BXD + Sửa đổi 1:2023`.  
   * `SKILL_PHULUC/docx_generator.py` đặt `NORMAL_FONT = 'Arial'`, trái ngược với [SKILL\_PHULUC/SKILL.md](https://drive.google.com/file/d/1l2zaHy80MXgClGipt-DJcD-EgbbVeKcw/view?usp=drivesdk) và [generate\_tmtt\_docx.py](https://drive.google.com/file/d/1etQnUOfe181Bo9wRNeyK8ZLj43u5OY85/view?usp=drivesdk) quy định bắt buộc dùng `Times New Roman` cho hồ sơ pháp lý.  
6. **Lệch Schema khóa JSON giữa [report\_dispatcher.py](https://drive.google.com/file/d/1UmnAKoZvz23zeJSmQOukpIhut9j5lHb9/view?usp=drivesdk) và [SKILL\_BRIDGE.md](https://drive.google.com/file/d/1J5S3Vz8G9ASRR4wPteJv-rjH01rVR5df/view?usp=drivesdk) & thiếu ký hiệu TCVN trong [report\_consistency\_check.py](https://drive.google.com/file/d/1jbT2bSMYfzfYCcf8R73YPt_1ryQheJVS/view?usp=drivesdk) — Mức độ: HIGH (P1):**  
   * `report_dispatcher.py` chỉ đọc khóa tiếng Việt cấp cao nhất (`Ten_Du_An`, `Hang_Muc`, `Calculation_Logs`), không tự động ánh xạ khi nhận Handoff JSON chuẩn v3.0.0 (`project_context.project_name`, `payload.calculation_logs`).  
   * `report_consistency_check.py` chỉ quét các ký hiệu Eurocode (`fck`, `fy`, `M_Rd`, `V_Rd`) mà chưa quét các ký hiệu TCVN (\$R\_b, R\_{bt}, R\_s, R\_{sc}, R\_{sw}, M\_{gh}, Q\_b, a\_{crc}, f, L\_{an}, L\_{lap}\$).

### 2.2. Mã nguồn Bản vá Chuẩn hóa cho Sprint 1

#### A. Bản vá `.agents/skills/SKILL_PHULUC/generator_full.py` (Chuẩn hóa Bảng Vật liệu TCVN 5574:2018 & TCVN 5575:2024)

Thay thế khối `CONCRETE_GRADES`, `STEEL_GRADES_RC`, `STEEL_GRADES_STEEL` tại dòng 70–95 của [generator\_full.py](https://drive.google.com/file/d/19XBAPi5nRGvxZhO2zONWjZCQmh_mOV-q/view?usp=drivesdk) bằng dữ liệu khóa cứng từ [TCVN 5574:2018 (Bảng 7 trang 35, Bảng 13 trang 47\)](https://drive.google.com/file/d/193EqIjOv_X6-oHMxYjQYl46LEvxl4tS9/view?usp=drivesdk):

CONCRETE\_GRADES \= {

    "B12.5": {"Rb": 7.5, "Rbt": 0.66, "Eb": 21500, "fc": 7.5, "fct": 0.66, "Ec": 21500, "class": 12.5},

    "B15":   {"Rb": 8.5, "Rbt": 0.75, "Eb": 24000, "fc": 8.5, "fct": 0.75, "Ec": 24000, "class": 15},

    "B20":   {"Rb": 11.5, "Rbt": 0.90, "Eb": 27500, "fc": 11.5, "fct": 0.90, "Ec": 27500, "class": 20},

    "B22.5": {"Rb": 13.0, "Rbt": 1.00, "Eb": 29000, "fc": 13.0, "fct": 1.00, "Ec": 29000, "class": 22.5},

    "B25":   {"Rb": 14.5, "Rbt": 1.05, "Eb": 30000, "fc": 14.5, "fct": 1.05, "Ec": 30000, "class": 25},

    "B30":   {"Rb": 17.0, "Rbt": 1.15, "Eb": 32500, "fc": 17.0, "fct": 1.15, "Ec": 32500, "class": 30},

    "B35":   {"Rb": 19.5, "Rbt": 1.30, "Eb": 34500, "fc": 19.5, "fct": 1.30, "Ec": 34500, "class": 35},

    "B40":   {"Rb": 22.0, "Rbt": 1.40, "Eb": 36000, "fc": 22.0, "fct": 1.40, "Ec": 36000, "class": 40},

    "B45":   {"Rb": 25.0, "Rbt": 1.50, "Eb": 37000, "fc": 25.0, "fct": 1.50, "Ec": 37000, "class": 45},

    "B50":   {"Rb": 27.5, "Rbt": 1.60, "Eb": 38000, "fc": 27.5, "fct": 1.60, "Ec": 38000, "class": 50},

    "B55":   {"Rb": 30.0, "Rbt": 1.70, "Eb": 39000, "fc": 30.0, "fct": 1.70, "Ec": 39000, "class": 55},

    "B60":   {"Rb": 33.0, "Rbt": 1.80, "Eb": 39500, "fc": 33.0, "fct": 1.80, "Ec": 39500, "class": 60},

}

STEEL\_GRADES\_RC \= {

    "CB240-T": {"Rs": 210, "Rsc": 210, "Rsw": 170, "Rk": 240, "Es": 200000, "fy": 210, "fyk": 240},

    "CB300-T": {"Rs": 260, "Rsc": 260, "Rsw": 210, "Rk": 300, "Es": 200000, "fy": 260, "fyk": 300},

    "CB300-V": {"Rs": 260, "Rsc": 260, "Rsw": 210, "Rk": 300, "Es": 200000, "fy": 260, "fyk": 300},

    "CB400-V": {"Rs": 350, "Rsc": 350, "Rsw": 280, "Rk": 400, "Es": 200000, "fy": 350, "fyk": 400},

    "CB500-V": {"Rs": 435, "Rsc": 400, "Rsw": 300, "Rk": 500, "Es": 200000, "fy": 435, "fyk": 500},

    \# Alias tuong thich nguoc

    "CB240":   {"Rs": 210, "Rsc": 210, "Rsw": 170, "Rk": 240, "Es": 200000, "fy": 210, "fyk": 240},

    "CB300":   {"Rs": 260, "Rsc": 260, "Rsw": 210, "Rk": 300, "Es": 200000, "fy": 260, "fyk": 300},

    "CB400":   {"Rs": 350, "Rsc": 350, "Rsw": 280, "Rk": 400, "Es": 200000, "fy": 350, "fyk": 400},

    "CB500":   {"Rs": 435, "Rsc": 400, "Rsw": 300, "Rk": 500, "Es": 200000, "fy": 435, "fyk": 500},

}

#### B. Bản vá `.agents/skills/Structural_Design_Engineer/scripts/export_calc_sheet.py` (Thuyết minh Kép: Bảng Thông số Kỹ thuật \+ Đầy đủ Dòng Thay số \+ Bảng Tổng hợp \$\\eta\$ Động)

Cập nhật hàm `generate_markdown(data, args)` trong [export\_calc\_sheet.py](https://drive.google.com/file/d/1m3B0Gmsi9fVECO_paHvXdTUAy_Ktyh8j/view?usp=drivesdk):

\# Tu dien anh xa ten ky thuat, ky hieu va don vi cho bang Input

INPUT\_PARAM\_META \= {

    "b": ("Bề rộng tiết diện", "b", "mm"),

    "h": ("Chiều cao tiết diện", "h", "mm"),

    "L": ("Nhịp tính toán", "L", "mm"),

    "a": ("Khoảng cách trọng tâm cốt thép chịu kéo", "a", "mm"),

    "a\_prime": ("Khoảng cách trọng tâm cốt thép chịu nén", "a'", "mm"),

    "h0": ("Chiều cao làm việc tiết diện", "h\_0", "mm"),

    "concrete": ("Cấp độ bền bê tông", "B", "—"),

    "rebar": ("Nhóm cốt thép dọc", "CB", "—"),

    "stirrup\_grade": ("Nhóm cốt thép đai", "CB\_w", "—"),

    "dia": ("Đường kính cốt thép", "d\_s", "mm"),

    "M": ("Mô men uốn tính toán", "M", "kN.m"),

    "M\_Ed": ("Mô men uốn tính toán", "M", "kN.m"),

    "V": ("Lực cắt tính toán", "Q", "kN"),

    "V\_Ed": ("Lực cắt tính toán", "Q", "kN"),

    "N": ("Lực dọc tính toán", "N", "kN"),

    "N\_Ed": ("Lực dọc tính toán", "N", "kN"),

    "splice\_ratio": ("Tỷ lệ thanh nối chồng trong cùng tiết diện", "r\_lap", "—"),

    "seismic\_class": ("Cấp dẻo kháng chấn", "DCL/DCM/DCH", "—"),

}

ETA\_LABELS \= {

    "eta\_M": ("Kiểm tra Khả năng chịu Uốn (TTGH1)", "M / M\_gh ≤ 1.00"),

    "eta\_V": ("Kiểm tra Khả năng chịu Cắt trên tiết diện nghiêng (TTGH1)", "Q / Q\_b,sw ≤ 1.00"),

    "eta\_strut": ("Kiểm tra Nén vỡ Dải bê tông nghiêng (TTGH1)", "Q / Q\_b,max ≤ 1.00"),

    "eta\_N": ("Kiểm tra Khả năng chịu Nén / Kéo dọc trục (TTGH1)", "N / N\_gh ≤ 1.00"),

    "eta\_NM": ("Kiểm tra Nén uốn lệch tâm (TTGH1)", "η\_NM ≤ 1.00"),

    "eta\_LTB": ("Kiểm tra Ổn định tổng thể dầm chịu uốn (TTGH1)", "M / (φ\_b W\_c f γ\_c) ≤ 1.00"),

    "eta\_shear": ("Kiểm tra Chịu cắt bản bụng (TTGH1)", "V / V\_c ≤ 1.00"),

    "eta\_bolt": ("Kiểm tra Liên kết Bu lông (TTGH1)", "F / \[F\]\_bolt ≤ 1.00"),

    "eta\_weld": ("Kiểm tra Liên kết Đường hàn (TTGH1)", "τ\_w / (f\_w γ\_c) ≤ 1.00"),

    "eta\_pile": ("Kiểm tra Sức chịu tải Cọc (TTGH1)", "P\_max / R\_c,d ≤ 1.00"),

    "eta\_punch": ("Kiểm tra Chọc thủng đài/sàn (TTGH1)", "F / F\_b,u ≤ 1.00"),

    "eta\_crack": ("Kiểm tra Bề rộng vết nứt (TTGH2)", "a\_crc / \[a\_crc\] ≤ 1.00"),

    "eta\_defl": ("Kiểm tra Độ võng cấu kiện (TTGH2)", "f / \[f\] ≤ 1.00"),

    "eta\_max": ("Chỉ số sử dụng chịu lực tổng hợp cực đại", "η\_max ≤ 1.00"),

}

def \_render\_input\_table(inputs: dict) \-\> list\[str\]:

    """Chuyển dict Input thành bảng thông số kỹ thuật chuẩn thay vì in raw JSON."""

    if not inputs:

        return \["\*Không có dữ liệu thông số đầu vào chi tiết.\*", ""\]

    lines \= \[

        "| STT | Thông số kỹ thuật | Ký hiệu | Giá trị đầu vào | Đơn vị |",

        "| :---: | :--- | :---: | :---: | :---: |",

    \]

    for idx, (k, v) in enumerate(inputs.items(), 1):

        label, sym, unit \= INPUT\_PARAM\_META.get(k, (k.replace("\_", " ").title(), f"\`{k}\`", "—"))

        val\_str \= f"{v:,.3f}".rstrip("0").rstrip(".") if isinstance(v, float) else str(v)

        lines.append(f"| {idx} | {label} | \${sym}\$ | \*\*{val\_str}\*\* | {unit} |")

    lines.append("")

    return lines

* Trong vòng lặp duyệt `Calculation_Logs` của [export\_calc\_sheet.py](https://drive.google.com/file/d/1m3B0Gmsi9fVECO_paHvXdTUAy_Ktyh8j/view?usp=drivesdk) (dòng 99–116), sửa lỗi đọc khóa thay số và bổ sung số trang tiêu chuẩn:

    for log in logs:

        step \= log.get("Step") or log.get("Step\_Number") or ""

        desc \= log.get("Description") or log.get("Title") or ""

        form \= log.get("Formula") or log.get("formula") or ""

        \# VÁ LỖI MẤT THAY SỐ: Ưu tiên đọc "Substitution" rồi mới fallback sang "Values"

        sub \= log.get("Substitution") or log.get("substitution") or log.get("Values") or ""

        res \= log.get("Result") or log.get("result") or ""

        cit \= log.get("Citation") or log.get("citation") or {}

        if isinstance(cit, dict):

            tc \= cit.get("Tieu\_chuan") or cit.get("Standard") or cit.get("code") or ""

            dm \= cit.get("Dieu\_Muc") or cit.get("Clause") or cit.get("article") or ""

            bh \= cit.get("Bang\_Hinh") or cit.get("Table") or ""

            tr \= cit.get("Trang") or cit.get("Page") or ""

            cit\_parts \= \[p for p in \[tc, dm, bh, f"Trang {tr}" if tr else ""\] if p\]

            cit\_str \= " — ".join(cit\_parts)

        else:

            cit\_str \= str(cit)

        md.append(f"\#\#\# Bước {step}: {desc}")

        if form:

            md.append(f"- \*\*Công thức:\*\* \`{form}\`")

        if sub:

            md.append(f"- \*\*Thay số:\*\* \`{sub}\`")

        if res is not None and str(res) \!= "":

            md.append(f"- \*\*Kết quả:\*\* \*\*{res}\*\*")

        if cit\_str:

            md.append(f"- \*Căn cứ tiêu chuẩn: {cit\_str}\*")

        md.append("")

* Trong Mục 5 (*"BẢNG TỔNG HỢP CHỈ SỐ SỬ DỤNG"*), thay thế 2 dòng cố định bằng cơ chế quét động toàn bộ các trường `eta_*` và kết quả chính trong `results`:

    md.append("\#\# 5\. BẢNG TỔNG HỢP CHỈ SỐ SỬ DỤNG (UTILIZATION SUMMARY)")

    md.append("| Hạng mục kiểm tra | Điều kiện giới hạn | Hệ số sử dụng (η) | Đánh giá |")

    md.append("| :--- | :---: | :---: | :---: |")

    eta\_found \= False

    for key, val in results.items():

        if key.startswith("eta\_") and isinstance(val, (int, float)):

            eta\_found \= True

            label, cond \= ETA\_LABELS.get(key, (f"Kiểm tra {key}", "η ≤ 1.00"))

            icon \= "🔴 KHÔNG ĐẠT" if val \> 1.0 else ("🟠 CẢNH BÁO (\>0.90)" if val \> 0.90 else ("🟢 ĐẠT (Dự trữ VE)" if val \<= 0.70 else "✅ ĐẠT TỐI ƯU"))

            md.append(f"| {label} | \`{cond}\` | \*\*{val:.3f}\*\* ({val\*100:.1f}%) | {icon} |")

    if not eta\_found:

        \# Cho các bài toán xuất thông số cấu tạo như Neo & Nối chồng cốt thép (L\_an, L\_lap)

        for k, v in results.items():

            if isinstance(v, (int, float, str)) and k not in ("Status",):

                md.append(f"| Kết quả \`{k}\` | Theo TCVN | \*\*{v}\*\* | ✅ ĐÃ XÁC ĐỊNH |")

#### C. Đồng bộ Schema trong `report_dispatcher.py` và Mở rộng Từ điển TCVN trong `report_consistency_check.py`

1. Trong [report\_dispatcher.py](https://drive.google.com/file/d/1UmnAKoZvz23zeJSmQOukpIhut9j5lHb9/view?usp=drivesdk), thêm hàm chuẩn hóa đầu vào `_normalize_handoff_schema(data: dict) -> dict` ngay đầu hàm `load_handoff()` để tự động ánh xạ hai chiều giữa Schema tiếng Anh của [SKILL\_BRIDGE.md](https://drive.google.com/file/d/1J5S3Vz8G9ASRR4wPteJv-rjH01rVR5df/view?usp=drivesdk) (`project_context.project_name`, `project_context.phase`, `payload.calculation_logs`) và các khóa tiếng Việt (`Ten_Du_An`, `Giai_Doan_TK`, `Calculation_Logs`).  
2. Trong [report\_consistency\_check.py](https://drive.google.com/file/d/1jbT2bSMYfzfYCcf8R73YPt_1ryQheJVS/view?usp=drivesdk), bổ sung các pattern TCVN vào `NUMBER_PATTERNS` và `JSON_TO_DOCX_KEY_MAP`:  
   * `Rb`: `r"R[_\s]?b\s*[=:]\s*([0-9]+[.,]?[0-9]*)"`  
   * `Rbt`: `r"R[_\s]?bt\s*[=:]\s*([0-9]+[.,]?[0-9]*)"`  
   * `Rs`: `r"R[_\s]?s\s*[=:]\s*([0-9]+[.,]?[0-9]*)"`  
   * `Rsw`: `r"R[_\s]?sw\s*[=:]\s*([0-9]+[.,]?[0-9]*)"`  
   * `L_an`: `r"L[_\s]?an\s*[=:]\s*([0-9]+[.,]?[0-9]*)"`  
   * `L_lap`: `r"L[_\s]?lap\s*[=:]\s*([0-9]+[.,]?[0-9]*)"`  
   * `a_crc`: `r"a[_\s]?crc\s*[=:]\s*([0-9]+[.,]?[0-9]*)"`  
   * Hỗ trợ dấu thập phân tiếng Việt (`,`) bằng `float(m.replace(",", "."))`.

## 3\. ĐẶC TẢ CHI TIẾT SPRINT 2 — ĐỌC DỮ LIỆU ĐẦU VÀO & KIỂM SOÁT XUNG ĐỘT HỒ SƠ CHÉO

Từ kinh nghiệm thực chiến tại báo cáo thẩm tra [ThamTra\_ClashDetection\_TMTT.md](https://drive.google.com/file/d/1x2O7wc5zAK37xQq1KNhmaBQV4ufBWxH3/view?usp=drivesdk) và kiến trúc kiểm chứng tại [verify\_all.py](https://drive.google.com/file/d/1W0-P9nxkjSHnI4lfQ4bzwMsYtwtayimp/view?usp=drivesdk), Sprint 2 xây dựng cơ chế **Đọc Hồ sơ Đa nguồn \$\\rightarrow\$ Chuẩn hóa về Đồ thị Sự thật Dự án (`project_truth_graph.json`) \$\\rightarrow\$ Chạy 8 Luật Kiểm soát Xung đột Chéo (`cross_doc_conflict_checker.py`)** ngay trước khi tính toán.

### 3.1. Cấu trúc Chuẩn `project_truth_graph.json` (Single Source of Truth)

File `.agents/_SHARED/schemas/project_truth_graph.schema.json` định nghĩa cấu trúc hợp nhất từ 5 nguồn tài liệu của dự án:

* `documents_registry`: Danh mục các bộ môn hiện có (`ARCH`, `STRUC`, `MEP_ELEC`, `MEP_PLUMB`, `MEP_HVAC`, `MEP_FIRE`, `GEOTECH`, `BOQ`, `FEM_MODEL`), giai đoạn thiết kế từng hồ sơ (`S1_CONCEPT`, `S2_FEED`, `S3_BASIC_DESIGN`, `S4_TECH_DESIGN`, `S5_SHOP_DRAWING`), ngày phát hành.  
* `materials`: Cấp độ bền bê tông (`concrete_grade`), nhóm thép dọc (`rebar_main`), nhóm thép đai (`rebar_stirrup`), lớp bê tông bảo vệ (`cover_mm`) theo từng nguồn (`general_notes`, `calc_report`, `fem_model`, `boq`).  
* `grids_and_levels`:  
  * `total_width_x_mm`, `total_length_y_mm` và danh sách khoảng cách trục theo từng bộ môn (`STRUC`, `ARCH`, `MEP`).  
  * `story_levels`: Cao độ từng tầng theo `STRUC` (cốt kết cấu), `ARCH` (cốt hoàn thiện \+ lớp cấu tạo sàn hoàn thiện `finish_thickness_mm`), và `FEM_MODEL`.  
* `elements`: Danh mục cột, dầm, sàn, móng theo từng tầng kèm kích thước tiết diện `(b_mm, h_mm)`, cao độ đáy dầm, chiều cao thông thủy yêu cầu của Kiến trúc/MEP (`ceiling_aff_mm`, `mep_duct_clearance_req_mm`).  
* `geotech`: Mực nước ngầm `gwt_m`, danh sách lớp đất \$(z\_{top}, z\_{bot}, N\_{SPT}, c, \\varphi, \\gamma)\$ và cao độ mũi cọc thiết kế `pile_tip_elev_m`.

### 3.2. Đặc tả Module 1 (Sprint 2): `.agents/skills/SKILL_VERIFY/scripts/ingest_project_docs.py`

Module này đóng vai trò cổng đọc dữ liệu đầu vào hợp nhất (kế thừa và mở rộng [boq\_extractor.py](https://drive.google.com/file/d/1rfXLJfuAL-GiB_7SlJzM_RoU1rcRkf0r/view?usp=drivesdk) và [compare\_with\_etabs.py](https://drive.google.com/file/d/1LPp2mrk0FF7viYqT5nn5r_pnYOkq0ERD/view?usp=drivesdk)):

1. **Adapter 1 — Đọc Bảng xuất Excel/CSV từ ETABS/SAFE (`parse_fem_tables`)**:  
   * Đọc các sheet `Story Definitions`, `Material Properties - Concrete Data`, `Frame Section Assignments`, `Frame Section Properties` để trích xuất cao độ tầng mô hình, cấp độ bền bê tông (\$E\_b, f'\_c\$), và tiết diện dầm/cột theo từng tầng.  
2. **Adapter 2 — Đọc Dự toán BOQ Excel/CSV (`parse_boq_summary`)**:  
   * Tích hợp trực tiếp với [boq\_extractor.py](https://drive.google.com/file/d/1rfXLJfuAL-GiB_7SlJzM_RoU1rcRkf0r/view?usp=drivesdk), dùng Regex bóc tách cấp độ bền bê tông (`B15`–`B60` hoặc `M150`–`M600`), nhóm cốt thép (`CB240`, `CB300`, `CB400`, `CB500`) và danh mục hạng mục có trong BOQ.  
3. **Adapter 3 — Đọc Bản vẽ DXF / Bảng trích xuất Bản vẽ KC-KT-MEP (`parse_drawing_metadata`)**:  
   * Đọc file `.dxf` (qua `ezdxf` nếu có) hoặc file JSON/Markdown bóc tách từ PDF bản vẽ để lấy: Giai đoạn hồ sơ (`S3`/`S4`), Ghi chú vật liệu, Lưới trục X/Y, Bảng cao độ tầng KC vs KT, và Bảng thống kê tiết diện cột/dầm theo tầng.  
4. **Adapter 4 — Đọc Hồ sơ Địa chất (`parse_geotech_summary`)**:  
   * Đọc thông số trụ địa chất (chiều sâu các lớp đất, \$N\_{SPT}\$, mực nước ngầm `GWT`) để phục vụ kiểm tra chiều sâu ngàm cọc theo [TCVN 10304:2025](https://drive.google.com/file/d/1D6DiH3SQIWoRtDaVQW_BXtAxwqZNcArZ/view?usp=drivesdk).

### 3.3. Đặc tả Module 2 (Sprint 2): `.agents/skills/SKILL_VERIFY/scripts/cross_doc_conflict_checker.py`

Module này thực thi **8 Quy tắc Kiểm soát Hồ sơ & Bắt Xung đột Chéo (Rule CDC-01 đến CDC-08)** trên tệp `project_truth_graph.json` và tự động xuất cả JSON Handoff lẫn Báo cáo Markdown/DOCX:

| Mã Luật | Tên Quy tắc Kiểm soát Xung đột | Logic Kiểm tra Toán học / Cơ học | Phân loại Mức độ |
| :---- | :---- | :---- | :---- |
| **CDC-01** | **Đồng bộ Giai đoạn Pháp lý Hồ sơ (Stage-Gate Sync)** | Nếu `stage(STRUC) > stage(ARCH)` (ví dụ KC đã phát hành `S4/BVTC` khi KT mới ở `S3/TKCS` chưa phê duyệt) \$\\rightarrow\$ Báo lỗi vi phạm trình tự thiết kế theo Nghị định 15/2021/NĐ-CP. | **🔴 CRITICAL** |
| **CDC-02** | **Đầy đủ Thành phần Hồ sơ theo Giai đoạn (Completeness Gate)** | Kiểm tra các bộ môn bắt buộc theo giai đoạn (`ARCH`, `STRUC`, `GEOTECH`, `MEP_ELEC`, `MEP_PLUMB`, `MEP_FIRE`). Phát hiện ngay trường hợp thiếu hồ sơ Địa chất hoặc thiếu MEP Cấp thoát nước/PCCC. | **🟠 MAJOR** |
| **CDC-03** | **Xung đột Mác Vật liệu Đa nguồn (Cross-Doc Material Clash)** | Quy đổi mọi ký hiệu mác cũ (`M200`, `M250`, `M300`, `AII`, `AIII`) sang cấp độ bền chuẩn [TCVN 5574:2018](https://drive.google.com/file/d/193EqIjOv_X6-oHMxYjQYl46LEvxl4tS9/view?usp=drivesdk) (`B15`, `B20`, `B22.5`, `CB300-V`, `CB400-V`). Nếu có sự khác biệt giữa `Ghi chú chung KC` \$\\leftrightarrow\$ `Thuyết minh` \$\\leftrightarrow\$ `Mô hình ETABS` \$\\leftrightarrow\$ `Dự toán BOQ` \$\\rightarrow\$ Báo lỗi. | **🔴 CRITICAL** |
| **CDC-04** | **Xung đột Cao độ Tầng KC – KT – Mô hình (Elevation Clash)** | Kiểm tra \$\\Delta Z\_i \= |(Z\_{ARCH,i} \- t\_{finish,i}) \- Z\_{STRUC,i}|\$. Nếu \$\\Delta Z\_i \> 5\\text{ mm}\$ (mặc định khi chưa trừ lớp cán nền hoặc lệch cốt sàn như vụ lệch \$50\\text{ mm}\$ ở Tầng 2/Tầng 3\) hoặc \$|Z\_{FEM,i} \- Z\_{STRUC,i}| \> 10\\text{ mm}\$ \$\\rightarrow\$ Báo lỗi. | **🔴 CRITICAL** |
| **CDC-05** | **Xung đột Lưới Trục & Kích thước Mặt bằng KC – KT – MEP (Grid Clash)** | Kiểm tra tổng kích thước mặt bằng \$\\sum L\_{X}, \\sum L\_{Y}\$ và từng nhịp trục giữa `STRUC`, `ARCH`, `MEP`. Nếu lệch \$\> 10\\text{ mm}\$ (như vụ lưới MEP \$18,000\\text{ mm}\$ vs KC \$16,800\\text{ mm}\$) \$\\rightarrow\$ Báo lỗi. | **🟠 MAJOR** |
| **CDC-06** | **Kiểm tra Liên tục Đường truyền Tải & Cột/Vách Mồ côi (Load Path Continuity)** | Với mọi cột/vách ở tầng \$k\$ (\$k \\ge 2\$), kiểm tra sự tồn tại của cột/vách đỡ dưới tại tầng \$k-1\$ (hoặc dầm chuyển/móng ở tầng 1\) và kiểm tra sự xuất hiện trên mặt bằng Kiến trúc tầng \$k\$. Bắt tự động các cột mồ côi (như `CC1`, `CC3`) hoặc cột tầng trên có tiết diện lớn hơn tầng dưới (\$b\_k \> b\_{k-1}\$ hoặc \$h\_k \> h\_{k-1}\$). | **🔴 CRITICAL / 🟠 MAJOR** |
| **CDC-07** | **Xung đột Tĩnh không Đáy Dầm & Không gian MEP (Headroom & MEP Clearance)** | Với mỗi dầm có chiều cao \$h\_{beam}\$ tại tầng có cao độ đáy sàn \$Z\_{slab\_bot} \= Z\_{STRUC} \- t\_{slab}\$ và cao độ trần giả \$Z\_{ceiling}\$: tính khoảng không gian kỹ thuật trên trần \$H\_{MEP} \= (Z\_{STRUC} \- h\_{beam}) \- Z\_{ceiling}\$. Nếu \$H\_{MEP} \< H\_{MEP,req}\$ (ví dụ \$\< 450\\text{ mm}\$ khi có ống gió VRV) hoặc tĩnh không thông thủy dưới dầm \$\< 2,100\\text{ mm}\$ \$\\rightarrow\$ Báo lỗi. | **🟠 MAJOR** |
| **CDC-08** | **Xung đột Mũi Cọc & Địa tầng Khảo sát (Geotech – Foundation Clash)** | Kiểm tra lớp đất tại cao độ mũi cọc thiết kế \$Z\_{pile\_tip}\$ trong hồ sơ Địa chất: nếu mũi cọc nằm trong lớp đất yếu (\$N\_{SPT} \< 15\$ hoặc bùn/sét dẻo mềm) hoặc chiều sâu ngàm vào lớp đất tốt không đạt tối thiểu theo [TCVN 10304:2025](https://drive.google.com/file/d/1D6DiH3SQIWoRtDaVQW_BXtAxwqZNcArZ/view?usp=drivesdk) \$\\rightarrow\$ Báo lỗi. | **🔴 CRITICAL** |

### 3.4. Mã nguồn Khung cho `cross_doc_conflict_checker.py`

File: `.agents/skills/SKILL_VERIFY/scripts/cross_doc_conflict_checker.py`

\#\!/usr/bin/env python3

\# \-\*- coding: utf-8 \-\*-

"""

SKILL\_VERIFY Loại 6 (MỚI \- Sprint 2): Cross-Document Conflict & Document Control Checker

Đối chiếu chéo 5 nguồn hồ sơ (Bản vẽ KC, Bản vẽ KT, Bản vẽ MEP, Mô hình FEM, Địa chất & BOQ)

từ project\_truth\_graph.json theo 8 quy tắc CDC-01 đến CDC-08.

"""

import sys

if sys.stdout.encoding \!= "utf-8":

    sys.stdout.reconfigure(encoding="utf-8")

import json

import argparse

from datetime import datetime

from pathlib import Path

STAGE\_ORDER \= {

    "S1": 1, "CONCEPT": 1,

    "S2": 2, "FEED": 2,

    "S3": 3, "TKCS": 3, "BASIC\_DESIGN": 3,

    "S4": 4, "TKKT": 4, "TECH\_DESIGN": 4,

    "S5": 5, "BVTC": 5, "SHOP\_DRAWING": 5,

}

LEGACY\_CONCRETE\_MAP \= {

    "M150": "B12.5", "M200": "B15", "M250": "B20", "M300": "B22.5",

    "M350": "B25", "M400": "B30", "M450": "B35", "M500": "B40", "M600": "B45",

}

def normalize\_concrete(grade: str) \-\> str:

    g \= str(grade or "").strip().upper()

    return LEGACY\_CONCRETE\_MAP.get(g, g)

def run\_conflict\_checks(graph: dict) \-\> dict:

    issues \= \[\]

    def add\_issue(rule\_id: str, severity: str, disciplines: str, title: str,

                  detail: str, action: str, deadline\_days: int \= 7):

        issues.append({

            "Rule\_ID": rule\_id,

            "Severity": severity,

            "Disciplines": disciplines,

            "Title": title,

            "Detail": detail,

            "Action": action,

            "Deadline\_Days": deadline\_days,

        })

    docs \= graph.get("documents\_registry", {})

    \# \--- CDC-01: Đồng bộ giai đoạn hồ sơ KC vs KT \---

    arch\_stage \= str(docs.get("ARCH", {}).get("stage", "")).upper()

    struc\_stage \= str(docs.get("STRUC", {}).get("stage", "")).upper()

    if arch\_stage in STAGE\_ORDER and struc\_stage in STAGE\_ORDER:

        if STAGE\_ORDER\[struc\_stage\] \> STAGE\_ORDER\[arch\_stage\]:

            add\_issue(

                "CDC-01", "CRITICAL", "KC \+ KT",

                f"Giai đoạn hồ sơ không đồng bộ (KC: {struc\_stage} \> KT: {arch\_stage})",

                f"Hồ sơ Kết cấu đã ở giai đoạn {struc\_stage} trong khi Kiến trúc mới ở giai đoạn {arch\_stage}.",

                "Phê duyệt hồ sơ Kiến trúc trước và rà soát đồng bộ lại Kết cấu theo Nghị định 15/2021/NĐ-CP.",

                5

            )

    \# \--- CDC-02: Kiểm tra thiếu bộ môn bắt buộc \---

    required\_disciplines \= graph.get("required\_disciplines", \["ARCH", "STRUC", "MEP\_ELEC", "MEP\_PLUMB"\])

    for req\_disc in required\_disciplines:

        info \= docs.get(req\_disc, {})

        if not info or info.get("present") is False:

            add\_issue(

                "CDC-02", "MAJOR", req\_disc,

                f"Thiếu hồ sơ bộ môn bắt buộc: {req\_disc}",

                f"Không tìm thấy dữ liệu hoặc bản vẽ của bộ môn {req\_disc} trong bộ hồ sơ đầu vào.",

                f"Bổ sung đầy đủ hồ sơ bộ môn {req\_disc} trước khi trình thẩm định.",

                10

            )

    \# \--- CDC-03: Xung đột mác vật liệu giữa các tài liệu \---

    mats \= graph.get("materials", {})

    concrete\_by\_source \= {}

    for src, mdata in mats.items():

        if isinstance(mdata, dict) and mdata.get("concrete\_grade"):

            raw\_g \= mdata\["concrete\_grade"\]

            norm\_g \= normalize\_concrete(raw\_g)

            concrete\_by\_source\[src\] \= (raw\_g, norm\_g)

            if raw\_g.upper().startswith("M") and norm\_g.startswith("B"):

                add\_issue(

                    "CDC-03", "WARNING", "KC",

                    f"Sử dụng ký hiệu mác bê tông cũ '{raw\_g}' tại nguồn '{src}'",

                    f"Nguồn '{src}' ghi '{raw\_g}'. Theo TCVN 5574:2018 phải ghi cấp độ bền '{norm\_g}'.",

                    f"Đổi ký hiệu trên bản vẽ/thuyết minh/BOQ sang cấp độ bền '{norm\_g}'.",

                    7

                )

    unique\_norm\_grades \= set(v\[1\] for v in concrete\_by\_source.values())

    if len(unique\_norm\_grades) \> 1:

        detail\_pairs \= ", ".join(\[f"{s}: {r} ({n})" for s, (r, n) in concrete\_by\_source.items()\])

        add\_issue(

            "CDC-03", "CRITICAL", "KC \+ BOQ \+ FEM",

            "Xung đột cấp độ bền bê tông giữa các tài liệu",

            f"Phát hiện nhiều cấp độ bền khác nhau cho cùng hạng mục: {detail\_pairs}.",

            "Thống nhất cấp độ bền bê tông giữa Bản vẽ, Thuyết minh, Mô hình ETABS và Dự toán BOQ.",

            5

        )

    \# \--- CDC-04: Xung đột cao độ tầng KC vs KT vs FEM \---

    levels \= graph.get("grids\_and\_levels", {}).get("story\_levels", \[\])

    for lv in levels:

        story \= lv.get("story", "?")

        z\_kc \= lv.get("z\_struc\_mm")

        z\_kt \= lv.get("z\_arch\_mm")

        finish\_t \= lv.get("finish\_thickness\_mm", 0\)

        if z\_kc is not None and z\_kt is not None:

            delta \= (z\_kt \- finish\_t) \- z\_kc

            if abs(delta) \> 5:

                add\_issue(

                    "CDC-04", "CRITICAL", "KC \+ KT",

                    f"Cao độ sàn {story} lệch {delta:+.0f}mm giữa KC và KT",

                    f"Tầng {story}: KC \= {z\_kc}mm, KT \= {z\_kt}mm (lớp hoàn thiện \= {finish\_t}mm) \-\> Lệch {delta:+.0f}mm.",

                    "Thống nhất lại cao độ sàn kết cấu và hoàn thiện giữa KC và KT để tránh sai bậc thang và ngưỡng cửa.",

                    5

                )

    \# \--- CDC-05: Xung đột lưới trục KC vs KT vs MEP \---

    grids \= graph.get("grids\_and\_levels", {})

    w\_kc \= grids.get("total\_width\_x\_mm", {}).get("STRUC")

    for other\_disc in ("ARCH", "MEP"):

        w\_other \= grids.get("total\_width\_x\_mm", {}).get(other\_disc)

        if w\_kc is not None and w\_other is not None and abs(w\_other \- w\_kc) \> 10:

            diff \= w\_other \- w\_kc

            add\_issue(

                "CDC-05", "MAJOR", f"KC \+ {other\_disc}",

                f"Tổng chiều rộng lưới trục X của {other\_disc} lệch {diff:+.0f}mm so với KC",

                f"Tổng bề rộng mặt bằng KC \= {w\_kc}mm nhưng {other\_disc} \= {w\_other}mm (sai lệch {diff:+.0f}mm).",

                f"Cập nhật toàn bộ mặt bằng bộ môn {other\_disc} theo đúng lưới trục Kết cấu.",

                7

            )

    \# \--- CDC-06: Kiểm tra đường truyền tải cột & Cột mồ côi \---

    columns \= graph.get("elements", {}).get("columns", \[\])

    for col in columns:

        cid \= col.get("id", "?")

        stories\_present \= col.get("stories\_present", \[\])

        has\_foundation \= col.get("has\_foundation", True)

        in\_arch \= col.get("in\_arch\_plan", True)

        if not has\_foundation or (stories\_present and "T1" not in stories\_present and "F1" not in stories\_present):

            add\_issue(

                "CDC-06", "MAJOR", "KC \+ KT",

                f"Cột {cid} xuất hiện tại {stories\_present} nhưng thiếu cột tầng dưới / móng đỡ",

                f"Cột {cid} (tiết diện {col.get('section', '?')}) chỉ xuất hiện ở {stories\_present}, has\_foundation={has\_foundation}, in\_arch={in\_arch}.",

                f"Kiểm tra đường truyền tải của cột {cid}, bổ sung chi tiết dầm chuyển/móng và đồng bộ với mặt bằng Kiến trúc.",

                7

            )

    \# \--- CDC-07: Kiểm tra tĩnh không đáy dầm vs MEP âm trần \---

    beams \= graph.get("elements", {}).get("beams", \[\])

    for bm in beams:

        bid \= bm.get("id", "?")

        z\_floor \= bm.get("story\_elevation\_mm")

        h\_beam \= bm.get("h\_mm")

        z\_ceil \= bm.get("ceiling\_aff\_mm")

        mep\_req \= bm.get("mep\_clearance\_req\_mm", 450\)

        if all(v is not None for v in (z\_floor, h\_beam, z\_ceil)):

            beam\_bot \= z\_floor \- h\_beam

            mep\_space \= beam\_bot \- z\_ceil

            if mep\_space \< mep\_req:

                sev \= "CRITICAL" if mep\_space \< 250 else "MAJOR"

                add\_issue(

                    "CDC-07", sev, "KC \+ MEP \+ KT",

                    f"Không gian MEP dưới đáy dầm {bid} không đủ ({mep\_space:.0f}mm \< {mep\_req:.0f}mm)",

                    f"Đáy dầm {bid} (h={h\_beam}mm) ở cốt \+{beam\_bot}mm AFF, trần giả ở \+{z\_ceil}mm \-\> Khoảng MEP còn {mep\_space:.0f}mm (yêu cầu \>= {mep\_req:.0f}mm).",

                    "Giảm chiều cao dầm (tăng bề rộng b), hạ cốt trần hoàn thiện hoặc bố trí lỗ xuyên dầm có gia cường.",

                    7

                )

    \# \--- CDC-08: Kiểm tra mũi cọc trong lớp đất địa chất \---

    geo \= graph.get("geotech", {})

    pile\_tip\_spt \= geo.get("pile\_tip\_layer\_spt")

    if pile\_tip\_spt is not None and pile\_tip\_spt \< 15:

        add\_issue(

            "CDC-08", "CRITICAL", "KC \+ GEOTECH",

            f"Mũi cọc đặt trong lớp đất yếu (N\_SPT \= {pile\_tip\_spt} \< 15)",

            f"Cao độ mũi cọc thiết kế ({geo.get('pile\_tip\_elev\_m')}m) nằm trong lớp đất có N\_SPT \= {pile\_tip\_spt}, nguy cơ lún vượt giới hạn theo TCVN 10304:2025.",

            "Tăng chiều dài cọc để ngàm mũi cọc vào lớp đất tốt hoặc tính toán kiểm tra lún nhóm cọc chi tiết.",

            5

        )

    critical\_cnt \= sum(1 for i in issues if i\["Severity"\] \== "CRITICAL")

    major\_cnt \= sum(1 for i in issues if i\["Severity"\] \== "MAJOR")

    warning\_cnt \= sum(1 for i in issues if i\["Severity"\] \== "WARNING")

    status \= "CRITICAL" if critical\_cnt \> 0 else ("MAJOR" if major\_cnt \> 0 else ("WARNING" if warning\_cnt \> 0 else "PASS"))

    return {

        "Verification\_Type": "Cross-Document-Conflict-Control",

        "Timestamp": datetime.now().isoformat(),

        "Project\_Name": graph.get("project\_name", "N/A"),

        "Overall\_Status": status,

        "Summary": {

            "Total\_Issues": len(issues),

            "Critical\_Count": critical\_cnt,

            "Major\_Count": major\_cnt,

            "Warning\_Count": warning\_cnt,

        },

        "Issues": issues,

    }

## 4\. KỊCH BẢN KIỂM THỬ BẮT BUỘC CHO SPRINT 1 & SPRINT 2

Antigravity cần khởi tạo và chạy thành công 2 bộ kiểm thử tự động sau:

1. **Bộ kiểm thử Sprint 1 (`.agents/tests/test_sprint1_reporting.py`):**  
   * **Test 1.1 (`generator_full.py` Material Accuracy):** Kiểm tra `CONCRETE_GRADES["B30"]["Rbt"] == 1.15` (không phải `1.20`), `STEEL_GRADES_RC["CB400-V"]["Rs"] == 350` (không phải `340`), `STEEL_GRADES_RC["CB500-V"]["Rs"] == 435` và `Rsc == 400`.  
   * **Test 1.2 (`export_calc_sheet.py` No Raw JSON & Full Substitution):** Chạy `generate_markdown()` với đầu ra thật của `calc_anchorage_lap.py` và `calc_rc_section.py`. Xác nhận chuỗi kết quả **không chứa** ```` ```json ```` ở Mục 2, **có chứa** đầy đủ dòng `- **Thay số:**` ở mọi bước tính trong Mục 4, và hiển thị đầy đủ các chỉ số `eta_*` trong bảng Mục 5\.  
   * **Test 1.3 (`report_consistency_check.py` TCVN Symbols):** Kiểm tra trích xuất và đối chiếu khớp các ký hiệu `Rb`, `Rbt`, `Rs`, `L_an`, `L_lap` giữa file thuyết minh và JSON handoff.  
2. **Bộ kiểm thử Sprint 2 (`.agents/tests/test_sprint2_conflict_control.py`):**  
   * Tạo fixture tái hiện đúng hồ sơ dự án thực tế [ThamTra\_ClashDetection\_TMTT.md](https://drive.google.com/file/d/1x2O7wc5zAK37xQq1KNhmaBQV4ufBWxH3/view?usp=drivesdk) (*"Nhà Nguyên \- Trương Công Định"*):  
     * KC ở giai đoạn `S4`, KT ở giai đoạn `S3` \$\\rightarrow\$ Bắt lỗi `CDC-01` (`CRITICAL`).  
     * Thiếu bộ môn `MEP_PLUMB` \$\\rightarrow\$ Bắt lỗi `CDC-02` (`MAJOR`).  
     * Bản vẽ ghi `M250` \$\\rightarrow\$ Cảnh báo quy đổi sang `B20` theo `CDC-03`.  
     * Cao độ Tầng 2 KC `+3850mm` vs KT `+3900mm` \$\\rightarrow\$ Bắt lỗi `CDC-04` (`CRITICAL`, lệch `+50mm`).  
     * Lưới trục MEP rộng `18000mm` vs KC `16800mm` \$\\rightarrow\$ Bắt lỗi `CDC-05` (`MAJOR`, lệch `+1200mm`).  
     * Cột `CC1`, `CC3` chỉ có ở Tầng 2, không có móng \$\\rightarrow\$ Bắt lỗi `CDC-06` (`MAJOR`).  
     * Dầm `D1X1*` (\$250\\times 450\$) với trần `+2800mm` và ống gió VRV yêu cầu `450mm` \$\\rightarrow\$ Bắt lỗi `CDC-07` (`MAJOR`).

## 5\. CÂU LỆNH CHỈ DẪN THỰC THI CHO ANTIGRAVITY IDE (SPRINT 1 & SPRINT 2\)

> **Hướng dẫn cho User:** Sau khi Antigravity hoàn tất bản vá v7.1, bạn hãy dán câu lệnh dưới đây để Antigravity triển khai tiếp **Sprint 1 (Thuyết minh kèm theo)** và **Sprint 2 (Đọc dữ liệu & Kiểm soát xung đột hồ sơ)**:

Chào Antigravity, hãy đọc toàn bộ hồ sơ đặc tả kỹ thuật tại file \`.agents/docs/ARGON\_SPRINT\_1\_2\_SPEC\_v8.0.md\` và triển khai tuần tự Lộ trình Sprint 1 & Sprint 2:

\[SPRINT 1 — NÂNG CẤP THUYẾT MINH TÍNH TOÁN & PHỤ LỤC STEP-BY-STEP\]

1\. Cập nhật \`.agents/skills/SKILL\_PHULUC/generator\_full.py\` theo Mục 2.2.A: Sửa bảng CONCRETE\_GRADES và STEEL\_GRADES\_RC đúng tuyệt đối theo TCVN 5574:2018 Bảng 7 & Bảng 13 (B30 có Rbt=1.15 MPa; CB400-V có Rs=350 MPa; CB500-V có Rs=435 MPa, Rsc=400 MPa; bổ sung B12.5, B22.5, B45-B60, CB240-T, CB300-T).

2\. Nâng cấp \`.agents/skills/Structural\_Design\_Engineer/scripts/export\_calc\_sheet.py\` theo Mục 2.2.B:

   \- Thay thế đoạn in raw JSON (\`json.dumps\`) ở Mục 2 bằng bảng thông số kỹ thuật chuẩn (\`\_render\_input\_table\`).

   \- Sửa lỗi mất bước thay số ở Mục 4 bằng cách đọc \`log.get("Substitution") or log.get("Values")\` và hiển thị đầy đủ số trang tiêu chuẩn.

   \- Nâng cấp bảng tổng hợp Mục 5 để tự động duyệt toàn bộ các chỉ số \`eta\_\*\` và kết quả tính toán thay vì chỉ cố định 2 dòng Uốn & Cắt.

3\. Cập nhật \`.agents/skills/SKILL\_PHULUC/templates/TMTT\_FULL.md\` và \`docx\_generator.py\`: Thay QCVN 03:2012/BXD và TT 06/2021/TT-BXD bằng QCVN 03:2022/BXD và TT 02/2025/TT-BXD, bổ sung TCVN 9386:2025, TCVN 10304:2025; đổi NORMAL\_FONT trong \`docx\_generator.py\` từ 'Arial' sang 'Times New Roman'.

4\. Cập nhật \`Design\_Evaluation/scripts/report\_dispatcher.py\` (hỗ trợ đồng thời schema tiếng Anh của SKILL\_BRIDGE.md và khóa tiếng Việt) và \`SKILL\_VERIFY/scripts/report\_consistency\_check.py\` (bổ sung regex kiểm tra các ký hiệu TCVN: Rb, Rbt, Rs, Rsw, L\_an, L\_lap, a\_crc) theo Mục 2.2.C.

\[SPRINT 2 — BỘ ĐỌC HỒ SƠ ĐẦU VÀO & KIỂM SOÁT XUNG ĐỘT CHÉO\]

5\. Tạo schema \`.agents/\_SHARED/schemas/project\_truth\_graph.schema.json\` và script đọc dữ liệu đa nguồn \`.agents/skills/SKILL\_VERIFY/scripts/ingest\_project\_docs.py\` theo Mục 3.1 & 3.2.

6\. Tạo script \`.agents/skills/SKILL\_VERIFY/scripts/cross\_doc\_conflict\_checker.py\` cài đặt 8 quy tắc kiểm soát xung đột hồ sơ (CDC-01 đến CDC-08) theo Mục 3.3 & 3.4, tích hợp vào \`SKILL\_VERIFY/scripts/verify\_all.py\` và cập nhật từ khóa điều phối trong \`Global\_Dispatcher/scripts/keyword\_database.json\`.

7\. Tạo và chạy 2 bộ unit tests \`.agents/tests/test\_sprint1\_reporting.py\` và \`.agents/tests/test\_sprint2\_conflict\_control.py\` theo Mục 4, sau đó chạy lại \`python .agents/tests/run\_all\_tests.py\` để xác nhận 100% PASS.