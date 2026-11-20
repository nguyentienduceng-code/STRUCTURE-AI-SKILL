# Biên bản kiểm toán độc lập Sprint 2 — 2026-11-14

Người thực hiện: CODEX — Chief Systems Architect & Verification Lead.

**Kết luận:** Hoàn tất kiểm toán, sửa lỗi, stress-test và kiểm tra hồi quy. Đạt yêu cầu hiệu năng dưới 2 giây trên hai mẫu đã đo; I/O MCP được cô lập local. **Chưa nghiệm thu khả năng tự động làm sạch mọi nhãn trên bản vẽ dày đặc.** Các bản kết quả còn va chạm trả `NEEDS_REVIEW`; không được diễn giải thành hồ sơ sẵn sàng phát hành.

## 1. Phạm vi và dữ liệu thử

Sinh hai DXF bằng `skills/Technical_Illustrator/cad_integration/cad_plan_engine.py`, dùng `build_structural_model()` của engine. Đây là hình học mẫu tháp 40 tầng, 57 × 28 m, có cột/vách, lõi, dầm, kích thước, thống kê và khung tên. Không phải dữ liệu nội lực đã kiểm chứng của một dự án thực tế; không mô phỏng 40 tầng độc lập.

Tên tờ theo yêu cầu người dùng được ánh xạ như sau:

| Tờ trong audit | Hàm engine | Mã tờ bên trong template |
|---|---|---|
| KC-01 Cột Vách | `render_sheet_kc02()` | KC-02 |
| KC-02 Dầm Sàn | `render_sheet_kc03()` | KC-03 |

Không đổi quy ước đánh số của engine. Không chạy AutoCAD/Revit, DLL/LISP/XLL thương mại hoặc installer. Không ghi vào `C:/Dce Pro` hoặc Starter Kit.

## 2. Phát hiện và sửa lỗi

| Phát hiện | Biện pháp |
|---|---|
| Nhãn được dời nhưng còn trong ô spatial grid cũ | Xóa khỏi các ô cũ trước khi đổi bbox, rồi chèn vào các ô mới |
| Chọn vị trí vẫn va chạm khi hết ứng viên | Chỉ nhận ứng viên không có penalty va chạm; giữ nguyên và báo review nếu không có vị trí |
| Dry-run thay đổi scene trong RAM, làm lần gọi sau khác kết quả | Khôi phục bbox, anchor và grid sau lập kế hoạch; kiểm tra dry-run lặp lại |
| MTEXT không xét rotation, paragraph/format; TEXT bỏ qua alignment; INSERT dùng hộp giả định | Dùng `ezdxf.bbox.extents(fast=True)` cho layout, phép biến đổi Block lồng nhau và ATTRIB; thêm margin 50 drawing units |
| Đổi INSERT bằng insert point không dịch ATTRIB; TEXT căn giữa có thể không dịch đúng | Dùng phép `translate()` của entity |
| Block nhãn dầm `Dce_KhTenDam` bị coi là Block tĩnh | Allowlist chính xác nhãn cột và nhãn dầm trên layer được phép |
| Chữ khung tên đặt cùng layer nhãn kết cấu | Cố định nội dung trong vùng khung tên của template |
| Bbox toàn khung A1 cấm mọi vị trí bên trong khung | Chỉ mục cạnh của hai khung lớn; giữ khung tên nhỏ là vùng cấm; giới hạn ứng viên trong khung trong |
| Tool MCP có thể ghi đè DXF nguồn hoặc ghi ra cloud | Luôn cấp DXF kết quả UUID trong scratch local; output yêu cầu chỉ là gợi ý. API solver từ chối output cloud và ghi đè nguồn trước khi áp thay đổi |
| Thất bại áp dụng bị in lỗi nhưng vẫn trả OK | Thu thập `apply_errors`; lỗi hoặc va chạm còn lại chuyển trạng thái review |
| Không xác minh scene sau commit | Dựng lại index từ document đã sửa; audit còn đọc lại DXF độc lập để kiểm tra |
| Leader bắt đầu trong vùng chữ | Bắt đầu trên biên bbox nhãn mới, kết thúc tại vị trí annotation cũ; kiểm tra giao đoạn thẳng với bbox annotation khác |
| Cache font có thể theo XDG_CACHE_HOME ngoài scratch | `configure_runtime()` ghi đè biến này bằng đường dẫn đã qua `require_local()` |

