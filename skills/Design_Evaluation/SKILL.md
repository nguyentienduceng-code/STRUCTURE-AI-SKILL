---
name: design-evaluation-audit
version: 3.4.0
updated: 2026-10-27
status: PRODUCTION_READY
description: Tham tra Thiet ke Ket cau va Da bo mon cap Chu tri (Ban Xay dung Cao cap - 7 Cong Kiem soat & 6 Module Chuyen sau v3.4.0, tich hop Module CAD_DEEP_READER doc/boc tach file .DWG/.DXF) theo TCVN 2737:2023, TCVN 5575:2024, TCVN 5574:2018, TCVN 9362:2012, TCVN 9386:2025, TT 34/2026/TT-BXD, QCVN 03:2022/BXD va QCVN 06:2022/BXD. Kich hoat khi nguoi dung yeu cau tham tra thiet ke, ra soat ban ve CAD (.dwg/.dxf) hoac PDF ket cau/kien truc, phan tich tai trong, to hop tai trong, duong truyen luc, kiem tra mo hinh ETABS/SAP2000, phat hanh phieu RFI/NCR, hoac xuat Bao cao Tham tra & Ho so Khoanh loi.
---

# Design Evaluation Audit - Quy Trinh Tham Tra Chuyen Sau 7 Cong & 6 Module (v3.4.0)

Thuc hien tham tra doc lap ho so thiet ke xay dung (Ban ve AutoCAD `.dwg/.dxf`, Ban ve PDF Vector, Thuyet minh tinh toan TMKC `.docx/.xlsx`, Mo hinh ETABS/SAP2000 va Du toan/Bao gia) theo Quy trinh 7 Cong Kiem soat Khep kin (7-Gate Interlocked Pipeline v3.4.0) cua Ban Xay dung Cao cap.

## Khi nao su dung Skill nay

- Khi nguoi dung yeu cau tham tra, kiem tra, audit, hoac phan bien ho so thiet ke ket cau (nha xuong thep tien che PEB, nha cong nghiep, cong trinh ngam, be nuoc PCCC, nha cao tang, nen mong).
- Khi ho so dau vao co chua ban ve CAD goc (`.dwg` / `.dxf`) can boc tach Xref, phang hoa Nested/Dynamic Block (`*U...`) ve WCS, giai ma font `.shx` / `TCVN3` / `VNI` sang UTF-8 va phat hien sua so kich thuoc gia (Dimension Override) qua `scripts/cad_deep_reader.py`.
- Khi can phan tich chuyen sau Tai trong (TCVN 2737:2023), To hop tai trong (ULS/SLS, gio boc nguoc, day noi), So do tinh, Lien ket bu long/duong han va Duong truyen luc 3D.
- Khi can doi soat tu dong 4 chieu giua Ban ve Kien truc, Mat bang Ket cau, Mat cat/Chi tiet/Tag thep va Thuyet minh tinh toan, xuat Bao cao Tham tra va Ho so Khoanh loi chuan 1 Phieu / 1 Trang A4 (`scripts/generate_clash_dossier.py`).

## Phan Cong Chi Tiet Tung Nhiem Vu Theo 6 Module (Task-Level Specification v3.4.0)

### Module 1: `Design_Evaluation` (Master Orchestrator - Gate 0 & Gate 6)

- **Task 1.1 (Boc tach Quy hoach)**: Doc Bang can bang dat dai tren Tong mat bang, tach biet dien tich khu dat toan khu, dien tich hien huu (GD I) va dien tich san xay moi (GFA) cua giai doan dang cap phep (GD II).
- **Task 1.2 (Phan cap Da tieu chi)**: Phan cap cong trinh theo Thong tu 34/2026/TT-BXD dua tren $\max(\text{GFA}, L_{\max}, H)$ va xac dinh Cap hau qua ($C_1, C_2, C_3$), he so $\gamma_n$ theo QCVN 03:2022/BXD.
- **Task 1.3 (Khoa Tieu chuan & 02 Chot chan Phap ly Hold Points)**:
  1. Kiem tra su ton tai cua Bao cao Khao sat Dia chat Cong trinh (DCCT) co dau phap nhan (cam gia dinh suc chiu tai quy uoc $R_{tc}$ khong can cu).
  2. Kiem tra thuyet minh Bac chiu lua va giai phap bao ve chiu lua ket cau thep/BTCT theo QCVN 06:2022/BXD.
- **Task 1.4 (Quan tri 7 Stage Gates)**: Kiem soat trang thai mo/khoa cua tung Cong tren `DUAL_AGENT_BUS.json`, cam nhay coc qua buoc xuat bao cao khi chua hoan thanh Kiem toan Tai trong - To hop - Duong truyen luc - Doi soat 4 chieu.

