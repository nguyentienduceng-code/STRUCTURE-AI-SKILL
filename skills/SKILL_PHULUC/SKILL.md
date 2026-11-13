---
name: SKILL_PHULUC
version: 3.1.0
last_updated: 2026-11-12
description: "Master Engine Lập Thuyết minh Tính toán Kết cấu, Địa kỹ thuật, Biện pháp Thi công (BPTC) và Phụ lục Tính toán chi tiết step-by-step theo TCVN. Tự động biên dịch từ Calculator JSON sang Markdown & xuất file Word (.docx) chuẩn 2 Bộ Chuan (Bộ 1 BKTECHS hoặc Bộ 2 TVTK Đa Hạng mục). Tích hợp Thư viện Phụ lục Hiện đại và Cổng Kiểm toán Độc lập 8 Tiêu chí (audit_phuluc_docx.py)."
---
# Skill Phụ Lục & Thuyết Minh Tính Toán Kỹ Thuật (SKILL_PHULUC v3.0 Master Engine)

Tạo hồ sơ Thuyết minh Tính toán Kết cấu, Địa kỹ thuật, Gia cường và Biện pháp Thi công (BPTC) chi tiết step-by-step theo tiêu chuẩn TCVN và xuất ra file Word (`.docx`) với đầy đủ Bìa đôi, Mục lục tự động (`Auto-TOC`), phân cấp Heading màu sắc khoáng vật tự nhiên, công thức Office Math (`OMML`) và Header/Footer chuyên nghiệp.

Tích hợp bộ ba công cụ cốt lõi:
1. **`json_to_tmtt_compiler.py`**: Trình biên dịch tự động kết quả tính toán từ file JSON của bất kỳ Calculator nào thành Thuyết minh Markdown chuẩn 6 chương / 9 chương và tự động xuất Word DOCX.
2. **Thư viện Template Phụ lục Chuyên sâu Mới**:
   - `templates/APPENDIX_HOIST_CRANE.md`: Thuyết minh tính toán Vận thăng & Cẩu tháp xây dựng.
   - `templates/APPENDIX_FORMWORK_SHORING.md`: Thuyết minh Ván khuôn sàn/cột/tường & Hệ giáo Shoring Ringlock/Nêm.
   - `templates/APPENDIX_STEEL_PORTAL_FRAME.md`: Thuyết minh Khung nhà thép tiền chế & Liên kết bu lông TCVN 5575:2024.
   - Cùng 7 template bê tông cốt thép & nền móng truyền thống: `APPENDIX_COLUMN_RC.md`, `APPENDIX_SLAB_RC.md`, `APPENDIX_PILE_FOUNDATION.md`, `APPENDIX_STAIR_RC.md`, `APPENDIX_WATER_TANK.md`, `APPENDIX_STRIP_FOUNDATION.md`, `APPENDIX_RETAINING_WALL.md`.
3. **`audit_phuluc_docx.py` (Cổng Kiểm toán Độc lập 8 Tiêu chí)**: Tự động kiểm tra chất lượng file `.docx` sau khi xuất, triệt tiêu 100% chữ trắng trên nền tối (Rule 12b), bảo đảm sàn cỡ chữ $\ge 10\text{ pt}$ (Rule 12e), không mã thô LaTeX `$`, không double bullet `• •`, độ sâu diễn giải $\ge 800$ từ (Rule 13), và đầy đủ Approval Matrix & Disclaimer AI (Rule 8).

---

## Khi Nào Sử Dụng Skill Này

