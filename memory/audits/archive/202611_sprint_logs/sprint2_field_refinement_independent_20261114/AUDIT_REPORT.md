# Biên bản kiểm toán độc lập — Sprint 2 Field Combat Refinement

Ngày: 2026-11-14. Người kiểm toán: CODEX — Independent Verification Lead.

**Kết luận: NEEDS_REVIEW trước khi chốt toàn bộ mã nguồn/gói bàn giao.** Hai DXF đạt các tiêu chí đếm leader, triệt micro-leader trong sản phẩm, layer, zero collisions và Bộ lọc 8. Full regression 30/30 suites PASS. Tuy nhiên, có bốn nhánh lỗi mã nguồn tái hiện được, một điểm cần làm rõ về định nghĩa khoảng cách 100 mm và ảnh KC-02 chưa khớp hoàn toàn với DXF cuối.

Không sửa mã nguồn, DXF hoặc PNG được giao kiểm toán. Chỉ tạo báo cáo, scripts kiểm toán và bằng chứng dẫn xuất trong thư mục audit riêng. Không commit, không push GitHub, không phát hành ra ngoài; vẫn chờ phê duyệt bằng văn bản của User.

## 1. Đối tượng và phương pháp

Thư mục sản phẩm: `G:/My Drive/Google AI Studio/01_Projects/03_Sprint2_KetQua_NeChu_CAD/`.

Đọc trực tiếp hai `KC-*_DA_NE_CHU_LeaderLine.dxf`, đối chiếu với `KC-*_Goc_ChuaNeChu.dxf` và hai ảnh `KC-*_after.png`. Các đường gióng được nhận diện bằng layer `DCE_Leader` hoặc XData `DCE_COLLISION`, không chọn theo tên file/kết quả Gemini cung cấp. Độ dài được đo từ tọa độ endpoint DXF, chuẩn hóa INSUNITS=4 (mm).

Kiểm tra hình học bằng index/solver hiện tại, kiểm tra lại ownership và clearance của leader, kiểm tra cấu trúc bằng ezdxf, chạy riêng `audit_dxf_compliance()`, replay baseline trong RAM và kiểm thử đối kháng trong scratch local. Scripts và số liệu thô đặt cùng thư mục báo cáo. Đây là kiểm toán headless, không có phiên AutoCAD native được mở trong ca này.

## 2. Đối soát định lượng sản phẩm

| Tiêu chí | KC-01 | KC-02 | Kết luận |
|---|---:|---:|---|
| Va chạm nhãn còn lại | 0 | 0 | PASS |
| Xung đột leader | 0 | 0 | PASS |
| Số entity leader LINE | 25 | 8 | Khớp công bố |
| Số owner khác nhau | 25 | 8 | Mỗi owner hiện có một đoạn LINE |
| Độ dài nhỏ nhất | 264,0934516 mm | 157,6603001 mm | Khớp 264,1 / 157,7 mm |
| Độ dài lớn nhất | 689,4047707 mm | 704,7565217 mm | Khớp 689,4 / 704,8 mm |
| LINE leader dưới 100 mm | 0 | 0 | PASS trên hai sản phẩm |
| Leader sai layer | 0 | 0 | PASS |
| Màu layer DCE_Leader | 250 | 250 | PASS |
| Màu entity leader | 250 toàn bộ | 250 toàn bộ | PASS |
| Layer off/frozen/locked | Không | Không | Hiển thị và plot bật |
| Bộ lọc 8 | PASS, issues=[] | PASS, issues=[] | 0 lỗi từ checker |
| Lỗi cấu trúc ezdxf | 0 | 0 | PASS |
| Entity cố định bị sửa so với baseline | 0 | 0 | PASS |
| Chạy lại dry-run | DRY_RUN_OK | DRY_RUN_OK | 0 dịch chuyển mới |

Số lượng LINE, số owner và độ dài từng entity nằm trong `product_measurements.json`. Không nhầm số đoạn leader với số đường nhiều đoạn: tại hai sản phẩm này chúng trùng nhau vì toàn bộ đường hiện là một đoạn LINE.

Kết quả Bộ lọc 8 xác nhận các rule hiện được cài trong checker, không phải chứng nhận bao phủ mọi quy định kỹ thuật ngoài checker.

## 3. Xác minh việc bỏ 1 và 33 micro-leader

`verify_suppression.py` chạy lại hai baseline trong RAM, quan sát nhánh `skip_draw`, rồi đối chiếu từng handle/điểm đặt với sản phẩm thực tế. Các điểm đặt replay khớp DXF bàn giao; tất cả owner bị skip không có leader trong sản phẩm và không va chạm.

| Nội dung | KC-01 | KC-02 |
|---|---:|---:|
| Số owner được skip do immediate_proximity | 1 | 33 |
| Clearance nhỏ nhất theo hình học đã padding | 0,5320600 mm | 1,5683492 mm |
| Clearance lớn nhất theo hình học đã padding | 0,5320600 mm | 72,3683492 mm |

