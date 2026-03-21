# Demo Data List - Toan Bo Nghiep Vu HRM PM CRM

## 1. HRM - Co Cau To Chuc

### 1.1 Phong ban
1. PB-BOD | Ban Giam Doc | parent: none
2. PB-HR | Hanh chinh Nhan su | parent: PB-BOD
3. PB-PM | Van phong Du an | parent: PB-BOD
4. PB-SALES | Kinh doanh | parent: PB-BOD
5. PB-CS | Cham soc khach hang | parent: PB-SALES

### 1.2 Chuc vu
1. CV-CEO | Giam doc dieu hanh | phong ban: PB-BOD
2. CV-HRM | Truong phong Nhan su | phong ban: PB-HR
3. CV-PMM | Truong phong Du an | phong ban: PB-PM
4. CV-SM | Truong phong Kinh doanh | phong ban: PB-SALES
5. CV-AM | Account Manager | phong ban: PB-SALES
6. CV-SE | Ky su phan mem | phong ban: PB-PM
7. CV-QA | Kiem thu vien | phong ban: PB-PM
8. CV-CSA | Chuyen vien ho tro | phong ban: PB-CS

### 1.3 Nhan vien
1. NV001 | Nguyen Van A | CV-CEO | PB-BOD | trang_thai: active
2. NV002 | Tran Thi B | CV-HRM | PB-HR | quan_ly: NV001 | active
3. NV003 | Le Van C | CV-PMM | PB-PM | quan_ly: NV001 | active
4. NV004 | Pham Thi D | CV-SM | PB-SALES | quan_ly: NV001 | active
5. NV005 | Hoang Van E | CV-AM | PB-SALES | quan_ly: NV004 | active
6. NV006 | Vu Thi F | CV-SE | PB-PM | quan_ly: NV003 | active
7. NV007 | Do Van G | CV-QA | PB-PM | quan_ly: NV003 | active
8. NV008 | Bui Thi H | CV-CSA | PB-CS | quan_ly: NV004 | active

### 1.4 Hop dong lao dong
1. HD001 | NV005 | xac_dinh_thoi_han | luong_co_ban: 18000000 | phu_cap: 2000000 | active
2. HD002 | NV006 | xac_dinh_thoi_han | luong_co_ban: 22000000 | phu_cap: 3000000 | active
3. HD003 | NV007 | xac_dinh_thoi_han | luong_co_ban: 20000000 | phu_cap: 2500000 | active
4. HD004 | NV008 | xac_dinh_thoi_han | luong_co_ban: 15000000 | phu_cap: 1500000 | active

## 2. HRM - Van Hanh Nhan su

### 2.1 Cham cong (1 thang mau)
- Thang: 2026-03
- NV005, NV006, NV007, NV008: tao 22 ban ghi/nguoi
- Trang thai mau:
1. 16 ngay di_lam
2. 2 ngay cong_tac
3. 2 ngay nghi_phep
4. 1 ngay nghi_om
5. 1 ngay nghi_khong_luong

### 2.2 Don nghi phep
1. NP001 | NV006 | phep_nam | 2026-03-10 -> 2026-03-11 | duyet_cap_2
2. NP002 | NV007 | om | 2026-03-14 -> 2026-03-14 | duyet_cap_2
3. NP003 | NV008 | cong_tac | 2026-03-20 -> 2026-03-21 | duyet_cap_2
4. NP004 | NV005 | khong_luong | 2026-03-24 -> 2026-03-24 | cho_duyet

### 2.3 Tinh luong
1. BL2026-03 | thang_nam: 2026-03 | trang_thai: da_duyet
- Chi tiet 4 nhan vien NV005..NV008
- Co du lieu: luong_co_ban, phu_cap, thuong_tu_dong, bao_hiem, thue, thuc_linh

### 2.4 Tuyen dung

#### Vi tri tuyen dung
1. VT001 | Backend Engineer | PB-PM | so_luong_tuyen: 2 | open
2. VT002 | Customer Support | PB-CS | so_luong_tuyen: 1 | open

#### Ung vien
1. UV001 | Nguyen Thi I | VT001 | screening | diem_cv: 7.5
2. UV002 | Tran Van K | VT001 | phong_van | diem_cv: 8.0 | diem_phong_van: 8.5
3. UV003 | Le Thi L | VT002 | offer | diem_cv: 8.2 | luong_thoa_thuan: 13000000
4. UV004 | Pham Van M | VT002 | hired | lien_ket_nhan_vien: NV009

