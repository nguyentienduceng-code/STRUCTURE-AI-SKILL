# Kiểm toán xác nhận độc lập Sprint v7.5.x

- **Ca** `MASTER_SYSTEM_VERIFY_V75X_20261122`
- **Commit** `d7707bd17a762880a04b5a7ce01b48b58ac401a8` · Windows · Python 3.12.7
- **Kết luận** Xác nhận P0-1. P0-2 và P0-4 chưa đạt. P0-3 đạt một phần. `BP-01` đã chạy qua checker và danh mục 25 cổng có đủ mã. Hai điều kiện xác nhận còn mở là phạm vi hình học của DCE và cách nội suy độ võng giới hạn.
- **Bằng chứng** [Nhật ký, mã thoát, snapshot SHA-256 và phép kiểm độc lập](EVIDENCE.zip) · SHA-256 `ea5aa53faf11f992119e6dd511f82f1abef9810ed5a190c221215bfa1f340cea`

## 1. Kết quả theo hạng mục

| Hạng mục | Kết quả | Bằng chứng chính |
| --- | --- | --- |
| P0-1 · `--full` trên checkout sạch | Đạt | **50/50 PASS**, 295,23 giây, exit 0. |
| P0-2 · Cô lập đầu ra kiểm thử | Chưa đạt | 0 thay đổi trong `RECEIPTS` và `traces`. Có 1 DB phát sinh trong đường dẫn vận hành. |
| P0-3 · 25 cổng theo bằng chứng và BP-01 | Đạt một phần | Hai mẫu BP-01 đạt các cổng áp dụng. G8.25 vẫn PASS với một mẫu có tâm vùng làm việc nằm ngoài ranh giới vẽ. G8.23 và G8.24 còn giới hạn về độ bao phủ. |
| P0-4 · TCVN 2737:2023 Bảng G.1 | Chưa đạt | Các mốc và nhãn tiêu chuẩn đã cập nhật. Nội suy mẫu số thay cho độ võng giới hạn làm đổi FAIL thành PASS ở ca nhịp 9 m. |

## 2. P0-1 và P0-2 · Tái lập và kiểm tra rò rỉ