- Khi người dùng yêu cầu lập mới, gộp, hoặc chuẩn hóa **Thuyết minh Tính toán Kết cấu (TMTT)**, **Thuyết minh Biện pháp Thi công (BPTC)**, **Báo cáo Thẩm tra Kết cấu**, hoặc **Phụ lục Tính toán chi tiết (Calculation Sheet)**.
- Khi người dùng yêu cầu xuất hồ sơ thuyết minh theo **Bộ 1 (Chuẩn BKTECHS)** hoặc **Bộ 2 (Chuẩn TVTK Đa Hạng Mục)**.
- Khi cần chuyển đổi trực tiếp kết quả tính toán JSON từ các Calculator sang tài liệu Word `.docx` hoàn chỉnh phục vụ thẩm duyệt pháp lý.
- Khi cần kiểm toán chất lượng hồ sơ `.docx` trước khi bàn giao cho Chủ đầu tư hoặc nộp Cơ quan Chuyên môn về Xây dựng.

---

## Lựa Chọn 2 Bộ Chuẩn Trình Bày và Bố Trí Chapter

Mỗi khi xuất hồ sơ thuyết minh, hỗ trợ 2 bộ chuẩn trình bày (mặc định ưu tiên **Bộ 1 - BKTECHS** nếu người dùng không chỉ định khác):

### 1. Bộ Chuẩn 1: Phong cách `bktechs` (Mặc định Ưu tiên — Viện / Trường / Thẩm tra / Chuyên sâu)

- **Ứng dụng**: Thuyết minh tính toán chuyên sâu 1 đến 2 hạng mục (Bể nước ngầm, Bể tự hoại, Móng cọc, Tường chắn, Biện pháp thi công hố đào, Vận thăng & Cẩu tháp, Cốp pha shoring, Gia cường CFRP) và Báo cáo thẩm tra kết cấu.
- **Bố cục Section 0 (Bìa đôi + Mục lục)**:
  - **Trang 1 (Bìa chính)**: Tiêu đề Trường ĐH Bách Khoa / BKTECHS, dải băng xanh Navy (`#1E3246`), Logo lục giác BKTECHS ở giữa, tên hồ sơ cỡ lớn (`24pt`), và bảng thông tin Dự án / Hạng mục / Chủ đầu tư. Không hiển thị Header/Footer trên Trang 1 (`different_first_page_header_footer = True`).
  - **Trang 2 (Bìa phụ ký duyệt)**: Bảng kiểm soát chất lượng 3 cột (`Thực hiện` - `Kiểm tra` - `Chủ trì` kèm học vị và số CCHN) và khối ký đóng dấu Chủ đầu tư / Đơn vị tư vấn.
  - **Trang 3 (Mục lục tự động)**: Trường `TOC \o "1-3" \h \z \u` tự động cập nhật kèm bảng tóm tắt cấu trúc chương mục.
- **Bố cục Section 1 (Nội dung chính)**:
  - Ngắt Section mới và khởi động lại số trang từ `Trang 1 / N`.
  - **Header**: Tên đơn vị màu xanh (`#1E3246`) + Tên Dự án/Hạng mục phía trên đường kẻ ngang màu **Đồng Thau Trầm (`#A67C37` Bronze Ochre)**.
  - **Footer**: `BKTECHS || Địa chỉ | Liên hệ || Trang 1 / N` với vạch đôi `||` màu vàng cam.
  - **Typography & Màu sắc**: Font `Times New Roman` (`12pt` body, `10.5pt` table). `Heading 1` (`1.`): `14pt` Bold IN HOA màu Xanh Navy (`#1E3246`); `Heading 2` (`1.1.`): `13pt` Bold màu Xanh lam sáng (`#2E4A62`); `Heading 3` (`1.1.1.`): `12pt` Bold Italic màu `#4A5D6E`. Bảng biểu có header nền Xanh Đá Phiến Sương Nhạt (`#DCE4EC`) chữ Xanh Đá Phiến Đậm (`#1E3246`) — cấm dùng chữ trắng trên nền tối và dòng **Kết luận / Kiểm tra (`ĐẠT / OK`)** tô nền xanh lá nhạt (`#EBF3ED`).
