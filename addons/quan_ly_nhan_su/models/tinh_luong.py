# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
import calendar

class TinhLuong(models.Model):
    _name = "tinh_luong"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Bảng lương tháng"
    _rec_name = "ma_bang_luong"
    _order = "thang_nam desc"

    ma_bang_luong = fields.Char(string="Mã bảng lương", required=True, index=True, default=lambda self: _('New'))
    thang_nam = fields.Char(string="Tháng năm", required=True, tracking=True, help="Format: YYYY-MM")
    ngay_bat_dau = fields.Date(string="Ngày bắt đầu", compute="_compute_month_dates", inverse="_inverse_month_dates", store=True)
    ngay_ket_thuc = fields.Date(string="Ngày kết thúc", compute="_compute_month_dates", inverse="_inverse_month_dates", store=True)
    
    # Trạng thái
    trang_thai = fields.Selection([
        ('nhap', 'Nháp'),
        ('cho_duyet', 'Chờ duyệt'),
        ('da_duyet', 'Đã duyệt'),
        ('da_thanh_toan', 'Đã thanh toán'),
    ], string="Trạng thái", default='nhap', required=True, tracking=True)
    
    # Người xử lý
    nguoi_tao_id = fields.Many2one('nhan_vien', string="Người tạo", default=lambda self: self.env.user.nhan_vien_id, readonly=True)
    ngay_tao = fields.Date(string="Ngày tạo", default=fields.Date.today, readonly=True)
    nguoi_duyet_id = fields.Many2one('nhan_vien', string="Người duyệt", tracking=True)
    ngay_duyet = fields.Date(string="Ngày duyệt", tracking=True)
    ngay_thanh_toan = fields.Date(string="Ngày thanh toán", tracking=True)
    ngan_hang = fields.Char(string="Ngân hàng thanh toán")
    ghi_chu = fields.Text(string="Ghi chú")
    
    # Chi tiết lương từng nhân viên
    chi_tiet_ids = fields.One2many('tinh_luong_chi_tiet', 'tinh_luong_id', string="Chi tiết lương")
    
    # Aggregates - tính tổng
    tong_co_ban = fields.Float(string="Tổng lương cơ bản", compute="_compute_aggregates", store=True)
    tong_phu_cap = fields.Float(string="Tổng phụ cấp", compute="_compute_aggregates", store=True)
    tong_thuong = fields.Float(string="Tổng thưởng", compute="_compute_aggregates", store=True)
    tong_khaу_tru = fields.Float(string="Tổng khấu trừ", compute="_compute_aggregates", store=True)
    tong_thue = fields.Float(string="Tổng thuế", compute="_compute_aggregates", store=True)
    tong_thuc_linh = fields.Float(string="Tổng thực lĩnh", compute="_compute_aggregates", store=True)
    so_nhan_vien = fields.Integer(string="Số nhân viên", compute="_compute_aggregates", store=True)
    
    @api.depends('thang_nam')
    def _compute_month_dates(self):
        """Tính ngày bắt đầu và kết thúc của tháng"""
        for record in self:
            if record.thang_nam:
                try:
                    year, month = map(int, record.thang_nam.split('-'))
                    record.ngay_bat_dau = datetime(year, month, 1).date()
                    last_day = calendar.monthrange(year, month)[1]
                    record.ngay_ket_thuc = datetime(year, month, last_day).date()
                except:
                    record.ngay_bat_dau = False
                    record.ngay_ket_thuc = False
            else:
                record.ngay_bat_dau = False
                record.ngay_ket_thuc = False

    def _inverse_month_dates(self):
        """Cho phép người dùng chỉnh tay kỳ lương trên form khi cần ngoại lệ."""
        return

    @api.onchange('thang_nam')
    def _onchange_thang_nam(self):
        """Tự động convert các format phổ biến về YYYY-MM"""
        if not self.thang_nam:
            return
        val = self.thang_nam.strip()
        # MM/YYYY hoặc MM-YYYY → YYYY-MM
        for sep in ('/', '-'):
            if sep in val:
                parts = val.split(sep)
                if len(parts) == 2:
                    a, b = parts[0].strip(), parts[1].strip()
                    if len(b) == 4 and b.isdigit() and len(a) <= 2 and a.isdigit():
                        # dạng MM/YYYY
                        self.thang_nam = f"{b}-{int(a):02d}"
                        return
                    elif len(a) == 4 and a.isdigit() and len(b) <= 2 and b.isdigit():
                        # dạng YYYY-MM hoặc YYYY/MM — đã đúng hoặc chuẩn hóa
                        self.thang_nam = f"{a}-{int(b):02d}"
                        return
    
    @api.depends('chi_tiet_ids', 'chi_tiet_ids.luong_co_ban', 'chi_tiet_ids.phu_cap', 
                 'chi_tiet_ids.tien_thuong', 'chi_tiet_ids.tong_khau_tru', 'chi_tiet_ids.thue_thu_nhap', 'chi_tiet_ids.thuc_linh')
    def _compute_aggregates(self):
        """Tính các tổng từ chi tiết"""
        for record in self:
            record.tong_co_ban = sum(record.chi_tiet_ids.mapped('luong_co_ban'))
            record.tong_phu_cap = sum(record.chi_tiet_ids.mapped('phu_cap'))
            record.tong_thuong = sum(record.chi_tiet_ids.mapped('tien_thuong'))
            record.tong_khaу_tru = sum(record.chi_tiet_ids.mapped('tong_khau_tru'))
            record.tong_thue = sum(record.chi_tiet_ids.mapped('thue_thu_nhap'))
            record.tong_thuc_linh = sum(record.chi_tiet_ids.mapped('thuc_linh'))
            record.so_nhan_vien = len(record.chi_tiet_ids)
    
    def action_load_employees(self):
        """Tải danh sách nhân viên đang hoạt động vào bảng lương"""
        self.chi_tiet_ids.unlink()
        
        # Tìm nhân viên có hợp đồng hiệu lực
        employees = self.env['nhan_vien'].search([
            ('trang_thai', '=', 'active'),
        ])
        
        chi_tiet_list = []
        for emp in employees:
            # Lấy hợp đồng hiện tại
            hop_dong = emp.hop_dong_ids.filtered(lambda x: x.trang_thai == 'active')
            if hop_dong:
                hop_dong = hop_dong[0]
                chi_tiet_list.append({
                    'nhan_vien_id': emp.id,
                    'luong_co_ban': hop_dong.luong_co_ban,
                    'phu_cap': hop_dong.phu_cap,
                })
        
        if chi_tiet_list:
            self.chi_tiet_ids = [(0, 0, val) for val in chi_tiet_list]
    
    def action_calculate_payroll(self):
        """Tính lương cho tất cả nhân viên"""
        for record in self:
            if record.trang_thai != 'nhap':
                raise ValidationError(_("Chỉ có thể tính lương khi ở trạng thái 'Nháp'!"))
            
            # Lặp qua từng chi tiết để tính
            for chi_tiet in record.chi_tiet_ids:
                chi_tiet._calculate_salary()
    
    def action_submit(self):
        """Nộp duyệt bảng lương"""
        for record in self:
            if record.trang_thai != 'nhap':
                raise ValidationError(_("Chỉ có thể nộp duyệt từ trạng thái 'Nháp'!"))
            if not record.chi_tiet_ids:
                raise ValidationError(_("Bảng lương phải có ít nhất 1 nhân viên!"))
            record.trang_thai = 'cho_duyet'
    
    def action_approve(self):
        """Phê duyệt bảng lương"""
        for record in self:
            if record.trang_thai != 'cho_duyet':
                raise ValidationError(_("Chỉ có thể phê duyệt từ trạng thái 'Chờ duyệt'!"))
            record.trang_thai = 'da_duyet'
            record.nguoi_duyet_id = self.env.user.nhan_vien_id
            record.ngay_duyet = fields.Date.today()
    
    def action_mark_paid(self):
        """Đánh dấu đã thanh toán"""
        for record in self:
            if record.trang_thai != 'da_duyet':
                raise ValidationError(_("Chỉ có thể thanh toán khi đã phê duyệt!"))
            record.trang_thai = 'da_thanh_toan'
            record.ngay_thanh_toan = fields.Date.today()
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('ma_bang_luong', _('New')) == _('New'):
                vals['ma_bang_luong'] = self.env['ir.sequence'].next_by_code('tinh_luong') or _('New')
        return super().create(vals_list)