Đối chiếu Git index với commit rồi trích toàn bộ tệp được quản lý vào thư mục tạm. Chạy `python .agents/tests/run_all_tests.py --full --report-dir <temp>/suite_logs` từ thư mục này, với môi trường UTF-8, tắt ghi bytecode và đặt cache đồ họa và CAD trong thư mục tạm. Không cần mang theo `01_Projects`, thư mục người dùng `00_Template_&_Standards/CAD_Forms` hay thư mục rỗng `_deprecated`. Suite 1 kiểm tra sự vắng mặt của các script đã chuyển, suite 23 dùng fixture được quản lý và suite 40 dựng tầng biểu mẫu người dùng từ bản chuẩn vào thư mục tạm. [Suite 1](../../../tests/integration_test.py#L87) · [Fixture suite 23](../../../tests/fixtures/calc_hoist_ssot_fixture.py) · [Suite 40](../../../tests/test_cad_open_forms_and_blocks.py)

Snapshot từ **1.259 lên 1.260 mục**. Tệp mới duy nhất là `.agents/_SHARED/standards/standards_graph.db`. Có 0 tệp/thư mục bị xóa hoặc thay đổi. Phép so dùng đường dẫn và SHA-256 của nội dung dưới `.agents`, đồng thời ghi nhận thư mục mới hoặc mất. Số rò rỉ là số chênh lệch còn lại sau lượt chạy. Một phần logic ghi biên nhận đã chuyển sang xác định workspace tại thời điểm gọi. Các test bus và trạng thái đã chuyển một số đầu ra sang vùng tạm. Riêng suite 14 vẫn tạo DB ở đường dẫn mặc định. Biên nhận thật do thao tác chuyển ca sau kiểm toán thuộc luồng vận hành. [Bus](../../../tools/sync_bus.py#L624) · [Kiểm thử trạng thái](../../../tests/test_cognitive_and_control_systems.py) · [Kiểm thử policy](../../../tests/test_policy_engine.py#L494)

**Tái hiện độc lập P0-2.** Trên bản checkout thứ hai, chạy `--suite 14` đạt 55/55 test, exit 0, và tạo DB cùng SHA-256 `b98feb78e1d791574786c9fe3c6298249e487ab887835dd6608ddcf9d36a528e` như lượt `--full`. Module `standards_graph.py` khởi tạo `StandardsGraph()` khi import. Hàm khởi tạo mở DB mặc định trước khi fixture tạo `sg_test.db` riêng. Cần bỏ thao tác mở DB tại import hoặc cấu hình đường dẫn thử trước import, rồi chạy lại hai snapshot. [Khởi tạo kho mặc định](../../../_SHARED/standards/standards_graph.py#L136) · [Khởi tạo khi import](../../../_SHARED/standards/standards_graph.py#L907)

| Kiểm tra bổ sung | Kết quả | Mã thoát |
| --- | --- | --- |
| `audit_zero_white_text.py` tại bản sao | 487 tệp, 29 nhóm, 0 cảnh báo | 0 |
| `sync_bus.py --validate` trên ticket đang giữ | Schema hợp lệ | 0 |
| Chạy trực tiếp `test_deflection_check.py` | 6/6 test có sẵn PASS | 0 |

## 3. P0-3 · 25 cổng DCE và BP-01

Sinh DXF bằng các entry point thật, tính lại SHA-256 và đối chiếu cả hai trường hash của sidecar. Chạy profile tương ứng và kiểm tra danh sách đủ 25 mã duy nhất G8.01–G8.25 trên mỗi mẫu. Suite 35 và 41 có ca âm tính cho hồ sơ thiếu vùng an toàn, thiếu thiết bị, thiếu ký hiệu hàn, sai bước lỗ và DXF lệch hash sidecar.

| Mẫu | PASS | N/A | FAIL | Kết quả checker |
| --- | ---: | ---: | ---: | --- |
| BP-01 mặc định | 6 | 19 | 0 | PASS |
| BP-01 với vị trí và bán kính khác | 6 | 19 | 0 | PASS |
| BP-01 với tâm vùng làm việc ngoài ranh giới vẽ | 6 | 19 | 0 | PASS |
| BP-02 mặc định | 12 | 13 | 0 | PASS |
| ST-01 mặc định | 12 | 13 | 0 | PASS |

G8.01 của BP-01 đã PASS. G8.23 và G8.24 được ghi N/A theo bố cục tổng mặt bằng. Sáu cổng áp dụng đạt trong hai mẫu dương là G8.01, .02, .12, .17, .20 và .25. Với từng mẫu, `full_compliance_verified=true` nghĩa là các cổng mà checker đánh dấu áp dụng đều PASS. `probes-stdout.txt` lưu từng cổng, trạng thái, bằng chứng trả về và hash DXF. [Engine BP-01](../../../skills/Technical_Illustrator/cad_integration/cad_bptc_engine.py#L405) · [Tổng hợp trạng thái](../../../skills/SKILL_VERIFY/scripts/dce_cad_compliance_checker.py#L1531) · [Đặc tả](../../../docs/SPEC_DCE_PRO_V5.md#L29)

- **G8.25** kiểm tra có thiết bị và vòng bán kính dương trên BP-01. Mẫu thử có tâm nằm ngoài ranh giới vẫn PASS. Điều này xác nhận cổng chưa đối chiếu vị trí hay khoảng hở với ranh giới và vật cản. Trên BP-02 cổng dùng số lượng thực thể và kết quả kiểm lỗ, chưa đối chiếu chiều sâu neo với hồ sơ tính. Kết quả là kiểm chứng sự có mặt của hình học. [G8.25](../../../skills/SKILL_VERIFY/scripts/dce_cad_compliance_checker.py#L819)
- **G8.23** đã đọc tổng khối lượng trên DXF và đối chiếu sidecar. Mã chưa đối chiếu tiết diện từng cấu kiện với dữ liệu tính độc lập. **G8.24** kiểm tra số khung và tìm nhãn tỷ lệ trên bản vẽ, chưa gắn nhãn và DimStyle với từng ô chi tiết. Các cổng theo profile nên đánh dấu chưa xác minh khi thiếu loại bằng chứng mà đặc tả yêu cầu. [G8.23–24](../../../skills/SKILL_VERIFY/scripts/dce_cad_compliance_checker.py#L744) · [Hợp đồng dữ liệu](../../../docs/SPEC_DCE_PRO_V5.md#L56)

## 4. P0-4 · Đối chiếu trực tiếp Bảng G.1

Đọc bản PDF TCVN 2737:2023 trong thư mục tiêu chuẩn của workspace, SHA-256 `33bfafe019a77f71188f05a1146b0e1575da95c1f9ccfd1658243934fb21953d`. Đối chiếu Lời nói đầu trang 5, G.1.7 và Bảng G.1 mục 2a, chú thích 1–3, trang 79–81. Tuyến mặc định đã chuyển sang TCVN 2737:2023. Mốc 6 m cho 30 mm, tuyến legacy ở cùng nhịp cho 24 mm có cảnh báo. Các mốc theo chiều cao phòng khớp bảng. [Danh mục tiêu chuẩn VSQI](https://tieuchuan.vsqi.gov.vn/tieuchuan/view?sohieu=TCVN+2737%3A2023) · [Calculator](../../../skills/Design_Evaluation/calculators/deflection_check.py#L7) · [Khóa tiêu chuẩn](../../../skills/STANDARDS_LOCK.md#L48)

Chú thích 2 yêu cầu nội suy tuyến tính **độ võng giới hạn**. Phép tính đối chiếu nội suy giữa hai giá trị `f_u` đã đổi ra mm. Calculator nội suy giữa hai mẫu số `L/f_u` trước khi chia chiều dài, tạo chênh lệch ngay trong phạm vi mặc định.

| Ca kiểm tra | Giới hạn theo bảng và chú thích | Calculator |
| --- | ---: | ---: |
| Nhịp 6 m, phòng ≤6 m | 30,00 mm | 30,00 mm |
| Nhịp 9 m, phòng ≤6 m | 39,00 mm, trung điểm của 30 và 48 mm | 40,00 mm |
| Nhịp 12 m, phòng >6 m | 52,00 mm, nội suy giữa 30 và 96 mm | 55,38 mm |
| Công xôn vươn 3 m, `L` tra bảng bằng 6 m | 30,00 mm cho giới hạn bảng | 15,00 mm |

**Ca đổi kết luận.** Với nhịp 9 m, đầu vào mô men 379 kN·m, `E=30×10^6` kPa, `I_eff=0,0054` m⁴, calculator tính võng 39,48 mm và báo PASS so với 40 mm. Giữ nguyên giá trị võng để cô lập ảnh hưởng của giới hạn, kết quả là **FAIL** khi so với 39 mm. Ca công xôn còn dùng chiều dài vươn ở tử số và giữ công thức chuyển vị của dầm hai gối. Phép đối chiếu ở dòng công xôn chỉ xác nhận giới hạn bảng. Các test giữa mốc đang đặt kỳ vọng theo mẫu số nội suy, nên bộ 6/6 chưa phát hiện chênh lệch này. [Phép tra và tính](../../../skills/Design_Evaluation/calculators/deflection_check.py#L17) · [Giá trị kỳ vọng của test](../../../skills/Design_Evaluation/calculators/tests/test_deflection_check.py#L23)

## 5. Bàn giao

Chuyển `NEED_REVIEW` cho Gemini với ba hạng mục còn mở. P0-2 cần cô lập DB tại thời điểm import. P0-3 cần phân biệt kiểm tra có thực thể với kiểm tra hình học và nguồn đối chiếu. P0-4 cần nội suy `f_u` theo Bảng G.1, xác định rõ phạm vi công xôn, và thêm ca biên có thể đổi PASS/FAIL. Phạm vi ghi của ca gồm báo cáo, bằng chứng và tệp điều phối do CLI quản lý. HEAD được kiểm tra ở `d7707bd`.

