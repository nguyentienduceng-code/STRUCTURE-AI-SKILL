---
name: SKILL_PHULUC
version: 2.0.0
last_updated: 2026-10-21
description: "Lap Thuyet minh Tinh toan Ket cau, Dia ky thuat, Bien phap Thi cong (BPTC) va Phu luc Tinh toan chi tiet step-by-step theo TCVN, xuat file Word (.docx) theo 2 Bo Chuan (Bo 1 BKTECHS hoac Bo 2 TVTK Da Hang Muc). Kich hoat khi nguoi dung yeu cau lap, gop, hoac xuat thuyet minh tinh toan, phu luc tinh toan, bao cao tham tra ket cau, bien phap thi cong, hoac calculation sheet."
---
# Skill Phu Luc va Thuyet Minh Tinh Toan Ket Cau (SKILL_PHULUC v2.0)

Tao ho so Thuyet minh Tinh toan Ket cau, Dia ky thuat, Gia cuong va Bien phap Thi cong (BPTC) chi tiet step-by-step theo tieu chuan TCVN va xuat ra file Word (`.docx`) voi day du Bia doi, Muc luc tu dong (`Auto-TOC`), phan cap Heading mau sac va Header/Footer chuyen nghiep.

## Khi nao su dung Skill nay

- Khi nguoi dung yeu cau lap moi, gop, hoac chuan hoa **Thuyet minh Tinh toan Ket cau (TMTT)**, **Thuyet minh Bien phap Thi cong (BPTC)**, **Bao cao Tham tra Ket cau**, hoac **Phu luc Tinh toan chi tiet (Calculation Sheet)**.
- Khi nguoi dung yeu cau xuat ho so thuyet minh theo **Bo 1 (Chuan BKTECHS)** hoac **Bo 2 (Chuan TVTK Da Hang Muc)**.
- Khi can chuyen doi ban nhap Markdown (`.md`) hoac du lieu JSON tinh toan sang file `.docx` co dinh dang chuan phap ly xay dung Viet Nam.

## Lua chon 2 Bo Chuan Trinh Bay va Bo Tri Chapter

Moi khi xuat ho so thuyet minh, ho tro 2 bo chuan trinh bay (mac dinh uu tien **Bo 1 - BKTECHS** neu nguoi dung khong chi dinh khac):

### 1. Bo Chuan 1: Phong cach `bktechs` (Mac dinh uu tien - Vien / Truong / Tham tra / Chuyen sau)

- **Ung dung**: Thuyet minh tinh toan chuyen sau 1 den 2 hang muc (Be nuoc ngam, Be tu hoai, Mong coc, Tuong chan, Bien phap thi cong ho dao, Gia cuong CFRP) va Bao cao tham tra ket cau.
- **Bo cuc Section 0 (Bia doi + Muc luc)**:
  - **Trang 1 (Bia chinh)**: Tieu de Truong DH Bach Khoa / BKTECHS, dai bang xanh Navy (`#002060`), Logo luc giac BKTECHS o giua, ten ho so co lon (`24pt`), va bang thong tin Du an / Hang muc / Chu dau tu. Khong hien thi Header/Footer tren Trang 1 (`different_first_page_header_footer = True`).
  - **Trang 2 (Bia phu ky duyet)**: Bang kiem soat chat luong 3 cot (`Thuc hien` - `Kiem tra` - `Chu tri` kem hoc vi va so CCHN) va khoi ky dong dau Chu dau tu / Don vi tu van.
  - **Trang 3 (Muc luc tu dong)**: Truong `TOC \o "1-3" \h \z \u` tu dong cap nhat kem bang tom tat cau truc chuong muc.
