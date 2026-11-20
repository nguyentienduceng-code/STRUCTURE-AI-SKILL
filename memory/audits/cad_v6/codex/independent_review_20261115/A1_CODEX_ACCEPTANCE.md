# A1 — Kiểm định độc lập nâng cấp DCE CAD v6

Ngày: 2026-11-15. Người kiểm định: CODEX. Mã: `09_DCE_CAD_BLOCK_SEMANTICS_V6`.

**Kết luận: FAIL — chưa nghiệm thu toàn bản nâng cấp.** Pha A1 đã đọc trực tiếp năm DXF C2, chạy lại thử thay đổi dữ liệu C1, round-trip G2, compliance physical/plan và regression. Báo cáo `a1_independent_audit.json` có sẵn trước ca này đánh dấu PASS không đủ cơ sở cho C2; kết luận trong biên bản này thay thế phần nghiệm thu C2 đó. File cũ được giữ nguyên để truy vết.

## Bằng chứng trực tiếp

Script `review.py`, kết quả `physical_evidence.json`, `mutation_roundtrip.json` trong cùng thư mục. DXF bàn giao không bị sửa. Các hash đầu vào nằm trong JSON. Bus trước khi tiếp nhận được lưu ở `bus_before_codex.json`; USER chỉ thị chuyển phần nghiệm thu sang CODEX dù bus còn ghi GEMINI giữ ca.

| Tờ C2 | Modelspace thực | Viewport | Chồng lấn giấy | Tỷ lệ thật / khai báo | VP frozen layers |
|---|---|---:|---:|---|---|
| KC-02 | 4 LINE + 1 TEXT | 2 | 99.450 mm² | 1:11,7647 / 1:50 | rỗng |
| KC-03 | 4 LINE + 1 TEXT | 1 | — | 1:11,7647 / 1:50 | rỗng |
| KC-04 | 4 LINE + 1 TEXT | 2 | 99.450 mm² | 1:11,7647 / 1:50 | rỗng |
| KC-06 | 4 LINE + 1 TEXT | 1 | — | 1:11,7647 / 1:50 | rỗng |
| KC-07 | 4 LINE + 1 TEXT | 1 | — | 1:11,7647 / 1:50 | rỗng |

Mỗi viewport có bbox giấy `[15,15,405,270]`, cao 255 mm; view_height=3000 nên mẫu số tỷ lệ là 3000/255=11,76470588. Đổi layer của entity VIEWPORT thành `VP_TOP/VP_BOTTOM` không lọc các entity bên trong view. Không có frozen-layer filter để ẩn `REBAR_BOTTOM` ở view TOP và ngược lại.

## Các lỗi chặn nghiệm thu và người xử lý

| ID | Mức | Phát hiện | Người sửa / yêu cầu |
|---|---|---|---|
| A1-01 | P0 | `export_sheet_set` tạo cùng 4 LINE từ chỉ số vòng lặp cho mọi tờ, không xuất hình học cột/dầm/sàn/Steel của dữ liệu thiết kế. Không có INSERT, ATTRIB, DIMENSION, HATCH của sản phẩm cấu kiện trên 5 tờ. | CLAUDE: tích hợp renderer C1/G2 thực, dựng nội dung theo loại view và nguồn fixture. Tờ chi tiết phải có chi tiết, không chỉ tiêu đề. |
| A1-02 | P0 | KC-02 và KC-04 có 2 viewport nằm chồng hoàn toàn. | CLAUDE: bbox giấy riêng, kiểm giao hình học sau save/reopen. |
| A1-03 | P0 | TOP/BOTTOM chỉ được tách strip_ids trong manifest; viewport không có bộ lọc hiển thị tương ứng. | CLAUDE: lọc thực bằng layer freeze theo view hoặc scene riêng đã kiểm; kiểm entity nhìn thấy, không chỉ JSON. |
| A1-04 | P0 | Tỷ lệ thật 1:11,7647 khác 1:50. | CLAUDE: `view_height = paper_height * scale_denominator` theo cùng hệ đơn vị, kiểm tỷ lệ thực với ít nhất hai tỷ lệ khác nhau. |
| A1-05 | P1 | Chỉ có khung ngoài trong paperspace; chưa có template A3 dải phải, mục lục thực, tiêu đề view theo bố cục được yêu cầu. | CLAUDE: hoàn thiện template/bộ tờ và xuất PDF/preview có nội dung. |
| A1-06 | P1 | Registry fixture có chuỗi geometry/tag/schedule refs nhưng C2 không xuất các đối tượng tương ứng; semantic PASS không chứng minh handle tồn tại. | GEMINI: validator đối chiếu refs với entity map của DXF; CLAUDE cung cấp map xuất thật. |
| A1-07 | P1 | Checker physical trả PASS cả 5 tờ tối giản; plan NEEDS_REVIEW, cả 5 thiếu sidecar bound hash. | CLAUDE: xuất sidecar thật; CODEX kiểm lại cả semantic và vật lý. Không dùng physical PASS làm bằng chứng bộ tờ đủ. |
| A1-08 | P1 | 3 test C2 chỉ kiểm manifest/disjoint ID/file tồn tại. Báo cáo audit cũ hard-code C2 capability PASS và bỏ compliance khỏi overall_pass. | CLAUDE: test hồi quy các lỗi A1-01..05; GEMINI: sửa kết luận bàn giao liên quan; CODEX giữ phép kiểm đọc DXF độc lập. |

## Phần có bằng chứng hoạt động

Full regression chạy mới: **33/33 suites PASS**, 147,38 giây; logs và timings trong `regression/`. Suite block semantics 10 tests được chạy riêng vì runner hiện không đăng ký trực tiếp suite này. Kết quả này xác nhận bộ test đang có đạt, không loại trừ các lỗi C2 mà test chưa bao phủ.

Chạy lại helper mutation C1 vào thư mục ca mới: đổi tên/tiết diện dầm, scale, chiều dày sàn, hạ cốt, cao độ, stable ID, manual override và leader đều đạt các assert hiện hữu. Đây là PASS trong phạm vi fixture, chưa chứng minh mọi tình huống collision hoặc mọi polygon sàn.

G2 round-trip và semantic helpers chạy lại đạt. Bộ `test_dce_block_semantics.py`: 10/10 test PASS. Steel vẫn là static output; dynamic evaluation và chỉnh sửa thương mại DCE/XData chưa được xác minh. Việc có catalog metadata Steel không đồng nghĩa import được dynamic geometry.

Preview headless `KC-04_actual_paperspace.png` đã thử nhưng hiển thị trắng; không dùng ảnh này để xác nhận native CAD plot. Các lỗi geometry/viewports ở trên được đo trực tiếp từ entity DXF, độc lập với khả năng render của backend.

## Kế hoạch sửa và tái nghiệm thu

CLAUDE nhận ca sửa C2 các lỗi A1-01..05,07,08; báo cáo kết quả và bàn giao GEMINI xử lý validator A1-06 cùng đối chiếu refs. Không sửa thư viện nguồn DCE. Tất cả sản phẩm sửa xuất sang thư mục mới, giữ nguyên artifact C2 cũ. Sau đó bàn giao CODEX kiểm lại bằng script độc lập; không ghi PASS trước khi đọc lại entity và render đủ nội dung.

Các test PASS hiện có không thay thế những tiêu chí hình học bị thiếu. A1 hoàn thành công tác kiểm định; dự án v6 còn cần khắc phục, trạng thái điều phối là NEED_REVIEW.
