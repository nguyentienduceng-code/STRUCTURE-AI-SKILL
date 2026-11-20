# BIÊN BẢN KIỂM ĐỊNH ĐỘC LẬP HỆ THỐNG & DỰ ÁN

**Mã kiểm toán** AUDIT-CODEX-20261120  
**Đơn vị kiểm định** Codex (Chief Technical Auditor)  
**Ngày lập** 20/11/2026  
**Kết luận chung** **FAIL — Chưa đủ điều kiện nghiệm thu tổng thể**  
**Kính gửi** Tổng Công Trình Sư

Phạm vi gồm 5 chuyên đề tại Phần 7 của hồ sơ CODEX-AUDIT-PACKAGE-20261120-v3.4. Biên bản đối chiếu hồ sơ nguồn, mã triển khai, biên nhận P2 và sản phẩm thực tế trong thư mục dự án. Kết luận áp dụng cho bộ bằng chứng được kiểm tra ngày 20/11/2026. Hồ sơ nguồn có mã SHA-256 là `12b77d8230617ffc1e993036cae37d1ccf4a07cc2365946a081ab975e4ac885b`.

Ba điều kiện còn treo gồm phân luồng đúng ở điểm vào vận hành, bằng chứng trọn vòng CAD P2 và xác thực hồ sơ Cảng Liên Chiểu. Riêng hồ sơ dự án có **9 tệp mang tên phương án 21 hoặc 7 hố nhưng trùng từng byte** với bộ 8 hoặc 4 hố tương ứng. Chỉ số sử dụng η không áp dụng vì phạm vi kiểm định không gồm kiểm tra sức chịu tải cấu kiện.

## 1. Đánh giá Kiến trúc Phân luồng 2 Chiều (Rule 0)

**Kết luận chuyên đề — Chưa đạt điều kiện đưa vào vận hành bắt buộc.** Bộ thử hiện có đạt 12/12 ca khi chạy lại. Thử bổ sung bằng tiếng Việt cho thấy ngữ cảnh tham chiếu và câu giao việc tự nhiên vẫn có thể đổi tuyến sai.

| Ca đối chiếu | Kết quả quan sát | Đánh giá |
| --- | --- | --- |
| Sửa script cục bộ của `17_LIEN_CHIEU_DA_NANG` rồi xuất lại tờ trình | `PRODUCT_COLLAB`, điểm 0,85, đúng dự án, `allow_script_patch=True` | Luồng chuẩn hoạt động |
| Cùng yêu cầu trên, kèm tham chiếu `.agents/AGENTS.md` hoặc `.agents\skills\STANDARDS_LOCK.md` | `SYSTEM_UPGRADE`, điểm 0,90, mất dự án đích và quyền sửa script cục bộ | Sai đối tượng thao tác |
| “Chỉnh lại phần trình bày để bộ 17_LIEN_CHIEU_DA_NANG sẵn sàng gửi khách.” | `SOLO_EXECUTION`, điểm 0,00 | Bỏ sót yêu cầu sản phẩm có mã dự án |
| “Giải thích cú pháp /prod và /solo cho người mới.” | `PRODUCT_COLLAB`, điểm 1,00, yêu cầu xác nhận dự án | Cờ trong câu giải thích bị xem là lệnh |
| “/sys /prod sửa bộ phân luồng” | Chọn `PRODUCT_COLLAB` | Cờ xung đột được chọn theo thứ tự cấu hình |
| “Xuất tờ trình Word cho dự án Sao Hỏa.” | `PRODUCT_COLLAB`, `NOT_FOUND`, yêu cầu xác nhận | Khóa dự án thiếu hoạt động khi ý định sản phẩm đủ rõ |

Hai điểm vào cùng tên đang trả hai hợp đồng dữ liệu. Lệnh trong hướng dẫn Global_Dispatcher gọi bản dưới `scripts/`, trả chuyên môn Design_Evaluation với điểm 1,00 cho yêu cầu kiểm định. Bản 2D tại thư mục gốc trả `SOLO_EXECUTION` điểm 0,00 khi chỉ nhận câu giao việc. Khi nối thêm đường dẫn tệp nguồn, bản 2D trả `SYSTEM_UPGRADE` điểm 0,90. Sự khác biệt ảnh hưởng quyền ghi và cách mở ca. Hai bản `AGENTS.md` ở `.agents` và `.agents/skills` trùng toàn tệp theo SHA-256. Trạng thái đồng bộ Điều 0 trên bản thứ ba và các điểm vào cần kiểm thử riêng.

