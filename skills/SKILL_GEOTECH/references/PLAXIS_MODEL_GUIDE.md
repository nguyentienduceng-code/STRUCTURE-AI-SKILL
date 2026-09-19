# HUONG DAN CHON MO HINH & NHAP LIEU PLAXIS

> **Pham vi:** Huong dan chi tiet cach chon mo hinh dat phu hop va nhap thong so vao Plaxis 2D/3D.
> **Phien ban:** Plaxis 2D AE / Plaxis 3D

---

## 1. SO SANH CAC MO HINH DAT

### 1.1. Bang tong hop

```
+------------------+-------------+-------------+-------------+-----------------+
| Tieu chi         | Mohr-      | Hardening   | Soft Soil   | Soft Soil       |
|                  | Coulomb     | Soil (HS)   | Creep (SSC)| (SS)           |
+------------------+-------------+-------------+-------------+-----------------+
| So thong so      | 5          | 9           | 11         | 8               |
| Ung xu do tai   | Khong      | Co          | Co         | Co             |
| Ung xu co ket   | Khong      | Khong       | Co         | Co             |
| Tu bien         | Khong      | Khong       | Co         | Khong          |
| Non-linear       | Khong      | Co          | Co         | Co             |
| Thoi gian       | Tinh       | Tinh        | Theo TG    | Tinh           |
+------------------+-------------+-------------+-------------+-----------------+
| Do phuc tap      | Thap       | Trung binh  | Cao        | Trung binh      |
| Chi phi tinh toan| Thap       | Trung binh  | Cao        | Trung binh      |
+------------------+-------------+-------------+-------------+-----------------+
```

### 1.2. Khi nao dung mo hinh nao

#### Mohr-Coulomb (MC) - Don gian
**Nen dung khi:**
- Phan tich so bo, uoc luong nhanh
- Bai toan on dinh mai doc don gian
- Lop dat san lap, dat cung (stiff)
- Khi khong co du so lieu Lab Test

**Thong so can nhap:**
```
+-----------------------------------------------------+
| PROPERTIES - Mohr-Coulomb                           |
+-----------------------------------------------------+
| General                                            |
|   Material type:    Drained / Undrained A / B      |
|                                                     |
| Parameters                                         |
|   gamma_unsat:    [kN/m3]   <- Dung trong tu nhien|
|   gamma_sat:      [kN/m3]   <- Dung trong bao hoa |
|   E_ref:          [kN/m2]   <- Module dan hoi     |
|   nu:             [-]         <- He so Poisson       |
|                                                     |
| Strength                                          |
|   c:              [kN/m2]   <- Luc dinh           |
|   phi:            [do]       <- Goc ma sat trong   |
|   psi:            [do]       <- Goc no (thuong 0) |
|                                                     |
| Hydraulic                                         |
|   kx:             [m/day]   <- He so tham ngang   |
|   ky:             [m/day]   <- He so tham dung    |
+-----------------------------------------------------+
```

#### Hardening Soil (HS) - Tieu chuan cho ho dao sau
**Nen dung khi:**
- **BAT BUOC** cho ho dao sau tai TP.HCM
- Can du bao chuyen vi tuong vay
- Can mo phong ung xu do tai - gia tai lai
- Phan tich tuong tac dat - ket cau

**Thong so can nhap:**
```
+-----------------------------------------------------+
| PROPERTIES - Hardening Soil                          |
+-----------------------------------------------------+
| General                                            |
|   Material type:    Drained / Undrained B          |
|                                                     |
| Soil weight                                      |
|   gamma_unsat:    [kN/m3]                        |
|   gamma_sat:      [kN/m3]                        |
|                                                     |
| Basic parameters (Parameters tab)                  |
|   E50_ref:        [kN/m2]   <- Module cat tuyen  |
|   Eoed_ref:       [kN/m2]   <- Module oedometer |
|   Eur_ref:        [kN/m2]   <- Module do tai     |
|   m:              [-]         <- He so mu          |
|                                                     |
| Advanced (Strength tab)                            |
|   c:              [kN/m2]                        |
|   phi:            [do]                            |
|   psi:            [do]      <- psi = 0 cho dat mem|
|                                                     |
| Advanced (Flow tab)                               |
|   kx:             [m/day]                        |
|   ky:             [m/day]                        |
|                                                     |
| Advanced (Interfaces tab)                          |
|   R_inter:         [-]       <- He so tuong tac    |
+-----------------------------------------------------+
```

