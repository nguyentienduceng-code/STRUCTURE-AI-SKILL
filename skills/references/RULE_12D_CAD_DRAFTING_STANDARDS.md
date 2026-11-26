## 12d. Quy chuẩn Đồ họa Bản vẽ Kỹ thuật CAD DCE Pro (CAD Drafting & Visual Quality Standards)

> **Cơ sở kỹ thuật**: Chuẩn bản vẽ thi công xây dựng Việt Nam và quốc tế, kế thừa hệ thống Drawing Template DCE Pro (`DCE_Master_Seed_Template.dxf` / `Dam_200x400_DCE.dxf` AC1021). Nguồn thực thi: `cad_plan_engine.py` và Bộ lọc 8 `dce_cad_compliance_checker.py`.

Mọi bản vẽ mặt bằng kết cấu (Mặt bằng định vị cột vách, Mặt bằng kết cấu dầm sàn) xuất ra tệp CAD (`.dxf` / `.dwg`) BẮT BUỘC tuân thủ 5 điều cấm và quy cách đồ họa sau:

1. **Khóa phân đoạn dầm (No Continuous Beam Line Lock)**:
   - Nghiêm cấm vẽ dầm chạy thẳng một mạch xuyên suốt toàn sàn qua các cột và lõi cứng. Dầm bắt buộc phân đoạn theo từng nhịp giữa 2 gối tựa (nút cột - vách).
   - Trên **Mặt bằng Định vị Cột Vách**: Tuyệt đối **KHÔNG ghi nhãn dầm** (`DCE_Name`). Dầm chỉ được hiển thị làm nét mờ tham chiếu trên layer `DCE_NetThay` (linetype `HIDDEN_DBIM`) để tránh loạn thị giác. Nhãn dầm thuộc riêng bản vẽ Mặt bằng Kết cấu Dầm Sàn.
2. **Khóa chống đè chữ & căn tâm cấu kiện (Anti-Collision & Centering Lock)**:
   - Block `TenCauKien` (Tên cột và tiết diện) phải được căn đúng tâm cấu kiện trong hệ tọa độ bản vẽ (World Coordinates), triệt tiêu hoàn toàn độ lệch $700\text{ mm}$ do basepoint block.
   - Nhãn ghi chú lõi cứng, buồng thang máy phải đặt trong không gian thông thoáng, không bao giờ đè ngang qua buồng thang hay lỗ kỹ thuật.
3. **Khóa 4 tầng biên ngoài chuẩn xây dựng (4-Tier Exterior Dimension Hierarchy)**:
   - Thứ tự từ mép công trình đi ra ngoài bắt buộc:
     1. *Mép sàn / Công trình* $\rightarrow$
     2. *Tầng 1*: Kích thước chi tiết cột & chuỗi neo định vị trắc đạc (`DCE_Setout`) $\rightarrow$
     3. *Tầng 2*: Kích thước khoảng cách liên trục từng bước (`DCE_Dim`, DimStyle `Dce_100MV`) $\rightarrow$
     4. *Tầng 3*: Kích thước phủ bì tổng thể công trình (`DCE_Dim`) $\rightarrow$
     5. *Tầng 4*: Bong bóng trục ngoài cùng (`Dce_KhTenTruc`, text căn giữa, đường tim trục vươn xuyên qua các tầng dim).
4. **Khóa Solid Hatch Bê tông (Solid Concrete Hatch Enforcer)**:
   - 100% cột và vách BTCT phải có Solid Hatch màu xám kỹ thuật (`color = 8`, layer `DCE_Hatch`) với lệnh gọi `set_pattern_fill("SOLID")`. Cấm để cấu kiện rỗng ruột (hollow wireframe).
5. **Khóa Khung bản vẽ tiêu chuẩn & Bảng thống kê (Drawing Frame & Schedule Table Lock)**:
   - Mọi bản vẽ phải được đóng khung tiêu chuẩn A1 ($84100 \times 59400\text{ mm}$ ở 1:100) hoặc A0, có khung viền trong (lề gáy $25\text{ mm}$, lề khác $10\text{ mm}$) và Khung tên đồ án chuẩn DCE Pro (`DCE_Frame`) góc dưới phải.
   - Bản vẽ định vị cột vách bắt buộc có **Bảng Thống kê Tiết diện & Cốt thép Cột Vách** (`DCE_Schedule`) đặt ở lề phải, liệt kê đầy đủ STT, Mã CK, Kích thước, Cấp bê tông B35, Thép dọc, Thép đai và Số lượng.
   - Ô mở thang máy phải thể hiện nét cửa mở (`DCE_GapOpen`) có dầm lanh tô (`DCE_Lanh_To`); lỗ rỗng xuyên sàn thang bộ / MEP shaft phải có 2 nét gạch chéo X (`DCE_VoidX`).
6. **Khóa Luồng CAD-first, MCP-first & Visual Gate (Bài học 2026-11-15)**:
   - Xuất **CAD (`.dxf`/`.dwg`) qua MCP `dce-cad`** là mục tiêu chính: **không mặc định xuất PDF (`export_pdf=False`)** khi User không yêu cầu.
   - Luôn dùng luồng chính `DcePlanEngine` (`v6=True`) + `DCE_Master_Seed_Template.dxf`, cấm vẽ song song từ đầu trên fixture giả.
   - Bắt buộc test 1 ca công trình thật + tự soi ảnh `render_preview` trước khi bàn giao Dual-Agent (`DUAL_AGENT_BUS.json`) hay chốt hoàn thành.

---
