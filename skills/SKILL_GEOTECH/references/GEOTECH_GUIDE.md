# HUONG DAN THUYET MINH GIAI TRINH KY THUAT

> **Pham vi:** Huong dan AI tao Thuyet minh giai trinh day du cho Thuyet minh/To trinh Bo phan thiet ke.
> **Yeu cau bat buoc:** Moi ket qua quy doi thong so dat va ket cau dua vao ho so phai di kem giai trinh chi tiet cong thuc goc.

---

## 1. CAU TRUC THUYET MINH GIAI TRINH

### 1.1. Bo cuc bat buoc

```
PHAN THUYET MINH GIAI TRINH
|
|+-- I. CO SO LY THUYET
|    +-- 1.1. Nguon tieu chuan, tai lieu tham khao
|    +-- 1.2. Gia dinh tinh toan
|    +-- 1.3. Gioi han ap dung
|
|+-- II. CONG THUC TONG QUAT
|    +-- 2.1. Cong thuc tong quat (dang symbolic)
|    +-- 2.2. Giai thich cac bien so
|    +-- 2.3. Nguon goc cong thuc (tac gia, nam, trang)
|
|+-- III. THE SO VA TINH TOAN
|    +-- 3.1. Bang so lieu dau vao
|    +-- 3.2. Tung buoc tinh (step-by-step)
|    +-- 3.3. Bang ket qua trung gian
|
|+-- IV. KET QUA QUY DOI
|    +-- 4.1. Bang tong hop thong so dau vao Plaxis
|    +-- 4.2. Giai thich y nghia tung thong so
|
|+-- V. KIEM CHUNG
|    +-- 5.1. Doi chieu Ground Truth (neu co)
|    +-- 5.2. Kiem tra tam gia tri hop ly (range check)
|    +-- 5.3. Canh bao (W001, W002, W003)
|
+-- VI. PHU LUC
     +-- A. Bang tuong quan SPT/CPT
     +-- B. So do phan bo lop dat
     +-- C. Ket qua kiem chung
```

---

## 2. CONG THUC TONG HOP (MASTER REFERENCE)

### 2.1. Tuong quan SPT -> Thong so dat

#### 2.1.1. E50ref cho dat roi (Drained)

```
Nguon: Bowles (1997), Foundation Analysis and Design, 5th Ed, pp. 67-68

Cong thuc tong quat:
    E50ref = alpha x N_SPT

Trong do:
    - E50ref : Module cat tuyen tham chieu [kN/m2]
    - alpha  : He so kinh nghiem, alpha = 1500-2500 kN/m2 per SPT blow
    - N_SPT  : So bua SPT trung binh tai lop dat (da hieu chinh)

Gia tri khuyen nghi:
    - Cat san, chat:     alpha = 2500 kN/m2 per SPT
    - Cat min, trung:    alpha = 2000 kN/m2 per SPT
    - Cat pha, bui:     alpha = 1500 kN/m2 per SPT
```

#### 2.1.2. E50ref cho dat dinh (Undrained)

```
Nguon: TCVN 9351:2012, Phu luc B; Das (2010), Principles of Geotechnical Eng.

Cong thuc tong quat:
    E50ref = beta x Su

Trong do:
    - E50ref : Module cat tuyen tham chieu [kN/m2]
    - beta   : He so kinh nghiem, beta = 400-500
    - Su     : Suc khang cat khong thoat nuoc [kN/m2]
              Su = Qu/2 (neu co ket qua nen don)
              Su = sigma'_v x tan(phi') + c' (cong thuc tong quat)

Gia tri khuyen nghi:
    - Set mem, bun:  beta = 400
    - Set deo:       beta = 450
    - Set nua cung:  beta = 500
```

#### 2.1.3. Suc khang cat khong thoat nuoc Su

```
Nguon: ASTM D2166, TCVN 9351:2012

Cach 1: Tu thi nghiem nen don (UU)
    Su = Qu / 2

    Trong do:
    - Qu : Cuong do chiu nen mot truc (kN/m2)

Cach 2: Tu CPT/CPTu
    Su = (qt - sigma_v0) / Nkt

    Trong do:
    - qt    : Suc khang mui da hieu chinh [kN/m2]
    - sigma_v0 : Ung suat tong tai do sau [kN/m2]
    - Nkt   : He so tuong quan, Nkt = 10-25 (phu thuoc loai dat)

Tuong quan Nkt (Robertson, 2016):
    - Set mem (Bq > 0.1):  Nkt = 10-12
    - Set nua cung:       Nkt = 15-18
    - Cat pha:            Nkt = 18-22
```

