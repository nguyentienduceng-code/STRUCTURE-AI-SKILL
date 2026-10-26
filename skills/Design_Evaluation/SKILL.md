---
name: design-evaluation-audit
description: Tham tra Thiet ke Ket cau va Da bo mon cap Chu tri (Ban Xay dung Cao cap - 7 Cong Kiem soat & 6 Module Chuyen sau v3.3.0) theo TCVN 2737:2023, TCVN 5575:2024, TCVN 5574:2018, TCVN 9362:2012, TCVN 9386:2025, TT 34/2026/TT-BXD, QCVN 03:2022/BXD va QCVN 06:2022/BXD. Kich hoat khi nguoi dung yeu cau tham tra thiet ke, ra soat ban ve ket cau/kien truc, phan tich tai trong, to hop tai trong, duong truyen luc, kiem tra mo hinh ETABS/SAP2000, phat hanh phieu RFI/NCR, hoac xuat Bao cao Tham tra Ket cau.
---

# Design Evaluation Audit - Quy Trinh Tham Tra Chuyen Sau 7 Cong & 6 Module (v3.3.0)

Thuc hien tham tra doc lap ho so thiet ke xay dung (Ban ve Kien truc, Ban ve Ket cau, Thuyet minh tinh toan TMKC, Mo hinh ETABS/SAP2000 va Du toan/Bao gia) theo Quy trinh 7 Cong Kiem soat Khep kin (7-Gate Interlocked Pipeline) va Phan cong Chi tiet Tung Nhiem vu (Task-Level Specification v3.3.0) cua Ban Xay dung Cao cap.

## Khi nao su dung Skill nay

- Khi nguoi dung yeu cau tham tra, kiem tra, audit, hoac phan bien ho so thiet ke ket cau (nha xuong thep tien che PEB, nha cong nghiep, cong trinh ngam, be nuoc PCCC, nha cao tang, nen mong).
- Khi can phan tich chuyen sau Tai trong (TCVN 2737:2023), To hop tai trong (ULS/SLS, gio boc nguoc, day noi), So do tinh va Duong truyen luc 3D.
- Khi can doi soat tu dong 4 chieu giua Ban ve Kien truc, Mat bang Ket cau, Mat cat/Chi tiet/Tag thep va Thuyet minh tinh toan.
- Khi can lap danh muc Phieu Yeu cau Lam ro (`RFI-DES-YYYYMMDD-NNN`), Bien ban Khong phu hop (`NCR-DES-YYYYMMDD-NNN`) va xuat Bao cao Tham tra `.docx` chuan Corporate.

## Phan Cong Chi Tiet Tung Nhiem Vu Theo 6 Module (Task-Level Specification v3.3.0)

### Module 1: `Design_Evaluation` (Master Orchestrator - Gate 0 & Gate 6)

- **Task 1.1 (Boc tach Quy hoach)**: Doc Bang can bang dat dai tren Tong mat bang, tach biet dien tich khu dat toan khu, dien tich hien huu (GD I) va dien tich san xay moi (GFA) cua giai doan dang cap phep (GD II).
- **Task 1.2 (Phan cap Da tieu chi)**: Phan cap cong trinh theo Thong tu 34/2026/TT-BXD dua tren $\max(	ext{GFA}, L_{max}, H)$ va xac dinh Cap hau qua ($C_1, C_2, C_3$), he so $\gamma_n$ theo QCVN 03:2022/BXD.
- **Task 1.3 (Khoa Tieu chuan & 02 Chot chan Phap ly Hold Points)**:
  1. Kiem tra su ton tai cua Bao cao Khao sat Dia chat Cong trinh (DCCT) co dau phap nhan (cam gia dinh suc chiu tai quy uoc $R_{tc}$ khong can cu).
  2. Kiem tra thuyet minh Bac chiu lua va giai phap bao ve chiu lua ket cau thep/BTCT theo QCVN 06:2022/BXD.
- **Task 1.4 (Quan tri 7 Stage Gates)**: Kiem soat trang thai mo/khoa cua tung Cong tren `DUAL_AGENT_BUS.json`, cam nhay coc qua buoc xuat bao cao khi chua hoan thanh Kiem toan Tai trong - To hop - Duong truyen luc - Doi soat 4 chieu.