#### Phong van
1. PV001 | UV002 | technical | scheduled
2. PV002 | UV003 | culture_fit | done | diem: 8.8

### 2.5 Onboarding Offboarding
1. ONB001 | NV009 | onboarding | in_progress | 5 task
2. OFF001 | NV010 | offboarding | done | 6 task

## 3. PM - Du an Cong viec

### 3.1 Du an
1. DA001 | Trien khai CRM cho Alpha | quan_ly: NV003 | ngan_sach: 1200000000 | dang_thuc_hien
2. DA002 | Bao tri he thong Beta | quan_ly: NV003 | ngan_sach: 400000000 | dang_thuc_hien
3. DA003 | Chuyen doi so Gamma | quan_ly: NV003 | ngan_sach: 900000000 | chuan_bi

### 3.2 Cong viec
1. CVIEC001 | DA001 | Phan tich yeu cau | NV006 | hoan_thanh
2. CVIEC002 | DA001 | Thiet ke giai phap | NV006 | hoan_thanh
3. CVIEC003 | DA001 | Phat trien module lead | NV006 | dang_thuc_hien | phu_thuoc: CVIEC002
4. CVIEC004 | DA001 | Kiem thu module lead | NV007 | moi | phu_thuoc: CVIEC003 | bi_chan: true
5. CVIEC005 | DA001 | Dao tao nguoi dung | NV005 | moi | phu_thuoc: CVIEC004 | bi_chan: true
6. CVIEC006 | DA002 | Xu ly ticket P1 | NV008 | dang_thuc_hien
7. CVIEC007 | DA002 | Toi uu hieu nang | NV006 | tam_dung
8. CVIEC008 | DA003 | Lap ke hoach tong the | NV003 | moi

### 3.3 Nguoi tham gia
- Moi cong viec co 2-3 nguoi tham gia
- Vai tro mau: dev, qa, ba, pm

### 3.4 Bao cao tien do
- Moi cong viec dang_thuc_hien co it nhat 3 ban ghi bao cao
- Du lieu mau:
1. BC001 | CVIEC003 | tien_do: 30 | so_gio: 6
2. BC002 | CVIEC003 | tien_do: 55 | so_gio: 7
3. BC003 | CVIEC006 | tien_do: 65 | so_gio: 5

### 3.5 Phan bo nguon luc
1. NNL001 | DA001 | Server cloud | so_luong: 4 | don_gia: 2500000
2. NNL002 | DA001 | License BI | so_luong: 10 | don_gia: 900000
3. NNL003 | DA002 | Monitoring tool | so_luong: 2 | don_gia: 1800000

### 3.6 Bangiao timesheet
- Tao 40 ban ghi approved cho NV006 NV007 NV008
- loai_cong_viec: thuong, tang_ca, lao_dung
- Du lieu mau:
1. TS001 | NV006 | DA001 | CVIEC003 | ngay_lam: 2026-03-05 | tong_gio: 8 | approved
2. TS002 | NV006 | DA001 | CVIEC003 | ngay_lam: 2026-03-06 | tong_gio: 3 | tang_ca | approved
3. TS003 | NV007 | DA001 | CVIEC004 | ngay_lam: 2026-03-07 | tong_gio: 6 | submitted

### 3.7 Rui ro du an
1. RR001 | DA001 | Tre deadline do scope tang | xac_suat: cao | tac_dong: nang | active
2. RR002 | DA002 | Mat nhan su key | xac_suat: trung_binh | tac_dong: rat_nang | monitoring
3. RR003 | DA003 | Tre procurement | xac_suat: thap | tac_dong: trung_binh | identified

### 3.8 Issue du an
1. ISSUE001 | DA001 | Loi mapping du lieu khach hang | do_uu_tien: rat_cao | in_progress
2. ISSUE002 | DA001 | API timeout cao diem | do_uu_tien: cao | open
3. ISSUE003 | DA002 | Sai mau bao cao KPI | do_uu_tien: trung_binh | resolved

## 4. CRM - Khach hang Ban hang Ho tro

### 4.1 Khach hang
1. KH001 | Cong ty Alpha | trang_thai_hop_tac: dang_hop_tac | owner: NV005
2. KH002 | Cong ty Beta | trang_thai_hop_tac: dang_hop_tac | owner: NV005
3. KH003 | Cong ty Gamma | trang_thai_hop_tac: tiem_nang | owner: NV005
4. KH004 | Cong ty Delta | trang_thai_hop_tac: tam_ngung | owner: none

