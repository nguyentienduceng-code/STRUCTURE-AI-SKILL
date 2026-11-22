# Đề xuất kiến trúc Tầng 2B/2C sau kiểm toán 2A

**Mã ca:** `TIER2_PHASE2A_REVIEW_AND_2B_DESIGN_20261122`  
**Phạm vi:** Kiến trúc đề xuất; chưa triển khai tích hợp native DWG/Revit trong ca này.  
**Nguyên tắc:** giữ nguyên Tầng 1 và API hợp đồng JSON; mọi phép ghép/diff xác định, mọi thay đổi mô hình đều cần người có thẩm quyền duyệt.

## 1. Kết luận kiểm toán Tầng 2A

- Diff của 8 tệp khớp với memo: mở 5 profile MCP và `full_evidence`; chấp nhận offset cột có dấu; thêm XData `DCE_ELEMENT_ID`; sửa fallback đơn vị/tính chiều dài dầm/deduplicate `bim_id`; map family Revit theo loại và truyền `Element_ID`/`SSOT_UUID`; bỏ `pipeline` 1D khi `/sys`; bổ sung suite nền.
- Suite riêng `test_tier2_phase2a_foundation.py`: **6/6 PASS**.
- `audit_zero_white_text.py`: **0 warnings**.
- Điểm cần bảo toàn cho 2B: `bim_model_translator._dedupe_bim_id()` hậu tố hóa khóa trùng (`#2`), điều này ngăn va chạm khóa đầu ra nhưng không xác định cấu kiện nào là owner đúng. Không dùng hậu tố làm căn cứ tự ghép; duplicate `PRIMARY_GEOM` phải vào trạng thái conflict để người dùng phân xử.
- XData hiện tuần tự hóa `ID=...;ROLE=...;FLOOR=...` trong một chuỗi. Nên giới hạn/escape `;` và ký tự điều khiển trong định danh hoặc chuyển sang định dạng field có version, để dữ liệu nhập không làm vỡ parser. Phải kiểm tra owner duplicate xuyên ModelSpace, paper space và block/xref theo phạm vi nghiệp vụ đã chốt.
- `full_evidence=True` tạo sidecar bằng chứng, nhưng chưa thay thế cổng nghiệm thu AutoCAD native: DXF PASS không chứng minh DWG mở/regen/plot đúng trong AutoCAD 2021.
- Các điểm trên là yêu cầu thiết kế/kiểm chứng tiếp theo, không phải lỗi test đã tái hiện trong 2A.

## 2. Giải pháp tối ưu Tầng 2B — AutoCAD 2021 Native DWG + Snapshot Diff

### Kiến trúc khuyến nghị

Giữ `dce-cad`/`ezdxf` làm bộ lập kế hoạch, sinh DXF, compliance check và diff thuần dữ liệu. Thêm adapter native DWG riêng, chạy **AutoCAD 2021 Core Console (`accoreconsole.exe`) + plugin .NET Framework 4.8 nhỏ, ký/phiên bản hóa**, làm cổng đọc/ghi DWG thực. Core Console chỉ được gọi qua worker có hàng đợi một DWG/một tiến trình; không để MCP gọi trực tiếp các lệnh tùy ý.

Luồng D1/D1A:

1. Đóng băng D1 nguồn: SHA-256, kích thước, bản AutoCAD, units, Xref paths + hashes; tuyệt đối không sửa file nguồn.
2. Tạo working copy trong thư mục staging cục bộ (không chạy trực tiếp trên Google Drive). Mở/regen bằng Core Console; adapter xuất snapshot JSON chuẩn hóa và log đầy đủ. D1A được sinh vào một output mới.
3. Chụp D1A theo cùng schema: drawing metadata, layers/layouts, entities cần theo dõi, handles hiện thời, block transforms/attributes, XData, extents, Xref lineage, và giá trị đã chuẩn hóa về mm.
4. Diff theo `element_id + role + floor_id + drawing_id/revision`; mark chỉ là thuộc tính hiển thị, không làm khóa. Không tự ghép theo mark hoặc tọa độ khi ID thiếu; xuất `CANDIDATE_MATCH` để người dùng duyệt.
5. Phân loại `ADDED`, `REMOVED`, `GEOMETRY_CHANGED`, `PROPERTY_CHANGED`, `TAG_MOVED/RELINKED`, `DUPLICATE_PRIMARY_OWNER`, `UNMATCHED`, `UNVERIFIED`. Ghi giá trị cũ/mới, đơn vị, tolerance, handles hai bên, nguồn/tờ, hash và lý do quyết định.
6. Sinh báo cáo diff/ảnh/PDF chứng minh; kỹ sư duyệt trước khi có bước áp thay đổi vào DWG. Giai đoạn đầu **read-only**; chỉ bật ghi khi có giao dịch staging, preview thay đổi, backup, xác thực revision/hash trước ghi, và reopen/re-audit sau ghi.

### Xử lý định danh và sai số

