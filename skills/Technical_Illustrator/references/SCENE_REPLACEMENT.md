<!-- REFERENCE FILE — Đọc khi cần thay thế/chèn chi tiết kỹ thuật vào ảnh hiện trạng. -->

# Scene Replacement Protocol — Kỹ thuật Thay thế Phối cảnh Chân thực

## 1. Tổng quan

Kỹ thuật Scene Replacement cho phép AI:
- **Giữ nguyên** bối cảnh hiện trạng (cây cối, mặt nước, công trình lân cận, góc nhìn, ánh sáng).
- **Thay thế** chỉ những yếu tố cần cải tạo (hàng rào cũ → mới, bờ đất sạt → kè, mái tôn → mái kính).
- **Kết quả** trông như ảnh chụp thực tế sau khi thi công xong, không phải render 3D.

---

## 2. Scene Analysis Protocol (Phân tích Cảnh Hiện trạng)

Trước khi viết prompt, BẮT BUỘC phân tích ảnh hiện trạng theo 7 tiêu chí:

| # | Tiêu chí | Câu hỏi cần trả lời | Ví dụ |
|---|----------|---------------------|-------|
| 1 | **Góc chụp** | Eye-level? Aerial? Panorama? Telephoto? | "Eye-level, slight high angle, ~1.5m height" |
| 2 | **Ánh sáng** | Thời điểm nào? Trời nắng/mây/mưa? Bóng đổ hướng nào? | "Afternoon overcast, soft shadows from left" |
| 3 | **Tông màu** | Ảnh thiên warm/cool/neutral? Có bão hòa cao không? | "Warm green dominant, slightly desaturated" |
| 4 | **Tiền cảnh** | Vật thể gần camera nhất là gì? Cần giữ hay thay? | "Mặt cầu gỗ cũ — GIỮ NGUYÊN" |
| 5 | **Trung cảnh** | Khu vực chính cần can thiệp là gì? | "Bờ kênh sạt lở, hàng rào tôn cũ — THAY THẾ" |
| 6 | **Hậu cảnh** | Cây cối, công trình phía xa? | "Hàng trúc Yên Tử, nhà dân — GIỮ NGUYÊN" |
| 7 | **Yếu tố đặc trưng** | Chi tiết nào làm ảnh có hồn (phản chiếu nước, rêu phong, lá rụng)? | "Mặt nước phản chiếu cây xanh, bùn ẩm ven bờ" |

---

## 3. Replacement Zone Mapping (Bản đồ Khu vực Thay thế)

Sau khi phân tích, phân chia ảnh thành 3 vùng:

```
┌────────────────────────────────────────────────┐
│                  KEEP ZONE                     │ ← Hậu cảnh: giữ nguyên 100%
│  (cây xanh, bầu trời, công trình lân cận)      │
├────────────────────────────────────────────────┤
│              REPLACEMENT ZONE                  │ ← Trung cảnh: thay thế chi tiết
│  (hàng rào cũ → mới, bờ đất → kè/cỏ)           │
├────────────────────────────────────────────────┤
│                 KEEP ZONE                      │ ← Tiền cảnh: giữ nguyên
│  (mặt cầu, lan can cũ, mặt nước)               │
└────────────────────────────────────────────────┘
```

Trong prompt phải mô tả RÕ RÀNG:
- **KEEP**: "PRESERVE the existing [mô tả cụ thể] exactly as shown in the reference image"
- **REPLACE**: "REPLACE the [mô tả cũ] WITH [mô tả mới chi tiết]"

---

## 4. Photorealism Checklist (Bảng Kiểm Độ Chân thực)

Trước khi hoàn thiện prompt, kiểm tra 10 yếu tố sau:

| # | Yếu tố | Mô tả chi tiết | Cách viết trong prompt |
|---|--------|-----------------|----------------------|
| 1 | **Weathering (Phong hóa)** | Vật liệu mới vẫn cần có vệt mưa, bám bụi nhẹ nếu bối cảnh không phải công trường mới | "slightly weathered surface with natural patina" |
| 2 | **Ground Contact (Tiếp xúc mặt đất)** | Chân cột/móng phải có đất, cỏ mọc quanh chân, không "lơ lửng" | "grass growing naturally around the base, soil contact visible" |
| 3 | **Shadow Consistency (Bóng đổ thống nhất)** | Bóng đổ của vật mới phải cùng hướng với bóng đổ trong ảnh gốc | "shadows falling to the [left/right] consistent with existing scene lighting" |
| 4 | **Material Aging (Tuổi vật liệu)** | Nếu bối cảnh là khu dân cư lâu năm, vật liệu mới nên hơi cũ | "new but naturally aged [material] matching surrounding environment" |
| 5 | **Water Interaction (Tương tác nước)** | Mép kè/taluy giao nước phải có: rêu, vệt ẩm, phản chiếu | "waterline with moss, damp marks, and water reflection" |
| 6 | **Vegetation Blend (Hòa trộn thực vật)** | Cỏ/cây mới phải blend với cây cối xung quanh, không quá xanh | "vegetation blending naturally with existing mature plants" |
| 7 | **Scale Accuracy (Tỷ lệ chính xác)** | So sánh với vật tham chiếu đã có trong ảnh (cửa sổ, người, xe) | "matching the scale of existing elements in the scene" |
| 8 | **Edge Blending (Hòa mép)** | Ranh giới giữa vùng cũ và mới phải mượt, không có đường cắt rõ | "seamless transition between new and existing elements" |
| 9 | **Atmospheric Perspective (Viễn cận khí quyển)** | Vật xa hơi mờ, vật gần sắc nét — phải đúng với ảnh gốc | "depth of field and atmospheric haze matching reference" |
| 10 | **Color Grading (Tông màu)** | Màu sắc vật mới phải khớp tông màu chung của ảnh gốc | "color palette harmonizing with the warm/cool tones of the existing scene" |

---

## 5. Prompt Structure cho Scene Replacement

Khi thay thế chi tiết trong ảnh hiện trạng, BẮT BUỘC dùng cấu trúc prompt sau:

```
"Edit this photograph to show the completed renovation/construction.

PRESERVE EXACTLY: [Liệt kê chi tiết giữ nguyên — VD: the old wooden 
  bridge, the bamboo trees on both banks, the water channel, the existing 
  houses in the background].

REPLACE: [Mô tả chi tiết cần thay thế — VD: Replace the eroded bare 
  earth banks with compacted earth slopes covered in lush green lawn grass 
  (Bermuda grass), sloping smoothly from the fence line down to the 
  water edge].

ADD NEW: [Mô tả chi tiết mới — VD: Install a continuous natural brown 
  wooden fence along the top edge of the grass slope, with vertical wood 
  planks (120mm wide, 15mm gap between planks), mounted on square steel 
  posts at 2m intervals. The fence height is approximately 1.2m above 
  ground level. The steel posts have concrete footings buried below grade].

STYLE: This should look like a real photograph taken after construction 
  is complete, not a 3D render. Match the exact lighting conditions, 
  color temperature, and atmospheric quality of the original photo.

MUST NOT: [Liệt kê chi tiết cấm — VD: Do NOT add any chain-link fence. 
  Do NOT add gabion walls. Do NOT remove the existing bridge. 
  Do NOT change the water level].

Quality: photorealistic photograph, natural lighting matching original 
  scene, seamless integration, no visible editing artifacts, 8K detail."
```

---

## 6. Material Reality Library (Thư viện Mô tả Vật liệu Chân thực)

Dùng các mô tả vật liệu dưới đây thay vì viết chung chung:

### 6a. Kim loại (Metal)
| Vật liệu | Mô tả prompt chân thực |
|-----------|----------------------|
| Thép mạ kẽm mới | "hot-dip galvanized steel with bright silvery-grey matte finish, slight zinc crystal pattern (spangle) visible" |
| Thép mạ kẽm cũ | "weathered galvanized steel with dull grey patina, slight surface oxidation and water stains" |
| Thép sơn tĩnh điện xám | "powder-coated steel in RAL 7016 anthracite grey, smooth semi-gloss finish" |
| Lưới B40 mạ kẽm | "chain-link wire mesh (diamond pattern, 50mm opening), hot-dip galvanized silver finish, tensioned taut between steel posts" |
| Thép hình sơn lót đỏ | "structural steel with red oxide primer coating, rough brush-mark texture" |

### 6b. Bê tông (Concrete)
| Vật liệu | Mô tả prompt chân thực |
|-----------|----------------------|
| BT mới đổ tại chỗ | "fresh cast-in-place concrete, light grey with visible formwork marks and slight surface imperfections" |
| BT cũ phong hóa | "aged concrete with dark water stains, moss patches at base, hairline surface cracks" |
| BT đúc sẵn | "precast concrete with smooth factory finish, uniform light grey color, chamfered edges" |
| Gờ móng BT | "concrete grade beam protruding 150mm above ground, with rough top surface and visible aggregate" |

### 6c. Gỗ (Wood)
| Vật liệu | Mô tả prompt chân thực |
|-----------|----------------------|
| Gỗ tự nhiên mới | "natural hardwood planks with warm honey-brown color, visible wood grain, freshly sanded smooth surface" |
| Gỗ tự nhiên phong hóa | "naturally weathered timber with silver-grey patina, deep grain texture, slight warping" |
| Gỗ sơn phủ nâu | "timber painted in dark walnut brown, semi-gloss finish, with slight brush marks" |
| Gỗ hàng rào đứng | "vertical wooden fence boards (120mm width × 20mm thick), 10-15mm gap between boards, rounded top edges" |

### 6d. Địa hình & Cảnh quan (Landscape)
| Yếu tố | Mô tả prompt chân thực |
|---------|----------------------|
| Taluy cỏ xanh | "compacted earth slope (1:1.5 ratio) covered with dense Bermuda grass lawn, uniformly green, freshly maintained" |
| Taluy đất trần | "bare compacted laterite earth slope, reddish-brown color, with visible compaction marks" |
| Kè đá hộc xếp khan | "dry-stacked natural river stones (150-300mm diameter), irregular shapes, grey-brown color, moss growing between joints" |
| Mương nước trong | "clear water canal with visible bottom, slight green tint from algae, gentle current ripples" |
| Mương nước đục | "murky brown canal water with floating debris, water hyacinth patches along edges" |

---

## 7. Common Mistakes & Fixes (Lỗi Thường gặp & Cách sửa)

| Lỗi | Nguyên nhân | Cách sửa trong prompt |
|-----|-------------|---------------------|
| Vật thể "lơ lửng" trên mặt đất | Thiếu mô tả tiếp xúc đất | Thêm "firmly embedded in the ground" + "grass growing around base" |
| Hàng rào quá hoàn hảo, giả tạo | Mô tả quá "mới" | Thêm "with natural weathering" + "slightly imperfect alignment" |
| Bóng đổ sai hướng | Không phân tích ánh sáng ảnh gốc | Thêm "shadows consistent with [hướng] sun position in original photo" |
| Cỏ quá xanh, không tự nhiên | Thiếu mô tả blend | Thêm "matching the green tones of surrounding vegetation" |
| Mất chi tiết hậu cảnh | Prompt quá dài về foreground | Thêm "PRESERVE background exactly as reference" ở đầu prompt |
| Tỷ lệ kết cấu sai | Thiếu vật tham chiếu | Thêm "fence height approximately equal to chest height of an adult person" |
| Ranh giới cũ/mới rõ quá | Thiếu edge blending | Thêm "seamless natural transition at boundaries" |
| Vật liệu trông như plastic | Mô tả bề mặt thiếu | Dùng Material Reality Library (mục 6) |