**Luu y quan trong cho HS:**
1. `pref = 100 kN/m2` la mac dinh, khong can thay doi
2. `nu_ur = 0.2` la mac dinh cho unloading-reloading
3. Quan he: `Eoed <= E50 <= Eur`

#### Soft Soil Creep (SSC) - Cho dat yeu
**Nen dung khi:**
- Lop set mem, bun, than bun
- Can phan tich lun theo thoi gian (co ket + tu bien)
- Thoi gian thi cong keo dai
- Can du bao lun sau thi cong

**Thong so can nhap:**
```
+-----------------------------------------------------+
| PROPERTIES - Soft Soil Creep                         |
+-----------------------------------------------------+
| General                                            |
|   Material type:    Undrained B                    |
|   Set type:        Standard / Custom K0NC         |
|                                                     |
| Soil weight                                      |
|   gamma_unsat:    [kN/m3]                        |
|   gamma_sat:      [kN/m3]                        |
|                                                     |
| Parameters                                       |
|   lambda*:         [-]      <- Chi so nen         |
|   kappa*:          [-]      <- Chi so no          |
|   mu*:            [-]      <- Chi so tu bien     |
|   v_init:          [-]      <- He so Poisson ban dau|
|                                                     |
| Advanced (Strength)                              |
|   c:              [kN/m2]                        |
|   phi:            [do]                            |
|   OCR:            [-]      <- Ty so qua co ket   |
|   POP:            [kN/m2]  <- Pre-overburden    |
|                                                     |
| Advanced (Flow)                                  |
|   kx:             [m/day]                        |
|   ky:             [m/day]                        |
+-----------------------------------------------------+
```

---

## 2. HUONG DAN NHAP LIEU CHI TIET

### 2.1. Nhap vat lieu dat (Material Sets)

#### Buoc 1: Tao Material Set moi
```
Plaxis 2D:
    -> Materials -> Soil -> New Soil Material Set
    
Plaxis 3D:
    -> Materials -> Soils -> New Soil
```

#### Buoc 2: Nhap thong so theo checklist

**Cho Hardening Soil Model:**

| Tab | Truong | Cach xac dinh | Ghi chu |
|-----|--------|---------------|---------|
| General | Material type | Theo loai dat va dieu kien | Drained cho cat, Undrained B cho set |
| Soil weight | gamma_unsat | Tu Lab Test hoac SPT correlation | |
| Soil weight | gamma_sat | Tu Lab Test hoac SPT correlation | gamma_sat = gamma_unsat + delta_gamma_w x S |
| Parameters | E50_ref | Tu SPT correlation: alpha x N hoac beta x Su | **Quan trong nhat** |
| Parameters | Eoed_ref | = E50_ref hoac tu Oedometer | |
| Parameters | Eur_ref | = 3 x E50_ref (mac dinh) | |
| Parameters | m | Tra bang theo loai dat | |
| Strength | c | Tu CU triaxial hoac SPT correlation | |
| Strength | phi | Tu CU triaxial hoac SPT correlation | |
| Strength | psi | = phi' - 30 do hoac = 0 | |
| Flow | kx, ky | Tu Lab Test hoac tra bang kinh nghiem | |
| Interfaces | R_inter | Theo CIRIA C760 | |

### 2.2. Nhap ket cau (Structural Elements)

#### Tuong vay (Diaphragm Wall) - Plate Element
```
1. Tao Plate:
   -> Structures -> Plate -> Draw

2. Thiet lap thong so trong Plate Properties:
   
   +-----------------------------------------------------+
   | PLATE PROPERTIES                                   |
   +-----------------------------------------------------+
   | General                                           |
   |   Type:        Elastic / Elasto-plastic          |
   |                                                     |
   | Mechanical                                       |
   |   EA:          [kN/m]     <- Do cung doc truc  |
   |   EI:          [kNm2/m]   <- Do cung uon       |
   |   w:           [kN/m/m]   <- Trong luong ban than |
   |   nu:          [-]          <- He so Poisson (=0.15)|
   |                                                     |
   |   ** Chu y: EA = Ec x A, EI = Ec x I x beta_crack ** |
   +-----------------------------------------------------+
```

**Cach tinh EA, EI:**
```
EA = Ec x (b x h)

EI = Ec x (b x h^3 / 12) x beta_crack

Trong do:
- Ec  = 30,000,000 kN/m2 (B25) hoac tinh theo TCVN
- b   = 1.0 m (tinh cho 1m chieu dai)
- h   = Be day tuong (VD: 0.8m)
- beta_crack = 0.6 (he so nut khuyen nghi)

Vi du: Tuong B25 day 0.8m
    Ec = 30,000,000 kN/m2
    EA = 30,000,000 x 1.0 x 0.8 = 24,000,000 kN/m
    EI = 30,000,000 x 1.0 x 0.8^3 / 12 x 0.6
       = 30,000,000 x 0.512 / 12 x 0.6
       = 768,000 kNm2/m
```

