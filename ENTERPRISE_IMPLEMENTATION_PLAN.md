# Comprehensive ERP Module Implementation Plan
**Date**: March 21, 2026  
**Scope**: Enterprise-level with advanced automation & analytics  
**Integration**: Full timesheet-payroll integration

---

## Missing Models to Implement

### HRM Module (quan_ly_nhan_su) - 2 NEW
1. **tuyen_dung** (Recruitment) - Job postings, candidates, interviews
2. **onboarding** (Onboarding/Offboarding) - New employee & exit checklists

### PM Module (quan_ly_cong_viec) - 3 ENHANCEMENTS
1. **bangiao_timesheet** (Timesheet) - Detailed work logging per task
2. **du_an_rui_ro** (Risk Management) - Risk tracking & mitigation
3. **du_an_issue** (Issue Management) - Issue tracking & resolution

### CRM Module (quan_ly_khach_hang) - 5 NEW
1. **bao_gia** (Quotation) - Quotes with line items & approval
2. **don_hang** (Sales Order) - Orders from approved quotes
3. **hop_dong_khach_hang** (Customer Contract) - Contract tracking & renewal
4. **yeu_cau_ho_tro** (Support/Service Request) - Post-sales support
5. **hoat_dong_sales** (Sales Activity) - Calls, meetings, tasks logging

---

## Implementation Roadmap

### Phase 1: HRM Completion (Est. 3-4 hours)
- ✅ nghi_phep, tinh_luong (already done)
- 🆕 tuyen_dung (Recruitment) 
- 🆕 onboarding (Onboarding/Offboarding)

### Phase 2: PM Enhancement (Est. 3-4 hours)
- ✅ du_an, cong_viec (already done)
- 🆕 bangiao_timesheet (Detailed timesheet with project/task linking)
- 🆕 du_an_rui_ro (Risk Management)
- 🆕 du_an_issue (Issue Management)
- Enhancement: Task dependencies, blocking, priority

### Phase 3: CRM Completion (Est. 4-5 hours)
- ✅ khach_hang, lead, co_hoi_ban_hang (already done)
- 🆕 bao_gia (Quotation with approval workflow)
- 🆕 don_hang (Sales Order)
- 🆕 hop_dong_khach_hang (Contract Management)
- 🆕 yeu_cau_ho_tro (Support Ticket)
- 🆕 hoat_dong_sales (Activity logging)

### Phase 4: Integration & Automation (Est. 2-3 hours)
- Timesheet → Payroll automation
- Opportunity → Quote creation
- Quote → Order → Invoice workflow
- Risk → Issue escalation
- Lead scoring enhancement

### Phase 5: Reporting & Analytics (Est. 2-3 hours)
- HRM: Payroll dashboards, attrition analytics
- PM: Burndown charts, resource utilization, risk heatmaps
- CRM: Sales pipeline forecast, revenue analytics, conversion funnels

---

## Database Schema Overview

### HRM Tables
```
nhan_vien (✅ done)
├── hop_dong (✅ done)
├── cham_cong (✅ done)
├── nghi_phep (✅ done)
├── tinh_luong (✅ done)
├── danh_gia (✅ done)
├── dao_tao (✅ done)
├── vi_tri_tuyen_dung (🆕 Job positions)
├── ung_vien (🆕 Candidates)
├── phong_van (🆕 Interviews)
└── onboarding_offboarding (🆕 Checklists)
```

### PM Tables
```
du_an (✅ done)
├── cong_viec (✅ done)
├── nguoi_tham_gia (✅ done)
├── phan_bo_nguon_luc (✅ done)
├── bao_cao_tien_do (✅ done)
├── bangiao_timesheet (🆕 Work hours per task)
├── du_an_rui_ro (🆕 Risk register)
└── du_an_issue (🆕 Issue tracker)
```

### CRM Tables
```
khach_hang (✅ done)
├── khach_hang_tuong_tac (✅ done)
├── lead (✅ done)
├── co_hoi_ban_hang (✅ done)
├── bao_gia (🆕 Quotation with lines)
│   └── bao_gia_chi_tiet
├── don_hang (🆕 Sales Order)
│   └── don_hang_chi_tiet
├── hop_dong_khach_hang (🆕 Customer contracts)
├── yeu_cau_ho_tro (🆕 Support tickets)
│   └── yeu_cau_ho_tro_chi_tiet (Attachments)
└── hoat_dong_sales (🆕 Activities)
```

---

## Key Business Rules

### HRM Integration
- Leave approval → Updates cham_cong
- cham_cong → Triggers tinh_luong calculation
- Recruited candidate → Creates nhan_vien on hire
- Resignation → Triggers offboarding checklist

### PM Integration
- Task updates → Updates du_an progress
- bangiao_timesheet → Feeds into task completion %
- Risk materialization → Creates issue
- Issue resolution → Removes from blocked task list

### CRM Integration
- Lead qualified → Auto-creates opportunity
- Opportunity won → Auto-creates khách_hàng
- Quote approved → Can create don_hang
- Won opportunity → Auto-creates hop_dong_khach_hang
- Activity logged → Updates last_contact date
- Support request → Linked to khách_hàng & past contracts

---

## Advanced Features

### HRM
- Resume parsing & screening
- Interview scoring & ranking
- Onboarding task automation
- Leave balance auto-calculation by accrual rules
- Salary adjustment notifications
- Department-based payroll reports

### PM
- Task dependency visualization
- Critical path analysis
- Resource conflict detection
- SPI/CPI calculation (Schedule/Cost Performance Index)
- Risk probability × impact heatmap
- Burn-down charts per iteration/sprint

### CRM
- Lead scoring (auto, rule-based)
- Quote version control & approval chain
- AR aging report (Accounts Receivable)
- Win/loss analysis
- Contract auto-renewal alerts
- Customer satisfaction surveys (post-support)
- Sales forecast by weighted probability

---

## Implementation Details

All models will include:
✅ Full field specifications  
✅ Relationships & constraints  
✅ Computed fields  
✅ Workflow state machines  
✅ Security rules  
✅ XML views (form, tree, kanban, calendar)  
✅ Sequences & document IDs  
✅ Automation crons & buttons  
✅ Demo data  
✅ Access controls by role  

---

## Timeline

- Start: Now
- Phase 1-2: Today (~6 hours)
- Phase 3: Tomorrow (~5 hours)
- Phase 4-5: Post implementation testing

Total Effort: ~17 hours, creating 15+ new models with comprehensive views and automation.

Let's begin! 🚀
