<!-- REFERENCE FILE — Chỉ đọc khi dùng MODE A (generate_image). KHÔNG đọc khi chỉ dùng MODE B (Python). -->

# Prompt Engineering Templates — MODE A (AI Realistic Render)

## Framework 5 Yếu tố Bắt buộc

| # | Yếu tố | Mô tả | Ví dụ |
|---|--------|-------|-------|
| 1 | **Subject** | Loại kết cấu chính, kích thước, hình dạng | "Heavy steel I-beam H400x200x8x13" |
| 2 | **Material Detail** | Kết cấu bề mặt, màu sắc vật liệu thực tế | "Raw grey concrete surface, galvanized steel bolts, red oxide primer" |
| 3 | **Scale Reference** | Vật/người tham chiếu kích thước | "A construction worker in orange safety vest standing next to it" |
| 4 | **Lighting & Style** | Kiểu render, ánh sáng | "Cinematic golden hour lighting, photorealistic, 8K detail" |
| 5 | **Camera Angle** | Góc camera cụ thể | "Low angle perspective shot, 35mm lens, shallow depth of field" |

---

## 8 Prompt Templates cho Kết cấu Phổ biến

**Template 1 — Dầm Thép (Steel Beam):**

```
"Photorealistic 3D render of a heavy steel I-beam [HxBxtw×tf] connected to 
a reinforced concrete column using steel base plate and [N] high-strength 
anchor bolts M[d]. The steel beam has red oxide primer coating with visible 
bolt holes. A construction worker in orange safety vest standing nearby for 
scale. Construction site background with formwork and rebar. Cinematic 
lighting, highly detailed technical engineering visualization, 8K resolution."
```

**Template 2 — Cột BTCT (RC Column):**

```
"Detailed photorealistic render of a reinforced concrete column cross-section, 
[width]x[depth]mm, showing [N] longitudinal rebars [diameter]mm arranged 
symmetrically with [spacing]mm stirrups. Grey concrete texture with visible 
aggregate. Exposed rebar ends with rust texture. Technical cutaway view, 
studio lighting, clean white background, architectural visualization style."
```

**Template 3 — Móng Cọc (Pile Foundation):**

```
"Isometric 3D cutaway render of a reinforced concrete pile cap foundation, 
showing [N] concrete piles [diameter]mm embedded in soil layers (topsoil, 
clay, sand). The pile cap has exposed rebar cage. Geological cross-section 
showing soil stratification. Technical engineering illustration, 8K quality."
```

**Template 4 — Khung Giàn Thép (Steel Truss Frame):**

```
"Wide angle photorealistic render of a steel truss roof structure spanning 
[L]m, with Warren/Pratt/Howe truss configuration. Steel members with 
galvanized finish, gusset plates at nodes with high-strength bolts. Purlins 
and bracing visible. Interior view of an industrial warehouse. Natural 
daylight streaming through skylights, architectural photography, highly detailed."
```

**Template 5 — Mái Vòm / Canopy:**

```
"Stunning photorealistic render of a curved steel canopy/roof structure with 
glass panels, spanning [L]m. Tubular steel members forming elegant curves. 
Stainless steel tension cables and spider glass fittings. Modern architectural 
context. Golden hour sunlight creating dramatic shadows. 8K architectural visualization."
```

**Template 6 — Sàn Thép Nhẹ (Light Gauge Steel Floor):**

```
"Detailed isometric 3D render of a light gauge steel floor system showing 
C-purlins/joists at [spacing]mm spacing, top chord bracing, bottom chord 
bracing, and composite concrete deck on top. Metal deck sheeting visible. 
Cutaway showing floor layers. Technical illustration style, clean lighting."
```

**Template 7 — Container Module:**

```
"Photorealistic render of a modified shipping container structure, 20ft/40ft, 
showing structural reinforcement steel frames where wall panels have been 
removed. Corner castings and twist locks visible. Stacked 2-story 
configuration with external steel staircase. Industrial photography style."
```

**Template 8 — Biện pháp Thi công (Construction Method):**