- **Cấu trúc 6 Chương Trọng tâm (Đánh số trực tiếp `1.`, `2.`, không ghi chữ `CHƯƠNG`)**:
  1. `1. CƠ SỞ THIẾT KẾ, TIÊU CHUẨN ÁP DỤNG & TÀI LIỆU THAM KHẢO`
  2. `2. TỔNG QUAN HẠNG MỤC & ĐẶC TRƯNG CƠ LÝ VẬT LIỆU`
  3. `3. TẢI TRỌNG TÁC DỤNG & TỔ HỢP TẢI TRỌNG TÍNH TOÁN`
  4. `4. MÔ HÌNH HÓA & PHƯƠNG PHÁP PHÂN TÍCH NỘI LỰC`
  5. `5. TÍNH TOÁN & KIỂM TRA KHẢ NĂNG CHỊU LỰC CẤU KIỆN ĐIỂN HÌNH`
  6. `6. TỔNG HỢP KẾT QUẢ KIỂM TRA, KẾT LUẬN & KIẾN NGHỊ KỸ THUẬT`

### 2. Bộ Chuẩn 2: Phong cách `tvtk` (TVTK Đa Hạng Mục — 9 Chương Cơ sở + N Chương Hạng mục)

- **Ứng dụng**: Hồ sơ Thiết kế Kỹ thuật (TKKT) hoặc Bản vẽ Thi công (BVTC) tổng hợp nhiều hạng mục công trình trong cùng một dự án.
- **Bố cục Section 0 (Bìa đôi Pháp lý + Mục lục)**:
  - **Trang 1 (Bìa ngoài)**: Khung viền đôi (`Double-line Box Border #1E3246`), thông tin công ty TVTK ở đầu trang, tên công trình/hạng mục ở giữa.
  - **Trang 2 (Bìa lót Pháp lý)**: Quốc hiệu `CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM` và bảng ký đóng dấu 2 cột cân xứng (`CHỦ ĐẦU TƯ` - `ĐƠN VỊ TƯ VẤN THIẾT KẾ`).
  - **Trang 3 (Mục lục tự động)**: Trường `TOC \o "1-3"` 3 cấp (`1`, `1.1`, `1.1.1`).
- **Bố cục Section 1 (Nội dung chính)**:
  - Font `Arial` (`11pt` body, `10pt` table), header bảng tô nền **Xanh lam nhạt (`#E6E2DA`)** chữ đen đậm, dòng kết luận tô nền xanh lá nhạt (`#EBF3ED`).
- **Cấu trúc `9 Chương Cơ sở Chung + N Chương Phụ lục Hạng mục`**:
  - **Phần I (Chương 1 đến Chương 9)**: `1 QUY CHUẨN VÀ TIÊU CHUẨN THIẾT KẾ` -> `2 CÁC TIÊU CHÍ KIỂM TRA ỔN ĐỊNH TỔNG THỂ` -> `3 ĐỘ VÕNG VÀ BỀ RỘNG VẾT NỨT CHO PHÉP` -> `4 ĐỘ LÚN CỦA MÓNG` -> `5 CÁC YÊU CẦU VỀ CHỐNG THẤM` -> `6 PHẦN MỀM PHÂN TÍCH VÀ TÍNH TOÁN` -> `7 TẢI TRỌNG VÀ TỔ HỢP TẢI TRỌNG` -> `8 VẬT LIỆU KẾT CẤU` -> `9 CHIỀU DÀY LỚP BÊ TÔNG BẢO VỆ`.
  - **Phần II (Chương 10 trở đi)**: Mỗi hạng mục là 1 chương `Heading 1` nối tiếp (`10 PHỤ LỤC TÍNH TOÁN HẠNG MỤC 01...`, `11 PHỤ LỤC TÍNH TOÁN HẠNG MỤC 02...`), bên trong gồm `.1 Mô hình tính toán`, `.2 Tải trọng tác dụng`, `.3 Tính toán nền móng`, `.4 Tính toán kết cấu phần thân`.

---

## Quy trình Thực thi Chuẩn hóa (Workflow v3.0)