Phân giải dự án thực tế dùng ngưỡng 0,38 và khoảng cách điểm 0,12. Nhiều ứng viên qua ngưỡng vẫn có thể tự chọn ứng viên đứng đầu. Điều 0.2 yêu cầu xác nhận khi từ hai dự án trở lên cùng khớp. Nên quy định rõ trường hợp mã dự án chính xác ưu tiên hơn tên gần đúng, rồi đồng bộ quy tắc với bộ thử hai rễ. Trạng thái chờ xác nhận phải giữ quyền ghi ở mức chưa cấp.

Điểm 0,35 là điểm cộng trọng số từ khóa, chưa có hiệu chuẩn như xác suất. Giảm ngưỡng vẫn không cứu được ca điểm 0,00. Kiến nghị dùng ngưỡng này cho câu hỏi thực sự độc lập. Khi có mã dự án, yêu cầu bàn giao hoặc dấu hiệu sửa tài liệu mà ý định chưa rõ, cần giữ yêu cầu ở trạng thái làm rõ trước khi mở ca. Chỉ nhận cờ điều khiển tại đầu câu giao việc. Chuẩn hóa đường dẫn Windows và POSIX, đồng thời xác định tệp đang được yêu cầu sửa hay chỉ được viện dẫn. Khi có cả hai loại thao tác thật, biểu diễn thành các bước nối tiếp có quyền và đầu ra riêng.

Căn cứ đối chiếu gồm [bộ phân loại 2D](<G:/My Drive/Google AI Studio/.agents/skills/Global_Dispatcher/intent_classifier.py:195>), [bộ phân giải dự án](<G:/My Drive/Google AI Studio/.agents/skills/Global_Dispatcher/project_target_resolver.py:181>), [hướng dẫn điểm vào](<G:/My Drive/Google AI Studio/.agents/skills/Global_Dispatcher/SKILL.md>) và [12 ca hồi quy](<G:/My Drive/Google AI Studio/.agents/tests/test_dispatcher_2d_modes.py>).

## 2. Đánh giá Cơ chế Phân vai Gemini Maker ↔ Claude Lead Reviewer

**Kết luận chuyên đề — Phân vai khả thi có điều kiện. Cổng bàn giao hiện chưa đủ để nghiệm thu.**

Máy kiểm định chạy Python 3.11.9 và nạp được các thư viện đọc Word, Excel, PDF và DXF. Kết quả này xác nhận khả năng đọc trên máy kiểm định. Quyền sửa, quyền ghi ổ G:, môi trường COM của Microsoft Word và đường dẫn AutoCAD/ODA trong từng phiên Claude còn cần xác minh. Script thuyết minh 8 hố lưu DOCX rồi gọi Word qua `win32com` để xuất PDF. Cần thực hiện kiểm tra môi trường ngay trong tiến trình xuất, với phiên bản phụ thuộc đã chốt và dữ liệu thử được duyệt.

`allow_script_patch=True` mô tả ý định sửa script dự án. Quyền ghi thật cần được xác định theo host, thư mục và phiên bản đầu vào. Khi Claude trực tiếp sửa và chạy, biên bản đầu ra cần ghi người kiểm tra lại thay đổi và người duyệt số liệu. Nên xuất vào thư mục tạm, đọc lại sản phẩm rồi mới chuyển bản đủ điều kiện sang vị trí bàn giao. Cách này giữ nguyên bản đã duyệt khi xuất lỗi giữa chừng hoặc khi Word đang mở tệp đích.

