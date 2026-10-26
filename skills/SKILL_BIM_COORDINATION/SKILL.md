---
name: SKILL_BIM_COORDINATION
version: 1.3.0
updated: 2026-10-25
status: PRODUCTION_READY
description: >
  Hệ thống Kiểm soát Xung đột Hình học, Lưới trục, Cao độ thông thủy và Đối chiếu Nội bộ Bản vẽ
  (Kiến trúc ↔ Mặt bằng Kết cấu ↔ Mặt cắt ↔ Chi tiết cấu kiện).
---

# SKILL_BIM_COORDINATION — ĐỐI SOÁT HÌNH HỌC, KHÔNG GIAN & XUNG ĐỘT BẢN VẼ (v1.3.0)

## 1. QUY TRÌNH RÀ SOÁT XUNG ĐỘT 3 LỚP HÌNH HỌC (3-TIER GEOMETRIC & DRAWING CLASH AUDIT)

### Lớp 1: Đối soát Hệ Lưới Trục & Định Vị Tổng Mặt Bằng (Grid & Site Boundary Coordination)
1. **Đồng bộ số lượng trục và bước cột (`Grid Axis Consistency`):**
   - Trích xuất danh sách trục dọc ($X_1 \dots X_n$) và trục ngang ($Y_1 \dots Y_m$) trên:
     (a) Bản vẽ Tổng mặt bằng (`TMB`), (b) Bản vẽ Kiến trúc (`KT`), (c) Bản vẽ Mặt bằng móng/khung (`KC-01`), (d) Bản vẽ Chi tiết móng (`KC-02, KC-03`), và (e) Sơ đồ gán tải trong Thuyết minh (`TMKC`).
   - Phát hiện tức thì các lỗi:
     + **Lệch hệ trục khung:** Ví dụ Kiến trúc dùng 7 trục `Y1–Y7` (bước $7.75\text{ m}$) nhưng Thuyết minh dùng 3 trục `Y1–Y3` (nhịp $23.25\text{ m}$).
     + **Lỗi ký hiệu trục trên bản vẽ chi tiết (Copy-Paste Ghost Axes):** Ví dụ Mặt bằng `KC-01` chỉ có trục `X1–X11` và cột giữa tại `Y4`, nhưng tờ Chi tiết móng `KC-02` ghi móng giữa tại trục `Y2` và `KC-03` ghi móng tại trục `X1–X14` (dư 3 trục ma `X12–X14`).
2. **Kiểm tra xung đột ranh đất và hạ tầng kỹ thuật ngoài nhà:**
   - Kiểm tra phần đài móng biên/cổ cột nhô ra ngoài trục biên ($e_{\text{out}} = B_{\text{móng}}/2 + e_0$) có xâm phạm vào mương thoát nước mưa, đường nội bộ hoặc ranh giới lô đất hay không.

### Lớp 2: Đối soát Nội bộ Bản vẽ Kết cấu (Mặt bằng ↔ Mặt cắt ↔ Chi tiết ↔ Tag thép)
1. **Kiểm tra tính nhất quán hình học giữa Mặt bằng và Mặt cắt:**
   - **Độ lệch tâm móng:** Nếu Mặt bằng móng vẽ cổ cột lệch tâm ($a_1 \ne a_2$, ví dụ $1230\text{ mm}$ và $770\text{ mm}$ trên móng $2000\text{ mm}$), nhưng Mặt cắt `1-1` ngay phía trên lại vẽ cổ cột chính giữa móng đối xứng $\rightarrow$ Báo lỗi `CRITICAL` (vẽ sai mặt cắt và tính thiếu mô men lệch tâm).
   - **Kích thước cổ cột và cấu kiện:** Đối chiếu kích thước ghi trên Mặt bằng/Mặt cắt cổ cột (`500x350` vs `500x300` trong TMKC; hoặc `200x450` trên bản vẽ Nhà xe vs `250x200` trong TMKC).
