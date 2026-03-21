# Three-Module Integration: Workflow & Business Logic Analysis

**Date**: March 2026  
**Modules Analyzed**:
1. `quan_ly_nhan_su` (Employee Management)
2. `quan_ly_cong_viec` (Task/Project Management)
3. `quan_ly_khach_hang` (Customer Management)

---

## Table of Contents
1. [Module Overview](#module-overview)
2. [Primary Entities](#primary-entities)
3. [Data Model Relationships](#data-model-relationships)
4. [Complete Workflow Sequence](#complete-workflow-sequence)
5. [Data Flows Between Modules](#data-flows-between-modules)
6. [Business Rules & Validations](#business-rules--validations)
7. [Computed Fields & Metrics](#computed-fields--metrics)
8. [User Actions & Workflows](#user-actions--workflows)

---

## Module Overview

### Dependency Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                     QUAN_LY_KHACH_HANG                           │
│              (Customer Management - Top Layer)                    │
│        Depends: base, mail, quan_ly_nhan_su, quan_ly_cong_viec   │
└──────────────────────────────────────────────────────────────────┘
                              ▲
                              │ depends on
                              │
┌──────────────────────────────────────────────────────────────────┐
│                  QUAN_LY_CONG_VIEC                                │
│         (Task/Project Management - Middle Layer)                  │
│          Depends: base, mail, quan_ly_nhan_su                     │
└──────────────────────────────────────────────────────────────────┘
                              ▲
                              │ depends on
                              │
┌──────────────────────────────────────────────────────────────────┐
│                   QUAN_LY_NHAN_SU                                 │
│         (Employee Management - Foundation Layer)                  │
│               Depends: base, mail                                 │
└──────────────────────────────────────────────────────────────────┘
```

**Key Insight**: Each module acts as a building block. Lower layers are completely independent; upper layers extend and integrate lower layers.

---

## Primary Entities

### 1. QUAN_LY_NHAN_SU - Employee Management

#### Core Entity: `nhan_vien` (Employee)

**Core Fields**:
```
nhan_vien
├── Identity
│   ├── ma_nhan_vien (Unique Employee ID) *UNIQUE*
│   ├── ho_va_ten (Full Name)
│   ├── ngay_sinh (Date of Birth)
│   ├── gioi_tinh (Gender: nam, nu, khac)
│   ├── cmnd_cccd (ID Card Number) *UNIQUE*
│   └── hinh_anh (Photo)
│
├── Contact & Address
│   ├── email
│   ├── dien_thoai (Phone)
│   ├── dia_chi (Address)
│   └── dia_chi_hien_tai (Current Address)
│
├── Education
│   ├── trinh_do_hoc_van (Education Level)
│   ├── chuyen_nganh (Major)
│   ├── truong_tot_nghiep (University)
│   └── nam_tot_nghiep (Graduation Year)
│
├── Organization Relationships [Many2one References]
│   ├── phong_ban_id → phong_ban (Department)
│   ├── chuc_vu_id → chuc_vu (Job Position)
│   └── quan_ly_id → nhan_vien (Direct Manager - Self Reference)
│
├── Employment Info
│   ├── ngay_vao_lam (Start Date)
│   ├── trang_thai (Status: active, probation, leave, suspended)
│   ├── ngay_nghi_viec (Resignation Date)
│   └── ly_do_nghi_viec (Resignation Reason)
│
├── Financial/Insurance
│   ├── so_tai_khoan (Bank Account)
│   ├── ten_ngan_hang (Bank Name)
│   ├── chi_nhanh (Branch)
│   ├── so_bhxh (Social Insurance)
│   ├── so_bhyt (Health Insurance)
│   └── [date fields for insurance]
│
├── One2many Relationships (Collections)
│   ├── hop_dong_ids (Contracts)
│   ├── cham_cong_ids (Attendance Records)
│   ├── danh_gia_ids (Performance Reviews)
│   └── dao_tao_ids (Training Records)
│
└── Extended from quan_ly_khach_hang
    ├── user_id → res.users (Odoo User Account)
    ├── khach_hang_phu_trach_ids (Customers Responsible For) [One2many]
    └── du_an_quan_ly_ids (Projects Managing) [One2many]
```

**Related Organization Models**:
- `phong_ban` (Department): Can have hierarchical parent/child
- `chuc_vu` (Job Position): Basic position info

---

### 2. QUAN_LY_CONG_VIEC - Task/Project Management

#### Core Entity 1: `du_an` (Project)

**Fields**:
```
du_an
├── Identity
│   ├── ma_du_an (Project Code) *UNIQUE*
│   ├── ten_du_an (Project Name)
│   └── mo_ta (Description)
│
├── Timeline
│   ├── ngay_bat_dau (Start Date) [Required]
│   └── ngay_ket_thuc (End Date, Optional)
│
├── Relationships [Many2one]
│   ├── nguoi_quan_ly_id → nhan_vien (Project Manager)
│   └── khach_hang_id → khach_hang (Customer) [Extended from quan_ly_khach_hang]
│
├── Status & Finance
│   ├── trang_thai (Status: chuan_bi, dang_thuc_hien, tam_dung, hoan_thanh, huy_bo)
│   ├── ngan_sach (Budget in VND)
│   └── chi_phi_thuc_te (Actual Cost - Computed)
│
├── Computed Metrics
│   ├── so_luong_cong_viec (Count of Tasks) [Computed]
│   └── ti_le_hoan_thanh (Completion %: completed_tasks/total_tasks) [Computed]
│
└── One2many Collections
    ├── cong_viec_ids (Tasks in this Project)
    └── nguon_luc_ids (Resource Allocations)
```

**Validation Rule**: 
- Automatic status sync: When all tasks complete → project auto-marks complete

#### Core Entity 2: `cong_viec` (Task)

**Fields**:
```
cong_viec
├── Identity
│   ├── ma_cong_viec (Task Code) *UNIQUE*
│   ├── ten_cong_viec (Task Name)
│   └── mo_ta (Description)
│
├── Timeline & Planning
│   ├── ngay_bat_dau (Start Date) [Required]
│   ├── ngay_ket_thuc (End Date, Optional)
│   └── ke_hoach_gio (Planned Hours)
│
├── Relationships [Many2one]
│   ├── du_an_id → du_an (Parent Project) [Required, Cascade Delete]
│   ├── nguoi_phu_trach_id → nhan_vien (Task Owner)
│   ├── khach_hang_id → khach_hang (Customer) [Extended]
│   └── contact_person_id → khach_hang (Contact) [Extended, Subdomain filtered]
│
├── Status & Priority
│   ├── trang_thai (Status: moi, dang_thuc_hien, tam_dung, hoan_thanh, huy_bo)
│   └── do_uu_tien (Priority: thap, trung_binh, cao, rat_cao)
│
├── Progress Tracking (Computed)
│   ├── thuc_te_gio (Actual Hours - Sum of progress reports)
│   ├── tien_do % (Progress - Latest report percentage)
│   └── nguon_phat_sinh (Origin: goi_dien, lich_hen, bao_gia, thu_cong) [Extended]
│
└── One2many Collections
    ├── nguoi_tham_gia_ids (Task Participants)
    ├── bao_cao_tien_do_ids (Progress Reports)
    └── nguon_luc_ids (Resource Allocations)
```

**Validation Rules**:
- Task dates must be within project dates
- Start date ≤ End date

#### Supporting Model 1: `nguoi_tham_gia` (Task Participant)

**Purpose**: M2M junction between nhan_vien and cong_viec with role tracking

**Fields**:
```
nguoi_tham_gia
├── Relationships
│   ├── cong_viec_id → cong_viec [Required, Cascade]
│   └── nhan_vien_id → nhan_vien [Required]
│
├── Role & Timeline
│   ├── vai_tro (Role: phu_trach, thuc_hien, ho_tro, kiem_tra, khac)
│   ├── ngay_bat_dau (Start Date) [Required]
│   ├── ngay_ket_thuc (End Date)
│   └── so_gio_du_kien (Estimated Hours)
│
├── Denormalized Fields (Computed/Related, read-only)
│   ├── du_an_id → via cong_viec_id.du_an_id
│   ├── ten_cong_viec → via cong_viec_id.ten_cong_viec
│   ├── ten_nhan_vien → via nhan_vien_id.ho_va_ten
│   └── phong_ban_id → via nhan_vien_id.phong_ban_id
│
└── Logic
    - Unique constraint: Each employee added once per task
    - Creating vai_tro='phu_trach' auto-updates cong_viec.nguoi_phu_trach_id
```

#### Supporting Model 2: `bao_cao_tien_do` (Progress Report)

**Purpose**: Track task execution progress with hours and percentage

**Fields**:
```
bao_cao_tien_do
├── Relationships
│   ├── cong_viec_id → cong_viec [Required, Cascade]
│   └── nhan_vien_id → nhan_vien (Reporter) [Required]
│
├── Progress Data
│   ├── ngay_bao_cao (Report Date) [Defaults to today]
│   ├── noi_dung (Report Content)
│   ├── tien_do % (0-100) [Required, Validated 0-100]
│   └── so_gio (Hours Worked) [Required]
│
├── Issues & Attachments
│   ├── van_de_phat_sinh (Issues Encountered)
│   ├── giai_phap (Proposed Solution)
│   ├── file_dinh_kem (Attached File, Binary)
│   └── ten_file (Filename)
│
├── Denormalized (Computed/Related, read-only)
│   ├── du_an_id → via cong_viec_id.du_an_id
│   └── ten_cong_viec → via cong_viec_id.ten_cong_viec
│
└── Auto-Actions on Create
    - If tien_do == 100 → cong_viec.trang_thai = 'hoan_thanh'
    - If tien_do > 0 & cong_viec.trang_thai == 'moi' → 'dang_thuc_hien'
```

#### Supporting Model 3: `phan_bo_nguon_luc` (Resource Allocation)

**Purpose**: Track resource usage (human, financial, materials) against project or task

**Fields**:
```
phan_bo_nguon_luc
├── Identity
│   └── ten_nguon_luc (Resource Name)
│
├── Classification
│   └── loai_nguon_luc (Type: nhan_luc, tai_chinh, vat_tu, thiet_bi, khac)
│
├── Allocation & Scope
│   ├── du_an_id → du_an (Project) [Optional]
│   ├── cong_viec_id → cong_viec (Task, Filtered by du_an_id) [Optional]
│   └── nhan_vien_id → nhan_vien [Optional - for human resources]
│
├── Quantity & Cost
│   ├── so_luong (Quantity, default=1)
│   ├── don_vi (Unit)
│   ├── don_gia (Unit Price)
│   └── chi_phi (Total Cost - Computed: so_luong × don_gia)
│
├── Timeline
│   ├── ngay_phan_bo (Allocation Date) [Defaults to today]
│   ├── ngay_bat_dau (Usage Start)
│   └── ngay_ket_thuc (Usage End)
│
├── Status
│   └── trang_thai (Status: du_kien, da_phan_bo, dang_su_dung, da_hoan_tra)
│
└── Constraints & Logic
    - Must have at least du_an_id OR cong_viec_id
    - If cong_viec_id set → du_an_id auto-filled from cong_viec.du_an_id
```

---

### 3. QUAN_LY_KHACH_HANG - Customer Management

#### Core Entity: `khach_hang` (Customer)

**Fields**:
```
khach_hang
├── Identity
│   ├── ma_khach_hang (Customer Code, Auto-generated from sequence)
│   └── ten_khach_hang (Customer Name) [Required]
│
├── Contact & Location
│   ├── nguoi_lien_he (Contact Person)
│   ├── email
│   ├── dien_thoai (Phone)
│   └── dia_chi (Address)
│
├── Business Info
│   ├── nguon (Source: facebook, zalo, website, gioi_thieu, khac)
│   ├── mo_ta (Description)
│   ├── tong_ngan_sach (Total Budget in VND)
│   └── active (Status flag)
│
├── Customer Classification
│   ├── rank (Tier: dong, bac, vang) [Default: dong]
│   └── trang_thai_hop_tac (Cooperation Status: tiem_nang, dang_hop_tac, tam_ngung, ngung_hop_tac)
│
├── Organizational Links
│   ├── nhan_vien_phu_trach_id → nhan_vien (Responsible Employee)
│   ├── parent_khach_hang_id → khach_hang (Parent Customer for subsidiaries)
│   └── subsidiary_khach_hang_ids → khach_hang (Child contacts/branches) [One2many]
│
├── Computed Metrics
│   ├── so_du_an (Project Count)
│   ├── so_du_an_dang_thuc_hien (In-progress Projects)
│   ├── so_cong_viec (Task Count)
│   ├── so_cong_viec_dang_thuc_hien (In-progress Tasks)
│   ├── so_lan_tuong_tac (Total Interactions)
│   ├── so_tuong_tac_qua_han (Overdue Interactions)
│   ├── so_ban_ghi_trung (Duplicate Records Found)
│   ├── lan_tuong_tac_cuoi (Last Interaction Datetime)
│   └── lan_tuong_tac_cuoi_index (Last Interaction Date)
│
└── One2many Collections
    ├── du_an_ids (Projects for this Customer)
    ├── cong_viec_ids (Tasks for this Customer)
    ├── tuong_tac_ids (Interaction History)
    └── subsidiary_khach_hang_ids (Sub-contacts)
```

#### Extended Models in Customer Module

**Model 1: `khach_hang_tuong_tac` (Customer Interaction)**

**Purpose**: Log all customer interactions (calls, meetings, emails)

**Fields**:
```
khach_hang_tuong_tac
├── Relationships
│   ├── khach_hang_id → khach_hang [Required, Cascade]
│   └── nhan_vien_id → nhan_vien (Responsible Employee)
│
├── Interaction Data
│   ├── tieu_de (Title) [Required]
│   ├── loai_tuong_tac (Type: goi_dien, gap_mat, email, khac)
│   ├── ngay_lien_he (Contact DateTime) [Defaults to now]
│   └── noi_dung (Interaction Notes)
│
├── Outcome & Follow-up
│   ├── ket_qua (Result: chot_hop_dong, hen_gap_lai, can_theo_doi, khong_quan_tam)
│   ├── hen_lien_he_tiep (Next Contact Date)
│   ├── trang_thai (Status: planned, done, cancel)
│   └── qua_han (Overdue - Computed: planned + past next_contact_date)
│
└── Order: ngay_lien_he descending (latest first)
```

**Model 2: `lich_hen` (Appointment)**

**Purpose**: Schedule appointments, auto-create tasks

**Fields**:
```
lich_hen [Inherits khach_hang_tuong_tac via _inherits]
├── Parent Relationship
│   └── tuong_tac_id → khach_hang_tuong_tac [Cascade delete]
│
├── Appointment Specific
│   ├── dia_diem (Location/Address)
│   ├── trang_thai_hen (Appointment Status: sap_dien_ra, da_hoan_thanh, huy)
│   └── cong_viec_id → cong_viec (Auto-created Task)
│
└── _tao_cong_viec() Auto-Creation Logic
    When appointment status changes → creates/updates linked task:
    - trang_thai='sap_dien_ra' → Task tien_do=20%
    - trang_thai='da_hoan_thanh' → Task tien_do=100% (and status='hoan_thanh')
    - trang_thai='huy' → Task tien_do=0%
```

**Model 3: `bao_gia` (Quotation)**

**Purpose**: Generate quotes for customers [Brief mention - linked to tasks]

---

## Data Model Relationships

### Relationship Diagram: All Cross-Module Links

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          NHAN_VIEN (Employee)                               │
│                         [quan_ly_nhan_su base]                              │
└─────────────────────────────────────────────────────────────────────────────┘
                    ▲                                    ▲
                    │                                    │
        phong_ban_id│                          quan_ly_id│ (self-ref)
        chuc_vu_id  │                                    │
                    │                                    │
     ┌──────────────┘                    ┌───────────────┘
     │
     │                    Reverse Relations (from quan_ly_khach_hang/cong_viec):
     │                    - khach_hang.nhan_vien_phu_trach_id → nhan_vien
     │                    - du_an.nguoi_quan_ly_id → nhan_vien
     │                    - cong_viec.nguoi_phu_trach_id → nhan_vien
     │                    - nguoi_tham_gia.nhan_vien_id → nhan_vien
     │                    - bao_cao_tien_do.nhan_vien_id → nhan_vien
     │
     ▼
┌──────────────────────┐
│  PHONG_BAN (Dept)    │
│   CHUC_VU (Position) │
│   HOP_DONG (Contract)│
│  CHAM_CONG (Attend)  │
│  DANH_GIA (Review)   │
│   DAO_TAO (Training) │
└──────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                          DU_AN (Project)                                    │
│                      [quan_ly_cong_viec base]                               │
└─────────────────────────────────────────────────────────────────────────────┘
     │                                           │
     │ nguoi_quan_ly_id→nhan_vien                │ khach_hang_id (extended)
     │                                           ▼
     │                                   ┌─────────────────────┐
     │                                   │  KHACH_HANG         │
     │                                   │  (Customer)         │
     │                                   │  [quan_ly_khach_hang│
     │                                   │   base]             │
     │                                   └────────┬────────────┘
     │                                           │
     │                                           │ nhan_vien_phu_trach_id
     │                                           │   →nhan_vien
     │                                           │
     │ One2many: cong_viec_ids                   │
     ├─────────────────────────────────────────────────────┐
     │                                           │          │
     ▼                                           │          │ One2many:
┌─────────────────────────────────────────┐   │    du_an_ids
│        CONG_VIEC (Task)                  │   │    cong_viec_ids
│     [quan_ly_cong_viec base]             │   │    tuong_tac_ids
│    Extended in quan_ly_khach_hang        │   │    subsidiary_khach_hang_ids
└──┬──────────────────────────────────────┘   │
   │                                           │
   ├─ nguoi_phu_trach_id→nhan_vien            │
   │                                           │
   ├─ khach_hang_id→khach_hang (extended)     │
   │  contact_person_id→khach_hang (extended) │
   │  nguon_phat_sinh={goi_dien,lich_hen...} │
   │                                           │
   ├─ One2many: nguoi_tham_gia_ids           │
   │         ↓↓↓                              │
   │   ┌──────────────────────────────────┐   │
   │   │ NGUOI_THAM_GIA (Participant)     │   │
   │   │ Junction M2M with nhan_vien      │   │
   │   │ vai_tro, ngay_bat_dau, etc.     │   │
   │   └──────────────────────────────────┘   │
   │                                           │
   ├─ One2many: bao_cao_tien_do_ids          │
   │         ↓↓↓                              │
   │   ┌──────────────────────────────────┐   │
   │   │ BAO_CAO_TIEN_DO (Progress Report)│   │
   │   │ nhan_vien_id→nhan_vien           │   │
   │   │ tien_do %, so_gio tracked        │   │
   │   │ Auto-updates task status         │   │
   │   └──────────────────────────────────┘   │
   │                                           │
   └─ One2many: nguon_luc_ids                │
           ↓↓↓                                 │
   ┌──────────────────────────────────┐       │
   │ PHAN_BO_NGUON_LUC (Resources)   │       │
   │ Can link to du_an OR cong_viec  │       │
   │ loai_nguon_luc, chi_phi tracked │       │
   └──────────────────────────────────┘       │
                                              │
                                              │
      ┌───────────────────────────────────────┘
      │
      ▼
  ┌──────────────────────────────────────┐
  │  KHACH_HANG_TUONG_TAC (Interaction)  │
  │  ngay_lien_he, loai_tuong_tac        │
  │  ket_qua, hen_lien_he_tiep           │
  │  trang_thai, qua_han (computed)      │
  │  One2many from khach_hang            │
  └────────┬─────────────────────────────┘
           │
           │ _inherits (special inheritance)
           ▼
  ┌──────────────────────────────────────┐
  │     LICH_HEN (Appointment)            │
  │     dia_diem, trang_thai_hen          │
  │     cong_viec_id (auto-linked)        │
  │     Auto-creates cong_viec on status  │
  └──────────────────────────────────────┘

```

---

## Complete Workflow Sequence

### Phase 1: Setup & Initialization (Admin/Manager Tasks)

**Step 1.1: Create Organizational Structure**
- Create `phong_ban` (Departments) - can be hierarchical
- Create `chuc_vu` (Job Positions) - basic master data

**Step 1.2: Create Employees**
- Create `nhan_vien` records with:
  - ma_nhan_vien (unique)
  - ho_va_ten, ngay_sinh, etc.
  - Link to phong_ban_id, chuc_vu_id
  - Set quan_ly_id for reporting lines
- Later: Create `hop_dong` (employment contracts) on nhan_vien

**Step 1.3: Optional - Link Employees to Users**
- (In Customer module): Set nhan_vien.user_id to link with Odoo user accounts
- This enables permission-based access control

---

### Phase 2: Project Management Workflow (Project Manager/Team Lead)

**Step 2.1: Create Project**
```
du_an created:
- ma_du_an, ten_du_an (unique code)
- ngay_bat_dau, ngay_ket_thuc
- nguoi_quan_ly_id = project manager nhan_vien
- ngan_sach (allocated budget)
- trang_thai = 'chuan_bi' (Preparing)
```

**Step 2.2: Create Tasks for Project**
```
FOR EACH cong_viec in project:
  - ma_cong_viec (unique)
  - ten_cong_viec
  - ngay_bat_dau, ngay_ket_thuc (must be within du_an dates)
  - du_an_id = parent project (REQUIRED)
  - nguoi_phu_trach_id = main task owner nhan_vien
  - trang_thai = 'moi' (New)
  - ke_hoach_gio (planned hours)
```

**Step 2.3: Assign Task Participants**
```
FOR EACH task, add nguoi_tham_gia:
  - nhan_vien_id = team member
  - vai_tro = 'phu_trach' OR 'thuc_hien' OR 'ho_tro' OR 'kiem_tra'
  - ngay_bat_dau, ngay_ket_thuc (participation period)
  - so_gio_du_kien (estimated hours for this person)

SYSTEM ACTION:
  - If vai_tro == 'phu_trach' → cong_viec.nguoi_phu_trach_id auto-updates
  - Each employee can only be added once per task (unique constraint)
```

**Step 2.4: Allocate Resources**
```
FOR EACH phan_bo_nguon_luc:
  - ten_nguon_luc, loai_nguon_luc
  - du_an_id = project OR cong_viec_id = task (at least one required)
  - nhan_vien_id (if human resource allocation)
  - so_luong, don_gia
  - trang_thai = 'du_kien' (Planned)

SYSTEM ACTION:
  - chi_phi auto-calculated: so_luong × don_gia
  - If cong_viec_id set → du_an_id auto-filled
  - du_an.chi_phi_thuc_te sums all allocated resource costs
```

**Step 2.5: Update Project Status**
```
- Project remains 'chuan_bi' until tasks start
- When first task starts → du_an.trang_thai = 'dang_thuc_hien'
- When all non-cancelled tasks complete → du_an.trang_thai = 'hoan_thanh'
  (Auto via _cron_sync_project_status)
```

---

### Phase 3: Customer Acquisition & Relationship Building (Sales/CRM)

**Step 3.1: Create Customer Record**
```
khach_hang created:
- ten_khach_hang (required)
- nguoi_lien_he (primary contact at customer)
- email, dien_thoai, dia_chi
- nguon (how they were acquired: facebook, zalo, website, gioi_thieu, khac)
- nhan_vien_phu_trach_id = assigned sales employee
- rank = 'dong' (default Bronze - can be upgraded to bac/vang)
- trang_thai_hop_tac = 'tiem_nang' (Prospect)
- active = True

SYSTEM ACTION:
- ma_khach_hang auto-generated from sequence
- Employee relationships automatically appear in nhan_vien.khach_hang_phu_trach_ids
```

**Step 3.2: Create Interaction/Contact Records**
```
WHEN employee contacts customer → Create khach_hang_tuong_tac:
- tieu_de (e.g., "First call with ABC Company")
- loai_tuong_tac = 'goi_dien' | 'gap_mat' | 'email' | 'khac'
- ngay_lien_he = contact datetime
- noi_dung = conversation notes
- ket_qua = 'hen_gap_lai' (schedule meeting) OR 'chot_hop_dong' (deal closed)
           OR 'can_theo_doi' (follow up) OR 'khong_quan_tam' (not interested)
- hen_lien_he_tiep = next follow-up date (if applicable)
- trang_thai = 'planned' (waiting for next contact)

SYSTEM ACTION:
- khach_hang.so_lan_tuong_tac auto-counts all interactions
- khach_hang.lan_tuong_tac_cuoi = latest interaction datetime
- khach_hang.so_tuong_tac_qua_han counts planned interactions past next_date
```

**Step 3.3: Schedule Appointment (if decision was hen_gap_lai)**
```
CREATE lich_hen:
- Inherits from khach_hang_tuong_tac, so fields like tieu_de, loai_tuong_tac,
  khach_hang_id, nhan_vien_id come from parent
- dia_diem (meeting location)
- trang_thai_hen = 'sap_dien_ra' (Upcoming)
- cong_viec_id = NULL initially

SYSTEM ACTION on Status Change:
  IF trang_thai_hen changes:
    - 'sap_dien_ra' → Auto-create cong_viec with tien_do=20%, so_gio=0
                       (task is upcoming/in prep)
    - 'da_hoan_thanh' → Update cong_viec to tien_do=100%, trang_thai='hoan_thanh'
                        (appointment completed successfully)
    - 'huy' → Update cong_viec to tien_do=0%
              (appointment cancelled)
```

**Step 3.4: Update Customer Cooperation Status**
```
As relationship progresses:
- trang_thai_hop_tac = 'tiem_nang' → 'dang_hop_tac' (when first order/project starts)
                    → 'tam_ngung' (if paused deliberately)
                    → 'ngung_hop_tac' (relationship ended)

- rank can be upgraded: 'dong' → 'bac' → 'vang' based on deal value
  (affects task prioritization: vang=rank set on task→do_uu_tien='rat_cao')
```

---

### Phase 4: Link Customer to Projects & Tasks (Integration Point)

**Step 4.1: Create Project for Customer**
```
CREATE du_an with:
- ten_du_an (e.g., "Website Redesign for ABC Corp")
- khach_hang_id = the customer [Extended field]
- nguoi_quan_ly_id = project manager
- ngay_bat_dau, ngay_ket_thuc
- ngan_sach (what's budgeted for this customer project)

SYSTEM ACTION:
- Customer metric: so_du_an auto-increases
- Customer metric: so_du_an_dang_thuc_hien counts if project status not in (hoan_thanh, huy)
```

**Step 4.2: Create Tasks for Customer Project**
```
CREATE cong_viec with:
- ten_cong_viec
- du_an_id = project for customer
- khach_hang_id = same as parent du_an [EXTENDED]
- contact_person_id = if customer has sub-contacts (via parent_khach_hang_id)
                      [filtered domain: subsidiary contacts only]
- nguon_phat_sinh = 'bao_gia' | 'lich_hen' | 'goi_dien' | 'thu_cong'
  (where this task originated from in CRM process)
- nguoi_phu_trach_id = task owner

SYSTEM ACTION:
- Task shows in khach_hang.cong_viec_ids
- Customer metric: so_cong_viec auto-increases
- Customer metric: so_cong_viec_dang_thuc_hien counts if status not in (hoan_thanh, huy_bo)
```

**Step 4.3: Link Quotation (Optional)**
```
CREATE bao_gia:
- For customer khach_hang
- Links to task cong_viec (via many2one, not shown in detail)
- Quotation details tracked separately
```

---

### Phase 5: Task Execution & Progress Tracking

**Step 5.1: Team Works on Task**
```
As team executes cong_viec:
- Task auto-transitions to 'dang_thuc_hien' when first progress report created
  with tien_do > 0
- Team members complete assigned work (nguoi_tham_gia vai_tro='thuc_hien')
```

**Step 5.2: Submit Progress Report**
```
CREATE bao_cao_tien_do:
- cong_viec_id = task
- nhan_vien_id = employee reporting (usually vai_tro='thuc_hien' or 'phu_trach')
- ngay_bao_cao = report date (defaults to today)
- tien_do = % complete (0-100, required)
- so_gio = hours worked since last report
- noi_dung = what was accomplished
- van_de_phat_sinh = any blockers (optional)
- giai_phap = proposed solutions (optional)
- file_dinh_kem = attachments (optional)

SYSTEM ACTIONS:
  IF tien_do == 0 → task stays in 'moi'
  IF 0 < tien_do < 100 & task.trang_thai == 'moi' → task → 'dang_thuc_hien'
  IF tien_do == 100 → task → 'hoan_thanh'
  cong_viec.thuc_te_gio = SUM(all bao_cao.so_gio)
  cong_viec.tien_do = latest bao_cao.tien_do %
```

**Step 5.3: Multiple Reports Per Task**
```
Multiple bao_cao_tien_do can be created for one task (day-by-day or week-by-week)
- System uses latest (ngay_bao_cao desc) for tien_do %
- So_gio is cumulative (sum of all reports)
- This tracks actual hours vs ke_hoach_gio
```

---

### Phase 6: Project Completion & Close-out

**Step 6.1: All Tasks Complete**
```
When all cong_viec in du_an reach trang_thai='hoan_thanh':
- du_an.ti_le_hoan_thanh = 100%
- du_an.trang_thai auto-updates to 'hoan_thanh' (via CRON daily)
- du_an.chi_phi_thuc_te is final (sum of all resource allocations)
```

**Step 6.2: Update Customer Status**
```
After project completion:
- If successful → Update khach_hang.trang_thai_hop_tac = 'dang_hop_tac' (ongoing)
- If no more projects → could transition to 'tam_ngung' or 'ngung_hop_tac'
- Update khach_hang.lan_tuong_tac_cuoi (last interaction timestamp)
```

**Step 6.3: Generate Reports**
```
- Efficiency reports: Task thuc_te_gio vs ke_hoach_gio
- Resource utilization: SUM(phan_bo_nguon_luc.chi_phi) vs du_an.ngan_sach
- Employee productivity: nhan_vien.bao_cao_tien_do aggregate
- Customer satisfaction: khach_hang interactions & final quality metrics
```

---

## Data Flows Between Modules

### 1. NHAN_SU → CONG_VIEC (Employee to Task/Project)

**Direct Relationships**:
```
nhan_vien.id ──────┐
                   ├─→ du_an.nguoi_quan_ly_id (project manager)
                   │
                   ├─→ cong_viec.nguoi_phu_trach_id (task owner)
                   │
                   ├─→ nguoi_tham_gia.nhan_vien_id (task participants)
                   │
                   └─→ bao_cao_tien_do.nhan_vien_id (progress reporter)
                       ↓
                       + Reads nhan_vien.ho_va_ten, nhan_vien.phong_ban_id
                         (stored in bao_cao_tien_do via related fields)
                       
phan_bo_nguon_luc.nhan_vien_id ──────→ (optional human resource allocation)
```

**Data Flow Direction**: ← Unidirectional (Task references Employee)

**Reverse References** (auto-created one2many):
```
nhan_vien.khach_hang_phu_trach_ids ← khach_hang[nhan_vien_phu_trach_id=this_nhan_vien]
nhan_vien.du_an_quan_ly_ids ← du_an[nguoi_quan_ly_id=this_nhan_vien]
```

**Sample Data Flow Scenario**:
```
1. Create nhan_vien: "Nguyễn Văn A" [ID=1] in "Phòng IT"
2. Create du_an: "Website" with nguoi_quan_ly_id=1
   → nhan_vien[1].du_an_quan_ly_ids now includes this project
3. Create cong_viec: "Frontend" with du_an_id=project, nguoi_phu_trach_id=1
4. Create nguoi_tham_gia: Add nhan_vien[2] with vai_tro='thuc_hien'
   → nhan_vien[2].phong_ban_id automatically denormalized here
5. nhan_vien[1] creates bao_cao_tien_do: tien_do=50%, so_gio=4
   → cong_viec.thuc_te_gio becomes 4, cong_viec.tien_do becomes 50%
```

---

### 2. CONG_VIEC → KHACH_HANG (Task/Project to Customer)

**Extended Field Relationships** (quan_ly_khach_hang extends du_an & cong_viec):
```
du_an.khach_hang_id ←────────────── khach_hang.id (Many2one, optional)
                    
cong_viec.khach_hang_id ←──────────── khach_hang.id (Many2one, optional)
cong_viec.contact_person_id ←──────── khach_hang.id (subdomain: subsidiaries only)
cong_viec.nguon_phat_sinh ←──────────  origin of task
                                      (goi_dien, lich_hen, bao_gia, thu_cong)
```

**Data Flow Direction**: ← PULL from khach_hang into task/project

**Reverse References** (auto-created one2many):
```
khach_hang.du_an_ids ← du_an[khach_hang_id=this_khach_hang]
                       (all projects for this customer)

khach_hang.cong_viec_ids ← cong_viec[khach_hang_id=this_khach_hang]
                           (all tasks for this customer)
```

**Sample Data Flow Scenario**:
```
1. Create khach_hang: "ABC Corporation" [khach_hang_id=10]
   nhan_vien_phu_trach_id=1 (Nguyễn Văn A)
2. Create du_an: "Website Redesign" with khach_hang_id=10
   → khach_hang[10].du_an_ids now shows this project
3. Create cong_viec: "Frontend Mockup" 
   with du_an_id=project, khach_hang_id=10, contact_person_id=10
   → cong_viec form shows khach_hang info populated
   → khach_hang[10].cong_viec_ids now shows this task
4. Appointment scheduled via lich_hen
   → auto-creates cong_viec with:
     - khach_hang_id = appointment's khach_hang_id
     - nguon_phat_sinh = 'lich_hen'
     - ten_cong_viec = "Lịch hẹn KH ABC Corporation"
```

---

### 3. KHACH_HANG → NHAN_SU (Customer to Employee)

**Direct Relationships**:
```
khach_hang.nhan_vien_phu_trach_id ───→ nhan_vien.id
```

**Data Flow Direction**: ← PULL from nhan_vien into customer

**Reverse References** (auto-created one2many):
```
nhan_vien.khach_hang_phu_trach_ids ← khach_hang[nhan_vien_phu_trach_id=this_nhan_vien]
                                     (all customers managed by this employee)
```

**Extended User Linking**:
```
nhan_vien.user_id ───→ res.users.id (Odoo user account)
                        (enables permission control)
```

---

### 4. Inter-Task Progress Metrics

**Cascade Computation Chain**:
```
bao_cao_tien_do (Progress Report)
  ├─ tien_do % (user input: 0-100)
  │  └─ affects cong_viec.tien_do (COMPUTE: latest bao_cao.tien_do)
  │
  └─ so_gio (user input: hours)
     └─ affects cong_viec.thuc_te_gio (COMPUTE: SUM(bao_cao.so_gio))


cong_viec (Task)
  ├─ tien_do % (from latest bao_cao)
  │  └─ affects du_an.ti_le_hoan_thanh (COMPUTE: % of completed tasks)
  │
  └─ trang_thai (auto-updated when bao_cao created)
     ├─ if tien_do == 100 → 'hoan_thanh'
     ├─ if 0 < tien_do < 100 → 'dang_thuc_hien'
     └─ affects du_an.trang_thai (CRON: if all tasks hoan_thanh → project hoan_thanh)


khach_hang (Customer)
  ├─ so_cong_viec (COMPUTE: COUNT(cong_viec[khach_hang_id=this]))
  │  └─ so_cong_viec_dang_thuc_hien (COMPUTE: COUNT where trang_thai not in (hoan_thanh, huy_bo))
  │
  ├─ so_du_an (COMPUTE: COUNT(du_an[khach_hang_id=this]))
  │  └─ so_du_an_dang_thuc_hien (COMPUTE: COUNT where trang_thai not in (hoan_thanh, huy))
  │
  └─ tuong_tac_ids
     ├─ so_lan_tuong_tac (COMPUTE: COUNT(khach_hang_tuong_tac))
     ├─ lan_tuong_tac_cuoi (COMPUTE: MAX(ngay_lien_he))
     └─ so_tuong_tac_qua_han (COMPUTE: COUNT where trang_thai='planned' & hen_lien_he_tiep < today)
```

---

## Business Rules & Validations

### Employee (nhan_vien)

| Rule | Validation | Action |
|------|-----------|--------|
| Unique Employee ID | ma_nhan_vien UNIQUE constraint | DB enforces, form shows error |
| Unique Identity | cmnd_cccd UNIQUE constraint | DB enforces, form shows error |
| Manager Hierarchy | quan_ly_id can be self-reference | Allows multi-level reporting chains |

### Project (du_an)

| Rule | Validation | Action |
|------|-----------|--------|
| Unique Project Code | ma_du_an UNIQUE constraint | DB enforces |
| Valid Timeline | Check in _check_dates() | Must: ngay_bat_dau ≤ ngay_ket_thuc |

### Task (cong_viec)

| Rule | Validation | Action |
|------|-----------|--------|
| Unique Task Code | ma_cong_viec UNIQUE constraint | DB enforces |
| Task in Project Scope | Check ngay_bat_dau ≥ du_an.ngay_bat_dau | Prevents tasks before project start |
| Task End Before Project | Check ngay_ket_thuc ≤ du_an.ngay_ket_thuc | Prevents tasks after project end |
| Valid Timeline | Check ngay_bat_dau ≤ ngay_ket_thuc | Within-task date validation |
| Auto Status Update | When bao_cao_tien_do created | moi→dang_thuc_hien (when 0<tien_do<100), →hoan_thanh (when tien_do=100) |

### Task Participant (nguoi_tham_gia)

| Rule | Validation | Action |
|------|-----------|--------|
| Unique per Task | UNIQUE(cong_viec_id, nhan_vien_id) | Each employee once per task |
| Participant Dates Valid | Check ngay_bat_dau ≤ ngay_ket_thuc | Must be valid date range |
| Within Task Dates | Check participation dates within task dates | Prevents participation outside task timeline |
| Auto-update Task Owner | If vai_tro='phu_trach' created | Auto-sets cong_viec.nguoi_phu_trach_id |

### Progress Report (bao_cao_tien_do)

| Rule | Validation | Action |
|------|-----------|--------|
| Valid Progress % | Check 0 ≤ tien_do ≤ 100 | Raises ValidationError if out of range |
| Auto-Complete Task | If tien_do == 100 on create | Auto-set cong_viec.trang_thai = 'hoan_thanh' |
| Auto-Start Task | If tien_do > 0 & task.trang_thai='moi' on create | Auto-set cong_viec.trang_thai = 'dang_thuc_hien' |

### Resource Allocation (phan_bo_nguon_luc)

| Rule | Validation | Action |
|------|-----------|--------|
| Has Target | Check du_an_id OR cong_viec_id | Must have at least one target |
| Task in Project | If cong_viec_id set | Check cong_viec.du_an_id == du_an_id |
| Auto-fill Project | If cong_viec_id populated | Auto-fill du_an_id from cong_viec.du_an_id |

### Project Auto-Status (Cron Job)

| Condition | Action |
|----------|--------|
| All tasks 'hoan_thanh' | Project → 'hoan_thanh' |
| Any task 'dang_thuc_hien' & project in ('chuan_bi', 'hoan_thanh') | Project → 'dang_thuc_hien' |

### Customer (khach_hang)

| Rule | Validation | Action |
|------|-----------|--------|
| Auto ID Generation | ma_khach_hang sequence | On create, if ma='New', generate from ir.sequence |
| Duplicate Detection | _compute_so_ban_ghi_trung | Count records with same email/phone (excluding self) |

### Interaction (khach_hang_tuong_tac)

| Rule | Validation | Action |
|------|-----------|--------|
| Auto Overdue Flag | qua_han computed | = (trang_thai='planned' AND hen_lien_he_tiep < today) |

### Appointment (lich_hen)

| Rule | Validation | Action |
|------|-----------|--------|
| Auto Task Creation | On status change | Creates/updates linked cong_viec with progress % |
| Status-Specific Progress | trang_thai_hen maps to tien_do % | sap_dien_ra→20%, da_hoan_thanh→100%, huy→0% |
| Cascade Delete | On lich_hen.delete() | Also deletes linked cong_viec |

---

## Computed Fields & Metrics

### Employee (nhan_vien) - Extended

```python
# Computed by quan_ly_khach_hang extension:
so_khach_hang_phu_trach = COUNT(khach_hang[nhan_vien_phu_trach_id=this])
so_du_an_quan_ly = COUNT(du_an[nguoi_quan_ly_id=this])
```

### Project (du_an)

```python
# Computed periodically:
so_luong_cong_viec = COUNT(cong_viec[du_an_id=this])
ti_le_hoan_thanh = (COUNT(cong_viec[trang_thai='hoan_thanh']) / 
                     COUNT(cong_viec[du_an_id=this])) * 100
                   = 0 if no tasks

chi_phi_thuc_te = SUM(phan_bo_nguon_luc[du_an_id=this].chi_phi)
```

### Task (cong_viec)

```python
# Updated dynamically:
thuc_te_gio = SUM(bao_cao_tien_do[cong_viec_id=this].so_gio)
tien_do = (latest bao_cao_tien_do[cong_viec_id=this, order by ngay_bao_cao desc]).tien_do
        = 0 if no reports

# Related (read-only):
du_an_id                           # parent project
ten_cong_viec from self             # redundant with _rec_name
```

### Task Participant (nguoi_tham_gia)

```python
# Related/Denormalized (for display efficiency):
du_an_id = cong_viec_id.du_an_id
ten_cong_viec = cong_viec_id.ten_cong_viec
ten_nhan_vien = nhan_vien_id.ho_va_ten
phong_ban_id = nhan_vien_id.phong_ban_id
```

### Progress Report (bao_cao_tien_do)

```python
# Related (read-only):
du_an_id = cong_viec_id.du_an_id
ten_cong_viec = cong_viec_id.ten_cong_viec
```

### Customer (khach_hang)

```python
# Computed (all computed fields):
so_du_an = COUNT(du_an[khach_hang_id=this])
so_du_an_dang_thuc_hien = COUNT(du_an[khach_hang_id=this, 
                                       trang_thai NOT IN ('hoan_thanh', 'huy')])

so_cong_viec = COUNT(cong_viec[khach_hang_id=this])
so_cong_viec_dang_thuc_hien = COUNT(cong_viec[khach_hang_id=this, 
                                              trang_thai NOT IN ('hoan_thanh', 'huy_bo')])

so_lan_tuong_tac = COUNT(khach_hang_tuong_tac[khach_hang_id=this])
so_tuong_tac_qua_han = COUNT(khach_hang_tuong_tac[khach_hang_id=this,
                                                   trang_thai='planned',
                                                   hen_lien_he_tiep < today])

so_ban_ghi_trung = COUNT(khach_hang[id != this,
                                    (email=this.email OR dien_thoai=this.dien_thoai)])
                 = 0 if no email/phone

lan_tuong_tac_cuoi = MAX(khach_hang_tuong_tac[khach_hang_id=this].ngay_lien_he)
lan_tuong_tac_cuoi_index = lan_tuong_tac_cuoi.date()  # for indexing
```

### Interaction (khach_hang_tuong_tac)

```python
# Computed:
qua_han = (trang_thai == 'planned' AND 
           hen_lien_he_tiep is not null AND 
           hen_lien_he_tiep < today)
```

---

## User Actions & Workflows

### Customer View Smart Buttons

```xml
<button type="object" name="action_xem_du_an" 
        class="oe_stat_button" icon="fa-folder-open">
    <field name="so_du_an" string="Dự án" widget="statinfo"/>
</button>
→ Opens list of all projects for this customer
  Domain: [('khach_hang_id', '=', customer_id)]
```

```xml
<button type="object" name="action_xem_cong_viec" 
        class="oe_stat_button" icon="fa-tasks">
    <field name="so_cong_viec" string="Công việc" widget="statinfo"/>
    <field name="so_cong_viec_dang_thuc_hien" string="Đang thực hiện" widget="statinfo"/>
</button>
→ Opens list of all tasks for this customer
  Domain: [('khach_hang_id', '=', customer_id)]
```

```xml
<button type="object" name="action_xem_tuong_tac" 
        class="oe_stat_button" icon="fa-comments">
    <field name="so_lan_tuong_tac" string="Tương tác" widget="statinfo"/>
</button>
→ View interaction history
```

```xml
<button type="object" name="action_tao_du_an_nhanh" 
        string="Tạo dự án nhanh" class="oe_highlight"/>
→ Quick-create project for this customer
  Context: {'default_khach_hang_id': customer_id}
```

```xml
<button type="object" name="action_merge_duplicate_khach_hang" 
        string="Gộp khách hàng trùng" groups="quan_ly_khach_hang.group_khach_hang_manager"/>
→ Admin: Merge duplicate customer records
```

### Employee View Smart Buttons (Extended)

```xml
<button type="object" name="action_xem_khach_hang_phu_trach" 
        class="oe_stat_button" icon="fa-users">
    <field name="so_khach_hang_phu_trach" string="Khách hàng" widget="statinfo"/>
</button>
→ View all customers this employee manages
  Domain: [('nhan_vien_phu_trach_id', '=', employee_id)]
```

```xml
<button type="object" name="action_xem_du_an_quan_ly" 
        class="oe_stat_button" icon="fa-folder-open">
    <field name="so_du_an_quan_ly" string="Dự án" widget="statinfo"/>
</button>
→ View all projects this employee manages
  Domain: [('nguoi_quan_ly_id', '=', employee_id)]
```

### Project/Task Context Filters

**When assigning task to customer:**
At form load, `khach_hang_id` field is empty.
Once selected:
```xml
<field name="contact_person_id" 
        domain="[('parent_khach_hang_id', '=', khach_hang_id)]" 
        attrs="{'invisible': [('khach_hang_id', '=', False)]}"/>
```
→ contact_person_id field becomes visible
→ Domain filters to show only subsidiary contacts of selected customer

---

## Workflow State Machine

### Project States

```
[chuan_bi] ──→ [dang_thuc_hien] ──→ [hoan_thanh]
    ↓              ↓                    ↑
    └──→ [tam_dung] ───→ [dang_thuc_hien] ┘
    
    Any ──→ [huy_bo] (cancellation)
```

**Triggers**:
- User manually changes `trang_thai` (clickable statusbar)
- Auto-transition: When tasks update (CRON job daily)

### Task States

```
[moi] ──→ [dang_thuc_hien] ──→ [hoan_thanh]
  ↓           ↓                    
  └─→ [tam_dung] ──→ [dang_thuc_hien] ┘
  
  Any ──→ [huy_bo]
```

**Triggers**:
- User manually changes `trang_thai`
- Auto-transition: When `bao_cao_tien_do` created with tien_do > 0 (becomes dang_thuc_hien)
- Auto-transition: When `bao_cao_tien_do` created with tien_do == 100 (becomes hoan_thanh)

### Customer Cooperation Status

```
[tiem_nang] ──→ [dang_hop_tac] ──→ [ngung_hop_tac]
                      ↓
                 [tam_ngung] ──→ [dang_hop_tac]
```

**Manual Triggers**:
- User changes `trang_thai_hop_tac` via statusbar
- Reflects decision/phase in sales workflow

### Interaction State

```
[planned] ──→ [done]
    ↓
 [cancel]
```

**Manual Triggers**:
- action_mark_done() button
- action_mark_cancel() button
- action_bulk_mark_done() for bulk operations
- action_bulk_postpone_2_days() to extend follow-up dates

---

## Summary: Data Integration Example

### Complete User Journey Scenario

**Scenario**: Import a customer, create a project with tasks, and track progress

```
DAY 1:
═════
1. HR creates employee:
   nhan_vien: ID=100, ma_nhan_vien="NV001", ho_va_ten="Trần A"
   phong_ban_id=phong_ban[IT], chuc_vu_id=chuc_vu[Developer]

2. Sales creates customer:
   khach_hang: ID=200, ma_khach_hang="KH001", ten_khach_hang="ABC Corp"
   nhan_vien_phu_trach_id=100 (Trần A is account manager)
   trang_thai_hop_tac='tiem_nang', nguon='facebook'
   
   System: nhan_vien[100].khach_hang_phu_trach_ids now includes khach_hang[200]

3. Sales calls customer, logs interaction:
   khach_hang_tuong_tac: khach_hang_id=200, nhan_vien_id=100
   loai_tuong_tac='goi_dien', ket_qua='hen_gap_lai'
   hen_lien_he_tiep=tomorrow
   
   System: khach_hang[200].so_lan_tuong_tac=1, lan_tuong_tac_cuoi=now

DAY 2:
═════
4. Sales schedules appointment:
   lich_hen: khach_hang_id=200, nhan_vien_id=100
   trang_thai_hen='sap_dien_ra'
   
   System: Auto-creates cong_viec[CV001] with tien_do=20%, nguon_phat_sinh='lich_hen'

5. Update customer status:
   khach_hang[200].trang_thai_hop_tac='dang_hop_tac' (now an active lead)

DAY 3:
═════
6. Project Manager creates project:
   du_an: ID=1000, ma_du_an="DA001", ten_du_an="ABC Website"
   khach_hang_id=200, nguoi_quan_ly_id=100
   ngay_bat_dau=today, ngay_ket_thuc=+30days
   ngan_sach=100,000,000 VND
   
   System: 
   - nhan_vien[100].du_an_quan_ly_ids includes du_an[1000]
   - khach_hang[200].du_an_ids includes du_an[1000]
   - khach_hang[200].so_du_an=1, so_du_an_dang_thuc_hien=1

7. PM creates tasks:
   cong_viec[CV002]: "Backend API", du_an_id=1000, khach_hang_id=200
                    nguoi_phu_trach_id=100, ngay_bat_dau=today
   cong_viec[CV003]: "Frontend UI", du_an_id=1000, khach_hang_id=200
                    nguoi_phu_trach_id=100, ngay_bat_dau=+5days
   
   System:
   - cong_viec.trang_thai all='moi'
   - du_an[1000].so_luong_cong_viec=3 (including auto-created lich_hen task)
   - khach_hang[200].so_cong_viec=3

DAY 5:
═════
8. Backend dev adds themselves as participant:
   nguoi_tham_gia: cong_viec_id=CV002, nhan_vien_id=101 (Backend team)
   vai_tro='thuc_hien', ngay_bat_dau=today
   
   System: Record is created, unique constraint prevents duplicate

9. Dev starts work, submits first progress report:
   bao_cao_tien_do: cong_viec_id=CV002, nhan_vien_id=101
   tien_do=30%, so_gio=8, noi_dung="Database schema designed"
   
   System:
   - cong_viec[CV002].trang_thai changes from 'moi' → 'dang_thuc_hien'
   - cong_viec[CV002].tien_do=30%, thuc_te_gio=8
   - du_an[1000].ti_le_hoan_thanh=(1 dang_thuc_hien / 3 total)=33%
   - khach_hang[200].so_cong_viec_dang_thuc_hien=2 (CV002, CV003 started via appointment)

DAY 10:
══════
10. Resource allocation for project:
    phan_bo_nguon_luc: du_an_id=1000, loai_nguon_luc='tai_chinh'
    so_luong=1, don_gia=50,000,000, chi_phi=50,000,000
    
    System: du_an[1000].chi_phi_thuc_te=50,000,000 (vs ngan_sach=100M)

DAY 15:
══════
11. Multiple progress reports accumulate:
    bao_cao_tien_do reports for CV002: 30%→60%→100%
    bao_cao_tien_do reports for CV003: 20%→70%→100%
    bao_cao_tien_do reports for lich_hen task: 20%→100% (appointment happened)
    
    System (after reports):
    - Each task's trang_thai auto-set to 'hoan_thanh' when tien_do=100%
    - cong_viec[CV002].thuc_te_gio=SUM(8+10+4)=22 hours
    - cong_viec[CV003].thuc_te_gio=SUM(5+12+8)=25 hours
    - du_an[1000].ti_le_hoan_thanh=100% (all tasks complete)
    - CRON job daily checks: all tasks 'hoan_thanh' → du_an[1000].trang_thai='hoan_thanh'
    - khach_hang[200].so_cong_viec_dang_thuc_hien=0 (all complete)

DAY 20:
══════
12. Final interaction log:
    khach_hang_tuong_tac: khach_hang_id=200, nhan_vien_id=100
    loai_tuong_tac='email', ket_qua='chot_hop_dong'
    
    System:
    - khach_hang[200].so_lan_tuong_tac=2
    - khach_hang[200].lan_tuong_tac_cuoi=now

13. Upgrade customer:
    khach_hang[200].rank='bac' (Promotion to Silver tier)
    khach_hang[200].trang_thai_hop_tac='dang_hop_tac' (ongoing relationship)

FINAL STATE:
════════════
Employee (Trần A / nhan_vien[100]):
  - so_khach_hang_phu_trach = 1
  - du_an_quan_ly_ids = [1000]
  - so_du_an_quan_ly = 1

Project (ABC Website / du_an[1000]):
  - so_luong_cong_viec = 3
  - ti_le_hoan_thanh = 100%
  - chi_phi_thuc_te = 50,000,000 VND
  - trang_thai = 'hoan_thanh'

Customer (ABC Corp / khach_hang[200]):
  - so_du_an = 1
  - so_cong_viec = 3
  - so_cong_viec_dang_thuc_hien = 0
  - so_lan_tuong_tac = 2
  - rank = 'bac'
  - trang_thai_hop_tac = 'dang_hop_tac'
```

---

## Key Insights & Design Patterns

1. **Hierarchical Relationships**: 
   - Projects contain Tasks (du_an → cong_viec)
   - Customers can have subsidiaries (parent_khach_hang_id self-reference)
   - Employees have managers (quan_ly_id self-reference)

2. **Junction Models for M2M**:
   - `nguoi_tham_gia` bridges employees to tasks with role context
   - Allows rich metadata (vai_tro, participation dates) beyond simple M2M

3. **Computed vs Stored Fields**:
   - Progress fields (`tien_do`, `thuc_te_gio`) are computed from reports
   - Customer metrics (`so_cong_viec`, `so_du_an`) are computed via SEARCH
   - This ensures data freshness without manual updates

4. **Inheritance Patterns**:
   - `lich_hen` uses `_inherits` from `khach_hang_tuong_tac` for appointment-specific logic
   - quan_ly_khach_hang extends models from quan_ly_cong_viec (du_an, cong_viec)
   - Enables module reuse without modifying core

5. **Auto-Actions**:
   - Creating `bao_cao_tien_do` with tien_do=100 auto-completes task
   - Adding `nguoi_tham_gia` with vai_tro='phu_trach' updates task owner
   - Changing `lich_hen.trang_thai_hen` auto-creates/updates task progress
   - Ensures data consistency across modules

6. **Validation Boundaries**:
   - Tasks must fall within project date ranges (preventive validation)
   - Each employee once per task (unique constraint)
   - Resource allocations constrained to project OR task scopes
   - Ensures business rule compliance

---

**End of Analysis Document**
