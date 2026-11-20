# Biên bản nghiệm thu tái kiểm Sprint 2 — F1–F4, Perception Loop và regression

Ngày phát hành: 14/11/2026, múi giờ +07:00. Kiểm toán viên: CODEX, Independent Verification Lead.

**Quyết định: APPROVED trong phạm vi tái kiểm được yêu cầu.** Bốn phản ví dụ F1–F4 đã đạt. Hai ảnh khớp render DXF với 0 pixel RGB khác biệt. Full regression đạt 30/30 suites PASS trong 130,70 giây.

**Không xác nhận toàn bộ 20 cổng Bộ lọc 8.** Kiểm tra bổ sung phát hiện API trả PASS nhưng chi tiết chỉ đạt 5/20 cổng trên mỗi DXF. Phát hiện F5 được ghi riêng bên dưới. Biên bản này không cho phép push GitHub hoặc phát hành mã nguồn ra ngoài.

## 1. Phạm vi và cơ sở nghiệm thu

User yêu cầu chạy lại ba lệnh kiểm tra sau khi Gemini sửa F1–F4 và đồng bộ ảnh KC-02. CODEX đã chạy trực tiếp các script được chỉ định. Kết quả trong biên bản lấy từ lần chạy mới, không dùng kết luận của Gemini thay cho kiểm toán.

Đối tượng nghiệm thu là các phản ví dụ đã tái hiện trong `AUDIT_REPORT.md`, ảnh KC-01/KC-02 và toàn bộ registry regression hiện hành. Hai DXF `KC-01_DA_NE_CHU_LeaderLine.dxf` và `KC-02_DA_NE_CHU_LeaderLine.dxf` được đo lại để xác nhận sản phẩm vẫn giữ các chỉ tiêu hình học đã đạt.

Thư mục sản phẩm là `G:/My Drive/Google AI Studio/01_Projects/03_Sprint2_KetQua_NeChu_CAD/`. Các PDF và bộ ba bản vẽ mang hậu tố v47 có trong thư mục không thuộc phạm vi sign-off này. Biên bản không đánh giá kết cấu chịu lực và không thay thế thẩm tra thiết kế.

`AUDIT_REPORT.md` được giữ nguyên để bảo toàn lịch sử. Biên bản mới đóng các phản ví dụ F1–F4 và cập nhật kết quả ảnh. Các nhận định không thuộc phép tái kiểm không tự động được chuyển thành PASS.

## 2. Đóng phản ví dụ F1–F4

| Mã | Điều kiện đối kháng | Kết quả quan sát | Kết luận |
|---|---|---|---|
| F1 | Hai nhãn chồng nhau, không có cấu kiện nguồn | `OK`; 0 leader; `leader_paths={}` | PASS |
| F2 | Inject OSError khi tạo DCE_Leader | `NEEDS_REVIEW`; 0 leader; có apply_errors | PASS |
| F3 | Document chưa có DCE_Leader, chạy dry-run | `DRY_RUN_OK`; `new_layers=[]` | PASS |
| F4 | DCE_Leader có sẵn màu 1 | `OK`; màu layer thành 250; một leader 180 mm trên DCE_Leader | PASS |

Ở F1, đoạn leader 44,4145 mm của ca cũ không còn xuất hiện. Nhánh không có nguồn cấu kiện đã áp dụng kiểm tra ngưỡng trước và sau bước rút ngắn endpoint. Kết luận này đóng phản ví dụ cụ thể được giao; không phải chứng minh mọi cấu hình dogleg hoặc mọi bản vẽ đều không thể sinh đoạn ngắn.

Ở F2, trả `NEEDS_REVIEW` là kết quả đúng của phép thử. Khi tạo layer bị từ chối, chương trình không chuyển sang DCE_Name rồi báo thành công. Lỗi được đưa vào `apply_errors`, giúp phía gọi phân biệt thất bại thực thi với kết quả đã áp dụng. Vì đây là failure-injection, yêu cầu trạng thái `OK` trong ca này sẽ làm sai tiêu chí nghiệm thu.

Ở F3, bảng layer không có mục mới sau dry-run. Việc tách tạo layer khỏi giai đoạn lập phương án đã khắc phục thay đổi RAM được báo cáo trước đây. Phép thử gốc kiểm tra danh sách layer; không diễn giải nó thành kiểm chứng tuyệt đối mọi trường metadata của document.

Ở F4, Gemini chọn chính sách chuẩn hóa layer chuyên dụng, thay vì từ chối layer sai màu. Mã nguồn mô tả rõ việc đưa DCE_Leader về màu 250, CONTINUOUS, lineweight 13 và trạng thái mở khóa, bật, thaw. Probe xác nhận trường hợp sai màu. Đây là hành vi cần được phía tích hợp hiểu rõ: commit có thể sửa cấu hình layer chuyên dụng; sign-off không khẳng định layer này giữ mọi tùy chỉnh của kỹ sư.