#### 2.1.4. Tuong quan SPT -> c', phi' (phuong phap kinh nghiem)

```
Nguon: Huong dan su dung phan mem Plaxis; Database 15+ du an TP.HCM

Bang 1: Dat dinh (Cohesive)
+---------------------+--------+-------------+--------+-----------------+
| Loai dat           | SPT (N) | c' (kN/m2) | phi' (do) | E50ref (kN/m2) |
+---------------------+---------+-------------+-----------+-----------------+
| Bun set             | 0-2     | 5-10        | 3-5      | 3,500-5,000     |
| Set mem            | 2-5     | 10-20      | 8-12     | 8,000-12,000    |
| Set trung binh     | 5-15    | 15-35      | 12-18    | 10,000-25,000   |
| Set cung           | 15-30   | 25-85      | 15-17    | 20,000-35,000   |
+---------------------+---------+-------------+-----------+-----------------+

Bang 2: Dat roi (Granular)
+---------------------+--------+-------------+-----------+-----------------+
| Loai dat           | SPT (N) | c' (kN/m2) | phi' (do) | E50ref (kN/m2) |
+---------------------+---------+-------------+-----------+-----------------+
| Cat roi            | 4-10    | 3-8         | 20-25    | 12,000-20,000   |
| Cat chat vua      | 10-30   | 4-15       | 22-30    | 18,000-33,000   |
| Cat rat chat      | 30-50   | 5-20       | 28-35    | 30,000-45,000   |
+---------------------+---------+-------------+-----------+-----------------+
```

---

### 2.2. Ung suat huu hieu va K0

#### 2.2.1. Ung suat huu hieu

```
Nguon: Terzaghi (1943), Theory of Soil Mechanics

Cong thuc:
    sigma'_v = sigma_v - u

Trong do:
    - sigma'_v : Ung suat huu hieu theo phuong dung [kN/m2]
    - sigma_v  : Ung suat tong theo phuong dung [kN/m2]
    - u        : Ap luc nuoc lo rong [kN/m2]

Tinh sigma_v:
    sigma_v = SUM(gamma_i x h_i)

    Trong do:
    - gamma_i : Dung trong lop dat thu i [kN/m3]
    - h_i     : Chieu day lop dat thu i [m]

Tinh u (muc nuoc ngam tai z = -z_w):
    u = gamma_w x (z - z_w)    khi z > z_w
    u = 0                    khi z <= z_w

    Trong do:
    - gamma_w : Dung trong nuoc = 9.81 kN/m3
    - z_w     : Cao do muc nuoc ngam [m]
```

#### 2.2.2. He so K0 - Dat nguyen dang (NC)

```
Nguon: Jaky (1944), "Pressure in Soils"

Cong thuc tong quat:
    K0 = 1 - sin(phi')

Hoac theo Alpan (1967) cho dat dinh:
    K0 = 0.19 + 0.233 x log10(Ip)

Trong do:
    - K0   : He so ap luc ngang o trang thai nghi
    - phi' : Goc ma sat trong hieu qua [do]
    - Ip   : Chi so deo [%]
```

#### 2.2.3. He so K0 - Dat qua co ket (OC)

```
Nguon: Mayne & Kulhawy (1982), "K0-OCR relationship in soils"

Cong thuc:
    K0(OC) = K0(NC) x OCR^sin(phi')

Trong do:
    - K0(OC) : He so K0 cho dat qua co ket
    - K0(NC) : He so K0 cho dat nguyen dang (tinh theo Jaky)
    - OCR    : Ty so qua co ket (Over-Consolidation Ratio)

Gioi han:
    K0(OC) <= Kp = (1 + sin(phi')) / (1 - sin(phi'))

    Trong do Kp la he so ap luc bi dong Rankine
```

---

### 2.3. Thong so mo hinh Hardening Soil (HS)

#### 2.3.1. Cac thong so co ban

