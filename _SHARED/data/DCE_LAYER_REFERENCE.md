# BỘ LAYER CHUẨN HỢP NHẤT DCE PRO (FORM 2) + DCE STEEL

- **Schema:** `1.0.0`
- **Nguồn gốc:** `Form 2.dxf / DCE_Master_Seed_Template.dxf (46 layers)` + `C:\Dce Pro\AddinSteelCad\DbimSteelAutocad.dll -> DbimSteelAutocad.DceLayerName + Form 2_Steel.dwg` + `C:\Dce Pro\System\VN_Layer*.txt`
- **Tổng số layer:** `86` (`Form 2`: 46, `DCE STEEL`: 16, `Mặt bằng & Khung`: 16, `Compat`: 8)
- **File đồng bộ đa thiết bị:** `dce_layers_standard.json`, `DCE_Pro_And_Steel_Template.dxf`, `cad_layer_standard.py`

| Nhóm | Tên Layer | ACI (Gốc) | ACI (In Nền Sáng) | Linetype | Lineweight (1/100mm) | Ghi chú |
|---|---|---:|---:|---|---:|---|
| `form2_btct_46` | `0` | 7 | 7 | `Continuous` | 18 | Layer mặc định AutoCAD |
| `form2_btct_46` | `DCE_Name` | 142 | 5 | `Continuous` | 20 | Nhãn tên cấu kiện, mặt cắt, dầm |
| `form2_btct_46` | `DCE_KT` | 142 | 142 | `Continuous` | 20 | Kích thước / ký hiệu kỹ thuật DCE |
| `form2_btct_46` | `Defpoints` | 7 | 7 | `Continuous` | 5 | Điểm định nghĩa Dim không in |
| `form2_btct_46` | `DCE_Dim` | 254 | 8 | `Continuous` | 9 | Đường kích thước chuẩn Dce_*MV |
| `form2_btct_46` | `DCE_Block` | 8 | 8 | `Continuous` | 9 | Block ký hiệu trục, tiêu đề |
| `form2_btct_46` | `DCE_MCZiCZac` | 144 | 144 | `Continuous` | 13 | Đường cắt ziczac mặt cắt |
| `form2_btct_46` | `Dce_text` | 7 | 7 | `Continuous` | 13 | Văn bản thuyết minh, ghi chú |
| `form2_btct_46` | `DCE_BaoBeTong` | 4 | 7 | `Continuous` | 18 | Đường bao bê tông dầm, cột, sàn |
| `form2_btct_46` | `DCE_ThepChu` | 1 | 1 | `Continuous` | 35 | Cốt thép chịu lực chính |
| `form2_btct_46` | `DCE_ThepDai` | 220 | 220 | `Continuous` | 25 | Cốt thép đai / thép cấu tạo |
| `form2_btct_46` | `DCE_Truc` | 8 | 1 | `DASHDOT2_DBIM` | 13 | Đường tim lưới trục (DASHDOT2_DBIM) |
| `form2_btct_46` | `DCE_NetKhuat` | 9 | 9 | `HIDDEN_DBIM` | 5 | Nét khuất / lót tham chiếu kiến trúc |
| `form2_btct_46` | `DCE_NetDut` | 8 | 8 | `HIDDEN_DBIM` | 5 | Nét đứt cấu kiện ẩn / nhịp khuất |
| `form2_btct_46` | `DCE_Hatch` | 8 | 8 | `Continuous` | 13 | Hatch vật liệu bê tông / thép / vùng hạ cốt |
| `form2_btct_46` | `DCE_Gen_Open` | 144 | 144 | `CENTER2_DBIM` | 13 | Ký hiệu hộp kỹ thuật / lỗ mở (CENTER2_DBIM) |
| `form2_btct_46` | `AREAS` | 1 | 1 | `Continuous` | 18 | Vùng tính diện tích |
| `form2_btct_46` | `POINTS` | 5 | 5 | `Continuous` | 18 | Điểm định vị |
| `form2_btct_46` | `DCE_ThepChu.TTT` | 5 | 5 | `Continuous` | 35 | Cốt thép chủ mặt cắt / thống kê TTT |
| `form2_btct_46` | `DCE_ThepDai.TTT` | 6 | 6 | `Continuous` | 25 | Cốt thép đai mặt cắt / thống kê TTT |
| `form2_btct_46` | `DCE_Nhip` | 7 | 7 | `Continuous` | 30 | Đường nhịp / dầm biên nhịp |
| `form2_btct_46` | `DCE_TKT-TEXT` | 2 | 7 | `Continuous` | 15 | Chữ khung tên và bảng thống kê thép |
| `form2_btct_46` | `DCE_Symbol` | 8 | 6 | `Continuous` | 9 | Ký hiệu cao trình, sàn hạ, tag sàn |
| `form2_btct_46` | `DCE_WIPEOUT` | 7 | 7 | `Continuous` | 18 | Vùng che nền Wipeout |
| `form2_btct_46` | `DCE_TenNhip` | 7 | 7 | `Continuous` | 18 | Nhãn tên nhịp dầm |
| `form2_btct_46` | `DCE_GoiDam` | 7 | 7 | `Continuous` | 18 | Ký hiệu gối tựa dầm |
| `form2_btct_46` | `DCE_SUB-COLN_T---` | 6 | 6 | `Continuous` | 25 | Cột phân vùng T (DCE Pro) |
| `form2_btct_46` | `DCE_SUB-COWA_----` | 210 | 210 | `Continuous` | 25 | Cột / vách phân vùng COWA (VN_LayerCot) |
| `form2_btct_46` | `DCE_SUB-COLN_S---` | 6 | 6 | `Continuous` | 25 | Cột phân vùng S (DCE Pro) |
| `form2_btct_46` | `DCE_NetThay` | 7 | 7 | `Continuous` | 18 | Nét thấy / dầm tham chiếu (BEAM HIDEN_DBIM trên MB cột) |
| `form2_btct_46` | `DCE_Lanh_To` | 3 | 3 | `Continuous` | 18 | Dầm lanh tô cửa mở / khu vệ sinh (VN_LayerVeSinh) |
| `form2_btct_46` | `DCE_BottomBars` | 1 | 1 | `HIDDEN_DBIM` | 40 | Cốt thép lớp dưới sàn (HIDDEN_DBIM) |
| `form2_btct_46` | `DCE_Beam` | 2 | 7 | `BEAM HIDEN_DBIM` | 25 | Dầm BTCT / dầm phụ (BEAM HIDEN_DBIM trong Form 2) |
| `form2_btct_46` | `DCE_CDD` | 142 | 142 | `Continuous` | 25 | Cao độ / đường dẫn chi tiết DCE |
| `form2_btct_46` | `DCE_ChiaDoiTuong` | 51 | 51 | `Continuous` | 18 | Đường chia đối tượng / phân đoạn |
| `form2_btct_46` | `DCE_Note` | 117 | 7 | `Continuous` | 18 | Khung ghi chú kỹ thuật |
| `form2_btct_46` | `DCE_Coc` | 2 | 2 | `Continuous` | 13 | Tim và biên dạng cọc móng |
| `form2_btct_46` | `DCE_TextCoc` | 2 | 2 | `Continuous` | 15 | Tên và ghi chú cọc móng |
| `form2_btct_46` | `DCE_Coc3D` | 8 | 8 | `Continuous` | 13 | Đối tượng cọc 3D |
| `form2_btct_46` | `DCE_Dim2` | 8 | 8 | `Continuous` | 5 | Đường kích thước phụ / chi tiết |
| `form2_btct_46` | `Dce_ViTriThep` | 7 | 7 | `Continuous` | 13 | Đánh dấu vị trí thanh thép |
| `form2_btct_46` | `DCE_Hatch @ 1` | 8 | 8 | `Continuous` | 13 | Layer Form 2.dxf (DCE_Hatch @ 1) |
| `dce_steel_16` | `DCE_MainBeam` | 3 | 7 | `Continuous` | 30 | Dầm / kèo chính kết cấu thép & BTCT |
| `dce_steel_16` | `DCE_SubBeam` | 2 | 8 | `Continuous` | 20 | Dầm phụ kết cấu thép / sàn |
| `dce_steel_16` | `DCE_Flange` | 4 | 5 | `Continuous` | 30 | Cánh thép hình I/H/C |
| `dce_steel_16` | `DCE_Web` | 2 | 7 | `Continuous` | 25 | Bụng thép hình I/H/C |
| `dce_steel_16` | `DCE_Plate` | 6 | 6 | `Continuous` | 25 | Bản mã, bản đế, sườn tăng cứng thép |
| `dce_steel_16` | `DCE_Bracing` | 3 | 3 | `DASHDOT2_DBIM` | 18 | Hệ giằng mái, giằng cột thép |
| `dce_steel_16` | `DCE_Purlin` | 2 | 5 | `HIDDEN_DBIM` | 18 | Xà gồ C/Z mái và tường |
| `dce_steel_16` | `DCE_Rod` | 1 | 1 | `CENTER2_DBIM` | 15 | Ty giằng, thanh kéo giằng |
| `dce_steel_16` | `DCE_Weld` | 1 | 1 | `Continuous` | 18 | Ký hiệu & đường hàn liên kết thép |
| `dce_steel_16` | `DCE_Tole` | 8 | 8 | `Continuous` | 13 | Tôn lợp mái / vách / sàn deck |
| `dce_steel_16` | `DCE_Pipe` | 4 | 4 | `Continuous` | 25 | Thép ống tròn kết cấu |
| `dce_steel_16` | `DCE_Tube` | 4 | 4 | `Continuous` | 25 | Thép hộp vuông / chữ nhật |
| `dce_steel_16` | `DCE_L` | 3 | 3 | `Continuous` | 20 | Thép góc L |
| `dce_steel_16` | `DCE_U` | 3 | 3 | `Continuous` | 20 | Thép chữ U / C |
| `dce_steel_16` | `DCE_TopBars` | 5 | 5 | `Continuous` | 40 | Cốt thép lớp trên sàn (đối xứng DCE_BottomBars) |
| `dce_steel_16` | `DCE_ThepSanGC` | 1 | 1 | `Continuous` | 35 | Cốt thép gia cường gối/bụng sàn |
| `dce_plan_extensions_17` | `DCE_Cot` | 2 | 7 | `Continuous` | 35 | Cột BTCT mặt bằng định vị |
| `dce_plan_extensions_17` | `DCE_Vach` | 4 | 4 | `Continuous` | 35 | Vách / lõi cứng BTCT |
| `dce_plan_extensions_17` | `DCE_Boundary_Zone` | 1 | 1 | `HIDDEN_DBIM` | 25 | Vùng biên vách chịu lực (Boundary Element) |
| `dce_plan_extensions_17` | `DCE_Setout` | 3 | 8 | `Continuous` | 13 | Đường kích thước định vị trắc đạc cột/vách |
| `dce_plan_extensions_17` | `DCE_Schedule` | 7 | 7 | `Continuous` | 20 | Bảng thống kê cấu kiện & vật liệu |
| `dce_plan_extensions_17` | `DCE_Frame` | 7 | 7 | `Continuous` | 50 | Khung bản vẽ A0/A1/A3 & khung tên |
| `dce_plan_extensions_17` | `DCE_CouplingBeam` | 6 | 6 | `Continuous` | 25 | Dầm nối lõi cứng (Coupling Beam) |
| `dce_plan_extensions_17` | `DCE_VoidX` | 8 | 1 | `Continuous` | 13 | Lỗ rỗng xuyên sàn & nét gạch chéo X |
| `dce_plan_extensions_17` | `DCE_Thep_Chu` | 1 | 1 | `Continuous` | 40 | Cốt thép chủ mặt cắt / bảng vẽ |
| `dce_plan_extensions_17` | `DCE_Thep_Dai` | 3 | 3 | `Continuous` | 18 | Cốt thép đai mặt cắt / bảng vẽ |
| `dce_plan_extensions_17` | `DCE_Core` | 4 | 4 | `Continuous` | 30 | Biên lõi cứng / thang máy / MEP shaft |
| `dce_plan_extensions_17` | `DCE_GapOpen` | 3 | 3 | `HIDDEN_DBIM` | 15 | Cửa mở thang máy / lỗ mở nét đứt |
| `dce_plan_extensions_17` | `DCE_Leader` | 250 | 7 | `Continuous` | 13 | Đường dẫn leader chú thích né đè chữ |
| `dce_plan_extensions_17` | `DCE_RanhDat` | 1 | 1 | `DASHDOT2_DBIM` | 30 | Ranh giới khu đất pháp lý |
| `dce_plan_extensions_17` | `DCE_ChiGioi` | 6 | 6 | `HIDDEN_DBIM` | 20 | Chỉ giới xây dựng / khoảng lùi |
| `dce_plan_extensions_17` | `DCE_Road` | 8 | 8 | `Continuous` | 15 | Đường giao thông / vỉa hè tiếp giáp |
| `compat_aliases_8` | `DCE_Steel_Sect` | 5 | 5 | `Continuous` | 30 | Compat alias trong dce_steel_adapter.py (khuyên dùng DCE_Flange/DCE_Web) |
| `compat_aliases_8` | `DCE_Steel_Plate` | 6 | 6 | `Continuous` | 25 | Compat alias trong dce_steel_adapter.py (khuyên dùng DCE_Plate) |
| `compat_aliases_8` | `DCE_Steel_Bolt` | 1 | 1 | `Continuous` | 18 | Compat bu lông kết cấu thép trong dce_steel_adapter.py |
| `compat_aliases_8` | `REBAR_TOP` | 1 | 1 | `Continuous` | 35 | PaperSpace/C2 tách lớp thép lớp trên |
| `compat_aliases_8` | `REBAR_BOTTOM` | 5 | 5 | `Continuous` | 35 | PaperSpace/C2 tách lớp thép lớp dưới |
| `compat_aliases_8` | `VP_TOP` | 1 | 1 | `Continuous` | 25 | PaperSpace C2 viewport trên |
| `compat_aliases_8` | `VP_BOTTOM` | 5 | 5 | `Continuous` | 25 | PaperSpace C2 viewport dưới |
| `compat_aliases_8` | `VP_MODEL` | 7 | 7 | `Continuous` | 25 | PaperSpace C2 viewport mô hình |
