# PHẢN BIỆN KIẾN TRÚC — 4 FORM MỞ & BLOCK DCE

> Bàn giao: CLAUDE → GEMINI  
> Ngày: 2026-11-16  
> Phạm vi: phản biện kiến trúc, chưa sửa code sản xuất.

## Kết luận điều hành

Đề xuất 4 Form mở là đúng hướng, nhưng không nên coi DXF người dùng sửa là “nguồn sự thật duy nhất” cho hình học sinh tự động. Kiến trúc an toàn nhất là **Template Contract + Zone Manifest + non-destructive renderer**, trong đó:

- Form người dùng sửa giữ vai trò **presentation shell**: khung, title block, layer/style, logo, ghi chú và vùng bố cục.
- Model JSON/registry giữ vai trò **engineering source of truth**: cột, dầm, trục, cọc, cao độ, thông số và semantic IDs.
- Engine chỉ cập nhật vùng được đánh dấu và ATTRIB đã biết; không xóa ModelSpace, không ghi đè style đã có.
- Mỗi Form phải có `form_manifest` và `template_contract_version`, nếu thiếu hoặc sai thì fallback an toàn về template chuẩn, không tự đoán.

## Câu hỏi 1 — 4 Form mở và các lỗ hổng khi kỹ sư sửa trong AutoCAD

### Đánh giá

Mô hình Zone Marker + TitleBlock ATTDEF + Inherit-from-Form khả thi, nhưng cần bổ sung các khóa sau.

1. **User xóa hoặc đổi tên Zone Marker**
   - Không được mặc định full-sheet hoặc tọa độ cứng.
   - Manifest phải yêu cầu zone bắt buộc theo Form: `VIEWPORT`, `TABLE`, `NOTE`, `KEYPLAN`, `TITLEBLOCK`.
   - Thiếu zone → báo `E002 TEMPLATE_ZONE_MISSING`, không render vào vùng đoán.
   - Cho phép zone alias trong manifest, nhưng alias phải khai báo tường minh.

2. **User kéo dãn zone hoặc đổi UCS**
   - Lưu bbox theo WCS và ghi `ucs_name`/tọa độ kiểm tra trong manifest.
   - Không dùng INSERT scale để “sửa” UCS âm thầm.
   - Nếu UCS không phải World hoặc có transform không trực giao → `W003 TEMPLATE_TRANSFORM_REVIEW`.
   - Geometry engine vẫn dùng WCS; chỉ phép biến đổi affine đã kiểm tra và ghi audit.

3. **ModelSpace so với PaperSpace/Layout**
   - Form Contract phải khai báo `space: MODEL` hoặc `space: PAPER` cho từng zone.
   - V1 nên hỗ trợ MODELSPACE trước để tránh phụ thuộc viewport AutoCAD.
   - PAPERSPACE chỉ được hỗ trợ khi có layout name, viewport handle và mapping rõ ràng.
   - Không trộn geometry ModelSpace vào PaperSpace mà không có explicit mapping.

4. **DXF/DWG version AC1027/AC1032**
   - `ezdxf` không nên được coi là bộ chuyển đổi DWG hoặc dynamic-block engine.
   - Khi đọc DXF version cao hơn mức hỗ trợ: audit metadata rồi mở ở chế độ read/limited, không tự ghi đè.
   - Preserve unknown sections/entities khi có thể; nếu không đảm bảo round-trip thì xuất bản copy mới và đánh dấu `ROUNDTRIP_LIMITED`.
   - DWG phải đi qua adapter ODA/AutoCAD optional; không chặn DXF pipeline khi ODA không có.

5. **Khung tên trong Form**
   - `DCE_TITLEBLOCK_A1/A3` phải là named block có ATTDEF chuẩn, không dùng TEXT tĩnh làm contract.
   - ATTDEF thiếu tag bắt buộc → block không đạt contract, không fallback bằng TEXT im lặng.
   - Các tag lạ của công ty được giữ nguyên; engine chỉ cập nhật tag trong allowlist.

### Form Manifest tối thiểu

```json
{
  "template_contract_version": "1.0",
  "form_id": "FORM_02_MULTIVIEW_A3_BTCT",
  "source_space": "MODEL",
  "required_zones": {
    "VIEWPORT_TOP": "DCE_ZONE_VIEWPORT_TOP",
    "VIEWPORT_BOTTOM": "DCE_ZONE_VIEWPORT_BOTTOM",
    "TABLE": "DCE_ZONE_TABLE",
    "NOTE": "DCE_ZONE_NOTE",
    "KEYPLAN": "DCE_ZONE_KEYPLAN",
    "TITLEBLOCK": "DCE_TITLEBLOCK_A3"
  },
  "required_title_tags": ["TEN_CONG_TRINH", "TEN_BAN_VE", "KY_HIEU", "TY_LE"],
  "preserve_user_styles": true,
  "min_supported_dxf_version": "AC1021"
}
```

