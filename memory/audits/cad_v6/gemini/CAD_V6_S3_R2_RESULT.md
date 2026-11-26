# BÁO CÁO BÀN GIAO SPRINT 3 R2 — KHẮC PHỤC THẨM TRA CLAUDE (`CAD_V6_S3_R2_RESULT`)

## 1. Tóm tắt ca
- Khắc phục triệt để **2 phát hiện thẩm tra của Claude** trên bản Sprint 3 R1 mà **không ghi đè bất kỳ `.dwg` cũ nào**, đóng gói mới sang `04_Deliverables_ToTrinh/Sprint3_Xref_Workbook_R2/`:
  1. **Loại bỏ hình học cầu thang giả định trong `02_XREF_ARCH_BG.dwg`:** Xóa bỏ khối chữ nhật `(6700..10200, 2400..4800)` chưa có căn cứ kiến trúc; chỉ giữ ranh sàn `(0..18000, 0..5000)`, tường vây hầm `200 mm` và hố thang máy `ĐM.TM` `(14450..16000)` / lỗ mở `(14650..15800)` đã xác minh từ PDF kết cấu, kèm nhãn chờ nền Kiến trúc duyệt.
  2. **Loại bỏ toàn bộ tên/chức danh tự điền trên `03_XREF_TITLEBLOCK_A3.dwg` và `cad_rc_detail_engine.py`:** Chuyển về chuỗi rỗng `""` cho `CHU_DAU_TU`, `CONG_TY`, `GIAM_DOC`, `KIEM_TRA`, `THIET_KE`, `THE_HIEN`, giữ duy nhất thông tin đã xác minh trên PDF (`NHÀ Ở RIÊNG LẺ`, `THỬA 1039 TỜ BẢN ĐỒ 20`, `PHƯỜNG CÁT LÁI, TP.HCM`, `BẢN VẼ KẾT CẤU`, `TKTC`, `2026`).
  3. **Chỉnh trung thực trạng thái phát hành:** `SheetSet_Manifest.json` đặt `artifact_lifecycle_state="NATIVE_GENERATED"`, `engineering_release_status="HOLD_PENDING_ARCH_BG_AND_TITLEBLOCK_SIGNATORIES"`, tách rõ `technical_cad_audit="PASS"` khỏi `missing_approvals`. Đồng bộ `work_ticket["task_title"]` trong `sync_bus.py`.

## 2. Sản phẩm & Đường dẫn thật
- Mã nguồn cập nhật:
  - `g:\My Drive\Google AI Studio\.agents\skills\Technical_Illustrator\cad_integration\cad_xref_workbook_builder.py`
  - `g:\My Drive\Google AI Studio\.agents\skills\Technical_Illustrator\cad_integration\cad_rc_detail_engine.py`
  - `g:\My Drive\Google AI Studio\.agents\tools\sync_bus.py`
  - `g:\My Drive\Google AI Studio\01_Projects\03_Sprint2_KetQua_NeChu_CAD\build_catlai_sprint3_xref_workbook.py`
  - `g:\My Drive\Google AI Studio\.agents\tests\test_cad_sprint3_xref_workbook.py`
- Gói giao nộp R2 `04_Deliverables_ToTrinh\Sprint3_Xref_Workbook_R2\`:
  - `01_Xref\01_XREF_GRID.dwg` (`43.2 KB`, `sha=0edd9d78148d`), `02_XREF_ARCH_BG.dwg` (`39.9 KB`, `sha=685b2e7bba51`), `03_XREF_TITLEBLOCK_A3.dwg` (`41.4 KB`, `sha=9f4b4c972098`).
  - `02_Workbook\01_KC-02_MatBangKetCauNgam.dwg` .. `08_KC-09_ChiTietCotVach_2.dwg` (`8/8` tờ, `86.1–111.4 KB`, mọi tờ `xrefs=3`, `audit_err=0`).
  - `SheetSet_Manifest.json` (`SPRINT3_XREF_WORKBOOK_V1_R2`) & `BAO_CAO_THUC_CHIEN_KETC_CAU_CATLAI_KC02_KC09.md`.

## 3. Kết quả Kiểm định & Test
- `accoreconsole_adapter.py --audit-only` trên 4 tệp R2 (`02_XREF_ARCH_BG`, `03_XREF_TITLEBLOCK_A3`, `01_KC-02`, `08_KC-09`): `OK`, `0 errors / 0 fixes`, `xref_count=3` trên các Workbook.
- Chạy đầy đủ **7 bộ unit test (`31/31 OK`)** + `audit_zero_white_text.py` (`0 WARNINGS`) sau chỉnh sửa cuối cùng.

## 4. Sai sót / Lưu ý mở
- Trạng thái pháp lý/kỹ thuật của gói là `HOLD_PENDING_ARCH_BG_AND_TITLEBLOCK_SIGNATORIES` (chờ Chủ đầu tư/Chủ trì Kiến trúc cung cấp nền Kiến trúc DWG và thông tin người ký duyệt để chuyển lên `ENGINEER_APPROVED`). `native_dst=False`.

## 5. Phạm vi đề nghị Claude xác nhận đóng ca Sprint 3 R2
1. Chạy `python .agents/tools/accoreconsole_adapter.py --audit-only` trên các tệp trong `Sprint3_Xref_Workbook_R2/` và kiểm tra `SheetSet_Manifest.json` đã tách `NATIVE_GENERATED` / `HOLD_PENDING_ARCH_BG_AND_TITLEBLOCK_SIGNATORIES`.
2. Xác nhận `test_cad_sprint3_xref_workbook.py` + `audit_zero_white_text.py` PASS và đóng ca `--complete` nếu đạt.