### Module 2: `SKILL_VERIFY` (7-Layer Deep Verification Engine - Gate 1 & Gate 5)

Doc chi tiet trong `references/SKILL_VERIFY.md` va chay `scripts/cad_deep_reader.py` + `scripts/drawing_calc_crosscheck.py`:

- **Task 2.1 (`EMF Deep Parser`)**: Giai nen `word/media/image*.emf` trong toan bo file `.docx` thuyet minh, trich xuat 100% ban ghi nhi phan `EMR_EXTTEXTOUTW` (UTF-16LE) de doc toan bo cong thuc va so lieu goc tu Excel / Young Steel / Ketcausoft.
- **Task 2.2 (`CAD_DEEP_READER Engine` - `scripts/cad_deep_reader.py`)**:
  - **Stage 1 (Multi-Engine DWG Bridge & Xref Binder)**: Dieu phoi `accoreconsole.exe` (+ AutoLISP `-XREF _Bind *`) hoac `ODAFileConverter` + `ezdxf` de chuyen doi `.dwg -> .dxf` R2018.
  - **Stage 2 (4x4 WCS Matrix Flattener)**: Nhan ma tran dong nhat $4\times 4$ phan ra Nested Blocks & Anonymous Dynamic Blocks (`*U123`) kem thuoc tinh `ATTRIB` ve He toa do The gioi (WCS).
  - **Stage 3 (Vietnamese SHX/TCVN3/VNI Decoder)**: Chuyen doi 100% chuoi byte TCVN3 (`.VnTime`, `tc.shx`), VNI (`VNI-Helve`, `vn_vni.shx`), va ma AutoCAD (`%%c -> Ø`, `%%d -> °`, `%%p -> ±`, `\U+XXXX`) sang Unicode UTF-8 theo tu (Token-aware); khoi phuc chu SHX bi pha khoi (`TXTEXP`) qua do thi net (`Stroke-Graph`).
  - **Stage 4 & 5 (Semantic Layer & Fake-Dim Detector)**: Phan loai Layer ve 7 nhom chuan (`GRID_AXIS`, `FOUNDATION`, `COLUMN_WALL`, `BEAM_SLAB`, `STEEL_PURLIN_BRACE`, `REBAR_TAG`, `DIMENSION_TEXT`); kiem tra cheo `actual_measurement` (DXF group 42) vs `dim_text` (DXF group 1) de bat song loi sua so Dim gia (`|dim_text - actual| > 2%`).
- **Task 2.3 (`Formula & Cell Audit`)**: Quet tu dong chuoi `#VALUE!`, `#REF!`, `#DIV/0!`, `#NAME?` trong moi bang EMF/DOCX/XLSX.
- **Task 2.4 (`ETABS Reaction Tracer` & `Rebar Area Calculator`)**: Doi soat bang xuat `Joint Reactions` cua ETABS voi bang tinh mong; quy doi moi tag thep (`nØd`, `ØdaS`) ra dien tich $A_{s,drawing}$ ($\text{cm}^2$) va kiem tra $A_{s,drawing} \ge A_{s,tt}$.

### Module 3: `SKILLKC` (Principal Structural Mechanics Auditor - Gate 2, Gate 3 & Gate 4)

Doc chi tiet trong `references/SKILLKC.md`:

- **Task 3.1 (Tham tra Phan tich Tai trong - Gate 2)**:
  - Tach $D_{permanent}$ va $D_{Solar}$; kiem tra hoat tai mai $\ge 0.30\text{ kN/m}^2$ ($\gamma_f = 1.30$); kiem tra hoat tai xe chua chay ($20 \div 30\text{ kPa}$) tren nap be ngam; truy vet 100% tai gian thao tac treo / tran M&E (`KC-12..15`) va kiem tra **dong nuoc mai / mang xoi biên (Ponding Instability)** theo TCVN 2737:2023 Muc 9.
  - Kiem tra tai trong gio TCVN 2737:2023: he so giat $G_f$ theo Phu luc E, ap luc khi dong trong nha $c_i \in [-0.3, +0.2]$ (hoac $+0.6$ khi bung cua), va kiem toan xa go duoi gio boc nguoc (`Up`).
- **Task 3.2 (Tham tra To hop Tai trong - Gate 3)**:
  - Khoa cung $\gamma_{f,\text{tinh tai giu}} = 0.90$ va loai tru tai Solar chua lap dat khi tinh gio boc / lat mong / day noi ($K_{dn} \ge 1.15$).
  - Cam gop nuoc trong be va dat ngoai be tu triet tieu nhau; bat buoc xet to hop Be rong bao tri + Day dat & Nuoc ngam + Xe PCCC.
