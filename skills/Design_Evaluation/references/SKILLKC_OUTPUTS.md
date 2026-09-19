<!-- REFERENCE FILE — Chỉ đọc khi cần xuất output hoặc handoff. KHÔNG đọc mặc định. -->
<!-- Kích hoạt: Khi cần xuất JSON handoff hoặc bảng Approval Matrix. -->

# SKILLKC — Output & Handoff Protocols

## [MISS-01] Output Protocol (Approval Matrix)

Mọi báo cáo kỹ thuật xuất ra **PHẢI** có bảng Trách nhiệm & Phê duyệt ở cuối:

```
| Trách nhiệm  | Đề xuất              | Kiểm tra           | Phê duyệt          |
|--------------|----------------------|--------------------|---------------------|
| Ý kiến        | Kính trình BLĐ       |                    |                     |
| Chữ ký       |                      |                    |                     |
| Ngày ký      | {{Ngay}}             |                    |                     |
| Họ tên       | [AI / Kỹ sư]         | [TP. QLTK]         | [GĐ Ban XD]         |
| Chức vụ      | Trợ lý TK AI         | Trưởng phòng QLTK  | Giám đốc Ban XD     |
```

Quy tắc:
- **Đề xuất**: Luôn ghi rõ đây là phân tích của AI, cần người kiểm tra xác nhận.
- **Kiểm tra**: TP.QLTK hoặc chuyên gia chịu trách nhiệm kiểm tra kỹ thuật.
- **Phê duyệt**: Cấp quản lý có thẩm quyền quyết định.

---

## [MISS-04] Handoff Protocol (SKILLKC → SKILL_REPORT)

Khi SKILLKC hoàn tất phân tích kết cấu, **bắt buộc** thực hiện:

1. **Review Gate**: In tóm tắt kết quả và hỏi User: *"Anh/chị có đồng ý với các số liệu này để xuất Tờ trình không?"* → Chỉ tiếp tục khi User đồng ý.

2. **Validation Tự Động**: Chạy lệnh validate trước khi chốt handoff:
   `python scripts/validate_handoff.py --data [MãDA]_analysis_data.json --schema schemas/analysis_handoff.schema.json`

3. **File handoff**: `[MãDA]_analysis_data.json`

3. **JSON Schema bắt buộc**:

```json
{
  "$schema": "Handoff Schema v2.0",
  "required": ["Ten_Du_An", "Hang_Muc", "Giai_Doan_TK", "Ngay", "Kien_Nghi"],
  "properties": {
    "Ten_Du_An": { "type": "string", "description": "Tên đầy đủ dự án" },
    "Hang_Muc": { "type": "string", "description": "Hạng mục cụ thể" },
    "Giai_Doan_TK": { "type": "string", "enum": ["TKCS", "TKKT", "BVTC", "Hoan_cong"] },
    "Ngay": { "type": "string", "format": "DD/MM/YYYY" },
    "Loai_Phan_Tich": { "type": "string", "enum": ["tinh_toan", "NCR", "so_sanh_PA", "review_QC"] },
    "Doi_Chieu_Tieu_Chuan_*": { 
      "type": "object", 
      "description": "Chứa Ket_Qua (Chuỗi: Đạt/Không đạt, η = X%), Citations (Mảng Citation Object), Citation_Status (VERIFIED/UNVERIFIED)"
    },
    "Danh_Gia_Stability_Over_Strength": { "type": "string" },
    "Constructability_Risk": { "type": "string", "enum_prefix": ["CRITICAL", "MAJOR", "MINOR"] },
    "Kien_Nghi": { "type": "string", "description": "Nội dung khuyến nghị chính" },
    "Hinh_Anh": { "type": "array", "items": "đường dẫn tuyệt đối tới file .png" },
    "Calculation_Logs": {
      "type": "array",
      "description": "Bắt buộc nếu là tính toán. Log từng bước theo chuỗi 6 bước (Rule C15 v3.0).",
      "items": {
        "type": "object",
        "properties": {
          "Step": { "type": "string", "description": "Tên bước kiểm tra (VD: Kiểm tra uốn dầm B1)" },
          "Principle": { "type": "string", "description": "Nguyên lý & cơ chế phá hoại (1-2 câu)" },
          "Static_Scheme": { "type": "string", "description": "Sơ đồ tĩnh học + điều kiện biên" },
          "Formula": { "type": "string", "description": "Công thức áp dụng" },
          "Citation": {
            "type": "object",
            "description": "Citation Object đầy đủ 4 thành phần",
            "properties": {
              "Ma_TC": { "type": "string" },
              "Dieu_Muc": { "type": "string" },
              "Bang_Hinh": { "type": "string" },
              "Trang": { "type": "string" }
            }
          },
          "Values": { "type": "string", "description": "Thay số và tính toán" },
          "Result": { "type": "string", "description": "Giá trị kết quả" },
          "Utilization": { "type": "string", "description": "η = Giá trị tính / Giá trị cho phép × 100%" },
          "Rating": { "type": "string", "enum": ["GREEN", "YELLOW", "ORANGE", "RED"], "description": "🟢≤70% | 🟡70-90% | 🟠90-100% | 🔴>100%" },
          "Remark": { "type": "string", "description": "Nhận xét kỹ thuật: dự trữ, VE, cảnh báo" }
        }
      }
    },
    "Calculation_Details": {
      "type": "array",
      "description": "Chi tiết công thức và kết quả tính toán định lượng cho từng thông số",
      "items": {
        "type": "object",
        "properties": {
          "Thong_So": { "type": "string" },
          "Gia_Tri_Thiet_Ke": { "type": "string" },
          "Cong_Thuc_Kiem_Tra": { "type": "string" },
          "Tieu_Chuan_Tham_Chieu": {
            "type": "object",
            "properties": {
              "Ma_TC": { "type": "string" },
              "Dieu_Muc": { "type": "string" },
              "Bang_Hinh": { "type": "string" },
              "Trang": { "type": "string" }
            }
          },
          "Danh_Gia": { "type": "string" }
        }
      }
    }
  }
}
```