### Cách 1: Tự động Hóa Toàn tuyến qua Compiler JSON (`json_to_tmtt_compiler.py`) — KHUYẾN NGHỊ

Khi đã có file JSON kết quả tính toán từ bất kỳ script Calculator nào:

```bash
python "g:/My Drive/Google AI Studio/.agents/skills/SKILL_PHULUC/calculators/json_to_tmtt_compiler.py" \
  --input "du_an/results_calc.json" \
  --output "du_an/TMTT_HOAN_CHINH.md" \
  --style bktechs \
  --project "Tên Dự án" \
  --item "Tên Hạng mục" \
  --client "Tên Chủ Đầu Tư" \
  --location "Địa điểm" \
  --appendices ".agents/skills/SKILL_PHULUC/templates/APPENDIX_HOIST_CRANE.md" \
  --auto-docx
```

Compiler tự động:
1. Bóc tách dữ liệu JSON thành 6 chương BKTECHS hoàn chỉnh.
2. Trích xuất Step-by-Step các công thức và Citation Object đủ 6 trường.
3. Ghép nối phụ lục chuyên sâu vào Section riêng biệt.
4. Triệt tiêu toàn bộ mã thô LaTeX `$`, render công thức sang Native Office Math (`OMML`).
5. Xuất file Word `.docx` hoàn chỉnh.

### Cách 2: Soạn thảo Thủ công Markdown & Xuất DOCX qua Engine `docx_generator_v2.py`

Khi người dùng tự soạn thảo nội dung thuyết minh Step-by-Step (`.md`):

```bash
python "g:/My Drive/Google AI Studio/.agents/skills/SKILL_PHULUC/docx_generator_v2.py" \
  --input draft_tmtt.md \
  --appendices templates/APPENDIX_FORMWORK_SHORING.md \
  --output TMTT_KET_CAU_HOAN_CHINH.docx \
  --style bktechs \
  --project "Tên Dự Án" \
  --item "Thuyết minh Tính toán Kết cấu kèm Phụ lục" \
  --client "Tên Chủ Đầu Tư" \
  --location "Địa điểm xây dựng"
```

### Cách 3: Kiểm toán Chất lượng Sau Xuất (`audit_phuluc_docx.py`)

Sau khi file `.docx` được tạo, chạy cổng kiểm toán độc lập:

```bash
python "g:/My Drive/Google AI Studio/.agents/skills/SKILL_PHULUC/scripts/audit_phuluc_docx.py" \
  "du_an/TMTT_KET_CAU_HOAN_CHINH.docx"
```

Cổng kiểm toán tự động quét 8 tiêu chí:
- `12b: ZERO WHITE TEXT LOCK`: Không có chữ trắng trên nền tối.
- `12e: SÀN CỠ CHỮ BẢNG >= 10.0pt`: Cỡ chữ bảng $\ge 10\text{ pt}$.
- `12e: MATH LOCK`: Xóa sạch 100% mã thô `$`, render Math OMML.
- `12e: CHỐNG DOUBLE BULLET`: Không có `•  •`.
- `13: MINIMUM NARRATIVE DEPTH`: Thuyết minh $\ge 800$ từ.
- `8: APPROVAL MATRIX & DISCLAIMER`: Đầy đủ bảng ký duyệt và câu miễn trừ AI.
- `TABLE INTEGRITY LOCK`: Đầy đủ `w:tblHeader` lặp tiêu đề và `w:cantSplit` chống rách dòng.

---

## Quy tắc Bắt buộc về Hệ thống Tiêu chuẩn & Địa kỹ thuật (STANDARDS_LOCK v3.3.0)