### Module 2: `SKILL_VERIFY` (6-Layer Deep Verification Engine - Gate 1 & Gate 5)

Doc chi tiet trong `references/SKILL_VERIFY.md` va chay `scripts/drawing_calc_crosscheck.py`:

- **Task 2.1 (`EMF Deep Parser`)**: Giai nen `word/media/image*.emf` trong toan bo file `.docx` thuyet minh, trich xuat 100% ban ghi nhi phan `EMR_EXTTEXTOUTW` (UTF-16LE) de doc toan bo cong thuc va so lieu goc tu Excel / Young Steel / Ketcausoft.
- **Task 2.2 (`Formula & Cell Audit`)**: Quet tu dong chuoi `#VALUE!`, `#REF!`, `#DIV/0!`, `#NAME?` trong moi bang EMF/DOCX/XLSX; kiem tra cac o gop (`MergedCell`) lam dut lien ket cong thuc giua cac sheet va doi chieu so tien bang so - bang chu.
- **Task 2.3 (`ETABS Reaction Tracer`)**: Doi soat truc tiep bang xuat `Joint Reactions` cua ETABS (toa do nut chan cot giua vs cot bien) voi gia tri $N, M, Q$ nhap vao bang tinh mong.
- **Task 2.4 (`Rebar Area Calculator`)**: Quy doi moi tag thep tren ban ve (`nØd`, `ØdaS`) ra dien tich $A_{s,drawing}$ ($	ext{cm}^2$) va kiem tra dieu kien $A_{s,drawing} \ge A_{s,tt}$.

### Module 3: `SKILLKC` (Principal Structural Mechanics Auditor - Gate 2, Gate 3 & Gate 4)

Doc chi tiet trong `references/SKILLKC.md`:

- **Task 3.1 (Tham tra Phan tich Tai trong - Gate 2)**:
  - *Tinh tai & Hoat tai*: Tach $D_{permanent}$ va $D_{Solar}$; kiem tra hoat tai mai $\ge 0.30	ext{ kN/m}^2$ ($\gamma_f = 1.30$); kiem tra hoat tai xe chua chay ($20 \div 30	ext{ kPa}$ hoac tai truc $100 \div 120	ext{ kN}$) tren nap be ngam; truy vet 100% tai gian thao tac treo / tran M&E / cau truc tren ban ve (`KC-12..15`).
  - *Tai trong Gio (TCVN 2737:2023)*: Kiem tra $W_0, k(z_e)$; tinh he so hieu ung giat $G_f$ theo Muc 10.2.7 va Phu luc E (voi nha thep do can diu $\zeta = 0.02$, bac bo cong thuc tu che $G_f = 0.85+h/1010$); bat buoc to hop $c_e$ voi **ap luc gio ben trong nha $c_i \in [-0.3, +0.2]$ (hoac toi $+0.6$ khi bung cua don gio)**; bat buoc kiem toan xa go duoi tai gio boc nguoc (`Up`, cam nhap `Gio = 0`).
  - *Ap luc Dat/Nuoc ngam & Dong dat*: Tinh ap luc dat tinh $K_0 = 1-\sinarphi$ tach roi ap luc thuy tinh nuoc ngam; kiem tra khang chan theo TCVN 9386:2025.
- **Task 3.2 (Tham tra To hop Tai trong - Gate 3)**:
  - *To hop Dao dau / Gio boc / Lat mong / Day noi*: Khoa cung $\gamma_{f,	ext{tinh tai giu}} = 0.90$ va **loai tru tai Solar chua lap dat** ($	ext{COMB}_{Uplift} = 0.9 D_{perm} + 1.0 W_{boc}$).
  - *To hop Be ngam*: Cam gop nuoc trong be (`HTN`) va dat ngoai be (`TTĐ`) tu triet tieu nhau; bat buoc xet to hop **Be rong bao tri + Day dat & Nuoc ngam + Xe PCCC chay tren nap**.
  - *To hop SLS*: Xet tung huong gio tieu chuan ($\gamma_f = 1.0$) rieng biet, khong gop ham `ENVE`.