```
Nguon: Plaxis Material Models Manual (2018), Schanz et al. (1999)

Bang tong hop thong so HS:
+--------------------+-------------+-----------+------------------------------+
| Thong so          | Ky hieu     | Don vi    | Y nghia                    |
+--------------------+-------------+-----------+------------------------------+
| Dung trong        | gamma_unsat | kN/m3    | Dung trong tu nhien/bao hoa |
| Module E50        | E50ref     | kN/m2    | Module cat tuyen tai pref   |
| Module Eoed       | Eoedref    | kN/m2    | Module tiep tuyen oedometer |
| Module Eur        | Eurref     | kN/m2    | Module do tai-gia tai lai |
| He so mu          | m          | -        | Phu thuoc loai dat         |
| Ap luc ref        | pref       | kN/m2    | Thay = 100 kN/m2          |
| He so nu_ur       | nu_ur      | -        | Poisson do tai = 0.2      |
| Luc dinh          | c'         | kN/m2    | Thong so cuong do huu hieu  |
| Goc ma sat        | phi'       | do       | Thong so cuong do huu hieu  |
| Goc no           | psi        | do       | Thay = phi' - 30 hoac 0  |
+--------------------+-------------+-----------+------------------------------+
```

#### 2.3.2. Quan he giua cac module

```
Nguon: Plaxis Material Models Manual

Eoedref:
    Eoedref = E50ref (cho dat thong thuong)

    Hoac tu Oedometer test:
    Eoedref = (1 + e0) x sigma'_v / Cc x ln(10)  [kN/m2]

    Trong do:
    - e0    : He so rong ban dau
    - sigma'_v: Ung suat huu hieu tai giua lop [kN/m2]
    - Cc    : Chi so nen

Eurref:
    Eurref = 3 x E50ref  (mac dinh kinh nghiem)

    Gia tri chinh xac hon (neu co Lab Test):
    Eurref = 2 x Eoedref den 5 x Eoedref

He so mu m:
    m phu thuoc loai dat:
    +---------------------+--------+
    | Loai dat            | m      |
    +---------------------+--------+
    | Cat sach, chat      | 0.50   |
    | Cat min, chat vua   | 0.55   |
    | Cat pha, bui        | 0.60   |
    | Set pha, deo mem    | 0.65-0.70 |
    | Set deo cung        | 0.70-0.80 |
    | Set mem, bun        | 0.80-0.90 |
    +---------------------+--------+
```

---

### 2.4. Thong so mo hinh Soft Soil Creep (SSC)

#### 2.4.1. Chuyen doi tu Oedometer sang SSC

```
Nguon: Plaxis Material Models Manual; Vermeer & Neher (1999)

Cong thuc chuyen doi:
    lambda_star = Cc / [2.3 x (1 + e0)]
    kappa_star = Cs / [1.15 x (1 + e0)]
    mu_star = Ca / [2.3 x (1 + e0)]

    Hoac: mu_star = lambda_star / R  (R = 20 cho set Viet Nam)

Trong do:
    - lambda_star : He so nen thuan tuy (khong co don vi)
    - kappa_star  : He so no (khong co don vi)
    - mu_star     : He so tu bien (khong co don vi)
    - Cc          : Chi so nen (Compression Index)
    - Cs           : Chi so no (Swelling Index), thuong Cs = Cc/5
    - Ca           : Chi so nen thu cap (Secondary Compression Index)
    - e0           : He so rong ban dau
    - R            : Ty so lambda_star/mu_star (thuong 15-25)
```

---

### 2.5. Ket cau chan giu (Tuong vay)

#### 2.5.1. Thong so tuong vay BTCT

```
Nguon: TCVN 5574:2018; Plaxis Material Models Manual

Tiet dien:
    A = b x h
    I = b x h^3 / 12

    Trong do:
    - b : Be rong tinh toan = 1.0 m/m
    - h : Be day tuong vay [m]

Thong so Plaxis:
    EA = Ec x A
    EI = Ec x I x beta_crack

    Trong do:
    - Ec         : Module dan hoi be tong [kN/m2]
                  Ec = 4500 x SQRT(Rb) x 10^3  [kN/m2]
                  Hoac tra bang: B25 -> Ec = 30,000 MPa
    - beta_crack : He so giam doc cung do nut (Stiffness Degradation)
                  beta_crack = 0.5-0.7 (thuong lay 0.6)

Stiffness Degradation:
    Gia tri beta_crack phu thuoc vao muc do nut:
    - Tiet dien nguyen:          beta = 1.0
    - Nut nhe (w < 0.2mm):       beta = 0.8
    - Nut trung binh:             beta = 0.6  <- Khuyen nghi
    - Nut nang (w > 0.4mm):     beta = 0.4
```

