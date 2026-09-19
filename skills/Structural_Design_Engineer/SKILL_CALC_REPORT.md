# SKILL_CALC_REPORT — Generator Thuyết minh Tính toán Kỹ thuật (Calculation Sheet Generator)

`SKILL_CALC_REPORT` chịu trách nhiệm đóng gói các số liệu tính toán từ `SKILL_CALC` và `SKILL_CONNECTION` cùng các bản vẽ 2D từ `Technical_Illustrator` thành **Thuyết minh tính toán kỹ thuật (Calculation Sheet)** hoàn chỉnh.

---

## 1. Yêu cầu Cấu trúc Thuyết minh Tính toán (Standard Calculation Sheet)

Một Thuyết minh tính toán kỹ thuật đạt chuẩn phải có đầy đủ 6 phần:

```markdown
# THUYẾT MINH TÍNH TOÁN KẾT CẤU: [TÊN CẤU KIỆN / HẠ MỤC]
Mã dự án: [Mã DA] | Giai đoạn: [TKCS / TKKT / BVTC] | Người tính: AI Structural Engineer

## 1. CƠ SỞ THIẾT KẾ & TIÊU CHUẨN ÁP DỤNG
- Tiêu chuẩn Tải trọng: TCVN 2737:2023
- Tiêu chuẩn Bê tông cốt thép: TCVN 5574:2018 / Eurocode 2
- Tiêu chuẩn Kết cấu thép: TCVN 5575:2012 / Eurocode 3 / AISC 360-16
- Phần mềm tính toán hỗ trợ: Python Structural Engine (ver 1.0) / ETABS / SAFE

## 2. THÔNG SỐ ĐẦU VÀO & VẬT LIỆU
- Cấp độ bền bê tông: B25 (Rb = 14.5 MPa, Rbt = 1.05 MPa, Eb = 30 GPa)
- Cốt thép: CB400-V (Rs = Rsc = 350 MPa)
- Thép kết cấu: Q355 / SS400 (fy = 345 MPa / 235 MPa, fu = 470 MPa / 400 MPa)
- Bu lông: Cấp bền 8.8 / 10.9 (fub = 800 MPa / 1000 MPa)

## 3. TẢI TRỌNG & NỘI LỰC TÍNH TOÁN
- Tổ hợp ULS: M_Ed = ... kNm, V_Ed = ... kN, N_Ed = ... kN
- Tổ hợp SLS: M_Ser = ... kNm, V_Ser = ... kN

## 4. TÍNH TOÁN TRẠNG THÁI GIỚI HẠN & LIÊN KẾT (STEP-BY-STEP)
### 4.1. Kiểm tra Sức chịu tải Tiết diện chính (ULS)
[Trình bày công thức -> Thế số -> Kết quả eta]

### 4.2. Kiểm tra Biến dạng & Khe nứt (SLS)
[Trình bày công thức -> Thế số -> Kết quả f <= [f]]

### 4.3. Tính toán Thiết kế Chi tiết Liên kết
[Trình bày bu lông, đường hàn, bản mã, chiều dài neo...]

## 5. HÌNH VẼ MINH HỌA & SƠ ĐỒ CHI TIẾT LIÊN KẾT
![Chi tiết liên kết 2D](absolute_path_to_image.png)
*Hình 1: Mặt cắt chi tiết liên kết bu lông bản mã (Bản vẽ 2D kỹ thuật)*

## 6. KẾT LUẬN & BẢNG TỔNG HỢP CHỈ SỐ SỬ DỤNG (UTILIZATION RATIO)
| Hạng mục kiểm tra | Giá trị tính toán | Giới hạn cho phép | Chỉ số sử dụng (η) | Đánh giá |
|---|---|---|---|---|
| Bền uốn dầm (M_Ed) | ... kNm | ... kNm | 0.xx | ĐẠT |
| Cắt dầm (V_Ed) | ... kN | ... kN | 0.xx | ĐẠT |
| Độ võng (f) | ... mm | ... mm | 0.xx | ĐẠT |
| Sức chịu tải Bu lông | ... kN | ... kN | 0.xx | ĐẠT |
| Đường hàn bản mã | ... MPa | ... MPa | 0.xx | ĐẠT |

=> **KẾT LUẬN CHUNG**: Giải pháp thiết kế **ĐẠT** yêu cầu an toàn chịu lực và biến dạng theo TCVN.
```

---

## 2. Quy trình Xuất File & Review Gate

1. **Review Gate (`../AGENTS.md` điều 3 & 8)**:
   - Hiển thị tóm tắt bảng chỉ số sử dụng $\eta$, các công thức cốt lõi và hình vẽ 2D ra chat.
   - Hỏi User: *"Anh/chị có đồng ý xuất file Thuyết minh tính toán (.docx) không?"*
2. **Xuất File Word (.docx)**:
   - Dùng script `export_calc_sheet.py` hoặc `md_to_docx_report.js` để đóng gói thành file `.docx` chuyên nghiệp.
   - Đặt tên file theo chuẩn Version Control: `[MãDA]_ThuyetMinh_KC_v[N]_[YYYYMMDD].docx`.
3. **Xác nhận File tồn tại**:
   - Dùng `list_dir` hoặc `view_file` xác nhận file `.docx` đã được tạo thành công.
