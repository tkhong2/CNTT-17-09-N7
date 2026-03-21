# Design Document: Missing MVP Models

## 1. HRM - LEAVE REQUEST MODEL (nghi_phep)

### Purpose
Manage employee leave requests with approval workflow, balance tracking, and historical records.

### Model Name: `nghi_phep`

### Fields

#### Basic Information
- `ma_nghi_phep` (Char, unique, required) - Leave request ID
- `nhan_vien_id` (Many2one → nhan_vien, required) - Employee submitting request
- `loai_nghi_phep` (Selection, required) - Type of leave:
  - phép_năm: Annual leave
  - ốm: Sick leave
  - ốm_không_giấy_tờ: Sick leave (no cert, max 1 day)
  - thai_sản: Maternity leave
  - nhân_sự: Personal/family leave
  - công_tác: Business trip
  - không_lương: Unpaid leave
  
#### Timeline
- `ngày_bắt_đầu` (Date, required) - Leave start date
- `ngày_kết_thúc` (Date, required) - Leave end date
- `số_ngày` (Float, computed based on dates) - Number of leave days
- `ngày_nộp_đơn` (Date, default today) - Submission date
- `ngày_duyệt` (Date) - Approval date

#### Approval Workflow
- `người_duyệt_id` (Many2one → nhan_vien) - Approver (usually direct manager)
- `người_duyệt_cấp_2_id` (Many2one → nhan_vien) - Second approver if needed
- `trạng_thái` (Selection, default 'chờ_duyệt'):
  - chờ_duyệt: Pending approval
  - duyệt_cấp_1: Level 1 approved
  - duyệt_cấp_2: Level 2 approved (if > 5 days)
  - từ_chối: Rejected
  - hủy_bỏ: Cancelled
  
#### Details
- `lý_do` (Text) - Reason for leave
- `ghi_chú_duyệt` (Text) - Approver notes
- `số_điện_thoại_liên_hệ` (Char) - Contact during leave
- `người_thay_thế_id` (Many2one → nhan_vien) - Substitute contact person

#### Computed Fields
- `tên_loại_nghi_phep` (Char, computed) - Display leave type
- `tên_nhân_viên` (Char, related → nhan_vien.ho_va_ten)
- `ngày_làm_việc` (Float, computed) - Working days (excluding weekends/holidays)

### Constraints
- Start date must be ≤ End date
- Leave request can only be submitted for future dates
- Cannot have overlapping leave requests
- Days > 5 requires 2-level approval
- Only specific leave types require cert (ốm)

### Workflow
1. Employee submits leave request
2. Direct manager reviews & approves (Level 1)
3. If > 5 days, HR/Department head approves (Level 2)
4. If approved, updates employee leave balance
5. Record for payroll processing

### Related Views
- Tree: all leave requests, filterable by status
- Form: full leave request with approval notes
- Kanban: by status
- Calendar: visual leave schedule

---

## 2. HRM - PAYROLL MODEL (tinh_luong)

### Purpose
Process monthly payroll with salary calculation, deductions, bonuses, and slip generation.

### Model Name: `tinh_luong`

### Tables Needed
Main: `tinh_luong`, Supporting: `tinh_luong_chi_tiet`, `tinh_luong_khoân_tạm`

### Main Model: `tinh_luong`

#### Basic Information
- `ma_bang_luong` (Char, unique, required) - Payroll batch ID
- `tháng_năm` (Char, required) - Month/Year (YYYY-MM)
- `ngày_bắt_đầu` (Date, computed) - Month start
- `ngày_kết_thúc` (Date, computed) - Month end
- `trạng_thái` (Selection, default 'nháp'):
  - nháp: Draft
  - chờ_duyệt: Pending approval
  - đã_duyệt: Approved
  - đã_thanh_toán: Paid

#### Processing
- `ngày_tạo` (Date, default today)
- `người_tạo_id` (Many2one → nhan_vien) - Payroll creator
- `người_duyệt_id` (Many2one → nhan_vien) - Payroll approver
- `ngày_duyệt` (Date) - Approval date
- `ngày_thanh_toán` (Date) - Payment date
- `ngân_hàng` (Char) - Bank for transfer
- `ghi_chú` (Text) - Notes