- **Bo cuc Section 1 (Noi dung chinh)**:
  - Ngat Section moi va khoi dong lai so trang tu `Trang 1 / N`.
  - **Header**: Ten don vi mau xanh (`#003399`) + Ten Du an/Hang muc phia tren duong ke ngang mau **vang cam (`#FFC000`)**.
  - **Footer**: `BKTECHS || Dia chi | Lien he || Trang 1 / N` voi vach doi `||` mau vang cam.
  - **Typography & Mau sac**: Font `Times New Roman` (`12pt` body, `10.5pt` table). `Heading 1` (`1.`): `14pt` Bold IN HOA mau Xanh Navy (`#002060`); `Heading 2` (`1.1.`): `13pt` Bold mau Xanh lam sang (`#0070C0`); `Heading 3` (`1.1.1.`): `12pt` Bold Italic mau `#1F4E79`. Bang bieu co header nen `#002060` chu trang va dong **Ket luan / Kiem tra (`DAT / OK`)** to nen vang nhat (`#FFF2CC`).
- **Cau truc 6 Chuong Trong tam (Danh so truc tiep `1.`, `2.`, khong ghi chu `CHUONG`)**:
  1. `1. CO SO THIET KE, TIEU CHUAN AP DUNG & TAI LIEU THAM KHAO`
  2. `2. TONG QUAN HANG MUC & DAC TRUNG CO LY VAT LIEU`
  3. `3. TAI TRONG TAC DUNG & TO HOP TAI TRONG TINH TOAN`
  4. `4. MO HINH HOA & PHUONG PHAP PHAN TICH NOI LUC`
  5. `5. TINH TOAN & KIEM TRA KHA NANG CHIU LUC CAU KIEN DIEN HINH`
  6. `6. TONG HOP KET QUA KIEM TRA, KET LUAN & KIEN NGHI KY THUAT`

### 2. Bo Chuan 2: Phong cach `tvtk` (TVTK Da Hang Muc - 9 Chuong Co so + N Chuong Hang muc)

- **Ung dung**: Ho so Thiet ke Ky thuat (TKKT) hoac Ban ve Thi cong (BVTC) tong hop nhieu hang muc cong trinh trong cung mot du an.
- **Bo cuc Section 0 (Bia doi Phap ly + Muc luc)**:
  - **Trang 1 (Bia ngoai)**: Khung vien doi (`Double-line Box Border #002060`), thong tin cong ty TVTK o dau trang, ten cong trinh/hang muc o giua.
  - **Trang 2 (Bia lot Phap ly)**: Quoc hieu `CONG HOA XA HOI CHU NGHIA VIET NAM` va bang ky dong dau 2 cot can xung (`CHU DAU TU` - `DON VI TU VAN THIET KE`).
  - **Trang 3 (Muc luc tu dong)**: Truong `TOC \o "1-3"` 3 cap (`1`, `1.1`, `1.1.1`).
- **Bo cuc Section 1 (Noi dung chinh)**:
  - Font `Arial` (`11pt` body, `10pt` table), header bang to nen **Xanh lam nhat (`#B4C6E7`)** chu den dam, dong ket luan to nen xanh la nhat (`#E2EFDA`).
- **Cau truc `9 Chuong Co so Chung + N Chuong Phu luc Hang muc`**:
  - **Phan I (Chuong 1 den Chuong 9)**: `1 QUY CHUAN VA TIEU CHUAN THIET KE` -> `2 CAC TIEU CHI KIEM TRA ON DINH TONG THE` -> `3 DO VONG VA BE RONG VET NUT CHO PHEP` -> `4 DO LUN CUA MONG` -> `5 CAC YEU CAU VE CHONG THAM` -> `6 PHAN MEM PHAN TICH VA TINH TOAN` -> `7 TAI TRONG VA TO HOP TAI TRONG` -> `8 VAT LIEU KET CAU` -> `9 CHIEU DAY LOP BE TONG BAO VE`.
  - **Phan II (Chuong 10 tro di)**: Moi hang muc la 1 chuong `Heading 1` noi tiep (`10 PHU LUC TINH TOAN HANG MUC 01...`, `11 PHU LUC TINH TOAN HANG MUC 02...`), ben trong gom `.1 Mo hinh tinh toan`, `.2 Tai trong tac dung`, `.3 Tinh toan nen mong`, `.4 Tinh toan ket cau phan than`.