Layer bị khóa và entity có XData `DCE_USER_OVERRIDE` được giữ cố định. Đây là cơ chế khóa opt-in; bridge tự nhận diện mọi chỉnh sửa tay của kỹ sư chưa nằm trong phạm vi triển khai.

## 3. Kết quả định lượng

| To | Entity | Nhan di chuyen duoc | Va cham dau/cuoi | Nhann da doi | Max wall (3 lan) |
|---|---:|---:|---:|---:|---:|
| KC-01 | 430 | 27 | 34 / 8 | 22 | 0.7750 s |
| KC-02 | 491 | 59 | 177 / 142 | 13 | 0.8519 s |

Mỗi tờ đo 3 lần qua hàm MCP `resolve_cad_collisions`. Wall-clock bắt đầu trước gọi tool và kết thúc khi tool trả kết quả: gồm nạp module solver, đọc DXF, index, tìm vị trí, dịch entity, tạo leader, lưu DXF và reindex kiểm tra. Không gồm khởi động Python/MCP, sinh bản vẽ, hay kiểm toán độc lập sau phép đo. Không chạy test suites đồng thời với lần benchmark cuối.

Ngưỡng < 2 giây được đánh giá trên từng lần gọi, không lấy trung bình để che lần chậm. Không suy rộng kết quả sang bản vẽ khác hoặc hàng chục nghìn entity. Số va chạm là cặp bbox theo hướng truy vấn; có thể có hai chiều giữa hai nhãn, không phải số nhãn độc lập.

## 4. Bảo toàn và an toàn I/O

Script benchmark xác nhận ở cả 3 lần mỗi tờ:

- SHA256 DXF nguồn giữ nguyên.
- Toàn bộ entity modelspace không được phép di chuyển giữ nguyên DXF tags, gồm DIM, khung tên, thống kê và hình học kết cấu.
- DXF kết quả đọc được và `doc.audit()` không có lỗi.
- Số va chạm khi đọc lại DXF bằng index mới khớp số tool báo.
- Không nhãn đã dịch nào còn giao vùng `DCE_Frame`/`DCE_Schedule` theo kiểm tra AABB.
- Không leader mới nào cắt bbox annotation khác theo bộ kiểm tra hiện tại.
- `require_local()` xác nhận đường dẫn output; yêu cầu output G: được điều hướng vào C:.

`runtime_paths.json` ghi TEMP/TMP, Matplotlib cache, XDG cache và trạng thái tắt bytecode. Spatial grid/bbox chỉ ở RAM, không có cache không gian trên Drive. Benchmark chủ động đặt `XDG_CACHE_HOME` về G: trước khi gọi `configure_runtime()`, sau đó kiểm tra biến đã trở về local. Đây là kiểm tra đường dẫn và hành vi tại entrypoint MCP, không phải giám sát mọi syscall hoặc sandbox hệ điều hành.

## 5. Kiểm thử hồi quy

Full runner: **30/30 suites PASS**, 99.13 s. After the font-cache guard change, Suites 18/28/29/30 all PASS again (23.22 s).

Suite 30 tăng từ 6 lên **18 test**: nested Block scale/rotate; tiếng Việt decomposed Unicode; TEXT căn giữa góc 137°; MTEXT xoay/paragraph/format; dry-run lặp; vùng kín không có nghiệm; locked layer/XData override; chuyển ô grid; ATTRIB đi cùng INSERT; từ chối cloud/ghi đè nguồn; cố định khung tên; nhãn dầm chéo; giao cắt leader dùng đoạn thẳng thay vì bbox của đoạn.

Suite 29 có **7 test**, gồm tool thứ 8, điều hướng output cloud về local và SHA256 nguồn giữ nguyên. Test MCP cũ luôn yêu cầu OK trên bản vẽ thật đã được sửa thành kiểm tra trạng thái theo residual/error, số va chạm không tăng và output tồn tại; không bỏ kiểm tra để che va chạm.

