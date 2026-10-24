# THUYẾT MINH TÍNH TOÁN KẾT CẤU (RÚT GỌN)
## CÔNG TRÌNH: {{project_name}}

---

# CĂN CỨ THIẾT KẾ

## Tiêu chuẩn áp dụng

| STT | Tiêu chuẩn | Số hiệu |
|:---:|---|---|
| 1 | Tải trọng và tác động | TCVN 2737:2023 |
| 2 | Kết cấu thép – Tiêu chuẩn thiết kế | TCVN 5575:2024 |
| 3 | Kết cấu BTCT – Tiêu chuẩn thiết kế | TCVN 5574:2018 |

## Vật liệu chính

| Vật liệu | Thông số | Ghi chú |
|---|---|---|
| {{vat_lieu_1}} | {{thong_so_1}} | {{ghi_chu_1}} |
| {{vat_lieu_2}} | {{thong_so_2}} | {{ghi_chu_2}} |

---

# TẢI TRỌNG THIẾT KẾ

## Tải trọng gió (TCVN 2737:2023)

- Vùng gió: {{vung_gio}}
- W_0 = {{W_0}} kN/m², k(z) = {{k_z}}, c = {{c}}, γ_f = {{gamma_f}}
- **W_ULS = {{W_ULS}} kN/m²**

## Tổ hợp tải trọng chính

| Tổ hợp | Nội dung | Loại |
|---|---|---|
| COMBO-ULS | 1.1×DL + 1.2×SDL + 0.9×1.2×LL + 0.9×2.1×W | TTGH-I |
| SLS | 1.0×DL + 1.0×SDL + 0.9×LL + 0.9×W | TTGH-II |

---

# ĐÁNH GIÁ VÀ ĐỀ XUẤT

{{#each hang_muc_items}}
## {{ten_hang_muc}}

{{mo_ta_ngan_gon}}

| STT | Cấu kiện | Tiết diện | η | Kết luận |
|:---:|---|---|:---:|---|
| 1 | {{cau_kien_1}} | {{tiet_dien_1}} | {{eta_1}} | {{ket_luan_1}} |
| 2 | {{cau_kien_2}} | {{tiet_dien_2}} | {{eta_2}} | {{ket_luan_2}} |
{{/each}}

---

# BẢNG TỔNG HỢP KIỂM TRA

| STT | Hạng mục | η | Kết luận |
|:---:|---|:---:|---|
| 1 | {{hang_muc_1}} | {{eta_1}} | {{ket_luan_1}} |
| 2 | {{hang_muc_2}} | {{eta_2}} | {{ket_luan_2}} |

---

# KHUYẾN NGHỊ

1. **Bắt buộc:** {{khuyen_nghi_1}}
2. **Theo dõi:** {{khuyen_nghi_2}}

---

> Tài liệu do trợ lý AI lập tự động. Kết quả tính toán mang tính tham khảo, phải được kỹ sư có chứng chỉ hành nghề phù hợp kiểm tra và chịu trách nhiệm trước khi sử dụng cho hồ sơ thiết kế, thi công hoặc thẩm tra.