## Quy trinh Thuc thi (Workflow)

1. **Xac dinh Bo Chuan & Thu thap Du lieu**:
   - Xac dinh bo chuan nguoi dung yeu cau (`bktechs` la mac dinh, hoac `tvtk` khi lap ho so tong hop nhieu hang muc).
   - Thu thap thong so dau vao: ten du an, ten hang muc, chu dau tu, dia diem, cap do ben be tong (`B20`, `B25`, `B30`...), nhom cot thep (`CB240-T`, `CB300-V`, `CB400-V`...), so lieu dia chat va noi luc.

2. **Soan thao Noi dung Thuyet minh Step-by-Step (`.md`)**:
   - Moi buoc tinh toan bat buoc trinh bay day du: **Gia thiet / Thong so dau vao** -> **Cong thuc & Trich dan dieu khoan TCVN** -> **The so trung gian** -> **Ket qua & Don vi** -> **Ket luan danh gia (`DAT / OK` voi he so su dung $\eta \le 1.00$ hoac $SF \ge [SF]$)**.
   - Su dung `#` cho Heading 1, `##` cho Heading 2, `###` cho Heading 3 va bang Markdown chuan `| Cot 1 | Cot 2 |`.

3. **Chay Engine `docx_generator_v2.py` de Xuat File `.docx` (Ho tro Tich hop Phu luc & Dau dong Da cap)**:
   - Goi script `docx_generator_v2.py` de bien dich file `.md` sang `.docx`, co the tich hop truc tiep cac file phu luc qua `--appendices`:

```bash
python "g:/My Drive/Google AI Studio/.agents/skills/SKILL_PHULUC/docx_generator_v2.py" \
  --input draft_tmtt.md \
  --appendices templates/APPENDIX_PILE_FOUNDATION.md templates/APPENDIX_WATER_TANK.md \
  --output TMTT_KET_CAU_HOAN_CHINH.docx \
  --style bktechs \
  --project "Ten Du An" \
  --item "Thuyet minh Tinh toan Ket cau kem Phu luc" \
  --client "Ten Chu Dau Tu" \
  --location "Dia diem xay dung"
```

4. **Kiem tra Chuyen doi PDF & Ban giao**:
   - Chay `libreoffice --headless --convert-to pdf` hoac kiem tra file `.docx` truoc khi ban giao cho nguoi dung.

## Quy cach Trinh bay Dau dong & Ky hieu Ky thuat Chuan hoa

- **Quy cach Dau dong Da cap (Multi-level Indentation)**:
  - **Cap 1 (Gach dau dong `- ` hoac `– `)**: Thut le trai `0.63 cm`, hien thi dau gach ngang `– ` dam net.
  - **Cap 2 (Dau cong dau dong `+ ` hoac thut le 2 khoang trang)**: Thut le trai `1.27 cm`, hien thi dau cong `+ ` mau xanh Navy hoac chu dam.
  - **Cap 3 (Dau cham tron `• ` hoac thut le >= 4 khoang trang)**: Thut le trai `1.90 cm`.
  - **Khoan muc thu tu (`1. `, `1) `, `a) `, `b) `)**: Thut le trai `0.75 cm` / `1.27 cm`, giu nguyen so hoac chu cai.
- **Tu dong Chuan hoa Ky hieu Ky thuat (Engineering Symbol Normalizer)**:
  - Duong kinh cot thep: `%%c`, `Phi`, `phi`, `fi` truoc so -> Chuyen thanh `Φ` (VD: `Phi 20` -> `Φ20`).
  - Toan hoc so sanh: `<=`, `=<` -> `≤`; `>=`, `=>` -> `≥`; `+-` -> `±`; `x` hoac `*` giua cac kich thuoc (`200x400` -> `200 × 400`).
  - Don vi luy thua: `m2` -> `m²`, `m3` -> `m³`, `mm2` -> `mm²`, `cm2` -> `cm²`, `kN/m2` -> `kN/m²`, `daN/cm2` -> `daN/cm²`, `kNm` -> `kN.m`.
  - Ky tu Hy Lap hay dung: `eta` -> `η`, `sigma` -> `σ`, `tau` -> `τ`, `gamma` -> `γ`, `alpha` -> `α`, `beta` -> `β`, `delta` -> `δ`, `Delta` -> `Δ`.
  - Trang thai kiem tra: `[OK]`, `[DAT]` -> `[ĐẠT]`, `[FAIL]` -> `[KHÔNG ĐẠT]`.