`ProductDeliverableGate.verify()` thu thập tệp theo phần mở rộng, dung lượng và thời điểm sửa, rồi ghi mã băm. Điều kiện hiện tại chỉ yêu cầu có ít nhất một tệp đủ thuộc tính. Cổng chưa yêu cầu đủ từng sản phẩm theo đơn, chưa mở tệp để xác nhận định dạng và chưa ràng buộc mã dự án hoặc phương án trong nội dung. Trường hợp Liên Chiểu cho thấy tệp mới có thể đọc được nhưng vẫn mang dữ liệu dự án khác. Kiến nghị dùng danh mục đầu ra theo ca, gồm mã dự án, giai đoạn, phương án, phiên bản, tên tệp, số đối tượng dự kiến và mã băm nguồn. Đọc được đủ định dạng và đối soát mã hố giữa bảng tính, thuyết minh và CAD trước khi đóng ca.

`JargonLinter` chặn được “SHA-256” và “refactor” trong phép thử. Câu “All done.” vẫn đạt dù thiếu cả 3 ý. Câu “Đã rà soát file theo TCVN.” cũng đạt và được xem là đủ ý dù thiếu vị trí file và kết quả. Cần sinh báo cáo từ ba trường bắt buộc, nối trường đường dẫn với danh mục đã xác minh và bắt buộc kết luận có giá trị rõ ràng. Danh sách từ cấm là phép kiểm bổ sung sau khi đã kiểm tra nội dung.

Bộ chuyển tiếp 2D có luồng dựng và kiểm tra phiếu bàn giao. Tra cứu mã vận hành chưa xác lập việc mọi lệnh đóng ca qua `sync_bus.py` đều đi qua cổng sản phẩm. Đường dẫn mặc định của bộ chuyển tiếp ghép `workspace_root/memory/DUAL_AGENT_BUS.json`. Tệp đã quan sát nằm dưới `.agents/memory/`. Cần thống nhất cách phân giải đường dẫn và thử từ đầu đến cuối qua đúng lệnh người dùng sử dụng trước khi bật rộng.

Căn cứ đối chiếu gồm [cổng sản phẩm và bộ lọc](<G:/My Drive/Google AI Studio/.agents/skills/Global_Dispatcher/product_deliverable_gate.py:152>), [bộ chuyển tiếp 2D](<G:/My Drive/Google AI Studio/.agents/skills/Global_Dispatcher/sync_bus_2d_patch.py:52>) và [lệnh vận hành](<G:/My Drive/Google AI Studio/.agents/tools/sync_bus.py:1395>).

## 3. Đánh giá Hợp đồng P2 MCP Perception Loop

**Kết luận chuyên đề — Đạt kiểm tra giao diện cục bộ. Chưa đủ bằng chứng nghiệm thu vận hành hai phía.**

Máy chủ có 13 công cụ đăng ký, gồm tạo và bố trí tờ, xem ảnh, kiểm tra, sửa, thao tác biểu mẫu và chuyển DWG. Bảng tại §1 của hợp đồng liệt kê 12 tên, thiếu `convert_to_dwg`. Bốn ca MCP chọn lọc chạy lại đạt 4/4 trong 6,229 giây. Ca vòng xem ảnh dùng dữ liệu thử, có `physical=PASS` và `full=NEEDS_REVIEW`. Kết quả này kiểm chứng cách gọi và vòng đời ảnh tạm. Nó chưa chứng minh đạt 20 cổng trên mô hình thật hoặc đồng nhất giữa hai máy khách.

Nhóm công cụ đủ cho một vòng kiểm soát mặt bằng kết cấu có đầu vào tương thích. Trước khi mở sang CAD dự án cảng, cần định rõ nghiệp vụ đối soát tọa độ VN-2000, mặt chuẩn cao độ, danh mục hố và khớp dữ liệu giữa bản vẽ với bảng tính. DWG, tệp tham chiếu ngoài, phông SHX, tỷ lệ in và trao đổi với bản gốc cũng cần tiêu chí kiểm tra riêng. Các tuyên bố về khảo sát chuyên ngành cần được đánh giá theo cấu hình dự án.