Script `adversarial_probes.py` xuất dữ liệu nhưng không tự assert toàn bộ tiêu chí. Vì vậy, CODEX đã chạy thêm `evaluate_recheck.py` để đánh giá kết quả theo kỳ vọng riêng của từng phản ví dụ. Bốn điều kiện đều đúng; không lấy riêng mã thoát 0 làm bằng chứng PASS.

## 3. Đồng bộ ảnh Perception Loop

| Ảnh | Kích thước | Pixel RGB khác biệt | Kết luận |
|---|---:|---:|---|
| KC-01_after.png | 8490 × 5410 | 0 / 45.930.900 | PASS |
| KC-02_after.png | 8490 × 5410 | 0 / 45.930.900 | PASS |

Ảnh được render lại từ DXF cuối bằng cấu hình DPI 100, layout Model và view_box `(14500,33000,36500,47000)`. Phép so sánh xét ba kênh RGB và đếm mọi pixel có ít nhất một kênh khác. Cả hai ảnh có cùng kích thước với ảnh render mới; difference_bbox đều bằng null.

Kết quả đóng khác biệt 150 pixel của KC-02 trong báo cáo trước. Đây là sự trùng khớp pixel ảnh, không phải khẳng định byte của file PNG hoặc metadata phải giống nhau. View_box là vùng crop. Kết quả ảnh không thay thế phép đo vector trên toàn bản vẽ và không phải thử nghiệm trực tiếp trong AutoCAD native.

Các preview tạm được sinh trên ổ local do VirtualDriveGuard quản lý và được cleanup sau khi so sánh. Ảnh overview dẫn xuất và số liệu provenance được lưu trong thư mục tái kiểm. CODEX không ghi đè PNG sản phẩm của Gemini.

## 4. Regression và đối soát DXF bổ sung

Full regression chạy với registry đầy đủ, không dùng `--fast` và không lọc suite. Kết quả là **30/30 suites PASS**, wall-clock **130,7012671 giây**. Suite collision solver chạy 30 test và đạt. Bộ kết quả gồm 30 log riêng và `full_tests/timings.json`.

Các probes F1–F4 được chạy độc lập với full suite. Do đó, không diễn giải con số 30/30 suites thành việc mọi probe đã được đưa vào regression registry. Test leader hiện vẫn có assertion chấp nhận DCE_Name hoặc DCE_Leader; phép thử F2 độc lập mới trực tiếp bảo vệ điều kiện không fallback trong lần tái kiểm này.

| Chỉ tiêu vector | KC-01 | KC-02 |
|---|---:|---:|
| Va chạm nhãn còn lại | 0 | 0 |
| Xung đột leader | 0 | 0 |
| Số leader | 25 | 8 |
| Độ dài nhỏ nhất, mm | 264,0934516 | 157,6603001 |
| Độ dài lớn nhất, mm | 689,4047707 | 704,7565217 |
| Leader dưới 100 mm | 0 | 0 |
| Leader sai layer hoặc màu | 0 | 0 |
| Entity cố định bị đổi so với baseline | 0 | 0 |
| Lỗi cấu trúc ezdxf | 0 | 0 |
| Dịch chuyển mới khi dry-run lại | 0 | 0 |

Khoảng hở dưới 100 mm trong chính sách solver vẫn được hiểu theo envelope đã padding. Biên bản không đổi nó thành khoảng cách từ biên chữ chưa padding đến mép dầm. Số đo 5/33 nhãn có khoảng cách chưa padding dưới 100 mm trong báo cáo trước không bị xóa hoặc tuyên bố đã sửa. Hai tiêu chí này đo hai đại lượng khác nhau.

## 5. F5 — Phạm vi compliance chưa được nghiệm thu

Kiểm tra bổ sung gọi lại `audit_dxf_compliance()` bằng checker mới. Cả hai sản phẩm trả `status=PASS`, `issues=[]`, nhưng đồng thời trả `gates_passed=5`, `gates_total=20`. Có 15 gate với `passed=false` trên mỗi bản vẽ: G8.02–G8.12 và G8.17–G8.20.

Tại `skills/SKILL_VERIFY/scripts/dce_cad_compliance_checker.py:732`, hàm API nhận `all_passed` và tạo `gate_issues`, nhưng không dùng hai giá trị này khi xác định trạng thái. Trạng thái trả về chỉ kế thừa physical audit. Vì vậy, `PASS` hiện có không chứng minh tất cả 20 cổng đạt.