- **Chuyen doi Cong thuc Toan LaTeX sang Native Word OMML (`<m:oMath>`)**: Tu dong nhan dien ca cong thuc doc lap `$$...$$` va cong thuc inline `$math$`, bien dich qua `pylatexenc` sang Math XML chuan Office Math hien thi sac net tren moi phien ban Word/WPS (ho tro phan so `\frac`, can `\sqrt`, chi so duoi/tren `_{...}`, `^{...}`, ky tu Hy Lap `\alpha, \beta, \sigma, \tau, \eta, \phi...`, toan tu `\le, \ge, \pm, \times, \cdot`).
- **Phan khu Section Break & Danh so Trang Doc lap cho tung Phu luc**: Moi phu luc khi truyen qua `--appendices` duoc tao Section Break (`WD_SECTION.NEW_PAGE`), Header/Footer duoc khoi tao rieng biet khong bi leak tu Thuyet minh chinh, va so trang duoc danh lai tu `Trang 1 / [SECTIONPAGES]`.
- **Lien ket Cheo Noi bo Tu dong (Auto Cross-Reference Bookmarks & Hyperlinks)**: Tu dong gan Bookmark `PHU_LUC_{n}` tai cac tieu de Phu luc; dong thoi tu dong nhan dien cac cau dan chieu "Xem chi tiet tai Phu luc 1", "Xem Phu luc 2", "theo Phu luc 3" trong thuyet minh de tao the `w:hyperlink w:anchor` mau xanh co gach chan de nguoi doc click nhay truc tiep toi phu luc tuong ung.
- **Bao ve Bang bieu Chong Rach trang (Table Layout Reinforcement)**: Khoi phuc do cao toi thieu Header Row `w:trHeight atLeast 360 twips` ket hop `w:tblHeader` lap lai tieu de tren moi trang va `w:cantSplit` cho toan bo cac hang du lieu de chong bi cat ngang khi in an.
- **Tinh chinh Typography & Kiem soat Dong Co don (Widow/Orphan Control)**: Line spacing `1.2`, gian cach doan chuan `space_before 2pt`, `space_after 4-6pt`, bat che do `w:widowControl` toan tai lieu, phong chu bang bieu `10pt` can giua theo chieu doc.
- **Trang Mục lục Tự động & Trực quan (Visual & Dynamic Auto-TOC Engine)**:
  - Tự động trích xuất toàn bộ cấu trúc phân cấp (Phần I, II, III; Chương 1, 2, 3; Mục con 1.1, 1.2; Phụ lục 1, 2...) từ nội dung Markdown và danh sách `--appendices`.
  - Định dạng chuẩn xuất bản: Dòng chấm dot leader căn lề phải tại `9072 twips` (`w:leader="dot"`), thụt lề cấp bậc rõ ràng (Phần: `0 cm`, Chương/Phụ lục: `0.4 cm`, Mục con: `0.85 cm`), số trang ước tính thông minh (`1, 2...` và `P1-1, P2-1...`).
  - Tích hợp Hyperlinks nội bộ (`w:hyperlink w:anchor="TOC_NAV_{n}"` / `w:anchor="PHU_LUC_{n}"`) cho phép click nhảy trực tiếp tới đề mục tương ứng.
  - Bảo lưu trường mã TOC động của Word (`TOC \o "1-3" \h \z \u`) và cờ `w:updateFields="true"`, cho phép người dùng nhấn F9 trong MS Word để cập nhật số trang vật lý chính xác bất kỳ lúc nào.
