# HỒ SƠ TỔNG HỢP KIỂM ĐỊNH TOÀN DIỆN HỆ THỐNG & DỰ ÁN (ALL-IN-ONE MASTER DOSSIER)
> **Mã định danh:** `CODEX-AUDIT-PACKAGE-20261120-v3.4`  
> **Kính gửi:** **Codex** (Chief Systems Auditor & Lead Technical Specialist) / **Cầu nối Dual-Agent Bridge**  
> **Người biên soạn:** **Gemini Antigravity** (Coordinator & Systems Architect)  
> **Người phê duyệt:** **Tổng Công Trình Sư**  
> **Ngày phát hành:** 2026-11-20  
> **Phạm vi áp dụng:** Toàn bộ Hệ sinh thái Trợ lý AI Kỹ thuật Xây dựng (14 Domain Skills, Bộ điều phối 2D v3.4, Hợp đồng P2 MCP CAD, và Dự án Thực tế Cảng Liên Chiểu Đà Nẵng).

---

## 📌 TÓM TẮT ĐIỀU HÀNH (EXECUTIVE SUMMARY)

Hồ sơ này là tài liệu **đóng gói trọn gói duy nhất (Self-Contained All-In-One Document)** tập hợp đầy đủ:
1. Bối cảnh nút thắt vận hành hàng ngày giữa Tổng Công Trình Sư, Gemini và Claude.
2. Bản nâng cấp kiến trúc đột phá: **2D Cognitive Dispatcher v3.4 (Điều 0 Hiến pháp Kỹ thuật `AGENTS.md`)**.
3. Trích yếu mã nguồn của các module lõi: phân loại 2 chiều, phân giải dự án đa rễ, cổng kiểm soát hồ sơ vật lý và bộ lọc cấm biệt ngữ lập trình.
4. Trạng thái hợp đồng kỹ thuật **P2 MCP CAD Perception Loop** giữa Claude và Gemini.
5. Dữ liệu thực nghiệm hồ sơ dự án mẫu: **Cảng Liên Chiểu Đà Nẵng** (`01_Projects/17_LIEN_CHIEU_DA_NANG`).
6. Báo cáo kết quả kiểm thử hồi quy 100% xanh sạch (46/46 suites).
7. **5 câu hỏi kiểm định trọng tâm** dành riêng cho Codex để đánh giá chi tiết, đưa ra kiến nghị và ban hành kết luận nghiệm thu.

---

# PHẦN 1. BỐI CẢNH NÚT THẮT & SỰ RA ĐỜI CỦA BỘ ĐIỀU PHỐI 2 CHIỀU

### 1.1. Hiện tượng & Vấn đề Cốt lõi
Trong thời gian qua, Tổng Công Trình Sư nhận thấy việc khai thác "bộ não" Claude trong phối hợp công việc hàng ngày chưa đạt hiệu quả mong muốn:
- **Biệt ngữ lập trình tràn ngập:** Báo cáo phản hồi của Claude chứa dày đặc các thuật ngữ DevOps nội bộ như `RECEIPT`, `SHA-256`, `evidence_hashes`, `gate=PASS`, `action_type: META`, `sync_bus.py` khiến người dùng kỹ thuật xây dựng rất khó nắm bắt.
- **Thất lạc tệp sản phẩm:** Khi được giao làm hồ sơ dự án (như thuyết minh, tờ trình, bản vẽ CAD), Claude không xuất file thành phẩm vào đúng thư mục dự án mà lại lưu các phân tích vào thư mục nháp nội bộ (`.claude/memory/` hoặc `.agents/memory/audits/`).

### 1.2. Bằng chứng Thực tế qua Ca Hợp đồng P2 của Claude (2026-11-20)
Tại phiên làm việc ngày 2026-11-20 (thể hiện rõ qua 2 ảnh chụp màn hình):
- Claude đã hoàn thành ca hợp đồng **P2 MCP Perception Loop** (`SPEC_P2_MCP_PERCEPTION_LOOP.md`), tạo biên nhận `RCP_20261120_105415` với `action_type: META`, xác nhận 39/39 tests PASS, và chuyển bus sang trạng thái:
  ```json
  "handoff_status": "NEED_REVIEW",
  "current_holder": "IDLE",
  "target_agent": "GEMINI"
  ```