- `DCE_ELEMENT_ID` là ID nghiệp vụ bền; handle là tham chiếu vật lý theo revision, không phải ID bền.
- Mỗi ID cho phép nhiều entity vai trò `PRIMARY_GEOM`, `ANNOTATION_TAG`, `DETAIL_VIEW`, `SCHEDULE_ROW`; trong cùng phạm vi bản vẽ/tầng chỉ được có một owner primary. COPY/WBLOCK giữ nguyên ID phải bị phát hiện; không tự đổi ID hay chọn owner.
- Snapshot giữ cả raw value và normalized value; mm là đơn vị chuẩn cho hình học. Tolerances phải cấu hình theo nhóm phép đo, version hóa và hiện ở report, không hardcode dùng chung cho tọa độ, góc, kích thước và khối lượng.
- Handle đổi không đồng nghĩa cấu kiện đổi; ghi lại liên kết handle cũ/mới sau khi ghép bằng ID đã xác nhận.
- Block lồng nhau phải lưu transform tích lũy WCS và đường dẫn block; Xref cần định danh file/transform/hash riêng. Nếu không phân giải được transform hoặc Xref, gắn `UNVERIFIED`, không so như hình học cùng hệ tọa độ.

### Cổng phát hành và an toàn vận hành

- Mỗi lượt chạy idempotent theo source hash + plugin version + config hash; cùng input phải cho cùng snapshot nghiệp vụ sau loại bỏ timestamp/handle volatile.
- Worker khóa theo đường dẫn chuẩn hóa, timeout và hủy an toàn; lưu stdout/stderr, exit code, crash dump nếu có. Không mở hai tiến trình AutoCAD đồng thời trên cùng DWG.
- Kiểm tra `accoreconsole.exe`/plugin đúng bản 2021 trước khi chạy; nếu thiếu hoặc lệnh không hỗ trợ, trả `UNAVAILABLE`, không fallback âm thầm sang DXF rồi báo native pass.
- Acceptance native gồm mở/recover/regen DWG, XData sau save-close-reopen, COPY/WBLOCK, block lồng, Xref, Unicode/attribute, plotting bằng PC3/CTB thật, kích thước PDF và đối chiếu snapshot. DXF checker và AutoCAD-native checker là hai kết quả tách biệt.
- Giữ file nguồn bất biến; staging, output và evidence tách biệt; chỉ promote bản đã duyệt. Google Drive sync không được dùng như cơ chế khóa tiến trình.

### Vai trò 2B

- **Gemini (maker):** triển khai adapter Core Console/.NET trong nhánh riêng, fixture DWG tối thiểu, snapshot schema v1 và worker an toàn.
- **Claude (review/verification):** duyệt contract/schema, ma trận lỗi và tính bất biến; lập bộ ca đối kháng ID/COPY/WBLOCK/Xref/plot; xác minh hash nguồn không đổi và kết quả cùng revision.
- **Kỹ sư CAD phụ trách:** cung cấp DWG thật đã ẩn dữ liệu nhạy cảm, CTB/PC3, tolerance được duyệt, đáp án D1/D1A; duyệt mọi promotion đầu ra.

## 3. Giải pháp tối ưu Tầng 2C — Revit 2024 Read-Only + IFC

### Lộ trình ít rủi ro

Bắt đầu bằng pilot 10 ngày trên **bản sao RVT 2024**, thử một connector tại một thời điểm: BIMwright `rvt-mcp` v1.2.2 làm ứng viên đầu; nếu thiếu snapshot/lô đọc cần thiết, benchmark Horizun v4.0.1 trên đúng cùng model và bộ đáp án. Không dùng bridge có quyền ghi cho pilot. Nếu bridge cộng đồng không đạt, thay bằng add-in C# Revit 2024 read-only chỉ xuất snapshot; không mở rộng sang ghi Revit.

Định nghĩa interface độc lập nhà cung cấp: `open_document_readonly`, `list_elements(scope,categories)`, `get_elements_batch(ids)`, `get_types_batch(type_ids)`, `document_fingerprint`, `close_document`. Snapshot phải ghi document identity, Revit build, connector/tag, view/scope, category filter, unit schema, shared/project coordinate transforms, link identity/transform, model revision/fingerprint, expected/returned/error counts, pagination/batch details và completion flag.

### Canonical BIM snapshot và ghép dữ liệu