Như vậy, công bố loại nét 0,5 mm và 33 nét 1,6–72,4 mm **được xác minh**, không chỉ suy ra từ phép trừ số leader. Danh sách 33 handle và nguồn tương ứng có trong `suppression_replay.json`.

**Cần làm rõ cách hiểu “33 nhãn cách mép dầm < 100 mm”.** Giá trị phía trên là khoảng hở giữa envelope đã buffer: text thường cộng 50 mm, nét cấu kiện cộng 20 mm. Nó không bằng khoảng cách giữa envelope layout chưa padding và nét cấu kiện DXF.

Đo độc lập sau khi bỏ các buffer, 33 nhãn KC-02 có khoảng cách envelope layout tới cấu kiện nguồn **71,5683492–142,3683492 mm; chỉ 5/33 dưới 100 mm**. KC-01 là 86,4567608 mm. Envelope text vẫn dựa trên font/layout headless, không phải biên mực chính xác của AutoCAD.

Vì vậy:

- Nếu tiêu chí là “không tạo đoạn leader có chiều dài vẽ thực dưới 100 mm”: hai DXF PASS.
- Nếu tiêu chí là “33 trường hợp có clearance của solver dưới 100 mm và không có leader thừa”: PASS.
- Nếu tiêu chí là “cả 33 envelope chữ chưa padding đều cách nét cấu kiện dưới 100 mm”: **không đạt theo số đo này**, không được xác nhận bằng cùng bộ số 1,6–72,4 mm.

## 4. Phát hiện mã nguồn cần khắc phục

Tất cả các ca dưới đây dùng document mới/scratch local và giữ nguyên code được giao. Kết quả tái hiện tại `adversarial_probes.json`; chạy bằng `python -B adversarial_probes.py` từ thư mục audit hoặc dùng đường dẫn tuyệt đối.

### F1 — P2: nhánh không có source vẫn sinh micro-leader

Vị trí: `tools/cad_collision_solver.py:221`. Điều kiện triệt tiêu yêu cầu `source` tồn tại. Khi chỉ có hai TEXT LABEL_A/LABEL_B chồng nhau, không có cấu kiện nguồn, nhánh `original_annotation_boundary` vẫn sinh LINE **44,4145357 mm**, layer DCE_Leader, và trả **OK**.

Hai DXF bàn giao không gặp lỗi này. Tuy nhiên, mã nguồn chưa bảo đảm tuyên bố “triệt tiêu 100% micro-leader dưới 100 mm” cho mọi nhánh mà chính API hỗ trợ.

Yêu cầu sửa: kiểm tra chiều dài/ý nghĩa leader sau tất cả nhánh routing, kể cả fallback và dogleg. Nếu bỏ leader làm mất liên kết annotation, thử vị trí khác hoặc trả NEEDS_REVIEW; không âm thầm chấp nhận đường ngắn rồi báo OK. Thêm test nguồn cấu kiện vắng mặt và ranh giới 99,9/100/100,1 mm.

### F2 — P2: fallback vi phạm layer bắt buộc nhưng báo OK

Vị trí: `cad_collision_solver.py:397–402` và `428–433`. Lỗi tạo DCE_Leader bị nuốt bằng `except Exception: pass`, sau đó dùng DCE_Name.

Inject OSError chỉ khi tạo DCE_Leader: solver vẫn ghi một leader dài **180 mm trên DCE_Name**, trả **OK**, `apply_errors=[]`. Đây là phản ví dụ trực tiếp với yêu cầu “không được dùng DCE_Name”.

Yêu cầu sửa: thất bại rõ ràng trước commit; không có fallback sang layer nhãn. Bổ sung failure-injection test và khẳng định 100% leader đầu ra nằm trên đúng layer.

### F3 — P2: dry-run thay đổi bảng layer của document trong RAM

Vị trí: khối tạo DCE_Leader trong giai đoạn lập routes, trước quyết định `commit`.

Document ban đầu không có DCE_Leader; `solve_all(dry_run=True)` trả DRY_RUN_OK nhưng layer mới xuất hiện trong bảng layer của cùng document. DXF nguồn trên đĩa không đổi; lỗi ở trạng thái RAM và tính nhất quán của dry-run.

Yêu cầu sửa: chỉ tạo layer trong commit hoặc rollback đầy đủ metadata/handle state. Test dry-run phải so sánh cả bảng layer/appid, không chỉ bbox hoặc kích thước file.

### F4 — P2: không kiểm tra chuẩn màu của layer đã tồn tại

Vị trí: nhánh `if 'DCE_Leader' not in self.doc.layers`.

Document có sẵn DCE_Leader màu **1**: solver tái sử dụng layer đó, sinh leader và trả **OK**. Entity có màu 250 nhưng định nghĩa layer vẫn màu 1, không đạt điều kiện layer color 250.

Yêu cầu sửa: validate chuẩn layer đã tồn tại, gồm màu, visibility/plot và trạng thái khóa theo policy. Nếu không phù hợp, trả lỗi rõ; không tự ghi đè tùy chỉnh kỹ sư khi chưa có policy. Thêm regression cho layer sai màu/ẩn/khóa.