#### Aggregates (Automated Calculation)
- `tổng_cơ_bản` (Float, computed) - Sum of base salaries
- `tổng_phụ_cấp` (Float, computed) - Sum of allowances
- `tổng_thưởng` (Float, computed) - Sum of bonuses
- `tổng_khấu_trừ` (Float, computed) - Sum of deductions
- `tổng_thuế` (Float, computed) - Sum of taxes
- `tổng_thực_lĩnh` (Float, computed) - Net pay total
- `số_nhân_viên` (Integer, computed) - Employee count

#### One2many
- `chi_tiết_ids` (One2many → tinh_luong_chi_tiet) - Detail per employee

### Detail Line Model: `tinh_luong_chi_tiet`

#### Employee Info
- `nhan_vien_id` (Many2one → nhan_vien, required) - Employee
- `mã_nhân_viên` (Char, readonly) - Employee code
- `tên_nhân_viên` (Char, readonly) - Employee name

#### Salary Components
- `lương_cơ_bản` (Float) - Base salary from contract
- `phụ_cấp_chức_vụ` (Float) - Position allowance
- `phụ_cấp_khác` (Float) - Other allowances

#### Adjustments
- `chứng_thư_từ_khohoàn` (Float) - Paid advances/loans
- `tiền_thưởng` (Float) - Bonuses
- `bảo_hiểm_xã_hội` (Float) - Social insurance deduction
- `bảo_hiểm_y_tế` (Float) - Health insurance
- `bảo_hiểm_thất_nghiệp` (Float) - Unemployment insurance
- `khoản_khác` (Float) - Other deductions

#### Tax
- `thuế_thu_nhập_cá_nhân` (Float) - Personal income tax
- `tax_notes` (Char) - Tax calculation notes

#### Computed
- `tổng_lương_trước_khấu_trừ` (Float) - Gross: base + allowances + bonuses
- `tổng_khấu_trừ` (Float) - Total deductions
- `thực_lĩnh` (Float) - Net: gross - deductions - tax
- `số_ngày_làm_việc` (Float) - Actual working days (from cham_cong)
- `số_ngày_vắng_không_lương` (Float) - Unpaid absences

#### Audit
- `ghi_chú` (Text)
- `slip_created` (Boolean) - Payroll slip generated?
- `slip_sent_date` (Date)

### Support Model: `tinh_luong_khoân_tạm`

Track advance payments/loans:
- `nhan_vien_id` (Many2one → nhan_vien)
- `số_tiền` (Float) - Advance amount
- `ngày_cho_vay` (Date) - Advance date
- `ngày_trả` (Date) - Repayment date
- trạng_thái: pending/repaid
- `ghi_chú` (Text)

### Key Calculations (in code)
1. **Attendance Impact:**
   - Calculate actual working days from `cham_cong`
   - Deduct unpaid leave days
   
2. **Salary Calculation:**
   - Gross = Base + Allowances + Bonuses
   - Total Deductions = Insurance + Advances + Other
   - Taxable Income = Gross - Insurance (not all deductible)
   - Tax = Taxable × Tax Rate (simplified, can be enhanced)
   - Net = Gross - Deductions - Tax

3. **Tax Calculation** (simplified Vietnamese):
   - Personal exemption: 11M VND/month
   - Tax Rate: 5-35% (progressive)
   - Can integrate actual tax table later

### Workflow
1. Select month
2. Auto-load employees with active contracts
3. Retrieve attendance data
4. Calculate each component
5. Review & adjust if needed
6. Approve payroll batch
7. Generate payroll slips
8. Mark as paid

### Related Views
- Tree: payroll batches by month
- Form: full payroll with line editor
- Report: payroll summary, tax summary
- Slip view: individual payroll slip pdf/print

---

## 3. CRM - LEAD MODEL (lead)

### Purpose
Track sales leads from various sources through qualification process to customer conversion.

### Model Name: `lead`

#### Basic Information
- `ma_lead` (Char, unique, required) - Lead ID
- `tên_lead` (Char, required) - Lead/Company name
- `người_liên_hệ` (Char) - Contact person
- `email` (Char) - Contact email
- `số_điện_thoại` (Char) - Phone
- `địa_chỉ` (Text) - Address
- `mô_tả` (Text) - Lead notes

#### Classification
- `nguồn_lead` (Selection, required) - Lead source:
  - website: Website form
  - phone: Incoming call
  - email: Email inquiry
  - referral: Referral
  - event: Event/Exhibition
  - social_media: Social network
  - partnership: Partner referral
  - other: Other
  