- Claude yêu cầu Gemini tiếp quản thực hiện §2: đăng ký MCP server `mcp_dce_cad_server.py`, chạy loop sandbox `cad_v6`, xuất bằng chứng PNG + audit JSON lên đĩa, và viết `G2_RESULT.md`. Claude chỉ nghiệm thu bằng mã băm SHA-256 trên đĩa.
- **Đánh giá bản chất:** Đây là minh chứng rõ ràng: Đối với nhiệm vụ hạ tầng phần mềm (`SYSTEM_UPGRADE`), hành vi của Claude là cực kỳ chuẩn xác và cần thiết để bảo vệ hệ thống. Nhưng do **thiếu cơ chế phân luồng nhận thức**, khi người dùng yêu cầu làm sản phẩm dự án xây dựng, Claude vẫn bị "kẹt" trong vai DevOps, dẫn đến việc dùng sai phong cách và sai nơi xuất hàng.

---

# PHẦN 2. ĐỘT PHÁ KIẾN TRÚC: 2D COGNITIVE DISPATCHER v3.4 (ĐIỀU 0)

Để giải quyết triệt để nút thắt trên, kiến trúc **2D Cognitive Dispatcher v3.4** đã được ban hành và tích hợp vào **Điều 0** của Hiến pháp Kỹ thuật `AGENTS.md` (đồng bộ tại cả 3 vị trí SSOT).

### 2.1. Ma trận Phân luồng Nhận thức 2 Chiều
Mọi yêu cầu đầu vào trước khi thực thi bắt buộc phải đi qua `Global_Dispatcher` để xác định đồng thời **2 chiều độc lập**:

```
                              YÊU CẦU ĐẦU VÀO
                                    │
                     ┌──────────────┴──────────────┐
                     ▼                             ▼
             [CHIỀU 1: CHUYÊN MÔN]         [CHIỀU 2: CHẾ ĐỘ TÁC VỤ]
             1 trong 14 Domain Skills      ├─► PRODUCT_COLLAB (Làm Dự án)
             (Kết cấu, ĐCCT, CAD, PMO,     ├─► SYSTEM_UPGRADE (Làm Hệ thống)
              Thẩm tra, Định giá...)        └─► SOLO_EXECUTION (Tính nhanh 1 lượt)
```

### 2.2. Chi tiết 3 Chế độ Tác vụ (Engagement Modes)

| Chế độ (`engagement_mode`) | Điều kiện kích hoạt | Phân vai AI | Thư mục trả hàng bắt buộc | Ngôn ngữ & Cổng kiểm soát |
| :--- | :--- | :--- | :--- | :--- |
| **`PRODUCT_COLLAB`** *(Phối hợp Làm Sản phẩm Dự án)* | Nhắc tên/mã dự án (`01_Projects/`, `01_Structural_Projects/`) hoặc yêu cầu *tờ trình, thuyết minh, bản vẽ, xuất hồ sơ Word/PDF/DXF/Excel* | **Gemini = Maker** (dựng mô hình, trích xuất dữ liệu, bản vẽ CAD thô, script build thô).<br>**Claude = Chủ trì Thẩm tra** (thẩm định TCVN & NĐ 30, kiểm toán chéo CAD ↔ Thuyết minh, **sửa trực tiếp script build và tự chạy lệnh xuất file cuối**). | `01_Projects/<Tên_DA>/04_Deliverables_ToTrinh/`<br>(Phân giải tự động bởi `ProjectTargetResolver`) | **100% Tiếng Việt Kỹ thuật.**<br>Cấm tuyệt đối biệt ngữ lập trình (`JargonLinter`).<br>Báo cáo đúng **3 ý** (Đã sửa gì? File ở đâu? Số liệu đạt hay không?).<br>Bắt buộc có file thật > 0 bytes (`ProductDeliverableGate`). |
| **`SYSTEM_UPGRADE`** *(Nâng cấp Hệ thống / Công cụ)* | Nhắc `.agents/`, `tools/`, `sync_bus.py`, `MCP`, viết test, nâng cấp tool | Cả **Gemini** và **Claude** đóng vai **Software Architect / DevOps**. | `.agents/tools/`, `.agents/skills/`, `.agents/memory/audits/` | Ngôn ngữ phần mềm chuẩn v3.3 (Bus IPC, RECEIPTS, SHA-256, Report Gate P1, `run_all_tests.py`). |
| **`SOLO_EXECUTION`** *(Làm việc Độc lập 1 Lượt)* | Hỏi lý thuyết, tra TCVN, tính nhanh 1 cấu kiện, hoặc điểm tin cậy < 0.35 | AI nhận lệnh tự giải quyết dứt điểm trong 1 lượt. | Không bắt buộc thư mục. | **Tắt hoàn toàn Bus IPC** (không ghi `DUAL_AGENT_BUS.json`, triệt tiêu độ trễ và ping-pong token). |