- **Task 3.3 (Phan tich Duong truyen luc 3D & So do tinh - Gate 4)**:
  - Kiem tra tuong thich dieu kien bien `Chan ngam / Chan khop` voi do cung ban de va su tach roi day mong ($\sigma_{min} < 0$ gay xoay mong $	heta$ lam vot do vong dau cong son; khung manh $\mu_x > 2.0$ phai xet bac 2 $P-\Delta$).
  - Kiem tra chieu dai tu do thuc te $L_{ef}$ cua canh duoi chiu nen tai vung mo men am nach keo (co thanh chong canh `Flange Stay` tren ban ve khong?).
  - Kiem tra do manh ban bung ($ar{\lambda}_w, ar{\lambda}_{uw}$) de bat buoc ve suon ngang va **suon doc**; kiem tra duong truyen luc doc nha tai truc cot giua (`Truc Y4`) va kiem toan day noi Archimedes ($K_{dn} \ge 1.15$).

### Module 4: `SKILL_BIM_COORDINATION` (3-Tier Spatial & Blueprint Auditor - Gate 1 & Gate 5)

Doc chi tiet trong `references/SKILL_BIM_COORDINATION.md`:

- **Task 4.1 (Dong bo Luoi truc & Ranh dat)**: Doi chieu truc $X, Y$ giua TMB - Kien truc - MB mong - Chi tiet mong (`KC-02, KC-03`), phat hien truc ma (`X1-X14`), lech ten truc (`Y2` vs `Y4`) va dai mong nho ra ngoai ranh dat.
- **Task 4.2 (Doi soat Noi bo Ban ve Ket cau: MB - MC - Chi tiet - Tag thep)**: Do do lech tam co cot $e_0$ tren MB vs MC; dem so luong cau kien tren MB vs Tieu de chi tiet (`5 cot/5 dam` vs `3 cot/3 dam`); doi chieu tag thep giua MB va MC tren cung to ban ve (`Ø10a200` vs `Ø10a150`); kiem tra chi tiet bu long neo ve thua nhieu duong kinh (`D20` va `D24`).
- **Task 4.3 (Tinh khong Thong thuy 3D)**: Kiem tra cao do day gian treo (`+6.000m`, thanh xien ha xuong `+5.300m`) voi xe nang va tuyen ong Sprinkler.

### Module 5: `SKILL_RFI` (Technical Enforcement - Gate 6)

Doc chi tiet trong `references/SKILL_RFI.md`:

- **Task 5.1 & 5.2**: Phan loai `CRITICAL (Hold Point -> NCR)`, `MAJOR (RFI)` va `MINOR (RFI)`; xuat ma dinh danh chuan `RFI-DES-YYYYMMDD-NNN` va `NCR-DES-YYYYMMDD-NNN` voi day du 6 truong thong tin dinh luong.

### Module 6: `SKILL_REPORT` (Corporate Engineering Publisher - Gate 6)

Doc chi tiet trong `references/SKILL_REPORT.md`:

- **Task 6.1 & 6.2**: Ve bo bieu do dinh luong 300 DPI (`matplotlib`) va xuat Bao cao Tham tra `.docx` chuan Ban Xay dung Cao cap (`Body >= 11pt`, `Table >= 10pt`, `w:cantSplit`, `w:tblHeader`).

  - **Task 6.3 (Xuat Ho so Khoanh Loi Xung Dot Ban ve Chuan v3.3.0 - `scripts/generate_clash_dossier.py`)**:
    + Dong bo 100% bang mau voi Form Thuyet minh chuan: Header ngang Xanh Navy (`#1B365D`) chu trang; cot nhan ben trai (6 muc) to nen Xanh Bang nhat (`#EAF0F6`) chu Navy dam (`#1B365D`); badge muc do tram (`#991B1B` Critical, `#B45309` Major, `#1E40AF` Minor).
    + Tu dong lam sach anh PNG (`sanitize_and_reheader_redline_image`): cat bo banner den va hop chu 4 dong trung lap trong anh PNG, ve thanh tieu de khung ban ve bang phong Serif day du dau tieng Viet (`LiberationSerif-Bold`) tu dong co vua khung (0% tran chu).
    + Khoa cung bo cuc **"1 Phieu = 1 Trang A4 Khep Kin"** (`max_h_cm <= 7.6 cm`, 0 dong mo coi rot sang trang sau, 0 trang trang) va khoa nguon du lieu don nhat (`SSOT Anti-Drift Lock`) giua Bang Ma tran, Bang Danh muc (Sentence Case) va Bang Chi tiet 6 muc.