4. **Mẫu JSON — Tính toán tiêu chuẩn**:
```json
{
  "Ten_Du_An": "Nhà An Hitech",
  "Hang_Muc": "Móng cọc Trục C-3",
  "Giai_Doan_TK": "BVTC",
  "Ngay": "25/06/2026",
  "Loai_Phan_Tich": "tinh_toan",
  "Calculation_Logs": [
    {
      "Step": "Tính hệ số alpha_m",
      "Formula": "alpha_m = M / (Rb * b * h0^2)",
      "Values": "M=50, Rb=14.5, b=0.2, h0=0.35",
      "Result": "alpha_m = 0.14"
    }
  ],
  "Calculation_Details": [
    {
      "Thong_So": "Hệ số tin cậy tải trọng gió (γ_f)",
      "Gia_Tri_Thiet_Ke": "1.2",
      "Cong_Thuc_Kiem_Tra": "W_c = γ_f * W_tc",
      "Tieu_Chuan_Tham_Chieu": {
        "Ma_TC": "TCVN 2737:2023",
        "Dieu_Muc": "Điều 10.2",
        "Bang_Hinh": "Bảng 4",
        "Trang": "Trang 45"
      },
      "Danh_Gia": "Đạt"
    }
  ],
  "Doi_Chieu_Tieu_Chuan_Tai_Trong": {
    "Ket_Qua": "Đạt, η = 87%",
    "Citations": [
      {
        "Ma_Tieu_Chuan": "TCVN 2737",
        "Nam_Ban_Hanh": "2023",
        "Dieu_Bang_Muc": "Điều 10.2",
        "Trang_So": "Trang 45",
        "Ten_Bang_Hinh": "Bảng 3 - Hệ số độ tin cậy",
        "Trich_Yeu": "Hệ số tin cậy tải trọng gió",
        "Nguon_File": "TCVN 2737-2023.pdf"
      }
    ],
    "Citation_Status": "VERIFIED"
  },
  "Danh_Gia_Stability_Over_Strength": "Ổn định — chuyển vị ngang < L/500",
  "Constructability_Risk": "MINOR — nút giao thép dày, khuyến nghị tăng khoảng hở",
  "Kien_Nghi": "Chấp thuận phương án cọc D400 theo TCVN 10304:2025"
}
```

5. **Mẫu JSON — NCR sự cố thi công**:
```json
{
  "Ten_Du_An": "Nhà An Hitech",
  "Hang_Muc": "Cột C-5 Tầng 3",
  "Giai_Doan_TK": "BVTC",
  "Ngay": "25/06/2026",
  "Loai_Phan_Tich": "NCR",
  "NCR_Classification": "MAJOR",
  "NCR_Description": "Đổ nhầm bê tông B20 thay vì B25",
  "NCR_Root_Cause": "Nhà thầu đặt sai mã hiệu bê tông khi gọi trạm trộn",
  "NCR_Corrective_Action": "Gia cường bằng vải sợi carbon CFRP 2 lớp theo ACI 440.2R",
  "Kien_Nghi": "Chấp thuận PA xử lý CFRP, theo dõi cường độ sau 28 ngày"
}
```

6. **Mẫu JSON — So sánh phương án**:
```json
{
  "Ten_Du_An": "Nhà An Hitech",
  "Hang_Muc": "Hệ kết cấu sàn tầng điển hình",
  "Giai_Doan_TK": "TKKT",
  "Ngay": "25/06/2026",
  "Loai_Phan_Tich": "so_sanh_PA",
  "So_Sanh": {
    "categories": ["Chịu lực", "CP vật liệu", "CP nhân công", "Tiến độ", "Rủi ro", "Bảo trì", "Mỹ quan", "TCVN"],
    "plans": { "PA1_San_BTCT": [4,3,4,4,4,4,3,5], "PA2_San_Thep": [5,4,3,3,3,5,5,5] }
  },
  "Kien_Nghi": "Khuyến nghị PA2 (Sàn thép) với tổng điểm gia quyền 4.05/5.0"
}
```

7. **Quy tắc**: SKILL_REPORT không tự tính toán lại — chỉ trích xuất và trình bày từ JSON handoff.