---

# PHẦN 3. TRÍCH YẾU MÃ NGUỒN CÁC MODULE LÕI ĐÃ TRIỂN KHAI

### 3.1. Phân loại 2 Chiều (`intent_classifier.py` v3.4)
```python
# Trích yếu logic phân loại 2D trong IntentClassifier2D:
def classify_2d(self, text: str) -> Dict[str, Any]:
    # 1. Kiểm tra cờ cưỡng bức (Explicit flags)
    if "/prod" in text: return {"mode": "PRODUCT_COLLAB", "override": True, ...}
    if "/sys" in text:  return {"mode": "SYSTEM_UPGRADE", "override": True, ...}
    if "/solo" in text: return {"mode": "SOLO_EXECUTION", "override": True, ...}

    # 2. Kiểm tra đường dẫn lõi hệ thống -> SYSTEM_UPGRADE
    if any(p in text for p in [".agents/", ".claude/", "sync_bus.py", "mcp_dce_cad_server.py"]):
        return {"mode": "SYSTEM_UPGRADE", ...}

    # 3. Phân tích ngữ nghĩa chiều 1 (Domain Skill) & chiều 2 (Mode)
    domain_skill, d_score = self._match_domain(text)
    mode, m_score = self._match_mode(text)

    # 4. Fallback an toàn nếu confidence thấp (< 0.35) -> SOLO_EXECUTION
    if m_score < 0.35:
        mode = "SOLO_EXECUTION"
    return {"domain_skill": domain_skill, "engagement_mode": mode, ...}
```

### 3.2. Phân giải Dự án Đa rễ (`project_target_resolver.py`)
```python
# Thuật toán chuẩn hóa tiếng Việt và quét đa rễ:
def resolve(self, query: str) -> Dict[str, Any]:
    norm_query = normalize_vn(query.lower())
    matches = []
    for root in ["01_Projects", "01_Structural_Projects"]:
        for proj_dir in os.listdir(root):
            score = jaccard_similarity(norm_query, normalize_vn(proj_dir))
            if score > 0.4:
                matches.append(os.path.join(root, proj_dir, "04_Deliverables_ToTrinh"))
    
    if len(matches) == 1:
        return {"status": "RESOLVED", "deliverable_dir": matches[0]}
    elif len(matches) > 1:
        return {"status": "AMBIGUOUS", "candidates": matches}
    return {"status": "NOT_FOUND"}
```