#### Cu Larsen - Plate Element
```
1. Chon tu thu vien hoac nhap thu cong:
   -> Structures -> Plate -> Input

2. Nhap thong so tu catalog:
   
   SP III w (Hyundai Steel):
     EA = 2.1E+08 x 0.02425 = 5,092,500 kN/m
     EI = 2.1E+08 x 3.86E-04 = 81,060 kNm2/m
```

#### Thanh chong (Strut) - Node-to-Node Anchor
```
1. Tao Anchor:
   -> Structures -> Anchor -> Node-to-Node

2. Thiet lap thong so:
   
   +-----------------------------------------------------+
   | ANCHOR PROPERTIES (Node-to-Node)                    |
   +-----------------------------------------------------+
   | General                                           |
   |   Type:        Fixed-end anchor                  |
   |                                                     |
   | Geometry                                        |
   |   Ls (spacing): [m]     <- Khoang cach giua strut |
   |                                                     |
   | Spring type:   Elastic                            |
   |   EA:            [kN]     <- Do cung doc truc  |
   +-----------------------------------------------------+

Cach tinh EA cho strut:
    EA = Es x As
    
    Vi du: H300 voi khoang cach 6m
        As = 119.8 cm2 = 0.01198 m2
        EA = 210,000,000 x 0.01198 = 2,515,800 kN
        EA/m = 2,515,800 / 6 = 419,300 kN/m
```

#### Neo (Anchor) - Fixed-end Anchor
```
1. Tao Fixed-end Anchor:
   -> Structures -> Anchor -> Fixed-end Anchor

2. Thong so:
   - Chieu dai tu do (Lf): Khoang cach tu tuong den diem neo co dinh
   - Chieu dai co dinh (Lb): Chieu dai neo trong dat neo
   - EA: Do cung cap neo
   - Spacing: Khoang cach giua cac neo
```

### 2.3. Thiet lap Interface (Tuong tac dat - ket cau)

```
1. Tao Interface:
   -> Structures -> Interface -> Draw

2. Thiet lap do day:
   - Thickness factor: 0.1 (do day ao = 0.1 x be day that)
   - Thuong dung 0.1 cho simplification

3. Thiet lap R_inter:
   - Chon "Manual" va nhap gia tri R_inter
   - Hoac dung gia tri mac dinh tu CIRIA C760

Bang gia tri R_inter mac dinh:
+----------------------------------+
| Loai ket cau      | R_inter mac dinh|
+-------------------+----------------+
| Tuong vay (DW)   | 0.67          |
| Cu Larsen (SP)     | 0.67          |
| Coc khoan nhoi     | 0.67          |
+----------------------------------+
```

---

## 3. THIET LAP DIEU KIEN BIEN

### 3.1. Conditions va Phases

#### Default Supports
```
- Day mo hinh: Fixed (co dinh ca x va y)
- Hai ben: Normal stresses (ung suat phap tuyen theo phuong ngang)
```

#### Drainage Conditions
```
- Dieu kien thoat nuoc (Drained):
  -> Boundary -> Global water conditions -> Phreatic level
  
- Dieu kien khong thoat nuoc (Undrained):
  -> Thiet lap trong Soil Material Properties
  -> Khong can khai bao rieng tren bien
```

### 3.2. Cac Phase trong phan tich ho dao

```
Phase 1: Initial Phase (Giai doan ban dau)
    - Tao ung suat trong luong ban than (K0 procedure)
    - Muc nuoc ngam ban dau
    
Phase 2: Thi cong tuong vay (Excavation wall)
    - Kich hoat tuong vay
    - Kich hoat Interface
    
Phase 3: Dao den cot -2.0m
    - Deactivate dat trong pham vi ho dao
    - Tinh toan ung suat ban dau
    
Phase 4: Thi cong san chong level 1
    - Activate san chong (Plate voi stiffness)
    - Dao tiep
    
Phase 5: Dao den day ho
    - Deactivate dat tiep theo
    - Activate tiep cac san chong
    
Phase 6: Hoan thien
    - Thi cong ket cau ben trong
    - Loai bo tam thoi mot so gilang
```

---

## 4. CAC CANH BAO THUONG GAP