Biên nhận `RCP_20261120-105415_CLAUDE_NEED_REVIEW` có `action_type=META` và dẫn tới `P2_RESULT.md` của Claude. Bốn mục bằng chứng có mã băm trong biên nhận là ảnh mang tên Cát Lái. Báo cáo Claude ghi phạm vi chốt hợp đồng và chuyển phần triển khai cho Gemini. Tệp `cad_v6/gemini/G2_RESULT.md` hiện mô tả bộ dữ liệu thử adapter thép của ca khác. Bộ bằng chứng đã xem chưa có chuỗi PNG cuối, kết quả full và báo cáo cùng phiên bản DXF để nghiệm thu P2.

`consume_preview` đọc ảnh rồi dọn tệp tạm. Vì vậy, bước lưu ảnh bằng chứng phải hoàn tất trước khi dọn, hoặc từ dữ liệu ảnh trả về trong chính lượt gọi cuối. `visual_gate_check` mặc định kiểm tên bằng chứng. Nhánh kiểm đĩa có thể xác minh tệp và mã băm, nhưng không phân biệt đủ ba loại đầu ra P2 và không đọc kết quả 20 cổng. Cần bắt buộc cùng một phép kiểm trong mọi đường đóng ca CAD. Biên nhận phải liên kết DXF, PNG, JSON kiểm tra và báo cáo theo cùng mã ca, lần sửa và cấu hình. Chỉ báo đạt P2 khi kết quả full thực sự đạt và có dấu vết người kiểm tra đã xem ảnh chốt.

Thử đọc và băm mẫu hồ sơ cỡ KB đến 3,84 MB trên ổ G: ghi nhận khoảng 16–37 ms mỗi tệp trong lượt kiểm tra. Đây là phép đo đọc cộng băm tại thời điểm kiểm định. Độ trễ đồng bộ Drive, dựng hình và chờ khóa chưa đo. Nên giữ SHA-256 tại lần chốt và lần nhận, đo riêng từng bước, đóng băng tệp trước khi tính băm và tránh băm mọi ảnh tạm. Thử lại khi Drive chưa đồng bộ hoặc tệp đang mở để kiểm chứng cách khôi phục.

Căn cứ đối chiếu gồm [hợp đồng P2](<G:/My Drive/Google AI Studio/.agents/docs/SPEC_P2_MCP_PERCEPTION_LOOP.md>), [công cụ CAD](<G:/My Drive/Google AI Studio/.agents/tools/mcp_dce_cad_server.py:206>), [cổng bằng chứng](<G:/My Drive/Google AI Studio/.agents/tools/sync_bus.py:518>), [kết quả Claude P2](<G:/My Drive/Google AI Studio/.agents/memory/audits/skill_dual_agent_bridge/claude/P2_RESULT.md>) và [kết quả Gemini G2 đã đối chiếu](<G:/My Drive/Google AI Studio/.agents/memory/audits/cad_v6/gemini/G2_RESULT.md>).

## 4. Đánh giá Hồ sơ Dự án Cảng Liên Chiểu Đà Nẵng

**Kết luận chuyên đề — Không đạt định danh và tính nhất quán. Kiến nghị giữ bộ hồ sơ ở trạng thái chưa phát hành cho Chủ đầu tư.**

### 4.1. Định danh và đối soát số liệu

Phần 5 khai báo Bến cảng Liên Chiểu, phần cơ sở hạ tầng dùng chung. Bảng tọa độ, thuyết minh và mã nguồn kiểm tra ghi nhà cao tầng “Nhà Bạn Thân”, 18 tầng và 2 tầng hầm, thửa đất 128, tờ bản đồ 121, Hòa Minh 1. Tài liệu đầu vào tại thư mục dự án cũng có đề nghị liên quan khu đất tư nhân và tài liệu quy hoạch Hòa Khánh. Chưa tìm thấy đầu vào xác thực cho hạng mục cảng trong thư mục đã đối chiếu. Số hố, chiều sâu và tọa độ của nhà cao tầng không có giá trị xác nhận cho phạm vi khảo sát cảng.

