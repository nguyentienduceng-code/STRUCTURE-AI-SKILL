# Nghiệm thu Sprint 2 — bản hoàn thiện ngày 2026-11-14

**Thư mục bằng chứng v2:** `G:/My Drive/Google AI Studio/.agents/memory/audits/sprint2_collision_completion_20261114/`. Mọi tên tệp tương đối trong biên bản này được tính từ thư mục đó. Số liệu cũ trong thư mục `sprint2_collision_solver_20261114` chỉ là lịch sử kiểm toán.

**Kết quả: PASS trong phạm vi hai mặt bằng tháp 40 tầng, 57 × 28 m được sinh bằng engine của dự án.** Hai DXF sau xử lý có **0 va chạm nhãn, 0 xung đột leader**, được kiểm tra lại sau khi mở file. Chạy lại không phát sinh thêm dịch chuyển hoặc leader. Full regression **30/30 suites PASS**, Suite 30 gồm **30 test PASS**.

Biên bản này thay kết luận NEEDS_REVIEW của vòng kiểm toán trước cho bộ mẫu trên. Bản trước được giữ riêng dưới tên `ACCEPTANCE_v1.md` trong thư mục kiểm toán ban đầu. Kế hoạch thực hiện tại `PLAN.md` đã hoàn thành cả tám bước.

## Kết quả đo cuối cùng

| To | Entity | Nhan | Va cham truoc/sau | Leader conflicts | Max wall (3 lan) |
|---|---:|---:|---:|---:|---:|
| KC-01 | 430 | 27 | 80 / 0 | 0 | 0.8498 s |
| KC-02 | 491 | 59 | 132 / 0 | 0 | 0.9322 s |

Mỗi tờ đo ba lần qua `resolve_cad_collisions` của MCP; mọi lần đều < 2 giây và trả `OK`. Đo từ trước lời gọi tool tới khi nhận kết quả: gồm nạp module solver, đọc DXF, index, giải nhãn, lập và kiểm tra đường leader, áp dụng và lưu DXF. Không gồm khởi động Python/MCP, sinh fixture, render PNG hoặc đọc lại độc lập. Không chạy hồi quy/render đồng thời với benchmark này.

Full regression cuối: **30/30 suites PASS trong 103,58 giây**. Log từng suite và timing tại `final_full_tests/`. Bộ `full_tests/` là checkpoint trước khi sửa màu/Attribute; không dùng checkpoint đó để chứng nhận phiên bản cuối.

Tên KC-01/KC-02 trong bảng theo yêu cầu nghiệm thu. Hàm engine tương ứng là `render_sheet_kc02()` cho Cột Vách và `render_sheet_kc03()` cho Dầm Sàn; mã tờ bên trong template vẫn lần lượt KC-02/KC-03. Fixture là hình học tầng điển hình của mẫu tháp 40 tầng, không phải 40 bản sao tầng hoặc dữ liệu nội lực của công trình đã thẩm tra.

## Các lỗi đã đóng

1. **Đường bao sàn bị hiểu thành vùng đặc:** engine đánh dấu chính entity bao sàn bằng RegApp `DCE_SCENE`, giá trị `boundary_only`. Vòng va chạm xét nét biên thay vì cấm toàn diện tích sàn. Polygon cột/vách không có vai trò này tiếp tục là vùng đặc. Không dùng ngưỡng diện tích để tự bỏ qua cấu kiện lớn.
2. **Va chạm giả do bbox:** spatial grid chỉ lọc sơ bộ. Giao cắt được quyết định bằng primitives/polygon có hướng, tách DIM và nested Block; khoảng trống giữa các nét không bị gộp thành vật cản đặc. Text vẫn dùng envelope theo font/layout của ezdxf với margin.
3. **Tìm kiếm vị trí:** tìm tám hướng theo các bán kính có giới hạn tới 7500 mm. Nếu vị trí đầu tiên không dẫn được leader an toàn, thử lại vị trí nhãn trong scene cuối. Không thu nhỏ chữ, đổi nội dung hoặc dịch cấu kiện.
4. **Leader:** thử đường trực tiếp và dogleg có giới hạn. Tránh annotation, vùng đặc và leader khác; không đi xuyên chính nhãn chủ. Đường trục và đường bao sàn là nét tham chiếu có thể cắt; chữ và mũi tên DIM vẫn được bảo vệ. Tiếp xúc tại đầu nối với biên cấu kiện được cho phép, đi xuyên vùng đặc bị từ chối.
5. **Kiểm tra leader sau lưu:** các đoạn có RegApp `DCE_COLLISION`, handle nhãn chủ, handle nguồn và cờ đoạn cuối. Bộ kiểm tra đọc lại metadata, phát hiện cả leader bị sửa để cắt qua cấu kiện. Tiếp xúc có chủ đích tại envelope nhãn chủ được phân biệt với đi xuyên chữ.
6. **Đơn vị:** INSUNITS bắt buộc được khai báo; bán kính, margin và ngưỡng leader chuẩn hóa từ mm sang drawing units. Test tương đương mét/mm PASS. Đơn vị chưa khai báo bị từ chối.
7. **Chỉnh sửa kỹ sư và dry-run:** layer khóa hoặc XData `DCE_USER_OVERRIDE` được giữ nguyên; xung đột của nhãn khóa trả NEEDS_REVIEW. Dry-run khôi phục chính xác bbox, anchor và geometry gốc, kể cả chữ xoay có tọa độ lẻ. Khi không tìm được leader bắt buộc, không áp dụng một phần kế hoạch.
8. **Nhãn trắng/Attribute chồng dòng:** kiểm tra ảnh phát hiện ATTRIB TENDAM màu ACI 255 từ seed và hai dòng bị đặt cùng tọa độ. Engine nay sinh tên/tiết diện và tỷ lệ trên các dòng riêng, chữ thẳng đứng, màu tối `#1E3246`. Solver giữ nguyên nội dung và style của DXF đầu vào; sửa màu nằm ở nguồn sinh fixture.
9. **Preview crop:** đặt aspect bằng chế độ `adjustable="box"` để không làm thay đổi giới hạn vùng kiểm tra. PNG trước/sau đã render lại và kiểm tra trực quan, tên dầm đọc được và không chồng dòng.