#### 2.5.2. Cu Larsen

```
Nguon: Catalog nha san xuat; Plaxis Material Models Manual

Thong so cu Larsen theo catalog:
+----------------+----------+------------+------------+
| Loai cu       | A (m2/m) | I (m4/m)   | E (kN/m2) |
+----------------+----------+------------+------------+
| SP III w      | 0.02425  | 3.86E-04   | 2.1E+08   |
| SP IV         | 0.02930  | 5.96E-04   | 2.1E+08   |
| SP V          | 0.03650  | 8.60E-04   | 2.1E+08   |
+----------------+----------+------------+------------+

Thong so Plaxis:
    EA = E x A  [kN/m]
    EI = E x I  [kNm2/m]
```

#### 2.5.3. He so tuong tac Rinter

```
Nguon: CIRIA C760 (2020); Plaxis Material Models Manual

Bang gia tri Rinter theo CIRIA C760:
+--------------------+---------------+---------------------+
| Loai ket cau       | Loai dat     | Rinter Khuyen nghi |
+--------------------+---------------+---------------------+
| Tuong vay (DW)    | Cat          | 0.80-0.90          |
|                    | Set cung     | 0.80               |
|                    | Set mem      | 0.60-0.70          |
| Cu Larsen (SP)    | Cat          | 0.70-0.80          |
|                    | Set          | 0.50-0.65          |
| Coc khoan nhoi    | Moi loai     | 0.70-0.90          |
+--------------------+---------------+---------------------+

Cong thuc tinh cuong do tuong tac:
    c_interface = Rinter x c_soil
    tan(phi_interface) = Rinter x tan(phi_soil)
```

---

### 2.6. Kiem tra SLS (Clough & O'Rourke)

#### 2.6.1. Gioi han chuyen vi ngang tuong vay

```
Nguon: Clough & O'Rourke (1990), "Construction induced movements"

Cong thuc:
    delta_allowable = eta x H

    Trong do:
    - delta_allowable : Chuyen vi ngang cho phep [mm]
    - H               : Chieu sau ho dao [mm]
    - eta             : He so kinh nghiem phu thuoc dieu kien dat

Bang gia tri eta:
+------------------------+--------+---------------------+
| Dieu kien dat          | eta    | delta_allow (% cua H) |
+------------------------+--------+---------------------+
| Cat chat / Set cung    | 0.002  | 0.20%               |
| Set trung binh        | 0.005  | 0.50%               |
| Set mem / Bun         | 0.010  | 1.00%               |
+------------------------+--------+---------------------+

He so su dung:
    zeta = delta_max / delta_allowable

    - zeta <= 0.7 : An toan, co du (co the toi uu hoa)
    - 0.7 < zeta <= 1.0 : Dat yeu cau
    - zeta > 1.0 : Khong dat, can tang doc cung tuong/gilang
```

---

### 2.7. Thi nghiem nen tinh coc

#### 2.7.1. Phuong phap Davisson

```
Nguon: Davisson (1972), "High Capacity Piles"

Cong thuc xac dinh suc chiu tai gioi han:
    delta_Davisson = delta_L + 4.0 + D/120

    Trong do:
    - delta_Davisson : Chuyen vi theo tieu chi Davisson [mm]
    - delta_L        : Bien dang dan hoi cua coc = PL/AE [mm]
    - 4.0           : Hang so (4 mm = 0.15 inch)
    - D              : Duong kinh coc [mm]
    - D/120          : He so hieu chinh theo duong kinh

Xac dinh Qu:
    - Ve duong cong tai trong - lun
    - Tai diem giao nhau giua duong cong va duong Davisson
    - Tung do giao diem = Qu (suc chiu tai gioi han)
```

#### 2.7.2. Phuong phap Chin-Kondner (Hyperbolic)

```
Nguon: Chin (1971), Kondner (1963)

Cong thuc:
    s/P = c1 x s + c2

    Trong do:
    - s : Lun [mm]
    - P : Tai trong [kN]
    - c1, c2 : He so tu hoi quy tuyen tinh

Suc chiu tai gioi han:
    Qu = 1 / c1

Tai trong thiet ke (FS = 2):
    P_allowable = Qu / 2
```

