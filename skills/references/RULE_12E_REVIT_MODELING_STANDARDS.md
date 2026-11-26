# Revit BIM — đối chiếu mô hình khi bàn giao

Áp dụng cho ca trích xuất hoặc chuyển dữ liệu CAD sang mô hình Revit. Dùng hướng dẫn của SKILL_BIM_COORDINATION khi kiểm tra trục, cao độ và xung đột liên bộ môn. Xác nhận phiên bản mô hình, đơn vị, hệ tọa độ, tầng và dữ liệu nguồn trước khi đối chiếu. Với family, đối chiếu loại cấu kiện, tham số và kích thước với bảng thống kê trên bản mẫu trước khi ghi vào mô hình dự án. Ghi rõ phần chưa kiểm chứng trên Revit thật trong kết quả bàn giao.

Đặc tả P4.3 yêu cầu đối chiếu các trường sau trước bàn giao.

| Phần tử | Dữ liệu đối chiếu |
|---|---|
| Cột | Vị trí, tiết diện, chiều cao tầng, cấp bê tông, thép dọc và đai |
| Vách | Tọa độ tim, chiều dài, chiều dày |
| Dầm | Tim và nhịp, kích thước tiết diện, loại cấu kiện |

Xem [đặc tả P4.3](../../memory/CLAUDE_P4_SPEC_AND_COMPLEX_TASKS.md) và [bộ chuyển dữ liệu BIM](../Technical_Illustrator/cad_integration/bim_model_translator.py) khi lập bảng ánh xạ family.

Quy tắc trình bày Word/Excel gốc của Điều 12e nằm tại [Typography](RULE_12E_TYPOGRAPHY.md).