## Bằng chứng bảo toàn và I/O

`benchmark_reproduce.py` đo hiệu năng và kiểm tra từng kết quả. `verify_outputs.py` mở lại độc lập cả sáu DXF của ba lần chạy mỗi tờ. `verification.json` ghi hash của từng output và các kết quả sau:

- SHA256 nguồn không thay đổi; DXF kết quả qua `doc.audit()` không có lỗi.
- Toàn bộ entity modelspace cố định giữ nguyên DXF tags: 403 entity trên tờ Cột Vách và 432 entity trên tờ Dầm Sàn, gồm DIM, hình học, khung tên và bảng thống kê.
- Với nhãn được dịch, mọi tag ngoài tọa độ dịch được đối chiếu; nội dung, style, màu, chiều cao, góc xoay, tỉ lệ Block, Attribute và metadata giữ nguyên.
- Không nhãn đã dịch nào giao vùng khung tên/thống kê; kiểm tra nhãn và kiểm tra leader đều bằng 0.
- Chạy lại output bằng dry-run trả DRY_RUN_OK, 0 kế hoạch dịch chuyển và không có leader mới.
- Output MCP dùng UUID trong scratch C:, không ghi đè nguồn. Tham số output G: được coi là gợi ý và điều hướng local.
- TEMP/TMP, Matplotlib cache, XDG font cache và trạng thái tắt bytecode được ghi trong `runtime_paths.json`. Benchmark cố tình đặt XDG_CACHE_HOME về G: trước configure_runtime rồi xác nhận nó đã được chuyển về local bằng Virtual Drive Guard.

Spatial index ở RAM. Các PNG preview được tạo local, sao chép thành bằng chứng báo cáo rồi dọn preview qua lifecycle API. Các DXF local được giữ để người dùng xem xét; đường dẫn và SHA256 nằm trong benchmark/verification. Không sửa `C:/Dce Pro` hoặc Starter Kit, không chạy binary/installer thương mại.

## Hồi quy và phụ thuộc

Suite 30 có 30 test, bao gồm Unicode tiếng Việt decomposed, TEXT xoay/căn giữa, MTEXT định dạng/xoay, nested Block, ATTRIB dịch đồng bộ, scene grid, bảo vệ nguồn/cloud, đơn vị, semantic đường bao sàn, phần rỗng của DIM, nét chéo, nhãn khóa, leader lưu/đọc lại, leader hỏng, dry-run chính xác, hai bản vẽ lớn sạch và màu/bố trí nội bộ Attribute.

Đã dùng Python 3.12, ezdxf 1.4.4 và Shapely 2.1.2 có sẵn trên máy. Phụ thuộc khai báo trong `tools/requirements-cad-collision.txt`; phiên này không cài thêm package. Hình học dùng [ezdxf disassemble](https://ezdxf.readthedocs.io/en/stable/disassemble.html) và [Shapely](https://shapely.readthedocs.io/en/stable/manual.html).

## Phạm vi nghiệm thu

Các kiểm tra trên xác nhận bộ máy xử lý và hai bản vẽ thử nghiệm đã hoàn thành tiêu chí Sprint 2. Chúng không khẳng định mọi bản vẽ tùy ý đều có nghiệm dưới hai giây. Trường hợp không có vị trí/đường dẫn hợp lệ tiếp tục trả NEEDS_REVIEW; dữ liệu đơn vị thiếu bị từ chối.

Khi chưa có mapping cấu kiện semantic, đầu nối leader được ghi là suy luận biên cấu kiện gần nhãn hoặc vùng annotation cũ, không được gọi là liên kết mô hình kết cấu đã xác minh. Bbox chữ/font SHX/MTEXT phức tạp vẫn chịu giới hạn headless của ezdxf. Native Dynamic Block, XREF/ACIS, bảng CAD chuyên dụng và kiểm tra bằng AutoCAD thật nằm ngoài bộ chứng cứ này. DIM và nội dung engineering được bảo toàn; thuật toán không sửa giá trị kích thước để che va chạm.

## Tệp bàn giao

- `PLAN.md`: tám bước thực hiện.
- `benchmark.json`, `runtime_paths.json`: số liệu thô và đường dẫn runtime.
- `benchmark_reproduce.py`: tái lập sinh mẫu và đo qua MCP.
- `verify_outputs.py`, `verification.json`: sáu lần kiểm tra DXF độc lập.
- `KC-01_before.png`, `KC-01_after.png`, `KC-02_before.png`, `KC-02_after.png`: vùng kiểm tra trước/sau.
- `final_full_tests/`: log 30 suites cuối cùng.
- `source_hashes.json`: hash mã nguồn/kiểm thử nghiệm thu.

Lệnh tái lập từ `.agents`:

```powershell
python -B memory/audits/sprint2_collision_completion_20261114/benchmark_reproduce.py
python -B memory/audits/sprint2_collision_completion_20261114/verify_outputs.py
python -B tests/run_all_tests.py --report-dir memory/audits/sprint2_collision_completion_20261114/final_full_tests
```