2. **Kiểm tra xung đột số lượng cấu kiện và ký hiệu tên cấu kiện:**
   - Đếm số lượng cấu kiện vẽ trên Mặt bằng/Mặt cắt dọc và so sánh với con số ghi trong tiêu đề Chi tiết (ví dụ: Mặt bằng bể PCCC vẽ **5 cột cấy `CC` và 5 dầm `DS1`**, nhưng tiêu đề chi tiết ghi **`(3 CỘT)` và `(3 DẦM)`**).
   - Kiểm tra tên cấu kiện trên Mặt bằng đà kiềng/dầm so với tên Mặt cắt chi tiết (ví dụ: Mặt bằng ghi `DK1A`, chi tiết ghi `DK1`).
3. **Kiểm tra xung đột Tag thép giữa Mặt bằng và Mặt cắt trên cùng 1 tờ bản vẽ:**
   - So sánh tag thép rải sàn/vách trên Mặt bằng với tag chỉ dẫn trên Mặt cắt (ví dụ: Mặt bằng thép sàn mái Nhà bảo vệ ghi `Ø10a200`, nhưng Mặt cắt `1-1` ngay bên dưới ghi `Ø10a150`; hoặc chi tiết bản mã chân cột `KC-09` ghi `4M24` trên mặt bằng nhưng vẽ cả `BL neo D.20x750` lẫn `D.24x850` ở góc bản vẽ).

### Lớp 3: Kiểm tra Tĩnh không Thông thủy & Xung đột Cơ điện - PCCC (3D Spatial Clearance)
1. **Xung đột cao độ hệ giàn treo trần / sàn thao tác với luồng xe nâng và Sprinkler:**
   - Tính cao độ đáy thấp nhất của hệ giàn treo và thanh giằng xiên (ví dụ: giàn treo ở cốt $+6.000\text{ m}$ nhưng có thanh chống xiên `V50x50x3` tụt xuống cốt $+5.300\text{ m}$), kiểm tra va chạm với tuyến ống chữa cháy tự động Sprinkler, máng cáp điện và chiều cao nâng hàng của xe nâng công nghiệp.
2. **Đối chiếu tiết diện cấu kiện bao che giữa Kiến trúc và Kết cấu:**
   - Kiểm tra các ghi chú kết cấu trên bản vẽ Mặt cắt Kiến trúc so với bản vẽ Kết cấu (ví dụ: Kiến trúc Nhà bơm `KT-02` ghi `Xà gồ hộp 60x120x1.5`, nhưng Kết cấu `KC-02` vẽ `[]-30x60x1.4`).


## 2. QUY CHUẨN TRÍCH XUẤT VÙNG KHOANH ĐỎ BẢN VẼ CAD (CLEAN REDLINE CROPPING STANDARD v1.3.0)
1. **Cắt sát vùng cấu kiện (Tight CAD Bounding-Box Crop):** Loại bỏ toàn bộ khoảng trắng thừa bên trái/bên phải khung bản vẽ; đối với ảnh ghép 2 khung đối chứng (ví dụ: Mặt bằng vs Mặt cắt, hoặc Bản vẽ Kiến trúc vs Bản vẽ Kết cấu), đặt 2 khung cạnh nhau với khoảng cách chuẩn `18px` trên nền Xanh Băng `#F0F4F8`, viền ngoài `#1B365D` dày `2px`.
2. **Cấm vẽ trùng lặp Banner & Hộp chữ trong ảnh PNG (`Zero Box-in-Box`):** Không vẽ thanh tiêu đề đen ở đỉnh ảnh và không vẽ hộp thoại 4 dòng ở đáy ảnh PNG; toàn bộ thuyết minh 6 mục do bảng Word bên dưới đảm nhận.
3. **Thanh tiêu đề khung bản vẽ chuẩn Serif tiếng Việt:** Trên đỉnh mỗi khung cắt bản vẽ, vẽ thanh tiêu đề cao `34px` nền Xanh Navy `#1B365D`, chữ trắng dùng phông Serif đầy đủ dấu tiếng Việt (`LiberationSerif-Bold` / `NotoSerif-Bold`), căn giữa và tự động co cỡ chữ (`fit_subheader_font`) để không bao giờ tràn khỏi khung.