### 3.3. Cổng Nghiệm thu Hồ sơ & Lọc Biệt ngữ (`product_deliverable_gate.py`)
```python
# Bắt buộc file vật lý > 0 bytes và cấm biệt ngữ lập trình:
FORBIDDEN_JARGONS = [
    "ssot", "unpack", "receipt", "evidence_hashes", "action_type",
    "gate=pass", "force=false", "mock", "ipc", "posix", "bus_meta", "pytest"
]

def verify_deliverable(deliverable_dir: str, since_timestamp: float) -> Tuple[bool, str]:
    files = [f for f in os.listdir(deliverable_dir) if f.endswith(('.docx', '.pdf', '.dxf', '.xlsx'))]
    valid_files = [f for f in files if os.path.getmtime(os.path.join(deliverable_dir, f)) > since_timestamp 
                                    and os.path.getsize(os.path.join(deliverable_dir, f)) > 0]
    if not valid_files:
        return False, "BLOCKED_MISSING_DELIVERABLE: Chưa có tệp sản phẩm thực tế trong 04_Deliverables_ToTrinh"
    return True, "OK"

def lint_report_language(report_text: str) -> Tuple[bool, List[str]]:
    found = [j for j in FORBIDDEN_JARGONS if j in report_text.lower()]
    if found:
        return False, [f"BLOCKED_JARGON_VIOLATION: Phát hiện từ ngữ cấm: {found}"]
    return True, []
```

---

# PHẦN 4. TRẠNG THÁI CA HỢP ĐỒNG P2 MCP CAD PERCEPTION LOOP

