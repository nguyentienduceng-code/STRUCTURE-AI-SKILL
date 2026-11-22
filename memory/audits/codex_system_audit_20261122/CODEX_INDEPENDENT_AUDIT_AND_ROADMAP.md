# Kiểm toán độc lập hệ thống .agents và lộ trình v7.5 → v8.0+

- **Ca** `MASTER_SYSTEM_AUDIT_20261122`
- **Mốc mã** `ac3b80fa6adc125c0e228797166fc0eca5a78c85` · Windows · Python 3.12.7
- **Kết luận** Giữ v7.5 làm đường cơ sở. Ưu tiên độ tin cậy của kết quả kiểm toán và khả năng tái lập trước khi mở rộng phạm vi DCE.
- **Bằng chứng** [Nhật ký kiểm toán, mã thoát và kết quả theo suite](EVIDENCE.zip) · SHA-256 `0cd223a30beb005d4e8cca442457a352dc9cb05648f919dad170b5a2d78a8582`

## 1. Kiểm thử độc lập

| Lệnh | Phạm vi và kết quả | Mã thoát |
| --- | --- | --- |
| `python .agents/tests/run_all_tests.py --full --report-dir …` | 50 suite đã chạy, **48 PASS / 2 FAIL** trong 428,90 giây. Suite 1 thiếu thư mục rỗng và suite 40 thiếu đầu vào CAD Forms. | 1 |
| `python .agents/tests/run_all_tests.py --full --report-dir …` | 50 suite đã chạy, **49 PASS / 1 FAIL** trong 309,97 giây. Suite 1 đạt sau khi bổ sung thư mục, suite 40 còn thiếu CAD Forms tại thời điểm chạy. | 1 |
| `python .agents/tests/run_all_tests.py --suite 1 --report-dir …` | 1/1 trong bản sao có thư mục rỗng. Chạy riêng tại workspace cũng đạt 64/64 checks. | 0 cho cả hai |
| `python .agents/tools/audit_zero_white_text.py` | Bản commit tách riêng và workspace đều quét 484 tệp thuộc 29 nhóm, 0 cảnh báo. | 0 cho cả hai |
| `python .agents/tools/sync_bus.py --validate` | Schema bus đang giữ ca hợp lệ. | 0 |