| Nhóm tệp | Kiểm chứng trực tiếp | Kết luận |
| --- | --- | --- |
| A, 21 hố và 8 hố | Trùng SHA-256 theo từng cặp ở 6 tệp XLSX, DXF, PNG, PDF bản vẽ, DOCX thuyết minh và PDF thuyết minh | Chỉ xác nhận được nội dung bộ 8 hố trong các tệp mang tên 21 hố |
| B, 7 hố và 4 hố | Trùng SHA-256 theo từng cặp ở 3 tệp DXF, PNG và PDF | DXF hiện thể hiện 4 hố đợt 1 và 4 hố đợt 2 |
| Tờ trình ngày 18/11 | Tiêu đề phương án A ghi 21 hố, đoạn diễn giải ghi 8 hố và 340,0 m, đầu bảng ghi 6 hố | Mâu thuẫn trực tiếp trong văn bản |
| Phương án B trong cùng tờ trình | Đoạn mô tả ghi 7 hố và 290,0 m, đầu bảng ghi 4 hố | Chưa xác lập phương án ký duyệt |
| Cự ly TKCS | Thuyết minh và XLSX đặt dải 29–66 m cạnh dải viện dẫn 50–200 m rồi ghi “đạt” | Khoảng dưới 50 m cần giải trình theo đúng phạm vi và điều khoản áp dụng |

Mã băm rút gọn để tra soát gồm XLSX A `f3152f526f1c`, DXF A `9ada0832a2dd`, DOCX thuyết minh A `21b88f0324b1` và DXF B `cc236ab436f3`. Kiến nghị đối chiếu dữ liệu thủ công với hồ sơ gốc có phê duyệt trước khi xác lập phương án. Việc chốt số hố, chiều sâu, cự ly, khối lượng khoan và thí nghiệm cần dựa vào hạng mục, địa tầng, giai đoạn thiết kế và khả năng tái sử dụng số liệu đã khảo sát.

### 4.2. Script và kiểm tra trình bày theo Điều 12b, 12d, 12e

Ba script nêu ở Phần 5 được tìm thấy tại `03_Agent_Workspace/scripts/`. Script thuyết minh 6 hố và script tờ trình `build_perfect_totrinh_lienchieu.py` có nội dung nhà cao tầng 8 tầng và 1–2 tầng hầm. Script thuyết minh 8 hố ghi 18 tầng và 2 tầng hầm. Script `generate_cad_plan_4_boreholes_option_b.py` dùng Matplotlib để ghi PNG/PDF. Script `generate_cad_dxf_8_boreholes.py` đọc bản mẫu và ghi DXF trực tiếp bằng ezdxf. Các đường xuất cần có bản kê liên kết với đúng nguồn, phương án và tệp giao cuối.

Điều 12b đạt một phần ở mẫu kiểm tra. XML nội dung hai DOCX không có màu chữ trắng gán trực tiếp. Các bảng có nền `#DCE4EC`, `#EAE6DF`, `#F8F7F4` hoặc trắng. Kiểm tra các ô có dữ liệu trong XLSX thấy màu chữ tối và tiêu đề nền `#DCE4EC`. Quét lớp chữ trích xuất của các PDF mẫu không phát hiện chữ trắng. Phạm vi phép kiểm này giới hạn ở màu gán trực tiếp và lớp chữ đọc được. Cần kiểm tiếp kiểu kế thừa, chú thích trong ảnh và bản in đen trắng. Điều 12e chưa đạt trên tờ trình. XML có 114 lượt định dạng 8,5 pt và 18 lượt 9 pt, dưới sàn 10 pt cho bảng và chú thích.

Hai DXF đại diện mở được, định dạng AC1021, đơn vị mm và 0 lỗi cấu trúc khi kiểm tra bằng ezdxf. Cả hai có đồ họa trong Model và hai bố cục giấy rỗng. Không có thực thể DIMENSION trong các bố cục đã đọc. Có nét trên lớp `DCE_Dim` và khung trên lớp `DCE_Frame`. Những dấu hiệu này chưa xác nhận bố cục in, tỷ lệ hay chuỗi kích thước 4 tầng. Điều 12d quy định dầm, cột, vách và trục cho mặt bằng kết cấu. Với mặt bằng hố khoan, các mục cấu kiện không áp dụng. Các mục cần đánh giá theo loại bản vẽ gồm khung, tỷ lệ, độ rõ ký hiệu, mốc tọa độ và đối chiếu danh mục hố. Chưa có kết quả kiểm tra trên bản đóng băng qua luồng `DcePlanEngine(v6=True)` và xem ảnh qua MCP.