1. **Phân biệt 3 Hệ thống Phân cấp Pháp lý - Kỹ thuật (Cấm nhầm lẫn)**:
   - **Cấp công trình (`Đặc biệt, Cấp I, II, III, IV`)**: Xác định theo **Thông tư 06/2021/TT-BXD** và **Thông tư 34/2026/TT-BXD** (hiệu lực từ 01/07/2026, thay thế TT 06/2021 và TT 02/2025). Bắt buộc xét đồng thời **6 tiêu chí tại Mục 2.1.1 Bảng 2 Phụ lục II** và lấy cấp cao nhất: Chiều cao (`2.1.1.a`), Số tầng cao (`2.1.1.b`), **Tổng diện tích sàn GFA (`2.1.1.c`: `> 30.000 m2` -> Cấp I; `10.000 - 30.000 m2` -> Cấp II)**, Nhịp kết cấu lớn nhất (`2.1.1.d`), **Độ sâu ngầm (`2.1.1.d`: tính đến mặt trên sàn tầng hầm sâu nhất; `6 - 18m` -> Cấp II)**, **Số tầng ngầm (`2.1.1.e`: `2 - 4 tầng hầm` -> Cấp II; `1 tầng hầm` -> Cấp III)**.
   - **Cấp hậu quả (`C1, C2, C3`) và Tuổi thọ thiết kế (`Bảng 1`)**: Xác định theo **QCVN 03:2022/BXD** (Mục 2.1 Bảng 1 và Phụ lục A). Tuyệt đối không dùng QCVN 03:2022/BXD để phân cấp I-IV. Nhà cao tầng, TTTM, chung cư thông thường thuộc **Mục 3: Tối thiểu 50 năm** (`C2/C3`), trừ khi Nhiệm vụ thiết kế của CĐT yêu cầu nâng lên 100 năm.
   - **Cấp phức tạp điều kiện ĐCCT (`Cấp I, II, III`)**: Xác định theo **Điều 3.5 và Phụ lục 2 TCVN 4419:1987** (dẫn chiếu tại Chú thích Điều 5.2.4.1 TCVN 9363:2012).
2. **Khảo sát Địa kỹ thuật Nhà cao tầng (`TCVN 9363:2012`)**:
   - **TKCS**: Khoảng cách hố khoan **`50 m - 200 m`** (**Điều 5.2.4.2**).
   - **TKKT**: Khoảng cách hố khoan **`20 m - 30 m`** (lưới `20m x 20m` đến `30m x 30m` cho ĐCCT Cấp III).
   - **Tỷ lệ Hố khoan Khống chế**: Phải đạt **tối thiểu 1/3 (`>= 33.3%`) tổng số điểm thăm dò** (**Điều 5.3.6.3 TCVN 9363:2012**).
3. **Tiêu chuẩn Bắt buộc Cập nhật**:
   - Tải trọng & Tác động: **TCVN 2737:2023** (thay thế TCVN 2737:1995).
   - Kết cấu bê tông: **TCVN 5574:2018** (B25–B35, tối đa B40 theo Điều 12c AGENTS.md).
   - Kết cấu thép: **TCVN 5575:2024** (thay thế TCVN 5575:2012).
   - Móng cọc: **TCVN 10304:2025** (thay thế TCVN 10304:2014).
   - Công tác đất & Đào đắp đầm nén K95: **TCVN 4447:2012** & **TCVN 9436:2012**.
   - Nền nhà & công trình: **TCVN 9362:2012**.

## Khắc phục nghiệm thu v3.1

- Cổng audit kiểm toàn bộ hàng cantSplit và chặn ô dữ liệu mẫu ___ trong hồ sơ phát hành.
- Bộ đếm diễn giải loại bảng, heading, mục lục và disclaimer.
- Chế độ --json trả đúng exit code; PASS chỉ xác nhận các tiêu chí tự động, không xác nhận pháp lý.
- Generator bảo vệ bảng bìa/ký duyệt trước khi lưu; dùng phụ lục dự án đã điền, không phát hành template trống.

- Compiler --auto-docx tự chạy cổng audit sau khi xuất và trả mã lỗi nếu hồ sơ chưa đạt.