Manifest nên được lưu cạnh Form, không nhúng toàn bộ contract vào tên layer. Layer/Block vẫn là marker trong CAD; manifest là contract máy đọc được.

## Câu hỏi 2 — Chiến lược Block Cột/Trục/Cọc/Dầm/Tiêu đề

### Nguyên tắc chung

Tách ba lớp:

1. **Geometry block**: hình học có thể scale.
2. **Annotation block**: ATTRIB/text giữ kích thước chữ theo tỷ lệ bản vẽ.
3. **Semantic registry**: mapping `element_id → block_name → ATTRIB tags → WCS insert`.

Không nên dùng non-uniform scale trực tiếp lên dynamic block DCE có `*U*`. Các dynamic block `DCE_CL_REC1_`, `DCE_CL_Circle_`, `DCE_Beam2` phụ thuộc action/anonymous block của AutoCAD; `ezdxf` có thể bảo toàn dữ liệu nhưng không đáng tin cậy để chỉnh tham số động và không đảm bảo chữ/hatch sau non-uniform scale.

### Quyết định theo nhóm

| Nhóm | Chiến lược chuẩn | Lý do |
|---|---|---|
| Trục | Dùng `Dce_KhTenTruc`/`Dce_TenTruc` dạng INSERT + ATTRIB `TRUC`; uniform scale theo sheet scale | Block đã có semantic tag, headless và AutoCAD tương thích tốt |
| Cao trình/sàn/nhãn | Dùng block hiện có + `dce_block_binding.py`; chỉ ghi tag đã đăng ký | Đã có formatter/parser và round-trip contract |
| Cột | Không chỉnh dynamic `*U*` trực tiếp; tạo named block theo kích thước hoặc geometry block + `TenCauKien` annotation riêng | Tránh méo ATTDEF, hatch và phụ thuộc AutoCAD Action |
| Dầm | Dùng named geometry block theo tiết diện/chiều dài hoặc line geometry theo nhịp; dùng `Dce_KhTenDam`/`Dce_KhTenNhip` riêng cho nhãn | Dầm có hướng và chiều dài biến đổi; annotation phải xoay độc lập |
| Cọc | Tạo block chuẩn mới `DCE_Pile` với circle/cross + ATTDEF `PILE_ID`, `D`, `L`, `Q`; không dùng circle/line rời trong output mới | Cần semantic identity và checker có thể audit |
| Khung tên | Tạo `DCE_TITLEBLOCK_A1` và `DCE_TITLEBLOCK_A3` named block + ATTDEF allowlist | Cho phép User sửa trong Block Editor mà không phá engine |

### Quy tắc scale ATTRIB

- Không dùng non-uniform scale cho block chứa chữ.
- Geometry có thể scale theo X/Y; annotation INSERT giữ `xscale=yscale=1` hoặc uniform scale theo `S`.
- Nếu cần cột 300x500: geometry block `DCE_COL_300x500`, annotation `TenCauKien` chèn riêng tại tâm WCS.
- `ATTRIB` phải được set qua binding registry, không sửa chuỗi DXF thô.
- Mọi block insert cần có `element_id`, `source_model_id` và `form_role` trong evidence registry.

### Dynamic Block fallback

- `ezdxf` chỉ dùng dynamic block như **read/preserve/clone**, không dùng để thay đổi Action Parameters.
- Khi cần biến kích thước headless, dùng generated named blocks có hash ổn định, ví dụ `DCE_COL_300x500_v1`.
- AutoCAD live có thể giữ dynamic block nguyên bản nếu User chỉnh thủ công; engine phải nhận diện `dynamic_preserved=true` và không cố normalize về named block.
- Không silently explode dynamic blocks. Nếu explode, phải ghi diagnostic và mất liên kết dynamic.

### Compliance Checker

`dce_cad_compliance_checker.py` cần mở rộng theo hướng adapter, không đổi gate API:

- `entities_log` vẫn là semantic evidence.
- Với `INSERT`, đọc `insert.dxf.name`, tọa độ WCS và `ATTRIB` con bằng `virtual_entities()`/attribs.
- Native checks phải xác nhận block tồn tại, ATTDEF/ATTRIB tag hợp lệ và giá trị round-trip.
- `TEXT` fallback chỉ được chấp nhận ở chế độ legacy/degraded; không coi là đạt semantic block gate.
- Các gate mới cho Pile/TitleBlock nên là `UNVERIFIED` nếu block chưa có contract, không đánh dấu PASS dựa trên tên layer.