- Chuẩn hóa về cấu kiện vật lý với `element_id`, `floor_id`, category, `UniqueId`, `TypeUniqueId`, family/type, mark, raw parameter + storage/spec/type-vs-instance/source, geometry endpoints/solid summary, coordinates gốc và tọa độ chuẩn hóa mm, link/document identity.
- Chỉ `element_id` đã được ánh xạ/duyệt mới là khóa xuyên CAD–Revit. `UniqueId` nhận dạng phần tử trong tài liệu Revit; `IfcGlobalId` nhận dạng trong IFC; không giả định hai khóa này tương đương hay bền qua exporter/recreate.
- Đọc kích thước từ parameter có GUID ổn định/shared parameter hoặc BuiltInParameter đã xác định. Lưu nguồn Type/Instance; phát hiện type dùng chung và liệt kê toàn bộ instance bị ảnh hưởng. Không suy đoán b/h từ tên family.
- Dùng đường cong LocationCurve/XYZ cho dầm; đối chiếu hai đầu không phụ thuộc thứ tự, xét ΔZ. Cột cần footprint/rotation, base/top level, offsets và tiết diện; tường/sàn cần biên/lỗ mở khi phạm vi kiểm tra yêu cầu. Mọi phép biến đổi link phải rõ ràng; thiếu transform thì không ghép tự động.
- Snapshot thất bại giữa lô, model đổi trong lúc đọc, document sai hoặc thiếu trường bắt buộc phải mang trạng thái incomplete/blocked; không đưa vào pass report.

### IFC là kênh trao đổi độc lập

- Chỉ nhận IFC đã xuất thật; parser nội bộ hiện có nhánh demo/fallback nên phải chặn tuyệt đối demo payload khỏi pipeline nghiệm thu.
- Ghi hash IFC, schema, exporter, timestamp, unit assignments, project/site/building placement và mapping GlobalId. Cài IfcOpenShell vào môi trường cô lập/version-pinned trước khi bật production.
- Dùng IfcDiff/IfcOpenShell làm phép đối chiếu IFC↔IFC phụ trợ; không tự coi GlobalId ổn định giữa lần xuất. Đo độ ổn định bằng cùng model xuất hai lần và revision có sửa, phân biệt element modified với delete+create.
- Revit bridge snapshot là nguồn đối chiếu trực tiếp cho pilot; IFC là round-trip/openBIM cross-check và fallback khi không có quyền/bridge Revit, không thay thế tự động cho RVT-native parameters.

### Acceptance test 2C

1. Đếm 100% Structural Framing/Columns trong scope so với schedule đã duyệt; giải thích mọi thiếu/thừa.
2. Chạy cùng snapshot 2 lần không đổi revision: kết quả normalized identic, không thiếu lô.
3. D1/D1A: hai dầm cùng mark D1, chỉ B–C đổi 250×500→250×600 và mark D1A; phát hiện đúng B–C, không báo đổi giả cho A–B; thử type dùng chung, tag sai, dầm chéo 3–4–5, đảo đầu, cao độ Z, cột xoay/offset, linked model.
4. Cố tình ngắt bridge giữa các lô, mở sai document, thiếu parameter, thay đổi model giữa snapshot, IFC demo/GlobalId đổi; mọi ca phải block hoặc unresolved, không PASS giả.
5. Chứng minh read-only bằng danh sách tool/capability hiệu lực, quyền chỉ đọc trên bản sao, hash trước-sau và audit/log; pilot không mở file sản xuất để tránh nâng cấp RVT ngoài dự kiến.
6. Chủ trì chấm 100% lỗi cài; báo cáo sai dương, ghép mơ hồ, trường thiếu, thời gian đọc, thời gian kỹ sư xử lý và công tích hợp. Chỉ mở rộng khi hiệu quả đo được tốt hơn cách hiện tại.

### Vai trò 2C

- **Gemini:** đóng gói pilot connector 2024 (một bridge), snapshot adapter và fixture/export test; ghi rõ phiên bản/nguồn và quyền thực tế.
- **Claude:** review threat model read-only, canonical schema, transform/unit provenance, diff oracle và các ca lỗi; độc lập chấm snapshot trên cùng đáp án.
- **BIM lead/kỹ sư Revit:** cung cấp bản sao RVT, schedule làm oracle, family thật, shared parameter GUID, scope/tolerance và xác nhận điều kiện cấp phép/plugin.
- **Điều kiện rẽ nhánh:** BIMwright đạt đủ dữ liệu và độ lặp lại thì tiếp tục; thiếu batch/snapshot thì thử Horizun cùng ca; cả hai thiếu trường thiết yếu thì mới duyệt dự toán add-in C# riêng. IFC chỉ làm cross-check sau khi có IfcOpenShell pinned và IFC thực.

## 4. Trình tự ưu tiên

1. Chốt canonical element identity và XData versioning/escape + duplicate-owner policy trước khi native snapshot.
2. 2B read-only native DWG snapshot trên một bản vẽ, rồi D1/D1A diff; nghiệm thu plot và COPY/WBLOCK trước khi phát triển ghi.
3. 2C pilot Revit 2024 với hai category/ một tầng và oracle schedule; connector độc lập khỏi thuật toán diff.
4. Chỉ sau khi hai adapter tạo cùng canonical snapshot mới mở rộng phạm vi, IFC và tự động hóa; không gộp 2B/2C thành một plugin phụ thuộc chéo.

**Khuyến nghị quyết định:** phê duyệt thiết kế và pilot read-only theo giai đoạn; chưa phê duyệt ghi DWG/RVT tự động hoặc chọn vendor sản xuất cho đến khi acceptance trên file thật đạt và kỹ sư độc lập ký kết quả.
