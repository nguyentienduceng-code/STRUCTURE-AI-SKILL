---
name: Structural_Design_Engineer
version: 1.3.0
last_updated: 2026-08-30
description: "Kỹ sư Thiết kế Kết cấu Chuyên nghiệp Độc lập: Thiết kế tính toán kết cấu (BTCT, thép, móng), kiểm tra trạng thái giới hạn (ULS/SLS), tính toán thiết kế chi tiết liên kết (nút khung, bu lông, đường hàn, bản mã, neo cốt thép), và xuất Thuyết minh tính toán kỹ thuật (Calculation Sheet) chuyên sâu kèm bản vẽ chi tiết 2D. Kích hoạt khi nhắc đến các keyword: tính toán kết cấu, thuyết minh tính toán, tính liên kết, tính bu lông, tính đường hàn, thiết kế dầm, thiết kế cột, tính móng cọc, tính võng nứt, calculation sheet, chi tiết liên kết, tính bản mã, neo cốt thép."
---

# Structural Design Engineer — SKILL Entry Point

## ⚠ ĐỌC TRƯỚC: Đây có đúng là skill cần dùng không?

Skill này đóng vai **Kỹ sư Thiết kế độc lập** — tự tính ra tiết diện, cốt thép, liên kết và xuất Thuyết minh tính toán.

**Nếu User muốn REVIEW / THẨM TRA hồ sơ người khác, xử lý NCR, lập tờ trình, so sánh phương án, bóc khối lượng → dùng `Design_Evaluation`, KHÔNG dùng skill này.**

Bảng phân xử đầy đủ giữa 3 skill: `../AGENTS.md` mục 0.

## Tổng quan

Bộ skill **Structural_Design_Engineer** cung cấp năng lực chuyên môn của một **Kỹ sư Thiết kế Kết cấu Chuyên nghiệp Độc lập**, chịu trách nhiệm trực tiếp về giải pháp kỹ thuật, tính toán sức chịu tải, kiểm tra an toàn theo tiêu chuẩn và xuất **Thuyết minh tính toán (Calculation Sheet)** hoàn chỉnh.

Khác với vai trò Quản lý Thiết kế (`Design_Evaluation`), Skill này không tập trung vào thủ tục hành chính hay review dự án, mà tập trung vào **tính toán định lượng kỹ thuật trực tiếp và chi tiết hóa liên kết**.

| Module | File | Chức năng |
|--------|------|-----------|
| **SKILL_CALC** | `SKILL_CALC.md` | Tính toán thiết kế tiết diện & kết cấu (BTCT, Thép, Móng) theo TCVN/Eurocode/ACI |
| **SKILL_CONNECTION** | `SKILL_CONNECTION.md` | Thiết kế chi tiết liên kết (Bu lông, Đường hàn, Bản mã, Nút khung, Neo cốt thép) |
| **SKILL_CALC_REPORT** | `SKILL_CALC_REPORT.md` | Xuất Thuyết minh tính toán kỹ thuật (Calculation Sheet `.docx` / `.md`) |

---

## Quy tắc Điều phối (Dispatcher Logic)

Khi nhận yêu cầu từ User, AI xác định luồng thực hiện:

### → Kích hoạt SKILL_CALC khi:
- User yêu cầu tính toán tiết diện, tính uốn, nén, cắt, kiểm tra nứt/võng, tính toán móng cọc/móng nông.
- Keywords: *tính dầm, tính cột, tính sàn, kiểm tra tiết diện, tính móng cọc, tính sức chịu tải, kiểm tra độ võng, kiểm tra bề rộng khe nứt, ULS, SLS*.

### → Kích hoạt SKILL_CONNECTION khi:
- User yêu cầu thiết kế chi tiết nút liên kết, tính toán bu lông, đường hàn, bản mã, mối nối dầm, chân cột.
- Keywords: *tính bu lông, tính đường hàn, tính bản mã, liên kết dầm cột, liên kết chân cột, neo cốt thép, chiều dài nối thép, chi tiết nút khung*.

### → Kích hoạt SKILL_CALC_REPORT khi:
- User yêu cầu lập **Thuyết minh tính toán**, xuất Calculation Sheet, tổng hợp hồ sơ tính toán thiết kế.
- Keywords: *lập thuyết minh tính toán, xuất calculation sheet, thuyết minh kết cấu, hồ sơ tính toán*.