## Câu hỏi 3 — Lộ trình Phase regression-safe

### Phase 0 — Contract, inventory, read-only audit

- Tạo manifest schema cho 4 Form.
- Tạo `template_loader` đọc Form, phát hiện space, version, zone và title block.
- Thêm read-only inventory: zones, blocks, ATTDEF, layers, dimstyles, DXF version.
- Mở rộng `cad_evidence_contract.py` để ghi `template_contract`, `zone_evidence`, `block_evidence`.
- Không thay đổi renderer hiện tại; toàn bộ output cũ giữ nguyên.
- Test: fixture thiếu zone, sai tag, AC1021, unknown block, stale SHA256.

**Tiêu chí:** 184 test hiện có xanh; test mới chỉ kiểm tra contract, chưa ép Form mở vào path cũ.

### Phase 1 — TitleBlock + Zone Marker cho một Form thí điểm

- Chọn Form 02 A3 làm pilot vì đã có luồng multiview.
- Tạo `DCE_TITLEBLOCK_A3` ATTDEF và các zone marker.
- Thêm `template_mode="open"`; default vẫn `template_mode="legacy"`.
- Renderer không xóa ModelSpace khi open mode; chỉ xóa/rebuild entities thuộc vùng engine-owned, dựa trên owner/evidence ID.
- Inherit layer/style; chỉ bổ sung layer thiếu từ SSOT.

**Exit gate:** output pilot có đủ zone/title evidence, physical audit PASS, full audit không giả PASS; suite cũ vẫn xanh.

### Phase 2 — Block adapters cho Trục, Cột, Dầm, Cọc

- Trục/cao trình/sàn trước vì block đã ổn định và có binding.
- Sau đó generated named blocks cho cột/dầm.
- Tạo `DCE_Pile` và binding registry.
- ATTRIB extraction + native checker tests.
- Không bật output block-first mặc định cho các Form legacy cho tới khi golden DXF và ảnh preview đạt parity.

### Phase 3 — Bốn Form và override theo dự án

Ưu tiên tìm Form theo thứ tự:

1. `project_dir/CAD_Forms/`
2. `00_Template_&_Standards/CAD_Forms/`
3. `.agents/_SHARED/data/CAD_Forms/` fallback

Mỗi Form có file DXF/DWG, manifest JSON, README ngắn và revision/changelog. Không dùng file trong `.agents/skills` làm nơi User chỉnh hàng ngày.

### Phase 4 — PaperSpace, DWG/ODA và live AutoCAD round-trip

- PaperSpace chỉ sau khi ModelSpace contract ổn định.
- ODA/AutoCAD là optional adapters.
- Test round-trip: open → edit title/zone/style → save → engine reload → export copy → reopen.
- Nếu round-trip không bảo toàn entity unknown, status phải là `ROUNDTRIP_LIMITED`, không PASS.

## Các quyết định không nên làm ngay

- Không xóa `msp.delete_entity` trong legacy path trước khi có `template_mode="open"` riêng.
- Không chuyển toàn bộ cột/dầm sang dynamic block ngay.
- Không dùng `Block_ALL` như một khối duy nhất để sinh bản vẽ; khó truy vết ownership và zone.
- Không đặt Form User-editable duy nhất trong `.agents/skills`; nên tách fallback chuẩn và workspace override.
- Không gọi `full_compliance_verified=true` chỉ vì sidecar v6 hợp lệ; phải có native block/ATTRIB evidence và zone evidence.

## Acceptance checklist cho Gemini

- [ ] Có manifest versioned và validator.
- [ ] Có explicit Model/Paper space contract.
- [ ] Có missing-zone/missing-ATTDEF/unsupported-version diagnostics.
- [ ] Có generated named block path cho dynamic-block-independent headless output.
- [ ] Có `DCE_Pile` + binding `PILE_ID/D/L/Q`.
- [ ] Checker đọc INSERT + ATTRIB native và phân biệt legacy/degraded.
- [ ] 4 Form chỉ bật từng Form qua feature flag.
- [ ] Mỗi phase giữ nguyên test cũ; golden DXF/preview được lưu riêng.

## Kết luận

Kiến trúc nên là **Open Form Contract, không phải Open DXF tùy ý**. Form được mở và sửa tự do trong AutoCAD, nhưng engine chỉ hành động trong contract có manifest, zone và tag rõ ràng. Block DCE hiện có được tái sử dụng cho trục, cao trình, nhãn và title; dynamic block `*U*` chỉ preserve/clone, còn output headless dùng named blocks sinh ổn định. Lộ trình bắt đầu bằng read-only audit rồi pilot một Form, sau đó mới bật block-first và PaperSpace/DWG.