### 4.1. Warnings trong Plaxis

| Warning | Nguyen nhan | Khac phuc |
|---------|-------------|-----------|
| W001: Large yield zones | Ung suat vuot qua cuong do | Giam tai trong, tang cuong do dat |
| W002: Excessive plastic points | Qua nhieu diem chay deo | Them gilang, tang doc cung tuong |
| W003: Unstable | Mo hinh mat on dinh | Kiem tra dieu kien bien, dat yeu |
| W004: Large displacements | Chuyen vi lon | Tang doc cung ket cau, gilang |

### 4.2. Troubleshooting

**Van de: Ket qua khong hoi tu**
```
1. Giam buoc gia tai (Load advancement)
2. Tang so vong lap (Iterations): Max = 100
3. Giam tolerance: 0.01 -> 0.02
4. Kiem tra dieu kien bien
```

**Van de: Chuyen vi qua lon**
```
1. Tang doc cung tuong (EA, EI)
2. Them gilang/neo
3. Giam buoc dao
4. Xem xet dieu kien dat yeu
```

**Van de: Moment am bat thuong**
```
1. Kiem tra chieu dat gilang
2. Kiem tra dieu kien lien ket (hinge/pinned)
3. Xem xet so do tinh
```

---

## 5. CHECKLIST TRUOC KHI CHAY MO PHONG

### 5.1. Kiem tra dau vao

- [ ] Tat ca lop dat da co Material Set
- [ ] Thong so dat nam trong tam gia tri hop ly
- [ ] Tuong vay da nhap EA, EI dung
- [ ] Gilang/neo da khai bao khoang cach
- [ ] Interface da thiet lap R_inter
- [ ] Muc nuoc ngam dung vi tri
- [ ] Dieu kien bien hop ly

### 5.2. Kiem tra so do

- [ ] Hinh hoc ho dao chinh xac
- [ ] Lop dat phan bo dung vi tri
- [ ] Ket cau dat dung cao do
- [ ] Pham vi mo hinh du lon (>= 3x chieu sau dao)

### 5.3. Kiem tra ket qua

- [ ] Chuyen vi nam trong gioi han SLS
- [ ] Moment uon trong tuong hop ly
- [ ] Luc doc trong gilang hop ly
- [ ] Khong co warnings nghiem trong
- [ ] Ung suat trong dat khong vuot qua cuong do

---

## 6. MAU BAO CAO KET QUA PLAXIS

### 6.1. Bang tong hop ket qua

```
BANG TONG HOP KET QUA PHAN TICH PLAXIS
================================================================

I. THONG TIN MO HINH
--------------------------------------------------------------------------------
- Phan mem: Plaxis 2D AE
- Phien ban: [version]
- Ngay chay: [date]
- Nguoi chay: [name]

II. KET QUA CHUYEN VI
--------------------------------------------------------------------------------
+-------------------+----------------+----------------+
| Phase             | delta_max (mm)  | delta_allow (mm)|
+-------------------+----------------+----------------+
| Sau khi dao den -5.0m| [value]        | [value]         |
| Sau khi dao den -10.0m| [value]       | [value]         |
| Sau khi dao den -15.0m| [value]       | [value]         |
+-------------------+----------------+----------------+

III. KET QUA NOI LUC TUONG VAY
--------------------------------------------------------------------------------
+-------------------+----------------+----------------+
| Phase             | Mmax (kNm/m)   | Vmax (kN/m)    |
+-------------------+----------------+----------------+
| [Phase name]      | [value]         | [value]         |
+-------------------+----------------+----------------+

IV. KET QUA GILANG/ NEO
--------------------------------------------------------------------------------
+-------------------+----------------+----------------+
| Gilang/Neo        | Luc (kN/m)     | %Capacity       |
+-------------------+----------------+----------------+
| [Name]            | [value]         | [value]         |
+-------------------+----------------+----------------+

V. KIEM TRA SLS
--------------------------------------------------------------------------------
+-------------------+----------------+----------------+
| Tieu chi          | Gia tri         | Ket luan        |
+-------------------+----------------+----------------+
| delta_max / (0.5% x H)| [eta]          | DAT/KHONG DAT   |
+-------------------+----------------+----------------+
```

---

> **Ghi chu:**
> - Luon luu file Plaxis goc (.p2dx, .cas) sau moi lan chay thanh cong
> - Ghi lai tat ca cac thong so dau vao vao Thuyet minh
> - Ket qua Plaxis can duoc Ky su CCHN xem xet va ky duyet