---

## 3. VI DU THUYET MINH (TEMPLATE)

### 3.1. Vi du: Tinh E50ref cho lop cat pha

```
============================================================================
III. THE SO VA TINH TOAN
============================================================================

3.1. So lieu dau vao
----------------------
Bao cao khao sat: [Ten BCTC KSDC]
Ho khoan: BH-01
Lop dat: 2a - Cat pha, deo cung
Chieu sau: -6.0m den -12.5m
N_SPT trung binh: N = 15 bua/30cm
Loai dat: Dat roi (Granular) -> Drained

3.2. Cong thuc ap dung
----------------------
    E50ref = alpha x N_SPT

Nguon: Bowles (1997), Foundation Analysis and Design, Eq. 3-12, p.67
        Database 15+ du an TP.HCM

Trong do:
    - alpha = 2000 kN/m2 per SPT (cat pha, chat vua)
    - N_SPT = 15 bua/30cm

3.3. Tinh toan tung buoc
--------------------------
Buoc 1: Xac dinh he so alpha
    alpha = 2000 kN/m2 per SPT (tra bang muc 2.1.1)

Buoc 2: The so
    E50ref = 2000 x 15

Buoc 3: Ket qua
    E50ref = 30,000 kN/m2

3.4. Kiem tra voi Ground Truth
--------------------------------
Du an tham khao: Navi Tower - Quy Nhon (Lop 1A, SPT=11, E50=15,000 kN/m2)
Tuong quan: 15,000/11 = 1,364 kN/m2 per SPT (thap hon do set pha nhieu)
Du an hien tai: Cat pha chat vua -> alpha=2000 phu hop ✓
Do lech: < 20% so voi database -> Chap nhan duoc

============================================================================
IV. KET QUA QUY DOI
============================================================================

| Lop | Mo hinh | gamma_sat | E50ref | Eoedref | Eurref | m | c' | phi' | Rinter |
|-----|---------|-----------|--------|---------|--------|---|----|------|--------|
| 2a  | HS      | 19.5     | 30,000 | 30,000  | 90,000 | 0.6 | 5  | 25   | 0.8    |

Giai thich thong so:
- E50ref = 30,000 kN/m2: Module cat tuyen tai pref=100 kPa
- Eoedref = E50ref: Gia dinh theo Plaxis Manual
- Eurref = 3xE50ref = 90,000 kN/m2: Module do tai-gia tai lai
- m = 0.6: He so mu cho cat pha (theo bang 2.3.2)
- Rinter = 0.8: Theo CIRIA C760 cho tuong vay trong cat

============================================================================
```

---

## 4. CHECKLIST TRUOC KHI XUAT HO SO

### 4.1. Kiem tra dau vao
- [ ] Bao cao khao sat DCCT day du, co chu ky, dong dau
- [ ] So lieu SPT/CPT duoc ghi nhan dung (N_SPT da hieu chinh theo Skempton)
- [ ] Muc nuoc ngam (GWL) xac dinh ro rang
- [ ] Phan loai lop dat nhat quan giua cac ho khoan

### 4.2. Kiem tra tuong quan
- [ ] Thong so nam trong tam gia tri kinh nghiem (range check)
- [ ] Doi chieu voi Ground Truth database
- [ ] Canh bao (W001, W002, W003) da duoc xem xet

### 4.3. Kiem tra dau ra
- [ ] Bang thong so Plaxis day du cac truong bat buoc
- [ ] Thuyet minh giai trinh cong thuc day du
- [ ] Nguon tham khao duoc ghi ro

### 4.4. Kiem tra phap ly
- [ ] Ky su co CCHN da ra soat va ky xac nhan
- [ ] Ghi chu tai lieu mang tinh tham khao, can kiem tra truoc khi su dung

---

## 5. BANG TUONG QUAN TRA CUU NHANH

### 5.1. Don vi thuong dung trong Plaxis