Cả hai lần chạy đầy đủ dùng cùng nội dung Git và bản sao của một đầu vào ngoài repo mà suite 23 yêu cầu trực tiếp, `01_Projects/16.BPTC Q12/02_Calculation_Models/calc_hoist_sunrise_q12.py`. Lần tái lập thêm thư mục rỗng `skills/Technical_Illustrator/scripts/_deprecated` có sẵn ở workspace. Suite 1 dựa vào sự tồn tại của thư mục này. Git không lưu thư mục rỗng, nên sự khác biệt tái hiện được giữa bản checkout sạch và workspace. Suite 40 kiểm tra thêm bản sao người dùng của bốn CAD Form, manifest và README trong `00_Template_&_Standards/CAD_Forms`, ngoài phạm vi repo. Sau khi sao chép đủ nhóm tệp vào bản tách riêng, chạy `--suite 40` đạt 5/5 test, mã thoát 0. Thư mục biểu mẫu chưa có ở thời điểm suite 40 chạy trong hai lần `--full`. Suite 17 ghi các workbook tùy chọn vắng mặt là bỏ qua nhưng cộng vào số PASS. Suite 18 dùng DXF tự sinh khi thiếu hồ sơ dự án. Đọc danh sách suite và điều kiện đầu vào cùng bảng tổng hợp trước khi diễn giải độ phủ. [Suite 1](../../../tests/integration_test.py#L88) · [Suite 17](../../../tests/test_suite17_xlsx_view_sanity.py#L159) · [Suite 18](../../../tests/test_dce_cad_compliance.py#L122) · [Suite 23](../../../tests/test_citation_grounding_guard.py#L435) · [Suite 40](../../../tests/test_cad_open_forms_and_blocks.py#L57)

Báo cáo cũ ghi **33 suite, 854 checks**. Collector nhập 33 mục tĩnh trong `SUITES`, còn runner đăng ký thêm 17 tệp tại thời điểm chạy. Một số phân hệ tự đếm kiểm tra lồng nhau hoặc có skip. Mốc 854 thuộc báo cáo cũ, còn kết quả lần này dựa trên 50 mã thoát của suite, bảng thời gian và stdout/stderr riêng. Bộ quét Điều 12b/12e là kiểm tra mẫu trong mã và Markdown. Chất lượng Word, Excel và bản in cần kiểm tra trên sản phẩm thực. [Runner](../../../tests/run_all_tests.py#L72) · [Collector](../../../tools/_collect_tests.py#L217) · [Bộ quét](../../../tools/audit_zero_white_text.py#L38)

## 2. DCE Pro v5.0 và K1–K5

| Hạng mục | Kết quả thẩm tra | Phần còn thiếu |
| --- | --- | --- |
| K1 · Cổng có bằng chứng | G8.02 đọc bảng layer. G8.21 đo tâm/radius lỗ và bounding box bản mã. G8.22 đếm thực thể hàn, tam giác và nhãn. G8.25 đếm thực thể thiết bị, giằng, neo và vùng an toàn. Có test âm tính cho cả G8.21, G8.22 và G8.25. | G8.03–04, .06, .09–12 và .17–20 trả PASS hằng trong nhánh thép/BPTC. G8.21 thiếu phép ghép từng lỗ với bản mã, G8.22 thiếu liên kết nhãn theo từng mối, G8.25 chưa đo khoảng hở và chiều chôn neo. G8.23 cộng các dòng cùng sidecar và G8.24 kiểm tra khai báo bố cục, nên hai cổng chưa đối chiếu độc lập với DXF và nguồn tính. |
| K2 · Liên kết DXF–sidecar | Các engine lưu SHA-256 byte DXF vào sidecar. Test thay đổi DXF báo `NEEDS_REVIEW`. | Giữ hợp đồng nguồn tính độc lập với mã băm DXF. Chuỗi đầu vào tính toán → DXF → BOM chưa được kiểm chứng ở G8.23. |
| K3 · Chuẩn layer | JSON chốt `DCE_Steel_Plate` màu 6/lw25 và `DCE_Steel_Bolt` màu 1/lw18. | Tài liệu chiến lược vẫn ghi 3/35 và 2/25. `SPEC_DCE_PRO_V5.md` được nêu trong báo cáo Maker nhưng thiếu ở tree của commit. G8.02 mới kiểm tra lineweight dương. |
| K4 · Quy cách thép | Mẫu đầu vào không nhận dạng trả `GENERIC` kèm một cảnh báo. Chế độ strict trả `ValueError`. | Cần bắt buộc dữ liệu tiết diện được xác nhận tại các luồng dùng cho phát hành và có đường đi rõ ràng cho chế độ tương thích. |
| K5 · Nhãn chiều dài hàn | Có nhãn `lw toàn bộ` khi `lw <= 0`, với test kiểm tra metadata và đối tượng chữ. | Cần xác định tại đầu vào khi nào được phép hiểu là hàn toàn chiều dài. |

**Phát hiện chặn xác nhận DCE đầy đủ.** `full_compliance_verified` vẫn có thể là true khi một phần cổng chỉ dựa vào khai báo. Hợp đồng `BP-01` cũng tự mâu thuẫn. Gọi trực tiếp `generate_bp01_site_plan()` với mặc định rồi kiểm tra hồ sơ `bptc` cho kết quả **FAIL tại G8.01, G8.23, G8.24**. Công cụ sinh bản vẽ đã có `ST-01`, `BP-01` và `BP-02`. Các mục `ST-02..04` và `BP-03` thuộc phạm vi kế hoạch. [Checker](../../../skills/SKILL_VERIFY/scripts/dce_cad_compliance_checker.py#L229) · [BPTC](../../../skills/Technical_Illustrator/cad_integration/cad_bptc_engine.py#L405) · [PEB](../../../skills/Technical_Illustrator/cad_integration/cad_steel_peb_engine.py#L83) · [Primitives](../../../skills/Technical_Illustrator/cad_integration/cad_steel_primitives.py#L57) · [Chuẩn layer](../../../_SHARED/data/dce_layers_standard.json#L1039) · [Chiến lược DCE](../../../docs/CHIEN_LUOC_NANG_CAP_CAD_DCE_PRO_V5.md#L47)

## 3. Đồng bộ nguồn chuẩn và nhiễm dữ liệu test

- Ba bản `AGENTS.md` hiện trùng byte, SHA-256 `7effda4a0323907e022666cd2b1768de43ccbe2d31162f816a6ff82ad0209b40`. Drift đã xác nhận nằm ở danh mục suite, cấu hình layer trong tài liệu và mẫu số độ phủ calculator. TD-07 ghi 23/95, còn bản inventory tự sinh ghi 122 script. Chưa có bảng định danh từng calculator nối với assertion và phiên bản tiêu chuẩn để so hai số này. [Nợ kỹ thuật](../../../docs/TECHNICAL_DEBT.md#L128) · [Inventory](../../../docs/BAO_CAO_PHAT_TRIEN_DIEU_PHOI_AI.md#L129)
- So sánh tệp sau test với tree của commit cho thấy 0 tệp Git thay đổi, 0 tệp Git bị thiếu và 5 tệp mới gồm 3 biên nhận, 1 trace và 1 cơ sở dữ liệu `standards_graph.db`. Biên nhận test nằm dưới đường dẫn vận hành của bản sao. Khi chạy trên workspace thật, các tệp dạng này có thể lẫn vào lịch sử ca trực. Suite 11 đã chuyển đầu ra chính vào thư mục tạm, song vẫn có hai đường dẫn tìm module tuyệt đối từ môi trường kiểm thử cũ. [Suite 11](../../../tests/test_dce_deep_integration.py#L28) · [Bộ ghi biên nhận](../../../tools/sync_bus.py#L615)

## 4. Liêm chính tiêu chuẩn và calculator

- Bộ regression sử dụng các entry point thép theo TCVN 5575:2024. Khóa phiên bản chỉ rõ nhánh 2012 và Eurocode phục vụ đối chiếu. Calculator gió yêu cầu `gamma_f` tường minh và đánh dấu thiếu căn cứ nguồn. Đây là kiểm tra hợp đồng và định tuyến mẫu. Từng công thức và phạm vi áp dụng vẫn cần hồ sơ thẩm tra theo điều khoản. [Regression](../../../tests/test_runner.py#L46) · [Khóa tiêu chuẩn](../../../skills/STANDARDS_LOCK.md#L42) · [TCVN 5575:2024, VSQI](https://tieuchuan.vsqi.gov.vn/tieuchuan/view?sohieu=TCVN+5575%3A2024)
- **Drift có ảnh hưởng nghiệp vụ.** `deflection_check.py` xuất `Standard_Method`, trích dẫn và ngưỡng theo Phụ lục M TCVN 5574:2018. `STANDARDS_LOCK.md` vẫn gắn nhãn khớp. VSQI xác nhận Điều 11 và Phụ lục G TCVN 2737:2023 thay Phụ lục M này. Rà riêng giới hạn độ võng và mô hình tính độ võng. Đưa nhánh hiện tại về chế độ đối chiếu có chỉ định cho đến khi kỹ sư xác nhận bảng/điều thay thế và bộ ví dụ vàng. [Calculator](../../../skills/Design_Evaluation/calculators/deflection_check.py#L45) · [Khóa tiêu chuẩn](../../../skills/STANDARDS_LOCK.md#L48) · [TCVN 2737:2023, VSQI](https://tieuchuan.vsqi.gov.vn/tieuchuan/view?sohieu=TCVN+2737%3A2023)
- Soát mẫu số hiệu TCVN 10304:2025, Thông tư 34/2026/TT-BXD và QCVN 18:2021/BXD qua nguồn công bố. Các tuyên bố về kích thước lỗ, neo, khoảng hở và khả năng áp dụng vào công trường cần hồ sơ nguồn cấp điều khoản. Điểm PASS của DCE chỉ có giá trị theo phép đo thực hiện được. [TCVN 10304:2025, VSQI](https://tieuchuan.vsqi.gov.vn/tieuchuan/view?sohieu=TCVN+10304%3A2025) · [Thông tư 34/2026](https://vanban.chinhphu.vn/?docid=218637&pageid=27160) · [QCVN 18:2021/BXD](https://vanban.chinhphu.vn/default.aspx?docid=204974&pageid=27160)

## 5. 2D Dispatcher và Dual-Agent Bus v3.4

- Chạy lại prompt của chính ca. `/sys` cho `SYSTEM_UPGRADE`, `AUTO`, bus bật. Domain vẫn rơi vào `SKILL_GEOTECH` với 0,35 do keyword `Su`. Ticket chứa đồng thời `primary_skill=Design_Evaluation`. Từ trùng yếu được ưu tiên trước domain tổng và ngưỡng `< 0.35` giữ nguyên trường hợp bằng 0,35. Hai trường skill khác nhau khiến tác tử đọc nhầm hướng dẫn cho ca hệ thống. [Classifier](../../../skills/Global_Dispatcher/intent_classifier.py#L165)
- Nhận ca CODEX, lấy lease và kiểm tra schema thành công. `lease_ttl_sec=600` trong ticket trong khi CLI cấp 60 phút theo mặc định từ cấu hình môi trường máy. `handoff_status` được cập nhật khi claim còn `work_ticket.status` vẫn `QUEUED`. Khóa cục bộ điều phối tiến trình trên cùng máy. Chưa thẩm tra tính nhất quán giữa hai máy qua Google Drive. `--validate` kiểm tra schema, còn nghiệm thu lệnh, sản phẩm và kết quả cần dựa vào bằng chứng riêng. [Bus](../../../tools/sync_bus.py#L89) · [Claim](../../../tools/sync_bus.py#L1422)

## 6. Giá trị thực chiến của 01_Projects

| Mẫu đọc | Bằng chứng quan sát được | Giá trị và ranh giới |
| --- | --- | --- |
| Sprint 2, ba bản KC-01/KC-02/KC-03 v50 | Cả ba DXF mở được, 0 lỗi `ezdxf.audit()`, `physical_status=PASS`. Profile hiện hành `plan` trả FAIL với 13/15/14 cổng lỗi theo thứ tự. | Có đầu ra CAD thật để xây bộ hồi quy theo phiên bản. Cần giữ tương quan giữa phiên bản producer, hồ sơ và checker trước khi diễn giải lỗi hiện hành thành lỗi thiết kế gốc. |
| Sunrise Q12 · thuyết minh vận thăng v3 | DOCX đọc được 307 đoạn và 15 bảng. Script dự án dùng chung mô-đun citation và calculator, có kiểm tra hồi quy nhập mô-đun chuẩn tại suite 23. | Có đường nối từ tính toán sang hồ sơ. Chưa đối soát từng ô DOCX với toàn bộ đầu vào hoặc phiên bản mô hình ban đầu. |
| Liên Chiểu · nhiệm vụ khảo sát | PDF 7 trang, XLSX 3 sheet, DXF 164 đối tượng trong model space và 0 lỗi đọc audit. | Có đầu ra đa định dạng để thử đối soát tọa độ và truy vết. Ca này xác nhận khả năng đọc và nhận dạng mẫu, chưa so khớp từng tọa độ hoặc ký duyệt nhiệm vụ. |

Đây là mẫu có chủ đích. SHA-256 và đường dẫn tương đối nằm trong `targeted-stdout.txt`. Chưa có dữ liệu thời gian thủ công đối chứng, số lỗi qua thẩm tra hay hồ sơ nghiệm thu đã ký để tính hiệu quả định lượng. Vai trò phù hợp là trợ lý hậu xử lý, đối chiếu và rà soát cho kỹ sư chủ trì. [Định hướng kiến trúc](../../../docs/STRATEGIC_ALIGNMENT_GEMINI_CODEX.md#L21)

## 7. Lộ trình đề xuất

| Chân trời | Trọng tâm | Điều kiện qua mốc |
| --- | --- | --- |
| **v7.5.x · Sprint kế tiếp** | Tái lập kiểm thử từ checkout mới. Chốt danh mục test, sửa phân loại và cách trình bày trạng thái. Chặn tuyên bố DCE đầy đủ khi bằng chứng chưa đủ và rà ngay tiêu chuẩn võng. | Một lần `--full` ở checkout có fixture được quản lý đạt 50/50 hoặc toàn bộ danh mục mới. 0 đầu ra lẫn vào thư mục vận hành. Mỗi cổng CAD có căn cứ PASS, FAIL, N/A hoặc chưa xác minh. |
| **v7.6–v7.9 · 2–3 sprint sau** | Thử nghiệm BTCT, BPTC và hồ sơ khảo sát đã ẩn thông tin nhạy cảm. Đối chiếu từng mục từ đầu vào, calculator, bản vẽ đến hồ sơ. Mở rộng cổng DCE theo dữ liệu pilot và rà code theo mức rủi ro. | Mỗi mẫu có bộ đầu vào, phiên bản công cụ và mã băm cuối. Ghi số lần sửa lại, thời gian xử lý và lỗi phát hiện trên cả cách làm hiện tại lẫn cách có trợ lý. Kỹ sư duyệt các khác biệt. |
| **v8.0+ · Sau pilot** | Mở rộng điều phối nhiều dự án, biên nhận kiểm tra độc lập theo revision, tiếp nhận dữ liệu từ công cụ chuyên dụng và bảo toàn ghi đè của kỹ sư. Xem xét kho trạng thái giao dịch nếu kết quả đo cho thấy giới hạn điều phối file. | Tái hiện được job trên máy khác, xử lý được xung đột và khôi phục bước dở, truy được từng bản phát hành về mô hình nguồn và xác nhận của kỹ sư. |

### Next Sprint · 7 việc và tiêu chí nghiệm thu

| # | Ưu tiên · Phụ trách đề xuất | Việc | Nghiệm thu |
| --- | --- | --- | --- |
| 1 | P0 · Hạ tầng kiểm thử | Khai báo các điều kiện đầu vào của suite 1, 23 và 40 trong cấu hình test. | Suite 1 không lệ thuộc thư mục Git bỏ qua. Suite 23 và 40 dùng fixture có mã băm và kiểm tra đầu vào trước khi chạy. Mẫu dự án tùy chọn báo `SKIP` riêng. |
| 2 | P0 · Hạ tầng kiểm thử | Định tuyến ghi của test vào thư mục tạm theo từng suite. | Hai lần `--full` liên tiếp cho cùng kết quả và 0 biên nhận, trace hoặc DB mới trong đường dẫn vận hành. |
| 3 | P1 · Hạ tầng báo cáo | Sinh bảng kết quả phát hành từ chung một danh mục và tệp kết quả runner. | Số suite, commit, mã thoát và file log khớp máy đọc được. Mẫu số calculator có định danh và loại kiểm tra. |
| 4 | P0 · DCE/QA | Chốt hợp đồng kết quả cổng theo profile, gồm `BP-01`. | PASS cần phép đo hoặc nguồn có định danh. Cổng chưa đo không được tính là đã xác minh. Test dương và âm cho BP-01 cùng kiểm tra trạng thái tổng hợp. |
| 5 | P0 · Kỹ sư kết cấu/Calculator | Sửa tuyến kiểm tra giới hạn võng cho hồ sơ mới. | Khóa tiêu chuẩn, calculator và trích dẫn dùng cùng phiên bản được kỹ sư xác minh. Ca đối chiếu dùng điều khoản cũ có cờ rõ. |
| 6 | P1 · Điều phối | Sửa chọn domain cho ca hệ thống. | Prompt ca này, prompt địa kỹ thuật thật và prompt lai có kết quả kiểm thử. Skill chính ăn khớp domain hoặc nêu quy tắc chuyển tuyến rõ. |
| 7 | P1 · Điều phối | Thống nhất hợp đồng lease và trạng thái bus. | `claim`, `heartbeat`, `need-review` cho trạng thái/TTL khớp giữa ticket, bus và memo. Test hai tiến trình cùng máy bằng vùng dữ liệu tạm. |

### Kết quả bàn giao

Báo cáo và bằng chứng là đầu ra của ca kiểm toán. Mã chạy tại commit đã chỉ định, các thay đổi vận hành của bus thực hiện qua CLI, và dữ liệu test ghi trong bản sao. Kết quả phát hành của commit sạch và các cổng CAD được ghi theo từng phép kiểm để đối tác quyết định bước sửa tiếp theo.