- **Task 3.3 (Phan tich Duong truyen luc 3D, Lien ket Bu long/Duong han & Do ben Moi truong - Gate 4)**:
  - Kiem tra tuong thich dieu kien bien `Chan ngam / Chan khop`, xoay mong $\sigma_{\min} < 0$, $L_{ef}$ canh duoi chiu nen (`Flange Stay`), va do manh ban bung ($\bar{\lambda}_w, \bar{\lambda}_{uw}$).
  - Kiem toan chi tiet lien ket mat bich bu long cuong do cao tai nach khung, dinh keo va dinh cot giua (`CT3-K1, CT5-K1, CT6-K1`), kiem tra ban ghep canh tren chiu keo, hieu ung don bay (Prying action), chieu cao duong han $h_f$, que han tuong thich thep `Q355B` (`E70XX`) va cap do chong an mon hoa chat/dung moi (`C3-C4` theo TCVN 12041:2017 & TCVN 9346:2012).

### Module 4: `SKILL_BIM_COORDINATION` (4-Tier Spatial, CAD & Blueprint Auditor - Gate 1 & Gate 5)

Doc chi tiet trong `references/SKILL_BIM_COORDINATION.md`:

- **Task 4.1 (Dong bo Luoi truc & Ranh dat)**: Doi chieu truc $X, Y$ giua TMB - Kien truc - MB mong - Chi tiet mong (`KC-02, KC-03`), phat hien truc ma (`X1-X14`), lech ten truc (`Y2` vs `Y4`) va dai mong nho ra ngoai ranh dat.
- **Task 4.2 (Doi soat Noi bo Ban ve Ket cau & CAD Deep Reader)**: Do do lech tam co cot $e_0$ tu toa do WCS tren MB vs MC; dem so luong cau kien tren MB vs Tieu de chi tiet (`5 cot/5 dam` vs `3 cot/3 dam`); doi chieu tag thep giua MB va MC (`Ø10a200` vs `Ø10a150`); bat loi sua so Dim gia (`check_dimension_override`).
- **Task 4.3 (Tinh khong Thong thuy 3D)**: Kiem tra cao do day gian treo (`+6.000m`, thanh xien ha xuong `+5.300m`) voi xe nang va tuyen ong Sprinkler.

### Module 5: `SKILL_RFI` (Technical Enforcement - Gate 6)

Doc chi tiet trong `references/SKILL_RFI.md`:

- **Task 5.1 & 5.2**: Phan loai `CRITICAL (Hold Point -> NCR)`, `MAJOR (RFI)` va `MINOR (RFI)`; xuat ma dinh danh chuan `RFI-DES-YYYYMMDD-NNN` va `NCR-DES-YYYYMMDD-NNN` voi day du 6 truong thong tin dinh luong va che tai tam dung nghiem thu / giu thanh toan theo Nghi dinh 175/2024/ND-CP & Nghi dinh 37/2015/ND-CP.

### Module 6: `SKILL_REPORT` (Corporate Engineering Publisher v3.3.0 - Gate 6)

Doc chi tiet trong `references/SKILL_REPORT.md` va chay `scripts/generate_clash_dossier.py`:

- **Task 6.1 & 6.2**: Ve bo bieu do dinh luong 300 DPI (`Noto Serif / Liberation Serif` day du dau tieng Viet) va xuat Bao cao Tham tra `.docx` chuan Ban Xay dung Cao cap (`Body >= 11pt`, `Table >= 10pt`, `w:cantSplit`, `w:tblHeader`).
- **Task 6.3 (Xuat Ho so Khoanh Loi Xung Dot Ban ve Chuan v3.3.0 - `scripts/generate_clash_dossier.py`)**:
  - Dong bo 100% bang mau voi Form Thuyet minh chuan: Header ngang Xanh Navy (`#1B365D`) chu trang; cot nhan ben trai (6 muc) to nen Xanh Bang nhat (`#EAF0F6`) chu Navy dam (`#1B365D`); badge muc do tram (`#991B1B` Critical, `#B45309` Major, `#1E40AF` Minor).
  - Tu dong lam sach anh PNG (`sanitize_and_reheader_redline_image`): cat bo banner den va hop chu 4 dong trung lap trong anh PNG, ve thanh tieu de khung ban ve bang phong Serif day du dau tieng Viet (`LiberationSerif-Bold`) tu dong co vua khung (0% tran chu).
  - Khoa cung bo cuc **"1 Phieu = 1 Trang A4 Khep Kin"** (`max_h_cm <= 7.6 cm`, 0 dong mo coi rot sang trang sau, 0 trang trang) va khoa nguon du lieu don nhat (`SSOT Anti-Drift Lock`).