```
+---------------------+------------------+---------------------+
| Thong so           | Plaxis           | Don vi             |
+---------------------+------------------+---------------------+
| Module (E, E50...) | Eref             | kN/m2 (= kPa)     |
| Luc dinh (c)       | c                | kN/m2 (= kPa)     |
| Dung trong (gamma) | gamma            | kN/m3             |
| Chieu dai (L)      | L                | m                  |
| Dien tich (A)      | A                | m2/m               |
| Momen quan tinh (I) | I                | m4/m               |
| Ap luc tham chieu   | pref            | kN/m2 (= 100)     |
+---------------------+------------------+---------------------+

Quy doi:
- 1 MPa = 1000 kN/m2 = 1000 kPa
- 1 kN/m2 = 1 kPa
```

### 5.2. Gioi han tam gia tri thong so dat TP.HCM

```
+----------------------------+--------------------------------+
| E50ref [kN/m2]           | Gioi han hop ly              |
+----------------------------+--------------------------------+
| Set mem, bun              | 3,000 - 12,000              |
| Set trung binh            | 10,000 - 30,000             |
| Set cung                  | 20,000 - 70,000             |
| Cat pha                    | 15,000 - 35,000             |
| Cat chat                   | 20,000 - 50,000             |
+----------------------------+--------------------------------+
| phi' [do]                | Gioi han hop ly              |
+----------------------------+--------------------------------+
| Set nguyen dang           | 15 - 25                     |
| Set pha                   | 20 - 30                     |
| Cat                       | 25 - 40                     |
+----------------------------+--------------------------------+
| c' [kN/m2]              | Gioi han hop ly              |
+----------------------------+--------------------------------+
| Cat                       | 0 - 10                      |
| Set pha                   | 5 - 30                      |
| Set cung                  | 20 - 100                    |
+----------------------------+--------------------------------+
```

---

---

## 6. KIEM TRA ON DINH DAY HO DAO (BASE HEAVE)

### 6.1. Cong thuc Base Heave theo Terzaghi

```
Nguon: Terzaghi (1943), Theory of Soil Mechanics;
       Bjerrum-Eide (1956); CIRIA C760

Cong thuc tong quat:
    Fs = (Nc x Su) / (gamma_avg x H_đao + q)

Trong do:
    - Nc    : He so suc chiu tai hinh hoc
              Nc = 5.14 x (1 + 0.2 x B/L)
    - Su    : Suc khang cat khong thoat nuoc tai day ho [kN/m2]
    - gamma_avg: Dung trong trung binh phan lop [kN/m3]
              gamma_avg = Σ(γi x hi) / H_đao
    - H_đao : Chieu sau ho dao [m]
    - q     : Hoat tai tren mep ho [kN/m2] (mac dinh 10 kN/m2)

Gioi han cho phep:
    Fs >= 1.50 : On dinh dam bao
    1.25 <= Fs < 1.50 : Can theo doi
    Fs < 1.25 : Mat on dinh — can tang chieu sau ngam cu hoac gia co dat
```

### 6.2. Trinh tu tinh toan Base Heave

```
Buoc 1: Tinh Nc
    Nc = 5.14 x (1 + 0.2 x B/L)

Buoc 2: Tinh gamma_avg
    gamma_avg = [γ_ad x h_ad + γ_1 x (H - h_ad)] / H

Buoc 3: Tinh σ_v,base
    σ_v,base = γ_avg x H + q

Buoc 4: Tinh Fs
    Fs = (Nc x Su) / σ_v,base

Buoc 5: Danh gia
    η = Fs / 1.50
    η <= 0.70: An toan (xanh)
    0.70 < η <= 0.90: Tot (vang)
    0.90 < η <= 1.00: Luu y (cam)
    η > 1.00: Vuot gioi han (do)
```

### 6.3. Vi du tinh toan (tham khao: Sunrise CVPM Quang Trung)