class TinhLuongChiTiet(models.Model):
    _name = "tinh_luong_chi_tiet"
    _description = "Chi tiết lương từng nhân viên"
    _rec_name = "nhan_vien_id"

    tinh_luong_id = fields.Many2one('tinh_luong', string="Bảng lương", required=True, ondelete='cascade')
    nhan_vien_id = fields.Many2one('nhan_vien', string="Nhân viên", required=True)
    ma_nhan_vien = fields.Char(string="Mã nhân viên", related='nhan_vien_id.ma_nhan_vien', readonly=True, store=True)
    ten_nhan_vien = fields.Char(string="Tên nhân viên", related='nhan_vien_id.ho_va_ten', readonly=True, store=True)
    
    # Thành phần lương
    luong_co_ban = fields.Float(string="Lương cơ bản")
    phu_cap = fields.Float(string="Phụ cấp")
    tien_thuong = fields.Float(string="Thưởng", default=0.0)
    thuong_tu_dong = fields.Float(string="Thưởng tự động", default=0.0)
    
    # Khấu trừ
    bao_hiem_xa_hoi = fields.Float(string="Bảo hiểm xã hội", default=0.0)
    bao_hiem_y_te = fields.Float(string="Bảo hiểm y tế", default=0.0)
    bao_hiem_that_nghiep = fields.Float(string="Bảo hiểm thất nghiệp", default=0.0)
    ung_luong = fields.Float(string="Ứng lương", default=0.0)
    khoan_khac = fields.Float(string="Khoản khác", default=0.0)
    
    # Thuế
    thue_thu_nhap = fields.Float(string="Thuế thu nhập cá nhân", default=0.0)
    ghi_chu_thue = fields.Char(string="Ghi chú thuế")
    
    # Computed
    tong_luong_truoc_khau_tru = fields.Float(string="Tổng lương trước khấu trừ", compute="_compute_salary", store=True)
    tong_khau_tru = fields.Float(string="Tổng khấu trừ", compute="_compute_salary", store=True)
    thuc_linh = fields.Float(string="Thực lĩnh", compute="_compute_salary", store=True)
    
    # Dữ liệu chấm công
    so_ngay_lam_viec = fields.Float(string="Số ngày làm việc", default=0.0)
    so_ngay_vang_khong_luong = fields.Float(string="Số ngày vắng không lương", default=0.0)
    
    ghi_chu = fields.Text(string="Ghi chú")
    slip_created = fields.Boolean(string="Đã tạo slip", default=False)
    slip_sent_date = fields.Date(string="Ngày gửi slip")
    
    @api.depends('luong_co_ban', 'phu_cap', 'tien_thuong', 'thuong_tu_dong', 'bao_hiem_xa_hoi', 'bao_hiem_y_te', 
                 'bao_hiem_that_nghiep', 'ung_luong', 'khoan_khac', 'thue_thu_nhap')
    def _compute_salary(self):
        """Tính lương"""
        for record in self:
            # Tổng trước khấu trừ
            record.tong_luong_truoc_khau_tru = (
                record.luong_co_ban + record.phu_cap + record.tien_thuong + record.thuong_tu_dong
            )
            
            # Tổng khấu trừ (không bao gồm thuế)
            record.tong_khau_tru = (
                record.bao_hiem_xa_hoi + record.bao_hiem_y_te + 
                record.bao_hiem_that_nghiep + record.ung_luong + record.khoan_khac
            )
            
            # Thực lĩnh
            record.thuc_linh = (
                record.tong_luong_truoc_khau_tru - record.tong_khau_tru - record.thue_thu_nhap
            )
    
    def _calculate_salary(self):
        """Tính lương chi tiết từ dữ liệu chấm công và phụ cấp"""
        for record in self:
            if not (record.tinh_luong_id and record.tinh_luong_id.ngay_bat_dau and record.tinh_luong_id.ngay_ket_thuc):
                continue

            start_date = record.tinh_luong_id.ngay_bat_dau
            end_date = record.tinh_luong_id.ngay_ket_thuc

            attendance_records = self.env['cham_cong'].search([
                ('nhan_vien_id', '=', record.nhan_vien_id.id),
                ('ngay_cham_cong', '>=', start_date),
                ('ngay_cham_cong', '<=', end_date),
            ])

            paid_status = {'di_lam', 'cong_tac', 'nghi_phep', 'nghi_le', 'nghi_om'}
            record.so_ngay_lam_viec = len(attendance_records.filtered(lambda x: x.trang_thai in paid_status))
            record.so_ngay_vang_khong_luong = len(attendance_records.filtered(lambda x: x.trang_thai == 'nghi_khong_luong'))

            work_day_standard = 22.0
            ngay_tinh_luong = min(record.so_ngay_lam_viec, work_day_standard)

            hop_dong = record.nhan_vien_id.hop_dong_ids.filtered(lambda x: x.trang_thai == 'active')[:1]
            luong_co_ban_hop_dong = hop_dong.luong_co_ban if hop_dong else record.luong_co_ban
            luong_co_ban_thuc_te = (luong_co_ban_hop_dong / work_day_standard) * ngay_tinh_luong if work_day_standard else 0.0
            record.luong_co_ban = luong_co_ban_thuc_te

            # Cộng thêm thưởng tăng ca từ timesheet đã duyệt nếu module có dữ liệu
            thuong_tang_ca = 0.0
            if 'bangiao_timesheet' in self.env:
                overtime_entries = self.env['bangiao_timesheet'].search([
                    ('nhan_vien_id', '=', record.nhan_vien_id.id),
                    ('ngay_lam', '>=', start_date),
                    ('ngay_lam', '<=', end_date),
                    ('trang_thai', '=', 'approved'),
                    ('loai_cong_viec', 'in', ['tăng_ca', 'lao_dung']),
                ])
                thuong_tang_ca = sum(overtime_entries.mapped('luong_nhan'))
            record.thuong_tu_dong = thuong_tang_ca

            # Tự động lấy ứng lương chưa tất toán trong tháng
            ung_luong = self.env['tinh_luong_khoan_tam'].search([
                ('nhan_vien_id', '=', record.nhan_vien_id.id),
                ('trang_thai', '=', 'dang_cho'),
                ('ngay_cho_vay', '>=', start_date),
                ('ngay_cho_vay', '<=', end_date),
            ])
            record.ung_luong = sum(ung_luong.mapped('so_tien'))

            # Tính BH theo tỷ lệ cơ bản
            record.bao_hiem_xa_hoi = round(record.luong_co_ban * 0.08, 0)
            record.bao_hiem_y_te = round(record.luong_co_ban * 0.015, 0)
            record.bao_hiem_that_nghiep = round(record.luong_co_ban * 0.01, 0)

            thu_nhap_tinh_thue = (
                record.luong_co_ban + record.phu_cap + record.tien_thuong
                - record.bao_hiem_xa_hoi - record.bao_hiem_y_te - record.bao_hiem_that_nghiep
                - 11000000
            )

            if thu_nhap_tinh_thue <= 0:
                record.thue_thu_nhap = 0.0
                record.ghi_chu_thue = _("Không phát sinh thuế TNCN")
            elif thu_nhap_tinh_thue <= 5000000:
                record.thue_thu_nhap = round(thu_nhap_tinh_thue * 0.05, 0)
                record.ghi_chu_thue = _("Thuế suất 5%")
            elif thu_nhap_tinh_thue <= 10000000:
                record.thue_thu_nhap = round(250000 + (thu_nhap_tinh_thue - 5000000) * 0.10, 0)
                record.ghi_chu_thue = _("Thuế suất lũy tiến 5%-10%")
            else:
                record.thue_thu_nhap = round(750000 + (thu_nhap_tinh_thue - 10000000) * 0.15, 0)
                record.ghi_chu_thue = _("Thuế suất lũy tiến đến 15%")
    
    def action_generate_slip(self):
        """Tạo phiếu lương"""
        for record in self:
            record.slip_created = True
            record.slip_sent_date = fields.Date.today()


class TinhLuongKhoanTam(models.Model):
    _name = "tinh_luong_khoan_tam"
    _description = "Ứng lương / Khoản tạm ứng"
    _rec_name = "display_name"

    display_name = fields.Char(compute="_compute_display_name", store=True)
    nhan_vien_id = fields.Many2one('nhan_vien', string="Nhân viên", required=True, ondelete='cascade')
    so_tien = fields.Float(string="Số tiền", required=True)
    ngay_cho_vay = fields.Date(string="Ngày cho vay", default=fields.Date.today, required=True)
    ngay_tra = fields.Date(string="Ngày trả")
    trang_thai = fields.Selection([
        ('dang_cho', 'Đang chờ trả'),
        ('da_tra', 'Đã trả'),
    ], string="Trạng thái", default='dang_cho')
    ghi_chu = fields.Text(string="Ghi chú")

    @api.depends('nhan_vien_id', 'so_tien')
    def _compute_display_name(self):
        for record in self:
            if record.nhan_vien_id and record.so_tien:
                record.display_name = f"{record.nhan_vien_id.ho_va_ten} - {record.so_tien:,.0f}đ"
            else:
                record.display_name = False