Lần full đầu tiên thất bại ở kỳ vọng trạng thái cũ. Log được giữ tại `full_tests/`. Lần full sau PASS ở `final_full_tests/`. Nhãn suite được runner nạp lúc khởi động còn ghi 16 test cho Suite 30; log con xác nhận thực chạy 18 test. Registry hiện đã cập nhật 18.

## 6. Giới hạn và quyết định nghiệm thu

**PASS:** kiểm toán độc lập; hồi quy; hiệu năng trên mẫu; bounded search tối đa 56 ứng viên/nhãn; bảo toàn entity cố định; I/O MCP local; báo cáo trung thực khi không có nghiệm.

**Chưa đạt để tự động phát hành bản vẽ:** vẫn còn các cặp va chạm trong benchmark. Cần review các residual trong `benchmark.json`. Chúng có thể gồm xung đột thật hoặc false-positive do AABB của cấu kiện xiên/Dimension bao cả khoảng trống. Không được tự loại bỏ tất cả residual như false-positive.

Công việc tiếp theo cần ưu tiên:

1. Narrow-phase theo hình học đoạn/đa giác của dầm xiên, DIM và chữ xoay; không dùng một bbox lớn cho mọi vùng trống bên trong.
2. Thêm ứng viên theo local axes cấu kiện và bố trí nhiều nhãn phối hợp; bán kính hiện tối đa 1600 drawing units có thể không đủ chỗ.
3. Leader routing nhiều đoạn, clearance và tránh hình học kết cấu. Kiểm tra hiện tại chỉ phát hiện giao với annotation; không bảo đảm mọi leader tránh dầm/cột hoặc nối đúng feature kết cấu. Đầu cuối hiện là vị trí annotation cũ.
4. Chuẩn hóa đơn vị: hai mẫu có INSUNITS=4 (mm). Tool xuất `units_verified_mm`; các ngưỡng 50/300/1600 không được áp như mm khi drawing dùng đơn vị khác.
5. Kiểm tra bằng host/render khi font SHX/fallback, glyph tiếng Việt hoặc Block phức tạp làm bbox khác AutoCAD. Bbox text của ezdxf là xấp xỉ; không chứng nhận pixel-perfect. [Giới hạn chính thức ezdxf bbox](https://ezdxf.readthedocs.io/en/stable/bbox.html).

Nhận diện khung hiện dựa trên layer DCE_Frame và kích thước template A1 đang dùng; chưa là bộ suy luận mọi khung tên tùy ý. Không kiểm toán ACAD_TABLE, XREF, ACIS hay cyclic Block; DIM được giữ cố định, chưa tự bố trí lại các tầng DIM. DXF được lưu lại bằng ezdxf, không cam kết toàn tệp byte-identical hoặc round-trip mọi đối tượng CAD không hỗ trợ.

**Trạng thái bàn giao:** hoàn tất nhiệm vụ kiểm toán; giữ `NEEDS_REVIEW` cho hai bản vẽ. Việc đóng ca IPC không phải chấp thuận phát hành bản vẽ hoặc nghiệm thu toàn bộ năng lực chống va chạm.

## 7. Bằng chứng và tái lập

- `benchmark.json`: từng lần gọi, kế hoạch, residual, hash nguồn và đường dẫn DXF local.
- `runtime_paths.json`: đường dẫn runtime/cache đã kiểm tra.
- `benchmark_reproduce.py`: script tái lập trên máy này từ thư mục `.agents`.
- `final_full_tests/`: full log 30 suites và timings.
- `final_cache_checks/`: kiểm tra lại các suites bị ảnh hưởng sau bổ sung cache guard.
- `source_hashes.json`: hash các tệp triển khai/kiểm thử cuối ca.

Lệnh hồi quy: `python tests/run_all_tests.py --report-dir memory/audits/sprint2_collision_solver_20261114/final_full_tests`.

Không sửa các thư mục nguồn thương mại trong nhiệm vụ này. Mọi DXF thử nghiệm được sinh trong scratch local và được giữ lại để xem xét.