```
============================================================================
 VI DU: KIEM TRA BASE HEAVE - HO DAO 7.0m x 14.5m, H=3.95m

So lieu dau vao:
    B = 7.0 m, L = 14.5 m
    H = 3.95 m
    Su = 21.15 kPa (set pha deo mem, lop 1)
    γ_ad = 17.50 kN/m3, γ_1 = 19.12 kN/m3
    q = 10.0 kPa (hoat tai thi cong)
    h_ad = 0.80 m

Buoc 1: Nc
    B/L = 7.0/14.5 = 0.483
    Nc = 5.14 x (1 + 0.2 x 0.483)
       = 5.14 x 1.097
       = 5.64

Buoc 2: gamma_avg
    gamma_avg = (17.50 x 0.80 + 19.12 x 3.15) / 3.95
             = (14.00 + 60.23) / 3.95
             = 74.23 / 3.95
             = 18.79 kN/m3

Buoc 3: σ_v,base
    σ_v,base = 18.79 x 3.95 + 10.0
             = 74.22 + 10.0
             = 84.22 kPa

Buoc 4: Fs
    Fs = (5.64 x 21.15) / 84.22
       = 119.29 / 84.22
       = 1.416 ≈ 1.42

Buoc 5: Danh gia
    η = 1.42 / 1.50 = 0.947
    Ket luan: 0.90 < η <= 1.00 → 🟠 Lưu ý

    Khuyen nghi:
    1. Gioi han hoat tai tren mep ho: q <= 10 kPa
    2. Dot betong lot trong vong 24h sau khi dao den day
    3. Theo doi chuyen vi va luc nen thanh chong bang cam bien
============================================================================
```

---

## 7. KIEM TRA ON DINH THANH CHONG (STRUT BUCKLING)

### 7.1. Cong thuc kiem tra on dinh thanh chong

```
Nguon: TCVN 5575:2018; Eurocode 3 (EN 1993-1-1)

Buoc 1: Do manh
    λ = L0 / i_min

    Trong do:
    - L0 = μ x L_span  [m]
    - L_span : Chieu dai nhịp thanh chong [m]
    - μ : He so chieu dai tinh toan (0.5-1.0, mac dinh 1.0)
    - i_min : Ban kinh quan tinh nho nhat [m]

    Gioi han: λ <= 150

Buoc 2: Do manh quy uoc
    λ_bar = (λ / π) x √(f_y / E)

    Trong do:
    - f_y : Cuong do chay thep [kPa]
    - E : Module dan hoi thep [kPa] (= 210,000 MPa = 2.1e8 kPa)

Buoc 3: He so uon doc φ (duong cong Euler B)
    Neu λ_bar <= 0.2: φ = 1.0 (khong xay ra mat on dinh)
    Neu λ_bar > 0.2:
        Φ = 0.5 x [1 + α(λ_bar - 0.2) + λ_bar²]
        φ = 1 / (Φ + √(Φ² - λ_bar²))

    Trong do: α = 0.34 (he so khuyet tap, duong cong B)

Buoc 4: Kha nang chiu nen
    N_Rd = φ x A x f_y / γ_M0

    Trong do:
    - A : Dien tich mat cat ngang [m2]
    - γ_M0 : He so vat lieu (= 1.0)

Buoc 5: Kiem tra voi N_Ed tu Plaxis
    η_N = N_Ed / N_Rd
    η_N <= 0.70: An toan (xanh)
    0.70 < η_N <= 0.90: Tot (vang)
    0.90 < η_N <= 1.00: Luu y (cam)
    η_N > 1.00: Vuot gioi han (do)
```

### 7.2. Bang tieu dien thep hinh pho bien (Viet Nam)

```
+--------+------------------------+------+--------+--------+--------+--------+
| Ky hieu| Ten (Catalog)         | A    | ix     | iy     | W_x    |
|        |                        | cm2  | cm     | cm     | cm3    |
+--------+------------------------+------+--------+--------+--------+
| H150   | H150x150x7x10        | 27.2 | 6.72   | 4.56   | 163    |
| H200   | H200x200x8x12        | 62.1 | 8.62   | 5.08   | 461    |
| H250   | H250x250x9x14        | 92.2 | 10.84  | 6.29   | 864    |
| H300   | H300x300x10x15       | 119.8| 13.05  | 7.51   | 1360   |
| H350   | H350x350x12x19       | 173.9| 15.23  | 8.84   | 2300   |
| H400   | H400x400x13x21       | 218.7| 17.73  | 10.12  | 3445   |
| 2H200  | 2xH200x200x8x12     | 124.2| 8.62   | 7.18   | 922    |
| 2H300  | 2xH300x300x10x15    | 239.6| 13.05  | 10.62  | 2720   |
+--------+------------------------+------+--------+--------+--------+--------+
```

### 7.3. Vi du tinh toan (tham khao: Sunrise CVPM Quang Trung)