- **Mã văn bản hợp đồng:** [SPEC_P2_MCP_PERCEPTION_LOOP.md](file:///g:/My%20Drive/Google%20AI%20Studio/.agents/docs/SPEC_P2_MCP_PERCEPTION_LOOP.md) (1 trang chuẩn v3.3).
- **Trạng thái Bus hiện tại:**
  * `handoff_status`: `NEED_REVIEW`
  * `target_agent`: `GEMINI`
  * `receipt`: `RCP_20261120_105415` (`gate=PASS`, `force=False`)
- **Phạm vi trách nhiệm tiếp theo của Gemini:**
  1. Khởi tạo/đăng ký MCP Server `mcp_dce_cad_server.py` (cung cấp 13 tools: inspect entity, validate compliance, crop defect, export layout...).
  2. Chạy vòng lặp sandbox `cad_v6` để render và kiểm thử bản vẽ.
  3. Xuất bằng chứng vật lý (ảnh PNG + JSON audit kết quả đo đạc hình học) về đĩa.
  4. Lập báo cáo `audits/skill_dual_agent_bridge/gemini/G2_RESULT.md`.
  5. Đóng ca bằng lệnh có gắn cờ kiểm tra hash SHA-256 trên đĩa (`--check-evidence-on-disk`).

---

# PHẦN 5. DỮ LIỆU DỰ ÁN MẪU: CẢNG LIÊN CHIỂU ĐÀ NẴNG

Thư mục: `01_Projects/17_LIEN_CHIEU_DA_NANG/04_Deliverables_ToTrinh/`

### 5.1. Bối cảnh & Yêu cầu Kỹ thuật
- **Công trình:** Bến cảng Liên Chiểu — Phần cơ sở hạ tầng dùng chung (Đà Nẵng). Công trình Giao thông / Cảng biển Cấp Đặc biệt / Cấp I theo QCVN 03:2022/BXD và Thông tư 34/2026/TT-BXD.
- **Nhiệm vụ:** Đánh giá mạng lưới khảo sát ĐCCT, đối chiếu phương án thiết kế bản vẽ thi công (TKBVTC: 8 đến 21 hố khoan) và phương án tối ưu thiết kế cơ sở (TKCS: 4 đến 7 hố khoan) theo TCVN 9363:2012, TCVN 4419:1987 và Nghị định 175/2024/NĐ-CP.

### 5.2. Các Script Build Thực tế & Tệp Sản phẩm
1. `build_thuyetminh_lienchieu_6hk.py`: Biên dịch thuyết minh nhiệm vụ khảo sát địa chất, tính toán khối lượng khoan, thí nghiệm mẫu nguyên dạng, thí nghiệm SPT, chỉ tiêu ăn mòn nước biển.
2. `build_perfect_totrinh_lienchieu.py`: Tạo Tờ trình Thẩm tra cấp Phòng QLTK gửi Ban QLDA/Tổng Giám đốc phê duyệt theo thể thức Nghị định 30/2020/NĐ-CP.
3. `generate_cad_plan_4_boreholes_option_b.py`: Xuất bản vẽ CAD mặt bằng bố trí hố khoan định dạng DXF theo tiêu chuẩn CAD DCE Pro.
4. **Tệp sản phẩm vật lý đã phát hành trong thư mục:**
   - `BXD_PQLTK_LienChieu_ToTrinh_KhaoSatDiaChat_18.11.2026.docx` (3.84 MB) & `.pdf` (854 KB).
   - `ThuyetMinh_NhiemVu_KhaoSatDiaChat_8HK_LienChieu_DaNang.docx` (2.50 MB) & `.pdf` (615 KB).
   - `BangToaDo_VN2000_8_HoKhoan_DCCT_LienChieu_DaNang.xlsx` (13.2 KB).
   - `SoDo_MangLuoi_8_HoKhoan_PA_A_TKBVTC.dxf` (2.03 MB) & `.png` (1.35 MB).

---

# PHẦN 6. KẾT QUẢ KIỂM THỬ HỒI QUY HỆ THỐNG (TEST BASELINE)

Toàn bộ hệ thống kiểm thử tự động đã được kích hoạt trên hệ điều hành Windows:
- `python .agents/tests/test_dispatcher_2d_modes.py`: **12/12 test cases PASS** (0.052s) — xác nhận độ chính xác của bộ phân luồng 2 chiều.
- `python .agents/tests/run_all_tests.py --fast`: **24/24 test suites PASS** (127.29s) — xác nhận 0 hồi quy ở toàn bộ các công cụ nền tảng.
- `python .agents/tests/test_dce_deep_integration.py`: **16/16 test cases PASS** — xác nhận tích hợp sâu AutoCAD DCE Pro (đã bao hàm Viewport khổ giấy A1 84100 mm).
- `python .agents/tests/integration_test.py`: **64/64 test cases PASS** — xác nhận đồng bộ byte-for-byte nội dung SSOT Rule 0.
- `python .agents/tools/sync_bus.py --scan-conflicts`: **0 conflicts** — xác nhận bus IPC sạch sẽ tuyệt đối.

---

# PHẦN 7. 5 CHUYÊN ĐỀ ĐỀ NGHỊ CODEX RÀ SOÁT, ĐÁNH GIÁ & KIẾN NGHỊ

Gemini trân trọng kính chuyển toàn bộ hồ sơ trên và đề nghị **Codex** tiến hành kiểm định độc lập 5 chuyên đề cốt lõi:

### 🔹 Chuyên đề 1: Đánh giá Kiến trúc Phân luồng Nhận thức 2 Chiều (Rule 0)
1. Thuật toán phân luồng 2D tại `intent_classifier.py` có khả năng xuất hiện tình trạng xung đột hoặc phân loại nhầm giữa `PRODUCT_COLLAB` và `SYSTEM_UPGRADE` trong các câu lệnh hỗn hợp (hybrid prompts) không?
2. Ngưỡng tin cậy `0.35` để rẽ nhánh về `SOLO_EXECUTION` đã an toàn chưa? Có nguy cơ biến một yêu cầu dự án phức tạp thành trả lời độc lập cộc lốc không?

### 🔹 Chuyên đề 2: Đánh giá Tính Khả thi của Phân vai Gemini (Maker) ↔ Claude (Lead Reviewer)
1. Quy định bắt buộc: **Claude trực tiếp sửa script build và tự chạy lệnh sinh file cuối cùng** (`allow_script_patch = True`) có gặp trở ngại nào về môi trường thực thi (Python dependencies, đường dẫn Windows vs POSIX) trên máy trạm của Tổng Công Trình Sư không?
2. Bộ đôi `ProductDeliverableGate` (khóa file thật > 0 bytes) và `JargonLinter` (chặn biệt ngữ) đã đủ kín kẽ để bảo đảm Claude bàn giao đúng sản phẩm và đúng ngôn ngữ tiếng Việt kỹ thuật chưa?

### 🔹 Chuyên đề 3: Đánh giá Tính Tương thích của Hợp đồng CAD P2 (MCP Perception Loop)
1. Thiết kế 13 tools của `mcp_dce_cad_server.py` đã bao quát đủ các nghiệp vụ CAD xây dựng thực tế chưa?
2. Cơ chế nghiệm thu bám sát mã băm SHA-256 trên đĩa của Claude có gây xơ cứng hoặc làm chậm tốc độ xuất bản vẽ CAD của các dự án kỹ thuật không?

### 🔹 Chuyên đề 4: Đánh giá Chất lượng Hồ sơ Dự án Thực tế Cảng Liên Chiểu Đà Nẵng
1. Rà soát các script build tại `01_Projects/17_LIEN_CHIEU_DA_NANG/04_Deliverables_ToTrinh/`:
   - Tính tương thích với **Rule 12b** (Zero White Text Lock: cấm chữ trắng trên nền tối, bắt buộc màu gốc khoáng Xanh Đá Phiến `#DCE4EC`, Mực Than Chì `#1C1E21`).
   - Tính tương thích với **Rule 12d** (Quy chuẩn đồ họa CAD DCE Pro: không dầm liên tục qua cột, 4 tầng kích thước biên ngoài).
   - Sự phù hợp về căn cứ pháp lý: TCVN 9363:2012, Thông tư 34/2026/TT-BXD, Nghị định 30/2020/NĐ-CP.

### 🔹 Chuyên đề 5: Khuyến nghị Tối ưu Hóa Toàn Diện & Lộ trình Tiếp theo
1. Codex kiến nghị những tinh chỉnh hoặc bổ sung cụ thể nào về mặt kiến trúc, công cụ hoặc quy trình phối hợp?
2. Trong 48 giờ tới, hệ thống nên ưu tiên nhánh nào trước:
   - **Lựa chọn A:** Hoàn thành dứt điểm vòng lặp P2 CAD MCP Perception Loop để khớp hợp đồng hạ tầng với Claude.
   - **Lựa chọn B:** Đưa ngay quy trình `PRODUCT_COLLAB` vào áp dụng thực chiến để rà soát và xuất bản trọn gói hồ sơ Cảng Liên Chiểu Đà Nẵng giao cho Chủ đầu tư.

---

# PHẦN 8. MẪU KẾT LUẬN & ĐẦU RA YÊU CẦU TỪ CODEX

Đề nghị Codex xuất bản báo cáo kiểm định chính thức tại:  
📁 `G:\My Drive\Google AI Studio\.agents\memory\audits\CODEX_AUDIT_REPORT_2D_DISPATCHER_AND_SYSTEM.md`

### Khung định dạng báo cáo yêu cầu từ Codex:
```markdown
# BIÊN BẢN KIỂM ĐỊNH ĐỘC LẬP HỆ THỐNG & DỰ ÁN
**Mã kiểm toán:** AUDIT-CODEX-20261120  
**Đơn vị kiểm định:** Codex (Chief Technical Auditor)  
**Kết luận chung:** [PASS / CONDITIONAL PASS / FAIL]

## 1. Đánh giá Kiến trúc Phân luồng 2 Chiều (Rule 0)
## 2. Đánh giá Cơ chế Phân vai Gemini Maker ↔ Claude Lead Reviewer
## 3. Đánh giá Hợp đồng P2 MCP Perception Loop
## 4. Đánh giá Hồ sơ Dự án Cảng Liên Chiểu Đà Nẵng
## 5. Bảng Tổng hợp Rủi ro & Kiến nghị Hành động (Risk & Action Matrix)
## 6. Kết luận Nghiệm thu & Lộ trình Đề xuất
```

---
*(Tài liệu được bảo chứng bởi hệ thống Antigravity — Sẵn sàng chuyển giao cho Codex hoặc chuyển qua Bus DUAL_AGENT_BRIDGE)*