- `loại_khách_hàng` (Selection):
  - cá_nhân: Individual
  - công_ty_nhỏ: Small business
  - công_ty_trung_bình: Medium business
  - doanh_nghiệp_lớn: Enterprise
  
- `ngành_công_nghiệp` (Char) - Industry
- `quy_mô` (Selection):
  - < 10 nhân viên
  - 10-50 nhân viên
  - 50-100 nhân viên
  - > 100 nhân viên

#### Assignment
- `nhan_viên_phụ_trách_id` (Many2one → nhan_vien) - Sales person owner
- `ngày_gán` (Date) - Assignment date
- `độ_ưu_tiên` (Selection):
  - thấp
  - trung_bình
  - cao
  - rất_cao

#### Qualification
- `trạng_thái` (Selection, default 'mới', readonly after conversion):
  - mới: New lead
  - đang_tiếp_cận: Being contacted
  - quan_tâm: Shows interest
  - chưa_sẵn_sàng: Not ready (nurish)
  - sẵn_sàng: Qualified & ready
  - chuyển_khách: Converted to customer
  - vô_kiến_cự: Dead lead
  
- `điểm_đánh_giá` (Float 0-100, default 0) - Lead score
  - Auto-calculated based on activities
  - Activities: email opens, website visits, calls
  - Can be manually adjusted

- `ngày_liên_hệ_cuối` (Date) - Last contact date
- `số_lần_liên_hệ` (Integer) - Contact count
- `ngày_theo_dõi_tiếp` (Date) - Next follow-up date

#### Timeline
- `ngày_tạo` (Date, default today)
- `ngày_sửa` (Date, auto-update)
- `ngày_chuyển_đổi_khách` (Date) - Conv. date if converted
- `thời_gian_chuyển_đổi` (Integer, computed) - Days to conversion

#### Relations
- `khách_hàng_id` (Many2one → khach_hang) - If converted to customer
- `co_hội_ids` (One2many → co_hoi_ban_hang) - Related opportunities
- `hoạt_động_ids` (One2many → lead_hoat_dong) - Activities/notes

#### Budget (Estimated)
- `ngân_sách_ước_tính` (Float) - Est. budget
- `tiềm_năng_doanh_thu` (Float, computed) - Revenue potential

### Support Model: `lead_hoat_dong`

Track activities on leads:
- `lead_id` (Many2one → lead, cascade)
- `loại_hoạt_động` (Selection):
  - gọi: Call
  - email: Email sent
  - cuộc_họp: Meeting
  - note: Internal note
  - document: Document sent
  
- `ngày_giờ` (Datetime, default now)
- `người_thực_hiện_id` (Many2one → nhan_vien)
- `nội_dung` (Text)
- `kết_quả` (Char) - Result/outcome

### Workflow & Automation
1. Lead created (mới)
2. Sales person contacts → đang_tiếp_cận
3. Customer shows interest → quan_tâm
4. If not ready → chưa_sẵn_sàng (nurture with periodic follow-ups)
5. When ready → sẵn_sàng (qualified lead)
6. Create opportunity from lead
7. Upon deal close → chuyển_khách to customer
8. Auto-create khach_hang record

### Related Views
- Kanban: by trạng_thái (pipeline view)
- Tree: all leads with score
- Form: full lead info with activity log
- Chart: lead source analysis, conversion rate

---

## 4. CRM - SALES OPPORTUNITY MODEL (co_hoi_ban_hang)

### Purpose
Manage sales opportunities from qualified leads through deal closure with revenue forecast.

### Model Name: `co_hoi_ban_hang`

#### Basic Information
- `ma_cơ_hội` (Char, unique, required) - Opportunity ID
- `tên_cơ_hội` (Char, required) - Deal/Opportunity name
- `mô_tả` (Text) - Description

#### Origin
- `lead_id` (Many2one → lead) - Source lead (optional)
- `khách_hàng_id` (Many2one → khach_hang) - Related customer
- `dự_án_id` (Many2one → du_an) - Related project (if created)

#### Sales Info
- `nhan_viên_phu_trách_id` (Many2one → nhan_vien, required) - Owner
- `nhóm_bán_hàng_id` (Many2one → nhan_vien) - Sales team/manager (optional)
- `ngày_tạo` (Date, default today)