```
============================================================================
 VII DU: KIEM TRA STRUT H200x200x8x12, L_span = 7.0m

So lieu dau vao:
    Loai thep: H200x200x8x12 (SS400)
    A = 62.08 cm2 = 6.208e-3 m2
    i_min = iy = 5.08 cm = 0.0508 m
    L_span = 7.0 m
    μ = 1.0 (thanh chong ngang, hai dau nut)
    f_y = 235 MPa = 235,000 kPa
    E = 210,000 MPa = 210,000,000 kPa

Buoc 1: Do manh λ
    L0 = μ x L_span = 1.0 x 7.0 = 7.0 m
    λ = 7.0 / 0.0508 = 137.8
    λ <= 150 → ✓ Dat

Buoc 2: Do manh quy uoc λ_bar
    λ_bar = (137.8 / 3.1416) x √(235000 / 210000000)
           = 43.86 x 0.03345
           = 1.467

Buoc 3: He so uon doc φ
    α = 0.34 (duong cong B - thep hinh H)
    Φ = 0.5 x [1 + 0.34(1.467 - 0.2) + 1.467²]
       = 0.5 x [1 + 0.43 + 2.152]
       = 0.5 x 3.582
       = 1.791

    √(Φ² - λ_bar²) = √(3.209 - 2.152) = √1.057 = 1.028
    φ = 1 / (1.791 + 1.028) = 1 / 2.819 = 0.355

Buoc 4: N_Rd
    N_Rd = 0.355 x 6.208e-3 x 235000
          = 0.355 x 1458800
          = 517,374 N = 517.4 kN

Buoc 5: Ket luan
    N_Rd = 517.4 kN
    (N_Ed tu Plaxis can bo sung sau khi chay mo hinh)

============================================================================
```

---

## 8. BANG TUONG QUAN E50 - GROUND TRUTH (v2.3)

### 8.1. Bang Ke = E50/Su cho dat dinh

```
Nguon: Jamiolkowski et al. (1979), Stroud (1974), CIRIA C760 (Table 5.3)

+----------+-----------+------------+------------+------------------------------+
| Ip (%)   | Mo ta     | Ke_min     | Ke_max     | Ke_khuyen nghi             |
+----------+-----------+------------+------------+------------------------------+
| < 15     | Set mem, bun | 300       | 500       | 400                        |
| 15 - 25  | Set deo mem | 400       | 600       | 500                        |
| 25 - 40  | Set trung binh| 500      | 700       | 600                        |
| 40 - 60  | Set nua cung | 600       | 900       | 710 (CIRIA C760 chuan)    |
| > 60     | Set cung   | 800         | 1200      | 1000                       |
+----------+-----------+------------+------------+------------------------------+

Cong thuc: E50ref = Ke x Su
  VD: Ip = 12.8%, Su = 21.15 kPa → Ke = 500
       E50ref = 500 x 21.15 = 10,575 kPa ≈ 11,000 kPa

  VD: Ip = 30%, Su = 50 kPa → Ke = 600
       E50ref = 600 x 50 = 30,000 kPa
```

### 8.2. Bang α = E50/N_SPT cho dat roi

```
Nguon: Bowles (1997), Webb (1969), CIRIA C760

+---------------+-------------+------------+------------------------------+
| Loai cat     | α_min       | α_max     | α_khuyen nghi               |
+---------------+-------------+------------+------------------------------+
| Cat min, roi  | 1500        | 2000      | 1500                        |
| Cat trung     | 2000        | 2700      | 2000                        |
| Cat tho, chat | 2500        | 3000      | 2500                        |
| Cat soi, rat chat | 3000   | 4000      | 3000                        |
+---------------+-------------+------------+------------------------------+

Cong thuc: E50ref = α x N_SPT
  VD: Cat trung, N = 13 → α = 2000
       E50ref = 2000 x 13 = 26,000 kPa

  VD: Cat tho chat, N = 30 → α = 2500
       E50ref = 2500 x 30 = 75,000 kPa
```

---

> **Ghi chu quan trong:**
> Tai lieu nay la phu luc ky thuat cho SKILL_GEOTECH v2.3. Ket qua tinh toan mang tinh tham khao, can duoc Ky su co Chung chi Hanh nghe kiem tra va chiu trach nhiem truoc khi su dung cho ho so thiet ke, thi cong hoac tham tra.