```
"Aerial perspective photorealistic render of an active construction site 
showing [specific activity: formwork installation / rebar tying / concrete 
pouring / steel erection]. Mobile crane [capacity]T operating. Workers in 
safety gear. Temporary shoring/scaffolding system visible. Bright daylight, 
detailed site layout, drone photography style, 8K."
```

---

## Negative Prompt (Luôn thêm vào cuối)

```
"Avoid: text overlays, watermarks, distorted proportions, unrealistic 
physics, floating objects, blurry details, cartoon style."
```

---

## Template 9 — Từ Bản vẽ Chi tiết (From-Drawing)

> **Khi nào dùng**: User cung cấp bản vẽ 2D chi tiết kỹ thuật (mặt cắt, mặt đứng, chi tiết cấu tạo) và yêu cầu tạo ảnh phối cảnh 3D thể hiện đúng các chi tiết đó.

### Quy trình bắt buộc trước khi viết prompt:

| Bước | Tên | Chi tiết |
|------|-----|----------|
| 1 | **Decompose Drawing** | Đọc bản vẽ 2D, liệt kê từng lớp cấu kiện: (a) Kết cấu chịu lực (thép hình, BT, gỗ), (b) Lớp hoàn thiện (sơn, mạ, gỗ tự nhiên), (c) Phụ kiện (bu lông, ghim neo, bản mã), (d) Cảnh quan (cỏ, cây, nước, đất), (e) Bối cảnh (công trình kề, đường, cầu) |
| 2 | **Build Prompt Layer-by-Layer** | Mỗi lớp cấu kiện phải có 1 câu mô tả riêng trong prompt, bao gồm: Vật liệu + Màu sắc + Kết cấu bề mặt + Kích thước tương đối |
| 3 | **Inject Constraint Negatives** | Liệt kê rõ ràng những gì KHÔNG muốn xuất hiện (VD: "NO gabion", "NO exposed concrete", "NO wooden fence") — đặt vào MUST NOT |
| 4 | **Multi-pass Iteration** | Nếu ảnh lần 1 chưa đúng chi tiết → phân tích sai ở layer nào → tinh chỉnh prompt tại layer đó → tạo ảnh lần 2. Tối đa 3 lần iteration/ảnh |

### Prompt Template:

```
"Photorealistic 3D architectural render based on the provided 2D 
engineering drawing.
[LAYER 1 - Structure]: [Mô tả cấu kiện chịu lực chính — loại thép/BT/gỗ, 
  kích thước tiết diện, bước nhịp, cao độ].
[LAYER 2 - Finish]: [Mô tả lớp hoàn thiện — sơn màu gì, mạ kẽm, gỗ tự 
  nhiên màu nâu, bề mặt bê tông xám].
[LAYER 3 - Accessories]: [Mô tả phụ kiện — bu lông, ghim neo, bản mã, 
  kích thước, vị trí lắp đặt].
[LAYER 4 - Landscape]: [Mô tả cảnh quan — loại cỏ, cây trồng, mặt nước, 
  taluy đất, bề mặt hoàn thiện nền].
[LAYER 5 - Context]: [Mô tả bối cảnh — công trình lân cận giữ nguyên, 
  con đường, hàng rào kề bên, cầu hiện hữu].
Scale reference: [Vật/người tham chiếu kích thước].
Camera: [Góc nhìn cụ thể — eye-level / aerial / low angle].
Lighting: [Kiểu ánh sáng — natural daylight / golden hour / overcast].
MUST NOT include: [Liệt kê chi tiết cần loại trừ — VD: NO stones on 
  slope, NO exposed concrete blocks].
Avoid: text overlays, watermarks, distorted proportions, unrealistic 
physics, floating objects, blurry details, cartoon style."
```

### Reference Image Protocol:

Khi User cung cấp ảnh hiện trạng kèm bản vẽ chi tiết:
1. Đọc **ảnh hiện trạng** → xác định: góc chụp, yếu tố cảnh quan cần giữ nguyên, yếu tố cần thay đổi.
2. Đọc **bản vẽ chi tiết** → trích xuất: kích thước, vật liệu, cấu tạo từng lớp.
3. Kết hợp (1) + (2) thành prompt phân lớp theo Template 9.
4. Pass ảnh hiện trạng vào `ImagePaths` của `generate_image` để AI giữ nguyên bối cảnh gốc.