#### Amount & Forecast
- `giá_trị_cơ_hội` (Float, required) - Expected deal value
- `xác_suất_thắng` (Float, default 0) - Win probability %
- `doanh_thu_dự_báo` (Float, computed) - Forecast: giá_trị × xác_suất
- `hạn_chót` (Date) - Expected close date
- `ghi_chú_tài_chính` (Text)

#### Sales Pipeline
- `giai_đoạn` (Selection, required, default 'khám_phá'):
  - khám_phá: Discovery - initial qualification
  - phát_triển: Development - detailed needs analysis
  - đề_xuất: Proposal - quote/proposal sent
  - thương_lượng: Negotiation - negotiating terms
  - sắp_đóng: Nearly closed - final stage
  - thắng: Won - deal closed successfully
  - thua: Lost - deal lost
  - hủy_bỏ: Cancelled
  
- `ngày_cập_nhật_giai_đoạn` (Date) - Last stage change

#### Activity & Progress
- `số_lần_liên_hệ` (Integer) - Contact count
- `ngày_liên_hệ_cuối` (Date) - Last contact
- `ngày_theo_dõi_tiếp` (Date) - Next follow-up
- `hoạt_động_ids` (One2many → co_hoi_hoat_dong) - Activity log

#### Timeline
- `ngày_tạo` (Date)
- `ngày_đóng_thắng` (Date) - Actual close date if won
- `thời_gian_kinh_doanh` (Integer, computed) - Days in pipeline
- `nguyên_nhân_thua` (Text) - If lost, why?
- `lối_quay_lại` (Text) - Recovery possibility?

#### Reason/Status
- `trạng_thái_khác` (Selection):
  - hoạt_động: Active
  - tạm_dừng: On hold
  - không_hoạt_động: Inactive

### Support Model: `co_hoi_hoat_dong`

Track opportunity activities:
- `co_hoi_id` (Many2one → co_hoi_ban_hang, cascade)
- `loại` (Selection):
  - gọi: Call
  - email: Email
  - meeting: Meeting
  - đề_xuất: Quote sent
  - cuộc_họp_video: Video call
  - khác: Other
  
- `ngày_giờ` (Datetime, default now)
- `người_thực_hiện_id` (Many2one → nhan_vien)
- `mô_tả` (Text)
- `kết_quả` (Char)

### Key Calculations
1. **Forecast Revenue** = giá_trị × xác_suất / 100
2. **Pipeline Duration** = Today - ngày_tạo
3. **Stage Progression** = Auto-calculated based on activities

### Workflow
1. Create from lead → khám_phá
2. Detailed discovery → phát_triển
3. Send quote → đề_xuất
4. Negotiations → thương_lượng
5. Final agreement → sắp_đóng
6. Contract signed → thắng (or thua if lost)
7. If won: can auto-create project/customer interaction

### Related Views
- Kanban: by giai_đoạn (sales pipeline view)
- Tree: all opportunities
- Form: full opportunity with activities, forecast
- Dashboard: revenue forecast, win/loss rate
- Chart: pipeline analysis, forecast by sales person
- Calendar: deadlines

### Analytics (Dashboards)
- Total pipeline value
- Forecast revenue by stage
- Win rate by sales person
- Average deal size
- Sales cycle duration
- Deal age distribution

---

## Integration Points

### HRM Cross-Module
- nghi_phep → tính_lương: Leave days affect payroll
- cham_cong → tính_luong: Attendance affects payroll
- nghi_phep → cham_cong: Approved leave auto-marks attendance

### CRM Cross-Module
- lead → co_hoi_ban_hang: Lead converts to opportunity
- lead → khach_hang: Qualified lead becomes customer (chuyển_khách)
- co_hoi_ban_hang → khach_hang: Won deal creates customer record
- co_hoi_ban_hang → du_an: Can link or auto-create project
- khach_hang_tuong_tac: Can log interactions from lead/opportunity

### PM Integration
- co_hoi_ban_hang → du_an: Won opportunity creates project
- du_an → khach_hang: Projects are customer-centric

---

## Next Steps
1. Implement all 4 models with fields & constraints
2. Create views (forms, trees, kanban)
3. Add security rules
4. Create demo data
5. Write automations/crons for:
   - Lead aging reports
   - Opportunity forecasting
   - Payroll batch processing
   - Leave balance updates