### → Luồng Phối hợp Đầy đủ (Full Design Flow):
1. **SKILL_CALC**: Giải nội lực & Tính toán kích thước/tiết diện chính.
2. **SKILL_CONNECTION**: Tính toán chi tiết nút liên kết & mối nối.
3. **Technical_Illustrator (MODE 2D)**: Tự động vẽ mặt cắt & sơ đồ chi tiết liên kết.
4. **Review Gate**: Tóm tắt kết quả tính toán ($\eta \le 1.0$), công thức chính, chờ User duyệt.
5. **SKILL_CALC_REPORT**: Bơm số liệu & hình vẽ vào Thuyết minh tính toán chính thức (`.docx`).

---

## Cấu trúc Thư mục

```
Structural_Design_Engineer/
├── SKILL.md                          ← BẠN ĐANG Ở ĐÂY (Entry Point)
├── SKILL_CALC.md                     ← Quy trình & Công thức tính toán kết cấu
├── SKILL_CONNECTION.md               ← Thiết kế chi tiết liên kết & mối nối
├── SKILL_CALC_REPORT.md              ← Generator Thuyết minh tính toán
├── references/                       ← Hướng dẫn tiêu chuẩn & công thức chi tiết
│   ├── STEEL_DESIGN_GUIDE.md
│   ├── RC_DESIGN_GUIDE.md
│   └── FOUNDATION_DESIGN_GUIDE.md
├── templates/                        ← Form mẫu Thuyết minh tính toán (xem README.md trong đó)
├── scripts/                          ← Tool Python tính toán & xuất file
│   ├── calc_steel_beam_tcvn.py     ← ✅ Dầm thép: uốn + cắt + LTB + võng (TCVN 5575:2024)
│   ├── calc_steel_connection_tcvn.py ← ✅ Bu lông: cắt + ép mặt + kéo (TCVN 5575:2024)
│   ├── calc_rc_section.py           ← Dầm BTCT: uốn + cắt (TCVN 5574:2018)
│   └── export_calc_sheet.py          ← Xuất Thuyết minh tính toán (.md)
└── _deprecated/                      ← ⚠️ Scripts Eurocode — THAM KHẢO ĐỐI CHIẾU
    ├── README.md                    ← Chính sách deprecation
    ├── calc_steel_beam.py           ← EN 1993-1-1 (KHÔNG dùng cho hồ sơ mới)
    └── calc_steel_connection.py      ← EN 1993-1-8 (KHÔNG dùng cho hồ sơ mới)
```

> **⚠️ Quy tắc:** Chỉ dùng scripts có ✅ trong thư mục `scripts/`. Scripts trong `_deprecated/` chỉ để đối chiếu quốc tế.

**Quy tắc bắt buộc với script tính toán:**

- Mọi script trả về `Standard_Method` (phiên bản tiêu chuẩn thực sự cài đặt), `Scope_Limitation` (các kiểm tra CHƯA làm) và `Unverified_Items`.
- Báo cáo PHẢI in cả 3 trường này. Không được kết luận "ĐẠT" khi bỏ qua `Scope_Limitation`.
- Trạng thái `INCONCLUSIVE` (VD: chưa nhập cốt đai) **không phải** là ĐẠT — phải hỏi User bổ sung số liệu.

---

## Quy tắc Kỹ thuật Bắt buộc

1. **Hiển thị Công thức & Từng bước tính (Step-by-Step Calculation)**: Mọi kết quả phải có công thức tổng quát, thế số và kết quả. Không chỉ đưa ra kết luận chung chung.
2. **Kiểm tra Hệ số Sử dụng ($\eta = S/R \le 1.0$)**: Mọi linh kiện/liên kết đều phải tính tỷ lệ sử dụng khả năng chịu lực $\eta$. Nếu $\eta > 1.0 \rightarrow$ Đánh giá Không Đạt và đề xuất phương án tăng cường.
3. **Standards Citation Lock**: Trích dẫn chính xác Tiêu chuẩn (Mã - Năm - Điều/Bảng). Ví dụ: TCVN 5575:2012 Điều 5.2.1 hoặc Eurocode 3 EN 1993-1-8 Table 3.4.
4. **Tự động nhúng Bản vẽ 2D**: Mọi thuyết minh chi tiết liên kết BẮT BUỘC có hình vẽ 2D từ `Technical_Illustrator` minh họa vị trí bu lông, bản mã, đường hàn, bố trí thép.

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.3.0 | 2026-08-30 | Phase 1: Eurocode scripts moved to `_deprecated/`; Updated script table with TCVN versions |
| 1.2.0 | 2026-08-18 | Thêm SKILL_CONNECTION.md, SKILL_CALC_REPORT.md |
| 1.1.0 | 2026-07-15 | Cập nhật TCVN 5575:2024 |
| 1.0.0 | 2026-06-01 | Initial release |