### 4.3. Căn cứ pháp lý và chuyên ngành

| Căn cứ | Điều hoặc mục, trang đối chiếu | Kết quả kiểm định |
| --- | --- | --- |
| TCVN 9363:2012 | Phạm vi áp dụng trên danh mục VSQI. Điều 5.2.4.2 và Phụ lục D là viện dẫn của hồ sơ, chưa xác nhận số trang bản gốc | Phù hợp về đối tượng nhà cao tầng. Chưa đủ căn cứ dùng định mức khoảng cách và tỷ lệ hố của tiêu chuẩn này cho các hạng mục cảng. [VSQI](https://tieuchuan.vsqi.gov.vn/tieuchuan/view?sohieu=TCVN+9363%3A2012) |
| TCVN 4419:1987 | Điều 3.5, Điều 3.19 và Phụ lục 2 theo bảng khóa tiêu chuẩn nội bộ. Chưa đối chiếu số trang | Dùng xem xét nguyên tắc chung, phải xác định tiêu chuẩn khảo sát chuyên ngành tương ứng cho công trình đặc thù. [VSQI](https://tieuchuan.vsqi.gov.vn/tieuchuan/view?sohieu=TCVN+4419%3A1987) |
| Thông tư 34/2026/TT-BXD | Điều 2, trang PDF 1–2. Phụ lục I mục 1.4.5, trang PDF 27–28. Bảng 2 Phụ lục II mục 2.11, trang PDF 36 | Phân cấp từng hạng mục theo loại, công suất hoặc quy mô kết cấu. Cần tải trọng tàu thiết kế, chiều cao hoặc diện tích mặt bến và dữ liệu tương ứng đối với luồng, đê hoặc kè. Chưa thể chốt cấp Đặc biệt hay cấp I. [Bản chính thức](https://datafiles.chinhphu.vn/cpp/files/vbpq/2026/7/34-bxd.pdf) |
| QCVN 03:2022/BXD | Mục 2.1, Phụ lục A theo bảng khóa tiêu chuẩn, chưa đối chiếu số trang | Xác định cấp hậu quả phục vụ thiết kế theo phạm vi quy chuẩn. Cấp hậu quả C1–C3 và cấp quản lý theo Thông tư 34/2026 được xác định theo các tiêu chí riêng. [Thông tư ban hành quy chuẩn](https://vanban.chinhphu.vn/?classid=1&docid=207058&pageid=27160&typegroupid=6) |
| Nghị định 217/2026/NĐ-CP | Điều 10–12 về khảo sát, từ trang PDF 10 của bản ban hành. Điều 75–76 về hiệu lực và chuyển tiếp, từ trang PDF 76 | Có hiệu lực từ 01/07/2026. Khoản 2 Điều 75 quy định hết hiệu lực Nghị định 175/2024/NĐ-CP. Phải đối chiếu điều khoản chuyển tiếp với mốc thẩm định và phê duyệt thực tế. Kiểm tra bản hợp nhất 91/2026/VBHN-NĐ-BXD khi lập lại danh mục pháp lý. [Công báo](https://congbao.chinhphu.vn/van-ban/nghi-dinh-so-217-2026-nd-cp-469819.htm) · [Bộ Xây dựng](https://moc.gov.vn/vn/Pages/ChiTietVanBan.aspx?TypeVB=2&vID=5074) |
| Nghị định 30/2020/NĐ-CP | Điều 8–9 và Phụ lục I, phần thể thức và kỹ thuật trình bày. Chưa xác nhận số trang bản ký quét | Kiểm tra đối tượng áp dụng và mẫu tờ trình được duyệt. Mẫu có trang A4 nhưng lề lưu trong DOCX chỉ khoảng trên/dưới 10 mm, trái 12 mm, phải 8 mm. Nếu trình theo Nghị định 30, đối chiếu lại yêu cầu lề và toàn bộ thể thức. [Bản ký](https://datafiles.chinhphu.vn/cpp/files/vbpq/2020/03/30.signed.pdf) |

Đề nghị chủ trì địa kỹ thuật rà danh mục áp dụng cho bến, đê, kè, luồng và nền tôn tạo theo hạng mục được giao. Danh mục VSQI xác nhận TCVN 11820-1:2026 về nguyên tắc chung và TCVN 11820-4-1:2020 về nền móng có phạm vi công trình cảng biển. Hai mục này được nêu để Chủ đầu tư xem xét đưa vào danh mục áp dụng. Chưa có kết luận điều khoản cụ thể về số hố hoặc phạm vi thăm dò. [TCVN 11820-1:2026](https://tieuchuan.vsqi.gov.vn/tieuchuan/view?sohieu=TCVN+11820-1%3A2026) · [TCVN 11820-4-1:2020](https://tieuchuan.vsqi.gov.vn/tieuchuan/view?sohieu=TCVN+11820-4-1%3A2020).

**UNVERIFIED — Dữ liệu còn thiếu.** Mã dự án và hạng mục cảng được duyệt, nhiệm vụ khảo sát và giai đoạn áp dụng, mặt bằng/cao độ chuẩn, dữ liệu địa chất hoặc địa vật lý gốc, phương án nền móng dự kiến, thông số tàu/bến/luồng, hồ sơ chuyển tiếp pháp lý và thẩm quyền ký. Khi có dữ liệu này, lập bảng đối chiếu theo từng mã hố giữa tọa độ, cao độ, chiều sâu, chỉ tiêu thí nghiệm, khối lượng và vị trí trên bản vẽ.

## 5. Bảng Tổng hợp Rủi ro & Kiến nghị Hành động (Risk & Action Matrix)

| Mã | Mức | Phát hiện | Chủ trì kiến nghị | Điều kiện đóng |
| --- | --- | --- | --- | --- |
| LC-01 | Nghiêm trọng | Hồ sơ tự nhận là cảng nhưng nguồn và tệp thực tế ghi nhà cao tầng | Chủ đầu tư / QLTK | Xác nhận mã, phạm vi cảng và bộ nguồn phê duyệt. Danh mục giao phải có 0 tệp sai định danh |
| LC-02 | Nghiêm trọng | 9 cặp tệp trùng từng byte qua hai phương án. Tờ trình mâu thuẫn 21/8/6 và 7/4 | Chủ trì ĐCCT | Chốt một phiên bản cho từng giai đoạn. Đối chiếu 100% mã hố, tọa độ, chiều sâu và khối lượng |
| SYS-01 | Cao | Tham chiếu đường dẫn đổi tuyến. Hai điểm vào trả khác hợp đồng | Chủ trì hệ thống | Một điểm vào vận hành. Bộ kiểm thử bao gồm câu trích dẫn cờ, tham chiếu tệp, nội dung đính kèm và dự án đa rễ |
| SYS-02 | Cao | Cổng nhận một tệp bất kỳ trong tập định dạng. Bộ lọc có thể đạt khi thiếu 3 ý | Chủ trì hệ thống / chủ trì thẩm tra | Theo đúng lệnh đóng ca, xác nhận đủ tệp đọc được, đúng dự án, đúng phương án và đủ 3 trường báo cáo |
| CAD-01 | Cao | Biên nhận META có ảnh ngoài ca. Bằng chứng P2 chưa đủ theo cùng bản DXF | Gemini, Claude kiểm chứng | Một ca thật đã khóa nguồn, đủ DXF, PNG, JSON full và báo cáo. Hai phía kiểm lại cùng mã băm |
| LC-03 | Cao | Chưa chốt cấp công trình, bộ căn cứ và thời điểm chuyển tiếp | Chủ trì cảng / pháp chế | Hồ sơ có căn cứ theo hạng mục, điều khoản phân cấp, văn bản chuyển tiếp và người phê duyệt |
| LC-04 | Trung bình | Chữ Word dưới 10 pt, bố cục giấy DXF rỗng, chưa kiểm in | QLTK / CAD | Kiểm tra Word/PDF và sơ đồ in theo đúng mẫu, tỷ lệ, chú thích, màu và bố cục được duyệt |

## 6. Kết luận Nghiệm thu & Lộ trình Đề xuất

**FAIL đối với nghiệm thu tổng thể ngày 20/11/2026.** Đã chạy lại 12/12 ca bộ phân luồng, 16/16 ca tích hợp CAD và 4/4 ca MCP chọn lọc. Tuyên bố 46/46 suites, 24/24 chế độ nhanh, 64/64 tích hợp, 39/39 của ca META và 0 xung đột là số liệu do hồ sơ hoặc biên bản ca trước báo cáo. Chưa tái lập toàn bộ tại cùng một phiên bản. Chế độ nhanh của runner khai báo 24 nhóm thử. Khi tái nghiệm thu, cần ghim bản mã, lưu danh mục từng nhóm thử và gắn kết quả với tệp đầu ra. Các kết quả kiểm thử hiện có không xử lý được 9 cặp trùng nội dung và sai định danh dự án.

**Ưu tiên 48 giờ — Lựa chọn A.** Hoàn thành một vòng P2 trên ca CAD có nguồn hợp lệ, đã khóa phiên bản và xác định rõ cấu hình kiểm tra. Song song, QLTK xác thực lại bộ nguồn Cảng Liên Chiểu. Tạm giữ bước giao hồ sơ Cảng Liên Chiểu trong lựa chọn B cho đến khi có dữ liệu cảng và đóng LC-01, LC-02, LC-03. Chu trình P2 đạt sẽ xác nhận năng lực vận hành CAD. Việc phê duyệt mạng lưới khảo sát cần kiểm tra chuyên môn trên nguồn dự án riêng.

| Mốc từ khi giao khắc phục | Công việc đề xuất | Bằng chứng chấp nhận |
| --- | --- | --- |
| 0–8 giờ | QLTK khoanh bộ tài liệu nhầm, xác nhận mã dự án và đầu mối hồ sơ cảng. Hai bên thống nhất bảng 13 công cụ và tiêu chí P2 | Danh mục tệp trùng, nguồn dự án được xác nhận, lệnh thử và cấu hình CAD thống nhất |
| 8–24 giờ | Gemini hoàn thành vòng tạo, xem, sửa và kiểm tra. Claude đọc lại tệp và đối chiếu kết quả độc lập | Một DXF chốt, PNG đọc được, JSON đạt cấu hình full đủ 20 cổng và báo cáo P1 cùng phiên bản |
| 24–48 giờ | Kiểm thử điểm vào và cổng đóng ca. Chủ trì ĐCCT đối chiếu nhiệm vụ khảo sát với dữ liệu cảng đã nhận | Mở B khi dữ liệu dự án đủ và sai lệch giữa thuyết minh, XLSX, CAD đã được xử lý. Nếu thiếu nguồn, lập danh mục chờ xác nhận và giữ trạng thái chưa phát hành |

**Trách nhiệm**

| Công việc | Đề xuất | Kiểm tra, phê duyệt |
| --- | --- | --- |
| Tiếp nhận kết luận và giao khắc phục | Trợ lý AI — cần kỹ sư có chứng chỉ hành nghề kiểm tra xác nhận trước khi ký | Tổng Công Trình Sư |
| Xác nhận hồ sơ khảo sát cảng | Trợ lý AI — cần kỹ sư có chứng chỉ hành nghề kiểm tra xác nhận trước khi ký | Chủ trì địa kỹ thuật, QLTK và Chủ đầu tư theo thẩm quyền |
| Nghiệm thu vận hành P2 | Trợ lý AI — cần kỹ sư có chứng chỉ hành nghề kiểm tra xác nhận trước khi ký | Chủ trì hệ thống và người kiểm tra CAD độc lập |

*Tài liệu do trợ lý AI lập tự động. Kết quả tính toán mang tính tham khảo, phải được kỹ sư có chứng chỉ hành nghề phù hợp kiểm tra và chịu trách nhiệm trước khi sử dụng cho hồ sơ thiết kế, thi công hoặc thẩm tra.*