Một phần cổng đọc metadata hoặc quy ước của generator mới. Chưa đủ căn cứ quy mọi gate false thành lỗi hình học vật lý của DXF cũ. Tuy nhiên, cũng không có căn cứ để xác nhận 20/20. Phía triển khai cần thể hiện rõ cổng áp dụng, thiếu dữ liệu, physical status và gate status. Nếu tuyên bố nghiệm thu toàn bộ 20 cổng, trạng thái tổng phải phản ánh các cổng bắt buộc thất bại.

**Quyết định cho F5: chuyển Gemini xử lý; không ký PASS 100% toàn Bộ lọc 8.** F5 không phủ nhận kết quả bốn probes, so sánh pixel và regression đã chạy. Nó giới hạn việc dùng biên bản này để chốt toàn bộ gói v4.7 hoặc tuyên bố tuân thủ toàn bộ các cổng mới.

## 6. Tính toàn vẹn và khả năng tái lập

Manifest đầu ca theo dõi 31 tệp, gồm 17 tệp trong thư mục sản phẩm, 10 tệp production/test và 4 script audit. SHA256, dung lượng và mtime được đối chiếu cuối ca. Toàn bộ sản phẩm và mã nguồn production/test giữ nguyên. Thay đổi duy nhất trong tập theo dõi là sửa loader của script audit `inspect_products.py`.

Lần chạy đầu của script audit bổ sung gặp lỗi import dataclass trên Python 3.12. CODEX đã đăng ký module `independent_compliance` vào `sys.modules` trước `exec_module`, rồi chạy lại thành công. Bản script trước sửa được lưu trong `previous_evidence`. Thay đổi này không sửa checker, solver hoặc bất kỳ điều kiện nghiệm thu nào.

Mã nguồn, DXF và PNG được nhận diện bằng hash đầy đủ trong manifest. Các hash chính:

| Tệp | SHA256 |
|---|---|
| cad_collision_solver.py | `d696f358501a72a859c6b617a7620cdd511335aa819931eac8e31d7d17f8c5b7` |
| KC-01_DA_NE_CHU_LeaderLine.dxf | `d393d359cdb2c941aa1ea0bde4241216c406a409802d620d613239af09153c9e` |
| KC-02_DA_NE_CHU_LeaderLine.dxf | `01a0293abc275dfe896fee4ff5d357bb40fa91ce44935fc9acd157ec5236bf8d` |
| KC-02_after.png | `731402d9db9f4a53de273fb030f4a5ad8576305f44a402af61622da181f9cf58` |

Không chạy installer hoặc thực thi phần mềm nguồn ngoài. Không commit, không push GitHub. Các thao tác ghi giới hạn ở bằng chứng audit và Bus IPC. Quyền phát hành ra ngoài vẫn thuộc User.

## 7. Hồ sơ và quyết định ký xác nhận

Bằng chứng của vòng này nằm tại [recheck_signoff_20261114](recheck_signoff_20261114/). Dữ liệu chính là `adversarial_probes.json`, `preview_comparison.json`, `product_measurements.json`, `full_tests/timings.json`, `integrity.json` và `verdict.json`. `previous_evidence` giữ bản tài liệu có tại thời điểm bắt đầu ca. Các bản sao script trong thư mục bằng chứng dùng để truy vết; chạy lại các entry point ở thư mục audit gốc để giữ đúng cách xác định đường dẫn.

Lệnh tái lập từ workspace:

```powershell
python "G:/My Drive/Google AI Studio/.agents/memory/audits/sprint2_field_refinement_independent_20261114/adversarial_probes.py"
python "G:/My Drive/Google AI Studio/.agents/memory/audits/sprint2_field_refinement_independent_20261114/compare_previews.py"
python "G:/My Drive/Google AI Studio/.agents/tests/run_all_tests.py" --report-dir "G:/My Drive/Google AI Studio/.agents/memory/audits/sprint2_field_refinement_independent_20261114/recheck_signoff_20261114/full_tests"
```

CODEX xác nhận **đóng F1–F4 theo các phản ví dụ gốc, chấp nhận ảnh đã đồng bộ và kết quả regression 30/30**. Phạm vi này được nghiệm thu chính thức bằng biên bản hiện tại. Full 20-gate compliance và phê duyệt xuất bản vẫn chưa được xác nhận.

| Trách nhiệm | Chủ thể | Trạng thái |
|---|---|---|
| Triển khai bản sửa | Gemini | Đã bàn giao để tái kiểm |
| Kiểm toán phần mềm, đề xuất | CODEX — Trợ lý AI, cần kỹ sư có chứng chỉ hành nghề kiểm tra xác nhận trước khi ký hồ sơ thiết kế | APPROVED cho phạm vi nêu trên |
| Xử lý F5 và hợp đồng trạng thái checker | Gemini | Cần đối soát |
| Phê duyệt phát hành/GitHub | User — Kỹ sư Trưởng | Chưa cấp quyền push |