- **Khung Ghi chu / Luu y (`> text`)**: Tu dong tao khung trich dan vien trai mau Xanh Navy, nen xam sang `#F2F5F9`, chu nghiêng thanh lich.
- **Chen Hinh anh Markdown (`![caption](path)`)**: Tu dong nhung truc tiep anh vao file Word can giua trang kem dong caption in nghieng mau xam dam.

## Quy tac Bat buoc ve He thong Tieu chuan, Phan cap Cong trinh & Dia ky thuat (STANDARDS_LOCK v3.1.0)

1. **Phan biet 3 He thong Phan cap Phap ly - Ky thuat (Cam nham lan)**:
   - **Cap cong trinh (`Dac biet, Cap I, II, III, IV`)**: Xac dinh theo **Thong tu 06/2021/TT-BXD** va **Thong tu 34/2026/TT-BXD** (hieu luc tu 01/07/2026, thay the TT 06/2021 va TT 02/2025). Bat buoc xet dong thoi **6 tieu chi tai Muc 2.1.1 Bang 2 Phu luc II** va lay cap cao nhat: Chieu cao (`2.1.1.a`), So tang cao (`2.1.1.b`), **Tong dien tich san GFA (`2.1.1.c`: `> 30.000 m2` -> Cap I; `10.000 - 30.000 m2` -> Cap II)**, Nhip ket cau lon nhat (`2.1.1.d`), **Do sau ngam (`2.1.1.d`: tinh den mat tren san tang ham sau nhat; `6 - 18m` -> Cap II)**, **So tang ngam (`2.1.1.e`: `2 - 4 tang ham` -> Cap II; `1 tang ham` -> Cap III)**.
   - **Cap hau qua (`C1, C2, C3`) va Tuoi tho thiet ke (`Bang 1`)**: Xac dinh theo **QCVN 03:2022/BXD** (Muc 2.1 Bang 1 va Phu luc A). Tuyet doi khong dung QCVN 03:2022/BXD de phan cap I-IV. Nha cao tang, TTTM, chung cu thong thuong thuoc **Muc 3: Toi thieu 50 nam** (`C2/C3`), tru khi Nhiem vu thiet ke cua CĐT yeu cau nang len 100 nam.
   - **Cap phuc tap dieu kien ĐCCT (`Cap I, II, III`)**: Xac dinh theo **Dieu 3.5 va Phu luc 2 TCVN 4419:1987** (dan chieu tai Chu thich Dieu 5.2.4.1 TCVN 9363:2012; khong trich dan nham sang Dieu 4.2 TCVN 9363:2012).
2. **Quy dinh Khao sat Dia ky thuat Nha cao tang (`TCVN 9363:2012`)**:
   - **TKCS**: Khoang cach ho khoan **`50 m - 200 m`** (**Dieu 5.2.4.2**), chieu sau theo **Dieu 5.2.5 va Phu luc C**.
   - **TKKT**: Khoang cach ho khoan **`20 m - 30 m`** (luoi `20m x 20m` den `30m x 30m` cho ĐCCT Cap III), chieu sau theo **Dieu 5.3.6 va Phu luc D (Muc D.1, Bang D.1)** (khong ghi nham la Dieu 5.2.2 va Bang 1).
   - **Ty le Ho khoan Khong che**: Phai dat **toi thieu 1/3 (`>= 33.3%`) tong so diem tham do** (**Dieu 5.3.6.3 TCVN 9363:2012**).
3. **Phien ban Tieu chuan Bat buoc Cap nhat**:
   - Mong coc: **TCVN 10304:2025** (thay the TCVN 10304:2014).
   - Thi nghiem SPT: **TCVN 9351:2022** (thay the TCVN 9351:2012).
   - Danh gia an mon nuoc ngam doi voi BTCT: **TCVN 12041:2017** va **TCVN 9346:2012** (thay the `TCVN 3994:1985` da het hieu luc).
