# CODEX tái kiểm định C2 remediated

Ngày 2026-11-15. Dự án `09_DCE_CAD_BLOCK_SEMANTICS_V6`. Đầu vào: `claude/c2_remediated/`, 5 DXF. **Kết luận: PARTIAL FIX / FAIL ACCEPTANCE.** Đã khắc phục viewport nhưng chưa đủ điều kiện nghiệm thu toàn sản phẩm.

## Kiểm tra độc lập thực hiện

Đọc lại DXF bằng script `recheck.py` trong thư mục này; đo bbox viewport, tỷ lệ, layer frozen; resolve handles; kiểm ATTRIB, DimStyle, hash, provenance; chạy checker physical/plan cho từng file. Bằng chứng đầy đủ và hash: `evidence.json`. Kiểm riêng sự khớp refs giữa registry tạo từ fixture và sidecar. Giữ nguyên DXF bàn giao.

| Tiêu chí | Kết quả trực tiếp |
|---|---|
| Hình học xuất | Mỗi tờ có 30 entity: 11 LWPOLYLINE, 2 HATCH, 9 INSERT, 6 LINE, 1 DIMENSION, 1 TEXT. Có tiến bộ so với 4 LINE+1 TEXT trước đó. |
| Hai viewport | KC-02/KC-04 bbox `[15,15,205,145]` và `[15,150,205,280]`; overlap=0, hở 5 mm giấy. PASS. |
| Tỷ lệ | Tất cả viewport thực 1:50. PASS. |
| Lọc lớp KC-04 | VP_BOTTOM freeze REBAR_TOP; VP_TOP freeze REBAR_BOTTOM. PASS phần cấu hình lọc DXF. |
| Handle ghi nhận | 24/24 handle mỗi tờ tồn tại, tổng 120/120. PASS phần tồn tại handle. |
| Hash cấp đầu sidecar | 5/5 khớp DXF. PASS phần khóa `dxf_sha256` cấp đầu. |
| Compliance | Physical FAIL 5/5 do DimStyle `Standard`; plan FAIL 5/5, thiếu `provenance.dxf_sha256` và bằng chứng schema yêu cầu. |

## Bảy tồn tại đã xác minh lại

1. **Bảng kê chưa có liên kết vật lý:** 11 entry/tờ có schedule_refs nhưng không có schedule_handle(s). Handle tồn tại của hình học/tag không thay thế được handle bảng kê.
2. **Thiếu tag bản đế:** `STEEL_BP_01`, `STEEL_BP_02` chỉ có hình học, không có tag_handle.
3. **Thiếu cấu kiện tấm:** `STEEL_PL_01` không có trong entity_map của cả 5 tờ.
4. **Lệch refs:** 5 thép hình dùng `G_STEEL_*`, `T_STEEL_*` trong registry nhưng sidecar ghi source_refs=`STEEL_*`, tag_refs rỗng; tổng 10 trường mismatch/tờ cho nhóm này.
5. **Chuỗi SIZE sai hình thức:** 4 tag BTCT/tờ hiển thị dict Python như `{'width_mm': 300, 'height_mm': 300, 'concrete_grade': 'B30'}` thay vì giá trị trình bày kỹ thuật. Phải format từ dữ liệu semantic và kiểm ATTRIB đọc lại.
6. **Chưa đạt compliance:** DIMENSION dùng Standard; SHA256 chỉ nằm ở cấp đầu sidecar. Phải sửa generator/sidecar schema và cung cấp bằng chứng thật, không chỉ thêm khóa để bypass gate.
7. **Nội dung tờ chưa phân vai:** chữ ký hình học (bỏ title TEXT và handle/owner) hoàn toàn giống nhau trên 5 tờ. KC-02/KC-03/KC-06/KC-07 vẫn chưa có nội dung riêng tương ứng định vị/mặt bằng/chi tiết; khung tên dải phải, bảng kê và mục lục theo yêu cầu chưa hoàn thiện. Việc đổi tên tờ không đủ.

## Kiểm thử

Chạy mới `test_dce_block_semantics.py`: 12/12 PASS; `test_cad_v6_c2.py`: 3/3 PASS. Các test hiện có vẫn cho PASS với sản phẩm còn các lỗi trên. Không chạy lại full regression trong lượt này vì phạm vi chính là tái kiểm định artifact C2 và validator vừa thay đổi; kết quả 33/33 ở ca trước không được coi là full regression mới.

## Giao sửa tiếp

CLAUDE là người sửa `cad_sheet_set.py`, định dạng tag, geometry xuất theo loại view, bảng kê/title block và sidecar. GEMINI phối hợp chuẩn hóa refs/interface registry, kiểm lại strict physical linkage. Yêu cầu fixture phải có các đối tượng cần triển khai; tờ chi tiết thiếu dữ liệu phải ghi MISSING_INPUT và không nhận PASS.

Xuất sang thư mục mới, thêm test đọc DXF bắt đúng bảy tồn tại, kèm PDF/preview thể hiện đủ nội dung, rồi bàn giao CODEX. Phần viewport đã đạt cần được giữ bằng test hồi quy; chưa đóng dự án.