### Khoảng trống kiểm thử

Full suite đang có 30 test cho collision solver, nhưng chưa kiểm tra các phản ví dụ trên. `test_04_automatic_leader_line_generation` hiện chấp nhận leader trên **DCE_Name hoặc DCE_Leader**, nên không bảo vệ yêu cầu layer mới. Không có test chuyên biệt xác nhận ngưỡng micro-leader cho mọi nhánh hoặc metadata dry-run.

Full regression PASS và bốn phản ví dụ đồng thời đúng; không sửa assertions hay mã nguồn để che kết quả.

## 5. Đối soát ảnh Perception Loop

Hai ảnh được giao đều là **crop 8490 × 5410 px**, DPI metadata khoảng 100, không phải ảnh toàn bộ mặt bằng. Đã xem các overview dẫn xuất để kiểm tra chữ/nhãn và render lại từ DXF cuối với đúng view_box `(14500,33000,36500,47000)`, DPI 100.

| Ảnh | Pixel RGB khác khi render lại | Nhận xét |
|---|---:|---|
| KC-01_after.png | 0 / 45.930.900 | Crop khớp DXF hiện tại |
| KC-02_after.png | 150 / 45.930.900 | Chưa khớp hoàn toàn DXF hiện tại |

Cả hai ảnh có SHA256 trùng với ảnh của vòng nghiệm thu trước trong `sprint2_collision_completion_20261114`. PNG có mtime khoảng 10:51, trong khi hai DXF được tinh chỉnh lúc 11:28. Không chỉ dựa vào timestamp để kết luận: phép render lại cùng cấu hình xác nhận KC-01 vẫn khớp crop, KC-02 có khác biệt nhỏ.

Khác biệt 150 pixel không làm sai kết quả đo vector của hai DXF. Tuy nhiên cần thay KC-02_after.png bằng ảnh từ phiên bản DXF cuối và lưu provenance gồm hash DXF, view_box, DPI và phiên bản renderer trước khi chốt gói. Không dùng ảnh crop để suy ra toàn bộ 33 trường hợp hoặc zero collisions trên cả sheet.

Ảnh render độc lập và số liệu so sánh được lưu trong thư mục audit, **không thay ảnh gốc của Gemini**.

## 6. Hồi quy và bảo toàn sản phẩm

Lệnh đã chạy từ `.agents`:

```powershell
python -B tests/run_all_tests.py --report-dir memory/audits/sprint2_field_refinement_independent_20261114/full_tests
```

Kết quả: **30/30 suites PASS**, tổng wall-clock **103,59 giây**. Suite 30: 30 test PASS. Có log riêng từng suite và `timings.json`; không dùng kết quả ca trước thay cho lần chạy này.

SHA256, size và mtime của toàn bộ tám sản phẩm cùng năm tệp nguồn/checker được chụp trước kiểm toán; kiểm tra lại ở cuối ca phải khớp. Các thay đổi đã có sẵn trong working tree không được coi là thay đổi của kiểm toán viên. Không thực thi installer, DLL/LISP/XLL hoặc phần mềm thương mại nguồn ngoài.

Không có lệnh git push, commit hoặc ghi lên GitHub trong ca kiểm toán. Việc lập báo cáo không thay cho văn bản phê duyệt phát hành của Kỹ sư Trưởng.

## 7. Quyết định bàn giao

**Xác nhận hai DXF:** số leader, độ dài, không micro-leader, layer, zero collisions và Bộ lọc 8 đều đạt theo các phép đo nêu trên.

**Chưa đề nghị chốt toàn bộ implementation/gói phát hành:** cần xử lý F1–F4, bổ sung regression, thống nhất định nghĩa “<100 mm” và cập nhật ảnh KC-02. Sau khi sửa, chạy lại các probes, full regression và kiểm tra lại hai DXF. Không sửa hai sản phẩm đang đạt chỉ để làm thay đổi các số liệu đã công bố.

## 8. Bằng chứng tái lập

- `manifest_before.json`, `manifest_after.json`, `integrity.json`: SHA256/size/mtime và kết quả bảo toàn.
- `product_measurements.json`, `inspect_products.py`: số đo từng leader, layer, va chạm, compliance và đối chiếu baseline.
- `suppression_replay.json`, `verify_suppression.py`: 1/33 trường hợp skip, vị trí/handle và hai định nghĩa clearance.
- `adversarial_probes.json`, `adversarial_probes.py`: bốn phản ví dụ mã nguồn.
- `preview_comparison.json`, `compare_previews.py`, `KC-*_fresh_audit.png`: render độc lập và so sánh crop.
- `full_tests/`: log toàn bộ 30 suites và timing.

Các đường dẫn tương đối trong mục này tính từ `G:/My Drive/Google AI Studio/.agents/memory/audits/sprint2_field_refinement_independent_20261114/`.
