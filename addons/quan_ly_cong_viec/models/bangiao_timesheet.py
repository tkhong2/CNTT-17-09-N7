# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta

class BangiaoTimesheet(models.Model):
    """Detailed Timesheet - Work hours per task"""
    _name = "bangiao_timesheet"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Bảng ghi nhận giờ làm việc"
    _rec_name = "display_name"
    _order = "ngay_lam desc"

    nhan_vien_id = fields.Many2one('nhan_vien', string="Nhân viên", required=True, tracking=True, ondelete='cascade')
    du_an_id = fields.Many2one('du_an', string="Dự án", required=True, tracking=True, ondelete='cascade')
    cong_viec_id = fields.Many2one('cong_viec', string="Công việc", required=True, tracking=True, ondelete='cascade')
    
    display_name = fields.Char(compute="_compute_display_name", store=True)
    
    ngay_lam = fields.Date(string="Ngày làm", required=True, default=fields.Date.today, tracking=True)
    gio_bat_dau = fields.Float(string="Giờ bắt đầu", help="VD: 8.5 = 8h30")
    gio_ket_thuc = fields.Float(string="Giờ kết thúc")
    
    tong_gio = fields.Float(string="Tổng giờ", compute="_compute_tong_gio", store=True)
    
    loai_cong_viec = fields.Selection([
        ('thuong', 'Thường'),
        ('tăng_ca', 'Tăng ca'),
        ('lao_dung', 'Lao động thêm'),
    ], string="Loại công việc", default='thuong', tracking=True)
    
    mo_ta = fields.Text(string="Mô tả công việc")
    tien_do_phan_tram = fields.Float(string="% Tiến độ", default=0, help="0-100%")
    
    trang_thai = fields.Selection([
        ('draft', 'Nháp'),
        ('submitted', 'Đã nộp'),
        ('approved', 'Đã duyệt'),
        ('rejected', 'Từ chối'),
    ], string="Trạng thái", default='draft', tracking=True)
    
    nguoi_duyet_id = fields.Many2one('nhan_vien', string="Người duyệt", tracking=True)
    ngay_duyet = fields.Date(string="Ngày duyệt")
    
    ghi_chu = fields.Text(string="Ghi chú")
    
    # Tính lương
    luong_nhan = fields.Float(string="Lương nhận", compute="_compute_luong_nhan", store=False, help="Dùng cho tính lương")
    
    @api.depends('nhan_vien_id', 'ngay_lam', 'cong_viec_id')
    def _compute_display_name(self):
        for record in self:
            if record.nhan_vien_id and record.ngay_lam:
                record.display_name = f"{record.nhan_vien_id.ho_va_ten} - {record.ngay_lam} - {record.cong_viec_id.ten_cong_viec or ''}"
            else:
                record.display_name = False
    
    @api.depends('gio_bat_dau', 'gio_ket_thuc')
    def _compute_tong_gio(self):
        for record in self:
            if record.gio_bat_dau > 0 and record.gio_ket_thuc > record.gio_bat_dau:
                record.tong_gio = record.gio_ket_thuc - record.gio_bat_dau
            else:
                record.tong_gio = 0
    
    @api.depends('tong_gio', 'loai_cong_viec', 'nhan_vien_id')
    def _compute_luong_nhan(self):
        """Tính lương dựa trên giờ làm (dùng cho tinh_luong)"""
        today = fields.Date.today()
        for record in self:
            luong_co_ban = 0.0
            if record.nhan_vien_id:
                hop_dong = self.env['hop_dong'].search([
                    ('nhan_vien_id', '=', record.nhan_vien_id.id),
                    ('trang_thai', '=', 'active'),
                    ('luong_co_ban', '>', 0),
                ], limit=1, order='ngay_bat_dau desc')
                if hop_dong:
                    luong_co_ban = hop_dong.luong_co_ban
            if luong_co_ban:
                luong_gio = luong_co_ban / 176.0
                if record.loai_cong_viec == 'tăng_ca':
                    record.luong_nhan = record.tong_gio * luong_gio * 1.5
                elif record.loai_cong_viec == 'lao_dung':
                    record.luong_nhan = record.tong_gio * luong_gio * 2.0
                else:
                    record.luong_nhan = record.tong_gio * luong_gio
            else:
                record.luong_nhan = 0.0
    
    @api.constrains('gio_bat_dau', 'gio_ket_thuc')
    def _check_time(self):
        for record in self:
            # Dùng > 0 để kiểm tra đã nhập thực sự (float 0.0 được coi là False)
            if record.gio_bat_dau > 0 and record.gio_ket_thuc > 0:
                if record.gio_bat_dau >= record.gio_ket_thuc:
                    raise ValidationError(_("Giờ bắt đầu không thể lớn hơn hoặc bằng giờ kết thúc!"))
                tong = record.gio_ket_thuc - record.gio_bat_dau
                if tong > 12:
                    raise ValidationError(_("Không được làm việc quá 12 giờ/ngày! (%.1f giờ)" % tong))
    
    def action_submit(self):
        """Nộp timesheet"""
        for record in self:
            if record.trang_thai != 'draft':
                raise ValidationError(_("Chỉ timesheet ở trạng thái Nháp mới được nộp!"))
        self.trang_thai = 'submitted'
    
    def action_approve(self):
        """Duyệt timesheet"""
        for record in self:
            if record.trang_thai != 'submitted':
                raise ValidationError(_("Chỉ timesheet đã nộp mới được duyệt!"))
            record.trang_thai = 'approved'
            record.nguoi_duyet_id = self.env.user.nhan_vien_id
            record.ngay_duyet = fields.Date.today()

            # Cập nhật tiến độ công việc
            if record.cong_viec_id:
                record.cong_viec_id._update_progress_from_timesheet()
    
    def action_reject(self):
        """Từ chối timesheet"""
        for record in self:
            if record.trang_thai != 'submitted':
                raise ValidationError(_("Chỉ timesheet đã nộp mới được từ chối!"))
        self.trang_thai = 'rejected'