### 4.2 Tuong tac khach hang
- Moi khach hang co 4-8 ban ghi tuong tac
- Trang thai mau: planned, done, cancel
- Ket qua mau: chot_hop_dong, tiep_tuc_theo_doi, khong_phu_hop

### 4.3 Lead
1. LEAD0001 | Alpha Retail | source: website | quan_tam | diem: 72
2. LEAD0002 | Beta Foods | source: referral | san_sang | diem: 85
3. LEAD0003 | Gamma Logistics | source: event | dang_tiep_can | diem: 55
4. LEAD0004 | Delta Edu | source: phone | chua_san_sang | diem: 40

### 4.4 Co hoi ban hang
1. OPP0001 | Goi CRM Enterprise Alpha | gia_tri: 950000000 | xac_suat: 80 | sap_dong
2. OPP0002 | Bao tri he thong Beta | gia_tri: 280000000 | xac_suat: 60 | thuong_luong
3. OPP0003 | MRF Gamma | gia_tri: 1200000000 | xac_suat: 40 | de_xuat
4. OPP0004 | Goi ho tro Delta | gia_tri: 150000000 | xac_suat: 20 | kham_pha

### 4.5 Bao gia
1. BG000001 | KH001 | OPP0001 | tong_tien: 1045000000 | sent
2. BG000002 | KH002 | OPP0002 | tong_tien: 305000000 | accepted
3. BG000003 | KH003 | OPP0003 | tong_tien: 1320000000 | pending_approval

### 4.6 Don hang
1. DH000001 | KH002 | from BG000002 | tong_tien: 305000000 | in_delivery
2. DH000002 | KH001 | from BG000001 | tong_tien: 1045000000 | confirmed

### 4.7 Hop dong khach hang
1. HDKH00001 | KH001 | gia_tri: 950000000 | executing | ngay_ket_thuc con 20 ngay
2. HDKH00002 | KH002 | gia_tri: 280000000 | signed
3. HDKH00003 | KH004 | gia_tri: 150000000 | pending_signature

### 4.8 Yeu cau ho tro va SLA
1. HT000001 | KH001 | uu_tien: khan_cap | sla_gio: 8 | in_progress | qua_han_sla: true
2. HT000002 | KH001 | uu_tien: cao | sla_gio: 24 | waiting_customer | qua_han_sla: false
3. HT000003 | KH002 | uu_tien: trung_binh | sla_gio: 48 | resolved
4. HT000004 | KH003 | uu_tien: thap | sla_gio: 72 | new

### 4.9 Hoat dong sales
1. HDS001 | KH001 | goi_dien | completed
2. HDS002 | KH001 | gap_truc_tiep | planned
3. HDS003 | KH002 | email | completed
4. HDS004 | KH003 | demo_san_pham | rescheduled

## 5. Dashboard KPI - Bo du lieu kiem thu

### 5.1 HR KPI
- tong_nhan_vien_active: >= 8
- tong_bang_luong_da_duyet: >= 1
- payroll_variance: co duong va am (tao 2 ky luong lien tiep)

### 5.2 PM KPI
- tong_cong_viec_active: >= 5
- tong_cong_viec_bi_chan: >= 2
- blocked_task_ratio: > 0

### 5.3 CRM KPI
- tong_ticket_ho_tro (mo): >= 2
- ticket_qua_han_sla: >= 1
- sla_breach_rate: > 0

## 6. Checklist luong nghiep vu de demo
1. Duyet don nghi phep NP001 -> kiem tra cham_cong ngay tuong ung duoc tao cap nhat
2. Chay tinh luong BL2026-03 -> kiem tra so_ngay_lam_viec, thuong_tu_dong, thue
3. Thu bat dau CVIEC004 khi CVIEC003 chua hoan_thanh -> phai bi chan
4. Chuyen CVIEC003 sang hoan_thanh -> CVIEC004 het chan
5. Tao ticket HT000005 co sla_gio=1 va ngay_tao_datetime lui 2 gio -> qua_han_sla=true
6. Mo Dashboard KPI CRM -> SLA breach rate tang

## 7. Goi y seed theo dot
1. Dot 1: HRM co ban (phong ban, chuc vu, nhan vien, hop dong)
2. Dot 2: PM (du an, cong viec, dependency, timesheet)
3. Dot 3: CRM pre-sales (khach hang, lead, co hoi, bao gia)
4. Dot 4: CRM post-sales (don hang, hop dong, ho tro, SLA)
5. Dot 5: Dashboard KPI va regression test
